"""
Lore Chat Service - AI-assisted lore document development.

Manages chat sessions for creating lore documents for existing universes.
Uses the existing LoreService for finalizing documents to UniverseHardCanonDoc.
"""

import json
import logging
import re
from typing import Any

from django.db import transaction

from apps.campaigns.services.llm_client import (
    LLMClient,
    LLMClientConfig,
    LLMError,
    Message,
)
from apps.llm_config.models import LlmEndpointConfig
from apps.lore.services.lore_service import LoreService
from apps.universes.models import (
    LoreSession,
    Universe,
    UniverseHardCanonDoc,
)

logger = logging.getLogger(__name__)


# System prompt for lore development
LORE_SYSTEM_PROMPT = """You are a creative lore development assistant helping a user create detailed canon documents for their fantasy universe.

## Universe: {universe_name}

{universe_description}

## Existing Canon Documents
{existing_docs}

## Current Document Being Developed
Title: {current_title}
Content so far:
{current_content}
Tags: {current_tags}

## Your Role

Help the user develop rich, detailed lore documents through conversation:
1. Ask clarifying questions to flesh out details
2. Suggest connections to existing lore
3. Flag potential contradictions with existing canon
4. Extract information from the conversation into the document

## Output Format

Your response must ALWAYS include two sections:

CHAT:
<Your conversational response to the user>

DOCUMENT_UPDATE:
{{
  "title": "Updated title if changed or null",
  "content_additions": "New content to append to the document (or null if none)",
  "tags": ["new", "tags", "to", "add"]
}}

If no document updates are needed, use null values:
DOCUMENT_UPDATE:
{{
  "title": null,
  "content_additions": null,
  "tags": []
}}

## Guidelines

- Be creative and enthusiastic about the user's ideas
- Ask one or two questions at a time to flesh out details
- For content_additions, write detailed prose that can be appended to the document
- Don't repeat content that's already in the document
- Maintain consistency with existing universe lore
- Suggest specific names, places, events, and relationships
- Keep the established tone of the universe"""


class LoreChatService:
    """
    Service for AI-assisted lore document development via chat.

    Usage:
        service = LoreChatService(user)
        session = service.create_session(universe_id)
        result = service.send_message(session.id, "I want to write about the thieves guild")
    """

    def __init__(self, user):
        """Initialize the service for a user."""
        self.user = user
        self.llm_config = self._get_llm_config()
        self.lore_service = LoreService()

    def _get_llm_config(self) -> LlmEndpointConfig | None:
        """Get user's active LLM configuration."""
        return LlmEndpointConfig.objects.filter(
            user=self.user,
            is_active=True,
        ).first()

    def has_llm_config(self) -> bool:
        """Check if user has an active LLM configuration."""
        return self.llm_config is not None

    def _get_user_preferences(self) -> tuple[int | None, float | None]:
        """Get user's max_tokens and temperature preferences."""
        settings = getattr(self.user, "settings_json", {}) or {}
        endpoint_pref = settings.get("endpoint_pref")
        if not isinstance(endpoint_pref, dict):
            return None, None

        max_tokens = endpoint_pref.get("max_tokens")
        if not (isinstance(max_tokens, int) and max_tokens > 0):
            max_tokens = None

        temp = endpoint_pref.get("temperature")
        if isinstance(temp, (int, float)):
            temp = float(temp)
        else:
            temp = None

        return max_tokens, temp

    def create_session(self, universe_id: str) -> LoreSession:
        """
        Create a new lore development session for a universe.

        Args:
            universe_id: The universe to develop lore for

        Returns:
            New LoreSession instance
        """
        try:
            universe = Universe.objects.get(id=universe_id, user=self.user)
        except Universe.DoesNotExist:
            raise ValueError("Universe not found or you don't have access")

        session = LoreSession.objects.create(
            user=self.user,
            universe=universe,
            current_document_json={
                "title": "",
                "content": "",
                "tags": [],
            },
            conversation_json=[],
            draft_documents_json=[],
        )

        # Add initial AI greeting
        session.add_message(
            "assistant",
            f"Welcome! I'm here to help you develop lore documents for **{universe.name}**. "
            "What would you like to write about? You could create documents about:\n\n"
            "- **Geography**: Regions, cities, landmarks, climate\n"
            "- **History**: Major events, wars, golden ages, catastrophes\n"
            "- **Factions**: Guilds, kingdoms, religious orders, secret societies\n"
            "- **Cultures**: Peoples, traditions, languages, customs\n"
            "- **Notable Figures**: Heroes, villains, rulers, legends\n"
            "- **Magic & Technology**: Systems, artifacts, limitations\n\n"
            "What topic interests you?"
        )
        session.save()

        return session

    def get_session(self, session_id: str, universe_id: str) -> LoreSession | None:
        """Get a session by ID, ensuring it belongs to the user and universe."""
        try:
            return LoreSession.objects.get(
                id=session_id,
                universe_id=universe_id,
                user=self.user,
                status=LoreSession.Status.ACTIVE,
            )
        except LoreSession.DoesNotExist:
            return None

    def list_sessions(self, universe_id: str) -> list[LoreSession]:
        """List user's active lore sessions for a universe."""
        return list(
            LoreSession.objects.filter(
                user=self.user,
                universe_id=universe_id,
                status=LoreSession.Status.ACTIVE,
            ).order_by("-updated_at")[:20]
        )

    def _get_existing_docs_summary(self, universe: Universe) -> str:
        """Get a summary of existing canon documents for context."""
        docs = UniverseHardCanonDoc.objects.filter(universe=universe).order_by("-created_at")[:10]
        if not docs:
            return "(No existing canon documents)"

        summaries = []
        for doc in docs:
            # Truncate long content
            content_preview = doc.raw_text[:200] + "..." if len(doc.raw_text) > 200 else doc.raw_text
            summaries.append(f"**{doc.title}**\n{content_preview}")

        return "\n\n".join(summaries)

    def _build_system_prompt(self, session: LoreSession) -> str:
        """Build the system prompt with current context."""
        universe = session.universe
        current_doc = session.current_document_json or {}

        prompt = LORE_SYSTEM_PROMPT.replace("{universe_name}", universe.name)
        prompt = prompt.replace("{universe_description}", universe.description or "(No description)")
        prompt = prompt.replace("{existing_docs}", self._get_existing_docs_summary(universe))
        prompt = prompt.replace("{current_title}", current_doc.get("title", "(No title yet)"))
        prompt = prompt.replace("{current_content}", current_doc.get("content", "(No content yet)"))
        prompt = prompt.replace("{current_tags}", ", ".join(current_doc.get("tags", [])) or "(No tags)")

        return prompt

    def _build_messages(self, session: LoreSession) -> list[Message]:
        """Build message list for LLM from session conversation."""
        messages = [Message(role="system", content=self._build_system_prompt(session))]

        for msg in session.conversation_json:
            if msg["role"] in ("user", "assistant"):
                messages.append(Message(role=msg["role"], content=msg["content"]))

        return messages

    def _parse_ai_response(self, response_text: str) -> tuple[str, dict]:
        """
        Parse AI response into chat text and document update.

        Returns:
            Tuple of (chat_text, document_update)
        """
        chat_text = ""
        doc_update = {"title": None, "content_additions": None, "tags": []}

        # Try to extract CHAT: section
        chat_match = re.search(r"CHAT:\s*\n?(.*?)(?=DOCUMENT_UPDATE:|$)", response_text, re.DOTALL)
        if chat_match:
            chat_text = chat_match.group(1).strip()
        else:
            # Fallback: use everything before DOCUMENT_UPDATE
            json_start = response_text.find("DOCUMENT_UPDATE:")
            if json_start > 0:
                chat_text = response_text[:json_start].strip()
            else:
                chat_text = response_text.strip()

        # Try to extract DOCUMENT_UPDATE section
        json_match = re.search(r"DOCUMENT_UPDATE:\s*\n?```json\s*\n?(.*?)\n?```", response_text, re.DOTALL)
        if not json_match:
            json_match = re.search(r"DOCUMENT_UPDATE:\s*\n?({.*?})\s*$", response_text, re.DOTALL)

        if json_match:
            try:
                doc_update = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                logger.warning("Failed to parse DOCUMENT_UPDATE from AI response")

        return chat_text, doc_update

    def _apply_document_update(self, session: LoreSession, doc_update: dict) -> None:
        """Apply document updates from AI response to session."""
        current = session.current_document_json or {
            "title": "",
            "content": "",
            "tags": [],
        }

        # Update title if provided
        if doc_update.get("title"):
            current["title"] = doc_update["title"]

        # Append content additions
        content_additions = doc_update.get("content_additions")
        if content_additions and content_additions.strip():
            existing_content = current.get("content", "")
            if existing_content:
                # Check if content is already present (AI repeated it)
                if content_additions.strip() not in existing_content:
                    current["content"] = f"{existing_content.rstrip()}\n\n{content_additions.strip()}"
            else:
                current["content"] = content_additions.strip()

        # Add new tags (deduplicate)
        new_tags = doc_update.get("tags", [])
        if new_tags:
            existing_tags = set(current.get("tags", []))
            for tag in new_tags:
                if tag and tag.strip():
                    existing_tags.add(tag.strip().lower())
            current["tags"] = sorted(list(existing_tags))

        session.current_document_json = current

    def send_message(self, session_id: str, universe_id: str, user_message: str) -> dict:
        """
        Send a message and get a response.

        Args:
            session_id: The session ID
            universe_id: The universe ID
            user_message: The user's message

        Returns:
            Dict with 'response', 'current_document', 'draft_documents'
        """
        session = self.get_session(session_id, universe_id)
        if not session:
            raise ValueError("Session not found")

        if not self.llm_config:
            raise LLMError("No LLM configuration found. Please configure an API key in Settings.")

        # Add user message to history
        session.add_message("user", user_message)

        # Build messages and call LLM
        messages = self._build_messages(session)
        max_tokens, temperature = self._get_user_preferences()

        config = LLMClientConfig.from_endpoint_config(self.llm_config)
        with LLMClient(config) as client:
            response = client.chat(
                messages,
                temperature=temperature or 0.8,  # Slightly creative for lore
                max_tokens=max_tokens or 2048,
            )

        # Parse response
        chat_text, doc_update = self._parse_ai_response(response.content)

        # Apply document updates
        self._apply_document_update(session, doc_update)

        # Add assistant message
        session.add_message("assistant", chat_text)
        session.save()

        return {
            "response": chat_text,
            "current_document": session.current_document_json,
            "draft_documents": session.draft_documents_json,
        }

    def save_current_document(self, session_id: str, universe_id: str) -> dict:
        """
        Save the current document to the draft documents list.

        Returns:
            Dict with updated session state
        """
        session = self.get_session(session_id, universe_id)
        if not session:
            raise ValueError("Session not found")

        current_doc = session.current_document_json
        if not current_doc or not current_doc.get("title"):
            raise ValueError("Cannot save document without a title")
        if not current_doc.get("content"):
            raise ValueError("Cannot save empty document")

        # Save to drafts
        session.save_current_document()

        # Add system message to conversation
        session.add_message(
            "assistant",
            f"I've saved **{current_doc.get('title')}** to your drafts. "
            "You can start a new document or finalize your session to create the canon documents. "
            "What would you like to work on next?"
        )
        session.save()

        return {
            "current_document": session.current_document_json,
            "draft_documents": session.draft_documents_json,
        }

    def start_new_document(self, session_id: str, universe_id: str, title: str = "") -> dict:
        """
        Start working on a new document.

        If there's a current document with content, saves it first.

        Returns:
            Dict with updated session state
        """
        session = self.get_session(session_id, universe_id)
        if not session:
            raise ValueError("Session not found")

        # Start new document (this handles saving current if needed)
        session.start_new_document(title)

        # Add message to conversation
        if title:
            session.add_message(
                "assistant",
                f"Let's start a new document: **{title}**. Tell me what you'd like to include."
            )
        else:
            session.add_message(
                "assistant",
                "Starting a new document. What topic would you like to explore?"
            )
        session.save()

        return {
            "current_document": session.current_document_json,
            "draft_documents": session.draft_documents_json,
        }

    def update_current_document(
        self, session_id: str, universe_id: str, updates: dict
    ) -> dict:
        """
        Manually update the current document.

        Args:
            updates: Dict with optional title, content, tags

        Returns:
            Dict with updated session state
        """
        session = self.get_session(session_id, universe_id)
        if not session:
            raise ValueError("Session not found")

        current = session.current_document_json or {
            "title": "",
            "content": "",
            "tags": [],
        }

        if "title" in updates:
            current["title"] = updates["title"]
        if "content" in updates:
            current["content"] = updates["content"]
        if "tags" in updates:
            current["tags"] = updates["tags"]

        session.current_document_json = current
        session.save()

        return {
            "current_document": session.current_document_json,
            "draft_documents": session.draft_documents_json,
        }

    def finalize_session(
        self, session_id: str, universe_id: str
    ) -> list[UniverseHardCanonDoc]:
        """
        Finalize all draft documents as UniverseHardCanonDocs.

        Uses LoreService.ingest_hard_canon() for each document,
        which automatically handles chunking and vector embeddings.

        Returns:
            List of created UniverseHardCanonDoc instances
        """
        session = self.get_session(session_id, universe_id)
        if not session:
            raise ValueError("Session not found")

        # Save current document if it has content
        if session.current_document_json and session.current_document_json.get("content"):
            if not session.current_document_json.get("title"):
                session.current_document_json["title"] = "Untitled Document"
            session.save_current_document()
            session.save()

        drafts = session.draft_documents_json
        if not drafts:
            raise ValueError("No documents to finalize")

        created_docs = []

        with transaction.atomic():
            for draft in drafts:
                title = draft.get("title", "Untitled")
                content = draft.get("content", "")
                tags = draft.get("tags", [])

                if not content.strip():
                    continue

                # Use LoreService to ingest (handles chunking + vectors)
                result = self.lore_service.ingest_hard_canon(
                    universe=session.universe,
                    title=title,
                    raw_text=content,
                    source_type="user_edit",  # User created via chat
                    tags=tags,
                    never_compact=True,
                )

                if result.success and result.document_id:
                    doc = UniverseHardCanonDoc.objects.get(id=result.document_id)
                    created_docs.append(doc)

            # Mark session as completed
            session.status = LoreSession.Status.COMPLETED
            session.save()

        return created_docs

    def abandon_session(self, session_id: str, universe_id: str) -> None:
        """Mark a session as abandoned."""
        session = self.get_session(session_id, universe_id)
        if not session:
            raise ValueError("Session not found")

        session.status = LoreSession.Status.ABANDONED
        session.save()
