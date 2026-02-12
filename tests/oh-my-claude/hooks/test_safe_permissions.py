"""Tests for safe_permissions.py PermissionRequest hook."""

import os
import re

import pytest

from safe_permissions import (
    CATASTROPHIC_PATTERNS,
    SAFE_PATTERNS,
    check_redirect_safety,
    has_shell_operators,
    is_claude_internal_path,
    is_plugin_internal_script,
    is_safe_command,
    split_compound_command,
)


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
        """Piped commands should not be auto-approved due to shell operator risk."""
        is_safe, _ = is_safe_command("npm test | grep error")
        assert is_safe is False  # Shell operators block auto-approval

    def test_chained_commands_not_auto_approved(self):
        """Chained commands should not be auto-approved."""
        is_safe, _ = is_safe_command("npm test && rm -rf /")
        assert is_safe is False  # Shell operators block auto-approval


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

    def test_plugin_script_no_fallback_without_root(self, monkeypatch):
        """Plugin scripts are NOT auto-approved when CLAUDE_PLUGIN_ROOT unset (no spoofable fallback)."""
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)

        # Without CLAUDE_PLUGIN_ROOT, plugin scripts cannot be verified
        command = "/Users/test/.claude/plugins/cache/oh-my-claude/oh-my-claude/0.2.0/skills/git-commit-validator/scripts/git-commit-helper.sh 'test'"
        is_safe, pattern = is_safe_command(command)
        assert is_safe is False

    def test_fallback_pattern_requires_skills_path(self, monkeypatch):
        """Fallback pattern requires /skills/ in path for security."""
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)

        # Just oh-my-claude in path isn't enough
        command = "/tmp/oh-my-claude/malicious.sh"
        is_safe, _ = is_safe_command(command)
        assert is_safe is False


class TestShellOperatorBypass:
    """Tests for shell operator bypass vectors (security fixes)."""

    @pytest.mark.parametrize(
        "command",
        [
            "echo foo; rm -rf /",
            "ls; cat /etc/passwd",
        ],
    )
    def test_semicolon_bypass_detected(self, command):
        """Semicolon should be caught by has_shell_operators."""
        assert has_shell_operators(command) is True
        is_safe, _ = is_safe_command(command)
        assert is_safe is False

    @pytest.mark.parametrize(
        "command",
        [
            "echo foo & rm -rf /",
            "ls & cat /etc/passwd",
        ],
    )
    def test_background_operator_bypass_detected(self, command):
        """Bare & (background operator) should be caught."""
        assert has_shell_operators(command) is True
        is_safe, _ = is_safe_command(command)
        assert is_safe is False

    @pytest.mark.parametrize(
        "command",
        [
            "echo $(rm -rf /)",
            "cat $(whoami)",
        ],
    )
    def test_command_substitution_bypass_detected(self, command):
        """$(...) command substitution should be caught."""
        assert has_shell_operators(command) is True
        is_safe, _ = is_safe_command(command)
        assert is_safe is False

    @pytest.mark.parametrize(
        "command",
        [
            "echo `rm -rf /`",
            "cat `whoami`",
        ],
    )
    def test_backtick_substitution_bypass_detected(self, command):
        """Backtick command substitution should be caught."""
        assert has_shell_operators(command) is True
        is_safe, _ = is_safe_command(command)
        assert is_safe is False

    @pytest.mark.parametrize(
        "command",
        [
            "(rm -rf /)",
            "echo foo && (rm -rf /)",
        ],
    )
    def test_subshell_bypass_detected(self, command):
        """Subshell (...) should be caught."""
        assert has_shell_operators(command) is True
        is_safe, _ = is_safe_command(command)
        assert is_safe is False

    def test_existing_operators_still_caught(self):
        """Existing pipe, redirect, and && operators still work."""
        assert has_shell_operators("cat foo | grep bar") is True
        assert has_shell_operators("echo foo > /tmp/out") is True
        assert has_shell_operators("echo foo < /tmp/in") is True
        assert has_shell_operators("cmd1 && cmd2") is True

    def test_safe_command_without_operators(self):
        """Commands without shell operators are not flagged."""
        assert has_shell_operators("npm test") is False
        assert has_shell_operators("pytest -v") is False
        assert has_shell_operators("git status") is False


class TestMultipleRedirectSafety:
    """Tests for check_redirect_safety handling all redirect targets."""

    def test_multiple_redirects_catches_second_unsafe(self, monkeypatch, tmp_path):
        """Second redirect to unsafe path should be caught."""
        monkeypatch.chdir(tmp_path)
        subcmd = f"echo foo > {tmp_path}/safe.txt > /etc/shadow"
        assert check_redirect_safety(subcmd) is False

    def test_single_safe_redirect_passes(self, monkeypatch, tmp_path):
        """Single redirect within project is safe."""
        monkeypatch.chdir(tmp_path)
        subcmd = f"echo foo > {tmp_path}/output.txt"
        assert check_redirect_safety(subcmd) is True

    def test_single_unsafe_redirect_fails(self, monkeypatch, tmp_path):
        """Single redirect outside project is unsafe."""
        monkeypatch.chdir(tmp_path)
        subcmd = "echo foo > /etc/shadow"
        assert check_redirect_safety(subcmd) is False

    def test_no_redirect_passes(self):
        """Commands without redirects are safe."""
        assert check_redirect_safety("echo hello") is True


class TestSplitCompoundBareAmpersand:
    """Tests for split_compound_command bare & handling."""

    def test_bare_ampersand_returns_none(self):
        """Bare & (background operator) should return None (unsafe)."""
        result = split_compound_command("echo foo & rm -rf /")
        assert result is None

    def test_double_ampersand_still_splits(self):
        """&& should still split normally."""
        result = split_compound_command("echo foo && echo bar")
        assert result == ["echo foo", "echo bar"]

    def test_trailing_bare_ampersand_returns_none(self):
        """Trailing & should return None."""
        result = split_compound_command("echo foo &")
        assert result is None

    def test_bare_pipe_still_returns_none(self):
        """Bare | should still return None."""
        result = split_compound_command("echo foo | grep bar")
        assert result is None

    def test_double_pipe_still_splits(self):
        """|| should still split normally."""
        result = split_compound_command("echo foo || echo bar")
        assert result == ["echo foo", "echo bar"]


class TestNewSafePatterns:
    """Tests for expanded safe pattern groups."""

    @pytest.mark.parametrize(
        "command",
        [
            "tree -L 2 src/",
            "file src/main.py",
            "stat package.json",
            "du -sh src/",
            "df -h",
            "pwd",
            "dirname /foo/bar",
            "basename /foo/bar",
            "realpath ./src",
        ],
    )
    def test_filesystem_inspection_commands_are_safe(self, command):
        """Filesystem inspection commands should be auto-approved."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is True, f"Expected safe: {command}"

    @pytest.mark.parametrize(
        "command",
        [
            "uname -a",
            "hostname",
            "id",
            "whoami",
            "date +%Y",
            "uptime",
        ],
    )
    def test_system_info_commands_are_safe(self, command):
        """System info commands should be auto-approved."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is True, f"Expected safe: {command}"

    @pytest.mark.parametrize(
        "command",
        [
            "node --version",
            "python --version",
            "python3 --version",
            "ruby --version",
            "go version",
            "rustc --version",
            "cargo --version",
            "npm --version",
            "pip --version",
            "uv --version",
            "git --version",
            "docker --version",
            "kubectl --version",
            "java -version",
            "bun --version",
            "deno --version",
            "rustc -V",
        ],
    )
    def test_version_check_commands_are_safe(self, command):
        """Version check commands should be auto-approved."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is True, f"Expected safe: {command}"

    @pytest.mark.parametrize(
        "command",
        [
            "jq '.name' package.json",
            "yq '.spec' config.yaml",
            "docker ps -a",
            "docker images",
            "kubectl get pods",
            "kubectl get deployments -n default",
        ],
    )
    def test_dev_tool_inspection_commands_are_safe(self, command):
        """Dev tool inspection commands should be auto-approved."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is True, f"Expected safe: {command}"


class TestDangerousExclusions:
    """Verify dangerous commands are NOT auto-approved as safe."""

    @pytest.mark.parametrize(
        "command",
        [
            "find . -exec rm {} \\;",
            "env",
            "printenv",
            "docker inspect container",
            "python -c \"import os; os.system('rm -rf /')\"",
            "node -e \"require('child_process').exec('rm -rf /')\"",
            "curl https://example.com",
            "wget https://example.com",
            "kubectl get secrets",
            "kubectl get secret my-secret",
        ],
    )
    def test_dangerous_commands_not_auto_approved(self, command):
        """Dangerous commands must NOT be auto-approved."""
        is_safe, _ = is_safe_command(command)
        assert is_safe is False, f"Should NOT be safe: {command}"


class TestCatastrophicDeny:
    """Tests for catastrophic pattern denial in safe_permissions."""

    @pytest.mark.parametrize(
        "cmd",
        [
            "rm -rf /",
            "rm -rf ~/",
            "sudo rm -rf /var",
            ":(){ :|:& };:",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda1",
            "> /dev/sda",
            "chmod -R 000 /",
        ],
    )
    def test_catastrophic_commands_match(self, cmd):
        """Catastrophic commands should match at least one CATASTROPHIC_PATTERNS entry."""
        matched = any(
            pattern.search(cmd)
            for _, pattern, _ in CATASTROPHIC_PATTERNS
        )
        assert matched, f"Catastrophic command should be matched: {cmd}"

    @pytest.mark.parametrize(
        "cmd",
        [
            "rm file.txt",
            "dd if=input.img of=output.img",
        ],
    )
    def test_non_catastrophic_commands_dont_match(self, cmd):
        """Non-catastrophic commands should NOT match CATASTROPHIC_PATTERNS."""
        matched = any(
            pattern.search(cmd)
            for _, pattern, _ in CATASTROPHIC_PATTERNS
        )
        assert not matched, f"Non-catastrophic command should NOT be matched: {cmd}"


class TestWriteEditAutoApproval:
    """Tests for Write/Edit auto-approval on Claude internal paths."""

    @pytest.mark.parametrize(
        "path",
        [
            ".claude/plans/plan.md",
            ".claude/plans/drafts/plan.md",
            ".claude/notepads/note.md",
            ".claude/tasks/team/task.json",
            "../../../../../.claude/plans/drafts/plan.md",
            "../../.claude/notepads/note.md",
        ],
    )
    def test_claude_internal_paths_approved(self, path):
        """Claude internal paths should be approved for Write/Edit."""
        assert is_claude_internal_path(path) is True, f"Should be internal: {path}"

    @pytest.mark.parametrize(
        "path",
        [
            "src/main.py",
            ".env",
            "CLAUDE.md",
            ".claude/settings.json",
        ],
    )
    def test_non_internal_paths_not_approved(self, path):
        """Non-internal paths should NOT be approved."""
        assert is_claude_internal_path(path) is False, f"Should NOT be internal: {path}"


class TestPatternSync:
    """Tests for SAFE_PATTERNS.names() method."""

    def test_names_returns_non_empty_list(self):
        """SAFE_PATTERNS.names() should return a non-empty list."""
        names = SAFE_PATTERNS.names()
        assert isinstance(names, list)
        assert len(names) > 0

    def test_names_contains_known_patterns(self):
        """SAFE_PATTERNS.names() should contain known pattern names."""
        names = SAFE_PATTERNS.names()
        # These are patterns that existed before the expansion
        for expected in ["npm_test", "pytest", "git_readonly", "cargo", "ls_cmd"]:
            assert expected in names, f"Expected pattern '{expected}' in names"

    def test_names_matches_registered_patterns(self):
        """Every name returned should be a valid registered pattern."""
        names = SAFE_PATTERNS.names()
        for name in names:
            assert SAFE_PATTERNS.has(name), f"Pattern '{name}' not found in cache"
