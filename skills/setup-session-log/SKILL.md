---
name: setup-session-log
description: Set up the session logging system — auto-summarizes every Claude Code session using Haiku at session end, writing a structured daily log to ~/.claude/session_log/. Run this once on a new machine to activate the system.
---

# Setup Session Log

Installs Zen's session logging system onto this machine. When complete, every Claude Code session will be automatically summarized by Haiku at session end and written to a daily markdown log file.

## What gets installed

- `~/.claude/hooks/session-logger.ps1` — SessionEnd hook: writes skeleton entry + spawns summarizer
- `~/.claude/hooks/session-summarizer.ps1` — Background process: calls Haiku to fill the entry, then Sonnet for a 1-line digest
- `~/.claude/session_log/` — daily log directory (YYYY/MM/YYYY-MM-DD.md)
- SessionEnd hook entry in `~/.claude/settings.json`

## Log format

Each session entry looks like:

```
## Session HH:MM - `<session-id>` (<reason>)
- Title / Status
### Goal
### What done
### Decisions
### Mistakes  ← root cause, fix, generalizable rule
### Followup
```

Daily file: `~/.claude/session_log/YYYY/MM/YYYY-MM-DD.md`

## Steps

**Prerequisites:** Claude Code CLI must be installed and `claude` must be on PATH (needed by the summarizer).

### 1. Copy hook scripts

Read the two scripts from this skill's directory and write them to `~/.claude/hooks/`:

- Source: `~/.claude/plugins/marketplaces/zen-skills/skills/setup-session-log/hooks/session-logger.ps1`
- Source: `~/.claude/plugins/marketplaces/zen-skills/skills/setup-session-log/hooks/session-summarizer.ps1`
- Destination: `~/.claude/hooks/` (create the directory if it doesn't exist)

### 2. Create log directory

Create `~/.claude/session_log/` if it doesn't exist.

### 3. Add SessionEnd hook to settings.json

Read `~/.claude/settings.json`. Add the following under `"hooks"` > `"SessionEnd"` (create the keys if missing). Use the user's actual USERPROFILE path for the script path:

```json
"SessionEnd": [
  {
    "matcher": "",
    "hooks": [
      {
        "type": "command",
        "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"<USERPROFILE>\\.claude\\hooks\\session-logger.ps1\"",
        "timeout": 120
      }
    ]
  }
]
```

Replace `<USERPROFILE>` with the actual path (e.g. `C:\Users\YourName`). Get it by running `$env:USERPROFILE` in PowerShell.

**Important:** If `"hooks"` or `"SessionEnd"` already exists, merge carefully — do not overwrite existing entries.

### 4. Confirm

Tell the user:
- Which files were written
- The exact hook command that was added to settings.json
- That the system will activate on the next Claude Code session

## Related skills

- `/session-summary` — manually backfill a session that the auto-summarizer missed
- `/session-index` — generate monthly index from daily logs
