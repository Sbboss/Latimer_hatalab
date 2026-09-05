import re
import unittest
from pathlib import Path


FRONTEND_SOURCE = Path("frontend/src")


class FrontendProductContractTests(unittest.TestCase):
    def test_primary_and_expanded_analysis_use_explicit_scopes(self):
        app_source = (FRONTEND_SOURCE / "App.tsx").read_text(encoding="utf-8")
        api_source = (FRONTEND_SOURCE / "lib/api.ts").read_text(encoding="utf-8")

        self.assertIn('onAnalyze={() => handleAnalyze("primary")}', app_source)
        self.assertIn('onAnalyzeMore={() => handleAnalyze("all")}', app_source)
        self.assertNotIn("onAnalyze={handleAnalyze}", app_source)
        self.assertIn("opts.selectedModels ?? opts.modelNames", api_source)

    def test_product_copy_avoids_prototype_and_demo_language(self):
        violations = []
        banned = re.compile(r"\b(?:prototype|demo)\b", re.IGNORECASE)
        for path in FRONTEND_SOURCE.rglob("*"):
            if path.suffix not in {".ts", ".tsx", ".css"}:
                continue
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if banned.search(line):
                    violations.append(f"{path}:{line_number}")

        self.assertEqual(violations, [])

    def test_redundant_workspace_labels_are_absent(self):
        workspace = (FRONTEND_SOURCE / "components/Workspace.tsx").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("Analyzed document", workspace)
        self.assertNotIn("Draft document", workspace)
        self.assertNotIn("Active model:", workspace)

    def test_insight_board_shows_one_question_per_survey_and_a_continuation_cue(self):
        insight_board = (
            FRONTEND_SOURCE / "components/InsightBoard.tsx"
        ).read_text(encoding="utf-8")

        self.assertIn("groupEvidenceBySurvey(highlight.evidence, 1)", insight_board)
        self.assertIn("Continue to more survey questions", insight_board)

    def test_neutral_analysis_avoids_empty_evidence_cards_and_biased_examples(self):
        insight_board = (
            FRONTEND_SOURCE / "components/InsightBoard.tsx"
        ).read_text(encoding="utf-8")
        social_evidence = (
            FRONTEND_SOURCE / "components/SocialEvidence.tsx"
        ).read_text(encoding="utf-8")

        self.assertNotIn("surprisingly articulate", insight_board)
        self.assertNotIn("evidence-card-missing", social_evidence)
        self.assertIn("if (evidenceItems.length === 0) return null", social_evidence)

    def test_about_replaces_homepage_method_and_includes_ray_contact(self):
        app_source = (FRONTEND_SOURCE / "App.tsx").read_text(encoding="utf-8")
        nav_source = (FRONTEND_SOURCE / "components/Nav.tsx").read_text(encoding="utf-8")
        about_source = (FRONTEND_SOURCE / "components/About.tsx").read_text(encoding="utf-8")

        self.assertNotIn("<HowItWorks", app_source)
        self.assertIn("About", nav_source)
        self.assertIn("Humanity and Technoscience (HAT) Lab", about_source)
        self.assertIn("fouche@northwestern.edu", about_source)

    def test_url_input_is_visible_in_workspace_copy(self):
        workspace = (FRONTEND_SOURCE / "components/Workspace.tsx").read_text(encoding="utf-8")
        self.assertGreaterEqual(workspace.count("public URL"), 2)

    def test_homepage_filler_copy_is_absent(self):
        active_sources = "\n".join(
            (FRONTEND_SOURCE / path).read_text(encoding="utf-8")
            for path in [
                "App.tsx",
                "components/Hero.tsx",
                "components/Nav.tsx",
                "components/SocialEvidence.tsx",
                "components/Footer.tsx",
            ]
        )
        for phrase in [
            "Evidence-led bias learning",
            "Open workspace",
            "Response shares appear when percentages exist",
            "Research scope cards show",
        ]:
            self.assertNotIn(phrase, active_sources)

    def test_decorative_coverage_timeline_is_replaced_by_measurement_profile(self):
        coverage = (FRONTEND_SOURCE / "components/CoverageChart.tsx").read_text(encoding="utf-8")
        self.assertNotIn("<svg", coverage)
        self.assertIn("How this question was measured", coverage)
        self.assertIn("Response scale", coverage)


if __name__ == "__main__":
    unittest.main()
