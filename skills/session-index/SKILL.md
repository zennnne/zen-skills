---
name: session-index
description: Generates a monthly session index at ~/.claude/session_log/YYYY/MM/YYYY-MM-INDEX.md — collects title, date, status, and mistake count of every session in the target month into a searchable table. สร้างไฟล์ index สรุป session ของเดือน ใช้ค้นหา session เก่าๆ ได้เร็ว. Triggers on /session-index, "ทำ index เดือนนี้", "รวม session เดือน X", "monthly session index", "session index for [month]".
allowed-tools: "Read Glob Write"
---

## Argument parsing

- `/session-index` (no arg) → เดือนปัจจุบัน
- `/session-index YYYY-MM` → เดือนที่ระบุ
- "ทำ index เดือนนี้" / "รวม session เดือน X" / "monthly session index"

## Path layout

```
~/.claude/session_log/YYYY/MM/
├── YYYY-MM-DD.md            ← daily files (one per day, multiple sessions)
├── YYYY-MM-DD.md
└── YYYY-MM-INDEX.md         ← this skill writes here
```

## Steps

1. **Resolve target month**
   - No arg → ใช้ `Get-Date -Format 'yyyy-MM'` (Windows) หรือ `date +%Y-%m` (macOS/Linux) → split เป็น year/month
   - Arg `YYYY-MM` → ใช้ตามนั้น
   - ถ้าโฟลเดอร์ `~/.claude/session_log/YYYY/MM/` ไม่มี → รายงาน "ไม่มี session ในเดือนนี้" และจบ

2. **Scan daily files**
   - Glob: `~/.claude/session_log/YYYY/MM/YYYY-MM-DD.md` (เรียงตาม date ascending)
   - **ข้าม** `YYYY-MM-INDEX.md` ตัวเอง

3. **Parse แต่ละ daily file** — extract per session:
   - **Date** จากชื่อไฟล์
   - **Time** จาก section header `## Session HH:MM - ...`
   - **Session ID** จาก backtick ใน header (`` `<id>` ``)
   - **Reason** จากใน parentheses ของ header
   - **Title** จาก `- **Title:** ...` ถ้ามี (อาจไม่มี ถ้า summary ยังค้าง)
   - **Status** จาก `- **Status:** ...` (completed/interrupted/blocked/filling)
   - **Mistake count** = จำนวน `- **what:**` ใน section นั้น (ถ้ามี)

4. **Render INDEX file** ตาม format นี้:
   ```markdown
   ---
   month: YYYY-MM
   generated: YYYY-MM-DD HH:mm
   total_sessions: N
   ---
   # Session Index — YYYY-MM

   | Date | Time | Title | Status | Mistakes | Session |
   |------|------|-------|--------|----------|---------|
   | YYYY-MM-DD | HH:MM | <session title> | completed | 1 | [link](YYYY-MM-DD.md) |
   | YYYY-MM-DD | HH:MM | <session title> | completed | 0 | [link](YYYY-MM-DD.md) |
   | ...

   ## Recurring mistake tags
   - `[cli, documentation]` — 2 ครั้ง
   - `[powershell, script-reliability]` — 1 ครั้ง

   ## Stats
   - Total sessions: N
   - Completed: X | Interrupted: Y | Blocked: Z | Pending summary: W
   - Total mistakes recorded: M
   ```

5. **Write file** ที่ `~/.claude/session_log/YYYY/MM/YYYY-MM-INDEX.md` (UTF-8 no BOM)
   - **Overwrite** ถ้ามีไฟล์เดิม (regenerate semantics)

6. **รายงาน user สั้นๆ**
   - "Index เดือน YYYY-MM เขียนแล้ว — N sessions, M mistakes"
   - แสดง path ไฟล์ที่เขียน

## Anti-patterns

- ❌ Index entry แบบที่ Title ยังไม่ filled (`(filling...)`) → ใส่ `_pending_` แทน อย่าเดา
- ❌ เขียน INDEX file ทับ daily file ที่ชื่อใกล้กัน (ตรวจ `INDEX` suffix ก่อนเขียน)
- ❌ Generate index สำหรับเดือนที่ไม่มีไฟล์ — แค่รายงานว่าไม่มี
- ❌ Hallucinate stats — count จากที่อ่านได้จริงเท่านั้น
- ❌ ใส่ link relative path แบบ absolute (`C:/Users/...`) — ใช้ relative `YYYY-MM-DD.md` เพื่อ portable

## Tips

- ถ้ามี session ที่ summary ค้าง (`_(auto-summary failed...)_`) → แสดงใน status column ว่า `pending` และเตือน user ว่า run `/session-summary` ก่อน rebuild index ได้
- Recurring mistake tags useful สำหรับ harvest-insights — pattern ซ้ำหมายถึง memory feedback ที่ควรเพิ่ม
