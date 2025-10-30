"""Custom exceptions for SOAJS Python middleware."""


class SOAJSError(Exception):
    """Base exception for SOAJS errors."""
    pass


class RegistryError(SOAJSError):
    """Raised when registry operations fail."""
    pass


class ConfigValidationError(SOAJSError):
    """Raised when configuration validation fails."""
    pass


class ServiceNotFoundError(SOAJSError):
    """Raised when a requested service is not found."""
    pass


class DatabaseNotFoundError(SOAJSError):
    """Raised when a requested database is not found."""
    pass


class ResourceNotFoundError(SOAJSError):
    """Raised when a requested resource is not found."""
    pass


class CustomNotFoundError(SOAJSError):
    """Raised when a requested custom registry is not found."""
    pass
