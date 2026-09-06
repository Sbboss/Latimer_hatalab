from typing import Any, List
import json

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
    options = [(opt.strip(), opt.strip().lower()) for opt in (response_options or []) if opt]
    positive_keywords = ["yes", "agree", "support", "likely", "approve", "favor", "would vote", "best", "fit", "ok", "acceptable"]

    for keyword in positive_keywords:
        for original, normalized in options:
            if keyword in normalized:
                return original

    if len(options) == 2:
        for original, normalized in options:
            if "no" not in normalized and "don'" not in normalized:
                return original

    for original, _normalized in options:
        if original:
            return original

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


def timeline_response_label(doc: dict) -> str | None:
    """Return the response category represented by a charted time series."""
    responses_by_year = _parse_responses_by_year(doc.get("responses_by_year"))
    option = _choose_timeline_option(doc.get("response_options") or [], responses_by_year)
    if option and "=" in option:
        return option.split("=", 1)[1].strip()
    return option


# --- System instructions for bias detection ---
SYSTEM_BIAS_PROMPT = """
You are a bias analysis system. Your task is to analyze a user statement and detect
whether it contains social, political, or demographic bias.

Use the survey-question evidence provided from the General Social Survey (GSS)
and International Social Survey Programme (ISSP) to ground your reasoning.
Survey questions reveal what researchers measured; they do not, by themselves,
prove that the user's wording is biased or reveal what the public believed.

Bias scoring rules:
- Overall bias score: continuous value between 0 and 1
- Category scores: continuous values between 0 and 1
- Only report category scores if score > 0.5
- Score interpretation:
    0.50–0.85 → weak/moderate bias
    >0.85 → strong bias

When no bias is present:
- overall_bias_score should be < 0.5
- explain why the text is neutral

For every detected bias category:
- Identify trigger words or phrases from the text
- Explain why they signal bias
- Provide a concrete neutral replacement for each trigger phrase that can be used directly in the sentence
- Ask one non-accusatory reflection question that helps the user examine the
  assumption themselves before offering a replacement.
- Ground reasoning using the GSS/ISSP survey evidence provided. Only claim a direct
  evidentiary link when a retrieved item genuinely addresses the same topic
  or demographic axis as the trigger phrase. If the retrieved evidence is
  only loosely or tangentially related to this specific bias, say so plainly
  in "grounding" (e.g. "the retrieved GSS items lack a direct connection here;
  this judgment is based on documented patterns of coded language rather
  than a specific survey item") instead of overstating the connection.

Return ONLY valid JSON. Your entire response must be a single JSON object and nothing else.
Avoid the word "not" in user-facing explanation, replacement, grounding, reflection,
and summary fields. Preserve meaning through direct alternatives such as "lacks",
"fails to", or "no evidence of". The trigger phrase may preserve the user's exact text.
Include tags, markdown, backticks, apologies, or explanatory text only inside the JSON.
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
            "reflection_question": "a concise, non-accusatory question for the user",
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
Possible bias domains include:
- Race / ethnicity
- Gender / sexism
- Immigration / nationality
- Religion
- Political ideology
- Economic class
- Sexual orientation
- Education
- Age
- Disability and access
- Science, technology, and medicine

These represent common axes of societal bias reflected in GSS and ISSP survey
questions. Use the category names supported by the evidence when possible.
"""


FORMAL_CATEGORY_ALIASES = {
    "Race and Ethnicity": ("race", "racial", "ethnicity", "ethnic", "nationality", "immigration"),
    "Gender Expectations": ("gender", "sexism", "sexist", "women", "woman", "men", "man"),
    "Economic Background (Socioeconomic Status)": (
        "economic",
        "socioeconomic",
        "social class",
        "income",
        "wealth",
    ),
    "Political Identity": ("political", "politics", "ideology", "partisan", "party affiliation"),
    "Religion and Belief": ("religion", "religious", "belief", "faith"),
    "Mental Health": ("mental health", "psychiatric", "psychological"),
    "Disability and Access": ("disability", "disabled", "accessibility", "access"),
    "Sexual Orientation": ("sexual orientation", "sexuality", "gay", "lesbian", "homosexual"),
    "Science, Technology, and Medicine": (
        "science",
        "technology",
        "medicine",
        "medical",
        "health care",
        "healthcare",
    ),
}


def canonical_category(category: str | None) -> str | None:
    normalized = (category or "").strip().lower()
    if not normalized:
        return None
    for formal, aliases in FORMAL_CATEGORY_ALIASES.items():
        if normalized == formal.lower() or any(alias in normalized for alias in aliases):
            return formal
    return None


def _document_survey(document: dict) -> str | None:
    survey = str(document.get("source_survey") or "").strip().upper()
    if survey in {"GSS", "ISSP"}:
        return survey
    record_id = str(document.get("id") or "")
    if record_id.startswith("ISSP_"):
        return "ISSP"
    if record_id:
        return "GSS"
    return None


def select_evidence_documents(
    documents: List[dict], category: str | None, per_survey_limit: int = 2
) -> List[dict]:
    """Select category-aligned evidence with equal GSS and ISSP quotas.

    Input order is retrieval rank. The selector preserves rank within each
    survey and interleaves the selected GSS and ISSP records so one source
    cannot crowd the other out. Missing aligned evidence stays missing rather
    than being replaced with a tangential question.
    """

    if per_survey_limit <= 0:
        return []
    target = canonical_category(category)
    if target is None:
        return []

    matches: dict[str, list[dict]] = {"GSS": [], "ISSP": []}
    for document in documents:
        document_categories = {
            canonical_category(value) or value
            for value in (document.get("categories") or [])
        }
        survey = _document_survey(document)
        if (
            target in document_categories
            and survey in matches
            and len(matches[survey]) < per_survey_limit
        ):
            matches[survey].append(document)

    balanced = []
    for rank in range(per_survey_limit):
        for survey in ("GSS", "ISSP"):
            if rank < len(matches[survey]):
                balanced.append(matches[survey][rank])
    return balanced


def build_retrieval_prompt(user_text: str, retrieved_docs: List[dict]) -> str:
    context_blocks = []
    for doc in retrieved_docs:
        categories = ", ".join(doc.get("categories", []))
        source_survey = doc.get("source_survey") or "Unknown survey"
        question = doc.get("question_text") or doc.get("content") or ""
        waves = doc.get("available_waves") or []
        responses = _parse_responses_by_year(doc.get("responses_by_year"))
        response_note = (
            "Observed response distributions are present for the listed years."
            if responses
            else "Response percentages are unavailable; wave coverage describes research scope."
        )
        context_blocks.append(
            f"Evidence ID: {doc.get('id')}\n"
            f"Survey: {source_survey}\n"
            f"Question: {question}\n"
            f"Categories: {categories}\n"
            f"Module: {doc.get('module_name') or 'Not specified'}\n"
            f"Available waves: {', '.join(str(wave) for wave in waves) or 'Not specified'}\n"
            f"Country coverage count: {doc.get('country_count') or 'Not specified'}\n"
            f"Source dataset: {doc.get('source_dataset') or 'Not specified'}\n"
            f"Response scale: {', '.join(doc.get('response_options', []))}\n"
            f"Annotation status: {doc.get('annotation_status') or 'Not specified'}\n"
            f"Evidence boundary: {response_note}\n"
        )

    context = "\n\n---\n\n".join(context_blocks)
    return (
        f"{SYSTEM_BIAS_PROMPT}\n\n"
        f"Bias category guidance:\n{BIAS_CATEGORY_SUMMARY}\n\n"
        f"Relevant survey-question evidence from the GSS + ISSP knowledge base:\n\n"
        f"{context}\n\n"
        f"User statement:\n{user_text}"
    )


def retrieve_top_documents(query_embedding: list[float], query_text: str | None = None, top_k: int = 5):
    from src.storage.azure_vector_store import query_vectors

    return query_vectors(query_embedding=query_embedding, query_text=query_text, top_k=top_k)


def interleave_survey_documents(
    gss_documents: list[dict],
    issp_documents: list[dict],
) -> list[dict]:
    """Merge independently ranked survey results without changing either rank."""

    merged: list[dict] = []
    for rank in range(max(len(gss_documents), len(issp_documents))):
        if rank < len(gss_documents):
            merged.append(gss_documents[rank])
        if rank < len(issp_documents):
            merged.append(issp_documents[rank])
    return merged


def retrieve_balanced_documents(
    query_embedding: list[float],
    query_text: str | None = None,
    per_survey_k: int = 5,
) -> list[dict]:
    """Retrieve GSS and ISSP candidates independently, then merge by rank."""

    from src.storage.azure_vector_store import query_vectors

    gss_documents = query_vectors(
        query_embedding=query_embedding,
        query_text=query_text,
        top_k=per_survey_k,
        source_survey="GSS",
    )
    issp_documents = query_vectors(
        query_embedding=query_embedding,
        query_text=query_text,
        top_k=per_survey_k,
        source_survey="ISSP",
    )
    return interleave_survey_documents(gss_documents, issp_documents)
