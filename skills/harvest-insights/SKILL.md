---
name: harvest-insights
description: Reflect on the current session, extract transferable insights worth keeping, classify each as memory or skill, then ask user per item whether to save. Use at end of significant sessions, or when user says "harvest insights", "distill session", "เก็บ insight จาก session", "อะไรน่าจำจาก session นี้".
allowed-tools: "Read Write Edit AskUserQuestion"
---

# Harvest Insights

Reflects on the current session, classifies findings, and routes each to memory or skill on user approval. When generating skill content, applies `~/.claude/docs/skill-authoring-checklist.md`; escalates to `skill-authoring-rules.md` only on uncertainty.

## Trigger heuristics — when this skill is worth invoking

The skill works best when the session has at least one of these signals (guidance, not strict rules):

- WebSearch / WebFetch happened → external knowledge entered the session
- User explicitly taught Claude something ("จำไว้ว่า...", "ทำแบบนี้นะ", "next time do X")
- User corrected Claude multiple times → patterns to learn
- User pointed Claude at a doc/file → domain knowledge
- A repeated workflow happened → procedure worth crystallizing

If none of these applied, tell the user the session may not have harvest-worthy insights and ask whether to proceed anyway.

## Phase 1: Reflect & list candidates

Walk through the session and extract candidate insights. For each:

- **Insight** — one-sentence claim of the learning
- **Source** — what in the session made it stand out (which message, which tool result, which user correction)
- **Classification** — memory or skill (rules below)
- **Sub-type** — for memory: `user` / `feedback` / `project` / `reference`. For skill: proposed `name`
- **Rationale** — one sentence why this classification

Be selective. The bar: would this improve future sessions if remembered? If unsure, skip.

## Phase 2: Classify (memory vs skill)

Use this boundary:

| Insight type | Goes to | Memory sub-type or notes |
|---|---|---|
| Fact about user (preference, role, identity) | Memory | `user` |
| Feedback / correction the user gave | Memory | `feedback` |
| Project state, decisions, deadlines | Memory | `project` |
| Pointer to external system | Memory | `reference` |
| **How-to procedure, transferable workflow** | **Skill** | propose name |
| **Domain technique reusable across tasks** | **Skill** | propose name |

Rule of thumb: **"what is true?"** → memory. **"how do I do X?"** → skill.

## Phase 3: Per-item approval

For each candidate, use `AskUserQuestion` with options:

- **Save as proposed** (whichever type was classified)
- **Switch type** (memory ↔ skill) and save
- **Skip** (don't save)
- **Edit content first** (user describes change, then save)

Process items one at a time. Don't batch the questions.

## Phase 4: Save approved items

### Memory items

Follow the auto-memory protocol:

1. Memory location: `~/.claude/projects/C--Users-User/memory/`
2. Write content file `<name>.md` with frontmatter:
   ```yaml
   ---
   name: ...
   description: one-line for relevance matching
   metadata:
     type: user | feedback | project | reference
   ---
   ```
3. Add one-line entry to `MEMORY.md` index: `- [Title](file.md) — one-line hook`
4. **Check for existing memory to update** before creating a new file. Don't duplicate
5. For `feedback` and `project` types, structure body as:
   - Lead with the rule/fact
   - **Why:** the reason
   - **How to apply:** when this kicks in

### Skill items

1. Draft SKILL.md applying the **Pre-save checklist** from `~/.claude/docs/skill-authoring-checklist.md`. Escalate per its `Escalation` section only on uncertainty.
2. Run the **Fresh-Claude walkthrough** (from the same file) against one realistic future task that should trigger this skill. Revise on failure.
3. Show draft + walkthrough result to user for confirmation.
4. Save to `~/.claude/skills/<name>/SKILL.md`.

## Phase 5: Report

After all items processed, summarize:
- N saved as memory (broken down by sub-type)
- N saved as skill
- N skipped
- Paths of all new/updated files

## What NOT to harvest

Never save (per memory protocol):
- Code patterns derivable by reading current files
- Git history info
- Debugging recipes — the fix is in the code, the why is in the commit
- Anything already in CLAUDE.md
- Ephemeral conversation state
- One-off task details

If user explicitly asks to save one of these, push back: "this is derivable / ephemeral — what was actually surprising about it?"
