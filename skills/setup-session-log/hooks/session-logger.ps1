# session-logger.ps1
# Claude Code SessionEnd hook.
#
# Strategy: skeleton-first + detached fill.
#  1. Read JSON from stdin (session metadata).
#  2. Skip trivial sessions (clear/logout, transcript < 5KB).
#  3. Append a SKELETON entry to today's daily log file (with placeholder).
#  4. Spawn session-summarizer.ps1 as a DETACHED background process so the
#     summarization can outlive this hook (SessionEnd is killed at parent exit
#     even with timeout config; see issue #41577).
#  5. Exit 0 immediately.
#
# Daily file layout: ~/.claude/session_log/YYYY/MM/YYYY-MM-DD.md
#
# This script is intentionally ASCII-only. UTF-8 content goes through explicit
# encoding because Windows PowerShell 5.1 can otherwise mangle non-ASCII.

$ErrorActionPreference = 'Stop'

# Recursion guard: if this hook fires inside a `claude -p` child started by
# the summarizer, skip immediately. The summarizer sets this env var before
# spawning claude. (`--bare` would do this too but disables OAuth keychain
# auth, which we rely on for Claude Code subscription users.)
if ($env:CLAUDE_LOGGER_ACTIVE -eq '1') { exit 0 }

try {
    # --- Read stdin as UTF-8 (console code page 874/1252 mangles JSON) ------
    $stdin  = [Console]::OpenStandardInput()
    $reader = New-Object System.IO.StreamReader($stdin, (New-Object System.Text.UTF8Encoding($false)))
    $raw    = $reader.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }

    $data = $raw | ConvertFrom-Json

    $sessionId      = [string]$data.session_id
    $cwd            = [string]$data.cwd
    $reason         = [string]$data.reason
    $transcriptPath = [string]$data.transcript_path
    $now            = Get-Date
    $timestamp      = $now.ToString('yyyy-MM-dd HH:mm')
    $timeOnly       = $now.ToString('HH:mm')
    $dateOnly       = $now.ToString('yyyy-MM-dd')
    $year           = $now.ToString('yyyy')
    $month          = $now.ToString('MM')

    # --- Skip trivial sessions ---------------------------------------------
    if ($reason -in @('clear', 'logout', 'prompt_input_exit')) { exit 0 }

    if ($transcriptPath -and (Test-Path -LiteralPath $transcriptPath)) {
        $size = (Get-Item -LiteralPath $transcriptPath).Length
        if ($size -lt 5000) { exit 0 }

        # Count real user turns (exclude tool_result lines, which also use type:"user").
        # Skip summary entirely if < 5 turns -- saves a Haiku call on trivial sessions.
        $userTurns = 0
        $reader2 = [System.IO.File]::OpenText($transcriptPath)
        try {
            while (-not $reader2.EndOfStream) {
                $line = $reader2.ReadLine()
                if ($line -match '"type":"user"' -and $line -notmatch '"tool_use_id"') {
                    $userTurns++
                }
            }
        } finally { $reader2.Dispose() }
        if ($userTurns -lt 5) { exit 0 }
    }
    # -----------------------------------------------------------------------

    $logRoot   = Join-Path $env:USERPROFILE '.claude\session_log'
    $dayDir    = Join-Path $logRoot (Join-Path $year $month)
    $dailyFile = Join-Path $dayDir ("{0}.md" -f $dateOnly)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)

    if (-not (Test-Path -LiteralPath $dayDir)) {
        New-Item -ItemType Directory -Path $dayDir -Force | Out-Null
    }

    # --- Initialize daily file if missing ----------------------------------
    if (-not (Test-Path -LiteralPath $dailyFile)) {
        $header = @"
---
date: $dateOnly
---
# $dateOnly

"@
        [System.IO.File]::WriteAllText($dailyFile, $header, $utf8NoBom)
    }

    # --- Append skeleton entry (placeholder for summarizer to replace) -----
    # Mutex name must be machine-unique, scoped to this daily file.
    $mutexName = 'Global\ClaudeSessionLog_' + ($dailyFile -replace '[^A-Za-z0-9]', '_')
    $mutex     = New-Object System.Threading.Mutex($false, $mutexName)
    if (-not $mutex.WaitOne(5000)) { exit 0 }

    try {
        $skeleton = @"
## Session $timeOnly - ``$sessionId`` ($reason)
- **CWD:** ``$cwd``
- **Transcript:** ``$transcriptPath``

<!-- placeholder:$sessionId -->

---

"@
        [System.IO.File]::AppendAllText($dailyFile, $skeleton, $utf8NoBom)
    } finally {
        $mutex.ReleaseMutex()
        $mutex.Dispose()
    }

    # --- Spawn detached summarizer ----------------------------------------
    # Start-Process with -WindowStyle Hidden is the Windows equivalent of
    # `nohup ... & disown`. The child outlives the SessionEnd hook even
    # when the parent harness kills the hook process.
    $summarizerScript = Join-Path $env:USERPROFILE '.claude\hooks\session-summarizer.ps1'
    if (Test-Path -LiteralPath $summarizerScript) {
        $childArgs = @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass',
            '-File', $summarizerScript,
            '-TranscriptPath', $transcriptPath,
            '-DailyFile', $dailyFile,
            '-SessionId', $sessionId
        )
        Start-Process -FilePath 'powershell.exe' `
                      -ArgumentList $childArgs `
                      -WindowStyle Hidden `
                      -WorkingDirectory $env:USERPROFILE | Out-Null
    }

    exit 0
} catch {
    try {
        $errPath = Join-Path $env:USERPROFILE '.claude\hooks\session-logger.error.log'
        $msg = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] logger: $($_.Exception.Message)`r`n"
        $utf8NoBomErr = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::AppendAllText($errPath, $msg, $utf8NoBomErr)
    } catch { }
    exit 0
}
