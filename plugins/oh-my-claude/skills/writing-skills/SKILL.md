---
name: writing-skills
description: "Methodology for creating effective skills using TDD principles. Use when creating new skills, editing existing skills, or authoring plugin components. Triggers on: 'create skill', 'write skill', 'new skill', 'skill authoring'."
---

# Writing Skills Skill

TDD applied to process documentation.

## Core Principle

Writing skills IS TDD applied to process documentation. If you can't test it breaks without the skill, the skill isn't needed.

## When to Apply

- Creating new skills
- Editing existing skills
- Reviewing skill quality
- Authoring plugin components

## TDD Mapping

| TDD Concept | Skill Equivalent |
|-------------|------------------|
| Test case | Pressure scenario (situation where agent fails without skill) |
| Production code | SKILL.md content |
| Failing test | Agent demonstrably fails the scenario |
| Passing test | Agent handles scenario correctly with skill loaded |
| Refactor | Trim to minimum effective content |

## RED-GREEN-REFACTOR for Skills

### RED: Identify Failure Scenarios

Identify 3+ pressure scenarios where the agent fails without this skill. Document the failure mode. This is your test suite. If you can't find 3 scenarios, the skill probably isn't needed.

### GREEN: Write Minimum Effective Content

Write SKILL.md that addresses every identified failure. Minimum content to pass -- no extras, no nice-to-haves, no "comprehensive guides." Every section must map to at least one pressure scenario.

### REFACTOR: Trim Aggressively

Remove anything that doesn't directly address a pressure scenario. Target ~120 lines. If removing a line doesn't weaken any pressure scenario, remove it.

## SKILL.md Structure Template

```
---
name: {short-name}
description: "{Role sentence}. Use when {triggers}. Triggers on: {keywords}."
---
# {Name} Skill
{Tagline}
## When to Apply
## Core Pattern / Framework
## Anti-Rationalization Table (if methodology skill)
## Common Mistakes
## The Bottom Line
```

## Claude Search Optimization (CSO)

The description field determines when Claude loads your skill. Get it wrong and the skill never fires.

- Description = "Use when..." triggers ONLY
- NEVER summarize the workflow in the description
- Include trigger keywords that match how users/agents naturally phrase the need

**Good:** `"Use when receiving review comments from code-reviewer agent, PR reviews, or external feedback. Triggers on: 'review feedback', 'address review', 'fix review comments'."`

**Bad:** `"A comprehensive guide to handling code review feedback through a structured process"`

The bad example describes what the skill contains. The good example describes when to load it.

## Skill Types

| Type | Purpose | Example | Line Target |
|------|---------|---------|-------------|
| Technique | How to do X | debugger | ~120 lines |
| Pattern | When to use X | receiving-code-review | ~120 lines |
| Methodology | Discipline for X | tdd, verification | ~130 lines |
| Meta | How to create X | writing-skills | ~140 lines |

## Anti-Rationalization for Skipping Tests

| Excuse | Counter |
|--------|---------|
| "The skill is obviously clear" | If it's obvious, you can write 3 failure scenarios in 2 minutes |
| "It's just a reference doc" | Reference docs that don't address failures are shelf-ware |
| "Testing documentation is overkill" | Testing docs IS identifying what problems they solve |
| "I'll test it in practice" | Without defined scenarios, you won't notice when it fails |

## When NOT to Create a Skill

Not everything deserves a skill:

- Information easily found in docs (link to docs instead)
- One-time procedures (just do them)
- Tool-specific configuration (use CLAUDE.md)
- Content under 30 lines (too simple -- put it in CLAUDE.md)

## Token Efficiency

Every line must earn its place:

- Technique/pattern skills: ~120 lines
- Methodology skills: ~130 lines
- Meta skills: ~140 lines

The test: "If removing this line doesn't weaken any pressure scenario, remove it."

Avoid:
- Repetitive examples that demonstrate the same point
- "Nice to know" sections that don't prevent failures
- Long prose when a table communicates faster
- Headers with only 1-2 lines of content (merge them)

## Frontmatter Rules

Skills use ONLY `name` and `description` in frontmatter:

```yaml
---
name: my-skill
description: "What it does. Use when X. Triggers on: 'keyword1', 'keyword2'."
---
```

No `model`, `tools`, or `permissionMode`. These are not agent definitions.

## Common Mistakes

| Mistake | Why It's Wrong | Do This Instead |
|---------|---------------|-----------------|
| Writing without pressure scenarios | No way to verify the skill works | RED phase first -- always |
| Summarizing workflow in description | Claude can't match it to triggers | Use "Use when..." pattern |
| Including everything you know | Bloats context, dilutes signal | Only what prevents identified failures |
| Skipping refactor phase | Skills grow stale and verbose | Trim after every edit |
| Copying another skill's structure | Different types need different shapes | Match structure to skill type |

## The Bottom Line

A skill without tested pressure scenarios is documentation. Documentation without a problem to solve is noise.
