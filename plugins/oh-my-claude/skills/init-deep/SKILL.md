---
name: init-deep
description: "Initialize or migrate to nested CLAUDE.md structure for progressive disclosure. Claude auto-loads CLAUDE.md from any directory it reads, enabling true contextual guidance. Triggers on: '/init-deep', 'deep init', 'initialize deeply', 'setup claude deeply', 'refactor claude.md', 'migrate claude.md', 'nested claude', 'progressive disclosure'."
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - AskUserQuestion
---

# Init Deep Skill

Create a minimal root CLAUDE.md with nested CLAUDE.md files throughout the repository for true progressive disclosure.

## Key Insight

Claude automatically loads CLAUDE.md from any directory it reads. Instead of centralizing documentation in `.claude/docs/`, place CLAUDE.md files directly in relevant directories. When Claude reads `src/api/users.ts`, it also loads `src/api/CLAUDE.md` - contextual guidance exactly when needed.

**Closest Wins:** When multiple CLAUDE.md files apply, the one closest to the file being edited takes precedence. A rule in `src/api/CLAUDE.md` overrides the same topic in root `CLAUDE.md`.

## When This Skill Activates

| Category | Trigger Phrases |
|----------|-----------------|
| **Initialize** | `/init-deep`, `deep init`, `initialize deeply`, `setup claude deeply` |
| **Migrate** | `refactor claude.md`, `migrate claude.md`, `restructure claude` |
| **Structure** | `nested claude`, `progressive disclosure`, `contextual claude` |

## CLI Variants

```
/init-deep              # Update: modify existing + create new where needed
/init-deep --fresh      # Delete all CLAUDE.md files, regenerate from scratch
/init-deep --max-depth=2 # Limit nesting depth (default: unlimited)
```

| Flag | Behavior |
|------|----------|
| (none) | Additive - creates missing, preserves existing |
| `--fresh` | Destructive - deletes all CLAUDE.md, starts clean |
| `--max-depth=N` | Limits nested CLAUDE.md to N levels deep |

## Philosophy: Instruction Budget

Claude has ~150-200 instruction capacity before diminishing returns. A bloated root CLAUDE.md means wasted context on every interaction.

**Solution:** Minimal root + nested CLAUDE.md files that load only when relevant directories are accessed.

### Size Limits (Strict)

| File | Lines | Status |
|------|-------|--------|
| Root CLAUDE.md | 50-150 | Optimal range |
| Root CLAUDE.md | 150+ | Needs refactoring |
| Nested CLAUDE.md | 30-80 | Optimal range |
| Nested CLAUDE.md | 80+ | Too verbose |

**Telegraphic style required.** No verbose explanations. Each line must carry weight.

### Deduplication Rules

Child CLAUDE.md files NEVER repeat parent content:

- If root says "use TypeScript" - children don't repeat it
- If root defines import order - children inherit it
- Child files add domain-specific rules only

**Review Phase Requirement:** Before finalizing, scan all generated CLAUDE.md files for duplicated guidance. Remove duplicates from children, keep in nearest common ancestor.

---

## Directory Scoring System

Not every directory needs a CLAUDE.md. Use weighted scoring to decide.

### Scoring Formula

```
Score = (file_count * 3) + (reference_centrality * 3) + (symbol_density * 1) + (export_count * 1)
```

| Factor | Weight | How to Measure |
|--------|--------|----------------|
| File count | 3x | Number of files in directory |
| Reference centrality | 3x | How many imports/exports reference this dir |
| Symbol density | 1x | Functions, classes, types defined |
| Export count | 1x | Public API surface |

### Score Thresholds

| Score | Action |
|-------|--------|
| >15 | Definitely gets CLAUDE.md |
| 8-15 | Only if distinct domain (tests, api, components) |
| <8 | Parent CLAUDE.md covers it |

### Quick Heuristics

When scoring isn't practical, use these rules:

| Directory | Create CLAUDE.md? | Reason |
|-----------|-------------------|--------|
| tests/ | YES | Testing patterns are domain-specific |
| src/components/ | YES | Component patterns are specialized |
| src/api/ | YES | API design patterns are critical |
| src/hooks/ | MAYBE | If project has custom hooks |
| src/utils/ | MAYBE | If utility patterns are non-obvious |
| src/services/ | MAYBE | If services have specific patterns |
| src/ | MAYBE | For general coding conventions |
| scripts/ | RARELY | Only if complex build system |
| node_modules/ | NEVER | Not your code |
| dist/ | NEVER | Generated code |

---

## Two Operating Modes

### Mode 1: Fresh Project (No CLAUDE.md)

Create minimal root + nested structure from scratch.

### Mode 2: Existing CLAUDE.md

Analyze, categorize, and migrate content to nested CLAUDE.md files.

---

## Workflow

### Phase 1: Discovery

**Goal:** Understand current state and scope.

**Actions:**

1. Check if root CLAUDE.md exists
2. Scan for common directories that should have nested CLAUDE.md
3. Check for existing nested CLAUDE.md files
4. Detect if `.claude/docs/` exists (old pattern to migrate)
5. Calculate directory scores for prioritization

**Dynamic Agent Scaling:**

| Condition | Action |
|-----------|--------|
| Files >100 | Spawn additional scout agents |
| Depth >=4 | Increase exploration scope |
| Multiple languages | Spawn language-specific analysis |

**Concurrent Execution:** Launch all exploration agents in parallel (one message, multiple Task calls). Do not wait for one to finish before starting others.

**Directory Detection Patterns:**

```
src/           # Source code root
tests/         # Test files
test/          # Alternative test directory
lib/           # Library code
api/           # API layer (may be under src/)
components/    # UI components
hooks/         # React/custom hooks
utils/         # Utility functions
services/      # Service layer
scripts/       # Build/dev scripts
packages/      # Monorepo packages
apps/          # Monorepo apps
```

**Nested directory patterns (check inside src/):**

```
src/api/
src/components/
src/hooks/
src/utils/
src/services/
src/lib/
src/routes/
src/pages/
src/stores/
src/models/
```

**Detection Script:**

```bash
# Find directories that should have CLAUDE.md
for dir in tests test src lib api components hooks utils services scripts packages apps; do
  if [ -d "$dir" ]; then
    echo "FOUND: $dir/"
  fi
done

# Check src/ subdirectories
if [ -d "src" ]; then
  for subdir in api components hooks utils services lib routes pages stores models; do
    if [ -d "src/$subdir" ]; then
      echo "FOUND: src/$subdir/"
    fi
  done
fi
```

---

### Phase 2: Interview

**Goal:** Gather essential project info.

**For Fresh Projects, Ask:**

**Question 1: Project Description**
```
What does this project do? (One sentence)

Example: "A CLI tool for managing Kubernetes deployments"
```

**Question 2: Package Manager**
```
Which package manager does this project use?

Options:
- npm (default, will not be documented)
- pnpm
- yarn
- bun
- none (not a JS/TS project)
```

**Question 3: Non-Standard Commands**
```
Any build, test, or lint commands that differ from standard?

Leave blank if using standard commands (npm test, npm run build).
Only specify if different, e.g., "pytest -v" or "make release"
```

**Question 4: Nested CLAUDE.md Selection**
```
I detected these directories. Which should have their own CLAUDE.md?

Detected:
- [x] tests/
- [x] src/components/
- [x] src/api/
- [ ] src/utils/
- [ ] scripts/

Select all that would benefit from contextual guidance.
(Default: tests/ and any domain-specific src/ directories)
```

**For Existing CLAUDE.md Migration, Ask:**

```
Found existing CLAUDE.md ({N} lines). Options:

1. Analyze and migrate - Extract content to nested CLAUDE.md files
2. Replace - Create fresh minimal structure (backup original)
3. Cancel - Keep existing structure
```

---

### Phase 3: Analysis (Existing CLAUDE.md Only)

**Goal:** Categorize existing content for migration.

**Metrics to Calculate:**

| Metric | How | Threshold |
|--------|-----|-----------|
| Line Count | Total non-empty lines | >150 = needs migration |
| Instruction Count | Count MUST/NEVER/ALWAYS/should | >30 = instruction overload |
| Hardcoded Paths | Regex for file paths | >10 = staleness risk |
| Sections | Count ## headers | >8 = fragmented |

**Content Categorization:**

Map existing content to potential nested locations:

| Content Type | Destination |
|--------------|-------------|
| Project description, tech stack | Root CLAUDE.md |
| Package manager, build commands | Root CLAUDE.md |
| Task-to-location mapping | Root CLAUDE.md |
| Agent workflow guidance | Root CLAUDE.md |
| Testing patterns, mocking, coverage | tests/CLAUDE.md |
| Component patterns, naming, props | src/components/CLAUDE.md |
| API design, endpoints, error handling | src/api/CLAUDE.md |
| Hook patterns, naming, dependencies | src/hooks/CLAUDE.md |
| Utility patterns, when to use | src/utils/CLAUDE.md |
| Service patterns, external integrations | src/services/CLAUDE.md |
| Coding conventions (general) | Root or src/CLAUDE.md |

**Analysis Output Template:**

```markdown
## CLAUDE.md Analysis

### Metrics
| Metric | Value | Status |
|--------|-------|--------|
| Total Lines | 245 | MIGRATE |
| Instructions | 52 | HIGH |
| Hardcoded Paths | 18 | WARNING |

### Content Migration Plan
| Lines | Content | Destination |
|-------|---------|-------------|
| 1-15 | Project description | Root CLAUDE.md |
| 20-45 | Testing patterns | tests/CLAUDE.md |
| 50-95 | Component conventions | src/components/CLAUDE.md |
| 100-140 | API design patterns | src/api/CLAUDE.md |
| 145-180 | General coding style | src/CLAUDE.md |
| 185-245 | Outdated/stale content | REMOVE (with approval) |
```

---

### Phase 4: Generation

**Goal:** Create minimal root + nested CLAUDE.md files.

**Parallel Generation:** When creating multiple nested CLAUDE.md files, generate them in parallel (multiple Write calls in one message).

#### Root CLAUDE.md Template (50-100 lines target)

```markdown
# {Project Name}

{One-sentence description}

## Development

{Package manager line - ONLY if not npm}

{Non-standard commands - ONLY if provided}

## Where to Look

| Task | Location |
|------|----------|
| Add new API endpoint | src/api/ |
| Add UI component | src/components/ |
| Add utility function | src/utils/ |
| Write tests | tests/ |
| Add service integration | src/services/ |
| Modify build/deploy | scripts/ |

## Agent Workflow

Scout finds -> Librarian reads -> You plan -> Worker implements -> Validator checks

When delegating to agents:
- Use positive constraints ("ensure X") not negative ("don't do Y")
- Include context, expected output, acceptance criteria
- Launch independent tasks in parallel

## Guidance

Context-specific guidance lives in nested CLAUDE.md files throughout the repo.
These load automatically when you work in those directories.
Closest CLAUDE.md to the file being edited takes precedence.
```

**Conditional Rules:**
- Omit "Package manager" if npm
- Omit "Development" section if no non-standard info
- Customize "Where to Look" table based on actual project structure
- Never include coding conventions (put in src/CLAUDE.md or nested)

#### Nested CLAUDE.md Templates

Each nested file: 30-80 lines max. Telegraphic style. Domain-specific anti-patterns required.

---

**tests/CLAUDE.md Template (30-50 lines):**

```markdown
# Testing

## Framework

{e.g., Jest, Vitest, pytest, Go testing}

## Patterns

- Test files: `*.test.ts` or `*.spec.ts`
- Describe blocks mirror module structure
- One assertion per test when practical

## Running Tests

```bash
{test command}
```

## Mocking

- Prefer real implementations over mocks
- Mock only: network, time, randomness, file system

## Coverage

Focus on behavior, not percentage. Critical paths need thorough coverage.

## Anti-Patterns

- Don't mock what you can test directly
- Don't test implementation details
- Don't share mutable state between tests
- Don't write tests that pass when code is broken
```

---

**src/components/CLAUDE.md Template (30-50 lines):**

```markdown
# Components

## Structure

```
ComponentName/
  index.ts          # Re-export
  ComponentName.tsx # Implementation
  ComponentName.test.tsx
```

## Naming

- Components: PascalCase
- Props interface: `{ComponentName}Props`
- Files match component name

## Patterns

- Prefer composition over inheritance
- Extract hooks for reusable logic
- Props over context for explicit dependencies

## Exports

{Named exports / default exports preference}

## Anti-Patterns

- Don't use inline styles when CSS modules exist
- Don't prop-drill beyond 2 levels - use context
- Don't mix data fetching with presentation
- Don't create god components (>200 lines)
```

---

**src/api/CLAUDE.md Template (30-50 lines):**

```markdown
# API Layer

## Design

- RESTful endpoints / GraphQL / tRPC
- Consistent error response format
- Request validation at boundary

## Patterns

- Controllers handle HTTP concerns only
- Business logic lives in services
- Validate input, sanitize output

## Error Handling

```
{error response format example}
```

## Authentication

{auth pattern if applicable}

## Anti-Patterns

- Don't expose internal errors to clients
- Don't skip input validation
- Don't leak sensitive data in responses
- Don't mix auth logic with business logic
```

---

**src/hooks/CLAUDE.md Template (30-50 lines):**

```markdown
# Hooks

## Naming

- Prefix with `use`: `useAuth`, `useForm`, `useFetch`
- Name describes the capability, not implementation

## Patterns

- Single responsibility per hook
- Return stable references (useMemo, useCallback)
- Handle cleanup in useEffect

## Testing

- Test hooks via @testing-library/react-hooks
- Test state transitions, not implementation

## Common Hooks

{list project-specific hooks if established}

## Anti-Patterns

- Don't call hooks conditionally
- Don't create hooks with side effects on mount without cleanup
- Don't return unstable references
- Don't nest hooks more than 2 levels deep
```

---

**src/utils/CLAUDE.md Template (30-50 lines):**

```markdown
# Utilities

## When to Create

Create a utility when:
- Logic is used in 3+ places
- Function is pure (no side effects)
- Behavior is well-defined and testable

## Patterns

- Pure functions preferred
- No dependencies on external state
- Comprehensive input validation
- Clear, descriptive names

## Naming

- Functions: camelCase, verb-first (`formatDate`, `parseInput`)
- Files: kebab-case or camelCase (match project convention)

## Testing

Every utility function needs tests. They're isolated and easy to test.

## Anti-Patterns

- Don't create utils for single-use logic
- Don't add side effects to pure functions
- Don't create "misc" or "helpers" grab-bags
- Don't depend on global state
```

---

**src/services/CLAUDE.md Template (30-50 lines):**

```markdown
# Services

## Purpose

Services encapsulate external integrations and complex business logic.

## Patterns

- One service per external dependency
- Services are injectable/mockable
- Handle retries, timeouts, circuit breaking

## Structure

```
services/
  userService.ts
  authService.ts
  emailService.ts
```

## Error Handling

- Wrap external errors in domain-specific errors
- Log at service boundary
- Never expose internal details to callers

## Anti-Patterns

- Don't call services from other services directly - use orchestrator
- Don't mix HTTP/DB concerns in same service
- Don't retry without backoff
- Don't swallow errors silently
```

---

**src/CLAUDE.md Template (30-50 lines):**

```markdown
# Source Code

## Style

- {indent style}
- {semicolons yes/no}
- {quote style}

## Imports

```typescript
// 1. External packages
// 2. Internal aliases (@/)
// 3. Relative imports
// 4. Types (import type)
```

## Naming

- Files: {convention}
- Functions: camelCase
- Classes: PascalCase
- Constants: SCREAMING_SNAKE

## Patterns

- Prefer early returns
- Explicit over implicit
- Composition over inheritance

## Anti-Patterns

- Don't use `any` - use `unknown` and narrow
- Don't nest callbacks >2 levels
- Don't mutate function arguments
- Don't use magic numbers without constants
```

---

**scripts/CLAUDE.md Template (30-50 lines):**

```markdown
# Scripts

## Purpose

Build, deployment, and development automation scripts.

## Conventions

- Scripts are executable: `chmod +x script.sh`
- Include usage comment at top
- Exit codes: 0 success, 1 error
- Use `set -euo pipefail` for bash scripts

## Running

```bash
./scripts/{script-name}.sh
# or
npm run {script-name}
```

## Adding New Scripts

1. Create in scripts/ directory
2. Add npm script alias if frequently used
3. Document purpose in script header

## Anti-Patterns

- Don't hardcode paths - use variables
- Don't skip error handling
- Don't assume dependencies exist - check first
- Don't write scripts without idempotency
```

---

### Phase 5: Execution

**For Fresh Projects:**

1. Create root CLAUDE.md
2. Create nested CLAUDE.md files in detected/selected directories (parallel writes)
3. Report created files

**For Migration:**

1. Create backup: `cp CLAUDE.md CLAUDE.md.backup`
2. Create nested CLAUDE.md files with migrated content
3. Rewrite root CLAUDE.md to minimal version
4. If `.claude/docs/` exists, offer to migrate or remove
5. Present before/after comparison

**For --fresh Flag:**

1. Find all existing CLAUDE.md files: `find . -name "CLAUDE.md" -type f`
2. Delete all found CLAUDE.md files
3. Run fresh project workflow

**Deduplication Check (Required):**

Before finalizing, review all generated files:
1. List all rules in root CLAUDE.md
2. Check each nested file for duplicates
3. Remove any duplicated guidance from children
4. Only domain-specific additions remain in nested files

**Before/After Report:**

```markdown
## Migration Complete

### Before
- Root CLAUDE.md: 245 lines
- Nested CLAUDE.md: 0 files
- .claude/docs/: 3 files

### After
- Root CLAUDE.md: 85 lines (65% reduction)
- Nested CLAUDE.md: 4 files
  - tests/CLAUDE.md (35 lines)
  - src/components/CLAUDE.md (42 lines)
  - src/api/CLAUDE.md (38 lines)
  - src/CLAUDE.md (30 lines)

### Backup
Original preserved at CLAUDE.md.backup

### Benefit
Root context cost reduced from 245 to 85 lines.
Domain guidance loads only when working in those directories.
```

---

## Behavior Rules

### MUST DO

- Detect existing CLAUDE.md before creating
- Ask before overwriting any existing CLAUDE.md files
- Create backup before modifying existing root CLAUDE.md
- Keep root CLAUDE.md 50-150 lines
- Keep nested CLAUDE.md files 30-80 lines each
- Include domain-specific anti-patterns in each nested file
- Run deduplication check before finalizing
- Use parallel Task calls for exploration
- Use parallel Write calls for generation

### MUST NOT

- Document hardcoded file paths (they go stale)
- Include standard commands (npm test, npm run build)
- Reference `.claude/docs/` (old pattern)
- Create overly comprehensive documentation
- Create nested CLAUDE.md in directories that don't benefit
- Duplicate parent guidance in child files
- Execute agents sequentially when parallel is possible

### SHOULD DO

- Explain the auto-loading behavior
- Explain "closest wins" precedence
- Suggest which directories would benefit from nested CLAUDE.md
- Offer to migrate `.claude/docs/` content if it exists
- Provide line counts in final report
- Use scoring system for borderline directories

---

## Content Location Decision

| Content Type | Location |
|--------------|----------|
| Project purpose | Root |
| Package manager | Root |
| Non-standard commands | Root |
| Where-to-look table | Root |
| Agent workflow guidance | Root |
| Testing philosophy | tests/CLAUDE.md |
| Component patterns | src/components/CLAUDE.md |
| API conventions | src/api/CLAUDE.md |
| General code style | src/CLAUDE.md |
| Import ordering | src/CLAUDE.md |
| Naming conventions | src/CLAUDE.md or domain-specific |

---

## Error Handling

### Directory Doesn't Exist

If selected directory doesn't exist:
1. Ask: "Directory {dir} doesn't exist. Create it with CLAUDE.md, or skip?"
2. Options: Create directory, Skip

### Existing Nested CLAUDE.md

If nested CLAUDE.md already exists:
1. Read current content
2. Ask: "Found existing {dir}/CLAUDE.md. Merge, replace, or skip?"
3. Options: Merge (append new patterns), Replace (backup first), Skip

### Permission Denied

If cannot write files:
1. Output generated content to chat
2. Say: "Could not write files. Here's the content to add manually:"

---

## Post-Generation Message

After creating files:

```
Created nested CLAUDE.md structure:

Root:
  - CLAUDE.md ({N} lines)

Nested:
  - tests/CLAUDE.md ({N} lines) - Testing patterns
  - src/components/CLAUDE.md ({N} lines) - Component patterns
  - src/api/CLAUDE.md ({N} lines) - API patterns

How it works:
Claude automatically loads CLAUDE.md from any directory it reads.
When you work in src/api/, the API patterns load automatically.
Closest file to your edit takes precedence ("closest wins").

Next steps:
1. Review each CLAUDE.md and customize for your project
2. Add patterns as they emerge during development
3. Keep files focused and minimal (30-80 lines nested, 50-150 root)
```
