#!/bin/bash
set -e

echo "Running Black..."
venv/bin/black --check .

echo "Running Isort..."
venv/bin/isort --check-only .

echo "Running Flake8..."
venv/bin/flake8 .

echo "Running Pydocstyle..."
venv/bin/pydocstyle app

echo "Running MyPy..."
venv/bin/mypy app

echo "All quality checks passed!"
