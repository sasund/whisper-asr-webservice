.PHONY: help install test lint format clean docs

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	poetry install --with dev

test: ## Run tests
	poetry run pytest tests/ -v

test-cov: ## Run tests with coverage
	poetry run pytest tests/ -v --cov=app --cov-report=html --cov-report=term

lint: ## Run linting
	poetry run ruff check app/ tests/
	poetry run black --check app/ tests/

format: ## Format code
	poetry run black app/ tests/
	poetry run ruff check --fix app/ tests/

security: ## Run security checks
	poetry run bandit -r app/ -f json -o bandit-report.json || true
	poetry run safety check --json --output safety-report.json || true
	@echo "Security checks completed. Check bandit-report.json and safety-report.json for details."

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

docs: ## Build documentation
	poetry run mkdocs build

serve: ## Start the webservice
	poetry run python -m app.webservice

dev: ## Start development server with auto-reload
	poetry run uvicorn app.webservice:app --reload --host 0.0.0.0 --port 9000

all: install lint test security ## Run all checks 