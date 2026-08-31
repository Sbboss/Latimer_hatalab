import unittest

from fastapi.testclient import TestClient

from src.api.fastapi_app import ANALYSIS_OUTPUT_SCHEMA, _document_to_evidence, app
from src.config import ordered_model_names


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

    def test_technical_issp_question_has_plain_language_and_original(self):
        original = "Father's occupation when R was (14-15-16): ILO, ISCO 1988 4-digit"
        evidence = _document_to_evidence(
            {
                "id": "ISSP_SOINQ_V64",
                "question_text": original,
                "categories": ["Economic Background (Socioeconomic Status)"],
                "source_survey": "ISSP",
                "available_waves": ["1987", "1992", "1999", "2009", "2019"],
                "country_count": 34,
                "responses_by_year": "{}",
            }
        )

        self.assertEqual(
            evidence["question"],
            "What occupation did the respondent's father have when the respondent was about 15 years old?",
        )
        self.assertEqual(evidence["originalQuestion"], original)

    def test_model_names_use_product_display_order(self):
        self.assertEqual(
            ordered_model_names(
                [
                    "DeepSeek-V4-Pro",
                    "GPT-5.5",
                    "Claude-Opus-4.8",
                    "Llama-3.3-70B-Instruct",
                ]
            ),
            [
                "GPT-5.5",
                "Claude-Opus-4.8",
                "DeepSeek-V4-Pro",
                "Llama-3.3-70B-Instruct",
            ],
        )

    def test_issp_statement_is_presented_as_an_agreement_question(self):
        evidence = _document_to_evidence(
            {
                "id": "ISSP_NATID_V45",
                "question_text": "Immigrants bring new ideas and cultures",
                "categories": ["Race and Ethnicity"],
                "source_survey": "ISSP",
                "responses_by_year": "{}",
            }
        )

        self.assertEqual(
            evidence["question"],
            "How strongly does the respondent agree or disagree with this statement: Immigrants bring new ideas and cultures?",
        )

    def test_analysis_schema_requires_reflection_question(self):
        category_schema = ANALYSIS_OUTPUT_SCHEMA["properties"]["categories"]["items"]

        self.assertIn("reflection_question", category_schema["required"])
        self.assertTrue(ANALYSIS_OUTPUT_SCHEMA["additionalProperties"] is False)


if __name__ == "__main__":
    unittest.main()
