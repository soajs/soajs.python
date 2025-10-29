# Contributing to SOAJS Python

Thank you for your interest in contributing to SOAJS Python! This document provides guidelines and instructions for contributing.

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/soajs/soajs.python.git
cd soajs.python
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install in editable mode with dev dependencies
pip install -e .[dev,fastapi,flask]

# Or use make
make install-dev
```

### 4. Set Environment Variables

```bash
export SOAJS_REGISTRY_API="localhost:5000"
export SOAJS_ENV="dev"
```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_registry.py

# Run specific test
pytest tests/test_registry.py::test_registry_manager_initialization
```

### Code Quality

```bash
# Run linters
make lint

# Format code
make format

# Type checking
mypy soajs
```

### Code Style

We follow these standards:

- **PEP 8** for code style
- **Black** for code formatting (line length: 88)
- **Ruff** for linting
- **Type hints** for all functions and methods
- **Docstrings** for all public APIs (Google style)

Example:

```python
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
    # Implementation
```

## Pull Request Process

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clear, concise code
- Add tests for new functionality
- Update documentation as needed
- Follow the existing code style

### 3. Run Tests and Linters

```bash
make lint
make test-cov
```

Ensure:
- All tests pass
- Coverage doesn't decrease
- No linting errors
- Type checking passes

### 4. Commit Your Changes

Use clear commit messages:

```bash
git commit -m "feat: add async registry support"
git commit -m "fix: handle nil pointer in middleware"
git commit -m "docs: update README with new examples"
```

Commit message prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `style:` - Code style changes
- `chore:` - Build/tooling changes

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear title and description
- Reference any related issues
- List of changes made
- Test results

## Testing Guidelines

### Writing Tests

```python
import pytest
from soajs import RegistryManager

def test_registry_initialization():
    """Test registry manager initialization."""
    # Arrange
    with patch("soajs.registry.RegistryClient") as mock:
        # Setup mock

        # Act
        manager = RegistryManager("test", "dev", "service")

        # Assert
        assert manager.service_name == "test"
```

### Test Coverage

- Aim for >90% coverage
- Test happy paths and error cases
- Mock external dependencies
- Use fixtures for common setup

### Running Integration Tests

Integration tests require a running SOAJS gateway:

```bash
# Skip integration tests
pytest -m "not integration"

# Run only integration tests
pytest -m integration
```

## Documentation

### Docstrings

All public functions, classes, and methods must have docstrings:

```python
class RegistryManager:
    """
    Thread-safe registry manager with auto-reload support.

    This class manages SOAJS registry data with automatic
    periodic reloading from the gateway.

    Example:
        ```python
        registry = RegistryManager("service", "dev", "service")
        db = registry.get_database("main")
        ```
    """
```

### README Updates

Update README.md when:
- Adding new features
- Changing public APIs
- Adding new examples
- Modifying installation steps

## Code Review

All submissions require review. We look for:

- **Correctness**: Does it work as intended?
- **Tests**: Are there adequate tests?
- **Style**: Does it follow project conventions?
- **Documentation**: Is it properly documented?
- **Performance**: Any performance implications?
- **Security**: Any security concerns?

## Release Process

Maintainers will handle releases:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag
4. Build and publish to PyPI
5. Create GitHub release

## Questions?

- Open an issue for bugs or feature requests
- Join our community chat
- Email: team@soajs.org

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
