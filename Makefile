.PHONY: help install install-dev test lint format clean build publish

help:
	@echo "SOAJS Python Development Commands"
	@echo ""
	@echo "  install       Install package"
	@echo "  install-dev   Install with dev dependencies"
	@echo "  test          Run tests"
	@echo "  test-cov      Run tests with coverage"
	@echo "  lint          Run linters (ruff, mypy)"
	@echo "  format        Format code (black, ruff)"
	@echo "  clean         Clean build artifacts"
	@echo "  build         Build distribution packages"
	@echo "  publish       Publish to PyPI"

install:
	pip install -e .

install-dev:
	pip install -e .[dev,fastapi,flask]

test:
	pytest tests/

test-cov:
	pytest --cov=soajs --cov-report=html --cov-report=term tests/

lint:
	ruff check soajs tests
	mypy soajs

format:
	black soajs tests examples
	ruff check --fix soajs tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

publish: build
	python -m twine upload dist/*
