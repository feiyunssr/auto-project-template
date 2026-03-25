#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
SERVICE_HOST_IP="${SERVICE_HOST_IP:-}"
BACKEND_PID=""
FRONTEND_PID=""

require_file() {
  local path="$1"
  local hint="$2"
  if [[ ! -e "$path" ]]; then
    echo "Missing required path: $path" >&2
    echo "$hint" >&2
    exit 1
  fi
}

detect_service_ip() {
  local detected_ip=""
  if [[ -n "$SERVICE_HOST_IP" ]]; then
    printf '%s\n' "$SERVICE_HOST_IP"
    return
  fi

  if command -v ip >/dev/null 2>&1; then
    detected_ip="$(ip route get 1.1.1.1 2>/dev/null | awk '{for (i = 1; i <= NF; i++) if ($i == "src") {print $(i + 1); exit}}')"
  fi

  if [[ -z "$detected_ip" ]]; then
    detected_ip="$(hostname -I 2>/dev/null | tr ' ' '\n' | awk '/^[0-9]+\./ {print; exit}')"
  fi

  if [[ -z "$detected_ip" ]]; then
    echo "Failed to detect a reachable IPv4 address. Set SERVICE_HOST_IP manually." >&2
    exit 1
  fi

  printf '%s\n' "$detected_ip"
}

cleanup() {
  local exit_code=$?

  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
  fi

  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi

  exit "$exit_code"
}

trap cleanup EXIT INT TERM

require_file "$ROOT_DIR/.venv/bin/python" "Create the backend venv first: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'"
require_file "$ROOT_DIR/apps/frontend/package.json" "Frontend project is missing."
require_file "$ROOT_DIR/apps/frontend/node_modules" "Install frontend deps first: cd apps/frontend && npm install"

SERVICE_HOST_IP="$(detect_service_ip)"
export SERVICE_PUBLIC_BASE_URL="http://${SERVICE_HOST_IP}:${BACKEND_PORT}"
export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://${SERVICE_HOST_IP}:${BACKEND_PORT}}"
export VITE_REQUIRE_HUB_AUTH="${VITE_REQUIRE_HUB_AUTH:-${REQUIRE_HUB_AUTH:-false}}"

echo "Starting backend on http://${SERVICE_HOST_IP}:${BACKEND_PORT}"
echo "Starting frontend on http://${SERVICE_HOST_IP}:${FRONTEND_PORT}"
echo "Hub auth required: ${REQUIRE_HUB_AUTH:-false}"
echo "Press Ctrl+C to stop both services."

cd "$ROOT_DIR"
"$ROOT_DIR/.venv/bin/python" -m uvicorn apps.backend.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" &
BACKEND_PID=$!

cd "$ROOT_DIR/apps/frontend"
npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

wait "$BACKEND_PID" "$FRONTEND_PID"
