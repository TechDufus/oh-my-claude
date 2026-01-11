---
description: "Prime context for fresh session: /prime [task hint] [--quick] [--verbose]"
argument-hint: "[task hint] [--quick] [--verbose]"
allowed-tools:
  - Bash(git:*)
  - Bash(gh:*)
  - Task
  - Read
  - Grep
  - Glob
---

# /prime - Context Priming for Fresh Sessions

Rapidly build complete understanding of current work state after `/clear` or new session start. Uses parallel subagents to maximize context gathering while minimizing main context token usage.

## Usage

```
/prime                                    # Full context priming (default)
/prime <task-hint>                        # Prime with upcoming task focus
/prime --quick                            # Essential git state only (faster)
/prime --verbose                          # Include full diffs in report
```

### Examples
```
/prime                                    # General orientation
/prime migrating postgres init scripts    # Focus exploration on postgres/init
/prime reviewing PR #42                   # Pull PR context to forefront
```

## Arguments: $ARGUMENTS

---

## Philosophy

**Problem**: Fresh sessions lack context about in-progress work.

**Solution**: Subagents explore repository state in parallel, then synthesize into a concise briefing. Main context receives only the summary, not raw exploration data.

**Task-Focused**: When a task hint is provided, subagents prioritize context relevant to that task (pyramid approach - start with intent).

---

## Phase -1: Parse Arguments

Parse `$ARGUMENTS` to extract:
- **Task hint**: Any non-flag text (e.g., "migrating postgres init scripts")
- **Flags**: `--quick`, `--verbose`

---

## Phase 0: Quick Snapshot (Main Agent)

Run these commands in parallel via Bash tool:

```bash
git branch --show-current
git rev-parse --abbrev-ref HEAD@{upstream} 2>/dev/null || echo "no upstream"
git status --short --branch
git log --oneline -5
git stash list --format="%gd: %s"
```

Display immediately:
```
## Quick Snapshot
- **Branch**: <current-branch> (tracking: <upstream-or-none>)
- **Status**: <N files changed, M staged, K untracked>
- **Recent commits**: <last 3-5 one-liners>
- **Stashes**: <count or "none">
```

If `--quick` flag provided, STOP HERE.

---

## Subagent Prompt Template

All subagents receive this wrapper structure. Replace `{AGENT_NAME}`, `{WORD_LIMIT}`, `{COMMANDS}`, `{REQUIREMENTS}`, and `{XML_FIELDS}`:

```
Task(
  subagent_type: "general-purpose",
  description: "{description}",
  prompt: """
  <task_context>
  TASK HINT: {task_hint or "None provided - do general analysis"}
  </task_context>

  {AGENT_SPECIFIC_INSTRUCTIONS}

  Provide a CONCISE summary (under {WORD_LIMIT} words).
  If task hint provided, prioritize findings relevant to that task.

  <commands>
  {COMMANDS}
  </commands>

  <analysis_requirements>
  {REQUIREMENTS}
  If task hint provided, add: **Task relevance**: Which findings relate to the hinted task?
  </analysis_requirements>

  <output_format>
  Return structured XML:
  <{agent}_analysis>
    {XML_FIELDS}
    <task_relevance>...</task_relevance>  <!-- only if task hint provided -->
  </{agent}_analysis>
  </output_format>
  """
)
```

---

## Phase 1: Parallel Subagent Exploration

Launch THREE subagents simultaneously (all in single message):

### Subagent 1: Git Changes Analyst

**Word limit**: 500 | **Description**: "Analyze git changes"

**Commands**:
1. `git log main..HEAD --format='%h %s' 2>/dev/null || git log -10 --format='%h %s'`
2. `git diff --cached --stat` (staged)
3. `git diff --stat` (unstaged)
4. `git diff --cached` (full staged - summarize, don't echo)
5. `git diff` (full unstaged - summarize, don't echo)
6. `git stash show -p stash@{0} 2>/dev/null` (if stashes exist)
7. `git ls-files --others --exclude-standard | head -20` (untracked)

**Requirements**:
- **Branch commits**: Group by feature/fix/refactor
- **Staged/Unstaged/Untracked changes**: Categorize by src/test/config/docs
- **Stash contents**: Any paused work?
- **Work narrative**: 2-3 sentences on current developer activity

**XML Fields**: `branch_commits`, `staged`, `unstaged`, `untracked`, `stashes`, `narrative`

### Subagent 2: GitHub Context Analyst

**Word limit**: 400 | **Description**: "Analyze GitHub context"

**Commands**:
1. `gh pr list --state open --author @me --json number,title,headRefName,baseRefName,isDraft,updatedAt,reviewDecision --limit 5`
2. `gh pr view --json number,title,body,state,commits,reviews,statusCheckRollup 2>/dev/null`
3. `gh issue list --assignee @me --state open --json number,title,labels,updatedAt --limit 10`
4. `gh run list --limit 3 --json conclusion,name,updatedAt,headBranch`

**Requirements**:
- If current branch has PR: Draft status? Review feedback? CI status?
- If branch name contains issue number: Fetch issue, extract requirements
- If task hint mentions PR/issue: Fetch that directly

**XML Fields**: `current_pr`, `related_issue`, `ci_status`, `other_prs`, `open_issues`

Return `<github_analysis><none>No GitHub context available</none></github_analysis>` if gh CLI fails.

### Subagent 3: Project Context Analyst

**Word limit**: 300 | **Description**: "Analyze project context"

**Standard Checks**:
1. `CLAUDE.md` - Look for "## Active Work" section
2. `.claude/CLAUDE.md` - Project-specific instructions
3. `TODO.md` or `TODO` - Tracked tasks
4. `.claude/notepads/` - learnings.md, decisions.md, context.md
5. `git diff --name-only HEAD~5..HEAD 2>/dev/null | head -20`

**Task-Focused Exploration** (if hint provided):
- Glob: Find files matching task keywords
- Grep: Search for relevant patterns
- Read: Top 3-5 matching files, summarize structure
- Note file locations for main agent reference

**Requirements**:
- Active work description and phase from CLAUDE.md
- Key learnings, decisions, context from notepads
- Primary directories and patterns from recent changes
- Relevant files and conventions (if task hint provided)

**XML Fields**: `active_work`, `notepad_context` (with learnings/decisions/context), `focus_areas`, `project_type`, `available_commands`, `task_exploration` (with relevant_files/implementation_summary/conventions)

---

## Phase 2: Synthesis

After all subagents return, synthesize into unified briefing.

**Token Budget**: Keep under 800 tokens. Leave room for actual work.

### With Task Hint Format

```markdown
# Work State Briefing

## TL;DR
<One paragraph: Current state + relevance to hinted task>

## Task Context: {task_hint}
- **Relevant files**: <From Project Context>
- **Related changes**: <From Git Changes>
- **Associated PRs/issues**: <From GitHub Context>
- **Implementation notes**: <Key patterns discovered>

## General State
### Git
<Non-task-related branch, commits, changes>

### GitHub
<Other PRs, issues, CI status>

### Project
<Active work tracking, focus areas>

## Suggested Next Actions
<Tailored to the hinted task>
```

### Without Task Hint Format

```markdown
# Work State Briefing

## TL;DR
<One paragraph: Work in progress, state, next steps>

## Git State
<Branch, commits, changes summary>

## GitHub Context
<PR status, issue linkage, CI>

## Project Context
<Active work, focus areas>

## Suggested Next Actions
<2-3 logical next steps>
```

---

## Mode Variations

| Mode | Behavior | Token Usage | Best For |
|------|----------|-------------|----------|
| `--quick` | Phase 0 only, no subagents | ~100-200 | Quick orientation |
| `--verbose` | Include actual diff content | Higher | Complex changes |
| Default | Full Phase 0 + 1 + 2 | ~500-800 | Most situations |

---

## Example: With Task Hint

**Command**: `/prime migrating postgres chart init scripts`

```markdown
# Work State Briefing

## TL;DR
Branch main is clean. Found init scripts in `charts/shared-init/` ConfigMap.
Three postgres charts reference shared init. No active PR for this migration.

## Task Context: migrating postgres chart init scripts

### Relevant Files
- `charts/shared-init/templates/configmap.yaml` - Current shared init
- `charts/postgres-*/values.yaml` - Reference shared-init
- `charts/shared-init/files/*.sql` - 4 SQL init scripts

### Current Implementation
Shared-init creates ConfigMap with SQL scripts mounted to `/docker-entrypoint-initdb.d/`.
Scripts: `01-extensions.sql`, `02-schemas.sql`, `03-users.sql`, `04-grants.sql`.

### Conventions
- Numeric prefix for ordering
- Secrets via `envFrom`
- Pattern: `{{ include "shared-init.fullname" . }}-scripts`

## General State
- **Branch**: main (clean)
- **CI**: All passing

## Suggested Next Actions
1. Create branch: `feat/postgres-init-migration`
2. Copy SQL files to each postgres chart
3. Update templates for local ConfigMap
4. Remove shared-init dependency
```

## Example: Without Task Hint

**Command**: `/prime`

```markdown
# Work State Briefing

## TL;DR
Working on OAuth2 feature (branch: feat/oauth2-login). 3 commits implementing
provider abstraction. Focus: Google callback handler. PR #47 draft, CI passing.

## Git State
- **Branch**: feat/oauth2-login (5 ahead of main)
- **Unstaged**: `src/auth/google.ts` (callback logic)
- **Untracked**: `src/auth/github.ts` (next provider)

## GitHub Context
- **PR #47**: Draft, CI passing, no reviews
- **Issue #42**: "Add social login" - requires Google + GitHub

## Project Context
- **Active Work**: OAuth2 callback handlers
- **Focus**: `src/auth/`

## Suggested Next Actions
1. Complete Google callback handler
2. Add tests for callback flow
3. Start GitHub provider
```

---

## Error Handling

- **Not a git repo**: Report error, suggest running from repo root
- **No gh CLI**: Skip GitHub context, note in output
- **No CLAUDE.md**: Skip project context section
- **Empty branch**: Focus on staged/unstaged only
- **Network issues**: Timeout GitHub calls after 10s, report partial

---

## When to Use Task Hints

| Scenario | Use Hint? | Example |
|----------|-----------|---------|
| General orientation | No | `/prime` |
| Resuming specific work | Yes | `/prime fixing auth timeout` |
| Starting new feature | Yes | `/prime implementing rate limiting` |
| Reviewing PR | Yes | `/prime reviewing PR #42` |

**Tips**: Be specific ("postgres init scripts" beats "database stuff"). Don't chain with `/compact`. Clear before priming for cleanest context.
