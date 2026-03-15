import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/lib/api'
import { DocViewer } from '@/components/DocViewer'

interface DocData { path: string; frontmatter: Record<string, string>; html: string }
interface ProjectConfig { slug: string; title: string; color: string; repo_full_name: string; owner_email: string }

export default function DocPage() {
  const { project, '*': splat } = useParams()
  const docPath = splat || ''
  const projectBase = `/${project}`

  const { data: doc } = useQuery({
    queryKey: ['doc', project, docPath],
    queryFn: () => apiGet<DocData>(`${projectBase}/api/doc/${encodeURI(docPath)}`),
    enabled: !!docPath,
  })

  const { data: settings } = useQuery({
    queryKey: ['settings', project],
    queryFn: () => apiGet<{ project: ProjectConfig; is_owner: boolean }>(`${projectBase}/api/settings`).catch(() => null),
    retry: false,
  })

  const config = settings?.project
  const editBaseUrl = config?.repo_full_name
    ? `https://github.com/${config.repo_full_name}/edit/main/`
    : undefined

  return (
    <div className="h-full">
      <DocViewer doc={docPath ? (doc || null) : null} editBaseUrl={editBaseUrl} />
    </div>
  )
}
