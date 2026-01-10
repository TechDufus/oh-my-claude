#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
lsp_auto_config.py
SessionStart hook: Auto-detects project languages and checks LSP server availability
"""

import json
import os
import sys
from pathlib import Path
from shutil import which


# LSP servers to check (language -> command name)
LSP_SERVERS = {
    "typescript": "typescript-language-server",
    "python": "pyright",
    "go": "gopls",
    "rust": "rust-analyzer",
    "java": "jdtls",
    "c": "clangd",
    "php": "intelephense",
    "ruby": "solargraph",
    "kotlin": "kotlin-language-server",
    "swift": "sourcekit-lsp",
}

# Install hints for missing servers
INSTALL_CMDS = {
    "typescript": "./scripts/install-lsp.sh typescript  # uses bun > npm",
    "python": "./scripts/install-lsp.sh python  # uses uv > pipx > pip",
    "go": "./scripts/install-lsp.sh go  # uses go install",
    "rust": "./scripts/install-lsp.sh rust  # uses rustup > brew",
    "java": "./scripts/install-lsp.sh java  # uses brew or manual",
    "c": "./scripts/install-lsp.sh c  # uses brew or apt/dnf",
    "php": "./scripts/install-lsp.sh php  # uses bun > npm (intelephense)",
    "ruby": "gem install solargraph",
    "kotlin": "./scripts/install-lsp.sh kotlin  # uses brew",
    "swift": "(included with Xcode)",
}


def find_files_with_extensions(directory: Path, extensions: list[str], max_depth: int = 3) -> bool:
    """Check if any files with given extensions exist within max_depth."""
    def search(path: Path, depth: int) -> bool:
        if depth > max_depth:
            return False
        try:
            for entry in path.iterdir():
                if entry.is_file() and entry.suffix in extensions:
                    return True
                if entry.is_dir() and not entry.name.startswith('.'):
                    if search(entry, depth + 1):
                        return True
        except PermissionError:
            pass
        return False
    return search(directory, 1)


def detect_languages(directory: Path) -> set[str]:
    """Detect languages in project based on file presence."""
    detected = set()

    # TypeScript/JavaScript
    if ((directory / "package.json").exists() or
        (directory / "tsconfig.json").exists() or
        find_files_with_extensions(directory, [".ts", ".tsx", ".js", ".jsx"])):
        detected.add("typescript")

    # Python
    if ((directory / "pyproject.toml").exists() or
        (directory / "setup.py").exists() or
        (directory / "requirements.txt").exists() or
        find_files_with_extensions(directory, [".py"])):
        detected.add("python")

    # Go
    if ((directory / "go.mod").exists() or
        find_files_with_extensions(directory, [".go"])):
        detected.add("go")

    # Rust
    if ((directory / "Cargo.toml").exists() or
        find_files_with_extensions(directory, [".rs"])):
        detected.add("rust")

    # Java
    if ((directory / "pom.xml").exists() or
        (directory / "build.gradle").exists() or
        find_files_with_extensions(directory, [".java"])):
        detected.add("java")

    # C/C++
    if ((directory / "CMakeLists.txt").exists() or
        (directory / "Makefile").exists() or
        find_files_with_extensions(directory, [".c", ".cpp", ".h", ".hpp"])):
        detected.add("c")

    # PHP
    if ((directory / "composer.json").exists() or
        find_files_with_extensions(directory, [".php"])):
        detected.add("php")

    # Ruby
    if ((directory / "Gemfile").exists() or
        find_files_with_extensions(directory, [".rb"])):
        detected.add("ruby")

    # Kotlin
    if find_files_with_extensions(directory, [".kt", ".kts"]):
        detected.add("kotlin")

    # Swift
    if ((directory / "Package.swift").exists() or
        find_files_with_extensions(directory, [".swift"])):
        detected.add("swift")

    return detected


def check_server(server: str) -> bool:
    """Check if LSP server is available."""
    return which(server) is not None


def main() -> None:
    # Read input from stdin
    input_data = json.loads(sys.stdin.read())
    cwd = Path(input_data.get("cwd", "."))

    # Detect languages
    detected_langs = detect_languages(cwd)

    # If no languages detected, exit silently
    if not detected_langs:
        sys.exit(0)

    # Build status report
    available = []
    missing = []
    install_hints = []

    for lang in detected_langs:
        server = LSP_SERVERS.get(lang)
        if server:
            if check_server(server):
                available.append(lang)
            else:
                missing.append(lang)
                install_hints.append(f"[{server}] {INSTALL_CMDS.get(lang, 'unknown')}")

    # Output install hints for missing servers to stderr
    if missing:
        for hint in install_hints:
            print(hint, file=sys.stderr)

    # Output context for Claude
    if available or missing:
        context_parts = [
            "[oh-my-claude LSP Status]",
            "",
            f"Detected: {' '.join(sorted(detected_langs))}"
        ]

        if available:
            context_parts.append(
                f"Ready: {' '.join(sorted(available))} (LSP tools available: goToDefinition, findReferences, hover, getDiagnostics)"
            )

        if missing:
            context_parts.extend([
                f"Missing: {' '.join(sorted(missing))}",
                "Install: ./scripts/install-lsp.sh <language>  (auto-detects best package manager)"
            ])

        # Check if LSP is enabled
        if os.environ.get("ENABLE_LSP_TOOL") != "1":
            context_parts.extend([
                "",
                "Enable LSP: export ENABLE_LSP_TOOL=1 (add to shell profile)"
            ])

        context = "\n".join(context_parts)

        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context
            }
        }
        print(json.dumps(output))


if __name__ == "__main__":
    main()
