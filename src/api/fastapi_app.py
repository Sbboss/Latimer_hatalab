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
from src.config import (
    AZURE_MODEL_DEPLOYMENTS,
    AZURE_DEFAULT_MODEL,
    default_model_names,
    ordered_model_names,
)
from src.retrieval.rag import (
    build_retrieval_prompt,
    extract_timeline_from_document,
    timeline_response_label,
    retrieve_balanced_documents,
    select_evidence_documents,
)
import re
import json
from concurrent.futures import ThreadPoolExecutor, wait
import os
import time
import hashlib
from threading import Lock
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
import ipaddress
import socket

app = FastAPI(title="Latimer AI Bias Backend")

ANALYZE_RETRIEVAL_CACHE_TTL_SECONDS = int(os.getenv("ANALYZE_RETRIEVAL_CACHE_TTL_SECONDS", "900"))
ANALYZE_EVIDENCE_POOL_SIZE = int(os.getenv("ANALYZE_EVIDENCE_POOL_SIZE", "32"))
ANALYZE_MODEL_TIMEOUT_SECONDS = float(os.getenv("ANALYZE_MODEL_TIMEOUT_SECONDS", "45"))
PAGE_FETCH_TIMEOUT_SECONDS = float(os.getenv("PAGE_FETCH_TIMEOUT_SECONDS", "12"))
PAGE_FETCH_MAX_BYTES = int(os.getenv("PAGE_FETCH_MAX_BYTES", "2000000"))
PAGE_FETCH_MAX_CHARACTERS = int(os.getenv("PAGE_FETCH_MAX_CHARACTERS", "24000"))
_retrieval_cache_lock = Lock()
_retrieval_cache: dict[str, dict] = {}

ANALYSIS_OUTPUT_SCHEMA = {
    "name": "bias_analysis_output",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "overall_bias_score": {"type": "number"},
        "bias_detected": {"type": "boolean"},
        "reasoning_summary": {"type": "string"},
        "categories": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "category": {"type": "string"},
                    "score": {"type": "number"},
                    "strength": {"type": "string", "enum": ["weak", "strong"]},
                    "reflection_question": {"type": "string"},
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
                "required": [
                    "category",
                    "score",
                    "strength",
                    "reflection_question",
                    "grounding",
                    "trigger_phrases",
                ],
            },
        },
    },
    "required": [
        "overall_bias_score",
        "bias_detected",
        "reasoning_summary",
        "categories",
    ],
}

FRONTEND_DIST_DIR = Path("frontend_dist")
if FRONTEND_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST_DIR / "assets"), name="assets")


class QueryRequest(BaseModel):
    text: str
    top_k: int = 8
    model: str | None = None
    models: list[str] | None = None


class UrlRequest(BaseModel):
    url: str


class _PageTextParser(HTMLParser):
    """Collect readable text while prioritizing article and main content."""

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self._content_depth = 0
        self._all_parts: list[str] = []
        self._main_parts: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg", "nav", "footer", "aside"}:
            self._skip_depth += 1
        if tag in {"main", "article"}:
            self._content_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg", "nav", "footer", "aside"} and self._skip_depth:
            self._skip_depth -= 1
        if tag in {"main", "article"} and self._content_depth:
            self._content_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._skip_depth:
            return
        text = " ".join(data.split())
        if not text:
            return
        if self._in_title:
            self.title = f"{self.title} {text}".strip()
        self._all_parts.append(text)
        if self._content_depth:
            self._main_parts.append(text)

    def text(self) -> str:
        parts = self._main_parts if len(" ".join(self._main_parts)) >= 240 else self._all_parts
        return " ".join(parts)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _validated_public_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=400, detail="Enter a complete public http or https URL.")
    if parsed.username or parsed.password or parsed.port not in {None, 80, 443}:
        raise HTTPException(status_code=400, detail="This URL format is unavailable for page analysis.")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise HTTPException(status_code=422, detail="The page host is unavailable.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise HTTPException(status_code=400, detail="Local or private network addresses are unavailable.")
    return parsed.geturl()


def _fetch_page(url: str) -> dict[str, str]:
    current_url = _validated_public_url(url)
    opener = build_opener(_NoRedirect())
    for _ in range(4):
        request = Request(current_url, headers={"User-Agent": "LatimerBiasResearch/1.0"})
        try:
            response = opener.open(request, timeout=PAGE_FETCH_TIMEOUT_SECONDS)
        except HTTPError as exc:
            if exc.code in {301, 302, 303, 307, 308} and exc.headers.get("Location"):
                current_url = _validated_public_url(urljoin(current_url, exc.headers["Location"]))
                continue
            raise HTTPException(status_code=422, detail="This page is unavailable. Check the link and try again.") from exc
        except (TimeoutError, URLError, OSError) as exc:
            raise HTTPException(status_code=504, detail="Page retrieval timed out or failed. Please try another link.") from exc
        with response:
            content_type = response.headers.get_content_type()
            if content_type not in {"text/html", "text/plain"}:
                raise HTTPException(status_code=422, detail="This link provides no readable page text.")
            raw = response.read(PAGE_FETCH_MAX_BYTES + 1)
            if len(raw) > PAGE_FETCH_MAX_BYTES:
                raise HTTPException(status_code=413, detail="This page is too large for one analysis. Paste a shorter excerpt.")
            charset = response.headers.get_content_charset() or "utf-8"
            body = raw.decode(charset, errors="replace")
            if content_type == "text/plain":
                text = " ".join(body.split())
                title = ""
            else:
                parser = _PageTextParser()
                parser.feed(body)
                text = parser.text()
                title = parser.title
            if len(text) < 80:
                raise HTTPException(status_code=422, detail="The page contains too little readable text for analysis.")
            return {"url": current_url, "title": title, "text": text[:PAGE_FETCH_MAX_CHARACTERS]}
    raise HTTPException(status_code=422, detail="This link redirected too many times.")


def _original_question_text(document: dict) -> str:
    question = (document.get("question_text") or "").strip()
    if question:
        return question
    content = str(document.get("content") or "")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("question:"):
            return stripped.split(":", 1)[1].strip()
    return content.splitlines()[0].strip() if content.splitlines() else ""


def _plain_language_question(document: dict) -> str:
    """Turn technical survey labels into readable questions without changing meaning."""

    original = _original_question_text(document)
    source_survey = document.get("source_survey") or (
        "ISSP" if str(document.get("id")).startswith("ISSP_") else "GSS"
    )
    if not original:
        return original

    if source_survey == "GSS":
        compact = re.sub(r"\s+", " ", original).strip(" .")
        if re.search(r"father.?s occupation", compact, flags=re.IGNORECASE):
            return "What work did the respondent's father do while the respondent was growing up?"
        if re.search(r"mother.?s occupation", compact, flags=re.IGNORECASE):
            return "What work did the respondent's mother do while the respondent was growing up?"
        if compact.endswith(("?", "!")):
            return compact
        return f"What does this survey measure: {compact}?"

    occupation_match = re.match(
        r"^(Father|Mother)'s occupation when R was \([^)]*\):.*$",
        original,
        flags=re.IGNORECASE,
    )
    if occupation_match:
        parent = occupation_match.group(1).lower()
        return (
            f"What occupation did the respondent's {parent} have when the "
            "respondent was about 15 years old?"
        )

    plain = original
    plain = re.sub(r"\bR\b", "the respondent", plain)
    plain = re.sub(r"\[Country\]", "the respondent's country", plain, flags=re.IGNORECASE)
    plain = re.sub(
        r"\s*:\s*(?:ILO|ISCO|NACE|SIOPS|ISEI|EGP)\b.*$",
        "",
        plain,
        flags=re.IGNORECASE,
    )
    plain = re.sub(r"\s+", " ", plain).strip(" .")
    question_starter = re.match(
        r"^(who|what|when|where|why|how|do|does|did|is|are|was|were|can|could|would|should|has|have|which)\b",
        plain,
        flags=re.IGNORECASE,
    )
    if plain and not plain.endswith("?") and not question_starter:
        plain = (
            "How strongly does the respondent agree or disagree with this statement: "
            f"{plain}?"
        )
    elif plain and not plain.endswith(("?", "!")):
        plain += "?"
    return plain or original


def _document_to_evidence(document: dict) -> dict:
    source_survey = document.get("source_survey") or (
        "ISSP" if str(document.get("id")).startswith("ISSP_") else "GSS"
    )
    timeline = extract_timeline_from_document(document)
    waves = document.get("available_waves") or []
    if not waves and document.get("year_start") is not None:
        start = document.get("year_start")
        end = document.get("year_end")
        waves = [str(start)] if start == end else [str(start), str(end)]

    response_options = document.get("response_options") or []
    response_option_count = len(response_options)

    return {
        "recordId": document.get("id"),
        "question": _plain_language_question(document),
        "originalQuestion": _original_question_text(document),
        "category": ", ".join(document.get("categories") or []),
        "insight": "",
        "timeline": timeline,
        "timelineResponseLabel": timeline_response_label(document),
        "survey": source_survey,
        "module": document.get("module_name"),
        "sourceDataset": document.get("source_dataset"),
        "availableWaves": [str(wave) for wave in waves],
        "countryCount": document.get("country_count"),
        "annotationStatus": document.get("annotation_status"),
        "uncertain": bool(document.get("annotation_uncertain")),
        "limitations": document.get("limitations"),
        "responseOptionCount": response_option_count,
        "responseOptions": response_options[:8],
    }


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
    configured = list(AZURE_MODEL_DEPLOYMENTS.keys()) or [AZURE_DEFAULT_MODEL]
    ordered = ordered_model_names(configured)
    return {"models": ordered, "defaultModels": default_model_names(ordered)}


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
    return {"status": "ok", "message": "Frontend build unavailable. API is running."}


@app.post("/extract-url")
def extract_url(request: UrlRequest):
    return _fetch_page(request.url)


@app.post("/api/extract-url")
def extract_url_api(request: UrlRequest):
    return extract_url(request)


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
    per_survey_k = max(1, (request.top_k + 1) // 2)
    documents = retrieve_balanced_documents(
        embedding,
        query_text=request.text,
        per_survey_k=per_survey_k,
    )[: request.top_k]

    prompt = build_retrieval_prompt(request.text, documents)
    completion = create_completion(client, prompt, model=request.model)

    return {
        "query": request.text,
        "top_k": request.top_k,
        "model": request.model,
        "documents": [doc for doc in documents],
        "response": completion.text,
        "thinking": completion.thinking,
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
    evidence_pool_size = max(request.top_k, ANALYZE_EVIDENCE_POOL_SIZE)
    per_survey_pool_size = max(2, (evidence_pool_size + 1) // 2)
    cache_key = hashlib.sha256(
        f"{text}||{request.top_k}||{per_survey_pool_size}||balanced-v1".encode("utf-8")
    ).hexdigest()
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
        documents = retrieve_balanced_documents(
            embedding,
            query_text=text,
            per_survey_k=per_survey_pool_size,
        )
        with _retrieval_cache_lock:
            _retrieval_cache[cache_key] = {
                "embedding": embedding,
                "documents": documents,
                "expires_at": now_ts + ANALYZE_RETRIEVAL_CACHE_TTL_SECONDS,
            }

    configured_models = ordered_model_names(
        list(AZURE_MODEL_DEPLOYMENTS.keys()) or [AZURE_DEFAULT_MODEL]
    )
    requested_models = request.models or default_model_names(configured_models)
    unknown_models = [name for name in requested_models if name not in configured_models]
    if unknown_models:
        raise HTTPException(status_code=400, detail="One or more selected models are unavailable.")
    model_names = [name for name in configured_models if name in requested_models]
    if not model_names:
        raise HTTPException(status_code=400, detail="Choose at least one available model.")

    # Build RAG grounded prompt once (shared across model fan-out)
    prompt = build_retrieval_prompt(text, documents[: request.top_k])

    def run_model(model_name: str):
        model_status = "ok"
        model_error = None
        thinking_trace = None
        try:
            # Generous budget: reasoning models (e.g. GPT-5.5) spend part of
            # this on internal reasoning tokens before producing the visible
            # JSON answer, on top of the JSON output itself. Claude gets an
            # extended-thinking scratchpad on top of this budget separately.
            completion = create_completion(
                client,
                prompt,
                model=model_name,
                max_tokens=3000,
                response_schema=ANALYSIS_OUTPUT_SCHEMA,
                strict_json=True,
            )
            raw = completion.text
            thinking_trace = completion.thinking
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
                    "The model declined this input through its safety policy. Try another configured model, "
                    "or rephrase the input."
                )
            elif model_error == "reasoning_budget_exhausted":
                reasoning_summary = (
                    "This model spent its entire token budget on internal reasoning and returned no "
                    "answer. Try a shorter input, or increase max_tokens for this model."
                )
            else:
                reasoning_summary = "This model produced no output for the request."
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
            evidence_documents = select_evidence_documents(
                documents,
                cat_label,
                per_survey_limit=2,
            )
            evidence = [_document_to_evidence(document) for document in evidence_documents]

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
                            "reflectionQuestion": cat.get("reflection_question", "").strip()
                            or "What assumption about this person or group might this wording invite?",
                            "rewriteReason": cat.get("grounding", reasoning_summary),
                            "dimensions": [
                                {"label": cat_label, "score": cat_score},
                            ],
                            "evidence": evidence,
                        }
                    )

        return {
            "model": model_name,
            "status": model_status,
            "error": model_error,
            "overallScore": bias_score,
            "confidence": 0.72,
            "categories": category_scores,
            "thinking": thinking_trace,
            "result": {
                "inputText": text,
                "overallScore": bias_score,
                "confidence": 0.72,
                "signalLabel": "Bias signal detected" if highlights else "No signal",
                "reasoningSummary": reasoning_summary,
                "thinking": thinking_trace,
                "highlights": highlights,
            },
        }

    def timed_out_output(model_name: str) -> dict:
        return {
            "model": model_name,
            "status": "error",
            "error": "completion_timeout",
            "overallScore": 0.5,
            "confidence": 0.0,
            "categories": [],
            "thinking": None,
            "result": {
                "inputText": text,
                "overallScore": 0.5,
                "confidence": 0.0,
                "signalLabel": "Analysis unavailable",
                "reasoningSummary": "This model exceeded the analysis time limit. Other results remain available.",
                "thinking": None,
                "highlights": [],
            },
        }

    # Fan out model calls in parallel while keeping output order stable. A
    # bounded wait prevents a provider stall from leaving the browser at 92%.
    ordered_outputs: dict[str, dict] = {}
    max_workers = min(8, max(1, len(model_names)))
    executor = ThreadPoolExecutor(max_workers=max_workers)
    try:
        future_to_model = {executor.submit(run_model, model_name): model_name for model_name in model_names}
        completed, pending = wait(
            future_to_model,
            timeout=ANALYZE_MODEL_TIMEOUT_SECONDS,
        )
        for future in completed:
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
                    "thinking": None,
                    "result": {
                        "inputText": text,
                        "overallScore": 0.5,
                        "confidence": 0.72,
                        "signalLabel": "No signal",
                        "reasoningSummary": "This model produced no output for the request.",
                        "thinking": None,
                        "highlights": [],
                    },
                }
        for future in pending:
            model_name = future_to_model[future]
            future.cancel()
            ordered_outputs[model_name] = timed_out_output(model_name)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    model_outputs = [ordered_outputs[m] for m in model_names if m in ordered_outputs]

    return {"models": model_outputs}


@app.post("/api/analyze")
def analyze_api(request: QueryRequest):
    return analyze(request)
