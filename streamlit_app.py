from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import json
import re

import streamlit as st

from src.config import AZURE_MODEL_DEPLOYMENTS
from src.llm.azure_openai_client import create_completion, openai_client, resolve_model_provider
from src.llm.azure_openai_client import create_embedding
from src.retrieval.rag import retrieve_top_documents, build_retrieval_prompt, SYSTEM_BIAS_PROMPT


APP_MODELS = list(AZURE_MODEL_DEPLOYMENTS.keys())
DEFAULT_MAX_TOKENS = 2048


@dataclass
class ModelResult:
    model: str
    provider: str
    deployment: str
    elapsed_seconds: float
    ok: bool
    text: str


def model_badge(provider: str) -> str:
    return "Anthropic Foundry" if provider == "anthropic" else "OpenAI-compatible"


def ask_model(model_name: str, prompt: str, max_tokens: int, temperature: float) -> ModelResult:
    provider = resolve_model_provider(model_name)
    deployment = AZURE_MODEL_DEPLOYMENTS.get(model_name, model_name)
    started = time.perf_counter()
    try:
        # Embeddings always use the Azure OpenAI-compatible endpoint.
        embedding_client = openai_client()
        client = None if provider == "anthropic" else openai_client()

        # --- RAG retrieval step ---
        embedding = create_embedding(embedding_client, prompt)
        docs = retrieve_top_documents(embedding, query_text=prompt, top_k=8)
        user_prompt = build_retrieval_prompt(prompt, docs)

        completion = create_completion(
            client=client,
            prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model_name,
            system_prompt=SYSTEM_BIAS_PROMPT,
        )
        return ModelResult(
            model=model_name,
            provider=provider,
            deployment=deployment,
            elapsed_seconds=time.perf_counter() - started,
            ok=True,
            text=completion.text.strip() or "(empty response)",
        )
    except Exception as exc:
        return ModelResult(
            model=model_name,
            provider=provider,
            deployment=deployment,
            elapsed_seconds=time.perf_counter() - started,
            ok=False,
            text=str(exc),
        )


def ask_all_models(prompt: str, models: list[str], max_tokens: int, temperature: float) -> list[ModelResult]:
    results_by_model: dict[str, ModelResult] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(models))) as executor:
        futures = {
            executor.submit(ask_model, model_name, prompt, max_tokens, temperature): model_name
            for model_name in models
        }
        for future in as_completed(futures):
            model_name = futures[future]
            results_by_model[model_name] = future.result()

    return [results_by_model[model_name] for model_name in models]


def page_styles(light_mode: bool = False) -> None:
    if light_mode:
        css = """
        <style>
            .stApp {
                background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
                color: #0f172a;
            }
            [data-testid="stSidebar"] {
                background: #ffffff;
                border-right: 1px solid rgba(0,0,0,0.08);
            }
            .hero {
                background: #ffffff;
                border: 1px solid rgba(0,0,0,0.08);
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            }
            .model-card {
                background: #ffffff;
                border: 1px solid rgba(0,0,0,0.08);
                box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            }
        </style>
        """
    else:
        css = """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(81, 77, 255, 0.18), transparent 34rem),
                    radial-gradient(circle at top right, rgba(0, 180, 216, 0.14), transparent 30rem),
                    linear-gradient(180deg, #07111f 0%, #0b1020 42%, #0f172a 100%);
                color: #e5edf7;
            }
            [data-testid="stSidebar"] {
                background: rgba(15, 23, 42, 0.92);
                border-right: 1px solid rgba(148, 163, 184, 0.18);
            }
            .hero {
                padding: 1.35rem 1.45rem;
                border: 1px solid rgba(148, 163, 184, 0.25);
                border-radius: 1.3rem;
                background: linear-gradient(135deg, rgba(30, 41, 59, 0.82), rgba(15, 23, 42, 0.62));
                box-shadow: 0 24px 70px rgba(2, 8, 23, 0.36);
                margin-bottom: 1rem;
            }
            .hero h1 {
                margin: 0;
                font-size: 2.3rem;
                line-height: 1.05;
                letter-spacing: -0.05em;
            }
            .hero p {
                margin: 0.55rem 0 0;
                color: #aebbd0;
                font-size: 1.02rem;
            }
            .model-card {
                padding: 1rem;
                border: 1px solid rgba(148, 163, 184, 0.20);
                border-radius: 1rem;
                background: rgba(15, 23, 42, 0.68);
                min-height: 14rem;
                box-shadow: 0 18px 50px rgba(2, 8, 23, 0.24);
            }
            .model-title {
                font-weight: 800;
                font-size: 1.05rem;
                color: #f8fafc;
                margin-bottom: 0.2rem;
            }
            .model-meta {
                font-size: 0.78rem;
                color: #94a3b8;
                margin-bottom: 0.85rem;
            }
            .status-ok {
                color: #86efac;
                font-weight: 700;
            }
            .status-error {
                color: #fca5a5;
                font-weight: 700;
            }
            div[data-testid="stChatMessage"] {
                border-radius: 1.1rem;
                border: 1px solid rgba(148, 163, 184, 0.16);
                background: rgba(15, 23, 42, 0.56);
            }
        </style>
        """

    st.markdown(css, unsafe_allow_html=True)


def _extract_bias_json(raw: str) -> dict | None:
    raw = raw.strip()

    def try_load_json(text: str) -> dict | None:
        text = text.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            return None

    def extract_balanced_json(text: str) -> str | None:
        start = text.find("{")
        if start == -1:
            return None

        depth = 0
        for index, char in enumerate(text[start:], start=start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start:index + 1]
        return None

    # Prefer tagged JSON, allowing for a missing closing tag.
    tagged = re.search(r"<BIAS_JSON>([\s\S]*?)(</BIAS_JSON>|$)", raw, re.IGNORECASE)
    if tagged:
        content = tagged.group(1).strip()
        content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.IGNORECASE).strip()
        parsed = try_load_json(content)
        if parsed is not None:
            return parsed
        raw = content

    # Remove common apology/safety fragments before parsing.
    cleaned = re.sub(r"I'?m sorry[\s\S]*$", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"cannot assist[\s\S]*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"please use the following format[\s\S]*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    parsed = try_load_json(cleaned)
    if parsed is not None:
        return parsed

    candidate = extract_balanced_json(cleaned)
    if candidate is not None:
        parsed = try_load_json(candidate)
        if parsed is not None:
            return parsed

    return None


def render_result_card(result: ModelResult) -> None:
    status_class = "status-ok" if result.ok else "status-error"
    status_text = "Ready" if result.ok else "Error"
    st.markdown(
        f"""
        <div class="model-card">
            <div class="model-title">{result.model}</div>
            <div class="model-meta">
                {model_badge(result.provider)} · deployment: <code>{result.deployment}</code> · {result.elapsed_seconds:.1f}s ·
                <span class="{status_class}">{status_text}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not result.ok:
        st.error(result.text)
        return

    data = _extract_bias_json(result.text)

    if data is None:
        st.markdown(result.text)
        return

    overall = data.get("overall_bias_score", 0)
    detected = data.get("bias_detected", False)

    st.markdown("### Bias Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Overall Bias Score", f"{overall:.2f}")
    with col2:
        st.metric("Bias Detected", "Yes" if detected else "No")

    categories = data.get("categories", [])

    if categories:
        st.markdown("#### Detected Bias Categories")
        for cat in categories:
            name = cat.get("category")
            score = cat.get("score", 0)
            strength = cat.get("strength", "")

            st.markdown(f"**{name}** — score: {score:.2f} ({strength})")
            st.progress(min(max(score, 0.0), 1.0))

            triggers = cat.get("trigger_phrases", [])
            if triggers:
                st.markdown("**Trigger phrases:**")
                for t in triggers:
                    phrase = t.get("phrase")
                    explanation = t.get("explanation")
                    st.markdown(f"• **\"{phrase}\"** — {explanation}")

            grounding = cat.get("grounding")
            if grounding:
                st.markdown(f"_Grounding:_ {grounding}")

            st.divider()

    summary = data.get("reasoning_summary")
    if summary:
        st.markdown("#### Summary")
        st.markdown(summary)


def initialize_state() -> None:
    if "turns" not in st.session_state:
        st.session_state.turns = []


def main() -> None:
    st.set_page_config(
        page_title="Latimer LLM Arena",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    if "light_mode" not in st.session_state:
        st.session_state.light_mode = False

    with st.sidebar:
        st.session_state.light_mode = st.toggle("Light theme", value=st.session_state.light_mode)

    page_styles(st.session_state.light_mode)
    initialize_state()

    st.markdown(
        """
        <div class="hero">
            <h1>⚖️ Latimer LLM Arena</h1>
            <p>Send one prompt and compare the answers from GPT-5.5, Claude Opus 4.6, and Llama 3.3 70B through Azure AI Foundry.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Run settings")
        selected_models = st.multiselect(
            "Models to compare",
            options=APP_MODELS,
            default=APP_MODELS,
            help="These display names map to Azure deployment names from AZURE_MODEL_DEPLOYMENTS_JSON.",
        )
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.5, value=0.2, step=0.05)
        st.caption(f"Using a fixed {DEFAULT_MAX_TOKENS}-token generation limit for better JSON completeness.")

        st.divider()
        st.caption("Configured deployments")
        for display, deployment in AZURE_MODEL_DEPLOYMENTS.items():
            st.markdown(f"- **{display}** → `{deployment}`")

        if st.button("Clear chat", use_container_width=True):
            st.session_state.turns = []
            st.rerun()

    if not APP_MODELS:
        st.error("No models configured. Set AZURE_MODEL_DEPLOYMENTS_JSON in .env.")
        return

    if not selected_models:
        st.warning("Select at least one model in the sidebar.")

    for turn in st.session_state.turns:
        with st.chat_message("user"):
            st.markdown(turn["prompt"])
        with st.chat_message("assistant"):
            cols = st.columns(len(turn["results"]))
            for col, result in zip(cols, turn["results"]):
                with col:
                    render_result_card(result)

    prompt = st.chat_input("Ask all 3 LLMs anything…")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Calling Azure AI Foundry deployments…"):
                results = ask_all_models(prompt, selected_models, DEFAULT_MAX_TOKENS, temperature)

            cols = st.columns(len(results))
            for col, result in zip(cols, results):
                with col:
                    render_result_card(result)

        st.session_state.turns.append({"prompt": prompt, "results": results})


if __name__ == "__main__":
    main()