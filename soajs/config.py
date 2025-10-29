"""Configuration validation for SOAJS services."""

import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .exceptions import ConfigValidationError


class MaintenancePort(BaseModel):
    """Maintenance port configuration."""
    type: str
    value: Optional[int] = None


class MaintenanceCommand(BaseModel):
    """Maintenance command configuration."""
    label: str
    path: str
    icon: str


class Maintenance(BaseModel):
    """Maintenance configuration."""
    port: MaintenancePort
    readiness: str
    commands: Optional[list[MaintenanceCommand]] = None


class InterConnectConfig(BaseModel):
    """InterConnect configuration."""
    name: str
    version: str


class Config(BaseModel):
    """SOAJS service configuration."""

    service_name: str = Field(alias="name")
    service_group: str = Field(alias="group")
    service_port: int = Field(alias="port", gt=0)
    service_ip: Optional[str] = Field(None, alias="IP")
    type: str
    service_version: str = Field(alias="version")
    sub_type: Optional[str] = Field(None, alias="subType")
    description: Optional[str] = None
    oauth: bool = False
    urac: bool = False
    urac_profile: bool = Field(False, alias="urac_Profile")
    urac_acl: bool = Field(False, alias="urac_ACL")
    urac_config: bool = Field(False, alias="urac_Config")
    urac_group_config: bool = Field(False, alias="urac_GroupConfig")
    tenant_profile: bool = Field(False, alias="tenant_Profile")
    provision_acl: bool = Field(False, alias="provision_ACL")
    ext_key_required: bool = Field(False, alias="extKeyRequired")
    request_timeout: int = Field(0, alias="requestTimeout")
    request_timeout_renewal: int = Field(0, alias="requestTimeoutRenewal")
    maintenance: Maintenance
    inter_connect: Optional[list[InterConnectConfig]] = Field(None, alias="interConnect")
    prerequisites: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("service_name", "service_group")
    @classmethod
    def validate_name_syntax(cls, v: str) -> str:
        """Validate service name and group syntax."""
        pattern = r"^(([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])?$"
        if not re.match(pattern, v):
            raise ConfigValidationError(
                f"Invalid name syntax: {v}. Must match pattern: {pattern}"
            )
        return v

    @field_validator("service_version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate service version format."""
        pattern = r"^[0-9]+(\.[0-9]+)?$"
        if not re.match(pattern, v):
            raise ConfigValidationError(
                f"Invalid version format: {v}. Must match pattern: {pattern}"
            )
        return v

    @field_validator("service_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate service port is positive."""
        if v <= 0:
            raise ConfigValidationError(f"Port must be positive, got: {v}")
        return v

    def validate_maintenance(self) -> None:
        """Additional validation for maintenance configuration."""
        if not self.maintenance.readiness:
            raise ConfigValidationError("maintenance.readiness is required")
        if not self.maintenance.port.type:
            raise ConfigValidationError("maintenance.port.type is required")
