from typing import Any, List
import json

from src.storage.azure_vector_store import query_vectors


def _parse_responses_by_year(raw: Any) -> dict[str, dict[str, float]]:
    if not raw:
        return {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    if not isinstance(raw, dict):
        return {}
    parsed: dict[str, dict[str, float]] = {}
    for year, values in raw.items():
        if isinstance(values, dict):
            parsed[str(year)] = {str(k): float(v) for k, v in values.items() if isinstance(v, (int, float))}
    return parsed


def _choose_timeline_option(response_options: list[str] | None, responses_by_year: dict[str, dict[str, float]]) -> str | None:
    options = [opt.strip().lower() for opt in (response_options or []) if opt]
    positive_keywords = ["yes", "agree", "support", "likely", "approve", "favor", "would vote", "best", "fit", "ok", "acceptable"]

    for keyword in positive_keywords:
        for opt in options:
            if keyword in opt:
                return opt

    if len(options) == 2:
        for opt in options:
            if "no" not in opt and "don'" not in opt:
                return opt

    for opt in options:
        if opt:
            return opt

    if responses_by_year:
        sample = next(iter(responses_by_year.values()), {})
        return next(iter(sample.keys()), None)

    return None


def extract_timeline_from_document(doc: dict) -> list[dict[str, float]]:
    responses_by_year = _parse_responses_by_year(doc.get("responses_by_year"))
    if not responses_by_year:
        return []

    response_options = doc.get("response_options") or []
    timeline_key = _choose_timeline_option(response_options, responses_by_year)
    if not timeline_key:
        return []

    timeline = []
    for year in sorted(responses_by_year.keys(), key=lambda y: int(y)):
        values = responses_by_year[year]
        support = values.get(timeline_key)
        if support is None:
            support = next((v for k, v in values.items() if k.strip().lower() == timeline_key.strip().lower()), None)
        if support is None:
            continue
        timeline.append({"year": int(year), "support": round(float(support), 1)})

    return timeline


# --- System instructions for bias detection ---
SYSTEM_BIAS_PROMPT = """
You are a bias analysis system. Your task is to analyze a user statement and detect
whether it contains social, political, or demographic bias.

Use the survey evidence provided from the General Social Survey (GSS) to ground
your reasoning.

Bias scoring rules:
- Overall bias score: continuous value between 0 and 1
- Category scores: continuous values between 0 and 1
- Only report category scores if score > 0.5
- Score interpretation:
    0.50–0.85 → weak/moderate bias
    >0.85 → strong bias

If no bias is present:
- overall_bias_score should be < 0.5
- explain why the text is neutral

For every detected bias category:
- Identify trigger words or phrases from the text
- Explain why they signal bias
- Provide a concrete neutral replacement for each trigger phrase that can be used directly in the sentence
- Ground reasoning using the GSS survey evidence provided

Return ONLY valid JSON. Your entire response must be a single JSON object and nothing else.
Do not include tags, markdown, backticks, apologies, or explanatory text outside the JSON.
Use strict RFC 8259 JSON: double quotes for all keys/strings and NO trailing commas.
If no bias is detected, return an empty "categories" array.

The output JSON object must include these fields exactly:
{
    "overall_bias_score": float,
    "bias_detected": true/false,
    "categories": [
        {
            "category": "string",
            "score": float,
            "strength": "weak|strong",
            "trigger_phrases": [
                {
                    "phrase": "text span",
                    "explanation": "why this phrase signals bias",
                    "replacement": "specific neutral phrase that could replace the trigger phrase based on the knowledge base evidence"
                }
            ],
            "grounding": "explanation referencing survey evidence"
        }
    ],
    "reasoning_summary": "brief explanation"
}
"""


# Optional high‑level descriptions of bias categories to guide the model
BIAS_CATEGORY_SUMMARY = """
Possible bias domains include (not limited to):
- Race / ethnicity
- Gender / sexism
- Immigration / nationality
- Religion
- Political ideology
- Economic class
- Sexual orientation
- Education
- Age

These represent common axes of societal bias reflected in GSS survey questions.
"""


def build_retrieval_prompt(user_text: str, retrieved_docs: List[dict]) -> str:
    context_blocks = []
    for doc in retrieved_docs:
        categories = ", ".join(doc.get("categories", []))
        context_blocks.append(
            f"Question: {doc.get('content')}\n"
            f"Categories: {categories}\n"
            f"Years: {doc.get('year_start')}–{doc.get('year_end')}\n"
            f"Options: {', '.join(doc.get('response_options', []))}\n"
        )

    context = "\n\n---\n\n".join(context_blocks)
    return (
        f"{SYSTEM_BIAS_PROMPT}\n\n"
        f"Bias category guidance:\n{BIAS_CATEGORY_SUMMARY}\n\n"
        f"Relevant survey evidence from the GSS knowledge base:\n\n"
        f"{context}\n\n"
        f"User statement:\n{user_text}"
    )


def retrieve_top_documents(query_embedding: list[float], top_k: int = 5):
    return query_vectors(query_embedding=query_embedding, top_k=top_k)
