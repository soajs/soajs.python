"""Registry management with thread-safe access and auto-reload."""

from __future__ import annotations

import os
import threading
from typing import Any, Optional

from .exceptions import (
    DatabaseNotFoundError,
    RegistryError,
    ResourceNotFoundError,
    ServiceNotFoundError,
)
from .models import Database, Registry, Resource, Service
from .registry_client import RegistryClient


class RegistryManager:
    """Thread-safe registry manager with auto-reload support."""

    def __init__(
        self,
        service_name: str,
        env_code: str,
        service_type: str,
        auto_reload: bool = True,
        service_port: Optional[int] = None,
        service_ip: Optional[str] = None,
        service_group: Optional[str] = None,
        service_version: Optional[str] = None,
        config: Optional[Any] = None,
    ):
        """
        Initialize registry manager.

        Args:
            service_name: Name of the service
            env_code: Environment code
            service_type: Type of service (e.g., "service", "daemon")
            auto_reload: Enable automatic registry reload
            service_port: Service port for manual deployment registration
            service_ip: Service IP address for manual deployment registration
            service_group: Service group for manual deployment registration
            service_version: Service version for manual deployment registration
            config: Full service configuration object for manual deployment
        """
        self.service_name = service_name
        self.env_code = env_code
        self.service_type = service_type
        self.service_port = service_port
        self.service_ip = service_ip
        self.service_group = service_group
        self.service_version = service_version
        self.config = config

        self._lock = threading.RLock()
        self._registry: Optional[Registry] = None
        self._client = RegistryClient()
        self._stop_reload = threading.Event()
        self._reload_thread: Optional[threading.Thread] = None

        # Initial load
        self.reload()

        # Handle manual deployment registration
        self._handle_manual_deployment()

        # Start auto-reload if requested
        if auto_reload:
            self._start_auto_reload()

    def _handle_manual_deployment(self) -> None:
        """
        Handle manual deployment service registration.

        Reads SOAJS_DEPLOY_MANUAL environment variable and registers the service
        if set to "true". This matches the behavior of the Go implementation.

        Raises:
            RegistryError: If manual deployment is enabled but registration fails
        """
        deploy_manual_str = os.getenv("SOAJS_DEPLOY_MANUAL", "false")

        # Parse boolean value (case-insensitive)
        deploy_manual = deploy_manual_str.lower() in ("true", "1", "yes")

        if not deploy_manual:
            return

        # Build registration configuration
        service_ip = self.service_ip or "127.0.0.1"

        if not self.service_port:
            raise RegistryError(
                "service_port is required when SOAJS_DEPLOY_MANUAL is true"
            )

        if not self.service_group:
            raise RegistryError(
                "service_group is required when SOAJS_DEPLOY_MANUAL is true"
            )

        if not self.service_version:
            raise RegistryError(
                "service_version is required when SOAJS_DEPLOY_MANUAL is true"
            )

        # Build registration payload
        register_config: dict[str, Any] = {
            "name": self.service_name,
            "group": self.service_group,
            "port": self.service_port,
            "ip": service_ip,
            "type": self.service_type,
            "version": self.service_version,
            "middleware": True,
        }

        # Add optional fields from config if provided
        if self.config:
            optional_fields = [
                "subType",
                "description",
                "oauth",
                "urac",
                "urac_Profile",
                "urac_ACL",
                "urac_Config",
                "urac_GroupConfig",
                "tenant_Profile",
                "provision_ACL",
                "requestTimeout",
                "requestTimeoutRenewal",
                "extKeyRequired",
                "maintenance",
                "interConnect",
            ]
            for field in optional_fields:
                if hasattr(self.config, field):
                    register_config[field] = getattr(self.config, field)

        # Register the service
        try:
            self._client.register_service(register_config)
        except Exception as e:
            raise RegistryError(f"Failed to register service for manual deployment: {e}") from e

    def reload(self) -> None:
        """
        Reload registry from SOAJS gateway.

        Raises:
            RegistryError: If reload fails
        """
        data = self._client.get_registry(
            self.service_name, self.env_code, self.service_type
        )

        new_registry = Registry(**data)
        new_registry.service_type = self.service_type

        with self._lock:
            self._registry = new_registry

    def _start_auto_reload(self) -> None:
        """Start background thread for automatic registry reload."""
        self._reload_thread = threading.Thread(
            target=self._auto_reload_loop, daemon=True, name="registry-auto-reload"
        )
        self._reload_thread.start()

    def _auto_reload_loop(self) -> None:
        """Background thread loop for auto-reload."""
        while not self._stop_reload.is_set():
            interval = self._get_reload_interval()
            self._stop_reload.wait(interval)

            if not self._stop_reload.is_set():
                try:
                    self.reload()
                except Exception as e:
                    # Log error but continue
                    print(f"Registry reload failed: {e}")

    def _get_reload_interval(self) -> float:
        """
        Get reload interval in seconds.

        Returns:
            Reload interval (minimum 1 second)
        """
        with self._lock:
            if not self._registry:
                return 3600.0

            awareness = self._registry.service_config.awareness
            ms = awareness.auto_reload_registry or 3600000
            seconds = ms / 1000.0

            # Ensure minimum 1 second to prevent performance issues
            return max(seconds, 1.0)

    def stop(self) -> None:
        """Stop auto-reload thread and close client."""
        self._stop_reload.set()
        if self._reload_thread and self._reload_thread.is_alive():
            self._reload_thread.join(timeout=5)
        self._client.close()

    @property
    def registry(self) -> Registry:
        """
        Get current registry with thread-safe access.

        Returns:
            Current Registry object

        Raises:
            RuntimeError: If registry is not loaded
        """
        with self._lock:
            if not self._registry:
                raise RuntimeError("Registry not loaded")
            return self._registry

    def get_database(self, name: str) -> Database:
        """
        Get database by name.

        Args:
            name: Database name

        Returns:
            Database object

        Raises:
            DatabaseNotFoundError: If database not found
        """
        with self._lock:
            reg = self.registry

            if name in reg.core_dbs:
                return reg.core_dbs[name]

            if name in reg.tenant_meta_dbs:
                return reg.tenant_meta_dbs[name]

            raise DatabaseNotFoundError(f"Database not found: {name}")

    def get_all_databases(self) -> dict[str, Database]:
        """
        Get all databases (core + tenant).

        Returns:
            Dictionary of all databases
        """
        with self._lock:
            reg = self.registry
            return {**reg.core_dbs, **reg.tenant_meta_dbs}

    def get_service(self, name: str) -> Service:
        """
        Get service by name.

        Args:
            name: Service name

        Returns:
            Service object

        Raises:
            ServiceNotFoundError: If service not found
        """
        with self._lock:
            reg = self.registry

            if name not in reg.services:
                raise ServiceNotFoundError(f"Service not found: {name}")

            return reg.services[name]

    def get_resource(self, name: str) -> Resource:
        """
        Get resource by name.

        Args:
            name: Resource name

        Returns:
            Resource object

        Raises:
            ResourceNotFoundError: If resource not found
        """
        with self._lock:
            reg = self.registry

            for resource_list in reg.resources.values():
                if name in resource_list:
                    return resource_list[name]

            raise ResourceNotFoundError(f"Resource not found: {name}")

    def __enter__(self) -> RegistryManager:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop()

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        try:
            self.stop()
        except Exception:
            pass
