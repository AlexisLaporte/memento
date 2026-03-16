"""MCP OAuth authentication via Auth0."""

import os

from fastmcp.server.auth.providers.auth0 import Auth0Provider
from fastmcp.server.dependencies import get_access_token


def create_auth_provider() -> Auth0Provider:
    return Auth0Provider(
        config_url=f"https://{os.getenv('AUTH0_DOMAIN')}/.well-known/openid-configuration",
        client_id=os.getenv('AUTH0_CLIENT_ID'),
        client_secret=os.getenv('AUTH0_CLIENT_SECRET'),
        audience=os.getenv('AUTH0_MCP_AUDIENCE', 'https://mcp.mento.cc/'),
        base_url=os.getenv('MCP_BASE_URL', 'https://mcp.mento.cc'),
    )


def get_user_email() -> str:
    """Extract email from the current request's access token."""
    token = get_access_token()
    if not token:
        raise ValueError("No access token")
    email = (
        token.claims.get('email')
        or token.claims.get('https://mento.cc/email')
        or token.claims.get('https://memento.otomata.tech/email')
    )
    if not email:
        raise ValueError("No email in token claims")
    return email
