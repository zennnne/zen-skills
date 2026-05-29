---
name: updating-plugins
description: Updates all 4 Claude Code plugins to latest. karpathy-skills & document-skills use `claude plugin update`. 9arm-skills & mattpocock-skills do selective update (installed skills only) + report new uninstalled skills with last-updated date. Triggers on /update-plugins, /updating-plugins, "อัปเดต plugin", "อัปเดต skill", "update plugins".
allowed-tools: "Bash PowerShell Read"
---

## Plugin inventory

| Plugin | Marketplace | Source | Marketplace dir |
|--------|-------------|--------|-----------------|
| `andrej-karpathy-skills` | `karpathy-skills` | GitHub (Claude-managed) | `~/.claude/plugins/marketplaces/karpathy-skills` |
| `document-skills` | `anthropic-agent-skills` | GitHub (Claude-managed) | `~/.claude/plugins/marketplaces/anthropic-agent-skills` |
| `9arm-skills` | `9arm-skills` | Local git repo → `https://github.com/thananon/9arm-skills` | `~/.claude/plugins/marketplaces/9arm-skills` |
| `mattpocock-skills` | `mattpocock-skills` | Local dir (no git) → `https://github.com/mattpocock/skills` | `~/.claude/plugins/marketplaces/mattpocock-skills` |

---

## Step 1 — karpathy-skills & document-skills

Run via Bash:
```
claude plugin update andrej-karpathy-skills@karpathy-skills
claude plugin update document-skills@anthropic-agent-skills
```
Report success or error for each.

---

## Step 2 — 9arm-skills (selective update)

**Marketplace dir:** `~/.claude/plugins/marketplaces/9arm-skills`

**Currently installed skills** (from `plugin.json`):
- `skills/engineering/debug-mantra`
- `skills/engineering/post-mortem`
- `skills/engineering/scrutinize`
- `skills/productivity/management-talk`

### 2a. Fetch remote (no merge)
```bash
git -C ~/.claude/plugins/marketplaces/9arm-skills fetch origin
```

### 2b. Selective update — installed skills only
For each path listed above:
```bash
git -C ~/.claude/plugins/marketplaces/9arm-skills checkout FETCH_HEAD -- <skill-path>
```
Do NOT do `git pull` — that would merge all remote content including new skills. After selective checkout, HEAD will differ from remote — this is expected.

### 2c. Discover new/uninstalled skills
List skill dirs from remote in the public buckets only (`engineering/`, `productivity/`, `misc/`):
```bash
git -C ~/.claude/plugins/marketplaces/9arm-skills ls-tree --name-only FETCH_HEAD skills/engineering/
git -C ~/.claude/plugins/marketplaces/9arm-skills ls-tree --name-only FETCH_HEAD skills/productivity/
git -C ~/.claude/plugins/marketplaces/9arm-skills ls-tree --name-only FETCH_HEAD skills/misc/ 2>/dev/null
```
Cross-reference with installed list. For each skill NOT in `plugin.json`, get last updated date:
```bash
git -C ~/.claude/plugins/marketplaces/9arm-skills log FETCH_HEAD --format="%cd" --date=short -1 -- <skill-path>
```

### 2d. Refresh plugin cache
```bash
claude plugin update 9arm-skills@9arm-skills
```
If command not found or fails, note "cache ไม่ได้ refresh — restart Claude Code เพื่อ apply"

---

## Step 3 — mattpocock-skills (selective update)

**Marketplace dir:** `~/.claude/plugins/marketplaces/mattpocock-skills`
**Source repo:** `https://github.com/mattpocock/skills`

**Currently installed skills** (from `plugin.json`):
- `skills/engineering/diagnose`
- `skills/engineering/grill-with-docs`
- `skills/engineering/improve-codebase-architecture`
- `skills/engineering/prototype`
- `skills/engineering/tdd`
- `skills/engineering/to-prd`
- `skills/engineering/zoom-out`
- `skills/productivity/caveman`
- `skills/productivity/grill-me`
- `skills/productivity/handoff`
- `skills/productivity/write-a-skill`

### 3a. Clone to temp dir
```powershell
$tempDir = "$env:TEMP/mattpocock-update-$(Get-Random)"
git clone --depth 1 https://github.com/mattpocock/skills $tempDir
```

### 3b. Verify structure
Check that `$tempDir/skills/` exists. If not → abort and warn: "repo structure อาจเปลี่ยน — ต้อง update manual"

### 3c. Selective copy — installed skills only
For each installed skill path:
```powershell
$src = "$tempDir/<skill-path>"
$dst = "~/.claude/plugins/marketplaces/mattpocock-skills/<skill-path>"
if (Test-Path $src) {
    Copy-Item -Recurse -Force $src (Split-Path $dst -Parent)
}
```
Do NOT copy `.claude-plugin/` from temp — ใช้ metadata เดิม.

### 3d. Discover new/uninstalled skills
List all skill dirs in `$tempDir/skills/engineering/` and `$tempDir/skills/productivity/` (or other buckets if present). Cross-reference with installed list. For each new skill, get last commit date from temp repo:
```bash
git -C $tempDir log --format="%cd" --date=short -1 -- <skill-path>
```

### 3e. Cleanup temp
```powershell
Remove-Item -Recurse -Force $tempDir
```

### 3f. Refresh plugin cache
```bash
claude plugin update mattpocock-skills@mattpocock-skills
```
If fails, note "restart Claude Code เพื่อ apply"

---

## Step 4 — Final report

Print summary:

```
Plugin update summary
─────────────────────────────────────────
✅ andrej-karpathy-skills  — updated
✅ document-skills         — updated
✅ 9arm-skills             — N skills updated
   🆕 New (not installed):
      - <skill-name>  last updated YYYY-MM-DD
✅ mattpocock-skills       — N skills updated
   🆕 New (not installed):
      - <skill-name>  last updated YYYY-MM-DD

⚠️  Restart Claude Code เพื่อให้ plugin update มีผล
```

---

## Anti-patterns

- ❌ `git pull` ตรงๆ ใน 9arm — จะ merge new skills เข้า plugin.json โดยไม่ตั้งใจ
- ❌ Copy `.claude-plugin/marketplace.json` หรือ `plugin.json` จาก temp — metadata เดิมต้องคงไว้
- ❌ นับ skills จาก `skills/personal/`, `skills/in-progress/`, `skills/deprecated/` ว่าเป็น "new" — buckets พวกนี้ไม่ expose
- ❌ ข้าม step report ถ้าไม่มี new skills — ให้บอก "ไม่มี skill ใหม่" แทน
