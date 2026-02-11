"""Tests for context_monitor.py.

These tests ensure the context monitoring hook correctly:
1. Gets context usage from native percentage or falls back to estimation
2. Triggers warnings at appropriate thresholds (70% warning, 85% critical)
3. Prevents warning spam via filesystem-based deduplication
4. Respects environment variable configuration
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from context_monitor import (
    CONTEXT_LIMIT,
    DEFAULT_CRITICAL_PCT,
    DEFAULT_WARNING_PCT,
    estimate_tokens,
    get_critical_threshold,
    get_usage_percentage,
    get_warning_threshold,
    has_warned,
    mark_warned,
)


class TestEstimateTokens:
    """Tests for the estimate_tokens fallback function.

    The function approximates tokens as chars // 4, which is a reasonable
    heuristic for mixed English text and code.
    """

    def test_empty_transcript(self):
        """Empty transcript should estimate 0 tokens."""
        assert estimate_tokens([]) == 0

    def test_single_short_entry(self):
        """Single entry with known length should estimate correctly."""
        transcript = [{"content": "hello"}]
        result = estimate_tokens(transcript)
        assert result == len(str(transcript[0])) // 4

    def test_multiple_entries_sum_correctly(self):
        """Multiple entries should have their characters summed."""
        entry1 = "a" * 100  # 100 chars -> 25 tokens
        entry2 = "b" * 200  # 200 chars -> 50 tokens
        transcript = [entry1, entry2]
        assert estimate_tokens(transcript) == 75  # (100 + 200) // 4

    def test_handles_dict_entries(self):
        """Dict entries should be stringified and counted."""
        transcript = [{"role": "user", "content": "test message"}]
        result = estimate_tokens(transcript)
        expected_chars = len(str(transcript[0]))
        assert result == expected_chars // 4

    def test_handles_mixed_types(self):
        """Should handle mixed entry types in transcript."""
        transcript = [
            "plain string",
            {"role": "assistant", "content": "response"},
            123,
            ["nested", "list"],
        ]
        total_chars = sum(len(str(entry)) for entry in transcript)
        assert estimate_tokens(transcript) == total_chars // 4

    def test_large_transcript_estimation(self):
        """Large transcript should estimate correctly without overflow."""
        message = {"role": "user", "content": "x" * 150}
        transcript = [message] * 1000
        result = estimate_tokens(transcript)
        assert result > 40000

    def test_empty_entries_contribute_minimally(self):
        """Empty or minimal entries should contribute their str() representation."""
        transcript = [{}, "", {"content": ""}]
        result = estimate_tokens(transcript)
        assert result >= 0


class TestThresholdDefaults:
    """Tests to verify default threshold values."""

    def test_context_limit_is_200k(self):
        """Context limit should be 200,000 tokens (Claude's context window)."""
        assert CONTEXT_LIMIT == 200_000

    def test_default_warning_is_70_percent(self):
        """Default warning should be at 70% usage."""
        assert DEFAULT_WARNING_PCT == 70

    def test_default_critical_is_85_percent(self):
        """Default critical should be at 85% usage."""
        assert DEFAULT_CRITICAL_PCT == 85

    def test_critical_above_warning(self):
        """Critical threshold must be higher than warning threshold."""
        assert get_critical_threshold() > get_warning_threshold()


class TestThresholdEnvVars:
    """Tests for environment variable configuration."""

    def test_default_warning_threshold(self, monkeypatch):
        """Without env var, should return default 70%."""
        monkeypatch.delenv("OMC_CONTEXT_WARN_PCT", raising=False)
        assert get_warning_threshold() == 0.70

    def test_default_critical_threshold(self, monkeypatch):
        """Without env var, should return default 85%."""
        monkeypatch.delenv("OMC_CONTEXT_CRITICAL_PCT", raising=False)
        assert get_critical_threshold() == 0.85

    def test_custom_warning_threshold(self, monkeypatch):
        """Custom warning threshold via env var."""
        monkeypatch.setenv("OMC_CONTEXT_WARN_PCT", "60")
        assert get_warning_threshold() == 0.60

    def test_custom_critical_threshold(self, monkeypatch):
        """Custom critical threshold via env var."""
        monkeypatch.setenv("OMC_CONTEXT_CRITICAL_PCT", "90")
        assert get_critical_threshold() == 0.90

    def test_invalid_warning_returns_default(self, monkeypatch):
        """Invalid env var value should return default."""
        monkeypatch.setenv("OMC_CONTEXT_WARN_PCT", "not_a_number")
        assert get_warning_threshold() == 0.70

    def test_invalid_critical_returns_default(self, monkeypatch):
        """Invalid env var value should return default."""
        monkeypatch.setenv("OMC_CONTEXT_CRITICAL_PCT", "invalid")
        assert get_critical_threshold() == 0.85

    def test_threshold_clamped_to_100(self, monkeypatch):
        """Threshold above 100 should be clamped."""
        monkeypatch.setenv("OMC_CONTEXT_WARN_PCT", "150")
        assert get_warning_threshold() == 1.0

    def test_threshold_clamped_to_0(self, monkeypatch):
        """Negative threshold should be clamped to 0."""
        monkeypatch.setenv("OMC_CONTEXT_WARN_PCT", "-10")
        assert get_warning_threshold() == 0.0


class TestThresholdBehavior:
    """Tests for threshold-based warning behavior."""

    def test_below_warning_threshold(self):
        """Usage below 70% should not trigger any warning."""
        tokens_at_69_percent = int(CONTEXT_LIMIT * 0.69)
        usage_pct = tokens_at_69_percent / CONTEXT_LIMIT
        assert usage_pct < get_warning_threshold()

    def test_at_warning_threshold(self):
        """Usage at exactly 70% should trigger warning."""
        tokens_at_70_percent = int(CONTEXT_LIMIT * 0.70)
        usage_pct = tokens_at_70_percent / CONTEXT_LIMIT
        assert usage_pct >= get_warning_threshold()
        assert usage_pct < get_critical_threshold()

    def test_between_warning_and_critical(self):
        """Usage between 70-85% should trigger warning, not critical."""
        tokens_at_80_percent = int(CONTEXT_LIMIT * 0.80)
        usage_pct = tokens_at_80_percent / CONTEXT_LIMIT
        assert usage_pct >= get_warning_threshold()
        assert usage_pct < get_critical_threshold()

    def test_at_critical_threshold(self):
        """Usage at exactly 85% should trigger critical warning."""
        tokens_at_85_percent = int(CONTEXT_LIMIT * 0.85)
        usage_pct = tokens_at_85_percent / CONTEXT_LIMIT
        assert usage_pct >= get_critical_threshold()

    def test_above_critical_threshold(self):
        """Usage above 85% should trigger critical warning."""
        tokens_at_90_percent = int(CONTEXT_LIMIT * 0.90)
        usage_pct = tokens_at_90_percent / CONTEXT_LIMIT
        assert usage_pct >= get_critical_threshold()


class TestSessionDeduplication:
    """Tests for filesystem-based session warning deduplication.

    Each hook invocation is a fresh Python process, so dedup uses
    filesystem markers at /tmp/omc_context_{session_id}_{threshold}.
    """

    def test_no_marker_means_not_warned(self, tmp_path, monkeypatch):
        """Fresh session should not show as warned."""
        monkeypatch.setattr("context_monitor._DEDUP_DIR", tmp_path)
        assert not has_warned("session_123", "warning")

    def test_mark_creates_file(self, tmp_path, monkeypatch):
        """mark_warned should create a marker file."""
        monkeypatch.setattr("context_monitor._DEDUP_DIR", tmp_path)
        mark_warned("session_123", "warning")
        assert (tmp_path / "omc_context_session_123_warning").exists()

    def test_has_warned_after_mark(self, tmp_path, monkeypatch):
        """has_warned returns True after mark_warned."""
        monkeypatch.setattr("context_monitor._DEDUP_DIR", tmp_path)
        mark_warned("session_abc", "critical")
        assert has_warned("session_abc", "critical")

    def test_different_thresholds_tracked_separately(self, tmp_path, monkeypatch):
        """Warning and critical markers are independent per session."""
        monkeypatch.setattr("context_monitor._DEDUP_DIR", tmp_path)
        mark_warned("session_1", "warning")
        assert has_warned("session_1", "warning")
        assert not has_warned("session_1", "critical")

    def test_different_sessions_tracked_separately(self, tmp_path, monkeypatch):
        """Markers are independent across sessions."""
        monkeypatch.setattr("context_monitor._DEDUP_DIR", tmp_path)
        mark_warned("session_1", "warning")
        assert not has_warned("session_2", "warning")

    def test_mark_warned_handles_os_error(self, monkeypatch):
        """mark_warned should not raise on OSError."""
        monkeypatch.setattr("context_monitor._DEDUP_DIR", Path("/nonexistent/path"))
        # Should not raise
        mark_warned("session_err", "warning")


class TestGetUsagePercentage:
    """Tests for get_usage_percentage: native vs fallback."""

    def test_native_percentage_preferred(self):
        """Should use context_window.used_percentage when available."""
        data = {"context_window": {"used_percentage": 75}}
        assert get_usage_percentage(data) == 0.75

    def test_native_zero(self):
        """Native 0% should return 0.0."""
        data = {"context_window": {"used_percentage": 0}}
        assert get_usage_percentage(data) == 0.0

    def test_native_100(self):
        """Native 100% should return 1.0."""
        data = {"context_window": {"used_percentage": 100}}
        assert get_usage_percentage(data) == 1.0

    def test_native_float_value(self):
        """Native float value should be handled correctly."""
        data = {"context_window": {"used_percentage": 72.5}}
        assert get_usage_percentage(data) == 0.725

    def test_fallback_when_context_window_missing(self):
        """Falls back to transcript estimation when context_window is absent."""
        # 80% of context in chars: 200k tokens * 0.80 * 4 chars/token
        chars = CONTEXT_LIMIT * 4 * 80 // 100
        data = {"transcript": ["x" * chars]}
        result = get_usage_percentage(data)
        assert abs(result - 0.80) < 0.01

    def test_fallback_when_used_percentage_missing(self):
        """Falls back when context_window exists but used_percentage is absent."""
        data = {"context_window": {}, "transcript": []}
        assert get_usage_percentage(data) == 0.0

    def test_fallback_with_empty_transcript(self):
        """Fallback with empty transcript returns 0.0."""
        data = {"transcript": []}
        assert get_usage_percentage(data) == 0.0

    def test_fallback_with_no_transcript(self):
        """Fallback with no transcript key returns 0.0."""
        data = {}
        assert get_usage_percentage(data) == 0.0

    def test_fallback_logs_debug(self):
        """Fallback path should call log_debug."""
        data = {"transcript": ["hello"]}
        with patch("context_monitor.log_debug") as mock_debug:
            get_usage_percentage(data)
            mock_debug.assert_called()
            calls = [str(c) for c in mock_debug.call_args_list]
            assert any("estimation" in c for c in calls)

    def test_native_does_not_log_fallback(self):
        """Native path should not log fallback message."""
        data = {"context_window": {"used_percentage": 50}}
        with patch("context_monitor.log_debug") as mock_debug:
            get_usage_percentage(data)
            calls = [str(c) for c in mock_debug.call_args_list]
            assert not any("estimation" in c for c in calls)

    def test_invalid_native_falls_back(self):
        """Invalid native value triggers fallback."""
        data = {
            "context_window": {"used_percentage": "not_a_number"},
            "transcript": [],
        }
        with patch("context_monitor.log_debug") as mock_debug:
            result = get_usage_percentage(data)
            assert result == 0.0
            mock_debug.assert_called()


class TestTokenToCharacterMapping:
    """Tests verifying the ~4 chars per token heuristic."""

    def test_chars_to_reach_warning_threshold(self):
        """Calculate chars needed to reach 70% warning threshold."""
        warning_threshold = get_warning_threshold()
        warning_tokens = int(CONTEXT_LIMIT * warning_threshold)
        chars_needed = warning_tokens * 4

        assert warning_tokens == 140_000
        assert chars_needed == 560_000

        transcript = ["x" * chars_needed]
        estimated = estimate_tokens(transcript)
        assert estimated == warning_tokens

    def test_chars_to_reach_critical_threshold(self):
        """Calculate chars needed to reach 85% critical threshold."""
        critical_threshold = get_critical_threshold()
        critical_tokens = int(CONTEXT_LIMIT * critical_threshold)
        chars_needed = critical_tokens * 4

        assert critical_tokens == 170_000
        assert chars_needed == 680_000

    @pytest.mark.parametrize(
        "char_count,expected_tokens",
        [
            (0, 0),
            (1, 0),  # 1 char -> 0 tokens (integer division)
            (3, 0),  # 3 chars -> 0 tokens
            (4, 1),  # 4 chars -> 1 token
            (7, 1),  # 7 chars -> 1 token
            (8, 2),  # 8 chars -> 2 tokens
            (100, 25),  # 100 chars -> 25 tokens
            (1000, 250),  # 1000 chars -> 250 tokens
        ],
    )
    def test_character_to_token_conversion(self, char_count, expected_tokens):
        """Verify character to token conversion formula."""
        transcript = ["x" * char_count]
        assert estimate_tokens(transcript) == expected_tokens
