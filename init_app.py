#!/usr/bin/env python3
"""
Initialize the application: create database, train models, and set up the system.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PYTHON.app import create_app
from PYTHON.models import db, User
from PYTHON.main import main as train_models_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('init_app.log'),
        logging.StreamHandler()
    ]
)

def create_database():
    """Create database tables."""
    logging.info("Creating database tables...")
    try:
        db.create_all()
        logging.info("Database tables created successfully!")
        return True
    except Exception as e:
        logging.error(f"Error creating database: {str(e)}")
        return False

def create_admin_user():
    """Create a default admin user for testing."""
    logging.info("Creating default admin user...")
    try:
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            logging.info("Admin user already exists")
            return True
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com'
        )
        admin.set_password('admin123')  # Change this in production!
        
        db.session.add(admin)
        db.session.commit()
        
        logging.info("Admin user created successfully!")
        logging.info("Username: admin")
        logging.info("Password: admin123")
        logging.info("⚠️  IMPORTANT: Change the admin password in production!")
        
        return True
    except Exception as e:
        logging.error(f"Error creating admin user: {str(e)}")
        db.session.rollback()
        return False

def train_ml_models():
    """Train the machine learning models."""
    logging.info("Training machine learning models...")
    try:
        # Run the training script
        train_models_main()
        logging.info("Machine learning models trained successfully!")
        return True
    except Exception as e:
        logging.error(f"Error training models: {str(e)}")
        return False

def main():
    """Main initialization function."""
    logging.info("🚀 Starting application initialization...")
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        success = True
        
        # Step 1: Create database
        if not create_database():
            success = False
        
        # Step 2: Create admin user
        if success and not create_admin_user():
            success = False
        
        # Step 3: Train models
        if success and not train_ml_models():
            success = False
        
        if success:
            logging.info("✅ Application initialization completed successfully!")
            logging.info("\n" + "="*60)
            logging.info("🎉 SETUP COMPLETE!")
            logging.info("="*60)
            logging.info("Your Smart Expense Categorizer is ready to use!")
            logging.info("")
            logging.info("Next steps:")
            logging.info("1. Run the application: python PYTHON/app.py")
            logging.info("2. Open your browser to: http://localhost:5000")
            logging.info("3. Login with:")
            logging.info("   Username: admin")
            logging.info("   Password: admin123")
            logging.info("")
            logging.info("Features available:")
            logging.info("✓ User authentication and accounts")
            logging.info("✓ AI-powered expense categorization")
            logging.info("✓ Expense tracking history")
            logging.info("✓ Lightweight ensemble ML models")
            logging.info("✓ Model performance feedback")
            logging.info("✓ Responsive web interface")
            logging.info("="*60)
        else:
            logging.error("❌ Application initialization failed!")
            logging.error("Please check the logs above for details.")
            sys.exit(1)

if __name__ == "__main__":
    main()