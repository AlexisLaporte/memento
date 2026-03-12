"""Documentation file tree and markdown viewer routes."""

from pathlib import Path

import markdown
import yaml
from flask import Blueprint, g, jsonify, render_template, session

from ..auth import requires_access

docs_bp = Blueprint('docs', __name__)

_md = markdown.Markdown(extensions=[
    'tables',
    'fenced_code',
    'codehilite',
    'toc',
    'pymdownx.tasklist',
    'pymdownx.magiclink',
], extension_configs={
    'codehilite': {'css_class': 'highlight', 'guess_lang': False},
})


# ─── Route: project index ────────────────────────────────────────────────────

@docs_bp.route('/')
@docs_bp.route('/<path:doc_path>')
@requires_access
def index(doc_path=None):
    return render_template('index.html', config=g.config, project_slug=g.project)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _base_path():
    return Path(g.config.base_path).resolve()


def _safe_path(relative: str) -> Path | None:
    """Resolve a relative path under base, return None if traversal detected."""
    base = _base_path()
    target = (base / relative).resolve()
    if not str(target).startswith(str(base)):
        return None
    rel = target.relative_to(base)
    parts = rel.parts
    if not parts:
        return None
    root = parts[0]
    if root in g.config.docs_paths:
        return target
    if len(parts) == 1 and root in g.config.allowed_files:
        return target
    return None


def _build_tree() -> list[dict]:
    """Build a JSON-serializable file tree for configured paths."""
    base = _base_path()
    tree = []
    for root_name in sorted(g.config.docs_paths):
        root_path = base / root_name
        if not root_path.is_dir():
            continue
        node = _dir_node(root_path, base)
        if node:
            tree.append(node)
    for filename in sorted(g.config.allowed_files):
        fp = base / filename
        if fp.is_file():
            tree.append({"name": filename, "path": filename, "type": "file"})
    return tree


def _dir_node(dir_path: Path, base: Path) -> dict | None:
    """Recursively build a directory node."""
    children = []
    try:
        for entry in sorted(dir_path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            if entry.name.startswith('.'):
                continue
            if entry.is_dir():
                child = _dir_node(entry, base)
                if child:
                    children.append(child)
            elif entry.suffix.lower() in ('.md', '.markdown'):
                children.append({
                    "name": entry.name,
                    "path": str(entry.relative_to(base)),
                    "type": "file",
                })
    except PermissionError:
        return None
    if not children:
        return None
    return {
        "name": dir_path.name,
        "path": str(dir_path.relative_to(base)),
        "type": "dir",
        "children": children,
    }


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from markdown text."""
    if not text.startswith('---'):
        return {}, text
    end = text.find('---', 3)
    if end == -1:
        return {}, text
    try:
        fm = yaml.safe_load(text[3:end]) or {}
    except Exception:
        fm = {}
    body = text[end + 3:].lstrip('\n')
    return fm, body


def _render_markdown(text: str) -> str:
    _md.reset()
    return _md.convert(text)


# ─── API Routes ──────────────────────────────────────────────────────────────

@docs_bp.route('/api/tree')
@requires_access
def api_tree():
    return jsonify(_build_tree())


@docs_bp.route('/api/doc/<path:doc_path>')
@requires_access
def api_doc(doc_path: str):
    target = _safe_path(doc_path)
    if not target or not target.is_file():
        return jsonify({"error": "Not found"}), 404

    text = target.read_text(errors='replace')
    fm, body = _parse_frontmatter(text)
    html = _render_markdown(body)

    return jsonify({"path": doc_path, "frontmatter": fm, "html": html})
