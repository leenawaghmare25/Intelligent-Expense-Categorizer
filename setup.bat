@echo off
echo ================================================
echo    Smart Expense Categorizer - Setup Script
echo ================================================
echo.

echo 📋 Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found!
echo.

echo 🏗️ Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment created!
echo.

echo 🔧 Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment activated!
echo.

echo 📦 Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed!
echo.

echo 🤖 Training the model...
cd PYTHON
python main.py
if %errorlevel% neq 0 (
    echo ❌ Model training failed
    pause
    exit /b 1
)

cd ..
echo ✅ Model trained successfully!
echo.

echo 🎉 Setup completed successfully!
echo.
echo To run the application:
echo 1. Activate virtual environment: venv\Scripts\activate
echo 2. Run the application: python run.py
echo 3. Open browser: http://localhost:5000
echo.

pause