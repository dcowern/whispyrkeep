"""
LLM Endpoint Configuration model.

Based on SYSTEM_DESIGN.md section 5.1 LlmEndpointConfig entity.
Stores encrypted API keys for user's LLM providers.
"""

import uuid

from django.conf import settings
from django.db import models


class LlmEndpointConfig(models.Model):
    """
    User's LLM endpoint configuration with encrypted API key.

    Fields from spec:
    - id
    - user_id fk
    - provider_name (openai, azure-openai, local, etc.)
    - base_url
    - api_key_encrypted (AES-GCM with server KMS)
    - default_model
    - created_at, updated_at
    - is_active
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="llm_configs",
    )
    provider_name = models.CharField(
        max_length=50,
        choices=[
            ("openai", "OpenAI"),
            ("azure-openai", "Azure OpenAI"),
            ("anthropic", "Anthropic"),
            ("local", "Local/Custom"),
        ],
    )
    base_url = models.URLField(blank=True)
    api_key_encrypted = models.BinaryField(
        help_text="AES-GCM encrypted API key"
    )
    default_model = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "LLM Endpoint Config"
        verbose_name_plural = "LLM Endpoint Configs"

    def __str__(self):
        return f"{self.provider_name} - {self.default_model}"
