"""Tests for receipt processing functionality."""

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PYTHON.app import create_app
from PYTHON.models import db, User, Expense
from PYTHON.receipt_processor import ReceiptImageProcessor, ReceiptExpenseManager, ReceiptData, ReceiptItem
from PYTHON.exceptions import ValidationError
from config import config

class TestReceiptProcessor(unittest.TestCase):
    """Test receipt image processing functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('testpass')
        db.session.add(self.user)
        db.session.commit()
        
        # Create temporary directory for test images
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize processor
        self.processor = ReceiptImageProcessor()
        self.manager = ReceiptExpenseManager()
    
    def tearDown(self):
        """Clean up test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_receipt_image(self, filename='test_receipt.png'):
        """Create a synthetic receipt image for testing."""
        # Create a simple receipt-like image
        img = Image.new('RGB', (400, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font, fallback to basic if not available
        try:
            font = ImageFont.truetype("arial.ttf", 16)
            small_font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw receipt content
        y_pos = 20
        
        # Header
        draw.text((50, y_pos), "WALMART SUPERCENTER", fill='black', font=font)
        y_pos += 30
        draw.text((50, y_pos), "123 Main St, City, ST 12345", fill='black', font=small_font)
        y_pos += 20
        draw.text((50, y_pos), "Tel: (555) 123-4567", fill='black', font=small_font)
        y_pos += 40
        
        # Date and time
        draw.text((50, y_pos), "01/15/2024  14:30:25", fill='black', font=small_font)
        y_pos += 30
        
        # Items
        items = [
            ("BANANAS ORGANIC", "2.99"),
            ("MILK 2% GALLON", "3.49"),
            ("BREAD WHOLE WHEAT", "2.79"),
            ("CHICKEN BREAST", "8.99")
        ]
        
        for item_name, price in items:
            draw.text((50, y_pos), item_name, fill='black', font=small_font)
            draw.text((300, y_pos), f"${price}", fill='black', font=small_font)
            y_pos += 25
        
        y_pos += 20
        draw.line([(50, y_pos), (350, y_pos)], fill='black', width=1)
        y_pos += 10
        
        # Totals
        draw.text((50, y_pos), "SUBTOTAL", fill='black', font=small_font)
        draw.text((300, y_pos), "$18.26", fill='black', font=small_font)
        y_pos += 20
        
        draw.text((50, y_pos), "TAX", fill='black', font=small_font)
        draw.text((300, y_pos), "$1.46", fill='black', font=small_font)
        y_pos += 20
        
        draw.text((50, y_pos), "TOTAL", fill='black', font=font)
        draw.text((300, y_pos), "$19.72", fill='black', font=font)
        y_pos += 30
        
        # Receipt number
        draw.text((50, y_pos), "Receipt #: 1234567890", fill='black', font=small_font)
        
        # Save image
        image_path = os.path.join(self.temp_dir, filename)
        img.save(image_path)
        return image_path
    
    def test_processor_initialization(self):
        """Test processor initialization."""
        self.assertIsNotNone(self.processor)
        self.assertIsInstance(self.processor.patterns, dict)
        self.assertIn('price', self.processor.patterns)
        self.assertIn('total', self.processor.patterns)
    
    def test_image_preprocessing(self):
        """Test image preprocessing functionality."""
        image_path = self.create_test_receipt_image()
        
        # Test preprocessing
        processed_image = self.processor.preprocess_image(image_path)
        self.assertIsInstance(processed_image, np.ndarray)
        self.assertEqual(len(processed_image.shape), 2)  # Should be grayscale
    
    def test_invalid_image_path(self):
        """Test handling of invalid image paths."""
        with self.assertRaises(ValidationError):
            self.processor.preprocess_image("nonexistent_image.jpg")
    
    @patch('pytesseract.image_to_string')
    @patch('pytesseract.image_to_data')
    def test_text_extraction(self, mock_image_to_data, mock_image_to_string):
        """Test OCR text extraction."""
        # Mock OCR responses
        mock_image_to_string.return_value = """
        WALMART SUPERCENTER
        123 Main St, City, ST 12345
        01/15/2024  14:30:25
        BANANAS ORGANIC     $2.99
        MILK 2% GALLON      $3.49
        SUBTOTAL           $18.26
        TAX                 $1.46
        TOTAL              $19.72
        Receipt #: 1234567890
        """
        
        mock_image_to_data.return_value = {
            'conf': ['85', '90', '88', '92', '87', '89', '91', '86']
        }
        
        # Create test image
        image_path = self.create_test_receipt_image()
        processed_image = self.processor.preprocess_image(image_path)
        
        # Test text extraction
        text, confidence = self.processor.extract_text(processed_image)
        
        self.assertIsInstance(text, str)
        self.assertIsInstance(confidence, float)
        self.assertGreater(len(text), 0)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_receipt_data_parsing(self):
        """Test parsing of receipt text into structured data."""
        sample_text = """
        WALMART SUPERCENTER
        123 Main St, City, ST 12345
        01/15/2024  14:30:25
        BANANAS ORGANIC     $2.99
        MILK 2% GALLON      $3.49
        BREAD WHOLE WHEAT   $2.79
        CHICKEN BREAST      $8.99
        SUBTOTAL           $18.26
        TAX                 $1.46
        TOTAL              $19.72
        Receipt #: 1234567890
        """
        
        receipt_data = self.processor.parse_receipt_data(sample_text, 0.85)
        
        self.assertIsInstance(receipt_data, ReceiptData)
        self.assertIsNotNone(receipt_data.merchant_name)
        self.assertIsNotNone(receipt_data.total)
        self.assertIsNotNone(receipt_data.tax)
        self.assertIsNotNone(receipt_data.subtotal)
        self.assertIsNotNone(receipt_data.receipt_number)
        self.assertGreater(len(receipt_data.items), 0)
        
        # Check specific values
        self.assertEqual(float(receipt_data.total), 19.72)
        self.assertEqual(float(receipt_data.tax), 1.46)
        self.assertEqual(float(receipt_data.subtotal), 18.26)
    
    def test_merchant_name_extraction(self):
        """Test merchant name extraction."""
        lines = ["WALMART SUPERCENTER", "123 Main St", "Phone: 555-1234"]
        merchant = self.processor._extract_merchant_name(lines)
        self.assertEqual(merchant, "Walmart Supercenter")
    
    def test_price_pattern_matching(self):
        """Test price pattern matching."""
        test_cases = [
            ("$19.99", "19.99"),
            ("19.99", "19.99"),
            ("$5", "5"),
            ("Total: $123.45", "123.45")
        ]
        
        for text, expected in test_cases:
            matches = self.processor.patterns['price'].findall(text)
            self.assertIn(expected, matches)
    
    @patch('PYTHON.receipt_processor.ReceiptImageProcessor')
    def test_expense_manager_integration(self, mock_processor_class):
        """Test integration with expense management."""
        # Mock the processor
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        # Mock processed receipt data
        mock_receipt_data = ReceiptData(
            merchant_name="Test Store",
            total=25.99,
            tax=2.08,
            subtotal=23.91,
            items=[
                ReceiptItem(name="Test Item 1", total_price=15.99),
                ReceiptItem(name="Test Item 2", total_price=9.99)
            ],
            confidence_score=0.85
        )
        
        mock_processor.preprocess_image.return_value = np.zeros((100, 100))
        mock_processor.extract_text.return_value = ("mock text", 0.85)
        mock_processor.parse_receipt_data.return_value = mock_receipt_data
        
        # Create test image
        image_path = self.create_test_receipt_image()
        
        # Process receipt
        result = self.manager.process_receipt_image(image_path, self.user.id)
        
        # Verify results
        self.assertTrue(result['success'])
        self.assertEqual(result['expenses_created'], 2)  # Two items
        self.assertIn('receipt_data', result)
        self.assertIn('expenses', result)
        
        # Verify expenses were created in database
        expenses = Expense.query.filter_by(user_id=self.user.id).all()
        self.assertEqual(len(expenses), 2)
        
        for expense in expenses:
            self.assertEqual(expense.source, 'receipt_upload')
            self.assertIsNotNone(expense.metadata)
            self.assertEqual(expense.user_id, self.user.id)
    
    def test_invalid_user_id(self):
        """Test handling of invalid user ID."""
        image_path = self.create_test_receipt_image()
        
        with self.assertRaises(ValidationError):
            self.manager.process_receipt_image(image_path, 99999)  # Non-existent user
    
    def test_receipt_data_validation(self):
        """Test receipt data validation."""
        # Test with future date (should be corrected)
        from datetime import datetime, timedelta
        future_date = datetime.now() + timedelta(days=30)
        
        receipt_data = ReceiptData(
            merchant_name="Test Store",
            date=future_date,
            total=25.99
        )
        
        # This should log a warning and set date to None
        self.processor._validate_receipt_data(receipt_data)
        self.assertIsNone(receipt_data.date)

class TestReceiptDataClasses(unittest.TestCase):
    """Test receipt data classes."""
    
    def test_receipt_item_creation(self):
        """Test ReceiptItem creation."""
        item = ReceiptItem(
            name="Test Item",
            quantity=2,
            unit_price=5.99,
            total_price=11.98
        )
        
        self.assertEqual(item.name, "Test Item")
        self.assertEqual(item.quantity, 2)
        self.assertEqual(float(item.unit_price), 5.99)
        self.assertEqual(float(item.total_price), 11.98)
    
    def test_receipt_data_creation(self):
        """Test ReceiptData creation."""
        receipt = ReceiptData(
            merchant_name="Test Store",
            total=25.99,
            confidence_score=0.85
        )
        
        self.assertEqual(receipt.merchant_name, "Test Store")
        self.assertEqual(float(receipt.total), 25.99)
        self.assertEqual(receipt.confidence_score, 0.85)
        self.assertEqual(len(receipt.items), 0)  # Should initialize empty list

if __name__ == '__main__':
    unittest.main()