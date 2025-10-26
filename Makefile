.PHONY: help install install-dev setup test lint format clean run run-dev docker-build docker-up docker-down

# Default target
help:
	@echo "Paralegal AI - Development Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install        - Install production dependencies"
	@echo "  make install-dev    - Install development dependencies"
	@echo "  make setup          - Complete project setup (install + hooks)"
	@echo ""
	@echo "Development:"
	@echo "  make run            - Run backend server"
	@echo "  make run-dev        - Run backend in development mode"
	@echo "  make run-frontend   - Run frontend development server"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test           - Run all tests"
	@echo "  make test-backend   - Run backend tests"
	@echo "  make test-frontend  - Run frontend tests"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make type-check     - Run type checkers"
	@echo "  make security-check - Run security scans"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-up      - Start Docker containers"
	@echo "  make docker-down    - Stop Docker containers"
	@echo "  make docker-logs    - View Docker logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove build artifacts"
	@echo "  make clean-all      - Remove all generated files"

# ============================================================================
# Setup & Installation
# ============================================================================

install:
	@echo "Installing production dependencies..."
	pip install -r requirements.txt
	pip install -r backend/requirements.txt
	cd frontend && npm ci --only=production

install-dev:
	@echo "Installing development dependencies..."
	pip install -r requirements.txt
	pip install -r backend/requirements.txt
	pip install pytest pytest-cov pytest-asyncio black flake8 isort mypy bandit safety
	cd frontend && npm install

setup: install-dev
	@echo "Setting up development environment..."
	pip install pre-commit
	pre-commit install
	cp .env.example .env
	@echo ""
	@echo "✅ Setup complete!"
	@echo "⚠️  Don't forget to update .env with your configuration"

# ============================================================================
# Running the Application
# ============================================================================

run:
	@echo "Starting backend server..."
	cd backend && python api_server.py

run-dev:
	@echo "Starting backend in development mode..."
	cd backend && uvicorn api_server:app --reload --port 8080

run-frontend:
	@echo "Starting frontend development server..."
	cd frontend && npm run dev

run-all:
	@echo "Starting full stack..."
	@make -j2 run-dev run-frontend

# ============================================================================
# Testing
# ============================================================================

test: test-backend test-frontend

test-backend:
	@echo "Running backend tests..."
	pytest backend/ -v --cov=backend --cov-report=term --cov-report=html

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

test-integration:
	@echo "Running integration tests..."
	python AMD_server/test_complete_system.py

# ============================================================================
# Code Quality
# ============================================================================

lint: lint-backend lint-frontend

lint-backend:
	@echo "Linting Python code..."
	flake8 backend/ AMD_server/ --max-line-length=100 --ignore=E203,W503
	black --check backend/ AMD_server/ --line-length=100
	isort --check-only backend/ AMD_server/ --profile=black

lint-frontend:
	@echo "Linting TypeScript code..."
	cd frontend && npm run lint

format: format-backend format-frontend

format-backend:
	@echo "Formatting Python code..."
	black backend/ AMD_server/ --line-length=100
	isort backend/ AMD_server/ --profile=black

format-frontend:
	@echo "Formatting TypeScript code..."
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}"

type-check:
	@echo "Type checking Python code..."
	mypy backend/ --ignore-missing-imports --no-strict-optional
	@echo "Type checking TypeScript code..."
	cd frontend && npx tsc --noEmit

security-check:
	@echo "Running security checks..."
	@echo "Checking Python dependencies..."
	safety check --file requirements.txt --file backend/requirements.txt || true
	@echo "Checking JavaScript dependencies..."
	cd frontend && npm audit || true
	@echo "Running Bandit security scan..."
	bandit -r backend/ -ll || true

# ============================================================================
# Docker
# ============================================================================

docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "Viewing Docker logs..."
	docker-compose logs -f

docker-restart:
	@make docker-down
	@make docker-up

docker-clean:
	@echo "Cleaning Docker resources..."
	docker-compose down -v
	docker system prune -f

# ============================================================================
# Database
# ============================================================================

db-create:
	@echo "Creating database..."
	createdb paralegal_db || echo "Database may already exist"

db-migrate:
	@echo "Running database migrations..."
	psql paralegal_db < AMD_server/scraper/database_schema.sql
	psql paralegal_db < AMD_server/scraper/case_management_schema.sql
	psql paralegal_db < AMD_server/scraper/client_communications_schema.sql

db-reset:
	@echo "⚠️  Resetting database (this will delete all data)..."
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		dropdb paralegal_db || true; \
		make db-create; \
		make db-migrate; \
	fi

# ============================================================================
# Cleanup
# ============================================================================

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	cd frontend && rm -rf dist/ node_modules/.cache/ 2>/dev/null || true

clean-all: clean
	@echo "Removing all generated files..."
	rm -rf venv/ 2>/dev/null || true
	cd frontend && rm -rf node_modules/ 2>/dev/null || true
	rm -rf logs/ data/ models/ 2>/dev/null || true

# ============================================================================
# Pre-commit
# ============================================================================

pre-commit:
	@echo "Running pre-commit hooks..."
	pre-commit run --all-files

pre-commit-update:
	@echo "Updating pre-commit hooks..."
	pre-commit autoupdate

# ============================================================================
# Documentation
# ============================================================================

docs-serve:
	@echo "Serving API documentation..."
	@echo "Backend API: http://localhost:8080/docs"
	@make run-dev

# ============================================================================
# CI/CD Simulation
# ============================================================================

ci: lint type-check test security-check
	@echo "✅ All CI checks passed!"

# ============================================================================
# Monitoring & Logs
# ============================================================================

logs:
	@echo "Viewing application logs..."
	tail -f logs/*.log 2>/dev/null || echo "No logs found"

logs-backend:
	@echo "Viewing backend logs..."
	tail -f logs/backend.log 2>/dev/null || echo "No backend logs found"
