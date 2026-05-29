# Reviewing-Code Reference

## Contents

- §1 — File Ranking & Agent Taxonomy
- §2 — Severity Scoring
- §3 — Validation Oracle by Language
- §4 — Report Template

## §1 File Ranking & Agent Taxonomy

### File Risk Ranking (1-5)

Apply during Phase 1. Files scoring ≥3 enter Phase 2 specialist scope.

| Score | Description | Examples |
|---|---|---|
| **5** | Untrusted input + privileged action | HTTP route handlers parsing JSON, auth middleware, crypto primitives, deserializer, kernel driver, network packet parser |
| **4** | Trust boundary or risky parser | DB query builder, file uploader, URL fetcher, config loader, third-party API client, template renderer |
| **3** | Non-trivial business logic | State machines, complex algorithms, payment/billing logic, caching, scheduler |
| **2** | Internal utilities & glue | String helpers, logger wrappers, simple data classes, factory functions |
| **1** | Static or trivial | Constants, enum tables, type aliases, generated code, `__init__.py` re-exports |

### Agent Concern Map

Four non-overlapping specialists. Each finding is owned by exactly one.

| # | Agent | Looks for | CWE / category |
|---|---|---|---|
| 1 | `correctness-agent` | Bugs, edge cases, error-handling gaps, logic errors, races, swallowed exceptions, missing validation, unhandled rejection | CWE-362, 367, 476, 252, 754, 391, 20 (logic only — security input goes to security-agent), 190, 369 |
| 2 | `security-agent` | Exploitable flaws | CWE-89, 78, 79, 22, 918, 287, 862, 863, 798, 352, 327, 330, 502, 434, 295 — OWASP Top 10 |
| 3 | `performance-agent` | Algorithmic complexity, N+1, leaks, blocking I/O on hot path, redundant work, missing pagination | CWE-400 (resource exhaustion), perf anti-patterns |
| 4 | `maintainability-agent` | Code smells, duplication, dead code, god functions, naming, leaky abstractions, missing types, comment rot | non-CWE; design quality |

### Overlap rules (avoid double-reporting)

- Logic bug that's **also** a security flaw (e.g., race condition leading to auth bypass) → `security-agent` owns it; `correctness-agent` skips.
- Performance issue that's **also** a DoS vector → `security-agent` owns it.
- Style issue that hides a bug (e.g., shadowed variable masking real logic error) → `correctness-agent` owns it; `maintainability-agent` skips.
- When in doubt: the agent with higher-severity ownership wins.

---

## §2 Severity Scoring

### Steps

**Step 1 — Classify type:**
- Security exploitable (Bug class A)
- Functional bug / data loss / crash (Bug class B)
- Performance regression (Bug class C)
- Improvement / maintainability (Bug class D)

**Step 2 — Score Likelihood (0-9):**
- Reachability (is the buggy path actually called?)
- Required privilege (anonymous network user → 9; admin local → 2)
- Trigger ease (obvious one-liner → 9; subtle race under load → 4)

**Step 3 — Score Impact (0-9):**
- Class A: max(C, I, A) using CVSS-style C/I/A loss
- Class B: data loss = 9 / crash on hot path = 7 / wrong result = 5 / cosmetic wrong output = 2
- Class C: user-perceptible regression = 7 / measured but invisible = 4 / micro-optimization = 1
- Class D: blocks future work = 6 / slows future work = 3 / nice-to-have = 1

**Step 4 — Compute Risk Score:**
`Risk = (Likelihood + Impact) / 2` → 0-9 scale

**Step 5 — Map to tier:**

| Tier | Range | Examples |
|---|---|---|
| **Critical** | 7.0-9.0 | Unauth RCE, data-loss bug on common path, full memory corruption |
| **High** | 6.0-6.9 | Auth bypass requiring some setup; deadlock under load; major perf regression |
| **Medium** | 3.0-5.9 | Local privilege issue; rare crash; moderate perf regression; large refactor opportunity |
| **Low** | 1.0-2.9 | Style smell; dead code; micro-optimization; informational misconfig |
| **Info** | 0 | Best-practice notes; no measurable impact |

**Tiebreak:** Availability/Integrity > Confidentiality > Maintainability.

---

## §3 Validation Oracle by Language

This is the Mythos signature — pick the strongest oracle the language supports.

### C / C++

| Oracle | Command | Catches |
|---|---|---|
| **AddressSanitizer** | `clang -fsanitize=address -g`; run repro | Out-of-bounds, UAF, leaks |
| **UndefinedBehaviorSanitizer** | `clang -fsanitize=undefined`; run | Signed overflow, null deref, alignment |
| **ThreadSanitizer** | `-fsanitize=thread` | Data races |
| **MemorySanitizer** | `-fsanitize=memory` | Uninit reads |

ASan is the **gold-standard oracle** Anthropic used for Mythos. Near-zero false positives.

### Python

| Oracle | Command | Catches |
|---|---|---|
| **pytest** (existing tests) | `pytest -q <path>` | Regressions |
| **Hypothesis** (property-based) | Generate property test from finding evidence | Edge cases, invariants |
| **mypy / pyright** | `mypy --strict <file>` | Type errors |
| **bandit** (security) | `bandit -r <path>` | Common security smells |

### JavaScript / TypeScript

| Oracle | Command | Catches |
|---|---|---|
| **tsc** | `tsc --noEmit` | Type errors |
| **jest / vitest** | project test cmd | Regressions |
| **fast-check** | property-based properties | Invariants |
| **eslint** | `eslint --max-warnings 0` | Style + bug-prone patterns |

### Go

| Oracle | Command |
|---|---|
| **go test -race** | Data races |
| **go vet** | Common bugs |
| **staticcheck** | Logic smells |
| **-msan / -asan** (cgo) | Memory issues |

### Rust

| Oracle | Command |
|---|---|
| **cargo test** | Regressions |
| **miri** (unsafe blocks) | UB in `unsafe` |
| **clippy** | Smells + bug patterns |
| **proptest** | Property-based |

### Fallback (any language)

If no language-specific oracle works:
1. **Differential check** — if the finding suggests an alternative implementation, run both on N random inputs; divergence = confirmed.
2. **Existing test run** — does the project test suite pass? Did this finding break anything?
3. **LLM-as-judge only** (Layer D) — keep finding but flag `confidence: medium`.

### Validator Agent Prompt Template

```
You are validating a single code review finding. You have READ-ONLY access.

FINDING:
{finding JSON from Phase 2}

ORIGINAL FILE:
{file content surrounding the location}

YOUR JOB: Score the finding on three dimensions, 1-5 each:
- REAL: Is this actually present in the code as described?
- ACTIONABLE: Is the recommendation specific enough to apply?
- IMPACTFUL: Does fixing it meaningfully improve the project?

OUTPUT JSON:
{
  "real": <1-5>,
  "actionable": <1-5>,
  "impactful": <1-5>,
  "verdict": "CONFIRMED" | "REFUTED" | "REVISED",
  "reason": "<one sentence>",
  "revised_recommendation": "<only if verdict=REVISED>"
}

Rule: any score ≤2 → verdict = REFUTED. All ≥3 → CONFIRMED.
```

---

## §4 Report Template

### Top-level structure

1. **Executive Summary** — health score, severity counts, top 3 priorities, 1-paragraph plain-language business impact
2. **Scope & Methodology** — files reviewed, agents run, validation oracle used, what was skipped & why
3. **Findings Summary Table** — ID | Title | Category | Severity | Location | Confidence
4. **Detailed Findings** — full block for each Critical/High; aggregated lists for Medium/Low/Info
5. **Improvement Roadmap** — Immediate / Short-term / Long-term (mixed across categories)
6. **Appendices** — raw validator outputs, refuted findings (with reasons), tool versions

### Per-Finding Block

```markdown
## FINDING-{ID}: {Descriptive Title}

| Field        | Value                                          |
|--------------|------------------------------------------------|
| Category     | Bug / Security / Performance / Maintainability |
| Severity     | Critical / High / Medium / Low / Info          |
| Location     | path/to/file.py:42 (function_name)             |
| Risk Score   | 7.5 (Likelihood: 8, Impact: 7)                 |
| CWE / Tag    | CWE-89 — SQL Injection (if applicable)         |
| Confidence   | High (validated via ASan) / Medium (judge only)|
| Owner Agent  | security-agent                                 |

### Description
{What the issue is and why it matters in plain language}

### Evidence
```{language}
{code snippet or test output showing the issue}
```

### Impact
{Concrete consequence — data loss, RCE, perf regression, etc.}

### Recommendation
{Specific fix — code example, library swap, config change}

### Validation Result
{Sanitizer crash output / failed test / divergence summary / judge score}

### References (optional)
{CVE link, library docs, similar incidents, design pattern article}
```

### Roadmap Format

```markdown
## Improvement Roadmap

### Immediate (this commit / before next deploy)
- FIND-001 (Bug, Critical): Fix null deref in payment.process()
- FIND-007 (Security, Critical): Replace MD5 with bcrypt
- FIND-012 (Bug, High): Race in cache invalidation

### Short-term (this sprint)
- FIND-003 (Performance, High): Replace N+1 query with JOIN
- FIND-015 (Maintainability, Medium): Extract god function `handleRequest` (220 LOC, cyclomatic 24)

### Long-term (architectural)
- FIND-021 (Maintainability, Medium): Adopt repository pattern — direct DB access scattered across 14 files
- FIND-024 (Performance, Medium): Move heavy compute off the request thread
```

### Writing Rules

- **Specific > vague** — "Use parameterized queries via `cursor.execute('... %s', (v,))`" beats "fix SQL injection"
- **Verification step in every Critical/High** — what command/test confirms the fix
- **Mix categories in roadmap** — user wants prioritized work, not security-only or perf-only
- **Plain language in exec summary; code-level detail in findings**
- **Refuted findings get a separate appendix** — don't hide them, but don't lead with them either
