.PHONY: help install install-dev clean test test-unit test-integration test-cov lint format run dev docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make install-dev      - Install dependencies + dev tools"
	@echo "  make clean            - Remove generated files and caches"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo "  make lint             - Run linters (ruff, mypy)"
	@echo "  make format           - Format code (black)"
	@echo "  make run              - Run the application"
	@echo "  make dev              - Run in development mode with hot reload"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-up        - Start Docker containers"
	@echo "  make docker-down      - Stop Docker containers"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info/

test:
	pytest

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing

lint:
	ruff check src tests
	mypy src

format:
	black src tests
	ruff check --fix src tests

run:
	uvicorn src.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

db-init:
	python -m src.db.init_db
