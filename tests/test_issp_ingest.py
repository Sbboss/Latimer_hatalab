import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.data.azure_ingest import (
    build_search_document,
    load_source_documents,
    verify_indexed_documents,
)
from src.data.ingest import build_document_text
from src.data.issp_ingest import preserve_response_data


CORPUS_PATH = Path("data/issp/issp_questions_tagged.json")
REPORT_PATH = Path("data/issp/validation_report.json")


class ISSPCanonicalCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    def test_all_questions_are_preserved_with_unique_ids(self):
        ids = [document["id"] for document in self.documents]
        self.assertEqual(532, len(ids))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(532, self.report["normalized_document_count"])

    def test_quality_states_are_explicit(self):
        status_counts = self.report["annotation_status_counts"]
        self.assertEqual(476, status_counts["labeled"])
        self.assertEqual(46, status_counts["labeled_uncertain"])
        self.assertEqual(5, status_counts["no_labels"])
        self.assertEqual(5, status_counts["not_annotated"])
        self.assertEqual(
            51,
            sum(document["annotation_uncertain"] for document in self.documents),
        )

    def test_public_corpus_excludes_annotator_identity(self):
        forbidden = {"annotator", "timestamp", "assigned_at"}
        for document in self.documents:
            self.assertTrue(forbidden.isdisjoint(document))

    def test_multi_label_annotations_are_not_flattened(self):
        document = next(
            item for item in self.documents if item["id"] == "ISSP_NATID_V42"
        )
        self.assertEqual(
            {
                "Race and Ethnicity",
                "Economic Background (Socioeconomic Status)",
                "Political Identity",
            },
            set(document["categories"]),
        )

    def test_shared_search_payload_keeps_provenance(self):
        document = next(
            item for item in self.documents if item["id"] == "ISSP_REL_V6"
        )
        payload = build_search_document(document, [0.1, 0.2])
        self.assertEqual("ISSP", payload["source_survey"])
        self.assertEqual("Religion", payload["module_name"])
        self.assertEqual(document["available_waves"], payload["available_waves"])
        self.assertIn("Survey: ISSP", payload["content"])
        self.assertIn("Source dataset:", payload["content"])

    def test_default_source_load_is_issp_only_and_idempotent(self):
        first = load_source_documents("issp")
        second = load_source_documents("issp")
        self.assertEqual(
            [document["id"] for document in first],
            [document["id"] for document in second],
        )

    def test_document_text_does_not_claim_response_trends(self):
        document = next(
            item for item in self.documents if item["id"] == "ISSP_ENV_V10"
        )
        text = build_document_text(document)
        self.assertIn("Available waves:", text)
        self.assertNotIn("public support", text.lower())

    def test_all_questions_have_verified_response_distributions(self):
        for document in self.documents:
            with self.subTest(record_id=document["id"]):
                self.assertTrue(document["responses_by_year"])
                self.assertIn(document["response_data_status"], {"available", "partial"})
                self.assertTrue(document["response_data_doi"].startswith("https://doi.org/"))
                for year, distribution in document["responses_by_year"].items():
                    self.assertIn(year, document["available_waves"])
                    self.assertAlmostEqual(100.0, sum(distribution.values()), places=3)
                    self.assertTrue(all(0 <= share <= 100 for share in distribution.values()))
                    self.assertGreater(
                        document["response_base_by_year"][year]["unweighted_valid_responses"],
                        0,
                    )

    def test_samples_span_all_official_sources(self):
        by_source = {}
        for document in self.documents:
            by_source.setdefault(document["source_dataset"].split()[0], document)
        self.assertEqual(
            {"ZA4747", "ZA5960", "ZA8790", "ZA8792", "ZA8793", "ZA8794", "ZA8795", "ZA8797"},
            set(by_source),
        )
        self.assertTrue(all(item["responses_by_year"] for item in by_source.values()))

    def test_tag_refresh_preserves_verified_response_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.json"
            path.write_text(
                json.dumps(
                    [{
                        "id": "ISSP_SAMPLE",
                        "source_dataset": "ZA0000 v1.0.0",
                        "source_question": "V1",
                        "response_options": ["1 = Yes"],
                        "responses_by_year": {"2021": {"1 = Yes": 100.0}},
                        "response_data_status": "available",
                    }]
                ),
                encoding="utf-8",
            )
            refreshed = [{
                "id": "ISSP_SAMPLE",
                "source_dataset": "ZA0000 v1.0.0",
                "source_question": "V1",
                "response_options": ["1 = Yes"],
                "responses_by_year": {},
            }]
            preserve_response_data(refreshed, path)
            self.assertEqual({"2021": {"1 = Yes": 100.0}}, refreshed[0]["responses_by_year"])
            self.assertEqual("available", refreshed[0]["response_data_status"])

    @patch("src.storage.azure_vector_store.list_indexed_document_ids")
    def test_live_verification_requires_every_expected_id(self, list_ids):
        sample = self.documents[:3]
        list_ids.return_value = {document["id"] for document in sample}

        self.assertEqual({"ISSP": 3}, verify_indexed_documents(sample))

        list_ids.return_value = {sample[0]["id"]}
        with self.assertRaisesRegex(RuntimeError, "missing 2 ISSP documents"):
            verify_indexed_documents(sample)


if __name__ == "__main__":
    unittest.main()
