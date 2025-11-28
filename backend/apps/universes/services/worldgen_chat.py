"""
Worldgen Chat Service - Conversational AI universe building.

Manages chat sessions for AI-assisted universe creation with:
- Persistent conversation history
- Structured data extraction from AI responses
- Step completion tracking
- Streaming support
"""

import hashlib
import json
import logging
import re
from collections.abc import Generator
from datetime import datetime
from typing import Any

from django.db import transaction

from apps.campaigns.services.llm_client import (
    LLMClient,
    LLMClientConfig,
    LLMError,
    Message,
)
from apps.llm_config.models import LlmEndpointConfig
from apps.universes.models import (
    Universe,
    UniverseHardCanonDoc,
    WorldgenSession,
)
from apps.universes.schemas import (
    REQUIRED_STEPS,
    STEP_ORDER,
    STEP_SPECS,
    StepName,
    check_step_completion,
    get_ai_context_for_step,
    get_step_defaults,
)

logger = logging.getLogger(__name__)


# System prompt for the worldgen AI assistant
WORLDGEN_SYSTEM_PROMPT = """You are a creative world-building assistant helping a user create a universe for their tabletop RPG game using SRD 5.2 mechanics.

Your role is to:
1. Have a friendly conversation to understand the user's vision
2. Ask clarifying questions to flesh out details
3. Generate creative suggestions that match their preferences
4. Extract structured data from the conversation

## Output Format

Your response must ALWAYS include two sections:

CHAT:
<Your conversational response to the user>

DATA_JSON:
{
  "step": "<current step being discussed: basics|tone|rules|calendar|lore|homebrew>",
  "updates": {
    "<step_name>": {
      "<field_name>": <value>,
      ...
    }
  },
  "suggested_fields": ["<fields you're asking about>"]
}

## Step Information

{step_context}

## Current Draft Data

```json
{current_data}
```

## Guidelines

- Be creative and enthusiastic about the user's ideas
- Ask one or two questions at a time, don't overwhelm
- When you have enough information for a field, include it in DATA_JSON updates
- Always include DATA_JSON even if no updates (use empty updates: {{}})
- For tone sliders, use values 0-100 (0=low, 100=high)
- For homebrew content, generate valid SRD 5.2 compatible stats
- Keep lore documents concise but flavorful
- Respect the user's creative direction"""


class StreamingResponseParser:
    """Parse LLM streaming response, filtering out DATA_JSON during stream.

    Incrementally processes chunks from the LLM, extracting and yielding only
    the CHAT: section content. The DATA_JSON: section is buffered internally
    and made available after streaming completes for final parsing.

    This prevents the frontend from seeing technical JSON data during streaming,
    eliminating flashing and broken markdown rendering.
    """

    def __init__(self):
        self.full_buffer = ""
        self.yielded_length = 0  # Track how many chars of cleaned content we've yielded
        self.chat_started = False
        self.data_json_started = False
        self.marker_end_pos = -1  # Track where CHAT: marker ends

    def _get_cleaned_chat_content(self) -> str:
        """Extract CHAT content from full_buffer (before DATA_JSON if present), removing prefix.

        Returns:
            Cleaned chat content (without CHAT: prefix)
        """
        # Get content before DATA_JSON: if present
        idx = self.full_buffer.find("DATA_JSON:")
        if idx != -1:
            chat_section = self.full_buffer[:idx]
        else:
            chat_section = self.full_buffer

        # Remove CHAT: prefix
        cleaned = re.sub(r'^\s*CHAT:\s*\n?', '', chat_section, flags=re.IGNORECASE)
        return cleaned

    def add_chunk(self, chunk: str) -> Generator[str, None, None]:
        """Process a chunk and yield cleaned content.

        Args:
            chunk: A chunk of text from the LLM stream

        Yields:
            Cleaned content (only CHAT: section, without prefixes)
        """
        self.full_buffer += chunk

        # If we've already hit DATA_JSON, stop yielding anything
        if self.data_json_started:
            return

        # Check if DATA_JSON marker has appeared
        if "DATA_JSON:" in self.full_buffer:
            self.data_json_started = True
            # Get cleaned chat content and yield anything new
            cleaned = self._get_cleaned_chat_content()
            new_content = cleaned[self.yielded_length:]
            if new_content:
                yield new_content
                self.yielded_length = len(cleaned)
            return

        # If we haven't found and processed CHAT: yet, check for it
        if not self.chat_started:
            if "CHAT:" in self.full_buffer:
                self.chat_started = True
                # Find where CHAT: marker ends and content begins
                match = re.search(r'CHAT:\s*\n?', self.full_buffer, re.IGNORECASE)
                if match:
                    self.marker_end_pos = match.end()
                    # Extract and yield everything after CHAT: marker
                    new_content = self.full_buffer[self.marker_end_pos:]
                    if new_content:
                        yield new_content
                        self.yielded_length = len(new_content)
            # No CHAT: yet, don't yield anything - keep buffering
            return

        # We're in the middle of CHAT content (after we've found and passed the marker)
        if self.chat_started and not self.data_json_started and self.marker_end_pos != -1:
            # Yield only the content after the marker that we haven't yielded yet
            current_pos = self.marker_end_pos + self.yielded_length
            new_chunk_start = max(len(self.full_buffer) - len(chunk), self.marker_end_pos)
            if current_pos >= len(self.full_buffer) - len(chunk):
                # This chunk is new content after the marker
                yield chunk
                self.yielded_length += len(chunk)

    def get_full_response(self) -> str:
        """Get the complete buffered response for final parsing.

        Returns:
            The complete raw response including CHAT: and DATA_JSON: sections
        """
        return self.full_buffer


class WorldgenChatService:
    """
    Service for AI-assisted universe building via chat.

    Usage:
        service = WorldgenChatService(user)
        session = service.create_session()

        # Stream responses
        for chunk in service.send_message_stream(session.id, "I want a dark fantasy world"):
            print(chunk, end="", flush=True)

        # Get updated session state
        session = service.get_session(session.id)
    """

    def __init__(self, user):
        """Initialize the service for a user."""
        self.user = user
        self.llm_config = self._get_llm_config()
        self.user_max_tokens = self._get_user_max_tokens()
        self.user_temperature = self._get_user_temperature()

    def _get_llm_config(self) -> LlmEndpointConfig | None:
        """Get user's active LLM configuration."""
        return LlmEndpointConfig.objects.filter(
            user=self.user,
            is_active=True,
        ).first()

    def has_llm_config(self) -> bool:
        """Check if user has an active LLM configuration."""
        return self.llm_config is not None

    def create_session(self, mode: str = "ai_collab") -> WorldgenSession:
        """
        Create a new worldgen session.

        Args:
            mode: "ai_collab" or "manual"

        Returns:
            New WorldgenSession instance
        """
        # Initialize with default values
        draft_data = get_step_defaults()

        # Initialize step status
        step_status = {}
        for step_name in STEP_ORDER:
            is_complete, field_status = check_step_completion(
                step_name, draft_data.get(step_name.value, {})
            )
            step_status[step_name.value] = {
                "complete": is_complete,
                "fields": field_status,
            }

        session = WorldgenSession.objects.create(
            user=self.user,
            mode=mode,
            draft_data_json=draft_data,
            step_status_json=step_status,
            conversation_json=[],
        )

        # Add initial AI greeting for AI collab mode
        if mode == "ai_collab":
            session.add_message(
                "assistant",
                "Welcome! I'm here to help you create a unique universe for your RPG adventures. "
                "Let's start with the basics - what would you like to call your world? "
                "Do you have any initial vision or inspiration for it?"
            )
            session.save()

        return session

    def get_session(self, session_id: str) -> WorldgenSession | None:
        """Get a session by ID, ensuring it belongs to the user."""
        try:
            return WorldgenSession.objects.get(
                id=session_id,
                user=self.user,
                status=WorldgenSession.Status.DRAFT,
            )
        except WorldgenSession.DoesNotExist:
            return None

    def list_sessions(self) -> list[WorldgenSession]:
        """List user's draft sessions."""
        return list(
            WorldgenSession.objects.filter(
                user=self.user,
                status=WorldgenSession.Status.DRAFT,
            ).order_by("-updated_at")[:20]
        )

    def _build_system_prompt(self, session: WorldgenSession) -> str:
        """Build the system prompt with current context."""
        # Determine current step based on what's incomplete
        current_step = self._get_current_step(session)
        step_context = get_ai_context_for_step(current_step, session.draft_data_json)

        # Avoid str.format interpreting braces in JSON example; do simple placeholder replacement
        prompt = WORLDGEN_SYSTEM_PROMPT
        prompt = prompt.replace("{step_context}", step_context)
        prompt = prompt.replace(
            "{current_data}", json.dumps(session.draft_data_json, indent=2)
        )
        return prompt

    def _get_current_step(self, session: WorldgenSession) -> StepName:
        """Determine the current step based on completion status."""
        for step in STEP_ORDER:
            status = session.step_status_json.get(step.value, {})
            if not status.get("complete", False):
                return step
        # All steps complete, default to homebrew for additional content
        return StepName.HOMEBREW

    def _get_user_max_tokens(self) -> int | None:
        """Read a user-specified max_tokens preference from settings_json if present."""
        settings = getattr(self.user, "settings_json", {}) or {}
        endpoint_pref = settings.get("endpoint_pref")
        if not isinstance(endpoint_pref, dict):
            return None
        max_tokens = endpoint_pref.get("max_tokens")
        if isinstance(max_tokens, int) and max_tokens > 0:
            return max_tokens
        return None

    def _get_user_temperature(self) -> float | None:
        """Read a user-specified temperature preference from settings_json if present."""
        settings = getattr(self.user, "settings_json", {}) or {}
        endpoint_pref = settings.get("endpoint_pref")
        if not isinstance(endpoint_pref, dict):
            return None
        temp = endpoint_pref.get("temperature")
        if isinstance(temp, (int, float)):
            return float(temp)
        return None

    def _build_messages(self, session: WorldgenSession) -> list[Message]:
        """Build message list for LLM from session conversation."""
        messages = [Message(role="system", content=self._build_system_prompt(session))]

        for msg in session.conversation_json:
            if msg["role"] in ("user", "assistant"):
                messages.append(Message(role=msg["role"], content=msg["content"]))

        return messages

    def _parse_ai_response(self, response_text: str) -> tuple[str, dict]:
        """
        Parse AI response into chat text and structured data.

        Returns:
            Tuple of (chat_text, data_json)
        """
        chat_text = ""
        data_json = {"step": "basics", "updates": {}, "suggested_fields": []}

        # Try to extract CHAT: section
        chat_match = re.search(r"CHAT:\s*\n?(.*?)(?=DATA_JSON:|$)", response_text, re.DOTALL)
        if chat_match:
            chat_text = chat_match.group(1).strip()
        else:
            # Fallback: use everything before DATA_JSON
            json_start = response_text.find("DATA_JSON:")
            if json_start > 0:
                chat_text = response_text[:json_start].strip()
            else:
                chat_text = response_text.strip()

        # Try to extract DATA_JSON section
        json_match = re.search(r"DATA_JSON:\s*\n?```json\s*\n?(.*?)\n?```", response_text, re.DOTALL)
        if not json_match:
            json_match = re.search(r"DATA_JSON:\s*\n?({.*?})\s*$", response_text, re.DOTALL)

        if json_match:
            try:
                data_json = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                logger.warning("Failed to parse DATA_JSON from AI response")

        return chat_text, data_json

    def _apply_updates(self, session: WorldgenSession, data_json: dict) -> None:
        """Apply updates from AI response to session draft data."""
        updates = data_json.get("updates", {})

        for step_name, step_updates in updates.items():
            if step_name not in session.draft_data_json:
                session.draft_data_json[step_name] = {}

            for field_name, value in step_updates.items():
                # Validate and apply the update
                session.draft_data_json[step_name][field_name] = value

        # Recalculate step completion status
        for step in STEP_ORDER:
            step_data = session.draft_data_json.get(step.value, {})
            is_complete, field_status = check_step_completion(step, step_data)
            session.step_status_json[step.value] = {
                "complete": is_complete,
                "fields": field_status,
            }

    def send_message(self, session_id: str, user_message: str) -> dict:
        """
        Send a message and get a complete response (non-streaming).

        Args:
            session_id: The session ID
            user_message: The user's message

        Returns:
            Dict with 'response', 'step_status', 'draft_data'
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        if not self.llm_config:
            raise LLMError("No LLM configuration found")

        # Add user message to history
        session.add_message("user", user_message)

        # Build messages and call LLM
        messages = self._build_messages(session)

        config = LLMClientConfig.from_endpoint_config(self.llm_config)
        with LLMClient(config) as client:
            response = client.chat(
                messages,
                temperature=self.user_temperature,
                max_tokens=self.user_max_tokens,
            )

        # Parse response
        chat_text, data_json = self._parse_ai_response(response.content)

        # Apply updates
        self._apply_updates(session, data_json)

        # Add assistant message
        session.add_message("assistant", chat_text)
        session.save()

        return {
            "response": chat_text,
            "step_status": session.step_status_json,
            "draft_data": session.draft_data_json,
            "current_step": self._get_current_step(session).value,
        }

    def send_message_stream(
        self, session_id: str, user_message: str
    ) -> Generator[dict, None, None]:
        """
        Send a message and stream the response.

        Uses StreamingResponseParser to filter out DATA_JSON content during
        streaming, ensuring only clean CHAT content is sent to the frontend.

        Args:
            session_id: The session ID
            user_message: The user's message

        Yields:
            Dict with 'type' and 'content':
            - {"type": "chunk", "content": "..."} for text chunks (CHAT only)
            - {"type": "complete", "step_status": {...}, "draft_data": {...}}
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        if not self.llm_config:
            raise LLMError("No LLM configuration found")

        # Add user message to history
        session.add_message("user", user_message)
        session.save()

        # Build messages and call LLM with streaming
        messages = self._build_messages(session)

        config = LLMClientConfig.from_endpoint_config(self.llm_config)

        # Create parser for incremental filtering of DATA_JSON
        parser = StreamingResponseParser()

        with LLMClient(config) as client:
            for chunk in client.chat_stream(
                messages,
                temperature=self.user_temperature,
                max_tokens=self.user_max_tokens,
            ):
                # Process chunk through parser, only yield clean content
                for clean_chunk in parser.add_chunk(chunk):
                    yield {"type": "chunk", "content": clean_chunk}

        # Get complete response for final parsing
        full_response = parser.get_full_response()

        # Parse complete response
        chat_text, data_json = self._parse_ai_response(full_response)

        # Apply updates
        self._apply_updates(session, data_json)

        # Add assistant message (only the chat part)
        session.add_message("assistant", chat_text)
        session.save()

        # Yield final completion event
        yield {
            "type": "complete",
            "step_status": session.step_status_json,
            "draft_data": session.draft_data_json,
            "current_step": self._get_current_step(session).value,
        }

    def update_draft_data(
        self, session_id: str, step_name: str, data: dict
    ) -> WorldgenSession:
        """
        Update draft data directly (for manual mode).

        Args:
            session_id: The session ID
            step_name: The step to update
            data: The data to set

        Returns:
            Updated session
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        # Update the step data
        if step_name not in session.draft_data_json:
            session.draft_data_json[step_name] = {}
        session.draft_data_json[step_name].update(data)

        # Recalculate step completion
        try:
            step = StepName(step_name)
            is_complete, field_status = check_step_completion(
                step, session.draft_data_json[step_name]
            )
            session.step_status_json[step_name] = {
                "complete": is_complete,
                "fields": field_status,
            }
        except ValueError:
            pass

        session.save()
        return session

    def switch_mode(self, session_id: str, new_mode: str) -> WorldgenSession:
        """
        Switch session between AI collab and manual mode.

        Args:
            session_id: The session ID
            new_mode: "ai_collab" or "manual"

        Returns:
            Updated session
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        session.mode = new_mode
        session.save()
        return session

    def finalize_session(self, session_id: str) -> Universe:
        """
        Create a Universe from the session draft data.

        Args:
            session_id: The session ID

        Returns:
            Created Universe

        Raises:
            ValueError: If required data is missing
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        # Check required steps
        for step in REQUIRED_STEPS:
            status = session.step_status_json.get(step.value, {})
            if not status.get("complete", False):
                raise ValueError(f"Required step '{step.value}' is not complete")

        draft = session.draft_data_json

        with transaction.atomic():
            # Build universe data from draft
            basics = draft.get("basics", {})
            tone = draft.get("tone", {})
            rules = draft.get("rules", {})
            calendar = draft.get("calendar", {})

            # Create tone profile
            tone_profile = {
                "grimdark_cozy": tone.get("darkness", 50) / 100,
                "comedy_serious": tone.get("humor", 50) / 100,
                "low_high_magic": tone.get("magic_level", 50) / 100,
                "realism": tone.get("realism", 50) / 100,
                "themes": tone.get("themes", []),
            }

            # Create rules profile
            rules_profile = {
                "permadeath": rules.get("permadeath", False),
                "critical_fumbles": rules.get("critical_fumbles", False),
                "encumbrance": "variant" if rules.get("encumbrance", False) else "ignored",
                "rules_strictness": rules.get("rules_strictness", "standard"),
            }

            # Create calendar profile
            calendar_profile = calendar if calendar else {
                "calendar_type": "standard",
                "months_per_year": 12,
                "days_per_month": [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
            }

            # Create universe
            universe = Universe.objects.create(
                user=self.user,
                name=basics.get("name", "Untitled Universe"),
                description=basics.get("description", ""),
                tone_profile_json=tone_profile,
                rules_profile_json=rules_profile,
                calendar_profile_json=calendar_profile,
                current_universe_time={"year": 1, "month": 1, "day": 1},
            )

            # Create lore documents
            lore = draft.get("lore", {})
            canon_docs = lore.get("canon_docs", [])
            for doc in canon_docs:
                if doc.get("title") and doc.get("content"):
                    checksum = hashlib.sha256(doc["content"].encode()).hexdigest()
                    UniverseHardCanonDoc.objects.create(
                        universe=universe,
                        source_type="worldgen",
                        title=doc["title"],
                        raw_text=doc["content"],
                        checksum=checksum,
                        never_compact=True,
                    )

            # Create world overview if present
            if lore.get("world_overview"):
                overview_text = lore["world_overview"]
                checksum = hashlib.sha256(overview_text.encode()).hexdigest()
                UniverseHardCanonDoc.objects.create(
                    universe=universe,
                    source_type="worldgen",
                    title=f"{basics.get('name', 'World')} Overview",
                    raw_text=overview_text,
                    checksum=checksum,
                    never_compact=True,
                )

            # TODO: Create homebrew content when homebrew models are ready
            # homebrew = draft.get("homebrew", {})

            # Update session
            session.status = WorldgenSession.Status.COMPLETED
            session.resulting_universe = universe
            session.save()

            return universe

    def abandon_session(self, session_id: str) -> None:
        """Mark a session as abandoned."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        session.status = WorldgenSession.Status.ABANDONED
        session.save()

    def get_ai_assist(
        self,
        session_id: str,
        step_name: str,
        field_name: str | None = None,
        message: str | None = None,
    ) -> Generator[dict, None, None]:
        """
        Get AI assistance for a specific step/field (for manual mode).

        Args:
            session_id: The session ID
            step_name: The step to get help with
            field_name: Optional specific field to focus on
            message: Optional user message/question

        Yields:
            Same format as send_message_stream
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        if not self.llm_config:
            raise LLMError("No LLM configuration found")

        # Build a focused question for the AI
        step_spec = STEP_SPECS.get(StepName(step_name))
        if not step_spec:
            raise ValueError(f"Unknown step: {step_name}")

        # Use user's message if provided, otherwise generate a default question
        if message and message.strip():
            # Add context about the current step
            question = f"[Currently working on: {step_spec.display_name}] {message}"
        elif field_name:
            field = step_spec.get_field(field_name)
            if field:
                question = f"Help me with the {field.name} for my universe. {field.description}"
            else:
                question = f"Help me with {field_name} for the {step_name} step."
        else:
            question = f"Help me fill out the {step_spec.display_name} section for my universe."

        # Use the streaming message method
        yield from self.send_message_stream(session_id, question)
