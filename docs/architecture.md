# Architecture

Multi-tenant Flask app with per-project GitHub integration and MCP remote server.

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

### memento_members
| Column | Type | Description |
|--------|------|-------------|
| project_slug | TEXT FK | References memento_projects |
| email | TEXT | User email (PK with slug) |
| name | TEXT | Display name |
| picture | TEXT | Avatar URL |
| role | TEXT | `blocked`, `member`, `admin` |

## Auth Flow

```
User → memento.otomata.tech → Auth0 login → callback → session cookie
                                                          ↓
                                              requires_access decorator
                                                          ↓
                                              check domain allowlist
                                              OR member_exists(slug, email)
                                                          ↓
                                              upsert_member → get role
                                              blocked? → 403
                                              member/admin? → proceed
```

- `requires_auth` — just needs a session (used by project creation routes)
- `requires_access` — session + project membership (used by doc/issue routes)
- `requires_admin` — extends requires_access, checks `role == 'admin'` or owner
- `requires_super_admin` — checks `MEMENTO_SUPER_ADMINS` env var

Dev mode (`MEMENTO_DEV=1`): all decorators pass through, auto-login as `dev@local`.

## Multi-Tenancy

Project resolution happens in `url_value_preprocessor` (`app.py:51`):
1. Extract `project` from URL values
2. Load `ProjectConfig` from DB via `db.get_project(slug)`
3. Resolve GitHub default branch (cached in-memory)
4. Set `g.project` and `g.config`

All per-project blueprints are mounted at `/<project>/`:
- `docs_bp` — doc tree + markdown viewer
- `github_bp` — issues, labels, milestones
- `settings_bp` — members, config, invitations

## GitHub App Integration

```
memento → JWT (signed with App private key, 10min TTL)
       → POST /app/installations/{id}/access_tokens
       → installation token (cached 50min, valid 1h)
       → GET /repos/{owner/repo}/... (with installation token)
```

Key functions in `github_app.py`:
- `get_app_jwt()` — RS256-signed JWT with App ID
- `get_installation_token(id)` — cached installation access token
- `github_api(id, path, params)` — authenticated GET to GitHub API

Project creation (`routes/projects.py`): two-step selector fetches installations from `/app/installations`, then repos per installation.

## Doc Rendering Pipeline

```
GitHub git/trees API → _build_tree() → nested JSON tree (filtered by docs_paths)
GitHub contents API  → base64 decode → _parse_frontmatter() → _render_markdown() → HTML
```

- `_is_allowed(path, docs_paths, allowed_files)` — path gating (`/` = wildcard)
- `_build_tree(items, docs_paths, allowed_files)` — flat list → nested dirs/files, pruned + sorted
- Frontend (`app.js`) fetches tree + doc content via `/<project>/api/tree` and `/<project>/api/doc/<path>`

## MCP Server

Separate ASGI process (FastMCP on port 5003), OAuth2 via Auth0:

```
claude.ai → https://mcp.memento.otomata.tech/mcp
          → OAuth2 discovery (/.well-known/oauth-authorization-server)
          → DCR proxy (Auth0 doesn't support DCR natively)
          → Auth0 login → access token with email claim
          → MCP tool calls (list_projects, get_doc_tree, read_doc, list_issues)
```

Auth0 Action (post-login) injects email into access token:
```js
api.accessToken.setCustomClaim('https://memento.otomata.tech/email', event.user.email);
```

`mcp_auth.py:get_user_email()` reads email from token claims.
`mcp_server.py:_check_access()` verifies membership before each tool call.

## Email

`email.py` sends invitation emails via Resend API. Silently skips if `RESEND_API_KEY` not set.
