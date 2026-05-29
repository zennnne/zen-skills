---
name: auditing-security
description: Deep security-focused audit of a codebase using 8 parallel CWE-specialist agents — injection, auth & access control (incl. JWT/session/open-redirect), cryptography & secrets, memory & resource safety, insecure data handling, business-logic & race conditions, configuration & headers (incl. CSP/HSTS/CORS/cookies), and security logging & monitoring. Use ONLY for security-focused work, penetration-style review, OWASP Top 10 compliance check (A01–A10), CVE/CVSS-mapped vulnerability scan, hardening review before a release, or test-quality assessment (FIRST principles, pyramid distribution, mutation score). Produces a CVSS-style risk-scored report with CWE references and prioritized remediation. Works with any language; web-specific checks auto-skipped for non-web codebases. For general bug hunting, error handling review, refactoring opportunities, performance analysis, or "make this project better" — use `reviewing-code` instead (broader scope, includes Mythos-style runtime validation).
allowed-tools: "Read Glob Grep WebSearch Agent"
argument-hint: "[path] [--guidelines <file>]"
---

# Security Auditing

Three-phase multi-agent pipeline: **orchestrate → parallel specialist review → synthesize report**.

Cost: ~15× single-agent token cost. Use when comprehensive security coverage justifies the cost.

## Phase 1: Context Gathering (Orchestrator)

1. **Discover files** — Glob to find source files; prioritize entry points, route definitions, auth layers, config files.
2. **Read key files** — load main source + supporting context:
   - Import/dependency lists (identify dangerous libraries, version pins)
   - Config files (.env, yaml, settings) — spot secrets and insecure defaults
   - Auth middleware / route guards — verify what's protected
   - Schema/model definitions — understand data shapes and trust boundaries
3. **Load user guidelines** — if `--guidelines <file>` provided, read and incorporate into every agent brief as additional review criteria.
4. **Plan with extended thinking** — *(tip: invoke this skill on Opus; Opus-lead + Sonnet-workers outperforms single-Opus ~90% on analysis tasks — orchestrator does the hardest reasoning, specialist agents are well-scoped enough for Sonnet)* — identify:
   - Which of the 7 vulnerability categories are relevant (see `${CLAUDE_SKILL_DIR}/reference.md` §1)
   - Which files belong to which agent's scope (no overlap)
   - High-risk patterns visible at a glance (note them for the orchestrator's own findings)
5. **Write task manifest** — one entry per agent: `{category, files_in_scope, cwe_focus, output_format, model: "sonnet", tool_budget: 6}`

## Phase 2: Parallel Specialist Agents

Spawn all agents in **one assistant turn** (single message = true parallelism). Each owns a non-overlapping vulnerability category:

| Agent | Scope |
|---|---|
| `injection-agent` | SQL injection, XSS, OS command injection, path traversal, SSRF (CWE-89/79/78/22/918) |
| `auth-agent` | Auth bypass, broken access control, CSRF, hard-coded creds, privilege escalation, JWT verification flaws, session fixation, open redirects (CWE-287/862/863/798/352/345/384/601) |
| `crypto-agent` | Weak algorithms (MD5/SHA-1/ECB), insecure random, plaintext secrets, cert validation (CWE-327/330/522) |
| `memory-agent` | Buffer overflow, null deref, use-after-free, integer overflow *(skip for Python/JS unless C extensions)* |
| `data-handling-agent` | Unsafe deserialization, unrestricted file upload, missing input validation (CWE-502/434/20) |
| `logic-agent` | Race conditions, TOCTOU, off-by-one, broken state machines, missing rate limits (CWE-362/367) |
| `config-deps-agent` | Secrets in config, insecure defaults, debug mode in prod, outdated/vulnerable dependencies, missing security headers (CSP/HSTS/X-Frame-Options), cookie flags (Secure/HttpOnly/SameSite), permissive CORS (CWE-1021/614/1004/942) |
| `observability-agent` | Insufficient/missing security logging, sensitive data in logs, log injection, missing audit trail for security events *(skip for libraries or pure CLI tools without persistent runtime)* (CWE-778/532/117/223) |

**Spawn each agent with `model: sonnet`** — specialist agents do well-scoped parallel analysis; Sonnet is sufficient and saves 60–70% cost vs all-Opus.

**Every agent brief must include:**
- Exact files in scope
- CWE IDs for their category (from `reference.md` §1)
- Explicit list of what other agents cover (prevents duplication)
- Chain-of-thought instruction: *reason through the taint path before stating the finding* (reduces false positives significantly)
- Structured JSON output format: `{finding_id, category, cwe, location, severity_estimate, description, evidence, impact, recommendation}`
- Allowed tools: `Read, Glob, Grep, WebSearch` — no file editing
- Tool budget + done condition: *"6 tool calls max; return the JSON array when done — empty array means no findings in scope, not an incomplete review"*

**Optional:** If the codebase has tests, spawn a `test-quality-agent` using the checklist in `reference.md` §3.

**See `${CLAUDE_SKILL_DIR}/examples.md`** for a complete agent brief template and sample JSON output.

## Phase 3: Risk Scoring & Synthesis

After all agents return:

1. **Score each finding** — use hybrid OWASP Likelihood × Impact method from `reference.md` §2:
   - Likelihood (0–9): attack vector, ease of exploit, required privilege
   - Impact (0–9): Confidentiality / Integrity / Availability loss
   - Risk = (Likelihood + Impact) / 2 → map to Critical/High/Medium/Low/Info tier

2. **Deduplicate** — merge findings with the same root cause reported by multiple agents.

3. **Rank** — sort descending by risk score; tiebreak on Availability/Integrity impact.

4. **Synthesize report** using structure from `reference.md` §4:
   - Executive summary (overall risk posture, critical/high count, business impact)
   - Findings summary table (ID, title, severity, location)
   - Detailed findings (evidence + specific remediation per finding)
   - Remediation roadmap: Immediate → Short-term → Long-term

## Web Search During Audit

Each agent calls WebSearch as needed for:
- CVE details and CVSS scores for flagged library versions
- Patch notes or remediation examples for specific CWEs
- Current best practices for a flagged pattern

## Principles

- **Specialized agents > monolithic** — LLM detection rate 90–100% per category; drops with scope overload
- **CoT before conclusion** — mandatory in every brief; reduces false positives significantly
- **Partition at dispatch, not at synthesis** — pre-assigned scopes prevent duplicated findings
- **Opus orchestrator, Sonnet workers** — orchestrator does one-shot decomposition + synthesis (worth Opus); specialists do well-scoped parallel analysis (Sonnet sufficient; saves 60–70% vs all-Opus)
- **LLMs catch semantic/logic bugs SAST misses** — complement with traditional SAST for structural guarantees

## Reference Files

- `${CLAUDE_SKILL_DIR}/reference.md` — §1 vulnerability taxonomy, §2 risk scoring, §3 test quality checklist, §4 report template
- `${CLAUDE_SKILL_DIR}/examples.md` — sample agent brief, sample finding JSON, sample report excerpt
