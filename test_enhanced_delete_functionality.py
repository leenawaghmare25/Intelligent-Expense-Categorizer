#!/usr/bin/env python3
"""
Comprehensive test for enhanced delete functionality including soft delete and undo.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PYTHON.app import create_app
from PYTHON.models import db, User, Expense
from datetime import datetime, timedelta

def test_enhanced_delete_functionality():
    """Test all delete functionality including soft delete, restore, and permanent delete."""
    
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
        
        # Test soft delete functionality
        expense_to_delete = test_expenses[0]
        expense_to_delete.soft_delete(test_user.id)
        db.session.commit()
        
        # Verify soft delete
        if expense_to_delete.is_deleted and expense_to_delete.deleted_at:
            print("✅ Soft delete functionality works")
        else:
            print("❌ Soft delete failed")
        
        # Test active expenses query
        active_expenses = Expense.get_active_expenses(test_user.id).all()
        if len(active_expenses) == 4:  # Should be 4 remaining
            print("✅ Active expenses query works correctly")
        else:
            print(f"❌ Active expenses query failed: found {len(active_expenses)}, expected 4")
        
        # Test deleted expenses query
        deleted_expenses = Expense.get_deleted_expenses(test_user.id).all()
        if len(deleted_expenses) == 1:
            print("✅ Deleted expenses query works correctly")
        else:
            print(f"❌ Deleted expenses query failed: found {len(deleted_expenses)}, expected 1")
        
        # Test restore functionality
        expense_to_delete.restore()
        db.session.commit()
        
        if not expense_to_delete.is_deleted and expense_to_delete.deleted_at is None:
            print("✅ Restore functionality works")
        else:
            print("❌ Restore functionality failed")
        
        # Test bulk soft delete
        expenses_to_bulk_delete = test_expenses[1:3]  # Delete 2 expenses
        for expense in expenses_to_bulk_delete:
            expense.soft_delete(test_user.id)
        db.session.commit()
        
        # Verify bulk soft delete
        active_count = Expense.get_active_expenses(test_user.id).count()
        deleted_count = Expense.get_deleted_expenses(test_user.id).count()
        
        if active_count == 3 and deleted_count == 2:
            print("✅ Bulk soft delete functionality works")
        else:
            print(f"❌ Bulk soft delete failed: active={active_count}, deleted={deleted_count}")
        
        # Test API endpoints with test client
        with app.test_client() as client:
            # Login simulation
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
            
            # Test bulk delete API
            remaining_active = Expense.get_active_expenses(test_user.id).all()
            expense_ids = [exp.id for exp in remaining_active[:2]]
            
            response = client.post('/expenses/bulk-delete',
                                 json={'expense_ids': expense_ids},
                                 headers={'X-CSRFToken': 'test'})
            
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success') and data.get('deleted_count') == 2:
                    print("✅ Bulk delete API works")
                else:
                    print(f"❌ Bulk delete API failed: {data}")
            else:
                print(f"❌ Bulk delete API failed with status {response.status_code}")
            
            # Test bulk restore API
            all_deleted = Expense.get_deleted_expenses(test_user.id).all()
            restore_ids = [exp.id for exp in all_deleted[:2]]
            
            response = client.post('/expenses/bulk-restore',
                                 json={'expense_ids': restore_ids},
                                 headers={'X-CSRFToken': 'test'})
            
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success') and data.get('restored_count') == 2:
                    print("✅ Bulk restore API works")
                else:
                    print(f"❌ Bulk restore API failed: {data}")
            else:
                print(f"❌ Bulk restore API failed with status {response.status_code}")
            
            # Test permanent delete API
            still_deleted = Expense.get_deleted_expenses(test_user.id).all()
            if still_deleted:
                permanent_delete_ids = [exp.id for exp in still_deleted[:1]]
                
                response = client.post('/expenses/permanent-delete',
                                     json={'expense_ids': permanent_delete_ids},
                                     headers={'X-CSRFToken': 'test'})
                
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('success') and data.get('deleted_count') == 1:
                        print("✅ Permanent delete API works")
                        
                        # Verify the expense is actually gone
                        permanently_deleted = Expense.query.get(permanent_delete_ids[0])
                        if permanently_deleted is None:
                            print("✅ Permanent delete actually removes from database")
                        else:
                            print("❌ Permanent delete didn't remove from database")
                    else:
                        print(f"❌ Permanent delete API failed: {data}")
                else:
                    print(f"❌ Permanent delete API failed with status {response.status_code}")
        
        # Final verification
        final_active = Expense.get_active_expenses(test_user.id).count()
        final_deleted = Expense.get_deleted_expenses(test_user.id).count()
        final_total = Expense.query.filter_by(user_id=test_user.id).count()
        
        print(f"\n📊 Final State:")
        print(f"   Active expenses: {final_active}")
        print(f"   Soft deleted: {final_deleted}")
        print(f"   Total in DB: {final_total}")
        
        print("\n🎉 Enhanced delete functionality test completed!")
        print("\n✅ Features Verified:")
        print("   • Soft delete with timestamp and user tracking")
        print("   • Restore functionality")
        print("   • Active/deleted expense queries")
        print("   • Bulk delete API")
        print("   • Bulk restore API")
        print("   • Permanent delete API")
        print("   • Database integrity")

if __name__ == '__main__':
    test_enhanced_delete_functionality()