"""MCP remote server — exposes Memento docs to claude.ai."""

import base64
import os

from dotenv import load_dotenv

load_dotenv()

from fastmcp import FastMCP

from .config import ProjectConfig
from .db import get_project, load_projects_for_user, member_exists
from .github_app import github_api
from .mcp_auth import create_auth_provider, get_user_email
from .routes.docs import _build_tree, _is_allowed, _parse_frontmatter

mcp = FastMCP(
    name="Memento Docs",
    instructions="Access documentation and GitHub issues for projects hosted on Memento.",
    auth=create_auth_provider(),
)

# Cache default branches per project slug
_branch_cache: dict[str, str] = {}


def _resolve_branch(config: ProjectConfig) -> str:
    if config.slug not in _branch_cache:
        try:
            repo = github_api(config.installation_id, f'/repos/{config.repo_full_name}')
            _branch_cache[config.slug] = repo.get('default_branch', 'main')
        except Exception:
            _branch_cache[config.slug] = 'main'
    return _branch_cache[config.slug]


def _check_access(email: str, slug: str) -> ProjectConfig:
    """Verify user has access to project, return config."""
    config = get_project(slug)
    if not config:
        raise ValueError(f"Project '{slug}' not found")
    if not member_exists(slug, email):
        raise ValueError(f"Access denied to '{slug}'")
    config.default_branch = _resolve_branch(config)
    return config


@mcp.tool
def list_projects() -> list[dict]:
    """List documentation projects the current user has access to."""
    email = get_user_email()
    projects = load_projects_for_user(email)
    return [
        {"slug": slug, "title": c.title, "repo": c.repo_full_name}
        for slug, c in projects.items()
    ]


@mcp.tool
def get_doc_tree(project_slug: str) -> list[dict]:
    """Get the documentation file tree for a project."""
    email = get_user_email()
    config = _check_access(email, project_slug)
    tree_data = github_api(
        config.installation_id,
        f'/repos/{config.repo_full_name}/git/trees/{config.default_branch}',
        params={'recursive': '1'},
    )
    return _build_tree(tree_data.get('tree', []), config.docs_paths, config.allowed_files)


@mcp.tool
def read_doc(project_slug: str, path: str) -> dict:
    """Read a documentation file. Returns raw markdown content."""
    email = get_user_email()
    config = _check_access(email, project_slug)
    if not _is_allowed(path, config.docs_paths, config.allowed_files):
        raise ValueError(f"Path '{path}' is not accessible")
    data = github_api(
        config.installation_id,
        f'/repos/{config.repo_full_name}/contents/{path}',
    )
    content = base64.b64decode(data['content']).decode('utf-8', errors='replace')
    fm, body = _parse_frontmatter(content)
    return {"path": path, "frontmatter": fm, "content": body}


@mcp.tool
def list_issues(
    project_slug: str, state: str = "open", labels: str = "",
) -> list[dict]:
    """List GitHub issues for a project. Filter by state (open/closed) and labels."""
    email = get_user_email()
    config = _check_access(email, project_slug)
    params = {"state": state, "per_page": "30", "sort": "updated", "direction": "desc"}
    if labels:
        params["labels"] = labels
    issues = github_api(
        config.installation_id,
        f'/repos/{config.repo_full_name}/issues',
        params,
    )
    return [
        {
            "number": i["number"], "title": i["title"], "state": i["state"],
            "labels": [l["name"] for l in i.get("labels", [])],
            "assignee": i["assignee"]["login"] if i.get("assignee") else None,
            "created_at": i["created_at"], "url": i["html_url"],
        }
        for i in issues if not i.get("pull_request")
    ]


# ASGI app for uvicorn
app = mcp.http_app()


def main():
    port = int(os.getenv('MCP_PORT', '5003'))
    mcp.run(transport="http", host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
