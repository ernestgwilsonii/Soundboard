# Makefile for Soundboard
# Standardizes common development tasks using Docker Compose

# Default target
.PHONY: help
help:
	@echo "Soundboard Development Commands:"
	@echo "  make build    - Build the Docker images"
	@echo "  make run      - Start the application (localhost:5000)"
	@echo "  make stop     - Stop the application"
	@echo "  make test     - Run the full test suite in Docker"
	@echo "  make debug    - Get a shell inside the test container (for troubleshooting)"
	@echo "  make clean    - Remove containers and volumes (resets DB)"

.PHONY: build
build:
	docker compose build

.PHONY: run
run:
	@echo "Starting app..."
	docker compose up -d app
	@echo "App running at http://localhost:5000"
	docker compose logs -f app

.PHONY: stop
stop:
	docker compose down

.PHONY: test
test:
	@echo "Running tests..."
	docker compose run --rm test pytest

.PHONY: debug
debug:
	@echo "Starting debug shell..."
	docker compose run --rm --entrypoint /bin/bash test

.PHONY: clean
clean:
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -r {} +
