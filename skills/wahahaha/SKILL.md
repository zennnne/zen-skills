---
name: wahahaha
description: New machine onboarding wizard. Introduces zen-skills PDF catalogs, sets up session logging, installs recommended external plugins one by one, verifies everything, then self-destructs by deleting itself and /setup-session-log. Run once after installing zen-skills on a new machine.
---

# Wahahaha — Onboarding Wizard

One-time setup wizard for a new machine. Walk the user through each step interactively, asking before doing anything. After completion, this skill deletes itself.

## Step 0 — แนะนำ PDF Catalogs

ก่อนเริ่ม แนะนำ reference materials ให้ user รู้จักก่อน:

> "สวัสดีค่ะ! ก่อนเริ่ม onboarding มี catalog ให้อ่านประกอบได้เลยนะคะ:
>
> 📖 **zen-skills-catalog.pdf** — รวม skills ทั้งหมด พร้อม tier rating, วิธีใช้ และ career tags (ดาวน์โหลดได้จาก repo)
> 📋 **zen-session_log-detail.pdf** — รายละเอียด session log system
>
> ถ้างงตรงไหนระหว่าง setup เปิดดู PDF ได้เลยค่ะ เริ่มกันเลยนะคะ!"

จากนั้นดำเนินการ Step 1 ต่อได้เลย ไม่ต้องรอ user ตอบ

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

## Step 3 — Verification

หลังติดตั้ง plugins ทุกตัวแล้ว ตรวจสอบ:

1. อ่าน `~/.claude/settings.json` อีกครั้ง ตรวจว่า `enabledPlugins` มี plugins ที่ user เลือกครบ
2. ถ้า session log ถูกติดตั้ง ตรวจว่า hook `SessionStop` มีอยู่ใน `settings.json`
3. แจ้ง user ถ้าพบปัญหา หรือมี manual step ที่ยังค้างอยู่

## Step 4 — Summary

แสดง summary สั้นๆ ว่าติดตั้งอะไรไปแล้ว และ skip อะไรบ้าง ถ้ามี manual step ค้างให้แสดง list ชัดเจน

## Step 5 — Self-destruct

หลัง summary เสร็จ แจ้ง user และขอยืนยันก่อน:

> "Onboarding เสร็จแล้วค่ะ! /wahahaha และ /setup-session-log เป็น one-time tools จะลบตัวเองออกเพื่อ keep skills ให้ clean
> ยืนยันลบไหมคะ? (ใช่/ไม่)"

- **ใช่** →
  1. หา skill folders ใน paths ต่อไปนี้แล้วลบ:
     - `~/.claude/skills/wahahaha/`
     - `~/.claude/skills/setup-session-log/`
     - `~/.claude/plugins/*/skills/wahahaha/` (ถ้ามี)
     - `~/.claude/plugins/*/skills/setup-session-log/` (ถ้ามี)
  2. แจ้ง user: "ลบแล้วค่ะ! Restart Claude Code เพื่อให้ changes มีผลนะคะ ✨"
- **ไม่** → skip, จบ wizard ตามปกติ
