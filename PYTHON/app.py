"""Flask application factory for the Smart Expense Categorizer."""

import os
import sys
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from project_config import config
from PYTHON.models import db, User
from PYTHON.auth import auth_bp
from PYTHON.routes import main_bp

def create_app(config_name=None):
    """
    Application factory pattern with proper configuration management.
    
    Args:
        config_name: Configuration environment ('development', 'testing', 'production')
    
    Returns:
        Flask application instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure logging
    configure_logging(app)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Add security headers
    add_security_headers(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")
            raise
    
    app.logger.info(f"Flask application created successfully in {config_name} mode")
    return app

def configure_logging(app):
    """Configure application logging with rotation."""
    if not app.debug and not app.testing:
        # File handler with rotation
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.info('Smart Expense Categorizer startup')

def init_extensions(app):
    """Initialize Flask extensions."""
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(user_id)
        except Exception:
            return None

def register_blueprints(app):
    """Register application blueprints."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

def register_error_handlers(app):
    """Register custom error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        if request.is_json:
            return jsonify({'error': 'Bad request'}), 400
        return render_template('error.html', error='Bad request', error_code=400), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        if request.is_json:
            return jsonify({'error': 'Unauthorized'}), 401
        return render_template('error.html', error='Unauthorized access', error_code=401), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        if request.is_json:
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('error.html', error='Access forbidden', error_code=403), 403
    
    @app.errorhandler(404)
    def not_found(error):
        if request.is_json:
            return jsonify({'error': 'Not found'}), 404
        return render_template('error.html', error='Page not found', error_code=404), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('error.html', error='Internal server error', error_code=500), 500

def add_security_headers(app):
    """Add security headers to responses."""
    
    @app.after_request
    def set_security_headers(response):
        if hasattr(app.config, 'SECURITY_HEADERS'):
            for header, value in app.config['SECURITY_HEADERS'].items():
                response.headers[header] = value
        
        # Basic security headers for all environments
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response

def register_context_processors(app):
    """Register template context processors."""
    
    @app.context_processor
    def inject_now():
        """Make current datetime available to all templates."""
        return {'now': datetime.now()}

if __name__ == '__main__':
    app = create_app()
    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )