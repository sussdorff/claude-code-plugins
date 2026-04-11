# LinkedIn Browser Automation Reference

Detailed procedures for browser-based LinkedIn interaction via playwright-cli.

## Extraction Scripts

JavaScript helpers in `scripts/` for structured data extraction:

| Script | Purpose | Page Type |
|--------|---------|-----------|
| `extract_profile.js` | Extract profile data (name, headline, experience, education) | `/in/{username}/` |
| `extract_feed.js` | Extract feed posts with engagement metrics | `/feed/` |
| `extract_search_results.js` | Extract people/company search results | `/search/results/` |
| `extract_company.js` | Extract company page data | `/company/{slug}/` |
| `extract_connections.js` | Extract connections list | `/mynetwork/.../connections/` |
| `extract_invitations.js` | Extract pending invitations | `/mynetwork/invitation-manager/` |
| `extract_messages.js` | Extract message threads and content | `/messaging/` |
| `extract_notifications.js` | Extract notifications by type | `/notifications/` |
| `check_page_ready.js` | Verify page has finished loading | Any LinkedIn page |
| `format_profile_for_vault.js` | Format profile into structured markdown | Post-extraction |
| `format_post_for_vault.js` | Format post into structured markdown | Post-extraction |
| `format_company_for_vault.js` | Format company into structured markdown | Post-extraction |

**Usage with playwright-cli:**
```bash
playwright-cli -s=linkedin open --profile=~/.local/share/playwright-cli/profiles/linkedin <url>
sleep 3
playwright-cli -s=linkedin eval "$(cat scripts/extract_profile.js)"
```

Read the script file, then pass inline via `playwright-cli -s=linkedin eval "$(cat scripts/file.js)"`.

## Structured Data Output

### Formatting extracted profiles

After extracting profile data with `extract_profile.js`, use `format_profile_for_vault.js` to generate structured markdown:

```javascript
// Example flow (conceptual)
const profileData = extract_profile();  // Returns { profile, details }
const formatted = format_profile_for_vault(profileData.profile, profileData.details);
// formatted.markdown contains the structured output
// formatted.suggestedPath contains a suggested filename
```

Output includes:
- YAML frontmatter (name, company, role, linkedin_url, last_synced)
- Experience, Education, Skills sections
- Empty Notes section for user additions

### Formatting extracted posts

After extracting feed posts with `extract_feed.js`, format with `format_post_for_vault.js`:

```javascript
const feedData = extract_feed();  // Returns { posts: [...] }
const formatted = format_post_for_vault(feedData.posts[0]);
// formatted.markdown contains the structured post
```

Output includes:
- YAML frontmatter (author, source, captured date, engagement metrics)
- Post content with author info
- Shared article details if present

### Formatting extracted companies

After extracting company data with `extract_company.js`, format with `format_company_for_vault.js`:

Output includes:
- YAML frontmatter (name, industry, size, website, linkedin_url, last_synced)
- Overview table with key details
- About and Specialties sections

## Search

### URL patterns for search

| Search Type | URL |
|-------------|-----|
| Universal | `linkedin.com/search/results/all/?keywords={query}` |
| People | `linkedin.com/search/results/people/?keywords={query}` |
| Companies | `linkedin.com/search/results/companies/?keywords={query}` |
| Posts/Content | `linkedin.com/search/results/content/?keywords={query}` |
| Jobs | `linkedin.com/search/results/jobs/?keywords={query}` |

### Extract search results

1. Navigate to search URL
2. Wait 3 seconds for results
3. Scroll 2-3 times to load more results
4. Run `extract_search_results.js`

Returns structured data with name, headline, location, connection degree, and profile URLs.

## Company Pages

### Company page URLs

| Page | URL |
|------|-----|
| Main page | `linkedin.com/company/{slug}/` |
| About | `linkedin.com/company/{slug}/about/` |
| People | `linkedin.com/company/{slug}/people/` |
| Posts | `linkedin.com/company/{slug}/posts/` |
| Jobs | `linkedin.com/company/{slug}/jobs/` |

### Extract company data

1. Navigate to company page
2. Wait 3 seconds
3. Scroll to load About section
4. Run `extract_company.js`

Returns: name, industry, size, headquarters, website, about text, specialties

## Connections and Network

### My connections

1. Navigate to `https://www.linkedin.com/mynetwork/invite-connect/connections/`
2. Wait 3 seconds
3. Scroll multiple times to load more (connections use infinite scroll)
4. Run `extract_connections.js`

Returns: name, headline, profile URL, connection date for each connection.

### Search within connections

Use first-degree filter in search:
```
linkedin.com/search/results/people/?keywords={query}&network=%5B%22F%22%5D
```

### Pending invitations

1. Navigate to `https://www.linkedin.com/mynetwork/invitation-manager/`
2. Run `extract_invitations.js`

Toggle between received and sent invitations:
- Received: `?invitationType=CONNECTION`
- Sent: `?invitationType=SENT`

## Messages and Notifications

### Reading messages

**Privacy notice:** Messages are private content. Always show user what was extracted before any further operations.

1. Navigate to `https://www.linkedin.com/messaging/`
2. Run `extract_messages.js` for thread list overview
3. Click a thread to view conversation
4. Run `extract_messages.js` again for full message history
5. Scroll up in thread to load older messages

### Reading notifications

1. Navigate to `https://www.linkedin.com/notifications/`
2. Scroll to load more
3. Run `extract_notifications.js`

Notifications are categorized by type:
- `connection` - Connection requests
- `reaction` - Likes on your posts
- `comment` - Comments on your posts
- `mention` - Mentions in posts/comments
- `job` - Job alerts
- `birthday` - Contact birthdays
- `work_anniversary` - Contact work anniversaries
- `profile_view` - Profile views

## Profile Extraction Workflow

### 1. Navigate directly to profile

LinkedIn profiles have predictable URLs. Skip search when you know the username:

```
https://www.linkedin.com/in/{username}/
```

### 2. Search for a contact

```
https://www.linkedin.com/search/results/people/?keywords={name}
```

The search results show:
- Name with verification badge
- Current headline/role
- Location
- Connection degree (1st, 2nd, 3rd)
- Mutual connections

### 3. Extract profile data

Once on a profile page, use this workflow:

1. **Wait 3 seconds** for page to load
2. **Run `check_page_ready.js`** to verify content loaded
3. **Scroll down** 3-5 times to load dynamic content
4. **Run `extract_profile.js`** for structured data
5. **Use `get_page_text`** for additional context if needed

Key sections captured:
- Header: Name, headline, location, connections count
- About section
- Experience (scroll to load all)
- Education
- Skills

### 4. Profile data structure

Extract into this format:

```yaml
---
name: "First Last"
linkedin_url: "https://www.linkedin.com/in/username/"
headline: "Role | Keywords"
company: "Current Company"
role: "Current Title"
location: "Region"
connection_degree: "1st"
followers: 1234
last_synced: 2026-02-13
---
```

## Feed Reading

### Extract feed posts

1. Navigate to `https://www.linkedin.com/feed/`
2. Wait 3 seconds for initial load
3. Scroll 3-5 times to load more posts (2 seconds between scrolls)
4. Run `extract_feed.js` for structured post data

The extractor filters out:
- Promoted/sponsored posts
- Ads and suggestions
- UI noise (buttons, navigation)

### Own activity

Navigate to `/in/{username}/recent-activity/all/` to see your own posts with engagement metrics.

## Posting to LinkedIn

**LinkedIn posting should be done manually.** The post composer uses a complex contenteditable editor that's unreliable for automation.
WHY: React contenteditable doesn't respond to programmatic text insertion reliably.

**Workflow for posting:**
1. Draft the post content in conversation
2. Copy to clipboard with `pbcopy`
3. User pastes manually into LinkedIn

Example:
```bash
cat << 'EOF' | pbcopy
Your post content here...
EOF
echo "Copied to clipboard - paste into LinkedIn manually"
```

## Wait Time Guidelines

LinkedIn uses heavy lazy-loading. Follow these wait times:

| Action | Wait Time | Reason |
|--------|-----------|--------|
| After navigation | 3 seconds | SPA transitions, initial render |
| After scroll | 2 seconds | Lazy content loading |
| After expanding "see more" | 1 second | Text expansion animation |
| After search | 3 seconds | Results rendering |
| After clicking filter | 2 seconds | Results re-rendering |

**Pattern:** Always take a screenshot after waiting to verify content loaded.

## Scrolling for Dynamic Content

LinkedIn lazy-loads content.

**With playwright-cli (preferred):**
```bash
# Reliable: JS scrollTo reaches absolute bottom
playwright-cli -s=linkedin eval "window.scrollTo(0, document.body.scrollHeight)"
sleep 2
playwright-cli -s=linkedin snapshot  # verify new content loaded
```

**Standard scroll sequence:**
1. Scroll down
2. Wait 2 seconds
3. Verify new content loaded (snapshot or screenshot)
4. Repeat 2-4 more times until:
   - Desired section is visible
   - No new content loads
   - Maximum iterations reached (default: 10)

## LinkedIn-Specific Gotchas

### Radio buttons and form controls need JS activation

LinkedIn's React-based UI does not respond to simple `click` commands on radio buttons and some checkboxes. The DOM updates but React's internal state doesn't sync, leaving buttons disabled.
WHY: React uses synthetic events; native DOM clicks bypass React's state management.

**Fix:** Use JavaScript to set the value and dispatch events:
```javascript
const radio = document.getElementById('target-radio-id');
radio.checked = true;
radio.dispatchEvent(new Event('change', { bubbles: true }));
radio.dispatchEvent(new Event('input', { bubbles: true }));
```

With playwright-cli:
```bash
playwright-cli -s=linkedin eval "(() => { const radio = document.querySelector('input[type=\"radio\"][value=\"full\"]'); if (radio) { radio.checked = true; radio.dispatchEvent(new Event('change', { bubbles: true })); radio.dispatchEvent(new Event('input', { bubbles: true })); } return JSON.stringify({ checked: radio?.checked }); })()"
```

### Scrolling with playwright-cli

Use JS `scrollTo()` via eval for reliable infinite scroll triggering:
WHY: Ensures scrolling reaches the absolute bottom to trigger LinkedIn's IntersectionObserver-based loaders.
```bash
playwright-cli -s=linkedin eval "window.scrollTo(0, document.body.scrollHeight)"
```

## Token Efficiency

- Extract content immediately using JavaScript helpers.
  WHY: Avoids large page snapshots polluting context.
- Return metadata only (name, url, last_synced) not full page content
- Use subagents for multi-profile extraction to isolate context
- Write extracted data to file immediately, return path not content
