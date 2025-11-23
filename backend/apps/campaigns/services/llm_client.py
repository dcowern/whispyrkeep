"""
OpenAI-Compatible LLM Client.

Provides a unified interface for calling LLM endpoints with:
- Support for OpenAI, Anthropic, Azure OpenAI, and custom endpoints
- Retry with exponential backoff
- Encrypted API key decryption
- Streaming support (optional)

Tickets: 8.0.1, 8.0.2

Based on SYSTEM_DESIGN.md section 8 LLM Orchestration.
"""

import logging
import time
from collections.abc import Generator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx

from apps.llm_config.encryption import decrypt_api_key
from apps.llm_config.models import LlmEndpointConfig

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure-openai"
    LOCAL = "local"


class LLMError(Exception):
    """Base exception for LLM errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.retryable = retryable


class RateLimitError(LLMError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message, status_code=429, retryable=True)
        self.retry_after = retry_after


class AuthenticationError(LLMError):
    """Authentication failed."""

    def __init__(self, message: str):
        super().__init__(message, status_code=401, retryable=False)


class ServerError(LLMError):
    """Server-side error (5xx)."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message, status_code=status_code, retryable=True)


@dataclass
class LLMClientConfig:
    """Configuration for the LLM client."""

    provider: LLMProvider
    api_key: str
    model: str
    base_url: str | None = None
    timeout: float = 120.0
    max_retries: int = 3
    initial_retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    retry_multiplier: float = 2.0

    @classmethod
    def from_endpoint_config(cls, config: LlmEndpointConfig) -> "LLMClientConfig":
        """Create from a database LlmEndpointConfig."""
        # Decrypt the API key
        api_key = decrypt_api_key(config.api_key_encrypted)

        return cls(
            provider=LLMProvider(config.provider_name),
            api_key=api_key,
            model=config.default_model,
            base_url=config.base_url or None,
        )

    def get_base_url(self) -> str:
        """Get the base URL for API calls."""
        if self.base_url:
            return self.base_url

        if self.provider == LLMProvider.OPENAI:
            return "https://api.openai.com/v1"
        elif self.provider == LLMProvider.ANTHROPIC:
            return "https://api.anthropic.com/v1"
        elif self.provider == LLMProvider.AZURE_OPENAI:
            raise ValueError("Azure OpenAI requires a base_url")
        elif self.provider == LLMProvider.LOCAL:
            return "http://localhost:8080/v1"
        else:
            raise ValueError(f"Unknown provider: {self.provider}")


@dataclass
class Message:
    """A chat message."""

    role: str  # "system", "user", "assistant"
    content: str

    def to_dict(self) -> dict:
        """Convert to API format."""
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """Response from an LLM call."""

    content: str
    model: str
    usage: dict = field(default_factory=dict)
    finish_reason: str | None = None
    raw_response: dict = field(default_factory=dict)

    @property
    def input_tokens(self) -> int:
        """Get input token count."""
        return self.usage.get("prompt_tokens", 0)

    @property
    def output_tokens(self) -> int:
        """Get output token count."""
        return self.usage.get("completion_tokens", 0)

    @property
    def total_tokens(self) -> int:
        """Get total token count."""
        return self.usage.get("total_tokens", 0)


class LLMClient:
    """
    OpenAI-compatible LLM client with retry support.

    Supports:
    - OpenAI Chat Completions API
    - Anthropic Messages API (via compatibility layer)
    - Azure OpenAI
    - Local/custom OpenAI-compatible endpoints

    Usage:
        config = LLMClientConfig.from_endpoint_config(db_config)
        client = LLMClient(config)

        messages = [
            Message(role="system", content="You are a DM..."),
            Message(role="user", content="I attack the goblin"),
        ]
        response = client.chat(messages)
    """

    def __init__(self, config: LLMClientConfig):
        """Initialize the client."""
        self.config = config
        self._http_client: httpx.Client | None = None

    @property
    def http_client(self) -> httpx.Client:
        """Get or create HTTP client (lazy initialization)."""
        if self._http_client is None:
            self._http_client = httpx.Client(
                timeout=self.config.timeout,
                follow_redirects=True,
            )
        return self._http_client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
        }

        if self.config.provider == LLMProvider.ANTHROPIC:
            headers["x-api-key"] = self.config.api_key
            headers["anthropic-version"] = "2023-06-01"
        else:
            # OpenAI-style authorization
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        return headers

    def _build_request_body(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict:
        """Build the request body for the API call."""
        body: dict[str, Any] = {
            "model": self.config.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
        }

        if max_tokens:
            body["max_tokens"] = max_tokens

        # Add any additional parameters
        body.update(kwargs)

        return body

    def _parse_response(self, response_data: dict) -> LLMResponse:
        """Parse the API response."""
        # Handle OpenAI-style response
        if "choices" in response_data:
            choice = response_data["choices"][0]
            content = choice.get("message", {}).get("content", "")
            finish_reason = choice.get("finish_reason")
        # Handle Anthropic-style response
        elif "content" in response_data:
            content_blocks = response_data.get("content", [])
            content = "".join(
                block.get("text", "") for block in content_blocks if block.get("type") == "text"
            )
            finish_reason = response_data.get("stop_reason")
        else:
            content = ""
            finish_reason = None

        return LLMResponse(
            content=content,
            model=response_data.get("model", self.config.model),
            usage=response_data.get("usage", {}),
            finish_reason=finish_reason,
            raw_response=response_data,
        )

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API."""
        status_code = response.status_code

        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", response.text)
        except Exception:
            error_message = response.text

        if status_code == 401:
            raise AuthenticationError(f"Authentication failed: {error_message}")
        elif status_code == 429:
            retry_after = response.headers.get("retry-after")
            retry_seconds = float(retry_after) if retry_after else None
            raise RateLimitError(f"Rate limit exceeded: {error_message}", retry_seconds)
        elif 500 <= status_code < 600:
            raise ServerError(f"Server error: {error_message}", status_code)
        else:
            raise LLMError(
                f"API error ({status_code}): {error_message}",
                status_code=status_code,
                retryable=False,
            )

    def _calculate_retry_delay(self, attempt: int, retry_after: float | None = None) -> float:
        """Calculate delay before next retry with exponential backoff."""
        if retry_after is not None:
            return min(retry_after, self.config.max_retry_delay)

        delay = self.config.initial_retry_delay * (self.config.retry_multiplier ** attempt)
        return min(delay, self.config.max_retry_delay)

    def chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Send a chat completion request.

        Args:
            messages: List of messages in the conversation
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            **kwargs: Additional API parameters

        Returns:
            LLMResponse with the model's response

        Raises:
            LLMError: If the request fails after all retries
        """
        url = f"{self.config.get_base_url()}/chat/completions"
        headers = self._get_headers()
        body = self._build_request_body(messages, temperature, max_tokens, **kwargs)

        last_error: LLMError | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(f"LLM request attempt {attempt + 1}/{self.config.max_retries + 1}")

                response = self.http_client.post(url, json=body, headers=headers)

                if response.status_code == 200:
                    response_data = response.json()
                    return self._parse_response(response_data)
                else:
                    self._handle_error_response(response)

            except RateLimitError as e:
                last_error = e
                if attempt < self.config.max_retries:
                    delay = self._calculate_retry_delay(attempt, e.retry_after)
                    logger.warning(f"Rate limit hit, retrying in {delay:.1f}s")
                    time.sleep(delay)
                else:
                    raise

            except ServerError as e:
                last_error = e
                if attempt < self.config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(f"Server error, retrying in {delay:.1f}s: {e}")
                    time.sleep(delay)
                else:
                    raise

            except httpx.TimeoutException:
                last_error = LLMError("Request timeout", retryable=True)
                if attempt < self.config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(f"Timeout, retrying in {delay:.1f}s")
                    time.sleep(delay)
                else:
                    raise LLMError("Request timeout after all retries") from None

            except httpx.RequestError as e:
                last_error = LLMError(f"Request error: {e}", retryable=True)
                if attempt < self.config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(f"Request error, retrying in {delay:.1f}s: {e}")
                    time.sleep(delay)
                else:
                    raise LLMError(f"Request failed after all retries: {e}") from e

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise LLMError("Unknown error occurred")

    def chat_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """
        Send a streaming chat completion request.

        Args:
            messages: List of messages in the conversation
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            **kwargs: Additional API parameters

        Yields:
            String chunks of the response content
        """
        url = f"{self.config.get_base_url()}/chat/completions"
        headers = self._get_headers()
        body = self._build_request_body(messages, temperature, max_tokens, **kwargs)
        body["stream"] = True

        with self.http_client.stream("POST", url, json=body, headers=headers) as response:
            if response.status_code != 200:
                # Read the response to get error details
                response.read()
                self._handle_error_response(response)

            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break

                    try:
                        import json

                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue
