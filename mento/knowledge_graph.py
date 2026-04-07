"""Knowledge graph builder — extracts document relationships from local git clones."""

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from . import repo as git_repo
from .routes.docs import _file_kind, _is_allowed, _parse_frontmatter


# ─── Data Model ──────────────────────────────────────────────────────────────


class NodeType(str, Enum):
    PROJECT = "project"
    DIRECTORY = "directory"
    DOCUMENT = "document"


class EdgeType(str, Enum):
    CONTAINS = "contains"
    LINKS_TO = "links_to"


@dataclass
class Node:
    id: str
    type: NodeType
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    source: str
    target: str
    type: EdgeType
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    project_slug: str
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    _outgoing: dict[str, list[Edge]] = field(default_factory=dict)
    _incoming: dict[str, list[Edge]] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)
        self._outgoing.setdefault(edge.source, []).append(edge)
        self._incoming.setdefault(edge.target, []).append(edge)

    def neighbors(
        self,
        node_id: str,
        edge_types: list[EdgeType] | None = None,
        direction: str = "both",
    ) -> list[tuple[Edge, Node]]:
        results = []
        if direction in ("out", "both"):
            for e in self._outgoing.get(node_id, []):
                if edge_types is None or e.type in edge_types:
                    if e.target in self.nodes:
                        results.append((e, self.nodes[e.target]))
        if direction in ("in", "both"):
            for e in self._incoming.get(node_id, []):
                if edge_types is None or e.type in edge_types:
                    if e.source in self.nodes:
                        results.append((e, self.nodes[e.source]))
        return results

    def to_dict(self) -> dict:
        return {
            "project_slug": self.project_slug,
            "nodes": [
                {"id": n.id, "type": n.type.value, "label": n.label, **n.metadata}
                for n in self.nodes.values()
            ],
            "edges": [
                {"source": e.source, "target": e.target, "type": e.type.value, **e.metadata}
                for e in self.edges
            ],
        }


# ─── Link Extraction ────────────────────────────────────────────────────────

_MD_LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')


def _resolve_link(from_path: str, target: str) -> str:
    """Resolve a relative markdown link to an absolute repo path."""
    # Strip query strings and fragments for resolution
    clean = target.split('?')[0].split('#')[0]
    if not clean:
        return ''
    if clean.startswith('/'):
        clean = clean.lstrip('/')
    else:
        parent = '/'.join(from_path.split('/')[:-1])
        if parent:
            clean = f"{parent}/{clean}"
    # Normalize .. and . segments
    parts: list[str] = []
    for part in clean.split('/'):
        if part == '..':
            if parts:
                parts.pop()
        elif part and part != '.':
            parts.append(part)
    return '/'.join(parts)


# ─── Graph Builder ───────────────────────────────────────────────────────────


def build_graph(
    slug: str,
    docs_paths: list[str],
    allowed_files: list[str],
) -> KnowledgeGraph:
    """Build a knowledge graph from the local git clone of a project."""
    graph = KnowledgeGraph(project_slug=slug)

    # Project root node
    graph.add_node(Node(id=f"project:{slug}", type=NodeType.PROJECT, label=slug))

    items = git_repo.list_files(slug)
    allowed_items = [i for i in items if _is_allowed(i['path'], docs_paths, allowed_files)]

    dir_set: set[str] = set()
    doc_paths: list[str] = []

    # Pass 1: directories
    for item in allowed_items:
        if item['type'] == 'tree':
            path = item['path']
            dir_id = f"dir:{path}"
            name = path.split('/')[-1]
            graph.add_node(Node(
                id=dir_id, type=NodeType.DIRECTORY, label=name,
                metadata={"path": path},
            ))
            dir_set.add(path)
            parent = '/'.join(path.split('/')[:-1])
            parent_id = f"dir:{parent}" if parent in dir_set else f"project:{slug}"
            graph.add_edge(Edge(source=parent_id, target=dir_id, type=EdgeType.CONTAINS))
        elif item['type'] == 'blob' and _file_kind(item['path']) == 'markdown':
            doc_paths.append(item['path'])

    # Pass 2: markdown documents
    for path in doc_paths:
        try:
            raw = git_repo.read_file(slug, path)
            content = raw.decode('utf-8', errors='replace')
        except FileNotFoundError:
            continue

        fm, body = _parse_frontmatter(content)
        word_count = len(body.split())
        title = fm.get('title') or path.split('/')[-1].replace('.md', '').replace('.markdown', '')

        doc_id = f"doc:{path}"
        graph.add_node(Node(
            id=doc_id, type=NodeType.DOCUMENT, label=path.split('/')[-1],
            metadata={"path": path, "title": title, "word_count": word_count},
        ))

        # Parent directory edge
        parent_dir = '/'.join(path.split('/')[:-1])
        parent_id = f"dir:{parent_dir}" if parent_dir in dir_set else f"project:{slug}"
        graph.add_edge(Edge(source=parent_id, target=doc_id, type=EdgeType.CONTAINS))

        # Extract internal markdown links
        for match in _MD_LINK_RE.finditer(body):
            link_text, target = match.group(1), match.group(2)
            if target.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            resolved = _resolve_link(path, target)
            if not resolved:
                continue
            # Try with and without .md extension
            anchor = target.split('#')[1] if '#' in target else None
            target_doc_id = f"doc:{resolved}"
            if resolved and not resolved.endswith(('.md', '.markdown')):
                target_doc_id = f"doc:{resolved}.md"
            graph.add_edge(Edge(
                source=doc_id, target=target_doc_id, type=EdgeType.LINKS_TO,
                metadata={"link_text": link_text, **({"anchor": anchor} if anchor else {})},
            ))

    return graph


# ─── Cache ───────────────────────────────────────────────────────────────────

_graph_cache: dict[str, tuple[float, KnowledgeGraph]] = {}
_GRAPH_TTL = 120  # seconds


def get_or_build_graph(
    slug: str,
    docs_paths: list[str],
    allowed_files: list[str],
) -> KnowledgeGraph:
    key = f"kg:{slug}"
    entry = _graph_cache.get(key)
    if entry and entry[0] > time.monotonic():
        return entry[1]
    graph = build_graph(slug, docs_paths, allowed_files)
    _graph_cache[key] = (time.monotonic() + _GRAPH_TTL, graph)
    # Evict stale entries
    if len(_graph_cache) > 50:
        now = time.monotonic()
        for k in [k for k, (t, _) in _graph_cache.items() if t <= now]:
            del _graph_cache[k]
    return graph
