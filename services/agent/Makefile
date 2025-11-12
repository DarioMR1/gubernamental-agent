.PHONY: help install dev prod test clean format lint type-check docs

# Default target
help: ## Show this help message
	@echo "🤖 Governmental Agent - Available Commands:"
	@echo
	@awk 'BEGIN {FS = ":.*##"; printf "\033[36m\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

install: ## Install dependencies
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	playwright install chromium

dev: ## Run development server
	@echo "🚀 Starting development server..."
	python dev_server.py

dev-reload: ## Run development server with auto-reload
	@echo "🔄 Starting development server with auto-reload..."
	python run_server.py --reload

##@ Production

prod: ## Run production server
	@echo "🏭 Starting production server..."
	python run_server.py --env production

staging: ## Run staging server
	@echo "🧪 Starting staging server..."
	python run_server.py --env staging

##@ Testing

test: ## Run tests
	@echo "🧪 Running tests..."
	pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

##@ Code Quality

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	black src/ tests/
	isort src/ tests/

lint: ## Run linting
	@echo "🔍 Running linter..."
	black --check src/ tests/
	isort --check-only src/ tests/

type-check: ## Run type checking
	@echo "🔍 Running type checker..."
	mypy src/

quality: format lint type-check ## Run all quality checks

##@ Utilities

clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

docs: ## Generate documentation
	@echo "📚 Starting documentation server..."
	python run_server.py --env development &
	@echo "📖 API Documentation available at:"
	@echo "   OpenAPI: http://localhost:8000/docs"
	@echo "   ReDoc: http://localhost:8000/redoc"

setup: ## Initial project setup
	@echo "🔧 Setting up project..."
	cp .env.example .env
	@echo "✅ Created .env file"
	@echo "📝 Please edit .env file with your configuration"
	@echo "🔑 Don't forget to add your API keys!"

##@ Docker (Optional)

docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t gubernamental-agent .

docker-run: ## Run Docker container
	@echo "🐳 Running Docker container..."
	docker run -p 8000:8000 --env-file .env gubernamental-agent

##@ Database

db-migrate: ## Run database migrations
	@echo "🗄️  Running database migrations..."
	python -c "from src.storage import DatabaseManager; import asyncio; asyncio.run(DatabaseManager().migrate())"

db-seed: ## Seed database with sample data
	@echo "🌱 Seeding database..."
	python -c "from src.storage import DatabaseManager; import asyncio; asyncio.run(DatabaseManager().seed_sample_data())"

##@ Monitoring

logs: ## Show logs
	@echo "📋 Showing recent logs..."
	tail -f logs/gubernamental_agent.log

metrics: ## Show metrics endpoint
	@echo "📊 Opening metrics endpoint..."
	curl http://localhost:8080/metrics || echo "Metrics server not running"