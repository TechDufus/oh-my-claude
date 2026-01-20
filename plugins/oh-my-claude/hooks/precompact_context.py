#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
precompact_context.py
PreCompact hook: Preserves critical context before compaction.

Captures:
- Current mode (ultrawork/normal)
- Git state (branch, uncommitted changes)
- Recent files modified
- Semantic patterns (problems, solutions, decisions, key files)
"""

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

import json

from hook_utils import (
    get_nested,
    hook_main,
    log_debug,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)


def get_git_state(cwd: str | None = None) -> dict:
    """Get current git branch and uncommitted changes status."""
    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # Check for uncommitted changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5
        )
        has_changes = bool(status_result.stdout.strip()) if status_result.returncode == 0 else False

        # Get staged files
        staged_result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5
        )
        staged_files = staged_result.stdout.strip().split("\n") if staged_result.stdout.strip() else []

        return {
            "branch": branch,
            "uncommitted_changes": has_changes,
            "staged_files": staged_files[:10]
        }
    except Exception as e:
        log_debug(f"get_git_state failed: {e}")
        return {
            "branch": "unknown",
            "uncommitted_changes": False,
            "staged_files": []
        }


def get_recent_files(cwd: str | None = None, limit: int = 10) -> list[str]:
    """Get recently modified files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~5"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            files = result.stdout.strip().split("\n")
            return files[:limit]
        return []
    except Exception as e:
        log_debug(f"get_recent_files failed: {e}")
        return []


def detect_mode(data: dict) -> str:
    """Detect if ultrawork mode is active from session context."""
    session_context = get_nested(data, "session_context", default="")
    if "ultrawork" in session_context.lower() or "ulw" in session_context.lower():
        return "ultrawork"
    return "normal"


# Regex patterns for semantic extraction
PROBLEM_PATTERN = re.compile(
    r'\b(error|bug|issue|failed|broken|failing|crash|exception|problem)\b',
    re.IGNORECASE
)
SOLUTION_PATTERN = re.compile(
    r'\b(fix|fixed|solved|resolved|works|working|solution|workaround)\b',
    re.IGNORECASE
)
DECISION_PATTERN = re.compile(
    r'\b(decided|chose|chosen|will use|approach|going with|settled on|opted for)\b',
    re.IGNORECASE
)
FILE_PATH_PATTERN = re.compile(
    r'(?:^|[\s`"\'])([/~]?(?:[\w.-]+/)+[\w.-]+\.\w+)(?:[\s`"\']|$|:|\))',
    re.MULTILINE
)


def extract_patterns(transcript: list) -> dict:
    """
    Extract semantic patterns from recent transcript messages.

    Identifies:
    - Problems discussed (errors, bugs, issues)
    - Solutions found (fixes, resolutions)
    - Decisions made (choices, approaches)
    - Key files mentioned (file paths)

    Args:
        transcript: List of message dicts with 'content' or 'text' fields

    Returns:
        Dict with lists: problems, solutions, decisions, key_files
    """
    patterns = {
        "problems": [],
        "solutions": [],
        "decisions": [],
        "key_files": set()  # Use set to avoid duplicates
    }

    if not transcript:
        return {**patterns, "key_files": []}

    # Limit to last 20 messages to avoid slow processing
    recent_messages = transcript[-20:] if len(transcript) > 20 else transcript

    for msg in recent_messages:
        # Get message content - try common field names
        content = ""
        if isinstance(msg, dict):
            content = msg.get("content", "") or msg.get("text", "") or ""
        elif isinstance(msg, str):
            content = msg

        if not content or not isinstance(content, str):
            continue

        # Extract problems - get surrounding context (up to 80 chars)
        for match in PROBLEM_PATTERN.finditer(content):
            start = max(0, match.start() - 30)
            end = min(len(content), match.end() + 50)
            snippet = content[start:end].strip()
            # Clean up multiline and limit length
            snippet = " ".join(snippet.split())[:80]
            if snippet and snippet not in patterns["problems"]:
                patterns["problems"].append(snippet)

        # Extract solutions
        for match in SOLUTION_PATTERN.finditer(content):
            start = max(0, match.start() - 30)
            end = min(len(content), match.end() + 50)
            snippet = content[start:end].strip()
            snippet = " ".join(snippet.split())[:80]
            if snippet and snippet not in patterns["solutions"]:
                patterns["solutions"].append(snippet)

        # Extract decisions
        for match in DECISION_PATTERN.finditer(content):
            start = max(0, match.start() - 20)
            end = min(len(content), match.end() + 60)
            snippet = content[start:end].strip()
            snippet = " ".join(snippet.split())[:80]
            if snippet and snippet not in patterns["decisions"]:
                patterns["decisions"].append(snippet)

        # Extract file paths
        for match in FILE_PATH_PATTERN.finditer(content):
            path = match.group(1)
            # Filter out obvious non-files and common false positives
            if (path and
                not path.startswith("http") and
                not path.endswith("/") and
                len(path) > 5 and
                not path.startswith("...")):
                patterns["key_files"].add(path)

    # Limit results to avoid bloat, convert set to list
    return {
        "problems": patterns["problems"][:5],
        "solutions": patterns["solutions"][:5],
        "decisions": patterns["decisions"][:5],
        "key_files": list(patterns["key_files"])[:10]
    }


def format_context(
    mode: str,
    git_state: dict,
    recent_files: list[str],
    todos: list[dict],
    timestamp: str,
    patterns: dict | None = None
) -> str:
    """Format preserved context for injection."""
    files_str = "\n".join(f"  - {f}" for f in recent_files) if recent_files else "  (none)"

    todo_str = ""
    if todos:
        for todo in todos[:5]:
            status = todo.get("status", "pending")
            content = todo.get("content", "")[:80]
            todo_str += f"  - [{status}] {content}\n"
    else:
        todo_str = "  (none)\n"

    staged_str = ", ".join(git_state.get("staged_files", [])[:5]) or "(none)"

    # Format patterns section
    patterns_str = ""
    if patterns:
        problems_list = patterns.get("problems", [])
        solutions_list = patterns.get("solutions", [])
        decisions_list = patterns.get("decisions", [])
        key_files_list = patterns.get("key_files", [])

        # Only include section if we have any patterns
        if any([problems_list, solutions_list, decisions_list, key_files_list]):
            patterns_str = "\n### Patterns Detected\n"
            patterns_str += "- Problems: " + (
                ", ".join(f'"{p}"' for p in problems_list) if problems_list else "(none)"
            ) + "\n"
            patterns_str += "- Solutions: " + (
                ", ".join(f'"{s}"' for s in solutions_list) if solutions_list else "(none)"
            ) + "\n"
            patterns_str += "- Decisions: " + (
                ", ".join(f'"{d}"' for d in decisions_list) if decisions_list else "(none)"
            ) + "\n"
            patterns_str += "- Key Files: " + (
                ", ".join(key_files_list) if key_files_list else "(none)"
            ) + "\n"

    return f"""<context-preservation timestamp="{timestamp}">
## Session State Preserved

Mode: {mode}
Branch: {git_state.get('branch', 'unknown')}
Uncommitted Changes: {'Yes' if git_state.get('uncommitted_changes') else 'No'}
Staged Files: {staged_str}

### Recent Files Modified
{files_str}

### Active Todos
{todo_str}{patterns_str}
</context-preservation>

IMPORTANT: This context was preserved before compaction. Resume work from this state."""


def output_system_message(message: str) -> None:
    """
    Output a system message for PreCompact hook.

    PreCompact hooks should use systemMessage at the top level,
    not hookSpecificOutput (which only supports PreToolUse,
    UserPromptSubmit, and PostToolUse).
    """
    response = {"systemMessage": message}
    print(json.dumps(response))


@hook_main("PreCompact")
def main() -> None:
    """Preserve critical context before compaction."""
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        log_debug("no valid input data")
        return output_empty()

    cwd = get_nested(data, "cwd", default=os.getcwd())

    mode = detect_mode(data)
    git_state = get_git_state(cwd)
    recent_files = get_recent_files(cwd)
    todos = get_nested(data, "todos", default=[])

    # Extract semantic patterns from transcript
    transcript = get_nested(data, "transcript", default=[])
    patterns = extract_patterns(transcript)

    timestamp = datetime.now(timezone.utc).isoformat()

    context = format_context(mode, git_state, recent_files, todos, timestamp, patterns)
    log_debug(f"preserving context: mode={mode}, branch={git_state.get('branch')}, patterns={len(patterns.get('problems', []))}p/{len(patterns.get('solutions', []))}s/{len(patterns.get('decisions', []))}d")
    output_system_message(context)


if __name__ == "__main__":
    main()
