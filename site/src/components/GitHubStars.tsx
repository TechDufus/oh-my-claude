import { useState, useEffect } from 'react'
import { Star } from 'lucide-react'

export default function GitHubStars() {
  const [stars, setStars] = useState<number | null>(null)

  useEffect(() => {
    fetch('https://api.github.com/repos/TechDufus/oh-my-claude')
      .then(res => res.json())
      .then(data => setStars(data.stargazers_count))
      .catch(() => setStars(null))
  }, [])

  return (
    <a
      href="https://github.com/techdufus/oh-my-claude"
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 backdrop-blur-md border border-white/10 text-foreground hover:bg-white/10 hover:border-white/20 hover:shadow-lg hover:shadow-cyan/10 transition-all duration-300"
    >
      <Star className="h-4 w-4 text-yellow-400 fill-yellow-400" />
      {stars !== null && <span className="font-medium">{stars.toLocaleString()}</span>}
      <span className="text-muted-foreground">GitHub</span>
    </a>
  )
}
