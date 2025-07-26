"""Authentication blueprint for user management."""

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse as url_parse
import logging

from PYTHON.models import db, User
from PYTHON.forms import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/csrf-debug')
def csrf_debug():
    """Debug route to check CSRF token generation."""
    from flask_wtf.csrf import generate_csrf
    try:
        token = generate_csrf()
        return jsonify({
            'csrf_token': token,
            'session_keys': list(session.keys()),
            'has_session': bool(session),
            'session_id': session.get('_id', 'No session ID')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if request.method == 'POST':
        current_app.logger.info(f"Login POST request received. Form errors: {form.errors}")
        current_app.logger.info(f"CSRF token in form: {'csrf_token' in request.form}")
        current_app.logger.info(f"Session: {dict(request.session) if hasattr(request, 'session') else 'No session'}")
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user)
            logging.info(f"User {user.username} logged in successfully")
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.dashboard')
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
            logging.warning(f"Failed login attempt for username: {form.username.data}")
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegisterForm()
    
    if request.method == 'POST':
        current_app.logger.info(f"Register POST request received. Form errors: {form.errors}")
        current_app.logger.info(f"CSRF token in form: {'csrf_token' in request.form}")
    
    if form.validate_on_submit():
        # Check if username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            logging.info(f"New user registered: {user.username}")
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error registering user: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout route."""
    username = current_user.username
    logout_user()
    logging.info(f"User {username} logged out")
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    stats = current_user.get_expense_stats()
    return render_template('auth/profile.html', user=current_user, stats=stats)