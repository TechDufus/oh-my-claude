# Debugger Skill

Systematic debugging methodology for diagnosing failures and root cause analysis.

## When to Apply This Guidance

- 2+ failed fix attempts on the same issue
- Debugging that's gone in circles
- Complex system behavior you don't understand
- Multi-system integration problems
- Intermittent failures (Heisenbugs)

## Structured Analysis Framework

### Step 1: Restate the Problem

Before investigating, articulate:
- What is the actual vs expected behavior?
- What assumptions might be wrong?
- What could cause the specific symptoms described?
- Are there hidden dependencies or side effects?

### Step 2: Generate Ranked Hypotheses

Always generate multiple hypotheses, ranked by likelihood:

**Most Likely:**
- Evidence: What supports this theory?
- Test: How to verify quickly?

**Possible:**
- Evidence: What partially supports this?
- Test: How to confirm or eliminate?

**Unlikely but worth checking:**
- Evidence: Limited, but possible
- Test: Quick check to rule out

### Step 3: Systematic Verification

Test hypotheses in order. For each:
1. State what you're testing
2. Describe the expected outcome if hypothesis is correct
3. Execute the test
4. Document actual results
5. Update hypothesis ranking based on findings

## Reasoning Principles

1. **Challenge assumptions** - The "obvious" cause is often wrong after 2+ failures
2. **Follow the data** - What do logs/errors actually say vs what's assumed?
3. **Consider timing** - Race conditions, async issues, initialization order
4. **Check boundaries** - Module interfaces, API contracts, type conversions
5. **Question the environment** - Config, dependencies, network, state

## Decision Framework

When choosing between approaches:

| Factor | Weight | Considerations |
|--------|--------|----------------|
| Correctness | Critical | Does it actually solve the problem? |
| Simplicity | High | Prefer boring solutions over clever ones |
| Leverage | High | Use existing patterns/libraries/code |
| Developer Experience | Medium | How hard is it to debug/maintain? |
| Performance | Low* | *Unless performance IS the problem |

## Effort Estimation

Tag recommendations by effort:

| Tag | Meaning | Example |
|-----|---------|---------|
| **[Quick]** | <30 min | Add logging, check config |
| **[Short]** | 30min-2hr | Refactor function, add test |
| **[Medium]** | 2hr-1day | New component, integration |
| **[Large]** | >1 day | Architecture change |

## Common Failure Patterns

| Pattern | Signal | Investigation Focus |
|---------|--------|---------------------|
| Fix-break cycle | Each fix causes new problem | Root cause analysis - treating symptoms not cause |
| Confusion | "I don't understand why X happens" | Add logging, trace execution path |
| Tradeoff paralysis | Multiple valid approaches | Use decision framework above |
| Integration hell | System A + B don't work together | Interface contracts, data formats |
| Heisenbug | Works sometimes, fails randomly | Timing, state, race conditions |

## Traps to Avoid

- **Premature fixing** - Understand before changing
- **Single hypothesis** - Always consider alternatives
- **Assuming correctness** - Verify each component independently
- **Ignoring evidence** - If data contradicts theory, update theory
- **Scope creep** - Fix the bug, not everything around it

## Output Template

When debugging, structure findings as:

```
## Problem Understanding
{Restate in own words. Challenge framing if wrong.}

## Hypotheses (Ranked)
1. Most Likely: {hypothesis} - Evidence: {support} - Test: {verification}
2. Possible: {hypothesis} - Evidence: {support} - Test: {verification}
3. Unlikely: {hypothesis} - Evidence: {limited} - Test: {quick check}

## Recommended Approach
{Specific next steps. Be prescriptive.}

## Traps to Avoid
{What NOT to do for this specific problem.}
```
