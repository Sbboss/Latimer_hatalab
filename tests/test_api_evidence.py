import json
import unittest
import time
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.fastapi_app import ANALYSIS_OUTPUT_SCHEMA, _PageTextParser, _document_to_evidence, app
from src.config import default_model_names, ordered_model_names
from src.llm.azure_openai_client import CompletionResult


class ApiEvidenceTests(unittest.TestCase):
    def test_health_and_models_routes_load_without_cloud_credentials(self):
        client = TestClient(app)

        self.assertEqual(client.get("/health").json(), {"status": "ok"})
        self.assertEqual(client.get("/api/health").json(), {"status": "ok"})
        self.assertIn("models", client.get("/api/models").json())

    def test_issp_evidence_keeps_response_trends_empty_when_percentages_are_unavailable(self):
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
                "response_data_status": "source_missing",
                "response_data_missing_waves": ["1994", "2002", "2012"],
                "annotation_status": "labeled",
                "annotation_uncertain": False,
            }
        )

        self.assertEqual(evidence["survey"], "ISSP")
        self.assertEqual(evidence["timeline"], [])
        self.assertEqual(evidence["insight"], "")
        self.assertEqual(evidence["availableWaves"], ["1994", "2002", "2012"])
        self.assertEqual(evidence["responseDataStatus"], "source_missing")
        self.assertEqual(evidence["responseDataMissingWaves"], ["1994", "2002", "2012"])

    def test_issp_verified_distribution_becomes_a_timeline(self):
        evidence = _document_to_evidence(
            {
                "id": "ISSP_HEALTH_V10",
                "source_survey": "ISSP",
                "question_text": "Health damaging behaviour causes health problems",
                "response_options": ["1 = Strongly agree", "2 = Agree"],
                "responses_by_year": json.dumps(
                    {
                        "2011": {"1 = Strongly agree": 20.0, "2 = Agree": 80.0},
                        "2021": {"1 = Strongly agree": 25.0, "2 = Agree": 75.0},
                    }
                ),
                "response_data_status": "available",
            }
        )

        self.assertEqual(
            [{"year": 2011, "support": 20.0}, {"year": 2021, "support": 25.0}],
            evidence["timeline"],
        )
        self.assertEqual("Strongly agree", evidence["timelineResponseLabel"])

    def test_issp_evidence_exposes_the_full_compact_response_scale(self):
        options = [
            "Strongly agree",
            "Agree",
            "Neither agree nor disagree",
            "Disagree",
            "Strongly disagree",
        ]
        evidence = _document_to_evidence(
            {
                "id": "ISSP_HEALTH_001",
                "question_text": "Health damaging behaviour causes health problems",
                "categories": ["Health and Health Care"],
                "source_survey": "ISSP",
                "response_options": options,
            }
        )

        self.assertEqual(evidence["responseOptionCount"], 5)
        self.assertEqual(evidence["responseOptions"], options)

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

    def test_default_models_are_gpt_and_claude(self):
        self.assertEqual(
            default_model_names(["DeepSeek-V4-Pro", "Claude-Opus-4.8", "GPT-5.5", "Llama-3.3"]),
            ["GPT-5.5", "Claude-Opus-4.8"],
        )

    def test_page_parser_prefers_article_text_and_skips_navigation(self):
        parser = _PageTextParser()
        parser.feed("<html><title>Example</title><nav>Navigation words</nav><article><p>" + "Useful research text " * 20 + "</p></article></html>")
        self.assertEqual(parser.title, "Example")
        self.assertIn("Useful research text", parser.text())
        self.assertNotIn("Navigation words", parser.text())

    def test_mental_illness_sentence_returns_primary_model_results(self):
        payload = '{"overall_bias_score": 0.7, "bias_detected": true, "reasoning_summary": "A claim about a group merits careful evidence.", "categories": []}'
        with (
            patch("src.api.fastapi_app.openai_client", return_value=object()),
            patch("src.api.fastapi_app.create_embedding", return_value=[0.1]),
            patch("src.api.fastapi_app.retrieve_balanced_documents", return_value=[]),
            patch("src.api.fastapi_app.create_completion", return_value=CompletionResult(text=payload)),
        ):
            response = TestClient(app).post(
                "/api/analyze",
                json={"text": "Mental illnesses are not real illnesses."},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["models"]), 2)

    def test_stalled_model_returns_timeout_result(self):
        def slow_completion(*_args, **_kwargs):
            time.sleep(0.05)
            return CompletionResult(text="{}")

        with (
            patch("src.api.fastapi_app.openai_client", return_value=object()),
            patch("src.api.fastapi_app.create_embedding", return_value=[0.2]),
            patch("src.api.fastapi_app.retrieve_balanced_documents", return_value=[]),
            patch("src.api.fastapi_app.create_completion", side_effect=slow_completion),
            patch("src.api.fastapi_app.ANALYZE_MODEL_TIMEOUT_SECONDS", 0.01),
        ):
            response = TestClient(app).post(
                "/api/analyze", json={"text": "A fresh timeout regression case."}
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            all(model["error"] == "completion_timeout" for model in response.json()["models"])
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
