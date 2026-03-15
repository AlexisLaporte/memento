import { useEffect, useState } from 'react'

interface TocHeading {
  level: number
  id: string
  text: string
}

function useActiveHeading(headings: TocHeading[]): string {
  const [activeId, setActiveId] = useState('')

  useEffect(() => {
    if (headings.length < 2) { setActiveId(''); return }
    const observer = new IntersectionObserver(
      entries => {
        for (const entry of entries) {
          if (entry.isIntersecting) { setActiveId(entry.target.id); break }
        }
      },
      { rootMargin: '-80px 0px -70% 0px', threshold: 0 }
    )
    headings.forEach(h => {
      const el = document.getElementById(h.id)
      if (el) observer.observe(el)
    })
    return () => observer.disconnect()
  }, [headings])

  return activeId
}

export function TocSidebar({ headings }: { headings: TocHeading[] }) {
  const activeId = useActiveHeading(headings)

  if (headings.length < 2) return null

  return (
    <nav className="hidden lg:block w-[200px] shrink-0 sticky top-0 h-screen overflow-y-auto border-r border-border bg-background/50 px-3 py-4">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 px-2">
        On this page
      </p>
      <ul className="space-y-0.5">
        {headings.map(h => (
          <li key={h.id} style={{ paddingLeft: `${(h.level - 2) * 0.75}rem` }}>
            <a
              href={`#${h.id}`}
              className={`block py-1 pl-2.5 border-l-2 text-sm transition-colors truncate ${
                activeId === h.id
                  ? 'border-primary text-foreground font-medium'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {h.text}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
