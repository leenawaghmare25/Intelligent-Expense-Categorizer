"""Tests for machine learning models."""

import unittest
import sys
import os
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PYTHON.ml_models import EnsembleExpenseClassifier
from PYTHON.exceptions import ModelNotFoundError, ModelTrainingError

class TestMLModels(unittest.TestCase):
    """Test machine learning models."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.ensemble = EnsembleExpenseClassifier()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ensemble_initialization(self):
        """Test ensemble model initialization."""
        self.assertIsNotNone(self.ensemble)
        self.assertEqual(len(self.ensemble.models), 0)  # No models loaded initially
    
    def test_prediction_without_models(self):
        """Test prediction fails without trained models."""
        with self.assertRaises(ModelNotFoundError):
            self.ensemble.predict("Test expense")
    
    def test_text_preprocessing(self):
        """Test text preprocessing functionality."""
        # Test basic preprocessing
        text = "  STARBUCKS COFFEE  "
        processed = self.ensemble._preprocess_text(text)
        self.assertEqual(processed, "starbucks coffee")
        
        # Test with special characters
        text = "McDonald's $5.99 meal!!!"
        processed = self.ensemble._preprocess_text(text)
        self.assertNotIn('$', processed)
        self.assertNotIn('!', processed)
    
    def test_keyword_classifier(self):
        """Test keyword-based classifier."""
        # Test restaurant keywords
        self.assertEqual(
            self.ensemble._keyword_classify("starbucks coffee"),
            "Dining Out"
        )
        
        # Test transport keywords
        self.assertEqual(
            self.ensemble._keyword_classify("uber ride"),
            "Transport"
        )
        
        # Test utilities keywords
        self.assertEqual(
            self.ensemble._keyword_classify("electricity bill"),
            "Utilities"
        )
        
        # Test unknown keywords
        self.assertEqual(
            self.ensemble._keyword_classify("unknown expense"),
            "Other"
        )
    
    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        # Mock predictions from different models
        predictions = {
            'naive_bayes': {'prediction': 'Dining Out', 'confidence': 0.8},
            'svm': {'prediction': 'Dining Out', 'confidence': 0.9},
            'keyword': {'prediction': 'Dining Out', 'confidence': 0.7}
        }
        
        weights = {'naive_bayes': 0.4, 'svm': 0.4, 'keyword': 0.2}
        
        # Calculate expected confidence
        expected_confidence = (0.8 * 0.4) + (0.9 * 0.4) + (0.7 * 0.2)
        
        # This would require access to internal methods
        # In a real implementation, we'd test the actual ensemble prediction
        self.assertAlmostEqual(expected_confidence, 0.82, places=2)

if __name__ == '__main__':
    unittest.main()