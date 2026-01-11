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
6. **Verify worktree creation:**
   - Run `git -C .worktrees/<name> status` to confirm clean state
   - Run `git worktree list` to confirm worktree is registered
   - If verification fails, run cleanup and report error
7. Report path and instructions

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

## Decision Matrix: Worktree vs Branch

| Situation | Use Worktree | Use Branch |
|-----------|--------------|------------|
| Working on two features simultaneously | YES | NO |
| Quick hotfix while mid-feature | YES | NO |
| Sequential feature development | NO | YES |
| Code review while continuing work | YES | NO |
| Simple branch for later work | NO | YES |
| Different node_modules needed | YES | NO |
| Testing against different deps | YES | NO |
| Just want to save work in progress | NO | YES (stash or branch) |

**Rule of thumb:**
- **Parallel work** = worktree (isolated directories, no context switching)
- **Sequential work** = branch (single directory, normal git workflow)
- **Different dependencies** = worktree (each has own node_modules)

## Example Sessions

### Create Worktree - Complete Session

```
User: /worktree create auth-refactor

Claude: Creating worktree for auth-refactor...
```

```bash
# Step 1: Verify we're in a git repo and check current state
$ git rev-parse --is-inside-work-tree
true

$ git worktree list
/Users/dev/myapp  abc1234 [main]

# Step 2: Check if branch already exists
$ git branch --list 'feat/auth-refactor'
(no output = branch doesn't exist, safe to proceed)

# Step 3: Create the worktree with new branch
$ git worktree add .worktrees/auth-refactor -b feat/auth-refactor
Preparing worktree (new branch 'feat/auth-refactor')
HEAD is now at abc1234 feat: add user dashboard

# Step 4: Copy environment files
$ cp .env .worktrees/auth-refactor/ 2>/dev/null && echo "Copied .env" || echo "No .env found"
Copied .env

$ cp .nvmrc .worktrees/auth-refactor/ 2>/dev/null && echo "Copied .nvmrc" || echo "No .nvmrc found"
Copied .nvmrc

# Step 5: Detect package manager and install
$ ls .worktrees/auth-refactor/package-lock.json
.worktrees/auth-refactor/package-lock.json

$ cd .worktrees/auth-refactor && npm install
added 847 packages in 32s

# Step 6: Ensure .worktrees/ is in .gitignore
$ grep -q "^\.worktrees/$" .gitignore || echo ".worktrees/" >> .gitignore
(added to .gitignore)

# Step 7: Verify worktree is functional
$ git -C .worktrees/auth-refactor status
On branch feat/auth-refactor
nothing to commit, working tree clean

$ git worktree list
/Users/dev/myapp                      abc1234 [main]
/Users/dev/myapp/.worktrees/auth-refactor  abc1234 [feat/auth-refactor]
```

**Output to user:**
```
Worktree created successfully.

Location: .worktrees/auth-refactor
Branch:   feat/auth-refactor
Base:     main (abc1234)

Environment files copied:
  - .env
  - .nvmrc

Dependencies installed via npm.

To work in this worktree:
  cd .worktrees/auth-refactor

To open in new terminal/editor:
  code .worktrees/auth-refactor
```

### List Worktrees - Complete Session

```
User: /worktree list

Claude: Current worktrees:
```

```bash
$ git worktree list
/Users/dev/myapp                          abc1234 [main]
/Users/dev/myapp/.worktrees/auth-refactor def5678 [feat/auth-refactor]
/Users/dev/myapp/.worktrees/api-cache     ghi9012 [feat/api-cache]
```

**Output to user:**
```
Active Worktrees:

1. main (primary)
   Path:   /Users/dev/myapp
   Commit: abc1234

2. auth-refactor
   Path:   .worktrees/auth-refactor
   Branch: feat/auth-refactor
   Commit: def5678

3. api-cache
   Path:   .worktrees/api-cache
   Branch: feat/api-cache
   Commit: ghi9012
```

### Remove Worktree - Complete Session (With Warning)

```
User: /worktree remove auth-refactor

Claude: Checking worktree status before removal...
```

```bash
# Step 1: Check for uncommitted changes
$ git -C .worktrees/auth-refactor status --porcelain
 M src/auth/login.ts
?? src/auth/temp.ts

# Step 2: Check for unpushed commits
$ git -C .worktrees/auth-refactor log origin/feat/auth-refactor..HEAD --oneline 2>/dev/null || git -C .worktrees/auth-refactor log origin/main..HEAD --oneline
a1b2c3d feat(auth): add session validation
d4e5f6g feat(auth): refactor token storage
```

**Output to user:**
```
WARNING: This worktree has uncommitted changes:

Modified:  src/auth/login.ts
Untracked: src/auth/temp.ts

WARNING: This worktree has 2 unpushed commits:

a1b2c3d feat(auth): add session validation
d4e5f6g feat(auth): refactor token storage

Are you sure you want to remove this worktree?
This will DELETE all uncommitted changes permanently.

Options:
1. Commit and push changes first, then remove
2. Force remove (loses uncommitted changes)
3. Cancel
```

```
User: force remove, I don't need those changes

Claude: Removing worktree...
```

```bash
# Step 3: Force remove the worktree
$ git worktree remove .worktrees/auth-refactor --force
Removing worktree directory .worktrees/auth-refactor

# Step 4: Ask about branch deletion
```

**Output to user:**
```
Worktree removed.

The branch 'feat/auth-refactor' still exists with 2 commits.
Delete the branch as well? (y/n)
```

```
User: yes

Claude: Deleting branch...
```

```bash
$ git branch -D feat/auth-refactor
Deleted branch feat/auth-refactor (was a1b2c3d).

$ git worktree list
/Users/dev/myapp                      abc1234 [main]
/Users/dev/myapp/.worktrees/api-cache ghi9012 [feat/api-cache]
```

**Output to user:**
```
Cleanup complete.
- Worktree directory removed
- Branch feat/auth-refactor deleted
```

## Error Handling

### Error: Branch Already Exists

```bash
$ git worktree add .worktrees/auth-feature -b feat/auth-feature
fatal: a branch named 'feat/auth-feature' already exists
```

**Recovery:**
```bash
# Option 1: Use existing branch (if worktree doesn't exist for it)
$ git worktree add .worktrees/auth-feature feat/auth-feature

# Option 2: Choose a different name
$ git worktree add .worktrees/auth-feature-v2 -b feat/auth-feature-v2

# Option 3: Delete the old branch first (if safe)
$ git branch -d feat/auth-feature  # safe delete (fails if unmerged)
$ git worktree add .worktrees/auth-feature -b feat/auth-feature
```

**User message:** "Branch 'feat/auth-feature' already exists. Would you like to: (1) use the existing branch, (2) choose a different name, or (3) delete the old branch first?"

### Error: Worktree Directory Already Exists

```bash
$ git worktree add .worktrees/auth-feature -b feat/auth-feature
fatal: '.worktrees/auth-feature' already exists
```

**Recovery:**
```bash
# Check if it's a valid worktree
$ git worktree list | grep auth-feature

# If listed: worktree exists, inform user
# If not listed: orphaned directory, safe to remove
$ rm -rf .worktrees/auth-feature
$ git worktree prune
$ git worktree add .worktrees/auth-feature -b feat/auth-feature
```

**User message:** "Directory '.worktrees/auth-feature' already exists. This appears to be an orphaned directory (not a valid worktree). Remove it and retry?"

### Error: Package Install Fails

```bash
$ cd .worktrees/auth-feature && npm install
npm ERR! code ERESOLVE
npm ERR! ERESOLVE could not resolve
npm ERR! peer dep missing: react@^17.0.0
```

**Recovery:**
```bash
# Worktree is created but deps failed
# Option 1: Try with legacy peer deps
$ cd .worktrees/auth-feature && npm install --legacy-peer-deps

# Option 2: Use different package manager
$ cd .worktrees/auth-feature && yarn install

# Option 3: Skip install, let user handle
```

**User message:** "Worktree created successfully, but npm install failed with dependency conflicts. The worktree is ready at .worktrees/auth-feature. You may need to run `npm install --legacy-peer-deps` or resolve the conflicts manually."

### Error: Disk Space Insufficient

```bash
$ cd .worktrees/auth-feature && npm install
npm ERR! code ENOSPC
npm ERR! syscall write
npm ERR! errno -28
npm ERR! ENOSPC: no space left on device
```

**Recovery:**
```bash
# Clean up the partial worktree
$ git worktree remove .worktrees/auth-feature --force
$ git branch -D feat/auth-feature

# Check disk space
$ df -h .
```

**User message:** "Disk space insufficient. The partial worktree has been cleaned up. Free up disk space and try again. Current usage: [show df output]"

### Error: Invalid Worktree Name

```bash
$ git worktree add ".worktrees/my feature" -b "feat/my feature"
fatal: 'feat/my feature' is not a valid branch name
```

**Prevention:** Validate names before attempting creation.

```bash
# Valid patterns: alphanumeric, hyphens, underscores
# Invalid: spaces, special chars, starting with hyphen

# Sanitize input
name="my feature"
sanitized=$(echo "$name" | tr ' ' '-' | tr -cd 'a-zA-Z0-9-_')
# Result: my-feature
```

**User message:** "Invalid name 'my feature'. Branch names cannot contain spaces. Using 'my-feature' instead."

### Error: Worktree Locked

```bash
$ git worktree remove .worktrees/auth-feature
fatal: '.worktrees/auth-feature' is locked
```

**Recovery:**
```bash
# Check why it's locked
$ cat .git/worktrees/auth-feature/locked
Process still running or editor has files open

# Unlock if safe
$ git worktree unlock .worktrees/auth-feature
$ git worktree remove .worktrees/auth-feature
```

**User message:** "Worktree is locked (possibly by another process or editor). Close any editors with files from this worktree open, then retry."

## Cleanup Instructions for Partial Failures

If worktree creation fails partway through, clean up in reverse order:

```bash
# 1. Remove node_modules if install started
$ rm -rf .worktrees/<name>/node_modules 2>/dev/null

# 2. Remove the worktree directory
$ git worktree remove .worktrees/<name> --force 2>/dev/null || rm -rf .worktrees/<name>

# 3. Prune worktree references
$ git worktree prune

# 4. Delete the branch if it was created
$ git branch -D feat/<name> 2>/dev/null

# 5. Verify clean state
$ git worktree list
$ git branch --list 'feat/<name>'
```

**Automated cleanup function:**
```bash
cleanup_failed_worktree() {
    local name="$1"
    rm -rf ".worktrees/${name}/node_modules" 2>/dev/null
    git worktree remove ".worktrees/${name}" --force 2>/dev/null || rm -rf ".worktrees/${name}"
    git worktree prune
    git branch -D "feat/${name}" 2>/dev/null
    echo "Cleaned up failed worktree: ${name}"
}
```

---

**Note:** This skill manages worktrees only. Use standard git commands for commits, pushes, and merges within worktrees.
