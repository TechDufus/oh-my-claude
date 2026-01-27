"""Tests for ultrawork_detector.py."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Import the module to test its patterns and functions
from ultrawork_detector import (
    PATTERNS,
    PLAN_EXECUTION_CONTEXT,
    PLAN_EXECUTION_PREFIXES,
    check_plan_execution_prompt,
    detect_validation,
    is_trivial_request,
)

HOOK_PATH = Path(__file__).parent.parent.parent.parent / "plugins/oh-my-claude/hooks/ultrawork_detector.py"


def run_hook(input_data: dict, marker_dir: Path) -> dict:
    """Run the hook with given input and return parsed output."""
    env = {
        "HOME": str(marker_dir),
        "PATH": "/usr/bin:/bin",
    }
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        pytest.fail(f"Hook failed: {result.stderr}")

    if not result.stdout.strip():
        return {}

    return json.loads(result.stdout)


def get_context(output: dict) -> str:
    """Extract additionalContext from hook output."""
    return output.get("hookSpecificOutput", {}).get("additionalContext", "")


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
            ("ultraresearch", "ulr best practices", True),
            ("ultrawork", "ulr best practices", False),
            ("ultradebug", "uld the issue", True),
            ("ultrawork", "uld the issue", False),
        ]
        for pattern_name, text, should_match in test_cases:
            match = PATTERNS.match(pattern_name, text)
            if should_match:
                assert match is not None, f"{pattern_name} should match '{text}'"
            else:
                assert match is None, f"{pattern_name} should NOT match '{text}'"


class TestIsTrivialRequest:
    """Tests for is_trivial_request function.

    The new conservative approach:
    - Returns True ONLY if prompt starts with trivial pattern AND has NO action verbs
    - We'd rather overwork than underwork
    """

    @pytest.mark.parametrize(
        "prompt",
        [
            # Simple questions matching TRIVIAL_PATTERNS without action verbs
            "what is this?",
            "what does this mean?",
            "what are the options?",
            "what was the error?",
            "what were the results?",
            "how do I use this?",
            "how do I run it?",
            "explain the architecture",
            "explain this code",
            "show me the errors",
            "show me the config",
            "where is the config?",
            "where are the tests?",
            "where do I start?",
            "where does this go?",
        ],
    )
    def test_trivial_requests_match(self, prompt):
        """Simple questions without action verbs should return True."""
        assert is_trivial_request(prompt) is True, f"Should be trivial: '{prompt}'"

    @pytest.mark.parametrize(
        "prompt",
        [
            # Questions with action verbs - NOT trivial
            "what is broken and fix it",
            "what needs to be implemented?",
            "what should I refactor?",
            "explain and then update the code",
            "show me what to fix",
            "where is the bug I need to fix?",
            # Prompts starting with action verbs - NOT trivial
            "fix the bug",
            "implement the feature",
            "refactor this module",
            "update all the imports",
            "change the database schema",
            "modify the configuration",
            "rewrite the parser",
            "create a new class",
            "add validation to the form",
            "build the component",
            "write unit tests",
            "develop the API",
            "make a new service",
            "configure the CI pipeline",
            "integrate the payment system",
            "migrate to the new API",
            "set up the database",
            # Questions that don't match trivial patterns
            "why does this fail?",
            "how does this work?",  # "how does" not "how do I"
            "when should I use this?",
            "who wrote this?",
            "which file handles auth?",
            "can you explain this?",
            "is this correct?",
            "does this make sense?",
            "list the files",
            "run the tests",
        ],
    )
    def test_non_trivial_requests(self, prompt):
        """Prompts with action verbs or non-trivial patterns should return False."""
        assert is_trivial_request(prompt) is False, f"Should NOT be trivial: '{prompt}'"

    def test_empty_string(self):
        """Empty string should return False."""
        assert is_trivial_request("") is False

    def test_whitespace_only(self):
        """Whitespace-only string should return False."""
        assert is_trivial_request("   ") is False

    @pytest.mark.parametrize(
        "prompt",
        [
            "ulw what is this?",
            "ultrawork what is this?",
            "ulw explain the code",
            "ultrawork show me the errors",
        ],
    )
    def test_ultrawork_prefix_stripped(self, prompt):
        """Ultrawork prefix should be stripped before matching."""
        assert is_trivial_request(prompt) is True, f"Should be trivial after prefix strip: '{prompt}'"

    @pytest.mark.parametrize(
        "prompt",
        [
            "ulw implement the feature",
            "ultrawork fix all the bugs",
            "ulw refactor the entire system",
            "ultrawork create a new service",
            "ulw what is broken and fix it",  # Has "fix" action verb
        ],
    )
    def test_ultrawork_prefix_with_action_verb(self, prompt):
        """Prompts with action verbs should return False even with ultrawork prefix."""
        assert is_trivial_request(prompt) is False, f"Should NOT be trivial: '{prompt}'"

    @pytest.mark.parametrize(
        "prompt",
        [
            "WHAT is this?",
            "What Is This?",
            "Explain the architecture",
            "EXPLAIN THE ARCHITECTURE",
            "SHOW ME the errors",
            "WHERE is the config?",
        ],
    )
    def test_case_insensitivity(self, prompt):
        """Matching should be case insensitive."""
        assert is_trivial_request(prompt) is True, f"Should be trivial (case insensitive): '{prompt}'"

    @pytest.mark.parametrize(
        "prompt",
        [
            "IMPLEMENT the feature",
            "FIX all the bugs",
            "Refactor The Module",
            "CREATE A NEW CLASS",
            "What is broken and FIX it",
        ],
    )
    def test_case_insensitivity_action_verbs(self, prompt):
        """Action verb detection should also be case insensitive."""
        assert is_trivial_request(prompt) is False, f"Should NOT be trivial: '{prompt}'"


# =============================================================================
# Plan Execution Prompt Detection Tests
# =============================================================================

@pytest.fixture
def test_home(tmp_path):
    """Create a temporary home directory for tests."""
    claude_dir = tmp_path / ".claude" / "plans"
    claude_dir.mkdir(parents=True)
    return tmp_path


class TestPlanExecutionPromptDetection:
    """Tests for plan execution detection via prompt prefix."""

    def test_exact_prefix_detected(self, test_home):
        """Prompt starting with exact prefix should inject plan context."""
        output = run_hook(
            {"prompt": "Implement the following plan:\n\n## Plan content", "session_id": "test"},
            test_home,
        )
        context = get_context(output)
        assert "ULTRAWORK MODE ACTIVE" in context
        assert "PLAN EXECUTION" in context
        assert "Create tasks" in context

    def test_prefix_with_leading_whitespace(self, test_home):
        """Leading whitespace should be stripped."""
        output = run_hook(
            {"prompt": "  Implement the following plan:\n...", "session_id": "test"},
            test_home,
        )
        context = get_context(output)
        assert "PLAN EXECUTION" in context

    def test_new_prefix_detected(self, test_home):
        """New v2.1.20 prefix should inject plan context."""
        output = run_hook(
            {"prompt": "Plan to implement\n\n## Plan content", "session_id": "test"},
            test_home,
        )
        context = get_context(output)
        assert "ULTRAWORK MODE ACTIVE" in context
        assert "PLAN EXECUTION" in context
        assert "Create tasks" in context

    def test_similar_but_different_prefix_not_detected(self, test_home):
        """User typing similar text should NOT trigger plan execution."""
        output = run_hook(
            {"prompt": "implement following plan for the feature", "session_id": "test"},
            test_home,
        )
        context = get_context(output)
        assert "PLAN EXECUTION" not in context

    def test_case_sensitive_prefix(self, test_home):
        """Prefix detection should be case-sensitive."""
        output = run_hook(
            {"prompt": "implement the following plan:", "session_id": "test"},
            test_home,
        )
        context = get_context(output)
        assert "PLAN EXECUTION" not in context

    def test_empty_prompt_no_crash(self, test_home):
        """Empty prompt should not crash."""
        output = run_hook({"prompt": "", "session_id": "test"}, test_home)
        context = get_context(output)
        assert "PLAN EXECUTION" not in context

    def test_prefix_priority_over_ultrawork_keyword(self, test_home):
        """Plan execution prefix should take priority over ultrawork keyword."""
        output = run_hook(
            {"prompt": "Implement the following plan:\n\nultrawork fix bugs", "session_id": "test"},
            test_home,
        )
        context = get_context(output)
        # Should get PLAN_EXECUTION context, not generic ULTRAWORK context
        assert "PLAN EXECUTION" in context
        assert "Create tasks" in context

    def test_no_prefix_normal_ultrawork_behavior(self, test_home):
        """Without prefix, ultrawork keyword should inject generic ultrawork context."""
        output = run_hook(
            {"prompt": "ultrawork fix bugs", "session_id": "test"},
            test_home,
        )
        context = get_context(output)
        assert "ULTRAWORK MODE ACTIVE" in context
        # Should get generic ultrawork content (not plan execution)
        assert "CERTAINTY PROTOCOL" in context
        assert "PLAN EXECUTION" not in context

    def test_context_includes_execution_protocol(self, test_home):
        """Injected context should include execution protocol."""
        output = run_hook(
            {"prompt": "Implement the following plan:\n\n## Steps", "session_id": "test"},
            test_home,
        )
        context = get_context(output)
        assert "Create tasks" in context
        assert "Execute in order" in context
        assert "Verify each step" in context

    def test_context_includes_compliance_rules(self, test_home):
        """Injected context should include plan compliance rules."""
        output = run_hook(
            {"prompt": "Implement the following plan:\n\n## Rules", "session_id": "test"},
            test_home,
        )
        context = get_context(output)
        assert "Allowed" in context
        assert "NOT Allowed" in context


class TestCheckPlanExecutionPromptFunction:
    """Unit tests for check_plan_execution_prompt function directly."""

    def test_returns_true_for_exact_prefix(self):
        """Should return True for exact prefix match."""
        assert check_plan_execution_prompt("Implement the following plan:\n\nContent") is True

    def test_returns_true_with_leading_whitespace(self):
        """Should return True when prefix has leading whitespace."""
        assert check_plan_execution_prompt("  Implement the following plan:\nContent") is True
        assert check_plan_execution_prompt("\nImplement the following plan:") is True

    def test_returns_false_for_different_text(self):
        """Should return False for similar but different text."""
        assert check_plan_execution_prompt("implement the following plan:") is False
        assert check_plan_execution_prompt("Implement following plan:") is False
        assert check_plan_execution_prompt("Please implement the following plan:") is False

    def test_returns_false_for_empty_string(self):
        """Should return False for empty string."""
        assert check_plan_execution_prompt("") is False

    def test_returns_false_for_none(self):
        """Should return False for None input."""
        assert check_plan_execution_prompt(None) is False

    def test_prefix_constant_value(self):
        """Verify the prefixes tuple has expected values."""
        assert isinstance(PLAN_EXECUTION_PREFIXES, tuple)
        assert "Implement the following plan:" in PLAN_EXECUTION_PREFIXES
        assert "Plan to implement" in PLAN_EXECUTION_PREFIXES

    def test_new_prefix_detected(self):
        """New v2.1.20 prefix should return True."""
        assert check_plan_execution_prompt("Plan to implement\n\nContent") is True

    def test_new_prefix_with_whitespace(self):
        """New prefix with leading whitespace should return True."""
        assert check_plan_execution_prompt("  Plan to implement\nContent") is True

    def test_both_prefixes_independently_trigger(self):
        """Both old and new prefixes should independently trigger detection."""
        assert check_plan_execution_prompt("Implement the following plan:\n\nContent") is True
        assert check_plan_execution_prompt("Plan to implement\n\nContent") is True
