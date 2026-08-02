from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

from src.llm.azure_openai_client import (
    ModelCompletionError,
    create_embedding,
    create_completion,
    openai_client,
)
from src.config import AZURE_MODEL_DEPLOYMENTS, AZURE_DEFAULT_MODEL
from src.retrieval.rag import build_retrieval_prompt, retrieve_top_documents, extract_timeline_from_document
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time
import hashlib
from threading import Lock

app = FastAPI(title="Latimer AI Bias Backend")

ANALYZE_RETRIEVAL_CACHE_TTL_SECONDS = int(os.getenv("ANALYZE_RETRIEVAL_CACHE_TTL_SECONDS", "900"))
_retrieval_cache_lock = Lock()
_retrieval_cache: dict[str, dict] = {}

ANALYSIS_OUTPUT_SCHEMA = {
    "name": "bias_analysis_output",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "overall_bias_score": {"type": "number"},
        "reasoning_summary": {"type": "string"},
        "categories": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "category": {"type": "string"},
                    "score": {"type": "number"},
                    "grounding": {"type": "string"},
                    "trigger_phrases": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "phrase": {"type": "string"},
                                "explanation": {"type": "string"},
                                "replacement": {"type": "string"},
                            },
                            # OpenAI strict json_schema mode requires every
                            # property to be listed as required (nothing may
                            # be omitted); without this the whole schema is
                            # rejected with a 400, silently falling back to
                            # unstructured prompting for every single request.
                            "required": ["phrase", "explanation", "replacement"],
                        },
                    },
                },
                "required": ["category", "score", "grounding", "trigger_phrases"],
            },
        },
    },
    "required": ["overall_bias_score", "reasoning_summary", "categories"],
}

FRONTEND_DIST_DIR = Path("frontend_dist")
if FRONTEND_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST_DIR / "assets"), name="assets")


class QueryRequest(BaseModel):
    text: str
    top_k: int = 5
    model: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/health")
def health_api():
    return health()


@app.get("/ready")
def ready():
    return {"status": "ready"}


@app.get("/api/ready")
def ready_api():
    return ready()


@app.get("/models")
def models():
    """Expose the actual configured model deployments so the frontend never
    hardcodes/guesses model names that may drift from .env configuration."""
    return {"models": list(AZURE_MODEL_DEPLOYMENTS.keys()) or [AZURE_DEFAULT_MODEL]}


@app.get("/api/models")
def models_api():
    return models()


# index.html must never be cached: its referenced asset hashes change on
# every build, so a stale cached copy points at 404'd assets (blank page).
# The hashed /assets themselves stay long-cacheable via StaticFiles defaults.
_INDEX_NO_CACHE_HEADERS = {"Cache-Control": "no-cache, no-store, must-revalidate"}


def _index_response() -> FileResponse:
    return FileResponse(FRONTEND_DIST_DIR / "index.html", headers=_INDEX_NO_CACHE_HEADERS)


@app.get("/")
def serve_frontend_root():
    index_file = FRONTEND_DIST_DIR / "index.html"
    if index_file.exists():
        return _index_response()
    return {"status": "ok", "message": "Frontend build not found. API is running."}


@app.get("/{full_path:path}")
def serve_frontend_spa(full_path: str):
    # Keep API routes handled by declared endpoints above.
    # For non-API paths, serve SPA index fallback when available.
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="Not Found")

    index_file = FRONTEND_DIST_DIR / "index.html"
    if index_file.exists():
        return _index_response()
    raise HTTPException(status_code=404, detail="Not Found")


@app.post("/bias-query")
def bias_query(request: QueryRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Request text is required")

    client = openai_client()
    embedding = create_embedding(client, request.text)
    documents = retrieve_top_documents(embedding, top_k=request.top_k)

    prompt = build_retrieval_prompt(request.text, documents)
    answer = create_completion(client, prompt, model=request.model)

    return {
        "query": request.text,
        "top_k": request.top_k,
        "model": request.model,
        "documents": [doc for doc in documents],
        "response": answer,
    }


@app.post("/api/bias-query")
def bias_query_api(request: QueryRequest):
    return bias_query(request)


@app.post("/analyze")
def analyze(request: QueryRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Request text is required")

    client = openai_client()

    text = request.text

    # Retrieve vector evidence once (shared grounding context), cached by input hash.
    cache_key = hashlib.sha256(f"{text}||{request.top_k}".encode("utf-8")).hexdigest()
    now_ts = time.time()

    embedding = None
    documents = None
    with _retrieval_cache_lock:
        cached = _retrieval_cache.get(cache_key)
        if cached and cached.get("expires_at", 0) > now_ts:
            embedding = cached.get("embedding")
            documents = cached.get("documents")
        elif cached:
            _retrieval_cache.pop(cache_key, None)

    if embedding is None or documents is None:
        embedding = create_embedding(client, text)
        documents = retrieve_top_documents(embedding, top_k=request.top_k)
        with _retrieval_cache_lock:
            _retrieval_cache[cache_key] = {
                "embedding": embedding,
                "documents": documents,
                "expires_at": now_ts + ANALYZE_RETRIEVAL_CACHE_TTL_SECONDS,
            }

    model_names = list(AZURE_MODEL_DEPLOYMENTS.keys()) or [AZURE_DEFAULT_MODEL]

    # Build RAG grounded prompt once (shared across model fan-out)
    prompt = build_retrieval_prompt(text, documents)

    def run_model(model_name: str):
        model_status = "ok"
        model_error = None
        try:
            # Generous budget: reasoning models (e.g. GPT-5.5) spend part of
            # this on internal reasoning tokens before producing the visible
            # JSON answer, on top of the JSON output itself.
            raw = create_completion(
                client,
                prompt,
                model=model_name,
                max_tokens=3000,
                response_schema=ANALYSIS_OUTPUT_SCHEMA,
                strict_json=True,
            )
        except ModelCompletionError as e:
            print("⚠️ model call failed", model_name, e)
            model_status = "error"
            model_error = getattr(e, "code", "completion_failed")
            raw = "{}"
        except Exception as e:
            print("⚠️ model call failed", model_name, e)
            model_status = "error"
            model_error = "completion_failed"
            raw = "{}"

        # log raw model output
        print("\n==============================")
        print(f"MODEL: {model_name}")
        print("RAW OUTPUT:")
        print(raw)
        print("==============================\n")

        # ---- normalize model output so we can parse JSON ----
        # handle cases where SDK returned an object repr instead of text
        if hasattr(raw, "choices"):
            try:
                text_output = raw.choices[0].message.content or ""
            except Exception:
                text_output = str(raw)
        else:
            text_output = str(raw)

        text_output = text_output.strip()

        # remove markdown code fences
        if "```" in text_output:
            text_output = text_output.replace("```json", "").replace("```", "").strip()

        # sometimes SDK returns object repr; try extracting JSON block
        if "{" in text_output:
            start = text_output.find("{")
            end = text_output.rfind("}")
            if end != -1:
                text_output = text_output[start:end+1]
            else:
                text_output = text_output[start:]

        # try parsing JSON
        try:
            data = json.loads(text_output)
        except Exception:
            # attempt recovery for malformed JSON often produced by models
            fixed = text_output

            # remove markdown fences if they slipped through
            fixed = fixed.replace("```json", "").replace("```", "").strip()

            # normalize common smart quotes that can break strict JSON parsing
            fixed = fixed.replace("“", '"').replace("”", '"').replace("’", "'")

            # remove trailing commas before object/array close, across newlines
            fixed = re.sub(r",(?=\s*[}\]])", "", fixed)

            # try again
            try:
                data = json.loads(fixed)
            except Exception:
                print("⚠️ Could not parse model JSON. Raw output:\n", text_output)
                data = {}

        bias_score = float(data.get("overall_bias_score", 0.5))
        categories = data.get("categories", [])
        reasoning_summary = data.get("reasoning_summary", "")

        if model_status == "error":
            if model_error == "content_filter_blocked":
                reasoning_summary = (
                    "Blocked by Azure's content filter before reaching the model. "
                    "Try less explicit phrasing, or adjust the filter severity threshold for this "
                    "deployment in the Azure AI Foundry portal (Guardrails + controls > Content filters)."
                )
            elif model_error == "model_refusal":
                reasoning_summary = (
                    "The model itself declined to analyze this input (a Claude safety refusal, not an "
                    "Azure content filter block — Foundry guardrails aren't yet configurable for Claude "
                    "deployments). Try another configured model, or rephrase the input."
                )
            elif model_error == "reasoning_budget_exhausted":
                reasoning_summary = (
                    "This model spent its entire token budget on internal reasoning and returned no "
                    "answer. Try a shorter input, or increase max_tokens for this model."
                )
            else:
                reasoning_summary = "Model could not produce an output for this request."
            categories = []
            bias_score = 0.5

        # create slightly different dimension scores per model
        dim1 = round(bias_score, 2)
        dim2 = round(max(0.1, min(1.0, bias_score * 0.6)), 2)
        dim3 = round(max(0.05, min(1.0, bias_score * 0.4)), 2)

        highlights = []
        category_scores = []

        for cat in categories:
            cat_label = cat.get("category", "Bias")
            cat_score = float(cat.get("score", bias_score))
            category_scores.append({"category": cat_label, "score": cat_score})

            triggers = cat.get("trigger_phrases", [])

            for trig in triggers:
                phrase = trig.get("phrase", "")
                explanation = trig.get("explanation", reasoning_summary)
                replacement = trig.get("replacement", "").strip() or "Use more neutral wording."

                for m in re.finditer(re.escape(phrase), text, re.IGNORECASE):
                    start, end = m.start(), m.end()

                    highlights.append(
                        {
                            "id": f"{model_name}-{phrase}-{start}",
                            "phrase": text[start:end],
                            "start": start,
                            "end": end,
                            "category": cat_label,
                            "score": cat_score,
                            "explanation": explanation,
                            "replacement": replacement,
                            "rewriteReason": cat.get("grounding", reasoning_summary),
                            "dimensions": [
                                {"label": cat_label, "score": cat_score},
                            ],
                            "evidence": [
                                {
                                    "question": d.get("content", ""),
                                    "category": ", ".join(d.get("categories", [])),
                                    "insight": "Derived from GSS survey evidence retrieved via vector search.",
                                    "timeline": extract_timeline_from_document(d)
                                }
                                for d in documents[:2]
                            ],
                        }
                    )

        return {
            "model": model_name,
            "status": model_status,
            "error": model_error,
            "overallScore": bias_score,
            "confidence": 0.72,
            "categories": category_scores,
            "result": {
                "inputText": text,
                "overallScore": bias_score,
                "confidence": 0.72,
                "signalLabel": "Bias signal detected" if highlights else "No signal",
                "reasoningSummary": reasoning_summary,
                "highlights": highlights,
            },
        }

    # Fan out model calls in parallel while keeping output order stable.
    ordered_outputs: dict[str, dict] = {}
    max_workers = min(8, max(1, len(model_names)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_model = {executor.submit(run_model, model_name): model_name for model_name in model_names}
        for future in as_completed(future_to_model):
            model_name = future_to_model[future]
            try:
                ordered_outputs[model_name] = future.result()
            except Exception as e:
                print("⚠️ parallel model worker failed", model_name, e)
                ordered_outputs[model_name] = {
                    "model": model_name,
                    "status": "error",
                    "error": "completion_failed",
                    "overallScore": 0.5,
                    "confidence": 0.72,
                    "categories": [],
                    "result": {
                        "inputText": text,
                        "overallScore": 0.5,
                        "confidence": 0.72,
                        "signalLabel": "No signal",
                        "reasoningSummary": "Model could not produce an output for this request.",
                        "highlights": [],
                    },
                }

    model_outputs = [ordered_outputs[m] for m in model_names if m in ordered_outputs]

    return {"models": model_outputs}


@app.post("/api/analyze")
def analyze_api(request: QueryRequest):
    return analyze(request)
