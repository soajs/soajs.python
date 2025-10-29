"""Tests for configuration validation."""

import pytest
from pydantic import ValidationError
from soajs.config import Config, Maintenance, MaintenancePort
from soajs.exceptions import ConfigValidationError


def test_valid_config():
    """Test valid configuration."""
    config_data = {
        "name": "test-service",
        "group": "test-group",
        "port": 4000,
        "version": "1.0",
        "type": "service",
        "maintenance": {
            "port": {"type": "inherit"},
            "readiness": "/heartbeat",
        },
    }
    config = Config(**config_data)
    assert config.service_name == "test-service"
    assert config.service_port == 4000
    assert config.service_version == "1.0"


def test_invalid_service_name():
    """Test invalid service name format."""
    config_data = {
        "name": "test service",  # Space not allowed
        "group": "test-group",
        "port": 4000,
        "version": "1.0",
        "type": "service",
        "maintenance": {
            "port": {"type": "inherit"},
            "readiness": "/heartbeat",
        },
    }
    with pytest.raises(ConfigValidationError):
        Config(**config_data)


def test_invalid_version_format():
    """Test invalid version format."""
    config_data = {
        "name": "test-service",
        "group": "test-group",
        "port": 4000,
        "version": "v1.0",  # 'v' prefix not allowed
        "type": "service",
        "maintenance": {
            "port": {"type": "inherit"},
            "readiness": "/heartbeat",
        },
    }
    with pytest.raises(ConfigValidationError):
        Config(**config_data)


def test_invalid_port():
    """Test invalid port number."""
    config_data = {
        "name": "test-service",
        "group": "test-group",
        "port": 0,  # Must be positive
        "version": "1.0",
        "type": "service",
        "maintenance": {
            "port": {"type": "inherit"},
            "readiness": "/heartbeat",
        },
    }
    with pytest.raises(ValidationError):
        Config(**config_data)


def test_missing_required_fields():
    """Test missing required fields."""
    config_data = {
        "name": "test-service",
        # Missing group, port, version, type, maintenance
    }
    with pytest.raises(ValidationError):
        Config(**config_data)


def test_valid_version_formats():
    """Test various valid version formats."""
    valid_versions = ["1", "1.0", "2.5", "10.99"]

    for version in valid_versions:
        config_data = {
            "name": "test-service",
            "group": "test-group",
            "port": 4000,
            "version": version,
            "type": "service",
            "maintenance": {
                "port": {"type": "inherit"},
                "readiness": "/heartbeat",
            },
        }
        config = Config(**config_data)
        assert config.service_version == version
