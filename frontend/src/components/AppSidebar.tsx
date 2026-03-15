import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/lib/api'
import { useAuth } from '@/hooks/use-auth'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { FileTree } from '@/components/FileTree'

interface Project {
  slug: string
  title: string
  color: string
  repo_full_name: string
  is_owner: boolean
}

interface TreeNode {
  name: string
  path: string
  type: 'file' | 'dir'
  children?: TreeNode[]
}

interface ProjectConfig {
  slug: string
  title: string
  color: string
  repo_full_name: string
  owner_email: string
}

const RESERVED = ['new', 'admin', 'auth']

function useAppContext() {
  const location = useLocation()
  const segments = location.pathname.split('/').filter(Boolean)
  const first = segments[0] || ''

  if (!first || RESERVED.includes(first)) {
    return { context: 'dashboard' as const, project: null, subPath: '' }
  }

  // Check if it's a special sub-route
  const sub = segments[1] || ''
  const isSpecial = ['settings', 'issues'].includes(sub)
  const docPath = isSpecial ? '' : segments.slice(1).join('/')

  return { context: 'project' as const, project: first, subPath: docPath }
}

function getInitials(name: string, email: string) {
  if (name) return name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
  return email[0]?.toUpperCase() || '?'
}

function DashboardSidebar() {
  const { user } = useAuth()

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiGet<Project[]>('/api/projects'),
  })

  return (
    <>
      <nav className="flex-1 overflow-y-auto px-3 py-2">
        <div className="flex items-center justify-between mb-1 px-1">
          <span className="text-xs font-medium text-sidebar-foreground/50 uppercase tracking-wider">Projects</span>
          <Link
            to="/new"
            className="text-xs text-sidebar-primary hover:text-sidebar-primary/80 font-medium"
          >
            + New
          </Link>
        </div>
        <div className="space-y-0.5">
          {projects.map(p => (
            <Link
              key={p.slug}
              to={`/${p.slug}/`}
              className="flex items-center gap-2.5 px-2 py-1.5 rounded-md text-sm hover:bg-sidebar-accent transition-colors"
            >
              <div className="w-2 h-2 rounded-full shrink-0" style={{ background: p.color }} />
              <span className="truncate">{p.title}</span>
            </Link>
          ))}
        </div>

        {user?.is_super_admin && (
          <div className="mt-4 pt-3 border-t border-sidebar-border">
            <Link
              to="/admin"
              className="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm text-sidebar-foreground/70 hover:bg-sidebar-accent transition-colors"
            >
              Admin
            </Link>
          </div>
        )}
      </nav>
    </>
  )
}

function ProjectSidebar({ project, activePath }: { project: string; activePath: string }) {
  const navigate = useNavigate()
  const location = useLocation()
  const projectBase = `/${project}`

  const { data: tree = [] } = useQuery({
    queryKey: ['tree', project],
    queryFn: () => apiGet<TreeNode[]>(`${projectBase}/api/tree`),
  })

  const { data: settings } = useQuery({
    queryKey: ['settings', project],
    queryFn: () => apiGet<{ project: ProjectConfig; is_owner: boolean }>(`${projectBase}/api/settings`).catch(() => null),
    retry: false,
  })

  const config = settings?.project
  const isOnIssues = location.pathname === `${projectBase}/issues`
  const isOnSettings = location.pathname === `${projectBase}/settings`

  return (
    <>
      <nav className="flex-1 overflow-y-auto px-3 py-2">
        {/* Back to projects */}
        <Link
          to="/"
          className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs text-sidebar-foreground/50 hover:text-sidebar-foreground hover:bg-sidebar-accent transition-colors mb-3"
        >
          ← Projects
        </Link>

        {/* Project header */}
        <div className="flex items-center gap-2 px-2 mb-3">
          {config && <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: config.color }} />}
          <span className="font-semibold text-sm truncate">{config?.title || project}</span>
        </div>

        {/* Docs section */}
        <div className="mb-1 px-2">
          <span className="text-xs font-medium text-sidebar-foreground/50 uppercase tracking-wider">Docs</span>
        </div>
        <div className="mb-3">
          <FileTree
            nodes={tree}
            activePath={activePath}
            onSelect={(path) => navigate(`${projectBase}/${path}`)}
          />
        </div>

        {/* Links */}
        <div className="space-y-0.5">
          <Link
            to={`${projectBase}/issues`}
            className={`flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors ${
              isOnIssues ? 'bg-sidebar-accent text-sidebar-foreground font-medium' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent'
            }`}
          >
            Issues
          </Link>
          {settings && (
            <Link
              to={`${projectBase}/settings`}
              className={`flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors ${
                isOnSettings ? 'bg-sidebar-accent text-sidebar-foreground font-medium' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent'
              }`}
            >
              Settings
            </Link>
          )}
        </div>
      </nav>
    </>
  )
}

export function AppSidebar() {
  const { user } = useAuth()
  const { context, project, subPath } = useAppContext()

  if (!user) return null

  return (
    <aside className="w-60 h-screen flex flex-col bg-sidebar border-r border-sidebar-border shrink-0">
      {/* Header */}
      <div className="px-4 py-3 border-b border-sidebar-border">
        <Link to="/" className="flex items-center gap-2">
          <img src="/logo-book.svg" alt="Memento" className="h-6 w-6" />
          <span className="text-base font-bold tracking-tight font-serif">Memento</span>
        </Link>
      </div>

      {/* Context-dependent navigation */}
      {context === 'dashboard' ? (
        <DashboardSidebar />
      ) : (
        <ProjectSidebar project={project!} activePath={subPath} />
      )}

      {/* Footer — user */}
      <div className="px-3 py-3 border-t border-sidebar-border">
        <div className="flex items-center gap-2.5 px-1">
          <Avatar className="h-6 w-6">
            <AvatarImage src={user.picture} />
            <AvatarFallback className="text-[10px] bg-sidebar-accent">
              {getInitials(user.name, user.email)}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium leading-tight truncate">{user.name || user.email}</div>
          </div>
          <a
            href="/auth/logout"
            className="text-xs text-sidebar-foreground/40 hover:text-sidebar-foreground transition-colors"
          >
            Sign out
          </a>
        </div>
      </div>
    </aside>
  )
}
