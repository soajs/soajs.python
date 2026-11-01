"""Tests for GET /mcp/tools and the request context helper."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from flask import Flask

from soajs.config import Config
from soajs.mcp import MCPTools, is_mcp_tools_request, load_swagger
from soajs.middleware import SOAJSMiddleware, SOAJSWSGIMiddleware, get_soajs_context
from soajs.registry import RegistryManager

SWAGGER_YAML = """swagger: "2.0"
info:
  title: demo
  version: "1.0.0"
paths:
  /hello:
    get:
      summary: Hello
"""

INJECT = json.dumps(
    {
        "tenant": {"id": "t1", "code": "TNT"},
        "key": {"iKey": "ik", "eKey": "ek", "config": {}},
        "application": {"product": "PROD", "package": "PROD_PCK"},
        "awareness": {"host": "127.0.0.1", "port": 4000},
    }
)


@pytest.fixture
def registry():
    """A registry with only what the middleware reads without a gateway header."""
    reg = SimpleNamespace(service_name="demo", service_version="2")
    reg.registry = MagicMock()
    return reg


@pytest.fixture
def in_tmp(tmp_path, monkeypatch):
    """Run from an empty folder, the way a service finds its swagger file."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# load_swagger
# ---------------------------------------------------------------------------


def test_load_yaml_file_as_text(in_tmp):
    (in_tmp / "swagger.yml").write_text(SWAGGER_YAML)
    assert load_swagger() == SWAGGER_YAML


def test_load_json_file_parsed(in_tmp):
    (in_tmp / "api.json").write_text(json.dumps({"openapi": "3.0.0", "paths": {}}))
    assert load_swagger(swagger_filename="/api.json") == {"openapi": "3.0.0", "paths": {}}


def test_load_missing_file(in_tmp):
    assert load_swagger() is None
    assert load_swagger(swagger_filename="/nope.json") is None


def test_load_invalid_json(in_tmp):
    (in_tmp / "bad.json").write_text("{not json")
    (in_tmp / "list.json").write_text("[1, 2]")
    assert load_swagger(swagger_filename="bad.json") is None
    assert load_swagger(swagger_filename="list.json") is None


def test_load_document_wins_over_file(in_tmp):
    (in_tmp / "swagger.yml").write_text(SWAGGER_YAML)
    assert load_swagger({"openapi": "3.1.0"}) == {"openapi": "3.1.0"}
    assert load_swagger(lambda: {"openapi": "3.1.0"}) == {"openapi": "3.1.0"}


def test_load_document_callable_failing_or_not_a_dict(in_tmp):
    def broken():
        raise RuntimeError("boom")

    assert load_swagger(broken) is None
    assert load_swagger(lambda: "text") is None


def test_is_mcp_tools_request():
    assert is_mcp_tools_request("GET", "/mcp/tools", False)
    assert is_mcp_tools_request("get", "/mcp/tools", False)
    assert not is_mcp_tools_request("GET", "/mcp/tools", True)
    assert not is_mcp_tools_request("POST", "/mcp/tools", False)
    assert not is_mcp_tools_request("GET", "/mcp/tools/x", False)


def test_mcp_tools_loads_once(in_tmp):
    calls = []

    def document():
        calls.append(1)
        return {"openapi": "3.0.0"}

    tools = MCPTools("demo", None, document)
    first = json.loads(tools.response_body())
    tools.response_body()
    assert calls == [1]
    assert first["result"] is True
    assert first["service"] == {"service": "DEMO", "type": "rest", "route": "/mcp/tools"}
    assert first["data"] == {"name": "demo", "version": "1", "swagger": {"openapi": "3.0.0"}}


def test_mcp_tools_without_document(in_tmp):
    body = json.loads(MCPTools("demo", "3").response_body())
    assert body["result"] is True
    assert body["data"] == {"name": "demo", "version": "3", "tools": []}


# ---------------------------------------------------------------------------
# ASGI (FastAPI)
# ---------------------------------------------------------------------------


def make_fastapi(registry, **kwargs):
    app = FastAPI(title="demo", version="1.0.0")

    @app.get("/hello", summary="Hello")
    async def hello(request: Request):
        context = get_soajs_context(request)
        return {"tenant": context.tenant.code if context else None}

    app.add_middleware(SOAJSMiddleware, registry=registry, swagger_document=app.openapi, **kwargs)
    return app


def test_asgi_mcp_tools_serves_fastapi_openapi(registry):
    app = make_fastapi(registry)
    client = TestClient(app)
    response = client.get("/mcp/tools")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    body = response.json()
    assert body["data"]["name"] == "demo"
    assert body["data"]["version"] == "2"
    assert body["data"]["swagger"]["paths"]["/hello"]["get"]["summary"] == "Hello"


def test_asgi_mcp_tools_through_gateway_goes_to_app(registry):
    client = TestClient(make_fastapi(registry))
    response = client.get("/mcp/tools", headers={"soajsinjectobj": INJECT})
    assert response.status_code == 404


def test_asgi_mcp_tools_other_method_goes_to_app(registry):
    client = TestClient(make_fastapi(registry))
    assert client.post("/mcp/tools").status_code == 404


def test_get_soajs_context_reads_the_scope():
    context = object()
    request = SimpleNamespace(scope={"type": "http", "soajs": context})
    assert get_soajs_context(request) is context
    assert get_soajs_context(SimpleNamespace(scope={"type": "http"})) is None


def test_get_soajs_context_without_scope():
    assert get_soajs_context(object()) is None


# ---------------------------------------------------------------------------
# WSGI (Flask)
# ---------------------------------------------------------------------------


def make_flask(registry, **kwargs):
    app = Flask("demo")

    @app.route("/hello")
    def hello():
        return {"ok": True}

    app.wsgi_app = SOAJSWSGIMiddleware(app.wsgi_app, registry, **kwargs)
    return app


def test_wsgi_mcp_tools_serves_the_file(registry, in_tmp):
    (in_tmp / "swagger.yml").write_text(SWAGGER_YAML)
    client = make_flask(registry).test_client()
    response = client.get("/mcp/tools")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.get_json()["data"] == {"name": "demo", "version": "2", "swagger": SWAGGER_YAML}


def test_wsgi_mcp_tools_without_file(registry, in_tmp):
    client = make_flask(registry).test_client()
    assert client.get("/mcp/tools").get_json()["data"]["tools"] == []


def test_wsgi_mcp_tools_through_gateway_goes_to_app(registry, in_tmp):
    client = make_flask(registry).test_client()
    assert client.get("/mcp/tools", headers={"soajsinjectobj": INJECT}).status_code == 404
    assert client.get("/hello").get_json() == {"ok": True}


# ---------------------------------------------------------------------------
# Manual deployment registration
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client():
    with patch("soajs.registry.RegistryClient") as mock:
        client = mock.return_value
        client.get_registry.return_value = {
            "name": "test",
            "environment": "dev",
            "timeLoaded": 0,
            "serviceConfig": {"awareness": {"autoReloadRegistry": 0}},
        }
        client.register_service.return_value = {"result": True}
        yield client


def register_with(config):
    with patch.dict("os.environ", {"SOAJS_DEPLOY_MANUAL": "true"}):
        RegistryManager(
            "demo",
            "dev",
            "service",
            auto_reload=False,
            service_port=8000,
            service_group="group",
            service_version="1",
            config=config,
        )


def test_register_sends_camel_case_fields_from_config(mock_client):
    config = Config(
        name="demo",
        group="group",
        port=8000,
        type="service",
        version="1",
        oauth=True,
        extKeyRequired=True,
        urac_Profile=True,
        requestTimeout=30,
        maintenance={"port": {"type": "inherit"}, "readiness": "/heartbeat"},
        interConnect=[{"name": "urac", "version": "3"}],
    )
    register_with(config)
    payload = mock_client.register_service.call_args[0][0]
    assert payload["mw"] is True
    assert payload["oauth"] is True
    assert payload["extKeyRequired"] is True
    assert payload["urac_Profile"] is True
    assert payload["requestTimeout"] == 30
    assert payload["maintenance"] == {"port": {"type": "inherit"}, "readiness": "/heartbeat"}
    assert payload["interConnect"] == [{"name": "urac", "version": "3"}]
    assert "subType" not in payload
    json.dumps(payload)


def test_register_sends_fields_from_a_dict(mock_client):
    register_with({"oauth": True, "subType": "ecommerce", "description": None})
    payload = mock_client.register_service.call_args[0][0]
    assert payload["oauth"] is True
    assert payload["subType"] == "ecommerce"
    assert "description" not in payload
