#!/usr/bin/env python3
"""
Database migration script to add soft delete columns to existing expenses table.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PYTHON.app import create_app
from PYTHON.models import db
from sqlalchemy import text

def migrate_soft_delete():
    """Add soft delete columns to the expenses table."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if columns already exist
            result = db.session.execute(text("PRAGMA table_info(expenses)"))
            columns = [row[1] for row in result.fetchall()]
            
            migrations_needed = []
            
            if 'is_deleted' not in columns:
                migrations_needed.append("ALTER TABLE expenses ADD COLUMN is_deleted BOOLEAN DEFAULT 0 NOT NULL")
            
            if 'deleted_at' not in columns:
                migrations_needed.append("ALTER TABLE expenses ADD COLUMN deleted_at DATETIME")
            
            if 'deleted_by' not in columns:
                migrations_needed.append("ALTER TABLE expenses ADD COLUMN deleted_by VARCHAR(36)")
            
            if migrations_needed:
                print("🔄 Running soft delete migration...")
                
                for migration in migrations_needed:
                    print(f"   Executing: {migration}")
                    db.session.execute(text(migration))
                
                # Create index for is_deleted column
                try:
                    db.session.execute(text("CREATE INDEX idx_expenses_is_deleted ON expenses(is_deleted)"))
                    print("   Created index on is_deleted column")
                except Exception as e:
                    if "already exists" not in str(e):
                        print(f"   Warning: Could not create index: {e}")
                
                db.session.commit()
                print("✅ Soft delete migration completed successfully!")
                
                # Verify the migration
                result = db.session.execute(text("SELECT COUNT(*) FROM expenses WHERE is_deleted = 0"))
                active_count = result.fetchone()[0]
                print(f"📊 Found {active_count} active expenses in the database")
                
            else:
                print("✅ Soft delete columns already exist - no migration needed")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {str(e)}")
            raise

if __name__ == '__main__':
    migrate_soft_delete()