.PHONY: install dev worker scheduler test test-unit test-integration test-agent test-security lint format typecheck migrate migrate-create seed benchmark evaluate docker-build docker-up docker-down docker-test clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -e ".[dev]"
	$(VENV)/bin/pre-commit install

dev:
	$(VENV)/bin/uvicorn planos.app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	$(VENV)/bin/celery -A planos.app.workers.celery_app worker --loglevel=info --concurrency=4

scheduler:
	$(VENV)/bin/celery -A planos.app.workers.celery_app beat --loglevel=info

test:
	$(VENV)/bin/pytest tests/ -v --tb=short

test-unit:
	$(VENV)/bin/pytest tests/unit -v --tb=short

test-integration:
	$(VENV)/bin/pytest tests/integration -v --tb=short

test-agent:
	$(VENV)/bin/pytest tests/agent -v --tb=short

test-security:
	$(VENV)/bin/pytest tests/security -v --tb=short

lint:
	$(VENV)/bin/ruff check planos/ tests/

format:
	$(VENV)/bin/ruff format planos/ tests/

typecheck:
	$(VENV)/bin/mypy planos/

migrate:
	$(VENV)/bin/alembic upgrade head

migrate-create:
	@read -p "Migration message: " msg; $(VENV)/bin/alembic revision --autogenerate -m "$$msg"

seed:
	$(PYTHON) scripts/seed_data.py

benchmark:
	$(PYTHON) scripts/benchmark.py

evaluate:
	$(PYTHON) scripts/run_evaluation.py

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-test:
	docker compose -f docker-compose.test.yml up --abort-on-container-exit

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache $(VENV)
