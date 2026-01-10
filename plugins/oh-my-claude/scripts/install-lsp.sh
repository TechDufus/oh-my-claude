#!/usr/bin/env bash
# install-lsp.sh
# Smart LSP server installer - detects OS/arch and uses best available package manager
#
# Priority chains:
#   Node.js: bun > npm > yarn > pnpm
#   Python:  uv > pipx > pip3 > pip
#   System:  brew (macOS) > apt/dnf/pacman (Linux)

set -euo pipefail

# Colors (if terminal supports it)
if [[ -t 1 ]]; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    GREEN='' RED='' YELLOW='' BLUE='' NC=''
fi

usage() {
    cat <<EOF
Usage: install-lsp.sh <language> [options]

Languages:
  typescript, ts    TypeScript/JavaScript (typescript-language-server)
  python, py        Python (pyright)
  go                Go (gopls)
  rust, rs          Rust (rust-analyzer)
  java              Java (jdtls)
  c, cpp            C/C++ (clangd)
  php               PHP (intelephense or phpactor)
  ruby, rb          Ruby (solargraph)
  kotlin, kt        Kotlin (kotlin-language-server)
  swift             Swift (sourcekit-lsp)
  all               Check/install common languages

Options:
  --check           Only check if installed, don't install
  --verbose         Show detailed output
  --help, -h        Show this help

Package Manager Priority:
  Node.js:  bun > npm > yarn > pnpm
  Python:   uv > pipx > pip3 > pip
  System:   brew (macOS) > apt/dnf/pacman/apk (Linux)

Examples:
  install-lsp.sh typescript
  install-lsp.sh all --check
  install-lsp.sh python --verbose
EOF
    exit 0
}

# Detect OS and architecture
detect_os() {
    case "$(uname -s)" in
        Darwin*) echo "macos" ;;
        Linux*)  echo "linux" ;;
        MINGW*|CYGWIN*|MSYS*) echo "windows" ;;
        *) echo "unknown" ;;
    esac
}

detect_arch() {
    case "$(uname -m)" in
        x86_64|amd64) echo "x64" ;;
        arm64|aarch64) echo "arm64" ;;
        armv7l) echo "arm" ;;
        *) echo "unknown" ;;
    esac
}

# Check if command exists
has_cmd() {
    command -v "$1" &>/dev/null
}

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# =============================================================================
# Package Manager Detection
# =============================================================================

# Get best Node.js package manager (bun preferred)
get_node_pm() {
    if has_cmd bun; then echo "bun"
    elif has_cmd npm; then echo "npm"
    elif has_cmd yarn; then echo "yarn"
    elif has_cmd pnpm; then echo "pnpm"
    else echo ""
    fi
}

# Get best Python package manager (uv preferred)
get_python_pm() {
    if has_cmd uv; then echo "uv"
    elif has_cmd pipx; then echo "pipx"
    elif has_cmd pip3; then echo "pip3"
    elif has_cmd pip; then echo "pip"
    else echo ""
    fi
}

# Get system package manager
get_system_pm() {
    local os=$(detect_os)
    if [[ "$os" == "macos" ]]; then
        if has_cmd brew; then echo "brew"; else echo ""; fi
    elif [[ "$os" == "linux" ]]; then
        if has_cmd apt; then echo "apt"
        elif has_cmd dnf; then echo "dnf"
        elif has_cmd pacman; then echo "pacman"
        elif has_cmd apk; then echo "apk"
        elif has_cmd zypper; then echo "zypper"
        else echo ""
        fi
    else
        echo ""
    fi
}

# =============================================================================
# Install Functions
# =============================================================================

install_typescript() {
    local pm=$(get_node_pm)
    if [[ -z "$pm" ]]; then
        log_error "No Node.js package manager found (bun, npm, yarn, pnpm)"
        log_info "Install bun: curl -fsSL https://bun.sh/install | bash"
        return 1
    fi

    log_info "Installing typescript-language-server via $pm..."
    case "$pm" in
        bun)  bun install -g typescript-language-server typescript ;;
        npm)  npm install -g typescript-language-server typescript ;;
        yarn) yarn global add typescript-language-server typescript ;;
        pnpm) pnpm add -g typescript-language-server typescript ;;
    esac
}

install_python() {
    local pm=$(get_python_pm)
    if [[ -z "$pm" ]]; then
        log_error "No Python package manager found (uv, pipx, pip)"
        log_info "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi

    log_info "Installing pyright via $pm..."
    case "$pm" in
        uv)    uv tool install pyright ;;
        pipx)  pipx install pyright ;;
        pip3)  pip3 install --user pyright ;;
        pip)   pip install --user pyright ;;
    esac
}

install_go() {
    if ! has_cmd go; then
        log_error "Go not installed"
        log_info "Install from: https://go.dev/dl/"
        return 1
    fi

    log_info "Installing gopls via go install..."
    go install golang.org/x/tools/gopls@latest

    # Check if GOPATH/bin is in PATH
    local gobin="${GOPATH:-$HOME/go}/bin"
    if [[ ":$PATH:" != *":$gobin:"* ]]; then
        log_warn "Add to PATH: export PATH=\"\$PATH:$gobin\""
    fi
}

install_rust() {
    if has_cmd rustup; then
        log_info "Installing rust-analyzer via rustup..."
        rustup component add rust-analyzer
    elif has_cmd brew && [[ "$(detect_os)" == "macos" ]]; then
        log_info "Installing rust-analyzer via brew..."
        brew install rust-analyzer
    else
        log_error "rustup not found"
        log_info "Install from: https://rustup.rs"
        return 1
    fi
}

install_java() {
    local pm=$(get_system_pm)
    local os=$(detect_os)

    if [[ "$os" == "macos" && "$pm" == "brew" ]]; then
        log_info "Installing jdtls via brew..."
        brew install jdtls
    elif [[ "$os" == "linux" ]]; then
        case "$pm" in
            apt)
                log_info "Installing eclipse-jdt-ls via apt..."
                sudo apt update && sudo apt install -y default-jdk
                log_warn "jdtls requires manual download from Eclipse"
                log_info "Download: https://download.eclipse.org/jdtls/snapshots/"
                ;;
            *)
                log_warn "Manual install required for jdtls"
                log_info "Download: https://download.eclipse.org/jdtls/snapshots/"
                ;;
        esac
    else
        log_warn "Manual install required for jdtls"
        log_info "Download: https://download.eclipse.org/jdtls/snapshots/"
        return 1
    fi
}

install_c() {
    local pm=$(get_system_pm)
    local os=$(detect_os)

    if [[ "$os" == "macos" ]]; then
        if [[ "$pm" == "brew" ]]; then
            log_info "Installing clangd via brew..."
            brew install llvm
            log_info "Add to PATH: export PATH=\"\$(brew --prefix llvm)/bin:\$PATH\""
        else
            log_info "Installing via Xcode Command Line Tools..."
            xcode-select --install 2>/dev/null || log_ok "Xcode tools already installed"
        fi
    elif [[ "$os" == "linux" ]]; then
        case "$pm" in
            apt)    log_info "Installing clangd..."; sudo apt update && sudo apt install -y clangd ;;
            dnf)    log_info "Installing clangd..."; sudo dnf install -y clang-tools-extra ;;
            pacman) log_info "Installing clangd..."; sudo pacman -S --noconfirm clang ;;
            apk)    log_info "Installing clangd..."; sudo apk add clang-extra-tools ;;
            *)      log_error "Unknown package manager"; return 1 ;;
        esac
    else
        log_error "Unsupported OS for clangd installation"
        return 1
    fi
}

install_php() {
    local node_pm=$(get_node_pm)

    # Prefer intelephense (Node-based, better features)
    if [[ -n "$node_pm" ]]; then
        log_info "Installing intelephense via $node_pm..."
        case "$node_pm" in
            bun)  bun install -g intelephense ;;
            npm)  npm install -g intelephense ;;
            yarn) yarn global add intelephense ;;
            pnpm) pnpm add -g intelephense ;;
        esac
    elif has_cmd composer; then
        log_info "Installing phpactor via composer..."
        composer global require phpactor/phpactor
    else
        log_error "No package manager found (bun/npm for intelephense, or composer for phpactor)"
        return 1
    fi
}

install_ruby() {
    if ! has_cmd gem; then
        log_error "Ruby/gem not installed"
        log_info "Install Ruby from: https://www.ruby-lang.org/en/downloads/"
        return 1
    fi

    log_info "Installing solargraph via gem..."
    gem install solargraph
}

install_kotlin() {
    local pm=$(get_system_pm)
    local os=$(detect_os)

    if [[ "$os" == "macos" && "$pm" == "brew" ]]; then
        log_info "Installing kotlin-language-server via brew..."
        brew install kotlin-language-server
    else
        log_warn "Manual install required for kotlin-language-server"
        log_info "Download: https://github.com/fwcd/kotlin-language-server/releases"
        return 1
    fi
}

install_swift() {
    if has_cmd sourcekit-lsp; then
        log_ok "sourcekit-lsp already available (bundled with Swift toolchain)"
        return 0
    fi

    local os=$(detect_os)
    if [[ "$os" == "macos" ]]; then
        log_info "sourcekit-lsp is included with Xcode"
        log_info "Install Xcode from App Store or: xcode-select --install"
    else
        log_info "Install Swift toolchain from: https://swift.org/download/"
    fi
    return 1
}

# =============================================================================
# Check Functions
# =============================================================================

check_typescript() { has_cmd typescript-language-server; }
check_python() { has_cmd pyright-langserver || has_cmd pyright; }
check_go() { has_cmd gopls; }
check_rust() { has_cmd rust-analyzer; }
check_java() { has_cmd jdtls; }
check_c() { has_cmd clangd; }
check_php() { has_cmd intelephense || has_cmd phpactor; }
check_ruby() { has_cmd solargraph; }
check_kotlin() { has_cmd kotlin-language-server; }
check_swift() { has_cmd sourcekit-lsp; }

# =============================================================================
# Main
# =============================================================================

[[ $# -eq 0 ]] && usage

LANG_ARG=""
CHECK_ONLY=false
VERBOSE=false

for arg in "$@"; do
    case "$arg" in
        --check) CHECK_ONLY=true ;;
        --verbose) VERBOSE=true ;;
        --help|-h) usage ;;
        -*) log_error "Unknown option: $arg"; exit 1 ;;
        *) LANG_ARG="$arg" ;;
    esac
done

[[ -z "$LANG_ARG" ]] && usage

# Normalize language name
case "$LANG_ARG" in
    ts|typescript|js|javascript) LANG="typescript" ;;
    py|python) LANG="python" ;;
    golang|go) LANG="go" ;;
    rs|rust) LANG="rust" ;;
    java) LANG="java" ;;
    c|cpp|c++|cc) LANG="c" ;;
    php) LANG="php" ;;
    rb|ruby) LANG="ruby" ;;
    kt|kotlin) LANG="kotlin" ;;
    swift) LANG="swift" ;;
    all) LANG="all" ;;
    *) log_error "Unknown language: $LANG_ARG"; exit 1 ;;
esac

# Show environment info in verbose mode
if $VERBOSE; then
    echo "Environment:"
    echo "  OS: $(detect_os)"
    echo "  Arch: $(detect_arch)"
    echo "  Node PM: $(get_node_pm || echo 'none')"
    echo "  Python PM: $(get_python_pm || echo 'none')"
    echo "  System PM: $(get_system_pm || echo 'none')"
    echo ""
fi

# Select languages to process
if [[ "$LANG" == "all" ]]; then
    LANGS=(typescript python go rust c ruby php)
else
    LANGS=("$LANG")
fi

# Process each language
EXIT_CODE=0
for lang in "${LANGS[@]}"; do
    check_fn="check_$lang"
    install_fn="install_$lang"

    if $CHECK_ONLY; then
        if $check_fn 2>/dev/null; then
            log_ok "$lang: installed"
        else
            echo -e "${RED}✗${NC} $lang: not installed"
            EXIT_CODE=1
        fi
    else
        if $check_fn 2>/dev/null; then
            log_ok "$lang: already installed"
        else
            echo ""
            if $install_fn; then
                log_ok "$lang: installed successfully"
            else
                log_error "$lang: installation failed"
                EXIT_CODE=1
            fi
        fi
    fi
done

echo ""
echo -e "${BLUE}Remember:${NC} export ENABLE_LSP_TOOL=1"
exit $EXIT_CODE
