#!/usr/bin/env sh
set -eu

# Hugging Face Spaces provides PORT (default 7860)
PORT="${PORT:-7860}"

exec uvicorn src.api.fastapi_app:app --host 0.0.0.0 --port "$PORT"
