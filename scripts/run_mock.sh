#!/usr/bin/env bash
set -euo pipefail

# allow optional port arg: default 9000
cd "$(dirname "$0")/.."
PORT=${1:-9000}
echo "Starting mock server on http://127.0.0.1:${PORT}"
# activate virtualenv if present
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi
uvicorn backend.mock_server:app --host 127.0.0.1 --port ${PORT} --reload
