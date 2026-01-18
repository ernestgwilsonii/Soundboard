# Specification: Security Hardening & Automation

## 1. Overview
This track establishes a continuous security baseline for the Soundboard application. We will integrate automated tools to detect code vulnerabilities (SAST) and insecure dependencies (SCA). We will also create a standardized `make scan` command to empower developers to self-audit.

## 2. Goals
- **Static Application Security Testing (SAST):** Integrate `bandit` to scan Python code for common vulnerabilities (SQL injection risks, hardcoded secrets, weak cryptography).
- **Software Composition Analysis (SCA):** Integrate `safety` to check `requirements.txt` against known CVE databases.
- **Automation:** Create a `scripts/security_scan.sh` script and a `make scan` target.
- **Documentation:** Update `CONTRIBUTING.md` to include security checks in the workflow.

## 3. Tool Selection
- **Bandit:** Chosen for its Python-specificity and ability to detect AST-level flaws.
- **Safety:** Chosen for its simplicity in checking PyPI dependencies.

## 4. Implementation Details
### 4.1 Dependency Updates
- Add `bandit` and `safety` to `requirements.txt`.

### 4.2 Scripting
- Create `scripts/security_scan.sh`:
    - Run `safety check`
    - Run `bandit -r app/ -ll` (Medium confidence/severity threshold initially)

### 4.3 Makefile Integration
- Add `scan:` target to `Makefile`.

## 5. Acceptance Criteria
- `make scan` runs without error (after fixing any immediate critical findings).
- CI/CD ready (script returns non-zero exit code on failure).
