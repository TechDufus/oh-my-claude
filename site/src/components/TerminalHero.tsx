import { useEffect, useRef, useState } from 'react'

const SPINNER = ['✻', '✺', '✹', '✷']
const DEMO_CLAUDE_MODEL = 'claude-opus-4-6'
const DEMO_CLAUDE_CODE_VERSION = '2.1.107'
const DEMO_DIR = 'oh-my-claude'
const DEMO_BRANCH = 'main'

type ContentLineType =
  | 'submitted-prompt'
  | 'thinking'
  | 'task-header'
  | 'task-item'
  | 'agent-header'
  | 'agent-row'
  | 'success'

type PhaseName = 'idle' | 'research' | 'implementation' | 'validation' | 'complete'

interface ContentLine {
  id: string
  type: ContentLineType
  content: string
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
  status: 'running' | 'complete'
  statusText: string
}

interface PhaseConfig {
  id: PhaseName
  name: string
  tasks: Task[]
  agents: Agent[]
}

const PHASES: PhaseConfig[] = [
  {
    id: 'research',
    name: 'Research',
    tasks: [
      { id: 't1', label: 'Survey auth surface', status: 'pending' }
    ],
    agents: [
      { id: 'a1', name: 'Explore', task: 'Find files', status: 'running', statusText: 'Searching…' },
      { id: 'a2', name: 'Explore', task: 'Map deps', status: 'running', statusText: 'Mapping…' },
      { id: 'a3', name: 'librarian', task: 'Read patterns', status: 'running', statusText: 'Reading…' },
    ]
  },
  {
    id: 'implementation',
    name: 'Implementation',
    tasks: [
      { id: 't2', label: 'Add middleware', status: 'pending' },
      { id: 't3', label: 'Add validation', status: 'pending' },
      { id: 't4', label: 'Patch routes', status: 'pending' },
      { id: 't5', label: 'Handle failures', status: 'pending' },
    ],
    agents: [
      { id: 'a4', name: 'Task', task: 'Middleware', status: 'running', statusText: 'Writing…' },
      { id: 'a5', name: 'Task', task: 'Validation', status: 'running', statusText: 'Writing…' },
      { id: 'a6', name: 'Task', task: 'Routes', status: 'running', statusText: 'Writing…' },
      { id: 'a7', name: 'Task', task: 'Errors', status: 'running', statusText: 'Writing…' },
    ]
  },
  {
    id: 'validation',
    name: 'Validation',
    tasks: [
      { id: 't6', label: 'Run tests', status: 'pending' },
      { id: 't7', label: 'Run lints', status: 'pending' },
    ],
    agents: [
      { id: 'a8', name: 'validator', task: 'Tests', status: 'running', statusText: 'Testing…' },
      { id: 'a9', name: 'validator', task: 'Lints', status: 'running', statusText: 'Linting…' },
      { id: 'a10', name: 'Task', task: 'Commit check', status: 'running', statusText: 'Checking…' },
    ]
  }
]

const ALL_TASKS: Task[] = PHASES.flatMap((phase) => phase.tasks)

function getPhaseName(
  phase: 'idle' | 'running' | 'complete',
  tasks: Task[]
): PhaseName {
  if (phase === 'idle') return 'idle'
  if (phase === 'complete') return 'complete'

  if (tasks.some((task) => ['t6', 't7'].includes(task.id) && task.status === 'running')) {
    return 'validation'
  }

  if (tasks.some((task) => ['t2', 't3', 't4', 't5'].includes(task.id) && task.status === 'running')) {
    return 'implementation'
  }

  return 'research'
}

function formatElapsed(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

function ContextMeter({ percent }: { percent: number }) {
  const totalBars = 10
  const filledBars = Math.min(totalBars, Math.max(0, Math.round(percent / 10)))
  const emptyBars = totalBars - filledBars

  return (
    <span className="inline-flex items-center gap-2">
      <span>{percent}%</span>
      <span className="tracking-[0.08em] text-zinc-400">
        {'█'.repeat(filledBars)}
        <span className="text-zinc-800">{'░'.repeat(emptyBars)}</span>
      </span>
    </span>
  )
}

function ClaudePixelIcon() {
  return (
    <svg viewBox="0 0 32 32" className="h-12 w-12 sm:h-14 sm:w-14">
      <g transform="translate(3, 2)">
        <rect x="8" y="0" width="10" height="2" fill="#DA7756"/>
        <rect x="6" y="2" width="14" height="2" fill="#DA7756"/>
        <rect x="4" y="4" width="18" height="2" fill="#DA7756"/>
        <rect x="2" y="6" width="22" height="2" fill="#DA7756"/>
        <rect x="2" y="8" width="22" height="6" fill="#DA7756"/>
        <rect x="3" y="8" width="8" height="5" fill="#111"/>
        <rect x="4" y="9" width="6" height="3" fill="#1a3a4a"/>
        <rect x="11" y="9" width="4" height="2" fill="#111"/>
        <rect x="15" y="8" width="8" height="5" fill="#111"/>
        <rect x="16" y="9" width="6" height="3" fill="#1a3a4a"/>
        <rect x="5" y="9" width="2" height="1" fill="#3a6a7a"/>
        <rect x="17" y="9" width="2" height="1" fill="#3a6a7a"/>
        <rect x="0" y="9" width="3" height="2" fill="#111"/>
        <rect x="23" y="9" width="3" height="2" fill="#111"/>
        <rect x="2" y="14" width="22" height="2" fill="#DA7756"/>
        <rect x="4" y="16" width="18" height="2" fill="#DA7756"/>
        <rect x="6" y="18" width="14" height="2" fill="#DA7756"/>
        <rect x="6" y="20" width="3" height="5" fill="#DA7756"/>
        <rect x="11" y="20" width="4" height="6" fill="#DA7756"/>
        <rect x="17" y="20" width="3" height="5" fill="#DA7756"/>
      </g>
    </svg>
  )
}

function WelcomeScreen() {
  return (
    <div className="mb-3 rounded border border-orange-400/80 px-3 py-3 sm:px-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex min-w-0 flex-1 items-center gap-4">
          <div className="shrink-0 p-1">
            <ClaudePixelIcon />
          </div>
          <div className="min-w-0 text-zinc-400 text-xs">
            <div className="text-zinc-300">Claude Code v{DEMO_CLAUDE_CODE_VERSION}</div>
            <div>{DEMO_DIR}</div>
          </div>
        </div>
        <div className="hidden w-px self-stretch bg-orange-400/80 md:block"></div>
        <div className="min-w-0 flex-1 text-xs text-zinc-400">
          <div className="text-orange-400 font-medium">Tips for getting started</div>
          <div>Use plan mode for complex tasks</div>
          <div>Use ultrawork for maximum effort</div>
          <div className="mt-2 text-orange-400 font-medium">Recent activity</div>
          <div>No recent activity</div>
        </div>
      </div>
    </div>
  )
}

function TerminalHeader() {
  return (
    <div className="flex items-center border-b border-white/10 bg-zinc-950/95 px-4 py-3">
      <div className="flex items-center gap-2">
        <div className="h-3 w-3 rounded-full bg-red-500/90"></div>
        <div className="h-3 w-3 rounded-full bg-amber-400/90"></div>
        <div className="h-3 w-3 rounded-full bg-emerald-400/90"></div>
      </div>
      <div className="flex-1 text-center font-['JetBrains_Mono',_ui-monospace,_monospace] text-sm text-zinc-300">
        claude
      </div>
      <div className="hidden w-20 text-right font-['JetBrains_Mono',_ui-monospace,_monospace] text-xs text-zinc-600 sm:block">
        {DEMO_DIR}
      </div>
      <div className="w-0 sm:hidden"></div>
    </div>
  )
}

function PulsingLine({ active }: { active: boolean }) {
  return (
    <div className="relative h-px overflow-hidden bg-white/5">
      {active && (
        <div
          className="absolute h-full w-1/3 bg-gradient-to-r from-transparent via-cyan to-transparent"
          style={{ animation: 'pulse-slide 2.4s ease-in-out infinite' }}
        ></div>
      )}
    </div>
  )
}

function PromptLine({
  content,
  status,
}: {
  content: string
  status: 'idle' | 'typing' | 'submitted'
}) {
  const displayText =
    status === 'idle'
      ? ''
      : status === 'typing'
        ? content
        : ''

  return (
    <div className="border-t border-white/10 bg-black/20 px-4 py-3 font-['JetBrains_Mono',_ui-monospace,_monospace] text-sm text-zinc-300">
      <div className="flex items-center gap-2 overflow-hidden">
        <span className="text-zinc-500">{'>'}</span>
        <span className="truncate">{displayText}</span>
        {status === 'typing' && <span className="animate-pulse text-cyan">|</span>}
      </div>
    </div>
  )
}

function StatusLine({
  phase,
  contextPercent,
  elapsedSeconds,
  cost,
}: {
  phase: PhaseName
  contextPercent: number
  elapsedSeconds: number
  cost: string
}) {
  const phaseLabel =
    phase === 'idle'
      ? 'ready'
      : phase === 'complete'
        ? 'complete'
        : phase

  return (
    <div className="border-t border-white/10 bg-zinc-950/95 px-4 py-2 font-['JetBrains_Mono',_ui-monospace,_monospace] text-[10px] uppercase tracking-[0.12em] text-zinc-300 sm:text-[11px] sm:tracking-[0.16em]">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-zinc-100">[{DEMO_CLAUDE_MODEL}]</span>
        <span className="text-zinc-700">|</span>
        <span>{DEMO_DIR}</span>
        <span className="text-zinc-700">|</span>
        <span>{DEMO_BRANCH}</span>
      </div>
      <div className="mt-1 flex flex-wrap items-center gap-2 text-zinc-400">
        <span className="inline-flex items-center gap-2">
          <span>context</span>
          <ContextMeter percent={contextPercent} />
        </span>
        <span className="text-zinc-700">|</span>
        <span>{cost}</span>
        <span className="text-zinc-700">|</span>
        <span>{formatElapsed(elapsedSeconds)}</span>
        <span className="text-zinc-700">|</span>
        <span className={phase === 'complete' ? 'text-emerald-300' : 'text-zinc-200'}>
          {phaseLabel}
        </span>
      </div>
    </div>
  )
}

function ContentLineRenderer({
  line,
  spinnerIndex,
  agents,
  tasks,
  completedTaskIds,
}: {
  line: ContentLine
  spinnerIndex: number
  agents: Agent[]
  tasks: Task[]
  completedTaskIds: string[]
}) {
  const indentStyle = line.indent ? { paddingLeft: `${line.indent * 0.75}rem` } : undefined

  switch (line.type) {
    case 'submitted-prompt':
      return (
        <div className="mb-2 text-cyan" style={indentStyle}>
          {'>'} {line.content}
        </div>
      )

    case 'thinking':
      return (
        <div className="text-zinc-400" style={indentStyle}>
          <span className="text-yellow-300">{SPINNER[spinnerIndex]}</span> {line.content}
        </div>
      )

    case 'task-header':
      return (
        <div className="mt-3 text-zinc-200" style={indentStyle}>
          {line.content}
        </div>
      )

    case 'task-item': {
      const task = tasks.find((item) => item.id === line.id)
      const isComplete = task?.status === 'complete'
      const isRunning = task?.status === 'running'
      const isFromPreviousPhase = completedTaskIds.includes(line.id)

      return (
        <div className="text-zinc-400" style={indentStyle}>
          <span className={isComplete || isFromPreviousPhase ? 'text-emerald-300' : isRunning ? 'text-yellow-300' : 'text-zinc-600'}>
            {isComplete || isFromPreviousPhase ? '[✓]' : isRunning ? `[${SPINNER[spinnerIndex]}]` : '[ ]'}
          </span>{' '}
          <span className={
            isFromPreviousPhase
              ? 'text-zinc-600 line-through'
              : isComplete || isRunning
                ? 'text-zinc-300'
                : ''
          }>
            {line.content}
          </span>
        </div>
      )
    }

    case 'agent-header': {
      const runningAgents = agents.filter((agent) => agent.status === 'running').length
      const allComplete = agents.length > 0 && agents.every((agent) => agent.status === 'complete')
      const label = allComplete
        ? `${agents.length} agents complete`
        : runningAgents > 0
          ? `${runningAgents} agents active`
          : line.content

      return (
        <div className="mt-3 text-zinc-300" style={indentStyle}>
          * {label}
        </div>
      )
    }

    case 'agent-row': {
      const agent = agents.find((item) => item.id === line.id)
      if (!agent) return null

      return (
        <div className="text-zinc-400" style={indentStyle}>
          <span className="text-zinc-600">⎿</span>{' '}
          <span className="text-cyan">{agent.name}</span>
          <span className="text-zinc-500"> · {agent.task}</span>
          <span className="text-zinc-600"> · </span>
          {agent.status === 'running' ? (
            <span className="text-yellow-300">{agent.statusText}</span>
          ) : (
            <span className="text-emerald-300">Done</span>
          )}
        </div>
      )
    }

    case 'success':
      return (
        <div className="mt-3 text-emerald-300" style={indentStyle}>
          {line.content}
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
  const [tasks, setTasks] = useState<Task[]>(ALL_TASKS.map((task) => ({ ...task, status: 'pending' })))
  const [typedPrompt, setTypedPrompt] = useState('')
  const [cycle, setCycle] = useState(0)
  const [parentTokens, setParentTokens] = useState(0)
  const [completedTaskIds, setCompletedTaskIds] = useState<string[]>([])
  const [promptStatus, setPromptStatus] = useState<'idle' | 'typing' | 'submitted'>('idle')
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const contentRef = useRef<HTMLDivElement>(null)

  const fullPrompt = 'Implement auth system ultrawork'

  useEffect(() => {
    const timeouts: ReturnType<typeof setTimeout>[] = []
    const intervals: ReturnType<typeof setInterval>[] = []
    let typeInterval: ReturnType<typeof setInterval> | null = null

    setContentLines([])
    setAgents([])
    setTasks(ALL_TASKS.map((task) => ({ ...task, status: 'pending' })))
    setTypedPrompt('')
    setPhase('idle')
    setParentTokens(0)
    setCompletedTaskIds([])
    setPromptStatus('idle')
    setElapsedSeconds(0)

    const addLine = (line: ContentLine) => {
      setContentLines((previous) => [...previous, line])
    }

    const removeLinesByPrefix = (prefix: string) => {
      setContentLines((previous) => previous.filter((line) => !line.id.startsWith(prefix)))
    }

    const startRuntime = () => {
      const tokenInterval = setInterval(() => {
        setParentTokens((previous) => previous + Math.floor(Math.random() * 120) + 80)
      }, 500)
      intervals.push(tokenInterval)

      const elapsedInterval = setInterval(() => {
        setElapsedSeconds((previous) => previous + 1)
      }, 1000)
      intervals.push(elapsedInterval)
    }

    timeouts.push(setTimeout(() => {
      setPhase('running')
      setPromptStatus('typing')
      startRuntime()

      let charIndex = 0
      typeInterval = setInterval(() => {
        if (charIndex < fullPrompt.length) {
          charIndex++
          setTypedPrompt(fullPrompt.slice(0, charIndex))
        } else {
          if (typeInterval) clearInterval(typeInterval)
          setContentLines((previous) => [
            ...previous,
            { id: 'submitted-prompt', type: 'submitted-prompt', content: fullPrompt }
          ])
          setTypedPrompt('')
          setPromptStatus('submitted')
        }
      }, 40)
    }, 700))

    timeouts.push(setTimeout(() => {
      addLine({ id: 'thinking', type: 'thinking', content: 'Thinking…' })
    }, 2400))

    timeouts.push(setTimeout(() => {
      addLine({ id: 'task-header-1', type: 'task-header', content: PHASES[0].name })
    }, 2900))

    timeouts.push(setTimeout(() => {
      PHASES[0].tasks.forEach((task) => {
        addLine({ id: task.id, type: 'task-item', content: task.label, indent: 1 })
      })
    }, 3150))

    timeouts.push(setTimeout(() => {
      addLine({ id: 'agent-header', type: 'agent-header', content: `${PHASES[0].agents.length} agents active`, indent: 1 })
    }, 3400))

    timeouts.push(setTimeout(() => {
      const phaseAgents = PHASES[0].agents
      setAgents(phaseAgents)
      phaseAgents.forEach((agent) => {
        addLine({ id: agent.id, type: 'agent-row', content: '', indent: 2 })
      })
      setTasks((previous) => previous.map((task) =>
        task.id === 't1' ? { ...task, status: 'running' } : task
      ))
    }, 3600))

    timeouts.push(setTimeout(() => {
      setAgents((previous) => previous.map((agent) =>
        agent.id === 'a1' ? { ...agent, status: 'complete' } : agent
      ))
    }, 4600))

    timeouts.push(setTimeout(() => {
      setAgents((previous) => previous.map((agent) =>
        agent.id === 'a2' ? { ...agent, status: 'complete' } : agent
      ))
    }, 5100))

    timeouts.push(setTimeout(() => {
      setAgents((previous) => previous.map((agent) =>
        agent.id === 'a3' ? { ...agent, status: 'complete' } : agent
      ))
      setTasks((previous) => previous.map((task) =>
        task.id === 't1' ? { ...task, status: 'complete' } : task
      ))
    }, 5600))

    timeouts.push(setTimeout(() => {
      removeLinesByPrefix('a')
      removeLinesByPrefix('agent-header')
      setCompletedTaskIds(['t1'])
      addLine({ id: 'task-header-2', type: 'task-header', content: PHASES[1].name })
    }, 6200))

    timeouts.push(setTimeout(() => {
      PHASES[1].tasks.forEach((task) => {
        addLine({ id: task.id, type: 'task-item', content: task.label, indent: 1 })
      })
    }, 6450))

    timeouts.push(setTimeout(() => {
      addLine({ id: 'agent-header', type: 'agent-header', content: `${PHASES[1].agents.length} agents active`, indent: 1 })
    }, 6700))

    timeouts.push(setTimeout(() => {
      const phaseAgents = PHASES[1].agents
      setAgents(phaseAgents)
      phaseAgents.forEach((agent) => {
        addLine({ id: agent.id, type: 'agent-row', content: '', indent: 2 })
      })
      setTasks((previous) => previous.map((task) =>
        ['t2', 't3', 't4', 't5'].includes(task.id) ? { ...task, status: 'running' } : task
      ))
    }, 6900))

    timeouts.push(setTimeout(() => {
      setAgents((previous) => previous.map((agent) =>
        agent.id === 'a4' ? { ...agent, status: 'complete' } : agent
      ))
      setTasks((previous) => previous.map((task) =>
        task.id === 't2' ? { ...task, status: 'complete' } : task
      ))
    }, 7900))

    timeouts.push(setTimeout(() => {
      setAgents((previous) => previous.map((agent) =>
        agent.id === 'a6' ? { ...agent, status: 'complete' } : agent
      ))
      setTasks((previous) => previous.map((task) =>
        task.id === 't4' ? { ...task, status: 'complete' } : task
      ))
    }, 8450))

    timeouts.push(setTimeout(() => {
      setAgents((previous) => previous.map((agent) =>
        agent.id === 'a5' ? { ...agent, status: 'complete' } : agent
      ))
      setTasks((previous) => previous.map((task) =>
        task.id === 't3' ? { ...task, status: 'complete' } : task
      ))
    }, 9000))

    timeouts.push(setTimeout(() => {
      setAgents((previous) => previous.map((agent) =>
        agent.id === 'a7' ? { ...agent, status: 'complete' } : agent
      ))
      setTasks((previous) => previous.map((task) =>
        task.id === 't5' ? { ...task, status: 'complete' } : task
      ))
    }, 9550))

    timeouts.push(setTimeout(() => {
      removeLinesByPrefix('a')
      removeLinesByPrefix('agent-header')
      setCompletedTaskIds(['t1', 't2', 't3', 't4', 't5'])
      addLine({ id: 'task-header-3', type: 'task-header', content: PHASES[2].name })
    }, 10100))

    timeouts.push(setTimeout(() => {
      PHASES[2].tasks.forEach((task) => {
        addLine({ id: task.id, type: 'task-item', content: task.label, indent: 1 })
      })
    }, 10350))

    timeouts.push(setTimeout(() => {
      addLine({ id: 'agent-header', type: 'agent-header', content: `${PHASES[2].agents.length} agents active`, indent: 1 })
    }, 10600))

    timeouts.push(setTimeout(() => {
      const phaseAgents = PHASES[2].agents
      setAgents(phaseAgents)
      phaseAgents.forEach((agent) => {
        addLine({ id: agent.id, type: 'agent-row', content: '', indent: 2 })
      })
      setTasks((previous) => previous.map((task) =>
        ['t6', 't7'].includes(task.id) ? { ...task, status: 'running' } : task
      ))
    }, 10850))

    timeouts.push(setTimeout(() => {
      setAgents((previous) => previous.map((agent) =>
        agent.id === 'a8' ? { ...agent, status: 'complete' } : agent
      ))
      setTasks((previous) => previous.map((task) =>
        task.id === 't6' ? { ...task, status: 'complete' } : task
      ))
    }, 11800))

    timeouts.push(setTimeout(() => {
      setAgents((previous) => previous.map((agent) =>
        agent.id === 'a9' ? { ...agent, status: 'complete' } : agent
      ))
      setTasks((previous) => previous.map((task) =>
        task.id === 't7' ? { ...task, status: 'complete' } : task
      ))
    }, 12350))

    timeouts.push(setTimeout(() => {
      setAgents((previous) => previous.map((agent) =>
        agent.id === 'a10' ? { ...agent, status: 'complete' } : agent
      ))
    }, 12700))

    timeouts.push(setTimeout(() => {
      setContentLines((previous) => previous.filter((line) => line.id !== 'thinking'))
      addLine({ id: 'success', type: 'success', content: '✓ All tasks complete' })
      setPhase('complete')
    }, 13200))

    timeouts.push(setTimeout(() => {
      setCycle((value) => value + 1)
    }, 15400))

    return () => {
      timeouts.forEach(clearTimeout)
      intervals.forEach(clearInterval)
      if (typeInterval) clearInterval(typeInterval)
    }
  }, [cycle, fullPrompt])

  useEffect(() => {
    const interval = setInterval(() => {
      setSpinnerIndex((index) => (index + 1) % SPINNER.length)
    }, 140)

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight
    }
  }, [contentLines, agents, tasks])

  const phaseName = getPhaseName(phase, tasks)
  const contextPercent = phase === 'idle' ? 0 : Math.min(18, Math.max(1, Math.round(parentTokens / 180)))
  const cost = phase === 'idle' ? '$0.00' : `$${(parentTokens * 0.00001).toFixed(2)}`

  return (
    <div className="relative mx-auto w-full max-w-[46rem] px-0 sm:px-4">
      <div className="pointer-events-none absolute -inset-8 rounded-[2rem] bg-[radial-gradient(circle_at_20%_20%,rgba(34,211,238,0.16),transparent_36%),radial-gradient(circle_at_80%_22%,rgba(251,146,60,0.12),transparent_32%),radial-gradient(circle_at_50%_100%,rgba(255,255,255,0.06),transparent_40%)] blur-3xl"></div>

      <div
        data-terminal-shell
        className="relative overflow-hidden rounded-[1.75rem] border border-cyan/15 bg-zinc-950/95 shadow-[0_0_0_1px_rgba(34,211,238,0.08),0_28px_80px_rgba(8,145,178,0.18)] backdrop-blur-xl"
      >
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:24px_24px] opacity-30"></div>
        <div className="pointer-events-none absolute -left-24 top-24 h-40 w-40 rounded-full bg-cyan/10 blur-3xl"></div>
        <div className="pointer-events-none absolute -right-16 top-8 h-36 w-36 rounded-full bg-orange-400/8 blur-3xl"></div>
        <div className="pointer-events-none absolute inset-x-0 top-0 h-36 animate-terminal-scan bg-gradient-to-b from-white/8 via-cyan/5 to-transparent"></div>

        <div className="relative flex h-[600px] flex-col sm:h-[640px]">
          <TerminalHeader />
          <PulsingLine active={promptStatus === 'submitted' && phase !== 'complete'} />

          <div
            ref={contentRef}
            className="pointer-events-none flex-1 overflow-hidden px-4 py-4 font-['JetBrains_Mono',_ui-monospace,_monospace] text-[13px] leading-6 select-none sm:text-sm sm:leading-6"
          >
            <WelcomeScreen />
            {contentLines.map((line) => (
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

          <PromptLine content={typedPrompt} status={promptStatus} />
          <StatusLine
            phase={phaseName}
            contextPercent={contextPercent}
            elapsedSeconds={elapsedSeconds}
            cost={cost}
          />
        </div>
      </div>
    </div>
  )
}
