---
name: extracting-youtube-transcript
description: Extracts the full text transcript of a YouTube video by navigating to the watch URL with Playwright MCP, clicking the "Show transcript" button, and reading the rendered transcript panel. Use when the user pastes a YouTube URL or asks to summarize, study, or analyze a YouTube video. Triggers on "ดึง transcript", "สรุป YouTube", "อ่านคลิป", "study this video", "what does this video say", "extract subtitles", youtube.com, youtu.be.
allowed-tools: "mcp__playwright__browser_navigate mcp__playwright__browser_wait_for mcp__playwright__browser_evaluate Read"
---

# Extracting YouTube Transcript

Pulls the spoken text out of a YouTube video so Claude can summarize, quote, or analyze it.

## Steps

1. **Navigate to the watch URL**
   - Use `mcp__playwright__browser_navigate` with `https://www.youtube.com/watch?v=<ID>`
   - `youtu.be/<ID>` short links also work

2. **Wait ~3 seconds** for the page to hydrate (JS bundle lazy-loads player components)
   - `mcp__playwright__browser_wait_for` with `time: 3`

3. **Click the "Show transcript" button**
   - Selector: `button[aria-label="แสดงข้อความถอดเสียง"]` (Thai UI) or `button[aria-label="Show transcript"]` (English UI)
   - There are usually 2 matching buttons (description bar + engagement panel) — clicking the first works
   - Use `mcp__playwright__browser_evaluate` with this function:
     ```js
     () => {
       const btns = Array.from(document.querySelectorAll(
         'button[aria-label="แสดงข้อความถอดเสียง"], button[aria-label="Show transcript"]'
       ));
       if (btns.length === 0) return 'no transcript button';
       btns[0].click();
       return `clicked ${btns.length} button(s)`;
     }
     ```

4. **Wait ~2 seconds** for the transcript panel to render (player state must settle before extraction)

5. **Extract transcript text**
   - Use `mcp__playwright__browser_evaluate` with `filename` parameter so the result goes to a file (transcripts are big):
     ```js
     () => {
       const panel = document.querySelector(
         'ytd-transcript-renderer, ytd-transcript-search-panel-renderer, #segments-container'
       );
       if (panel) return panel.innerText;
       const segs = document.querySelectorAll('ytd-transcript-segment-renderer');
       if (segs.length > 0) return Array.from(segs).map(s => s.innerText).join('\n');
       return 'NOT_FOUND';
     }
     ```
   - Save with `filename: ".playwright-mcp/transcript_<id>.txt"` to keep main context clean

6. **Read the saved file** (only if needed for synthesis) and proceed with whatever the user asked.

## Edge cases

- **`NOT_FOUND` returned**: video is too new (auto-captions still generating — try again in 30+ minutes), captions disabled by uploader, or live stream. Fall back to reading the video description (`#description-inner` or `ytd-attributed-description-renderer`).
- **`no transcript button`**: same as above — auto-caption not available yet. Don't keep retrying; tell the user.
- **Multiple videos in one request**: navigate sequentially (one tab); Playwright MCP keeps a single browser context. Save each transcript to its own file.
- **Multi-language captions**: clicking the button gives the default track. To switch, click the panel's language dropdown — but for first-pass summarization the default is usually fine.

## Anti-patterns

- ❌ Using `youtube-transcript-api` Python library — IP-blocked, wastes time
- ❌ Calling `WebFetch` on `youtube.com/api/timedtext?...` URLs — returns empty body
- ❌ Reading the entire transcript into the conversation — always save to file first via `filename:` param
- ❌ Using `chrome-devtools` MCP attach mode — has "No page selected" bug; use Playwright MCP instead

## Output format

When summarizing for the user, report:
- Video title (from `document.title`)
- Duration / view count (from snapshot)
- 3–7 bullet summary
- Key quotes only when the user asks for them
