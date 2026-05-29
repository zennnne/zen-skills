# Code QA Examples

## Contents

- 1 — Sample Agent Brief (injection-agent)
- 2 — Sample Finding JSON Output
- 3 — Sample Executive Summary
- 4 — Remediation Roadmap Example
- 5 — Sample Agent Brief (observability-agent)

## 1. Sample Agent Brief (injection-agent)

```
CONTEXT: You are a security reviewer for a Python Flask REST API codebase.
The orchestrator analyzed the project and assigned you the Injection vulnerability category.

YOUR SLICE — Injection vulnerabilities only:
- SQL injection (CWE-89)
- OS command injection (CWE-78)
- Cross-site scripting / XSS (CWE-79)
- Path traversal (CWE-22)
- Server-side request forgery / SSRF (CWE-918)

OTHER AGENTS HANDLE (do NOT report these):
- Auth bypass, access control, CSRF → auth-agent
- Weak crypto, hardcoded secrets → crypto-agent
- Unsafe deserialization, file upload → data-handling-agent
- Race conditions, business logic → logic-agent
- Config issues, outdated deps → config-deps-agent

FILES TO REVIEW:
- src/routes/user.py
- src/routes/admin.py
- src/db/queries.py

TOOLS: Read, Glob, Grep, WebSearch — read-only; do not edit or write files.

TECHNIQUE — Chain-of-thought FIRST, then the finding:
1. Identify potential entry point (HTTP param / header / body field)
2. Trace propagation (variable assignments, function calls)
3. Check if it reaches a dangerous sink (DB query, shell command, file path, URL fetch)
4. Decide: exploitable? false positive? needs more context?
If unsure, WebSearch the CWE or a CVE for the specific library version.

OUTPUT FORMAT — JSON array:
[
  {
    "finding_id": "INJ-001",
    "category": "Injection",
    "cwe": "CWE-89",
    "location": "src/db/queries.py:45",
    "severity_estimate": "Critical",
    "description": "...",
    "evidence": "...",
    "impact": "...",
    "recommendation": "..."
  }
]

BUDGET: 6 tool calls max.
DONE CONDITION: Return the JSON array. Empty array = no findings in your scope — not an incomplete review. Do not stop without returning valid JSON.
```

---

## 2. Sample Finding JSON Output

```json
[
  {
    "finding_id": "INJ-001",
    "category": "Injection",
    "cwe": "CWE-89",
    "location": "src/db/queries.py:45",
    "severity_estimate": "Critical",
    "description": "User-supplied `username` from the POST /login body is interpolated directly into a SQL query string without parameterization.",
    "evidence": "query = f\"SELECT * FROM users WHERE username = '{username}'\"",
    "impact": "An unauthenticated attacker can bypass login or dump the entire users table via SQLi (e.g., username = \\' OR 1=1 --).",
    "recommendation": "Replace string interpolation with a parameterized query: cursor.execute('SELECT * FROM users WHERE username = %s', (username,)). Apply to all queries in queries.py that accept user input."
  },
  {
    "finding_id": "INJ-002",
    "category": "Injection",
    "cwe": "CWE-22",
    "location": "src/routes/admin.py:112",
    "severity_estimate": "High",
    "description": "File path from the `filename` query parameter is joined with a base directory using os.path.join without sanitization, allowing path traversal.",
    "evidence": "filepath = os.path.join(BASE_DIR, request.args.get('filename'))",
    "impact": "An authenticated admin can read arbitrary files on the server (e.g., /etc/passwd) via filename=../../etc/passwd.",
    "recommendation": "Validate that the resolved path starts with BASE_DIR: resolved = os.path.realpath(filepath); assert resolved.startswith(BASE_DIR). Alternatively, use a whitelist of allowed filenames."
  }
]
```

---

## 3. Sample Executive Summary

```markdown
## Executive Summary

This automated code audit of the Flask API (12 source files, ~2,400 LOC) identified
**3 Critical** and **5 High** findings across 4 vulnerability categories.

The most severe risk is an unauthenticated SQL injection in the login endpoint
(FINDING-INJ-001) that could allow full database exfiltration without credentials.
Immediate remediation of all Critical findings is recommended before the next
production deployment.

| Severity | Count |
|---|---|
| Critical | 3 |
| High | 5 |
| Medium | 7 |
| Low | 4 |
| Info | 2 |
| **Total** | **21** |

**Immediate action required:** INJ-001 (SQL injection, login), AUTH-003 (missing authZ
on /admin/export), CRYPTO-001 (MD5 for password hashing).
```

---

## 4. Remediation Roadmap Example

```markdown
## Remediation Roadmap

### Immediate (before next deploy)
- INJ-001: Parameterize all SQL queries in queries.py
- CRYPTO-001: Replace MD5 with bcrypt for password hashing
- AUTH-003: Add role check middleware to /admin routes

### Short-term (next sprint)
- INJ-002: Add path traversal guard to file download endpoint
- DATA-001: Restrict uploaded file types and scan with antivirus
- CFG-002: Move hardcoded API keys to environment variables

### Long-term (architectural)
- Adopt an ORM (SQLAlchemy) to eliminate raw SQL throughout the codebase
- Implement centralized input validation middleware
- Add dependency scanning to CI pipeline (pip-audit / Dependabot)
```

---

## 5. Sample Agent Brief (observability-agent)

```
CONTEXT: You are a security reviewer for a Node.js Express API codebase.
The orchestrator assigned you the Security Logging & Monitoring category (OWASP A09).

YOUR SLICE — Observability gaps only:
- Insufficient logging of security events (CWE-778) — auth failures, authZ denials, input validation failures
- Sensitive data written to logs (CWE-532) — passwords, tokens, PII, full session IDs
- Log injection (CWE-117) — unsanitized user input concatenated into log lines (CRLF injection)
- Omission of security-relevant context (CWE-223) — auth events missing user ID, IP, or timestamp
- Missing audit trail for privileged actions — admin ops, data exports, permission changes

OTHER AGENTS HANDLE (do NOT report these):
- Auth bypass / JWT / session issues → auth-agent
- Plaintext secrets in source files → crypto-agent
- Missing input validation at the boundary → data-handling-agent
- Missing rate limits → logic-agent
- Insecure config / missing security headers / cookie flags → config-deps-agent

FILES TO REVIEW:
- src/middleware/logger.js
- src/routes/auth.js
- src/services/admin.js
- config/winston.config.js

TOOLS: Read, Glob, Grep, WebSearch — read-only; do not edit or write files.

TECHNIQUE — Chain-of-thought FIRST, then the finding:
1. Enumerate security-relevant events (login success/failure, password change, role change, data export)
2. For each, verify a log statement exists AND contains who / what / when / from-where / outcome
3. Scan log statements for direct interpolation of user input (CRLF injection risk: `\r\n` allows log forgery)
4. Scan for sensitive fields (password, token, ssn, credit_card, authorization header) passed to logger
5. Decide: gap, leak, or injection? false positive if framework auto-redacts (e.g., Pino redact paths)?
If unsure, WebSearch CWE-778, CWE-532, or framework-specific logging guidance.

OUTPUT FORMAT — same JSON schema as other agents (see §2).

BUDGET: 6 tool calls max.
DONE CONDITION: Return the JSON array. Empty array = no findings in your scope — not an incomplete review. Do not stop without returning valid JSON.
```

