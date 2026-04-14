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
    <div className="flex flex-col items-center justify-center gap-4">
      <div className="w-full max-w-2xl overflow-x-auto px-4 py-3 bg-secondary/50 rounded-lg border border-border/50 font-mono text-sm">
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
        className="gap-2 font-medium"
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
