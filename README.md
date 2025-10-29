# SOAJS Python Middleware

Python implementation of the SOAJS middleware for microservices architecture. Provides registry management, service discovery, and HTTP middleware for Python web frameworks.

## Features

- ✅ **Registry Management** - Thread-safe registry with auto-reload
- ✅ **Service Discovery** - Mesh networking and gateway fallback
- ✅ **Multi-Framework Support** - ASGI (FastAPI, Starlette) and WSGI (Flask, Django)
- ✅ **Type Safety** - Full type hints with Pydantic models
- ✅ **Thread-Safe** - RLock-based concurrent access
- ✅ **Auto-Reload** - Configurable automatic registry updates
- ✅ **Context Injection** - Seamless tenant and user context handling

## Installation

```bash
pip install soajs-python
```

### Optional Dependencies

```bash
# For FastAPI/Starlette support
pip install soajs-python[fastapi]

# For Flask support
pip install soajs-python[flask]

# For Django support
pip install soajs-python[django]

# For development
pip install soajs-python[dev]
```

## Quick Start

### Environment Variables

Set the required environment variables:

```bash
export SOAJS_REGISTRY_API="localhost:5000"
export SOAJS_ENV="dev"
export SOAJS_DEPLOY_MANUAL="false"
```

### FastAPI Example

```python
from fastapi import FastAPI, Request
from soajs import RegistryManager
from soajs.middleware import SOAJSMiddleware, get_soajs_context

# Initialize registry
registry = RegistryManager(
    service_name="my-service",
    env_code="dev",
    service_type="service"
)

# Create app and add middleware
app = FastAPI()
app.add_middleware(SOAJSMiddleware, registry=registry)

@app.get("/")
async def handler(request: Request):
    context = get_soajs_context(request)
    if context:
        return {"tenant": context.tenant.code}
    return {"error": "No context"}
```

### Flask Example

```python
from flask import Flask, request, jsonify
from soajs import RegistryManager
from soajs.middleware import SOAJSWSGIMiddleware

# Initialize registry
registry = RegistryManager(
    service_name="my-service",
    env_code="dev",
    service_type="service"
)

# Create app and add middleware
app = Flask(__name__)
app.wsgi_app = SOAJSWSGIMiddleware(app.wsgi_app, registry)

@app.route("/")
def handler():
    context = request.environ.get("soajs.context")
    if context:
        return jsonify({"tenant": context.tenant.code})
    return jsonify({"error": "No context"})
```

## Core Components

### Registry Manager

Thread-safe registry management with automatic reload:

```python
from soajs import RegistryManager

# Initialize with auto-reload
registry = RegistryManager(
    service_name="my-service",
    env_code="dev",
    service_type="service",
    auto_reload=True  # Automatically reload from gateway
)

# Access registry data
db = registry.get_database("main")
service = registry.get_service("auth-service")
all_dbs = registry.get_all_databases()

# Manual reload
registry.reload()

# Cleanup
registry.stop()
```

### Service Discovery

Connect to other services in the mesh:

```python
from soajs.middleware import ServiceConnector

# Get SOAJS context from request
context = get_soajs_context(request)

# Create connector
connector = ServiceConnector(context)

# Connect to service (mesh or gateway)
connection = connector.connect("auth-service", version="1")

# Use connection info for HTTP request
import httpx
response = httpx.get(
    f"http://{connection.host}/endpoint",
    headers=connection.headers
)
```

### Configuration Validation

Validate service configuration:

```python
from soajs import Config

config = Config(
    name="my-service",
    group="my-group",
    port=4000,
    version="1.0",
    type="service",
    maintenance={
        "port": {"type": "inherit"},
        "readiness": "/heartbeat"
    }
)
```

## Data Models

All data structures use Pydantic for validation:

```python
from soajs.models import (
    Registry,
    Database,
    ServiceConfig,
    ContextData,
    Tenant,
    Urac
)

# Models provide type safety and validation
tenant: Tenant = context.tenant
database: Database = registry.get_database("main")
```

## Testing

Run tests with pytest:

```bash
# Install dev dependencies
pip install -e .[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=soajs --cov-report=html
```

## Architecture

### Thread Safety

The registry manager uses `threading.RLock` for thread-safe access:

- **Write Lock**: Acquired during `reload()` to update registry
- **Read Lock**: Acquired during data access (`get_database()`, etc.)
- **Minimum Reload Interval**: 1 second to prevent performance issues

### Middleware Flow

1. **Request arrives** with `soajsinjectobj` header
2. **Middleware extracts** context data
3. **Context injected** into request (ASGI scope or WSGI environ)
4. **Handler accesses** context via helper functions
5. **Response sent** with any added headers

### Service Discovery

Two modes of service-to-service communication:

1. **Mesh Mode** (Direct): Service found in InterConnect list
   - Direct connection to service host:port
   - Full SOAJS context forwarded via headers

2. **Gateway Mode** (Fallback): Service not in mesh
   - Route through gateway
   - Only API key passed in headers

## Comparison with Go Implementation

| Feature | Go | Python |
|---------|-----|--------|
| Type System | Compile-time structs | Runtime Pydantic models |
| Concurrency | sync.RWMutex | threading.RLock |
| HTTP Client | net/http | httpx |
| Validation | Manual | Pydantic validators |
| Middleware | Single handler | ASGI + WSGI |

## Examples

See the `examples/` directory for complete examples:

- `fastapi_example.py` - FastAPI integration
- `flask_example.py` - Flask integration

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

Copyright (c) SOAJS

## Support

- Documentation: https://wwww.soajs.org
- Issues: https://github.com/soajs/soajs.python/issues
- Email: team@soajs.org
