"""
SOAJS Python Middleware

A Python implementation of the SOAJS middleware for microservices architecture.
Provides registry management, service discovery, and HTTP middleware for Python web frameworks.
"""

from .registry import RegistryManager
from .models import (
    Registry,
    Database,
    ServiceConfig,
    ContextData,
    Tenant,
    Urac,
)
from .config import Config
from .exceptions import (
    RegistryError,
    ConfigValidationError,
    ServiceNotFoundError,
)

__version__ = "1.0.0"
__all__ = [
    "RegistryManager",
    "Registry",
    "Database",
    "ServiceConfig",
    "ContextData",
    "Tenant",
    "Urac",
    "Config",
    "RegistryError",
    "ConfigValidationError",
    "ServiceNotFoundError",
]
