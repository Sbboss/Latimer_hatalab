from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from src.config import (
    AZURE_ANTHROPIC_API_KEY,
    AZURE_ANTHROPIC_ENDPOINT,
    AZURE_DEFAULT_MODEL,
    AZURE_MODEL_DEPLOYMENTS,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_EMBEDDING_MODEL,
)


class ModelCompletionError(RuntimeError):
    """Structured completion error with optional classification code."""

    def __init__(self, message: str, code: str = "completion_failed"):
        super().__init__(message)
        self.code = code


@dataclass
class CompletionResult:
    """A model's final answer, plus its internal "thinking" trace when the
    deployment/provider exposes one (Claude extended thinking blocks, or an
    OpenAI reasoning-model summary). `thinking` is None when the provider
    doesn't support it or none was returned.
    """

    text: str
    thinking: str | None = None


def openai_client():
    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY:
        raise ValueError("AZURE_ENDPOINT/AZURE_OPENAI_ENDPOINT and AZURE_API_KEY/AZURE_OPENAI_API_KEY must be set")
    return OpenAI(api_key=AZURE_OPENAI_API_KEY, base_url=AZURE_OPENAI_ENDPOINT)


def anthropic_client():
    if not AZURE_ANTHROPIC_ENDPOINT or not AZURE_ANTHROPIC_API_KEY:
        raise ValueError("AZURE_ANTHROPIC_ENDPOINT and AZURE_API_KEY/AZURE_ANTHROPIC_API_KEY must be set")

    try:
        from anthropic import AnthropicFoundry
    except ImportError as exc:
        raise ImportError("Install the Anthropic SDK with `pip install anthropic` to use Claude Foundry deployments") from exc

    return AnthropicFoundry(api_key=AZURE_ANTHROPIC_API_KEY, base_url=AZURE_ANTHROPIC_ENDPOINT)


def resolve_model_deployment(model: str | None = None) -> str:
    """Resolve a display model name to its Azure deployment name."""
    selected = model or AZURE_DEFAULT_MODEL
    return AZURE_MODEL_DEPLOYMENTS.get(selected, selected)


def resolve_model_provider(model: str | None = None) -> str:
    """Infer provider from display name or Azure deployment name."""
    selected = model or AZURE_DEFAULT_MODEL
    deployment = resolve_model_deployment(selected)
    searchable_name = f"{selected} {deployment}".lower()
    if "claude" in searchable_name or "anthropic" in searchable_name:
        return "anthropic"
    return "openai"


def create_embedding(client, text: str) -> list[float]:
    result = client.embeddings.create(model=AZURE_OPENAI_EMBEDDING_MODEL, input=text)
    return result.data[0].embedding


def _anthropic_text(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content

    text_parts: list[str] = []
    for block in content or []:
        text = getattr(block, "text", None)
        if text:
            text_parts.append(text)
        elif isinstance(block, dict) and block.get("text"):
            text_parts.append(str(block["text"]))

    return "\n".join(text_parts) if text_parts else str(content)


def _anthropic_is_refusal(message: Any) -> bool:
    """Detect Claude's own model-level safety refusal.

    Unlike Azure OpenAI's content filter (a separate pre-classifier that raises
    an HTTP error), Claude can decline a request as a normal 200 response: either
    via `stop_reason == "refusal"` or a content block of type "refusal". Azure
    Foundry guardrails are not yet wired up for Claude deployments, so this is
    not something a Foundry content-filter config change can affect.
    """
    if getattr(message, "stop_reason", None) == "refusal":
        return True

    content = getattr(message, "content", None) or []
    for block in content:
        block_type = getattr(block, "type", None) or (isinstance(block, dict) and block.get("type"))
        if block_type == "refusal":
            return True

    return False


def _anthropic_thinking_text(message: Any) -> str | None:
    """Extract Claude's extended-thinking scratchpad text, if present.

    Thinking blocks have a `.thinking` attribute (not `.text`), so they're
    naturally skipped by `_anthropic_text()`'s content extraction above.
    """
    content = getattr(message, "content", None) or []
    parts: list[str] = []
    for block in content:
        block_type = getattr(block, "type", None) or (isinstance(block, dict) and block.get("type"))
        if block_type != "thinking":
            continue
        text = getattr(block, "thinking", None)
        if text is None and isinstance(block, dict):
            text = block.get("thinking")
        if text:
            parts.append(str(text))
    return "\n".join(parts) if parts else None


def _openai_reasoning_summary(response: Any) -> str | None:
    """Extract a reasoning model's summarized "thinking" trace from a
    Responses API result, when the deployment supports `reasoning.summary`
    and one was actually returned.
    """
    parts: list[str] = []
    for item in getattr(response, "output", []) or []:
        item_type = getattr(item, "type", None) or (isinstance(item, dict) and item.get("type"))
        if item_type != "reasoning":
            continue
        summary = getattr(item, "summary", None) or (isinstance(item, dict) and item.get("summary")) or []
        for part in summary:
            text = getattr(part, "text", None) or (isinstance(part, dict) and part.get("text"))
            if text:
                parts.append(str(text))
    return "\n".join(parts) if parts else None


def _openai_response_text(response: Any) -> str | None:
    """Extract text from OpenAI Responses API objects across SDK versions.

    Returns None (rather than a stringified response repr) when there's no
    real output text, so callers can treat that as a failed attempt and try
    the next payload/fallback instead of returning unparseable garbage.
    """
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text)

    text_parts: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                text_parts.append(str(text))

    return "\n".join(text_parts) if text_parts else None


def _openai_chat_text(response: Any) -> str | None:
    """Extract text from OpenAI-compatible chat completion responses.

    Returns None when there's no real content — e.g. a reasoning model that
    spent its entire `max_tokens` budget on internal reasoning and returned
    `finish_reason == "length"` with empty `content` — instead of falling
    back to a stringified response repr that looks superficially like
    "output" but can never be parsed as the expected JSON.
    """
    choices = getattr(response, "choices", []) or []
    if not choices:
        return None

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None)
    return str(content) if content else None


def create_completion(
    client,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.2,
    model: str | None = None,
    system_prompt: str | None = None,
    response_schema: dict[str, Any] | None = None,
    strict_json: bool = False,
) -> CompletionResult:
    deployment_name = resolve_model_deployment(model)
    provider = resolve_model_provider(model)

    if provider == "anthropic":
        prompt_text = prompt
        if system_prompt:
            prompt_text = f"{system_prompt.strip()}\n\n{prompt}"
        messages = [{"role": "user", "content": prompt_text}]

        # Extended thinking gives Claude an explicit scratchpad to reason in
        # before answering, which improves nuanced judgments like bias
        # classification. `temperature` must be left at its default (Claude
        # rejects a custom value while thinking is active) in both styles.
        # Claude API versions differ on how thinking is configured:
        #   - newer models (e.g. this Opus 4.8 deployment) use
        #     `thinking.type: "adaptive"` + a separate `output_config.effort`
        #     dial, and reject the older explicit-budget style outright.
        #   - older Claude 3.7+/4 models use `thinking.type: "enabled"` with
        #     an explicit `budget_tokens`, and `max_tokens` must comfortably
        #     exceed that budget since both draw from the same output cap.
        # Try both, then fall back to no thinking at all for deployments that
        # support neither.
        thinking_budget = max(1024, min(max_tokens, 8000))
        thinking_max_tokens = thinking_budget + max_tokens

        anthropic_payloads = [
            {
                "model": deployment_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "thinking": {"type": "adaptive"},
                "output_config": {"effort": "medium"},
            },
            {
                "model": deployment_name,
                "messages": messages,
                "max_tokens": thinking_max_tokens,
                "thinking": {"type": "enabled", "budget_tokens": thinking_budget},
            },
            {"model": deployment_name, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
            # Some newer Claude deployments reject a custom `temperature`
            # (e.g. "`temperature` is deprecated for this model").
            {"model": deployment_name, "messages": messages, "max_tokens": max_tokens},
        ]
        anthropic_errors: list[Exception] = []
        response = None
        for payload in anthropic_payloads:
            try:
                response = anthropic_client().messages.create(**payload)
                break
            except Exception as exc:
                anthropic_errors.append(exc)
        if response is None:
            raise ModelCompletionError(
                f"Anthropic completion failed for deployment '{deployment_name}'. "
                f"Errors: {[str(error) for error in anthropic_errors]}",
                code="completion_failed",
            )
        if _anthropic_is_refusal(response):
            raise ModelCompletionError(
                f"Claude deployment '{deployment_name}' declined to respond (model-level refusal, "
                "not an Azure content filter block).",
                code="model_refusal",
            )
        return CompletionResult(text=_anthropic_text(response), thinking=_anthropic_thinking_text(response))

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response_errors: list[Exception] = []
    # Note: the Responses API takes `input`, not `messages` (that's a Chat
    # Completions-only param name). Passing `messages` here always raised
    # "unexpected keyword argument 'messages'" and silently fell through to
    # the legacy Chat Completions payloads below on every call.
    #
    # Reasoning models (e.g. GPT-5.5) spend `reasoning_tokens` out of the same
    # `max_output_tokens` budget used for the visible answer, so we try a
    # "medium" effort first for deeper thinking (paired with `summary: auto`
    # to capture the actual reasoning trace, not just the model's own
    # self-reported summary), then degrade through lower effort and finally
    # no `reasoning` field at all for deployments/models that reject it.
    reasoning_tiers: list[dict[str, str] | None] = [
        {"effort": "medium", "summary": "auto"},
        {"effort": "medium"},
        {"effort": "low"},
        None,
    ]

    def _build_response_payloads(schema_format: dict[str, Any] | None) -> list[dict[str, Any]]:
        payloads = []
        for reasoning in reasoning_tiers:
            for use_temperature in (True, False):
                payload: dict[str, Any] = {
                    "model": deployment_name,
                    "input": messages,
                    "max_output_tokens": max_tokens,
                }
                if use_temperature:
                    payload["temperature"] = temperature
                if reasoning:
                    payload["reasoning"] = reasoning
                if schema_format:
                    payload["text"] = {"format": schema_format}
                payloads.append(payload)
        return payloads

    if response_schema:
        json_schema_payload = {
            "type": "json_schema",
            "name": response_schema.get("name", "analysis_output"),
            "schema": response_schema,
            "strict": strict_json,
        }
        response_payloads = _build_response_payloads(json_schema_payload) + _build_response_payloads(None)
    else:
        response_payloads = _build_response_payloads(None)

    for payload in response_payloads:
        try:
            response = client.responses.create(**payload)
            text = _openai_response_text(response)
            if text and text.strip():
                return CompletionResult(text=text, thinking=_openai_reasoning_summary(response))
            # A reasoning model can exhaust its budget on reasoning alone and
            # return no visible text; treat that as a failed attempt so we
            # try the next payload/fallback instead of returning nothing.
            response_errors.append(
                RuntimeError(
                    f"Responses API returned no usable output text "
                    f"(status={getattr(response, 'status', None)}, "
                    f"incomplete_reason={getattr(getattr(response, 'incomplete_details', None), 'reason', None)})"
                )
            )
        except Exception as exc:
            response_errors.append(exc)

    chat_errors: list[Exception] = []
    chat_payloads = [
        {
            "model": deployment_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        {
            "model": deployment_name,
            "messages": messages,
            "max_completion_tokens": max_tokens,
        },
        {
            "model": deployment_name,
            "messages": messages,
        },
    ]
    for payload in chat_payloads:
        try:
            response = client.chat.completions.create(**payload)
            text = _openai_chat_text(response)
            if text and text.strip():
                # Chat Completions has no reasoning-summary concept.
                return CompletionResult(text=text, thinking=None)
            finish_reason = getattr(response.choices[0], "finish_reason", None) if getattr(response, "choices", None) else None
            chat_errors.append(
                RuntimeError(f"Chat completion returned no usable content (finish_reason={finish_reason})")
            )
        except Exception as exc:
            chat_errors.append(exc)

    response_error_text = " ".join(str(error) for error in response_errors)
    chat_error_text = " ".join(str(error) for error in chat_errors)
    combined_error_text = f"{response_error_text} {chat_error_text}".lower()
    if "content_filter" in combined_error_text:
        error_code = "content_filter_blocked"
    elif "no usable" in combined_error_text or "finish_reason=length" in combined_error_text:
        error_code = "reasoning_budget_exhausted"
    else:
        error_code = "completion_failed"

    raise ModelCompletionError(
        f"OpenAI-compatible completion failed for deployment '{deployment_name}'. "
        f"Responses API errors: {[str(error) for error in response_errors]}. "
        f"Chat completions errors: {[str(error) for error in chat_errors]}",
        code=error_code,
    )
