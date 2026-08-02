import json
from pathlib import Path
from typing import List

from src.config import GSS_PROCESSED_PATH, GSS_RAW_PATH
from src.data.ingest import normalize_question, save_processed_questions, load_raw_questions
from src.llm.azure_openai_client import create_embedding, openai_client
from src.storage.azure_vector_store import create_or_update_index, upload_documents


def load_processed_documents(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_processed_documents() -> List[dict]:
    raw_questions = load_raw_questions(GSS_RAW_PATH)
    processed = [normalize_question(q) for q in raw_questions if q.get("categories")]
    save_processed_questions(processed, GSS_PROCESSED_PATH)
    return processed


def build_search_document(question: dict, embedding: list[float]) -> dict:
    return {
        "id": question["id"],
        "content": (
            f"Question: {question['question']}\n"
            f"Categories: {', '.join(question['categories'])}\n"
            f"Years: {question['year_start']}–{question['year_end']}\n"
            f"Options: {', '.join(question['response_options'])}"
        ),
        "content_vector": embedding,
        "var": question.get("var"),
        "categories": question.get("categories", []),
        "year_start": question.get("year_start"),
        "year_end": question.get("year_end"),
        "response_options": question.get("response_options", []),
        "responses_by_year": json.dumps(question.get("responses_by_year", {})),
    }


def main() -> None:
    processed_path = Path(GSS_PROCESSED_PATH)
    if not processed_path.exists():
        print(f"Processed questions not found at {GSS_PROCESSED_PATH}. Generating from raw data.")
        processed = build_processed_documents()
    else:
        processed = load_processed_documents(GSS_PROCESSED_PATH)

    client = openai_client()

    print(f"Loaded {len(processed)} processed questions from {GSS_PROCESSED_PATH}")

    create_or_update_index()

    documents = []
    for question in processed:
        text = (
            f"Question: {question['question']}\n"
            f"Categories: {', '.join(question['categories'])}\n"
            f"Years: {question['year_start']}–{question['year_end']}\n"
            f"Options: {', '.join(question['response_options'])}"
        )
        embedding = create_embedding(client, text)
        documents.append(build_search_document(question, embedding))

    upload_documents(documents)
    print(f"Ingested {len(documents)} documents into Azure Cognitive Search")


if __name__ == "__main__":
    main()
