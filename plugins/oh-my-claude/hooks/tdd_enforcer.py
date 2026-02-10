#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
tdd_enforcer.py
PreToolUse hook: Enforces TDD by requiring test files before source edits.

Modes (via OMC_TDD_MODE env var):
- off: No enforcement (default)
- guided: Warn but allow
- enforced: Block edits without tests
"""

import json
import os
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    get_nested,
    hook_main,
    log_debug,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

def output_deny(reason: str) -> None:
    """Output denial response for PreToolUse hook."""
    response = {"decision": "deny", "reason": reason}
    print(json.dumps(response))
    sys.exit(0)


# Source file extensions that should have tests
SOURCE_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx",  # TypeScript/JavaScript
    ".py",                          # Python
    ".go",                          # Go
    ".rs",                          # Rust
    ".java",                        # Java
}

# Patterns that indicate a file is already a test
TEST_PATTERNS = [
    r"\.test\.[jt]sx?$",           # .test.ts, .test.tsx, .test.js
    r"\.spec\.[jt]sx?$",           # .spec.ts, .spec.tsx, .spec.js
    r"_test\.go$",                 # Go test files
    r"_test\.py$",                 # Python test files
    r"^test_.*\.py$",              # Python test files
    r"Test\.java$",                # Java test files
    r"Tests\.java$",               # Java test files
]

# Paths that should be excluded from TDD enforcement
EXCLUDED_PATTERNS = [
    r"__tests__/",                 # Test directories
    r"/tests?/",                   # test/ or tests/ directories
    r"\.config\.",                 # Config files
    r"\.d\.ts$",                   # TypeScript definitions
    r"/types/",                    # Type definition directories
    r"types\.ts$",                 # Type files
    r"(^|/)index\.[jt]sx?$",      # Entry points
    r"(^|/)main\.[jt]sx?$",       # Entry points
    r"(^|/)app\.[jt]sx?$",        # Entry points
    r"\.generated\.",              # Generated files
    r"\.g\.",                      # Generated files (short form)
    r"\.(json|yaml|yml|toml|md)$", # Config/doc files
]


def get_tdd_mode() -> str:
    """Get TDD mode from environment variable."""
    mode = os.environ.get("OMC_TDD_MODE", "off").lower()
    if mode not in ("off", "guided", "enforced"):
        log_debug(f"Invalid OMC_TDD_MODE '{mode}', defaulting to 'off'")
        return "off"
    return mode


def is_source_file(path: str) -> bool:
    """Check if file is a source file that should have tests."""
    ext = Path(path).suffix.lower()
    return ext in SOURCE_EXTENSIONS


def is_test_file(path: str) -> bool:
    """Check if file is already a test file."""
    filename = Path(path).name
    for pattern in TEST_PATTERNS:
        if re.search(pattern, filename):
            return True
    return False


def is_excluded(path: str) -> bool:
    """Check if file should be excluded from TDD enforcement."""
    for pattern in EXCLUDED_PATTERNS:
        if re.search(pattern, path):
            return True
    return False


def get_test_patterns(source_path: str) -> list[str]:
    """Generate possible test file paths for a source file."""
    path = Path(source_path)
    stem = path.stem
    parent = path.parent
    ext = path.suffix

    patterns = []

    if ext in (".ts", ".tsx", ".js", ".jsx"):
        # TypeScript/JavaScript patterns
        patterns.extend([
            str(parent / f"{stem}.test{ext}"),
            str(parent / f"{stem}.spec{ext}"),
            str(parent / "__tests__" / f"{stem}{ext}"),
        ])
    elif ext == ".py":
        # Python patterns
        patterns.extend([
            str(parent / f"test_{stem}.py"),
            str(parent / f"{stem}_test.py"),
            str(parent.parent / "tests" / parent.name / f"test_{stem}.py"),
        ])
    elif ext == ".go":
        # Go pattern (same directory, _test suffix)
        patterns.append(str(parent / f"{stem}_test.go"))
    elif ext == ".java":
        # Java patterns
        patterns.extend([
            str(parent / f"{stem}Test.java"),
            str(parent / f"{stem}Tests.java"),
        ])

    return patterns


def find_test_file(source_path: str, cwd: str | None = None) -> str | None:
    """Find corresponding test file if it exists."""
    patterns = get_test_patterns(source_path)
    base = Path(cwd) if cwd else Path.cwd()

    for pattern in patterns:
        test_path = base / pattern if not Path(pattern).is_absolute() else Path(pattern)
        if test_path.exists():
            return str(test_path)

    return None


def format_expected_paths(source_path: str) -> str:
    """Format expected test paths for error message."""
    patterns = get_test_patterns(source_path)
    return "\n".join(f"  - {p}" for p in patterns[:5])


@hook_main("PreToolUse")
def main() -> None:
    """Check for test files before allowing source edits."""
    mode = get_tdd_mode()
    if mode == "off":
        log_debug("TDD mode is off, allowing all edits")
        return output_empty()

    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        return output_empty()

    tool_name = get_nested(data, "tool_name", default="")
    if tool_name not in ("Edit", "Write"):
        return output_empty()

    # Extract file path from tool input
    tool_input = get_nested(data, "tool_input", default={})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        return output_empty()

    log_debug(f"Checking TDD for: {file_path}")

    # Check if it's a source file
    if not is_source_file(file_path):
        log_debug(f"Not a source file: {file_path}")
        return output_empty()

    # Check exclusions
    if is_test_file(file_path):
        log_debug(f"Is a test file: {file_path}")
        return output_empty()

    if is_excluded(file_path):
        log_debug(f"Excluded path: {file_path}")
        return output_empty()

    # Look for test file
    cwd = get_nested(data, "cwd", default=None)
    test_file = find_test_file(file_path, cwd)

    if test_file:
        log_debug(f"Test found: {test_file}")
        return output_empty()

    # No test found
    log_debug(f"No test found for: {file_path}")

    if mode == "enforced":
        output_deny(
            f"""[TDD ENFORCEMENT - BLOCKED]

Cannot edit source file without corresponding test.

Source: {file_path}

Expected test at one of:
{format_expected_paths(file_path)}

## Required Action
Create the test file FIRST, then edit the source.

For TDD methodology guidance, invoke the `tdd` skill.

## Anti-Rationalization
- "I'll write tests after" → Tests written after prove nothing — they pass immediately.
- "Too simple to test" → Simple code breaks. Test takes 30 seconds.

Mode: enforced (set OMC_TDD_MODE=guided to warn only, or OMC_TDD_MODE=off to disable)"""
        )
    elif mode == "guided":
        patterns = get_test_patterns(file_path)
        suggested = patterns[0] if patterns else "unknown"
        output_context(
            "PreToolUse",
            f"""[TDD GUIDANCE]

Editing source file without test: {file_path}

Consider creating test first: {suggested}

The `tdd` skill provides Red-Green-Refactor methodology and anti-rationalization guidance.

Mode: guided (set OMC_TDD_MODE=enforced to block)"""
        )


if __name__ == "__main__":
    main()
