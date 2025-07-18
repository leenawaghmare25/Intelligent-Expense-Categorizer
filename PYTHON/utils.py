"""Utility functions for the Smart Expense Categorizer."""

import logging
import functools
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from flask import current_app, request
from PYTHON.exceptions import ValidationError

def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Set up a logger with proper formatting.
    
    Args:
        name: Logger name
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def log_execution_time(func):
    """Decorator to log function execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger = logging.getLogger(func.__module__)
        logger.info(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        
        return result
    return wrapper

def validate_expense_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate expense data input.
    
    Args:
        data: Raw expense data
    
    Returns:
        Validated and cleaned data
    
    Raises:
        ValidationError: If data is invalid
    """
    if not isinstance(data, dict):
        raise ValidationError("Expense data must be a dictionary")
    
    # Required fields
    required_fields = ['description']
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValidationError(f"Missing required field: {field}")
    
    # Clean and validate description
    description = str(data['description']).strip()
    if len(description) < 3:
        raise ValidationError("Description must be at least 3 characters long")
    if len(description) > 500:
        raise ValidationError("Description must be less than 500 characters")
    
    # Validate amount if provided
    amount = data.get('amount')
    if amount is not None:
        try:
            amount = float(amount)
            if amount < 0:
                raise ValidationError("Amount cannot be negative")
            if amount > 1000000:  # 1 million limit
                raise ValidationError("Amount exceeds maximum limit")
        except (ValueError, TypeError):
            raise ValidationError("Amount must be a valid number")
    
    return {
        'description': description,
        'amount': amount,
        'date': data.get('date', datetime.utcnow())
    }

def sanitize_input(text: str, max_length: int = 500) -> str:
    """
    Sanitize text input by removing potentially harmful content.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove potentially harmful characters (basic sanitization)
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text

def format_currency(amount: Optional[float], currency: str = 'USD') -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
        currency: Currency code
    
    Returns:
        Formatted currency string
    """
    if amount is None:
        return 'N/A'
    
    if currency == 'USD':
        return f"${amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"

def get_client_ip() -> str:
    """
    Get client IP address from request.
    
    Returns:
        Client IP address
    """
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']

def paginate_query(query, page: int, per_page: int, max_per_page: int = 100):
    """
    Paginate a SQLAlchemy query with validation.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        per_page: Items per page
        max_per_page: Maximum items per page
    
    Returns:
        Paginated query result
    """
    # Validate pagination parameters
    page = max(1, int(page))
    per_page = min(max_per_page, max(1, int(per_page)))
    
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def calculate_confidence_color(confidence: float) -> str:
    """
    Get Bootstrap color class based on confidence score.
    
    Args:
        confidence: Confidence score (0-1)
    
    Returns:
        Bootstrap color class
    """
    if confidence >= 0.8:
        return 'success'
    elif confidence >= 0.6:
        return 'warning'
    else:
        return 'danger'

def get_category_icon(category: str) -> str:
    """
    Get Font Awesome icon for expense category.
    
    Args:
        category: Expense category
    
    Returns:
        Font Awesome icon class
    """
    icons = {
        'Dining Out': 'fas fa-utensils',
        'Transport': 'fas fa-car',
        'Utilities': 'fas fa-bolt',
        'Groceries': 'fas fa-shopping-cart',
        'Entertainment': 'fas fa-film',
        'Shopping': 'fas fa-shopping-bag',
        'Healthcare': 'fas fa-heartbeat',
        'Education': 'fas fa-graduation-cap',
        'Salary': 'fas fa-money-bill-wave',
        'Other': 'fas fa-question-circle'
    }
    return icons.get(category, 'fas fa-question-circle')

def create_audit_log(user_id: int, action: str, details: Dict[str, Any]) -> None:
    """
    Create an audit log entry.
    
    Args:
        user_id: User ID performing the action
        action: Action performed
        details: Additional details
    """
    logger = logging.getLogger('audit')
    logger.info(f"User {user_id} performed {action}: {details}")

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely load JSON string with fallback.
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
    
    Returns:
        Parsed JSON or default value
    """
    try:
        import json
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default