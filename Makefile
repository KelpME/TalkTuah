.PHONY: help setup up down logs restart build clean test bench frontend install-frontend delete-model sync-settings apply

help:
	@echo "vLLM Chat Backend - Available Commands:"
	@echo "  make setup        - First-time setup: select default model"
	@echo "  make up           - Start all services (vLLM + API)"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - Follow logs from all services"
	@echo "  make restart      - Restart all services"
	@echo "  make apply        - Apply TUI settings and restart services"
	@echo "  make build        - Rebuild API service"
	@echo "  make clean        - Stop and remove all containers, volumes"
	@echo "  make delete-model - Delete a model (interactive)"
	@echo "  make test         - Run pytest tests"
	@echo "  make bench        - Run benchmark script"
	@echo ""
	@echo "Frontend Commands:"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo "  make frontend         - Run TUI chat interface"
	@echo "  make sync-settings    - Sync TUI settings to .env"

setup:
	@./scripts/setup/setup_first_model.sh

up:
	docker compose up -d
	@echo "Services starting... Check logs with 'make logs'"
	@echo "API will be available at http://localhost:8787"
	@echo "vLLM will be available at http://localhost:8000"

down:
	@echo "Stopping all services..."
	@docker stop vllm-server vllm-proxy-api 2>/dev/null || true
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart

build:
	docker compose build api

clean:
	docker compose down -v --remove-orphans

delete-model:
	@./scripts/management/delete_model.sh

test:
	@echo "Running tests..."
	pytest tests/ -v --tb=short

bench:
	@echo "Running benchmark..."
	python bench/latency.py

install-frontend:
	@echo "Installing frontend dependencies..."
	@if [ ! -d "frontend/venv" ]; then \
		echo "Creating virtual environment..."; \
		python -m venv frontend/venv; \
	fi
	@echo "Installing packages..."
	@frontend/venv/bin/pip install -r frontend/requirements.txt
	@echo "Frontend dependencies installed!"
	@echo "Virtual environment created at: frontend/venv"

frontend:
	@cd frontend && bash run.sh

sync-settings:
	@echo "Syncing TUI settings to .env..."
	@python3 scripts/management/sync_settings.py

apply: sync-settings
	@echo "Applying settings and restarting..."
	@docker compose restart vllm
	@echo "✓ Settings applied. vLLM restarting with new configuration."
