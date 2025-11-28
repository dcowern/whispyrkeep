"""
Unit tests for StreamingResponseParser and streaming endpoints.

Tests cover:
- Incremental chunk parsing
- Edge cases (marker splits, missing prefixes, etc.)
- Full response preservation
- Integration with send_message_stream()
"""

import json
import pytest

from apps.universes.services.worldgen_chat import StreamingResponseParser


class TestStreamingResponseParser:
    """Unit tests for StreamingResponseParser class."""

    def test_parser_normal_response(self):
        """Test standard CHAT: and DATA_JSON: format."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\nThis is ",
            "a test response.\n\n",
            "DATA_JSON:\n{\"step\": \"basics\"}",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert result == "This is a test response.\n\n"
        assert "DATA_JSON" not in result
        assert "CHAT:" not in result
        assert "step" not in result  # JSON should not appear

    def test_parser_multiple_chunks(self):
        """Test that all clean chunks are yielded incrementally."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\nHello ",
            "world! ",
            "How are you?\n\n",
            "DATA_JSON:\n{\"updates\": {}}",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert result == "Hello world! How are you?\n\n"

    def test_parser_marker_split_across_chunks(self):
        """Test marker split between chunks (DATA_J + SON:)."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\nContent here\nDATA_J",
            "SON:\n{\"updates\": {}}",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert "DATA_JSON" not in result
        assert "Content here" in result
        assert "{" not in result

    def test_parser_no_chat_prefix(self):
        """Test response starting directly with content (no CHAT: prefix)."""
        parser = StreamingResponseParser()

        chunks = [
            "This is content\n\n",
            "DATA_JSON:\n{\"step\": \"basics\"}",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert result == "This is content\n\n"
        assert "DATA_JSON" not in result

    def test_parser_no_data_json_section(self):
        """Test response with only CHAT section (no DATA_JSON)."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\nHello world!",
            " This is great!",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert result == "Hello world! This is great!"

    def test_parser_empty_chat_section(self):
        """Test response with empty CHAT section (only DATA_JSON)."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\n\nDATA_JSON:\n{\"step\": \"basics\"}",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        # Should be empty or just whitespace
        assert result.strip() == ""
        assert "DATA_JSON" not in result

    def test_parser_with_newlines_in_chat(self):
        """Test chat content with multiple newlines."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\nParagraph 1\n\nParagraph 2\n\n",
            "Paragraph 3\n\nDATA_JSON:\n{\"updates\": {}}",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result
        assert "Paragraph 3" in result
        assert "DATA_JSON" not in result

    def test_parser_with_markdown_content(self):
        """Test chat content with markdown formatting."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\n# Title\n\n",
            "**Bold text** and *italic text*.\n\n",
            "DATA_JSON:\n{\"updates\": {}}",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert "# Title" in result
        assert "**Bold text**" in result
        assert "*italic text*" in result
        assert "DATA_JSON" not in result

    def test_parser_case_insensitive_chat_prefix(self):
        """Test that CHAT: prefix matching is case insensitive."""
        parser = StreamingResponseParser()

        chunks = [
            "chat:\nThis should work\n\n",
            "DATA_JSON:\n{\"step\": \"basics\"}",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert result == "This should work\n\n"
        assert "DATA_JSON" not in result

    def test_parser_get_full_response(self):
        """Test that get_full_response returns complete buffered response."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\nHello ",
            "world!\n\n",
            "DATA_JSON:\n{\"step\": \"basics\", \"updates\": {}}",
        ]

        # Consume generator to populate buffer
        for chunk in chunks:
            list(parser.add_chunk(chunk))

        full_response = parser.get_full_response()
        # Full response should have everything
        assert "CHAT:" in full_response
        assert "Hello" in full_response
        assert "DATA_JSON:" in full_response
        assert "step" in full_response

    def test_parser_stops_yielding_after_data_json(self):
        """Test that no content is yielded after DATA_JSON: marker."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\nChat content\n\n",
            "DATA_JSON:\n{\"step\": \"basics\"}",
            "\nExtra stuff after JSON",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert result == "Chat content\n\n"
        # Extra stuff after JSON should not appear
        assert "Extra stuff" not in result

    def test_parser_data_json_marker_only_triggers_once(self):
        """Test that finding DATA_JSON: once prevents further yielding."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\nContent\n\n",
            "DATA_JSON:\nFirst JSON",
            "\nMore content that shouldn't appear",
            "\nEven more content",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert result == "Content\n\n"
        assert "More content" not in result
        assert "Even more" not in result

    def test_parser_small_chunks(self):
        """Test parsing with small realistic chunks (not character-by-character)."""
        parser = StreamingResponseParser()

        # Simulate streaming with small but realistic chunks
        chunks = [
            "CHAT:\n",
            "Hi!",
            "\n\n",
            "DATA_JSON:\n{}",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert result == "Hi!\n\n"
        assert "DATA_JSON" not in result

    def test_parser_large_chunk(self):
        """Test parsing with entire response as single chunk."""
        parser = StreamingResponseParser()

        large_chunk = "CHAT:\nLarge content\n\nDATA_JSON:\n{\"step\": \"basics\"}"
        output = list(parser.add_chunk(large_chunk))

        result = "".join(output)
        assert result == "Large content\n\n"
        assert "DATA_JSON" not in result

    def test_parser_with_realistic_json(self):
        """Test with realistic formatted JSON response."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\nGreat! Your world is coming together.\n\n",
            "Here are some suggestions:\n",
            "- Consider the balance between magic and realism\n",
            "- Think about major conflicts or tensions\n\n",
            "DATA_JSON:\n```json\n",
            '{\n  "step": "tone",\n',
            '  "updates": {\n',
            '    "tone": {\n',
            '      "darkness": 60\n',
            "    }\n",
            "  },\n",
            '  "suggested_fields": ["humor", "realism"]\n',
            "}\n",
            "```",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)

        # Check chat content is present
        assert "Great! Your world is coming together." in result
        assert "Consider the balance" in result

        # Check JSON is not in output
        assert "step" not in result
        assert "updates" not in result
        assert "darkness" not in result
        assert "{" not in result
        assert "}" not in result

    def test_parser_state_isolation(self):
        """Test that multiple parser instances don't interfere."""
        parser1 = StreamingResponseParser()
        parser2 = StreamingResponseParser()

        chunks1 = ["CHAT:\nParser1\n\n", "DATA_JSON:\n{}"]
        chunks2 = ["CHAT:\nParser2\n\n", "DATA_JSON:\n{}"]

        output1 = []
        output2 = []

        for chunk in chunks1:
            output1.extend(parser1.add_chunk(chunk))

        for chunk in chunks2:
            output2.extend(parser2.add_chunk(chunk))

        result1 = "".join(output1)
        result2 = "".join(output2)

        assert result1 == "Parser1\n\n"
        assert result2 == "Parser2\n\n"
        assert result1 != result2

    def test_parser_whitespace_preservation(self):
        """Test that whitespace in chat content is preserved."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\nLine with spaces  \n",
            "Another line\n\n",
            "DATA_JSON:\n{}",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        # Whitespace should be preserved (trailing spaces on first line, newlines between lines)
        assert "Line with spaces  " in result
        assert "Another line" in result
        assert "\n" in result  # Newlines preserved

    def test_parser_special_characters(self):
        """Test handling of special characters in chat content."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\nSpecial chars: <, >, &, \", '\n",
            "Emoji test: 🎉 🌟 ✨\n\n",
            "DATA_JSON:\n{}",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert "<" in result
        assert ">" in result
        assert "&" in result
        assert "🎉" in result
        assert "✨" in result

    def test_parser_empty_chunks(self):
        """Test handling of empty chunks."""
        parser = StreamingResponseParser()

        chunks = [
            "CHAT:\nHello",
            "",  # Empty chunk
            " world\n\n",
            "",  # Another empty chunk
            "DATA_JSON:\n{}",
        ]

        output = []
        for chunk in chunks:
            output.extend(parser.add_chunk(chunk))

        result = "".join(output)
        assert result == "Hello world\n\n"
