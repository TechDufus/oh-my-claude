"""Tests for claudemd_health.py hook."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from claudemd_health import (
    MAX_INSTRUCTIONS_HEALTHY,
    MAX_LINES_HEALTHY,
    analyze_claudemd,
    count_instructions,
    detect_nested_opportunities,
    find_hardcoded_paths,
)

HOOK_PATH = Path(__file__).parent.parent.parent.parent / "plugins/oh-my-claude/hooks/claudemd_health.py"


def run_hook(input_data: dict) -> dict:
    """Run the hook with given input and return parsed output."""
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Hook failed: {result.stderr}")

    if not result.stdout.strip():
        return {}

    return json.loads(result.stdout)


def get_context(output: dict) -> str:
    """Extract additionalContext from hook output."""
    return output.get("hookSpecificOutput", {}).get("additionalContext", "")


# =============================================================================
# Unit Tests: count_instructions
# =============================================================================


class TestCountInstructions:
    """Tests for count_instructions function."""

    def test_counts_bullet_points_dash(self):
        """Should count dash-prefixed bullet points."""
        content = "- Do this\n- Do that\n- Also this"
        assert count_instructions(content) == 3

    def test_counts_bullet_points_asterisk(self):
        """Should count asterisk-prefixed bullet points."""
        content = "* First\n* Second\n* Third"
        assert count_instructions(content) == 3

    def test_counts_imperative_verbs(self):
        """Should count lines starting with imperative verbs."""
        content = "Use pytest for testing\nAvoid global state\nPrefer composition"
        assert count_instructions(content) == 3

    def test_empty_content(self):
        """Should return 0 for empty content."""
        assert count_instructions("") == 0

    def test_no_instructions(self):
        """Should return 0 for content without instructions."""
        content = "# Title\n\nThis is a paragraph of text.\nAnother line."
        assert count_instructions(content) == 0

    def test_mixed_bullets_and_verbs(self):
        """Should count both bullets and imperative verb lines."""
        content = "- First item\nAlways check tests\n* Second item\nNever skip reviews"
        assert count_instructions(content) == 4

    def test_short_bullet_not_counted(self):
        """Bullet with only 1-2 chars should not be counted."""
        content = "- \n- x\n- ab"
        # "- " has len 2 after strip, not > 2
        # "- x" has len 3, > 2 -> counted
        # "- ab" has len 4, > 2 -> counted
        assert count_instructions(content) >= 1

    def test_bullet_takes_precedence_over_verb(self):
        """A bullet line starting with a verb should be counted once."""
        content = "- Use this library"
        # Counted as bullet, then continue (not counted again as verb)
        assert count_instructions(content) == 1

    def test_verb_with_comma(self):
        """Imperative verb followed by comma should be detected."""
        content = "Use, when possible, the standard library"
        assert count_instructions(content) == 1


# =============================================================================
# Unit Tests: find_hardcoded_paths
# =============================================================================


class TestFindHardcodedPaths:
    """Tests for find_hardcoded_paths function."""

    def test_detects_src_path_patterns(self):
        """Should detect src/utils/auth.ts style paths."""
        content = "Important file: src/utils/auth.ts"
        paths = find_hardcoded_paths(content)
        assert len(paths) >= 1
        assert any("src/utils/auth.ts" in p for p in paths)

    def test_detects_line_number_references(self):
        """Should detect auth.ts:42 style line references."""
        content = "See auth.ts:42 for the handler"
        paths = find_hardcoded_paths(content)
        assert len(paths) >= 1
        assert any("auth.ts:42" in p for p in paths)

    def test_detects_multiple_extensions(self):
        """Should detect paths with various source file extensions."""
        content = """
        - src/api/routes.py
        - lib/helpers/format.go
        - app/models/user.rs
        - components/Button.tsx
        """
        paths = find_hardcoded_paths(content)
        assert len(paths) >= 4

    def test_empty_for_no_matches(self):
        """Should return empty list when no hardcoded paths found."""
        content = "This is plain text with no file paths."
        paths = find_hardcoded_paths(content)
        assert paths == []

    def test_empty_content(self):
        """Should return empty list for empty content."""
        paths = find_hardcoded_paths("")
        assert paths == []

    def test_deduplicates_paths(self):
        """Should not return duplicate paths."""
        content = "See src/utils/auth.ts and also src/utils/auth.ts"
        paths = find_hardcoded_paths(content)
        # Uses a set internally, so no duplicates
        assert len([p for p in paths if "src/utils/auth.ts" in p]) == 1


# =============================================================================
# Unit Tests: detect_nested_opportunities
# =============================================================================


class TestDetectNestedOpportunities:
    """Tests for detect_nested_opportunities function."""

    def test_finds_dirs_without_claudemd(self, tmp_path):
        """Should find common directories that lack CLAUDE.md."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        suggestions = detect_nested_opportunities(tmp_path, "some content")
        assert len(suggestions) > 0
        assert any("without CLAUDE.md" in s for s in suggestions)

    def test_skips_dirs_with_claudemd(self, tmp_path):
        """Should not suggest dirs that already have CLAUDE.md."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "CLAUDE.md").write_text("# Instructions")
        suggestions = detect_nested_opportunities(tmp_path, "some content")
        # src should not appear in suggestions
        dir_suggestions = [s for s in suggestions if "without CLAUDE.md" in s]
        if dir_suggestions:
            assert "src" not in dir_suggestions[0]

    def test_detects_content_patterns(self, tmp_path):
        """Should detect domain-specific content patterns (5+ matches needed)."""
        # Create heavy testing content (5+ mentions)
        content = "test test test test test test spec spec spec spec spec"
        suggestions = detect_nested_opportunities(tmp_path, content)
        assert any("testing" in s.lower() for s in suggestions)

    def test_caps_at_3_suggestions(self, tmp_path):
        """Should cap total suggestions at 3 (plus /init-deep reference)."""
        # Create many directories without CLAUDE.md
        for dirname in ["src", "lib", "app", "tests", "api", "routes", "hooks"]:
            (tmp_path / dirname).mkdir()
        # Create content with many domain patterns
        content = ("test " * 10 + "component " * 10 + "api " * 10 +
                   "hook useEffect " * 10)
        suggestions = detect_nested_opportunities(tmp_path, content)
        # Max 3 suggestions + 1 /init-deep reference = 4
        assert len(suggestions) <= 4

    def test_includes_init_deep_when_suggestions_exist(self, tmp_path):
        """Should include /init-deep reference when suggestions found."""
        (tmp_path / "src").mkdir()
        suggestions = detect_nested_opportunities(tmp_path, "content")
        if suggestions:
            assert any("/init-deep" in s for s in suggestions)

    def test_empty_for_no_opportunities(self, tmp_path):
        """Should return empty list when no opportunities found."""
        # No common directories, minimal content
        suggestions = detect_nested_opportunities(tmp_path, "hello world")
        assert suggestions == []


# =============================================================================
# Unit Tests: analyze_claudemd
# =============================================================================


class TestAnalyzeClaudemd:
    """Tests for analyze_claudemd function."""

    def test_warns_large_file(self, tmp_path):
        """Should warn when CLAUDE.md exceeds MAX_LINES_HEALTHY."""
        claudemd = tmp_path / "CLAUDE.md"
        content = "\n".join(f"Line {i}" for i in range(MAX_LINES_HEALTHY + 10))
        claudemd.write_text(content)
        warnings = analyze_claudemd(claudemd)
        assert any("large" in w.lower() for w in warnings)

    def test_warns_high_instruction_density(self, tmp_path):
        """Should warn when instruction count exceeds MAX_INSTRUCTIONS_HEALTHY."""
        claudemd = tmp_path / "CLAUDE.md"
        # Generate many bullet points to exceed instruction threshold
        lines = [f"- Instruction number {i}" for i in range(MAX_INSTRUCTIONS_HEALTHY + 10)]
        claudemd.write_text("\n".join(lines))
        warnings = analyze_claudemd(claudemd)
        assert any("instruction" in w.lower() for w in warnings)

    def test_reports_hardcoded_paths(self, tmp_path):
        """Should report hardcoded file paths."""
        claudemd = tmp_path / "CLAUDE.md"
        claudemd.write_text("Important: src/utils/auth.ts handles authentication\n" * 5)
        warnings = analyze_claudemd(claudemd)
        assert any("hardcoded" in w.lower() for w in warnings)

    def test_empty_for_healthy_file(self, tmp_path):
        """Should return empty list for a healthy CLAUDE.md."""
        claudemd = tmp_path / "CLAUDE.md"
        claudemd.write_text("# Project\n\nSimple instructions here.")
        warnings = analyze_claudemd(claudemd)
        assert warnings == []

    def test_handles_unreadable_file(self, tmp_path):
        """Should return empty list for unreadable file."""
        claudemd = tmp_path / "CLAUDE.md"
        # File does not exist
        warnings = analyze_claudemd(claudemd)
        assert warnings == []

    def test_handles_binary_content(self, tmp_path):
        """Should handle file with binary/undecodable content."""
        claudemd = tmp_path / "CLAUDE.md"
        claudemd.write_bytes(b"\x80\x81\x82" * 100)
        warnings = analyze_claudemd(claudemd)
        assert warnings == []  # Gracefully returns empty


# =============================================================================
# Integration Tests: main function via subprocess
# =============================================================================


class TestMainIntegration:
    """Integration tests for the main hook function via subprocess."""

    def test_skips_for_subagents(self):
        """Should skip health check for subagents."""
        output = run_hook({"agent_type": "worker"})
        assert output == {}

    def test_skips_when_claudemd_missing(self, tmp_path):
        """Should skip when CLAUDE.md does not exist."""
        output = run_hook({"cwd": str(tmp_path)})
        assert output == {}

    def test_outputs_warnings_when_found(self, tmp_path):
        """Should output health warnings when CLAUDE.md has issues."""
        claudemd = tmp_path / "CLAUDE.md"
        content = "\n".join(f"- Instruction {i}" for i in range(200))
        claudemd.write_text(content)
        output = run_hook({"cwd": str(tmp_path)})
        context = get_context(output)
        assert "Health Check" in context

    def test_empty_for_healthy_claudemd(self, tmp_path):
        """Should output nothing for a healthy CLAUDE.md."""
        claudemd = tmp_path / "CLAUDE.md"
        claudemd.write_text("# Project\n\nKeep it simple.")
        output = run_hook({"cwd": str(tmp_path)})
        assert output == {}

    def test_empty_input(self):
        """Should handle empty input gracefully."""
        output = run_hook({})
        assert output == {}
