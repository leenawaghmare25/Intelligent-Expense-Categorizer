"""
Background cleanup tasks for maintaining database hygiene.
"""

from datetime import datetime, timedelta
from PYTHON.models import db, Expense
import logging

def cleanup_old_deleted_expenses(days_old=30):
    """
    Permanently delete expenses that have been soft-deleted for more than specified days.
    
    Args:
        days_old (int): Number of days after which to permanently delete
        
    Returns:
        int: Number of expenses permanently deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    # Find expenses that were deleted more than X days ago
    old_deleted_expenses = Expense.query.filter(
        Expense.is_deleted == True,
        Expense.deleted_at < cutoff_date
    ).all()
    
    deleted_count = 0
    deleted_descriptions = []
    
    for expense in old_deleted_expenses:
        deleted_descriptions.append(f"{expense.description[:50]} (deleted {expense.deleted_at})")
        db.session.delete(expense)
        deleted_count += 1
    
    if deleted_count > 0:
        db.session.commit()
        logging.info(f"Cleanup: Permanently deleted {deleted_count} old expenses")
        for desc in deleted_descriptions:
            logging.debug(f"  - {desc}")
    
    return deleted_count

def get_cleanup_stats():
    """
    Get statistics about expenses eligible for cleanup.
    
    Returns:
        dict: Statistics about cleanup-eligible expenses
    """
    now = datetime.utcnow()
    
    # Count expenses by age
    stats = {
        'total_deleted': Expense.query.filter(Expense.is_deleted == True).count(),
        'deleted_last_7_days': Expense.query.filter(
            Expense.is_deleted == True,
            Expense.deleted_at >= now - timedelta(days=7)
        ).count(),
        'deleted_last_30_days': Expense.query.filter(
            Expense.is_deleted == True,
            Expense.deleted_at >= now - timedelta(days=30)
        ).count(),
        'eligible_for_cleanup': Expense.query.filter(
            Expense.is_deleted == True,
            Expense.deleted_at < now - timedelta(days=30)
        ).count()
    }
    
    return stats

def schedule_cleanup_task():
    """
    Schedule the cleanup task to run periodically.
    This would typically be called by a task scheduler like Celery or cron.
    """
    try:
        deleted_count = cleanup_old_deleted_expenses()
        stats = get_cleanup_stats()
        
        logging.info(f"Cleanup task completed: {deleted_count} expenses permanently deleted")
        logging.info(f"Cleanup stats: {stats}")
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'stats': stats
        }
        
    except Exception as e:
        logging.error(f"Cleanup task failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == '__main__':
    # For testing purposes
    from PYTHON.app import create_app
    
    app = create_app()
    with app.app_context():
        result = schedule_cleanup_task()
        print(f"Cleanup result: {result}")