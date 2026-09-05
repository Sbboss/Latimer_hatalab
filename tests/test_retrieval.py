import unittest

from src.retrieval.evaluate import _metrics, evaluate_cases
from src.retrieval.rag import (
    build_retrieval_prompt,
    canonical_category,
    extract_timeline_from_document,
    interleave_survey_documents,
    select_evidence_documents,
)


class RetrievalGroundingTests(unittest.TestCase):
    def test_category_aliases_map_model_labels_to_formal_tags(self):
        self.assertEqual("Race and Ethnicity", canonical_category("Race / ethnicity"))
        self.assertEqual("Gender Expectations", canonical_category("Gender / sexism"))
        self.assertEqual(
            "Economic Background (Socioeconomic Status)",
            canonical_category("Economic class"),
        )

    def test_evidence_is_category_aligned_without_unrelated_fallback(self):
        documents = [
            {"id": "p", "categories": ["Political Identity"]},
            {"id": "g", "categories": ["Gender Expectations"]},
            {"id": "r", "categories": ["Religion and Belief"]},
        ]
        self.assertEqual(
            ["g"],
            [
                document["id"]
                for document in select_evidence_documents(
                    documents, "Gender / sexism", per_survey_limit=2
                )
            ],
        )
        self.assertEqual(
            [],
            select_evidence_documents(
                documents,
                "Age",
                per_survey_limit=2,
            ),
        )

    def test_evidence_preserves_rank_with_equal_survey_quotas(self):
        documents = [
            {
                "id": "gss-1",
                "source_survey": "GSS",
                "categories": ["Gender Expectations"],
            },
            {
                "id": "gss-2",
                "categories": ["Gender Expectations"],
            },
            {
                "id": "gss-3",
                "source_survey": "GSS",
                "categories": ["Gender Expectations"],
            },
            {
                "id": "ISSP_FCGR_1",
                "source_survey": "ISSP",
                "categories": ["Gender Expectations"],
            },
            {
                "id": "ISSP_FCGR_2",
                "source_survey": "ISSP",
                "categories": ["Gender Expectations"],
            },
            {
                "id": "ISSP_REL_1",
                "source_survey": "ISSP",
                "categories": ["Religion and Belief"],
            },
        ]

        selected = select_evidence_documents(
            documents,
            "Gender / sexism",
            per_survey_limit=2,
        )

        self.assertEqual(
            ["gss-1", "ISSP_FCGR_1", "gss-2", "ISSP_FCGR_2"],
            [document["id"] for document in selected],
        )

    def test_balanced_retrieval_merge_preserves_each_survey_rank(self):
        merged = interleave_survey_documents(
            [{"id": "gss-1"}, {"id": "gss-2"}, {"id": "gss-3"}],
            [{"id": "issp-1"}, {"id": "issp-2"}],
        )

        self.assertEqual(
            ["gss-1", "issp-1", "gss-2", "issp-2", "gss-3"],
            [document["id"] for document in merged],
        )

    def test_issp_without_response_percentages_has_no_timeline(self):
        self.assertEqual(
            [],
            extract_timeline_from_document(
                {
                    "response_options": ["Agree", "Disagree"],
                    "responses_by_year": "{}",
                    "available_waves": ["1990", "2000"],
                }
            ),
        )

    def test_prompt_states_evidence_boundary_and_provenance(self):
        prompt = build_retrieval_prompt(
            "example",
            [
                {
                    "id": "ISSP_REL_V6",
                    "source_survey": "ISSP",
                    "question_text": "Sexual relations between two adults of the same sex",
                    "categories": ["Sexual Orientation"],
                    "module_name": "Religion",
                    "available_waves": ["1991", "1998"],
                    "country_count": 20,
                    "source_dataset": "ZA8792",
                    "response_options": ["Agree", "Disagree"],
                    "responses_by_year": "{}",
                    "annotation_status": "labeled",
                }
            ],
        )
        self.assertIn("Evidence ID: ISSP_REL_V6", prompt)
        self.assertIn("Survey: ISSP", prompt)
        self.assertIn("Response percentages are unavailable", prompt)
        self.assertIn("reflection question", prompt)

    def test_metrics_use_rank_and_complete_relevant_set(self):
        metrics = _metrics(["x", "a", "b"], {"a", "b"}, top_k=3)
        self.assertEqual(1.0, metrics["recall_at_k"])
        self.assertEqual(0.5, metrics["reciprocal_rank"])
        self.assertGreater(metrics["ndcg_at_k"], 0.6)
        self.assertLess(metrics["ndcg_at_k"], 1.0)

    def test_evaluator_reports_all_cases(self):
        cases = [{"query": "q", "relevant_ids": ["a"]}]

        def search(_query, _top_k):
            return [{"id": "a"}]

        report = evaluate_cases(cases, search, top_k=1)
        self.assertEqual(1, report["aggregate"]["case_count"])
        self.assertEqual(1.0, report["aggregate"]["mean_recall_at_k"])


if __name__ == "__main__":
    unittest.main()
