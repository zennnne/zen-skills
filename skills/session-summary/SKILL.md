---
name: session-summary
description: Fills pending placeholders in daily session logs (~/.claude/session_log/YYYY/MM/YYYY-MM-DD.md) by reading the session's .jsonl transcript and synthesizing a structured summary. เติม placeholder ของ session ที่ยังไม่ถูกสรุป. Use when the auto-summarizer failed, or to regenerate an existing summary. Triggers on /session-summary, "สรุป session ที่แล้ว", "เติม log session ก่อนหน้า", "fill session log".
allowed-tools: "Read Edit Glob PowerShell Bash"
---

## Argument parsing

- `/session-summary` (no arg) → fill ทุก placeholder ที่ค้างอยู่ใน daily file ของวันนี้
- `/session-summary YYYY-MM-DD` → fill ทุก placeholder ใน daily file ของวันที่ระบุ
- `/session-summary <session-id>` → fill placeholder ของ session ID เฉพาะตัว
- "สรุป session ที่แล้ว" / "เติม log session ก่อนหน้า"

## Path layout

Daily session log อยู่ที่:
```
~/.claude/session_log/YYYY/MM/YYYY-MM-DD.md
```
แต่ละไฟล์มีหลาย session ของวันนั้น — section แต่ละ session ขึ้นต้นด้วย `## Session HH:MM - \`<session-id>\` (<reason>)`

## Steps

1. **Resolve target file(s)**
   - No arg → daily file ของวันนี้ (`Get-Date -Format 'yyyy-MM-dd'`)
   - Date arg `YYYY-MM-DD` → daily file ของวันนั้น
   - Session-id arg → grep หา session id ใน `~/.claude/session_log/` ทั้งหมด เจอที่ไฟล์ไหน → ใช้ไฟล์นั้น

2. **Identify pending entries**
   - หา section ที่มีบรรทัดประมาณ `_(auto-summary failed ...)_` หรือ `<!-- placeholder:<id> -->` ที่ค้าง
   - ดึง session-id และ transcript path ของแต่ละ entry

3. **For each pending entry: read transcript**
   - Path อยู่ใน metadata `**Transcript:** \`<path>\``
   - ถ้าไฟล์ขนาด > 50KB → อ่านแค่ 30KB ท้าย (50 KB ตรงกับ summarizer limit; tail 30 KB ครอบคลุม activity ล่าสุด)
   - ถ้าไฟล์ไม่มีอยู่จริง → แทน placeholder ด้วย `_(transcript missing -- cannot summarize)_` แล้วข้าม entry นั้น

4. **Synthesize structured body** (ตาม schema เดียวกับ summarizer)
   - Title (≤80 chars, ภาษาไทย)
   - Goal — user ต้องการอะไร
   - What done — bullets 3-5 ข้อ
   - Decisions (ถ้ามี) — context/decision/consequences
   - **Mistakes** — what/why/fix/rule/tags
   - Followup — action items ค้าง
   - Status — completed | interrupted | blocked

5. **Render body** ตาม format นี้:
   ```markdown
   - **Title:** <title>
   - **Status:** <status>

   ### Goal
   <goal>

   ### What done
   - <bullet>

   ### Decisions
   - **Context:** ...
     **Decision:** ...
     **Consequences:** ...

   ### Mistakes
   - **what:** ...
     **why:** ...
     **fix:** ...
     **rule:** ...
     **tags:** [tag1, tag2]

   ### Followup
   - <bullet>
   ```

6. **Replace placeholder in daily file**
   - แทน `_(auto-summary failed ...)_` หรือ `<!-- placeholder:<id> -->` ของ entry นั้นด้วย rendered body
   - **อย่าแตะ entry อื่น** ที่เติมแล้ว
   - Preserve metadata (Session header, CWD, Transcript)

7. **รายงาน user สั้นๆ**
   - "เติมแล้ว N entries ใน <file>" + bullet สรุป mistakes ที่จับได้

## Mistake field — quality bar

เขียน `rule` เป็น **กฎ generalizable** ที่ apply ได้นอกบริบทของ session นี้:

✅ ดี: `verify CLI flag ด้วย --help ก่อนเขียน hook ที่เรียก external CLI`
❌ ไม่ดี: `อย่าใส่ flag ผิดในไฟล์นี้`

## Anti-patterns

- ❌ Hallucinate mistakes ที่ session ไม่มีจริง — ถ้า session ราบรื่น ให้ `mistakes: []`
- ❌ แก้ entry อื่นที่เติมแล้ว
- ❌ อ่าน transcript เกิน 50KB (sample 30KB ท้ายแทน)
- ❌ เติมโดยไม่ verify transcript path
- ❌ เขียน rule generic แบบ "ระวังให้มากขึ้น" — ต้อง actionable
