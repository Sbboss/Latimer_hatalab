"""Evaluate ISSP retrieval with Recall@k, MRR, and nDCG@k."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Callable

from src.data.ingest import build_document_text


DEFAULT_GOLD_PATH = Path("data/evaluation/issp_retrieval_gold.json")
DEFAULT_CORPUS_PATH = Path("data/issp/issp_questions_tagged.json")
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def build_bm25_search(
    documents: list[dict],
) -> Callable[[str, int], list[dict]]:
    """Build a dependency-free lexical baseline over the canonical corpus."""

    tokenized = [_tokens(build_document_text(document)) for document in documents]
    frequencies = [Counter(tokens) for tokens in tokenized]
    lengths = [len(tokens) for tokens in tokenized]
    average_length = sum(lengths) / max(1, len(lengths))
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))

    total = len(documents)
    k1 = 1.5
    b = 0.75

    def search(query: str, top_k: int) -> list[dict]:
        query_terms = _tokens(query)
        ranked: list[tuple[float, str, dict]] = []
        for document, counts, length in zip(
            documents, frequencies, lengths, strict=True
        ):
            score = 0.0
            for term in query_terms:
                frequency = counts.get(term, 0)
                if not frequency:
                    continue
                df = document_frequency[term]
                inverse_document_frequency = math.log(
                    1 + (total - df + 0.5) / (df + 0.5)
                )
                denominator = frequency + k1 * (
                    1 - b + b * length / max(1.0, average_length)
                )
                score += inverse_document_frequency * (
                    frequency * (k1 + 1) / denominator
                )
            ranked.append((score, str(document["id"]), document))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [document for score, _, document in ranked[:top_k] if score > 0]

    return search


def _metrics(retrieved_ids: list[str], relevant_ids: set[str], top_k: int) -> dict:
    ranked = retrieved_ids[:top_k]
    hits = [record_id for record_id in ranked if record_id in relevant_ids]
    recall = len(set(hits)) / len(relevant_ids) if relevant_ids else 0.0
    reciprocal_rank = 0.0
    for rank, record_id in enumerate(ranked, start=1):
        if record_id in relevant_ids:
            reciprocal_rank = 1.0 / rank
            break

    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, record_id in enumerate(ranked, start=1)
        if record_id in relevant_ids
    )
    ideal_hits = min(len(relevant_ids), top_k)
    ideal_dcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    ndcg = dcg / ideal_dcg if ideal_dcg else 0.0
    return {
        "recall_at_k": recall,
        "reciprocal_rank": reciprocal_rank,
        "ndcg_at_k": ndcg,
        "hits": hits,
    }


def evaluate_cases(
    cases: list[dict],
    search: Callable[[str, int], list[dict]],
    top_k: int,
) -> dict:
    case_results = []
    for case in cases:
        retrieved = search(case["query"], top_k)
        retrieved_ids = [str(document.get("id")) for document in retrieved]
        relevant_ids = set(case["relevant_ids"])
        metrics = _metrics(retrieved_ids, relevant_ids, top_k)
        case_results.append(
            {
                "query": case["query"],
                "relevant_ids": sorted(relevant_ids),
                "retrieved_ids": retrieved_ids,
                **metrics,
            }
        )

    count = max(1, len(case_results))
    aggregate = {
        "case_count": len(case_results),
        "top_k": top_k,
        "mean_recall_at_k": sum(
            result["recall_at_k"] for result in case_results
        )
        / count,
        "mrr": sum(result["reciprocal_rank"] for result in case_results) / count,
        "mean_ndcg_at_k": sum(result["ndcg_at_k"] for result in case_results)
        / count,
    }
    return {"aggregate": aggregate, "cases": case_results}


def _live_search() -> Callable[[str, int], list[dict]]:
    from src.llm.azure_openai_client import create_embedding, openai_client
    from src.storage.azure_vector_store import query_vectors

    client = openai_client()

    def search(query: str, top_k: int) -> list[dict]:
        embedding = create_embedding(client, query)
        return query_vectors(embedding, query_text=query, top_k=top_k)

    return search


def _load_json_array(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"Expected a JSON array in {path}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("lexical", "live"), default="lexical")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD_PATH)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--minimum-recall", type=float, default=0.0)
    args = parser.parse_args()
    if args.top_k <= 0:
        raise ValueError("--top-k must be positive")

    cases = _load_json_array(args.gold)
    if args.mode == "live":
        search = _live_search()
    else:
        search = build_bm25_search(_load_json_array(args.corpus))

    report = {"mode": args.mode, **evaluate_cases(cases, search, args.top_k)}
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")

    if report["aggregate"]["mean_recall_at_k"] < args.minimum_recall:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
