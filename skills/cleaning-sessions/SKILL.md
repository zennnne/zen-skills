---
name: cleaning-sessions
description: Deletes Claude Code session transcript files (JSONL) older than a user-chosen number of days, freeing disk space. Use when accumulated sessions are taking up disk, or during periodic housekeeping. User must invoke explicitly — never auto-runs. Triggers on "clean sessions", "delete old sessions", "clear session history", "purge old conversations", "remove old transcripts", "ล้าง session", "ลบ session เก่า", "เคลียร์ session".
disable-model-invocation: true
argument-hint: "[days]"
arguments: [days]
allowed-tools: "PowerShell AskUserQuestion"
---

# Cleaning Sessions

Removes Claude Code session JSONL files older than **N days** from the Claude config directory. Frees disk space without touching memory files, skills, or settings.

## What gets deleted

- `~/.claude/projects/<project-dir>/<session-uuid>.jsonl` — session transcripts
- Filtered by `LastWriteTime` older than N days

## What is preserved

- `memory/` subdirectories and all `.md` files
- `settings.json`, `CLAUDE.md`, skills
- Tool-result spill files (`<session-id>/tool-results/`) — left intact

---

## Workflow

### Step 1 — Resolve N days

If `$days` argument was passed, use it. Otherwise ask the user how many days (suggest **30** — keeps ~1 month of history while reclaiming older storage).

### Step 2 — Scan (dry run)

```powershell
$claudeDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { "$env:USERPROFILE\.claude" }
$projectsDir = Join-Path $claudeDir "projects"
$cutoff = (Get-Date).AddDays(-[int]$days)

$targets = Get-ChildItem -Path "$projectsDir\*\*.jsonl" -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoff }

$count = $targets.Count
$sizeKB = [math]::Round(($targets | Measure-Object -Property Length -Sum).Sum / 1KB, 1)
Write-Output "Sessions to delete: $count files, $sizeKB KB"
```

Report count and size. If count = 0, tell user nothing to delete and stop.

### Step 3 — Confirm

Ask the user to confirm deletion of **$count files** ($sizeKB KB). Stop if they cancel.

### Step 4 — Delete

```powershell
$targets | Remove-Item -Force
Write-Output "Deleted $count session file(s) — $sizeKB KB freed"
```

---

## Platform paths

| OS | Default path |
|----|-------------|
| Windows | `$env:USERPROFILE/.claude/projects/` |
| macOS | `~/Library/Application Support/Claude/projects/` |
| Linux | `~/.config/claude-desktop/projects/` |

Override with `$CLAUDE_CONFIG_DIR` env var if set.

---

## Notes

- Never delete sessions while Claude Code is actively running in another terminal.
- Do not clean `history.jsonl` or `file-history/` snapshots — they are not session transcripts.
