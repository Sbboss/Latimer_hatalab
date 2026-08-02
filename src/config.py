import os
import json
from dotenv import load_dotenv

load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")


def _derive_anthropic_endpoint(endpoint: str | None) -> str | None:
	"""Derive Azure AI Foundry Anthropic endpoint from an OpenAI v1 endpoint."""
	if not endpoint:
		return None
	if endpoint.rstrip("/").endswith("/openai/v1"):
		return endpoint.rstrip("/")[: -len("/openai/v1")] + "/anthropic"
	return None


AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT") or AZURE_ENDPOINT
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or AZURE_API_KEY
AZURE_OPENAI_RESOURCE_NAME = os.getenv("AZURE_OPENAI_RESOURCE_NAME")
AZURE_OPENAI_EMBEDDING_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
AZURE_OPENAI_COMPLETION_MODEL = os.getenv("AZURE_OPENAI_COMPLETION_MODEL", "gpt-4o-mini")

AZURE_ANTHROPIC_ENDPOINT = (
	os.getenv("AZURE_ANTHROPIC_ENDPOINT")
	or os.getenv("AZURE_FOUNDRY_ANTHROPIC_ENDPOINT")
	or _derive_anthropic_endpoint(AZURE_OPENAI_ENDPOINT)
)
AZURE_ANTHROPIC_API_KEY = os.getenv("AZURE_ANTHROPIC_API_KEY") or AZURE_API_KEY
AZURE_ANTHROPIC_MODEL = os.getenv("AZURE_ANTHROPIC_MODEL", "claude-opus-4-6")

DEFAULT_MODEL_DEPLOYMENTS = {
	"GPT-5.5": "gpt-5.5",
	"Claude-Opus-4.6": "claude-opus-4-6",
	"Llama-3.3-70B-Instruct": "Llama-3.3-70B-Instruct",
}


def _load_model_deployments() -> dict[str, str]:
	"""Load display-name to Azure deployment-name mapping from JSON env, with defaults."""
	raw = os.getenv("AZURE_MODEL_DEPLOYMENTS_JSON") or os.getenv("AZURE_MODELS_JSON")
	if not raw:
		return DEFAULT_MODEL_DEPLOYMENTS
	try:
		parsed = json.loads(raw)
	except json.JSONDecodeError as exc:
		raise ValueError("AZURE_MODEL_DEPLOYMENTS_JSON must be valid JSON") from exc
	if not isinstance(parsed, dict):
		raise ValueError("AZURE_MODEL_DEPLOYMENTS_JSON must be a JSON object")
	return {str(display): str(deployment) for display, deployment in parsed.items()}


AZURE_MODEL_DEPLOYMENTS = _load_model_deployments()
AZURE_DEFAULT_MODEL = os.getenv("AZURE_DEFAULT_MODEL") or AZURE_OPENAI_COMPLETION_MODEL

AZURE_COGNITIVE_SEARCH_ENDPOINT = os.getenv("AZURE_COGNITIVE_SEARCH_ENDPOINT")
AZURE_COGNITIVE_SEARCH_API_KEY = os.getenv("AZURE_COGNITIVE_SEARCH_API_KEY")
AZURE_COGNITIVE_SEARCH_INDEX_NAME = os.getenv("AZURE_COGNITIVE_SEARCH_INDEX_NAME", "gss-index")

AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

GSS_RAW_PATH = "gss_questions.json"
GSS_PROCESSED_PATH = "data/processed/gss_questions_normalized.json"
