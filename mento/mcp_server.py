"""MCP remote server — exposes Mento docs to claude.ai."""

import base64
import os

from dotenv import load_dotenv

load_dotenv()

from fastmcp import FastMCP

from .config import ProjectConfig
from .db import get_member, get_project, load_projects_for_user, member_exists
from . import repo as git_repo
from .github_app import github_api
from .knowledge_graph import EdgeType, NodeType, get_or_build_graph
from .mcp_auth import create_auth_provider, get_user_email
from .routes.docs import _build_tree, _is_allowed, _parse_frontmatter

mcp = FastMCP(
    name="Mento",
    instructions="Access documentation and GitHub issues for projects hosted on Mento.",
    auth=create_auth_provider(),
)

def _check_access(email: str, slug: str) -> ProjectConfig:
    """Verify user has access to project, return config."""
    config = get_project(slug)
    if not config:
        raise ValueError(f"Project '{slug}' not found")
    if not member_exists(slug, email):
        raise ValueError(f"Access denied to '{slug}'")
    if git_repo.repo_exists(slug):
        config.default_branch = git_repo.resolve_default_branch(slug)
    return config


def _check_write_access(email: str, slug: str) -> ProjectConfig:
    """Verify user has admin access to project (required for write operations)."""
    config = _check_access(email, slug)
    member = get_member(slug, email)
    is_admin = (member and member['role'] == 'admin') or config.owner_email == email
    if not is_admin:
        raise ValueError(f"Write access denied: admin role required on '{slug}'")
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
    items = git_repo.list_files(project_slug)
    return _build_tree(items, config.docs_paths, config.allowed_files)


@mcp.tool
def read_doc(project_slug: str, path: str) -> dict:
    """Read a documentation file. Returns raw markdown content."""
    email = get_user_email()
    config = _check_access(email, project_slug)
    if not _is_allowed(path, config.docs_paths, config.allowed_files):
        raise ValueError(f"Path '{path}' is not accessible")
    raw = git_repo.read_file(project_slug, path)
    content = raw.decode('utf-8', errors='replace')
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


@mcp.tool
def create_doc(
    project_slug: str,
    path: str,
    content: str,
    message: str = "",
    branch: str = "",
) -> dict:
    """Create a new documentation file in the repository.

    Args:
        project_slug: Project identifier.
        path: File path in the repo (e.g. "docs/guide.md").
        content: File content (plain text / markdown).
        message: Commit message. Defaults to "Create <path>".
        branch: Target branch. Defaults to the repo's default branch.

    Returns:
        Dict with path, sha, and commit info.
    """
    email = get_user_email()
    config = _check_write_access(email, project_slug)
    if not _is_allowed(path, config.docs_paths, config.allowed_files):
        raise ValueError(f"Path '{path}' is not within allowed docs paths")
    target_branch = branch or config.default_branch
    commit_message = message or f"Create {path}"

    encoded = base64.b64encode(content.encode('utf-8')).decode('ascii')
    result = github_api(
        config.installation_id,
        f'/repos/{config.repo_full_name}/contents/{path}',
        method='PUT',
        json_body={
            'message': commit_message,
            'content': encoded,
            'branch': target_branch,
        },
    )
    return {
        "path": path,
        "sha": result['content']['sha'],
        "commit_sha": result['commit']['sha'],
        "commit_message": commit_message,
        "branch": target_branch,
    }


@mcp.tool
def update_doc(
    project_slug: str,
    path: str,
    content: str,
    message: str = "",
    branch: str = "",
) -> dict:
    """Update an existing documentation file in the repository.

    Automatically fetches the current file SHA required by GitHub.

    Args:
        project_slug: Project identifier.
        path: File path in the repo (e.g. "docs/guide.md").
        content: New file content (plain text / markdown).
        message: Commit message. Defaults to "Update <path>".
        branch: Target branch. Defaults to the repo's default branch.

    Returns:
        Dict with path, sha, and commit info.
    """
    email = get_user_email()
    config = _check_write_access(email, project_slug)
    if not _is_allowed(path, config.docs_paths, config.allowed_files):
        raise ValueError(f"Path '{path}' is not within allowed docs paths")
    target_branch = branch or config.default_branch
    commit_message = message or f"Update {path}"

    # Fetch current file to get its SHA (required for update)
    existing = github_api(
        config.installation_id,
        f'/repos/{config.repo_full_name}/contents/{path}',
    )
    current_sha = existing['sha']

    encoded = base64.b64encode(content.encode('utf-8')).decode('ascii')
    result = github_api(
        config.installation_id,
        f'/repos/{config.repo_full_name}/contents/{path}',
        method='PUT',
        json_body={
            'message': commit_message,
            'content': encoded,
            'sha': current_sha,
            'branch': target_branch,
        },
    )
    return {
        "path": path,
        "sha": result['content']['sha'],
        "previous_sha": current_sha,
        "commit_sha": result['commit']['sha'],
        "commit_message": commit_message,
        "branch": target_branch,
    }


@mcp.tool
def get_knowledge_graph(project_slug: str) -> dict:
    """Get the knowledge graph for a project's documentation.

    Returns document nodes, cross-references, and hierarchy.
    Use this to understand doc structure before diving into specific documents.
    """
    email = get_user_email()
    config = _check_access(email, project_slug)
    graph = get_or_build_graph(project_slug, config.docs_paths, config.allowed_files)
    nodes = graph.nodes
    return {
        "project_slug": project_slug,
        "stats": {
            "documents": sum(1 for n in nodes.values() if n.type == NodeType.DOCUMENT),
            "directories": sum(1 for n in nodes.values() if n.type == NodeType.DIRECTORY),
            "cross_references": sum(1 for e in graph.edges if e.type == EdgeType.LINKS_TO),
        },
        "documents": [
            {
                "path": n.metadata["path"],
                "title": n.metadata.get("title", n.label),
                "word_count": n.metadata.get("word_count", 0),
                "outgoing_links": sum(
                    1 for e in graph._outgoing.get(n.id, [])
                    if e.type == EdgeType.LINKS_TO
                ),
                "incoming_links": sum(
                    1 for e in graph._incoming.get(n.id, [])
                    if e.type == EdgeType.LINKS_TO
                ),
            }
            for n in nodes.values() if n.type == NodeType.DOCUMENT
        ],
    }


@mcp.tool
def get_related_docs(project_slug: str, path: str) -> dict:
    """Find documents related to a given document path.

    Returns documents connected by cross-references (links to/from)
    and sibling documents in the same directory.
    """
    email = get_user_email()
    config = _check_access(email, project_slug)
    graph = get_or_build_graph(project_slug, config.docs_paths, config.allowed_files)

    doc_id = f"doc:{path}"
    if doc_id not in graph.nodes:
        raise ValueError(f"Document '{path}' not found in knowledge graph")

    doc_node = graph.nodes[doc_id]

    links_to = [
        {
            "path": node.metadata["path"],
            "title": node.metadata.get("title", node.label),
            "link_text": edge.metadata.get("link_text", ""),
        }
        for edge, node in graph.neighbors(doc_id, [EdgeType.LINKS_TO], "out")
        if node.type == NodeType.DOCUMENT
    ]

    linked_from = [
        {
            "path": node.metadata["path"],
            "title": node.metadata.get("title", node.label),
            "link_text": edge.metadata.get("link_text", ""),
        }
        for edge, node in graph.neighbors(doc_id, [EdgeType.LINKS_TO], "in")
        if node.type == NodeType.DOCUMENT
    ]

    parent_dir = '/'.join(path.split('/')[:-1])
    parent_id = f"dir:{parent_dir}" if parent_dir else f"project:{project_slug}"
    siblings = [
        {"path": node.metadata["path"], "title": node.metadata.get("title", node.label)}
        for edge, node in graph.neighbors(parent_id, [EdgeType.CONTAINS], "out")
        if node.type == NodeType.DOCUMENT and node.id != doc_id
    ]

    return {
        "document": {"path": path, "title": doc_node.metadata.get("title", doc_node.label)},
        "links_to": links_to,
        "linked_from": linked_from,
        "siblings": siblings,
    }


@mcp.tool
def search_knowledge_graph(
    project_slug: str,
    query_type: str,
    value: str = "",
) -> list[dict]:
    """Query the knowledge graph.

    Args:
        project_slug: Project identifier.
        query_type: One of: "links_to" (docs linking to path), "linked_from" (docs
            linked from path), "orphans" (docs with no incoming links),
            "most_linked" (top 10 most referenced docs).
        value: File path for links_to/linked_from queries. Ignored for orphans/most_linked.
    """
    email = get_user_email()
    config = _check_access(email, project_slug)
    graph = get_or_build_graph(project_slug, config.docs_paths, config.allowed_files)

    if query_type == "links_to":
        doc_id = f"doc:{value}"
        return [
            {"path": n.metadata["path"], "title": n.metadata.get("title", n.label),
             "link_text": e.metadata.get("link_text", "")}
            for e, n in graph.neighbors(doc_id, [EdgeType.LINKS_TO], "in")
            if n.type == NodeType.DOCUMENT
        ]

    elif query_type == "linked_from":
        doc_id = f"doc:{value}"
        return [
            {"path": n.metadata["path"], "title": n.metadata.get("title", n.label)}
            for e, n in graph.neighbors(doc_id, [EdgeType.LINKS_TO], "out")
            if n.type == NodeType.DOCUMENT
        ]

    elif query_type == "orphans":
        return [
            {"path": n.metadata["path"], "title": n.metadata.get("title", n.label)}
            for n in graph.nodes.values()
            if n.type == NodeType.DOCUMENT
            and not any(
                e.type == EdgeType.LINKS_TO
                for e in graph._incoming.get(n.id, [])
            )
        ]

    elif query_type == "most_linked":
        docs = [
            (
                sum(1 for e in graph._incoming.get(n.id, []) if e.type == EdgeType.LINKS_TO),
                n,
            )
            for n in graph.nodes.values()
            if n.type == NodeType.DOCUMENT
        ]
        docs.sort(key=lambda x: x[0], reverse=True)
        return [
            {"path": n.metadata["path"], "title": n.metadata.get("title", n.label),
             "incoming_links": c}
            for c, n in docs[:10]
        ]

    else:
        raise ValueError(
            f"Unknown query_type: {query_type}. "
            "Use: links_to, linked_from, orphans, most_linked"
        )


# ASGI app for uvicorn
app = mcp.http_app()


def main():
    port = int(os.getenv('MCP_PORT', '5003'))
    mcp.run(transport="http", host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
