#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""
claudemd_health.py
SessionStart hook: Proactively checks CLAUDE.md health and warns about issues.

Non-blocking - always returns success, just injects warnings when needed.
Checks:
- Line count (warns if >100 lines)
- Instruction density (warns if >150 estimated instructions)
- Hardcoded file paths (staleness risk)
- Nested CLAUDE.md opportunities (when root is large)
"""

import re
from pathlib import Path

from hook_utils import (
    get_nested,
    hook_main,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

# Thresholds
MAX_LINES_HEALTHY = 100
MAX_INSTRUCTIONS_HEALTHY = 150
MAX_LINES_TO_ANALYZE = 1000

# Patterns for detecting hardcoded paths
PATH_PATTERNS = [
    # Directory/file patterns like src/utils/auth.ts
    r"\b(?:src|lib|app|components|utils|services|api|routes|models|controllers|views|helpers|middleware)/[\w/]+\.(?:ts|tsx|js|jsx|py|go|rs|rb|java)\b",
    # Line number references like auth.ts:42
    r"\b\w+\.(?:ts|tsx|js|jsx|py|go|rs|rb|java):\d+\b",
]

# Common directories that benefit from nested CLAUDE.md
COMMON_DIRS = [
    "src", "lib", "app", "tests", "test", "spec",
    "api", "routes", "components", "hooks", "utils",
    "services", "models", "controllers", "scripts",
]

# Content patterns for detecting domain-specific sections
# Maps topic -> (regex pattern, suggested path)
CONTENT_PATTERNS = {
    "testing": (r"test|spec|jest|mocha|pytest|coverage", "tests/CLAUDE.md"),
    "components": (r"component|react|vue|angular|ui", "src/components/CLAUDE.md or components/CLAUDE.md"),
    "api": (r"api|endpoint|route|rest|graphql", "src/api/CLAUDE.md or api/CLAUDE.md"),
    "hooks": (r"hook|use[A-Z]", "src/hooks/CLAUDE.md or hooks/CLAUDE.md"),
}


def count_instructions(content: str) -> int:
    """
    Estimate instruction count using heuristics.

    Counts:
    - Bullet points starting with - or *
    - Lines with imperative verbs (common instruction starters)
    """
    count = 0
    lines = content.split("\n")

    # Imperative verbs commonly starting instructions
    imperative_verbs = (
        "use",
        "do",
        "don't",
        "never",
        "always",
        "must",
        "should",
        "ensure",
        "make",
        "keep",
        "avoid",
        "prefer",
        "run",
        "check",
        "verify",
        "validate",
        "set",
        "create",
        "delete",
        "update",
        "add",
        "remove",
        "call",
        "return",
        "follow",
        "include",
        "exclude",
    )

    for line in lines:
        stripped = line.strip().lower()

        # Count bullet points
        if stripped.startswith(("-", "*")) and len(stripped) > 2:
            count += 1
            continue

        # Count lines starting with imperative verbs
        for verb in imperative_verbs:
            if stripped.startswith(verb + " ") or stripped.startswith(verb + ","):
                count += 1
                break

    return count


def find_hardcoded_paths(content: str) -> list[str]:
    """Find hardcoded file paths that may become stale."""
    found: set[str] = set()

    for pattern in PATH_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        found.update(matches)

    return list(found)


def detect_nested_opportunities(cwd: Path, content: str) -> list[str]:
    """
    Detect opportunities for nested CLAUDE.md files.

    Returns list of suggestions (max 3) for directories that could
    benefit from their own CLAUDE.md files.
    """
    suggestions: list[str] = []

    # Find directories that exist but lack CLAUDE.md
    missing_claudemd_dirs: list[str] = []
    for dirname in COMMON_DIRS:
        dir_path = cwd / dirname
        if dir_path.is_dir() and not (dir_path / "CLAUDE.md").exists():
            missing_claudemd_dirs.append(dirname)

    if missing_claudemd_dirs:
        # Cap display at 5 directories to keep message concise
        display_dirs = missing_claudemd_dirs[:5]
        extra = len(missing_claudemd_dirs) - 5
        dir_list = ", ".join(display_dirs)
        if extra > 0:
            dir_list += f" (+{extra} more)"
        suggestions.append(
            f"Found {len(missing_claudemd_dirs)} directories without CLAUDE.md: {dir_list}"
        )

    # Analyze content for domain-specific sections
    content_lower = content.lower()
    for topic, (pattern, suggested_path) in CONTENT_PATTERNS.items():
        # Check if content mentions this topic significantly (5+ matches)
        matches = re.findall(pattern, content_lower)
        if len(matches) >= 5:
            # Check if the suggested path already has CLAUDE.md
            # Extract first suggested directory from path
            first_suggestion = suggested_path.split(" or ")[0]
            check_path = cwd / first_suggestion
            if not check_path.exists():
                suggestions.append(
                    f"Content about '{topic}' could move to {suggested_path}"
                )

    # Cap total suggestions and add /init-deep reference if any found
    if suggestions:
        suggestions = suggestions[:3]
        suggestions.append("Run /init-deep to migrate to nested structure")

    return suggestions


def analyze_claudemd(filepath: Path) -> list[str]:
    """
    Analyze CLAUDE.md and return list of warning messages.

    Returns empty list if file is healthy.
    """
    warnings: list[str] = []

    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # Can't read file - not an error, just skip
        return []

    lines = content.split("\n")
    line_count = len(lines)

    # Truncate analysis for very large files
    if line_count > MAX_LINES_TO_ANALYZE:
        content = "\n".join(lines[:MAX_LINES_TO_ANALYZE])
        line_count = MAX_LINES_TO_ANALYZE

    # Check line count
    if line_count > MAX_LINES_HEALTHY:
        warnings.append(f"CLAUDE.md is large ({line_count} lines). Consider /refactor-claude")

    # Check instruction density
    instruction_count = count_instructions(content)
    if instruction_count > MAX_INSTRUCTIONS_HEALTHY:
        warnings.append(
            f"Approaching instruction budget ({instruction_count} estimated). Consider consolidating"
        )

    # Check for hardcoded paths
    hardcoded_paths = find_hardcoded_paths(content)
    if hardcoded_paths:
        warnings.append(f"Detected {len(hardcoded_paths)} hardcoded file paths (staleness risk)")

    return warnings


@hook_main("SessionStart")
def main() -> None:
    """Check CLAUDE.md health at session start.

    Non-blocking - always returns success, just injects warnings.
    Skips silently if CLAUDE.md doesn't exist or can't be read.
    """
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    # Skip for subagents - they don't need CLAUDE.md health checks
    agent_type = get_nested(data, "agent_type", default=None)
    if agent_type:
        return output_empty()

    # Get working directory from hook input
    cwd = get_nested(data, "cwd", default=".")
    cwd_path = Path(cwd)
    claudemd_path = cwd_path / "CLAUDE.md"

    # Skip if CLAUDE.md doesn't exist
    if not claudemd_path.exists():
        return output_empty()

    # Analyze and collect warnings
    warnings = analyze_claudemd(claudemd_path)

    # Check for nested CLAUDE.md opportunities if file is large
    try:
        content = claudemd_path.read_text(encoding="utf-8")
        line_count = len(content.split("\n"))
        if line_count > MAX_LINES_HEALTHY:
            nested_suggestions = detect_nested_opportunities(cwd_path, content)
            warnings.extend(nested_suggestions)
    except (OSError, UnicodeDecodeError):
        pass  # Skip nested check if file can't be read

    # Output warnings if any found
    if warnings:
        message = "[CLAUDE.md Health Check]\n" + "\n".join(f"- {w}" for w in warnings)
        output_context("SessionStart", message)
    else:
        output_empty()


if __name__ == "__main__":
    main()
