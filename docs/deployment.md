# Deployment

Production on `mento.cc` (51.15.225.121).

## Services

| Service | Port | Process | Domain |
|---------|------|---------|--------|
| memento | 5002 | gunicorn (Flask WSGI) | mento.cc |
| memento-mcp | 5004 | uvicorn (ASGI) | mcp.mento.cc |

Systemd units: `/etc/systemd/system/memento.service`, `/etc/systemd/system/memento-mcp.service`
Working directory: `/opt/memento`
Env file: `/opt/memento/.env`

## Environment Variables

### Required
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Flask session secret |
| `AUTH0_DOMAIN` | e.g. `otomata.us.auth0.com` |
| `AUTH0_CLIENT_ID` | Auth0 application client ID |
| `AUTH0_CLIENT_SECRET` | Auth0 application client secret |
| `GITHUB_APP_ID` | GitHub App ID (3078636) |
| `GITHUB_APP_PRIVATE_KEY_PATH` | Path to `.pem` file |
| `GITHUB_APP_WEBHOOK_SECRET` | Webhook signature secret |
| `GITHUB_APP_CLIENT_ID` | GitHub App OAuth Client ID (for user installations) |
| `GITHUB_APP_CLIENT_SECRET` | GitHub App OAuth Client Secret |

### Optional
| Variable | Default | Description |
|----------|---------|-------------|
| `MEMENTO_HOST` | `memento.local` | Main host for custom domain detection |
| `MEMENTO_SUPER_ADMINS` | `""` | Comma-separated admin emails |
| `MEMENTO_BASE_URL` | `https://mento.cc` | Used in emails |
| `RESEND_API_KEY` | — | Resend API key for invitation emails |
| `RESEND_FROM_EMAIL` | `noreply@otomata.tech` | Sender address |
| `AUTH0_MCP_AUDIENCE` | `https://mcp.mento.cc/` | Auth0 API audience for MCP |
| `MCP_BASE_URL` | `https://mcp.mento.cc` | MCP server public URL |
| `MCP_PORT` | `5003` | MCP server port |
| `MEMENTO_REPOS_DIR` | `/opt/memento/repos` | Local git clone storage directory |
| `GITHUB_APP_NAME` | `memento-document` | For install URL in project creation |

## CI/CD

`.github/workflows/deploy.yml` — on push to `master`:

**Job 1 — build** (GitHub runner):
1. `npm ci && npm run build` (frontend)
2. Upload `frontend/dist/` as artifact

**Job 2 — deploy** (SSH to server):
1. `git pull origin master`
2. `pip install -e .` (backend deps)
3. SCP `frontend/dist/` to server
4. `systemctl restart memento memento-mcp`
5. `nginx -t && systemctl reload nginx`

Deploy key: GitHub secret `SSH_PRIVATE_KEY` (no passphrase).

## Auth0 Setup

- **Application**: Regular Web App (authlib integration)
- **API**: audience `https://mcp.mento.cc/` (for MCP tokens)
- **Callback URLs**: `https://mento.cc/auth/callback`
- **Post-Login Action**: adds email claim to access tokens for MCP:
  ```js
  api.accessToken.setCustomClaim('https://mento.cc/email', event.user.email);
  ```

## GitHub App

- **Name**: memento-document (public)
- **ID**: 3078636
- **Client ID**: `Iv23lioCvLQveA2B7qx8`
- **Permissions**: Contents (read+write), Issues (read), Metadata (read)
- **Webhook URL**: `https://mento.cc/api/webhook/github`
- **Callback URLs**:
  - `https://mento.cc/auth/callback` (setup redirect after install)
  - `https://mento.cc/auth/github/callback` (OAuth user token)

## Database

PostgreSQL `memento` on localhost:5432. Tables auto-created by `db.ensure_schema()` on app startup.

## Server Setup

```bash
# On 51.15.225.121
cd /opt/memento
git clone https://github.com/AlexisLaporte/memento .
python3 -m venv venv
venv/bin/pip install -e .
cd frontend && npm install && npx vite build

# Clone all project repos locally
python -m memento.repo sync

# Copy .env with all required vars
# Copy systemd units and nginx configs
# Enable services + reload nginx
```

## SSL

Managed via `/data/infra/scripts/ssl-cert.sh` (Let's Encrypt, shared cert for otomata.tech subdomains).
