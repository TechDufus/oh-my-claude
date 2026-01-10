#!/usr/bin/env bash
# ultrawork-detector.sh
# Detects mode keywords and injects EXECUTION INTENSITY directives
# Context protection is handled by context-guardian.sh (always-on)
# This hook adds MODE-SPECIFIC behaviors on top

set -euo pipefail

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // ""')
CWD=$(echo "$INPUT" | jq -r '.cwd // "."')
PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')

# Detect project type for smart validation
detect_validation() {
    if [[ -f "$CWD/package.json" ]]; then
        echo "TypeScript/JS: npm run typecheck && npm run lint && npm test"
    elif [[ -f "$CWD/pyproject.toml" ]] || [[ -f "$CWD/setup.py" ]]; then
        echo "Python: ruff check . && pytest"
    elif [[ -f "$CWD/go.mod" ]]; then
        echo "Go: go vet ./... && go test ./..."
    elif [[ -f "$CWD/Cargo.toml" ]]; then
        echo "Rust: cargo check && cargo test"
    elif [[ -f "$CWD/Makefile" ]]; then
        echo "make test (or equivalent)"
    else
        echo "Run appropriate linters and tests for this project type."
    fi
}

# =============================================================================
# ULTRAWORK MODE - Maximum execution intensity
# Context protection is ALREADY ON (context-guardian.sh)
# This adds: relentless execution, zero tolerance, mandatory parallelization
# =============================================================================
if [[ "$PROMPT_LOWER" =~ (ultrawork|ulw|just[[:space:]]work|dont[[:space:]]stop|until[[:space:]]done|keep[[:space:]]going|finish[[:space:]]everything|relentless|get[[:space:]]it[[:space:]]done|make[[:space:]]it[[:space:]]happen|no[[:space:]]excuses|full[[:space:]]send|go[[:space:]]all[[:space:]]in|complete[[:space:]]everything|finish[[:space:]]it|see[[:space:]]it[[:space:]]through|dont[[:space:]]give[[:space:]]up|ship[[:space:]]it|crush[[:space:]]it|nail[[:space:]]it|lets[[:space:]]go|do[[:space:]]it[[:space:]]all|handle[[:space:]]everything) ]]; then

    VALIDATION=$(detect_validation)

    CONTEXT='[ULTRAWORK MODE ENABLED!]

You MUST output "ULTRAWORK MODE ENABLED!" as your first line, then execute with maximum intensity.

## ZERO TOLERANCE POLICY
- NO partial implementations
- NO "simplified versions"
- NO "leaving as exercise"
- NO skipped tests
- NO scope reduction
- DELIVER EXACTLY what was asked. NOT A SUBSET.

## Execution Rules
1. PARALLELIZE EVERYTHING - Launch ALL independent Task subagents in ONE message. Sequential is failure.
2. TODOWRITE IMMEDIATELY - Minimum 3 todos for any non-trivial work. Update status in real-time.
3. NEVER STOP - You may ONLY stop when ALL todos are "completed" AND validation passes.
4. NO QUESTIONS - Make reasonable decisions. Document them. Keep moving.

## Validation Required: '"$VALIDATION"'

## CRITICAL
- Multiple Tasks in ONE message = parallelism
- Single Task per message = sequential failure
- Incomplete todos = CANNOT stop
- Failed validation = CANNOT stop

Execute relentlessly until complete.'

    CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
    printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":%s}}' "$CONTEXT_ESCAPED"
    exit 0
fi

# =============================================================================
# SEARCH MODE - Parallel search strategy
# =============================================================================
if [[ "$PROMPT_LOWER" =~ (search[[:space:]]for|find[[:space:]]all|locate|where[[:space:]]is|look[[:space:]]for|grep[[:space:]]for|hunt[[:space:]]down|track[[:space:]]down|show[[:space:]]me[[:space:]]where|find[[:space:]]me|get[[:space:]]me[[:space:]]all|list[[:space:]]all) ]]; then

    CONTEXT='[SEARCH MODE ACTIVE]

MAXIMIZE SEARCH EFFORT. Launch multiple search agents IN PARALLEL.

## Search Strategy
- Launch 2-3 oh-my-claude:scout Tasks in ONE message with different strategies
- One for exact matches, one for fuzzy/related terms
- Use Grep for content, Glob for file patterns
- Combine results and deduplicate

## Report Format
- List all findings with file:line references
- Group by relevance or location
- Highlight most likely matches first'

    CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
    printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":%s}}' "$CONTEXT_ESCAPED"
    exit 0
fi

# =============================================================================
# ANALYZE MODE - Deep parallel analysis
# =============================================================================
if [[ "$PROMPT_LOWER" =~ (analyze|analyse|understand|explain[[:space:]]how|how[[:space:]]does|investigate|deep[[:space:]]dive|examine|inspect|audit|break[[:space:]]down|walk[[:space:]]through|tell[[:space:]]me[[:space:]]about|help[[:space:]]me[[:space:]]understand|whats[[:space:]]going[[:space:]]on) ]]; then

    CONTEXT='[ANALYZE MODE ACTIVE]

Gather comprehensive context before providing analysis.

## Analysis Protocol
- Launch parallel agents: one for main component, one for dependencies, one for tests
- Trace data/control flow through the system
- Provide evidence for every claim (file:line references)

## Output Requirements
- No speculation without verification
- Explain the "why" not just the "what"
- Identify potential issues or edge cases'

    CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
    printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":%s}}' "$CONTEXT_ESCAPED"
    exit 0
fi

# =============================================================================
# ULTRATHINK MODE - Extended reasoning before action
# =============================================================================
if [[ "$PROMPT_LOWER" =~ (ultrathink|think[[:space:]]deeply|deep[[:space:]]analysis|think[[:space:]]hard|careful[[:space:]]analysis|thoroughly[[:space:]]analyze) ]]; then

    CONTEXT='[ULTRATHINK MODE ACTIVE]

Extended reasoning before any action.

## Thinking Protocol
1. Gather context via scout + librarian
2. Consider 3+ approaches before committing to one
3. List pros/cons of each approach
4. Identify edge cases and potential failure modes
5. Validate ALL assumptions by reading code

## Requirements
- No implementation until analysis is complete
- Document reasoning in detail
- Challenge your own assumptions
- Consider maintainability and future implications'

    CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
    printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":%s}}' "$CONTEXT_ESCAPED"
    exit 0
fi

# =============================================================================
# ULTRADEBUG MODE - Systematic debugging protocol
# =============================================================================
if [[ "$PROMPT_LOWER" =~ (ultradebug|debug[[:space:]]this|fix[[:space:]]this[[:space:]]bug|troubleshoot|diagnose|why[[:space:]]is[[:space:]]this[[:space:]]failing|root[[:space:]]cause|whats[[:space:]]wrong|whats[[:space:]]broken|figure[[:space:]]out[[:space:]]why|fix[[:space:]]the[[:space:]]issue|whats[[:space:]]causing) ]]; then

    CONTEXT='[ULTRADEBUG MODE ACTIVE]

Systematic debugging with evidence-based diagnosis.

## Debug Protocol
1. REPRODUCE - Understand the exact failure condition
2. ISOLATE - Narrow down to the smallest failing case
3. TRACE - Follow execution path via scout + librarian
4. HYPOTHESIZE - Form 2-3 theories about root cause
5. VERIFY - Test each hypothesis with evidence
6. FIX - Apply minimal fix to address root cause
7. VALIDATE - Confirm fix works and no regression

## Evidence Requirements
- Every hypothesis must have supporting evidence (file:line)
- Check recent changes (git log, git diff)
- Verify fix with tests

## Parallel Investigation
- Launch multiple agents: one for failing code path, one for similar code that works'

    CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
    printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":%s}}' "$CONTEXT_ESCAPED"
    exit 0
fi

# No trigger - pass through (context-guardian already provided baseline rules at SessionStart)
exit 0
