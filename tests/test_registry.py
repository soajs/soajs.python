"""Tests for registry management."""

from unittest.mock import patch

import pytest

from soajs.exceptions import (
    DatabaseNotFoundError,
    RegistryError,
    ServiceNotFoundError,
)
from soajs.registry import RegistryManager
from soajs.registry_client import RegistryClient


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


def test_manual_deployment_disabled(mock_client):
    """Test that manual deployment is skipped when SOAJS_DEPLOY_MANUAL is false."""
    with patch.dict("os.environ", {"SOAJS_DEPLOY_MANUAL": "false"}):
        RegistryManager(
            "test-service",
            "dev",
            "service",
            auto_reload=False,
            service_port=8000,
            service_group="test-group",
            service_version="1.0.0",
        )

        # Should not have called register_service
        mock_client.register_service.assert_not_called()


def test_manual_deployment_enabled(mock_client):
    """Test that manual deployment registers service when SOAJS_DEPLOY_MANUAL is true."""
    with patch.dict("os.environ", {"SOAJS_DEPLOY_MANUAL": "true"}):
        mock_client.register_service.return_value = {"result": True}

        RegistryManager(
            "test-service",
            "dev",
            "service",
            auto_reload=False,
            service_port=8000,
            service_group="test-group",
            service_version="1.0.0",
            service_ip="192.168.1.10",
        )

        # Should have called register_service with correct config
        mock_client.register_service.assert_called_once()
        call_args = mock_client.register_service.call_args[0][0]

        assert call_args["name"] == "test-service"
        assert call_args["group"] == "test-group"
        assert call_args["port"] == 8000
        assert call_args["ip"] == "192.168.1.10"
        assert call_args["type"] == "service"
        assert call_args["version"] == "1.0.0"
        assert call_args["middleware"] is True


def test_manual_deployment_default_ip(mock_client):
    """Test that manual deployment uses default IP when not specified."""
    with patch.dict("os.environ", {"SOAJS_DEPLOY_MANUAL": "true"}):
        mock_client.register_service.return_value = {"result": True}

        RegistryManager(
            "test-service",
            "dev",
            "service",
            auto_reload=False,
            service_port=8000,
            service_group="test-group",
            service_version="1.0.0",
        )

        call_args = mock_client.register_service.call_args[0][0]
        assert call_args["ip"] == "127.0.0.1"


def test_manual_deployment_missing_port(mock_client):
    """Test that manual deployment fails when port is missing."""
    with patch.dict("os.environ", {"SOAJS_DEPLOY_MANUAL": "true"}):
        with pytest.raises(RegistryError, match="service_port is required"):
            RegistryManager(
                "test-service",
                "dev",
                "service",
                auto_reload=False,
                service_group="test-group",
                service_version="1.0.0",
            )


def test_manual_deployment_missing_group(mock_client):
    """Test that manual deployment fails when group is missing."""
    with patch.dict("os.environ", {"SOAJS_DEPLOY_MANUAL": "true"}):
        with pytest.raises(RegistryError, match="service_group is required"):
            RegistryManager(
                "test-service",
                "dev",
                "service",
                auto_reload=False,
                service_port=8000,
                service_version="1.0.0",
            )


def test_manual_deployment_missing_version(mock_client):
    """Test that manual deployment fails when version is missing."""
    with patch.dict("os.environ", {"SOAJS_DEPLOY_MANUAL": "true"}):
        with pytest.raises(RegistryError, match="service_version is required"):
            RegistryManager(
                "test-service",
                "dev",
                "service",
                auto_reload=False,
                service_port=8000,
                service_group="test-group",
            )


def test_manual_deployment_boolean_variations(mock_client):
    """Test that manual deployment handles various boolean string formats."""
    mock_client.register_service.return_value = {"result": True}

    for value in ["true", "True", "TRUE", "1", "yes", "Yes"]:
        with patch.dict("os.environ", {"SOAJS_DEPLOY_MANUAL": value}):
            RegistryManager(
                "test-service",
                "dev",
                "service",
                auto_reload=False,
                service_port=8000,
                service_group="test-group",
                service_version="1.0.0",
            )
            # Each should trigger registration
            assert mock_client.register_service.called

    mock_client.register_service.reset_mock()

    for value in ["false", "False", "FALSE", "0", "no", "No"]:
        with patch.dict("os.environ", {"SOAJS_DEPLOY_MANUAL": value}):
            RegistryManager(
                "test-service",
                "dev",
                "service",
                auto_reload=False,
                service_port=8000,
                service_group="test-group",
                service_version="1.0.0",
            )
        # Should not trigger registration
        assert not mock_client.register_service.called
