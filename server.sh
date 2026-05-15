#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${UPLOAD_HOST:-0.0.0.0}"
PORT="${UPLOAD_PORT:-8000}"
UPLOAD_DIR="${UPLOAD_DIR:-$ROOT_DIR/uploads}"

generate_token() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
    return
  fi

  python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
}

TOKEN="$(generate_token)"

mkdir -p "$UPLOAD_DIR"

export UPLOAD_HOST="$HOST"
export UPLOAD_PORT="$PORT"
export UPLOAD_DIR="$UPLOAD_DIR"
export FILE_TRANSFER_TOKEN="$TOKEN"

echo "Starting secure file transfer server..."
echo "Upload dir : $UPLOAD_DIR"
echo "Listen     : http://$HOST:$PORT"
echo "Token      : $TOKEN"
echo "Open       : http://127.0.0.1:$PORT/?token=$TOKEN"

exec python3 "$ROOT_DIR/upload_server.py"