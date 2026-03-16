/**
 * CSS-only mockup of the Mento interface (file tree + doc viewer).
 * Used as a visual in the hero section.
 */
export function AppMockup() {
  const files = [
    { name: 'docs/', type: 'dir', indent: 0 },
    { name: 'getting-started.md', type: 'file', indent: 1 },
    { name: 'architecture.md', type: 'file', indent: 1, active: true },
    { name: 'deployment.md', type: 'file', indent: 1 },
    { name: 'api/', type: 'dir', indent: 1 },
    { name: 'endpoints.md', type: 'file', indent: 2 },
    { name: 'README.md', type: 'file', indent: 0 },
  ]

  return (
    <div className="rounded-2xl border border-border bg-card shadow-lg overflow-hidden">
      {/* Title bar */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border bg-muted/50">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-400/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-400/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-green-400/60" />
        </div>
        <span className="text-[10px] text-muted-foreground ml-2 font-mono">mento.cc/stock</span>
      </div>

      <div className="flex h-[280px]">
        {/* Sidebar */}
        <div className="w-48 border-r border-border p-3 text-xs space-y-0.5 shrink-0">
          {files.map((f, i) => (
            <div
              key={i}
              className={`flex items-center gap-1.5 py-1 px-2 rounded ${
                f.active ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground'
              }`}
              style={{ paddingLeft: `${8 + f.indent * 12}px` }}
            >
              <span className="text-[10px]">{f.type === 'dir' ? '📁' : '📄'}</span>
              <span>{f.name}</span>
            </div>
          ))}
        </div>

        {/* Doc content */}
        <div className="flex-1 p-5 overflow-hidden">
          <div className="space-y-3">
            {/* Frontmatter bar */}
            <div className="flex items-center gap-2 pb-3 border-b border-border">
              <span className="text-xs font-medium text-foreground">Architecture</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-100 text-green-700">Published</span>
            </div>
            {/* Fake content lines */}
            <div className="space-y-2.5">
              <div className="h-3 bg-foreground/8 rounded w-3/4" />
              <div className="h-3 bg-foreground/5 rounded w-full" />
              <div className="h-3 bg-foreground/5 rounded w-5/6" />
              <div className="h-3 bg-foreground/5 rounded w-2/3" />
              <div className="h-8 bg-primary/5 rounded border border-primary/10 w-full mt-3" />
              <div className="h-3 bg-foreground/5 rounded w-full" />
              <div className="h-3 bg-foreground/5 rounded w-4/5" />
              <div className="h-3 bg-foreground/5 rounded w-3/4" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
