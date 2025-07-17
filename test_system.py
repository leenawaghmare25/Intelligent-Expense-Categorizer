#!/usr/bin/env python3
"""
Test script to verify the expense categorization system is working correctly.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from PYTHON.app import create_app
        from PYTHON.models import db, User, Expense
        from PYTHON.ml_models import EnsembleExpenseClassifier
        from config import Config
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

def test_model_loading():
    """Test that the ML models can be loaded."""
    print("Testing model loading...")
    try:
        from PYTHON.ml_models import EnsembleExpenseClassifier
        
        ensemble = EnsembleExpenseClassifier()
        if ensemble.load_models():
            print("✅ Models loaded successfully")
            return True
        else:
            print("❌ Failed to load models")
            return False
    except Exception as e:
        print(f"❌ Model loading error: {str(e)}")
        return False

def test_predictions():
    """Test that predictions work correctly."""
    print("Testing predictions...")
    try:
        from PYTHON.ml_models import EnsembleExpenseClassifier
        
        ensemble = EnsembleExpenseClassifier()
        if not ensemble.load_models():
            print("❌ Cannot test predictions - models not loaded")
            return False
        
        # Test predictions
        test_descriptions = [
            "Starbucks Coffee",
            "Uber ride to work",
            "Electricity bill payment",
            "Walmart groceries",
            "Netflix subscription"
        ]
        
        for desc in test_descriptions:
            detailed = ensemble.get_detailed_prediction(desc)
            print(f"  '{desc}' -> {detailed['ensemble_prediction']} "
                  f"(confidence: {detailed['ensemble_confidence']:.2f})")
        
        print("✅ Predictions working correctly")
        return True
    except Exception as e:
        print(f"❌ Prediction error: {str(e)}")
        return False

def test_database():
    """Test database connectivity."""
    print("Testing database...")
    try:
        from PYTHON.app import create_app
        from PYTHON.models import db, User
        
        app = create_app()
        with app.app_context():
            # Test database connection
            db.session.execute('SELECT 1')
            
            # Test user query
            user_count = User.query.count()
            print(f"  Database connected, {user_count} users found")
        
        print("✅ Database working correctly")
        return True
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running system tests...\n")
    
    tests = [
        test_imports,
        test_database,
        test_model_loading,
        test_predictions
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("="*50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run: python PYTHON/app.py")
        print("2. Open: http://localhost:5000")
        print("3. Login with admin/admin123")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Run: python init_app.py")
        print("2. Check logs for detailed error information")
        sys.exit(1)

if __name__ == "__main__":
    main()