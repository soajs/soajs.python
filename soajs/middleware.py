"""HTTP middleware for SOAJS - supports ASGI and WSGI frameworks."""

from __future__ import annotations

import json
from typing import Any, Optional

from .models import ConnectResponse, ContextData, Host, InterConnect, Key
from .registry import RegistryManager

# ============================================================================
# ASGI Middleware (FastAPI, Starlette, Quart)
# ============================================================================


class SOAJSMiddleware:
    """ASGI middleware for FastAPI/Starlette/Quart."""

    def __init__(self, app: Any, registry: RegistryManager) -> None:
        """
        Initialize ASGI middleware.

        Args:
            app: ASGI application
            registry: Registry manager instance
        """
        self.app = app
        self.registry = registry

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        """ASGI application callable."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract SOAJS context from headers
        headers = dict(scope.get("headers", []))
        context_data = self._extract_context(headers)

        if context_data:
            # Inject into scope
            scope["soajs"] = context_data

        await self.app(scope, receive, send)

    def _extract_context(self, headers: dict[bytes, bytes]) -> Optional[ContextData]:
        """
        Extract SOAJS context from request headers.

        Args:
            headers: Request headers

        Returns:
            ContextData if header present and valid, None otherwise
        """
        # Get header (case-insensitive)
        header_data = None
        for header_key, value in headers.items():
            if header_key.lower() == b"soajsinjectobj":
                header_data = value.decode("utf-8")
                break

        if not header_data:
            return None

        try:
            data = json.loads(header_data)

            if not data:
                return None

            # Build ContextData from header
            tenant_data = data.get("tenant", {})
            key_data = data.get("key", {})
            awareness_data = data.get("awareness", {})

            # Reconstruct Key
            key = Key(
                iKey=key_data.get("iKey"),
                eKey=key_data.get("eKey"),
                config=key_data.get("config", {}),
            )

            # Inject key into tenant
            tenant_data["key"] = key

            # Reconstruct Application
            application_data = data.get("application", {})
            package_data = data.get("package", {})
            if application_data:
                application_data["package_acl"] = package_data.get("acl", {})
                application_data["package_acl_all_env"] = package_data.get(
                    "acl_all_env", {}
                )
                tenant_data["application"] = application_data

            # Build InterConnect list
            interconnect_list = []
            for ic in awareness_data.get("interConnect", []):
                interconnect_list.append(InterConnect(**ic))

            # Build Host/Awareness
            awareness = Host(
                host=awareness_data.get("host", ""),
                port=awareness_data.get("port", 0),
                interConnect=interconnect_list,
            )

            # Build ContextData
            context = ContextData(
                tenant=tenant_data,
                urac=data.get("urac"),
                services_config=key_data.get("config", {}),
                device=data.get("device"),
                geo=data.get("geo"),
                awareness=awareness,
                registry=self.registry.registry,
            )

            return context

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Log error, continue without context
            print(f"Failed to parse SOAJS header: {e}")
            return None


def get_soajs_context(request: Any) -> Optional[ContextData]:
    """
    Helper to get SOAJS context from request (FastAPI/Starlette).

    Args:
        request: FastAPI/Starlette Request object

    Returns:
        ContextData if available, None otherwise

    Example:
        ```python
        from fastapi import Request
        from soajs.middleware import get_soajs_context

        @app.get("/")
        async def handler(request: Request):
            context = get_soajs_context(request)
            if context:
                return {"tenant": context.tenant.code}
        ```
    """
    return getattr(request.scope, "soajs", None) if hasattr(request, "scope") else None


# ============================================================================
# WSGI Middleware (Flask, Django)
# ============================================================================


class SOAJSWSGIMiddleware:
    """WSGI middleware for Flask/Django."""

    def __init__(self, app: Any, registry: RegistryManager) -> None:
        """
        Initialize WSGI middleware.

        Args:
            app: WSGI application
            registry: Registry manager instance
        """
        self.app = app
        self.registry = registry

    def __call__(self, environ: Any, start_response: Any) -> Any:
        """WSGI application callable."""
        # Extract SOAJS context from headers
        context = self._extract_context(environ)

        if context:
            # Inject into environ
            environ["soajs.context"] = context

        return self.app(environ, start_response)

    def _extract_context(self, environ: dict[str, Any]) -> Optional[ContextData]:
        """
        Extract SOAJS context from WSGI environ.

        Args:
            environ: WSGI environment

        Returns:
            ContextData if header present and valid, None otherwise
        """
        # Get header from environ (WSGI format: HTTP_HEADERNAME)
        header_data = environ.get("HTTP_SOAJSINJECTOBJ")

        if not header_data:
            return None

        try:
            data = json.loads(header_data)

            if not data:
                return None

            # Same logic as ASGI version
            tenant_data = data.get("tenant", {})
            key_data = data.get("key", {})
            awareness_data = data.get("awareness", {})

            key = Key(
                iKey=key_data.get("iKey"),
                eKey=key_data.get("eKey"),
                config=key_data.get("config", {}),
            )

            tenant_data["key"] = key

            application_data = data.get("application", {})
            package_data = data.get("package", {})
            if application_data:
                application_data["package_acl"] = package_data.get("acl", {})
                application_data["package_acl_all_env"] = package_data.get(
                    "acl_all_env", {}
                )
                tenant_data["application"] = application_data

            interconnect_list = []
            for ic in awareness_data.get("interConnect", []):
                interconnect_list.append(InterConnect(**ic))

            awareness = Host(
                host=awareness_data.get("host", ""),
                port=awareness_data.get("port", 0),
                interConnect=interconnect_list,
            )

            context = ContextData(
                tenant=tenant_data,
                urac=data.get("urac"),
                services_config=key_data.get("config", {}),
                device=data.get("device"),
                geo=data.get("geo"),
                awareness=awareness,
                registry=self.registry.registry,
            )

            return context

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Failed to parse SOAJS header: {e}")
            return None


# ============================================================================
# Service Discovery & Connect
# ============================================================================


class ServiceConnector:
    """Handle inter-service mesh connections."""

    def __init__(self, context: ContextData):
        """
        Initialize service connector.

        Args:
            context: SOAJS context data
        """
        self.context = context

    def connect(
        self, service_name: str, version: Optional[str] = None
    ) -> ConnectResponse:
        """
        Connect to another service (mesh or gateway).

        Args:
            service_name: Name of the service to connect to
            version: Optional version (defaults to latest)

        Returns:
            ConnectResponse with host and headers

        Example:
            ```python
            connector = ServiceConnector(context)
            response = connector.connect("auth-service", "1")
            # Use response.host and response.headers for HTTP request
            ```
        """
        # Try to find in InterConnect mesh for direct service-to-service communication
        found_in_mesh = False
        host = ""

        interconnect = self.context.awareness.inter_connect

        for service in interconnect:
            if service.name != service_name:
                continue

            # Match by version: either request latest version or specific version
            is_latest_match = not version and service.version == service.latest
            is_version_match = version and version == service.version

            if is_latest_match or is_version_match:
                host = f"{service.host}:{service.port}"
                found_in_mesh = True
                break

        # Service found in mesh: use direct connection with full SOAJS context
        if found_in_mesh:
            headers = {
                "soajsinjectobj": json.dumps(
                    {
                        "tenant": self.context.tenant.model_dump(by_alias=True),
                        "key": {
                            "iKey": self.context.tenant.key.i_key,
                            "eKey": self.context.tenant.key.e_key,
                            "config": self.context.services_config,
                        },
                        "application": (
                            self.context.tenant.application.model_dump(by_alias=True)
                            if self.context.tenant.application
                            else {}
                        ),
                        "package": {
                            "acl": (
                                self.context.tenant.application.package_acl
                                if self.context.tenant.application
                                else {}
                            ),
                            "acl_all_env": (
                                self.context.tenant.application.package_acl_all_env
                                if self.context.tenant.application
                                else {}
                            ),
                        },
                        "device": self.context.device,
                        "geo": self.context.geo,
                        "urac": (
                            self.context.urac.model_dump(by_alias=True)
                            if self.context.urac
                            else None
                        ),
                        "awareness": self.context.awareness.model_dump(by_alias=True),
                    }
                )
            }
            return ConnectResponse(host=host, headers=headers)

        # Service not found in mesh: fallback to gateway routing
        gateway_host = self._build_gateway_path(service_name, version)
        return ConnectResponse(
            host=gateway_host, headers={"key": self.context.tenant.key.e_key or ""}
        )

    def _build_gateway_path(self, service_name: str, version: Optional[str]) -> str:
        """
        Build gateway path for service.

        Args:
            service_name: Service name
            version: Service version

        Returns:
            Gateway path string
        """
        awareness = self.context.awareness
        host = awareness.host
        port = awareness.port

        path = f"{host}:{port}/"

        if service_name.lower() == "controller":
            path += f"{service_name}/"
            if version and version.isdigit():
                path += f"v{version}/"

        return path
