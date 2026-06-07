#!/usr/bin/env bash
set -euo pipefail

export PORT="${PORT:-10000}"
export API_BASE="${API_BASE:-http://127.0.0.1:8000}"
export PUBLIC_API_BASE="${PUBLIC_API_BASE:-/api}"
export FASTAPI_ROOT_PATH="${FASTAPI_ROOT_PATH:-/api}"

mkdir -p data/processed models /tmp/nginx-client-body /tmp/nginx-proxy

if [ -n "${PERSISTENT_STORAGE_DIR:-}" ]; then
  mkdir -p "${PERSISTENT_STORAGE_DIR}/data/processed" "${PERSISTENT_STORAGE_DIR}/models" "${PERSISTENT_STORAGE_DIR}/config"
  if [ ! -f "${PERSISTENT_STORAGE_DIR}/config/thresholds.yaml" ]; then
    cp config/thresholds.yaml "${PERSISTENT_STORAGE_DIR}/config/thresholds.yaml"
  fi
  rm -rf data/processed models
  mkdir -p data
  ln -s "${PERSISTENT_STORAGE_DIR}/data/processed" data/processed
  ln -s "${PERSISTENT_STORAGE_DIR}/models" models
  rm -f config/thresholds.yaml
  ln -s "${PERSISTENT_STORAGE_DIR}/config/thresholds.yaml" config/thresholds.yaml
fi

envsubst '${PORT}' < docker/nginx.conf.template > /tmp/nginx.conf

cleanup() {
  local status=$?
  trap - EXIT TERM INT
  kill -TERM "${NGINX_PID:-}" "${STREAMLIT_PID:-}" "${API_PID:-}" 2>/dev/null || true
  wait "${NGINX_PID:-}" "${STREAMLIT_PID:-}" "${API_PID:-}" 2>/dev/null || true
  exit "$status"
}
trap cleanup EXIT TERM INT

python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --proxy-headers &
API_PID=$!

python -m streamlit run src/dashboard/app.py \
  --server.address 127.0.0.1 \
  --server.port 8501 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false &
STREAMLIT_PID=$!

wait_for() {
  local name="$1"
  local url="$2"
  for _ in $(seq 1 60); do
    if curl -fsS "$url" >/dev/null; then
      return 0
    fi
    sleep 1
  done
  echo "${name} did not become ready in time" >&2
  return 1
}

wait_for "FastAPI" "http://127.0.0.1:8000/health"
wait_for "Streamlit" "http://127.0.0.1:8501/_stcore/health"

nginx -c /tmp/nginx.conf -g "daemon off;" &
NGINX_PID=$!

wait -n "$API_PID" "$STREAMLIT_PID" "$NGINX_PID"
