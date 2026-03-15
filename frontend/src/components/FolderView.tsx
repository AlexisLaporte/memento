interface TreeNode {
  name: string
  path: string
  type: 'file' | 'dir'
  kind?: string
  children?: TreeNode[]
}

const KIND_ICON: Record<string, string> = {
  markdown: '\u{1F4C4}',
  image: '\u{1F5BC}',
  pdf: '\u{1F4D5}',
  text: '\u{1F4DD}',
}

function countFiles(node: TreeNode): number {
  if (node.type === 'file') return 1
  return (node.children || []).reduce((sum, c) => sum + countFiles(c), 0)
}

export function FolderView({
  path,
  nodes,
  projectTitle,
  onNavigate,
}: {
  path: string
  nodes: TreeNode[]
  projectTitle: string
  onNavigate: (path: string) => void
}) {
  const title = path ? path.split('/').pop() : projectTitle

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 md:p-6">
      <div className="mb-6 pb-3 border-b">
        <h1 className="text-xl font-bold">{title}</h1>
        {path && (
          <span className="text-xs text-muted-foreground font-mono">{path}/</span>
        )}
      </div>

      <div className="grid gap-2">
        {nodes.map(node => (
          <button
            key={node.path}
            onClick={() => onNavigate(node.path)}
            className="flex items-center gap-3 w-full text-left px-4 py-3 rounded-lg border hover:bg-accent/30 hover:border-primary/20 transition-colors group"
          >
            <span className="text-lg shrink-0">
              {node.type === 'dir' ? '\u{1F4C1}' : (KIND_ICON[node.kind || ''] || '\u{1F4C4}')}
            </span>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                {node.type === 'file' && node.kind === 'markdown'
                  ? node.name.replace(/\.md$/i, '')
                  : node.name}
              </div>
              {node.type === 'dir' && (
                <div className="text-xs text-muted-foreground">
                  {countFiles(node)} {countFiles(node) === 1 ? 'file' : 'files'}
                </div>
              )}
            </div>
            <span className="text-muted-foreground/50 text-xs shrink-0 group-hover:text-primary transition-colors">
              {node.type === 'dir' ? '\u2192' : ''}
            </span>
          </button>
        ))}
      </div>

      {nodes.length === 0 && (
        <div className="flex items-center justify-center py-12 text-muted-foreground text-sm">
          This folder is empty
        </div>
      )}
    </div>
  )
}
