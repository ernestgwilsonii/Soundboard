# Plan: Security Hardening & Automation

This plan focuses on integrating security tooling and establishing a scanning workflow.

## Phase 1: Tooling & Integration
- [x] Add `bandit` and `pip-audit` to `requirements.txt` and install. 85fc82d
- [x] Create `scripts/security_scan.sh` with proper error handling. 85fc82d
- [x] Update `Makefile` to include the `scan` target. 85fc82d

## Phase 2: Baseline Scan & Remediation
- [ ] Run the first comprehensive scan.
- [ ] Triage and fix any "High" severity issues found by Bandit.
- [ ] Update any dependencies flagged by Safety (if possible without breaking changes).

## Phase 3: Documentation & Finalize
- [ ] Update `CONTRIBUTING.md` to mention the `make scan` command.
- [ ] Commit all changes and verify the workflow.
