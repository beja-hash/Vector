import asyncio
import json
import logging
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.services.llm.errors import LlmApiError, LlmConfigurationError, LlmInvalidJsonError
from app.services.llm.schemas import ChatCompletionRequest, ChatMessage

logger = logging.getLogger(__name__)

TRANSIENT_HTTP_STATUSES = {408, 409, 425, 429, 500, 502, 503, 504}


class PolzaClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int = 45,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.polza_api_key
        self.base_url = (base_url or settings.polza_base_url).rstrip("/")
        self.model = model or settings.polza_model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(1, max_retries)

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 220,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise LlmConfigurationError("POLZA_API_KEY is not configured")

        payload = ChatCompletionRequest(
            model=self.model,
            messages=[
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ],
            temperature=0,
            max_tokens=max_tokens,
        )
        response = await self._post_chat_completions(payload.model_dump())
        content = _extract_message_content(response)
        try:
            return _parse_json_content(content)
        except LlmInvalidJsonError:
            logger.warning("[LLM][ICP] invalid json response")
            raise

    async def _post_chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await asyncio.to_thread(self._post_once, url, body, headers)
            except HTTPError as exc:
                last_error = exc
                if exc.code not in TRANSIENT_HTTP_STATUSES or attempt == self.max_retries:
                    raise LlmApiError(f"Polza API returned HTTP {exc.code}") from exc
                await asyncio.sleep(min(2 ** (attempt - 1), 5))
            except URLError as exc:
                last_error = exc
                if attempt == self.max_retries:
                    raise LlmApiError("Polza API request failed") from exc
                await asyncio.sleep(min(2 ** (attempt - 1), 5))

        raise LlmApiError("Polza API request failed") from last_error

    def _post_once(self, url: str, body: bytes, headers: dict[str, str]) -> dict[str, Any]:
        request = Request(url, data=body, headers=headers, method="POST")
        with urlopen(request, timeout=self.timeout_seconds) as response:
            raw_body = response.read().decode("utf-8")
        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise LlmApiError("Polza API returned non-JSON response") from exc
        if not isinstance(parsed, dict):
            raise LlmApiError("Polza API returned unexpected response")
        return parsed


def _extract_message_content(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LlmApiError("Polza API response has no choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise LlmApiError("Polza API response has invalid choice")
    message = first.get("message")
    if not isinstance(message, dict):
        raise LlmApiError("Polza API response has invalid message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LlmApiError("Polza API response has empty content")
    return content


def _parse_json_content(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LlmInvalidJsonError("Model response is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise LlmInvalidJsonError("Model response JSON must be an object")
    return parsed
