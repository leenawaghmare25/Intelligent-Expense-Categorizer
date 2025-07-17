"""Main Flask application with user authentication and expense tracking."""

from flask import Flask, render_template
from flask_login import LoginManager
import os
import sys
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from PYTHON.models import db, User
from PYTHON.auth import auth_bp
from PYTHON.routes import main_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

def create_app():
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Error creating database tables: {str(e)}")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """404 error handler."""
        return render_template("error.html", 
                             error="Page not found", 
                             error_code=404), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 error handler."""
        db.session.rollback()
        logging.error(f"Internal server error: {str(error)}")
        return render_template("error.html", 
                             error="Internal server error", 
                             error_code=500), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        """403 error handler."""
        return render_template("error.html", 
                             error="Access forbidden", 
                             error_code=403), 403
    
    # Context processors
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    logging.info("Flask application created successfully")
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
