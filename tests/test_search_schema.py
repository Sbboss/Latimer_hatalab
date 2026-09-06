import unittest
from unittest.mock import MagicMock, patch

from src.storage.azure_vector_store import _index_definition, list_indexed_document_ids


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
            "response_base_by_year",
            "response_data_status",
            "response_data_source",
            "response_data_doi",
            "response_distribution_method",
            "response_data_missing_waves",
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

    @patch("src.storage.azure_vector_store.create_search_client")
    def test_read_back_collects_all_ids_with_a_source_filter(self, create_client):
        client = MagicMock()
        client.search.return_value = iter([{"id": "ISSP_1"}, {"id": "ISSP_2"}])
        create_client.return_value = client

        self.assertEqual(
            {"ISSP_1", "ISSP_2"},
            list_indexed_document_ids("ISSP"),
        )
        client.search.assert_called_once_with(
            search_text="*",
            filter="source_survey eq 'ISSP'",
            select=["id"],
        )


if __name__ == "__main__":
    unittest.main()
