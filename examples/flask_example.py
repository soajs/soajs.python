"""
Flask example with SOAJS middleware.

This example demonstrates how to integrate SOAJS middleware with Flask.
"""

from flask import Flask, request, jsonify
from soajs import RegistryManager, CustomNotFoundError
from soajs.middleware import SOAJSWSGIMiddleware, ServiceConnector

# Initialize registry manager
# For manual deployment (SOAJS_DEPLOY_MANUAL=true), also provide:
# - service_port, service_group, service_version
registry = RegistryManager(
    service_name="my-flask-service",
    env_code="dev",
    service_type="service",
    auto_reload=True,
    # Required for manual deployment registration (when SOAJS_DEPLOY_MANUAL=true)
    service_port=5000,
    service_group="my-group",
    service_version="1.0.0",
    service_ip="127.0.0.1",  # Optional, defaults to 127.0.0.1
)

# Create Flask app
app = Flask(__name__)

# Add SOAJS middleware
app.wsgi_app = SOAJSWSGIMiddleware(app.wsgi_app, registry)


def get_soajs_context():
    """Helper to get SOAJS context from Flask request."""
    return request.environ.get("soajs.context")


@app.route("/")
def root():
    """Root endpoint."""
    return jsonify({"message": "SOAJS Flask Example", "version": "1.0.0"})


@app.route("/tenant-info")
def get_tenant_info():
    """
    Get tenant information from SOAJS context.

    This endpoint demonstrates how to access SOAJS context data.
    """
    context = get_soajs_context()

    if not context:
        return jsonify({"error": "No SOAJS context available"}), 400

    return jsonify(
        {
            "tenant_id": context.tenant.id,
            "tenant_code": context.tenant.code,
            "environment": context.registry.environment if context.registry else None,
            "device": context.device,
        }
    )


@app.route("/database-info")
def get_database_info():
    """
    Get database configuration from registry.

    This demonstrates accessing database configuration via the registry.
    """
    try:
        # Get database from registry
        db = registry.get_database("main")

        return jsonify(
            {
                "database": db.name,
                "cluster": db.cluster,
                "servers": [
                    {"host": server.host, "port": server.port} for server in db.servers
                ],
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/services")
def list_services():
    """
    List all available services from registry.

    This demonstrates accessing service information from the registry.
    """
    try:
        services = registry.registry.services
        return jsonify(
            {
                "services": {
                    name: {"group": service.group, "port": service.port}
                    for name, service in services.items()
                }
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/custom-config")
def get_custom_config():
    """
    Get custom registry configuration.

    This demonstrates accessing custom registry data that can be used
    for application-specific configuration.

    Query params:
        name: Optional name of specific custom registry to retrieve
    """
    name = request.args.get("name")

    try:
        if name:
            # Get specific custom registry
            custom = registry.get_custom(name)
            return jsonify(
                {
                    "name": name,
                    "custom": custom,
                }
            )
        else:
            # Get all custom registries
            all_customs = registry.get_custom()
            return jsonify(
                {
                    "count": len(all_customs),
                    "customs": all_customs,
                }
            )
    except CustomNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/call-service", methods=["POST"])
def call_service():
    """
    Demonstrate service-to-service communication.

    This shows how to use ServiceConnector to call other services in the mesh.
    """
    context = get_soajs_context()

    if not context:
        return jsonify({"error": "No SOAJS context available"}), 400

    data = request.get_json() or {}
    service_name = data.get("service_name")
    version = data.get("version")

    if not service_name:
        return jsonify({"error": "service_name is required"}), 400

    # Create service connector
    connector = ServiceConnector(context)

    # Get connection information for the target service
    connection = connector.connect(service_name, version)

    return jsonify(
        {
            "target_service": service_name,
            "target_version": version or "latest",
            "connection_host": connection.host,
            "headers": list(connection.headers.keys()),
        }
    )


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@app.teardown_appcontext
def cleanup(error=None):
    """Cleanup on app context teardown."""
    if error:
        print(f"Error during request: {error}")


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        registry.stop()
