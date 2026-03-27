## 2024-05-22 - [Path Traversal in repo.py via startswith]
**Vulnerability:** The `read_file` function in `memento/repo.py` used `startswith` to verify if a resolved file path was within the project's repository directory. This was vulnerable to sibling directory attacks where a project slug could be a prefix of another directory (e.g., `p1` vs `p1-secret`). An attacker could use `../p1-secret/secret.txt` from within `p1` to bypass the check.
**Learning:** `startswith` on path strings is insufficient for directory containment checks because it doesn't respect directory boundaries.
**Prevention:** Use `os.path.commonpath` to robustly verify that a resolved path is contained within a base directory.
