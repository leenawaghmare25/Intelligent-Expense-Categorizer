#!/usr/bin/env python3
"""Test CSRF functionality."""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PYTHON.app import create_app
from PYTHON.models import db, User

def test_csrf():
    """Test CSRF token generation and validation."""
    app = create_app('development')
    
    with app.test_client() as client:
        with app.app_context():
            # Test GET request to login page
            response = client.get('/auth/login')
            print(f"Login page status: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Login page loads successfully")
                
                # Check if CSRF token is in the response
                if 'csrf_token' in response.get_data(as_text=True):
                    print("✓ CSRF token found in login form")
                else:
                    print("! CSRF token not found in login form")
            else:
                print("✗ Login page failed to load")
            
            # Test POST request (this should work now)
            response = client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)
            
            print(f"Login POST status: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Login POST request successful (no CSRF error)")
            else:
                print("✗ Login POST request failed")

if __name__ == "__main__":
    test_csrf()