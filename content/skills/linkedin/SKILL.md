---
name: linkedin
model: sonnet
description: LinkedIn automation and data analysis via playwright-cli. Use when extracting profiles, reading feeds, writing recommendations, or searching people. Triggers on LinkedIn, profile extraction, connections, feed, LinkedIn search, recommendation.
disableModelInvocation: true
requires_standards: [english-only]
---

# LinkedIn Skill

Browser automation skill for LinkedIn access via playwright-cli, plus offline analysis of GDPR data exports.

## When to Use

Use this skill when you need to:
- Extract LinkedIn profile information (contacts, connections)
- Search for people or companies on LinkedIn
- Read LinkedIn feed, posts, or notifications
- Write recommendations for connections
- Analyze LinkedIn GDPR data exports (connections, messages, activity)
- Format extracted data for structured output

## Mode Routing

| Request Type | Mode | Reference |
|-------------|------|-----------|
| Browse profiles, feed, search, messages | Browser automation | `references/browser-automation.md` |
| Write recommendations | Browser automation | See "Writing Recommendations" section below |
| Analyze GDPR CSV exports | Offline analysis | `references/gdpr-analysis.md` |

## Prerequisites

**playwright-cli** (token-efficient, headless, persistent profile):
- Profile: `~/.local/share/playwright-cli/profiles/linkedin/` (already authenticated)
- Usage: `playwright-cli -s=linkedin open --profile=~/.local/share/playwright-cli/profiles/linkedin <url>`
- For visual verification: add `--headed` flag

## Browser Automation (Summary)

Extraction scripts live in `scripts/`. Each targets a specific page type.
WHY: JavaScript extractors return structured JSON, avoiding large page snapshots in context.

**Core workflow:**
```bash
playwright-cli -s=linkedin open --profile=~/.local/share/playwright-cli/profiles/linkedin <url>
sleep 3
playwright-cli -s=linkedin eval "$(cat scripts/extract_profile.js)"
```

**Key scripts:** `extract_profile.js`, `extract_feed.js`, `extract_search_results.js`, `extract_company.js`, `extract_connections.js`, `extract_messages.js`, `extract_notifications.js`

**Formatting scripts:** `format_profile_for_vault.js`, `format_post_for_vault.js`, `format_company_for_vault.js` -- generate structured markdown with YAML frontmatter.

For full script table, URL patterns, extraction workflows, and formatting details, see `references/browser-automation.md`.

## Navigation Quick Reference

| Action | URL Pattern |
|--------|-------------|
| Profile | `linkedin.com/in/{username}/` |
| Experience details | `linkedin.com/in/{username}/details/experience/` |
| People search | `linkedin.com/search/results/people/?keywords={query}` |
| Company search | `linkedin.com/search/results/companies/?keywords={query}` |
| Feed | `linkedin.com/feed/` |
| Connections | `linkedin.com/mynetwork/invite-connect/connections/` |
| Messages | `linkedin.com/messaging/` |
| Notifications | `linkedin.com/notifications/` |
| GDPR export | `linkedin.com/mypreferences/d/download-my-data` |
| Write recommendation | Profile → More → Recommend (see workflow below) |

## Wait & Scroll Rules

LinkedIn uses heavy lazy-loading. Always wait after actions.
WHY: SPA transitions and IntersectionObserver-based loaders need time to render.

| Action | Wait |
|--------|------|
| After navigation | 3s |
| After scroll | 2s |
| After search/filter | 3s |

**Scrolling:** Use JS `scrollTo()` for reliable infinite scroll triggering:
```bash
playwright-cli -s=linkedin eval "window.scrollTo(0, document.body.scrollHeight)"
```
WHY: Ensures scrolling reaches the absolute bottom to trigger LinkedIn's loaders.

Always take a screenshot/snapshot after waiting to verify content loaded.

## GDPR Data Export Analysis (Summary)

LinkedIn GDPR exports contain CSV files (Connections, Messages, Invitations, etc.).

**Analyze with Python tools in `gdpr/`:**
```bash
uv run python gdpr/gdpr_analyzer.py /path/to/linkedin-export/
uv run python gdpr/gdpr_analyzer.py /path/to/export/ --section connections
```

**Key gotchas:**
- Export is async (minutes to hours), not instant
- Two-part delivery -- Part 2 has full data, wait for it before analysis
- playwright-cli has no `download` command -- use `--headed` mode and click the download link manually
- Store exports in `~/code/second-brain/data/linkedin/exports/`

For full CSV listing, analysis options, and download procedures, see `references/gdpr-analysis.md`.

## Content Pipeline Integration

Extracted LinkedIn data (browser-based and GDPR exports) can feed into downstream tools:
- Profile/company data formatted as structured markdown for knowledge bases
- Connection exports analyzed for networking patterns
- Feed posts captured for content curation
- GDPR exports provide bulk historical data for analytics

## Writing Recommendations

Standard form elements (combobox selects + textbox) — fully automatable, no contenteditable issues.

**Workflow:**

1. Navigate to profile, scroll down, click in-page **More** → **Recommend**
   - Or via direct URL: `linkedin.com/in/{username}/edit/forms/recommendation/write/?profileFormEntryPoint=TopLevel&profileUrn=...`
   - If coming from profile page, LinkedIn skips the person search (step 1) and goes straight to the form
2. **Step 1 of 2** (if shown): Search for person → select from typeahead → click **Continue**
3. **Step 2 of 2**: Fill three fields:
   - `select` **Relationship** (e.g. "X reported directly to you", "You worked with X in the same group")
   - `select` **Position at the time** (populated from their experience history)
   - `fill` **Add recommendation** textbox (max 3,000 chars)
4. Click **Send**

**Tips:**
- The sticky toolbar "More" button may be intercepted by the nav bar — scroll down ~400px and use the in-page "More" button instead
- Multiple recommendations for the same person are allowed (e.g. one per role/company)
- Draft the recommendation text first, review with user, then fill and send
- LinkedIn typeahead (person search): first click may not register — if selection doesn't stick, clear the field, retype the name, wait 2s for the dropdown, then click the option
- Profile URLs are not always `/in/firstname-lastname` — they may include a hash suffix (e.g. `/in/name-7806a667`). If a guessed URL returns 404, search by name via `/search/results/people/?keywords=...`

## Do NOT

- **Automate posting** -- LinkedIn's contenteditable editor is unreliable for automation. Draft content, copy to clipboard with `pbcopy`, let user paste manually.
  WHY: React contenteditable doesn't respond to programmatic text insertion.
- **Download GDPR archives in headless mode** -- playwright-cli has no `download` command, and headless click discards downloads. Use `--headed` mode instead.
  WHY: Headless Chromium discards downloads triggered by click events.
- **Use simple click on radio buttons/checkboxes** -- use JS `dispatchEvent` with change+input events.
  WHY: React synthetic events bypass native DOM clicks.
- **Skip wait times** -- LinkedIn rate-limits and lazy-loads aggressively.
- **Return full page content** -- extract metadata only, write to file, return path.
  WHY: Full pages waste context tokens.
- **Start GDPR analysis on Part 1 only** -- wait for Part 2 with complete data.

## DOM Changes (Feb 2026)

LinkedIn's DOM was completely overhauled in Feb 2026:
- CSS classes are fully obfuscated (e.g. `_92e46e58`) -- never match on class names
- `h2` is used instead of `h1` for profile names
- Section IDs (`#about`, `#experience`, `#education`, `#skills`) are gone
- `.pvs-entity` no longer exists
- `aria-hidden` spans no longer used for text
- `.text-body-medium`, `.text-body-small`, `.t-bold`, `.t-normal` classes no longer exist

**Extraction strategy:** Find sections by `h2` text content → walk up to parent `<section>` → parse `innerText`. The `extract_profile.js` script implements this approach with bilingual support (EN/DE headings like "Experience" / "Berufserfahrung", "Skills" / "Kenntnisse").

## Limitations

- **Rate limiting** -- LinkedIn may throttle rapid navigation
- **Login required** -- user must be authenticated (playwright-cli profile)
- **Dynamic content** -- requires scrolling to load all sections
- **Anti-automation** -- avoid rapid consecutive actions

## Resources

- `references/browser-automation.md` -- Full extraction scripts, URL patterns, formatting, gotchas
- `references/gdpr-analysis.md` -- GDPR export contents, analysis tools, download procedures
- `scripts/` -- JavaScript extraction and formatting helpers
- `gdpr/` -- Python GDPR analysis tools
