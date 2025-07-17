# 🏦 Smart Expense Categorizer

An advanced AI-powered expense categorization system with user authentication, expense tracking history, and lightweight ensemble machine learning models.

## ✨ Features

### 🔐 User Authentication & Accounts
- Secure user registration and login system
- Individual user accounts with personal expense history
- Profile management and statistics

### 🤖 AI-Powered Categorization
- **Ensemble ML Models**: Combines 3 lightweight models for better accuracy
  - Naive Bayes classifier
  - Support Vector Machine (SVM)
  - Keyword-based classifier
- **Smart Predictions**: Weighted ensemble voting for optimal results
- **Confidence Scoring**: Get reliability scores for each prediction
- **Model Transparency**: See individual model predictions and reasoning

### 📊 Expense Tracking & History
- Complete expense history with search and filtering
- Detailed expense views with model breakdowns
- User feedback system to improve model accuracy
- Category-wise statistics and analytics
- Pagination for large datasets

### 🎨 Modern Web Interface
- Responsive Bootstrap-based design
- Intuitive dashboard with expense analytics
- Real-time predictions with detailed breakdowns
- Mobile-friendly interface

### 🔧 Developer Features
- RESTful API endpoints
- Health monitoring and status checks
- Comprehensive logging system
- Database migrations and management

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Intelligent-Expense-Categorizer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the application** (One-time setup)
   ```bash
   python init_app.py
   ```
   This will:
   - Create the database tables
   - Train the ensemble ML models
   - Create a default admin user
   - Set up the complete system

4. **Run the application**
   ```bash
   python PYTHON/app.py
   ```

5. **Access the application**
   - Open your browser to `http://localhost:5000`
   - Login with:
     - Username: `admin`
     - Password: `admin123`
   - **⚠️ Change the admin password in production!**

## 📱 Usage

### Web Interface

1. **Register/Login**: Create an account or login to existing one
2. **Add Expenses**: Use the "Add Expense" feature to categorize transactions
3. **View History**: Browse your complete expense history with search/filter
4. **Dashboard**: Get insights and statistics about your spending patterns
5. **Provide Feedback**: Help improve the AI by marking predictions as correct/incorrect

### API Usage

**Authentication Required**: Most API endpoints require user authentication.

**Predict Expense Category**
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"description": "Starbucks Coffee", "amount": 5.50}'
```

**Response**
```json
{
  "expense_id": "uuid-here",
  "prediction": "Dining Out",
  "confidence": 0.87,
  "individual_predictions": {
    "naive_bayes": {
      "prediction": "Dining Out",
      "confidence": 0.92
    },
    "svm": {
      "prediction": "Dining Out", 
      "confidence": 0.85
    },
    "keyword": {
      "prediction": "Food",
      "confidence": 0.78
    }
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

**Get User Expenses**
```bash
curl http://localhost:5000/api/expenses?page=1&per_page=20
```

**Health Check**
```bash
curl http://localhost:5000/health
```

## 🧠 Machine Learning Architecture

### Ensemble Approach
The system uses a sophisticated ensemble of three lightweight models:

1. **Naive Bayes Classifier** (40% weight)
   - Fast and efficient for text classification
   - Works well with small datasets
   - Good baseline performance

2. **Linear SVM** (40% weight)
   - Excellent for high-dimensional text data
   - Good generalization capabilities
   - Robust to overfitting

3. **Keyword-Based Classifier** (20% weight)
   - Rule-based approach using category keywords
   - Provides interpretable predictions
   - Good fallback for edge cases

### Model Features
- **TF-IDF Vectorization**: Converts text to numerical features
- **Weighted Voting**: Combines predictions using configurable weights
- **Confidence Scoring**: Provides reliability metrics
- **Incremental Learning**: Models can be retrained with user feedback

### Categories Supported
- Dining Out
- Transport
- Utilities
- Groceries
- Entertainment
- Shopping
- Healthcare
- Education
- Salary
- Other

## 📁 Project Structure

```
Intelligent-Expense-Categorizer/
├── PYTHON/
│   ├── app.py              # Main Flask application
│   ├── models.py           # Database models
│   ├── auth.py             # Authentication blueprint
│   ├── routes.py           # Main application routes
│   ├── forms.py            # WTForms for user input
│   ├── ml_models.py        # Ensemble ML system
│   ├── main.py             # Model training script
│   ├── data/
│   │   └── synthetic_expenses.csv  # Training data
│   ├── models/             # Trained model files
│   └── templates/          # HTML templates
│       ├── base.html       # Base template
│       ├── auth/           # Authentication templates
│       ├── dashboard.html  # User dashboard
│       ├── expenses.html   # Expense history
│       └── ...
├── config.py               # Configuration settings
├── init_app.py             # Application initialization
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## ⚙️ Configuration

### Environment Variables
Copy `.env.example` to `.env` and customize:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=False

# Database Configuration  
DATABASE_URL=sqlite:///expense_tracker.db

# Model Weights (must sum to 1.0)
MODEL_WEIGHTS_NAIVE_BAYES=0.4
MODEL_WEIGHTS_SVM=0.4
MODEL_WEIGHTS_KEYWORD=0.2
```

### Database Configuration
- **Development**: SQLite (default)
- **Production**: PostgreSQL, MySQL, or other SQLAlchemy-supported databases

## 🔧 Development

### Adding New Categories

1. Update training data in `PYTHON/data/synthetic_expenses.csv`
2. Retrain models: `python PYTHON/main.py`
3. Restart the application

### Improving Model Performance

1. **Add Training Data**: More diverse examples improve accuracy
2. **Adjust Weights**: Modify ensemble weights in `config.py`
3. **Feature Engineering**: Enhance text preprocessing in `ml_models.py`
4. **User Feedback**: Collect and incorporate user corrections

### Database Migrations

```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade
```

## 📊 API Reference

### Authentication Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User login |
| POST | `/auth/register` | User registration |
| GET | `/auth/logout` | User logout |
| GET | `/auth/profile` | User profile |

### Main Application Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page |
| GET | `/dashboard` | User dashboard |
| POST | `/predict` | Add new expense |
| GET | `/expenses` | Expense history |
| GET | `/expense/<id>` | Expense details |
| POST | `/api/predict` | JSON API prediction |
| GET | `/api/expenses` | JSON API expense list |
| GET | `/health` | System health check |

### Error Handling
- `200`: Success
- `400`: Bad request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not found
- `500`: Internal server error

## 🐛 Troubleshooting

### Common Issues

1. **Database errors**
   ```bash
   # Reset database
   rm expense_tracker.db
   python init_app.py
   ```

2. **Model not found**
   ```bash
   # Retrain models
   python PYTHON/main.py
   ```

3. **Import errors**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

4. **Port conflicts**
   - Change port in `PYTHON/app.py`
   - Or kill process: `lsof -ti:5000 | xargs kill -9`

### Logs
- Application logs: `app.log`
- Training logs: `training.log`
- Initialization logs: `init_app.log`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Commit changes: `git commit -am 'Add feature'`
6. Push to branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Create an issue in the repository
4. Check existing issues for solutions

## 🎯 Roadmap

- [ ] Mobile app development
- [ ] Advanced analytics and reporting
- [ ] Receipt image processing
- [ ] Integration with banking APIs
- [ ] Multi-currency support
- [ ] Export functionality (CSV, PDF)
- [ ] Advanced ML models (BERT, transformers)
- [ ] Real-time notifications