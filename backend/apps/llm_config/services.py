"""
Utilities for working with external LLM endpoints.

Functions here are intentionally small and side-effect free so they can be
easily mocked in tests while keeping network calls isolated.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple

import requests

DEFAULT_BRAND_ENDPOINTS: Dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "mistral": "https://api.mistral.ai/v1",
    "meta": "https://api.meta.com/v1",
    "google": "https://generativelanguage.googleapis.com/v1beta",
}

DEFAULT_COMPATIBILITY: Dict[str, str] = {
    "openai": "openai",
    "anthropic": "anthropic",
    "mistral": "openai",  # Mistral exposes OpenAI-compatible endpoints
    "meta": "openai",  # Meta-hosted gateways are typically OpenAI-compatible
    "google": "google",
}


class LlmEndpointError(Exception):
    """Raised when an endpoint cannot be reached or parsed."""


def _normalize_base_url(base_url: str) -> str:
    """Ensure base URLs do not end with a trailing slash."""

    return base_url[:-1] if base_url.endswith("/") else base_url


def resolve_endpoint(
    provider: str,
    base_url: Optional[str] = None,
    compatibility: Optional[str] = None,
) -> Tuple[str, str, str]:
    """Resolve provider defaults for base URL and compatibility."""

    normalized_provider = provider.lower()
    resolved_base = base_url or DEFAULT_BRAND_ENDPOINTS.get(normalized_provider)
    resolved_compat = compatibility or DEFAULT_COMPATIBILITY.get(normalized_provider, "openai")

    if normalized_provider == "custom" and not resolved_base:
        raise LlmEndpointError("Custom providers require a base URL.")

    if normalized_provider != "custom" and not resolved_base:
        raise LlmEndpointError("Unknown provider; no base URL mapping found.")

    return normalized_provider, _normalize_base_url(resolved_base), resolved_compat


def _build_headers(compatibility: str, api_key: Optional[str]) -> Dict[str, str]:
    """Construct auth headers for supported compatibilities."""

    if compatibility == "openai":
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if compatibility == "anthropic":
        return {
            "x-api-key": api_key or "",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
    # Google uses API key in query params instead of headers
    return {"Content-Type": "application/json"}


def _parse_models(payload: Dict[str, object]) -> List[str]:
    """Extract model identifiers from known response shapes."""

    models: List[str] = []

    if isinstance(payload.get("data"), list):
        models.extend(
            str(item.get("id"))
            for item in payload["data"]
            if isinstance(item, dict) and item.get("id")
        )

    if isinstance(payload.get("models"), list):
        models.extend(
            str(item.get("id") or item.get("name"))
            for item in payload["models"]
            if isinstance(item, dict) and (item.get("id") or item.get("name"))
        )

    # Deduplicate while preserving order
    seen = set()
    unique_models: List[str] = []
    for model in models:
        if model not in seen:
            seen.add(model)
            unique_models.append(model)

    if not unique_models:
        raise LlmEndpointError("Unable to parse models from response.")

    return unique_models


def fetch_models(
    provider: str,
    base_url: Optional[str] = None,
    compatibility: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[str]:
    """Fetch available models for a provider endpoint."""

    provider, resolved_base, resolved_compat = resolve_endpoint(provider, base_url, compatibility)
    headers = _build_headers(resolved_compat, api_key)
    url = f"{resolved_base}/models"

    params = None
    if resolved_compat == "google":
        params = {"key": api_key}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
    except requests.RequestException as exc:  # pragma: no cover - network errors mocked in tests
        raise LlmEndpointError(f"Unable to reach endpoint: {exc}")

    if response.status_code >= 400:
        raise LlmEndpointError(
            f"Model list request failed with status {response.status_code}: {response.text}"
        )

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        raise LlmEndpointError(f"Invalid JSON response: {exc}")

    return _parse_models(payload)


def probe_model(
    provider: str,
    base_url: Optional[str],
    compatibility: Optional[str],
    api_key: Optional[str],
    model_name: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> None:
    """Send a minimal generation request to verify the model is usable."""

    _, resolved_base, resolved_compat = resolve_endpoint(provider, base_url, compatibility)
    headers = _build_headers(resolved_compat, api_key)

    if resolved_compat == "openai":
        url = f"{resolved_base}/chat/completions"
        payload = {"model": model_name, "messages": [{"role": "user", "content": "ping"}]}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
    elif resolved_compat == "anthropic":
        url = f"{resolved_base}/messages"
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "ping"}],
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
    else:  # google
        url = f"{resolved_base}/models/{model_name}:generateContent"
        payload = {"contents": [{"parts": [{"text": "ping"}]}]}
        params = {"key": api_key}
        if temperature is not None:
            payload["temperature"] = temperature
        try:
            response = requests.post(url, headers=headers, params=params, json=payload, timeout=10)
        except requests.RequestException as exc:  # pragma: no cover
            raise LlmEndpointError(f"Probe request failed: {exc}")
    if resolved_compat in {"openai", "anthropic"}:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
        except requests.RequestException as exc:  # pragma: no cover
            raise LlmEndpointError(f"Probe request failed: {exc}")

    if response.status_code >= 400:
        raise LlmEndpointError(
            f"Probe request failed with status {response.status_code}: {response.text}"
        )


def validate_endpoint(
    provider: str,
    base_url: Optional[str],
    compatibility: Optional[str],
    api_key: Optional[str],
    model_name: Optional[str],
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Dict[str, object]:
    """Validate an endpoint by listing models and optionally probing one."""

    provider_key, resolved_base, resolved_compat = resolve_endpoint(
        provider, base_url, compatibility
    )
    models: List[str] = []
    try:
        models = fetch_models(provider_key, resolved_base, resolved_compat, api_key)
    except LlmEndpointError:
        # Some endpoints may not support model listing; fall back to probing if a model was provided.
        if not model_name:
            raise
    if model_name:
        if models and model_name not in models:
            raise LlmEndpointError(
                "Selected model was not returned by the provider; double-check the name."
            )
        probe_model(
            provider_key,
            resolved_base,
            resolved_compat,
            api_key,
            model_name,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    return {
        "models": models,
        "resolved_base_url": resolved_base,
        "compatibility": resolved_compat,
    }
