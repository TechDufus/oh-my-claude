import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Check, Copy } from 'lucide-react'

const COMMANDS = [
  'curl -LsSf https://astral.sh/uv/install.sh | sh',
  'claude plugin marketplace add techdufus/oh-my-claude',
  'claude plugin install oh-my-claude@oh-my-claude',
]

export default function InstallBlock() {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(COMMANDS.join('\n'))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="flex w-full max-w-2xl flex-col items-stretch gap-4">
      <div className="w-full overflow-x-auto rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-4 font-mono text-sm shadow-[0_18px_50px_rgba(0,0,0,0.25)] backdrop-blur-sm">
        {COMMANDS.map((cmd, i) => (
          <div key={i} className="flex items-center gap-2 whitespace-nowrap">
            <span className="text-muted-foreground">$</span>
            <code className="text-cyan">{cmd}</code>
          </div>
        ))}
      </div>
      <Button
        variant="coral"
        size="lg"
        onClick={handleCopy}
        className="w-full gap-2 font-medium sm:w-fit"
      >
        {copied ? (
          <>
            <Check className="h-4 w-4" />
            Copied!
          </>
        ) : (
          <>
            <Copy className="h-4 w-4" />
            Copy Commands
          </>
        )}
      </Button>
    </div>
  )
}
