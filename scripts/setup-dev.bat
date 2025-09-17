@echo off
REM StellarIQ Backend Development Setup Script for Windows

echo 🚀 Setting up StellarIQ Backend for development...

REM Check if Poetry is installed
poetry --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Poetry is not installed. Please install Poetry first:
    echo    Invoke-RestMethod -Uri https://install.python-poetry.org ^| Invoke-Expression
    echo    Or visit: https://python-poetry.org/docs/#installation
    exit /b 1
)

echo ✅ Poetry found

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo Python version: %python_version%

REM Install dependencies
echo 📦 Installing dependencies...
poetry install
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    exit /b 1
)

REM Set up pre-commit hooks
echo 🔧 Setting up pre-commit hooks...
poetry run pre-commit install

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your configuration
) else (
    echo ✅ .env file already exists
)

REM Check if Docker is available
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    docker-compose --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo 🐳 Docker found. You can start services with:
        echo    make docker-up
        echo    or: docker-compose up -d postgres redis
    ) else (
        echo ⚠️  Docker Compose not found. Please install Docker Desktop
    )
) else (
    echo ⚠️  Docker not found. Please install Docker Desktop to run PostgreSQL and Redis locally
)

echo.
echo 🎉 Development setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your Alpha Vantage API key and other settings
echo 2. Start database services: make docker-up
echo 3. Run database migrations: make upgrade
echo 4. Start the development server: make run
echo.
echo Available commands:
echo   make help              # Show all available commands
echo   make run              # Start development server
echo   make test             # Run tests
echo   make lint             # Run linting
echo   make format           # Format code
echo.
echo Happy coding! 🚀
