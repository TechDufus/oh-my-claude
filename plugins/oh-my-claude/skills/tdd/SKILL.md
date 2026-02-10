---
name: tdd
description: "Systematic TDD methodology for writing tests first. Use when implementing features or fixes with OMC_TDD_MODE enabled, when unsure how to structure tests, or when test-first discipline needs reinforcement. Triggers on: 'tdd', 'test first', 'test driven', 'red green refactor'."
---

# TDD Skill

Write the test. Watch it fail. Make it pass. Clean up. Repeat.

## The Iron Law

`NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST`

If you're writing production code and no test just failed, you're doing it wrong.

## When to Apply

- `OMC_TDD_MODE` is enabled (guided or enforced)
- Implementing a new feature or behavior
- Fixing a bug (write the test that reproduces it first)
- Unsure how to structure tests for a piece of logic
- When the `tdd_enforcer` hook blocks an edit

## Red-Green-Refactor Cycle

### RED: Write a Failing Test

1. Write ONE test that describes the desired behavior
2. Run the test suite
3. Verify it fails for the RIGHT reason (not a syntax error, not a missing import)
4. If it passes, your test is wrong or the feature already exists

**Verification gate:** Test output shows a meaningful failure related to the behavior you're implementing.

### GREEN: Make It Pass

1. Write the MINIMUM code to make the test pass
2. No extra methods. No abstractions. No "while I'm here" additions
3. Run the test suite
4. ALL tests pass (not just the new one)

**Verification gate:** Full test suite green. Zero failures.

### REFACTOR: Clean Up

1. Remove duplication introduced in the GREEN step
2. Improve naming, extract methods if warranted
3. Run the test suite after EVERY change
4. No new behavior during refactor - tests stay green throughout

**Verification gate:** Tests still green. Code is cleaner. No new functionality added.

## Anti-Rationalization Table

| Excuse | Counter |
|--------|---------|
| "I'll write tests after" | Tests written after prove nothing - they pass immediately |
| "Too simple to test" | Simple code breaks. Test takes 30 seconds |
| "I know this works" | Confidence is not evidence. The test IS the evidence |
| "Tests will slow me down" | Debugging without tests slows you down more |
| "Just a refactor" | Refactors without tests are rewrites without safety nets |
| "The types guarantee correctness" | Types check structure, not behavior. Test the behavior |
| "It's just a config change" | Config changes cause production outages. Test them |
| "I'll TDD the next one" | You said that last time. Start now |

## Red Flags

Thoughts that signal you're about to violate TDD:

- "Let me just quickly implement this first..."
- "This is too obvious to need a test"
- "I'll come back and add tests"
- "The test would just be testing the framework"
- "It's only a one-line change"
- "I need to see the implementation to know what to test"

If you catch yourself thinking any of these: STOP. Write the test first.

## Hook Integration

The `tdd_enforcer` hook gates file edits when `OMC_TDD_MODE` is enabled. This skill guides the methodology. The hook fires, you see the gate, invoke this skill for how to proceed.

**Flow:** Hook blocks edit -> Read the message -> Write/update a test -> Run tests (see RED) -> Now implement (GREEN) -> Clean up (REFACTOR).

## When Stuck

| Problem | Solution |
|---------|----------|
| Can't figure out what to test | Test the simplest case first. What's the most basic input/output? |
| Test is too complex | Break the behavior into smaller units. Test each one |
| Don't know the test framework | Check existing tests in the project. Copy the pattern |
| Test requires too much setup | That's a design smell. Simplify the interface under test |
| Multiple things need testing | One test at a time. Pick the smallest behavior first |
| Existing code has no tests | Start with the change you're making. Test the new behavior |
| Test passes immediately | Your test isn't testing what you think. Check assertions |
| Can't make the test fail | You might be testing something already implemented. Test the GAP |

## The Bottom Line

A test that exists before the code proves the code works. A test written after proves nothing but that you can reverse-engineer assertions.
