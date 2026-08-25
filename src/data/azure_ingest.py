"""Idempotently upload normalized GSS and/or ISSP questions to Azure AI Search."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from src.config import (
    AZURE_OPENAI_EMBEDDING_BATCH_SIZE,
    GSS_PROCESSED_PATH,
    GSS_RAW_PATH,
    ISSP_PROCESSED_PATH,
)
from src.data.ingest import (
    build_document_text,
    load_raw_questions,
    normalize_question,
    save_processed_questions,
)
def load_processed_documents(path: str | Path) -> list[dict]:
    with Path(path).open("r", encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, list):
        raise ValueError(f"Expected a JSON array in {path}")
    return value


def build_processed_gss_documents() -> list[dict]:
    raw_questions = load_raw_questions(GSS_RAW_PATH)
    processed = [normalize_question(question) for question in raw_questions if question.get("categories")]
    save_processed_questions(processed, GSS_PROCESSED_PATH)
    return processed


def load_source_documents(source: str) -> list[dict]:
    documents: list[dict] = []
    if source in {"gss", "all"}:
        processed_path = Path(GSS_PROCESSED_PATH)
        if processed_path.exists():
            documents.extend(load_processed_documents(processed_path))
        elif Path(GSS_RAW_PATH).exists():
            documents.extend(build_processed_gss_documents())
        elif source == "gss":
            raise FileNotFoundError(
                f"Neither {GSS_PROCESSED_PATH} nor {GSS_RAW_PATH} exists"
            )
        else:
            print("GSS source files are absent; preserving existing GSS index documents.")

    if source in {"issp", "all"}:
        documents.extend(load_processed_documents(ISSP_PROCESSED_PATH))

    ids = [document.get("id") for document in documents]
    if any(not record_id for record_id in ids):
        raise ValueError("Every normalized search document must have an id")
    if len(ids) != len(set(ids)):
        raise ValueError("Normalized search document IDs must be unique")
    return documents


def build_search_document(question: dict, embedding: list[float]) -> dict:
    """Map either survey's canonical model into the shared index schema."""

    return {
        "id": question["id"],
        "content": build_document_text(question),
        "content_vector": embedding,
        "var": question.get("var"),
        "question_text": question.get("question"),
        "categories": question.get("categories", []),
        "year_start": question.get("year_start"),
        "year_end": question.get("year_end"),
        "response_options": question.get("response_options", []),
        "responses_by_year": json.dumps(question.get("responses_by_year", {})),
        "source_survey": question.get("source_survey") or question.get("source"),
        "module_name": question.get("module_name"),
        "source_dataset": question.get("source_dataset"),
        "available_waves": [str(value) for value in question.get("available_waves", [])],
        "countries": question.get("countries", []),
        "country_count": question.get("country_count"),
        "wave_count": question.get("wave_count"),
        "cross_wave_question_available": question.get(
            "cross_wave_question_available", False
        ),
        "limitations": question.get("limitations"),
        "annotation_status": question.get("annotation_status"),
        "annotation_uncertain": question.get("annotation_uncertain", False),
        "annotation_notes": question.get("annotation_notes"),
    }


def _batches(items: list[dict], batch_size: int) -> Iterable[list[dict]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def ingest_documents(documents: list[dict], embedding_batch_size: int) -> int:
    # Keep validation and --dry-run usable without cloud SDK dependencies.
    from src.llm.azure_openai_client import create_embeddings, openai_client
    from src.storage.azure_vector_store import create_or_update_index, upload_documents

    client = openai_client()
    create_or_update_index()

    uploaded = 0
    for batch in _batches(documents, embedding_batch_size):
        texts = [build_document_text(document) for document in batch]
        vectors = create_embeddings(client, texts)
        payloads = [
            build_search_document(document, vector)
            for document, vector in zip(batch, vectors, strict=True)
        ]
        upload_documents(payloads)
        uploaded += len(payloads)
        print(f"Uploaded {uploaded}/{len(documents)} documents")
    return uploaded


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        choices=("issp", "gss", "all"),
        default="issp",
        help="Default appends ISSP without replacing or deleting existing GSS documents.",
    )
    parser.add_argument(
        "--embedding-batch-size",
        type=int,
        default=AZURE_OPENAI_EMBEDDING_BATCH_SIZE,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate canonical input and index payloads without network calls.",
    )
    args = parser.parse_args()

    documents = load_source_documents(args.source)
    surveys: dict[str, int] = {}
    for document in documents:
        survey = document.get("source_survey") or document.get("source") or "Unknown"
        surveys[survey] = surveys.get(survey, 0) + 1

    if args.dry_run:
        payloads = [build_search_document(document, []) for document in documents]
        print(
            f"Dry run validated {len(payloads)} idempotent documents; "
            f"survey counts: {surveys}"
        )
        return

    uploaded = ingest_documents(documents, args.embedding_batch_size)
    print(f"Ingested {uploaded} documents into Azure AI Search; survey counts: {surveys}")


if __name__ == "__main__":
    main()
