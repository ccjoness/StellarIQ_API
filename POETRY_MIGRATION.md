# Poetry Migration Guide

This document outlines the migration of StellarIQ Backend from pip/requirements.txt to Poetry for dependency management.

## What Changed

### New Files Added
- `pyproject.toml` - Poetry configuration and project metadata
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `Makefile` - Development commands and shortcuts
- `Dockerfile.dev` - Development-specific Docker configuration
- `scripts/setup-dev.sh` - Linux/macOS setup script
- `scripts/setup-dev.bat` - Windows setup script
- `scripts/check-setup.py` - Environment validation script
- `.gitignore` - Updated for Poetry projects

### Modified Files
- `README.md` - Updated with Poetry installation instructions
- `Dockerfile` - Updated to use Poetry
- `docker-compose.yml` - Added development service and Poetry commands

## Benefits of Poetry

### 1. **Better Dependency Resolution**
- Poetry resolves dependencies more reliably than pip
- Prevents dependency conflicts before installation
- Creates a lock file for reproducible builds

### 2. **Virtual Environment Management**
- Automatically creates and manages virtual environments
- No need to manually activate/deactivate environments
- Consistent environment across team members

### 3. **Development Tools Integration**
- Built-in support for development dependencies
- Easy integration with linting, formatting, and testing tools
- Pre-commit hooks for code quality

### 4. **Modern Python Packaging**
- Uses `pyproject.toml` standard (PEP 518)
- Better project metadata management
- Simplified build and publish process

## Migration Steps

### For Existing Developers

1. **Install Poetry** (if not already installed):
   ```bash
   # Linux/macOS/WSL
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Windows PowerShell
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   ```

2. **Remove old virtual environment** (optional but recommended):
   ```bash
   deactivate  # if currently in a virtual environment
   rm -rf venv/  # or whatever your venv directory is called
   ```

3. **Install dependencies with Poetry**:
   ```bash
   poetry install
   ```

4. **Set up development tools**:
   ```bash
   poetry run pre-commit install
   ```

5. **Verify setup**:
   ```bash
   make check-setup
   ```

### For New Developers

Simply run the setup script:
```bash
# Linux/macOS
./scripts/setup-dev.sh

# Windows
scripts\setup-dev.bat
```

## Development Workflow

### Running Commands

**Old way (pip):**
```bash
source venv/bin/activate
python -m uvicorn main:app --reload
pytest
black .
```

**New way (Poetry):**
```bash
poetry run uvicorn main:app --reload
poetry run pytest
poetry run black .

# Or use the Makefile shortcuts:
make run
make test
make format
```

### Adding Dependencies

**Production dependency:**
```bash
poetry add fastapi
```

**Development dependency:**
```bash
poetry add --group dev pytest
```

**Remove dependency:**
```bash
poetry remove package-name
```

### Updating Dependencies

```bash
# Update all dependencies
poetry update

# Update specific dependency
poetry update fastapi

# Show outdated packages
poetry show --outdated
```

## Docker Integration

### Development
```bash
# Start development environment with hot reload
make docker-up-dev
# or: docker-compose --profile dev up -d
```

### Production
```bash
# Start production environment
make docker-up
# or: docker-compose up -d
```

## Available Make Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install production dependencies only |
| `make install-dev` | Install all dependencies including dev tools |
| `make run` | Start development server |
| `make test` | Run tests |
| `make test-cov` | Run tests with coverage |
| `make lint` | Run linting (flake8, mypy) |
| `make format` | Format code (black, isort) |
| `make format-check` | Check code formatting |
| `make clean` | Clean cache and temporary files |
| `make migrate` | Create new database migration |
| `make upgrade` | Apply database migrations |
| `make docker-up` | Start Docker services |
| `make docker-up-dev` | Start development Docker services |
| `make check-setup` | Verify development environment |

## Code Quality Tools

The project now includes several code quality tools:

### Formatting
- **Black**: Code formatter
- **isort**: Import sorter

### Linting
- **flake8**: Style guide enforcement
- **mypy**: Static type checking

### Pre-commit Hooks
Automatically run on every commit:
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Code formatting
- Linting

### Testing
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async test support

## Configuration Files

### pyproject.toml
Contains all project configuration:
- Dependencies
- Tool configurations (black, isort, mypy, pytest)
- Project metadata

### .pre-commit-config.yaml
Defines pre-commit hooks for code quality.

## Troubleshooting

### Poetry not found
Make sure Poetry is in your PATH. You may need to restart your terminal or run:
```bash
source ~/.bashrc  # Linux/macOS
# or restart your terminal
```

### Virtual environment issues
```bash
# Reset Poetry environment
poetry env remove python
poetry install
```

### Dependency conflicts
```bash
# Clear Poetry cache
poetry cache clear pypi --all
poetry install
```

### Docker build issues
```bash
# Rebuild containers
docker-compose build --no-cache
```

## Backward Compatibility

The `requirements.txt` file is still maintained for compatibility with systems that don't use Poetry. To update it:

```bash
make requirements
```

This exports the current Poetry dependencies to `requirements.txt`.

## Next Steps

1. **Team Adoption**: Ensure all team members migrate to Poetry
2. **CI/CD Update**: Update CI/CD pipelines to use Poetry
3. **Documentation**: Keep documentation updated with Poetry commands
4. **Monitoring**: Monitor for any issues during the transition period

## Support

If you encounter any issues with the Poetry migration:

1. Check the troubleshooting section above
2. Run `make check-setup` to verify your environment
3. Consult the [Poetry documentation](https://python-poetry.org/docs/)
4. Ask for help from the team
