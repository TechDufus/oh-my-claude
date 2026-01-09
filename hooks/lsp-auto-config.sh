#!/bin/bash
# lsp-auto-config.sh
# SessionStart hook: Auto-detects project languages and checks LSP server availability

set -euo pipefail

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // "."')

# Get plugin root for install script reference
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"

# Language detection based on file presence
declare -A DETECTED_LANGS
declare -A LSP_SERVERS
declare -A INSTALL_CMDS

# Define LSP servers to check (command name to verify installation)
LSP_SERVERS=(
    ["typescript"]="typescript-language-server"
    ["python"]="pyright"
    ["go"]="gopls"
    ["rust"]="rust-analyzer"
    ["java"]="jdtls"
    ["c"]="clangd"
    ["php"]="intelephense"
    ["ruby"]="solargraph"
    ["kotlin"]="kotlin-language-server"
    ["swift"]="sourcekit-lsp"
)

# Smart install hints (using the install script)
INSTALL_CMDS=(
    ["typescript"]="./scripts/install-lsp.sh typescript  # uses bun > npm"
    ["python"]="./scripts/install-lsp.sh python  # uses uv > pipx > pip"
    ["go"]="./scripts/install-lsp.sh go  # uses go install"
    ["rust"]="./scripts/install-lsp.sh rust  # uses rustup > brew"
    ["java"]="./scripts/install-lsp.sh java  # uses brew or manual"
    ["c"]="./scripts/install-lsp.sh c  # uses brew or apt/dnf"
    ["php"]="./scripts/install-lsp.sh php  # uses bun > npm (intelephense)"
    ["ruby"]="gem install solargraph"
    ["kotlin"]="./scripts/install-lsp.sh kotlin  # uses brew"
    ["swift"]="(included with Xcode)"
)

# Detect languages in project
detect_languages() {
    local dir="$1"

    # TypeScript/JavaScript
    if [[ -f "$dir/package.json" ]] || [[ -f "$dir/tsconfig.json" ]] || \
       find "$dir" -maxdepth 3 \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) 2>/dev/null | head -1 | grep -q .; then
        DETECTED_LANGS["typescript"]=1
    fi

    # Python
    if [[ -f "$dir/pyproject.toml" ]] || [[ -f "$dir/setup.py" ]] || [[ -f "$dir/requirements.txt" ]] || \
       find "$dir" -maxdepth 3 -name "*.py" 2>/dev/null | head -1 | grep -q .; then
        DETECTED_LANGS["python"]=1
    fi

    # Go
    if [[ -f "$dir/go.mod" ]] || find "$dir" -maxdepth 3 -name "*.go" 2>/dev/null | head -1 | grep -q .; then
        DETECTED_LANGS["go"]=1
    fi

    # Rust
    if [[ -f "$dir/Cargo.toml" ]] || find "$dir" -maxdepth 3 -name "*.rs" 2>/dev/null | head -1 | grep -q .; then
        DETECTED_LANGS["rust"]=1
    fi

    # Java
    if [[ -f "$dir/pom.xml" ]] || [[ -f "$dir/build.gradle" ]] || \
       find "$dir" -maxdepth 3 -name "*.java" 2>/dev/null | head -1 | grep -q .; then
        DETECTED_LANGS["java"]=1
    fi

    # C/C++
    if [[ -f "$dir/CMakeLists.txt" ]] || [[ -f "$dir/Makefile" ]] || \
       find "$dir" -maxdepth 3 \( -name "*.c" -o -name "*.cpp" -o -name "*.h" -o -name "*.hpp" \) 2>/dev/null | head -1 | grep -q .; then
        DETECTED_LANGS["c"]=1
    fi

    # PHP
    if [[ -f "$dir/composer.json" ]] || find "$dir" -maxdepth 3 -name "*.php" 2>/dev/null | head -1 | grep -q .; then
        DETECTED_LANGS["php"]=1
    fi

    # Ruby
    if [[ -f "$dir/Gemfile" ]] || find "$dir" -maxdepth 3 -name "*.rb" 2>/dev/null | head -1 | grep -q .; then
        DETECTED_LANGS["ruby"]=1
    fi

    # Kotlin
    if find "$dir" -maxdepth 3 \( -name "*.kt" -o -name "*.kts" \) 2>/dev/null | head -1 | grep -q .; then
        DETECTED_LANGS["kotlin"]=1
    fi

    # Swift
    if [[ -f "$dir/Package.swift" ]] || find "$dir" -maxdepth 3 -name "*.swift" 2>/dev/null | head -1 | grep -q .; then
        DETECTED_LANGS["swift"]=1
    fi
}

# Check if LSP server is available
check_server() {
    local server="$1"
    command -v "$server" &>/dev/null
}

# Run detection
detect_languages "$CWD"

# If no languages detected, exit silently
if [[ ${#DETECTED_LANGS[@]} -eq 0 ]]; then
    exit 0
fi

# Build status report
AVAILABLE=()
MISSING=()
INSTALL_HINTS=()

for lang in "${!DETECTED_LANGS[@]}"; do
    server="${LSP_SERVERS[$lang]:-}"
    if [[ -n "$server" ]]; then
        if check_server "$server"; then
            AVAILABLE+=("$lang")
        else
            MISSING+=("$lang")
            INSTALL_HINTS+=("[$server] ${INSTALL_CMDS[$lang]:-unknown}")
        fi
    fi
done

# Only output if there are missing servers to report
if [[ ${#MISSING[@]} -gt 0 ]]; then
    for hint in "${INSTALL_HINTS[@]}"; do
        echo "$hint" >&2
    done
fi

# Output context for Claude
if [[ ${#AVAILABLE[@]} -gt 0 ]] || [[ ${#MISSING[@]} -gt 0 ]]; then
    CONTEXT="[oh-my-claude LSP Status]

Detected: ${!DETECTED_LANGS[*]}"

    if [[ ${#AVAILABLE[@]} -gt 0 ]]; then
        CONTEXT+="
Ready: ${AVAILABLE[*]} (LSP tools available: goToDefinition, findReferences, hover, getDiagnostics)"
    fi

    if [[ ${#MISSING[@]} -gt 0 ]]; then
        CONTEXT+="
Missing: ${MISSING[*]}
Install: ./scripts/install-lsp.sh <language>  (auto-detects best package manager)"
    fi

    # Check if LSP is enabled
    if [[ "${ENABLE_LSP_TOOL:-}" != "1" ]]; then
        CONTEXT+="

Enable LSP: export ENABLE_LSP_TOOL=1 (add to shell profile)"
    fi

    CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
    printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}' "$CONTEXT_ESCAPED"
fi

exit 0
