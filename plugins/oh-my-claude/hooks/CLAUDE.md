# Hooks

Python scripts that respond to Claude Code lifecycle events.

## Structure

```
hooks/
  hooks.json         # Auto-discovered config (events → scripts)
  hook_utils.py      # Shared utilities (ALWAYS import)
  {hook_name}.py     # Individual hook implementations
```

## Template

Every hook follows this structure:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
hook_name.py - Brief description.

Hook type: {PreToolUse|PostToolUse|SessionStart|UserPromptSubmit|etc.}
"""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    hook_main,
    log_debug,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

@hook_main("HookEventName")
def main() -> None:
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        output_empty()
        return

    # Hook logic here

if __name__ == "__main__":
    main()
```

## Input/Output

| Direction | Format | Access |
|-----------|--------|--------|
| Input | JSON from stdin | `read_stdin_safe()` → `parse_hook_input()` |
| Output | JSON to stdout | `output_empty()`, `output_context()`, `output_block()` |
| Debug | stderr | `log_debug()` (only when `HOOK_DEBUG=1`) |

## Output Functions

| Function | When | Effect |
|----------|------|--------|
| `output_empty()` | Pass through | No modification |
| `output_context(event, ctx)` | Add context | Injects into conversation |
| `output_block(event, reason)` | Block action | Prevents tool execution |
| `output_permission(decision)` | Permission hooks | `allow`, `deny`, or `ask` |

## Configuration

Environment variables for user customization:

```python
def get_threshold() -> int:
    return int(os.environ.get("OMC_THRESHOLD", "100"))

def is_enabled() -> bool:
    return os.environ.get("OMC_FEATURE", "1").lower() not in ("0", "false", "no")
```

## Anti-Patterns

- Don't skip `@hook_main` decorator - handles all error recovery
- Don't print to stdout except via output functions
- Don't block stdin indefinitely - use `read_stdin_safe()`
- Don't import external packages without adding to `dependencies`
- Don't modify hook_utils.py without updating all dependents
