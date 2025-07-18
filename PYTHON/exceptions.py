"""Custom exceptions for the Smart Expense Categorizer."""

class ExpenseCategoryError(Exception):
    """Base exception for expense categorization errors."""
    pass

class ModelNotFoundError(ExpenseCategoryError):
    """Raised when ML models are not found or not trained."""
    pass

class ModelTrainingError(ExpenseCategoryError):
    """Raised when model training fails."""
    pass

class InvalidExpenseDataError(ExpenseCategoryError):
    """Raised when expense data is invalid or malformed."""
    pass

class DatabaseError(ExpenseCategoryError):
    """Raised when database operations fail."""
    pass

class ValidationError(ExpenseCategoryError):
    """Raised when input validation fails."""
    pass

class ConfigurationError(ExpenseCategoryError):
    """Raised when configuration is invalid."""
    pass