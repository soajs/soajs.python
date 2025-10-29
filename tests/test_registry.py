"""Tests for registry management."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from soajs.registry import RegistryManager
from soajs.registry_client import RegistryClient
from soajs.exceptions import (
    RegistryError,
    DatabaseNotFoundError,
    ServiceNotFoundError,
    ResourceNotFoundError,
)


@pytest.fixture
def mock_registry_data():
    """Mock registry data."""
    return {
        "timeLoaded": 1234567890,
        "name": "test-service",
        "environment": "dev",
        "coreDB": {
            "main": {
                "name": "main",
                "cluster": "cluster1",
                "servers": [{"host": "localhost", "port": 27017}],
            }
        },
        "tenantMetaDB": {},
        "serviceConfig": {
            "awareness": {
                "autoReloadRegistry": 5000,
            }
        },
        "custom": {},
        "resources": {},
        "services": {
            "auth": {"group": "auth-group", "port": 4001}
        },
    }


@pytest.fixture
def mock_client(mock_registry_data):
    """Mock registry client."""
    with patch("soajs.registry.RegistryClient") as mock:
        instance = mock.return_value
        instance.get_registry.return_value = mock_registry_data
        yield instance


def test_registry_manager_initialization(mock_client):
    """Test registry manager initialization."""
    manager = RegistryManager("test-service", "dev", "service", auto_reload=False)

    assert manager.service_name == "test-service"
    assert manager.env_code == "dev"
    assert manager.service_type == "service"
    assert manager.registry.name == "test-service"


def test_registry_reload(mock_client, mock_registry_data):
    """Test registry reload."""
    manager = RegistryManager("test-service", "dev", "service", auto_reload=False)

    # Modify mock data
    new_data = mock_registry_data.copy()
    new_data["name"] = "updated-service"
    mock_client.get_registry.return_value = new_data

    manager.reload()
    assert manager.registry.name == "updated-service"


def test_get_database_success(mock_client):
    """Test successful database retrieval."""
    manager = RegistryManager("test-service", "dev", "service", auto_reload=False)

    db = manager.get_database("main")
    assert db.name == "main"
    assert db.cluster == "cluster1"


def test_get_database_not_found(mock_client):
    """Test database not found error."""
    manager = RegistryManager("test-service", "dev", "service", auto_reload=False)

    with pytest.raises(DatabaseNotFoundError):
        manager.get_database("nonexistent")


def test_get_all_databases(mock_client):
    """Test get all databases."""
    manager = RegistryManager("test-service", "dev", "service", auto_reload=False)

    dbs = manager.get_all_databases()
    assert "main" in dbs
    assert len(dbs) == 1


def test_get_service_success(mock_client):
    """Test successful service retrieval."""
    manager = RegistryManager("test-service", "dev", "service", auto_reload=False)

    service = manager.get_service("auth")
    assert service.group == "auth-group"
    assert service.port == 4001


def test_get_service_not_found(mock_client):
    """Test service not found error."""
    manager = RegistryManager("test-service", "dev", "service", auto_reload=False)

    with pytest.raises(ServiceNotFoundError):
        manager.get_service("nonexistent")


def test_registry_client_invalid_env_var():
    """Test registry client with invalid environment variable."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(RegistryError, match="SOAJS_REGISTRY_API"):
            RegistryClient()


def test_registry_client_invalid_format():
    """Test registry client with invalid format."""
    with patch.dict("os.environ", {"SOAJS_REGISTRY_API": "invalid"}):
        with pytest.raises(RegistryError, match="Invalid format"):
            RegistryClient()


def test_registry_client_invalid_port():
    """Test registry client with invalid port."""
    with patch.dict("os.environ", {"SOAJS_REGISTRY_API": "localhost:abc"}):
        with pytest.raises(RegistryError, match="Port must be an integer"):
            RegistryClient()


def test_registry_client_empty_port():
    """Test registry client with empty port."""
    with patch.dict("os.environ", {"SOAJS_REGISTRY_API": "localhost:"}):
        with pytest.raises(RegistryError, match="Port is empty"):
            RegistryClient()


def test_context_manager(mock_client):
    """Test context manager usage."""
    with RegistryManager("test-service", "dev", "service", auto_reload=False) as manager:
        assert manager.registry.name == "test-service"


def test_auto_reload_interval(mock_client):
    """Test auto-reload interval calculation."""
    manager = RegistryManager("test-service", "dev", "service", auto_reload=False)

    interval = manager._get_reload_interval()
    # 5000ms = 5 seconds
    assert interval == 5.0


def test_auto_reload_minimum_interval(mock_client, mock_registry_data):
    """Test auto-reload minimum interval (1 second)."""
    # Set very small reload interval
    mock_registry_data["serviceConfig"]["awareness"]["autoReloadRegistry"] = 100  # 100ms

    manager = RegistryManager("test-service", "dev", "service", auto_reload=False)
    interval = manager._get_reload_interval()

    # Should be clamped to 1 second minimum
    assert interval == 1.0
