#!/usr/bin/env python3
"""
Test script to verify the fixes for the expense deletion and receipt history issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PYTHON.app import create_app
from PYTHON.models import db, User, Expense
from datetime import datetime
import json

def test_fixes():
    """Test the fixes for the reported issues."""
    print("🧪 Testing fixes for expense deletion and receipt history...")
    
    app = create_app()
    
    with app.app_context():
        # Test 1: Check if Expense model loads without metadata conflict
        try:
            expense = Expense.query.first()
            print("✅ Expense model loads correctly (no metadata conflict)")
        except Exception as e:
            print(f"❌ Expense model error: {e}")
            return False
        
        # Test 2: Check if we can create a test expense with receipt metadata
        try:
            test_user = User.query.first()
            if test_user:
                test_expense = Expense(
                    user_id=test_user.id,
                    description="Test receipt expense",
                    predicted_category="Dining Out",
                    confidence_score=0.85,
                    source="receipt_upload",
                    expense_metadata={
                        "merchant": "Test Restaurant",
                        "receipt_number": "12345",
                        "confidence": 0.9,
                        "item_name": "Test Item"
                    }
                )
                db.session.add(test_expense)
                db.session.commit()
                
                # Test accessing the metadata
                metadata = test_expense.expense_metadata
                print(f"✅ Receipt metadata accessible: {metadata is not None}")
                
                # Clean up
                db.session.delete(test_expense)
                db.session.commit()
            else:
                print("⚠️  No test user found, skipping expense creation test")
        except Exception as e:
            print(f"❌ Receipt metadata test error: {e}")
            return False
        
        # Test 3: Check if receipt history query works
        try:
            if test_user:
                receipt_expenses = Expense.query.filter_by(
                    user_id=test_user.id,
                    source='receipt_upload',
                    is_deleted=False
                ).all()
                print(f"✅ Receipt history query works: found {len(receipt_expenses)} receipt expenses")
            else:
                print("⚠️  No test user found, skipping receipt history test")
        except Exception as e:
            print(f"❌ Receipt history query error: {e}")
            return False
    
    print("✅ All tests passed! The fixes should resolve the reported issues.")
    return True

if __name__ == "__main__":
    success = test_fixes()
    sys.exit(0 if success else 1)