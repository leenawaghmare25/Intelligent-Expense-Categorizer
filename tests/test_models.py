"""Tests for database models."""

import unittest
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PYTHON.app import create_app
from PYTHON.models import db, User, Expense
from project_config import config

class TestModels(unittest.TestCase):
    """Test database models."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):
        """Clean up test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_user_creation(self):
        """Test user model creation."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass')
        
        db.session.add(user)
        db.session.commit()
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass'))
        self.assertFalse(user.check_password('wrongpass'))
    
    def test_expense_creation(self):
        """Test expense model creation."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        
        expense = Expense(
            description='Test expense',
            amount=25.50,
            predicted_category='Dining Out',
            confidence_score=0.85,
            user_id=user.id
        )
        
        db.session.add(expense)
        db.session.commit()
        
        self.assertEqual(expense.description, 'Test expense')
        self.assertEqual(expense.amount, 25.50)
        self.assertEqual(expense.predicted_category, 'Dining Out')
        self.assertEqual(expense.confidence_score, 0.85)
        self.assertEqual(expense.user_id, user.id)
    
    def test_user_expense_relationship(self):
        """Test user-expense relationship."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        
        expense1 = Expense(
            description='Expense 1',
            predicted_category='Transport',
            confidence_score=0.75,
            user_id=user.id
        )
        expense2 = Expense(
            description='Expense 2',
            predicted_category='Groceries',
            confidence_score=0.90,
            user_id=user.id
        )
        
        db.session.add_all([expense1, expense2])
        db.session.commit()
        
        self.assertEqual(len(user.expenses), 2)
        self.assertEqual(expense1.user, user)
        self.assertEqual(expense2.user, user)

if __name__ == '__main__':
    unittest.main()