# Variables
PYTHON := python
PIP := $(PYTHON) -m pip
DOCKER_COMPOSE := docker-compose

# Colors for terminal output
CYAN := \033[0;36m
NC := \033[0m # No Color

.PHONY: all setup-backend setup-frontend install-deps run-backend run-frontend run-dev build-frontend test clean help ngrok-setup ngrok-run

all: help

setup-backend:
	@echo "$(CYAN)Setting up backend...$(NC)"
	cd backend && asdf install python
	cd backend && $(PIP) install -r requirements.txt

setup-frontend:
	@echo "$(CYAN)Setting up frontend...$(NC)"
	cd frontend && npm install

install-deps: setup-backend setup-frontend

run-backend:
	@echo "$(CYAN)Running backend...$(NC)"
	$(DOCKER_COMPOSE) up --build backend

restart-backend:
	@echo "$(CYAN)Restarting backend...$(NC)"
	$(MAKE) stop-backend
	$(MAKE) run-backend

stop-backend:
	@echo "$(CYAN)Stopping backend...$(NC)"
	@pkill -f "uvicorn main:app"

run-frontend:
	@echo "$(CYAN)Running frontend...$(NC)"
	cd frontend && npm run dev

run-dev:
	@echo "$(CYAN)Running backend, frontend, and services...$(NC)"
	$(DOCKER_COMPOSE) up --build -d db backend ngrok
	$(MAKE) run-frontend
	@echo "$(CYAN)Fetching ngrok URL...$(NC)"
	@sleep 5  # Give ngrok a moment to start up
	@$(MAKE) get-ngrok-url
	@echo "$(CYAN)Update NEXT_PUBLIC_API_URL in frontend/.env.local with this URL$(NC)"

run-services:
	@echo "$(CYAN)Running database and ngrok...$(NC)"
	$(DOCKER_COMPOSE) up -d db ngrok

build-frontend:
	@echo "$(CYAN)Building frontend...$(NC)"
	cd frontend && npm run build

test:
	@echo "$(CYAN)Running tests...$(NC)"
	cd backend && pytest
	cd frontend && npm test

clean:
	@echo "$(CYAN)Cleaning up...$(NC)"
	cd frontend && rm -rf .next node_modules

help:
	@echo "$(CYAN)Available commands:$(NC)"
	@echo "  make setup-backend    - Set up the backend and install dependencies"
	@echo "  make setup-frontend   - Install frontend dependencies"
	@echo "  make install-deps     - Install all dependencies (backend and frontend)"
	@echo "  make run-backend      - Run the backend server"
	@echo "  make run-frontend     - Run the frontend development server"
	@echo "  make run-dev          - Run backend, frontend, and services"
	@echo "  make run-services     - Run database and ngrok services"
	@echo "  make build-frontend   - Build the frontend for production"
	@echo "  make test             - Run tests for both backend and frontend"
	@echo "  make clean            - Remove build artifacts"
	@echo "  make ngrok-setup      - Set up ngrok Docker image"
	@echo "  make ngrok-run        - Run ngrok in Docker"

ngrok-setup:
	@echo "$(CYAN)Setting up ngrok...$(NC)"
	docker pull ngrok/ngrok:latest
	@echo "$(CYAN)Ngrok setup complete. Make sure you have set your NGROK_AUTHTOKEN in the .env file.$(NC)"

ngrok-run:
	@echo "$(CYAN)Running ngrok...$(NC)"
	$(DOCKER_COMPOSE) up -d ngrok
	@echo "$(CYAN)Ngrok is running. Check the ngrok dashboard or logs for the public URL.$(NC)"

get-ngrok-url:
	@echo "$(CYAN)Fetching ngrok public URL...$(NC)"
	@curl -s localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'

run-backend-debug:
	@echo "$(CYAN)Running backend in debug mode...$(NC)"
	cd backend && ENVIRONMENT=development python -m debugpy --listen 0.0.0.0:5678 -m uvicorn main:app --reload --host 0.0.0.0 --port 8095
