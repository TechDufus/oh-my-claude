---
description: "Show LSP server and linter installation status: /lsp"
allowed-tools:
  - Bash(command:*)
  - Bash(which:*)
  - Bash(echo:*)
---

# /lsp - LSP and Linter Status

Shows which LSP servers and CLI linters are installed, helping users understand what code diagnostics are available.

## Usage

```
/lsp
```

## Execution

Run the detection script and format output exactly as shown.

### Step 1: Check All Tools

Run this bash script to check installations:

```bash
echo "## LSP Server Status"
echo ""
echo "| Language | Server | Status |"
echo "|----------|--------|--------|"

# Check each LSP server
check_cmd() { command -v "$1" &>/dev/null && echo "✓ Installed" || echo "✗ Missing"; }

echo "| TypeScript/JS | typescript-language-server | $(check_cmd typescript-language-server) |"
echo "| Python | pyright-langserver | $(check_cmd pyright-langserver) |"
echo "| Bash | bash-language-server | $(check_cmd bash-language-server) |"
echo "| Go | gopls | $(check_cmd gopls) |"
echo "| Rust | rust-analyzer | $(check_cmd rust-analyzer) |"
echo "| C/C++ | clangd | $(check_cmd clangd) |"
echo "| Java | jdtls | $(check_cmd jdtls) |"
echo "| PHP | intelephense | $(check_cmd intelephense) |"
echo "| Ruby | solargraph | $(check_cmd solargraph) |"
echo "| Lua | lua-language-server | $(check_cmd lua-language-server) |"
echo "| Zig | zls | $(check_cmd zls) |"
echo "| Swift | sourcekit-lsp | $(check_cmd sourcekit-lsp) |"
echo "| Kotlin | kotlin-language-server | $(check_cmd kotlin-language-server) |"
echo "| C# | OmniSharp | $(check_cmd OmniSharp) |"
echo "| Terraform | terraform-ls | $(check_cmd terraform-ls) |"
echo "| YAML | yaml-language-server | $(check_cmd yaml-language-server) |"
echo "| Dockerfile | docker-langserver | $(check_cmd docker-langserver) |"

echo ""
echo "## CLI Linter Status"
echo ""
echo "| Extension | Linter | Status |"
echo "|-----------|--------|--------|"

echo "| .sh/.bash | shellcheck | $(check_cmd shellcheck) |"
echo "| .ts/.tsx | tsc | $(check_cmd tsc) |"
echo "| .js/.jsx | eslint | $(check_cmd eslint) |"
echo "| .py | ruff | $(check_cmd ruff) |"
echo "| .go | go vet | $(check_cmd go) |"
echo "| .rs | cargo | $(check_cmd cargo) |"
echo "| .json | jq | $(check_cmd jq) |"
echo "| .yaml/.yml | yamllint | $(check_cmd yamllint) |"
echo "| .tf | tflint | $(check_cmd tflint) |"
echo "| .lua | luacheck | $(check_cmd luacheck) |"
echo "| .md | markdownlint | $(check_cmd markdownlint) |"
echo "| .swift | swiftlint | $(check_cmd swiftlint) |"
echo "| .kt | ktlint | $(check_cmd ktlint) |"
echo "| .cs | dotnet | $(check_cmd dotnet) |"
echo "| .zig | zig | $(check_cmd zig) |"
echo "| Dockerfile | hadolint | $(check_cmd hadolint) |"
```

### Step 2: Show Missing Tools

After displaying the tables, if there are missing tools, show install commands grouped by package manager:

```
## Install Missing Tools

### npm
npm i -g typescript-language-server typescript pyright bash-language-server yaml-language-server dockerfile-language-server-nodejs intelephense

### brew
brew install llvm lua-language-server zls kotlin-language-server hashicorp/tap/terraform-ls shellcheck jq hadolint swiftlint ktlint

### pip
pip install ruff yamllint

### Other
go install golang.org/x/tools/gopls@latest
rustup component add rust-analyzer
gem install solargraph
```

Only show install commands for tools that are actually missing.

## Output Style

- Use `✓ Installed` for found tools
- Use `✗ Missing` for missing tools
- Keep tables aligned and clean
- Group install commands by package manager
- Only show relevant install commands (skip if nothing missing for that manager)
