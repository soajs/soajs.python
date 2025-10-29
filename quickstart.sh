#!/bin/bash

# SOAJS Python Quick Start Script
# This script helps you get started with SOAJS Python development

set -e

echo "🚀 SOAJS Python Quick Start"
echo "============================"
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Found Python $python_version"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the soajs.python directory."
    exit 1
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q

# Install package
echo ""
echo "📥 Installing soajs-python with dev dependencies..."
pip install -e .[dev,fastapi,flask] -q
echo "✅ Installation complete"

# Set environment variables
echo ""
echo "🌍 Setting environment variables..."
export SOAJS_REGISTRY_API="${SOAJS_REGISTRY_API:-localhost:5000}"
export SOAJS_ENV="${SOAJS_ENV:-dev}"
export SOAJS_DEPLOY_MANUAL="${SOAJS_DEPLOY_MANUAL:-false}"

echo "   SOAJS_REGISTRY_API=$SOAJS_REGISTRY_API"
echo "   SOAJS_ENV=$SOAJS_ENV"
echo "   SOAJS_DEPLOY_MANUAL=$SOAJS_DEPLOY_MANUAL"

# Run tests
echo ""
read -p "🧪 Run tests? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running tests..."
    pytest tests/ -v
fi

# Run linters
echo ""
read -p "🔍 Run linters? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running linters..."
    ruff check soajs tests
    mypy soajs
fi

# Summary
echo ""
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "📚 Next steps:"
echo "   1. Activate virtual environment: source venv/bin/activate"
echo "   2. Run examples: python examples/fastapi_example.py"
echo "   3. Run tests: make test"
echo "   4. Read docs: cat README.md"
echo ""
echo "🔗 Useful commands:"
echo "   make help          - Show all available commands"
echo "   make test          - Run all tests"
echo "   make lint          - Run linters"
echo "   make format        - Format code"
echo ""
echo "📖 Documentation: README.md, SETUP.md, CONTRIBUTING.md"
echo ""
