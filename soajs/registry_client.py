"""HTTP client for SOAJS registry API communication."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .exceptions import RegistryError


class RegistryClient:
    """HTTP client for communicating with SOAJS registry API."""

    def __init__(self, timeout: int = 30):
        """
        Initialize registry client.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self.base_url = self._get_registry_address()
        self.client = httpx.Client(timeout=timeout)

    def _get_registry_address(self) -> str:
        """
        Parse and validate SOAJS_REGISTRY_API environment variable.

        Returns:
            Base URL for registry API

        Raises:
            RegistryError: If environment variable is missing or invalid
        """
        registry_api = os.getenv("SOAJS_REGISTRY_API")
        if not registry_api:
            raise RegistryError("SOAJS_REGISTRY_API environment variable not set")

        if ":" not in registry_api:
            raise RegistryError(
                f"Invalid format for SOAJS_REGISTRY_API. "
                f"Got [{registry_api}], expected [hostname:port]"
            )

        parts = registry_api.rsplit(":", 1)
        if len(parts) != 2:
            raise RegistryError(f"Invalid format: {registry_api}")

        host, port = parts
        if not port:
            raise RegistryError(
                f"Port is empty in SOAJS_REGISTRY_API. "
                f"Got [{registry_api}], expected [hostname:port]"
            )

        if not port.isdigit():
            raise RegistryError(f"Port must be an integer, got {port!r}")

        return f"http://{registry_api}"

    def get_registry(
        self, service_name: str, env_code: str, service_type: str
    ) -> dict[str, Any]:
        """
        Fetch registry from SOAJS gateway.

        Args:
            service_name: Name of the service
            env_code: Environment code
            service_type: Type of service

        Returns:
            Registry data dictionary

        Raises:
            RegistryError: If request fails or returns invalid response
        """
        url = f"{self.base_url}/getRegistry"
        params = {"env": env_code, "serviceName": service_name, "type": service_type}

        try:
            response = self.client.get(url, params=params)
        except httpx.RequestError as e:
            raise RegistryError(f"Failed to fetch registry: {e}") from e

        return self._handle_response(response)

    def register_service(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Register service for manual deployment.

        Args:
            config: Service configuration dictionary

        Returns:
            Registration response data

        Raises:
            RegistryError: If registration fails
        """
        url = f"{self.base_url}/register"

        try:
            response = self.client.post(url, json=config)
        except httpx.RequestError as e:
            raise RegistryError(f"Failed to register service: {e}") from e

        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """
        Parse and validate API response.

        Args:
            response: HTTP response object

        Returns:
            Parsed response data

        Raises:
            RegistryError: If response is invalid or indicates error
        """
        if not 200 <= response.status_code < 300:
            try:
                body = response.text
            except Exception as e:
                body = f"(unable to read response body: {e})"
            raise RegistryError(f"Non 2xx status code: {response.status_code} {body}")

        try:
            data = response.json()
        except Exception as e:
            raise RegistryError(f"Failed to decode JSON response: {e}") from e

        # Check for errors in response
        errors = data.get("errors", {})
        if errors.get("details"):
            error_detail = errors["details"][0]
            raise RegistryError(
                f"Registry error: [{error_detail['code']}] {error_detail['message']}"
            )

        # Check result flag
        if not data.get("result"):
            raise RegistryError("Negative result from registry")

        result: dict[str, Any] = data.get("data", {})
        return result

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> RegistryClient:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
