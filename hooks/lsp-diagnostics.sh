#!/bin/bash
# lsp-diagnostics.sh
# PostToolUse hook: Runs language-specific diagnostics after Edit/Write operations
# Provides immediate feedback on code quality issues

set -euo pipefail

INPUT=$(cat)

# Extract tool name and file path from hook input
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

# Only process Edit and Write tools
if [[ "$TOOL_NAME" != "Edit" && "$TOOL_NAME" != "Write" ]]; then
    exit 0
fi

# Need a file path to analyze
if [[ -z "$FILE_PATH" || ! -f "$FILE_PATH" ]]; then
    exit 0
fi

# Get file extension
EXT="${FILE_PATH##*.}"

# Run appropriate diagnostic based on file type
DIAGNOSTICS=""
SEVERITY="info"

run_diagnostic() {
    local cmd="$1"
    local args="$2"

    if command -v "$cmd" &>/dev/null; then
        # Run diagnostic, capture output and exit code
        local output
        output=$($cmd $args "$FILE_PATH" 2>&1) || true
        if [[ -n "$output" ]]; then
            DIAGNOSTICS="$output"
            # Determine severity based on output patterns
            if echo "$output" | grep -qiE 'error|fatal|critical'; then
                SEVERITY="error"
            elif echo "$output" | grep -qiE 'warning|warn'; then
                SEVERITY="warning"
            fi
        fi
    fi
}

case "$EXT" in
    sh|bash)
        # Shellcheck for shell scripts
        if command -v shellcheck &>/dev/null; then
            DIAGNOSTICS=$(shellcheck -f gcc "$FILE_PATH" 2>&1) || true
            if [[ -n "$DIAGNOSTICS" ]]; then
                if echo "$DIAGNOSTICS" | grep -q ':.*: error:'; then
                    SEVERITY="error"
                elif echo "$DIAGNOSTICS" | grep -q ':.*: warning:'; then
                    SEVERITY="warning"
                fi
            fi
        fi
        ;;

    ts|tsx|mts|cts)
        # TypeScript type checking
        if command -v tsc &>/dev/null; then
            # Run tsc on just this file, quick check
            DIAGNOSTICS=$(tsc --noEmit --pretty false "$FILE_PATH" 2>&1) || true
            if [[ -n "$DIAGNOSTICS" && "$DIAGNOSTICS" != *"error TS"*"Cannot find"* ]]; then
                SEVERITY="error"
            fi
        fi
        ;;

    js|jsx|mjs|cjs)
        # ESLint for JavaScript
        if command -v eslint &>/dev/null; then
            DIAGNOSTICS=$(eslint --format compact "$FILE_PATH" 2>&1) || true
            if [[ -n "$DIAGNOSTICS" ]]; then
                if echo "$DIAGNOSTICS" | grep -q ' Error -'; then
                    SEVERITY="error"
                elif echo "$DIAGNOSTICS" | grep -q ' Warning -'; then
                    SEVERITY="warning"
                fi
            fi
        fi
        ;;

    py)
        # Python: prefer ruff (fast), fall back to pyright
        if command -v ruff &>/dev/null; then
            DIAGNOSTICS=$(ruff check --output-format=concise "$FILE_PATH" 2>&1) || true
            if [[ -n "$DIAGNOSTICS" ]]; then
                SEVERITY="warning"
            fi
        elif command -v pyright &>/dev/null; then
            DIAGNOSTICS=$(pyright --outputjson "$FILE_PATH" 2>&1 | jq -r '.generalDiagnostics[]? | "\(.file):\(.range.start.line): \(.severity): \(.message)"' 2>/dev/null) || true
            if echo "$DIAGNOSTICS" | grep -q ': error:'; then
                SEVERITY="error"
            fi
        fi
        ;;

    go)
        # Go vet for Go files
        if command -v go &>/dev/null; then
            DIAGNOSTICS=$(go vet "$FILE_PATH" 2>&1) || true
            if [[ -n "$DIAGNOSTICS" ]]; then
                SEVERITY="warning"
            fi
        fi
        ;;

    rs)
        # Rust: cargo check (requires being in cargo project)
        # Note: This only works if we're in a cargo workspace
        if command -v cargo &>/dev/null; then
            local cargo_dir
            cargo_dir=$(dirname "$FILE_PATH")
            while [[ "$cargo_dir" != "/" ]]; do
                if [[ -f "$cargo_dir/Cargo.toml" ]]; then
                    DIAGNOSTICS=$(cd "$cargo_dir" && cargo check --message-format=short 2>&1 | head -20) || true
                    if echo "$DIAGNOSTICS" | grep -q '^error'; then
                        SEVERITY="error"
                    elif echo "$DIAGNOSTICS" | grep -q '^warning'; then
                        SEVERITY="warning"
                    fi
                    break
                fi
                cargo_dir=$(dirname "$cargo_dir")
            done
        fi
        ;;

    json)
        # JSON syntax validation
        if command -v jq &>/dev/null; then
            if ! jq empty "$FILE_PATH" 2>&1; then
                DIAGNOSTICS=$(jq empty "$FILE_PATH" 2>&1) || true
                SEVERITY="error"
            fi
        fi
        ;;

    yaml|yml)
        # YAML validation
        if command -v yamllint &>/dev/null; then
            DIAGNOSTICS=$(yamllint -f parsable "$FILE_PATH" 2>&1) || true
            if echo "$DIAGNOSTICS" | grep -q '\[error\]'; then
                SEVERITY="error"
            elif echo "$DIAGNOSTICS" | grep -q '\[warning\]'; then
                SEVERITY="warning"
            fi
        fi
        ;;

    *)
        # No diagnostic available for this file type
        exit 0
        ;;
esac

# If no diagnostics, exit silently
if [[ -z "$DIAGNOSTICS" ]]; then
    exit 0
fi

# Truncate if too long
if [[ ${#DIAGNOSTICS} -gt 1500 ]]; then
    DIAGNOSTICS="${DIAGNOSTICS:0:1500}... (truncated)"
fi

# Format output based on severity
case "$SEVERITY" in
    error)
        HEADER="[LSP DIAGNOSTICS: ERRORS FOUND]"
        ;;
    warning)
        HEADER="[LSP DIAGNOSTICS: WARNINGS]"
        ;;
    *)
        HEADER="[LSP DIAGNOSTICS]"
        ;;
esac

CONTEXT="$HEADER
File: $FILE_PATH

$DIAGNOSTICS

Consider fixing these issues before proceeding."

CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":%s}}' "$CONTEXT_ESCAPED"

exit 0
