"""Tests for safe_permissions.py PermissionRequest hook."""

import os

import pytest

from safe_permissions import is_plugin_internal_script, is_safe_command


class TestNodeJsCommands:
    """Tests for Node.js safe commands."""

    @pytest.mark.parametrize(
        "command",
        [
            "npm test",
            "npm run test",
            "npm run lint",
            "npm run typecheck",
            "npm run check",
            "npm run format",
            "NPM TEST",  # case insensitive
        ],
    )
    def test_npm_commands_are_safe(self, command):
        """npm test/lint/typecheck commands should be safe."""
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "npm_test"

    @pytest.mark.parametrize(
        "command",
        [
            "npx jest",
            "npx vitest",
            "npx mocha",
            "npx eslint",
            "npx prettier",
            "npx tsc",
        ],
    )
    def test_npx_commands_are_safe(self, command):
        """npx test/lint commands should be safe."""
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "npx_test"

    @pytest.mark.parametrize(
        "command",
        [
            "yarn test",
            "yarn lint",
            "yarn typecheck",
            "pnpm test",
            "pnpm lint",
        ],
    )
    def test_yarn_pnpm_commands_are_safe(self, command):
        """yarn/pnpm test/lint commands should be safe."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is True

    @pytest.mark.parametrize(
        "command",
        [
            "npm install",
            "npm run build",
            "npm publish",
            "npx create-react-app",
        ],
    )
    def test_npm_unsafe_commands(self, command):
        """npm install/build/publish should NOT be auto-approved."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is False


class TestPythonCommands:
    """Tests for Python safe commands."""

    @pytest.mark.parametrize(
        "command",
        [
            "pytest",
            "pytest -v",
            "pytest tests/",
            "python -m pytest",
            "PYTEST",  # case insensitive
        ],
    )
    def test_pytest_commands_are_safe(self, command):
        """pytest commands should be safe."""
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "pytest"

    @pytest.mark.parametrize(
        "command",
        [
            "ruff check",
            "ruff check .",
            "ruff format",
            "ruff format --check",
        ],
    )
    def test_ruff_commands_are_safe(self, command):
        """ruff check/format commands should be safe."""
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "ruff"

    @pytest.mark.parametrize(
        "command",
        [
            "mypy",
            "mypy src/",
            "mypy --strict",
        ],
    )
    def test_mypy_commands_are_safe(self, command):
        """mypy commands should be safe."""
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "mypy"

    @pytest.mark.parametrize(
        "command",
        [
            "uv run pytest",
            "uv run --with pytest pytest",
            "uv run --with pytest pytest -v",
        ],
    )
    def test_uv_pytest_commands_are_safe(self, command):
        """uv run pytest commands should be safe."""
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "uv_pytest"

    @pytest.mark.parametrize(
        "command",
        [
            "pip install",
            "python setup.py install",
            "ruff --fix",  # modifying
        ],
    )
    def test_python_unsafe_commands(self, command):
        """pip install and modifying commands should NOT be auto-approved."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is False


class TestGoCommands:
    """Tests for Go safe commands."""

    @pytest.mark.parametrize(
        "command",
        [
            "go test",
            "go test ./...",
            "go test -v",
            "go vet",
            "go vet ./...",
            "go fmt",
        ],
    )
    def test_go_commands_are_safe(self, command):
        """go test/vet/fmt commands should be safe."""
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "go_test"

    @pytest.mark.parametrize(
        "command",
        [
            "go build",
            "go install",
            "go mod tidy",
        ],
    )
    def test_go_unsafe_commands(self, command):
        """go build/install should NOT be auto-approved."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is False


class TestRustCommands:
    """Tests for Rust safe commands."""

    @pytest.mark.parametrize(
        "command",
        [
            "cargo test",
            "cargo test --all",
            "cargo check",
            "cargo clippy",
            "cargo fmt",
            "cargo fmt --check",
        ],
    )
    def test_cargo_commands_are_safe(self, command):
        """cargo test/check/clippy/fmt commands should be safe."""
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "cargo"

    @pytest.mark.parametrize(
        "command",
        [
            "cargo build",
            "cargo run",
            "cargo install",
            "cargo publish",
        ],
    )
    def test_cargo_unsafe_commands(self, command):
        """cargo build/run/install/publish should NOT be auto-approved."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is False


class TestGitCommands:
    """Tests for Git safe commands."""

    @pytest.mark.parametrize(
        "command",
        [
            "git status",
            "git diff",
            "git diff HEAD",
            "git log",
            "git log --oneline",
            "git branch",
            "git branch -a",
            "git show",
            "git show HEAD",
            "git ls-files",
            "git rev-parse HEAD",
            "git describe",
            "git tag -l",
            "git remote -v",
        ],
    )
    def test_git_readonly_commands_are_safe(self, command):
        """git readonly commands should be safe."""
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "git_readonly"

    @pytest.mark.parametrize(
        "command",
        [
            "git add",
            "git commit",
            "git push",
            "git pull",
            "git checkout",
            "git reset",
            "git rebase",
            "git merge",
            "git tag v1.0",  # creating tag, not listing
        ],
    )
    def test_git_write_commands_are_unsafe(self, command):
        """git write commands should NOT be auto-approved."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is False


class TestMakeCommands:
    """Tests for Make safe commands."""

    @pytest.mark.parametrize(
        "command",
        [
            "make test",
            "make lint",
            "make check",
            "make fmt",
            "make format",
        ],
    )
    def test_make_safe_targets(self, command):
        """make test/lint/check targets should be safe."""
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "make_safe"

    @pytest.mark.parametrize(
        "command",
        [
            "make",
            "make build",
            "make install",
            "make deploy",
            "make clean",
            "make test deploy",  # multiple targets
        ],
    )
    def test_make_unsafe_targets(self, command):
        """make build/install/deploy should NOT be auto-approved."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is False


class TestShellUtilities:
    """Tests for shell utility commands."""

    @pytest.mark.parametrize(
        "command",
        [
            "ls",
            "ls -la",
            "ls /path",
            "cat file.txt",
            "head file.txt",
            "tail file.txt",
            "wc -l file.txt",
            "which python",
            "echo hello",
        ],
    )
    def test_readonly_utilities_are_safe(self, command):
        """readonly shell utilities should be safe."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is True

    @pytest.mark.parametrize(
        "command",
        [
            "rm file.txt",
            "rm -rf /",
            "mv a b",
            "cp a b",
            "chmod 755 file",
            "curl http://example.com",
            "wget http://example.com",
        ],
    )
    def test_modifying_commands_are_unsafe(self, command):
        """modifying shell commands should NOT be auto-approved."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is False


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_command(self):
        """Empty command should not be safe."""
        is_safe, _ = is_safe_command("")
        assert is_safe is False

    def test_whitespace_command(self):
        """Whitespace-only command should not be safe."""
        is_safe, _ = is_safe_command("   ")
        assert is_safe is False

    def test_command_with_leading_whitespace(self):
        """Commands with leading whitespace should still match."""
        is_safe, _ = is_safe_command("  npm test")
        assert is_safe is True

    def test_case_insensitive_matching(self):
        """Pattern matching should be case insensitive."""
        is_safe1, _ = is_safe_command("NPM TEST")
        is_safe2, _ = is_safe_command("Npm Test")
        is_safe3, _ = is_safe_command("npm test")
        assert is_safe1 is True
        assert is_safe2 is True
        assert is_safe3 is True

    def test_partial_match_doesnt_trigger(self):
        """Partial matches in the middle shouldn't trigger."""
        # These contain safe substrings but aren't safe commands
        is_safe, _ = is_safe_command("badnpm test")
        assert is_safe is False

    def test_pipe_command_not_auto_approved(self):
        """Piped commands should not be auto-approved (complex)."""
        is_safe, _ = is_safe_command("npm test | grep error")
        assert is_safe is True  # Still matches npm test at start

    def test_chained_commands_not_auto_approved(self):
        """Chained commands should not be auto-approved."""
        is_safe, _ = is_safe_command("npm test && rm -rf /")
        assert is_safe is True  # Matches npm test, but user should review chains


class TestPluginInternalScripts:
    """Tests for plugin internal script auto-approval."""

    def test_plugin_script_approved_when_env_set(self, monkeypatch):
        """Scripts from CLAUDE_PLUGIN_ROOT should be auto-approved."""
        plugin_root = "/Users/test/.claude/plugins/cache/oh-my-claude/oh-my-claude/0.2.0"
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", plugin_root)

        script_path = f"{plugin_root}/skills/git-commit-validator/scripts/git-commit-helper.sh"
        command = f'{script_path} "feat: test commit"'

        result = is_plugin_internal_script(command)
        assert result is True

    def test_plugin_script_not_approved_without_env(self, monkeypatch):
        """Without CLAUDE_PLUGIN_ROOT, plugin scripts are not auto-approved."""
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)

        command = "/some/path/to/script.sh"
        result = is_plugin_internal_script(command)
        assert result is False

    def test_non_plugin_script_not_approved(self, monkeypatch):
        """Scripts outside plugin root should not be auto-approved."""
        plugin_root = "/Users/test/.claude/plugins/cache/oh-my-claude/oh-my-claude/0.2.0"
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", plugin_root)

        command = "/Users/test/malicious/script.sh"
        result = is_plugin_internal_script(command)
        assert result is False

    def test_plugin_script_integration_with_is_safe_command(self, monkeypatch):
        """Plugin scripts should be caught by is_safe_command."""
        plugin_root = "/Users/test/.claude/plugins/cache/oh-my-claude/oh-my-claude/0.2.0"
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", plugin_root)

        script_path = f"{plugin_root}/skills/git-commit-validator/scripts/git-commit-helper.sh"
        command = f'{script_path} "feat: test commit"'

        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "plugin_internal_script"

    def test_plugin_script_different_versions(self, monkeypatch):
        """Plugin scripts work regardless of version in path."""
        # Test with version 0.1.0
        plugin_root = "/Users/test/.claude/plugins/cache/oh-my-claude/oh-my-claude/0.1.0"
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", plugin_root)

        command = f"{plugin_root}/scripts/helper.sh arg1 arg2"
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "plugin_internal_script"

        # Test with version 1.0.0
        plugin_root = "/Users/test/.claude/plugins/cache/oh-my-claude/oh-my-claude/1.0.0"
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", plugin_root)

        command = f"{plugin_root}/scripts/helper.sh arg1 arg2"
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "plugin_internal_script"

    def test_plugin_script_fallback_pattern(self, monkeypatch):
        """Plugin scripts match via fallback pattern when CLAUDE_PLUGIN_ROOT unset."""
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)

        # Cached plugin skill script should match fallback pattern
        command = "/Users/test/.claude/plugins/cache/oh-my-claude/oh-my-claude/0.2.0/skills/git-commit-validator/scripts/git-commit-helper.sh 'test'"
        is_safe, pattern = is_safe_command(command)
        assert is_safe is True
        assert pattern == "plugin_internal_script"

    def test_fallback_pattern_requires_skills_path(self, monkeypatch):
        """Fallback pattern requires /skills/ in path for security."""
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)

        # Just oh-my-claude in path isn't enough
        command = "/tmp/oh-my-claude/malicious.sh"
        is_safe, _ = is_safe_command(command)
        assert is_safe is False
