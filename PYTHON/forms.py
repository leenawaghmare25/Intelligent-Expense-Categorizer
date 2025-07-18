"""Forms for the expense tracker application."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, TextAreaField, DecimalField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange
from wtforms.widgets import TextArea

class LoginForm(FlaskForm):
    """Login form."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])

class RegisterForm(FlaskForm):
    """Registration form."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address'),
        Length(max=120, message='Email must be less than 120 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])

class ExpenseForm(FlaskForm):
    """Expense categorization form."""
    description = TextAreaField('Transaction Description', validators=[
        DataRequired(message='Description is required'),
        Length(min=3, max=500, message='Description must be between 3 and 500 characters')
    ], render_kw={
        'placeholder': 'e.g., Starbucks Coffee, Uber ride, Grocery shopping',
        'rows': 3
    })
    amount = DecimalField('Amount (Optional)', validators=[
        Optional(),
        NumberRange(min=0, message='Amount must be positive')
    ], places=2, render_kw={
        'placeholder': '0.00',
        'step': '0.01'
    })

class FeedbackForm(FlaskForm):
    """User feedback form for expense predictions."""
    correct_category = SelectField('Correct Category', validators=[
        DataRequired(message='Please select the correct category')
    ], choices=[])  # Will be populated dynamically
    
    is_prediction_correct = BooleanField('Was the prediction correct?')

class ExpenseSearchForm(FlaskForm):
    """Form for searching and filtering expenses."""
    search_query = StringField('Search Description', validators=[
        Optional(),
        Length(max=200, message='Search query must be less than 200 characters')
    ], render_kw={
        'placeholder': 'Search expenses...'
    })
    
    category_filter = SelectField('Filter by Category', validators=[
        Optional()
    ], choices=[('', 'All Categories')])  # Will be populated dynamically
    
    amount_min = DecimalField('Min Amount', validators=[
        Optional(),
        NumberRange(min=0, message='Amount must be positive')
    ], places=2)
    
    amount_max = DecimalField('Max Amount', validators=[
        Optional(),
        NumberRange(min=0, message='Amount must be positive')
    ], places=2)

class ReceiptUploadForm(FlaskForm):
    """Form for uploading receipt images."""
    
    receipt_image = FileField('Receipt Image', validators=[
        FileRequired(message='Please select a receipt image'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'], 
                   message='Only image files are allowed (JPG, PNG, GIF, BMP, TIFF)')
    ])
    
    category_override = SelectField('Category Override (Optional)', validators=[
        Optional()
    ], choices=[
        ('', 'Auto-detect category'),
        ('Dining Out', 'Dining Out'),
        ('Transport', 'Transport'),
        ('Utilities', 'Utilities'),
        ('Groceries', 'Groceries'),
        ('Entertainment', 'Entertainment'),
        ('Shopping', 'Shopping'),
        ('Healthcare', 'Healthcare'),
        ('Education', 'Education'),
        ('Salary', 'Salary'),
        ('Other', 'Other')
    ])
    
    notes = TextAreaField('Additional Notes', validators=[
        Optional(),
        Length(max=500, message='Notes must be less than 500 characters')
    ], render_kw={'rows': 3, 'placeholder': 'Optional notes about this receipt...'})
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default help text
        self.receipt_image.description = 'Upload a clear image of your receipt. Supported formats: JPG, PNG, GIF, BMP, TIFF'
        self.category_override.description = 'Leave blank to automatically detect the category using AI'
        self.notes.description = 'Any additional information about this receipt'