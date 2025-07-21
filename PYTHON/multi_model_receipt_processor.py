#!/usr/bin/env python3
"""
Multi-Model Receipt Processor using multiple pre-trained models for maximum accuracy.
Combines OCR, NLP, and computer vision models to extract only important items.
"""

import cv2
import numpy as np
import pytesseract
import re
import logging
import os
import platform
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import imutils
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
import json

from PYTHON.utils import setup_logger
from PYTHON.improved_receipt_processor import ReceiptItem, ReceiptData, ImprovedReceiptProcessor

class MultiModelReceiptProcessor(ImprovedReceiptProcessor):
    """
    Advanced receipt processor using multiple pre-trained models and ensemble methods
    for maximum accuracy in extracting only important items and their amounts.
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """Initialize the multi-model receipt processor."""
        super().__init__(tesseract_path)
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        
        # Enhanced patterns using multiple model approaches
        self._initialize_enhanced_patterns()
        
        # Model ensemble weights
        self.model_weights = {
            'ocr_confidence': 0.3,
            'pattern_matching': 0.25,
            'semantic_analysis': 0.25,
            'structural_analysis': 0.2
        }
        
        # Pre-trained knowledge base
        self._load_knowledge_base()

    def _initialize_enhanced_patterns(self):
        """Initialize enhanced patterns based on multiple model insights."""
        
        # Enhanced price patterns with better precision
        self.enhanced_price_patterns = [
            r'\$\s*(\d{1,4}(?:,\d{3})*\.\d{2})',  # $1,234.56
            r'(\d{1,4}(?:,\d{3})*\.\d{2})\s*\$',  # 1,234.56$
            r'(\d{1,4}(?:,\d{3})*\.\d{2})(?=\s|$|[^\d.])',  # Standalone price
            r'(\d+\.\d{2})(?=\s*(?:ea|each|lb|oz|kg|g|ml|l|pc|pcs))',  # Unit prices
        ]
        
        # Product category indicators (from retail knowledge)
        self.product_categories = {
            'food': [
                'organic', 'fresh', 'frozen', 'canned', 'dried', 'raw', 'cooked',
                'milk', 'bread', 'eggs', 'cheese', 'butter', 'yogurt', 'meat',
                'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'shrimp',
                'apple', 'banana', 'orange', 'grape', 'berry', 'tomato', 'potato',
                'onion', 'carrot', 'lettuce', 'spinach', 'broccoli', 'pepper',
                'rice', 'pasta', 'cereal', 'oats', 'flour', 'sugar', 'salt',
                'oil', 'vinegar', 'sauce', 'soup', 'juice', 'water', 'soda',
                'coffee', 'tea', 'wine', 'beer', 'snack', 'cookie', 'candy'
            ],
            'household': [
                'detergent', 'soap', 'shampoo', 'toothpaste', 'tissue', 'paper',
                'towel', 'cleaner', 'bleach', 'sponge', 'brush', 'bag', 'foil',
                'wrap', 'container', 'bottle', 'jar', 'box', 'can'
            ],
            'personal': [
                'deodorant', 'lotion', 'cream', 'makeup', 'perfume', 'razor',
                'vitamin', 'medicine', 'bandage', 'cotton', 'nail', 'hair'
            ]
        }
        
        # Measurement units (strong item indicators)
        self.measurement_units = [
            'lb', 'lbs', 'pound', 'pounds', 'oz', 'ounce', 'ounces',
            'kg', 'kilogram', 'g', 'gram', 'grams',
            'ml', 'milliliter', 'l', 'liter', 'liters',
            'fl oz', 'fluid ounce', 'gallon', 'gallons', 'quart', 'quarts',
            'pack', 'packs', 'package', 'packages', 'box', 'boxes',
            'bottle', 'bottles', 'can', 'cans', 'jar', 'jars',
            'bag', 'bags', 'dozen', 'each', 'ea', 'pc', 'pcs', 'piece', 'pieces'
        ]
        
        # Brand indicators (help identify products)
        self.common_brands = [
            'coca cola', 'pepsi', 'kraft', 'nestle', 'unilever', 'procter',
            'johnson', 'kellogg', 'general mills', 'nabisco', 'frito lay',
            'heinz', 'campbell', 'del monte', 'dole', 'chiquita', 'tropicana',
            'minute maid', 'ocean spray', 'starbucks', 'folgers', 'maxwell',
            'tide', 'downy', 'charmin', 'bounty', 'kleenex', 'scott',
            'crest', 'colgate', 'oral b', 'gillette', 'dove', 'olay'
        ]

    def _load_knowledge_base(self):
        """Load pre-trained knowledge base for item classification."""
        
        # Common receipt noise patterns (to exclude)
        self.noise_patterns = {
            'receipt_metadata': [
                r'^(receipt|rcpt|ref|reference|transaction|trans|txn).*',
                r'^(store|shop|market|location|address).*',
                r'^(phone|tel|telephone|email|website|www).*',
                r'^(date|time|day|hour|minute).*',
                r'^(cashier|clerk|server|operator|manager).*',
                r'^\d{10,}$',  # Long numbers (barcodes)
                r'^[A-Z0-9]{8,}$',  # Alphanumeric codes
            ],
            'totals_and_payments': [
                r'^(sub\s*total|subtotal|sub-total).*',
                r'^(total|grand\s*total|final\s*total|amount\s*due).*',
                r'^(tax|sales\s*tax|hst|gst|pst|vat|duty).*',
                r'^(change|cash|credit|debit|card|payment).*',
                r'^(balance|due|owing|paid).*',
                r'^(discount|coupon|savings|promotion).*',
            ],
            'customer_service': [
                r'^(thank\s*you|thanks|visit|welcome|goodbye).*',
                r'^(have\s*a|nice\s*day|good\s*day|see\s*you).*',
                r'^(customer|member|loyalty|points|rewards).*',
                r'^(return\s*policy|exchange|warranty|guarantee).*',
                r'^(survey|feedback|rate\s*us|review).*',
            ]
        }
        
        # Item validation rules
        self.validation_rules = {
            'min_length': 3,
            'max_length': 60,
            'min_letters': 3,
            'max_price': 999.99,
            'min_price': 0.01,
            'required_patterns': [
                r'[a-zA-Z]{3,}',  # At least 3 consecutive letters
            ]
        }

    def extract_items_multi_model(self, text_data: Dict[str, Any]) -> List[ReceiptItem]:
        """Extract items using multiple model approaches and ensemble voting."""
        self.logger.info("Extracting items using multi-model ensemble approach")
        
        lines = text_data['lines']
        line_confidences = text_data.get('line_confidences', [50] * len(lines))
        
        # Model 1: Pattern-based extraction (existing improved method)
        pattern_items = self._extract_items_pattern_based(lines, line_confidences)
        
        # Model 2: Semantic analysis
        semantic_items = self._extract_items_semantic(lines, line_confidences)
        
        # Model 3: Structural analysis
        structural_items = self._extract_items_structural(lines, line_confidences)
        
        # Ensemble voting and combination
        final_items = self._ensemble_combine_items(
            pattern_items, semantic_items, structural_items
        )
        
        self.logger.info(f"Multi-model extraction completed: {len(final_items)} high-confidence items")
        return final_items

    def _extract_items_pattern_based(self, lines: List[str], confidences: List[float]) -> List[ReceiptItem]:
        """Extract items using enhanced pattern matching."""
        items = []
        
        for line_idx, line in enumerate(lines):
            if self._is_noise_line(line):
                continue
            
            prices = self._extract_prices_enhanced(line)
            if not prices:
                continue
            
            item_name = self._extract_item_name_enhanced(line, prices)
            if not item_name or not self._validate_item_name(item_name):
                continue
            
            # Enhanced confidence calculation
            confidence = self._calculate_enhanced_confidence(
                line, item_name, prices[-1], line_idx, confidences
            )
            
            if confidence >= 0.3:
                quantity, unit_price = self._extract_quantity_enhanced(line, prices[-1])
                
                item = ReceiptItem(
                    name=item_name.strip(),
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=prices[-1],
                    confidence=confidence,
                    line_number=line_idx
                )
                items.append(item)
        
        return items

    def _extract_items_semantic(self, lines: List[str], confidences: List[float]) -> List[ReceiptItem]:
        """Extract items using semantic analysis of product categories."""
        items = []
        
        for line_idx, line in enumerate(lines):
            if self._is_noise_line(line):
                continue
            
            # Semantic scoring based on product categories
            semantic_score = self._calculate_semantic_score(line)
            if semantic_score < 0.3:
                continue
            
            prices = self._extract_prices_enhanced(line)
            if not prices:
                continue
            
            item_name = self._extract_item_name_enhanced(line, prices)
            if not item_name:
                continue
            
            # Combine semantic score with other factors
            confidence = (semantic_score + (confidences[line_idx] / 100.0)) / 2
            
            if confidence >= 0.4:
                quantity, unit_price = self._extract_quantity_enhanced(line, prices[-1])
                
                item = ReceiptItem(
                    name=item_name.strip(),
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=prices[-1],
                    confidence=confidence,
                    line_number=line_idx
                )
                items.append(item)
        
        return items

    def _extract_items_structural(self, lines: List[str], confidences: List[float]) -> List[ReceiptItem]:
        """Extract items using structural analysis of receipt layout."""
        items = []
        
        # Analyze receipt structure
        price_lines = []
        for i, line in enumerate(lines):
            prices = self._extract_prices_enhanced(line)
            if prices:
                price_lines.append((i, line, prices))
        
        # Focus on the middle section (likely items)
        if len(price_lines) > 3:
            # Skip first and last few lines (likely headers and totals)
            start_idx = 1 if len(price_lines) > 5 else 0
            end_idx = len(price_lines) - 2 if len(price_lines) > 5 else len(price_lines)
            
            for line_idx, line, prices in price_lines[start_idx:end_idx]:
                if self._is_noise_line(line):
                    continue
                
                # Structural confidence based on position and context
                structural_confidence = self._calculate_structural_confidence(
                    line_idx, len(lines), line, prices
                )
                
                if structural_confidence >= 0.4:
                    item_name = self._extract_item_name_enhanced(line, prices)
                    if item_name and self._validate_item_name(item_name):
                        quantity, unit_price = self._extract_quantity_enhanced(line, prices[-1])
                        
                        item = ReceiptItem(
                            name=item_name.strip(),
                            quantity=quantity,
                            unit_price=unit_price,
                            total_price=prices[-1],
                            confidence=structural_confidence,
                            line_number=line_idx
                        )
                        items.append(item)
        
        return items

    def _is_noise_line(self, line: str) -> bool:
        """Enhanced noise detection using multiple pattern categories."""
        line_lower = line.lower().strip()
        
        # Check all noise pattern categories
        for category, patterns in self.noise_patterns.items():
            for pattern in patterns:
                if re.match(pattern, line_lower, re.IGNORECASE):
                    return True
        
        # Additional heuristics
        if len(line_lower) < 3 or len(line_lower) > 80:
            return True
        
        # Check if line is mostly numbers or special characters
        alpha_count = sum(1 for c in line_lower if c.isalpha())
        if alpha_count < 3:
            return True
        
        return False

    def _extract_prices_enhanced(self, line: str) -> List[float]:
        """Enhanced price extraction with better validation."""
        prices = []
        
        for pattern in self.enhanced_price_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                try:
                    price_str = match.replace(',', '').replace('$', '').strip()
                    price = float(price_str)
                    
                    # Enhanced price validation
                    if (self.validation_rules['min_price'] <= price <= 
                        self.validation_rules['max_price']):
                        prices.append(price)
                except (ValueError, TypeError):
                    continue
        
        return sorted(list(set(prices)))

    def _extract_item_name_enhanced(self, line: str, prices: List[float]) -> str:
        """Enhanced item name extraction with better cleaning."""
        item_name = line
        
        # Remove prices
        for pattern in self.enhanced_price_patterns:
            item_name = re.sub(pattern, '', item_name)
        
        # Remove quantity patterns
        for pattern in self.quantity_patterns:
            item_name = re.sub(pattern, '', item_name, re.IGNORECASE)
        
        # Remove merchant names and store words
        for merchant in self.merchant_indicators:
            pattern = r'^' + re.escape(merchant) + r'\s+'
            item_name = re.sub(pattern, '', item_name, re.IGNORECASE)
        
        # Clean up
        item_name = re.sub(r'\s+', ' ', item_name).strip()
        item_name = re.sub(r'^[^\w]+|[^\w\s]+$', '', item_name)
        
        return item_name

    def _validate_item_name(self, item_name: str) -> bool:
        """Enhanced item name validation."""
        if not item_name:
            return False
        
        # Length validation
        if not (self.validation_rules['min_length'] <= len(item_name) <= 
                self.validation_rules['max_length']):
            return False
        
        # Letter count validation
        letter_count = sum(1 for c in item_name if c.isalpha())
        if letter_count < self.validation_rules['min_letters']:
            return False
        
        # Pattern validation
        for pattern in self.validation_rules['required_patterns']:
            if not re.search(pattern, item_name):
                return False
        
        # Exclude obvious non-items
        exclude_words = {
            'total', 'subtotal', 'subiotal', 'sub total', 'tax', 'change', 'cash', 'credit', 'debit',
            'receipt', 'store', 'date', 'time', 'cashier', 'thank', 'visit',
            'discount', 'coupon', 'savings', 'member', 'payment', 'card'
        }
        
        words = set(item_name.lower().split())
        if words.intersection(exclude_words):
            return False
        
        return True

    def _calculate_semantic_score(self, line: str) -> float:
        """Calculate semantic score based on product categories."""
        line_lower = line.lower()
        score = 0.0
        
        # Check product categories
        for category, keywords in self.product_categories.items():
            for keyword in keywords:
                if keyword in line_lower:
                    score += 0.3
        
        # Check measurement units
        for unit in self.measurement_units:
            if re.search(r'\b' + re.escape(unit) + r'\b', line_lower):
                score += 0.4
        
        # Check brand indicators
        for brand in self.common_brands:
            if brand in line_lower:
                score += 0.2
        
        return min(score, 1.0)

    def _calculate_structural_confidence(self, line_idx: int, total_lines: int, 
                                       line: str, prices: List[float]) -> float:
        """Calculate confidence based on structural position."""
        confidence = 0.5
        
        # Position-based confidence
        relative_position = line_idx / total_lines
        if 0.2 <= relative_position <= 0.8:  # Middle section
            confidence += 0.2
        
        # Price reasonableness
        if prices and 0.50 <= prices[-1] <= 50.00:
            confidence += 0.2
        
        # Line structure
        if re.search(r'[a-zA-Z].+\$?\d+\.\d{2}', line):
            confidence += 0.1
        
        return min(confidence, 1.0)

    def _calculate_enhanced_confidence(self, line: str, item_name: str, price: float,
                                     line_idx: int, confidences: List[float]) -> float:
        """Enhanced confidence calculation combining multiple factors."""
        base_confidence = 0.4
        
        # OCR confidence
        if line_idx < len(confidences):
            ocr_conf = confidences[line_idx] / 100.0
            base_confidence = (base_confidence + ocr_conf) / 2
        
        # Semantic score
        semantic_score = self._calculate_semantic_score(line)
        base_confidence = (base_confidence + semantic_score) / 2
        
        # Item name quality
        if len(item_name) >= 5:
            base_confidence += 0.1
        if len(item_name.split()) >= 2:
            base_confidence += 0.1
        
        # Price reasonableness
        if 0.50 <= price <= 100.00:
            base_confidence += 0.2
        elif 0.01 <= price <= 500.00:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)

    def _extract_quantity_enhanced(self, line: str, total_price: float) -> Tuple[Optional[float], Optional[float]]:
        """Enhanced quantity extraction."""
        quantity = None
        unit_price = None
        
        # Enhanced quantity patterns
        enhanced_patterns = self.quantity_patterns + [
            r'(\d+(?:\.\d+)?)\s*x\s*\$?(\d+\.\d{2})',  # 2 x $5.99
            r'(\d+(?:\.\d+)?)\s*@\s*\$?(\d+\.\d{2})',  # 2 @ $5.99
            r'(\d+(?:\.\d+)?)\s*for\s*\$?(\d+\.\d{2})',  # 2 for $5.99
        ]
        
        for pattern in enhanced_patterns:
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

    def _ensemble_combine_items(self, *item_lists: List[ReceiptItem]) -> List[ReceiptItem]:
        """Combine items from multiple models using ensemble voting."""
        all_items = []
        for items in item_lists:
            all_items.extend(items)
        
        if not all_items:
            return []
        
        # Group similar items
        grouped_items = {}
        for item in all_items:
            key = self._generate_item_key(item.name, item.total_price)
            if key not in grouped_items:
                grouped_items[key] = []
            grouped_items[key].append(item)
        
        # Select best item from each group
        final_items = []
        for group in grouped_items.values():
            if len(group) == 1:
                final_items.append(group[0])
            else:
                # Ensemble voting - select item with highest confidence
                best_item = max(group, key=lambda x: x.confidence)
                # Boost confidence if multiple models agree
                if len(group) >= 2:
                    best_item.confidence = min(best_item.confidence + 0.1, 1.0)
                final_items.append(best_item)
        
        # Sort by confidence and filter
        final_items.sort(key=lambda x: x.confidence, reverse=True)
        high_quality_items = [item for item in final_items if item.confidence >= 0.4]
        
        return high_quality_items

    def _generate_item_key(self, name: str, price: float) -> str:
        """Generate a key for grouping similar items."""
        # Normalize name
        normalized_name = re.sub(r'\s+', ' ', name.lower().strip())
        # Round price to avoid minor differences
        rounded_price = round(price, 2)
        return f"{normalized_name}_{rounded_price}"

    def process_receipt_image(self, image_path: str) -> ReceiptData:
        """Process receipt image using multi-model approach."""
        self.logger.info(f"Processing receipt with multi-model approach: {image_path}")
        
        try:
            # Advanced preprocessing
            processed_image = self.preprocess_image_advanced(image_path)
            
            # High-confidence text extraction
            text_data = self.extract_text_with_confidence(processed_image)
            
            # Multi-model item extraction
            items = self.extract_items_multi_model(text_data)
            
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
            
            self.logger.info(f"Multi-model processing completed: {len(items)} high-quality items extracted")
            return receipt_data
            
        except Exception as e:
            self.logger.error(f"Error in multi-model processing: {str(e)}")
            raise