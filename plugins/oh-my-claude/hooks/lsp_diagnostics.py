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
import subprocess
from pathlib import Path

from hook_utils import (
    WHICH,
    get_nested,
    hook_main,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

# Tools that can be invoked via uvx (Python packages only)
UVX_TOOLS = {"ruff", "pyright", "yamllint", "taplo", "markdownlint-cli2"}


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


def run_with_fallback(cmd: list[str], cwd: str | None = None) -> str:
    """Run command, falling back to uvx for Python-packaged tools."""
    tool = cmd[0]
    # Try PATH first (fast)
    if WHICH.available(tool):
        return run_cmd(cmd, cwd)
    # uvx fallback for Python packages
    if tool in UVX_TOOLS:
        return run_cmd(["uvx"] + cmd, cwd)
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
    if not WHICH.available("shellcheck"):
        return None
    output = run_cmd(["shellcheck", "-f", "gcc", file_path])
    if not output:
        return None
    severity = detect_severity(output, [r":.*: error:"], [r":.*: warning:"])
    return output, severity


def check_typescript(file_path: str) -> tuple[str, str] | None:
    if not WHICH.available("tsc"):
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
    if not WHICH.available("eslint"):
        return None
    output = run_cmd(["eslint", "--format", "compact", file_path])
    if not output:
        return None
    severity = detect_severity(output, [r" Error -"], [r" Warning -"])
    return output, severity


def check_python(file_path: str) -> tuple[str, str] | None:
    """Run both ruff (lint) and pyright (types) for comprehensive coverage."""
    outputs = []
    max_severity = "info"

    # Run ruff for lint issues
    ruff_output = run_with_fallback(["ruff", "check", "--output-format=concise", file_path])
    if ruff_output:
        # Filter out the "Found X errors" summary line
        lines = [ln for ln in ruff_output.split("\n") if ln and not ln.startswith("Found ")]
        if lines:
            outputs.append("# ruff (lint)")
            outputs.extend(lines)
            max_severity = "warning"

    # Run pyright for type issues
    pyright_raw = run_with_fallback(["pyright", "--outputjson", file_path])
    if pyright_raw:
        try:
            data = json.loads(pyright_raw)
            diagnostics = data.get("generalDiagnostics", [])
            if diagnostics:
                outputs.append("# pyright (types)")
                for d in diagnostics:
                    line = d.get("range", {}).get("start", {}).get("line", 0)
                    sev = d.get("severity", "info")
                    msg = d.get("message", "")
                    outputs.append(f"{file_path}:{line}: {sev}: {msg}")
                    if sev == "error":
                        max_severity = "error"
                    elif sev == "warning" and max_severity != "error":
                        max_severity = "warning"
        except json.JSONDecodeError:
            pass

    if outputs:
        return "\n".join(outputs), max_severity
    return None


def check_go(file_path: str) -> tuple[str, str] | None:
    if not WHICH.available("go"):
        return None
    output = run_cmd(["go", "vet", file_path])
    if output:
        return output, "warning"
    return None


def check_rust(file_path: str) -> tuple[str, str] | None:
    if not WHICH.available("cargo"):
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
    if not WHICH.available("jq"):
        return None
    output = run_cmd(["jq", "empty", file_path])
    if output:
        return output, "error"
    return None


def check_yaml(file_path: str) -> tuple[str, str] | None:
    output = run_with_fallback(["yamllint", "-f", "parsable", file_path])
    if not output:
        return None
    severity = detect_severity(output, [r"\[error\]"], [r"\[warning\]"])
    return output, severity


def check_terraform(file_path: str) -> tuple[str, str] | None:
    if not WHICH.available("tflint"):
        return None
    output = run_cmd(["tflint", "--format", "compact", file_path])
    if not output:
        return None
    severity = detect_severity(output, [r"Error:"], [])
    if severity == "info":
        severity = "warning"
    return output, severity


def check_lua(file_path: str) -> tuple[str, str] | None:
    if not WHICH.available("luacheck"):
        return None
    output = run_cmd(["luacheck", "--formatter", "plain", file_path])
    if not output or "0 warnings" in output:
        return None
    severity = detect_severity(output, [r"\([EF]\d+\)"], [])
    if severity == "info":
        severity = "warning"
    return output, severity


def check_markdown(file_path: str) -> tuple[str, str] | None:
    output = run_with_fallback(["markdownlint-cli2", file_path])
    if output:
        return output, "warning"
    return None


def check_swift(file_path: str) -> tuple[str, str] | None:
    if not WHICH.available("swiftlint"):
        return None
    output = run_cmd(["swiftlint", "lint", "--quiet", "--path", file_path])
    if not output:
        return None
    severity = detect_severity(output, [r": error:"], [])
    if severity == "info":
        severity = "warning"
    return output, severity


def check_kotlin(file_path: str) -> tuple[str, str] | None:
    if not WHICH.available("ktlint"):
        return None
    output = run_cmd(["ktlint", file_path])
    if output:
        return output, "warning"
    return None


def check_csharp(file_path: str) -> tuple[str, str] | None:
    if not WHICH.available("dotnet"):
        return None
    dotnet_dir = find_project_root(file_path, ["*.csproj", "*.sln"])
    if not dotnet_dir:
        return None
    # Use --no-restore, -v q, and --nologo to minimize side effects
    raw = run_cmd(["dotnet", "build", "--no-restore", "-v", "q", "--nologo"], cwd=dotnet_dir)
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
    if not WHICH.available("zig"):
        return None
    output = run_cmd(["zig", "ast-check", file_path])
    if output:
        return output, "error"
    return None


def check_dockerfile(file_path: str) -> tuple[str, str] | None:
    if not WHICH.available("hadolint"):
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


@hook_main("PostToolUse")
def main() -> None:
    # Read input safely with timeout and size limits
    raw = read_stdin_safe()
    input_data = parse_hook_input(raw)

    if not input_data:
        return output_empty()

    # Extract tool name and file path (safely handles non-dict tool_input)
    tool_name = input_data.get("tool_name", "")
    file_path = get_nested(input_data, "tool_input", "file_path", default="")

    # Only process Edit and Write tools
    if tool_name not in ("Edit", "Write"):
        return output_empty()

    # Need a file path to analyze
    if not file_path or not os.path.isfile(file_path):
        return output_empty()

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
        return output_empty()

    # Type narrowing for pyright
    assert result is not None
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

    output_context("PostToolUse", context)


if __name__ == "__main__":
    main()
