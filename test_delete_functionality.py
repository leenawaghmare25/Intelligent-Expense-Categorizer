#!/usr/bin/env python3
"""
Test script for delete functionality (individual and bulk delete)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PYTHON.app import create_app
from PYTHON.models import db, User, Expense
from flask_login import login_user
import tempfile

def test_delete_functionality():
    """Test both individual and bulk delete functionality."""
    
    # Create test app
    app = create_app('testing')
    
    with app.app_context():
        # Create test user
        test_user = User(username='testuser', email='test@example.com')
        test_user.set_password('testpass')
        db.session.add(test_user)
        db.session.commit()
        
        # Create test expenses
        test_expenses = []
        for i in range(5):
            expense = Expense(
                user_id=test_user.id,
                description=f'Test Expense {i+1}',
                amount=10.00 + i,
                predicted_category='Test Category',
                confidence_score=0.8
            )
            test_expenses.append(expense)
            db.session.add(expense)
        
        db.session.commit()
        
        print(f"✅ Created {len(test_expenses)} test expenses")
        
        # Test individual delete
        with app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
            
            # Test individual delete
            expense_to_delete = test_expenses[0]
            response = client.post(f'/expense/{expense_to_delete.id}/delete', 
                                 data={'csrf_token': 'test'})
            
            # Check if expense was deleted
            deleted_expense = Expense.query.get(expense_to_delete.id)
            if deleted_expense is None:
                print("✅ Individual delete functionality works")
            else:
                print("❌ Individual delete failed")
            
            # Test bulk delete API
            remaining_expenses = Expense.query.filter_by(user_id=test_user.id).all()
            expense_ids = [exp.id for exp in remaining_expenses[:2]]
            
            response = client.post('/expenses/bulk-delete',
                                 json={'expense_ids': expense_ids},
                                 headers={'X-CSRFToken': 'test'})
            
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success') and data.get('deleted_count') == 2:
                    print("✅ Bulk delete API functionality works")
                else:
                    print(f"❌ Bulk delete API failed: {data}")
            else:
                print(f"❌ Bulk delete API failed with status {response.status_code}")
        
        # Verify final state
        remaining_count = Expense.query.filter_by(user_id=test_user.id).count()
        print(f"✅ Final expense count: {remaining_count} (expected: 2)")
        
        print("\n🎉 Delete functionality test completed!")

if __name__ == '__main__':
    test_delete_functionality()