"""Database models for the expense tracker application."""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship with expenses
    expenses = db.relationship('Expense', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_expense_stats(self):
        """Get user's expense statistics."""
        total_expenses = self.expenses.count()
        categories = db.session.query(
            Expense.predicted_category,
            db.func.count(Expense.id).label('count'),
            db.func.sum(Expense.amount).label('total')
        ).filter_by(user_id=self.id).group_by(Expense.predicted_category).all()
        
        return {
            'total_expenses': total_expenses,
            'categories': [
                {
                    'category': cat.predicted_category,
                    'count': cat.count,
                    'total': float(cat.total) if cat.total else 0.0
                }
                for cat in categories
            ]
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class Expense(db.Model):
    """Expense model for tracking user expenses."""
    __tablename__ = 'expenses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=True)
    predicted_category = db.Column(db.String(100), nullable=False, index=True)
    confidence_score = db.Column(db.Float, nullable=False)
    model_predictions = db.Column(db.JSON)  # Store individual model predictions
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User feedback
    user_feedback = db.Column(db.String(100), nullable=True)  # User can correct the category
    is_correct = db.Column(db.Boolean, nullable=True)  # User can mark if prediction was correct
    
    # Receipt processing fields
    source = db.Column(db.String(50), nullable=True, default='manual')  # 'manual', 'receipt_upload', 'api'
    expense_metadata = db.Column(db.JSON, nullable=True)  # Store receipt data, OCR confidence, etc.
    date = db.Column(db.DateTime, nullable=True)  # Expense date (can be different from created_at)
    
    def to_dict(self):
        """Convert expense to dictionary."""
        return {
            'id': self.id,
            'description': self.description,
            'amount': float(self.amount) if self.amount else None,
            'predicted_category': self.predicted_category,
            'confidence_score': self.confidence_score,
            'model_predictions': self.model_predictions,
            'user_feedback': self.user_feedback,
            'is_correct': self.is_correct,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'source': self.source,
            'expense_metadata': self.expense_metadata,
            'date': self.date.isoformat() if self.date else None
        }
    
    def __repr__(self):
        return f'<Expense {self.description[:50]}... -> {self.predicted_category}>'

class ModelPerformance(db.Model):
    """Track model performance metrics."""
    __tablename__ = 'model_performance'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = db.Column(db.String(50), nullable=False, index=True)
    accuracy = db.Column(db.Float, nullable=False)
    precision = db.Column(db.Float, nullable=False)
    recall = db.Column(db.Float, nullable=False)
    f1_score = db.Column(db.Float, nullable=False)
    training_date = db.Column(db.DateTime, default=datetime.utcnow)
    data_size = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f'<ModelPerformance {self.model_name}: {self.accuracy:.3f}>'