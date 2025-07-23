#!/usr/bin/env python3
"""
CSRF Fix - Temporary solution to disable CSRF in development mode
This allows the application to work while we debug the session issues.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def disable_csrf_for_development():
    """Temporarily disable CSRF for development mode."""
    config_file = project_root / "project_config.py"
    
    # Read the current config
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Replace CSRF settings for development
    if 'WTF_CSRF_ENABLED = True' in content:
        content = content.replace(
            'WTF_CSRF_ENABLED = True',
            'WTF_CSRF_ENABLED = False  # Temporarily disabled for development'
        )
        
        # Write back the modified config
        with open(config_file, 'w') as f:
            f.write(content)
        
        print("✅ CSRF temporarily disabled for development mode")
        print("⚠️  Remember to re-enable CSRF for production!")
        return True
    else:
        print("ℹ️  CSRF is already disabled or config not found")
        return False

def enable_csrf_for_production():
    """Re-enable CSRF for production mode."""
    config_file = project_root / "project_config.py"
    
    # Read the current config
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Replace CSRF settings for production
    if 'WTF_CSRF_ENABLED = False' in content:
        content = content.replace(
            'WTF_CSRF_ENABLED = False  # Temporarily disabled for development',
            'WTF_CSRF_ENABLED = True'
        )
        
        # Write back the modified config
        with open(config_file, 'w') as f:
            f.write(content)
        
        print("✅ CSRF re-enabled for production mode")
        return True
    else:
        print("ℹ️  CSRF is already enabled or config not found")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "enable":
        enable_csrf_for_production()
    else:
        disable_csrf_for_development()
        print("\nTo re-enable CSRF later, run:")
        print("python PYTHON/csrf_fix.py enable")