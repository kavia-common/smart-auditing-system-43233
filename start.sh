#!/usr/bin/env bash
set -euo pipefail

# PUBLIC_INTERFACE
# start.sh
# Purpose: Bootstrap and start the Django application for local/preview environments.
# - Creates/uses a Python virtual environment
# - Upgrades pip and installs dependencies from requirements.txt
# - Applies database migrations
# - Runs the development server bound to 0.0.0.0:3001
#
# This script is designed to be invoked by the preview system via Procfile:
#   web: bash start.sh

# Detect project root (this script is placed in the repo root for the container)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Python selector: prefer python3, fallback to python
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Error: No suitable Python binary found (python3 or python)."
    exit 1
  fi
fi

# Create venv if missing (ensure deterministic venv path under project root)
if [ ! -d "venv" ]; then
  "$PYTHON_BIN" -m venv venv
fi

# Activate venv (works for bash and sh)
# shellcheck disable=SC1091
source "venv/bin/activate"

# Ensure pip is present and up-to-date in the venv
python -m pip install --upgrade pip setuptools wheel

# Install dependencies before Django imports happen
if [ -f "requirements.txt" ]; then
  echo "Installing Python dependencies from requirements.txt ..."
  pip install -r requirements.txt
else
  echo "requirements.txt not found; please ensure dependencies are listed."
  exit 1
fi

# Verify pkg_resources (from setuptools) is available before Django imports
python - <<'PYCHK'
import sys, traceback
try:
    import pkg_resources  # provided by setuptools
except Exception:
    print("pkg_resources import failed. setuptools may be missing or broken in the venv.", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

# Confirm Django is importable (fail fast with helpful message)
try:
    import django  # noqa: F401
except Exception as exc:
    print("Failed to import Django after installing dependencies.", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)
else:
    import django
    print(f"Django import OK. Version: {django.get_version()}")
PYCHK

# Apply migrations (database setup)
python manage.py migrate --noinput

# Start development server on 0.0.0.0:3001 (as required by preview system)
exec python manage.py runserver 0.0.0.0:3001
