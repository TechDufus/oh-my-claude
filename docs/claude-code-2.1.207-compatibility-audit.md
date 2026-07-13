# Claude Code 2.1.207 Compatibility Audit

Date: 2026-07-13

## Summary

This pass updates oh-my-claude from a plugin that was last compatibility-touched around the early/mid Claude Code 2.1 series to one validated against `@anthropic-ai/claude-code@2.1.207`.

The highest-risk drift was not cosmetic:

- `PermissionRequest` hook output had moved to `hookSpecificOutput.decision.behavior`; the old top-level `permissionDecision` shape could make safe permission approvals/denials ineffective.
- Plugin-root `CLAUDE.md` is no longer loaded as runtime context; the runtime guidance needed to become an actual skill.
- `agents/CLAUDE.md` was being treated as an agent definition by the current validator.
- Agent-team guidance still referenced old/nonexistent `TeamCreate` and `Agent(team_name=...)` flows.
- Several skills/commands still allowed the old `Task` tool name instead of current `Agent`.

## Version Mapping

Current target:

- npm reports `@anthropic-ai/claude-code` latest as `2.1.207`, modified `2026-07-11T00:51:17.634Z`.
- Local installed `claude` was `2.1.37`, so all validation in this pass uses `npx -y @anthropic-ai/claude-code@2.1.207`.

Repo baseline:

- Remote `main` tip before this branch: `0905e45` (`2026-05-14`) `fix: Windows compatibility for stdin reading in hooks (#10)`.
- Last explicit compatibility PR: `#16`, merged `2026-04-13`, `fix(plugin): refresh Claude Code compatibility`.
- Earlier compatibility commit: `7926ed8` (`2026-02-11`) `fix(hooks,agents): adopt Claude Code 2.1.x features (v0.11.1)`.

Probable Claude Code correspondence:

- `7926ed8` was in the same week as Claude Code `2.1.37`-`2.1.41` releases, based on the official changelog dates. That commit likely targeted early `2.1.x` behavior.
- PR `#16` was around the `2.1.105`-`2.1.113` window and mostly addressed `Task(...)` to `Agent(...)` naming plus unsupported plugin-agent frontmatter.
- The latest remote commit on `2026-05-14` falls in the official Week 20 digest range (`2.1.139`-`2.1.142`), though the exact authoring CLI version was not recorded.

## Official Sources Reviewed

- Claude Code plugins: https://code.claude.com/docs/en/plugins
- Plugins reference: https://code.claude.com/docs/en/plugins-reference
- Hooks reference: https://code.claude.com/docs/en/hooks
- Skills: https://code.claude.com/docs/en/skills
- Subagents: https://code.claude.com/docs/en/sub-agents
- Agent teams: https://code.claude.com/docs/en/agent-teams
- What's new: https://code.claude.com/docs/en/whats-new
- Changelog: https://code.claude.com/docs/en/changelog

## Component Inventory

### Marketplace

Files:

- `.claude-plugin/marketplace.json`
- `plugins/oh-my-claude/.claude-plugin/plugin.json`

Current status:

- Marketplace source path remains correct: `./plugins/oh-my-claude`.
- Version bumped to `0.14.0` in all required locations.
- Skill list now includes `./skills/oh-my-claude-runtime`.

### Hooks

Config:

- `plugins/oh-my-claude/hooks/hooks.json`

Hook scripts:

- `agent_usage_reminder.py`
- `claudemd_health.py`
- `commit_quality_enforcer.py`
- `context_guardian.py`
- `context_monitor.py`
- `danger_blocker.py`
- `delegation_enforcer.py`
- `edit_error_recovery.py`
- `notification_alert.py`
- `openkanban_status.py`
- `plan_execution_injector.py`
- `precompact_context.py`
- `safe_permissions.py`
- `tdd_enforcer.py`
- `todo_enforcer.py`
- `ultrawork_detector.py`
- `verification_reminder.py`

Updates made:

- Converted hook handlers from shell command strings to structured `command: "uv"` plus `args`.
- Updated `output_permission()` for current `PermissionRequest` schema.
- Kept `Task` as a legacy alias in detection paths where current Claude Code still accepts it, but updated emitted guidance to prefer `Agent`.
- Replaced stale team spawning instructions with current natural-language teammate requests.

Not added:

- `PermissionDenied`, `PostToolBatch`, `PostToolUseFailure`, `InstructionsLoaded`, `ConfigChange`, `FileChanged`, and worktree hooks. These are real current extension points but not required for the plugin's existing intent.

### Agents

Plugin agents:

- `advisor`
- `code-reviewer`
- `critic`
- `librarian`
- `risk-assessor`
- `security-auditor`
- `validator`

Current supported frontmatter in use:

- `model: inherit`
- `memory: project`
- `color`
- `description`
- `disallowedTools: Write, Edit`

Updates made:

- Moved `agents/CLAUDE.md` to `docs/agents.md`; current `plugin validate --strict` treats `agents/*.md` as agent definitions.
- Kept `disallowedTools` for read-only/review agents.
- Removed public docs references to the removed `worker` agent.

Not added:

- `background`, `effort`, `maxTurns`, `isolation: worktree`, and agent `skills`. These are valid current fields, but the plugin's existing agents are mostly short-lived reviewers/readers. Add them only when a specific agent needs the behavior.

### Skills

Skills listed in plugin manifest:

- `debugger`
- `git-commit-validator`
- `init-deep`
- `oh-my-claude-runtime`
- `pr-creation`
- `ralph-loop-init`
- `ralph-plan`
- `receiving-code-review`
- `tdd`
- `verification`
- `worktree`
- `writing-skills`

Updates made:

- Migrated old plugin-root runtime guidance into `oh-my-claude-runtime`.
- Updated skill `allowed-tools` entries from `Task` to `Agent` where they referred to subagent spawning.

Future candidates:

- Add skill eval cases for trigger quality using the new `claude plugin eval` command.
- Consider `context: fork` for heavyweight research/debug skills only after testing whether isolation improves outcomes.

### Commands

Commands:

- `/prime` in `plugins/oh-my-claude/commands/prime.md`

Current status:

- Commands remain supported, but docs recommend `skills/` for new plugin capabilities.
- `/prime` is still command-shaped and argument-driven, so it stays as a command for now.
- Updated `allowed-tools` from `Task` to `Agent`.

### MCP

Config:

- `plugins/oh-my-claude/.mcp.json`

Servers:

- `sequential-thinking`
- `context7`

Current status:

- Plugin MCP server config still follows current plugin layout.
- No source changes were needed in this pass.

Watch item:

- Current docs require plugin-scoped MCP names in hook matchers when hooks target bundled MCP tools. oh-my-claude does not currently hook MCP tools, so no change was needed.

### LSP, Monitors, Themes, Bin, Settings

Current status:

- Not present.
- Current Claude Code supports these plugin components, but they are not required for oh-my-claude's intent as a workflow/guardrail plugin.

Recommended stance:

- Do not add LSP plugins here; users should install official language LSP plugins separately.
- Do not add monitors until the plugin has a concrete background watch use case.
- Do not use plugin `settings.json` to force a main-thread agent unless the plugin intentionally becomes a full behavior profile.

### Site and Docs

Updates made:

- Updated skill count from 11 to 12.
- Corrected lifecycle hook count to 17 where it was stale.
- Removed public `worker` references.
- Updated plugin structure documentation for current runtime-loading behavior and structured hook args.

## Validation Results

Completed for this branch:

- `jq empty plugins/oh-my-claude/.claude-plugin/plugin.json .claude-plugin/marketplace.json plugins/oh-my-claude/hooks/hooks.json`
- `npx -y @anthropic-ai/claude-code@2.1.207 plugin validate --strict .` passed
- `npx -y @anthropic-ai/claude-code@2.1.207 plugin validate --strict plugins/oh-my-claude` passed
- `uv run --with pytest pytest . -q` from `tests/oh-my-claude/hooks`: `920 passed`
- `uv tool run ruff check plugins/oh-my-claude/hooks tests/oh-my-claude/hooks` passed
- `git diff --check` passed

## Follow-Up Backlog

- Add plugin eval cases for `ultrawork`, plan mode, verification reminder, and commit/PR skill routing.
- Add strict `claude plugin validate --strict` checks to GitHub Actions when workflow-file updates can be pushed.
- Add focused tests asserting `safe_permissions.py` emits current `PermissionRequest` JSON, not just helper-level tests.
- Consider a `PostToolBatch` hook if context reminders should fire once per parallel batch instead of per tool.
- Evaluate whether `precompact_context.py` should also implement `PostCompact` recovery behavior.
- Revisit agent team prompts after the feature leaves experimental status.
