// site/src/content/copy.ts
// Draft artifact — copy is pasted into components, NOT imported at runtime.
// This file exists so all copy can be reviewed in one place.

// ── Hero ────────────────────────────────────────────────────────
export const heroHeadline = "Stop Wasting Your Context Window"
export const heroTagline = "A Claude Code plugin that delegates file reading, searching, and implementation to specialized agents — so your main session stays sharp."

// ── Stats Bar ───────────────────────────────────────────────────
export const stats = [
  { value: "6", label: "Custom Agents" },
  { value: "11", label: "Built-in Skills" },
  { value: "17", label: "Lifecycle Hooks" },
  { value: "1", label: "Plugin Install" },
]

// ── How It Works ────────────────────────────────────────────────
export const howItWorksSectionTitle = "Three steps. Zero hand-holding."
export const howItWorksSteps = [
  {
    step: 1,
    title: "You ask",
    description: "Describe what you need. A feature, a bug fix, a refactor — whatever. Type it like you're talking to a senior dev.",
    snippet: '$ "Add auth to the API routes"',
  },
  {
    step: 2,
    title: "Agents swarm",
    description: "Built-in Explore finds files. Librarian reads them. Plan mode designs. Tasks implement. Your context window never sees the raw dump.",
    snippet: "Explore → librarian → Plan → Task",
  },
  {
    step: 3,
    title: "You get results",
    description: "Clean output lands in your session. Code written, tests passing, files changed. You stayed in reasoning mode the whole time.",
    snippet: "4 files changed, tests passing",
  },
]

// ── Use Cases ───────────────────────────────────────────────────
export const useCasesSectionTitle = "Built for how you actually work"
export const useCases = [
  {
    title: "Exploring a New Codebase",
    description: "Drop into an unfamiliar repo without flooding your context with every file.",
    terminal: `Explore finds → 47 files matched
librarian reads → 3 relevant modules
Plan mode → dependency graph built
> "Auth lives in src/middleware/, uses JWT"`,
    accent: "cyan",
  },
  {
    title: "Implementing a Feature",
    description: "Describe what you want. The agent swarm handles the rest while you review.",
    terminal: `Plan mode → 5-step plan created
Task[1] → src/routes/auth.ts written
Task[2] → src/middleware/jwt.ts written
validator → all 12 tests passing`,
    accent: "coral",
  },
  {
    title: "Debugging Production",
    description: "When you're stuck after two attempts, use ultradebug skill for deep reasoning you shouldn't burn context on.",
    terminal: `ultradebug → root cause: race condition
  in useEffect cleanup on unmount
Task → fix applied to 2 files
validator → regression suite green`,
    accent: "cyan",
  },
]

// ── Features (rewritten, benefit-focused) ───────────────────────
export const featuresSectionTitle = "Your context is not a dumpster"
export const featuresSectionSubtitle = "Four systems that keep your session focused on what matters: reasoning."
export const features = [
  {
    icon: "shield",
    title: "Your context is sacred",
    description: "Raw file dumps destroy response quality. Subagents handle reading, searching, and grepping — your session only sees the conclusions.",
  },
  {
    icon: "zap",
    title: "Structured execution, not vibes",
    description: "Automatic task creation, progress tracking, and parallel agent delegation. Every complex task gets a plan before anyone writes code.",
  },
  {
    icon: "terminal",
    title: "Git workflows that don't suck",
    description: "Conventional commits, draft PRs, worktree isolation. Built-in skills handle the ceremony so you focus on the code.",
  },
  {
    icon: "cog",
    title: "Hooks that enforce your standards",
    description: "Python hooks inject context, validate actions, and catch mistakes automatically. Your patterns, enforced on every interaction.",
  },
]

// ── Plan Mode ───────────────────────────────────────────────────
export const planModeSectionTitle = "Plan mode, supercharged."
export const planModeSectionSubtitle = "Enter plan mode and get a structured 6-step pipeline automatically. No magic words needed — just Shift+Tab."
export const planModePipeline = [
  { step: 1, label: "Recon", description: "Explore and librarian gather codebase context before any questions are asked.", agent: "Explore + librarian" },
  { step: 2, label: "Interview", description: "Smart, recon-informed questions via AskUserQuestion. No guessing.", agent: null },
  { step: 3, label: "Research", description: "Targeted deep research informed by your answers.", agent: "Explore + librarian" },
  { step: 4, label: "Gap Analysis", description: "Advisor catches hidden assumptions, missing context, and scope risks.", agent: "advisor" },
  { step: 5, label: "Write Plan", description: "Structured plan with file:line refs, decisions, and risks.", agent: null },
  { step: 6, label: "Critic Review", description: "Critic must approve before plan exits. Loops until the plan is solid.", agent: "critic" },
]
export const planModeKeywords = [
  { keyword: "ultrawork", shortcut: "ulw", description: "Maximum execution intensity. Relentless task tracking and parallel delegation." },
  { keyword: "ultraresearch", shortcut: "ulr", description: "Systematic research with parallel searches, cross-referencing, and citations." },
  { keyword: "ultradebug", shortcut: "uld", description: "Forensic debugging protocol. Multiple hypotheses, 3-strike escalation." },
]

// ── Agent Grid (updated header) ─────────────────────────────────
export const agentGridTitle = "Meet the swarm"
export const agentGridSubtitle = "6 custom agents that extend Claude's built-in capabilities. Each does one thing well. None of them pollute your context window."

// ── Agent Teams ─────────────────────────────────────────────────
export const agentTeamsTitle = "One lead. Many teammates."
export const agentTeamsSubtitle = "Claude Code's agent teams let you spawn parallel sessions that coordinate through shared task lists and messaging. oh-my-claude makes every session smarter."
export const agentTeamsEnhancements = [
  { title: "Context protection everywhere", description: "Every teammate gets the same context discipline. Hooks enforce delegation to specialists and warn on context pressure — automatically." },
  { title: "Specialist agents for every role", description: "Teammates spawn librarian for file reading, advisor for gap analysis, critic for plan review, and code-reviewer before merge. No teammate wastes context on raw file dumps." },
  { title: "Standards enforced at scale", description: "Commit quality, TDD requirements, danger blocking, and safe permissions — all hooks fire in every session. Three teammates means three times the enforcement, not three times the risk." },
  { title: "Dual-mode intelligence", description: "Hooks detect whether they are running in a lead, teammate, or solo session and adapt behavior accordingly. Team leads get delegation reminders. Teammates get implementation focus." },
]

// ── Footer ──────────────────────────────────────────────────────
export const footerLine = "Built by someone who got tired of watching Claude forget what it just read."
