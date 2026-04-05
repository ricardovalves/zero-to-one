# Security Checklist Reference

Shared reference for `security-engineer`, `backend-engineer`, and `pr-reviewer`.
Use this for quick-scan reviews. Full threat modelling lives in `security-engineer.md`.

The tools listed below reflect common ecosystem defaults. Projects using a different stack
should override them in `workspace/{project}/src/CLAUDE.md`.

---

## Three-Tier Decision Model

### Always Do — non-negotiable, apply without asking

- [ ] Validate and sanitize all user input at the boundary (e.g. Pydantic v2, Zod, or equivalent)
- [ ] Use parameterized queries / ORM only — no string interpolation with user data
- [ ] Hash passwords with a slow hashing algorithm (e.g. bcrypt cost ≥ 12) — never MD5, SHA1, or plain text
- [ ] Enforce HTTPS in production — mark cookies as `secure` in production environments only
- [ ] Set security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- [ ] Never log passwords, tokens, or PII — structured JSON logs only
- [ ] Rate-limit authentication endpoints (login: 10/min, forgot-password: 3/min)
- [ ] Validate JWT signature on every protected request — never trust unverified claims

### Ask First — requires human review before implementing

- [ ] Any change to authentication or authorization logic
- [ ] New third-party integrations (new OAuth provider, new payment processor)
- [ ] Any endpoint that handles PII or financial data
- [ ] Schema changes that affect row-level access policies
- [ ] New admin or elevated-privilege endpoints

### Never Do — hard prohibitions, always block

- [ ] Commit secrets, API keys, or credentials to version control
- [ ] Trust client-side validation alone — always re-validate on the server
- [ ] Use `eval()`, `exec()`, or shell execution with user-controlled input
- [ ] Return stack traces or internal error details in API responses
- [ ] Store plaintext passwords or reversibly encrypted passwords
- [ ] Disable SSL certificate verification

---

## OWASP Top 10 Quick Scan

| Risk | Check |
|---|---|
| A01 Broken Access Control | Every endpoint verifies the authenticated user; users cannot access other users' data |
| A02 Cryptographic Failures | Passwords slow-hashed; tokens signed with a strong algorithm; sensitive fields encrypted at rest |
| A03 Injection | ORM only — no raw SQL with user input; no shell commands with user data |
| A04 Insecure Design | Auth endpoints rate-limited; no user enumeration in "email not found" errors |
| A05 Security Misconfiguration | No debug mode in production; CORS allowlist not `*`; security headers present |
| A06 Vulnerable Components | Dependency audit tool run in CI; no dependencies with known CVEs |
| A07 Auth Failures | Access token short TTL (≤ 15 min); refresh token in httpOnly cookie; no token in URL params |
| A08 Software Integrity | Webhook signatures verified before processing; no unsigned webhooks accepted |
| A09 Logging Failures | Structured JSON logs; no PII in logs; errors logged server-side, not exposed to client |
| A10 SSRF | No user-controlled URLs fetched server-side without allowlist validation |

---

## Auth Token Checklist

- [ ] Access token: short TTL (≤ 15 min), strongly signed, payload contains only user identity and expiry
- [ ] Refresh token: longer TTL (≤ 30 days), stored in httpOnly cookie AND returned in response body
- [ ] Cookie flags: `httpOnly`, `SameSite=lax`, `secure` in production only
- [ ] Refresh endpoint: accepts token from request **body** (not just cookie) — cookie can be blocked by browser policy
- [ ] On 401 in frontend: attempt one refresh, then redirect to login — never retry infinitely
- [ ] Logout: invalidate refresh token server-side; clear cookie; clear client-side auth state

---

## Sensitive Data Handling

- [ ] Third-party IDs and tokens (e.g. payment processor customer IDs, OAuth access tokens) encrypted at rest
- [ ] Response schemas never include password hashes, raw tokens, or internal IDs not needed by the client
- [ ] Response models explicitly exclude sensitive fields — do not serialize the full ORM object without exclusion
