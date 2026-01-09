#!/bin/bash
# ultrawork-detector.sh
# Detects ultrawork/search/analyze triggers and injects execution directives

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
# ULTRAWORK MODE - Maximum execution with parallel agents
# =============================================================================
if [[ "$PROMPT_LOWER" =~ (ultrawork|ulw|just[[:space:]]work|dont[[:space:]]stop|until[[:space:]]done|keep[[:space:]]going|finish[[:space:]]everything|relentless|get[[:space:]]it[[:space:]]done) ]]; then

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
2. DELEGATE FILE READS - Files >100 lines? Task(subagent_type="oh-my-claude:deep-explorer"). Your context is for reasoning.
3. TODOWRITE IMMEDIATELY - Minimum 3 todos for any non-trivial work. Update status in real-time.
4. NEVER STOP - You may ONLY stop when ALL todos are "completed" AND validation passes.
5. NO QUESTIONS - Make reasonable decisions. Document them. Keep moving.

## Agent Deployment Strategy
- Use oh-my-claude:deep-explorer for codebase understanding
- Use oh-my-claude:parallel-implementer for focused implementation (ONE task per agent)
- Use oh-my-claude:validator before declaring complete
- Use oh-my-claude:context-summarizer for large file digests

## Context Preservation Rules
- <100 lines: Read directly
- >100 lines: Delegate to subagent for summary
- Any search/explore: Always use Task with Explore or deep-explorer

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
# SEARCH MODE - Parallel search agents
# =============================================================================
if [[ "$PROMPT_LOWER" =~ (search[[:space:]]for|find[[:space:]]all|locate|where[[:space:]]is|look[[:space:]]for|grep[[:space:]]for|hunt[[:space:]]down|track[[:space:]]down) ]]; then

    CONTEXT='[SEARCH MODE ACTIVE]

MAXIMIZE SEARCH EFFORT. Launch multiple search agents IN PARALLEL.

## Search Strategy
1. Launch Task(subagent_type="oh-my-claude:deep-explorer") for pattern-based search
2. Use Grep tool for content matching
3. Use Glob tool for file pattern matching
4. Consider multiple search terms and variations

## Parallel Execution
- Launch 2-3 search Tasks in ONE message with different strategies
- One for exact matches, one for fuzzy/related terms
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
# ANALYZE MODE - Deep analysis before action
# =============================================================================
if [[ "$PROMPT_LOWER" =~ (analyze|analyse|understand|explain[[:space:]]how|how[[:space:]]does|investigate|deep[[:space:]]dive|examine|inspect|audit) ]]; then

    CONTEXT='[ANALYZE MODE ACTIVE]

Gather comprehensive context before providing analysis.

## Analysis Protocol
1. Launch Task(subagent_type="oh-my-claude:deep-explorer") to map relevant code
2. Identify all related files and dependencies
3. Trace data/control flow through the system
4. Document assumptions and verify them

## Parallel Context Gathering
- Launch multiple explorer agents for different aspects
- One for the main component, one for dependencies, one for tests/usage

## Output Requirements
- Provide evidence for every claim (file:line references)
- No speculation without verification
- Explain the "why" not just the "what"
- Identify potential issues or edge cases'

    CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
    printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":%s}}' "$CONTEXT_ESCAPED"
    exit 0
fi

# =============================================================================
# ULTRATHINK MODE - Extended reasoning
# =============================================================================
if [[ "$PROMPT_LOWER" =~ (ultrathink|think[[:space:]]deeply|deep[[:space:]]analysis|think[[:space:]]hard|careful[[:space:]]analysis|thoroughly[[:space:]]analyze) ]]; then

    CONTEXT='[ULTRATHINK MODE ACTIVE]

Extended reasoning before any action.

## Thinking Protocol
1. Use Task(subagent_type="oh-my-claude:deep-explorer") to thoroughly understand context
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
# ULTRADEBUG MODE - Systematic debugging
# =============================================================================
if [[ "$PROMPT_LOWER" =~ (ultradebug|debug[[:space:]]this|fix[[:space:]]this[[:space:]]bug|troubleshoot|diagnose|why[[:space:]]is[[:space:]]this[[:space:]]failing|root[[:space:]]cause) ]]; then

    CONTEXT='[ULTRADEBUG MODE ACTIVE]

Systematic debugging with evidence-based diagnosis.

## Debug Protocol
1. REPRODUCE - Understand the exact failure condition
2. ISOLATE - Narrow down to the smallest failing case
3. TRACE - Follow execution path with Task(subagent_type="oh-my-claude:deep-explorer")
4. HYPOTHESIZE - Form 2-3 theories about root cause
5. VERIFY - Test each hypothesis with evidence
6. FIX - Apply minimal fix to address root cause
7. VALIDATE - Confirm fix works and no regression

## Evidence Requirements
- Every hypothesis must have supporting evidence
- Use actual code references (file:line)
- Check recent changes (git log, git diff)
- Verify fix with tests

## Parallel Investigation
- Launch multiple explorers for different hypotheses
- One for the failing code path
- One for related/similar code that works'

    CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
    printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":%s}}' "$CONTEXT_ESCAPED"
    exit 0
fi

# No trigger - pass through
exit 0
