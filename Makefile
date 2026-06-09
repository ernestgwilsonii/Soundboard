# Makefile for Soundboard
# Standardizes common development tasks using Docker Compose

# Default target
.PHONY: help
help:
	@echo "Soundboard Development Commands:"
	@echo "  make build    - Build the Docker images"
	@echo "  make run      - Start the application (https://localhost)"
	@echo "  make stop     - Stop the application"
	@echo "  make test     - Run the full test suite in Docker"
	@echo "  make scan     - Run security scans (Bandit + pip-audit)"
	@echo "  make debug    - Get a shell inside the test container (for troubleshooting)"
	@echo "  make clean    - Remove containers and volumes (resets DB, uploads, TLS certs)"
	@echo "  make promote user=NAME - Promote a user to admin"
	@echo "  make backup   - Back up user data (DBs + uploads) to ~/soundboard-backups"
	@echo "  make restore dir=PATH - Restore user data from a backup directory"

.PHONY: build
build:
	docker compose build

.PHONY: run
run:
	@echo "Starting app..."
	docker compose up -d traefik app
	@echo "App running at https://localhost (HTTP on :80 redirects)"
	docker compose logs -f app

.PHONY: stop
stop:
	docker compose down

.PHONY: promote
promote:
	docker compose exec app sqlite3 /app/data/accounts.sqlite3 "UPDATE users SET role='admin' WHERE username='$(user)';"
	@echo "User $(user) promoted to admin."

.PHONY: test
test:
	@echo "Running tests..."
	docker compose run --rm test pytest

.PHONY: scan
scan:
	@echo "Running security scan..."
	docker compose run --rm test ./scripts/security_scan.sh

.PHONY: debug
debug:
	@echo "Starting debug shell..."
	docker compose run --rm --entrypoint /bin/bash test

.PHONY: backup
backup:
	./scripts/backup.sh

.PHONY: restore
restore:
	./scripts/restore.sh $(dir)

.PHONY: clean
clean:
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -r {} +
