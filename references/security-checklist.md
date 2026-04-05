# Security Checklist Reference

Shared reference for `security-engineer`, `backend-engineer`, and `pr-reviewer`.
Use this for quick-scan reviews. Full threat modelling lives in `security-engineer.md`.

---

## Three-Tier Decision Model

### Always Do — non-negotiable, apply without asking

- [ ] Validate and sanitize all user input at the boundary (Pydantic v2 / Zod)
- [ ] Use parameterized queries / ORM only — no string interpolation with user data
- [ ] Hash passwords with bcrypt (cost ≥ 12) — never MD5, SHA1, or plain text
- [ ] Enforce HTTPS in production — `secure=True` on cookies when `ENVIRONMENT == "production"`
- [ ] Set security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- [ ] Never log passwords, tokens, or PII — structured JSON logs only
- [ ] Rate-limit authentication endpoints (login: 10/min, forgot-password: 3/min)
- [ ] Validate JWT signature on every protected request — never trust unverified claims

### Ask First — requires human review before implementing

- [ ] Any change to authentication or authorization logic
- [ ] New third-party integrations (new OAuth provider, new payment processor)
- [ ] Any endpoint that handles PII or financial data
- [ ] Schema changes that affect RLS policies
- [ ] New admin or elevated-privilege endpoints

### Never Do — hard prohibitions, always block

- [ ] Commit secrets, API keys, or credentials to version control
- [ ] Trust client-side validation alone — always re-validate on the server
- [ ] Use `eval()`, `exec()`, or `subprocess` with user-controlled input
- [ ] Return stack traces or internal error details in API responses
- [ ] Store plaintext passwords or reversibly encrypted passwords
- [ ] Disable SSL certificate verification (`verify=False` in requests)

---

## OWASP Top 10 Quick Scan

| Risk | Check |
|---|---|
| A01 Broken Access Control | Every endpoint has `get_current_user` dependency; RLS set before queries; users cannot access other users' data |
| A02 Cryptographic Failures | Passwords bcrypt-hashed; tokens RS256-signed; sensitive fields AES-encrypted at rest |
| A03 Injection | ORM only — no raw SQL with user input; no shell commands with user data |
| A04 Insecure Design | Auth endpoints rate-limited; no user enumeration in "email not found" errors |
| A05 Security Misconfiguration | No debug mode in production; CORS allowlist not `*`; security headers present |
| A06 Vulnerable Components | `pip audit` / `npm audit` run in CI; no dependencies with known CVEs |
| A07 Auth Failures | Access token 15-min TTL; refresh token httpOnly cookie + body; no token in URL params |
| A08 Software Integrity | Stripe webhook signature verified before processing; no unsigned webhooks accepted |
| A09 Logging Failures | Structured JSON logs; no PII in logs; errors logged server-side, not exposed to client |
| A10 SSRF | No user-controlled URLs fetched server-side without allowlist validation |

---

## Auth Token Checklist

- [ ] Access token: 15-minute TTL, RS256-signed, payload contains only `sub` (user_id) and `exp`
- [ ] Refresh token: 30-day TTL, stored in httpOnly cookie AND returned in response body
- [ ] Cookie flags: `httponly=True`, `samesite="lax"`, `secure=True` in production only
- [ ] Refresh endpoint: accepts token from request **body** (not just cookie) — cookie can be blocked by browser policy
- [ ] On 401 in frontend: attempt one refresh, then redirect to `/login` — never retry infinitely
- [ ] Logout: invalidate refresh token in DB; clear cookie; clear Zustand store

---

## Sensitive Data Handling

- [ ] Stripe customer IDs encrypted at rest (AES-256-GCM)
- [ ] Plaid access tokens encrypted at rest
- [ ] Response schemas never include `password_hash`, raw tokens, or internal IDs not needed by the client
- [ ] Pydantic response models explicitly exclude sensitive ORM fields (do not use `model_validate` on the full ORM object without exclusion)
