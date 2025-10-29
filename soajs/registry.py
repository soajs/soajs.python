"""Registry management with thread-safe access and auto-reload."""

import threading
from typing import Any, Optional

from .exceptions import (
    DatabaseNotFoundError,
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
    ):
        """
        Initialize registry manager.

        Args:
            service_name: Name of the service
            env_code: Environment code
            service_type: Type of service
            auto_reload: Enable automatic registry reload
        """
        self.service_name = service_name
        self.env_code = env_code
        self.service_type = service_type

        self._lock = threading.RLock()
        self._registry: Optional[Registry] = None
        self._client = RegistryClient()
        self._stop_reload = threading.Event()
        self._reload_thread: Optional[threading.Thread] = None

        # Initial load
        self.reload()

        # Start auto-reload if requested
        if auto_reload:
            self._start_auto_reload()

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

    def __enter__(self) -> "RegistryManager":
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
