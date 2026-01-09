#!/bin/bash
# oh-my-claude installer
# Adds ultrawork hooks to your Claude Code settings

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
SETTINGS_FILE="${HOME}/.claude/settings.json"

echo "Installing oh-my-claude..."

# Check for jq
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq is required. Install with: brew install jq"
    exit 1
fi

# Check settings file exists
if [[ ! -f "$SETTINGS_FILE" ]]; then
    echo "ERROR: $SETTINGS_FILE not found"
    exit 1
fi

# Backup settings
cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak"
echo "Backed up settings to ${SETTINGS_FILE}.bak"

# Add UserPromptSubmit hook if not present
if jq -e '.hooks.UserPromptSubmit' "$SETTINGS_FILE" > /dev/null 2>&1; then
    echo "UserPromptSubmit hook already exists - updating..."
    jq --arg cmd "${PLUGIN_DIR}/hooks/ultrawork-detector.sh" \
       '.hooks.UserPromptSubmit = [{"hooks": [{"type": "command", "command": $cmd, "timeout": 5}]}]' \
       "$SETTINGS_FILE" > "${SETTINGS_FILE}.tmp" && mv "${SETTINGS_FILE}.tmp" "$SETTINGS_FILE"
else
    echo "Adding UserPromptSubmit hook..."
    jq --arg cmd "${PLUGIN_DIR}/hooks/ultrawork-detector.sh" \
       '.hooks.UserPromptSubmit = [{"hooks": [{"type": "command", "command": $cmd, "timeout": 5}]}]' \
       "$SETTINGS_FILE" > "${SETTINGS_FILE}.tmp" && mv "${SETTINGS_FILE}.tmp" "$SETTINGS_FILE"
fi

# Make hooks executable
chmod +x "${PLUGIN_DIR}/hooks/"*.sh

echo ""
echo "Installed! Restart Claude Code and use 'ultrawork' in any prompt."
echo ""
echo "Examples:"
echo "  ultrawork fix all the type errors"
echo "  ultrawork refactor the auth system"
echo "  ultrawork summarize this project"
