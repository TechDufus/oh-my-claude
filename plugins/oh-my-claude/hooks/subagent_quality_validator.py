#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
subagent_quality_validator.py - Validates subagent output quality before allowing stop.

SubagentStop hook that ensures subagents deliver expected outputs based on their type.
Prevents premature completion when work appears incomplete.

Agent-specific quality checks:
- worker: Must mention file paths (indicating code changes)
- scout: Must report file paths found
- librarian: Must provide summary content
- validator: Must report test/validation results

Configuration:
- OMC_SUBAGENT_QUALITY: Set to "0" to disable (default "1")
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    hook_main,
    log_debug,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
    RegexCache,
)

# =============================================================================
# Configuration
# =============================================================================

ENABLED = os.environ.get("OMC_SUBAGENT_QUALITY", "1") != "0"

# =============================================================================
# Pre-compiled patterns
# =============================================================================

PATTERNS = RegexCache()

# File path patterns (Unix and Windows)
PATTERNS.add(
    "file_path",
    r"(?:^|[\s\"\'`])(?:/[\w./-]+|[A-Za-z]:\\[\w.\\-]+|\.{1,2}/[\w./-]+)",
    re.MULTILINE,
)

# Summary indicators for librarian
PATTERNS.add(
    "summary_indicators",
    r"(?:summary|overview|key\s+(?:points|findings)|main\s+(?:points|takeaways)|"
    r"in\s+(?:summary|short|brief)|highlights?|tldr|tl;dr)",
    re.IGNORECASE,
)

# Test result indicators for validator
PATTERNS.add(
    "test_results",
    r"(?:pass(?:ed|ing)?|fail(?:ed|ing)?|error|success|"
    r"\d+\s+(?:tests?|specs?|assertions?)|"
    r"test\s+(?:results?|output|summary)|"
    r"all\s+(?:tests?|checks?)\s+(?:pass|passed)|"
    r"linting?\s+(?:pass|clean|ok|error)|"
    r"no\s+(?:errors?|issues?|problems?)|"
    r"validation\s+(?:pass|complete|success))",
    re.IGNORECASE,
)

# Code modification indicators for worker
PATTERNS.add(
    "code_modified",
    r"(?:created?|modified|updated|added|removed|deleted|wrote|edited|changed|"
    r"implemented|fixed|refactored|renamed)",
    re.IGNORECASE,
)

# Scout success indicators
PATTERNS.add(
    "scout_found",
    r"(?:found|located|discovered|identified|matches?|results?|files?|"
    r"no\s+(?:files?|matches?|results?)\s+found)",
    re.IGNORECASE,
)


# =============================================================================
# Output helpers
# =============================================================================


def output_block_subagent(reason: str) -> None:
    """Output a blocking response for SubagentStop hook."""
    response = {"decision": "block", "reason": reason}
    print(json.dumps(response))
    sys.exit(0)


# =============================================================================
# Quality validators
# =============================================================================


def extract_agent_type(full_type: str) -> str:
    """Extract base agent type from full agent type string.

    Args:
        full_type: Full agent type like "oh-my-claude:worker"

    Returns:
        Base type like "worker"
    """
    if ":" in full_type:
        return full_type.split(":")[-1].lower()
    return full_type.lower()


def check_non_empty(output: str) -> tuple[bool, str]:
    """Check if output is non-empty and meaningful.

    Returns:
        Tuple of (passed, reason_if_failed)
    """
    if not output or not output.strip():
        return False, "Output is empty. Subagent must provide results."

    # Check for minimal content (at least a few words)
    words = output.split()
    if len(words) < 5:
        return False, "Output is too brief. Provide more detail about what was done."

    return True, ""


def check_worker_output(output: str) -> tuple[bool, str]:
    """Validate worker agent output.

    Workers should mention file paths and indicate code modifications.

    Returns:
        Tuple of (passed, reason_if_failed)
    """
    has_file_path = PATTERNS.match("file_path", output) is not None
    has_modification = PATTERNS.match("code_modified", output) is not None

    log_debug(f"worker check: has_file_path={has_file_path}, has_modification={has_modification}")

    if not has_file_path:
        return False, (
            "Worker output must include file paths to indicate what was modified. "
            "List the files you created or changed."
        )

    if not has_modification:
        # File paths present but no modification verbs - might still be valid
        # Be lenient here to avoid false positives
        log_debug("worker has file paths but no modification verbs - allowing")

    return True, ""


def check_scout_output(output: str) -> tuple[bool, str]:
    """Validate scout agent output.

    Scouts should report file paths or explicitly state nothing was found.

    Returns:
        Tuple of (passed, reason_if_failed)
    """
    has_file_path = PATTERNS.match("file_path", output) is not None
    has_search_result = PATTERNS.match("scout_found", output) is not None

    log_debug(f"scout check: has_file_path={has_file_path}, has_search_result={has_search_result}")

    if not has_file_path and not has_search_result:
        return False, (
            "Scout output must include discovered file paths or clearly state "
            "that no matching files were found."
        )

    return True, ""


def check_librarian_output(output: str) -> tuple[bool, str]:
    """Validate librarian agent output.

    Librarians should provide summaries or structured information.

    Returns:
        Tuple of (passed, reason_if_failed)
    """
    has_summary = PATTERNS.match("summary_indicators", output) is not None

    # Also accept structured output (lists, sections) as valid
    has_structure = bool(re.search(r"(?:^[-*]|\d+\.|##?\s)", output, re.MULTILINE))

    log_debug(f"librarian check: has_summary={has_summary}, has_structure={has_structure}")

    # Librarians can provide either explicit summaries or structured content
    if not has_summary and not has_structure:
        # Be lenient - if output is substantial, accept it
        if len(output.split()) > 50:
            log_debug("librarian output is substantial - allowing without explicit summary")
            return True, ""

        return False, (
            "Librarian output should include a summary or structured analysis. "
            "Provide key findings and organized information."
        )

    return True, ""


def check_validator_output(output: str) -> tuple[bool, str]:
    """Validate validator agent output.

    Validators should report test/validation results.

    Returns:
        Tuple of (passed, reason_if_failed)
    """
    has_test_results = PATTERNS.match("test_results", output) is not None

    log_debug(f"validator check: has_test_results={has_test_results}")

    if not has_test_results:
        return False, (
            "Validator output must include test or validation results. "
            "Report what was tested and whether it passed or failed."
        )

    return True, ""


def validate_agent_output(agent_type: str, output: str) -> tuple[bool, str]:
    """Run appropriate validation based on agent type.

    Args:
        agent_type: The type of agent (worker, scout, librarian, validator, etc.)
        output: The agent's output text

    Returns:
        Tuple of (passed, reason_if_failed)
    """
    base_type = extract_agent_type(agent_type)

    log_debug(f"validating agent_type={agent_type}, base_type={base_type}")

    # Always check non-empty first
    passed, reason = check_non_empty(output)
    if not passed:
        return passed, reason

    # Agent-specific checks
    validators = {
        "worker": check_worker_output,
        "scout": check_scout_output,
        "librarian": check_librarian_output,
        "validator": check_validator_output,
    }

    validator_func = validators.get(base_type)
    if validator_func:
        return validator_func(output)

    # For unknown agent types (architect, critic, etc.), just pass non-empty check
    log_debug(f"no specific validator for {base_type} - passing")
    return True, ""


# =============================================================================
# Main
# =============================================================================


@hook_main("SubagentStop")
def main() -> None:
    """Validate subagent output quality before allowing completion."""
    # Check if validation is enabled
    if not ENABLED:
        log_debug("subagent quality validation disabled via OMC_SUBAGENT_QUALITY=0")
        output_empty()

    # Read and parse input
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        log_debug("no input data - allowing stop")
        output_empty()

    # Extract relevant fields
    agent_type = data.get("agent_type", "")
    agent_output = data.get("agent_output", "")
    agent_prompt = data.get("agent_prompt", "")

    log_debug(f"agent_type={agent_type}")
    log_debug(f"agent_output length={len(agent_output)}")
    log_debug(f"agent_prompt length={len(agent_prompt)}")

    # Skip validation if no agent type specified
    if not agent_type:
        log_debug("no agent_type - allowing stop")
        output_empty()

    # Run validation
    passed, reason = validate_agent_output(agent_type, agent_output)

    if not passed:
        log_debug(f"validation failed: {reason}")
        output_block_subagent(reason)

    log_debug("validation passed - allowing stop")
    output_empty()


if __name__ == "__main__":
    main()
