import { useState } from 'react'

interface TreeNode {
  name: string
  path: string
  type: 'file' | 'dir'
  children?: TreeNode[]
}

interface FileTreeProps {
  nodes: TreeNode[]
  activePath: string | null
  onSelect: (path: string) => void
}

function TreeDir({ node, activePath, onSelect }: { node: TreeNode } & Omit<FileTreeProps, 'nodes'>) {
  const [open, setOpen] = useState(() => isAncestor(node, activePath))

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 w-full px-1.5 py-0.5 rounded text-sm font-medium text-foreground hover:bg-accent"
      >
        <span className={`text-[10px] text-muted-foreground transition-transform ${open ? 'rotate-90' : ''}`}>
          {'\u25B6'}
        </span>
        {node.name}
      </button>
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
  return (
    <button
      onClick={() => onSelect(node.path)}
      className={`block w-full text-left px-1.5 py-0.5 pl-5 rounded text-sm truncate ${
        isActive ? 'bg-primary/15 text-primary font-medium' : 'text-muted-foreground hover:bg-accent hover:text-foreground'
      }`}
    >
      {node.name.replace(/\.md$/i, '')}
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
