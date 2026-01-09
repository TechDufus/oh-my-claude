---
description: "Prime context for fresh session: /prime [task hint] [--quick] [--verbose]"
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
/prime debugging auth timeout             # Look for auth-related changes
```

## Arguments: $ARGUMENTS

---

## Philosophy

**Problem**: Fresh sessions lack context about in-progress work. Manually explaining state wastes tokens and misses details.

**Solution**: Subagents explore repository state in parallel, then synthesize into a concise briefing. The main context receives only the summary, not the raw exploration data.

**Token Efficiency**: Each subagent has its own context window. Raw git diffs, PR bodies, and file contents stay in subagent contexts. Main context receives only distilled insights.

---

## Phase 0: Quick Snapshot (Main Agent)

First, gather low-token essentials directly:

```bash
# Run these commands in parallel:
git branch --show-current
git rev-parse --abbrev-ref HEAD@{upstream} 2>/dev/null || echo "no upstream"
git status --short --branch
git log --oneline -5
git stash list --format="%gd: %s"
```

**Parse and display immediately:**
```
## Quick Snapshot
- **Branch**: <current-branch> (tracking: <upstream-or-none>)
- **Status**: <N files changed, M staged, K untracked>
- **Recent commits**: <last 3-5 one-liners>
- **Stashes**: <count or "none">
```

If `--quick` flag provided, STOP HERE.

---

## Phase 1: Parallel Subagent Exploration

Launch THREE subagents simultaneously using `oh-my-claude:librarian`:

### Subagent 1: Git Changes Analyst
`Task(subagent_type="oh-my-claude:librarian", prompt="...")`

Analyze current git state:
- Branch commits since diverging from main
- Staged and unstaged changes (summarized, not raw)
- Untracked files
- Stash contents
- Work narrative: 2-3 sentences on what developer is working on

### Subagent 2: GitHub Context Analyst
`Task(subagent_type="oh-my-claude:librarian", prompt="...")`

Gather GitHub context:
- Current branch PR status (draft, reviews, CI)
- Related issue if branch name contains issue number
- Other open PRs by user
- Recent CI runs

### Subagent 3: Project Context Analyst
`Task(subagent_type="oh-my-claude:librarian", prompt="...")`

Gather project-level context:
- CLAUDE.md "Active Work" section if present
- Recent file changes pattern
- Project type and available commands
- If task hint provided: explore relevant files/directories

---

## Phase 2: Synthesis

After all subagents return, synthesize into unified briefing.

**Token Budget**: Keep synthesis under 800 tokens.

### With Task Hint

```markdown
# Work State Briefing

## TL;DR
<One paragraph: Current state + relevance to the hinted task>

## Task Context: {task_hint}
- **Relevant files**: <paths discovered>
- **Related changes**: <git changes related to task>
- **Associated PRs/issues**: <if any>
- **Implementation notes**: <key patterns discovered>

## General State
### Git
<Branch, commits, changes NOT related to task>

### GitHub
<Other PRs, issues, CI status>

## Suggested Next Actions
<Tailored to the hinted task>
```

### Without Task Hint

```markdown
# Work State Briefing

## TL;DR
<One paragraph: What work is in progress, what state, what's next>

## Git State
<Branch, commits, changes summary>

## GitHub Context
<PR status, issue linkage, CI status>

## Project Context
<Active work tracking, focus areas>

## Suggested Next Actions
<Based on all context, suggest 2-3 logical next steps>
```

---

## Mode Variations

### `--quick` Mode
- Only run Phase 0 (Quick Snapshot)
- No subagents spawned
- Minimal token usage (~100-200 tokens)
- Best for: Quick orientation, simple repos

### `--verbose` Mode
- Include actual diff content in synthesis
- Higher token usage
- Best for: Complex changes needing detailed review

### Default Mode
- Full Phase 0 + Phase 1 + Phase 2
- Balanced token usage (~500-800 tokens)
- Best for: Most situations

---

## Error Handling

- **Not a git repo**: Report error, suggest running from repo root
- **No gh CLI**: Skip GitHub context, note in output
- **No CLAUDE.md**: Skip project context section
- **Empty branch**: Focus on staged/unstaged only
- **Network issues**: Timeout GitHub calls after 10s, report partial results

---

## Integration with /work

After `/prime` completes, run `/work <task>` to continue. The priming context helps `/work` make better routing decisions.

```
/clear                                    # Fresh start
/prime                                    # Build context
/work continue PR #47                     # Resume with full understanding
```
