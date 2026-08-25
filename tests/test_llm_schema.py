import unittest
from types import SimpleNamespace

from src.llm.azure_openai_client import create_completion


class _FakeResponses:
    def __init__(self):
        self.payload = None

    def create(self, **payload):
        self.payload = payload
        return SimpleNamespace(output_text='{"ok": true}', output=[])


class LlmSchemaTests(unittest.TestCase):
    def test_schema_name_is_only_in_the_responses_format_wrapper(self):
        responses = _FakeResponses()
        client = SimpleNamespace(responses=responses)
        schema = {
            "name": "example_output",
            "type": "object",
            "additionalProperties": False,
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
        }

        completion = create_completion(
            client,
            "Return JSON",
            model="gpt-test",
            response_schema=schema,
            strict_json=True,
        )

        self.assertEqual(completion.text, '{"ok": true}')
        schema_format = responses.payload["text"]["format"]
        self.assertEqual(schema_format["name"], "example_output")
        self.assertNotIn("name", schema_format["schema"])
        self.assertEqual(schema_format["schema"]["type"], "object")


if __name__ == "__main__":
    unittest.main()
