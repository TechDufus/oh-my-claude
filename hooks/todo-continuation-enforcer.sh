#!/usr/bin/env bash
# todo-continuation-enforcer.sh
# Stop hook: Prevents stopping when todos are incomplete
#
# Called when Claude tries to stop. Returns continuation prompt if work remains.

set -euo pipefail

INPUT=$(cat)

# Extract stop reason
STOP_REASON=$(echo "$INPUT" | jq -r '.stopReason // .stop_reason // "unknown"')

# Allow explicit user interrupts
case "$STOP_REASON" in
    user_interrupt|explicit_stop|user_cancelled|abort)
        exit 0
        ;;
esac

# Parse for incomplete todos from the session state
INCOMPLETE_TODOS=$(echo "$INPUT" | jq -r '
  .todos // [] |
  map(select(.status == "pending" or .status == "in_progress")) |
  length
' 2>/dev/null || echo "0")

# Also check transcript for TodoWrite results if .todos not directly available
if [[ "$INCOMPLETE_TODOS" == "0" ]]; then
    INCOMPLETE_TODOS=$(echo "$INPUT" | jq -r '
      .transcript // [] |
      [.[] | select(.type == "tool_result" and .tool == "TodoWrite")] |
      if length > 0 then
        last.todos // [] |
        map(select(.status == "pending" or .status == "in_progress")) |
        length
      else
        0
      end
    ' 2>/dev/null || echo "0")
fi

# If incomplete todos exist, inject strong continuation
if [[ "$INCOMPLETE_TODOS" -gt 0 ]] && [[ "$INCOMPLETE_TODOS" != "null" ]]; then
    CONTEXT="[TODO CONTINUATION - CANNOT STOP]

You have $INCOMPLETE_TODOS incomplete task(s) in your todo list.

## Rules
- You CANNOT stop until ALL todos are marked 'completed'
- Review your TodoWrite list immediately
- Continue with the next 'pending' or 'in_progress' item
- Do NOT ask for permission - just continue working

## Next Action
Use TodoWrite to review your current tasks, then proceed with the next incomplete item.

CONTINUE WORKING NOW."

    CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
    printf '{"hookSpecificOutput":{"hookEventName":"Stop","decision":"block","reason":"Incomplete todos remain","additionalContext":%s}}' "$CONTEXT_ESCAPED"
    exit 0
fi

# Check for incomplete work patterns in last message
LAST_MESSAGE=$(echo "$INPUT" | jq -r '
  .transcript // [] |
  [.[] | select(.role == "assistant")] |
  if length > 0 then last.content // "" else "" end
' 2>/dev/null || echo "")

# Patterns suggesting premature stopping
PREMATURE_PATTERNS=(
    "let me know if you"
    "feel free to ask"
    "if you want me to"
    "would you like me to continue"
    "I can continue if"
    "shall I proceed"
    "want me to"
)

for pattern in "${PREMATURE_PATTERNS[@]}"; do
    if echo "$LAST_MESSAGE" | grep -qi "$pattern"; then
        # Check if there's uncommitted work suggesting incomplete task
        CWD=$(echo "$INPUT" | jq -r '.cwd // "."')
        if [[ -d "$CWD/.git" ]] && git -C "$CWD" status --porcelain 2>/dev/null | grep -q .; then
            CONTEXT="[INCOMPLETE WORK DETECTED]

Your message suggests you're waiting for permission, but there appear to be uncommitted changes.

If you were in ULTRAWORK mode or working on a task:
1. Check if all requested work is complete
2. Run validation if applicable
3. Complete the task fully before stopping

Do NOT ask - just finish the work."

            CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
            printf '{"hookSpecificOutput":{"hookEventName":"Stop","decision":"block","reason":"Uncommitted changes with incomplete work pattern","additionalContext":%s}}' "$CONTEXT_ESCAPED"
            exit 0
        fi
    fi
done

# Check if todos existed (work was done) - count completed todos
COMPLETED_TODOS=$(echo "$INPUT" | jq -r '
  .todos // [] |
  map(select(.status == "completed")) |
  length
' 2>/dev/null || echo "0")

# Also check transcript for completed todos if .todos not directly available
if [[ "$COMPLETED_TODOS" == "0" ]]; then
    COMPLETED_TODOS=$(echo "$INPUT" | jq -r '
      .transcript // [] |
      [.[] | select(.type == "tool_result" and .tool == "TodoWrite")] |
      if length > 0 then
        last.todos // [] |
        map(select(.status == "completed")) |
        length
      else
        0
      end
    ' 2>/dev/null || echo "0")
fi

# If work was done (completed todos exist), check validation status
if [[ "$COMPLETED_TODOS" -gt 0 ]] && [[ "$COMPLETED_TODOS" != "null" ]]; then
    # Check if validation was already triggered in recent transcript
    VALIDATION_RAN=$(echo "$INPUT" | jq -r '
      .transcript // [] |
      [.[] | select(
        (.type == "tool_use" and .tool == "Task" and (.input // {} | tostring | test("validator"; "i"))) or
        (.type == "assistant" and (.content // "" | test("validator|validation|oh-my-claude:validator"; "i")))
      )] |
      length > 0
    ' 2>/dev/null || echo "false")

    if [[ "$VALIDATION_RAN" != "true" ]]; then
        # Validation hasn't run yet - inject prompt to run validator
        CONTEXT="[AUTO-VALIDATION REQUIRED]

All $COMPLETED_TODOS todo(s) are marked completed. Before stopping, you MUST run validation.

## Required Action
Use Task with subagent_type=\"oh-my-claude:validator\" to verify the work:
- Run relevant tests
- Check for linting errors
- Verify the implementation matches requirements

Do NOT stop until validation passes. Run the validator now."

        CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
        printf '{"hookSpecificOutput":{"hookEventName":"Stop","decision":"block","reason":"Validation required before completion","additionalContext":%s}}' "$CONTEXT_ESCAPED"
        exit 0
    else
        # Validation already ran - inject completion summary prompt
        CONTEXT="[COMPLETION SUMMARY REQUIRED]

Work is complete and validated. Before stopping, provide a brief completion summary:

## Summary Format
1. **What was accomplished** - List the main changes/features implemented
2. **Files modified** - Key files that were changed
3. **Validation results** - Brief note on test/lint status

Provide this summary now, then you may stop."

        CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
        printf '{"hookSpecificOutput":{"hookEventName":"Stop","decision":"block","reason":"Completion summary required","additionalContext":%s}}' "$CONTEXT_ESCAPED"
        exit 0
    fi
fi

# No intervention needed - allow stop
exit 0
