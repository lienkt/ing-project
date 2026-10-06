#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

run_check() {
    local name="$1"
    shift
    echo "=== $name ==="
    if "$@"; then
        return 0
    else
        local status=$?
        echo "=== Verification failed: $name (exit $status) ===" >&2
        exit "$status"
    fi
}

cd backend
run_check "Backend tests" .venv/bin/python -m pytest -q --tb=short
cd "$PROJECT_ROOT"

# The existing build script runs tsc -b before vite build.
# No frontend test runner or standalone lint script is configured.
run_check "Frontend TypeScript check and build" npm --prefix frontend run build
run_check "Prettier formatting check" npm --prefix frontend run format:check
run_check "Python formatting check" backend/.venv/bin/ruff format --check backend

echo "=== Verification passed ==="
