# Architecture

Multi-tenant Flask API + React SPA with per-project GitHub integration and MCP remote server.

## Data Model

### memento_projects
| Column | Type | Description |
|--------|------|-------------|
| slug | TEXT PK | URL identifier (`/<slug>/`) |
| title | TEXT | Display name |
| repo_full_name | TEXT | `owner/repo` |
| installation_id | BIGINT | GitHub App installation |
| owner_email | TEXT | Project creator |
| docs_paths | TEXT[] | Directories to expose (default `{docs}`, `{/}` = all) |
| allowed_files | TEXT[] | Root-level files to expose |
| allowed_domains | TEXT[] | Auto-access email domains |
| color | TEXT | Theme color hex |
| custom_domain | TEXT | Optional custom domain (CNAME to memento.otomata.tech) |

### memento_members
| Column | Type | Description |
|--------|------|-------------|
| project_slug | TEXT FK | References memento_projects (CASCADE delete) |
| email | TEXT | User email (PK with slug) |
| name | TEXT | Display name |
| picture | TEXT | Avatar URL |
| role | TEXT | `blocked`, `member`, `admin` |

## Auth Flow

### Auth0 (login)
```
User → /auth/login → Auth0 → /auth/callback → session['user'] = {email, name, picture}
```

### GitHub OAuth (project creation)
```
User → /auth/github → github.com/login/oauth/authorize?client_id=<APP_CLIENT_ID>
     → /auth/github/callback → exchange code → session['github_token']
     → GET /user/installations (only user's installations)
```

GitHub OAuth uses the GitHub App's own OAuth credentials (GITHUB_APP_CLIENT_ID/SECRET), not Auth0. The token is only used during project creation to list user-specific installations and repos.

### Access decorators
- `requires_auth` — session exists (project creation, installations)
- `requires_access` — session + `member_exists(slug, email)` + role != blocked
- `requires_admin` — requires_access + role == admin or owner
- `requires_super_admin` — `MEMENTO_SUPER_ADMINS` env var

## Multi-Tenancy

Project resolution in `url_value_preprocessor` (`app.py`):
1. Extract `project` from URL values
2. Load `ProjectConfig` from DB via `db.get_project(slug)`
3. Resolve GitHub default branch (cached in-memory)
4. Set `g.project` and `g.config`

Per-project blueprints mounted at `/<project>/`:
- `docs_bp` — doc tree, markdown viewer, search, raw content
- `github_bp` — issues, labels, milestones
- `settings_bp` — members, config, invitations

Custom domains: `before_request` checks `request.host` against `memento_projects.custom_domain`, redirects to `/<slug>/` prefix.

## GitHub App Integration

### Server-to-server (installation tokens)
```
App private key → JWT (RS256, 10min TTL)
              → POST /app/installations/{id}/access_tokens
              → installation token (cached 50min)
              → GitHub API calls (contents, issues, trees)
```

### User-to-server (OAuth)
```
/auth/github → GitHub OAuth authorize (App Client ID)
             → /auth/github/callback → exchange code for user token
             → GET /user/installations → only user's accessible installs
             → GET /user/installations/{id}/repositories → user's repos
```

Key functions in `github_app.py`:
- `get_app_jwt()` — RS256-signed JWT with App ID
- `get_installation_token(id)` — cached installation access token
- `github_api(id, path, params, method, json_body)` — authenticated GitHub API request (GET/PUT/POST/DELETE)

## Doc Rendering Pipeline

```
GitHub git/trees API → _build_tree() → nested JSON tree (filtered by docs_paths)
GitHub contents API  → base64 decode → _parse_frontmatter()
                     → _render_markdown() → nh3.clean() → sanitized HTML
```

- `_is_allowed(path, docs_paths, allowed_files)` — path gating (`/` = wildcard)
- `_render_markdown()` — Python markdown → HTML → **nh3 sanitization** (strips script, event handlers)
- Supported file types: markdown, text/code, images, PDF
- Frontend receives HTML and renders via `dangerouslySetInnerHTML` (safe because sanitized server-side)

## Frontend (React SPA)

Notion-like layout: persistent sidebar + content area.

- **AppSidebar**: adapts to context (dashboard = project list, project = file tree + nav)
- **DocViewer**: renders markdown HTML, images, text/code, PDF. TOC sidebar on wide screens.
- **SearchModal**: Cmd+K global search across doc filenames
- **Routing**: React Router, URL is source of truth for sidebar ↔ content sync

Mobile: sidebar becomes a drawer, hamburger menu in sticky header.

## MCP Server

Separate ASGI process (FastMCP on port 5004), OAuth2 via Auth0:

```
claude.ai → https://mcp.memento.otomata.tech/mcp
          → OAuth2 (Auth0, DCR proxy)
          → Auth0 login → access token with email claim
          → MCP tool calls
```

### Tools
| Tool | Access | Description |
|------|--------|-------------|
| `list_projects` | any member | List user's accessible projects |
| `get_doc_tree` | member | File tree for a project |
| `read_doc` | member | Read markdown content (path must be in docs_paths) |
| `create_doc` | admin | Create new file in repo (path must be in docs_paths) |
| `update_doc` | admin | Update existing file (path must be in docs_paths) |
| `list_issues` | member | GitHub issues with filters |

Auth0 post-login Action injects email into access token:
```js
api.accessToken.setCustomClaim('https://memento.otomata.tech/email', event.user.email);
```

## Security

- **XSS prevention**: markdown HTML sanitized with `nh3` before frontend rendering
- **Path traversal**: `_is_allowed()` enforced on all read AND write operations (web + MCP)
- **RBAC**: every route has an access decorator; no unauthenticated data access
- **GitHub tokens**: installation tokens cached server-side, never exposed to frontend
- **GitHub user tokens**: stored in session only, used for installation listing during project creation
- **Webhook**: HMAC-SHA256 signature verification

## Email

`email.py` sends invitation emails via Resend API. Silently skips if `RESEND_API_KEY` not set.
