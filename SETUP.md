# SOAJS Python Setup Guide

This guide will help you set up the SOAJS Python repository for development or to move it to a separate repository.

## Project Structure

```
soajs.python/
├── soajs/                      # Main package
│   ├── __init__.py            # Package initialization
│   ├── config.py              # Configuration validation
│   ├── exceptions.py          # Custom exceptions
│   ├── middleware.py          # ASGI/WSGI middleware
│   ├── models.py              # Pydantic data models
│   ├── registry.py            # Registry manager
│   └── registry_client.py     # HTTP client
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_config.py
│   └── test_registry.py
├── examples/                   # Example applications
│   ├── fastapi_example.py
│   └── flask_example.py
├── .github/
│   └── workflows/
│       └── test.yml           # CI/CD pipeline
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── README.md
├── pyproject.toml             # Package configuration
├── requirements.txt           # Core dependencies
├── requirements-dev.txt       # Dev dependencies
└── SETUP.md                   # This file
```

## Moving to Separate Repository

### Option 1: Create New Repository

```bash
# Navigate to the directory
cd /opt/soajs/node_modules/soajs.python

# Initialize git (if not already initialized)
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: SOAJS Python implementation"

# Add remote repository
git remote add origin https://github.com/soajs/soajs.python.git

# Push to remote
git push -u origin main
```

### Option 2: Copy to New Location

```bash
# Copy the entire directory
cp -r /opt/soajs/node_modules/soajs.python /path/to/new/location/

# Navigate to new location
cd /path/to/new/location/soajs.python

# Initialize git
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/soajs/soajs.python.git
git push -u origin main
```

## Local Development Setup

### Prerequisites

- Python 3.9 or higher
- pip
- virtualenv (recommended)

### Installation Steps

1. **Create and activate virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install in development mode:**

```bash
# Install with all dependencies
pip install -e .[dev,fastapi,flask]

# Or use make
make install-dev
```

3. **Set environment variables:**

```bash
export SOAJS_REGISTRY_API="localhost:5000"
export SOAJS_ENV="dev"
export SOAJS_DEPLOY_MANUAL="false"
```

4. **Verify installation:**

```bash
# Run tests
pytest

# Check code quality
make lint
```

## Running Examples

### FastAPI Example

```bash
# Install FastAPI dependencies
pip install fastapi uvicorn

# Run the example
python examples/fastapi_example.py

# Or with uvicorn directly
uvicorn examples.fastapi_example:app --reload
```

### Flask Example

```bash
# Install Flask
pip install flask

# Run the example
python examples/flask_example.py
```

## Publishing to PyPI

### Prerequisites

- PyPI account
- Twine installed (`pip install twine`)

### Steps

1. **Update version in pyproject.toml:**

```toml
[project]
version = "1.0.0"  # Increment version
```

2. **Build distribution:**

```bash
make build
# Or manually:
python -m build
```

3. **Upload to PyPI:**

```bash
make publish
# Or manually:
python -m twine upload dist/*
```

4. **Test installation:**

```bash
pip install soajs-python
```

## Environment Variables

The following environment variables are required:

| Variable | Description | Example |
|----------|-------------|---------|
| `SOAJS_REGISTRY_API` | Registry gateway address | `localhost:5000` |
| `SOAJS_ENV` | Environment name | `dev`, `prod` |
| `SOAJS_DEPLOY_MANUAL` | Manual deployment flag | `true`, `false` |

## Testing

### Run All Tests

```bash
make test
```

### Run with Coverage

```bash
make test-cov
```

### Run Specific Tests

```bash
pytest tests/test_registry.py
pytest tests/test_config.py::test_valid_config
```

## Code Quality

### Linting

```bash
# Run all linters
make lint

# Individual tools
ruff check soajs tests
mypy soajs
```

### Formatting

```bash
# Format all code
make format

# Individual tools
black soajs tests examples
ruff check --fix soajs tests
```

## Continuous Integration

The project includes GitHub Actions workflow for CI/CD:

- **Runs on:** Python 3.9, 3.10, 3.11, 3.12
- **Steps:**
  1. Checkout code
  2. Install dependencies
  3. Run linters (ruff, mypy)
  4. Run tests with coverage
  5. Upload coverage to Codecov

## Project Status

✅ **Complete Features:**
- Core models with Pydantic
- Registry management with auto-reload
- Thread-safe operations
- ASGI middleware (FastAPI, Starlette)
- WSGI middleware (Flask, Django)
- Service discovery and Connect
- Comprehensive tests
- Examples for FastAPI and Flask
- Full documentation

## Next Steps

1. **Test with Real Registry:**
   - Set up SOAJS gateway
   - Test against live registry
   - Validate all operations

2. **Add More Examples:**
   - Django example
   - Async service calls
   - Database integration

3. **Performance Testing:**
   - Benchmark registry reload
   - Test concurrent access
   - Optimize hot paths

4. **Documentation:**
   - API reference with Sphinx
   - Tutorial videos
   - Migration guide from Node.js

## Comparison with Go Implementation

| Feature | Go (soajs.golang) | Python (soajs.python) |
|---------|-------------------|----------------------|
| **Lines of Code** | ~800 | ~1200 |
| **Models** | Structs | Pydantic models |
| **Concurrency** | sync.RWMutex | threading.RLock |
| **HTTP Client** | net/http | httpx |
| **Validation** | Manual | Pydantic validators |
| **Middleware** | Single | ASGI + WSGI |
| **Type Safety** | Compile-time | Runtime |
| **Test Framework** | testing | pytest |

## Support

- **Documentation:** https://docs.soajs.org
- **Issues:** https://github.com/soajs/soajs.python/issues
- **Email:** team@soajs.org
- **Community:** [Join our chat]

## License

Apache 2.0 License - See LICENSE file for details
