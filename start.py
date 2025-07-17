#!/usr/bin/env python3
"""
Startup script for the Smart Expense Categorizer.
This script handles initialization and starts the application.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed."""
    print("Checking requirements...")
    try:
        import flask
        import flask_sqlalchemy
        import flask_login
        import flask_wtf
        import pandas
        import sklearn
        import joblib
        import numpy
        import bcrypt
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {str(e)}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_initialization():
    """Check if the system has been initialized."""
    print("Checking system initialization...")
    
    # Check if database exists
    db_path = Path("expense_tracker.db")
    models_dir = Path("PYTHON/models")
    
    if not db_path.exists() or not models_dir.exists():
        print("❌ System not initialized")
        print("Running initialization...")
        
        try:
            subprocess.run([sys.executable, "init_app.py"], check=True)
            print("✅ System initialized successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Initialization failed")
            return False
    else:
        print("✅ System already initialized")
        return True

def start_application():
    """Start the Flask application."""
    print("Starting the application...")
    print("="*50)
    print("🚀 Smart Expense Categorizer")
    print("="*50)
    print("Application will start at: http://localhost:5000")
    print("Default login: admin / admin123")
    print("Press Ctrl+C to stop the application")
    print("="*50)
    
    try:
        subprocess.run([sys.executable, "PYTHON/app.py"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {str(e)}")

def main():
    """Main startup function."""
    print("🏦 Smart Expense Categorizer - Startup Script")
    print("="*50)
    
    # Step 1: Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Step 2: Check initialization
    if not check_initialization():
        sys.exit(1)
    
    # Step 3: Start application
    start_application()

if __name__ == "__main__":
    main()