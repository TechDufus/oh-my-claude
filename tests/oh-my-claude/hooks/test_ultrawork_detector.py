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
        assert PATTERNS.match("ultrawork", "ship it") is None
        assert PATTERNS.match("ultrawork", "just work") is None


class TestUltraresearchPatterns:
    """Tests for ultraresearch mode trigger patterns."""

    @pytest.mark.parametrize(
        "trigger",
        [
            "ultraresearch",
            "ulr",
        ],
    )
    def test_ultraresearch_triggers(self, trigger):
        """Each ultraresearch trigger should match."""
        assert PATTERNS.match("ultraresearch", trigger) is not None

    def test_ultraresearch_case_insensitive(self):
        """Ultraresearch patterns should be case insensitive."""
        assert PATTERNS.match("ultraresearch", "ULTRARESEARCH") is not None
        assert PATTERNS.match("ultraresearch", "ULR") is not None
        assert PATTERNS.match("ultraresearch", "Ultraresearch") is not None

    def test_ultraresearch_in_sentence(self):
        """Ultraresearch triggers should match within sentences."""
        assert PATTERNS.match("ultraresearch", "ultraresearch best practices") is not None
        assert PATTERNS.match("ultraresearch", "ulr what are the patterns") is not None

    def test_non_ultraresearch_no_match(self):
        """Non-trigger text should not match ultraresearch."""
        assert PATTERNS.match("ultraresearch", "research this") is None
        assert PATTERNS.match("ultraresearch", "look up") is None


class TestUltrathinkPatterns:
    """Tests for ultrathink mode trigger patterns."""

    @pytest.mark.parametrize(
        "trigger",
        [
            "ultrathink",
            "ult",
        ],
    )
    def test_ultrathink_triggers(self, trigger):
        """Each ultrathink trigger should match."""
        assert PATTERNS.match("ultrathink", trigger) is not None

    def test_ultrathink_case_insensitive(self):
        """Ultrathink patterns should be case insensitive."""
        assert PATTERNS.match("ultrathink", "ULTRATHINK") is not None
        assert PATTERNS.match("ultrathink", "ULT") is not None
        assert PATTERNS.match("ultrathink", "Ultrathink") is not None

    def test_ultrathink_in_sentence(self):
        """Ultrathink triggers should match within sentences."""
        assert PATTERNS.match("ultrathink", "ultrathink about this problem") is not None
        assert PATTERNS.match("ultrathink", "ult before implementing") is not None

    def test_non_ultrathink_no_match(self):
        """Non-trigger text should not match ultrathink."""
        assert PATTERNS.match("ultrathink", "think about it") is None
        assert PATTERNS.match("ultrathink", "deep analysis") is None


class TestUltradebugPatterns:
    """Tests for ultradebug mode trigger patterns."""

    @pytest.mark.parametrize(
        "trigger",
        [
            "ultradebug",
            "uld",
        ],
    )
    def test_ultradebug_triggers(self, trigger):
        """Each ultradebug trigger should match."""
        assert PATTERNS.match("ultradebug", trigger) is not None

    def test_ultradebug_case_insensitive(self):
        """Ultradebug patterns should be case insensitive."""
        assert PATTERNS.match("ultradebug", "ULTRADEBUG") is not None
        assert PATTERNS.match("ultradebug", "ULD") is not None
        assert PATTERNS.match("ultradebug", "Ultradebug") is not None

    def test_ultradebug_in_sentence(self):
        """Ultradebug triggers should match within sentences."""
        assert PATTERNS.match("ultradebug", "ultradebug this issue") is not None
        assert PATTERNS.match("ultradebug", "uld the failing test") is not None

    def test_non_ultradebug_no_match(self):
        """Non-trigger text should not match ultradebug."""
        assert PATTERNS.match("ultradebug", "debug this") is None
        assert PATTERNS.match("ultradebug", "fix this bug") is None


class TestPatternNonOverlap:
    """Tests to ensure patterns don't incorrectly match other modes."""

    def test_ultrawork_doesnt_match_others(self):
        """Ultrawork pattern shouldn't match other ultra triggers."""
        assert PATTERNS.match("ultrawork", "ultraresearch") is None
        assert PATTERNS.match("ultrawork", "ultrathink") is None
        assert PATTERNS.match("ultrawork", "ultradebug") is None

    def test_ultraresearch_doesnt_match_others(self):
        """Ultraresearch pattern shouldn't match other triggers."""
        assert PATTERNS.match("ultraresearch", "ultrawork") is None
        assert PATTERNS.match("ultraresearch", "ulw") is None

    def test_specific_mode_detection(self):
        """Each mode should detect its own triggers correctly."""
        test_cases = [
            ("ultrawork", "ulw fix bugs", True),
            ("ultrawork", "ultrawork fix bugs", True),
            ("ultraresearch", "ulw fix bugs", False),
            ("ultrathink", "ulw fix bugs", False),
            ("ultraresearch", "ulr best practices", True),
            ("ultrawork", "ulr best practices", False),
            ("ultrathink", "ult before coding", True),
            ("ultrawork", "ult before coding", False),
            ("ultradebug", "uld the issue", True),
            ("ultrawork", "uld the issue", False),
        ]
        for pattern_name, text, should_match in test_cases:
            match = PATTERNS.match(pattern_name, text)
            if should_match:
                assert match is not None, f"{pattern_name} should match '{text}'"
            else:
                assert match is None, f"{pattern_name} should NOT match '{text}'"
