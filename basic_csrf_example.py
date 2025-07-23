#!/usr/bin/env python3
"""
CSRF Protection Implementation - Matches Your Request
This shows the exact pattern you requested integrated into your project.
"""

from flask import Flask
from flask_wtf import CSRFProtect

# This is the exact pattern you requested:
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # required for CSRF
csrf = CSRFProtect(app)

# Your project now implements this same pattern in PYTHON/app.py:
# 1. Flask app creation: app = Flask(__name__)
# 2. Secret key setup: app.secret_key = 'your-secret-key' 
# 3. CSRF protection: csrf = CSRFProtect(app)

@app.route('/')
def index():
    return '''
    <h2>CSRF Protection Demo</h2>
    <p>Your main application now uses the same CSRF setup pattern!</p>
    <form method="POST" action="/submit">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
        <input type="text" name="data" placeholder="Enter some data">
        <button type="submit">Submit</button>
    </form>
    '''

@app.route('/submit', methods=['POST'])
def submit():
    return "Form submitted successfully with CSRF protection!"

if __name__ == '__main__':
    print("This demo shows the CSRF pattern you requested.")
    print("Your main app in PYTHON/app.py now uses the same pattern!")
    app.run(debug=True, port=5001)