#!/bin/bash
# oh-my-claude installer
# Installs all hooks from hooks.json to your Claude Code settings

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
SETTINGS_FILE="${HOME}/.claude/settings.json"
HOOKS_CONFIG="${PLUGIN_DIR}/hooks/hooks.json"

echo "Installing oh-my-claude..."

# Check for jq
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq is required. Install with: brew install jq"
    exit 1
fi

# Check settings file exists
if [[ ! -f "$SETTINGS_FILE" ]]; then
    echo "Creating ${SETTINGS_FILE}..."
    mkdir -p "$(dirname "$SETTINGS_FILE")"
    echo '{}' > "$SETTINGS_FILE"
fi

# Check hooks config exists
if [[ ! -f "$HOOKS_CONFIG" ]]; then
    echo "ERROR: ${HOOKS_CONFIG} not found"
    exit 1
fi

# Backup settings
cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak"
echo "Backed up settings to ${SETTINGS_FILE}.bak"

# Make hooks executable
chmod +x "${PLUGIN_DIR}/hooks/"*.sh 2>/dev/null || true

# Read hooks config and substitute CLAUDE_PLUGIN_ROOT with actual path
HOOKS_JSON=$(cat "$HOOKS_CONFIG" | sed "s|\${CLAUDE_PLUGIN_ROOT}|${PLUGIN_DIR}|g")

# Get list of hook event types from our config
HOOK_EVENTS=$(echo "$HOOKS_JSON" | jq -r '.hooks | keys[]')

# Merge each hook event with existing settings
TEMP_SETTINGS=$(cat "$SETTINGS_FILE")

for EVENT in $HOOK_EVENTS; do
    echo "Adding ${EVENT} hooks..."

    # Get our hooks for this event
    OUR_HOOKS=$(echo "$HOOKS_JSON" | jq ".hooks.${EVENT}")

    # Get existing hooks for this event (if any)
    EXISTING_HOOKS=$(echo "$TEMP_SETTINGS" | jq ".hooks.${EVENT} // []")

    # Get our command paths to check for duplicates
    OUR_COMMANDS=$(echo "$OUR_HOOKS" | jq -r '.[].hooks[].command // empty')

    # Filter out any existing hooks that match our commands (to avoid duplicates)
    FILTERED_EXISTING="$EXISTING_HOOKS"
    for CMD in $OUR_COMMANDS; do
        FILTERED_EXISTING=$(echo "$FILTERED_EXISTING" | jq --arg cmd "$CMD" \
            '[.[] | select(.hooks | all(.command != $cmd))]')
    done

    # Merge: our hooks + filtered existing hooks
    MERGED_HOOKS=$(echo "$OUR_HOOKS" "$FILTERED_EXISTING" | jq -s 'add')

    # Update temp settings
    TEMP_SETTINGS=$(echo "$TEMP_SETTINGS" | jq --argjson hooks "$MERGED_HOOKS" \
        ".hooks.${EVENT} = \$hooks")
done

# Write final settings
echo "$TEMP_SETTINGS" | jq '.' > "$SETTINGS_FILE"

echo ""
echo "Installed oh-my-claude hooks:"
echo "$HOOK_EVENTS" | while read -r event; do
    echo "  - ${event}"
done
echo ""
echo "Restart Claude Code to activate."
echo ""
echo "Features enabled:"
echo "  - ultrawork mode (use 'ultrawork' in prompts)"
echo "  - Context Guardian (auto-delegation guidance)"
echo "  - LSP diagnostics (auto after Edit/Write if linters installed)"
echo "  - Todo continuation (prevents stopping with incomplete todos)"
echo "  - Context preservation (saves state before /compact)"
