# zen-skills

Zen's personal Claude Code skill collection — 16 skills for workflow automation, code quality, and session management.

## Install

```
/plugin marketplace add zennnne/zen-skills
/plugin install zen-skills@zen-skills
```

Then run `/wahahaha` to set up external plugins and session logging in one shot.

## Skills

| Skill | Tier | What it does |
|-------|------|--------------|
| `harvest-insights` | S+ | Extracts insights from a session and asks whether to save each to memory/skills |
| `craft-skill` | S | Researches a topic and builds a SKILL.md through a 6-phase process |
| `reviewing-code` | S | 4-agent parallel code review covering correctness, security, performance, maintainability |
| `auditing-security` | S | 8-agent security audit with CVSS scoring and remediation roadmap |
| `designing-subagent-systems` | S | Helps choose the right multi-agent workflow shape before building |
| `crafting-skills-deeply` | A | Deep version of craft-skill with parallel researchers and critique loop |
| `designing-agent-roles` | A | Designs agent roles, tool scope, model tier, and system prompts |
| `wahahaha` | A | Onboarding wizard — sets up all plugins and session logging in one run |
| `extracting-youtube-transcript` | A | Extracts full YouTube transcripts via browser automation |
| `audit-skills` | A | Scans skill descriptions for discoverability issues and proposes fixes |
| `setup-session-log` | A | Installs auto session logging (Haiku summarizes every session) |
| `updating-plugins` | B | Updates all 4 external plugins in one command |
| `session-summary` | B | Backfills daily session summaries when auto-summarizer failed |
| `session-index` | B | Generates a searchable monthly session index |
| `applying-3-act-structure` | B | Analyzes or outlines narrative using three-act framework |
| `cleaning-sessions` | C | Deletes old session transcripts to free disk space |

## PDF Catalog

`gen_zenskills_pdf.py` generates a visual skill reference (`zen-skills-catalog.pdf`) covering all installed plugins — zen-skills, 9arm-skills, mattpocock-skills, karpathy-skills, and document-skills.

```bash
pip install reportlab pillow
python gen_zenskills_pdf.py
```
