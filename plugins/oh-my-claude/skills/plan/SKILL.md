---
name: plan
description: "Structured planning with draft management. Use this skill when the user wants to plan a feature, task, or project before implementation. Triggers on: '/plan <topic>', 'let's plan', 'plan for', 'help me plan'. Creates draft at .claude/plans/drafts/, conducts interview, generates final plan on confirmation."
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Task
  - AskUserQuestion
---

# Plan Skill

Structured planning through interview and draft management.

## When This Skill Activates

| Category | Trigger Phrases |
|----------|-----------------|
| **Start planning** | `/plan <topic>`, `let's plan`, `plan for`, `help me plan` |
| **Continue draft** | `continue planning`, `back to plan`, `resume plan` |
| **Finalize** | `make it a plan`, `finalize plan`, `generate plan`, `create the plan` |
| **Abandon** | `cancel plan`, `abandon planning`, `forget the plan` |

## Planning Workflow

### Phase 1: Initiation

When triggered with a topic:

1. Create draft file at `.claude/plans/drafts/{topic-slug}.md`
2. Initialize with template structure
3. Begin interview

**Draft location:** `.claude/plans/drafts/{topic-slug}.md`
**Final plan location:** `.claude/plans/{topic-slug}.md`

### Phase 2: Interview

Ask focused questions to gather requirements. Keep it to 3-5 core questions:

**Core Questions:**
1. "What problem does this solve?" (understand context)
2. "What's the scope - minimal viable vs complete?" (set boundaries)
3. "Any constraints, non-goals, or things to avoid?" (define exclusions)

**Follow-up Questions (as needed):**
- Technical approach preferences
- Dependencies on other work
- Priority/timeline considerations

After each answer, update the draft file with new information.

Use `AskUserQuestion` tool for structured multi-choice questions when options are clear.

### Phase 3: Research

Before finalizing, research the codebase:

```
Agent: oh-my-claude:scout
Task: Find relevant files for {topic}
Why: Need to understand existing code before planning changes
Expected: List of files that will be affected
```

```
Agent: oh-my-claude:librarian
Task: Read and summarize key files
Why: Need context for implementation planning
Expected: Summary of current implementation patterns
```

Add findings to draft under "## Research Findings".

### Phase 4: Confirmation

When user says "make it a plan" or similar:
1. Review draft completeness
2. Transform draft into final plan
3. Write to `.claude/plans/{topic-slug}.md`
4. Delete draft file (optional - can keep for reference)

## Draft Structure

```markdown
# Planning Draft: {topic}

## Status
Phase: Interview | Research | Ready for Plan
Started: {timestamp}

## Requirements
- [captured from interview]

## Decisions
- [choices made during interview]

## Research Findings
- [results from scout/librarian]

## Open Questions
- [unanswered items]
```

## Final Plan Structure

```markdown
# Plan: {topic}

## Context
[Why this plan exists, what problem it solves]

## Objectives

### Must Have
- [required outcomes]

### Must NOT Have
- [explicit exclusions]

## Implementation Steps
1. [Step with file references and details]
2. [Step with file references and details]

## Files to Modify
| File | Changes |
|------|---------|
| `path/to/file.ts` | [what changes] |

## Acceptance Criteria
- [ ] [Testable criterion]
- [ ] [Testable criterion]
```

## Decision Matrices

### Interview Depth by Complexity

| Complexity | Question Count | Interview Duration | Indicators |
|------------|----------------|-------------------|------------|
| **Simple** | 2-3 questions | 1-2 exchanges | Single file, typo fix, config change, obvious scope |
| **Standard** | 4-5 questions | 3-4 exchanges | Multi-file feature, clear requirements, bounded scope |
| **Complex** | 6-8+ questions | 5+ exchanges | Architecture change, new system, cross-cutting concerns |

**Complexity Detection Heuristics:**

| Signal | Points to... |
|--------|--------------|
| User says "just" or "simple" or "quick" | Simple |
| Mentions specific file or function | Simple to Standard |
| Says "redesign" or "rethink" or "overhaul" | Complex |
| Involves multiple systems or services | Complex |
| Unclear success criteria | Complex (need more questions) |
| User provides detailed spec upfront | May skip some questions |

### When to Skip Research

| Scenario | Skip Research? | Reason |
|----------|---------------|--------|
| User provides full context and file paths | Yes | Already have needed info |
| Typo fix, docs update, config tweak | Yes | Scope is obvious |
| User explicitly says "I know where changes go" | Yes | Trust user knowledge |
| New feature in unfamiliar codebase area | **No** | Must understand current state |
| Refactoring existing code | **No** | Need to know what exists |
| "I'm not sure where this should go" | **No** | Research required |
| User skips interview answers with "you decide" | **No** | Research compensates for missing context |

### When to Delegate to Architect

| Scenario | Delegate? | Rationale |
|----------|-----------|-----------|
| Single feature, clear scope | No | Plan skill handles this |
| Multi-phase project with dependencies | **Yes** | Architect decomposes into phases |
| User asks for "roadmap" or "strategy" | **Yes** | Beyond single plan scope |
| Involves trade-off analysis | **Yes** | Architect evaluates approaches |
| Plan would exceed 20 implementation steps | **Yes** | Too complex for single plan |

## Pre-Finalization Validation Checklist

Before writing the final plan, verify:

```
[ ] Context section explains WHY (not just what)
[ ] At least one "Must NOT Have" item defined
[ ] Implementation steps reference specific files
[ ] Each step is actionable (not vague)
[ ] Acceptance criteria are testable
[ ] No open questions remain unanswered
[ ] File paths verified via research (if research was done)
[ ] Scope matches user's stated complexity preference
```

**If any item fails:** Return to interview or research phase to fill gaps.

## Example Planning Sessions

### Example 1: Simple (Single File Change)

**Trigger:** `/plan add rate limit to login endpoint`

**Interview (2 questions):**

> **Claude:** What's the rate limit you want - requests per minute and per what (IP, user, both)?
>
> **User:** 5 per minute per IP
>
> **Claude:** Any bypass needed for testing or admin users?
>
> **User:** No, keep it simple

**Research:** Skipped - user specified the exact endpoint

**Draft Excerpt:**
```markdown
## Requirements
- 5 requests per minute per IP on /auth/login
- No bypasses needed

## Decisions
- Use existing rate limit middleware pattern
```

**Final Plan Excerpt:**
```markdown
# Plan: add rate limit to login endpoint

## Context
Login endpoint currently has no rate limiting, making it vulnerable
to brute force attacks.

## Objectives

### Must Have
- Rate limit /auth/login to 5 requests/minute/IP
- Return 429 status with retry-after header when exceeded

### Must NOT Have
- Admin bypass
- Per-user tracking (IP only)

## Implementation Steps
1. Add rate limit middleware to src/api/middleware/rateLimit.ts
   - Configure: window=60s, max=5, keyGenerator=req.ip
2. Apply middleware to login route in src/routes/auth.ts

## Files to Modify
| File | Changes |
|------|---------|
| `src/routes/auth.ts` | Add rateLimit middleware to POST /login |

## Acceptance Criteria
- [ ] 6th request within 60s returns 429
- [ ] Response includes Retry-After header
```

---

### Example 2: Standard (New Feature)

**Trigger:** `let's plan adding webhook support`

**Interview (5 questions):**

> **Claude:** What problem does webhook support solve for your users?
>
> **User:** They need real-time notifications when orders change status
>
> **Claude:** What's the scope - minimal viable or complete webhook system?
>
> **User:** Start minimal - just order status changes, single URL per user
>
> **Claude:** Any constraints or things to avoid?
>
> **User:** No external queue systems, keep it in-process for now
>
> **Claude:** Retry behavior when webhook delivery fails?
>
> **User:** 3 retries with exponential backoff, then give up
>
> **Claude:** Any security requirements - signatures, auth headers?
>
> **User:** HMAC signature so receivers can verify authenticity

**Research:**
```
Agent: scout
Task: Find order-related event code and existing notification patterns
Result: src/services/orderService.ts emits events, src/events/ has EventEmitter setup
```

```
Agent: librarian
Task: Summarize order event structure and existing patterns
Result: Orders emit 'order:created', 'order:updated' with full order payload
```

**Draft Excerpt:**
```markdown
## Requirements
- Webhook registration (one URL per user)
- Trigger on order status changes
- HMAC-SHA256 signature for verification
- 3 retries with exponential backoff

## Decisions
- Hook into existing order:updated event
- Store webhook URLs in user record (no separate table)
- In-process delivery, no external queue

## Research Findings
- Order events already exist in src/services/orderService.ts
- EventEmitter pattern in src/events/
- User model in src/models/user.ts
```

**Final Plan Excerpt:**
```markdown
# Plan: webhook support for order status

## Context
Users need real-time notifications when their orders change status.
Currently they must poll the API to detect changes.

## Objectives

### Must Have
- Register webhook URL (one per user)
- Fire webhook on order status change
- HMAC-SHA256 signature in X-Signature header
- 3 retries with exponential backoff (1s, 2s, 4s)

### Must NOT Have
- Multiple webhooks per user
- External queue/worker system
- Webhook for events other than order status

## Implementation Steps
1. Add webhookUrl field to User model in src/models/user.ts
2. Create webhook service in src/services/webhookService.ts
   - deliverWebhook(userId, event, payload)
   - generateSignature(payload, secret)
   - retry logic with backoff
3. Subscribe to order:updated in src/events/handlers/webhookHandler.ts
4. Add API endpoints in src/routes/webhooks.ts
   - POST /webhooks/register
   - DELETE /webhooks
   - GET /webhooks/test (sends test payload)

## Files to Modify
| File | Changes |
|------|---------|
| `src/models/user.ts` | Add webhookUrl, webhookSecret fields |
| `src/services/webhookService.ts` | New - delivery, signing, retry |
| `src/events/handlers/webhookHandler.ts` | New - listen to order events |
| `src/routes/webhooks.ts` | New - registration endpoints |
| `src/routes/index.ts` | Mount webhook routes |

## Acceptance Criteria
- [ ] User can register a webhook URL via API
- [ ] Order status change triggers HTTP POST to registered URL
- [ ] Request includes X-Signature header with valid HMAC
- [ ] Failed delivery retries 3 times with backoff
- [ ] Test endpoint delivers sample payload
```

---

### Example 3: Complex (Architecture Change)

**Trigger:** `/plan migrate from REST to GraphQL`

**Interview (8 questions):**

> **Claude:** What's driving this migration - specific pain points with REST?
>
> **User:** Mobile app makes too many round trips, need to batch queries
>
> **Claude:** Full replacement or hybrid (GraphQL alongside REST)?
>
> **User:** Hybrid - new features in GraphQL, REST stays for existing clients
>
> **Claude:** What's the scope - start with which domain?
>
> **User:** User and order domains first, that's what mobile needs
>
> **Claude:** Any GraphQL experience on the team, or greenfield?
>
> **User:** Greenfield, first time
>
> **Claude:** Schema-first or code-first approach preference?
>
> **User:** Code-first, easier for TypeScript devs
>
> **Claude:** Authentication approach - reuse existing or GraphQL-native?
>
> **User:** Reuse existing JWT middleware
>
> **Claude:** Any real-time requirements - subscriptions for live updates?
>
> **User:** Not in phase 1, but design for it
>
> **Claude:** Performance constraints - query depth limits, complexity?
>
> **User:** Yes, prevent deeply nested queries that could DOS us

**Research:**
```
Agent: scout
Task: Map current REST endpoints for user and order domains
Result: 12 endpoints in src/routes/users.ts, 18 in src/routes/orders.ts
```

```
Agent: librarian
Task: Summarize data models and relationships for User and Order
Result: User hasMany Orders, Order hasMany LineItems, Order belongsTo User
```

```
Agent: architect
Task: Evaluate GraphQL library options for Node.js with TypeScript
Result: Recommends @graphql-yoga with pothos for code-first, good TS support
```

**Draft Excerpt:**
```markdown
## Requirements
- GraphQL endpoint alongside existing REST
- User and Order types with queries and mutations
- Reuse existing JWT auth
- Query depth limiting
- Code-first schema with TypeScript

## Decisions
- Library: graphql-yoga + pothos (code-first, TypeScript-native)
- Mount at /graphql, REST unchanged
- Resolver pattern: thin resolvers calling existing services
- Phase 1: queries and mutations only, no subscriptions
- Depth limit: 5 levels max

## Research Findings
- 30 REST endpoints to eventually cover
- User -> Orders -> LineItems relationship
- JWT middleware in src/middleware/auth.ts is reusable
- Existing services (userService, orderService) can back resolvers

## Open Questions
- None remaining
```

**Final Plan Excerpt:**
```markdown
# Plan: GraphQL layer for mobile optimization

## Context
Mobile app makes 4-6 REST calls per screen due to resource-oriented
endpoints. GraphQL allows batching these into single requests.
Adding GraphQL alongside REST - no breaking changes to existing clients.

## Objectives

### Must Have
- /graphql endpoint with graphql-yoga
- User type: queries (me, user, users), mutations (updateProfile)
- Order type: queries (order, orders, myOrders), mutations (createOrder, updateStatus)
- JWT authentication via context
- Query depth limit of 5 levels
- Code-first schema using pothos

### Must NOT Have
- Removal or changes to existing REST endpoints
- Subscriptions (phase 2)
- Coverage of domains beyond User/Order
- Custom scalars beyond DateTime

## Implementation Steps

### Phase 1: Foundation (Week 1)
1. Install dependencies: graphql-yoga, pothos, graphql-depth-limit
2. Create GraphQL server setup in src/graphql/server.ts
3. Configure depth limiting and error formatting
4. Add /graphql route in src/routes/index.ts
5. Create auth context builder reusing JWT middleware

### Phase 2: User Domain (Week 1)
6. Define User type in src/graphql/types/User.ts
7. Implement user queries in src/graphql/resolvers/userQueries.ts
8. Implement user mutations in src/graphql/resolvers/userMutations.ts
9. Add DataLoader for N+1 prevention

### Phase 3: Order Domain (Week 2)
10. Define Order, LineItem types in src/graphql/types/
11. Define relationship: User.orders, Order.customer
12. Implement order queries and mutations
13. Add DataLoader for order->lineItems

### Phase 4: Polish (Week 2)
14. Add query complexity analysis
15. Set up GraphQL Playground for dev
16. Document schema with descriptions
17. Add integration tests for key queries

## Files to Modify
| File | Changes |
|------|---------|
| `package.json` | Add graphql-yoga, pothos, graphql-depth-limit |
| `src/graphql/server.ts` | New - yoga server config |
| `src/graphql/schema.ts` | New - pothos schema builder |
| `src/graphql/types/*.ts` | New - User, Order, LineItem types |
| `src/graphql/resolvers/*.ts` | New - queries and mutations |
| `src/graphql/context.ts` | New - auth context builder |
| `src/graphql/loaders/*.ts` | New - DataLoaders |
| `src/routes/index.ts` | Mount /graphql route |

## Acceptance Criteria
- [ ] POST /graphql accepts valid GraphQL queries
- [ ] Query { me { orders { id } } } returns user's orders in one request
- [ ] Queries deeper than 5 levels are rejected
- [ ] Invalid JWT returns authentication error
- [ ] Existing REST endpoints continue to work unchanged
- [ ] GraphQL Playground accessible in development
```

## Error Handling

### User Interrupts Mid-Planning

**Scenario:** User says "actually never mind" or "let's do something else" during interview.

**Recovery:**
1. Confirm: "Pause planning for '{topic}'? I'll keep the draft if you want to resume later."
2. If confirmed: Leave draft in place at `.claude/plans/drafts/{topic}.md`
3. Log interruption point in draft under "## Status":
   ```markdown
   ## Status
   Phase: Interview (paused)
   Last question: [the question that was pending]
   ```
4. If user says "delete it": confirm and remove draft

---

### Research Phase Fails

**Scenario:** Scout or librarian agent returns errors or finds nothing relevant.

**Recovery Actions:**

| Failure Type | Recovery |
|--------------|----------|
| Agent timeout | Retry once; if still fails, proceed without research and note gap |
| "No files found" | Ask user: "Scout found no relevant files. Can you point me to where this code lives?" |
| Agent returns confused output | Re-run with more specific prompt; if still fails, note gap and proceed |
| Permission error | Skip research, note in draft, proceed with user-provided context |

**Draft notation when research fails:**
```markdown
## Research Findings
- Scout: Unable to complete - no matching files found
- IMPACT: File paths in plan are estimates; verify before implementing
```

**Always inform user:** "Research couldn't find existing patterns. The plan will be based on your input and best practices - you may need to adjust file paths during implementation."

---

### Topic Too Vague

**Scenario:** User says `/plan make it better` or `/plan improve performance`

**Recovery:**
1. Do NOT create a draft yet
2. Ask a scoping question:
   - "Make what better - a specific feature, the codebase structure, or something else?"
   - "Improve performance where - API response times, build speed, database queries?"
3. Wait for clarification before creating draft
4. If user remains vague after 2 attempts: "I need a more specific topic to create an actionable plan. Can you describe the outcome you want?"

**Decision rule:** Create draft only when you can write a meaningful one-line summary of what the plan is for.

---

### Conflicting Requirements

**Scenario:** User provides requirements that contradict each other during interview.

**Examples:**
- "Keep it simple" + "Support all edge cases"
- "No dependencies" + "Use Redis for caching"
- "Finish today" + 20-step feature request

**Recovery:**
1. Name the conflict explicitly: "I'm hearing two things that might conflict: [A] and [B]."
2. Offer resolution options:
   - "Should we prioritize [A] and relax [B]?"
   - "Or prioritize [B] and accept [A] will be limited?"
3. Record the decision in draft:
   ```markdown
   ## Decisions
   - Conflict: User wanted X and Y which are mutually exclusive
   - Resolution: Prioritizing X per user preference; Y deferred to future
   ```

**Never silently pick one side.** Make the trade-off explicit.

---

### Agent Delegation Fails

**Scenario:** Task() call to scout, librarian, or architect fails or hangs.

**Recovery by Agent:**

| Agent | Failure | Recovery |
|-------|---------|----------|
| Scout | No response | Use Glob/Grep directly as fallback |
| Scout | Error | Ask user for file locations manually |
| Librarian | No response | Read files directly (if small) or summarize from grep output |
| Librarian | File too large error | Ask for specific sections to examine |
| Architect | No response | Proceed with planning yourself; note in draft |
| Architect | Confused output | Re-prompt with clearer task; if still fails, handle internally |

**Log delegation failures:**
```markdown
## Research Findings
- Scout delegation failed (timeout after 60s)
- Fallback: Used Glob to find *.ts files in src/
- Found: src/services/orderService.ts, src/routes/orders.ts
```

**Key principle:** Delegation is an optimization. Failures should not block planning - fall back to direct tool use.

---

### User Wants to Finalize Too Early

**Scenario:** User says "create the plan" but interview is incomplete or research hasn't run.

**Recovery:**
1. Check draft status - is there enough to create an actionable plan?
2. If critical gaps exist, say:
   - "I can create a plan now, but I'm missing [X]. The plan will be less actionable without it."
   - "Want me to proceed anyway, or should we [answer one more question / run quick research]?"
3. If user insists: create plan with explicit gaps noted:
   ```markdown
   ## Implementation Steps
   1. [Step based on assumptions - verify file path]

   ## Known Gaps
   - File locations unverified (research skipped)
   - Retry behavior undefined (question skipped)
   ```

## Behavior Rules

### MUST DO
- Create draft file before starting interview
- Update draft after each user response
- Research codebase before finalizing plan
- Include file references in final plan
- Keep interview focused (3-5 questions max)

### MUST NOT
- Auto-generate plan without user confirmation
- Delete draft without user confirmation
- Skip the interview phase
- Generate vague plans without concrete steps

## Handling Existing Drafts

If `/plan <topic>` is called and a draft already exists:

1. Ask user: "Found existing draft for '{topic}'. Resume or start fresh?"
2. If resume: continue from current phase
3. If start fresh: backup old draft as `{topic}-{timestamp}.md.bak`, create new

## Abandoning Plans

When user says "cancel plan" or "abandon planning":
1. Confirm: "Abandon planning for '{topic}'? Draft will be deleted."
2. If confirmed: delete draft file
3. If declined: continue planning

---

**Note:** This skill handles PLANNING only. Implementation is separate - use ultrawork or direct work after plan is approved.
