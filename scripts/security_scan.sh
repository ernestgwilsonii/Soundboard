#!/bin/bash
# Security scan script using Bandit and Pip-Audit

set -e

# Determine executable paths
BANDIT_CMD="bandit"
PIPAUDIT_CMD="pip-audit"

if [ -f "venv/bin/bandit" ]; then
    BANDIT_CMD="venv/bin/bandit"
fi

if [ -f "venv/bin/pip-audit" ]; then
    PIPAUDIT_CMD="venv/bin/pip-audit"
fi

echo "=== Starting Security Scan ==="

echo ""
echo "--- 1. Dependency Scan (Pip-Audit) ---"
if $PIPAUDIT_CMD -r requirements.txt; then
    echo ">> Pip-Audit check passed."
else
    echo ">> Pip-Audit check failed!"
    AUDIT_FAILED=1
fi

echo ""
echo "--- 2. Code Vulnerability Scan (Bandit) ---"
# -r: recursive
# -ll: report only medium and high severity
# -ii: report only medium and high confidence
# -x: exclude paths
if $BANDIT_CMD -r app/ -ll -ii -x tests/; then
    echo ">> Bandit check passed."
else
    echo ">> Bandit check failed!"
    BANDIT_FAILED=1
fi

echo ""
echo "=== Scan Complete ==="

if [ "$AUDIT_FAILED" = "1" ] || [ "$BANDIT_FAILED" = "1" ]; then
    echo "Result: FAIL"
    exit 1
else
    echo "Result: PASS"
    exit 0
fi
