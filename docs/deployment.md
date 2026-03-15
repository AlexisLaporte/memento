# Deployment

Production on `memento.otomata.tech` (51.15.225.121).

## Services

| Service | Port | Process | Domain |
|---------|------|---------|--------|
| memento | 5002 | gunicorn (Flask WSGI) | memento.otomata.tech |
| memento-mcp | 5003 | uvicorn (ASGI) | mcp.memento.otomata.tech |

Systemd units: `infra/prod/service.conf`, `infra/prod/memento-mcp.service`
Nginx configs: `infra/prod/nginx.conf`, `infra/prod/nginx-mcp.conf`

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

### Optional
| Variable | Default | Description |
|----------|---------|-------------|
| `MEMENTO_DEV` | `""` | Set `1` for dev mode (no auth) |
| `MEMENTO_SUPER_ADMINS` | `""` | Comma-separated admin emails |
| `MEMENTO_BASE_URL` | `https://memento.otomata.tech` | Used in emails |
| `RESEND_API_KEY` | — | Resend API key for invitation emails |
| `RESEND_FROM_EMAIL` | `noreply@otomata.tech` | Sender address |
| `AUTH0_MCP_AUDIENCE` | `https://mcp.memento.otomata.tech/` | Auth0 API audience for MCP |
| `MCP_BASE_URL` | `https://mcp.memento.otomata.tech` | MCP server public URL |
| `MCP_PORT` | `5003` | MCP server port |
| `GITHUB_APP_NAME` | `memento-document` | For install URL in project creation |

## CI/CD

`.github/workflows/deploy.yml` — on push to `master`:
1. SSH to server
2. `git pull origin master`
3. `pip install -e .`
4. `systemctl restart memento` + `memento-mcp`

Deploy key: GitHub secret `SSH_PRIVATE_KEY` (no passphrase).

## Auth0 Setup

- **Application**: Regular Web App (authlib integration)
- **API**: audience `https://mcp.memento.otomata.tech/` (for MCP tokens)
- **Callback URLs**: `https://memento.otomata.tech/auth/callback`
- **Post-Login Action**: adds email claim to access tokens for MCP:
  ```js
  api.accessToken.setCustomClaim('https://memento.otomata.tech/email', event.user.email);
  ```

## GitHub App

- **Name**: memento-document (public)
- **ID**: 3078636
- **Permissions**: Contents (read), Issues (read), Metadata (read)
- **Webhook URL**: `https://memento.otomata.tech/api/webhook/github`
- **Callback URL**: `https://memento.otomata.tech/auth/callback` (setup redirect)

## Database

PostgreSQL `memento` on localhost:5432. Tables auto-created by `db.ensure_schema()` on app startup.

## Server Setup

```bash
# On 51.15.225.121
cd /opt/memento
git clone https://github.com/AlexisLaporte/memento .
python3 -m venv venv
venv/bin/pip install -e .

# Copy .env with all required vars
# Copy systemd units and nginx configs
# Enable services + reload nginx
```

## SSL

Managed via `/data/infra/scripts/ssl-cert.sh` (Let's Encrypt, shared cert for otomata.tech subdomains).
