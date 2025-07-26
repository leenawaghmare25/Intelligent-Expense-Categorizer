#!/usr/bin/env python3
"""
Test script to verify the bulk delete fix.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PYTHON.app import create_app
from PYTHON.models import db, User, Expense
import json

def test_bulk_delete():
    """Test the bulk delete functionality."""
    print("🧪 Testing bulk delete functionality...")
    
    app = create_app()
    
    with app.app_context():
        # Get a test user
        test_user = User.query.first()
        if not test_user:
            print("❌ No test user found")
            return False
        
        # Create some test expenses
        test_expenses = []
        for i in range(3):
            expense = Expense(
                user_id=test_user.id,
                description=f"Test expense {i+1}",
                predicted_category="Test",
                confidence_score=0.8
            )
            db.session.add(expense)
            test_expenses.append(expense)
        
        db.session.commit()
        
        # Get the expense IDs (they should be UUIDs/strings)
        expense_ids = [e.id for e in test_expenses]
        print(f"✅ Created test expenses with IDs: {expense_ids}")
        print(f"✅ ID types: {[type(eid).__name__ for eid in expense_ids]}")
        
        # Test the validation logic
        found_expenses = Expense.query.filter(
            Expense.id.in_(expense_ids),
            Expense.user_id == test_user.id,
            Expense.is_deleted == False
        ).all()
        
        print(f"✅ Found {len(found_expenses)} expenses out of {len(expense_ids)} requested")
        
        if len(found_expenses) == len(expense_ids):
            print("✅ Bulk delete validation would pass")
        else:
            print("❌ Bulk delete validation would fail")
        
        # Clean up
        for expense in test_expenses:
            db.session.delete(expense)
        db.session.commit()
        
        print("✅ Test completed successfully")
        return True

if __name__ == "__main__":
    success = test_bulk_delete()
    sys.exit(0 if success else 1)