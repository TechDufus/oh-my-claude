"""Tests for tdd_enforcer.py."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tdd_enforcer import (
    get_tdd_mode,
    is_source_file,
    is_test_file,
    is_excluded,
    get_test_patterns,
)


class TestGetTddMode:
    """Tests for get_tdd_mode function."""

    def test_get_tdd_mode_default_off(self):
        """Default mode is off when env var not set."""
        with patch.dict("os.environ", {}, clear=True):
            # Remove OMC_TDD_MODE if it exists
            import os
            os.environ.pop("OMC_TDD_MODE", None)
            assert get_tdd_mode() == "off"

    def test_get_tdd_mode_from_env(self):
        """Reads mode from OMC_TDD_MODE environment variable."""
        with patch.dict("os.environ", {"OMC_TDD_MODE": "guided"}):
            assert get_tdd_mode() == "guided"

        with patch.dict("os.environ", {"OMC_TDD_MODE": "enforced"}):
            assert get_tdd_mode() == "enforced"

        with patch.dict("os.environ", {"OMC_TDD_MODE": "off"}):
            assert get_tdd_mode() == "off"

    def test_get_tdd_mode_case_insensitive(self):
        """Mode should be case insensitive."""
        with patch.dict("os.environ", {"OMC_TDD_MODE": "GUIDED"}):
            assert get_tdd_mode() == "guided"

        with patch.dict("os.environ", {"OMC_TDD_MODE": "Enforced"}):
            assert get_tdd_mode() == "enforced"

    def test_get_tdd_mode_invalid_defaults_off(self):
        """Invalid value defaults to off."""
        with patch.dict("os.environ", {"OMC_TDD_MODE": "invalid"}):
            assert get_tdd_mode() == "off"

        with patch.dict("os.environ", {"OMC_TDD_MODE": "strict"}):
            assert get_tdd_mode() == "off"

        with patch.dict("os.environ", {"OMC_TDD_MODE": ""}):
            assert get_tdd_mode() == "off"


class TestIsSourceFile:
    """Tests for is_source_file function."""

    def test_is_source_file_typescript(self):
        """.ts and .tsx are source files."""
        assert is_source_file("src/component.ts") is True
        assert is_source_file("src/component.tsx") is True
        assert is_source_file("/path/to/file.ts") is True
        assert is_source_file("/path/to/file.tsx") is True

    def test_is_source_file_javascript(self):
        """.js and .jsx are source files."""
        assert is_source_file("src/component.js") is True
        assert is_source_file("src/component.jsx") is True
        assert is_source_file("/path/to/file.js") is True
        assert is_source_file("/path/to/file.jsx") is True

    def test_is_source_file_python(self):
        """.py is source file."""
        assert is_source_file("src/module.py") is True
        assert is_source_file("/path/to/script.py") is True

    def test_is_source_file_go(self):
        """.go is source file."""
        assert is_source_file("src/main.go") is True
        assert is_source_file("/path/to/handler.go") is True

    def test_is_source_file_rust(self):
        """.rs is source file."""
        assert is_source_file("src/lib.rs") is True
        assert is_source_file("/path/to/main.rs") is True

    def test_is_source_file_java(self):
        """.java is source file."""
        assert is_source_file("src/Main.java") is True
        assert is_source_file("/path/to/Service.java") is True

    def test_is_source_file_non_source(self):
        """.json, .md, and other files are not source files."""
        assert is_source_file("package.json") is False
        assert is_source_file("README.md") is False
        assert is_source_file("config.yaml") is False
        assert is_source_file("data.xml") is False
        assert is_source_file("style.css") is False
        assert is_source_file("template.html") is False

    def test_is_source_file_case_insensitive(self):
        """Extension check should be case insensitive."""
        assert is_source_file("file.TS") is True
        assert is_source_file("file.PY") is True
        assert is_source_file("file.GO") is True


class TestIsTestFile:
    """Tests for is_test_file function."""

    def test_is_test_file_test_ts(self):
        """.test.ts detected as test file."""
        assert is_test_file("component.test.ts") is True
        assert is_test_file("utils.test.tsx") is True
        assert is_test_file("helper.test.js") is True
        assert is_test_file("helper.test.jsx") is True

    def test_is_test_file_spec_ts(self):
        """.spec.ts detected as test file."""
        assert is_test_file("component.spec.ts") is True
        assert is_test_file("utils.spec.tsx") is True
        assert is_test_file("helper.spec.js") is True
        assert is_test_file("helper.spec.jsx") is True

    def test_is_test_file_python_test(self):
        """test_*.py and *_test.py detected as test files."""
        assert is_test_file("test_module.py") is True
        assert is_test_file("module_test.py") is True

    def test_is_test_file_go_test(self):
        """_test.go detected as test file."""
        assert is_test_file("handler_test.go") is True
        assert is_test_file("main_test.go") is True

    def test_is_test_file_java_test(self):
        """Test.java and Tests.java detected as test files."""
        assert is_test_file("ServiceTest.java") is True
        assert is_test_file("ServiceTests.java") is True

    def test_is_test_file_not_test(self):
        """Regular source files are not test files."""
        assert is_test_file("component.ts") is False
        assert is_test_file("module.py") is False
        assert is_test_file("handler.go") is False
        assert is_test_file("Service.java") is False

    def test_is_test_file_full_path(self):
        """Test detection works with full paths."""
        assert is_test_file("/path/to/component.test.ts") is True
        assert is_test_file("/path/to/test_module.py") is True


class TestIsExcluded:
    """Tests for is_excluded function."""

    def test_is_excluded_config(self):
        """Config files excluded."""
        assert is_excluded("jest.config.ts") is True
        assert is_excluded("eslint.config.js") is True
        assert is_excluded("vite.config.ts") is True

    def test_is_excluded_type_defs(self):
        """Type definitions excluded."""
        assert is_excluded("types.d.ts") is True
        assert is_excluded("global.d.ts") is True
        assert is_excluded("/path/to/index.d.ts") is True

    def test_is_excluded_test_dir(self):
        """__tests__/ directories excluded."""
        assert is_excluded("src/__tests__/component.ts") is True
        assert is_excluded("__tests__/utils.ts") is True

    def test_is_excluded_tests_directory(self):
        """test/ and tests/ directories excluded (requires leading slash)."""
        # Pattern is /tests?/ - requires leading slash
        assert is_excluded("/tests/unit/module.py") is True
        assert is_excluded("/test/integration/handler.go") is True
        assert is_excluded("/project/tests/test_utils.py") is True
        assert is_excluded("src/tests/utils.py") is True

    def test_is_excluded_types_directory(self):
        """types/ directories excluded."""
        assert is_excluded("src/types/user.ts") is True
        assert is_excluded("/path/types/models.ts") is True

    def test_is_excluded_types_file(self):
        """types.ts files excluded."""
        assert is_excluded("src/types.ts") is True
        assert is_excluded("/path/to/types.ts") is True

    def test_is_excluded_entry_points(self):
        """Entry point files excluded."""
        assert is_excluded("index.ts") is True
        assert is_excluded("main.ts") is True
        assert is_excluded("app.tsx") is True
        assert is_excluded("src/index.js") is True
        assert is_excluded("/path/to/main.jsx") is True

    def test_is_excluded_generated_files(self):
        """Generated files excluded."""
        assert is_excluded("schema.generated.ts") is True
        assert is_excluded("types.g.ts") is True

    def test_is_excluded_config_doc_files(self):
        """Config and doc files excluded."""
        assert is_excluded("package.json") is True
        assert is_excluded("config.yaml") is True
        assert is_excluded("settings.yml") is True
        assert is_excluded("pyproject.toml") is True
        assert is_excluded("README.md") is True

    def test_is_excluded_regular_source(self):
        """Regular source files are not excluded."""
        assert is_excluded("src/component.ts") is False
        assert is_excluded("lib/utils.py") is False
        assert is_excluded("pkg/handler.go") is False


class TestGetTestPatterns:
    """Tests for get_test_patterns function."""

    def test_get_test_patterns_typescript(self):
        """Generates correct TS/JS patterns."""
        patterns = get_test_patterns("src/component.ts")
        assert "src/component.test.ts" in patterns
        assert "src/component.spec.ts" in patterns
        assert "src/__tests__/component.ts" in patterns

    def test_get_test_patterns_tsx(self):
        """Generates correct TSX patterns."""
        patterns = get_test_patterns("src/component.tsx")
        assert "src/component.test.tsx" in patterns
        assert "src/component.spec.tsx" in patterns

    def test_get_test_patterns_javascript(self):
        """Generates correct JS patterns."""
        patterns = get_test_patterns("lib/utils.js")
        assert "lib/utils.test.js" in patterns
        assert "lib/utils.spec.js" in patterns
        assert "lib/__tests__/utils.js" in patterns

    def test_get_test_patterns_python(self):
        """Generates correct Python patterns."""
        patterns = get_test_patterns("src/module.py")
        assert "src/test_module.py" in patterns
        assert "src/module_test.py" in patterns
        # Parent tests directory pattern
        assert any("tests" in p and "test_module.py" in p for p in patterns)

    def test_get_test_patterns_go(self):
        """Generates correct Go patterns."""
        patterns = get_test_patterns("pkg/handler.go")
        assert "pkg/handler_test.go" in patterns
        assert len(patterns) == 1  # Go only has one pattern

    def test_get_test_patterns_java(self):
        """Generates correct Java patterns."""
        patterns = get_test_patterns("src/Service.java")
        assert "src/ServiceTest.java" in patterns
        assert "src/ServiceTests.java" in patterns

    def test_get_test_patterns_unsupported_extension(self):
        """Unsupported extensions return empty list."""
        patterns = get_test_patterns("config.json")
        assert patterns == []


class TestHookIntegration:
    """Integration tests for the full hook via subprocess."""

    @pytest.fixture
    def hook_path(self):
        """Path to the hook script."""
        return Path(__file__).parent.parent.parent.parent / "plugins/oh-my-claude/hooks/tdd_enforcer.py"

    def run_hook(self, hook_path, input_data, env=None):
        """Run the hook with given input and environment."""
        import os
        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            env=run_env,
        )
        return result

    def parse_output(self, stdout):
        """Parse hook output, handling empty output case."""
        if not stdout.strip():
            return {}
        return json.loads(stdout)

    def is_blocked(self, output):
        """Check if output indicates blocking."""
        hook_output = output.get("hookSpecificOutput", {})
        return hook_output.get("blocked", False)

    def test_hook_off_mode_allows_all(self, hook_path):
        """Off mode allows all edits."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/component.ts"},
        }
        result = self.run_hook(hook_path, input_data, env={"OMC_TDD_MODE": "off"})
        assert result.returncode == 0
        output = self.parse_output(result.stdout)
        assert not self.is_blocked(output)

    def test_hook_skips_non_edit_tools(self, hook_path):
        """Non-Edit/Write tools pass through."""
        input_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "src/component.ts"},
        }
        result = self.run_hook(hook_path, input_data, env={"OMC_TDD_MODE": "enforced"})
        assert result.returncode == 0
        output = self.parse_output(result.stdout)
        assert not self.is_blocked(output)

    def test_hook_skips_bash_tool(self, hook_path):
        """Bash tool passes through."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        }
        result = self.run_hook(hook_path, input_data, env={"OMC_TDD_MODE": "enforced"})
        assert result.returncode == 0
        output = self.parse_output(result.stdout)
        assert not self.is_blocked(output)

    def test_hook_allows_test_file_edits(self, hook_path):
        """Test files can always be edited."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/component.test.ts"},
        }
        result = self.run_hook(hook_path, input_data, env={"OMC_TDD_MODE": "enforced"})
        assert result.returncode == 0
        output = self.parse_output(result.stdout)
        assert not self.is_blocked(output)

    def test_hook_allows_excluded_files(self, hook_path):
        """Excluded files can be edited."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/index.ts"},
        }
        result = self.run_hook(hook_path, input_data, env={"OMC_TDD_MODE": "enforced"})
        assert result.returncode == 0
        output = self.parse_output(result.stdout)
        assert not self.is_blocked(output)

    def test_hook_allows_non_source_files(self, hook_path):
        """Non-source files can be edited."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "package.json"},
        }
        result = self.run_hook(hook_path, input_data, env={"OMC_TDD_MODE": "enforced"})
        assert result.returncode == 0
        output = self.parse_output(result.stdout)
        assert not self.is_blocked(output)

    def test_hook_empty_input(self, hook_path):
        """Empty input returns empty output."""
        result = self.run_hook(hook_path, {}, env={"OMC_TDD_MODE": "enforced"})
        assert result.returncode == 0
        output = self.parse_output(result.stdout)
        assert not self.is_blocked(output)

    def test_hook_missing_file_path(self, hook_path):
        """Missing file_path returns empty output."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {},
        }
        result = self.run_hook(hook_path, input_data, env={"OMC_TDD_MODE": "enforced"})
        assert result.returncode == 0
        output = self.parse_output(result.stdout)
        assert not self.is_blocked(output)

    def test_hook_guided_mode_adds_context(self, hook_path, tmp_path):
        """Guided mode adds context message for missing tests."""
        # Create a source file without corresponding test
        source_file = tmp_path / "component.ts"
        source_file.write_text("export const foo = 1;")

        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(source_file)},
            "cwd": str(tmp_path),
        }
        result = self.run_hook(hook_path, input_data, env={"OMC_TDD_MODE": "guided"})
        assert result.returncode == 0
        output = self.parse_output(result.stdout)
        # Guided mode should add context, not block
        assert not self.is_blocked(output)

    def test_hook_enforced_mode_blocks(self, hook_path, tmp_path):
        """Enforced mode blocks edits without tests."""
        # Create a source file without corresponding test
        source_file = tmp_path / "component.ts"
        source_file.write_text("export const foo = 1;")

        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(source_file)},
            "cwd": str(tmp_path),
        }
        result = self.run_hook(hook_path, input_data, env={"OMC_TDD_MODE": "enforced"})
        assert result.returncode == 0
        output = self.parse_output(result.stdout)
        assert self.is_blocked(output)
        hook_output = output.get("hookSpecificOutput", {})
        assert "TDD" in hook_output.get("reason", "")

    def test_hook_allows_edit_when_test_exists(self, hook_path, tmp_path):
        """Edit allowed when corresponding test file exists."""
        # Create source and test files
        source_file = tmp_path / "component.ts"
        source_file.write_text("export const foo = 1;")
        test_file = tmp_path / "component.test.ts"
        test_file.write_text("test('foo', () => {});")

        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(source_file)},
            "cwd": str(tmp_path),
        }
        result = self.run_hook(hook_path, input_data, env={"OMC_TDD_MODE": "enforced"})
        assert result.returncode == 0
        output = self.parse_output(result.stdout)
        assert not self.is_blocked(output)

    def test_hook_write_tool_also_checked(self, hook_path, tmp_path):
        """Write tool is also subject to TDD enforcement."""
        # Create a path without test
        source_path = tmp_path / "newfile.ts"

        input_data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(source_path)},
            "cwd": str(tmp_path),
        }
        result = self.run_hook(hook_path, input_data, env={"OMC_TDD_MODE": "enforced"})
        assert result.returncode == 0
        output = self.parse_output(result.stdout)
        assert self.is_blocked(output)
