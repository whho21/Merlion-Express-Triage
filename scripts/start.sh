#!/usr/bin/env bash
# macOS and WSL: always use this checkout's POSIX virtual environment.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  printf '[ ] Project Python environment missing. Follow backend/api_service/backend_API_setup.md.\n' >&2
  exit 1
fi
exec "$PYTHON" "$SCRIPT_DIR/start_services.py" "$@"
