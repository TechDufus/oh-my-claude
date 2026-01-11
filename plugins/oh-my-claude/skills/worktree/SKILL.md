---
name: worktree
description: "Git worktree automation for isolated feature development. Triggers on: '/worktree create', '/worktree list', '/worktree remove'. Creates isolated working directories with automatic setup."
allowed-tools:
  - Bash(git worktree:*)
  - Bash(git branch:*)
  - Bash(git checkout:*)
  - Bash(mkdir:*)
  - Bash(cp:*)
  - Bash(rm:*)
  - Bash(ls:*)
  - Bash(npm:*)
  - Bash(yarn:*)
  - Bash(pnpm:*)
  - Read
  - Write
  - Glob
---

# Worktree Skill

Git worktree automation for isolated feature development.

## When This Skill Activates

| Category | Trigger Phrases |
|----------|-----------------|
| **Create worktree** | `/worktree create <name>`, `/worktree new <name>` |
| **List worktrees** | `/worktree list`, `/worktree ls` |
| **Remove worktree** | `/worktree remove <name>`, `/worktree rm <name>` |
| **Status** | `/worktree status` |

## Commands

### Create Worktree

```
/worktree create <feature-name>
```

Creates an isolated worktree for feature development.

**Workflow:**
1. Generate branch name: `feat/<feature-name>`
2. Create worktree: `git worktree add .worktrees/<feature-name> -b feat/<feature-name>`
3. Copy environment files (if they exist):
   - `.env`, `.env.local`, `.env.development`
   - `.nvmrc`, `.node-version`
   - `.npmrc`
4. Detect and run package manager install:
   - If `package-lock.json` → `npm install`
   - If `yarn.lock` → `yarn install`
   - If `pnpm-lock.yaml` → `pnpm install`
   - If `bun.lockb` → `bun install`
5. Add `.worktrees/` to `.gitignore` if not present
6. Report path and instructions

**Example:**
```bash
git worktree add .worktrees/auth-feature -b feat/auth-feature
cp .env .worktrees/auth-feature/ 2>/dev/null || true
cp .nvmrc .worktrees/auth-feature/ 2>/dev/null || true
cd .worktrees/auth-feature && npm install
```

### List Worktrees

```
/worktree list
```

Shows all active worktrees:
```bash
git worktree list
```

### Remove Worktree

```
/worktree remove <name>
```

Removes a worktree and optionally its branch:

**Workflow:**
1. Confirm removal with user
2. Remove worktree: `git worktree remove .worktrees/<name> --force`
3. Ask if branch should be deleted
4. If yes: `git branch -D feat/<name>`

### Status

```
/worktree status
```

Shows status of current worktree:
- Current branch
- Uncommitted changes
- Relationship to main worktree

## Directory Structure

```
project/
├── .worktrees/           # All worktrees live here
│   ├── auth-feature/     # Isolated worktree
│   └── api-refactor/     # Another worktree
├── .gitignore           # Should include .worktrees/
└── ...
```

## Environment Files

These files are copied to new worktrees if they exist:

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `.env.local` | Local overrides |
| `.env.development` | Development config |
| `.nvmrc` | Node version |
| `.node-version` | Node version (alternative) |
| `.npmrc` | npm configuration |
| `.tool-versions` | asdf version manager |

## Behavior Rules

### MUST DO
- Create worktrees under `.worktrees/` directory
- Add `.worktrees/` to `.gitignore` automatically
- Copy environment files to new worktrees
- Run package install in new worktrees
- Confirm before removing worktrees

### MUST NOT
- Create worktrees outside `.worktrees/`
- Force delete branches without confirmation
- Leave orphaned worktrees

## Safety

**Before removal, check:**
- No uncommitted changes in worktree
- No unpushed commits on branch
- Warn user if either condition exists

**Recovery:**
- Worktrees can be recovered with `git worktree add` if directory deleted manually
- Branches are not deleted unless explicitly requested

---

**Note:** This skill manages worktrees only. Use standard git commands for commits, pushes, and merges within worktrees.
