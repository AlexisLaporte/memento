# Memento

Multi-tenant documentation portal — renders GitHub markdown with team access control and AI (MCP) integration.

## Stack
- Python 3.11+, Flask (web app), FastMCP (MCP server)
- PostgreSQL (projects + members), Auth0 (OAuth2)
- GitHub App (repo access via installation tokens)
- Resend (invitation emails), Tailwind CSS (CDN)
- Gunicorn (prod WSGI), Uvicorn (prod ASGI for MCP)

## Architecture
```
memento/
├── app.py            # Flask factory, root routes (welcome/dashboard)
├── auth.py           # Auth0 OAuth, access decorators (requires_auth/access/admin)
├── config.py         # ProjectConfig dataclass
├── db.py             # PostgreSQL CRUD (projects, members)
├── email.py          # Resend invitation emails
├── github_app.py     # GitHub App JWT signing + installation tokens
├── mcp_auth.py       # MCP OAuth via Auth0Provider
├── mcp_server.py     # FastMCP server (4 tools: list_projects, get_doc_tree, read_doc, list_issues)
├── routes/
│   ├── docs.py       # Doc tree + markdown rendering API
│   ├── github.py     # GitHub issues/labels/milestones API
│   ├── projects.py   # Self-service project creation (account → repo selector)
│   ├── settings.py   # Per-project settings, members, invitations
│   └── global_admin.py  # Super admin dashboard + GitHub webhook
├── templates/
│   └── index.html    # SPA shell for doc viewer
└── static/
    ├── app.js        # Frontend: file tree, doc rendering, search
    └── app.css       # Styles (codehilite, tree, layout)
```

## Commands
```bash
# Dev
honcho start                     # Runs app (5002) + mcp (5003)
MEMENTO_DEV=1 python -m memento.app  # Dev mode (no auth)

# Prod
gunicorn 'memento.app:create_app()' -b 127.0.0.1:5002
uvicorn memento.mcp_server:app --host 127.0.0.1 --port 5003
```

## URL Routing
- `/<project>/` — doc viewer SPA
- `/<project>/api/tree` — doc file tree (JSON)
- `/<project>/api/doc/<path>` — rendered markdown (JSON)
- `/<project>/api/issues` — GitHub issues
- `/<project>/settings` — project admin
- `/new` — project creation wizard
- `/admin` — super admin (MEMENTO_SUPER_ADMINS)
- `/auth/login|callback|logout` — Auth0 flow

## Conventions
- Multi-tenant via URL prefix `/<project>/` resolved in `url_value_preprocessor`
- Access control: domain allowlist OR explicit membership (memento_members table)
- Roles: `blocked` → `member` → `admin`. Owner = creator of the project.
- `docs_paths=['/']` = wildcard (show all markdown in repo)
- HTML pages are inline f-strings (no Jinja templates except index.html)
- GitHub API calls always go through `github_app.github_api()` with installation tokens

## Key Concepts
- **Project**: slug + GitHub repo + access rules. Stored in `memento_projects` table.
- **Installation**: GitHub App install on an org/user. Provides repo access tokens.
- **MCP connector**: FastMCP remote server on separate port, OAuth2 via Auth0 with DCR proxy. Users add `https://mcp.memento.otomata.tech/mcp` in claude.ai.

## Docs
Detailed docs in `docs/`:
- `architecture.md` — Auth flow, data model, multi-tenancy, MCP integration
- `deployment.md` — Production setup, env vars, CI/CD, infra
