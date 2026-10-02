#!/usr/bin/env bash
set -e

# Render provides the port to bind to via $PORT
PORT="${PORT:-8000}"

echo "============================================================"
echo "🌀 Starting IMD Cyclone Detector on port ${PORT}"
echo "🧠 Workers: 1 (Optimized for Render 512MB RAM free tier)"
echo "⚡ Concurrency Limit: 50 | Timeout Keepalive: 5s"
echo "============================================================"

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers 1 \
    --limit-concurrency 50 \
    --backlog 128 \
    --timeout-keep-alive 5
