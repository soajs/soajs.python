"""
FastAPI example with SOAJS middleware.

This example demonstrates how to integrate SOAJS middleware with FastAPI.
"""

from fastapi import FastAPI, Request
from soajs import RegistryManager
from soajs.middleware import SOAJSMiddleware, get_soajs_context, ServiceConnector

# Initialize registry manager
# These values would typically come from environment variables or config
# For manual deployment (SOAJS_DEPLOY_MANUAL=true), also provide:
# - service_port, service_group, service_version
registry = RegistryManager(
    service_name="my-fastapi-service",
    env_code="dev",
    service_type="service",
    auto_reload=True,
    # Required for manual deployment registration (when SOAJS_DEPLOY_MANUAL=true)
    service_port=8000,
    service_group="my-group",
    service_version="1.0.0",
    service_ip="127.0.0.1",  # Optional, defaults to 127.0.0.1
)

# Create FastAPI app
app = FastAPI(title="SOAJS FastAPI Example")

# Add SOAJS middleware
app.add_middleware(SOAJSMiddleware, registry=registry)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "SOAJS FastAPI Example", "version": "1.0.0"}


@app.get("/tenant-info")
async def get_tenant_info(request: Request):
    """
    Get tenant information from SOAJS context.

    This endpoint demonstrates how to access SOAJS context data.
    """
    context = get_soajs_context(request)

    if not context:
        return {"error": "No SOAJS context available"}

    return {
        "tenant_id": context.tenant.id,
        "tenant_code": context.tenant.code,
        "environment": context.registry.environment if context.registry else None,
        "device": context.device,
    }


@app.get("/database-info")
async def get_database_info(request: Request):
    """
    Get database configuration from registry.

    This demonstrates accessing database configuration via the registry.
    """
    try:
        # Get database from registry
        db = registry.get_database("main")

        return {
            "database": db.name,
            "cluster": db.cluster,
            "servers": [
                {"host": server.host, "port": server.port} for server in db.servers
            ],
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/services")
async def list_services():
    """
    List all available services from registry.

    This demonstrates accessing service information from the registry.
    """
    try:
        services = registry.registry.services
        return {
            "services": {
                name: {"group": service.group, "port": service.port}
                for name, service in services.items()
            }
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/call-service")
async def call_service(request: Request, service_name: str, version: str = None):
    """
    Demonstrate service-to-service communication.

    This shows how to use ServiceConnector to call other services in the mesh.
    """
    context = get_soajs_context(request)

    if not context:
        return {"error": "No SOAJS context available"}

    # Create service connector
    connector = ServiceConnector(context)

    # Get connection information for the target service
    connection = connector.connect(service_name, version)

    return {
        "target_service": service_name,
        "target_version": version or "latest",
        "connection_host": connection.host,
        "headers": list(connection.headers.keys()),
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    registry.stop()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
