"""Tests for context_protector.py PreToolUse hook."""

import pytest

from context_protector import (
    DEFAULT_THRESHOLD,
    get_line_count,
    get_threshold,
    is_allowlisted,
    is_blocking_disabled,
)


class TestGetLineCount:
    """Tests for get_line_count function."""

    def test_small_file(self, tmp_path):
        """Small file should return correct line count."""
        f = tmp_path / "small.txt"
        f.write_text("line1\nline2\nline3\n")
        assert get_line_count(str(f)) == 3

    def test_empty_file(self, tmp_path):
        """Empty file should return 0 lines."""
        f = tmp_path / "empty.txt"
        f.write_text("")
        assert get_line_count(str(f)) == 0

    def test_large_file(self, tmp_path):
        """Large file should return correct line count."""
        f = tmp_path / "large.txt"
        f.write_text("\n".join([f"line{i}" for i in range(500)]) + "\n")
        assert get_line_count(str(f)) == 500

    def test_nonexistent_file(self, tmp_path):
        """Non-existent file should return None."""
        assert get_line_count(str(tmp_path / "nonexistent.txt")) is None

    def test_directory_returns_none(self, tmp_path):
        """Directory path should return None."""
        assert get_line_count(str(tmp_path)) is None

    def test_file_no_trailing_newline(self, tmp_path):
        """File without trailing newline should still count correctly."""
        f = tmp_path / "no_newline.txt"
        f.write_text("line1\nline2\nline3")  # No trailing newline
        # wc -l counts newlines, so this is 2
        assert get_line_count(str(f)) == 2

    def test_single_line_no_newline(self, tmp_path):
        """Single line without newline should be 0 (wc -l behavior)."""
        f = tmp_path / "single.txt"
        f.write_text("single line")
        assert get_line_count(str(f)) == 0

    def test_single_line_with_newline(self, tmp_path):
        """Single line with newline should be 1."""
        f = tmp_path / "single_newline.txt"
        f.write_text("single line\n")
        assert get_line_count(str(f)) == 1


class TestGetThreshold:
    """Tests for get_threshold function."""

    def test_default_threshold(self, monkeypatch):
        """Without env var, should return default."""
        monkeypatch.delenv("OMC_LARGE_FILE_THRESHOLD", raising=False)
        assert get_threshold() == DEFAULT_THRESHOLD

    def test_custom_threshold(self, monkeypatch):
        """With env var set, should return custom value."""
        monkeypatch.setenv("OMC_LARGE_FILE_THRESHOLD", "200")
        assert get_threshold() == 200

    def test_invalid_threshold_returns_default(self, monkeypatch):
        """Invalid env var value should return default."""
        monkeypatch.setenv("OMC_LARGE_FILE_THRESHOLD", "not_a_number")
        assert get_threshold() == DEFAULT_THRESHOLD

    def test_zero_threshold(self, monkeypatch):
        """Zero threshold should be valid."""
        monkeypatch.setenv("OMC_LARGE_FILE_THRESHOLD", "0")
        assert get_threshold() == 0

    def test_negative_threshold(self, monkeypatch):
        """Negative threshold should be valid (though unusual)."""
        monkeypatch.setenv("OMC_LARGE_FILE_THRESHOLD", "-1")
        assert get_threshold() == -1


class TestIsBlockingDisabled:
    """Tests for is_blocking_disabled function."""

    def test_default_enabled(self, monkeypatch):
        """Without env var, blocking should be enabled (function returns False)."""
        monkeypatch.delenv("OMC_ALLOW_LARGE_READS", raising=False)
        assert is_blocking_disabled() is False

    @pytest.mark.parametrize("value", ["1", "true", "yes", "TRUE", "Yes", "TRUE"])
    def test_disabled_values(self, monkeypatch, value):
        """Various truthy values should disable blocking."""
        monkeypatch.setenv("OMC_ALLOW_LARGE_READS", value)
        assert is_blocking_disabled() is True

    @pytest.mark.parametrize("value", ["0", "false", "no", "", "other"])
    def test_enabled_values(self, monkeypatch, value):
        """Various falsy values should keep blocking enabled."""
        monkeypatch.setenv("OMC_ALLOW_LARGE_READS", value)
        assert is_blocking_disabled() is False


class TestThresholdBehavior:
    """Tests for threshold-based blocking logic."""

    def test_file_under_threshold(self, tmp_path):
        """File under threshold should be allowed."""
        f = tmp_path / "small.txt"
        f.write_text("\n".join([f"line{i}" for i in range(50)]) + "\n")
        line_count = get_line_count(str(f))
        threshold = DEFAULT_THRESHOLD
        assert line_count is not None
        assert line_count <= threshold

    def test_file_at_threshold(self, tmp_path):
        """File exactly at threshold should be allowed."""
        f = tmp_path / "exact.txt"
        f.write_text("\n".join([f"line{i}" for i in range(DEFAULT_THRESHOLD)]) + "\n")
        line_count = get_line_count(str(f))
        threshold = DEFAULT_THRESHOLD
        assert line_count is not None
        assert line_count <= threshold

    def test_file_over_threshold(self, tmp_path):
        """File over threshold should be blocked."""
        f = tmp_path / "large.txt"
        f.write_text("\n".join([f"line{i}" for i in range(DEFAULT_THRESHOLD + 50)]) + "\n")
        line_count = get_line_count(str(f))
        threshold = DEFAULT_THRESHOLD
        assert line_count is not None
        assert line_count > threshold

    def test_custom_threshold_file_under(self, tmp_path, monkeypatch):
        """File under custom threshold should be allowed."""
        monkeypatch.setenv("OMC_LARGE_FILE_THRESHOLD", "200")
        f = tmp_path / "medium.txt"
        f.write_text("\n".join([f"line{i}" for i in range(150)]) + "\n")
        line_count = get_line_count(str(f))
        threshold = get_threshold()
        assert line_count is not None
        assert line_count <= threshold

    def test_custom_threshold_file_over(self, tmp_path, monkeypatch):
        """File over custom threshold should be blocked."""
        monkeypatch.setenv("OMC_LARGE_FILE_THRESHOLD", "50")
        f = tmp_path / "medium.txt"
        f.write_text("\n".join([f"line{i}" for i in range(100)]) + "\n")
        line_count = get_line_count(str(f))
        threshold = get_threshold()
        assert line_count is not None
        assert line_count > threshold


class TestEdgeCases:
    """Edge case tests."""

    def test_binary_file_handling(self, tmp_path):
        """Binary files should return some line count (or handle gracefully)."""
        f = tmp_path / "binary.bin"
        f.write_bytes(b"\x00\x01\x02\x03\n\x04\x05\n")
        # wc -l will count newline bytes even in binary
        result = get_line_count(str(f))
        assert result is not None
        assert result >= 0

    def test_file_with_long_lines(self, tmp_path):
        """File with very long lines should still count correctly."""
        f = tmp_path / "long_lines.txt"
        long_line = "x" * 10000
        f.write_text(f"{long_line}\n{long_line}\n{long_line}\n")
        assert get_line_count(str(f)) == 3

    def test_unicode_file(self, tmp_path):
        """Unicode file should count correctly."""
        f = tmp_path / "unicode.txt"
        f.write_text("日本語\n中文\nहिंदी\n", encoding="utf-8")
        assert get_line_count(str(f)) == 3

    def test_symlink_to_file(self, tmp_path):
        """Symlink to file should count the target file."""
        target = tmp_path / "target.txt"
        target.write_text("line1\nline2\nline3\n")
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        assert get_line_count(str(link)) == 3

    def test_symlink_to_nonexistent(self, tmp_path):
        """Broken symlink should return None."""
        link = tmp_path / "broken_link.txt"
        link.symlink_to(tmp_path / "nonexistent.txt")
        assert get_line_count(str(link)) is None


class TestAllowlist:
    """Tests for is_allowlisted function."""

    def test_claudemd_exact_match(self):
        """CLAUDE.md should be allowlisted."""
        assert is_allowlisted("CLAUDE.md") is True

    def test_claudemd_with_path(self):
        """CLAUDE.md with path prefix should be allowlisted."""
        assert is_allowlisted("/path/to/CLAUDE.md") is True

    def test_claudemd_in_dotclaude(self):
        """CLAUDE.md in .claude directory should be allowlisted."""
        assert is_allowlisted("/path/.claude/CLAUDE.md") is True

    def test_readme_not_allowlisted(self):
        """README.md should not be allowlisted."""
        assert is_allowlisted("README.md") is False

    def test_claudemd_backup_not_allowlisted(self):
        """CLAUDE.md.bak should not be allowlisted."""
        assert is_allowlisted("CLAUDE.md.bak") is False

    def test_prefixed_claudemd_not_allowlisted(self):
        """some_CLAUDE.md should not be allowlisted."""
        assert is_allowlisted("some_CLAUDE.md") is False
