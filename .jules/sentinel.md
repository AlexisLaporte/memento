## 2026-03-25 - Open Redirect and Module Shadowing
**Vulnerability:** Open Redirect in Auth0 login/callback flow and shadowing of standard `email` library.
**Learning:** Blindly trusting `next` parameters in redirect-heavy flows (like OAuth) can lead to users being sent to malicious sites. Also, naming local modules after standard library packages (like `email.py`) causes shadowing, which breaks common libraries that depend on the standard package (e.g., `urllib3`'s dependency on `email.utils`).
**Prevention:** Use a helper like `is_safe_url` to validate redirect targets against the request host. Always avoid naming local files with common standard library names (e.g., `email.py`, `json.py`, `csv.py`).
