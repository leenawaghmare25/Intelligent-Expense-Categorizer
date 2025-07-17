"""Main application routes."""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime
import logging

from PYTHON.models import db, Expense
from PYTHON.forms import ExpenseForm, FeedbackForm, ExpenseSearchForm
from PYTHON.ml_models import EnsembleExpenseClassifier

main_bp = Blueprint('main', __name__)

# Global ensemble model instance
ensemble_model = None

def load_ensemble_model():
    """Load the ensemble model."""
    global ensemble_model
    if ensemble_model is None:
        ensemble_model = EnsembleExpenseClassifier()
        if not ensemble_model.load_models():
            logging.error("Failed to load ensemble models")
            ensemble_model = None
    return ensemble_model

@main_bp.route('/')
def index():
    """Home page route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard."""
    # Get recent expenses
    recent_expenses = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.created_at.desc())\
        .limit(10).all()
    
    # Get user statistics
    stats = current_user.get_expense_stats()
    
    return render_template('dashboard.html', 
                         recent_expenses=recent_expenses, 
                         stats=stats)

@main_bp.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    """Expense prediction route."""
    form = ExpenseForm()
    
    if form.validate_on_submit():
        model = load_ensemble_model()
        if not model:
            flash("Prediction models are not available. Please try again later.", "error")
            return redirect(url_for('main.predict'))
        
        description = form.description.data.strip()
        amount = form.amount.data
        
        try:
            # Get detailed prediction from ensemble
            detailed_prediction = model.get_detailed_prediction(description)
            
            # Save expense to database
            expense = Expense(
                user_id=current_user.id,
                description=description,
                amount=amount,
                predicted_category=detailed_prediction['ensemble_prediction'],
                confidence_score=detailed_prediction['ensemble_confidence'],
                model_predictions=detailed_prediction['individual_models']
            )
            
            db.session.add(expense)
            db.session.commit()
            
            logging.info(f"Expense predicted and saved for user {current_user.username}: "
                        f"'{description}' -> {detailed_prediction['ensemble_prediction']}")
            
            return render_template('result.html', 
                                 expense=expense,
                                 detailed_prediction=detailed_prediction)
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in prediction: {str(e)}")
            flash("An error occurred during prediction. Please try again.", "error")
    
    return render_template('predict.html', form=form)

@main_bp.route('/expenses')
@login_required
def expenses():
    """Expense history page with search and filtering."""
    form = ExpenseSearchForm()
    
    # Build query
    query = Expense.query.filter_by(user_id=current_user.id)
    
    # Apply filters if form is submitted
    if request.args.get('search_query'):
        search_query = request.args.get('search_query')
        query = query.filter(Expense.description.contains(search_query))
        form.search_query.data = search_query
    
    if request.args.get('category_filter'):
        category_filter = request.args.get('category_filter')
        query = query.filter(Expense.predicted_category == category_filter)
        form.category_filter.data = category_filter
    
    if request.args.get('amount_min'):
        try:
            amount_min = float(request.args.get('amount_min'))
            query = query.filter(Expense.amount >= amount_min)
            form.amount_min.data = amount_min
        except (ValueError, TypeError):
            pass
    
    if request.args.get('amount_max'):
        try:
            amount_max = float(request.args.get('amount_max'))
            query = query.filter(Expense.amount <= amount_max)
            form.amount_max.data = amount_max
        except (ValueError, TypeError):
            pass
    
    # Get unique categories for filter dropdown
    categories = db.session.query(Expense.predicted_category.distinct())\
        .filter_by(user_id=current_user.id).all()
    form.category_filter.choices = [('', 'All Categories')] + \
        [(cat[0], cat[0]) for cat in categories]
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    expenses_paginated = query.order_by(Expense.created_at.desc())\
        .paginate(page=page, per_page=current_app.config['EXPENSES_PER_PAGE'], 
                 error_out=False)
    
    return render_template('expenses.html', 
                         expenses=expenses_paginated, 
                         form=form)

@main_bp.route('/expense/<expense_id>')
@login_required
def expense_detail(expense_id):
    """Detailed view of a specific expense."""
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    return render_template('expense_detail.html', expense=expense)

@main_bp.route('/expense/<expense_id>/feedback', methods=['POST'])
@login_required
def expense_feedback(expense_id):
    """Handle user feedback on expense predictions."""
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    
    form = FeedbackForm()
    
    # Populate category choices
    model = load_ensemble_model()
    if model and model.categories:
        form.correct_category.choices = [(cat, cat) for cat in model.categories]
    
    if form.validate_on_submit():
        expense.user_feedback = form.correct_category.data
        expense.is_correct = form.is_prediction_correct.data
        expense.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('Thank you for your feedback!', 'success')
            logging.info(f"User feedback received for expense {expense_id}: "
                        f"correct={expense.is_correct}, feedback={expense.user_feedback}")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving feedback: {str(e)}")
            flash('Error saving feedback. Please try again.', 'error')
    
    return redirect(url_for('main.expense_detail', expense_id=expense_id))

@main_bp.route('/api/predict', methods=['POST'])
@login_required
def api_predict():
    """API endpoint for expense prediction."""
    try:
        model = load_ensemble_model()
        if not model:
            return jsonify({"error": "Prediction models not available"}), 500
        
        data = request.get_json()
        if not data or 'description' not in data:
            return jsonify({"error": "Missing description"}), 400
        
        description = data['description'].strip()
        if not description:
            return jsonify({"error": "Empty description"}), 400
        
        amount = data.get('amount')
        
        # Get detailed prediction
        detailed_prediction = model.get_detailed_prediction(description)
        
        # Save expense to database
        expense = Expense(
            user_id=current_user.id,
            description=description,
            amount=amount,
            predicted_category=detailed_prediction['ensemble_prediction'],
            confidence_score=detailed_prediction['ensemble_confidence'],
            model_predictions=detailed_prediction['individual_models']
        )
        
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({
            "expense_id": expense.id,
            "prediction": detailed_prediction['ensemble_prediction'],
            "confidence": detailed_prediction['ensemble_confidence'],
            "individual_predictions": detailed_prediction['individual_models'],
            "timestamp": expense.created_at.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in API prediction: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@main_bp.route('/api/expenses')
@login_required
def api_expenses():
    """API endpoint to get user's expenses."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        expenses_paginated = Expense.query.filter_by(user_id=current_user.id)\
            .order_by(Expense.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "expenses": [expense.to_dict() for expense in expenses_paginated.items],
            "pagination": {
                "page": expenses_paginated.page,
                "pages": expenses_paginated.pages,
                "per_page": expenses_paginated.per_page,
                "total": expenses_paginated.total,
                "has_next": expenses_paginated.has_next,
                "has_prev": expenses_paginated.has_prev
            }
        })
        
    except Exception as e:
        logging.error(f"Error in API expenses: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@main_bp.route('/health')
def health_check():
    """Health check endpoint."""
    model = load_ensemble_model()
    status = {
        "status": "healthy",
        "models_loaded": model is not None,
        "database_connected": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Test database connection
        db.session.execute('SELECT 1')
    except Exception as e:
        status["database_connected"] = False
        status["database_error"] = str(e)
    
    return jsonify(status)