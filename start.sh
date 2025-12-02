#!/usr/bin/env bash
set -euo pipefail

# PUBLIC_INTERFACE
# start.sh
# Purpose: Bootstrap and start the Django application for local/preview environments.
# - Creates/uses a Python virtual environment
# - Upgrades pip and installs dependencies from requirements.txt
# - Applies database migrations
# - Runs the development server bound to 0.0.0.0:3001

# Detect project root (this script is placed in the repo root for the container)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_ROOT"

# Create venv if missing
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Upgrade pip and install deps
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
else
  echo "requirements.txt not found; please ensure dependencies are listed."
  exit 1
fi

# Migrate and run
python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:3001
