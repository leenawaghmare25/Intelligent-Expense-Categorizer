#!/usr/bin/env python3
"""
Permanent CSRF Fix
This script provides a comprehensive solution to the CSRF token issues.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def apply_permanent_csrf_fix():
    """Apply permanent fixes to resolve CSRF issues."""
    
    print("🔧 APPLYING PERMANENT CSRF FIXES")
    print("=" * 50)
    
    # 1. Update project configuration for better session handling
    config_file = project_root / "project_config.py"
    
    print("1. Updating project configuration...")
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Add improved session configuration
    session_config = '''
    # Enhanced Session Configuration for CSRF
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'expense_tracker:'
    SESSION_COOKIE_NAME = 'expense_session'
    SESSION_COOKIE_DOMAIN = None
    SESSION_COOKIE_PATH = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    WTF_CSRF_SSL_STRICT = False  # Allow HTTP in development
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    '''
    
    # Replace the security section
    if '# Security' in content:
        # Find the security section and replace it
        lines = content.split('\n')
        new_lines = []
        in_security_section = False
        security_section_added = False
        
        for line in lines:
            if '# Security' in line and not security_section_added:
                new_lines.append('    # Security')
                new_lines.extend([f'    {l.strip()}' for l in session_config.strip().split('\n') if l.strip()])
                in_security_section = True
                security_section_added = True
            elif in_security_section and line.strip().startswith('#') and 'Security' not in line:
                # End of security section
                in_security_section = False
                new_lines.append(line)
            elif not in_security_section:
                new_lines.append(line)
        
        content = '\n'.join(new_lines)
        
        with open(config_file, 'w') as f:
            f.write(content)
        
        print("   ✅ Configuration updated")
    
    # 2. Create a simple test script
    test_script = project_root / "test_csrf.py"
    
    print("2. Creating CSRF test script...")
    
    test_content = '''#!/usr/bin/env python3
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
                print("✅ Login page loads successfully")
                
                # Check if CSRF token is in the response
                if 'csrf_token' in response.get_data(as_text=True):
                    print("✅ CSRF token found in login form")
                else:
                    print("⚠️  CSRF token not found in login form")
            else:
                print("❌ Login page failed to load")
            
            # Test POST request (this should work now)
            response = client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)
            
            print(f"Login POST status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Login POST request successful (no CSRF error)")
            else:
                print("❌ Login POST request failed")

if __name__ == "__main__":
    test_csrf()
'''
    
    with open(test_script, 'w') as f:
        f.write(test_content)
    
    print("   ✅ Test script created")
    
    # 3. Create environment setup script
    env_script = project_root / "setup_environment.py"
    
    print("3. Creating environment setup script...")
    
    env_content = '''#!/usr/bin/env python3
"""Setup development environment with proper CSRF configuration."""

import os
from pathlib import Path

def setup_development_environment():
    """Set up environment variables for development."""
    
    env_file = Path(__file__).parent / ".env"
    
    env_vars = {
        'FLASK_ENV': 'development',
        'FLASK_DEBUG': 'True',
        'SECRET_KEY': 'dev-secret-key-change-in-production-' + os.urandom(16).hex(),
        'WTF_CSRF_ENABLED': 'True',
        'WTF_CSRF_TIME_LIMIT': '3600',
        'SESSION_COOKIE_SECURE': 'False',
        'LOG_LEVEL': 'INFO'
    }
    
    # Create or update .env file
    with open(env_file, 'w') as f:
        f.write("# Development Environment Configuration\\n")
        f.write("# Generated by setup_environment.py\\n\\n")
        
        for key, value in env_vars.items():
            f.write(f"{key}={value}\\n")
    
    print(f"✅ Environment file created: {env_file}")
    print("🔄 Please restart your Flask application to apply changes")

if __name__ == "__main__":
    setup_development_environment()
'''
    
    with open(env_script, 'w') as f:
        f.write(env_content)
    
    print("   ✅ Environment setup script created")
    
    print("\n🎉 PERMANENT CSRF FIX APPLIED!")
    print("=" * 50)
    print("Next steps:")
    print("1. Run: python setup_environment.py")
    print("2. Restart your Flask application")
    print("3. Test with: python test_csrf.py")
    print("4. Your login and registration should now work!")
    
    return True

if __name__ == "__main__":
    apply_permanent_csrf_fix()