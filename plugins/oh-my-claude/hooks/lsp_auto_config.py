#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
lsp_auto_config.py
SessionStart hook: Auto-detects project languages and checks LSP server availability
"""

import os
from pathlib import Path

from hook_utils import (
    WHICH,
    hook_main,
    log_debug,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)


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

# Marker files that indicate a language without traversal
MARKER_FILES = {
    "package.json": "typescript",
    "tsconfig.json": "typescript",
    "pyproject.toml": "python",
    "setup.py": "python",
    "requirements.txt": "python",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "pom.xml": "java",
    "build.gradle": "java",
    "CMakeLists.txt": "c",
    "Makefile": "c",
    "composer.json": "php",
    "Gemfile": "ruby",
    "Package.swift": "swift",
}

# Extension to language mapping
EXTENSION_TO_LANG = {
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "typescript",
    ".jsx": "typescript",
    ".py": "python",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".cpp": "c",
    ".h": "c",
    ".hpp": "c",
    ".php": "php",
    ".rb": "ruby",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".swift": "swift",
}


def detect_languages(directory: Path) -> set[str]:
    """Detect languages in project based on file presence.

    Optimized to check marker files first (no traversal), then do a single
    filesystem walk to collect all extensions in one pass.
    """
    detected: set[str] = set()

    # Check marker files first (no traversal needed)
    for marker, lang in MARKER_FILES.items():
        if (directory / marker).exists():
            detected.add(lang)
            log_debug(f"marker file {marker} -> {lang}")

    # Single traversal to collect extensions
    found_extensions: set[str] = set()
    max_depth = 3

    try:
        for root, dirs, files in os.walk(directory):
            # Calculate depth relative to start directory
            rel_path = Path(root).relative_to(directory)
            depth = len(rel_path.parts) + 1 if rel_path.parts else 1

            if depth > max_depth:
                dirs[:] = []  # Don't descend further
                continue

            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            # Collect extensions from files
            for filename in files:
                ext = Path(filename).suffix
                if ext in EXTENSION_TO_LANG:
                    found_extensions.add(ext)

    except PermissionError:
        log_debug("permission error during directory traversal")

    # Map extensions to languages
    for ext in found_extensions:
        lang = EXTENSION_TO_LANG.get(ext)
        if lang:
            detected.add(lang)
            log_debug(f"extension {ext} -> {lang}")

    return detected


@hook_main("SessionStart")
def main() -> None:
    # Safe stdin reading with timeout and size limits
    raw_input = read_stdin_safe()
    input_data = parse_hook_input(raw_input)

    cwd = Path(input_data.get("cwd", "."))
    log_debug(f"detecting languages in {cwd}")

    # Detect languages
    detected_langs = detect_languages(cwd)

    # If no languages detected, exit silently
    if not detected_langs:
        log_debug("no languages detected")
        output_empty()
        return

    # Build status report using cached which lookups
    available: list[str] = []
    missing: list[str] = []
    install_hints: list[str] = []

    for lang in detected_langs:
        server = LSP_SERVERS.get(lang)
        if server:
            if WHICH.available(server):
                available.append(lang)
            else:
                missing.append(lang)
                install_hints.append(f"[{server}] {INSTALL_CMDS.get(lang, 'unknown')}")

    # Output install hints for missing servers to stderr
    if missing:
        import sys

        for hint in install_hints:
            print(hint, file=sys.stderr)

    # Output context for Claude
    if available or missing:
        context_parts = [
            "[oh-my-claude LSP Status]",
            "",
            f"Detected: {' '.join(sorted(detected_langs))}",
        ]

        if available:
            context_parts.append(
                f"Ready: {' '.join(sorted(available))} (LSP tools available: goToDefinition, findReferences, hover, getDiagnostics)"
            )

        if missing:
            context_parts.extend(
                [
                    f"Missing: {' '.join(sorted(missing))}",
                    "Install: ./scripts/install-lsp.sh <language>  (auto-detects best package manager)",
                ]
            )

        # Check if LSP is enabled
        if os.environ.get("ENABLE_LSP_TOOL") != "1":
            context_parts.extend(
                [
                    "",
                    "Enable LSP: export ENABLE_LSP_TOOL=1 (add to shell profile)",
                ]
            )

        context = "\n".join(context_parts)
        output_context("SessionStart", context)


if __name__ == "__main__":
    main()
