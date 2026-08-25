import json
from pathlib import Path

from src.config import GSS_RAW_PATH, GSS_PROCESSED_PATH

CATEGORY_LABEL_MAP = {
    "race": "Race",
    "sexuality": "Sexuality",
    "gender": "Gender",
    "disability": "Disability",
    "ses": "Socioeconomic Status",
    "political": "Political Identification",
    "mental_health": "Mental Health",
}


def normalize_question(question: dict) -> dict:
    year_keys = [int(y) for y in question.get("responses_by_year", {}).keys() if str(y).isdigit()]
    year_start = min(year_keys) if year_keys else None
    year_end = max(year_keys) if year_keys else None

    response_options = set()
    for year_data in question.get("responses_by_year", {}).values():
        response_options.update(year_data.keys())

    response_options = sorted(response_options)

    normalized_categories = [CATEGORY_LABEL_MAP.get(cat, cat) for cat in question.get("categories", [])]

    return {
        "id": question.get("var") or f"doc_{hash(question.get('question', '')) % (10**12)}",
        "var": question.get("var"),
        "question": question.get("question"),
        "categories": normalized_categories,
        "year_start": year_start,
        "year_end": year_end,
        "response_options": response_options,
        "responses_by_year": question.get("responses_by_year", {}),
        "source": "GSS",
        "source_survey": "GSS",
        "module_name": "",
        "source_question": question.get("var"),
        "source_dataset": "General Social Survey",
        "available_waves": [str(year) for year in sorted(year_keys)],
        "countries": ["US-United States"],
        "country_count": 1,
        "wave_count": len(year_keys),
        "cross_wave_question_available": len(year_keys) > 1,
        "limitations": "GSS response distributions are United States public-opinion data.",
        "annotation_status": "not_applicable",
        "annotation_uncertain": False,
        "annotation_notes": "",
    }



def _summarize_options(options: list[str], max_items: int = 20, max_chars: int = 1500) -> str:
    """Cap huge coded-response lists (e.g. 4-digit occupation codes) so embedding text stays under model token limits."""
    if not options:
        return "None"
    truncated = options[:max_items]
    text = ", ".join(truncated)
    if len(options) > max_items or len(text) > max_chars:
        text = text[:max_chars]
        text += f" ... ({len(options)} total response options, truncated for embedding)"
    return text


def build_document_text(question: dict) -> str:
    options = question["response_options"]
    waves = question.get("available_waves") or []
    year_text = (
        f"Available waves: {', '.join(str(wave) for wave in waves)}"
        if waves
        else (
            f"Years: {question['year_start']}-{question['year_end']}"
            if question["year_start"]
            else "Years: unknown"
        )
    )
    categories = ", ".join(question["categories"]) or "Uncategorized"
    source_survey = question.get("source_survey") or question.get("source") or "Unknown"
    module = question.get("module_name") or "Not specified"
    source_dataset = question.get("source_dataset") or "Not specified"
    country_count = question.get("country_count")
    coverage = f"Country coverage: {country_count}" if country_count is not None else "Country coverage: unknown"
    quality = question.get("annotation_status") or "unknown"

    return (
        f"Survey: {source_survey}\n"
        f"Question: {question['question']}\n"
        f"Categories: {categories}\n"
        f"Module: {module}\n"
        f"{year_text}\n"
        f"Response scale: {_summarize_options(options)}\n"
        f"Source dataset: {source_dataset}\n"
        f"{coverage}\n"
        f"Annotation status: {quality}"
    )


def load_raw_questions(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_processed_questions(questions: list[dict], path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2)


def main() -> None:
    raw_questions = load_raw_questions(GSS_RAW_PATH)
    processed = [normalize_question(q) for q in raw_questions if q.get("categories")]
    save_processed_questions(processed, GSS_PROCESSED_PATH)
    print(f"Saved {len(processed)} normalized documents to {GSS_PROCESSED_PATH}")


if __name__ == "__main__":
    main()
