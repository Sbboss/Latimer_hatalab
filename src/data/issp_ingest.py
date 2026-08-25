"""Validate and normalize the tagged ISSP export.

The source ZIP stays outside the repository. This module creates a public,
deployment-ready canonical file containing survey-question metadata and
annotation quality flags, but no annotator identities or timestamps.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


QUESTIONS_SUFFIX = "ISSP Tagging System - Questions.csv"
ANNOTATIONS_SUFFIX = "ISSP Tagging System - Annotations.csv"
DEFAULT_OUTPUT_PATH = Path("data/issp/issp_questions_tagged.json")
DEFAULT_REPORT_PATH = Path("data/issp/validation_report.json")


class ISSPDataError(ValueError):
    """Raised when the tagged ISSP export violates a required invariant."""


def _read_csv_member(archive: zipfile.ZipFile, suffix: str) -> list[dict[str, str]]:
    matches = [
        name
        for name in archive.namelist()
        if name.endswith(suffix) and not name.startswith("__MACOSX/")
    ]
    if len(matches) != 1:
        raise ISSPDataError(
            f"Expected exactly one ZIP member ending in {suffix!r}; found {matches}"
        )

    raw = archive.read(matches[0]).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(raw)))


def _split_pipe(value: str | None) -> list[str]:
    return [part.strip() for part in (value or "").split("|") if part.strip()]


def _unique_rows(rows: list[dict[str, str]], kind: str) -> dict[str, dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    duplicates: list[str] = []
    for row in rows:
        record_id = (row.get("record_id") or "").strip()
        if not record_id:
            raise ISSPDataError(f"{kind} contains a row without record_id")
        if record_id in by_id:
            duplicates.append(record_id)
        by_id[record_id] = row
    if duplicates:
        raise ISSPDataError(f"{kind} contains duplicate record_id values: {duplicates}")
    return by_id


def _required_int(row: dict[str, str], field: str) -> int:
    try:
        return int((row.get(field) or "").strip())
    except ValueError as exc:
        raise ISSPDataError(
            f"{row.get('record_id', '<unknown>')} has invalid integer {field!r}"
        ) from exc


def _annotation_status(annotation: dict[str, str] | None) -> str:
    if annotation is None:
        return "not_annotated"
    labels = _split_pipe(annotation.get("labels"))
    if not labels:
        return "no_labels"
    if (annotation.get("uncertain") or "").strip().upper() == "TRUE":
        return "labeled_uncertain"
    return "labeled"


def _validate_question(row: dict[str, str]) -> tuple[list[str], list[str]]:
    record_id = row["record_id"].strip()
    question_text = (row.get("question_text") or "").strip()
    if not question_text:
        raise ISSPDataError(f"{record_id} has empty question_text")

    waves = _split_pipe(row.get("available_waves"))
    countries = _split_pipe(row.get("countries"))
    if not waves or any(not wave.isdigit() for wave in waves):
        raise ISSPDataError(f"{record_id} has invalid available_waves: {waves}")
    if _required_int(row, "wave_count") != len(waves):
        raise ISSPDataError(f"{record_id} wave_count does not match available_waves")
    if _required_int(row, "country_count") != len(countries):
        raise ISSPDataError(f"{record_id} country_count does not match countries")
    if _split_pipe(row.get("module_year")) != waves:
        raise ISSPDataError(f"{record_id} module_year does not match available_waves")
    return waves, countries


def normalize_issp_zip(zip_path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return all normalized ISSP questions and a deterministic quality report."""

    source_path = Path(zip_path)
    if not source_path.is_file():
        raise ISSPDataError(f"ISSP ZIP does not exist: {source_path}")

    with zipfile.ZipFile(source_path) as archive:
        question_rows = _read_csv_member(archive, QUESTIONS_SUFFIX)
        annotation_rows = _read_csv_member(archive, ANNOTATIONS_SUFFIX)

    questions_by_id = _unique_rows(question_rows, "Questions")
    annotations_by_id = _unique_rows(annotation_rows, "Annotations")
    unknown_annotation_ids = sorted(set(annotations_by_id) - set(questions_by_id))
    if unknown_annotation_ids:
        raise ISSPDataError(
            f"Annotations reference unknown question IDs: {unknown_annotation_ids}"
        )

    documents: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    module_counts: Counter[str] = Counter()

    for row in question_rows:
        record_id = row["record_id"].strip()
        waves, countries = _validate_question(row)
        annotation = annotations_by_id.get(record_id)
        categories = _split_pipe(annotation.get("labels")) if annotation else []
        status = _annotation_status(annotation)
        uncertain = bool(
            annotation
            and (annotation.get("uncertain") or "").strip().upper() == "TRUE"
        )
        years = [int(wave) for wave in waves]

        category_counts.update(categories)
        status_counts.update([status])
        module_counts.update([(row.get("module_name") or "").strip()])

        documents.append(
            {
                "id": record_id,
                "var": record_id,
                "question": (row.get("question_text") or "").strip(),
                "categories": categories,
                "year_start": min(years),
                "year_end": max(years),
                "response_options": _split_pipe(row.get("response_scale")),
                "responses_by_year": {},
                "source": "ISSP",
                "source_survey": "ISSP",
                "module_name": (row.get("module_name") or "").strip(),
                "source_question": (row.get("source_question") or "").strip(),
                "source_dataset": (row.get("source_dataset") or "").strip(),
                "available_waves": waves,
                "countries": countries,
                "country_count": len(countries),
                "wave_count": len(waves),
                "cross_wave_question_available": (
                    (row.get("trend_available") or "").strip().upper() == "YES"
                ),
                "limitations": (row.get("limitations") or "").strip(),
                "annotation_status": status,
                "annotation_uncertain": uncertain,
                "annotation_notes": (
                    (annotation.get("notes") or "").strip() if annotation else ""
                ),
            }
        )

    report: dict[str, Any] = {
        "source_archive_name": source_path.name,
        "question_count": len(question_rows),
        "annotation_count": len(annotation_rows),
        "normalized_document_count": len(documents),
        "all_question_ids_unique": len(question_rows) == len(questions_by_id),
        "annotation_status_counts": dict(sorted(status_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "module_counts": dict(sorted(module_counts.items())),
        "unannotated_record_ids": sorted(set(questions_by_id) - set(annotations_by_id)),
        "no_label_record_ids": sorted(
            doc["id"] for doc in documents if doc["annotation_status"] == "no_labels"
        ),
        "uncertain_record_ids": sorted(
            doc["id"]
            for doc in documents
            if doc["annotation_uncertain"]
        ),
    }
    return documents, report


def write_json(value: Any, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", required=True, help="Path to the original tagged ISSP ZIP")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--report", default=str(DEFAULT_REPORT_PATH))
    args = parser.parse_args()

    documents, report = normalize_issp_zip(args.zip)
    write_json(documents, args.output)
    write_json(report, args.report)
    print(
        f"Validated and normalized {len(documents)} ISSP questions; "
        f"wrote {args.output} and {args.report}"
    )


if __name__ == "__main__":
    main()
