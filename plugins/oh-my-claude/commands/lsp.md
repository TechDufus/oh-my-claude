---
description: "Show LSP server and linter installation status: /lsp"
allowed-tools:
  - Bash(command:*)
  - Bash(which:*)
  - Bash(echo:*)
  - Bash(ls:*)
  - Bash(jq:*)
  - Bash(wc:*)
---

# /lsp - LSP Diagnostics

Shows what language intelligence Claude Code has access to via oh-my-claude.

## Execution

Run this single diagnostic script:

```bash
#!/usr/bin/env bash

# Colors/formatting via unicode
READY="✓"
MISSING="✗"

check() { command -v "$1" &>/dev/null && echo "$READY" || echo "$MISSING"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  oh-my-claude LSP Diagnostics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  CONFIGURED LANGUAGE SERVERS"
echo "  These have .lsp.json configs - Claude Code uses them when available"
echo ""
echo "  Language          Server                        Status"
echo "  ─────────────────────────────────────────────────────────────────────"

printf "  %-17s %-29s %s\n" "TypeScript/JS" "typescript-language-server" "$(check typescript-language-server)"
printf "  %-17s %-29s %s\n" "Python" "pyright-langserver" "$(check pyright-langserver)"
printf "  %-17s %-29s %s\n" "Go" "gopls" "$(check gopls)"
printf "  %-17s %-29s %s\n" "Rust" "rust-analyzer" "$(check rust-analyzer)"
printf "  %-17s %-29s %s\n" "C/C++" "clangd" "$(check clangd)"
printf "  %-17s %-29s %s\n" "Java" "jdtls" "$(check jdtls)"
printf "  %-17s %-29s %s\n" "PHP" "intelephense" "$(check intelephense)"
printf "  %-17s %-29s %s\n" "Ruby" "solargraph" "$(check solargraph)"
printf "  %-17s %-29s %s\n" "Lua" "lua-language-server" "$(check lua-language-server)"
printf "  %-17s %-29s %s\n" "Swift" "sourcekit-lsp" "$(check sourcekit-lsp)"
printf "  %-17s %-29s %s\n" "Kotlin" "kotlin-language-server" "$(check kotlin-language-server)"
printf "  %-17s %-29s %s\n" "C#" "OmniSharp" "$(check OmniSharp)"
printf "  %-17s %-29s %s\n" "Zig" "zls" "$(check zls)"
printf "  %-17s %-29s %s\n" "Terraform" "terraform-ls" "$(check terraform-ls)"
printf "  %-17s %-29s %s\n" "YAML" "yaml-language-server" "$(check yaml-language-server)"
printf "  %-17s %-29s %s\n" "Dockerfile" "docker-langserver" "$(check docker-langserver)"

echo ""
echo "  CLI LINTER FALLBACKS"
echo "  Used when LSP unavailable - checked after Edit/Write operations"
echo ""
echo "  Extension         Linter                        Status"
echo "  ─────────────────────────────────────────────────────────────────────"

printf "  %-17s %-29s %s\n" ".sh .bash" "shellcheck" "$(check shellcheck)"
printf "  %-17s %-29s %s\n" ".ts .tsx" "tsc" "$(check tsc)"
printf "  %-17s %-29s %s\n" ".js .jsx" "eslint" "$(check eslint)"
printf "  %-17s %-29s %s\n" ".py" "ruff" "$(check ruff)"
printf "  %-17s %-29s %s\n" ".go" "go vet" "$(check go)"
printf "  %-17s %-29s %s\n" ".rs" "cargo check" "$(check cargo)"
printf "  %-17s %-29s %s\n" ".json" "jq" "$(check jq)"
printf "  %-17s %-29s %s\n" ".yaml .yml" "yamllint" "$(check yamllint)"
printf "  %-17s %-29s %s\n" ".tf" "tflint" "$(check tflint)"
printf "  %-17s %-29s %s\n" ".lua" "luacheck" "$(check luacheck)"
printf "  %-17s %-29s %s\n" ".md" "markdownlint" "$(check markdownlint)"
printf "  %-17s %-29s %s\n" ".swift" "swiftlint" "$(check swiftlint)"
printf "  %-17s %-29s %s\n" ".kt .kts" "ktlint" "$(check ktlint)"
printf "  %-17s %-29s %s\n" ".cs" "dotnet build" "$(check dotnet)"
printf "  %-17s %-29s %s\n" ".zig" "zig ast-check" "$(check zig)"
printf "  %-17s %-29s %s\n" "Dockerfile" "hadolint" "$(check hadolint)"

# Count ready vs missing
LSP_READY=0
LSP_TOTAL=16
for cmd in typescript-language-server pyright-langserver gopls rust-analyzer clangd jdtls intelephense solargraph lua-language-server sourcekit-lsp kotlin-language-server OmniSharp zls terraform-ls yaml-language-server docker-langserver; do
    command -v "$cmd" &>/dev/null && ((LSP_READY++))
done

LINT_READY=0
LINT_TOTAL=16
for cmd in shellcheck tsc eslint ruff go cargo jq yamllint tflint luacheck markdownlint swiftlint ktlint dotnet zig hadolint; do
    command -v "$cmd" &>/dev/null && ((LINT_READY++))
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SUMMARY"
echo ""
echo "  LSP Servers:   $LSP_READY/$LSP_TOTAL ready"
echo "  CLI Linters:   $LINT_READY/$LINT_TOTAL ready"
echo ""
if [[ $LSP_READY -lt $LSP_TOTAL ]] || [[ $LINT_READY -lt $LINT_TOTAL ]]; then
    echo "  Ask \"how do I install missing LSP servers?\" for installation help."
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

## Output

The script produces a clean, aligned diagnostic view. Do NOT add markdown formatting around the output - display the script output directly.
