import unittest

from fastapi.testclient import TestClient

from src.api.fastapi_app import ANALYSIS_OUTPUT_SCHEMA, _document_to_evidence, app


class ApiEvidenceTests(unittest.TestCase):
    def test_health_and_models_routes_load_without_cloud_credentials(self):
        client = TestClient(app)

        self.assertEqual(client.get("/health").json(), {"status": "ok"})
        self.assertEqual(client.get("/api/health").json(), {"status": "ok"})
        self.assertIn("models", client.get("/api/models").json())

    def test_issp_evidence_does_not_invent_a_response_trend(self):
        evidence = _document_to_evidence(
            {
                "id": "ISSP_FAM1994_001",
                "question_text": "A working mother can establish a warm relationship.",
                "categories": ["Gender"],
                "source_survey": "ISSP",
                "source_dataset": "ISSP tagged corpus",
                "module_name": "Family and Changing Gender Roles",
                "available_waves": ["1994", "2002", "2012"],
                "country_count": 37,
                "responses_by_year": "{}",
                "annotation_status": "labeled",
                "annotation_uncertain": False,
            }
        )

        self.assertEqual(evidence["survey"], "ISSP")
        self.assertEqual(evidence["timeline"], [])
        self.assertIn("not response percentages", evidence["insight"])
        self.assertEqual(evidence["availableWaves"], ["1994", "2002", "2012"])

    def test_analysis_schema_requires_reflection_question(self):
        category_schema = ANALYSIS_OUTPUT_SCHEMA["properties"]["categories"]["items"]

        self.assertIn("reflection_question", category_schema["required"])
        self.assertTrue(ANALYSIS_OUTPUT_SCHEMA["additionalProperties"] is False)


if __name__ == "__main__":
    unittest.main()
