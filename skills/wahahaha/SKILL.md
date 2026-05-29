---
name: wahahaha
description: New machine onboarding wizard. Walks through setting up session logging and installing recommended external plugins one by one. Run once after installing zen-skills on a new machine.
---

# Wahahaha — Onboarding Wizard

Welcome setup wizard for a new machine. Walk the user through each component interactively, asking before doing anything.

## Step 1 — Session log system

Ask the user:

> "อยากติดตั้ง session log system ไหม? (auto-summarize ทุก session ด้วย Haiku → เก็บเป็น daily log ที่ ~/.claude/session_log/)"

- **ใช่** → invoke the `/setup-session-log` skill immediately
- **ไม่** → skip, move to step 2

## Step 2 — External plugins

Check which plugins are already installed by reading `~/.claude/settings.json` and looking at the `enabledPlugins` object.

Then for each plugin below **that is NOT already in enabledPlugins**, ask the user one at a time:

---

### andrej-karpathy-skills
**Marketplace:** `karpathy-skills` (GitHub: `multica-ai/andrej-karpathy-skills`)

> "อยากลง `andrej-karpathy-skills` ไหม? → behavioral guidelines ลด LLM coding mistakes (think before coding, surgical changes, simplicity first)"

- **ใช่** → try: `/plugin install andrej-karpathy-skills@zen-skills`
  - If error "plugin not found" or source resolution fails → tell user to run manually:
    ```
    /plugin marketplace add multica-ai/andrej-karpathy-skills
    /plugin install andrej-karpathy-skills@karpathy-skills
    ```
- **ไม่** → skip

---

### mattpocock-skills
**Marketplace:** `mattpocock-skills` (GitHub: `mattpocock/skills`)

> "อยากลง `mattpocock-skills` ไหม? → TypeScript, TDD, PRD, prototype, architecture skills จาก Matt Pocock"

- **ใช่** → try: `/plugin install mattpocock-skills@zen-skills`
  - If error → tell user to run manually:
    ```
    /plugin marketplace add mattpocock/skills
    /plugin install mattpocock-skills@mattpocock-skills
    ```
- **ไม่** → skip

---

### anthropic-skills (document-skills)
**Marketplace:** `anthropic-agent-skills` (GitHub: `anthropics/skills`)

> "อยากลง `document-skills` ไหม? → official Anthropic skills สำหรับ Excel, Word, PowerPoint, PDF, web artifacts, canvas design และอื่นๆ"

- **ใช่** → try: `/plugin install anthropic-skills@zen-skills`
  - If error → tell user to run manually:
    ```
    /plugin marketplace add anthropics/skills
    /plugin install document-skills@anthropic-agent-skills
    ```
- **ไม่** → skip

---

### 9arm-skills
**Marketplace:** `9arm-skills` (GitHub: `thananon/9arm-skills`)

> "อยากลง `9arm-skills` ไหม? → debug mantra, post-mortem, scrutinize, management talk skills จาก 9arm"

- **ใช่** → try: `/plugin install 9arm-skills@zen-skills`
  - If error → tell user to run manually:
    ```
    /plugin marketplace add thananon/9arm-skills
    /plugin install 9arm-skills@9arm-skills
    ```
- **ไม่** → skip

---

## Step 3 — Summary

After all steps, show a summary of what was installed and what was skipped. If any manual steps are needed, list them clearly at the end.
