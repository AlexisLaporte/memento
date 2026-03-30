## 2025-05-15 - [Open Redirect in Auth0 Flow]
**Vulnerability:** The `next` parameter in `/login` and `/callback` routes was used for redirection without validation, allowing attackers to redirect users to external, potentially malicious domains after authentication.
**Learning:** Redirection parameters must always be validated against the application's own host and scheme to prevent phishing and other redirection-based attacks.
**Prevention:** Implement a helper like `_is_safe_url` using `urlparse` and `urljoin` to compare the target URL's domain and scheme against the current application's host.
