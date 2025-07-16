# 🏦 Smart Expense Categorizer

An intelligent machine learning web application that automatically classifies daily expenses into predefined categories using natural language processing (NLP) and text classification techniques.

## 📋 Features

- **Automatic Expense Classification**: Uses machine learning to categorize expenses based on description text
- **Web Interface**: Clean, responsive web interface built with Flask
- **REST API**: JSON API endpoints for programmatic access
- **High Accuracy**: Uses TF-IDF vectorization and Logistic Regression for reliable predictions
- **Confidence Scoring**: Provides confidence scores for each prediction
- **Real-time Processing**: Instant categorization of expense descriptions
- **Error Handling**: Comprehensive error handling and logging

## 🚀 Complete Setup Guide

### Prerequisites

Before you begin, ensure you have the following installed on your system:
- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **pip** (Python package manager) - Usually comes with Python
- **Git** (optional) - For cloning the repository

### Step 1: Download/Clone the Project

**Option A: Download ZIP**
1. Download the project as a ZIP file
2. Extract it to your desired location
3. Open terminal/command prompt in the extracted folder

**Option B: Clone with Git**
```bash
git clone <repository-url>
cd Intelligent-Expense-Categorizer
```

### Step 2: Set Up Virtual Environment

**For Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Verify activation (you should see (venv) in your prompt)
```

**For macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (you should see (venv) in your prompt)
```

### Step 3: Install Dependencies

```bash
# Make sure you're in the project directory and virtual environment is activated
pip install -r requirements.txt
```

### Step 4: Run the Application

**Option A: Using the Runner Script (Recommended)**
```bash
python run.py
```

**Option B: Manual Steps**
```bash
# Train the model first (if not already trained)
cd PYTHON
python main.py

# Run the Flask application
python app.py
```

### Step 5: Access the Application

1. Open your web browser
2. Go to `http://localhost:5000`
3. Start categorizing your expenses!

## 🖥️ System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux
- **Python**: Version 3.8 or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 1GB free space
- **Internet**: Required for initial package installation

## 📁 Project Structure (After Setup)

```
Intelligent-Expense-Categorizer/
├── 📄 config.py                 # Configuration settings
├── 🚀 run.py                    # Main runner script (START HERE)
├── 📋 requirements.txt          # Python dependencies
├── 📖 README.md                # This file (complete documentation)
├── 🚀 QUICKSTART.md            # Quick setup guide
├── 📁 venv/                    # Virtual environment (created during setup)
├── 🧪 test_api.py              # API testing script
├── ⚙️ setup.py                 # Package setup configuration
├── 🚫 .gitignore               # Git ignore file
├── 🔧 setup.bat                # Windows setup script
├── 🔧 setup.sh                 # macOS/Linux setup script
└── 📁 PYTHON/
    ├── 🤖 main.py              # Model training script
    ├── 🌐 app.py               # Flask web application
    ├── 📁 data/
    │   └── 📊 synthetic_expenses.csv  # Training data
    ├── 📁 model/                    # Model files (created after training)
    │   ├── 🧠 expense_model.pkl       # Trained model
    │   └── 📝 vectorizer.pkl          # TF-IDF vectorizer
    └── 📁 templates/
        ├── 🏠 index.html              # Home page
        ├── 📊 result.html             # Results page
        └── ❌ error.html              # Error page
```

## 🎯 Available Commands

### Basic Commands
```bash
# Start the application (recommended)
python run.py

# Train the model manually
cd PYTHON
python main.py

# Run Flask app directly
cd PYTHON
python app.py

# Test the API
python test_api.py
```

### Advanced Commands
```bash
# Check Python version
python --version

# List installed packages
pip list

# Update pip
pip install --upgrade pip

# Install specific package
pip install package_name

# Generate requirements file
pip freeze > requirements.txt

# Deactivate virtual environment
deactivate
```

## 🤖 Machine Learning Model

### Algorithm
- **Model**: Logistic Regression
- **Vectorization**: TF-IDF (Term Frequency-Inverse Document Frequency)
- **Features**: Text descriptions of expenses
- **Target**: Expense categories

### Categories
The model can classify expenses into the following categories:
- **Dining Out**: Restaurants, cafes, food delivery
- **Transport**: Uber, taxi, public transport, fuel
- **Utilities**: Electricity, water, internet bills
- **Groceries**: Supermarket shopping, food items
- **Shopping**: Clothing, electronics, general retail
- **Entertainment**: Movies, streaming, games
- **Healthcare**: Medical expenses, pharmacy
- **Education**: Books, courses, training

### Performance
- **Accuracy**: ~95% on test data
- **Cross-validation**: 5-fold CV implemented
- **Confidence Scoring**: Probability estimates for predictions

## 🌐 API Endpoints

### Web Interface
- `GET /` - Home page
- `POST /predict` - Submit expense for categorization

### REST API
- `POST /api/predict` - JSON API for predictions
- `GET /health` - Health check endpoint

### API Example

```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"description": "Starbucks coffee"}'
```

Response:
```json
{
  "prediction": "Dining Out",
  "confidence": 0.95,
  "timestamp": "2024-01-15T10:30:00"
}
```

## 🔧 Configuration

The application uses a configuration class in `config.py`:

```python
class Config:
    SECRET_KEY = 'your-secret-key-here'
    DEBUG = True
    MODEL_PATH = 'path/to/model.pkl'
    VECTORIZER_PATH = 'path/to/vectorizer.pkl'
```

## 📊 Training New Models

To retrain the model with new data:

1. **Add new data** to `PYTHON/data/synthetic_expenses.csv`
2. **Run training script**:
   ```bash
   cd PYTHON
   python main.py
   ```

The training script will:
- Load and preprocess the data
- Split into training/testing sets
- Train the model with cross-validation
- Save the trained model and vectorizer
- Generate performance metrics

## 🧪 Testing the Application

### Method 1: Web Interface Testing
1. Start the application: `python run.py`
2. Open your browser and go to `http://localhost:5000`
3. Test with these example descriptions:
   - "Starbucks coffee" → Should predict: Dining Out
   - "Uber ride to work" → Should predict: Transport
   - "Electricity bill payment" → Should predict: Utilities
   - "Grocery shopping" → Should predict: Groceries
   - "Netflix subscription" → Should predict: Entertainment

### Method 2: API Testing with curl
```bash
# Health check
curl http://localhost:5000/health

# Single prediction
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"description": "Netflix subscription"}'
```

### Method 3: Automated Testing Script
```bash
# Run the test script (make sure app is running first)
python test_api.py
```

### Method 4: Python Testing
```python
import requests

# Test prediction
response = requests.post('http://localhost:5000/api/predict', 
                        json={'description': 'Starbucks coffee'})
print(response.json())
```

## 🔄 Best Practices Implemented

### Code Quality
- **Modular Design**: Separation of concerns
- **Error Handling**: Comprehensive exception handling
- **Logging**: Detailed logging for debugging
- **Configuration Management**: Centralized configuration
- **Type Hints**: Better code documentation

### Security
- **Input Validation**: Sanitization of user inputs
- **Error Messages**: Safe error reporting
- **Configuration**: Environment-based settings

### Performance
- **Model Caching**: Models loaded once at startup
- **Efficient Vectorization**: Optimized TF-IDF parameters
- **Response Caching**: Fast prediction responses

### Deployment
- **Environment Management**: Virtual environment setup
- **Dependency Management**: Pinned requirements
- **Health Monitoring**: Health check endpoints
- **Logging**: Structured logging for monitoring

## 🐛 Troubleshooting Guide

### Common Issues and Solutions

#### 1. **"Python is not recognized" Error**
```bash
# Solution: Add Python to PATH or use full path
C:\Users\YourName\AppData\Local\Programs\Python\Python39\python.exe run.py
```

#### 2. **"No module named 'flask'" Error**
```bash
# Solution: Activate virtual environment and install dependencies
# Windows:
venv\Scripts\activate
pip install -r requirements.txt

# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. **"Model not found" Error**
```bash
# Solution: Train the model first
python run.py  # This will automatically train if model doesn't exist

# Or manually:
cd PYTHON
python main.py
```

#### 4. **"Port 5000 already in use" Error**
```bash
# Solution A: Kill the process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F

# macOS/Linux:
lsof -ti:5000 | xargs kill -9

# Solution B: Change port in config.py
# Edit config.py and change port to 5001 or other available port
```

#### 5. **"Permission denied" Error**
```bash
# Solution: Run as administrator (Windows) or use sudo (macOS/Linux)
# Windows: Right-click command prompt and "Run as administrator"
# macOS/Linux: sudo python run.py
```

#### 6. **Virtual Environment Issues**
```bash
# Delete and recreate virtual environment
rmdir /s venv          # Windows
rm -rf venv            # macOS/Linux

# Recreate
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

#### 7. **Browser Can't Access localhost:5000**
- Check if application is running (look for "Running on http://127.0.0.1:5000")
- Try `http://127.0.0.1:5000` instead of `localhost:5000`
- Check firewall settings
- Ensure no VPN is blocking local connections

### 🔧 Quick Fixes

```bash
# Reset everything and start fresh
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +  # macOS/Linux
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"  # Windows

# Check if all files are present
dir  # Windows
ls -la  # macOS/Linux
```

## 📱 Usage Examples

### Web Interface Usage
1. **Start the application**: `python run.py`
2. **Access the web interface**: Open browser → `http://localhost:5000`
3. **Enter expense description**: Type in the text field
4. **Get prediction**: Click "Categorize Expense" button
5. **View results**: See category and confidence score

### API Usage Examples

#### Using Python
```python
import requests

# Make a prediction
response = requests.post('http://localhost:5000/api/predict', 
                        json={'description': 'Starbucks coffee'})
result = response.json()
print(f"Category: {result['prediction']}")
print(f"Confidence: {result['confidence']:.2f}")
```

#### Using JavaScript
```javascript
fetch('http://localhost:5000/api/predict', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        description: 'Uber ride to work'
    })
})
.then(response => response.json())
.then(data => {
    console.log('Category:', data.prediction);
    console.log('Confidence:', data.confidence);
});
```

## 🔄 Updating the Project

### Adding New Training Data
1. **Edit the CSV file**: `PYTHON/data/synthetic_expenses.csv`
2. **Add new rows**: Format: `Date,Description,Amount,Category`
3. **Retrain the model**: `cd PYTHON && python main.py`
4. **Restart the application**: `python run.py`

### Updating Dependencies
```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade flask

# Generate new requirements
pip freeze > requirements.txt
```

## 🚀 Deployment Options

### Local Development
```bash
python run.py  # Development server
```

### Production Deployment
```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
cd PYTHON
gunicorn --bind 0.0.0.0:5000 app:app
```

### Docker Deployment
```dockerfile
# Create Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

## 📊 Performance Metrics

- **Training Time**: ~2-5 seconds
- **Prediction Time**: <100ms per request
- **Memory Usage**: ~50MB
- **Model Size**: ~1-2MB
- **Accuracy**: ~85-95% (depends on training data)

## 🎯 Quick Command Reference

```bash
# Essential Commands
python run.py                    # Start application
python PYTHON/main.py           # Train model
python test_api.py              # Test API
pip install -r requirements.txt # Install dependencies

# Troubleshooting Commands
python --version                # Check Python version
pip list                       # List installed packages
pip install --upgrade pip     # Update pip
deactivate                    # Exit virtual environment

# Development Commands
pip freeze > requirements.txt  # Update requirements
python -m venv venv           # Create virtual environment
venv\Scripts\activate         # Activate venv (Windows)
source venv/bin/activate      # Activate venv (macOS/Linux)
```

## 📈 Future Enhancements

- [ ] Add user authentication and accounts
- [ ] Implement expense tracking history
- [ ] Add data visualization dashboard
- [ ] Support for multiple languages
- [ ] Mobile app development
- [ ] Integration with banking APIs
- [ ] Advanced ML models (BERT, transformers)
- [ ] Real-time expense monitoring
- [ ] Budget tracking and alerts
- [ ] Export functionality (CSV, PDF)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📞 Support

If you encounter any issues:
1. Check the troubleshooting guide above
2. Look for similar issues in the project repository
3. Create a new issue with:
   - Your operating system
   - Python version (`python --version`)
   - Error message (full traceback)
   - Steps to reproduce

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Your Name** - *Initial work* - [YourGithub](https://github.com/yourusername)

## 🙏 Acknowledgments

- **scikit-learn** for machine learning tools
- **Flask** for the web framework
- **Pandas** for data manipulation
- **Community contributors** who helped improve this project

---

**📌 Remember**: Always activate your virtual environment before running any commands!

**🎉 Happy Expense Categorizing!**
