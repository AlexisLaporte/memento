## 2025-05-15 - [Robust Path Traversal Prevention]
**Vulnerability:** Path traversal using `startswith` on `os.path.realpath` is vulnerable to sibling directory attacks (e.g., `/repos/myslug` vs `/repos/myslug-secret`). Additionally, `_is_allowed` checks based on path components could be bypassed by `..` within a single segment (e.g., `docs/../README.md`).
**Learning:** `os.path.commonpath` is a safer way to verify that a resolved path is within a base directory because it respects path component boundaries.
**Prevention:** Use `os.path.commonpath` for containment checks and explicitly reject `..` in normalized path segments at the route level.
