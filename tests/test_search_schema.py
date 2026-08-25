import unittest

from src.storage.azure_vector_store import _index_definition


class SearchSchemaTests(unittest.TestCase):
    def test_index_keeps_legacy_fields_and_adds_issp_provenance(self):
        index = _index_definition()
        fields = {field.name: field for field in index.fields}

        for name in (
            "id",
            "content",
            "content_vector",
            "var",
            "response_options",
            "responses_by_year",
            "question_text",
            "source_survey",
            "module_name",
            "available_waves",
            "countries",
            "country_count",
            "annotation_status",
            "annotation_uncertain",
        ):
            self.assertIn(name, fields)

        self.assertEqual(fields["content_vector"].vector_search_dimensions, 1536)
        semantic = index.semantic_search.configurations[0]
        self.assertEqual(
            semantic.prioritized_fields.title_field.field_name,
            "question_text",
        )


if __name__ == "__main__":
    unittest.main()
