"""Tests for commit_quality_enforcer.py hook."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from commit_quality_enforcer import (
    FORBIDDEN_PATTERNS,
    count_message_body_lines,
    evaluate_message_quality,
    extract_commit_message,
    get_staged_diff_stats,
    validate_message_format,
)


class TestExtractCommitMessage:
    """Tests for extract_commit_message function."""

    def test_simple_double_quotes(self):
        """Should extract message from -m "message"."""
        cmd = 'git commit -m "feat: add feature"'
        assert extract_commit_message(cmd) == "feat: add feature"

    def test_simple_single_quotes(self):
        """Should extract message from -m 'message'."""
        cmd = "git commit -m 'fix: resolve bug'"
        assert extract_commit_message(cmd) == "fix: resolve bug"

    def test_with_other_flags(self):
        """Should extract message even with other flags present."""
        cmd = 'git commit --no-verify -m "chore: update deps" --author="Test"'
        assert extract_commit_message(cmd) == "chore: update deps"

    def test_multiline_message(self):
        """Should extract multiline message with newlines."""
        cmd = '''git commit -m "feat: add new feature

This is the body explaining the change."'''
        result = extract_commit_message(cmd)
        assert result is not None
        assert "feat: add new feature" in result
        assert "This is the body" in result

    def test_no_message_flag(self):
        """Should return None when no -m flag present."""
        cmd = "git commit --amend"
        assert extract_commit_message(cmd) is None

    def test_empty_message_returns_none(self):
        """Empty message should return None (no content to extract)."""
        cmd = 'git commit -m ""'
        # Empty quotes don't match .+ pattern, so returns None
        assert extract_commit_message(cmd) is None


class TestCountMessageBodyLines:
    """Tests for count_message_body_lines function."""

    def test_subject_only(self):
        """Should return 0 for subject-only message."""
        msg = "feat: add feature"
        assert count_message_body_lines(msg) == 0

    def test_subject_with_blank_line_only(self):
        """Should return 0 for subject with only blank line."""
        msg = "feat: add feature\n\n"
        assert count_message_body_lines(msg) == 0

    def test_single_body_line(self):
        """Should count single body line."""
        msg = "feat: add feature\n\nThis explains the change."
        assert count_message_body_lines(msg) == 1

    def test_multiple_body_lines(self):
        """Should count multiple body lines."""
        msg = """feat: add feature

This explains the change.
Here is more context.
And another line."""
        assert count_message_body_lines(msg) == 3

    def test_body_with_blank_lines(self):
        """Should only count non-empty body lines."""
        msg = """feat: add feature

First paragraph.

Second paragraph."""
        assert count_message_body_lines(msg) == 2

    def test_bullet_points(self):
        """Should count bullet point lines."""
        msg = """feat: add feature

Changes:
- First change
- Second change
- Third change"""
        assert count_message_body_lines(msg) == 4


class TestEvaluateMessageQuality:
    """Tests for evaluate_message_quality function."""

    def test_trivial_change_accepts_subject_only(self):
        """Trivial changes (<10 lines) should accept subject-only."""
        msg = "fix: typo"
        is_ok, reason = evaluate_message_quality(msg, lines_changed=5, files_changed=1)
        assert is_ok is True
        assert reason == ""

    def test_small_change_requires_body(self):
        """Small changes (10-50 lines) should require body."""
        msg = "feat: add feature"
        is_ok, reason = evaluate_message_quality(msg, lines_changed=30, files_changed=2)
        assert is_ok is False
        assert "Add a commit body" in reason

    def test_small_change_with_body_passes(self):
        """Small changes with body should pass."""
        msg = """feat: add feature

This adds the requested feature."""
        is_ok, reason = evaluate_message_quality(msg, lines_changed=30, files_changed=2)
        assert is_ok is True

    def test_medium_change_requires_detailed_body(self):
        """Medium changes (50-200 lines) should require detailed body."""
        msg = "refactor: restructure code"
        is_ok, reason = evaluate_message_quality(msg, lines_changed=100, files_changed=5)
        assert is_ok is False
        assert "at least 2-3 lines" in reason

    def test_medium_change_with_short_body_fails(self):
        """Medium changes with just one body line should fail."""
        msg = """refactor: restructure code

Quick change."""
        is_ok, reason = evaluate_message_quality(msg, lines_changed=100, files_changed=5)
        assert is_ok is False

    def test_medium_change_with_adequate_body_passes(self):
        """Medium changes with 2+ body lines should pass."""
        msg = """refactor: restructure code

Consolidated duplicate logic across modules.
This improves maintainability and reduces bugs."""
        is_ok, reason = evaluate_message_quality(msg, lines_changed=100, files_changed=5)
        assert is_ok is True

    def test_large_change_requires_extensive_body(self):
        """Large changes (200+ lines) should require 4+ body lines."""
        msg = """feat: major feature

Short body."""
        is_ok, reason = evaluate_message_quality(msg, lines_changed=300, files_changed=10)
        assert is_ok is False
        assert "Large changes require" in reason

    def test_large_change_with_detailed_body_passes(self):
        """Large changes with extensive body should pass."""
        msg = """feat: major feature

This implements the requested major feature.
It touches multiple modules across the codebase.
Key changes:
- Added new service layer
- Updated database schema"""
        is_ok, reason = evaluate_message_quality(msg, lines_changed=300, files_changed=10)
        assert is_ok is True


class TestGetStagedDiffStats:
    """Tests for get_staged_diff_stats function."""

    def test_with_staged_changes(self):
        """Should return correct stats for staged changes."""
        mock_output = "10\t5\tfile1.py\n20\t0\tfile2.py\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
            lines, files = get_staged_diff_stats()
            assert lines == 35  # 10+5+20+0
            assert files == 2

    def test_no_staged_changes(self):
        """Should return zeros when nothing staged."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            lines, files = get_staged_diff_stats()
            assert lines == 0
            assert files == 0

    def test_git_command_fails(self):
        """Should return zeros if git command fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            lines, files = get_staged_diff_stats()
            assert lines == 0
            assert files == 0

    def test_binary_files(self):
        """Should handle binary files (shown as -)."""
        mock_output = "-\t-\timage.png\n10\t5\tcode.py\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
            lines, files = get_staged_diff_stats()
            assert lines == 15  # Only code.py counted
            assert files == 2  # Both files counted

    def test_subprocess_timeout(self):
        """Should handle subprocess timeout gracefully."""
        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)
            lines, files = get_staged_diff_stats()
            assert lines == 0
            assert files == 0


class TestEdgeCases:
    """Edge case tests for commit quality enforcer."""

    def test_empty_message(self):
        """Should handle empty message."""
        is_ok, reason = evaluate_message_quality("", lines_changed=5, files_changed=1)
        assert is_ok is True  # Trivial change, subject can be empty technically

    def test_multiline_subject(self):
        """Should only count body lines, not subject."""
        msg = "feat: this is a very long subject that spans what looks like multiple conceptual parts"
        assert count_message_body_lines(msg) == 0

    def test_whitespace_only_body(self):
        """Should not count whitespace-only lines as body."""
        msg = "feat: add feature\n\n   \n   \n"
        assert count_message_body_lines(msg) == 0

    @pytest.mark.parametrize(
        "lines,files,expected",
        [
            (0, 0, True),  # No changes (edge case)
            (9, 2, True),  # Just under threshold (<10 lines AND <=2 files)
            (9, 3, False),  # <10 lines but >2 files - needs context
            (10, 1, False),  # At line threshold - requires body
            (10, 3, False),  # At line threshold - requires body
        ],
    )
    def test_boundary_conditions(self, lines, files, expected):
        """Test boundary conditions for trivial vs non-trivial changes.

        Trivial = <10 lines AND <=2 files. Otherwise requires body.
        """
        msg = "fix: simple fix"
        is_ok, _ = evaluate_message_quality(msg, lines_changed=lines, files_changed=files)
        assert is_ok is expected


# =============================================================================
# Tests for validate_message_format
# =============================================================================


class TestValidateMessageFormat:
    """Tests for validate_message_format function."""

    # --- Valid conventional commits ---

    @pytest.mark.parametrize(
        "message",
        [
            "feat: add new feature",
            "fix: resolve auth bug",
            "chore: update dependencies",
            "docs: update README",
            "style: format code",
            "refactor: simplify logic",
            "test: add unit tests",
            "perf: optimize query",
            "ci: update workflow",
            "build: update config",
        ],
    )
    def test_valid_conventional_commits_pass(self, message):
        """Valid conventional commit formats should pass."""
        is_valid, errors = validate_message_format(message)
        assert is_valid is True, f"Should pass: '{message}', errors: {errors}"
        assert errors == []

    def test_valid_with_scope(self):
        """Conventional commit with scope should pass."""
        is_valid, errors = validate_message_format("feat(auth): add JWT support")
        assert is_valid is True
        assert errors == []

    def test_valid_breaking_change(self):
        """Conventional commit with ! for breaking change should pass."""
        is_valid, errors = validate_message_format("feat!: drop Python 3.9")
        assert is_valid is True
        assert errors == []

    def test_valid_breaking_change_with_scope(self):
        """Conventional commit with scope and ! should pass."""
        is_valid, errors = validate_message_format("fix(api)!: change response format")
        assert is_valid is True
        assert errors == []

    # --- Invalid format ---

    def test_missing_type_prefix_fails(self):
        """Messages without a conventional commit type prefix should fail."""
        is_valid, errors = validate_message_format("add new feature")
        assert is_valid is False
        assert any("conventional commit" in e.lower() for e in errors)

    def test_missing_colon_fails(self):
        """Messages without colon separator should fail."""
        is_valid, errors = validate_message_format("feat add new feature")
        assert is_valid is False
        assert any("conventional commit" in e.lower() for e in errors)

    def test_uppercase_type_fails(self):
        """Type prefix must be lowercase."""
        is_valid, errors = validate_message_format("FEAT: add feature")
        assert is_valid is False

    # --- Subject length ---

    def test_subject_over_50_chars_fails(self):
        """Subject line exceeding 50 characters should fail."""
        long_subject = "feat: " + "a" * 50  # 56 chars total
        is_valid, errors = validate_message_format(long_subject)
        assert is_valid is False
        assert any("50 characters" in e for e in errors)

    def test_subject_at_50_chars_passes(self):
        """Subject line at exactly 50 characters should pass."""
        # "feat: " is 6 chars, so 44 more chars = 50 total
        subject = "feat: " + "a" * 44
        assert len(subject) == 50
        is_valid, errors = validate_message_format(subject)
        assert is_valid is True, f"errors: {errors}"

    # --- Body line length ---

    def test_body_line_over_72_chars_fails(self):
        """Body lines exceeding 72 characters should fail."""
        message = "feat: add feature\n\n" + "x" * 73
        is_valid, errors = validate_message_format(message)
        assert is_valid is False
        assert any("72 characters" in e for e in errors)

    def test_body_line_at_72_chars_passes(self):
        """Body line at exactly 72 characters should pass."""
        message = "feat: add feature\n\n" + "x" * 72
        is_valid, errors = validate_message_format(message)
        assert is_valid is True, f"errors: {errors}"

    # --- AI attribution patterns ---

    @pytest.mark.parametrize(
        "attribution",
        [
            "Generated with Claude",
            "Generated by AI",
            "Generated by GPT",
            "Generated by ChatGPT",
            "Generated with Anthropic",
            "Created by Claude",
            "Created by AI",
            "Written by Claude",
            "Written by AI",
            "Co-authored-by: Claude",
            "Co-authored-by: AI",
            "Co-authored-by: Anthropic",
            "Co-authored-by: ChatGPT",
            "Co-authored-by: Copilot",
            "co-authored-by claude",
            "ai-generated",
            "AI-Generated",
            "ai-assisted",
            "AI-Assisted",
            "\U0001F916",  # Robot emoji
        ],
    )
    def test_ai_attribution_blocked(self, attribution):
        """Each FORBIDDEN_PATTERNS entry should be detected and blocked."""
        message = f"feat: add feature\n\n{attribution}"
        is_valid, errors = validate_message_format(message)
        assert is_valid is False, f"Should block attribution: '{attribution}'"
        assert any("attribution" in e.lower() or "forbidden" in e.lower() for e in errors)

    def test_legitimate_ai_mention_not_blocked(self):
        """Mentioning AI in non-attribution context should be allowed."""
        message = "feat: add ai-powered search feature"
        is_valid, errors = validate_message_format(message)
        # "ai-powered" doesn't match any forbidden pattern
        assert is_valid is True, f"errors: {errors}"

    # --- Comment lines ---

    def test_comment_lines_skipped(self):
        """Lines starting with # should be skipped."""
        message = "# This is a comment\nfeat: add feature\n# Another comment"
        is_valid, errors = validate_message_format(message)
        assert is_valid is True, f"errors: {errors}"

    def test_comment_only_message(self):
        """Message with only comments should have no first_content_line."""
        message = "# comment only\n# another comment"
        is_valid, errors = validate_message_format(message)
        # No first_content_line found, so no conventional commit check
        assert is_valid is True

    # --- Empty lines before first content ---

    def test_empty_lines_before_content(self):
        """Empty lines before first content line should be ignored."""
        message = "\n\nfeat: add feature"
        is_valid, errors = validate_message_format(message)
        assert is_valid is True, f"errors: {errors}"

    def test_comments_and_empty_before_content(self):
        """Mix of comments and empty lines before content should work."""
        message = "# git status\n\nfeat: add feature"
        is_valid, errors = validate_message_format(message)
        assert is_valid is True, f"errors: {errors}"

    # --- Multiple errors ---

    def test_multiple_errors_reported(self):
        """Should report all errors, not just the first."""
        # Long subject (>50) + not conventional format + long body line
        long_subject = "this is a very long subject line that definitely exceeds fifty characters and has no type"
        long_body = "x" * 80
        message = f"{long_subject}\n\n{long_body}"
        is_valid, errors = validate_message_format(message)
        assert is_valid is False
        assert len(errors) >= 2  # At least subject length + conventional format

    # --- Edge cases ---

    def test_empty_message(self):
        """Empty message should pass (no first_content_line found)."""
        is_valid, errors = validate_message_format("")
        assert is_valid is True

    def test_whitespace_only_message(self):
        """Whitespace-only message should pass (no content lines)."""
        is_valid, errors = validate_message_format("   \n   \n   ")
        assert is_valid is True
