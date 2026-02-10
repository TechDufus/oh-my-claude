---
name: verification
description: "Evidence-based verification methodology before claiming work is complete. Use when about to claim work is done, before committing, before creating PRs, or when verification-reminder hook fires. Triggers on: 'verify', 'verification', 'is it done', 'complete', 'ready to merge'."
---

# Verification Skill

No evidence, no completion claim. Period.

## The Iron Law

`NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE`

"I think it works" is not evidence. "Tests passed 5 minutes ago" is not fresh. Run the checks NOW, read the output NOW, then claim completion.

## When to Apply

- About to say "done", "complete", or "ready"
- Before committing or creating a PR
- After agent teammates claim work is finished
- When the `verification_reminder` hook fires
- Before any handoff to another person or system

## Gate Function

### IDENTIFY
What needs verification? List every claim you're about to make.
- Tests pass? Which test suite?
- Build succeeds? Which build command?
- Feature works? What specific behavior?
- No regressions? What could have broken?

### RUN
Execute the actual checks. Not "I think they pass" - run them NOW.
- Run the test suite. Capture output.
- Run the build. Capture output.
- Run linters if applicable. Capture output.

### READ
Read the output. Actually read it. Don't assume.
- Check exit codes (0 = success, anything else = failure)
- Look for warnings that might indicate issues
- Count passing vs failing tests
- Verify the output matches expectations

### VERIFY
Does the output confirm success? Cross-reference against requirements.
- Every requirement has corresponding evidence
- No skipped tests that cover changed behavior
- No warnings that indicate degraded functionality

### CLAIM
Only now can you claim completion. Include the evidence.

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| "Tests pass" | Fresh test run output | "They passed before" |
| "Build succeeds" | Actual build output | "It should build" |
| "Feature works" | Demonstrated behavior | "I implemented it correctly" |
| "No regressions" | Full test suite run | "I only changed one file" |
| "PR is ready" | All checks green | "I think it's good" |
| "Bug is fixed" | Reproduction test passes | "I addressed the cause" |

## Anti-Rationalization Table

| Excuse | Counter |
|--------|---------|
| "The agent said it works" | Agents hallucinate. Read the actual output |
| "I'm confident it works" | Confidence is not evidence. Run the check |
| "I just ran tests a minute ago" | You changed code since then. Run again |
| "It's a trivial change" | Trivial changes cause production incidents. Verify |
| "Tests take too long" | Debugging takes longer. Run them |
| "I trust the subagent" | Trust but verify. Verification is cheap, debugging is expensive |
| "The types check out" | Types don't catch logic errors. Run the tests |
| "I'll verify after committing" | Commits without verification = tech debt |

## Red Flags

Thoughts that signal you're about to skip verification:

- "This obviously works, I don't need to check"
- "The agent already verified this"
- "I'll just commit and fix anything CI catches"
- "It's the same as last time, it'll be fine"
- "I only changed one line"
- "Running tests again would be redundant"

If you catch yourself thinking any of these: STOP. Run the verification.

## Hook Integration

The `verification_reminder` hook reminds you to verify after agent tasks complete. This skill enforces the methodology. The hook fires, you see the reminder, invoke this skill for the systematic verification process.

**Flow:** Agent completes work -> Hook reminds you -> IDENTIFY what to check -> RUN the checks -> READ output -> VERIFY against requirements -> CLAIM only with evidence.

## Verification Checklist

Use this before any completion claim:

- [ ] All changed files saved
- [ ] Test suite run AFTER last code change
- [ ] Test output actually read (not assumed)
- [ ] Build passes (if applicable)
- [ ] Linting passes (if applicable)
- [ ] Requirements cross-referenced against implementation
- [ ] Edge cases from requirements are covered
- [ ] No TODO/FIXME left in changed code (unless intentional)

## The Bottom Line

Evidence or it didn't happen. Run the check, read the output, then speak.
