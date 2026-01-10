---
description: "Show LSP server and linter installation status: /lsp"
allowed-tools:
  - Bash(command:*)
---

# /lsp - LSP Diagnostics

Shows what language intelligence Claude Code has access to via oh-my-claude.

## Execution

**Step 1**: Run this compact check (outputs JSON):

```bash
echo "{\"lsp\":{$(for c in typescript-language-server pyright-langserver gopls rust-analyzer clangd jdtls intelephense solargraph lua-language-server sourcekit-lsp kotlin-language-server OmniSharp zls terraform-ls yaml-language-server docker-langserver; do command -v "$c" &>/dev/null && echo "\"$c\":1," || echo "\"$c\":0,"; done | tr -d '\n' | sed 's/,$//')},\"lint\":{$(for c in shellcheck tsc eslint ruff go cargo jq yamllint tflint luacheck markdownlint swiftlint ktlint dotnet zig hadolint; do command -v "$c" &>/dev/null && echo "\"$c\":1," || echo "\"$c\":0,"; done | tr -d '\n' | sed 's/,$//')}}"
```

**Step 2**: Parse the JSON and output this formatted diagnostic (substitute ✓ for 1, ✗ for 0):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  oh-my-claude LSP Diagnostics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  CONFIGURED LANGUAGE SERVERS

  Language          Server                        Status
  ─────────────────────────────────────────────────────────────────────
  TypeScript/JS     typescript-language-server    [✓/✗]
  Python            pyright-langserver            [✓/✗]
  Go                gopls                         [✓/✗]
  Rust              rust-analyzer                 [✓/✗]
  C/C++             clangd                        [✓/✗]
  Java              jdtls                         [✓/✗]
  PHP               intelephense                  [✓/✗]
  Ruby              solargraph                    [✓/✗]
  Lua               lua-language-server           [✓/✗]
  Swift             sourcekit-lsp                 [✓/✗]
  Kotlin            kotlin-language-server        [✓/✗]
  C#                OmniSharp                     [✓/✗]
  Zig               zls                           [✓/✗]
  Terraform         terraform-ls                  [✓/✗]
  YAML              yaml-language-server          [✓/✗]
  Dockerfile        docker-langserver             [✓/✗]

  CLI LINTER FALLBACKS

  Extension         Linter                        Status
  ─────────────────────────────────────────────────────────────────────
  .sh .bash         shellcheck                    [✓/✗]
  .ts .tsx          tsc                           [✓/✗]
  .js .jsx          eslint                        [✓/✗]
  .py               ruff                          [✓/✗]
  .go               go vet                        [✓/✗]
  .rs               cargo check                   [✓/✗]
  .json             jq                            [✓/✗]
  .yaml .yml        yamllint                      [✓/✗]
  .tf               tflint                        [✓/✗]
  .lua              luacheck                      [✓/✗]
  .md               markdownlint                  [✓/✗]
  .swift            swiftlint                     [✓/✗]
  .kt .kts          ktlint                        [✓/✗]
  .cs               dotnet build                  [✓/✗]
  .zig              zig ast-check                 [✓/✗]
  Dockerfile        hadolint                      [✓/✗]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SUMMARY

  LSP Servers:   X/16 ready
  CLI Linters:   Y/16 ready

  [If not all ready: Ask "how do I install missing LSP servers?" for help.]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Output this formatted text DIRECTLY in your response (not via bash echo). The bash command is just for gathering data - the formatted output should be your own text response.
