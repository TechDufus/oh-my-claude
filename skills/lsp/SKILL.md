---
name: lsp
description: "Show LSP server and linter support status. Displays what's installed, missing, and how to install."
allowed-tools:
  - Bash(which:*)
  - Bash(command:*)
---

# LSP Status Command

Shows which LSP servers and CLI linters are available for code diagnostics.

## Execution

Run these checks and format the output as shown below.

### Step 1: Check LSP Servers

Check each LSP server with `command -v <binary> &>/dev/null && echo "installed" || echo "missing"`:

| Language | Binary | Install Command |
|----------|--------|-----------------|
| TypeScript/JS | typescript-language-server | `npm i -g typescript-language-server typescript` |
| Python | pyright-langserver | `npm i -g pyright` |
| Bash | bash-language-server | `npm i -g bash-language-server` |
| Go | gopls | `go install golang.org/x/tools/gopls@latest` |
| Rust | rust-analyzer | `rustup component add rust-analyzer` |
| C/C++ | clangd | `brew install llvm` |
| Java | jdtls | Eclipse JDT Language Server |
| PHP | intelephense | `npm i -g intelephense` |
| Ruby | solargraph | `gem install solargraph` |
| Lua | lua-language-server | `brew install lua-language-server` |
| Zig | zls | `brew install zls` |
| Swift | sourcekit-lsp | Included with Xcode |
| Kotlin | kotlin-language-server | `brew install kotlin-language-server` |
| C# | OmniSharp | `brew install omnisharp` |
| Terraform | terraform-ls | `brew install hashicorp/tap/terraform-ls` |
| YAML | yaml-language-server | `npm i -g yaml-language-server` |
| Dockerfile | docker-langserver | `npm i -g dockerfile-language-server-nodejs` |

### Step 2: Check CLI Linters

Check each linter with `command -v <binary> &>/dev/null && echo "installed" || echo "missing"`:

| Extension | Binary | Install Command |
|-----------|--------|-----------------|
| .sh, .bash | shellcheck | `brew install shellcheck` |
| .ts, .tsx | tsc | `npm i -g typescript` |
| .js, .jsx | eslint | `npm i -g eslint` |
| .py | ruff | `pip install ruff` |
| .go | go | Already installed with Go |
| .rs | cargo | Already installed with Rust |
| .json | jq | `brew install jq` |
| .yaml, .yml | yamllint | `pip install yamllint` |
| .tf | tflint | `brew install tflint` |
| .lua | luacheck | `luarocks install luacheck` |
| .md | markdownlint | `npm i -g markdownlint-cli` |
| .swift | swiftlint | `brew install swiftlint` |
| .kt | ktlint | `brew install ktlint` |
| .cs | dotnet | `brew install dotnet` |
| .zig | zig | `brew install zig` |
| Dockerfile | hadolint | `brew install hadolint` |

### Step 3: Format Output

Present results in this EXACT format:

```
## LSP Server Status

| Language | Server | Status |
|----------|--------|--------|
| TypeScript/JS | typescript-language-server | ✓ Installed |
| Python | pyright-langserver | ✗ Missing |
...

## CLI Linter Status

| Extension | Linter | Status |
|-----------|--------|--------|
| .sh/.bash | shellcheck | ✓ Installed |
| .py | ruff | ✗ Missing |
...

## Missing Tools

To install missing tools:

### LSP Servers
- pyright-langserver: `npm i -g pyright`
...

### CLI Linters
- ruff: `pip install ruff`
...
```

### Output Rules

1. Use `✓ Installed` (green implied) for found tools
2. Use `✗ Missing` (red implied) for missing tools
3. Only show "Missing Tools" section if there ARE missing tools
4. Group install commands by package manager (npm, pip, brew, etc.)
5. Keep output clean and scannable

### Example Bash Commands

```bash
# Check single tool
command -v typescript-language-server &>/dev/null && echo "✓ Installed" || echo "✗ Missing"

# Check multiple tools efficiently
for cmd in typescript-language-server pyright-langserver gopls; do
  if command -v "$cmd" &>/dev/null; then
    echo "$cmd: ✓ Installed"
  else
    echo "$cmd: ✗ Missing"
  fi
done
```

Execute the checks and present the formatted output to the user.
