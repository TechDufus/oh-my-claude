import { useState, useEffect, useRef } from 'react'

const SPINNER = ['\u273D', '\u273B', '\u2733', '\u2735']

// Types
type ContentLineType =
  | 'logo'
  | 'thinking'
  | 'task-header'
  | 'task-item'
  | 'agent-header'
  | 'agent-row'
  | 'success'
  | 'submitted-prompt'

interface ContentLine {
  id: string
  type: ContentLineType
  content: string
  status?: 'pending' | 'running' | 'complete'
  indent?: number
}

interface Task {
  id: string
  label: string
  status: 'pending' | 'running' | 'complete'
}

interface Agent {
  id: string
  name: string
  task: string
  toolUses: number
  tokens: number
  status: 'running' | 'complete'
  statusText: string
}

// Phase configuration for multi-phase animation
interface PhaseConfig {
  id: string
  name: string
  tasks: Task[]
  agents: Agent[]
}

const PHASES: PhaseConfig[] = [
  {
    id: 'research',
    name: 'Phase 1: Research',
    tasks: [
      { id: 't1', label: 'Explore codebase and find patterns', status: 'pending' }
    ],
    agents: [
      { id: 'a1', name: 'Explore', task: 'Find files', toolUses: 12, tokens: 0, status: 'running', statusText: 'Searching...' },
      { id: 'a2', name: 'Explore', task: 'Map deps', toolUses: 8, tokens: 0, status: 'running', statusText: 'Mapping...' },
      { id: 'a3', name: 'oh-my-claude:librarian', task: 'Read patterns', toolUses: 6, tokens: 0, status: 'running', statusText: 'Reading...' },
    ]
  },
  {
    id: 'implementation',
    name: 'Phase 2: Implementation',
    tasks: [
      { id: 't2', label: 'Implement auth middleware', status: 'pending' },
      { id: 't3', label: 'Add validation logic', status: 'pending' },
      { id: 't4', label: 'Update API routes', status: 'pending' },
      { id: 't5', label: 'Wire up error handling', status: 'pending' },
    ],
    agents: [
      { id: 'a4', name: 'Task', task: 'Auth middleware', toolUses: 14, tokens: 0, status: 'running', statusText: 'Writing...' },
      { id: 'a5', name: 'Task', task: 'Validation', toolUses: 10, tokens: 0, status: 'running', statusText: 'Writing...' },
      { id: 'a6', name: 'Task', task: 'API routes', toolUses: 12, tokens: 0, status: 'running', statusText: 'Writing...' },
      { id: 'a7', name: 'Task', task: 'Error handling', toolUses: 8, tokens: 0, status: 'running', statusText: 'Writing...' },
    ]
  },
  {
    id: 'validation',
    name: 'Phase 3: Validation',
    tasks: [
      { id: 't6', label: 'Run tests and linters', status: 'pending' },
      { id: 't7', label: 'Commit changes', status: 'pending' },
    ],
    agents: [
      { id: 'a8', name: 'oh-my-claude:validator', task: 'Run tests', toolUses: 4, tokens: 0, status: 'running', statusText: 'Testing...' },
      { id: 'a9', name: 'oh-my-claude:validator', task: 'Run lints', toolUses: 2, tokens: 0, status: 'running', statusText: 'Linting...' },
      { id: 'a10', name: 'Task', task: 'Git commit', toolUses: 3, tokens: 0, status: 'running', statusText: 'Committing...' },
    ]
  }
]

// Collect all tasks across phases for initial state
const ALL_TASKS: Task[] = PHASES.flatMap(p => p.tasks)

function TerminalHeader() {
  return (
    <div className="flex items-center px-4 py-3 bg-zinc-900 border-b border-zinc-700">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-red-500"></div>
        <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
        <div className="w-3 h-3 rounded-full bg-green-500"></div>
      </div>
      <div className="flex-1 text-center">
        <span className="text-zinc-500 text-sm font-['JetBrains_Mono',_ui-monospace,_monospace]">oh-my-claude</span>
      </div>
      <div className="w-[52px]"></div> {/* Spacer to balance the dots */}
    </div>
  )
}

function PulsingLine({ active }: { active: boolean }) {
  return (
    <div className="h-0.5 bg-zinc-800 overflow-hidden relative">
      {active && (
        <div
          className="absolute h-full w-1/4 bg-gradient-to-r from-transparent via-orange-500 to-transparent"
          style={{
            animation: 'pulse-slide 2s ease-in-out infinite'
          }}
        ></div>
      )}
    </div>
  )
}

interface StatusBarProps {
  phase: 'idle' | 'running' | 'complete'
  cost: string
  tokens: string
  agentCount: number
}

function StatusBar({ phase, cost, tokens, agentCount }: StatusBarProps) {
  const status = phase === 'idle'
    ? 'Ready'
    : phase === 'complete'
      ? 'Complete'
      : `${agentCount} agents active`

  return (
    <div className="flex items-center gap-4 px-4 py-2 bg-zinc-900 border-t border-zinc-700 text-xs text-zinc-400">
      <span>claude-opus-4-5</span>
      <span className="text-zinc-600">|</span>
      <span>{cost}</span>
      <span className="text-zinc-600">|</span>
      <span>{tokens}</span>
      <span className="text-zinc-600">|</span>
      <span className={phase === 'complete' ? 'text-emerald-400' : 'text-green-400'}>
        {status}
      </span>
    </div>
  )
}

interface PromptLineProps {
  content: string
  status: 'idle' | 'typing' | 'submitted'
}

function PromptLine({ content, status }: PromptLineProps) {
  return (
    <div className="px-4 py-2 border-t border-zinc-800 text-sm font-['JetBrains_Mono',_ui-monospace,_monospace]">
      <span className="text-zinc-500">{'>'}</span>{' '}
      {status !== 'submitted' && (
        <>
          <span className="text-cyan-400">{content}</span>
          {status === 'typing' && <span className="animate-pulse text-cyan-400">|</span>}
        </>
      )}
    </div>
  )
}

interface ContentLineRendererProps {
  line: ContentLine
  spinnerIndex: number
  agents: Agent[]
  tasks: Task[]
  completedTaskIds: string[]
}

function ContentLineRenderer({ line, spinnerIndex, agents, tasks, completedTaskIds }: ContentLineRendererProps) {
  const indent = line.indent ? `pl-${line.indent * 2}` : ''

  switch (line.type) {
    case 'logo':
      return (
        <div className="px-1 py-3 mx-0 mb-2 border border-orange-500 rounded">
          <div className="flex justify-between">
            {/* Left side - logo and version */}
            <div className="flex items-center gap-6 flex-1">
              <div className="p-1">
                <svg viewBox="0 0 32 32" className="w-20 h-20">
                  <g transform="translate(3, 2)">
                    {/* Head top */}
                    <rect x="8" y="0" width="10" height="2" fill="#DA7756"/>
                    <rect x="6" y="2" width="14" height="2" fill="#DA7756"/>
                    <rect x="4" y="4" width="18" height="2" fill="#DA7756"/>
                    <rect x="2" y="6" width="22" height="2" fill="#DA7756"/>
                    {/* Face row */}
                    <rect x="2" y="8" width="22" height="6" fill="#DA7756"/>
                    {/* Sunglasses */}
                    <rect x="3" y="8" width="8" height="5" fill="#111"/>
                    <rect x="4" y="9" width="6" height="3" fill="#1a3a4a"/>
                    <rect x="11" y="9" width="4" height="2" fill="#111"/>
                    <rect x="15" y="8" width="8" height="5" fill="#111"/>
                    <rect x="16" y="9" width="6" height="3" fill="#1a3a4a"/>
                    <rect x="5" y="9" width="2" height="1" fill="#3a6a7a"/>
                    <rect x="17" y="9" width="2" height="1" fill="#3a6a7a"/>
                    <rect x="0" y="9" width="3" height="2" fill="#111"/>
                    <rect x="23" y="9" width="3" height="2" fill="#111"/>
                    {/* Lower face */}
                    <rect x="2" y="14" width="22" height="2" fill="#DA7756"/>
                    <rect x="4" y="16" width="18" height="2" fill="#DA7756"/>
                    <rect x="6" y="18" width="14" height="2" fill="#DA7756"/>
                    {/* Tentacles */}
                    <rect x="6" y="20" width="3" height="5" fill="#DA7756"/>
                    <rect x="11" y="20" width="4" height="6" fill="#DA7756"/>
                    <rect x="17" y="20" width="3" height="5" fill="#DA7756"/>
                  </g>
                </svg>
              </div>
              <div className="text-zinc-400 text-xs">
                <div className="text-zinc-300">Claude Code v2.1.19</div>
                <div>oh-my-claude</div>
              </div>
            </div>
            {/* Orange divider */}
            <div className="w-0.5 bg-orange-500 mx-4 self-stretch"></div>
            {/* Right side - tips */}
            <div className="text-xs text-zinc-400 flex-1">
              <div className="text-orange-400 font-medium">Tips for getting started</div>
              <div>Use plan mode for complex tasks</div>
              <div>Use ultrawork for maximum effort</div>
              <div className="text-orange-400 font-medium mt-2">Recent activity</div>
              <div>No recent activity</div>
            </div>
          </div>
        </div>
      )

    case 'thinking':
      return (
        <div className={`text-zinc-400 ${indent}`}>
          <span className="text-yellow-400">{SPINNER[spinnerIndex]}</span> {line.content}
        </div>
      )

    case 'task-header':
      return (
        <div className={`text-zinc-300 mt-2 ${indent}`}>
          {line.content}
        </div>
      )

    case 'task-item': {
      const task = tasks.find(t => t.id === line.id)
      const isComplete = task?.status === 'complete'
      const isRunning = task?.status === 'running'
      const isFromPreviousPhase = completedTaskIds.includes(line.id)

      return (
        <div className={`text-zinc-400 ${indent}`}>
          <span className={isComplete || isFromPreviousPhase ? 'text-green-400' : isRunning ? 'text-yellow-400' : 'text-zinc-500'}>
            {isComplete || isFromPreviousPhase ? '[✓]' : isRunning ? `[${SPINNER[spinnerIndex]}]` : '[ ]'}
          </span>{' '}
          <span className={
            isFromPreviousPhase
              ? 'line-through text-zinc-600'
              : isComplete
                ? 'text-zinc-300'
                : isRunning
                  ? 'text-zinc-300'
                  : ''
          }>
            {line.content}
          </span>
          {isComplete && !isFromPreviousPhase && <span className="text-green-400 ml-1">ok</span>}
        </div>
      )
    }

    case 'agent-header': {
      const allComplete = agents.every(a => a.status === 'complete')
      return (
        <div className="flex items-center gap-2 text-zinc-300 mt-3">
          <span className={allComplete ? 'text-green-400' : 'text-green-400'}>*</span>
          <span>{line.content}</span>
          <span className="text-zinc-600">(ctrl+o to expand)</span>
        </div>
      )
    }

    case 'agent-row': {
      const agent = agents.find(a => a.id === line.id)
      if (!agent) return null
      return (
        <div className="pl-2 text-zinc-400">
          <div className="flex items-center gap-1">
            <span className="text-zinc-600">⎿</span>
            <span className="text-cyan-400">{agent.name}</span>
            <span className="text-zinc-500">({agent.task})</span>
            <span className="text-zinc-600">*</span>
            <span>{agent.toolUses} uses</span>
            <span className="text-zinc-600">*</span>
            <span>{Math.round(agent.tokens / 1000)}k</span>
          </div>
          <div className="flex items-center gap-1 text-zinc-500">
            <span className="text-zinc-600">  ⎿</span>
            {agent.status === 'running' ? (
              <>
                <span className="text-yellow-400">{SPINNER[spinnerIndex]}</span>
                <span>{agent.statusText}</span>
              </>
            ) : (
              <span className="text-green-400">Done</span>
            )}
          </div>
        </div>
      )
    }

    case 'success':
      return (
        <div className="text-green-400 mt-3 font-medium">
          {line.content}
        </div>
      )

    case 'submitted-prompt':
      return (
        <div className="mb-2">
          <span className="text-zinc-500">{'>'}</span>{' '}
          <span className="text-cyan-400">{line.content}</span>
        </div>
      )

    default:
      return <div className="text-zinc-400">{line.content}</div>
  }
}

export default function TerminalHero() {
  const [phase, setPhase] = useState<'idle' | 'running' | 'complete'>('idle')
  const [spinnerIndex, setSpinnerIndex] = useState(0)
  const [contentLines, setContentLines] = useState<ContentLine[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [tasks, setTasks] = useState<Task[]>(ALL_TASKS.map(t => ({ ...t, status: 'pending' })))
  const [typedPrompt, setTypedPrompt] = useState('')
  const [cycle, setCycle] = useState(0)
  const [parentTokens, setParentTokens] = useState(0)
  const [completedTaskIds, setCompletedTaskIds] = useState<string[]>([])
  const [promptStatus, setPromptStatus] = useState<'idle' | 'typing' | 'submitted'>('idle')

  const fullPrompt = 'Implement user authentication system ultrawork'

  // Main animation timeline - 15s total (3-phase execution)
  useEffect(() => {
    const timeouts: ReturnType<typeof setTimeout>[] = []
    const intervals: ReturnType<typeof setInterval>[] = []
    let typeInterval: ReturnType<typeof setInterval> | null = null

    // Reset state at start
    setContentLines([{ id: 'logo', type: 'logo', content: '' }])
    setAgents([])
    setTasks(ALL_TASKS.map(t => ({ ...t, status: 'pending' })))
    setTypedPrompt('')
    setPhase('idle')
    setParentTokens(0)
    setCompletedTaskIds([])
    setPromptStatus('idle')

    // Helper to add a line
    const addLine = (line: ContentLine) => {
      setContentLines(prev => [...prev, line])
    }

    // Helper to remove lines by id prefix
    const removeLinesByPrefix = (prefix: string) => {
      setContentLines(prev => prev.filter(l => !l.id.startsWith(prefix)))
    }

    // Start token growth interval (runs throughout)
    let tokenGrowthInterval: ReturnType<typeof setInterval> | null = null
    let parentTokenInterval: ReturnType<typeof setInterval> | null = null

    const startTokenGrowth = () => {
      tokenGrowthInterval = setInterval(() => {
        setAgents(prev => prev.map(a =>
          a.status === 'running'
            ? { ...a, tokens: a.tokens + Math.floor(Math.random() * 800) + 200 }
            : a
        ))
      }, 250)
      intervals.push(tokenGrowthInterval)

      parentTokenInterval = setInterval(() => {
        setParentTokens(prev => prev + Math.floor(Math.random() * 150) + 50)
      }, 500)
      intervals.push(parentTokenInterval)
    }

    // 0ms - Logo is already visible (fixed header)

    // 500ms - Start typing prompt
    timeouts.push(setTimeout(() => {
      setPhase('running')
      setPromptStatus('typing')

      let charIndex = 0
      typeInterval = setInterval(() => {
        if (charIndex < fullPrompt.length) {
          charIndex++
          setTypedPrompt(fullPrompt.slice(0, charIndex))
        } else {
          if (typeInterval) clearInterval(typeInterval)
          // Add prompt to content lines as submitted
          setContentLines(prev => [...prev, { id: 'submitted-prompt', type: 'submitted-prompt', content: fullPrompt }])
          setTypedPrompt('')
          setPromptStatus('submitted')
        }
      }, 40)
    }, 500))

    // 2500ms - Thinking appears (after prompt submission at ~2300ms)
    timeouts.push(setTimeout(() => {
      addLine({ id: 'thinking', type: 'thinking', content: 'Thinking...' })
    }, 2500))

    // ========== PHASE 1: RESEARCH ==========

    // 2800ms - Phase 1 task header
    timeouts.push(setTimeout(() => {
      addLine({ id: 'task-header-1', type: 'task-header', content: PHASES[0].name })
    }, 2800))

    // 3000ms - Phase 1 task list (1 task)
    timeouts.push(setTimeout(() => {
      PHASES[0].tasks.forEach(task => {
        addLine({ id: task.id, type: 'task-item', content: task.label, indent: 1 })
      })
    }, 3000))

    // 3300ms - Phase 1 agent header
    timeouts.push(setTimeout(() => {
      addLine({ id: 'agent-header', type: 'agent-header', content: `${PHASES[0].agents.length} agents running` })
    }, 3300))

    // 3500ms - Phase 1 agents appear, task starts running
    timeouts.push(setTimeout(() => {
      // Initialize phase 1 agents with random starting tokens
      const phase1Agents = PHASES[0].agents.map(a => ({
        ...a,
        tokens: Math.floor(Math.random() * 3000) + 5000
      }))
      setAgents(phase1Agents)

      // Add agent rows
      phase1Agents.forEach(agent => {
        addLine({ id: agent.id, type: 'agent-row', content: '' })
      })

      // Task t1 starts running
      setTasks(prev => prev.map(t => t.id === 't1' ? { ...t, status: 'running' } : t))

      // Start token growth
      startTokenGrowth()
    }, 3500))

    // 4500ms - Explore 1 complete
    timeouts.push(setTimeout(() => {
      setAgents(prev => prev.map(a => a.id === 'a1' ? { ...a, status: 'complete' } : a))
    }, 4500))

    // 5000ms - Explore 2 complete
    timeouts.push(setTimeout(() => {
      setAgents(prev => prev.map(a => a.id === 'a2' ? { ...a, status: 'complete' } : a))
    }, 5000))

    // 5500ms - Librarian complete, task t1 complete
    timeouts.push(setTimeout(() => {
      setAgents(prev => prev.map(a => a.id === 'a3' ? { ...a, status: 'complete' } : a))
      setTasks(prev => prev.map(t => t.id === 't1' ? { ...t, status: 'complete' } : t))
    }, 5500))

    // ========== PHASE 2: IMPLEMENTATION ==========

    // 6000ms - Clear agents, show phase 2 header
    timeouts.push(setTimeout(() => {
      // Remove old agent lines
      removeLinesByPrefix('a')
      removeLinesByPrefix('agent-header')

      // Add t1 to completed task IDs (for strikethrough)
      setCompletedTaskIds(['t1'])

      // Add phase 2 header
      addLine({ id: 'task-header-2', type: 'task-header', content: PHASES[1].name })
    }, 6000))

    // 6200ms - Phase 2 task list (4 tasks, t1 struck through)
    timeouts.push(setTimeout(() => {
      PHASES[1].tasks.forEach(task => {
        addLine({ id: task.id, type: 'task-item', content: task.label, indent: 1 })
      })
    }, 6200))

    // 6500ms - Phase 2 agent header
    timeouts.push(setTimeout(() => {
      addLine({ id: 'agent-header', type: 'agent-header', content: `${PHASES[1].agents.length} agents running` })
    }, 6500))

    // 6700ms - Phase 2 agents appear, tasks start running
    timeouts.push(setTimeout(() => {
      // Initialize phase 2 agents with random starting tokens
      const phase2Agents = PHASES[1].agents.map(a => ({
        ...a,
        tokens: Math.floor(Math.random() * 3000) + 5000
      }))
      setAgents(phase2Agents)

      // Add agent rows
      phase2Agents.forEach(agent => {
        addLine({ id: agent.id, type: 'agent-row', content: '' })
      })

      // Tasks t2-t5 start running
      setTasks(prev => prev.map(t =>
        ['t2', 't3', 't4', 't5'].includes(t.id) ? { ...t, status: 'running' } : t
      ))
    }, 6700))

    // 8000ms - Task 1 complete (auth middleware), t2 complete
    timeouts.push(setTimeout(() => {
      setAgents(prev => prev.map(a => a.id === 'a4' ? { ...a, status: 'complete' } : a))
      setTasks(prev => prev.map(t => t.id === 't2' ? { ...t, status: 'complete' } : t))
    }, 8000))

    // 8500ms - Task 3 complete (API routes), t4 complete
    timeouts.push(setTimeout(() => {
      setAgents(prev => prev.map(a => a.id === 'a6' ? { ...a, status: 'complete' } : a))
      setTasks(prev => prev.map(t => t.id === 't4' ? { ...t, status: 'complete' } : t))
    }, 8500))

    // 9000ms - Task 2 complete (validation), t3 complete
    timeouts.push(setTimeout(() => {
      setAgents(prev => prev.map(a => a.id === 'a5' ? { ...a, status: 'complete' } : a))
      setTasks(prev => prev.map(t => t.id === 't3' ? { ...t, status: 'complete' } : t))
    }, 9000))

    // 9500ms - Task 4 complete (error handling), t5 complete
    timeouts.push(setTimeout(() => {
      setAgents(prev => prev.map(a => a.id === 'a7' ? { ...a, status: 'complete' } : a))
      setTasks(prev => prev.map(t => t.id === 't5' ? { ...t, status: 'complete' } : t))
    }, 9500))

    // ========== PHASE 3: VALIDATION ==========

    // 10000ms - Clear agents, show phase 3 header
    timeouts.push(setTimeout(() => {
      // Remove old agent lines
      removeLinesByPrefix('a')
      removeLinesByPrefix('agent-header')

      // Add t1-t5 to completed task IDs
      setCompletedTaskIds(['t1', 't2', 't3', 't4', 't5'])

      // Add phase 3 header
      addLine({ id: 'task-header-3', type: 'task-header', content: PHASES[2].name })
    }, 10000))

    // 10200ms - Phase 3 task list (2 tasks)
    timeouts.push(setTimeout(() => {
      PHASES[2].tasks.forEach(task => {
        addLine({ id: task.id, type: 'task-item', content: task.label, indent: 1 })
      })
    }, 10200))

    // 10500ms - Phase 3 agent header
    timeouts.push(setTimeout(() => {
      addLine({ id: 'agent-header', type: 'agent-header', content: `${PHASES[2].agents.length} agents running` })
    }, 10500))

    // 10700ms - Phase 3 agents appear, tasks start running
    timeouts.push(setTimeout(() => {
      // Initialize phase 3 agents with random starting tokens
      const phase3Agents = PHASES[2].agents.map(a => ({
        ...a,
        tokens: Math.floor(Math.random() * 3000) + 5000
      }))
      setAgents(phase3Agents)

      // Add agent rows
      phase3Agents.forEach(agent => {
        addLine({ id: agent.id, type: 'agent-row', content: '' })
      })

      // Tasks t6-t7 start running
      setTasks(prev => prev.map(t =>
        ['t6', 't7'].includes(t.id) ? { ...t, status: 'running' } : t
      ))
    }, 10700))

    // 11500ms - Validator 1 complete (tests)
    timeouts.push(setTimeout(() => {
      setAgents(prev => prev.map(a => a.id === 'a8' ? { ...a, status: 'complete' } : a))
    }, 11500))

    // 12000ms - Validator 2 complete (lints), t6 complete
    timeouts.push(setTimeout(() => {
      setAgents(prev => prev.map(a => a.id === 'a9' ? { ...a, status: 'complete' } : a))
      setTasks(prev => prev.map(t => t.id === 't6' ? { ...t, status: 'complete' } : t))
    }, 12000))

    // 12500ms - Task (git commit) complete, t7 complete
    timeouts.push(setTimeout(() => {
      setAgents(prev => prev.map(a => a.id === 'a10' ? { ...a, status: 'complete' } : a))
      setTasks(prev => prev.map(t => t.id === 't7' ? { ...t, status: 'complete' } : t))
    }, 12500))

    // ========== COMPLETION ==========

    // 13000ms - Success message
    timeouts.push(setTimeout(() => {
      setContentLines(prev => prev.filter(l => l.id !== 'thinking'))
      addLine({ id: 'success', type: 'success', content: '✓ All tasks complete' })
      setPhase('complete')
    }, 13000))

    // 15000ms - Reset and loop (2s after success message)
    timeouts.push(setTimeout(() => {
      setCycle(c => c + 1)
    }, 15000))

    return () => {
      timeouts.forEach(clearTimeout)
      intervals.forEach(clearInterval)
      if (typeInterval) clearInterval(typeInterval)
    }
  }, [cycle, fullPrompt])

  // Spinner animation
  useEffect(() => {
    const interval = setInterval(() => {
      setSpinnerIndex(i => (i + 1) % SPINNER.length)
    }, 100)
    return () => clearInterval(interval)
  }, [])

  // Calculate cost and tokens for parent context (status bar)
  const displayTokens = Math.round(parentTokens / 1000)
  const cost = phase === 'idle' ? '$0.00' : `$${(parentTokens * 0.00001).toFixed(2)}`
  const tokens = phase === 'idle' ? '0K' : `${displayTokens}k`

  // Ref for auto-scrolling
  const contentRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when content changes
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight
    }
  }, [contentLines, agents, tasks])

  return (
    <div className="w-full max-w-2xl mx-auto px-4">
      <div className="rounded-lg border border-zinc-700 bg-zinc-950 overflow-hidden shadow-2xl flex flex-col h-[560px]">
        <TerminalHeader />
        <PulsingLine active={promptStatus === 'submitted' && phase !== 'complete'} />

        {/* Scrollable output area */}
        <div
          ref={contentRef}
          className="flex-1 overflow-hidden px-4 py-3 font-['JetBrains_Mono',_ui-monospace,_monospace] text-sm"
        >
          {contentLines.map(line => (
            <ContentLineRenderer
              key={line.id}
              line={line}
              spinnerIndex={spinnerIndex}
              agents={agents}
              tasks={tasks}
              completedTaskIds={completedTaskIds}
            />
          ))}
        </div>

        {/* Fixed prompt line */}
        <PromptLine content={typedPrompt} status={promptStatus} />

        {/* Fixed status bar */}
        <StatusBar
          phase={phase}
          cost={cost}
          tokens={tokens}
          agentCount={agents.filter(a => a.status === 'running').length}
        />
      </div>
    </div>
  )
}
