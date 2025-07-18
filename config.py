"""Configuration settings for the expense categorizer application."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with environment-based settings."""
    
    # Base directory
    BASE_DIR = Path(__file__).parent
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = False
    
    # Database settings
    DATABASE_URL = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/expense_tracker.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Model file paths
    MODEL_DIR = BASE_DIR / "PYTHON" / "models"
    DATA_DIR = BASE_DIR / "PYTHON" / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Ensure directories exist
    MODEL_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Model file paths
    NAIVE_BAYES_MODEL_PATH = MODEL_DIR / "naive_bayes_model.joblib"
    SVM_MODEL_PATH = MODEL_DIR / "svm_model.joblib"
    VECTORIZER_PATH = MODEL_DIR / "vectorizer.joblib"
    KEYWORD_RULES_PATH = MODEL_DIR / "keyword_rules.json"
    
    # Data file path
    DATA_FILE_PATH = DATA_DIR / "synthetic_expenses.csv"
    
    # Model ensemble weights (must sum to 1.0)
    MODEL_WEIGHTS = {
        'naive_bayes': float(os.environ.get('MODEL_WEIGHTS_NAIVE_BAYES', 0.4)),
        'svm': float(os.environ.get('MODEL_WEIGHTS_SVM', 0.4)),
        'keyword': float(os.environ.get('MODEL_WEIGHTS_KEYWORD', 0.2))
    }
    
    # Validate weights sum to 1.0
    if abs(sum(MODEL_WEIGHTS.values()) - 1.0) > 0.001:
        raise ValueError("Model weights must sum to 1.0")
    
    # Pagination
    EXPENSES_PER_PAGE = int(os.environ.get('EXPENSES_PER_PAGE', 20))
    MAX_EXPENSES_PER_PAGE = 100
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    SESSION_COOKIE_SECURE = not DEBUG  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Session
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = LOGS_DIR / 'app.log'
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    
    # Rate limiting (requests per minute)
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100 per minute')
    
    # ML Model settings
    ML_MODEL_RETRAIN_THRESHOLD = int(os.environ.get('ML_MODEL_RETRAIN_THRESHOLD', 100))
    ML_CONFIDENCE_THRESHOLD = float(os.environ.get('ML_CONFIDENCE_THRESHOLD', 0.6))
    
    # File Upload settings
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'}
    
    # Ensure upload directory exists
    UPLOAD_FOLDER.mkdir(exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    SESSION_COOKIE_SECURE = True
    SSL_REDIRECT = True
    
    # Enhanced security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'"
    }

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}