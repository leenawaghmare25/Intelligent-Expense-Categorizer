#!/bin/bash

echo "================================================"
echo "   Smart Expense Categorizer - Setup Script"
echo "================================================"
echo

echo "📋 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    echo "Please install Python3 from https://www.python.org/downloads/"
    exit 1
fi

python3 --version
echo "✅ Python found!"
echo

echo "🏗️ Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "✅ Virtual environment created!"
echo

echo "🔧 Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated!"
echo

echo "📦 Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed!"
echo

echo "🤖 Training the model..."
cd PYTHON
python main.py
if [ $? -ne 0 ]; then
    echo "❌ Model training failed"
    exit 1
fi

cd ..
echo "✅ Model trained successfully!"
echo

echo "🎉 Setup completed successfully!"
echo
echo "To run the application:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run the application: python run.py"
echo "3. Open browser: http://localhost:5000"
echo

read -p "Press Enter to continue..."