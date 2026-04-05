# Testing Patterns Reference

Shared reference for `backend-engineer`, `frontend-engineer`, and `qa-engineer`.
Agents cite this file rather than embedding the same patterns repeatedly.

---

## Test Pyramid

| Layer | Tool (Backend) | Tool (Frontend) | When to use |
|---|---|---|---|
| Unit | pytest | vitest | Pure functions, business logic, isolated components |
| Integration | pytest + httpx | vitest + MSW | API routes, DB queries, hook behaviour with mocked network |
| E2E / Smoke | pytest + httpx (live stack) | Playwright | Full user flows, auth, multi-step sequences |
| Contract | curl + python3 assertions | — | Verify API response shapes match what hooks expect |

**Rule:** Test at the lowest level that gives you confidence. Don't use E2E tests to cover things a unit test can prove.

---

## Backend: pytest Patterns

### Arrange-Act-Assert structure

```python
async def test_create_expense_returns_201(client, auth_headers):
    # Arrange
    payload = {"amount_cents": 5000, "schedule_c_category": "supplies", "expense_date": "2026-04-01"}

    # Act
    response = await client.post("/api/v1/expenses", json=payload, headers=auth_headers)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["amount_cents"] == 5000
    assert data["schedule_c_category"] == "supplies"
    assert "id" in data
```

### Naming convention

```
test_{resource}_{condition}_{expected_outcome}

test_login_with_wrong_password_returns_401
test_list_expenses_without_auth_returns_401
test_create_expense_on_free_tier_over_limit_returns_402
test_dashboard_for_new_user_returns_empty_waterfall
```

### Required test cases per endpoint

Every endpoint needs at minimum:
- ✅ Happy path (correct input → expected response)
- ✅ Auth failure (no token → 401)
- ✅ Validation failure (missing required field → 422)
- ✅ Not found (wrong ID → 404)
- ✅ Plan gate (free tier hitting paid feature → 402) — if applicable

### Regression test header

```python
"""
Regression: {one-line bug description}
Bug found: {date or sprint}
Fixed by: {what the fix was — reference the commit or PR}
"""
```

### Fixtures (standard set — always available in conftest.py)

```python
@pytest.fixture
async def db():          # real test DB, rolls back after each test
async def client():      # httpx AsyncClient against the test app
async def free_user():   # seeded free-tier user
async def solo_user():   # seeded solo-tier user
async def auth_headers(free_user): # Bearer token for free_user
```

### Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| `assert response.json() is not None` | Tests nothing; any response body passes |
| Mocking the database | Misses SQL errors, RLS failures, constraint violations |
| `time.sleep(1)` in tests | Flaky; use `asyncio.wait_for()` or event-driven assertions |
| Testing a mock was called | Tests the implementation, not the behaviour; breaks on refactor |
| Shared mutable state between tests | One test's side effect contaminates the next |

---

## Frontend: vitest + React Testing Library Patterns

### Component test structure

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

describe('ExpenseForm', () => {
  it('should call onSubmit with parsed cents when amount is entered', async () => {
    // Arrange
    const onSubmit = vi.fn()
    render(<ExpenseForm onSubmit={onSubmit} />)

    // Act
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '50.00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    // Assert
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ amount_cents: 5000 }))
  })

  it('should show error message when amount is negative', async () => {
    render(<ExpenseForm onSubmit={vi.fn()} />)
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '-10' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(screen.getByText(/must be greater than zero/i)).toBeInTheDocument()
  })
})
```

### Hook test structure (with MSW)

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

const server = setupServer(
  http.get('/api/v1/expenses', () =>
    HttpResponse.json({ data: [], total: 0, page: 1, per_page: 50 })
  )
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

it('should return empty list on first load', async () => {
  const { result } = renderHook(() => useExpenses())
  await waitFor(() => expect(result.current.isLoading).toBe(false))
  expect(result.current.expenses).toEqual([])
})
```

### Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Testing by class name or DOM structure | Breaks on every styling change |
| `screen.getByTestId('submit-btn')` | `getByRole('button', {name: 'Save'})` is more resilient and tests accessibility too |
| Snapshot tests for complex UI | Snapshots capture accidental changes as regressions; use specific assertions |
| `await new Promise(r => setTimeout(r, 100))` | Use `waitFor()` instead |
| Mocking `api.ts` entirely | Misses real request construction; use MSW to intercept at the network layer |

---

## Contract Tests (Backend ↔ Frontend)

Run these against the live Docker stack after every build. They catch the field-name drift that unit tests cannot see.

```bash
BASE="http://localhost:8000/api/v1"
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"<seed email>","password":"<seed password>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Verify list response shape:
curl -s "$BASE/expenses" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert 'data' in d and isinstance(d['data'], list), f'Missing data[]: {list(d.keys())}'
assert 'total' in d, 'Missing total'
assert 'page' in d, 'Missing page'
assert 'per_page' in d, 'Missing per_page'
print('PASS expenses list shape')
"

# Verify singleton response (no wrapper):
curl -s "$BASE/billing/subscription" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert 'plan' in d, f'Missing plan field — got: {list(d.keys())}'
print('PASS billing singleton shape')
"
```
