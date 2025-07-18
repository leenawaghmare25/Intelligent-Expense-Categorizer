"""
Receipt Image Processing Module

This module provides comprehensive receipt image processing capabilities using
OpenCV and pytesseract with best practices for production use.
"""

import cv2
import numpy as np
import pytesseract
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageEnhance
import imutils
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation

from PYTHON.exceptions import ValidationError, DatabaseError
from PYTHON.models import db, Expense, User
from PYTHON.utils import sanitize_input, validate_expense_data, setup_logger

# Configure logger
logger = setup_logger(__name__)

@dataclass
class ReceiptItem:
    """Data class for individual receipt items."""
    name: str
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    category: Optional[str] = None

@dataclass
class ReceiptData:
    """Data class for complete receipt information."""
    merchant_name: Optional[str] = None
    merchant_address: Optional[str] = None
    date: Optional[datetime] = None
    time: Optional[str] = None
    items: List[ReceiptItem] = None
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total: Optional[Decimal] = None
    payment_method: Optional[str] = None
    receipt_number: Optional[str] = None
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.items is None:
            self.items = []

class ReceiptImageProcessor:
    """
    Advanced receipt image processor with OCR capabilities.
    
    This class handles receipt image preprocessing, text extraction,
    and structured data parsing with comprehensive error handling.
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize the receipt processor.
        
        Args:
            tesseract_path: Path to tesseract executable (if not in PATH)
        """
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        
        # Configure tesseract path if provided
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Regex patterns for data extraction
        self._init_patterns()
        
        # Common merchant names for better recognition
        self._init_merchant_database()
    
    def _init_patterns(self):
        """Initialize regex patterns for data extraction."""
        self.patterns = {
            'price': re.compile(r'\$?(\d+\.?\d{0,2})', re.IGNORECASE),
            'date': re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', re.IGNORECASE),
            'time': re.compile(r'(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)', re.IGNORECASE),
            'total': re.compile(r'(?:total|amount|sum)[\s:]*\$?(\d+\.?\d{0,2})', re.IGNORECASE),
            'tax': re.compile(r'(?:tax|hst|gst|vat)[\s:]*\$?(\d+\.?\d{0,2})', re.IGNORECASE),
            'subtotal': re.compile(r'(?:subtotal|sub-total|sub total)[\s:]*\$?(\d+\.?\d{0,2})', re.IGNORECASE),
            'receipt_number': re.compile(r'(?:receipt|ref|transaction)[\s#:]*([A-Z0-9]+)', re.IGNORECASE),
            'phone': re.compile(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', re.IGNORECASE),
            'email': re.compile(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE)
        }
    
    def _init_merchant_database(self):
        """Initialize common merchant names for better recognition."""
        self.common_merchants = {
            'walmart', 'target', 'costco', 'amazon', 'starbucks', 'mcdonalds',
            'subway', 'kfc', 'pizza hut', 'dominos', 'taco bell', 'burger king',
            'home depot', 'lowes', 'best buy', 'cvs', 'walgreens', 'rite aid',
            'safeway', 'kroger', 'publix', 'whole foods', 'trader joes'
        }
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess receipt image for optimal OCR results.
        
        Args:
            image_path: Path to the receipt image
            
        Returns:
            Preprocessed image as numpy array
            
        Raises:
            ValidationError: If image cannot be loaded or processed
        """
        try:
            self.logger.info(f"Preprocessing image: {image_path}")
            
            # Load image
            if isinstance(image_path, str):
                if not Path(image_path).exists():
                    raise ValidationError(f"Image file not found: {image_path}")
                image = cv2.imread(image_path)
            else:
                # Handle PIL Image or numpy array
                if hasattr(image_path, 'save'):  # PIL Image
                    image = cv2.cvtColor(np.array(image_path), cv2.COLOR_RGB2BGR)
                else:  # numpy array
                    image = image_path
            
            if image is None:
                raise ValidationError("Could not load image")
            
            self.logger.debug(f"Original image shape: {image.shape}")
            
            # Resize image if too large (for performance)
            height, width = image.shape[:2]
            if width > 2000 or height > 2000:
                image = imutils.resize(image, width=min(2000, width))
                self.logger.debug(f"Resized image to: {image.shape}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply multiple preprocessing techniques and choose the best
            processed_images = []
            
            # Method 1: Basic threshold
            _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(('basic_threshold', thresh1))
            
            # Method 2: Adaptive threshold
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            processed_images.append(('adaptive_threshold', adaptive))
            
            # Method 3: Morphological operations
            kernel = np.ones((1, 1), np.uint8)
            morph = cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, kernel)
            processed_images.append(('morphological', morph))
            
            # Method 4: Gaussian blur + threshold
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh_blur = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(('gaussian_threshold', thresh_blur))
            
            # Choose the best preprocessing method based on text confidence
            best_image = self._select_best_preprocessing(processed_images)
            
            self.logger.info("Image preprocessing completed successfully")
            return best_image
            
        except Exception as e:
            self.logger.error(f"Error preprocessing image: {str(e)}")
            raise ValidationError(f"Image preprocessing failed: {str(e)}")
    
    def _select_best_preprocessing(self, processed_images: List[Tuple[str, np.ndarray]]) -> np.ndarray:
        """
        Select the best preprocessing method based on OCR confidence.
        
        Args:
            processed_images: List of (method_name, processed_image) tuples
            
        Returns:
            Best preprocessed image
        """
        best_confidence = 0
        best_image = processed_images[0][1]  # Default to first method
        
        for method_name, image in processed_images:
            try:
                # Get OCR confidence for this preprocessing method
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                self.logger.debug(f"Method {method_name}: confidence = {avg_confidence:.2f}")
                
                if avg_confidence > best_confidence:
                    best_confidence = avg_confidence
                    best_image = image
                    
            except Exception as e:
                self.logger.warning(f"Could not evaluate method {method_name}: {str(e)}")
                continue
        
        self.logger.info(f"Selected preprocessing method with confidence: {best_confidence:.2f}")
        return best_image
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extract text from preprocessed image using OCR.
        
        Args:
            image: Preprocessed image
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            self.logger.info("Extracting text using OCR")
            
            # Configure tesseract for better receipt recognition
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/$:()-# '
            
            # Extract text with confidence data
            data = pytesseract.image_to_data(image, config=custom_config, output_type=pytesseract.Output.DICT)
            
            # Calculate overall confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Extract text
            text = pytesseract.image_to_string(image, config=custom_config)
            
            self.logger.info(f"Text extraction completed. Confidence: {avg_confidence:.2f}%")
            self.logger.debug(f"Extracted text length: {len(text)} characters")
            
            return text.strip(), avg_confidence / 100.0  # Convert to 0-1 scale
            
        except Exception as e:
            self.logger.error(f"Error extracting text: {str(e)}")
            raise ValidationError(f"Text extraction failed: {str(e)}")
    
    def parse_receipt_data(self, text: str, confidence: float) -> ReceiptData:
        """
        Parse extracted text into structured receipt data.
        
        Args:
            text: Raw OCR text
            confidence: OCR confidence score
            
        Returns:
            Structured receipt data
        """
        try:
            self.logger.info("Parsing receipt data from extracted text")
            
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            receipt_data = ReceiptData(confidence_score=confidence)
            
            # Parse different sections
            receipt_data.merchant_name = self._extract_merchant_name(lines)
            receipt_data.date = self._extract_date(text)
            receipt_data.time = self._extract_time(text)
            receipt_data.total = self._extract_total(text)
            receipt_data.tax = self._extract_tax(text)
            receipt_data.subtotal = self._extract_subtotal(text)
            receipt_data.receipt_number = self._extract_receipt_number(text)
            receipt_data.items = self._extract_items(lines)
            
            # Validate extracted data
            self._validate_receipt_data(receipt_data)
            
            self.logger.info("Receipt data parsing completed successfully")
            return receipt_data
            
        except Exception as e:
            self.logger.error(f"Error parsing receipt data: {str(e)}")
            raise ValidationError(f"Receipt parsing failed: {str(e)}")
    
    def _extract_merchant_name(self, lines: List[str]) -> Optional[str]:
        """Extract merchant name from receipt lines."""
        # Usually the merchant name is in the first few lines
        for line in lines[:5]:
            line_lower = line.lower()
            for merchant in self.common_merchants:
                if merchant in line_lower:
                    return line.title()
        
        # If no known merchant found, return the first substantial line
        for line in lines[:3]:
            if len(line) > 3 and not re.match(r'^\d+$', line):
                return sanitize_input(line.title())
        
        return None
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract date from receipt text."""
        matches = self.patterns['date'].findall(text)
        if matches:
            date_str = matches[0]
            # Try different date formats
            formats = ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y', 
                      '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        
        return None
    
    def _extract_time(self, text: str) -> Optional[str]:
        """Extract time from receipt text."""
        matches = self.patterns['time'].findall(text)
        return matches[0] if matches else None
    
    def _extract_total(self, text: str) -> Optional[Decimal]:
        """Extract total amount from receipt text."""
        matches = self.patterns['total'].findall(text)
        if matches:
            try:
                return Decimal(matches[-1])  # Take the last match (usually the final total)
            except InvalidOperation:
                pass
        return None
    
    def _extract_tax(self, text: str) -> Optional[Decimal]:
        """Extract tax amount from receipt text."""
        matches = self.patterns['tax'].findall(text)
        if matches:
            try:
                return Decimal(matches[-1])
            except InvalidOperation:
                pass
        return None
    
    def _extract_subtotal(self, text: str) -> Optional[Decimal]:
        """Extract subtotal amount from receipt text."""
        matches = self.patterns['subtotal'].findall(text)
        if matches:
            try:
                return Decimal(matches[-1])
            except InvalidOperation:
                pass
        return None
    
    def _extract_receipt_number(self, text: str) -> Optional[str]:
        """Extract receipt number from receipt text."""
        matches = self.patterns['receipt_number'].findall(text)
        return matches[0] if matches else None
    
    def _extract_items(self, lines: List[str]) -> List[ReceiptItem]:
        """Extract individual items from receipt lines."""
        items = []
        
        # Look for lines that contain both text and prices
        for line in lines:
            # Skip lines that are clearly headers, totals, etc.
            if any(keyword in line.lower() for keyword in 
                   ['total', 'subtotal', 'tax', 'change', 'cash', 'card', 'receipt']):
                continue
            
            # Look for price patterns in the line
            price_matches = self.patterns['price'].findall(line)
            if price_matches:
                # Extract item name (text before the price)
                price_pattern = r'\$?\d+\.?\d{0,2}'
                item_name = re.sub(price_pattern, '', line).strip()
                
                if len(item_name) > 2:  # Valid item name
                    try:
                        price = Decimal(price_matches[-1])  # Take the last price (usually the total for that item)
                        items.append(ReceiptItem(
                            name=sanitize_input(item_name),
                            total_price=price
                        ))
                    except InvalidOperation:
                        continue
        
        return items
    
    def _validate_receipt_data(self, receipt_data: ReceiptData) -> None:
        """Validate extracted receipt data for consistency."""
        # Check if total matches sum of items (if available)
        if receipt_data.total and receipt_data.items:
            items_total = sum(item.total_price for item in receipt_data.items 
                            if item.total_price is not None)
            if items_total > 0:
                difference = abs(float(receipt_data.total) - float(items_total))
                if difference > 1.0:  # Allow small discrepancies
                    self.logger.warning(f"Total mismatch: receipt total {receipt_data.total}, items total {items_total}")
        
        # Validate date is not in the future
        if receipt_data.date and receipt_data.date > datetime.now():
            self.logger.warning("Receipt date is in the future")
            receipt_data.date = None

class ReceiptExpenseManager:
    """
    Manager class for handling receipt-based expense creation and storage.
    
    This class handles the business logic for converting receipt data
    into expense records and storing them in the database.
    """
    
    def __init__(self):
        """Initialize the receipt expense manager."""
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        self.processor = ReceiptImageProcessor()
    
    def process_receipt_image(self, image_path: str, user_id: int, 
                            category_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a receipt image and create expense records.
        
        Args:
            image_path: Path to the receipt image
            user_id: ID of the user uploading the receipt
            category_override: Optional category override
            
        Returns:
            Dictionary containing processing results and created expenses
            
        Raises:
            ValidationError: If processing fails
            DatabaseError: If database operations fail
        """
        try:
            self.logger.info(f"Processing receipt image for user {user_id}")
            
            # Validate user exists
            user = User.query.get(user_id)
            if not user:
                raise ValidationError(f"User with ID {user_id} not found")
            
            # Process the image
            preprocessed_image = self.processor.preprocess_image(image_path)
            text, confidence = self.processor.extract_text(preprocessed_image)
            receipt_data = self.processor.parse_receipt_data(text, confidence)
            
            # Create expense records
            expenses = self._create_expenses_from_receipt(receipt_data, user_id, category_override)
            
            # Store in database
            stored_expenses = self._store_expenses(expenses)
            
            result = {
                'success': True,
                'receipt_data': asdict(receipt_data),
                'expenses_created': len(stored_expenses),
                'expenses': [self._expense_to_dict(exp) for exp in stored_expenses],
                'confidence_score': confidence,
                'processing_summary': {
                    'merchant': receipt_data.merchant_name,
                    'date': receipt_data.date.isoformat() if receipt_data.date else None,
                    'total': float(receipt_data.total) if receipt_data.total else None,
                    'items_count': len(receipt_data.items)
                }
            }
            
            self.logger.info(f"Receipt processing completed successfully. Created {len(stored_expenses)} expenses")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing receipt: {str(e)}")
            raise
    
    def _create_expenses_from_receipt(self, receipt_data: ReceiptData, user_id: int, 
                                   category_override: Optional[str] = None) -> List[Expense]:
        """Create expense objects from receipt data."""
        expenses = []
        
        # If we have individual items, create separate expenses for each
        if receipt_data.items:
            for item in receipt_data.items:
                if item.total_price and item.total_price > 0:
                    expense_data = {
                        'description': f"{receipt_data.merchant_name or 'Receipt'} - {item.name}",
                        'amount': float(item.total_price),
                        'date': receipt_data.date or datetime.now(),
                        'user_id': user_id,
                        'receipt_data': {
                            'merchant': receipt_data.merchant_name,
                            'receipt_number': receipt_data.receipt_number,
                            'item_name': item.name,
                            'confidence': receipt_data.confidence_score
                        }
                    }
                    
                    # Validate expense data
                    validated_data = validate_expense_data(expense_data)
                    
                    # Create expense object (category will be predicted by ML model)
                    expense = Expense(
                        description=validated_data['description'],
                        amount=validated_data['amount'],
                        date=validated_data['date'],
                        user_id=user_id,
                        predicted_category=category_override,  # Will be set by ML model if None
                        confidence_score=receipt_data.confidence_score,
                        source='receipt_upload',
                        expense_metadata=expense_data['receipt_data']
                    )
                    
                    expenses.append(expense)
        
        # If no individual items or as fallback, create one expense for the total
        elif receipt_data.total and receipt_data.total > 0:
            expense_data = {
                'description': f"{receipt_data.merchant_name or 'Receipt Purchase'}",
                'amount': float(receipt_data.total),
                'date': receipt_data.date or datetime.now(),
                'user_id': user_id,
                'receipt_data': {
                    'merchant': receipt_data.merchant_name,
                    'receipt_number': receipt_data.receipt_number,
                    'total': float(receipt_data.total),
                    'confidence': receipt_data.confidence_score
                }
            }
            
            validated_data = validate_expense_data(expense_data)
            
            expense = Expense(
                description=validated_data['description'],
                amount=validated_data['amount'],
                date=validated_data['date'],
                user_id=user_id,
                predicted_category=category_override,
                confidence_score=receipt_data.confidence_score,
                source='receipt_upload',
                expense_metadata=expense_data['receipt_data']
            )
            
            expenses.append(expense)
        
        return expenses
    
    def _store_expenses(self, expenses: List[Expense]) -> List[Expense]:
        """Store expenses in the database with proper error handling."""
        try:
            stored_expenses = []
            
            for expense in expenses:
                # Use ML model to predict category if not provided
                if not expense.predicted_category:
                    try:
                        from PYTHON.ml_models import EnsembleExpenseClassifier
                        classifier = EnsembleExpenseClassifier()
                        classifier.load_models()
                        
                        prediction = classifier.predict(expense.description)
                        expense.predicted_category = prediction['category']
                        expense.confidence_score = min(expense.confidence_score, prediction['confidence'])
                        
                    except Exception as e:
                        self.logger.warning(f"Could not predict category: {str(e)}")
                        expense.predicted_category = 'Other'
                
                # Add to database session
                db.session.add(expense)
                stored_expenses.append(expense)
            
            # Commit all expenses
            db.session.commit()
            self.logger.info(f"Successfully stored {len(stored_expenses)} expenses")
            
            return stored_expenses
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error storing expenses: {str(e)}")
            raise DatabaseError(f"Failed to store expenses: {str(e)}")
    
    def _expense_to_dict(self, expense: Expense) -> Dict[str, Any]:
        """Convert expense object to dictionary for JSON serialization."""
        return {
            'id': expense.id,
            'description': expense.description,
            'amount': float(expense.amount),
            'date': expense.date.isoformat(),
            'predicted_category': expense.predicted_category,
            'confidence_score': expense.confidence_score,
            'source': expense.source,
            'expense_metadata': expense.expense_metadata
        }

# Convenience function for easy usage
def process_receipt_image(image_path: str, user_id: int, 
                         category_override: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to process a receipt image.
    
    Args:
        image_path: Path to the receipt image
        user_id: ID of the user uploading the receipt
        category_override: Optional category override
        
    Returns:
        Processing results dictionary
    """
    manager = ReceiptExpenseManager()
    return manager.process_receipt_image(image_path, user_id, category_override)