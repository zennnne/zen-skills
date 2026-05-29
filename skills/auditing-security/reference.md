# Code QA Reference

## Contents

- §1 — Vulnerability Category Taxonomy
- §2 — Risk Scoring Method
- §3 — Test Quality Checklist
- §4 — Report Template

## §1 Vulnerability Category Taxonomy

Eight non-overlapping categories — one per parallel agent. Assign files at dispatch time.

| # | Category | Agent | CWE IDs | Example Issues |
|---|---|---|---|---|
| 1 | **Injection** | `injection-agent` | CWE-89, 78, 79, 94, 22, 918 | SQL injection, XSS, OS command injection, code injection, path traversal, SSRF |
| 2 | **Auth & Access Control** | `auth-agent` | CWE-287, 862, 863, 798, 306, 352, 269, 345, 384, 601 | Auth bypass, missing authZ, hard-coded creds, missing auth for critical function, CSRF, privilege escalation, JWT verification flaws (alg:none / key confusion), session fixation, open redirects |
| 3 | **Cryptography & Secrets** | `crypto-agent` | CWE-327, 330, 522, 295 | MD5/SHA-1/ECB usage, `Math.random()` for tokens, plaintext secrets in source, improper cert validation |
| 4 | **Memory & Resource Safety** | `memory-agent` | CWE-787, 125, 476, 416, 401, 190 | Out-of-bounds write/read, null pointer deref, use-after-free, memory leak, integer overflow |
| 5 | **Insecure Data Handling** | `data-handling-agent` | CWE-502, 434, 20 | Unsafe deserialization, unrestricted file upload, missing input validation |
| 6 | **Business Logic & Race Conditions** | `logic-agent` | CWE-362, 367, 119 | Race conditions, TOCTOU, off-by-one, broken state machines, missing rate limits, improper resource limits |
| 7 | **Configuration, Headers & Dependencies** | `config-deps-agent` | CWE-16, 1104, 1021, 614, 1004, 942 | Secrets in config/env, insecure defaults, debug mode in prod, outdated/vulnerable deps, missing security headers (CSP/HSTS/X-Frame-Options), cookie flags (Secure/HttpOnly/SameSite), permissive CORS (`*` with credentials) |
| 8 | **Security Logging & Monitoring** | `observability-agent` | CWE-778, 532, 117, 223 | Missing logs for auth failures / authZ denials, sensitive data (passwords/tokens/PII) in logs, CRLF log injection from unsanitized user input, audit gaps on privileged actions (admin ops, data exports) |

**Language-specific note:** Skip `memory-agent` for Python/JS/TypeScript unless C extensions are present. Memory safety findings are most relevant for C, C++, Go, Rust.

**Project-type note:** Skip web-specific bits of `config-deps-agent` (headers, cookies, CORS) for CLI tools and libraries without an HTTP surface. Skip `observability-agent` for libraries — they delegate logging policy to the host application.

**SSRF placement:** SSRF (CWE-918) lives under Injection by root cause (attacker-controlled URL reaches network sink).

**JWT/session placement:** JWT verification, session fixation, and open redirects live under Auth — the root cause is broken authentication state, not crypto primitives.

**Cookie flags placement:** Cookie security flags live under Configuration — they are deployment configuration, not auth logic.

---

## §2 Risk Scoring Method

**Hybrid: OWASP Likelihood × Impact (CVSS-informed dimensions)**  
Sources: OWASP Risk Rating Methodology, CVSS v3.1 User Guide, DREAD model

### Scoring Steps (no exploit execution required)

**Step 1 — Classify type:** Security vulnerability OR non-security bug (performance / correctness / data loss)

**Step 2 — Score Likelihood (0–9)** from code reading:
- Attack vector: Network (AV:N) = highest; Local (AV:L) = lowest
- Ease of discovery: Is the attack surface obvious in the code?
- Ease of exploit: Does a known exploitation pattern exist (e.g., SQL string concatenation)?
- Required privilege: Anonymous internet user vs authenticated admin only

**Step 3 — Score Impact (0–9)**:
- Security: Confidentiality loss + Integrity loss + Availability loss (average or max)
- Non-security: data loss potential (1.0), crash likelihood (0.6), correctness failure (0.2)

**Step 4 — Compute Risk Score:**  
`Risk = (Likelihood + Impact) / 2` → 0–9 scale

**Step 5 — Map to tier** and sort findings descending; tiebreak on Availability/Integrity impact

### Severity Tiers

| Tier | Risk Range | Qualifying Criteria |
|---|---|---|
| **Critical** | 7.0–9.0 | Network-exploitable, no auth required, full C/I/A compromise — e.g., RCE, unauthenticated SQLi with data exfil |
| **High** | 6.0–6.9 | Significant data exposure or service disruption; partial auth bypass; data loss bugs |
| **Medium** | 3.0–5.9 | Requires some privilege or local access; limited blast radius; performance regressions |
| **Low** | 1.0–2.9 | Hard to exploit, minimal impact; informational misconfigurations, code smells |
| **Info** | 0 | Best-practice suggestions; no direct exploitability |

**Non-security bug weights:** Error (crash/data loss) = 1.0 / Warning (bad pattern) = 0.6 / Recommendation (maintainability) = 0.2

---

## §3 Test Quality Checklist

Use for the optional `test-quality-agent` or when the orchestrator evaluates test coverage.

### FIRST Principles (flag violations)

| Principle | What to Flag |
|---|---|
| **Fast** | `Thread.sleep`, real network calls, file I/O in unit test scope |
| **Independent** | Shared mutable state across tests; test ordering dependencies |
| **Repeatable** | Hardcoded timestamps, env-specific paths, unmocked external services |
| **Self-validating** | Tests with zero assertions (coverage theater) |
| **Timely** | Tests written long after production code (intent harder to verify) |

### Pyramid Distribution

- Target ~70% unit / 20% integration / 10% E2E
- Flag **ice cream cone** anti-pattern: many E2E, few unit → slow and fragile
- Flag **zero integration tests** in microservices: misses schema and contract bugs

### Structure & Anti-patterns

- Prefer Arrange / Act / Assert (or Given / When / Then)
- Test observable behavior, not implementation details
- DAMP over DRY: intentional test repetition is acceptable for readability
- **Flag:** mock overuse for call-order verification; fixed `sleep` instead of polling; hardcoded credentials in tests; one test asserting many unrelated things

### Coverage Metrics

| Metric | Gameable? | Recommended Use |
|---|---|---|
| Line coverage | Yes | Baseline; target >80% |
| Branch coverage | Partially | Better than line coverage |
| Mutation score | No | Gold standard — catches assertion gaps |
| Property-based | No | Pure functions, parsers, invariants |
| Fuzzing | No | Security-critical paths |

**Warning:** 100% line coverage with zero assertions = false safety. Always check assertion density.

---

## §4 Report Template

### Overall Structure

1. **Executive Summary** — overall risk posture, Critical/High finding count, business impact in plain language
2. **Scope & Methodology** — files reviewed, approach, limitations, what was out of scope
3. **Findings Summary Table** — ID | Title | Severity | Location (ranked Critical → Info)
4. **Detailed Findings** — one subsection per finding (see template below)
5. **Remediation Roadmap** — Immediate (patch now) / Short-term (next sprint) / Long-term (architectural)
6. **Appendices** — raw evidence, OWASP/CWE/CVE mapping

### Per-Finding Template

```markdown
## FINDING-{ID}: {Descriptive Title}

| Field      | Value                                              |
|------------|----------------------------------------------------|
| Severity   | Critical / High / Medium / Low / Info              |
| Location   | File path : function name : line number            |
| Risk Score | e.g., 7.5 (Likelihood: 8, Impact: 7)               |
| CWE        | e.g., CWE-89 — SQL Injection                       |
| Status     | Open / Accepted / Mitigated                        |

### Description
[What the issue is and why it is a problem]

### Evidence
[Code snippet or relevant lines showing the vulnerable pattern]

### Impact
[Concrete consequence: data exfiltration, RCE, service crash, auth bypass, etc.]

### Recommendation
[Specific fix — include code example, library/version, config flag, or architectural change]
[Verification: what to run after patching to confirm it is fixed]

### References
[CVE link, CWE page, OWASP guide, vendor patch notes]
```

### Remediation Writing Rules

- **Specific > vague**: "Use parameterized queries via `PreparedStatement`" beats "fix SQL injection"
- Include verification steps (command or test to confirm the fix)
- Tier by urgency: Immediate / Short-term (next sprint) / Long-term (redesign)
- Assign an owner or team role (AppSec, DevOps, DBA)
- Link CVE advisories, vendor patches, library changelogs
- Developer audience gets code-level detail; executive summary uses business-risk framing
