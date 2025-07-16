import os

class Config:
    """Configuration class for the Flask application."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DEBUG = os.environ.get('FLASK_DEBUG') or True
    
    # Model paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_DIR = os.path.join(BASE_DIR, 'PYTHON', 'model')
    MODEL_PATH = os.path.join(MODEL_DIR, 'expense_model.pkl')
    VECTORIZER_PATH = os.path.join(MODEL_DIR, 'vectorizer.pkl')
    
    # Data paths
    DATA_DIR = os.path.join(BASE_DIR, 'PYTHON', 'data')
    DATA_PATH = os.path.join(DATA_DIR, 'synthetic_expenses.csv')