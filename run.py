#!/usr/bin/env python3
"""
Smart Expense Categorizer - Runner Script
This script helps you run the complete project pipeline.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_requirements():
    """Check if all required packages are installed."""
    try:
        import pandas
        import sklearn
        import flask
        import joblib
        logging.info("✅ All required packages are installed")
        return True
    except ImportError as e:
        logging.error(f"❌ Missing required package: {e}")
        return False

def train_model():
    """Train the machine learning model."""
    try:
        logging.info("🤖 Training the model...")
        
        # Change to PYTHON directory and run training
        python_dir = Path(__file__).parent / "PYTHON"
        os.chdir(python_dir)
        
        result = subprocess.run([sys.executable, "main.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("✅ Model training completed successfully")
            return True
        else:
            logging.error(f"❌ Model training failed: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error during model training: {str(e)}")
        return False

def run_app():
    """Run the Flask application."""
    try:
        logging.info("🚀 Starting Flask application...")
        
        # Change to PYTHON directory and run app
        python_dir = Path(__file__).parent / "PYTHON"
        os.chdir(python_dir)
        
        # Run the Flask app
        subprocess.run([sys.executable, "app.py"])
        
    except KeyboardInterrupt:
        logging.info("🛑 Application stopped by user")
    except Exception as e:
        logging.error(f"❌ Error running application: {str(e)}")

def main():
    """Main runner function."""
    print("🏦 Smart Expense Categorizer")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please install required packages first:")
        print("pip install -r requirements.txt")
        return
    
    # Check if model exists
    model_path = Path(__file__).parent / "PYTHON" / "model" / "expense_model.pkl"
    
    if not model_path.exists():
        print("\n🤖 Model not found. Training new model...")
        if not train_model():
            print("❌ Model training failed. Please check the logs.")
            return
    else:
        print("✅ Model found. Skipping training.")
    
    print("\n🚀 Starting the application...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the application")
    
    run_app()

if __name__ == "__main__":
    main()