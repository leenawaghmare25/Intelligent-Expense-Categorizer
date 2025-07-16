# 🚀 Quick Start Guide

## For Windows Users

### Method 1: Automatic Setup (Recommended)
1. **Download** the project folder
2. **Double-click** `setup.bat`
3. **Wait** for setup to complete
4. **Run** the application:
   ```bash
   venv\Scripts\activate
   python run.py
   ```
5. **Open** your browser: `http://localhost:5000`

### Method 2: Manual Setup
```bash
# Open Command Prompt or PowerShell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

## For macOS/Linux Users

### Method 1: Automatic Setup (Recommended)
1. **Download** the project folder
2. **Open terminal** in the project folder
3. **Make setup script executable**:
   ```bash
   chmod +x setup.sh
   ```
4. **Run** the setup script:
   ```bash
   ./setup.sh
   ```
5. **Run** the application:
   ```bash
   source venv/bin/activate
   python run.py
   ```
6. **Open** your browser: `http://localhost:5000`

### Method 2: Manual Setup
```bash
# Open Terminal
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

## 🎯 One-Line Commands

### Windows
```bash
python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python run.py
```

### macOS/Linux
```bash
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python run.py
```

## 🔧 If Something Goes Wrong

1. **Check Python version**: `python --version` (should be 3.8+)
2. **Check if virtual environment is active**: Look for `(venv)` in your prompt
3. **Reinstall dependencies**: `pip install -r requirements.txt`
4. **Check the full README.md** for detailed troubleshooting

## 📱 Test the Application

Once running, test with these examples:
- "Starbucks coffee" → Dining Out
- "Uber ride" → Transport
- "Netflix subscription" → Entertainment
- "Grocery shopping" → Groceries

## 🆘 Need Help?

Check the detailed **README.md** file for:
- Complete troubleshooting guide
- Advanced usage examples
- API documentation
- Performance tips

---

**🎉 That's it! Your expense categorizer is ready to use!**