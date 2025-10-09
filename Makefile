.PHONY: help setup up down logs restart build clean test bench frontend install-frontend delete-model

help:
	@echo "vLLM Chat Backend - Available Commands:"
	@echo "  make setup        - First-time setup: select default model"
	@echo "  make up           - Start all services (vLLM + API)"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - Follow logs from all services"
	@echo "  make restart      - Restart all services"
	@echo "  make build        - Rebuild API service"
	@echo "  make clean        - Stop and remove all containers, volumes"
	@echo "  make delete-model - Delete a model (interactive)"
	@echo "  make test         - Run pytest tests"
	@echo "  make bench        - Run benchmark script"
	@echo ""
	@echo "Frontend Commands:"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo "  make frontend         - Run TUI chat interface"

setup:
	@./scripts/setup_first_model.sh

up:
	docker compose up -d
	@echo "Services starting... Check logs with 'make logs'"
	@echo "API will be available at http://localhost:8787"
	@echo "vLLM will be available at http://localhost:8000"

down:
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
	@./scripts/delete_model.sh

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
	@echo "Starting TUI chat interface..."
	@cd frontend && bash run.sh
