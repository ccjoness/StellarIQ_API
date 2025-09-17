.PHONY: help install install-dev test test-cov lint format clean run migrate upgrade downgrade docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	poetry install --only=main

install-dev: ## Install all dependencies including dev dependencies
	poetry install
	poetry run pre-commit install

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov=app --cov-report=html --cov-report=term-missing

lint: ## Run linting
	poetry run flake8 app tests
	poetry run mypy app

format: ## Format code
	poetry run black app tests
	poetry run isort app tests

format-check: ## Check code formatting
	poetry run black --check app tests
	poetry run isort --check-only app tests

clean: ## Clean up cache and temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ dist/ build/

run: ## Run the development server
	poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

migrate: ## Create a new migration
	poetry run alembic revision --autogenerate -m "$(msg)"

upgrade: ## Apply database migrations
	poetry run alembic upgrade head

downgrade: ## Rollback database migration
	poetry run alembic downgrade -1

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-up-dev: ## Start development services with Docker Compose
	docker-compose --profile dev up -d

docker-down: ## Stop services with Docker Compose
	docker-compose down

docker-build: ## Build Docker image
	docker-compose build

docker-build-dev: ## Build development Docker image
	docker-compose build app-dev

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-logs-dev: ## View development Docker logs
	docker-compose logs -f app-dev

shell: ## Open Poetry shell
	poetry shell

requirements: ## Export requirements.txt from Poetry
	poetry export -f requirements.txt --output requirements.txt --without-hashes --only=main

requirements-dev: ## Export dev requirements
	poetry export -f requirements.txt --output requirements-dev.txt --with dev --without-hashes

check: format-check lint test ## Run all checks (format, lint, test)

check-setup: ## Check if development environment is properly set up
	poetry run python scripts/check-setup.py

ci: install-dev check ## Run CI pipeline locally
