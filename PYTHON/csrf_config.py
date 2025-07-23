#!/usr/bin/env python3
"""
Improved CSRF Configuration
This module provides a robust CSRF setup that handles session issues properly.
"""

from flask import session, request, current_app
from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf
from werkzeug.exceptions import BadRequest
import logging

class ImprovedCSRFProtect(CSRFProtect):
    """Enhanced CSRF protection with better session handling."""
    
    def init_app(self, app):
        """Initialize CSRF protection with improved configuration."""
        super().init_app(app)
        
        # Add custom error handler
        def csrf_error(reason):
            app.logger.warning(f"CSRF validation failed: {reason}")
            app.logger.warning(f"Request method: {request.method}")
            app.logger.warning(f"Request endpoint: {request.endpoint}")
            app.logger.warning(f"Session keys: {list(session.keys()) if session else 'No session'}")
            app.logger.warning(f"Form data keys: {list(request.form.keys()) if request.form else 'No form data'}")
            
            if request.is_json:
                return {'error': 'CSRF token missing or invalid', 'reason': reason}, 400
            
            # For HTML forms, redirect back with error message
            from flask import flash, redirect, url_for
            flash('Security token expired or missing. Please try again.', 'error')
            
            # Try to redirect to the same page or login
            if request.endpoint and 'auth' in request.endpoint:
                return redirect(url_for('auth.login'))
            return redirect(request.referrer or url_for('main.index'))
        
        # Set the error handler
        self.error_handler(csrf_error)
        
        # Add before_request handler to ensure session exists
        @app.before_request
        def ensure_csrf_session():
            """Ensure session is properly initialized for CSRF."""
            if request.method == 'POST' and request.endpoint:
                # Skip CSRF for certain endpoints if needed
                skip_endpoints = ['auth.csrf_debug']
                if request.endpoint in skip_endpoints:
                    return
                
                # Ensure session exists
                if not session:
                    session.permanent = True
                    session['_csrf_initialized'] = True
                    app.logger.info("Initialized new session for CSRF")
                
                # Log CSRF token status
                csrf_token_in_form = 'csrf_token' in request.form
                csrf_token_in_headers = 'X-CSRFToken' in request.headers
                
                app.logger.info(f"CSRF check - Form token: {csrf_token_in_form}, Header token: {csrf_token_in_headers}")
                
                if not csrf_token_in_form and not csrf_token_in_headers:
                    app.logger.warning("No CSRF token found in request")

def setup_csrf_protection(app):
    """Set up enhanced CSRF protection configuration."""
    
    # Only enable CSRF if configured
    if not app.config.get('WTF_CSRF_ENABLED', True):
        app.logger.info("CSRF protection is disabled")
        return None
    
    # CSRF is already initialized in app.py, just add enhanced configuration
    
    # Add custom error handler using app.errorhandler
    @app.errorhandler(400)
    def handle_csrf_error(e):
        # Check if this is a CSRF error
        if 'CSRF' in str(e) or 'csrf' in str(e).lower():
            app.logger.warning(f"CSRF validation failed: {e}")
            app.logger.warning(f"Request method: {request.method}")
            app.logger.warning(f"Request endpoint: {request.endpoint}")
            
            if request.is_json:
                return {'error': 'CSRF token missing or invalid'}, 400
            
            # For HTML forms, redirect back with error message
            from flask import flash, redirect, url_for
            flash('Security token expired or missing. Please try again.', 'error')
            
            # Try to redirect to the same page or login
            if request.endpoint and 'auth' in request.endpoint:
                return redirect(url_for('auth.login'))
            return redirect(request.referrer or url_for('main.index'))
        
        # If not CSRF error, handle normally
        return e
    
    # Add context processor for CSRF token
    @app.context_processor
    def inject_csrf_token():
        """Inject CSRF token into all templates."""
        try:
            token = generate_csrf()
            return dict(csrf_token=lambda: token)
        except Exception as e:
            app.logger.error(f"Failed to generate CSRF token: {e}")
            return dict(csrf_token=lambda: '')
    
    # Add template global for manual token generation
    @app.template_global()
    def csrf_token():
        """Generate CSRF token for templates."""
        try:
            return generate_csrf()
        except Exception as e:
            app.logger.error(f"Failed to generate CSRF token in template: {e}")
            return ''
    
    app.logger.info("CSRF protection enabled with improved configuration")
    return True

def validate_csrf_token(token=None):
    """Manually validate CSRF token."""
    try:
        if token is None:
            token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
        
        if not token:
            return False, "No CSRF token provided"
        
        validate_csrf(token)
        return True, "Valid"
    
    except Exception as e:
        return False, str(e)

def get_csrf_token():
    """Get current CSRF token."""
    try:
        return generate_csrf()
    except Exception as e:
        current_app.logger.error(f"Failed to generate CSRF token: {e}")
        return None