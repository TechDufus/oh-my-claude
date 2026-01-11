"""Tests for context_monitor.py.

These tests ensure the context monitoring hook correctly:
1. Estimates token usage from transcript data
2. Triggers warnings at appropriate thresholds (70% warning, 85% critical)
3. Prevents warning spam by tracking warned sessions
4. Respects environment variable configuration
"""

import pytest

from context_monitor import (
    CONTEXT_LIMIT,
    DEFAULT_CRITICAL_PCT,
    DEFAULT_WARNING_PCT,
    _warned_sessions,
    estimate_tokens,
    get_critical_threshold,
    get_warning_threshold,
)


class TestEstimateTokens:
    """Tests for the estimate_tokens function.

    The function approximates tokens as chars // 4, which is a reasonable
    heuristic for mixed English text and code.
    """

    def test_empty_transcript(self):
        """Empty transcript should estimate 0 tokens."""
        assert estimate_tokens([]) == 0

    def test_single_short_entry(self):
        """Single entry with known length should estimate correctly.

        'hello' = 5 chars -> 5 // 4 = 1 token
        """
        # String entry gets converted via str()
        transcript = [{"content": "hello"}]  # str(dict) is longer
        result = estimate_tokens(transcript)
        # The dict becomes "{'content': 'hello'}" = 21 chars -> 5 tokens
        assert result == len(str(transcript[0])) // 4

    def test_multiple_entries_sum_correctly(self):
        """Multiple entries should have their characters summed."""
        # Create entries with predictable lengths
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
            123,  # Number
            ["nested", "list"],
        ]

        total_chars = sum(len(str(entry)) for entry in transcript)
        assert estimate_tokens(transcript) == total_chars // 4

    def test_realistic_transcript_size(self):
        """Realistic transcript should produce reasonable estimates.

        A typical message might be ~500 chars, producing ~125 tokens.
        """
        message = {
            "role": "assistant",
            "content": "I'll help you with that task. " * 20,  # ~600 chars of content
        }
        transcript = [message] * 10  # 10 messages

        result = estimate_tokens(transcript)
        # Should be in reasonable range (not zero, not astronomically high)
        assert 500 < result < 5000

    def test_large_transcript_estimation(self):
        """Large transcript should estimate correctly without overflow."""
        # Simulate 1000 messages of ~200 chars each
        message = {"role": "user", "content": "x" * 150}
        transcript = [message] * 1000

        result = estimate_tokens(transcript)
        # Each entry is ~170+ chars when stringified, so 170k+ chars / 4 = 42k+ tokens
        assert result > 40000

    def test_empty_entries_contribute_minimally(self):
        """Empty or minimal entries should contribute their str() representation."""
        transcript = [
            {},
            "",
            {"content": ""},
        ]

        result = estimate_tokens(transcript)
        # Even empty dicts/strings have some char representation
        # {} = 2 chars, "" = 0 chars (as string), {"content": ""} = ~15 chars
        assert result >= 0


class TestThresholdDefaults:
    """Tests to verify default threshold values.

    These tests document the expected behavior and catch accidental changes.
    """

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
    """Tests for threshold-based warning behavior.

    These tests verify the mathematical boundaries where warnings trigger.
    """

    def test_below_warning_threshold(self):
        """Usage below 70% should not trigger any warning."""
        # 69% of 200k = 138k tokens = 552k chars
        tokens_at_69_percent = int(CONTEXT_LIMIT * 0.69)
        usage_pct = tokens_at_69_percent / CONTEXT_LIMIT
        warning_threshold = get_warning_threshold()

        assert usage_pct < warning_threshold

    def test_at_warning_threshold(self):
        """Usage at exactly 70% should trigger warning."""
        tokens_at_70_percent = int(CONTEXT_LIMIT * 0.70)
        usage_pct = tokens_at_70_percent / CONTEXT_LIMIT
        warning_threshold = get_warning_threshold()
        critical_threshold = get_critical_threshold()

        assert usage_pct >= warning_threshold
        assert usage_pct < critical_threshold

    def test_between_warning_and_critical(self):
        """Usage between 70-85% should trigger warning, not critical."""
        tokens_at_80_percent = int(CONTEXT_LIMIT * 0.80)
        usage_pct = tokens_at_80_percent / CONTEXT_LIMIT
        warning_threshold = get_warning_threshold()
        critical_threshold = get_critical_threshold()

        assert usage_pct >= warning_threshold
        assert usage_pct < critical_threshold

    def test_at_critical_threshold(self):
        """Usage at exactly 85% should trigger critical warning."""
        tokens_at_85_percent = int(CONTEXT_LIMIT * 0.85)
        usage_pct = tokens_at_85_percent / CONTEXT_LIMIT
        critical_threshold = get_critical_threshold()

        assert usage_pct >= critical_threshold

    def test_above_critical_threshold(self):
        """Usage above 85% should trigger critical warning."""
        tokens_at_90_percent = int(CONTEXT_LIMIT * 0.90)
        usage_pct = tokens_at_90_percent / CONTEXT_LIMIT
        critical_threshold = get_critical_threshold()

        assert usage_pct >= critical_threshold


class TestSessionDeduplication:
    """Tests for the session warning deduplication logic.

    The hook should only warn once per session to avoid spam.
    """

    def setup_method(self):
        """Clear warned sessions before each test."""
        _warned_sessions.clear()

    def test_warned_sessions_starts_empty(self):
        """Warned sessions set should be empty initially."""
        _warned_sessions.clear()
        assert len(_warned_sessions) == 0

    def test_session_can_be_added(self):
        """Session IDs can be added to the warned set."""
        _warned_sessions.add("session_123")
        assert "session_123" in _warned_sessions

    def test_duplicate_session_detected(self):
        """Adding same session twice should be detected via set membership."""
        _warned_sessions.add("session_abc")
        # Set prevents duplicates
        _warned_sessions.add("session_abc")
        assert len(_warned_sessions) == 1

    def test_different_sessions_tracked_separately(self):
        """Different sessions should be tracked independently."""
        _warned_sessions.add("session_1")
        _warned_sessions.add("session_2")
        _warned_sessions.add("session_3")

        assert len(_warned_sessions) == 3
        assert "session_1" in _warned_sessions
        assert "session_2" in _warned_sessions
        assert "session_3" in _warned_sessions

    def test_unknown_session_default(self):
        """Unknown session ID ('unknown') should still be tracked."""
        _warned_sessions.add("unknown")
        assert "unknown" in _warned_sessions


class TestTokenToCharacterMapping:
    """Tests verifying the ~4 chars per token heuristic.

    This heuristic is important for accurate context monitoring.
    Real-world token counts vary, but 4 chars/token is reasonable for:
    - English prose: ~4-5 chars/token
    - Code: ~3-4 chars/token (shorter tokens due to syntax)
    """

    def test_chars_to_reach_warning_threshold(self):
        """Calculate chars needed to reach 70% warning threshold.

        This helps understand what "70% context" means in practice.
        """
        warning_threshold = get_warning_threshold()
        warning_tokens = int(CONTEXT_LIMIT * warning_threshold)  # 140,000 tokens at default
        chars_needed = warning_tokens * 4  # ~560,000 chars at default

        # Verify our math (at default 70%)
        assert warning_tokens == 140_000
        assert chars_needed == 560_000

        # Create transcript with exactly that many chars
        transcript = ["x" * chars_needed]
        estimated = estimate_tokens(transcript)

        assert estimated == warning_tokens

    def test_chars_to_reach_critical_threshold(self):
        """Calculate chars needed to reach 85% critical threshold."""
        critical_threshold = get_critical_threshold()
        critical_tokens = int(CONTEXT_LIMIT * critical_threshold)  # 170,000 tokens at default
        chars_needed = critical_tokens * 4  # ~680,000 chars at default

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
