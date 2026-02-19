<img width="1328" height="611" alt="oh-my-claude_hero" src="https://github.com/user-attachments/assets/ca862678-da89-45c3-8385-fb45415c1b6e" />

<p align="center">
  <a href="https://github.com/TechDufus/oh-my-claude/blob/main/LICENSE"><img src="https://img.shields.io/github/license/TechDufus/oh-my-claude?style=flat-square" alt="License"></a>
  <a href="https://github.com/TechDufus/oh-my-claude/stargazers"><img src="https://img.shields.io/github/stars/TechDufus/oh-my-claude?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/TechDufus/oh-my-claude/issues"><img src="https://img.shields.io/github/issues/TechDufus/oh-my-claude?style=flat-square" alt="Issues"></a>
</p>

<p align="center">
  <img src="site/public/favicon.svg" alt="oh-my-claude mascot" width="80" height="80">
</p>

<h3 align="center">Enhance Claude Code with context protection and specialized quality gates.</h3>

---

## TL;DR — Skip This README

Just add a trigger word anywhere in your prompt:

```
fix all the type errors, ultrawork
ultraresearch best practices for API design
```

<p align="center">
  <a href="https://github.com/user-attachments/assets/0d1e3ccf-fdd6-4623-b17d-4ad33d198ee9"><img src="https://github.com/user-attachments/assets/0d1e3ccf-fdd6-4623-b17d-4ad33d198ee9" alt="Demo GIF"></a>
</p>


Claude will parallelize everything, delegate file reads to subagents, track progress with todos, and refuse to stop until the job is done. No partial implementations. No asking for permission. Just execution.

[Install it](#install) and start using it. Come back here when you want the details.

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Install](#install)
- [Magic Keywords](#magic-keywords)
- [What Ultrawork Actually Does](#what-ultrawork-actually-does)
- [The Agent Team](#the-agent-team)
- [Enhanced Plan Mode](#enhanced-plan-mode)
- [All Components](#all-components)
- [Integrations](#integrations)
- [For LLM Agents](#for-llm-agents)
- [Philosophy](#philosophy)
- [Contributing](#contributing)
- [Uninstall](#uninstall)

---

## Why This Exists

Claude Code is already intelligent. oh-my-claude makes it even better by:

- **Protecting your context** — Delegates file reading to subagents so your main session stays sharp
- **Adding quality gates** — Specialized agents for gap analysis, plan review, and validation
- **Working invisibly** — Hooks run in the background; you get a better experience just for having it installed
- **Staying out of the way** — Enhances Claude's capabilities without conflicting with its built-in intelligence

Install it and forget it. Your context is protected. Your plans get reviewed. Your work gets validated.

---

## Install

Supported on macOS and Linux. Windows support is planned.

### Step 1: Install uv (required)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

uv manages Python automatically. No separate Python install needed.

### Step 2: Install the plugin

```bash
# In Claude Code:
/plugin marketplace add TechDufus/oh-my-claude
/plugin install oh-my-claude@oh-my-claude
```

### Alternative: From Local Directory

```bash
git clone https://github.com/TechDufus/oh-my-claude /tmp/oh-my-claude
# In Claude Code:
/plugin marketplace add /tmp/oh-my-claude
/plugin install oh-my-claude@oh-my-claude
```

### Step 3: Restart Claude Code

Required for hooks to activate.

### Update

```bash
# Refresh marketplace
/plugin marketplace update oh-my-claude

# Update to latest version
/plugin update oh-my-claude@oh-my-claude
```

---

## Magic Keywords

| Keyword | Shortcut | Effect |
|---------|----------|--------|
| **ultrawork** | `ulw` | Maximum parallel execution — won't stop until done |
| **ultraresearch** | `ulr` | Exhaust online sources — parallel WebSearch, cross-reference, cite everything |
| **ultradebug** | `uld` | Systematic 7-step debugging with evidence-based diagnosis |

---

## What Ultrawork Actually Does

When you prefix a prompt with **ultrawork**, Claude's behavior changes fundamentally:

| Behavior | Normal Mode | Ultrawork Mode |
|----------|-------------|----------------|
| Task execution | Sequential, one at a time | **Parallel** — multiple subagents in ONE message |
| File reading | Loads into main context | **Delegated** — librarian subagent reads, you get summaries |
| Progress tracking | Optional | **Mandatory** — TodoWrite immediately, update in real-time |
| Stopping condition | After each step | **Only when ALL todos complete AND validation passes** |
| Partial solutions | Accepted | **Zero tolerance** — full implementation or nothing |
| Asking permission | Frequent | **Never** — makes reasonable decisions, documents them |

The hook intercepts your prompt, detects the keyword, and injects context that guides Claude toward quality gates and parallel execution.

---

## The Agent Team

Five specialized subagents complement Claude Code's built-in agents:

| Agent | What It Does |
|-------|--------------|
| **advisor** | Pre-planning gap analysis for hidden requirements and scope risks |
| **critic** | Plan review — finds flaws and edge cases BEFORE execution |
| **librarian** | Smart reading — summarizes large files, git diffs and changelogs |
| **validator** | QA — runs tests, linters, type checks, reports pass/fail |
| **worker** | Focused implementation — executes ONE specific task completely |

### Claude Code Built-in Agents

Claude Code provides these agents out of the box, which oh-my-claude leverages:

| Built-in Agent | What It Does |
|----------------|--------------|
| **Explore** | Find files, search codebase, locate definitions |
| **Plan** | Design implementation approaches, decompose complex tasks |
| **Task** | General-purpose implementation tasks |

### Usage

```
Task(subagent_type="oh-my-claude:librarian", prompt="Summarize src/auth/service.ts")
Task(subagent_type="oh-my-claude:critic", prompt="Review this implementation plan for flaws")
Task(subagent_type="oh-my-claude:worker", prompt="Add password reset endpoint")
Task(subagent_type="oh-my-claude:validator", prompt="Run all tests and report results")
```

### Why Subagents Matter

Subagent context is **isolated** from your main context. When a librarian reads a 2000-line file, those lines don't consume your context window — you get a summary. This keeps your main Claude sharp for reasoning instead of drowning in file contents.

---

## Enhanced Plan Mode

Enter plan mode (Shift+Tab) and get a structured 6-step pipeline automatically — no magic words needed:

1. **Recon** — Explore and librarian gather codebase context before questions
2. **Interview** — Smart, recon-informed questions (not generic prompts)
3. **Research** — Targeted deep research informed by your answers
4. **Gap Analysis** — Advisor agent catches hidden assumptions and scope risks
5. **Write Plan** — Structured plan with file:line refs, decisions, and risks
6. **Critic Review** — Critic must approve before plan exits

Cross-session continuity means "Accept and clear" carries the full execution context into the next session automatically.

**Optional keyword modes** — drop these in your prompt for specialized behavior:

| Keyword | Shortcut | What It Does |
|---------|----------|-------------|
| `ultrawork` | `ulw` | Maximum execution intensity with relentless task tracking |
| `ultraresearch` | `ulr` | Systematic parallel research with cross-referencing and citations |
| `ultradebug` | `uld` | Forensic debugging with multiple hypotheses and 3-strike escalation |

---

## All Components

### Hooks (Automatic)

| Hook | When | What |
|------|------|------|
| **context-guardian** | Session start | Injects context protection rules |
| **ultrawork-detector** | Prompt submit | Detects keywords, injects execution directives |
| **safe-permissions** | Permission request | Auto-approves safe commands (tests, linters, readonly) |
| **todo-enforcer** | Stop | Prevents stopping with incomplete todos |
| **context-monitor** | Post tool use | Warns at high context usage |
| **subagent-quality-validator** | Subagent stop | Validates subagent outputs before completion |
| **precompact-context** | Pre compact | Preserves session state before compaction |

### Commands

| Command | Description |
|---------|-------------|
| `/prime` | Context recovery after /clear |

### Skills

| Skill | Trigger |
|-------|---------|
| **git-commit-validator** | Commit requests — "commit", "ship it", "push this" |
| **pr-creation** | PR requests — "create PR", "open PR", "ready for review" |
| **worktree** | `/worktree` — Git worktree automation for isolated development |
| **init-deep** | `/init-deep` — Initialize nested CLAUDE.md structure |
| **ralph-plan** | `/ralph-plan <topic>` — Structured PRD generation with interview and research |
| **ralph-loop-init** | `/ralph-loop-init` — Transform approved plans into ralph loop infrastructure |
| **debugger** | `/debugger` — Systematic debugging methodology guidance |

---

## Integrations

### OpenKanban

**[OpenKanban](https://github.com/TechDufus/openkanban)** is a TUI kanban board for orchestrating AI coding agents. When you run Claude Code in an OpenKanban-managed terminal, oh-my-claude automatically reports live status updates.

| Status | When |
|--------|------|
| `idle` | Session started, ready for input |
| `working` | Processing prompt or executing tools |
| `waiting` | Awaiting user permission |

**How it works:** OpenKanban sets `OPENKANBAN_SESSION` env var when spawning agent terminals. oh-my-claude detects this and writes status to `~/.cache/openkanban-status/{session}.status`. Zero overhead when not in OpenKanban — the hook exits immediately if the env var isn't set.

**No configuration required.** If you have both tools installed, they just work together.

---

## For LLM Agents

If you're an AI agent installing this plugin, here are the exact steps:

```bash
# Step 1: Add marketplace
/plugin marketplace add TechDufus/oh-my-claude

# Step 2: Install plugin
/plugin install oh-my-claude@oh-my-claude

# Step 3: Verify installation
/plugin
# Should show: oh-my-claude @ oh-my-claude, Status: Enabled

# Step 4: User must restart Claude Code (you cannot do this)
# Inform user: "Please restart Claude Code to activate the plugin"
```

After restart, use **ultrawork** in any prompt to activate parallel execution mode.

---

## Philosophy

> **Enhance, don't replace.**

- Claude Code is already smart — add quality gates, not overrides
- Your context is for reasoning — delegate storage to subagents
- Hooks work invisibly — better experience without extra commands
- Specialized agents fill gaps — advisor, critic, validator, worker
- Stay out of the way — let Claude do what it does well

---

## Contributing

### Version Bumping

Any change to cached content requires version bumps in BOTH:
- `plugins/oh-my-claude/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`

---

## Uninstall

```bash
/plugin uninstall oh-my-claude@oh-my-claude
```

---

## Credits

Inspired by [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode).
