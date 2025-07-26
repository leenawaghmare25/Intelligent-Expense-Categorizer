"""Main application routes."""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime
import logging
import os
from werkzeug.utils import secure_filename
from pathlib import Path

from PYTHON.models import db, Expense
from PYTHON.forms import ExpenseForm, FeedbackForm, ExpenseSearchForm, ReceiptUploadForm, BulkDeleteForm, DeleteConfirmationForm
from PYTHON.ml_models import EnsembleExpenseClassifier
from PYTHON.receipt_processor import ReceiptExpenseManager
from PYTHON.utils import setup_logger
from PYTHON.rate_limiter import rate_limit
from PYTHON.cleanup_tasks import cleanup_old_deleted_expenses, get_cleanup_stats

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
    
    # Build query - only show non-deleted expenses
    query = Expense.get_active_expenses(current_user.id)
    
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
    
    # Create feedback form with populated categories
    form = FeedbackForm()
    model = load_ensemble_model()
    if model and model.categories:
        form.correct_category.choices = [(cat, cat) for cat in model.categories]
    
    return render_template('expense_detail.html', expense=expense, form=form)

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

@main_bp.route('/expense/<expense_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    """Edit an existing expense."""
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    
    form = ExpenseForm()
    
    if form.validate_on_submit():
        try:
            # Update expense details
            expense.description = form.description.data.strip()
            expense.amount = form.amount.data
            expense.updated_at = datetime.utcnow()
            
            # Re-predict category if description changed
            model = load_ensemble_model()
            if model:
                detailed_prediction = model.get_detailed_prediction(expense.description)
                expense.predicted_category = detailed_prediction['ensemble_prediction']
                expense.confidence_score = detailed_prediction['ensemble_confidence']
                expense.model_predictions = detailed_prediction['individual_models']
            
            db.session.commit()
            flash('Expense updated successfully!', 'success')
            logging.info(f"Expense {expense_id} updated by user {current_user.username}")
            
            return redirect(url_for('main.expense_detail', expense_id=expense_id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating expense {expense_id}: {str(e)}")
            flash('Error updating expense. Please try again.', 'error')
    
    # Pre-populate form with existing data
    if request.method == 'GET':
        form.description.data = expense.description
        form.amount.data = expense.amount
    
    return render_template('edit_expense.html', form=form, expense=expense)

@main_bp.route('/expense/<expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    """Soft delete an existing expense with undo option."""
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id, is_deleted=False).first_or_404()
    
    try:
        description = expense.description  # Store for logging
        expense.soft_delete(current_user.id)
        db.session.commit()
        
        # Create undo link in flash message
        undo_url = url_for('main.restore_expense', expense_id=expense_id)
        flash(f'Expense deleted successfully! <a href="{undo_url}" class="alert-link">Undo</a>', 'success')
        logging.info(f"Expense {expense_id} '{description}' soft deleted by user {current_user.username}")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting expense {expense_id}: {str(e)}")
        flash('Error deleting expense. Please try again.', 'error')
    
    return redirect(url_for('main.expenses'))

@main_bp.route('/expense/<expense_id>/restore', methods=['POST'])
@login_required
def restore_expense(expense_id):
    """Restore a soft-deleted expense."""
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id, is_deleted=True).first_or_404()
    
    try:
        description = expense.description
        expense.restore()
        db.session.commit()
        
        flash('Expense restored successfully!', 'success')
        logging.info(f"Expense {expense_id} '{description}' restored by user {current_user.username}")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error restoring expense {expense_id}: {str(e)}")
        flash('Error restoring expense. Please try again.', 'error')
    
    return redirect(url_for('main.expenses'))

@main_bp.route('/expenses/bulk-delete', methods=['POST'])
@login_required
@rate_limit(max_requests=5, window_seconds=60)
def bulk_delete_expenses():
    """Delete multiple expenses at once."""
    try:
        data = request.get_json()
        if not data or 'expense_ids' not in data:
            return jsonify({'error': 'No expense IDs provided'}), 400
        
        expense_ids = data['expense_ids']
        if not expense_ids:
            return jsonify({'error': 'No expense IDs provided'}), 400
        
        # Validate that all expenses belong to the current user and are not already deleted
        expenses = Expense.query.filter(
            Expense.id.in_(expense_ids),
            Expense.user_id == current_user.id,
            Expense.is_deleted == False
        ).all()
        
        found_ids = [e.id for e in expenses]
        missing_ids = [eid for eid in expense_ids if eid not in found_ids]
        
        if len(expenses) != len(expense_ids):
            logging.warning(f"Bulk delete validation failed - User {current_user.username}")
            logging.warning(f"Requested IDs: {expense_ids}")
            logging.warning(f"Found IDs: {found_ids}")
            logging.warning(f"Missing IDs: {missing_ids}")
            return jsonify({
                'error': 'Some expenses not found or access denied',
                'requested_count': len(expense_ids),
                'found_count': len(expenses),
                'missing_ids': missing_ids
            }), 403
        
        # Soft delete expenses
        deleted_count = 0
        deleted_descriptions = []
        
        for expense in expenses:
            deleted_descriptions.append(expense.description[:50])
            expense.soft_delete(current_user.id)
            deleted_count += 1
        
        db.session.commit()
        
        flash(f'Successfully deleted {deleted_count} expense(s)!', 'success')
        logging.info(f"Bulk delete: User {current_user.username} deleted {deleted_count} expenses")
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} expense(s)',
            'undo_available': True
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in bulk delete: {str(e)}")
        return jsonify({'error': 'Failed to delete expenses'}), 500

@main_bp.route('/expenses/deleted')
@login_required
def deleted_expenses():
    """View recently deleted expenses with restore options."""
    # Get deleted expenses from the last 30 days
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    deleted_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.is_deleted == True,
        Expense.deleted_at >= thirty_days_ago
    ).order_by(Expense.deleted_at.desc()).all()
    
    return render_template('deleted_expenses.html', deleted_expenses=deleted_expenses)

@main_bp.route('/expenses/bulk-restore', methods=['POST'])
@login_required
def bulk_restore_expenses():
    """Restore multiple deleted expenses at once."""
    try:
        data = request.get_json()
        if not data or 'expense_ids' not in data:
            return jsonify({'error': 'No expense IDs provided'}), 400
        
        expense_ids = data['expense_ids']
        if not expense_ids:
            return jsonify({'error': 'No expense IDs provided'}), 400
        
        # Validate that all expenses belong to the current user and are deleted
        expenses = Expense.query.filter(
            Expense.id.in_(expense_ids),
            Expense.user_id == current_user.id,
            Expense.is_deleted == True
        ).all()
        
        if len(expenses) != len(expense_ids):
            return jsonify({'error': 'Some expenses not found or access denied'}), 403
        
        # Restore expenses
        restored_count = 0
        
        for expense in expenses:
            expense.restore()
            restored_count += 1
        
        db.session.commit()
        
        flash(f'Successfully restored {restored_count} expense(s)!', 'success')
        logging.info(f"Bulk restore: User {current_user.username} restored {restored_count} expenses")
        
        return jsonify({
            'success': True,
            'restored_count': restored_count,
            'message': f'Successfully restored {restored_count} expense(s)'
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in bulk restore: {str(e)}")
        return jsonify({'error': 'Failed to restore expenses'}), 500

@main_bp.route('/expenses/permanent-delete', methods=['POST'])
@login_required
def permanent_delete_expenses():
    """Permanently delete expenses (hard delete)."""
    try:
        data = request.get_json()
        if not data or 'expense_ids' not in data:
            return jsonify({'error': 'No expense IDs provided'}), 400
        
        expense_ids = data['expense_ids']
        if not expense_ids:
            return jsonify({'error': 'No expense IDs provided'}), 400
        
        # Validate that all expenses belong to the current user and are soft deleted
        expenses = Expense.query.filter(
            Expense.id.in_(expense_ids),
            Expense.user_id == current_user.id,
            Expense.is_deleted == True
        ).all()
        
        if len(expenses) != len(expense_ids):
            return jsonify({'error': 'Some expenses not found or access denied'}), 403
        
        # Permanently delete expenses
        deleted_count = 0
        deleted_descriptions = []
        
        for expense in expenses:
            deleted_descriptions.append(expense.description[:50])
            db.session.delete(expense)
            deleted_count += 1
        
        db.session.commit()
        
        flash(f'Permanently deleted {deleted_count} expense(s)!', 'warning')
        logging.info(f"Permanent delete: User {current_user.username} permanently deleted {deleted_count} expenses")
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Permanently deleted {deleted_count} expense(s)'
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in permanent delete: {str(e)}")
        return jsonify({'error': 'Failed to permanently delete expenses'}), 500

@main_bp.route('/admin/cleanup-stats')
@login_required
def admin_cleanup_stats():
    """Get cleanup statistics (admin only)."""
    # In a real app, you'd check if user is admin
    # For now, any logged-in user can see stats
    try:
        stats = get_cleanup_stats()
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logging.error(f"Error getting cleanup stats: {str(e)}")
        return jsonify({'error': 'Failed to get cleanup stats'}), 500

@main_bp.route('/admin/run-cleanup', methods=['POST'])
@login_required
@rate_limit(max_requests=1, window_seconds=300)  # Only 1 cleanup per 5 minutes
def admin_run_cleanup():
    """Manually trigger cleanup (admin only)."""
    # In a real app, you'd check if user is admin
    try:
        deleted_count = cleanup_old_deleted_expenses()
        stats = get_cleanup_stats()
        
        logging.info(f"Manual cleanup triggered by user {current_user.username}: {deleted_count} expenses deleted")
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'stats': stats,
            'message': f'Successfully cleaned up {deleted_count} old expenses'
        })
        
    except Exception as e:
        logging.error(f"Error in manual cleanup: {str(e)}")
        return jsonify({'error': 'Failed to run cleanup'}), 500

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

# Receipt Upload Routes
@main_bp.route('/upload-receipt', methods=['GET', 'POST'])
@login_required
def upload_receipt():
    """Handle receipt image upload and processing."""
    logger = setup_logger(__name__)
    form = ReceiptUploadForm()
    
    if form.validate_on_submit():
        try:
            # Get uploaded file
            receipt_file = form.receipt_image.data
            
            # Create uploads directory if it doesn't exist
            uploads_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
            uploads_dir.mkdir(exist_ok=True)
            
            # Save uploaded file securely
            filename = secure_filename(receipt_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{current_user.id}_{timestamp}_{filename}"
            file_path = uploads_dir / filename
            
            receipt_file.save(str(file_path))
            logger.info(f"Receipt image saved: {file_path}")
            
            # Process the receipt
            receipt_manager = ReceiptExpenseManager()
            category_override = form.category_override.data if form.category_override.data else None
            
            result = receipt_manager.process_receipt_image(
                str(file_path), 
                current_user.id, 
                category_override
            )
            
            # Clean up uploaded file (optional - you might want to keep it)
            try:
                os.remove(str(file_path))
            except Exception as e:
                logger.warning(f"Could not remove uploaded file: {e}")
            
            if result['success']:
                flash(f"Receipt processed successfully! Created {result['expenses_created']} expense(s).", 'success')
                return redirect(url_for('main.expenses'))
            else:
                flash('Receipt processing failed. Please try again.', 'error')
                    
        except Exception as e:
            logger.error(f"Error processing receipt: {str(e)}")
            flash(f'Error processing receipt: {str(e)}', 'error')
    
    return render_template('upload_receipt.html', form=form)

@main_bp.route('/api/upload-receipt', methods=['POST'])
@login_required
def api_upload_receipt():
    """API endpoint for receipt upload."""
    logger = setup_logger(__name__)
    
    try:
        # Check if file is present
        if 'receipt_image' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['receipt_image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'}
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Create uploads directory
        uploads_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
        uploads_dir.mkdir(exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{current_user.id}_{timestamp}_{filename}"
        file_path = uploads_dir / filename
        
        file.save(str(file_path))
        
        # Process receipt
        receipt_manager = ReceiptExpenseManager()
        category_override = request.form.get('category_override')
        
        result = receipt_manager.process_receipt_image(
            str(file_path), 
            current_user.id, 
            category_override if category_override else None
        )
        
        # Clean up file
        try:
            os.remove(str(file_path))
        except Exception as e:
            logger.warning(f"Could not remove uploaded file: {e}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in API receipt upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/receipt-history')
@login_required
def receipt_history():
    """Show expenses created from receipt uploads."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('EXPENSES_PER_PAGE', 20)
        
        # Get expenses from receipt uploads (only non-deleted ones)
        expenses_paginated = Expense.query.filter_by(
            user_id=current_user.id,
            source='receipt_upload',
            is_deleted=False
        ).order_by(Expense.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('receipt_history.html', 
                             expenses=expenses_paginated.items,
                             pagination=expenses_paginated)
        
    except Exception as e:
        logging.error(f"Error in receipt history: {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        flash('Error loading receipt history.', 'error')
        return redirect(url_for('main.dashboard'))