"""Build verified ISSP response distributions from official GESIS files.

The tagged corpus identifies the GESIS dataset and source variable for every
question. This script joins those records to the official respondent-level
Stata files, applies the supplied WEIGHT variable, excludes non-substantive
codes, and writes weighted valid-response percentages for each survey year.

Raw GESIS files remain outside the repository. Pass a directory containing
the official ``*.dta.zip`` downloads or extracted ``*.dta`` files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyreadstat


DEFAULT_CORPUS = Path("data/issp/issp_questions_tagged.json")
DEFAULT_REPORT = Path("data/issp/response_distribution_report.json")

DATASETS = {
    "ZA4747": {
        "archive": "ZA4747_v2-1-0.dta.zip",
        "dta": "ZA4747_v2-1-0.dta",
        "year": "year_sdno",
        "doi": "https://doi.org/10.4232/1.14113",
        "version": "2.1.0 (2023-06-30)",
    },
    "ZA5960": {
        "archive": "ZA5960_v1-0-0.dta.zip",
        "dta": "ZA5960_v1-0-0.dta",
        "year": "YEAR_SDNO",
        "doi": "https://doi.org/10.4232/1.13471",
        "version": "1.0.0 (2020-06-29)",
    },
    "ZA8790": {
        "archive": "ZA8790_v1-0-0.dta.zip",
        "dta": "ZA8790_v1-0-0b.dta",
        "year": "year",
        "doi": "https://doi.org/10.4232/1.14226",
        "version": "1.0.0 (2024-01-18)",
    },
    "ZA8792": {
        "archive": "ZA8792_v2-0-0.dta.zip",
        "dta": "ZA8792_v2-0-0.dta",
        "year": "year",
        "doi": "https://doi.org/10.4232/1.14482",
        "version": "2.0.0 (2025-02-10)",
    },
    "ZA8793": {
        "archive": "ZA8793_v1-1-0.dta.zip",
        "dta": "ZA8793_v1-1-0.dta",
        "year": "year",
        "doi": "https://doi.org/10.4232/1.14767",
        "version": "1.1.0 (2026-05-21)",
    },
    "ZA8794": {
        "archive": "ZA8794_v1-0-0.dta.zip",
        "dta": "ZA8794_v1-0-0.dta",
        "year": "year",
        "doi": "https://doi.org/10.4232/1.14438",
        "version": "1.0.0 (2024-12-16)",
    },
    "ZA8795": {
        "archive": "ZA8795_v1-0-0.dta.zip",
        "dta": "ZA8795_v1-0-0.dta",
        "year": "year",
        "doi": "https://doi.org/10.4232/1.14750",
        "version": "1.0.0 (2025-04-15)",
    },
    "ZA8797": {
        "archive": "ZA8797_v1-0-0.dta.zip",
        "dta": "ZA8797_v1-0-0.dta",
        "year": "year",
        "doi": "https://doi.org/10.4232/1.14391",
        "version": "1.0.0 (2024-10-07)",
    },
}

METHOD = (
    "Equal-country mean of valid-response percentages for each year, with the "
    "official GESIS WEIGHT variable applied within each country sample."
)


class DistributionBuildError(ValueError):
    """Raised when source data cannot be matched without guessing."""


def _dataset_code(record: dict[str, Any]) -> str:
    return str(record.get("source_dataset", "")).split(maxsplit=1)[0]


def _option_codes(options: list[str]) -> list[tuple[float, str]]:
    parsed: list[tuple[float, str]] = []
    for option in options:
        try:
            raw_code, _label = option.split("=", 1)
            parsed.append((float(raw_code.strip()), option))
        except (ValueError, AttributeError) as exc:
            raise DistributionBuildError(f"Invalid coded response option: {option!r}") from exc
    return parsed


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _find_source(data_dir: Path, dataset: str, temp_dir: Path) -> tuple[Path, Path]:
    info = DATASETS[dataset]
    direct = data_dir / str(info["dta"])
    if direct.is_file():
        return direct, direct

    archive = data_dir / str(info["archive"])
    if not archive.is_file():
        raise DistributionBuildError(
            f"Missing official source for {dataset}: expected {direct.name} or {archive.name}"
        )

    with zipfile.ZipFile(archive) as bundle:
        matches = [name for name in bundle.namelist() if Path(name).name == info["dta"]]
        if len(matches) != 1:
            raise DistributionBuildError(
                f"Expected one {info['dta']} member in {archive.name}; found {matches}"
            )

        target = temp_dir / str(info["dta"])
        with bundle.open(matches[0]) as source, target.open("wb") as output:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                output.write(block)
    return target, archive


def _rounded_shares(weighted_counts: list[float]) -> list[float]:
    total = sum(weighted_counts)
    if total <= 0:
        return []
    shares = [round(value * 100 / total, 4) for value in weighted_counts]
    residual = round(100.0 - sum(shares), 4)
    if residual:
        largest = max(range(len(shares)), key=shares.__getitem__)
        shares[largest] = round(shares[largest] + residual, 4)
    return shares


def _write_json(value: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def enrich_corpus(
    records: list[dict[str, Any]], data_dir: Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_dataset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        dataset = _dataset_code(record)
        if dataset not in DATASETS:
            raise DistributionBuildError(
                f"Unsupported source dataset for {record.get('id')}: {dataset}"
            )
        by_dataset[dataset].append(record)

    source_report: dict[str, Any] = {}
    missing_records: list[str] = []
    partial_records: list[str] = []

    with tempfile.TemporaryDirectory(prefix="issp-distributions-") as temp_name:
        temp_dir = Path(temp_name)
        for dataset, dataset_records in sorted(by_dataset.items()):
            dta_path, checksum_path = _find_source(data_dir, dataset, temp_dir)
            _empty, metadata = pyreadstat.read_dta(str(dta_path), metadataonly=True)
            names = {name.lower(): name for name in metadata.column_names}
            year_column = names.get(str(DATASETS[dataset]["year"]).lower())
            weight_column = names.get("weight")
            country_column = names.get("country")
            if not all((year_column, weight_column, country_column)):
                raise DistributionBuildError(
                    f"{dataset} lacks a required year, country, or WEIGHT variable"
                )

            variable_by_id: dict[str, str] = {}
            for record in dataset_records:
                requested = str(record.get("source_question", ""))
                actual = names.get(requested.lower())
                if not actual:
                    raise DistributionBuildError(
                        f"{record.get('id')} cannot be matched to {dataset} variable {requested}"
                    )
                variable_by_id[str(record["id"])] = actual

            usecols = sorted(
                set(variable_by_id.values())
                | {str(year_column), str(weight_column), str(country_column)}
            )
            frame, _metadata = pyreadstat.read_dta(str(dta_path), usecols=usecols)
            source_report[dataset] = {
                "archive_or_file": checksum_path.name,
                "doi": DATASETS[dataset]["doi"],
                "question_count": len(dataset_records),
                "sha256": _sha256(checksum_path),
                "version": DATASETS[dataset]["version"],
            }

            for record in dataset_records:
                variable = variable_by_id[str(record["id"])]
                coded_options = _option_codes(record.get("response_options", []))
                valid_codes = [code for code, _label in coded_options]
                distributions: dict[str, dict[str, float]] = {}
                bases: dict[str, dict[str, float | int]] = {}
                missing_waves: list[str] = []

                for wave in record.get("available_waves", []):
                    year = int(wave)
                    year_rows = frame[frame[str(year_column)] == year]
                    valid = year_rows[variable].isin(valid_codes)
                    valid &= year_rows[str(weight_column)].map(
                        lambda value: bool(
                            isinstance(value, (int, float))
                            and math.isfinite(value)
                            and value > 0
                        )
                    )
                    sample = year_rows.loc[
                        valid, [variable, str(weight_column), str(country_column)]
                    ]
                    if sample.empty:
                        missing_waves.append(str(wave))
                        continue

                    country_shares: list[list[float]] = []
                    for _country, country_sample in sample.groupby(str(country_column)):
                        weighted_by_code = country_sample.groupby(variable)[
                            str(weight_column)
                        ].sum()
                        country_shares.append(
                            _rounded_shares(
                                [
                                    float(weighted_by_code.get(code, 0.0))
                                    for code in valid_codes
                                ]
                            )
                        )
                    shares = _rounded_shares(
                        [
                            sum(country[index] for country in country_shares)
                            / len(country_shares)
                            for index in range(len(valid_codes))
                        ]
                    )
                    if not shares:
                        missing_waves.append(str(wave))
                        continue

                    distributions[str(wave)] = {
                        label: share
                        for (_code, label), share in zip(coded_options, shares, strict=True)
                    }
                    bases[str(wave)] = {
                        "country_samples": int(sample[str(country_column)].nunique()),
                        "unweighted_valid_responses": int(len(sample)),
                        "weighted_valid_responses": round(
                            float(sample[str(weight_column)].sum()), 3
                        ),
                    }

                record["responses_by_year"] = distributions
                record["response_base_by_year"] = bases
                record["response_data_doi"] = DATASETS[dataset]["doi"]
                record["response_data_source"] = (
                    f"GESIS {dataset} respondent-level cumulation file"
                )
                record["response_distribution_method"] = METHOD
                record["response_data_missing_waves"] = missing_waves
                if not distributions:
                    record["response_data_status"] = "source_missing"
                    missing_records.append(str(record["id"]))
                elif missing_waves:
                    record["response_data_status"] = "partial"
                    partial_records.append(str(record["id"]))
                else:
                    record["response_data_status"] = "available"

    report = {
        "available_record_count": sum(
            record["response_data_status"] == "available" for record in records
        ),
        "distribution_method": METHOD,
        "missing_record_count": len(missing_records),
        "missing_record_ids": sorted(missing_records),
        "partial_record_count": len(partial_records),
        "partial_record_ids": sorted(partial_records),
        "record_count": len(records),
        "sources": source_report,
    }
    return records, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        required=True,
        help="Directory containing official GESIS .dta.zip or extracted .dta files.",
    )
    parser.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    records = json.loads(corpus_path.read_text(encoding="utf-8"))
    enriched, report = enrich_corpus(records, Path(args.data_dir))
    _write_json(enriched, corpus_path)
    _write_json(report, Path(args.report))
    print(
        f"Built distributions for {report['available_record_count']} of "
        f"{report['record_count']} ISSP questions; "
        f"{report['partial_record_count']} partial and "
        f"{report['missing_record_count']} source-missing records."
    )


if __name__ == "__main__":
    main()
