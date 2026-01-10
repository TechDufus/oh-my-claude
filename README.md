<img width="1328" height="611" alt="oh-my-claude_hero" src="https://github.com/user-attachments/assets/ca862678-da89-45c3-8385-fb45415c1b6e" />

<p align="center">
  <a href="https://github.com/TechDufus/oh-my-claude/releases"><img src="https://img.shields.io/github/v/release/TechDufus/oh-my-claude?style=flat-square&label=version" alt="Version"></a>
  <a href="https://github.com/TechDufus/oh-my-claude/blob/main/LICENSE"><img src="https://img.shields.io/github/license/TechDufus/oh-my-claude?style=flat-square" alt="License"></a>
  <a href="https://github.com/TechDufus/oh-my-claude/stargazers"><img src="https://img.shields.io/github/stars/TechDufus/oh-my-claude?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/TechDufus/oh-my-claude/issues"><img src="https://img.shields.io/github/issues/TechDufus/oh-my-claude?style=flat-square" alt="Issues"></a>
</p>

<h3 align="center">Turn Claude Code into a relentless parallel execution engine.</h3>

---

## TL;DR — Skip This README

Just add a trigger word anywhere in your prompt:

```
fix all the type errors, ultrawork
ulw refactor the entire auth system
implement user analytics with tests, just get it done
```

Claude will parallelize everything, delegate file reads to subagents, track progress with todos, and refuse to stop until the job is done. No partial implementations. No asking for permission. Just execution.

[Install it](#install) and start using it. Come back here when you want the details.

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Install](#install)
- [Magic Keywords](#magic-keywords)
- [What Ultrawork Actually Does](#what-ultrawork-actually-does)
- [The Agent Team](#the-agent-team)
- [All Components](#all-components)
- [For LLM Agents](#for-llm-agents)
- [Philosophy](#philosophy)
- [Contributing](#contributing)
- [Uninstall](#uninstall)

---

## Why This Exists

Claude Code is powerful, but it's polite. Too polite. It asks permission. It implements things one at a time. It stops to check if you're happy.

Sometimes you don't want a conversation. You want a task force.

**oh-my-claude** transforms Claude from a helpful assistant into an autonomous execution engine:
- **Parallel by default** — Launch multiple subagents in a single message
- **Context-aware** — Delegates bulk reads to subagents so your main context stays sharp
- **Relentless** — Won't stop until all todos are complete and tests pass
- **Zero tolerance** — No "simplified versions," no "leaving as exercise," no scope reduction

One keyword. Total transformation.

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

| Keyword | Effect |
|---------|--------|
| **ultrawork** / **ulw** | Maximum parallel execution — won't stop until done |
| **ultrathink** | Extended reasoning with sequential-thinking MCP before action |
| **ultradebug** | Systematic debugging with evidence-based diagnosis |
| **analyze** | Deep analysis with parallel context gathering |
| **search for** | Multiple parallel search agents |

### Natural Language Triggers

These phrases also activate ultrawork mode:
- `just work`, `don't stop`, `until done`
- `keep going`, `finish everything`, `relentless`, `get it done`

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

The hook intercepts your prompt, detects the keyword, and injects execution directives that override Claude's default politeness.

---

## The Agent Team

Six specialized subagents, each optimized for a specific role:

| Agent | Model | What It Does |
|-------|-------|--------------|
| **scout** | haiku | Fast recon — finds files, locates definitions, checks existence |
| **librarian** | sonnet | Smart reading — summarizes large files, extracts relevant sections |
| **architect** | opus | Planning — decomposes complex tasks, identifies parallelization |
| **worker** | opus | Implementation — executes ONE specific task completely |
| **scribe** | opus | Documentation — writes clear docs for code, APIs, systems |
| **validator** | haiku | QA — runs tests, linters, type checks, reports pass/fail |

### Usage

```
Task(subagent_type="oh-my-claude:scout", prompt="Find all auth-related files")
Task(subagent_type="oh-my-claude:librarian", prompt="Summarize src/auth/service.ts")
Task(subagent_type="oh-my-claude:worker", prompt="Add password reset endpoint")
```

### Why Subagents Matter

Subagent context is **isolated** from your main context. When a librarian reads a 2000-line file, those lines don't consume your context window — you get a summary. This keeps your main Claude sharp for reasoning instead of drowning in file contents.

---

## All Components

### Hooks (Automatic)

| Hook | When | What |
|------|------|------|
| **context-guardian** | Session start | Injects context protection rules |
| **ultrawork-detector** | Prompt submit | Detects keywords, injects execution directives |
| **todo-enforcer** | Stop | Prevents stopping with incomplete todos |
| **context-monitor** | Post tool use | Warns at high context usage |

### Commands

| Command | Description |
|---------|-------------|
| `/prime` | Context recovery after /clear |

### Skills

| Skill | Trigger |
|-------|---------|
| **git-commit-validator** | Auto-invoked on commit requests |

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

> **Your context is for reasoning, not storage.**

- Delegate bulk reads to subagents — their context is free
- Launch parallel tasks in single messages — sequential is failure
- Track everything with TodoWrite — no task forgotten
- Never stop until done — incomplete todos mean keep working
- No partial solutions — deliver exactly what was asked

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
