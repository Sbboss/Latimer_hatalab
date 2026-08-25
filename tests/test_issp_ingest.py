import json
import unittest
from pathlib import Path

from src.data.azure_ingest import build_search_document, load_source_documents
from src.data.ingest import build_document_text


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


if __name__ == "__main__":
    unittest.main()
