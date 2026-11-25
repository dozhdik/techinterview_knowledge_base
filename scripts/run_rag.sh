#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export RAG_ENABLED="${RAG_ENABLED:-false}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export RAG_TIMEOUT_SECONDS="${RAG_TIMEOUT_SECONDS:-180}"
exec .venv-rag/bin/python -m uvicorn web.server:app --host 127.0.0.1 --port "${PORT:-8000}" "$@"
