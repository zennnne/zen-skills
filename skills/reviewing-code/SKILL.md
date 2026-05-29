---
name: reviewing-code
description: Comprehensive Mythos-style code review pipeline that finds bugs, errors, performance issues, AND improvement opportunities — broader than pure security audit. File ranking 1-5 by risk → 4 parallel specialist agents (correctness, security high-level, performance, maintainability) → runtime validation oracle (AddressSanitizer for C/C++, pytest+hypothesis for Python, fast-check/jest for JS/TS, miri for Rust, project test suite as fallback) → LLM-as-judge filter → prioritized improvement roadmap mixing bug fixes and refactors. Use when asked to review code, find bugs, hunt errors, improve code quality, look for refactor or performance opportunities, do general QA, assess code health, or "make this project better". Covers logic bugs, error handling, OWASP Top 10, performance (algorithmic complexity, N+1, leaks, blocking I/O), and maintainability smells (duplication, complexity, naming, design). For deep security-only audit with 8 CWE-mapped specialists, use `auditing-security` instead.
allowed-tools: "Read Glob Grep Bash WebSearch Agent"
argument-hint: "[path] [--guidelines <file>] [--scope <all|bugs|security|perf|maint>] [--no-validate]"
---

# Reviewing Code: Multi-Agent QA Pipeline

Four-phase pipeline: **triage → parallel specialists → validation oracle → synthesis**.

Inspired by Anthropic's Mythos workflow (file ranking → hypothesis → dynamic validation → secondary judge → report). Specialized multi-agent setups improve detection F1 by ~19% vs monolithic LLM review.

Cost: ~15× single-agent token cost. Use when comprehensive review justifies the cost.

## Phase 1: Triage (Orchestrator)

Single orchestrator runs sequentially. Goal: scope the work and rank where to look.

1. **Discover files** — Glob source files. Skip `node_modules/`, `.venv/`, `dist/`, generated code, vendored deps.
2. **Read entry points + skeleton** — main, route handlers, CLI entry, public API surface, config files (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`).
3. **Load user guidelines** — if `--guidelines <file>` provided, read it; treat each rule as a custom check every specialist must apply.
4. **Rank each candidate file 1-5** (Mythos pattern — see `${CLAUDE_SKILL_DIR}/reference.md` §1):
   - **5** = parses untrusted input, handles auth/crypto, runs as root, network-facing
   - **4** = trust boundary, parser, deserializer, query builder, file I/O
   - **3** = business logic, state machine, complex algorithm
   - **2** = utility / glue / internal helpers
   - **1** = constants, types, simple definitions
5. **Plan with extended thinking** — for files scored ≥3, decide:
   - Which of the 4 specialists owns it (no overlap)
   - Whether language allows runtime validation (sanitizer / test suite / property test)
   - Any high-leverage patterns visible at-a-glance to record as orchestrator findings
6. **Write task manifest** — one entry per agent: `{specialist, files_in_scope, max_findings, output_format}`

Skip Phase 2 entirely if `--scope` filters out a category. If `--scope=all` (default), spawn all four.

## Phase 2: Parallel Specialists

Spawn all selected agents in **one assistant turn** (single message = true parallelism). Each owns a non-overlapping concern:

| Agent | Concern | Looks for |
|---|---|---|
| `correctness-agent` | Bugs, errors, runtime failures | Off-by-one, null/undefined, race/TOCTOU, wrong condition, swallowed exceptions, missing input validation, unreachable error paths, integer/float traps, unhandled async rejection |
| `security-agent` | Exploitable flaws (OWASP/CWE) | Injection, auth bypass, weak crypto, unsafe deser, SSRF, hardcoded secrets, path traversal, missing authZ, vulnerable deps |
| `performance-agent` | Resource & speed issues | O(n²) where O(n) possible, N+1 queries, redundant allocation, blocking I/O on hot path, leak (handle/file/event listener), missing pagination, sync work in async context |
| `maintainability-agent` | Improvement opportunities | Duplication, dead code, god functions (>50 LOC, cyclomatic >10), confusing names, leaky abstraction, inconsistent error model, missing types, comment rot |

**Every agent brief MUST include:**
- Exact files in scope (from manifest)
- Explicit list of what the OTHER three agents cover (prevents duplicate findings)
- **Chain-of-thought instruction**: *reason through the data flow / control flow before stating the finding* — reduces false positives significantly
- Severity self-estimate (Critical / High / Medium / Low / Info — per `reference.md` §2)
- Structured JSON output: `{finding_id, agent, location, severity_estimate, description, evidence, impact, recommendation, validation_hint}`
- Budget cap: ≤ 8 tool calls, output ≤ 800 words

**Why 4 agents (not 7 like `auditing-security`):** broader scope → must compress taxonomy. Empirically 4 specialists at the right granularity outperform 7+ in cost-per-finding while keeping detection rate. See `reference.md` §1 for the merge mapping.

**See `${CLAUDE_SKILL_DIR}/examples.md`** for full agent brief template + sample JSON.

## Phase 3: Validation Oracle (Mythos-style)

This phase is what separates this skill from naive LLM review. Static-only review hallucinates fixes. Validation kills false positives.

For each Phase 2 finding, run **layered checks** in priority order. Stop at the first that confirms or refutes:

### Layer A — Runtime/Sanitizer (strongest signal)
Use the `validation_hint` from each finding to drive this layer. If the language supports a sanitizer or runtime check (see `reference.md` §3 oracle table):

- **C / C++** — Build with `-fsanitize=address,undefined`, run a minimal repro from the finding. ASan crash with matching report = **CONFIRMED**. No crash on plausible input = **REFUTED**.
- **Python** — Run `pytest -q` on tests touching the file. If `--validate` requests deeper check, generate property-based test with Hypothesis from the finding's evidence and run it.
- **JavaScript / TypeScript** — Run `tsc --noEmit` for type findings; `jest`/`vitest` for tests; `fast-check` properties for invariants.
- **Go** — Run `go test -race`; for memory: `-msan`.
- **Rust** — Run `cargo test`; for unsafe blocks: `miri`.

### Layer B — Existing test suite
For findings without a runtime oracle: run the project's test command (detected from `package.json` / `Makefile` / `pyproject.toml`) on the affected file/module. Crash or new failure = **CONFIRMED**.

### Layer C — Differential check (when reasonable)
If the finding involves a refactor suggestion or alternative implementation, generate both versions and compare outputs across N inputs. Divergence = **CONFIRMED issue with original**.

### Layer D — Secondary LLM judge (always runs as final filter)
Spawn a fresh Sonnet agent (`validator-agent`) with the finding + raw evidence. Ask:
> *"Is this finding (1) real in the current code, (2) actionable as written, (3) impactful enough to ship? Score each 1-5. If any score ≤2, mark REFUTED with reason."*

Validator gets only **Read** access. No tool overlap with the finding's author. This is an evaluator-optimizer loop (max 1 round — no iteration to keep cost bounded).

### Validation outcomes per finding
- **CONFIRMED** (Layer A/B/C crash OR Layer D scores all ≥3) → goes to Phase 4
- **REFUTED** (Layer A/B explicit pass + Layer D score ≤2) → drop, log reason
- **UNVERIFIED** (no oracle available, Layer D ≥3) → keep but mark `confidence: medium`

Use `--no-validate` to skip Phase 3 (faster; expect 30-50% more false positives).

## Phase 4: Synthesis & Report

After validation:

1. **Score each surviving finding** — hybrid OWASP Likelihood × Impact (`reference.md` §2). Risk = (L + I) / 2, mapped to Critical / High / Medium / Low / Info.
2. **Deduplicate** — merge findings with the same root cause (same file + same line range + same root condition).
3. **Group by category** — Bugs / Security / Performance / Maintainability — within each, sort by risk descending.
4. **Synthesize report** (`reference.md` §4):
   - **Executive summary** — overall health, count by severity, top 3 priorities, 1-paragraph business framing
   - **Findings table** — ID, title, category, severity, location, confidence
   - **Detailed findings** — one block per Critical/High; aggregated lists for Medium/Low/Info
   - **Improvement roadmap** — Immediate (next commit) / Short-term (this sprint) / Long-term (architectural). Bug fixes and improvements share the roadmap so the user gets one prioritized list.

## Principles

- **Specialize, don't kitchen-sink** — per-category detection rate 90-100%; drops sharply with scope overload. Use exactly 4 agents.
- **Require CoT before conclusion** in every brief — cuts false positives ~50%.
- **Validate before reporting** — sanitizer / test / property test / judge. Skipping validation = Mythos without the moat.
- **Partition at dispatch, not at synthesis** — assign scopes upfront; cheaper than dedup later.
- **Read-only by default** — no agent has Edit/Write; the skill produces a report only.
- **Treat improvement as first-class** — refactor suggestions live alongside bugs.

## Reference Files

- `${CLAUDE_SKILL_DIR}/reference.md` — §1 file-ranking + agent taxonomy, §2 severity scoring, §3 validation oracle by language, §4 report template
- `${CLAUDE_SKILL_DIR}/examples.md` — sample agent brief, sample finding JSON, sample validator response, sample report excerpt
