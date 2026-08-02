# Deploying Latimer AI Bias on Hugging Face (Docker)

This project is set up for **Hugging Face Spaces (Docker SDK)** with a single container that serves:
- FastAPI backend
- Built React frontend static files

---

## Why Docker for this project

Docker is a good fit because this app has:
- Python backend + Node frontend build
- environment-managed secrets
- custom dependencies and startup behavior

This gives reproducible builds and a professional deployment workflow.

---

## Security first (important)

Never commit real secrets to git.

### Required actions before pushing
1. Ensure `.env` is not committed (it is ignored by `.gitignore`).
2. Rotate any keys that were previously exposed in local files/history.
3. Store secrets in **Hugging Face Space Settings → Variables and secrets**.

### Use HF Secrets for sensitive values
Put these in Spaces Secrets (not repo files):
- `AZURE_API_KEY`
- `AZURE_OPENAI_API_KEY` (if used)
- `AZURE_ANTHROPIC_API_KEY` (if used)
- `AZURE_COGNITIVE_SEARCH_API_KEY`
- `HF_TOKEN` (if needed)
- any provider/API credentials

Use non-secret config as Variables (or Secrets if preferred):
- `AZURE_ENDPOINT`
- `AZURE_API_VERSION`
- `AZURE_DEFAULT_MODEL`
- `AZURE_MODEL_DEPLOYMENTS_JSON`
- `AZURE_OPENAI_EMBEDDING_MODEL`
- `AZURE_COGNITIVE_SEARCH_ENDPOINT`

---

## Files added for deployment

- `Dockerfile` (multi-stage build)
- `.dockerignore` (smaller build context, fewer leaks)
- `deploy/start.sh` (uses `PORT`, defaults to 7860)
- FastAPI serves frontend static assets from `frontend_dist/`

---

## Hugging Face Spaces setup

1. Create a new Space.
2. Choose **Docker** SDK.
3. Push this repository to the Space.
4. In Space Settings:
   - Add Variables/Secrets listed above.
5. Rebuild Space.

App will start with:

```bash
uvicorn src.api.fastapi_app:app --host 0.0.0.0 --port ${PORT:-7860}
```

---

## Local smoke test (Docker)

From repo root:

```bash
docker build -t latimer-ai-bias:local .

docker run --rm -p 7860:7860 \
  -e AZURE_API_KEY="..." \
  -e AZURE_ENDPOINT="..." \
  -e AZURE_DEFAULT_MODEL="GPT-5.5" \
  -e AZURE_MODEL_DEPLOYMENTS_JSON='{"GPT-5.5":"gpt-5.5"}' \
  -e AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-3-small" \
  -e AZURE_COGNITIVE_SEARCH_ENDPOINT="..." \
  -e AZURE_COGNITIVE_SEARCH_API_KEY="..." \
  latimer-ai-bias:local
```

Open: `http://localhost:7860`

---

## Professional practices checklist

- [x] Secrets excluded in `.gitignore`
- [x] `.dockerignore` excludes env, caches, notebooks, local artifacts
- [x] Multi-stage Docker build (smaller, cleaner runtime)
- [x] Single-port deployment compatible with HF Spaces
- [x] Static frontend served by backend (no second process)
- [ ] Add CI secret scanning (recommended)
- [ ] Add dependency pinning/lock files for strict reproducibility (recommended)

---

## Recommended optional next step

Add GitHub secret scanning (e.g., Gitleaks) in CI to prevent accidental future key leaks.
