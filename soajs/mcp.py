"""GET /mcp/tools: the service's Swagger / OpenAPI document for the SOAJS gateway.

The gateway lists a service's APIs as MCP tools, filtered by each tenant's package and each
user's ACL. A service built with this middleware describes its APIs with its Swagger 2.0 or
OpenAPI 3 document; the middleware serves it and the gateway turns it into tools.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Callable, Optional, Union

MCP_TOOLS_PATH = "/mcp/tools"
DEFAULT_SWAGGER_FILENAME = "/swagger.yml"

# a runtime alias: X | Y here would fail on Python 3.9
SwaggerDocument = Union[dict[str, Any], Callable[[], dict[str, Any]]]  # noqa: UP007


def load_swagger(
    swagger_document: Optional[SwaggerDocument] = None,
    swagger_filename: Optional[str] = None,
) -> Optional[dict[str, Any] | str]:
    """
    Load the service's Swagger / OpenAPI document.

    Args:
        swagger_document: the document, or a callable returning it (FastAPI: ``app.openapi``);
            wins over the file
        swagger_filename: file relative to the folder the service runs from
            (default /swagger.yml, the key the repositories service reads)

    Returns:
        A JSON document parsed, a YAML document as text, None when there is none
    """
    if swagger_document is not None:
        document: Any = swagger_document
        if callable(swagger_document):
            try:
                document = swagger_document()
            except Exception as e:
                print(f"Failed to build the OpenAPI document for /mcp/tools: {e}")
                return None
        return document if isinstance(document, dict) else None

    filename = swagger_filename or DEFAULT_SWAGGER_FILENAME
    path = os.path.join(os.getcwd(), filename.lstrip("/"))
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as file:
        content = file.read()
    if path.lower().endswith(".json"):
        try:
            parsed = json.loads(content)
        except ValueError:
            return None
        return parsed if isinstance(parsed, dict) else None
    return content


def is_mcp_tools_request(method: str, path: str, through_gateway: bool) -> bool:
    """
    Whether the request is the gateway asking for the tools.

    A client request to /<service>/mcp/tools comes through the gateway proxy with the
    soajsinjectobj header and goes to the app like any other request.
    """
    return method.upper() == "GET" and path == MCP_TOOLS_PATH and not through_gateway


class MCPTools:
    """Builds the GET /mcp/tools answer; the document is loaded once, on the first call."""

    def __init__(
        self,
        service_name: str,
        service_version: Optional[str] = None,
        swagger_document: Optional[SwaggerDocument] = None,
        swagger_filename: Optional[str] = None,
    ) -> None:
        self.service_name = service_name
        self.service_version = str(service_version or "1")
        self.swagger_document = swagger_document
        self.swagger_filename = swagger_filename
        self._lock = threading.Lock()
        self._loaded = False
        self._swagger: Optional[dict[str, Any] | str] = None

    def swagger(self) -> Optional[dict[str, Any] | str]:
        """The document, loaded once."""
        with self._lock:
            if not self._loaded:
                self._swagger = load_swagger(self.swagger_document, self.swagger_filename)
                self._loaded = True
            return self._swagger

    def response_body(self) -> bytes:
        """
        The JSON answer: the document in ``data.swagger``, or ``data.tools: []`` when the
        service has no document (the gateway then lists no tools for it).
        """
        data: dict[str, Any] = {
            "name": self.service_name,
            "version": self.service_version,
        }
        swagger = self.swagger()
        if swagger is not None:
            data["swagger"] = swagger
        else:
            data["tools"] = []
        body = {
            "result": True,
            "ts": int(time.time() * 1000),
            "service": {
                "service": self.service_name.upper(),
                "type": "rest",
                "route": MCP_TOOLS_PATH,
            },
            "data": data,
        }
        return json.dumps(body).encode("utf-8")
