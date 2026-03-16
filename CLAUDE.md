# Mento

Multi-tenant documentation portal — renders GitHub markdown with team access control and AI (MCP) integration.

## Stack
- **Backend**: Python 3.11+, Flask (web app), FastMCP (MCP server)
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui, React Query, Framer Motion
- **Data**: PostgreSQL (projects + members), Auth0 (OAuth2), GitHub App (repo access)
- **Infra**: Gunicorn (WSGI), Uvicorn (ASGI for MCP), nginx, systemd
- **Other**: Resend (invitation emails), nh3 (HTML sanitization), Mermaid (diagrams)

## Architecture
```
memento/
├── app.py            # Flask factory, SPA fallback, project resolution
├── auth.py           # Auth0 OAuth + GitHub OAuth, access decorators
├── config.py         # ProjectConfig dataclass
├── db.py             # PostgreSQL CRUD (projects, members)
├── email.py          # Resend invitation emails
├── github_app.py     # GitHub App JWT + installation tokens + API client
├── mcp_auth.py       # MCP OAuth via Auth0Provider
├── mcp_server.py     # FastMCP server (6 tools: list/read/create/update docs, issues)
└── routes/
    ├── docs.py       # Doc tree, markdown rendering, search API
    ├── github.py     # GitHub issues/labels/milestones API
    ├── projects.py   # Project CRUD, installations, user info
    ├── settings.py   # Per-project settings, members, invitations
    └── global_admin.py  # Super admin dashboard + GitHub webhook

frontend/                # React SPA (Vite)
├── src/
│   ├── App.tsx          # Router + sidebar layout
│   ├── components/
│   │   ├── AppSidebar.tsx   # Persistent sidebar (dashboard/project context)
│   │   ├── DocViewer.tsx    # Markdown/image/text/PDF renderer
│   │   ├── FileTree.tsx     # Collapsible doc tree
│   │   ├── SearchModal.tsx  # Global search (Cmd+K)
│   │   └── IssuesTable.tsx  # GitHub issues table
│   ├── pages/           # DashboardPage, DocPage, NewProjectPage, SettingsPage, etc.
│   ├── hooks/use-auth.ts
│   └── lib/api.ts       # Fetch wrapper
└── dist/                # Built assets (served by Flask/nginx)
```

## Commands
```bash
# Dev
cd frontend && npm run dev   # Vite dev server (proxies to Flask)
python -m memento.app         # Flask dev (port 5002, Auth0 required)

# Build
cd frontend && npm run build  # Build SPA to dist/

# Prod
gunicorn 'memento.app:create_app()' -b 127.0.0.1:5002
uvicorn memento.mcp_server:app --host 127.0.0.1 --port 5004
```

## URL Routing
- `/<project>/` — doc viewer (SPA, client-side routing)
- `/<project>/api/tree` — doc file tree (JSON)
- `/<project>/api/doc/<path>` — rendered markdown / file content (JSON)
- `/<project>/api/raw/<path>` — binary file proxy (PDF, images) with correct Content-Type
- `/<project>/api/issues` — GitHub issues
- `/<project>/issues` — issues page (SPA)
- `/<project>/settings` — project settings (SPA)
- `/new` — project creation wizard
- `/admin` — super admin (MEMENTO_SUPER_ADMINS)
- `/auth/login|callback|logout` — Auth0 flow
- `/auth/github|github/callback` — GitHub OAuth (user installations)

## Conventions
- Multi-tenant via URL prefix `/<project>/` resolved in `url_value_preprocessor`
- Access control: explicit membership in `memento_members` table
- Roles: `blocked` → `member` → `admin`. Owner = project creator
- `docs_paths=['/']` = wildcard (show all files in repo)
- Backend = pure JSON API, frontend = React SPA (no server-side HTML)
- Markdown HTML sanitized with `nh3` before sending to frontend
- GitHub API calls go through `github_app.github_api()` with installation tokens
- GitHub installations filtered per user via OAuth user-to-server tokens

## Key Concepts
- **Project**: slug + GitHub repo + access rules. Stored in `memento_projects` table.
- **Installation**: GitHub App install on an org/user. Provides repo access tokens.
- **GitHub OAuth**: Separate from Auth0 login. Users connect GitHub to see their installations when creating projects. Token stored in session.
- **MCP connector**: FastMCP remote server on port 5004, OAuth2 via Auth0 with DCR proxy. Users add `https://mcp.memento.otomata.tech/mcp` in claude.ai. 6 tools: list_projects, get_doc_tree, read_doc, create_doc, update_doc, list_issues.

## Docs
Detailed docs in `docs/`:
- `architecture.md` — Auth flow, data model, multi-tenancy, MCP integration, security
- `deployment.md` — Production setup, env vars, CI/CD, infra
- `design-assets.md` — Color palette, fonts, logo, illustrations (Firefly prompts)
