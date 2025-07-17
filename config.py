import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the Flask application."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Database configuration
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(BASE_DIR, "expense_tracker.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Model paths - Updated for lightweight models
    MODEL_DIR = os.path.join(BASE_DIR, 'PYTHON', 'models')
    NAIVE_BAYES_MODEL_PATH = os.path.join(MODEL_DIR, 'nb_model.pkl')
    SVM_MODEL_PATH = os.path.join(MODEL_DIR, 'svm_model.pkl')
    KEYWORD_MODEL_PATH = os.path.join(MODEL_DIR, 'keyword_model.pkl')
    VECTORIZER_PATH = os.path.join(MODEL_DIR, 'vectorizer.pkl')
    
    # Data paths
    DATA_DIR = os.path.join(BASE_DIR, 'PYTHON', 'data')
    DATA_PATH = os.path.join(DATA_DIR, 'synthetic_expenses.csv')
    
    # Pagination
    EXPENSES_PER_PAGE = 20
    
    # Model ensemble weights
    MODEL_WEIGHTS = {
        'naive_bayes': 0.4,
        'svm': 0.4,
        'keyword': 0.2
    }