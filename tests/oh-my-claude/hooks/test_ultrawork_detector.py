"""Tests for ultrawork_detector.py."""

import pytest

# Import the module to test its patterns and functions
from ultrawork_detector import PATTERNS, detect_validation


class TestDetectValidation:
    """Tests for detect_validation function."""

    def test_nodejs_project(self, nodejs_project):
        """Node.js project should return npm commands."""
        result = detect_validation(str(nodejs_project))
        assert "npm run typecheck" in result
        assert "npm run lint" in result
        assert "npm test" in result

    def test_python_pyproject(self, python_project):
        """Python project with pyproject.toml should return ruff/pytest."""
        result = detect_validation(str(python_project))
        assert "ruff check" in result
        assert "pytest" in result

    def test_python_setup_py(self, tmp_path):
        """Python project with setup.py should return ruff/pytest."""
        (tmp_path / "setup.py").write_text("from setuptools import setup")
        result = detect_validation(str(tmp_path))
        assert "ruff check" in result
        assert "pytest" in result

    def test_go_project(self, go_project):
        """Go project should return go vet/test commands."""
        result = detect_validation(str(go_project))
        assert "go vet" in result
        assert "go test" in result

    def test_rust_project(self, rust_project):
        """Rust project should return cargo commands."""
        result = detect_validation(str(rust_project))
        assert "cargo check" in result
        assert "cargo test" in result

    def test_makefile_only(self, makefile_project):
        """Makefile-only project should return make test."""
        result = detect_validation(str(makefile_project))
        assert "make test" in result

    def test_unknown_project(self, tmp_path):
        """Unknown project type should return generic message."""
        result = detect_validation(str(tmp_path))
        assert "appropriate linters and tests" in result

    def test_priority_nodejs_over_makefile(self, tmp_path):
        """Node.js should take priority over Makefile."""
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "Makefile").write_text("test:")
        result = detect_validation(str(tmp_path))
        assert "npm" in result
        assert "make" not in result

    def test_priority_python_over_makefile(self, tmp_path):
        """Python should take priority over Makefile."""
        (tmp_path / "pyproject.toml").write_text("[project]")
        (tmp_path / "Makefile").write_text("test:")
        result = detect_validation(str(tmp_path))
        assert "ruff" in result or "pytest" in result

    def test_priority_nodejs_over_python(self, tmp_path):
        """Node.js should take priority over Python when both exist."""
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "pyproject.toml").write_text("[project]")
        result = detect_validation(str(tmp_path))
        assert "npm" in result

    def test_nonexistent_path(self, tmp_path):
        """Non-existent path should return generic message."""
        result = detect_validation(str(tmp_path / "nonexistent"))
        assert "appropriate linters and tests" in result


class TestUltraworkPatterns:
    """Tests for ultrawork mode trigger patterns."""

    @pytest.mark.parametrize(
        "trigger",
        [
            "ultrawork",
            "ulw",
        ],
    )
    def test_ultrawork_triggers(self, trigger):
        """Each ultrawork trigger should match."""
        assert PATTERNS.match("ultrawork", trigger) is not None

    def test_ultrawork_case_insensitive(self):
        """Ultrawork patterns should be case insensitive."""
        assert PATTERNS.match("ultrawork", "ULTRAWORK") is not None
        assert PATTERNS.match("ultrawork", "ULW") is not None
        assert PATTERNS.match("ultrawork", "Ultrawork") is not None

    def test_ultrawork_in_sentence(self):
        """Ultrawork triggers should match within sentences."""
        assert PATTERNS.match("ultrawork", "Please ultrawork this task") is not None
        assert PATTERNS.match("ultrawork", "fix all bugs ulw") is not None
        assert PATTERNS.match("ultrawork", "ulw fix this") is not None

    def test_non_ultrawork_no_match(self):
        """Non-trigger text should not match ultrawork."""
        assert PATTERNS.match("ultrawork", "please help me") is None
        assert PATTERNS.match("ultrawork", "analyze this code") is None
        assert PATTERNS.match("ultrawork", "ship it") is None  # No longer a trigger
        assert PATTERNS.match("ultrawork", "just work") is None  # No longer a trigger


class TestSearchPatterns:
    """Tests for search mode trigger patterns."""

    @pytest.mark.parametrize(
        "trigger",
        [
            "search for",
            "find all",
            "locate",
            "where is",
            "look for",
            "grep for",
            "hunt down",
            "track down",
            "show me where",
            "find me",
            "get me all",
            "list all",
        ],
    )
    def test_search_triggers(self, trigger):
        """Each search trigger should match."""
        assert PATTERNS.match("search", trigger) is not None

    def test_search_in_sentence(self):
        """Search triggers should match within sentences."""
        assert PATTERNS.match("search", "search for all auth files") is not None
        assert PATTERNS.match("search", "where is the config?") is not None


class TestAnalyzePatterns:
    """Tests for analyze mode trigger patterns."""

    @pytest.mark.parametrize(
        "trigger",
        [
            "analyze",
            "analyse",  # British spelling
            "understand",
            "explain how",
            "how does",
            "investigate",
            "deep dive",
            "examine",
            "inspect",
            "audit",
            "break down",
            "walk through",
            "tell me about",
            "help me understand",
            "whats going on",
        ],
    )
    def test_analyze_triggers(self, trigger):
        """Each analyze trigger should match."""
        assert PATTERNS.match("analyze", trigger) is not None

    def test_analyze_both_spellings(self):
        """Both analyze and analyse should match."""
        assert PATTERNS.match("analyze", "analyze the code") is not None
        assert PATTERNS.match("analyze", "analyse the code") is not None


class TestUltrathinkPatterns:
    """Tests for ultrathink mode trigger patterns."""

    @pytest.mark.parametrize(
        "trigger",
        [
            "ultrathink",
            "think deeply",
            "deep analysis",
            "think hard",
            "careful analysis",
            "thoroughly analyze",
        ],
    )
    def test_ultrathink_triggers(self, trigger):
        """Each ultrathink trigger should match."""
        assert PATTERNS.match("ultrathink", trigger) is not None


class TestUltradebugPatterns:
    """Tests for ultradebug mode trigger patterns."""

    @pytest.mark.parametrize(
        "trigger",
        [
            "ultradebug",
            "debug this",
            "fix this bug",
            "troubleshoot",
            "diagnose",
            "why is this failing",
            "root cause",
            "whats wrong",
            "whats broken",
            "figure out why",
            "fix the issue",
            "whats causing",
        ],
    )
    def test_ultradebug_triggers(self, trigger):
        """Each ultradebug trigger should match."""
        assert PATTERNS.match("ultradebug", trigger) is not None


class TestPatternNonOverlap:
    """Tests to ensure patterns don't incorrectly match other modes."""

    def test_ultrawork_doesnt_match_analyze(self):
        """Ultrawork pattern shouldn't match analyze triggers."""
        assert PATTERNS.match("ultrawork", "analyze this") is None

    def test_search_doesnt_match_ultrawork(self):
        """Search pattern shouldn't match ultrawork triggers."""
        assert PATTERNS.match("search", "ultrawork") is None
        assert PATTERNS.match("search", "ulw") is None

    def test_specific_mode_detection(self):
        """Each mode should detect its own triggers correctly."""
        test_cases = [
            ("ultrawork", "ulw fix bugs", True),
            ("ultrawork", "ultrawork fix bugs", True),
            ("search", "ulw fix bugs", False),
            ("analyze", "ulw fix bugs", False),
            ("search", "search for the config", True),
            ("ultrawork", "search for the config", False),
            ("analyze", "analyze the codebase", True),
            ("ultrawork", "analyze the codebase", False),
            # Former triggers that should no longer match
            ("ultrawork", "ship it", False),
            ("ultrawork", "just work on this", False),
        ]
        for pattern_name, text, should_match in test_cases:
            match = PATTERNS.match(pattern_name, text)
            if should_match:
                assert match is not None, f"{pattern_name} should match '{text}'"
            else:
                assert match is None, f"{pattern_name} should NOT match '{text}'"
