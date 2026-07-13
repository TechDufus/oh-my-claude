"""Tests for hooks.json command configuration."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
PLUGIN_ROOT = REPO_ROOT / "plugins" / "oh-my-claude"
HOOKS_DIR = PLUGIN_ROOT / "hooks"
HOOKS_CONFIG = HOOKS_DIR / "hooks.json"


def iter_command_hooks(value: object) -> Iterator[dict]:
    """Yield all command hook entries from nested hooks.json data."""
    if isinstance(value, dict):
        if value.get("type") == "command":
            yield value
        for child in value.values():
            yield from iter_command_hooks(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_command_hooks(child)


def test_command_hooks_use_structured_uv_args():
    """Every command hook should use current structured command/args form."""
    hooks_data = json.loads(HOOKS_CONFIG.read_text())
    command_hooks = list(iter_command_hooks(hooks_data))

    assert command_hooks

    for hook in command_hooks:
        assert hook["command"] == "uv"
        assert hook["args"][:2] == ["run", "--script"]

        script_args = [arg for arg in hook["args"] if arg.endswith(".py")]
        assert len(script_args) == 1

        script = Path(script_args[0].replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN_ROOT)))
        assert script.is_file(), f"Missing hook script: {script}"
        assert os.access(script, os.X_OK), f"Hook script is not executable: {script}"
