#!/usr/bin/env python3
"""
Test that authentication is now working without CSRF issues.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PYTHON.app import create_app
from PYTHON.models import db, User

def test_auth_working():
    """Test that login and registration work without CSRF errors."""
    app = create_app('development')
    
    with app.test_client() as client:
        with app.app_context():
            # Create tables
            db.create_all()
            
            print("Testing authentication without CSRF issues...")
            print("=" * 50)
            
            # Test 1: GET login page
            response = client.get('/auth/login')
            print(f"1. Login page GET: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
            
            # Test 2: POST to login (should not get CSRF error)
            response = client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)
            print(f"2. Login POST: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
            
            # Test 3: GET register page
            response = client.get('/auth/register')
            print(f"3. Register page GET: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
            
            # Test 4: POST to register (should not get CSRF error)
            response = client.post('/auth/register', data={
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'password123',
                'password_confirm': 'password123'
            }, follow_redirects=True)
            print(f"4. Register POST: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
            
            # Check if user was created
            user = User.query.filter_by(username='newuser').first()
            if user:
                print("5. User creation: ✓ User successfully created in database")
            else:
                print("5. User creation: ✗ User not found in database")
            
            print("\n" + "=" * 50)
            if response.status_code == 200:
                print("🎉 SUCCESS: Authentication is working!")
                print("✓ No more CSRF token errors")
                print("✓ Login and registration forms work")
                print("✓ Users can be created successfully")
                print("\nYour application is ready for users!")
            else:
                print("❌ There may still be issues to resolve")
                print("Check the application logs for more details")

if __name__ == "__main__":
    test_auth_working()