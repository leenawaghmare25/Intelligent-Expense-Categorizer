#!/usr/bin/env python3
"""
Improved Receipt Processor focusing on extracting only important items and their amounts.
Uses advanced pattern matching and filtering to reduce noise.
"""

import cv2
import numpy as np
import pytesseract
import re
import logging
import os
import platform
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import imutils
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation

from PYTHON.utils import setup_logger

@dataclass
class ReceiptItem:
    """Represents a single item from a receipt."""
    name: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_price: float = 0.0
    confidence: float = 0.0
    line_number: int = 0

@dataclass
class ReceiptData:
    """Structured receipt data."""
    merchant_name: str = ""
    date: Optional[datetime] = None
    time: Optional[str] = None
    items: List[ReceiptItem] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    receipt_number: Optional[str] = None
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.items is None:
            self.items = []

class ImprovedReceiptProcessor:
    """
    Improved receipt processor that focuses on extracting only important items
    and their specific amounts while filtering out unwanted noise.
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """Initialize the improved receipt processor."""
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        
        # Configure tesseract path
        self._configure_tesseract(tesseract_path)
        
        # Enhanced price patterns with better precision
        self.price_patterns = [
            r'\$\s*(\d{1,4}(?:,\d{3})*\.\d{2})',  # $1,234.56 or $12.34
            r'(\d{1,4}(?:,\d{3})*\.\d{2})\s*\$',  # 1,234.56$ or 12.34$
            r'(\d{1,4}(?:,\d{3})*\.\d{2})(?=\s|$|[^\d.])',  # 12.34 (standalone)
        ]
        
        # Comprehensive exclusion patterns for non-items
        self.exclude_patterns = [
            # Totals and summaries
            r'^(sub\s*total|subtotal|sub-total).*',
            r'^(total|grand\s*total|final\s*total).*',
            r'^(tax|sales\s*tax|hst|gst|pst|vat).*',
            r'^(change|cash|credit|debit|payment).*',
            r'^(balance|amount\s*due|due).*',
            
            # Receipt metadata
            r'^(receipt|rcpt|#|no\.|number|ref).*',
            r'^(date|time|store|location|address).*',
            r'^(phone|tel|email|website|www).*',
            r'^(cashier|clerk|server|operator).*',
            r'^(transaction|trans|txn).*',
            
            # Common receipt text
            r'^(thank\s*you|thanks|visit|welcome).*',
            r'^(have\s*a|nice\s*day|good\s*day).*',
            r'^(customer|member|card).*',
            r'^(points|rewards|savings).*',
            r'^(return\s*policy|exchange).*',
            
            # Dates and times
            r'^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}$',
            r'^\d{1,2}:\d{2}(:\d{2})?\s*(am|pm)?$',
            r'^(mon|tue|wed|thu|fri|sat|sun).*',
            r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).*',
            
            # Contact info
            r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$',
            r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$',
            
            # Barcodes and codes
            r'^\d{10,}$',  # Long number sequences (barcodes)
            r'^[A-Z0-9]{8,}$',  # Long alphanumeric codes
            
            # Very short or meaningless text
            r'^.{1,2}$',  # 1-2 characters
            r'^[^\w]*$',  # Only special characters
        ]
        
        # Item validation patterns (what SHOULD be items)
        self.item_indicators = [
            r'[a-zA-Z]{3,}',  # At least 3 consecutive letters
            r'\b(pack|bottle|can|box|bag|lb|oz|kg|g|ml|l)\b',  # Units
            r'\b(organic|fresh|frozen|diet|light|low)\b',  # Descriptors
        ]
        
        # Common merchant indicators for better merchant detection
        self.merchant_indicators = [
            'walmart', 'target', 'costco', 'safeway', 'kroger', 'publix', 'whole foods',
            'mcdonald', 'starbucks', 'subway', 'kfc', 'pizza', 'burger', 'taco bell',
            'home depot', 'lowes', 'best buy', 'amazon', 'apple store', 'microsoft',
            'cvs', 'walgreens', 'rite aid', 'pharmacy', 'dollar', 'family dollar',
            'shell', 'exxon', 'bp', 'chevron', 'mobil', 'gas', 'fuel',
            'restaurant', 'cafe', 'deli', 'market', 'store', 'shop'
        ]
        
        # Quantity indicators
        self.quantity_patterns = [
            r'(\d+(?:\.\d+)?)\s*x\s*\$?(\d+\.\d{2})',  # 2 x $5.99
            r'(\d+(?:\.\d+)?)\s*@\s*\$?(\d+\.\d{2})',  # 2 @ $5.99
            r'qty\s*(\d+(?:\.\d+)?)',  # qty 2
            r'(\d+(?:\.\d+)?)\s*(ea|each|pc|pcs)',  # 2 ea
            r'(\d+(?:\.\d+)?)\s*(lb|lbs|oz|kg|g)',  # 2 lbs
        ]

    def _configure_tesseract(self, tesseract_path: Optional[str]):
        """Configure tesseract path with auto-detection."""
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        elif platform.system() == 'Windows':
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self.logger.info(f"Found Tesseract at: {path}")
                    break

    def preprocess_image_advanced(self, image_path: str) -> np.ndarray:
        """Advanced image preprocessing optimized for receipt text extraction."""
        self.logger.info(f"Preprocessing image: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Convert to PIL for initial enhancement
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Enhance contrast and sharpness
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.8)  # Increased contrast
        
        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(1.5)  # Increased sharpness
        
        # Convert back to OpenCV
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Resize for optimal OCR (minimum 1200px width)
        height, width = image.shape[:2]
        if width < 1200:
            scale_factor = 1200 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive threshold for better text separation
        adaptive = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10
        )
        
        # Morphological operations to clean up text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        cleaned = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel)
        
        self.logger.info("Advanced image preprocessing completed")
        return cleaned

    def extract_text_with_confidence(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text with high confidence using optimized OCR settings."""
        self.logger.info("Extracting text with optimized OCR settings")
        
        # Try different OCR approaches
        results = []
        
        # Method 1: Simple string extraction
        try:
            text1 = pytesseract.image_to_string(image, config='--psm 6')
            lines1 = [line.strip() for line in text1.split('\n') if line.strip()]
            results.append(('simple', lines1, 0.7))
        except Exception as e:
            self.logger.warning(f"Simple OCR failed: {e}")
        
        # Method 2: Detailed data extraction
        try:
            data = pytesseract.image_to_data(
                image, 
                output_type=pytesseract.Output.DICT,
                config='--psm 6'
            )
            
            # Process detailed data
            lines = []
            current_line = []
            current_line_num = -1
            
            for i, word in enumerate(data['text']):
                if int(data['conf'][i]) > 30 and word.strip():
                    line_num = data['line_num'][i]
                    
                    if line_num != current_line_num:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                        current_line_num = line_num
                    else:
                        current_line.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Calculate confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = np.mean(confidences) / 100.0 if confidences else 0.5
            
            results.append(('detailed', lines, avg_confidence))
            
        except Exception as e:
            self.logger.warning(f"Detailed OCR failed: {e}")
        
        # Choose the best result
        if not results:
            return {
                'text': '',
                'confidence': 0.0,
                'lines': [],
                'line_confidences': []
            }
        
        # Pick the result with more lines and reasonable confidence
        best_result = max(results, key=lambda x: len(x[1]) * x[2])
        method, lines, confidence = best_result
        
        # Clean up lines
        clean_lines = []
        for line in lines:
            cleaned = line.strip()
            if cleaned and len(cleaned) > 1:
                clean_lines.append(cleaned)
        
        self.logger.info(f"Text extraction completed using {method} method. Confidence: {confidence*100:.2f}%")
        
        return {
            'text': '\n'.join(clean_lines),
            'confidence': confidence,
            'lines': clean_lines,
            'line_confidences': [confidence * 100] * len(clean_lines)
        }

    def extract_items_smart(self, text_data: Dict[str, Any]) -> List[ReceiptItem]:
        """Smart extraction of items using advanced filtering and validation."""
        self.logger.info("Extracting items using smart filtering")
        
        lines = text_data['lines']
        line_confidences = text_data.get('line_confidences', [50] * len(lines))
        items = []
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Skip lines that should be excluded
            if self._should_exclude_line_smart(line):
                continue
            
            # Extract prices from the line
            prices = self._extract_prices_precise(line)
            if not prices:
                continue
            
            # Extract item name
            item_name = self._extract_item_name_smart(line, prices)
            if not item_name:
                continue
            
            # Validate that this is a real item
            if not self._is_valid_item_smart(item_name, line):
                continue
            
            # Use the rightmost price as total price
            total_price = prices[-1]
            
            # Extract quantity and unit price
            quantity, unit_price = self._extract_quantity_smart(line, total_price)
            
            # Calculate confidence
            confidence = self._calculate_item_confidence_smart(
                line, item_name, total_price, line_idx, line_confidences
            )
            
            # Only include items with reasonable confidence
            if confidence < 0.3:  # More lenient threshold
                continue
            
            item = ReceiptItem(
                name=item_name.strip(),
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                confidence=confidence,
                line_number=line_idx
            )
            
            items.append(item)
        
        # Post-process to remove duplicates and improve quality
        items = self._post_process_items_smart(items)
        
        self.logger.info(f"Extracted {len(items)} high-quality items")
        return items

    def _should_exclude_line_smart(self, line: str) -> bool:
        """Smart exclusion of non-item lines."""
        line_lower = line.lower().strip()
        
        # Check all exclusion patterns
        for pattern in self.exclude_patterns:
            if re.match(pattern, line_lower, re.IGNORECASE):
                return True
        
        # Exclude lines with only numbers and special characters
        alpha_count = sum(1 for c in line_lower if c.isalpha())
        if alpha_count < 3:  # Need at least 3 letters for a valid item
            return True
        
        # Exclude lines that are mostly uppercase (likely headers)
        upper_count = sum(1 for c in line if c.isupper())
        if len(line) > 5 and upper_count / len(line) > 0.8:
            return True
        
        # Exclude lines with suspicious patterns
        if re.search(r'^\d+\s*$', line):  # Only numbers
            return True
        if re.search(r'^[^a-zA-Z]*$', line):  # No letters
            return True
        
        return False

    def _extract_prices_precise(self, line: str) -> List[float]:
        """Extract prices with high precision."""
        prices = []
        
        for pattern in self.price_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                try:
                    # Clean and convert
                    price_str = match.replace(',', '').replace('$', '').strip()
                    price = float(price_str)
                    
                    # Validate reasonable price range
                    if 0.01 <= price <= 9999.99:
                        prices.append(price)
                except (ValueError, TypeError):
                    continue
        
        # Remove duplicates and sort
        return sorted(list(set(prices)))

    def _extract_item_name_smart(self, line: str, prices: List[float]) -> str:
        """Smart extraction of item name."""
        item_name = line
        
        # Remove all price patterns
        for pattern in self.price_patterns:
            item_name = re.sub(pattern, '', item_name)
        
        # Remove quantity patterns
        for pattern in self.quantity_patterns:
            item_name = re.sub(pattern, '', item_name, re.IGNORECASE)
        
        # Remove common receipt artifacts
        item_name = re.sub(r'\s*@\s*\d+\.\d{2}', '', item_name)
        item_name = re.sub(r'\s*#\d+', '', item_name)
        item_name = re.sub(r'\s*\d+\s*$', '', item_name)
        item_name = re.sub(r'^\s*\d+\s*', '', item_name)  # Leading numbers
        
        # Remove merchant names from the beginning if they appear
        for merchant in self.merchant_indicators:
            pattern = r'^' + re.escape(merchant) + r'\s+'
            item_name = re.sub(pattern, '', item_name, re.IGNORECASE)
        
        # Remove common store-related words from the beginning
        store_words = ['store', 'market', 'shop', 'grocery', 'supermarket']
        for word in store_words:
            pattern = r'^' + word + r'\s+'
            item_name = re.sub(pattern, '', item_name, re.IGNORECASE)
        
        # Clean whitespace and special characters
        item_name = re.sub(r'\s+', ' ', item_name).strip()
        item_name = re.sub(r'^[^\w]+|[^\w\s]+$', '', item_name)
        
        return item_name

    def _is_valid_item_smart(self, item_name: str, full_line: str) -> bool:
        """Smart validation of item names."""
        if not item_name or len(item_name) < 3:
            return False
        
        # Check for product-like characteristics
        word_count = len(item_name.split())
        has_multiple_words = word_count >= 2
        has_reasonable_length = 3 <= len(item_name) <= 50
        has_letters = re.search(r'[a-zA-Z]{3,}', item_name)
        
        # Exclude obvious non-items
        exclude_words = {
            'total', 'subtotal', 'tax', 'change', 'cash', 'credit', 'debit',
            'receipt', 'store', 'date', 'time', 'cashier', 'thank', 'visit',
            'balance', 'payment', 'card', 'member', 'customer', 'points',
            'phone', 'email', 'website', 'address'
        }
        
        words = set(item_name.lower().split())
        if words.intersection(exclude_words):
            return False
        
        # Must have at least one item indicator OR be a reasonable product name
        has_indicator = any(re.search(pattern, item_name, re.IGNORECASE) 
                          for pattern in self.item_indicators)
        
        # More lenient validation - if it has letters and reasonable length, likely an item
        is_likely_product = (has_letters and has_reasonable_length and 
                           not re.match(r'^(sub\s*total|total|tax|change|cash|credit|debit).*', item_name.lower()))
        
        return (has_indicator or has_multiple_words or is_likely_product) and has_reasonable_length

    def _extract_quantity_smart(self, line: str, total_price: float) -> Tuple[Optional[float], Optional[float]]:
        """Smart extraction of quantity and unit price."""
        quantity = None
        unit_price = None
        
        for pattern in self.quantity_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) >= 2:
                        quantity = float(match.group(1))
                        unit_price = float(match.group(2))
                    else:
                        quantity = float(match.group(1))
                        if quantity > 0:
                            unit_price = total_price / quantity
                    break
                except (ValueError, ZeroDivisionError):
                    continue
        
        return quantity, unit_price

    def _calculate_item_confidence_smart(self, line: str, item_name: str, price: float, 
                                       line_idx: int, line_confidences: List[float]) -> float:
        """Calculate smart confidence score."""
        confidence = 0.5  # Base confidence
        
        # OCR confidence factor
        if line_idx < len(line_confidences):
            ocr_conf = line_confidences[line_idx] / 100.0
            confidence = (confidence + ocr_conf) / 2
        
        # Item name quality
        if len(item_name) >= 5:
            confidence += 0.1
        if len(item_name.split()) >= 2:
            confidence += 0.1
        if re.search(r'[A-Z][a-z]+', item_name):
            confidence += 0.1
        
        # Price reasonableness
        if 0.50 <= price <= 100.00:
            confidence += 0.2
        elif 0.01 <= price <= 500.00:
            confidence += 0.1
        
        # Line structure (item name + price pattern)
        if re.search(r'[a-zA-Z].+\$?\d+\.\d{2}', line):
            confidence += 0.1
        
        return min(confidence, 1.0)

    def _post_process_items_smart(self, items: List[ReceiptItem]) -> List[ReceiptItem]:
        """Smart post-processing to improve item quality."""
        if not items:
            return items
        
        # Sort by confidence
        items.sort(key=lambda x: x.confidence, reverse=True)
        
        # Remove duplicates
        filtered_items = []
        for item in items:
            is_duplicate = False
            for existing in filtered_items:
                # Check similarity
                name_similarity = self._calculate_similarity(item.name, existing.name)
                price_diff = abs(item.total_price - existing.total_price)
                
                if name_similarity > 0.7 and price_diff < 0.01:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_items.append(item)
        
        # Filter by confidence threshold
        high_quality_items = [item for item in filtered_items if item.confidence >= 0.4]
        
        # If we have too few high-quality items, include medium quality
        if len(high_quality_items) < 3:
            medium_quality = [item for item in filtered_items if 0.3 <= item.confidence < 0.4]
            high_quality_items.extend(medium_quality[:5])  # Add up to 5 medium quality items
        
        return high_quality_items

    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between item names."""
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()
        
        if name1 == name2:
            return 1.0
        
        # Jaccard similarity
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    def extract_receipt_metadata_smart(self, text_data: Dict[str, Any]) -> Dict[str, Any]:
        """Smart extraction of receipt metadata."""
        lines = text_data['lines']
        metadata = {
            'merchant_name': '',
            'date': None,
            'time': None,
            'subtotal': None,
            'tax': None,
            'total': None,
            'receipt_number': None
        }
        
        # Extract merchant from top lines
        for line in lines[:5]:
            line_clean = re.sub(r'[^\w\s]', '', line).strip()
            if len(line_clean) > 3:
                for merchant in self.merchant_indicators:
                    if merchant.lower() in line_clean.lower():
                        metadata['merchant_name'] = line_clean.title()
                        break
                if metadata['merchant_name']:
                    break
        
        # Fallback merchant detection
        if not metadata['merchant_name']:
            for line in lines[:3]:
                line_clean = re.sub(r'[^\w\s]', '', line).strip()
                if len(line_clean) > 5 and not re.match(r'^\d', line_clean):
                    metadata['merchant_name'] = line_clean.title()
                    break
        
        # Extract totals from bottom lines
        for line in reversed(lines[-15:]):
            line_lower = line.lower()
            prices = self._extract_prices_precise(line)
            
            if prices:
                price = prices[-1]
                
                if re.search(r'\btotal\b', line_lower) and not re.search(r'\bsub', line_lower):
                    metadata['total'] = price
                elif re.search(r'\b(subtotal|sub\s*total)\b', line_lower):
                    metadata['subtotal'] = price
                elif re.search(r'\btax\b', line_lower):
                    metadata['tax'] = price
        
        # Extract date
        date_patterns = [
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})',
        ]
        
        for line in lines[:10]:
            for pattern in date_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        date_str = match.group(1)
                        for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d', '%Y-%m-%d', '%m/%d/%y', '%m-%d-%y']:
                            try:
                                metadata['date'] = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                        if metadata['date']:
                            break
                    except Exception:
                        continue
            if metadata['date']:
                break
        
        return metadata

    def process_receipt_image(self, image_path: str) -> ReceiptData:
        """Process receipt image with improved accuracy."""
        self.logger.info(f"Processing receipt image with improved accuracy: {image_path}")
        
        try:
            # Advanced preprocessing
            processed_image = self.preprocess_image_advanced(image_path)
            
            # High-confidence text extraction
            text_data = self.extract_text_with_confidence(processed_image)
            
            # Smart item extraction
            items = self.extract_items_smart(text_data)
            
            # Smart metadata extraction
            metadata = self.extract_receipt_metadata_smart(text_data)
            
            # Create receipt data
            receipt_data = ReceiptData(
                merchant_name=metadata['merchant_name'],
                date=metadata['date'],
                time=metadata['time'],
                items=items,
                subtotal=metadata['subtotal'],
                tax=metadata['tax'],
                total=metadata['total'],
                receipt_number=metadata['receipt_number'],
                confidence_score=text_data['confidence']
            )
            
            self.logger.info(f"Successfully processed receipt: {len(items)} high-quality items extracted")
            return receipt_data
            
        except Exception as e:
            self.logger.error(f"Error processing receipt: {str(e)}")
            raise