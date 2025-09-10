# CI/CD Dashboard Makefile

.PHONY: help build up down logs test clean dev-backend dev-frontend

# Default target
help:
	@echo "CI/CD Dashboard - Available commands:"
	@echo ""
	@echo "  build          - Build all Docker images"
	@echo "  up             - Start all services"
	@echo "  down           - Stop all services"
	@echo "  logs           - Show logs from all services"
	@echo "  test           - Run all tests"
	@echo "  clean          - Clean up containers and images"
	@echo "  dev-backend    - Start backend in development mode"
	@echo "  dev-frontend   - Start frontend in development mode"
	@echo "  setup          - Initial setup (copy env file)"
	@echo "  verify         - Verify the setup"

# Build all Docker images
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Show logs
logs:
	docker-compose logs -f

# Run tests
test:
	@echo "Running backend tests..."
	docker-compose exec backend python -m pytest test_backend.py -v
	@echo "Running frontend tests..."
	docker-compose exec frontend npm test
	@echo "Running integration tests..."
	python test_setup.py

# Clean up
clean:
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

# Development mode - Backend
dev-backend:
	cd backend && ./start.sh

# Development mode - Frontend
dev-frontend:
	cd frontend && ./start.sh

# Initial setup
setup:
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Created .env file from env.example"; \
		echo "Please edit .env file with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi

# Verify setup
verify:
	python test_setup.py

# Quick start
quick-start: setup build up
	@echo "Dashboard is starting up..."
	@echo "Backend: http://localhost:8001"
	@echo "Frontend: http://localhost:5173"
	@echo "API Docs: http://localhost:8001/docs"
	@echo ""
	@echo "Run 'make verify' to test the setup"

# Production deployment
deploy-prod:
	docker-compose -f docker-compose.prod.yml up -d

# Staging deployment
deploy-staging:
	docker-compose -f docker-compose.staging.yml up -d

# Backup database
backup:
	docker-compose exec backend cp /app/data/dashboard.db /app/data/dashboard.db.backup
	docker cp ci-dashboard-backend:/app/data/dashboard.db.backup ./backup-$(shell date +%Y%m%d-%H%M%S).db

# Restore database
restore:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make restore FILE=backup-file.db"; \
		exit 1; \
	fi
	docker cp $(FILE) ci-dashboard-backend:/app/data/dashboard.db
	docker-compose restart backend

# Health check
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8001/health && echo "Backend: OK" || echo "Backend: FAILED"
	@curl -f http://localhost:5173/ && echo "Frontend: OK" || echo "Frontend: FAILED"

# Update dependencies
update-deps:
	@echo "Updating backend dependencies..."
	cd backend && pip install -r requirements.txt --upgrade
	@echo "Updating frontend dependencies..."
	cd frontend && npm update

# Security scan
security-scan:
	@echo "Running security scans..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image ci-dashboard-backend:latest
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image ci-dashboard-frontend:latest
