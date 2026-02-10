---
name: receiving-code-review
description: "How to handle code review feedback with technical rigor. Use when receiving review comments from code-reviewer agent, PR reviews, or external feedback. Triggers on: 'review feedback', 'address review', 'fix review comments', 'code review response'."
---

# Receiving Code Review Skill

How to handle review feedback with technical rigor, not performative agreement.

## When to Apply

- After receiving code-reviewer agent output
- PR review comments from teammates or external reviewers
- External feedback on implementation decisions
- When told to "address review comments" or "fix review feedback"

## Response Pattern

READ -> UNDERSTAND -> VERIFY -> EVALUATE -> RESPOND -> IMPLEMENT

### READ
Read the full review. Don't skim, don't react immediately. Take in every comment before acting on any of them. Later comments may contradict or contextualize earlier ones.

### UNDERSTAND
For each issue, understand what's actually being flagged. Restate in your own words: "This comment is about X because Y." If you can't restate it, you don't understand it yet.

### VERIFY
Check if the reviewer's claim is factually correct. Read the code they reference. Don't assume they're right or wrong -- look at the actual code at `{file}:{line}`.

### EVALUATE
Is this a real issue? Does the suggested fix actually improve things? Is the effort justified given the impact? Not all feedback requires action.

### RESPOND
Technical response only:
- Agree with reasoning: "Correct. The null check is missing at line X. Fixing."
- Disagree with evidence: "The review flags X, but `{file}:{line}` shows Y handles this case."
- Ask for clarification: "The comment suggests X. Is the concern about safety or performance?"

### IMPLEMENT
Fix in order: clarify unclear items -> blocking issues -> simple fixes -> complex fixes. Test each fix independently before moving to the next.

## Forbidden Responses

These responses indicate you're people-pleasing, not engineering:

- **"You're absolutely right!"** -- Performative agreement without understanding
- **"Great point!"** -- Flattery is not technical discourse
- **"I'll fix that right away!"** -- Understand before acting
- **"Of course, makes total sense!"** -- Does it? Or are you people-pleasing?

Instead: "The review identifies X. Checking... [evidence]. This is correct because [reason]. Fixing."

Or: "The review suggests X, but [counter-evidence]. Keeping current approach because [reason]."

## Source-Specific Handling

| Source | Trust Level | Response Style |
|--------|------------|----------------|
| Human partner | High context | Clarify intent, implement thoughtfully |
| External reviewer | Medium context | Verify claims against code, ask about unknowns |
| code-reviewer agent | Systematic but no context | Cross-reference with requirements, verify specifics |

## When to Push Back

- **Technically incorrect** -- "The review suggests X, but the code at `{file}:{line}` shows Y"
- **YAGNI** -- "This adds complexity for a hypothetical scenario. Current implementation handles all existing cases"
- **Breaks existing functionality** -- "This change would break {specific behavior} because {evidence}"
- **Missing context** -- "The review assumes X, but the requirement specifies Y (see {reference})"

Pushing back is not adversarial. It's quality control. Reviewers benefit from knowing when their feedback misses context.

## Implementation Order

1. Clarify unclear items first (don't build on misunderstanding)
2. Blocking/critical issues (things that prevent the code from working)
3. Simple fixes (typos, naming, formatting)
4. Complex fixes (refactors, architectural changes)
5. Test each fix independently

## Common Mistakes

| Mistake | Why It's Wrong | Do This Instead |
|---------|---------------|-----------------|
| Fix everything without reading all comments | Later comments may contradict earlier ones | Read ALL comments first |
| Performative agreement | Hides misunderstanding | Respond with technical reasoning |
| Batch all fixes in one commit | Can't isolate if something breaks | One logical change per commit |
| Skip re-testing after fixes | Fixes introduce new bugs | Test after every change |
| Ignore minor issues | They accumulate | Fix or explicitly defer with reason |

## The Bottom Line

Review feedback is data, not judgment. Evaluate it technically, respond with evidence, implement with discipline.
