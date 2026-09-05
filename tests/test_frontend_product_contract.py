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

    def test_insight_board_shows_more_retrieved_questions_and_a_continuation_cue(self):
        insight_board = (
            FRONTEND_SOURCE / "components/InsightBoard.tsx"
        ).read_text(encoding="utf-8")

        self.assertIn("groupEvidenceBySurvey(highlight.evidence, 2)", insight_board)
        self.assertIn("Explore all {evidenceCount} retrieved questions", insight_board)


if __name__ == "__main__":
    unittest.main()
