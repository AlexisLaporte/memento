import { useState } from 'react'

interface TreeNode {
  name: string
  path: string
  type: 'file' | 'dir'
  kind?: string
  children?: TreeNode[]
}

interface FileTreeProps {
  nodes: TreeNode[]
  activePath: string | null
  onSelect: (path: string) => void
}

const KIND_ICON: Record<string, string> = {
  image: '🖼',
  pdf: '📕',
  text: '📝',
}

function fileLabel(node: TreeNode): string {
  if (node.kind === 'markdown') return node.name.replace(/\.md$/i, '')
  return node.name
}

function TreeDir({ node, activePath, onSelect }: { node: TreeNode } & Omit<FileTreeProps, 'nodes'>) {
  const [open, setOpen] = useState(() => isAncestor(node, activePath))
  const isActive = node.path === activePath

  return (
    <div>
      <div className={`flex items-center gap-0 rounded text-sm font-medium ${
        isActive ? 'bg-primary/15 text-primary' : 'text-foreground hover:bg-accent'
      }`}>
        <button
          onClick={(e) => { e.stopPropagation(); setOpen(!open) }}
          className="px-1.5 py-0.5 shrink-0"
        >
          <span className={`text-[10px] text-muted-foreground transition-transform inline-block ${open ? 'rotate-90' : ''}`}>
            {'\u25B6'}
          </span>
        </button>
        <button
          onClick={() => { onSelect(node.path); if (!open) setOpen(true) }}
          className="flex-1 text-left py-0.5 pr-1.5 truncate"
        >
          {node.name}
        </button>
      </div>
      {open && (
        <div className="ml-3 border-l pl-1">
          {node.children?.map(child => (
            <TreeItem key={child.path} node={child} activePath={activePath} onSelect={onSelect} />
          ))}
        </div>
      )}
    </div>
  )
}

function TreeItem({ node, activePath, onSelect }: { node: TreeNode } & Omit<FileTreeProps, 'nodes'>) {
  if (node.type === 'dir') {
    return <TreeDir node={node} activePath={activePath} onSelect={onSelect} />
  }
  const isActive = node.path === activePath
  const icon = node.kind && node.kind !== 'markdown' ? KIND_ICON[node.kind] : null

  return (
    <button
      onClick={() => onSelect(node.path)}
      className={`flex items-center gap-1 w-full text-left px-1.5 py-0.5 pl-5 rounded text-sm truncate ${
        isActive ? 'bg-primary/15 text-primary font-medium' : 'text-muted-foreground hover:bg-accent hover:text-foreground'
      }`}
    >
      {icon && <span className="text-xs shrink-0">{icon}</span>}
      <span className="truncate">{fileLabel(node)}</span>
    </button>
  )
}

function isAncestor(node: TreeNode, path: string | null): boolean {
  if (!path) return false
  return path.startsWith(node.path + '/')
}

export function FileTree({ nodes, activePath, onSelect }: FileTreeProps) {
  return (
    <div className="text-sm space-y-0.5">
      {nodes.map(node => (
        <TreeItem key={node.path} node={node} activePath={activePath} onSelect={onSelect} />
      ))}
    </div>
  )
}
