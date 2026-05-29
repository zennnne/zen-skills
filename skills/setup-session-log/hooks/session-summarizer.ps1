# session-summarizer.ps1
# Background fill script spawned by session-logger.ps1.
#
# Reads the transcript (last 30KB), calls `claude --bare -p` with a JSON
# schema to extract a structured summary, then replaces the placeholder
# inside the daily log file with the rendered markdown body.
#
# Recursion guard:
#   - Sets CLAUDE_LOGGER_ACTIVE=1 before spawning the child claude process.
#   - session-logger.ps1 checks this var at entry and exits 0 immediately.
#   - Note: --bare is intentionally NOT used (it disables OAuth keychain auth).
#
# This script is intentionally ASCII-only.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$TranscriptPath,
    [Parameter(Mandatory=$true)] [string]$DailyFile,
    [Parameter(Mandatory=$true)] [string]$SessionId
)

$ErrorActionPreference = 'Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-LoggerError {
    param([string]$Message)
    try {
        $errPath = Join-Path $env:USERPROFILE '.claude\hooks\session-logger.error.log'
        $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] summarizer($SessionId): $Message`r`n"
        [System.IO.File]::AppendAllText($errPath, $line, $utf8NoBom)
    } catch { }
}

function Replace-Placeholder {
    param([string]$Body)

    $mutexName = 'Global\ClaudeSessionLog_' + ($DailyFile -replace '[^A-Za-z0-9]', '_')
    $mutex     = New-Object System.Threading.Mutex($false, $mutexName)
    if (-not $mutex.WaitOne(10000)) {
        Write-LoggerError "mutex timeout -- skipping placeholder replace"
        return
    }

    try {
        $content     = [System.IO.File]::ReadAllText($DailyFile, $utf8NoBom)
        $placeholder = "<!-- placeholder:$SessionId -->"
        if ($content.Contains($placeholder)) {
            $content = $content.Replace($placeholder, $Body)
            [System.IO.File]::WriteAllText($DailyFile, $content, $utf8NoBom)
        } else {
            Write-LoggerError "placeholder not found in $DailyFile"
        }
    } finally {
        $mutex.ReleaseMutex()
        $mutex.Dispose()
    }
}

function Append-Digest {
    param([string]$DigestLine)

    if ([string]::IsNullOrWhiteSpace($DigestLine)) { return }

    $projectKey = ($env:USERPROFILE -replace ':', '-') -replace '\\', '-'
    $digestFile = Join-Path $env:USERPROFILE ".claude\projects\$projectKey\memory\auto\recent_digest.md"
    if (-not (Test-Path -LiteralPath $digestFile)) { return }

    $shortId   = if ($SessionId.Length -ge 8) { $SessionId.Substring(0, 8) } else { $SessionId }
    $stamp     = (Get-Date).ToString('yyyy-MM-dd HH:mm')
    $cleanLine = $DigestLine -replace '[\r\n]+', ' '
    $newEntry  = "- $stamp | ``$shortId`` | $cleanLine"

    $mutexName = 'Global\ClaudeSessionLog_digest'
    $mutex     = New-Object System.Threading.Mutex($false, $mutexName)
    if (-not $mutex.WaitOne(10000)) {
        Write-LoggerError "mutex timeout -- skipping digest append"
        return
    }

    try {
        $content   = [System.IO.File]::ReadAllText($digestFile, $utf8NoBom)
        $startTag  = '<!-- digest:start -->'
        $endTag    = '<!-- digest:end -->'
        $startIdx  = $content.IndexOf($startTag)
        $endIdx    = $content.IndexOf($endTag)
        if ($startIdx -lt 0 -or $endIdx -lt 0) { return }

        $blockStart = $startIdx + $startTag.Length
        $existing   = $content.Substring($blockStart, $endIdx - $blockStart).Trim()

        # Rotate: keep only entries < 7 days old.
        $cutoff = (Get-Date).AddDays(-7)
        $keep   = New-Object System.Collections.Generic.List[string]
        foreach ($line in $existing -split "`r?`n") {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $m = [regex]::Match($line, '^- (\d{4}-\d{2}-\d{2} \d{2}:\d{2})')
            if ($m.Success) {
                $entryDate = [DateTime]::ParseExact($m.Groups[1].Value, 'yyyy-MM-dd HH:mm', $null)
                if ($entryDate -ge $cutoff) { $keep.Add($line) }
            }
        }
        $keep.Add($newEntry)

        $newBlock = "`r`n" + ($keep -join "`r`n") + "`r`n"
        $newContent = $content.Substring(0, $blockStart) + $newBlock + $content.Substring($endIdx)
        [System.IO.File]::WriteAllText($digestFile, $newContent, $utf8NoBom)
    } finally {
        $mutex.ReleaseMutex()
        $mutex.Dispose()
    }
}

function Append-ExtractedFeedback {
    param($Feedback)

    if (-not $Feedback -or $Feedback.Count -eq 0) { return }

    $projectKey   = ($env:USERPROFILE -replace ':', '-') -replace '\\', '-'
    $feedbackFile = Join-Path $env:USERPROFILE ".claude\projects\$projectKey\memory\auto\extracted_mistakes.md"
    $stamp = (Get-Date).ToString('yyyy-MM-dd HH:mm')

    $mutexName = 'Global\ClaudeSessionLog_extracted'
    $mutex     = New-Object System.Threading.Mutex($false, $mutexName)
    if (-not $mutex.WaitOne(10000)) {
        Write-LoggerError "mutex timeout -- skipping extracted feedback append"
        return
    }

    try {
        $sb = New-Object System.Text.StringBuilder
        foreach ($f in $Feedback) {
            if (-not $f.rule) { continue }
            [void]$sb.AppendLine("## $stamp - $($f.topic)")
            [void]$sb.AppendLine("- **Rule:** $($f.rule)")
            [void]$sb.AppendLine("- **Why:** $($f.why)")
            [void]$sb.AppendLine("- **Source session:** ``$SessionId``")
            [void]$sb.AppendLine("")
        }
        if ($sb.Length -eq 0) { return }

        $fileHeader = @"
---
name: Extracted mistakes (auto)
description: High-importance mistakes auto-extracted by Haiku from session transcripts. Lower trust than manual feedback files — verify rule still applies before relying on it.
type: feedback
---
# Extracted mistakes (auto)

> Auto-extracted rules from session transcripts. Entries older than 180 days are pruned automatically.
> Each entry: timestamp, topic, rule, why. Verify before applying — Haiku may misjudge importance.

"@

        if (-not (Test-Path -LiteralPath $feedbackFile)) {
            [System.IO.File]::WriteAllText($feedbackFile, $fileHeader + $sb.ToString(), $utf8NoBom)
            return
        }

        # Rotate: keep entries newer than 180 days.
        $cutoff      = (Get-Date).AddDays(-180)
        $content     = [System.IO.File]::ReadAllText($feedbackFile, $utf8NoBom)
        $firstEntryM = [regex]::Match($content, '(?m)^## \d{4}-\d{2}-\d{2}')
        $preamble    = if ($firstEntryM.Success) { $content.Substring(0, $firstEntryM.Index) } else { $fileHeader }
        $entriesText = if ($firstEntryM.Success) { $content.Substring($firstEntryM.Index) } else { '' }

        $kept = New-Object System.Text.StringBuilder
        foreach ($block in [regex]::Split($entriesText, '\r?\n(?=## \d{4}-\d{2}-\d{2})')) {
            if ([string]::IsNullOrWhiteSpace($block)) { continue }
            $m = [regex]::Match($block, '^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2})')
            if ($m.Success) {
                $keep = $true
                try { $keep = ([DateTime]::ParseExact($m.Groups[1].Value, 'yyyy-MM-dd HH:mm', $null) -ge $cutoff) } catch {}
                if ($keep) { [void]$kept.Append($block.TrimEnd()); [void]$kept.Append("`r`n`r`n") }
            }
        }
        [void]$kept.Append($sb.ToString())
        [System.IO.File]::WriteAllText($feedbackFile, $preamble + $kept.ToString(), $utf8NoBom)
    } finally {
        $mutex.ReleaseMutex()
        $mutex.Dispose()
    }
}

function Render-Body {
    param($Parsed)

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("- **Title:** " + $Parsed.title)
    if ($Parsed.goal) {
        [void]$sb.AppendLine("- **Status:** " + $Parsed.status)
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("### Goal")
        [void]$sb.AppendLine($Parsed.goal)
    } else {
        [void]$sb.AppendLine("- **Status:** " + $Parsed.status)
    }

    if ($Parsed.what_done -and $Parsed.what_done.Count -gt 0) {
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("### What done")
        foreach ($item in $Parsed.what_done) {
            [void]$sb.AppendLine("- $item")
        }
    }

    if ($Parsed.decisions -and $Parsed.decisions.Count -gt 0) {
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("### Decisions")
        foreach ($d in $Parsed.decisions) {
            [void]$sb.AppendLine("- **Context:** $($d.context)")
            [void]$sb.AppendLine("  **Decision:** $($d.decision)")
            [void]$sb.AppendLine("  **Consequences:** $($d.consequences)")
        }
    }

    if ($Parsed.mistakes -and $Parsed.mistakes.Count -gt 0) {
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("### Mistakes")
        foreach ($m in $Parsed.mistakes) {
            [void]$sb.AppendLine("- **what:** $($m.what)")
            [void]$sb.AppendLine("  **why:** $($m.why)")
            [void]$sb.AppendLine("  **fix:** $($m.fix)")
            [void]$sb.AppendLine("  **rule:** $($m.rule)")
            if ($m.tags -and $m.tags.Count -gt 0) {
                [void]$sb.AppendLine("  **tags:** [" + ($m.tags -join ', ') + "]")
            }
        }
    }

    if ($Parsed.followup -and $Parsed.followup.Count -gt 0) {
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("### Followup")
        foreach ($item in $Parsed.followup) {
            [void]$sb.AppendLine("- $item")
        }
    }

    return $sb.ToString().TrimEnd()
}

try {
    # --- Read transcript (last 30KB) ---------------------------------------
    if (-not (Test-Path -LiteralPath $TranscriptPath)) {
        Replace-Placeholder "_(auto-summary failed -- transcript missing -- run /session-summary $SessionId)_"
        exit 0
    }

    $rawBytes = [System.IO.File]::ReadAllBytes($TranscriptPath)
    # 15KB transcript -- keeps input tokens low (~50% cheaper vs 30KB).
    $maxBytes = 15000
    if ($rawBytes.Length -gt $maxBytes) {
        $rawBytes = $rawBytes[($rawBytes.Length - $maxBytes)..($rawBytes.Length - 1)]
    }
    $transcriptContent = [System.Text.Encoding]::UTF8.GetString($rawBytes)
    # skip partial first line that byte-slicing may have created
    $firstNl = $transcriptContent.IndexOf("`n")
    if ($firstNl -ge 0) { $transcriptContent = $transcriptContent.Substring($firstNl + 1) }

    if ([string]::IsNullOrWhiteSpace($transcriptContent)) {
        Replace-Placeholder "_(auto-summary failed -- empty transcript)_"
        exit 0
    }

    # --- Build prompt asking for JSON in Thai ------------------------------
    # NOTE: we tried --json-schema first but the current claude CLI returns
    # empty output when that flag is set. Workaround is to describe the
    # shape inline and parse the response text ourselves.
    $prompt = @"
Below is a Claude Code session transcript (JSONL, possibly truncated at the start).
Output a JSON object matching this exact shape -- nothing else, no markdown fence, no preamble:

{
  "title": "<<= 80 chars, Thai>",
  "goal": "<what user wanted, Thai>",
  "what_done": ["<bullet>", ...],
  "decisions": [{"context":"...","decision":"...","consequences":"..."}],
  "mistakes": [{"what":"...","why":"...","fix":"...","rule":"...","tags":["..."]}],
  "followup": ["<bullet>", ...],
  "status": "completed" | "interrupted" | "blocked",
  "extracted_feedback": [{"topic":"<short kebab-case English>","rule":"<generalizable rule, Thai>","why":"<one-sentence reason>"}]
}

Focus especially on MISTAKES the assistant made: include root cause (why), the fix, and a generalizable rule for next time. Be concise.

For `extracted_feedback`: include 0-2 items ONLY if there is a HIGH-IMPORTANCE rule worth remembering across sessions (e.g., a rule containing "always/never", a recurring class of mistake, or a non-obvious gotcha). If the session is routine or has only minor mistakes, return an empty array. Do NOT include generic principles.

TRANSCRIPT:
$transcriptContent
"@

    # Recursion guard. session-logger.ps1 checks CLAUDE_LOGGER_ACTIVE at
    # entry and exits 0, so the SessionEnd hook of the child claude -p will
    # not re-trigger this summarizer.
    $env:CLAUDE_LOGGER_ACTIVE = '1'

    # Force UTF-8 on the pipe in BOTH directions, otherwise PowerShell 5.1
    # uses the OEM code page (cp874 on Thai Windows) and Thai text becomes
    # mojibake going into and coming out of `claude.exe`.
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [Console]::InputEncoding  = $utf8
    [Console]::OutputEncoding = $utf8
    $OutputEncoding           = $utf8

    # --system-prompt overrides the default system prompt (which loads
    # CLAUDE.md persona). Without this, Haiku replies as "kaho" and ignores
    # the JSON instruction.
    $systemPrompt = 'You are a JSON-only API. Output exactly one JSON object matching the user-provided shape, in Thai content where requested. No markdown fence. No commentary.'

    # Budget 0.15 to absorb the unavoidable CLAUDE.md user-memory prefix
    # (skill list + persona) that gets re-cached on every fresh `claude -p`
    # invocation. Real per-session cost typically lands around $0.05-0.08.
    $claudeArgs = @(
        '-p',
        '--model', 'haiku',
        '--max-turns', '1',
        '--max-budget-usd', '0.15',
        '--no-session-persistence',
        '--output-format', 'json',
        '--system-prompt', $systemPrompt
    )

    $claudeOut = $prompt | & claude @claudeArgs
    $exitCode  = $LASTEXITCODE

    if ($exitCode -ne 0 -or -not $claudeOut) {
        $sample = ($claudeOut -join "`n")
        if ($sample.Length -gt 500) { $sample = $sample.Substring(0, 500) }
        Write-LoggerError "claude exit=$exitCode out=$sample"
        Replace-Placeholder "_(auto-summary failed -- run /session-summary $SessionId)_"
        exit 0
    }

    # --- Parse JSON envelope ----------------------------------------------
    try {
        $envelope = ($claudeOut -join "`n") | ConvertFrom-Json
    } catch {
        Write-LoggerError "envelope parse: $($_.Exception.Message)"
        Replace-Placeholder "_(auto-summary failed -- bad JSON envelope)_"
        exit 0
    }

    # claude -p --output-format json returns a top-level object with
    # `result` (the assistant's text). Strip optional code fence then parse.
    $parsed = $null
    if ($envelope.PSObject.Properties.Name -contains 'result' -and $envelope.result) {
        $resultText = [string]$envelope.result
        # Strip ```json ... ``` or ``` ... ``` if present
        $fenceMatch = [regex]::Match($resultText, '(?s)```(?:json)?\s*(.+?)\s*```')
        if ($fenceMatch.Success) {
            $resultText = $fenceMatch.Groups[1].Value
        }
        try {
            $parsed = $resultText | ConvertFrom-Json
        } catch {
            Write-LoggerError "result-as-json parse: $($_.Exception.Message); first 300 chars: $($resultText.Substring(0,[Math]::Min(300,$resultText.Length)))"
        }
    }

    if (-not $parsed) {
        Replace-Placeholder "_(auto-summary failed -- no structured payload)_"
        exit 0
    }

    $body = Render-Body $parsed
    Replace-Placeholder $body

    # Best-effort digest (Sonnet) + extracted feedback writes. Failures here must not
    # prevent the main log from being filled, so wrap independently.
    try {
        $digestPrompt = @"
Below is a Claude Code session transcript (JSONL, possibly truncated at the start).
Output exactly one sentence (<= 100 chars, in Thai) capturing the ONE key takeaway of this session.
No markdown fence, no preamble, no explanation -- just the sentence.

TRANSCRIPT:
$transcriptContent
"@
        $digestArgs = @(
            '-p',
            '--model', 'sonnet',
            '--effort', 'medium',
            '--max-turns', '1',
            '--max-budget-usd', '0.20',
            '--no-session-persistence',
            '--output-format', 'json',
            '--system-prompt', 'You are a concise summarizer. Output only the requested text, nothing else.'
        )
        $digestOut = $digestPrompt | & claude @digestArgs
        $digestExitCode = $LASTEXITCODE
        if ($digestExitCode -eq 0 -and $digestOut) {
            $digestEnvelope = ($digestOut -join "`n") | ConvertFrom-Json
            if ($digestEnvelope.PSObject.Properties.Name -contains 'result' -and $digestEnvelope.result) {
                $digestLine = ([string]$digestEnvelope.result).Trim()
                Append-Digest $digestLine
            }
        } else {
            Write-LoggerError "digest-sonnet exit=$digestExitCode out=$(($digestOut -join ' ').Substring(0,[Math]::Min(300,($digestOut -join ' ').Length)))"
        }
    } catch { Write-LoggerError "digest: $($_.Exception.Message)" }
    try { Append-ExtractedFeedback $parsed.extracted_feedback } catch { Write-LoggerError "extracted: $($_.Exception.Message)" }

    exit 0
} catch {
    Write-LoggerError "fatal: $($_.Exception.Message)"
    try {
        Replace-Placeholder "_(auto-summary failed -- run /session-summary $SessionId)_"
    } catch { }
    exit 0
}
