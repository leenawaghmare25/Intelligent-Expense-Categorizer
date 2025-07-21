#!/usr/bin/env python3
"""
Advanced Receipt Processor using pre-trained models and best practices.
Focuses on extracting only important items and their specific amounts.
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
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import torch

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

class AdvancedReceiptProcessor:
    """
    Advanced receipt processor using pre-trained NLP models and computer vision
    to accurately extract only important items and their amounts.
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """Initialize the advanced receipt processor."""
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        
        # Configure tesseract path
        self._configure_tesseract(tesseract_path)
        
        # Initialize pre-trained models
        self._initialize_models()
        
        # Price patterns (more sophisticated)
        self.price_patterns = [
            r'\$\s*(\d+(?:\.\d{2})?)',  # $12.34 or $ 12.34
            r'(\d+\.\d{2})\s*\$',      # 12.34$
            r'(\d+,\d{3}\.\d{2})',     # 1,234.56
            r'(\d+\.\d{2})(?=\s|$)',   # 12.34 (standalone)
        ]
        
        # Item filtering patterns (what to exclude)
        self.exclude_patterns = [
            r'^(subtotal|sub total|sub-total)$',
            r'^(total|grand total)$',
            r'^(tax|sales tax|hst|gst|pst)$',
            r'^(change|cash|credit|debit)$',
            r'^(receipt|rcpt|#|no\.|number)$',
            r'^(date|time|store|location)$',
            r'^(thank you|thanks|visit)$',
            r'^(cashier|clerk|server)$',
            r'^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}$',  # dates
            r'^\d{1,2}:\d{2}(:\d{2})?\s*(am|pm)?$',   # times
            r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$',  # emails
            r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$',  # phones
        ]
        
        # Common merchant indicators
        self.merchant_indicators = [
            'walmart', 'target', 'costco', 'safeway', 'kroger', 'publix',
            'mcdonald', 'starbucks', 'subway', 'kfc', 'pizza', 'burger',
            'home depot', 'lowes', 'best buy', 'amazon', 'apple store',
            'cvs', 'walgreens', 'rite aid', 'pharmacy'
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

    def _initialize_models(self):
        """Initialize pre-trained models for NER and text processing."""
        try:
            # Load spaCy model for NER
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.logger.info("Loaded spaCy en_core_web_sm model")
            except OSError:
                self.logger.warning("spaCy en_core_web_sm not found, using basic processing")
                self.nlp = None
            
            # Initialize BERT-based NER for financial entities (if available)
            try:
                self.ner_pipeline = pipeline(
                    "ner",
                    model="dbmdz/bert-large-cased-finetuned-conll03-english",
                    tokenizer="dbmdz/bert-large-cased-finetuned-conll03-english",
                    aggregation_strategy="simple"
                )
                self.logger.info("Loaded BERT NER model")
            except Exception as e:
                self.logger.warning(f"Could not load BERT NER model: {e}")
                self.ner_pipeline = None
                
        except Exception as e:
            self.logger.error(f"Error initializing models: {e}")
            self.nlp = None
            self.ner_pipeline = None

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Advanced image preprocessing for better OCR accuracy."""
        self.logger.info(f"Preprocessing image: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Convert to PIL for initial processing
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Enhance image quality
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.5)
        
        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(1.2)
        
        # Convert back to OpenCV
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Resize if too small
        height, width = image.shape[:2]
        if height < 800 or width < 600:
            scale_factor = max(800/height, 600/width)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply multiple preprocessing techniques and choose the best
        methods = []
        
        # Method 1: Adaptive threshold
        adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        methods.append(("adaptive", adaptive))
        
        # Method 2: OTSU threshold
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        methods.append(("otsu", otsu))
        
        # Method 3: Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morph = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
        methods.append(("morphological", morph))
        
        # Method 4: Gaussian blur + threshold
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        methods.append(("gaussian", thresh))
        
        # Test each method and choose the one with highest OCR confidence
        best_method = None
        best_confidence = 0
        
        for method_name, processed_image in methods:
            try:
                # Quick OCR test on a small region
                h, w = processed_image.shape
                test_region = processed_image[h//4:3*h//4, w//4:3*w//4]
                
                # Get OCR confidence
                data = pytesseract.image_to_data(test_region, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = np.mean(confidences) if confidences else 0
                
                if avg_confidence > best_confidence:
                    best_confidence = avg_confidence
                    best_method = processed_image
                    
            except Exception as e:
                self.logger.warning(f"Error testing {method_name}: {e}")
                continue
        
        if best_method is None:
            best_method = adaptive  # fallback
            best_confidence = 50
        
        self.logger.info(f"Selected preprocessing method with confidence: {best_confidence:.2f}")
        return best_method

    def extract_text_with_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text with layout information using advanced OCR."""
        self.logger.info("Extracting text with layout information")
        
        # Use different PSM modes for better accuracy
        psm_modes = [6, 4, 3, 8]  # Different page segmentation modes
        best_result = None
        best_confidence = 0
        
        for psm in psm_modes:
            try:
                custom_config = f'--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!@#$%^&*()_+-=[]{{}}|;:\'\"<>?/~` '
                
                # Get detailed OCR data
                data = pytesseract.image_to_data(
                    image, 
                    output_type=pytesseract.Output.DICT,
                    config=custom_config
                )
                
                # Calculate average confidence
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = np.mean(confidences) if confidences else 0
                
                if avg_confidence > best_confidence:
                    best_confidence = avg_confidence
                    best_result = data
                    
            except Exception as e:
                self.logger.warning(f"Error with PSM {psm}: {e}")
                continue
        
        if best_result is None:
            # Fallback to simple OCR
            text = pytesseract.image_to_string(image)
            return {
                'text': text,
                'confidence': 50,
                'lines': text.split('\n'),
                'layout_data': None
            }
        
        # Process the best result
        lines = []
        current_line = []
        current_line_num = -1
        
        for i, word in enumerate(best_result['text']):
            if int(best_result['conf'][i]) > 30:  # Filter low confidence words
                line_num = best_result['line_num'][i]
                
                if line_num != current_line_num:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    current_line_num = line_num
                else:
                    current_line.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Filter empty lines
        lines = [line.strip() for line in lines if line.strip()]
        
        self.logger.info(f"Text extraction completed. Confidence: {best_confidence:.2f}%")
        
        return {
            'text': '\n'.join(lines),
            'confidence': best_confidence / 100.0,
            'lines': lines,
            'layout_data': best_result
        }

    def extract_items_and_prices(self, text_data: Dict[str, Any]) -> List[ReceiptItem]:
        """Extract only important items and their prices using advanced NLP."""
        self.logger.info("Extracting items and prices using advanced NLP")
        
        lines = text_data['lines']
        items = []
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip lines that match exclude patterns
            if self._should_exclude_line(line):
                continue
            
            # Extract prices from the line
            prices = self._extract_prices_from_line(line)
            if not prices:
                continue
            
            # Extract item name (everything before the price)
            item_name = self._extract_item_name(line, prices)
            if not item_name or len(item_name) < 2:
                continue
            
            # Validate that this looks like a real item
            if not self._is_valid_item(item_name):
                continue
            
            # Use the last (rightmost) price as the total price
            total_price = prices[-1]
            
            # Try to extract quantity and unit price
            quantity, unit_price = self._extract_quantity_and_unit_price(line, total_price)
            
            # Calculate confidence based on various factors
            confidence = self._calculate_item_confidence(line, item_name, total_price, text_data)
            
            item = ReceiptItem(
                name=item_name.strip(),
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                confidence=confidence,
                line_number=line_idx
            )
            
            items.append(item)
        
        # Post-process items to remove duplicates and improve accuracy
        items = self._post_process_items(items)
        
        self.logger.info(f"Extracted {len(items)} valid items")
        return items

    def _should_exclude_line(self, line: str) -> bool:
        """Check if a line should be excluded based on patterns."""
        line_lower = line.lower().strip()
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if re.match(pattern, line_lower, re.IGNORECASE):
                return True
        
        # Exclude very short lines
        if len(line_lower) < 3:
            return True
        
        # Exclude lines that are mostly numbers/symbols
        alpha_chars = sum(1 for c in line_lower if c.isalpha())
        if alpha_chars < 2:
            return True
        
        # Exclude lines that look like headers/footers
        if any(word in line_lower for word in ['store', 'location', 'address', 'phone', 'website', 'hours']):
            return True
        
        return False

    def _extract_prices_from_line(self, line: str) -> List[float]:
        """Extract all prices from a line."""
        prices = []
        
        for pattern in self.price_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                try:
                    # Clean the match
                    price_str = match.replace(',', '').replace('$', '').strip()
                    price = float(price_str)
                    
                    # Validate price range (reasonable for receipt items)
                    if 0.01 <= price <= 9999.99:
                        prices.append(price)
                except (ValueError, TypeError):
                    continue
        
        return sorted(set(prices))  # Remove duplicates and sort

    def _extract_item_name(self, line: str, prices: List[float]) -> str:
        """Extract item name from line by removing prices and cleaning."""
        item_name = line
        
        # Remove all price patterns
        for pattern in self.price_patterns:
            item_name = re.sub(pattern, '', item_name)
        
        # Remove common receipt artifacts
        item_name = re.sub(r'\s*@\s*\d+\.\d{2}', '', item_name)  # @ unit price
        item_name = re.sub(r'\s*x\s*\d+', '', item_name, re.IGNORECASE)  # x quantity
        item_name = re.sub(r'\s*qty\s*\d+', '', item_name, re.IGNORECASE)  # qty
        item_name = re.sub(r'\s*#\d+', '', item_name)  # item numbers
        item_name = re.sub(r'\s*\d+\s*$', '', item_name)  # trailing numbers
        
        # Clean whitespace and special characters
        item_name = re.sub(r'\s+', ' ', item_name).strip()
        item_name = re.sub(r'^[^\w]+|[^\w]+$', '', item_name)  # Remove leading/trailing non-word chars
        
        return item_name

    def _is_valid_item(self, item_name: str) -> bool:
        """Check if the extracted item name looks like a valid product."""
        if not item_name or len(item_name) < 2:
            return False
        
        # Must contain at least some alphabetic characters
        if not re.search(r'[a-zA-Z]{2,}', item_name):
            return False
        
        # Exclude common non-item words
        exclude_words = {
            'total', 'subtotal', 'tax', 'change', 'cash', 'credit', 'debit',
            'receipt', 'store', 'date', 'time', 'cashier', 'clerk', 'server',
            'thank', 'you', 'thanks', 'visit', 'again', 'welcome', 'hello'
        }
        
        words = item_name.lower().split()
        if any(word in exclude_words for word in words):
            return False
        
        # Use NLP models if available
        if self.nlp:
            doc = self.nlp(item_name)
            # Check if it contains product-like entities
            has_product_entity = any(
                ent.label_ in ['PRODUCT', 'ORG', 'PERSON'] for ent in doc.ents
            )
            # Check POS tags for nouns
            has_noun = any(token.pos_ in ['NOUN', 'PROPN'] for token in doc)
            
            if not (has_product_entity or has_noun):
                return False
        
        return True

    def _extract_quantity_and_unit_price(self, line: str, total_price: float) -> Tuple[Optional[float], Optional[float]]:
        """Extract quantity and unit price if available."""
        quantity = None
        unit_price = None
        
        # Look for quantity patterns
        qty_patterns = [
            r'(\d+(?:\.\d+)?)\s*x\s*\$?(\d+\.\d{2})',  # 2 x $5.99
            r'(\d+(?:\.\d+)?)\s*@\s*\$?(\d+\.\d{2})',  # 2 @ $5.99
            r'qty\s*(\d+(?:\.\d+)?)',  # qty 2
            r'(\d+(?:\.\d+)?)\s*ea',   # 2 ea
        ]
        
        for pattern in qty_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 2:
                        quantity = float(match.group(1))
                        unit_price = float(match.group(2))
                    else:
                        quantity = float(match.group(1))
                        unit_price = total_price / quantity if quantity > 0 else None
                    break
                except (ValueError, ZeroDivisionError):
                    continue
        
        return quantity, unit_price

    def _calculate_item_confidence(self, line: str, item_name: str, price: float, text_data: Dict[str, Any]) -> float:
        """Calculate confidence score for an extracted item."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on item name quality
        if len(item_name) >= 5:
            confidence += 0.1
        if re.search(r'[A-Z][a-z]+', item_name):  # Has proper capitalization
            confidence += 0.1
        
        # Boost confidence based on price reasonableness
        if 0.50 <= price <= 100.00:  # Reasonable price range
            confidence += 0.2
        elif 0.01 <= price <= 500.00:
            confidence += 0.1
        
        # Boost confidence if line has good OCR confidence
        if text_data.get('layout_data'):
            line_confidences = []
            layout_data = text_data['layout_data']
            for i, text in enumerate(layout_data['text']):
                if text.strip() and any(word in line for word in text.split()):
                    line_confidences.append(int(layout_data['conf'][i]))
            
            if line_confidences:
                avg_ocr_conf = np.mean(line_confidences) / 100.0
                confidence = (confidence + avg_ocr_conf) / 2
        
        # Use NLP models for additional validation
        if self.nlp:
            doc = self.nlp(item_name)
            if any(ent.label_ in ['PRODUCT', 'ORG'] for ent in doc.ents):
                confidence += 0.1
        
        return min(confidence, 1.0)

    def _post_process_items(self, items: List[ReceiptItem]) -> List[ReceiptItem]:
        """Post-process items to remove duplicates and improve accuracy."""
        if not items:
            return items
        
        # Sort by confidence
        items.sort(key=lambda x: x.confidence, reverse=True)
        
        # Remove duplicates based on similar names and prices
        filtered_items = []
        for item in items:
            is_duplicate = False
            for existing in filtered_items:
                # Check for similar names and same price
                name_similarity = self._calculate_name_similarity(item.name, existing.name)
                price_diff = abs(item.total_price - existing.total_price)
                
                if name_similarity > 0.8 and price_diff < 0.01:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_items.append(item)
        
        # Filter out items with very low confidence
        filtered_items = [item for item in filtered_items if item.confidence > 0.3]
        
        return filtered_items

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two item names."""
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()
        
        if name1 == name2:
            return 1.0
        
        # Simple Jaccard similarity
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    def extract_receipt_metadata(self, text_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract receipt metadata (merchant, date, totals)."""
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
        
        # Extract merchant (usually in first few lines)
        for line in lines[:5]:
            line_clean = re.sub(r'[^\w\s]', '', line).strip()
            if len(line_clean) > 3:
                for merchant in self.merchant_indicators:
                    if merchant.lower() in line_clean.lower():
                        metadata['merchant_name'] = line_clean.title()
                        break
                if metadata['merchant_name']:
                    break
        
        # If no known merchant found, use first substantial line
        if not metadata['merchant_name']:
            for line in lines[:3]:
                line_clean = re.sub(r'[^\w\s]', '', line).strip()
                if len(line_clean) > 5 and not re.match(r'^\d+', line_clean):
                    metadata['merchant_name'] = line_clean.title()
                    break
        
        # Extract totals from last few lines
        for line in reversed(lines[-10:]):
            line_lower = line.lower()
            prices = self._extract_prices_from_line(line)
            
            if prices:
                price = prices[-1]  # Take the last price on the line
                
                if 'total' in line_lower and 'sub' not in line_lower:
                    metadata['total'] = price
                elif 'subtotal' in line_lower or 'sub total' in line_lower:
                    metadata['subtotal'] = price
                elif 'tax' in line_lower:
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
                        # Try different date formats
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
        """Process a receipt image and return structured data."""
        self.logger.info(f"Processing receipt image: {image_path}")
        
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_path)
            
            # Extract text with layout
            text_data = self.extract_text_with_layout(processed_image)
            
            # Extract items and prices
            items = self.extract_items_and_prices(text_data)
            
            # Extract metadata
            metadata = self.extract_receipt_metadata(text_data)
            
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
            
            self.logger.info(f"Successfully processed receipt: {len(items)} items extracted")
            return receipt_data
            
        except Exception as e:
            self.logger.error(f"Error processing receipt: {str(e)}")
            raise