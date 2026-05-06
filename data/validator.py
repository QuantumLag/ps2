"""Custom exception classes and validation logic for data ingestion."""

class DataValidationError(Exception):
    """Base exception for data validation errors."""
    pass

class MissingDataError(DataValidationError):
    """Raised when a required file or column is missing."""
    pass

class InvalidValueError(DataValidationError):
    """Raised when a data field contains an invalid value or malformed type."""
    pass