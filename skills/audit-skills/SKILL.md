---
name: audit-skills
description: Scan personal skills at ~/.claude/skills/, find descriptions with discoverability issues or possible duplicates, propose fixes per item with before/after diff, and apply changes only on user approval. Use when user wants to clean up skills, improve discoverability, or says "audit skills", "review skill quality", "check skill descriptions", "scout skills".
allowed-tools: "Read Write Edit Glob Grep AskUserQuestion"
---

# Audit Skills

Read-only scan + per-item approval workflow. Never auto-modifies. Grounds audit criteria in `~/.claude/docs/skill-authoring-checklist.md`; escalates to full rules/pitfalls only when a red flag needs deeper justification.

## Scope

Four groups, distinguished by edit rights:

- **Personal skills**: `~/.claude/skills/*/SKILL.md` — full audit (quality + remediation, all edits allowed)
- **Plugin skills (invoke-editable)**: every `~/.claude/plugins/marketplaces/**/SKILL.md` **except** `claude-plugins-official` — quality scan; remediation limited to adjusting/disabling self-invocation phrases in `description:` on explicit per-item user approval. Includes `anthropic-agent-skills`, `9arm-skills`, `mattpocock-skills`, `karpathy-skills`, etc.
- **Official skills (read-only)**: `~/.claude/plugins/marketplaces/claude-plugins-official/**/SKILL.md` — scanned ONLY to detect overlap/duplication against outer skills (personal + invoke-editable plugins). **Never edited.** Any resulting fix is applied to the outer counterpart, not the official file.
- **Skip**: plugin cache (`~/.claude/plugins/cache/`), project skills (`.claude/skills/`), anything under `.git/`, and `*/template/SKILL.md`

Detection: `Glob` `~/.claude/skills/*/SKILL.md` and `~/.claude/plugins/marketplaces/**/SKILL.md`, then `Read` each. Classify each marketplace hit by path:
- path contains `claude-plugins-official` → official (read-only) group
- otherwise → plugin (invoke-editable) group
- drop hits under `.git/` or named `template/SKILL.md`

## Phase 1: Load audit criteria

Read `~/.claude/docs/skill-authoring-checklist.md` — covers the 90% case. Use the red-flag tables in Phase 2 to scan.

Escalate to companion docs **only when** a specific finding needs deeper justification:
- Pitfall reasoning (P1–P23 detection/why bad/fix) → `~/.claude/docs/skill-authoring-pitfalls.md`
- "Good description" intuition / writing-style → `~/.claude/docs/skill-authoring-examples.md` §1, §5
- Full rule with sub-cases → `~/.claude/docs/skill-authoring-rules.md` §1, §3, §4, §7, §10

## Phase 2: Scan each SKILL.md

For each personal skill, parse frontmatter and body. Check for red flags.
For plugin skills (invoke-editable), apply the same red-flag checks — but flag auto-invoke triggers specifically.
For official skills (read-only), scan ONLY to collect `name:` + trigger conditions for the Phase 3 overlap comparison — skip the detailed body red-flag pass.

### Description red flags

| Red flag | How to detect |
|---|---|
| Vague verb | Description starts with "Helps with", "Manages", "Handles", "Does", "Provides" |
| 1st person | Contains "I can", "I will", "My ", "we " |
| Too short | < 50 chars |
| Too long | > 1024 chars (technically invalid) |
| Missing WHEN | No "Use when", no "when user", no scenario phrase |
| Missing KEYWORDS | No domain terms a user would actually type |
| Keyword stuffing | List of nouns separated by commas with no prose |
| Forbidden tokens in name | `claude` or `anthropic` in `name:` |
| Auto-invoke trigger + overlap (plugin skills) | Phrases like "proactively whenever", "automatically when" in description — flag ONLY when the auto-invoke scope overlaps with another installed skill (personal OR other plugin). "Trigger on /command-name" is explicit invocation — not auto-invoke, skip. For each flagged case, analyze whether the overlapping skills are functionally substitutable (one can replace the other) or complementary (both should coexist). |

### Body red flags

| Red flag | How to detect | Maps to pitfall |
|---|---|---|
| Body > 500 lines | line count of body | P8 |
| No reference files when body is large | body > 400 lines + no `[...](...)` links | P8 |
| Reference depth > 1 | SKILL.md → A.md → B.md chains | P9 |
| Windows-style paths | backslashes in file refs (`scripts\helper.py`) | P15 |
| Time-sensitive content | inline years (`2024`, `2025`) without "old patterns" wrapper | P16 |
| Too many options without default | multiple "use X or Y or Z" with no preferred pick | P17 |
| Inconsistent terminology | mixed synonyms for same concept (`field` / `box` / `element`) | P18 |
| Second-person voice | `You should`, `you can`, `you need to`, `your task` | P19 |
| MCP tool without server prefix | bare MCP tool name (no `Server:` prefix) | P22 |
| Long reference file without TOC | companion file > 100 lines + no `## Contents` | P23 |

### Bundled script red flags (if `scripts/` exists)

| Red flag | How to detect | Maps to pitfall |
|---|---|---|
| Voodoo constants | magic numbers in scripts without comment justifying value | P20 |
| Punting errors to Claude | scripts that let exceptions propagate without handling | P21 |

## Phase 3: Detect possible duplicates

Heuristics:
- Names sharing core stem (`pdf-extract` vs `extract-pdf`, `review-pr` vs `pr-review`)
- Description keyword overlap > ~60% (rough word-set comparison)
- Same `paths:` or `allowed-tools:` patterns

For each suspect pair, **read both fully** to judge whether scope actually differs. Don't auto-merge.

Also run these heuristics **cross-group**: compare each official skill against outer skills (personal + invoke-editable plugins). When an overlap involves an official skill, the fix can ONLY touch the outer side — never the official file (e.g. `claude-plugins-official/.../skill-creator` overlapping personal `skill-creator` → propose editing the personal one's description; leave official untouched).

## Phase 4: Generate report

Output a structured report before any approval:

```
=== Skills Audit Report ===
Scanned: N personal skills at ~/.claude/skills/
         N invoke-editable plugin skills at ~/.claude/plugins/marketplaces/ (excl. claude-plugins-official)
         N official skills (read-only) at ~/.claude/plugins/marketplaces/claude-plugins-official/

== Description issues (personal skills) ==
1. [skill-name] — issue type
   Current: "..."
   Proposed: "..."
2. ...

== Body issues (personal skills) ==
1. [skill-name] — body too long (XXX lines)
   Suggestion: split into reference.md + examples.md

== Possible duplicates (personal skills) ==
1. [skill-a] vs [skill-b]
   Overlap: ...
   Proposed action: merge / clarify scope / keep separate

== Plugin skill issues (invoke-editable) ==
1. [plugin-name/skill-name] — auto-invoke overlaps with [other-skill-name]
   Current description: "..."
   Auto-invoke phrases: ["proactively whenever...", ...]
   Overlaps with: [skill name + their trigger conditions]
   Functional analysis: [substitutable (one replaces the other) OR complementary (both serve distinct purposes)]
   Available actions: adjust invoke conditions (narrow scope) / disable self-invocation entirely / skip

== Official-plugin overlaps (read-only) ==
1. [claude-plugins-official/.../skill-name] overlaps outer [group/skill-name]
   Official side: read-only — NOT editable
   Outer counterpart: [personal or invoke-editable plugin skill + its trigger conditions]
   Overlap: ...
   Proposed action (outer side only): edit outer description / narrow outer invoke / skip
```

## Phase 5: Per-item approval

For EACH issue, check skill type first, then use `AskUserQuestion`:

**If personal skill**, options:
- **Apply proposed fix**
- **Skip** (leave as-is)
- **Edit a custom version first** (user describes change)
- **Show full SKILL.md** before deciding

**If plugin skill** (third-party — body edits disallowed; only self-invocation control is in scope), options:
- **Adjust invoke conditions** — narrow the auto-invoke trigger so overlap is removed (edit only trigger phrases in description); appropriate when both skills serve distinct purposes and should coexist
- **Disable self-invocation entirely** — remove all auto-invoke phrases; appropriate when the overlapping skill is functionally substitutable
- **Skip** — no real overlap, or overlap is intentional

For duplicate pairs (personal skills only), options:
- **Merge into one** (show merged draft first)
- **Keep both, clarify scope** (suggest description edits to both)
- **Skip**

**If official-plugin overlap** (official side is read-only; only the outer counterpart can change), options:
- **Edit outer description** — clarify the outer skill's scope so it no longer overlaps
- **Narrow outer invoke** — tighten the outer skill's auto-invoke phrases (only if outer is personal or invoke-editable plugin)
- **Skip** — overlap is intentional or harmless

No option ever edits a file under `claude-plugins-official`.

Process one at a time. Don't batch.

## Phase 6: Apply approved changes

All edits target personal skills or invoke-editable plugin skills only. Official skills under `claude-plugins-official` are read-only — any overlap fix is applied to the outer counterpart instead.

### For description fixes (personal skills)

- Use `Edit` to replace only the `description:` line in frontmatter
- Verify YAML still valid after edit (no broken multi-line strings)
- Confirm written path

### For body splits (personal skills)

- Show user the proposed split first (which sections go to which file)
- On approval: write new reference files, edit SKILL.md to slim down with references

### For merges (personal skills)

- Show merged SKILL.md draft first
- On approval: write merged skill at chosen name, then mention to user that originals can be deleted manually
- **Do NOT auto-delete folders.** User decides

### For plugin skill invoke condition adjustment (on explicit approval only)

- Use `Edit` to replace only the `description:` line in frontmatter
- Narrow ONLY the auto-invoke phrases (e.g., restrict "proactively whenever the user asks to review anything" to "proactively when the user explicitly asks to scrutinize or question scope") so it no longer overlaps
- DO NOT alter any other content (body, name, allowed-tools, etc.)
- Confirm written path

### For plugin skill self-invocation disable (on explicit approval only)

- Use `Edit` to replace only the `description:` line in frontmatter
- Remove ONLY trigger/auto-invoke phrases (e.g., "proactively whenever...", "automatically when...")
- DO NOT alter any other content (body, name, allowed-tools, etc.)
- Confirm written path

## Safety rules

- NEVER modify invoke-editable plugin skill content (body, name, frontmatter fields other than description)
- For invoke-editable plugin skills: ONLY allowed edit is modifying auto-invoke trigger phrases in `description:` field (narrowing or removing) — and ONLY when there is real overlap with another installed skill, and ONLY on explicit per-item user approval. This now includes `anthropic-agent-skills` (treated as a normal invoke-editable plugin, no longer skipped)
- NEVER edit ANY file under `claude-plugins-official` — not even `description:`. It is read-only and scanned solely to detect overlap with outer skills; fix the outer counterpart instead
- All other modifications: personal skills only (`~/.claude/skills/`)
- NEVER auto-fix without explicit per-item approval
- NEVER delete a skill folder, even on merge — let user delete manually
- If unsure whether to flag, err on side of NOT flagging (false positives waste user time)
- Show before/after diff for every change

## Final report

Summarize at the end:
- N personal skills scanned, N invoke-editable plugin skills scanned, N official skills scanned (read-only)
- N issues found
- N fixes applied
- N skipped
- N merges performed (with new merged skill names)
- Paths of all modified files
