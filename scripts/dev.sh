#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.runtime"
VENV_BIN="$ROOT_DIR/.venv/bin"
BACKEND_DIR="$ROOT_DIR/apps/service-backend"
FRONTEND_DIR="$ROOT_DIR/apps/service-frontend"
WORKER_DIR="$ROOT_DIR/apps/service-worker"
ENV_FILE="$ROOT_DIR/.env"

BACKEND_HOST="${SERVICE_BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${SERVICE_BACKEND_PORT:-11010}"
FRONTEND_HOST="${SERVICE_FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${SERVICE_FRONTEND_PORT:-11011}"
DEFAULT_DB_URL="sqlite+aiosqlite:///$ROOT_DIR/service.db"
WORKER_HEARTBEAT_PATH="${SERVICE_WORKER_HEARTBEAT_PATH:-$RUNTIME_DIR/service-worker.json}"

BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"
WORKER_PID_FILE="$RUNTIME_DIR/worker.pid"

BACKEND_LOG="$RUNTIME_DIR/backend.log"
FRONTEND_LOG="$RUNTIME_DIR/frontend.log"
WORKER_LOG="$RUNTIME_DIR/worker.log"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/dev.sh start
  bash scripts/dev.sh stop
  bash scripts/dev.sh restart
  bash scripts/dev.sh status
EOF
}

ensure_runtime_dir() {
  mkdir -p "$RUNTIME_DIR"
}

load_env_file() {
  if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
  fi
}

running_pid() {
  local pid_file="$1"

  if [[ ! -f "$pid_file" ]]; then
    return 1
  fi

  local pgid
  pgid="$(tr -d '[:space:]' < "$pid_file")"

  if [[ -n "$pgid" ]] && ps -o pid= -g "$pgid" | grep -q '[0-9]'; then
    printf '%s\n' "$pgid"
    return 0
  fi

  rm -f "$pid_file"
  return 1
}

start_service() {
  local name="$1"
  local workdir="$2"
  local pid_file="$3"
  local log_file="$4"
  shift 4

  if running_pid "$pid_file" >/dev/null; then
    echo "$name is already running"
    return 0
  fi

  (
    cd "$workdir"
    setsid nohup "$@" >"$log_file" 2>&1 < /dev/null &
    local pid
    local pgid
    pid="$!"
    pgid="$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d '[:space:]')"
    echo "${pgid:-$pid}" >"$pid_file"
  ) >/dev/null 2>&1

  local pgid
  pgid="$(cat "$pid_file")"
  sleep 1

  if kill -0 -- "-$pgid" 2>/dev/null; then
    echo "Started $name (pgid=$pgid)"
    return 0
  fi

  echo "$name failed to start. Check $log_file"
  rm -f "$pid_file"
  return 1
}

stop_service() {
  local name="$1"
  local pid_file="$2"

  if ! running_pid "$pid_file" >/dev/null; then
    echo "$name is not running"
    return 0
  fi

  local pgid
  pgid="$(cat "$pid_file")"

  if [[ -n "$pgid" ]]; then
    local member_pids
    member_pids="$(ps -o pid= -g "$pgid" | tr '\n' ' ' | xargs || true)"

    if [[ -n "$member_pids" ]]; then
      kill -TERM $member_pids 2>/dev/null || true
      sleep 1

      member_pids="$(ps -o pid= -g "$pgid" | tr '\n' ' ' | xargs || true)"
      if [[ -n "$member_pids" ]]; then
        kill -KILL $member_pids 2>/dev/null || true
      fi
    fi
  fi

  rm -f "$pid_file"
  echo "Stopped $name"
}

check_requirements() {
  if [[ ! -x "$VENV_BIN/uvicorn" || ! -x "$VENV_BIN/python" ]]; then
    echo "Missing Python tools in $VENV_BIN"
    exit 1
  fi

  if ! command -v npm >/dev/null 2>&1; then
    echo "npm is required but not installed"
    exit 1
  fi

  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    echo "Missing frontend dependencies. Run npm install in apps/service-frontend"
    exit 1
  fi
}

start_all() {
  ensure_runtime_dir
  load_env_file
  check_requirements

  start_service \
    "backend" \
    "$BACKEND_DIR" \
    "$BACKEND_PID_FILE" \
    "$BACKEND_LOG" \
    env \
    PYTHONPATH=. \
    SERVICE_BACKEND_DATABASE_URL="${SERVICE_BACKEND_DATABASE_URL:-$DEFAULT_DB_URL}" \
    SERVICE_BACKEND_SERVICE_PUBLIC_BASE_URL="${SERVICE_BACKEND_SERVICE_PUBLIC_BASE_URL:-http://127.0.0.1:$BACKEND_PORT}" \
    SERVICE_BACKEND_RUN_EMBEDDED_WORKER=false \
    SERVICE_BACKEND_WORKER_HEARTBEAT_PATH="$WORKER_HEARTBEAT_PATH" \
    "$VENV_BIN/uvicorn" app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"

  start_service \
    "frontend" \
    "$FRONTEND_DIR" \
    "$FRONTEND_PID_FILE" \
    "$FRONTEND_LOG" \
    env \
    VITE_API_BASE_URL="${VITE_API_BASE_URL:-/api/v1}" \
    VITE_DEV_PROXY_TARGET="${VITE_DEV_PROXY_TARGET:-http://127.0.0.1:$BACKEND_PORT}" \
    npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"

  start_service \
    "worker" \
    "$WORKER_DIR" \
    "$WORKER_PID_FILE" \
    "$WORKER_LOG" \
    env \
    PYTHONPATH="$ROOT_DIR/apps/service-backend:$WORKER_DIR" \
    SERVICE_WORKER_DATABASE_URL="${SERVICE_WORKER_DATABASE_URL:-$DEFAULT_DB_URL}" \
    SERVICE_WORKER_HEARTBEAT_PATH="$WORKER_HEARTBEAT_PATH" \
    "$VENV_BIN/python" -m service_worker.main

  echo
  echo "Frontend: http://$FRONTEND_HOST:$FRONTEND_PORT"
  echo "Backend:  http://$BACKEND_HOST:$BACKEND_PORT/docs"
  echo "Logs:     $RUNTIME_DIR"
}

status_all() {
  ensure_runtime_dir
  load_env_file

  for entry in \
    "backend:$BACKEND_PID_FILE:$BACKEND_LOG" \
    "frontend:$FRONTEND_PID_FILE:$FRONTEND_LOG" \
    "worker:$WORKER_PID_FILE:$WORKER_LOG"; do
    IFS=":" read -r name pid_file log_file <<<"$entry"
    if running_pid "$pid_file" >/dev/null; then
      echo "$name: running (pid=$(cat "$pid_file")) log=$log_file"
    else
      echo "$name: stopped"
    fi
  done
}

stop_all() {
  load_env_file
  stop_service "worker" "$WORKER_PID_FILE"
  stop_service "frontend" "$FRONTEND_PID_FILE"
  stop_service "backend" "$BACKEND_PID_FILE"
}

case "${1:-start}" in
  start) start_all ;;
  stop) stop_all ;;
  restart)
    stop_all
    start_all
    ;;
  status) status_all ;;
  *)
    usage
    exit 1
    ;;
esac
