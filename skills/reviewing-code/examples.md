# Reviewing-Code Examples

## Contents

- 1 — Sample Specialist Agent Brief (correctness-agent)
- 2 — Sample Finding JSON (Phase 2 output)
- 3 — Sample Validator Response (Phase 3 Layer D)
- 4 — Sample Layer A Validation (Python + Hypothesis)
- 5 — Sample Executive Summary (Phase 4 output)
- 6 — Sample Roadmap (mixed categories)
- 7 — Invocation Examples

## 1. Sample Specialist Agent Brief (`correctness-agent`)

```
CONTEXT: You are a correctness reviewer for a Node.js/TypeScript Express API.
The orchestrator scoped these files to you and ranked them ≥3 on the attack-surface scale.

YOUR SLICE — Correctness only (logic bugs, edge cases, error handling):
- Off-by-one errors, wrong loop bounds
- Null / undefined dereferences and missing guards
- Race conditions, TOCTOU, async ordering bugs
- Swallowed exceptions, empty catch blocks, unhandled promise rejections
- Wrong condition (assignment vs equality, inverted logic)
- Integer / float traps (overflow, NaN propagation, precision loss)
- Missing input validation that causes wrong behavior (NOT injection — that's security-agent)
- Unreachable error paths

OTHER AGENTS COVER (do NOT report):
- Injection, auth, crypto, secrets → security-agent
- Algorithmic complexity, N+1, leaks → performance-agent
- Code smell, duplication, naming → maintainability-agent

FILES IN SCOPE:
- src/routes/orders.ts (rank 5)
- src/services/inventory.ts (rank 4)
- src/lib/cache.ts (rank 3)

TECHNIQUE — Chain-of-thought BEFORE the finding:
1. Identify the logical flow of the function (what state, what calls)
2. Walk through edge cases: empty input, nulls, concurrent calls, error paths
3. State the failure mode you see — which input triggers it, what goes wrong
4. ONLY THEN write the finding

For each finding include a `validation_hint` field: a one-line input/test that
would trigger the bug at runtime (Phase 3 will use this).

OUTPUT — JSON array, one entry per finding:
[
  {
    "finding_id": "BUG-001",
    "agent": "correctness-agent",
    "location": "src/routes/orders.ts:84",
    "severity_estimate": "High",
    "description": "...",
    "evidence": "<code snippet>",
    "impact": "...",
    "recommendation": "...",
    "validation_hint": "POST /orders with body {items: []} triggers crash on line 87"
  }
]

BUDGET: ≤8 tool calls, ≤800 words output.
```

---

## 2. Sample Finding JSON (Phase 2 output)

```json
[
  {
    "finding_id": "BUG-001",
    "agent": "correctness-agent",
    "location": "src/routes/orders.ts:84",
    "severity_estimate": "High",
    "description": "Order creation handler dereferences items[0] before checking that the array is non-empty. An empty cart submission (valid per the schema) crashes the request handler.",
    "evidence": "const firstSku = req.body.items[0].sku; // no length check above",
    "impact": "500 error on every empty-cart submission. Logs fill with TypeError. No graceful 400 response.",
    "recommendation": "Validate items.length > 0 before dereferencing, return 400 with clear message: if (!req.body.items?.length) return res.status(400).json({error: 'cart_empty'});",
    "validation_hint": "curl -X POST /orders -d '{\"items\":[]}' should return 400, not 500"
  },
  {
    "finding_id": "BUG-002",
    "agent": "correctness-agent",
    "location": "src/services/inventory.ts:142",
    "severity_estimate": "Critical",
    "description": "Race condition in stock decrement. The read-check-write sequence is not atomic; two concurrent requests for the last item can both pass the check and oversell.",
    "evidence": "const stock = await db.get(sku); if (stock > 0) { await db.set(sku, stock - 1); }",
    "impact": "Overselling under concurrent load. Customer charged for unavailable item. Inventory drifts negative.",
    "recommendation": "Use atomic decrement with conditional: UPDATE inventory SET qty = qty - 1 WHERE sku = ? AND qty > 0 — check rowsAffected. Or use Redis DECR / database row-level lock.",
    "validation_hint": "fire 100 concurrent POST /buy requests for a sku with stock=1; final stock should never be < 0"
  }
]
```

---

## 3. Sample Validator Response (Phase 3 Layer D)

Validator agent receives BUG-002 above and the surrounding code. Its output:

```json
{
  "finding_id": "BUG-002",
  "real": 5,
  "actionable": 5,
  "impactful": 5,
  "verdict": "CONFIRMED",
  "reason": "Read-modify-write across an await boundary is textbook TOCTOU. The atomic SQL recommendation is correct and applies cleanly.",
  "revised_recommendation": null
}
```

For comparison, here's a finding the validator REFUTES:

```json
{
  "finding_id": "BUG-014",
  "real": 2,
  "actionable": 4,
  "impactful": 1,
  "verdict": "REFUTED",
  "reason": "The 'unhandled promise rejection' is actually awaited two lines below (line 67) — the reviewer missed the await. No bug present.",
  "revised_recommendation": null
}
```

REFUTED findings move to the report's appendix, not the main findings list.

---

## 4. Sample Layer A Validation (Python + Hypothesis)

Original finding from `correctness-agent`:

```json
{
  "finding_id": "BUG-007",
  "location": "src/billing/discount.py:23",
  "description": "Discount calculation rounds incorrectly for inputs with many decimal places — float accumulation loses precision.",
  "validation_hint": "discount(price=0.1, qty=3) returns 0.30000000000000004 instead of 0.30"
}
```

Validator generates and runs a Hypothesis property test:

```python
from hypothesis import given, strategies as st
from decimal import Decimal
from src.billing.discount import discount

@given(price=st.decimals(min_value=0, max_value=1000, places=2),
       qty=st.integers(min_value=1, max_value=100))
def test_discount_precision(price, qty):
    result = discount(float(price), qty)
    expected = Decimal(price) * Decimal(qty)
    # result must round to 2 places matching expected
    assert abs(Decimal(str(result)) - expected) < Decimal('0.01')
```

Run output:
```
Falsifying example: test_discount_precision(price=Decimal('0.10'), qty=3)
AssertionError: 0.30000000000000004 ≠ 0.30
```

→ verdict CONFIRMED, confidence: high.

---

## 5. Sample Executive Summary (Phase 4 output)

```markdown
## Executive Summary

This review of the order-management service (47 source files, ~6,800 LOC) found
**2 Critical**, **5 High**, **11 Medium**, and **9 Low** issues — 27 actionable
findings after the validation pass refuted 8 false positives.

The most urgent risks are an inventory race condition that allows overselling
under concurrent load (BUG-002) and a missing authorization check on the admin
order export endpoint (SEC-001). Both should be patched before the next deploy.

The codebase shows a moderate maintainability trend: 4 functions exceed 200 LOC
with cyclomatic complexity above 20, suggesting room for extraction. Performance
findings are concentrated in the inventory service (3 N+1 queries in a single
hot path) — fixing those alone should noticeably improve p95 latency.

| Category        | Critical | High | Medium | Low | Info |
|-----------------|----------|------|--------|-----|------|
| Bugs            | 1        | 2    | 3      | 2   | 1    |
| Security        | 1        | 2    | 2      | 1   | 0    |
| Performance     | 0        | 1    | 4      | 3   | 0    |
| Maintainability | 0        | 0    | 2      | 3   | 4    |
| **Total**       | **2**    | **5**| **11** | **9**| **5**|

**Patch immediately:** BUG-002 (inventory race), SEC-001 (admin export authZ).
**This sprint:** PERF-001 (N+1 in cart load), BUG-005 (stale cache TTL), SEC-003 (weak token RNG).
```

---

## 6. Sample Roadmap (mixed categories)

```markdown
## Improvement Roadmap

### Immediate (next commit, before deploy)
- BUG-002 (Critical) — Atomic stock decrement; src/services/inventory.ts:142
- SEC-001 (Critical) — Add role check to /admin/orders/export; src/routes/admin.ts:23

### Short-term (this sprint)
- PERF-001 (High) — Replace N+1 in cart loader with single JOIN; src/services/cart.ts:88
- BUG-005 (High) — Cache TTL bug returns stale prices; src/lib/cache.ts:34
- SEC-003 (High) — Replace Math.random() with crypto.randomBytes for tokens; src/auth/token.ts:12
- BUG-007 (Medium) — Use Decimal for billing math; src/billing/discount.py:23

### Long-term (architectural)
- MAINT-002 (Medium) — Extract OrderController god class (340 LOC, 18 methods, cyclomatic 31)
- MAINT-005 (Medium) — Adopt repository pattern; raw DB calls in 14 files
- PERF-004 (Medium) — Move PDF generation off the request thread (currently blocks 800ms p95)
```

---

## 7. Invocation Examples

```bash
# Full review of a project
/reviewing-code ./src

# Only bugs + perf, skip validation phase (faster, more FPs)
/reviewing-code ./src --scope bugs,perf --no-validate

# With a custom rules file
/reviewing-code ./src --guidelines ./team-standards.md

# Specific file or subtree
/reviewing-code ./src/services/payment.ts
```
