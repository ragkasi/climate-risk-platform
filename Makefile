.PHONY: help setup dev stop format lint test train dvc-pull dvc-push seed tiles k8s-deploy clean

help: ## Show this help message
	@echo "Climate Risk Lens - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup - install dependencies and setup environment
	@echo "Setting up Climate Risk Lens..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; fi
	@echo "Installing Python dependencies..."
	cd backend && pip install -e .
	@echo "Installing Node.js dependencies..."
	cd frontend && npm install
	@echo "Installing ML dependencies..."
	cd ml && pip install -r requirements.txt
	@echo "Setting up pre-commit hooks..."
	pre-commit install
	@echo "Setup complete! Run 'make dev' to start development."

dev: ## Start development environment
	@echo "Starting development environment..."
	docker-compose up -d postgres redis mlflow minio
	@echo "Waiting for services to be ready..."
	sleep 10
	@echo "Starting backend..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend..."
	cd frontend && npm run dev &
	@echo "Starting Celery worker..."
	cd backend && celery -A app.workers.celery worker --loglevel=info &
	@echo "Starting Celery beat..."
	cd backend && celery -A app.workers.celery beat --loglevel=info &
	@echo "Development environment started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "MLflow: http://localhost:5000"

stop: ## Stop all development services
	@echo "Stopping development services..."
	docker-compose down
	pkill -f "uvicorn app.main:app" || true
	pkill -f "npm run dev" || true
	pkill -f "celery.*worker" || true
	pkill -f "celery.*beat" || true
	@echo "All services stopped."

format: ## Format code
	@echo "Formatting Python code..."
	cd backend && black . && ruff check --fix .
	cd ml && black . && ruff check --fix .
	@echo "Formatting TypeScript code..."
	cd frontend && npm run format
	@echo "Code formatting complete."

lint: ## Lint code
	@echo "Linting Python code..."
	cd backend && ruff check . && mypy .
	cd ml && ruff check . && mypy .
	@echo "Linting TypeScript code..."
	cd frontend && npm run lint
	@echo "Running ASCII compliance checks..."
	./scripts/check_ascii.sh
	./scripts/check_blocklist.sh
	@echo "Linting complete."

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && pytest --cov=app --cov-report=html --cov-report=term
	@echo "Running ML tests..."
	cd ml && pytest
	@echo "Running frontend tests..."
	cd frontend && npm test
	@echo "Running E2E tests..."
	cd frontend && npm run test:e2e
	@echo "All tests complete."

train: ## Train ML models
	@echo "Training ML models..."
	cd ml && python train_flood.py --demo
	cd ml && python train_heat.py --demo
	cd ml && python train_smoke.py --demo
	@echo "Model training complete."

dvc-pull: ## Pull data with DVC
	@echo "Pulling data with DVC..."
	cd data && dvc pull
	@echo "Data pull complete."

dvc-push: ## Push data with DVC
	@echo "Pushing data with DVC..."
	cd data && dvc push
	@echo "Data push complete."

seed: ## Seed demo data
	@echo "Seeding demo data..."
	cd scripts && python seed_demo_data.py
	@echo "Demo data seeded."

tiles: ## Build map tiles
	@echo "Building map tiles..."
	cd scripts && python build_tiles.py
	@echo "Map tiles built."

k8s-deploy: ## Deploy to Kubernetes
	@echo "Deploying to Kubernetes..."
	kubectl apply -k infra/k8s/overlays/dev
	@echo "Kubernetes deployment complete."

clean: ## Clean up temporary files
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete."
