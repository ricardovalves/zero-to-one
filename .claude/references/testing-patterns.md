# Testing Patterns Reference

Shared reference for `backend-engineer`, `frontend-engineer`, and `qa-engineer`.
Agents cite this file rather than embedding the same patterns repeatedly.

The tools listed below reflect the framework defaults. Projects using a different stack
should override them in `workspace/{project}/src/CLAUDE.md`.

---

## Test Pyramid

| Layer | Purpose | Default tools | When to use |
|---|---|---|---|
| Unit | Pure functions, business logic, isolated components | Language-native test runner | Any logic with clear inputs and outputs |
| Integration | API routes, DB queries, service-to-repository wiring | HTTP test client + real test DB | Verifying layers work together |
| E2E / Smoke | Full user flows against the running stack | Browser automation or HTTP client | Auth flows, multi-step sequences, post-deploy verification |
| Contract | API response shapes match what clients expect | curl + assertion script | Catch field-name drift between backend and frontend |

**Rule:** Test at the lowest level that gives you confidence. Don't use E2E tests to cover what a unit test can prove.

---

## Universal Patterns (apply regardless of language or framework)

### Arrange-Act-Assert

Every test follows this structure — no exceptions:

```
# Arrange — set up the state and inputs
# Act     — call the thing under test
# Assert  — verify the outcome precisely
```

A test with no Arrange is testing the wrong thing. A test with no Assert is not a test.

### Naming convention

```
{resource}_{condition}_{expected_outcome}

login_with_wrong_password → returns 401
list_items_without_auth   → returns 401
create_item_on_free_tier_over_limit → returns 402
dashboard_for_new_user    → returns empty collection, not error
```

Names are documentation. A failing test name should tell the reader what broke without reading the test body.

### Required cases per endpoint

Every API endpoint needs at minimum:
- ✅ Happy path — correct input produces expected response and status
- ✅ Auth failure — missing or invalid token returns 401
- ✅ Validation failure — missing required field returns the appropriate error status
- ✅ Not found — wrong or foreign ID returns 404, not 500
- ✅ Plan/role gate — lower-privilege caller hitting a restricted endpoint returns 402/403

### Regression test header

Every regression test file must open with:

```
Regression: {one-line description of the bug}
Bug found:  {date or sprint}
Fixed by:   {what the fix was — reference the commit or PR}
```

This makes the purpose of the test self-evident and ensures future refactors don't silently delete the guard.

---

## Backend Integration Test Patterns

### Structure

```
test_db      — real test database, transaction rolled back after each test
test_client  — HTTP client pointing at the test app
auth_headers — valid token for a test user

Test:
  1. Seed minimal required data
  2. Make the HTTP request via test_client
  3. Assert status code
  4. Assert specific fields in the response body (not "response is not null")
```

### Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Asserting the response body is non-null | Any response passes — including error responses |
| Mocking the database | Misses query errors, constraint violations, and auth policy failures |
| Sleeping to wait for async operations | Flaky — use proper async awaiting or polling with a timeout |
| Testing that a mock was called | Tests the implementation, not the behaviour; breaks on any refactor |
| Shared mutable state between tests | One test's side effect silently contaminates the next |
| Testing framework internals | If the framework guarantees it, don't test it |

---

## Frontend Component Test Patterns

### Structure

```
1. Render the component with controlled props
2. Simulate user interactions (click, type, submit)
3. Assert what the user sees or what callbacks were called
   — not what internal state changed
   — not what CSS class was applied
```

Query elements by their accessible role or label, not by class name or test ID — this makes tests resilient to visual redesigns and also validates accessibility.

### Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Querying by CSS class or DOM structure | Breaks on every styling change without a behaviour change |
| Snapshot tests for complex, data-driven UI | Snapshots encode accidental output as expected; use specific assertions |
| Arbitrary wait/sleep for async UI | Use the test library's `waitFor` equivalent instead |
| Mocking the entire API client | Misses real request construction; intercept at the network layer instead |
| Testing implementation details (state, refs) | Breaks on refactor even when behaviour is identical |

---

## Contract Tests (Backend ↔ Frontend)

Run against the live stack after every build. Catch field-name drift that unit and integration tests cannot see because they each mock the other side.

```bash
BASE="<api base url from src/CLAUDE.md>"

# 1. Authenticate and capture a token
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"<seed email>","password":"<seed password>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Verify list response envelope shape
curl -s "$BASE/<list endpoint>" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
required = ['data', 'total', 'page', 'per_page']
missing = [f for f in required if f not in d]
ok = not missing and isinstance(d.get('data'), list)
print('PASS' if ok else 'FAIL — ' + str(missing))
"

# 3. Verify singleton response (object at top level, no wrapper)
curl -s "$BASE/<singleton endpoint>" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
# Replace with the actual required fields for this endpoint
required = ['id', 'status']
missing = [f for f in required if f not in d]
print('PASS' if not missing else 'FAIL — missing: ' + str(missing))
"

# 4. Verify auth response has tokens at top level (not wrapped in {data: ...})
LOGIN=$(curl -s -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"<seed email>","password":"<seed password>"}')
python3 -c "
import sys, json
d = json.loads('$LOGIN')
ok = 'access_token' in d and 'refresh_token' in d
print('PASS auth shape' if ok else 'FAIL — tokens not at top level, got: ' + str(list(d.keys())))
"
```

Adapt the field names and endpoints to the project. The pattern — curl, parse JSON, assert field presence — is universal.
