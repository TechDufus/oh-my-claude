"""Tests for hook_utils.py."""

import io
import json
import re
from unittest.mock import patch

import pytest

import hook_utils
from hook_utils import (
    RegexCache,
    WhichCache,
    get_nested,
    get_session_context,
    is_agent_session,
    is_teams_enabled,
    output_block,
    output_context,
    output_permission,
    output_stop_block,
    parse_hook_input,
)


class TestReadStdinSafe:
    """Tests for safe stdin reading behavior."""

    def test_dispatches_to_unix_reader_when_sigalrm_available(self, monkeypatch):
        """SIGALRM-capable platforms should use the Unix implementation."""
        monkeypatch.setattr(hook_utils, "_HAS_SIGALRM", True)

        with (
            patch.object(hook_utils, "_read_stdin_unix", return_value="unix") as unix_reader,
            patch.object(hook_utils, "_read_stdin_windows", return_value="windows") as windows_reader,
        ):
            result = hook_utils.read_stdin_safe(timeout=3, max_bytes=12)

        assert result == "unix"
        unix_reader.assert_called_once_with(3, 12)
        windows_reader.assert_not_called()

    def test_dispatches_to_windows_reader_without_sigalrm(self, monkeypatch):
        """Platforms without SIGALRM should use the Windows-safe implementation."""
        monkeypatch.setattr(hook_utils, "_HAS_SIGALRM", False)

        with (
            patch.object(hook_utils, "_read_stdin_unix", return_value="unix") as unix_reader,
            patch.object(hook_utils, "_read_stdin_windows", return_value="windows") as windows_reader,
        ):
            result = hook_utils.read_stdin_safe(timeout=3, max_bytes=12)

        assert result == "windows"
        windows_reader.assert_called_once_with(3, 12)
        unix_reader.assert_not_called()

    def test_windows_reader_reads_stdin(self, monkeypatch):
        """Windows reader should return stdin content read by the background thread."""
        monkeypatch.setattr(hook_utils.sys, "stdin", io.StringIO("hook input"))

        result = hook_utils._read_stdin_windows(timeout=1, max_bytes=100)

        assert result == "hook input"

    def test_windows_reader_docstring_matches_implementation(self):
        """Windows reader docs should not claim an unused msvcrt implementation."""
        docstring = hook_utils._read_stdin_windows.__doc__

        assert docstring is not None
        assert "background thread" in docstring
        assert "msvcrt" not in docstring

    def test_windows_reader_raises_for_oversized_stdin(self, monkeypatch):
        """Windows reader should enforce max_bytes."""
        monkeypatch.setattr(hook_utils.sys, "stdin", io.StringIO("too large"))

        with pytest.raises(hook_utils.StdinSizeError, match="stdin exceeds 3 bytes"):
            hook_utils._read_stdin_windows(timeout=1, max_bytes=3)

    def test_windows_reader_returns_empty_on_timeout(self):
        """Windows reader should degrade gracefully when the read thread times out."""
        created_threads = []

        class BlockingThread:
            def __init__(self, target, daemon):
                self.target = target
                self.daemon = daemon
                self.join_timeout = None
                created_threads.append(self)

            def start(self):
                return None

            def join(self, timeout=None):
                self.join_timeout = timeout

        with patch("threading.Thread", BlockingThread):
            result = hook_utils._read_stdin_windows(timeout=2, max_bytes=100)

        assert result == ""
        assert created_threads[0].daemon is True
        assert created_threads[0].join_timeout == 2

    def test_unix_reader_returns_empty_when_select_times_out(self):
        """Unix reader should return empty string when stdin is not readable in time."""
        with patch.object(hook_utils.select, "select", return_value=([], [], [])):
            result = hook_utils._read_stdin_unix(timeout=1, max_bytes=100)

        assert result == ""


class TestParseHookInput:
    """Tests for parse_hook_input function."""

    def test_valid_json_dict(self):
        """Valid JSON dict should be parsed correctly."""
        raw = '{"key": "value", "number": 42}'
        result = parse_hook_input(raw)
        assert result == {"key": "value", "number": 42}

    def test_nested_json(self):
        """Nested JSON should be parsed correctly."""
        raw = '{"outer": {"inner": "value"}}'
        result = parse_hook_input(raw)
        assert result == {"outer": {"inner": "value"}}

    def test_empty_string(self):
        """Empty string should return empty dict."""
        assert parse_hook_input("") == {}

    def test_whitespace_only(self):
        """Whitespace-only string should return empty dict."""
        assert parse_hook_input("   \n\t  ") == {}

    def test_none_input(self):
        """None input should return empty dict."""
        # parse_hook_input expects str, but should handle falsy values
        assert parse_hook_input("") == {}

    def test_invalid_json(self):
        """Invalid JSON should return empty dict."""
        assert parse_hook_input("{not valid json}") == {}
        assert parse_hook_input("{'single': 'quotes'}") == {}

    def test_json_array_returns_empty(self):
        """JSON array (not dict) should return empty dict."""
        assert parse_hook_input("[1, 2, 3]") == {}
        assert parse_hook_input('["a", "b"]') == {}

    def test_json_string_returns_empty(self):
        """JSON string (not dict) should return empty dict."""
        assert parse_hook_input('"just a string"') == {}

    def test_json_number_returns_empty(self):
        """JSON number (not dict) should return empty dict."""
        assert parse_hook_input("42") == {}

    def test_json_null_returns_empty(self):
        """JSON null (not dict) should return empty dict."""
        assert parse_hook_input("null") == {}

    def test_unicode_content(self):
        """Unicode content should be handled correctly."""
        raw = '{"emoji": "🎉", "chinese": "中文"}'
        result = parse_hook_input(raw)
        assert result == {"emoji": "🎉", "chinese": "中文"}


class TestGetNested:
    """Tests for get_nested function."""

    def test_single_key(self):
        """Single key access should work."""
        data = {"key": "value"}
        assert get_nested(data, "key") == "value"

    def test_nested_keys(self):
        """Nested key access should work."""
        data = {"a": {"b": {"c": "deep"}}}
        assert get_nested(data, "a", "b", "c") == "deep"

    def test_missing_key_returns_default(self):
        """Missing key should return default."""
        data = {"a": 1}
        assert get_nested(data, "b") is None
        assert get_nested(data, "b", default="missing") == "missing"

    def test_missing_intermediate_key(self):
        """Missing intermediate key should return default."""
        data = {"a": {"b": 1}}
        assert get_nested(data, "a", "x", "y") is None
        assert get_nested(data, "a", "x", "y", default="nope") == "nope"

    def test_non_dict_intermediate(self):
        """Non-dict intermediate value should return default."""
        data = {"a": "string_not_dict"}
        assert get_nested(data, "a", "b") is None

    def test_none_value_at_path(self):
        """None value at path should return default."""
        data = {"a": {"b": None}}
        assert get_nested(data, "a", "b") is None
        assert get_nested(data, "a", "b", default="fallback") == "fallback"

    def test_empty_dict(self):
        """Empty dict should return default for any key."""
        assert get_nested({}, "any") is None

    def test_zero_keys(self):
        """Zero keys should return the data itself."""
        data = {"a": 1}
        assert get_nested(data) == {"a": 1}

    def test_list_value(self):
        """List value should be returned correctly."""
        data = {"items": [1, 2, 3]}
        assert get_nested(data, "items") == [1, 2, 3]


class TestRegexCache:
    """Tests for RegexCache class."""

    def test_add_and_match(self):
        """Adding pattern and matching should work."""
        cache = RegexCache()
        cache.add("test", r"\d+")
        match = cache.match("test", "abc123def")
        assert match is not None
        assert match.group() == "123"

    def test_case_insensitive_flag(self):
        """Case insensitive flag should be respected."""
        cache = RegexCache()
        cache.add("word", r"hello", re.IGNORECASE)
        assert cache.match("word", "HELLO") is not None
        assert cache.match("word", "HeLLo") is not None

    def test_no_match_returns_none(self):
        """No match should return None."""
        cache = RegexCache()
        cache.add("digits", r"\d+")
        assert cache.match("digits", "no numbers here") is None

    def test_missing_pattern_raises_keyerror(self):
        """Missing pattern name should raise KeyError."""
        cache = RegexCache()
        with pytest.raises(KeyError, match="pattern 'unknown' not in cache"):
            cache.match("unknown", "text")

    def test_has_method(self):
        """has() should correctly report pattern existence."""
        cache = RegexCache()
        assert cache.has("test") is False
        cache.add("test", r".")
        assert cache.has("test") is True

    def test_overwrite_pattern(self):
        """Adding same name should overwrite pattern."""
        cache = RegexCache()
        cache.add("test", r"first")
        cache.add("test", r"second")
        assert cache.match("test", "first") is None
        assert cache.match("test", "second") is not None

    def test_complex_pattern(self):
        """Complex regex patterns should work."""
        cache = RegexCache()
        # Pattern for ultrawork triggers
        cache.add(
            "ultrawork",
            r"\b(ultrawork|ulw|just\s+work|ship\s+it)\b",
            re.IGNORECASE,
        )
        assert cache.match("ultrawork", "let's ulw this") is not None
        assert cache.match("ultrawork", "ship it now") is not None
        assert cache.match("ultrawork", "just work please") is not None
        assert cache.match("ultrawork", "ultraworking") is None  # word boundary


class TestWhichCache:
    """Tests for WhichCache class."""

    def test_which_caches_result(self):
        """which() should cache the result."""
        cache = WhichCache()
        with patch("shutil.which", return_value="/usr/bin/python") as mock_which:
            # First call
            result1 = cache.which("python")
            # Second call
            result2 = cache.which("python")

            assert result1 == "/usr/bin/python"
            assert result2 == "/usr/bin/python"
            # Should only call shutil.which once
            mock_which.assert_called_once_with("python")

    def test_which_not_found(self):
        """which() should cache None for not found commands."""
        cache = WhichCache()
        with patch("shutil.which", return_value=None) as mock_which:
            result = cache.which("nonexistent_cmd_xyz")
            assert result is None
            # Second call should use cache
            cache.which("nonexistent_cmd_xyz")
            mock_which.assert_called_once()

    def test_available_true(self):
        """available() should return True for found commands."""
        cache = WhichCache()
        with patch("shutil.which", return_value="/usr/bin/git"):
            assert cache.available("git") is True

    def test_available_false(self):
        """available() should return False for not found commands."""
        cache = WhichCache()
        with patch("shutil.which", return_value=None):
            assert cache.available("nonexistent") is False

    def test_clear(self):
        """clear() should empty the cache."""
        cache = WhichCache()
        with patch("shutil.which", return_value="/bin/ls") as mock_which:
            cache.which("ls")
            cache.clear()
            cache.which("ls")
            # Should call twice after clear
            assert mock_which.call_count == 2


class TestOutputContext:
    """Tests for output_context function."""

    def test_output_format(self, capsys):
        """output_context should produce correct JSON format."""
        output_context("TestEvent", "Test context message")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result == {
            "hookSpecificOutput": {
                "hookEventName": "TestEvent",
                "additionalContext": "Test context message",
            }
        }

    def test_multiline_context(self, capsys):
        """Multiline context should be preserved."""
        context = "Line 1\nLine 2\nLine 3"
        output_context("Test", context)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["hookSpecificOutput"]["additionalContext"] == context


class TestOutputBlock:
    """Tests for output_block function."""

    def test_output_format(self, capsys):
        """output_block should produce correct JSON format."""
        output_block("Stop", "Task incomplete", "Please complete todos first")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result == {
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "blocked": True,
                "reason": "Task incomplete",
                "additionalContext": "Please complete todos first",
            }
        }

    def test_blocked_is_true(self, capsys):
        """blocked field should always be True."""
        output_block("Stop", "reason", "context")
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["hookSpecificOutput"]["blocked"] is True


class TestOutputStopBlock:
    """Tests for output_stop_block function."""

    def test_output_format(self, capsys):
        """output_stop_block should produce correct JSON format."""
        output_stop_block("Task incomplete", "Please complete todos first")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result == {
            "decision": "block",
            "reason": "Task incomplete\n\nPlease complete todos first",
        }

    def test_without_context(self, capsys):
        """output_stop_block should work without context."""
        output_stop_block("reason only")
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["decision"] == "block"
        assert result["reason"] == "reason only"

    def test_no_hook_specific_output(self, capsys):
        """Stop hooks must NOT use hookSpecificOutput."""
        output_stop_block("test", "context")
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "hookSpecificOutput" not in result

    def test_no_continue_field(self, capsys):
        """Stop hooks must NOT use continue field (wrong schema)."""
        output_stop_block("test", "context")
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "continue" not in result


class TestOutputPermission:
    """Tests for PermissionRequest output format."""

    def test_allow_format(self, capsys):
        """PermissionRequest allow uses current hookSpecificOutput schema."""
        output_permission("allow", "Auto-approved: pytest")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result == {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {
                    "behavior": "allow",
                },
            }
        }

    def test_deny_format(self, capsys):
        """PermissionRequest deny includes message for Claude."""
        output_permission("deny", "Blocked: root delete")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result == {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {
                    "behavior": "deny",
                    "message": "Blocked: root delete",
                },
            }
        }


class TestIsTeamsEnabled:
    """Tests for is_teams_enabled function."""

    def test_enabled_when_set_to_1(self, monkeypatch):
        """Should return True when env var is '1'."""
        monkeypatch.setenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "1")
        assert is_teams_enabled() is True

    def test_disabled_when_not_set(self, monkeypatch):
        """Should return False when env var is not set."""
        monkeypatch.delenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", raising=False)
        assert is_teams_enabled() is False

    def test_disabled_when_set_to_0(self, monkeypatch):
        """Should return False when env var is '0'."""
        monkeypatch.setenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "0")
        assert is_teams_enabled() is False

    def test_disabled_when_set_to_true(self, monkeypatch):
        """Should return False for 'true' (only '1' is valid)."""
        monkeypatch.setenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "true")
        assert is_teams_enabled() is False

    def test_disabled_when_empty(self, monkeypatch):
        """Should return False when env var is empty string."""
        monkeypatch.setenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "")
        assert is_teams_enabled() is False


class TestIsAgentSession:
    """Tests for is_agent_session function."""

    def test_true_with_agent_type(self):
        """Should return True when agent_type is present and truthy."""
        assert is_agent_session({"agent_type": "oh-my-claude:librarian"}) is True
        assert is_agent_session({"agent_type": "librarian"}) is True

    def test_false_without_agent_type(self):
        """Should return False when agent_type is missing."""
        assert is_agent_session({}) is False
        assert is_agent_session({"session_id": "test"}) is False

    def test_false_with_none_agent_type(self):
        """Should return False when agent_type is None."""
        assert is_agent_session({"agent_type": None}) is False

    def test_false_with_empty_agent_type(self):
        """Should return False when agent_type is empty string."""
        assert is_agent_session({"agent_type": ""}) is False

    def test_true_with_extra_fields(self):
        """Should work with additional fields present."""
        data = {"agent_type": "critic", "session_id": "abc", "cwd": "/tmp"}
        assert is_agent_session(data) is True


class TestGetSessionContext:
    """Tests for get_session_context function."""

    def test_agent_session(self, monkeypatch):
        """Agent sessions should return 'agent' regardless of teams env."""
        monkeypatch.delenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", raising=False)
        assert get_session_context({"agent_type": "oh-my-claude:librarian"}) == "agent"

    def test_agent_session_with_teams(self, monkeypatch):
        """Agent sessions should return 'agent' even when teams enabled."""
        monkeypatch.setenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "1")
        assert get_session_context({"agent_type": "teammate"}) == "agent"

    def test_team_lead(self, monkeypatch):
        """Main session with teams enabled should return 'team_lead'."""
        monkeypatch.setenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "1")
        assert get_session_context({}) == "team_lead"
        assert get_session_context({"session_id": "lead"}) == "team_lead"

    def test_solo_session(self, monkeypatch):
        """Main session without teams should return 'solo'."""
        monkeypatch.delenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", raising=False)
        assert get_session_context({}) == "solo"
        assert get_session_context({"session_id": "test"}) == "solo"

    def test_solo_with_teams_disabled(self, monkeypatch):
        """Explicitly disabled teams should return 'solo'."""
        monkeypatch.setenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "0")
        assert get_session_context({}) == "solo"
