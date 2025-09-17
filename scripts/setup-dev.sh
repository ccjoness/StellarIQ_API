#!/bin/bash

# StellarIQ Backend Development Setup Script

set -e

echo "🚀 Setting up StellarIQ Backend for development..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    echo "   Or visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

echo "✅ Poetry found"

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed"

# Install dependencies
echo "📦 Installing dependencies..."
poetry install

# Set up pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
poetry run pre-commit install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 Docker found. You can start services with:"
    echo "   make docker-up"
    echo "   or: docker-compose up -d postgres redis"
else
    echo "⚠️  Docker not found. Please install Docker to run PostgreSQL and Redis locally"
fi

echo ""
echo "🎉 Development setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Alpha Vantage API key and other settings"
echo "2. Start database services: make docker-up"
echo "3. Run database migrations: make upgrade"
echo "4. Start the development server: make run"
echo ""
echo "Available commands:"
echo "  make help              # Show all available commands"
echo "  make run              # Start development server"
echo "  make test             # Run tests"
echo "  make lint             # Run linting"
echo "  make format           # Format code"
echo ""
echo "Happy coding! 🚀"
