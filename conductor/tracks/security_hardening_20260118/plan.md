# Plan: Security Hardening & Automation

This plan focuses on integrating security tooling and establishing a scanning workflow.

## Phase 1: Tooling & Integration
- [x] Add `bandit` and `pip-audit` to `requirements.txt` and install. 85fc82d
- [x] Create `scripts/security_scan.sh` with proper error handling. 85fc82d
- [x] Update `Makefile` to include the `scan` target. 85fc82d

## Phase 2: Baseline Scan & Remediation
- [x] Run the first comprehensive scan. 85fc82d
- [x] Triage and fix any "High" severity issues found by Bandit. b1a9e9b
- [x] Update any dependencies flagged by Pip-Audit. b1a9e9b

## Phase 3: Documentation & Finalize
- [x] Update `CONTRIBUTING.md` to mention the `make scan` command. 991d223
- [x] Commit all changes and verify the workflow. 991d223
