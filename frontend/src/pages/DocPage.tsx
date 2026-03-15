import { useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/lib/api'
import { DocViewer } from '@/components/DocViewer'
import { FolderView } from '@/components/FolderView'

interface DocData {
  path: string
  kind: string
  frontmatter?: Record<string, string>
  html?: string
  toc?: { level: number; id: string; text: string }[]
  content?: string
  download_url?: string
  size?: number
}

interface TreeNode {
  name: string
  path: string
  type: 'file' | 'dir'
  kind?: string
  children?: TreeNode[]
}

interface ProjectConfig {
  slug: string; title: string; color: string; repo_full_name: string; owner_email: string
}

function flattenTree(nodes: TreeNode[]): { path: string; name: string }[] {
  const result: { path: string; name: string }[] = []
  for (const node of nodes) {
    if (node.type === 'file') {
      result.push({ path: node.path, name: node.name })
    } else if (node.children) {
      result.push(...flattenTree(node.children))
    }
  }
  return result
}

function findSubtree(nodes: TreeNode[], path: string): TreeNode[] | null {
  if (!path) return nodes
  for (const node of nodes) {
    if (node.type === 'dir' && node.path === path) return node.children || []
    if (node.type === 'dir' && node.children) {
      const found = findSubtree(node.children, path)
      if (found) return found
    }
  }
  return null
}

function isDirectory(nodes: TreeNode[], path: string): boolean {
  if (!path) return true
  for (const node of nodes) {
    if (node.type === 'dir' && node.path === path) return true
    if (node.type === 'dir' && node.children) {
      if (isDirectory(node.children, path)) return true
    }
  }
  return false
}

export default function DocPage() {
  const { project, '*': splat } = useParams()
  const navigate = useNavigate()
  const docPath = splat || ''
  const projectBase = `/${project}`

  const { data: tree = [] } = useQuery({
    queryKey: ['tree', project],
    queryFn: () => apiGet<TreeNode[]>(`${projectBase}/api/tree`),
  })

  const isDirPath = useMemo(() => isDirectory(tree, docPath), [tree, docPath])

  const { data: doc, isLoading: docLoading } = useQuery({
    queryKey: ['doc', project, docPath],
    queryFn: () => apiGet<DocData>(`${projectBase}/api/doc/${encodeURI(docPath)}`),
    enabled: !!docPath && !isDirPath,
    staleTime: 0,
  })

  const { data: settings } = useQuery({
    queryKey: ['settings', project],
    queryFn: () => apiGet<{ project: ProjectConfig; is_owner: boolean }>(`${projectBase}/api/settings`).catch(() => null),
    retry: false,
  })

  const flatFiles = useMemo(() => flattenTree(tree), [tree])
  const currentIdx = flatFiles.findIndex(f => f.path === docPath)
  const prevDoc = currentIdx > 0 ? flatFiles[currentIdx - 1] : null
  const nextDoc = currentIdx >= 0 && currentIdx < flatFiles.length - 1 ? flatFiles[currentIdx + 1] : null

  const config = settings?.project
  const editBaseUrl = config?.repo_full_name
    ? `https://github.com/${config.repo_full_name}/edit/main/`
    : undefined

  const handleNavigate = (path: string) => navigate(`${projectBase}/${path}`)

  // Show folder view for root or directory paths
  if (isDirPath) {
    const folderContents = findSubtree(tree, docPath) || []
    return (
      <div className="h-full flex">
        <FolderView
          path={docPath}
          nodes={folderContents}
          projectTitle={config?.title || project || ''}
          onNavigate={handleNavigate}
        />
      </div>
    )
  }

  return (
    <div className="h-full flex">
      <DocViewer
        doc={docLoading ? undefined : (doc || null)}
        editBaseUrl={editBaseUrl}
        prevDoc={prevDoc}
        nextDoc={nextDoc}
        onNavigate={handleNavigate}
      />
    </div>
  )
}
