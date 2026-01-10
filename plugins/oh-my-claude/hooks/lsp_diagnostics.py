#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
lsp_diagnostics.py
PostToolUse hook: Runs language-specific diagnostics after Edit/Write operations
Provides immediate feedback on code quality issues
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], cwd: str | None = None) -> str:
    """Run a command and return stdout+stderr, or empty string on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        return (result.stdout + result.stderr).strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def find_project_root(start_path: str, marker_files: list[str]) -> str | None:
    """Walk up from start_path looking for a directory containing any marker file."""
    current = Path(start_path).parent
    while current != current.parent:
        for marker in marker_files:
            if (current / marker).exists() or list(current.glob(marker)):
                return str(current)
        current = current.parent
    return None


def detect_severity(output: str, error_patterns: list[str], warning_patterns: list[str]) -> str:
    """Detect severity based on output patterns."""
    for pattern in error_patterns:
        if re.search(pattern, output):
            return "error"
    for pattern in warning_patterns:
        if re.search(pattern, output):
            return "warning"
    return "info"


# Linter configurations: maps extension(s) to linter config
# Each config is a dict with:
#   - tool: command name to check with shutil.which
#   - cmd: function that returns command list given file_path
#   - error_patterns: regex patterns indicating errors
#   - warning_patterns: regex patterns indicating warnings
#   - special: optional function for special handling (returns (output, severity) or None)

def check_shellcheck(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("shellcheck"):
        return None
    output = run_cmd(["shellcheck", "-f", "gcc", file_path])
    if not output:
        return None
    severity = detect_severity(output, [r":.*: error:"], [r":.*: warning:"])
    return output, severity


def check_typescript(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("tsc"):
        return None
    output = run_cmd(["tsc", "--noEmit", "--pretty", "false", file_path])
    if not output:
        return None
    # Ignore "Cannot find" errors (missing dependencies)
    if "error TS" in output and "Cannot find" not in output:
        return output, "error"
    if output:
        return output, "warning"
    return None


def check_eslint(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("eslint"):
        return None
    output = run_cmd(["eslint", "--format", "compact", file_path])
    if not output:
        return None
    severity = detect_severity(output, [r" Error -"], [r" Warning -"])
    return output, severity


def check_python(file_path: str) -> tuple[str, str] | None:
    # Prefer ruff (fast), fall back to pyright
    if shutil.which("ruff"):
        output = run_cmd(["ruff", "check", "--output-format=concise", file_path])
        if output:
            return output, "warning"
        return None
    if shutil.which("pyright"):
        raw = run_cmd(["pyright", "--outputjson", file_path])
        if raw:
            try:
                data = json.loads(raw)
                diagnostics = data.get("generalDiagnostics", [])
                lines = []
                for d in diagnostics:
                    line = d.get("range", {}).get("start", {}).get("line", 0)
                    sev = d.get("severity", "info")
                    msg = d.get("message", "")
                    lines.append(f"{file_path}:{line}: {sev}: {msg}")
                output = "\n".join(lines)
                if output:
                    severity = "error" if ": error:" in output else "warning"
                    return output, severity
            except json.JSONDecodeError:
                pass
    return None


def check_go(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("go"):
        return None
    output = run_cmd(["go", "vet", file_path])
    if output:
        return output, "warning"
    return None


def check_rust(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("cargo"):
        return None
    cargo_dir = find_project_root(file_path, ["Cargo.toml"])
    if not cargo_dir:
        return None
    output = run_cmd(["cargo", "check", "--message-format=short"], cwd=cargo_dir)
    if not output:
        return None
    # Limit to 20 lines
    lines = output.split("\n")[:20]
    output = "\n".join(lines)
    severity = detect_severity(output, [r"^error"], [r"^warning"])
    return output, severity


def check_json(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("jq"):
        return None
    output = run_cmd(["jq", "empty", file_path])
    if output:
        return output, "error"
    return None


def check_yaml(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("yamllint"):
        return None
    output = run_cmd(["yamllint", "-f", "parsable", file_path])
    if not output:
        return None
    severity = detect_severity(output, [r"\[error\]"], [r"\[warning\]"])
    return output, severity


def check_terraform(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("tflint"):
        return None
    output = run_cmd(["tflint", "--format", "compact", file_path])
    if not output:
        return None
    severity = detect_severity(output, [r"Error:"], [])
    if severity == "info":
        severity = "warning"
    return output, severity


def check_lua(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("luacheck"):
        return None
    output = run_cmd(["luacheck", "--formatter", "plain", file_path])
    if not output or "0 warnings" in output:
        return None
    severity = detect_severity(output, [r"\([EF]\d+\)"], [])
    if severity == "info":
        severity = "warning"
    return output, severity


def check_markdown(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("markdownlint"):
        return None
    output = run_cmd(["markdownlint", file_path])
    if output:
        return output, "warning"
    return None


def check_swift(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("swiftlint"):
        return None
    output = run_cmd(["swiftlint", "lint", "--quiet", "--path", file_path])
    if not output:
        return None
    severity = detect_severity(output, [r": error:"], [])
    if severity == "info":
        severity = "warning"
    return output, severity


def check_kotlin(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("ktlint"):
        return None
    output = run_cmd(["ktlint", file_path])
    if output:
        return output, "warning"
    return None


def check_csharp(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("dotnet"):
        return None
    dotnet_dir = find_project_root(file_path, ["*.csproj", "*.sln"])
    if not dotnet_dir:
        return None
    raw = run_cmd(["dotnet", "build", "--no-restore", "-v", "q"], cwd=dotnet_dir)
    if not raw:
        return None
    # Filter to CS errors/warnings only
    lines = [line for line in raw.split("\n") if re.search(r"(error|warning) CS", line)][:20]
    output = "\n".join(lines)
    if not output:
        return None
    severity = detect_severity(output, [r"error CS"], [])
    if severity == "info":
        severity = "warning"
    return output, severity


def check_zig(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("zig"):
        return None
    output = run_cmd(["zig", "ast-check", file_path])
    if output:
        return output, "error"
    return None


def check_dockerfile(file_path: str) -> tuple[str, str] | None:
    if not shutil.which("hadolint"):
        return None
    output = run_cmd(["hadolint", "--format", "gcc", file_path])
    if not output:
        return None
    severity = detect_severity(output, [r":.*: error:"], [])
    if severity == "info":
        severity = "warning"
    return output, severity


# Map extensions to checker functions
EXTENSION_CHECKERS = {
    "sh": check_shellcheck,
    "bash": check_shellcheck,
    "ts": check_typescript,
    "tsx": check_typescript,
    "mts": check_typescript,
    "cts": check_typescript,
    "js": check_eslint,
    "jsx": check_eslint,
    "mjs": check_eslint,
    "cjs": check_eslint,
    "py": check_python,
    "go": check_go,
    "rs": check_rust,
    "json": check_json,
    "yaml": check_yaml,
    "yml": check_yaml,
    "tf": check_terraform,
    "tfvars": check_terraform,
    "lua": check_lua,
    "md": check_markdown,
    "markdown": check_markdown,
    "swift": check_swift,
    "kt": check_kotlin,
    "kts": check_kotlin,
    "cs": check_csharp,
    "zig": check_zig,
}


def main() -> None:
    # Read input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Extract tool name and file path
    tool_name = input_data.get("tool_name", "")
    file_path = input_data.get("tool_input", {}).get("file_path", "")

    # Only process Edit and Write tools
    if tool_name not in ("Edit", "Write"):
        sys.exit(0)

    # Need a file path to analyze
    if not file_path or not os.path.isfile(file_path):
        sys.exit(0)

    basename = os.path.basename(file_path)
    ext = file_path.rsplit(".", 1)[-1] if "." in file_path else ""

    result: tuple[str, str] | None = None

    # Check for Dockerfile first (matched by name, not extension)
    if basename.startswith("Dockerfile") or basename.endswith(".dockerfile"):
        result = check_dockerfile(file_path)
    elif ext in EXTENSION_CHECKERS:
        result = EXTENSION_CHECKERS[ext](file_path)

    # If no diagnostics, exit silently
    if not result:
        sys.exit(0)

    diagnostics, severity = result

    # Truncate if too long
    if len(diagnostics) > 1500:
        diagnostics = diagnostics[:1500] + "... (truncated)"

    # Format output based on severity
    if severity == "error":
        header = "[LSP DIAGNOSTICS: ERRORS FOUND]"
    elif severity == "warning":
        header = "[LSP DIAGNOSTICS: WARNINGS]"
    else:
        header = "[LSP DIAGNOSTICS]"

    context = f"""{header}
File: {file_path}

{diagnostics}

Consider fixing these issues before proceeding."""

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": context,
        }
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
