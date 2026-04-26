# Feature Spec: weekly-prompt-kit-review

**Status**: Approved (v1.1, refinement loop closed 2026-04-26)
**Author**: Malte Sussdorff + spec-developer (inline run)
**Date**: 2026-04-26
**Version**: 1.1
**Bead**: CCP-vh2w
**Depends-on**: polaris-faker audit (new pre-spike bead, see OQ-2)
**Changelog**:
- 1.0 → 1.1 (2026-04-26): Match runs in host Claude Code session (no Anthropic SDK / no extra API key). AW-1, AW-3, AW-7 resolved. Active-bead set extended to {open, in_progress, blocked, human}. Tier-4 ordering: link-after-parent-message.

---

## Section 1: Executive Summary

A manually-triggered Friday-cadence skill that ingests new content from external "prompt-quality" sources (Executive Circle MCP and a single Matrix room bridged from WhatsApp), matches each item against the local agent harness corpus (skills, agents, standards, open beads) using Claude Sonnet, and produces inline approval prompts that turn approved items into beads. Single-user, signal-filtering optimised — the goal is "wow, that's something I would have missed" moments, not high throughput. State lives in a local SQLite file. Secrets stay in 1Password. WhatsApp content is pseudonymised before it ever lands in a bead body.

---

## Section 2: Problem Statement & Motivation

Today, Malte tracks Nate's AI Exec Circle output (newsletter posts, prompt kits, guides) and the connected WhatsApp discussion group manually. Two failure modes recur:

1. **The most valuable artefacts are skipped.** Nate publishes prompt kits that are dense, reusable, and frequently superior to home-grown skill bodies. Reading them takes focus; the WhatsApp scroll is faster, so prompt kits get bookmarked and never opened.
2. **Third-party links in WhatsApp evaporate.** Members share repos, gists, and skills from other authors. Without a structured capture, those links disappear into chat history.

Current workaround: scrolling WhatsApp on the phone, opening a few items, mostly forgetting the rest. The cost is opportunity cost — the home-grown skill library evolves slower than the field around it.

This feature is built now because:
- Executive Circle MCP recently became available locally (read-only, search + fetch tools).
- Matrix/Synapse with a working WhatsApp bridge is already deployed at `matrix.sussdorff.org` (`~/code/infra-devops/elysium-proxmox/lxc/matrix/`).
- The architecture-trinity vocabulary, beads workflow, and open-brain memory are mature enough to absorb a "review queue" without inventing new infrastructure.

If we don't build it: the gap between Malte's skill library and Nate's published patterns continues to widen, and the cost of "I should have read that" compounds week over week.

---

## Section 3: User Stories / Use Cases

### UC-1: Friday signal scan (primary happy path)
**Actor**: Malte (single user)
**Precondition**: At least 1 day has passed since the last successful run; cursors are populated; secrets resolvable from 1Password.
**Trigger**: Malte invokes the skill (`/weekly-prompt-kit-review` or natural-language match).
**Main Flow**:
1. Skill resolves Matrix access token and Anthropic API key from 1Password.
2. Skill rebuilds the local matching corpus (skills, agents, standards, open beads) — see Section 4.
3. Skill fetches deltas from each configured source since per-source cursor.
4. Skill matches each new item against the corpus using Claude Sonnet (Section 5, FR-MATCH-*).
5. Skill produces an in-memory findings queue ordered by priority tier (prompt-kits first, posts, WhatsApp last).
6. Skill batches items 4-at-a-time into AskUserQuestion calls; for each item, Malte chooses APPROVE / DISMISS / DEFER.
7. Approved items become beads via `bd create`. Dismissed items get `dismissed` state. Deferred items get a 4-week `defer_until` timestamp.
8. Cursors advance per source. Run summary lands in `run_history` table.
**Postcondition**: New beads exist for approved items; SQLite state reflects all decisions; cursors moved forward.
**Exceptions**:
- Source unreachable (EC MCP down, Matrix 5xx) → skill continues with available sources, run-summary flags missing source, that source's cursor does NOT advance.
- 1Password unreachable → skill aborts before fetching anything (fail-fast on secrets).
- Sonnet rate-limit → skill applies backoff, continues.

### UC-2: Mid-flight crash resume
**Actor**: Malte
**Precondition**: A previous run produced items in `proposed` state but did not finish reviewing them (terminal closed, network blip, AUQ cancelled).
**Trigger**: Skill is invoked again.
**Main Flow**:
1. Skill detects items in state `proposed` from prior runs.
2. Skill places them at the front of the queue, fetches new items behind them.
3. Inline approval continues from where it left off.
**Postcondition**: No item is silently dropped. Cursors only advance when the item's source delta has been fully drained.
**Exceptions**: If items have aged > 90 days while in `proposed`, skill warns Malte and offers a single bulk-dismiss.

### UC-3: Dry-run inspection
**Actor**: Malte
**Precondition**: Skill not yet trusted on a new source or after a config change.
**Trigger**: Skill invoked with `--dry-run`.
**Main Flow**:
1. Skill executes Phases 1-5 (resolve, corpus, fetch, match, prioritise) exactly as in UC-1.
2. Skill writes the findings table to stdout AND a temp file `~/.cache/weekly-prompt-kit-review/dry-run-YYYY-MM-DD-HHMM.md`.
3. No SQLite state mutation, no bead creation, no AUQ prompts.
**Postcondition**: User can read the would-be findings without side effects. Cursors unchanged.
**Exceptions**: Same source-unavailable handling as UC-1 (best-effort + report).

### UC-4: Backlog dedup hit
**Actor**: Malte
**Precondition**: An item from EC or WhatsApp shares an exact source URL or MCP-ID with an existing open bead's notes/description.
**Trigger**: Match phase finds the URL/ID match.
**Main Flow**:
1. Skill marks the item as `duplicate_of_bead:<bead-id>` in the findings table.
2. Item is shown to Malte with the existing bead reference, no AUQ choice.
3. Malte may optionally append a note to the existing bead via a follow-up dismiss-with-comment flow (out of scope v1; v2 enhancement).
**Postcondition**: No duplicate bead created. Source item marked `dismissed` with reason=`duplicate_of_bead:<id>`.

### UC-5: WhatsApp link extraction
**Actor**: Malte
**Precondition**: Matrix room contains a message with an external URL (skill repo, gist, blog post).
**Trigger**: Match phase processes a Matrix message with extractable URLs.
**Main Flow**:
1. URL extractor finds the URL, canonicalises it (strip tracking params, normalise scheme/host).
2. Skill fetches a 1-paragraph excerpt via existing `summarize` skill or `crwl crawl URL -o md`.
3. Item enters the queue as `whatsapp_link` with both message context (pseudonymised) and extracted excerpt.
4. Match runs against extracted excerpt + message context.
**Postcondition**: Linked content is treated as first-class match input, not just a trigger pointer.
**Exceptions**: Fetch fails → item still queued with message context only; findings table marks `link_fetch_failed`.

---

## Section 4: Data Model

### Entity: source
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| id | TEXT | Yes | Primary key (`ec_posts`, `ec_kits`, `ec_guides`, `matrix_aiec`) |
| kind | TEXT | Yes | `executive_circle` \| `matrix` |
| priority_tier | INTEGER | Yes | 1=prompt-kits, 2=posts, 3=guides, 4=whatsapp |
| cursor | TEXT | No | Last-seen identifier (timestamp ISO8601, Matrix sync token, or MCP pagination cursor) |
| last_run_at | TEXT | No | ISO8601 |
| last_status | TEXT | No | `ok` \| `failed:<reason>` |

### Entity: item
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| id | TEXT | Yes | Primary key — natural ID per Section 4.1 |
| source_id | TEXT | Yes | FK to `source.id` |
| kind | TEXT | Yes | `prompt_kit` \| `post` \| `guide` \| `matrix_message` \| `extracted_link` |
| native_url | TEXT | No | Canonical URL when applicable |
| discovered_at | TEXT | Yes | ISO8601 |
| state | TEXT | Yes | See state machine below |
| state_changed_at | TEXT | Yes | ISO8601 |
| match_payload | TEXT | No | JSON: `{ matched_targets: [{kind, name, score, why}], top_score: float }` |
| dedup_key | TEXT | Yes | Unique together with source_id |
| dismiss_reason | TEXT | No | Free-form when state=dismissed |
| defer_until | TEXT | No | ISO8601 when state=deferred |
| bead_id | TEXT | No | When state=approved |
| pseudonymised_excerpt | TEXT | No | For matrix_message and extracted_link only |

**State machine**:
```
discovered ──▶ filtered_out (no relevant target)
            │
            ├▶ proposed ──▶ approved   (bead created)
                        │
                        ├▶ dismissed   (user choice or duplicate)
                        │
                        └▶ deferred    (review again after defer_until)
                              │
                              └▶ proposed (auto-re-enter when deferred date passes)
```

Invariants:
- An item is never in two states at once.
- Once `approved`, `bead_id` is non-null and immutable.
- Once `filtered_out`, the item never re-enters the queue unless the corpus changes meaningfully (out of scope v1).

### 4.1 Dedup-key strategy
| Source | Natural ID | Fallback |
|--------|------------|----------|
| EC post | `ec:post:<mcp_id>` | sha256(canonical_url) |
| EC prompt-kit | `ec:kit:<mcp_id>` | sha256(canonical_url) |
| EC guide | `ec:guide:<mcp_id>` | sha256(canonical_url) |
| Matrix message | `matrix:event:<event_id>` | n/a (event_id is stable) |
| Extracted link | `link:<sha256(canonical_url)>` | n/a |

### Entity: run
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| run_id | TEXT | Yes | UUIDv7 |
| started_at | TEXT | Yes | ISO8601 |
| ended_at | TEXT | No | ISO8601 |
| mode | TEXT | Yes | `live` \| `dry_run` |
| sources_attempted | TEXT | Yes | JSON array of source.id |
| sources_failed | TEXT | Yes | JSON array (subset of attempted) |
| items_discovered | INTEGER | Yes | |
| items_proposed | INTEGER | Yes | |
| items_approved | INTEGER | Yes | |
| items_dismissed | INTEGER | Yes | |
| items_deferred | INTEGER | Yes | |
| sonnet_calls | INTEGER | Yes | |
| sonnet_tokens_in | INTEGER | Yes | |
| sonnet_tokens_out | INTEGER | Yes | |

### Storage
- File: `~/.cache/weekly-prompt-kit-review/state.db` (SQLite, WAL mode, single-writer).
- Schema migrations via `migrations/NNN_<name>.sql` files in the helper script directory.
- The state DB MUST NOT contain raw PII or secrets — only IDs, URLs, statuses, scores, timestamps. Pseudonymised excerpts may be stored.

---

## Section 5: Functional Requirements

### Source ingestion
**FR-INGEST-001**: The skill SHALL fetch new items from each configured source since that source's cursor.
- **Priority**: Must
- **Acceptance**: Given a cursor at T, items with timestamp > T are returned; items <= T are not.

**FR-INGEST-002**: The skill SHALL maintain a separate cursor per source and advance each cursor only after that source's items have been written to the `item` table.
- **Priority**: Must
- **Acceptance**: If Matrix fetch fails after EC succeeds, EC's cursor advances and Matrix's does not.

**FR-INGEST-003**: The skill SHALL read the Matrix room "Nate's AI Exec Circle" via the Matrix Client-Server API `/_matrix/client/v3/sync` (or `/messages` for catch-up) using a read-only access token.
- **Priority**: Must
- **Acceptance**: Skill can fetch the last 100 messages of the configured room without write permission. No bot membership required beyond the existing user.

**FR-INGEST-004**: The skill SHALL extract URLs from Matrix message bodies, canonicalise them (strip UTM params, normalise scheme/host casing), and queue each unique URL as an `extracted_link` item.
- **Priority**: Must
- **Acceptance**: A message containing 2 distinct URLs produces 1 `matrix_message` item + 2 `extracted_link` items.

**FR-INGEST-005**: For each `extracted_link`, the skill SHALL attempt a 1-paragraph excerpt via `summarize` skill or `crwl crawl URL -o md` and attach it to the item's match payload. Failure to fetch SHALL NOT abort the item; it remains queued with message context only.
- **Priority**: Must
- **Acceptance**: A link to a 404 page produces an item with `link_fetch_failed=true` flag, still proceeds to match phase.

### Corpus building
**FR-CORPUS-001**: The skill SHALL build a fresh matching corpus on every run by scanning:
- All `*/skills/<name>/SKILL.md` under `~/code/claude-code-plugins/` and `~/.claude/skills/`.
- All `*/agents/<name>.md` under the same roots.
- All `~/.claude/standards/**/*.md`.
- Open beads via `bd list --status=open --status=in_progress --json`.
- **Priority**: Must
- **Acceptance**: Adding a new skill between runs causes it to appear in corpus on the next run without manual config.

**FR-CORPUS-002**: For skills and agents, the skill SHALL extract `name` and `description` from YAML frontmatter only (not body content).
- **Priority**: Must
- **Acceptance**: A skill with a 500-line body produces a corpus entry with at most 600 chars.

**FR-CORPUS-003**: For standards, the skill SHALL extract the document title (first H1) and the first paragraph (up to 400 chars).
- **Priority**: Should
- **Acceptance**: Standards with no H1 are skipped with a warning.

**FR-CORPUS-004**: For "active" beads (statuses `open`, `in_progress`, `blocked`, `human`), the skill SHALL extract `id`, `title`, `status`, `description` (truncated to 600 chars), and any URLs/MCP-IDs found in `notes` or `description`. Closed beads are excluded.
- **Priority**: Must
- **Acceptance**: A bead with `notes` containing `https://nate.com/post/123` exposes that URL for dedup matching. A `blocked` bead is included; a `closed` bead is not.

### Matching
**FR-MATCH-001**: For each `discovered` item, matching is performed by the **host Claude Code session** (not a subprocess SDK call). The helper script writes a `match-input.json` file containing `{corpus, items}`; the skill body reads it and produces match results inline using the host model's reasoning, then writes `match-output.json` back. This keeps matching on the Claude Code subscription rather than a separate Anthropic API key.
- **Priority**: Must
- **Acceptance**: A run completes without any Anthropic SDK call from the helper script; match results are produced by the running Claude Code session and persisted to SQLite via the helper script.

**FR-MATCH-001a**: Match output schema MUST be: `[{ "item_id": "...", "matches": [{ "kind": "skill|agent|standard|bead", "name": "...", "score": 0.0, "why": "<one sentence>" }] }]` — at most 3 matches per item.
- **Priority**: Must
- **Acceptance**: Helper script validates the JSON against this schema before persisting; schema mismatch fails the run with a clear error.

**FR-MATCH-002**: An item with all returned scores below 0.4 SHALL be marked `filtered_out`.
- **Priority**: Must
- **Acceptance**: Items with no semantic relevance never reach the user.

**FR-MATCH-003**: Before invoking Sonnet, the skill SHALL check the item against the URL/ID dedup-against-open-beads rule. A match marks the item `dismissed` with `dismiss_reason=duplicate_of_bead:<id>` and skips Sonnet entirely.
- **Priority**: Must
- **Acceptance**: Item with native_url present in any open bead's text is dismissed without Sonnet cost.

**FR-MATCH-004**: ~~Sonnet rate-limit handling~~ — REMOVED. Matching uses the host session per FR-MATCH-001 (in-context, no API-side rate-limit at the SDK boundary). If subscription-tier limits are hit, the host session surfaces them naturally.
- **Priority**: n/a

### Approval flow
**FR-APPROVE-001**: The skill SHALL present items to the user in priority order: tier 1 (prompt-kits) → tier 2 (posts) → tier 3 (guides) → tier 4 (Matrix messages AND extracted links interleaved chronologically by parent message timestamp). Within tier 4, an extracted link follows immediately after its originating message.
- **Priority**: Must
- **Acceptance**: First AUQ batch contains only prompt-kit items if any exist. Within tier 4 a message at T1 with a link is followed by the link before any tier-4 item from T2.

**FR-APPROVE-002**: The skill SHALL batch up to 4 items per AskUserQuestion call, one question per item, with options APPROVE / DISMISS / DEFER and a recommended option.
- **Priority**: Must
- **Acceptance**: With 7 proposed items, exactly 2 AUQ calls happen (4+3).

**FR-APPROVE-003**: APPROVE creates a bead via `bd create --type=task --priority=3 --title='[prompt-kit-review] <item-title>' --description='<source-link + matched targets + match reasoning>' --notes='source:<source-id>, item:<item-id>'`.
- **Priority**: Must
- **Acceptance**: Created bead's notes contain enough metadata to trace back to the SQLite item.

**FR-APPROVE-004**: When an item matches multiple targets above 0.4, the bead description SHALL list all of them with individual scores; a single bead is created (not one per target).
- **Priority**: Must
- **Acceptance**: An item matched to skills A and B and standard C produces 1 bead listing all 3 in body.

**FR-APPROVE-005**: DISMISS sets state=dismissed; the item is never proposed again unless its source row is purged.
- **Priority**: Must

**FR-APPROVE-006**: DEFER sets state=deferred and `defer_until=now+28d`. The next run after that timestamp re-enters the item to `proposed`.
- **Priority**: Must
- **Acceptance**: An item deferred today reappears in the run on day 29.

### State management
**FR-STATE-001**: The skill SHALL persist all state mutations atomically in SQLite (single transaction per item state change).
- **Priority**: Must

**FR-STATE-002**: Items in `proposed` state from prior runs SHALL appear at the front of the next run's queue (auto-resume from crash).
- **Priority**: Must
- **Acceptance**: Killing the process mid-AUQ leaves items in `proposed`; next invocation surfaces them first.

**FR-STATE-003**: Every run SHALL write a row to the `run` table with the metrics defined in Section 4.
- **Priority**: Must

### Modes & flags
**FR-MODE-001**: `--dry-run` runs the full pipeline up to and including match scoring, prints findings to stdout AND writes a temp markdown file, does NOT mutate state.db, does NOT create beads, does NOT advance cursors.
- **Priority**: Must
- **Acceptance**: A dry-run followed by a live-run produces identical findings (modulo new arrivals).

**FR-MODE-002**: `--source <id>` restricts the run to a single source (e.g. `--source matrix_aiec`).
- **Priority**: Should

**FR-MODE-003**: `--since <ISO8601>` overrides the cursor for this run only.
- **Priority**: Could

---

## Section 6: Non-Functional Requirements

**NFR-PERF-001**: End-to-end matching phase (resolve secrets → fetch → match → enqueue) SHALL complete in under 5 minutes for a typical week's volume (≤ 50 items). The interactive AUQ phase has no time limit.

**NFR-PERF-002**: Sonnet token spend per run SHALL stay below 200k input + 20k output tokens for typical weeks. Run summary logs actual usage; if usage > 2× the budget for 3 consecutive runs, that is a "cost regression" and triggers reassessment.

**NFR-SEC-001**: Matrix access token MUST be resolved at runtime via `op read op://Private/matrix-readonly-token/credential`. No environment variable fallbacks. Skill aborts if resolution fails. (No Anthropic API key needed — matching runs in the host Claude Code session per FR-MATCH-001.)

**NFR-SEC-002**: WhatsApp/Matrix message bodies MUST be pseudonymised before storage in `pseudonymised_excerpt` or any bead body. Pseudonymisation strategy reuses the polaris-faker pattern (audit step required — see Open Questions OQ-2).

**NFR-SEC-003**: The SQLite state database MUST NOT store secrets, raw PII, or full Matrix event content beyond the pseudonymised excerpt and structural metadata.

**NFR-RELI-001**: The skill MUST be idempotent on retry: re-running after a successful run SHALL produce zero new items (same cursors, no duplicates).

**NFR-RELI-002**: Best-effort source isolation: a failure in one source MUST NOT prevent other sources from being processed. Cursors advance independently.

**NFR-OBS-001**: Every run logs to stdout AND a `run` row in SQLite. Failed runs include the failing source ID and a one-line error reason.

---

## Section 7: API / Interface Contracts

This skill is a single-user CLI-style invocation. It does NOT expose external APIs. Internal interfaces:

### Skill entry point
- **Invocation**: `/weekly-prompt-kit-review` (slash) or natural-language match per SKILL.md description
- **Args**: `--dry-run`, `--source <id>`, `--since <ISO8601>`
- **Exit code**: 0 on success (including best-effort partial), 1 on fatal (secrets unresolvable, SQLite locked, all sources failed)

### Helper script
- **Path**: `meta/skills/weekly-prompt-kit-review/scripts/review.py`
- **Mode**: PEP 723 with uv (deps: `httpx`, `anthropic`, `pyyaml`)
- **Subcommands**: `review.py run [--dry-run] [--source X] [--since T]`, `review.py status`, `review.py reset-cursor <source>`

### External calls
- **EC MCP**: `mcp__executive-circle__list_recent_posts`, `search_prompt_kits`, `list_prompt_kits`, `search_guides`, `list_guides`, `get_post`, `get_prompt_kit`, `get_guide` — invoked via the harness MCP layer (the helper script runs inside Claude's session, not standalone).
- **Matrix CS-API**: `GET https://matrix.sussdorff.org/_matrix/client/v3/sync?since=<token>&filter=<room_filter>` and `GET /_matrix/client/v3/rooms/<room_id>/messages?from=<token>&dir=b`
- **Anthropic**: `POST https://api.anthropic.com/v1/messages` with `claude-sonnet-4-7` (or current Sonnet alias) and a structured-JSON system prompt
- **bd**: shell-out `bd create`, `bd list --status=open --json`

### Match request schema (Sonnet)
```json
{
  "system": "You are a corpus matcher. Given an item and a corpus of skills/agents/standards/beads, return the 0-3 most relevant matches with scores.",
  "user_template": {
    "item": { "kind": "...", "title": "...", "content": "..." },
    "corpus": [{ "kind": "skill|agent|standard|bead", "name": "...", "description": "..." }, ...]
  },
  "expected_output": {
    "matches": [{ "kind": "...", "name": "...", "score": 0.0, "why": "..." }]
  }
}
```

---

## Section 8: Error Handling Strategy

| Error class | Examples | Response | Recovery |
|---|---|---|---|
| Secrets unresolvable | 1Password locked, missing item | Abort before any work | User unlocks 1Password, retries |
| Source unreachable | EC MCP 5xx, Matrix DNS fail | Mark source `failed:<reason>`, skip, continue with others | Cursor not advanced; next run retries |
| Source malformed response | Schema drift in MCP | Log + skip the offending item, continue | Bead filed manually if needed |
| LLM call failure | 429, 5xx, JSON parse error | One retry with backoff; if still fails, mark item `match_failed`, surface in findings as "needs manual triage" | User can manually approve/dismiss in next run |
| URL fetch failure (extracted link) | 404, timeout, paywall | Item still queued with message context only, `link_fetch_failed=true` | Match continues with reduced context |
| SQLite lock | Concurrent run, NFS mount weirdness | Abort with clear message — single-writer constraint | User checks for stuck process |
| `bd create` failure | beads server down | Item stays in `proposed` state, surfaced in run summary as "approved-but-not-dispatched" | Next run retries the dispatch |

Logging:
- stdout: human-readable, one line per item state transition.
- SQLite `run` table: structured metrics + error JSON.
- No file logs — `run` table is the durable record.

Alerting: none in v1. Skill is interactive; the user sees errors in real time.

Degraded modes:
- All sources fail: skill exits with code 1, no AUQ shown.
- Some sources fail: skill processes survivors, surfaces failed sources at the end.
- Sonnet fails entirely: items remain in `discovered`, run reports "0 proposed", cursors do NOT advance.

---

## Section 9: Edge Cases & Boundary Conditions

### EC-1: Empty source delta
**Scenario**: A source has produced no new content since the last cursor.
**Expected Behavior**: Source contributes 0 items. Run summary lists source with `items_discovered=0`. Cursor still updated to "now" (or unchanged for cursor-based APIs).
**Risk if Unhandled**: User confused why nothing showed up; might re-run repeatedly.

### EC-2: Same URL in multiple WhatsApp messages
**Scenario**: Three members share the same gist URL across two days.
**Expected Behavior**: First message produces `matrix_message` + `extracted_link`. Subsequent duplicates produce `matrix_message` items but the `extracted_link` dedup-key collides → only one link item exists in queue.
**Risk if Unhandled**: User shown the same link 3 times → annoyance.

### EC-3: Item URL matches an already-closed bead
**Scenario**: A prompt-kit URL appears in the description of bead CCP-abc which was closed last month.
**Expected Behavior**: Closed beads are NOT in the corpus (active = open + in_progress + blocked + human). Item proceeds to match. After approval, a new bead is created — closed bead's existence is informational only. **Confirmed v1 behaviour**: re-propose freely; v2 may add closed-bead awareness with `--reopen-of` linking.
**Risk if Unhandled**: minimal — user is the only consumer and can manually link related beads when relevant.

### EC-4: Matrix message with markdown / HTML / formatting
**Scenario**: Bridged WhatsApp messages may contain `<br>`, ANSI control chars, raw markdown, emoji shortcodes.
**Expected Behavior**: URL extractor uses a robust regex over plaintext-decoded body. Markdown/HTML tags do not break extraction.
**Risk if Unhandled**: Missed URLs.

### EC-5: Cursor-format drift
**Scenario**: EC MCP changes its pagination cursor format between runs.
**Expected Behavior**: Next run treats unparseable cursor as missing → falls back to "last 7 days" once, surfaces a warning, then resumes normal flow.
**Risk if Unhandled**: Source stuck, no items ever returned.

### EC-6: Massive backlog after long absence
**Scenario**: User skips 8 weeks. Cursor is 56 days old. Source returns 200+ items.
**Expected Behavior**: Skill processes everything but warns "200 items queued — consider --dry-run first". No hard cap (per Round 4 decision: "since last cursor"). User can DEFER en masse if they want.
**Risk if Unhandled**: 50× normal Sonnet spend.

### EC-7: Two simultaneous skill invocations
**Scenario**: User accidentally launches the skill twice.
**Expected Behavior**: SQLite WAL-mode + single-writer lock. Second invocation detects lock and aborts with "another run in progress at PID X".
**Risk if Unhandled**: State corruption, double bead creation.

### EC-8: Empty corpus
**Scenario**: Misconfiguration: skill paths point to empty dirs.
**Expected Behavior**: Skill aborts with "corpus empty — refusing to run; check paths".
**Risk if Unhandled**: Sonnet sees no targets, returns empty arrays for all items, everything filtered out, user sees no findings, no idea why.

---

## Section 10: Dependencies & Integration Points

**External services**:
- **Executive Circle MCP** — read-only, rate limit 120/min/2000/day (per system reminder). v1 uses ~5-10 calls per run. SLA: best-effort, no formal availability guarantee.
- **Matrix Synapse @ matrix.sussdorff.org** — self-hosted, 8GB RAM, behind NetBird/Traefik. Availability matches home-infra availability. CS-API stable.
- **Anthropic API** — for Sonnet match calls. Subject to API status; rate-limit handled per FR-MATCH-004.
- **1Password CLI (`op`)** — required at runtime. User must have an active session.
- **summarize / crwl** — used for extracted-link excerpt fetching. Must already be installed (they are, per CLAUDE.md "Browser/Web Routing").

**Internal services**:
- **bd CLI** — task tracker; required for bead creation.
- **polaris faker pattern** — referenced for PII pseudonymisation; needs a pre-implementation audit (OQ-2).

**Backward compatibility**: First-time run; no existing state to migrate. Schema version 1.

**Rollout**: No phased rollout. Single-user, pure-additive skill. If broken, user just doesn't invoke it.

---

## Section 11: Behavioral Contract

- When the user invokes the skill with no flags and all secrets resolve, the system fetches deltas from every configured source since the per-source cursor.
- When a source HTTP call fails, the system continues processing other sources and surfaces the failed source name + reason in the run summary.
- When 1Password cannot resolve required secrets, the system MUST NOT proceed to fetch any source — it aborts immediately with a clear error.
- When an item's source URL or MCP-ID exactly matches a substring in an open bead's text, the system marks that item `dismissed` with reason `duplicate_of_bead:<id>` and does NOT call Sonnet for it.
- When Sonnet returns scores all below 0.4 for an item, the system marks the item `filtered_out` and does NOT show it to the user.
- When the user chooses APPROVE in the AskUserQuestion prompt, the system creates exactly one bead via `bd create` with all matched targets listed in the body.
- When the user chooses DEFER, the system records `defer_until = now + 28 days` and re-enters the item to `proposed` on the first run after that date.
- When the skill is invoked with `--dry-run`, the system MUST NOT mutate `state.db`, MUST NOT create any beads, and MUST NOT advance any cursor.
- When a previous run left items in `proposed` state, the system places those items at the front of the queue before any newly-fetched items.
- When the SQLite database is locked by another invocation, the system aborts with `another run in progress at PID <X>` and exit code 1.
- When an extracted link's URL fetch fails, the system MUST NOT abort the item — it continues with message-context-only and flags `link_fetch_failed`.
- When two skill invocations would write to state simultaneously, only the first proceeds; the second exits without partial writes.

---

## Section 12: Explicit Non-Behaviors

- The system MUST NOT auto-approve items, even highly-scored ones. Reason: the entire point of the skill is human signal-filtering; auto-approval defeats it.
- The system MUST NOT modify, delete, or close existing beads. Reason: the skill is purely additive; bead lifecycle stays the user's responsibility.
- The system MUST NOT post messages to Matrix, react to messages, or write any data to matrix.sussdorff.org. Reason: read-only access token; any write would be a permission violation.
- The system MUST NOT store raw WhatsApp message bodies on disk or in beads. Reason: PII protection — bridged messages contain personal communication from third parties.
- The system MUST NOT advance a source's cursor when that source's fetch failed. Reason: silent data loss; failed-but-marked-done items would never be retried.
- The system MUST NOT call Anthropic with the full body of a SKILL.md or standard — only the frontmatter description / first paragraph. Reason: token-budget control + no benefit from body content for matching.
- The system MUST NOT create more than one bead per item, even on multi-target matches. Reason: lifecycle management — each bead must be independently closable, multi-target items are tracked as a single "review this item" task with multiple suggested touchpoints in the body.
- The system MUST NOT silently fall back to environment variables when 1Password resolution fails. Reason: secret-management discipline — env-var fallback hides misconfiguration and risks plaintext leaks.

---

## Section 13: Integration Boundaries

### Executive Circle MCP
- **Data Flow In**: search/list queries with filters (date, query string), get-by-ID requests
- **Data Flow Out**: post/kit/guide titles, IDs, snippets, full bodies (only when get_* called)
- **Failure Mode**: source marked `failed:ec_mcp_<reason>`, cursor unchanged, run summary surfaces; other sources continue
- **Timeout Strategy**: 30s per call; 3 retries with exponential backoff (1s, 5s, 15s); after that, mark source failed

### Matrix Client-Server API (matrix.sussdorff.org)
- **Data Flow In**: GET /_matrix/client/v3/sync (with filter for one room), GET /_matrix/client/v3/rooms/<id>/messages (catch-up)
- **Data Flow Out**: room timeline events including message bodies, sender MXIDs, event IDs, server timestamps
- **Failure Mode**: source marked `failed:matrix_<reason>`; same independence as EC. Connection refused / 5xx / timeout all map to the same reason class for cursor-safety.
- **Timeout Strategy**: 30s per call; 3 retries with exponential backoff; sync token unchanged on failure

### Host Claude Code session (in-context match)
- **Data Flow In**: `match-input.json` written by the helper script — `{ corpus: [...], items: [...] }`
- **Data Flow Out**: `match-output.json` written by the skill body after the host model produces match arrays
- **Failure Mode**: invalid JSON output → helper script aborts the run (no partial state); subscription-tier limits surface as natural session errors
- **Timeout Strategy**: none — limited only by host context and session length; if the run is too large the skill instructs the user to use `--source` to scope

### 1Password CLI
- **Data Flow In**: `op read op://Private/matrix-readonly-token/credential`, `op read op://Private/anthropic-api-key/credential`
- **Data Flow Out**: secret strings (held only in memory)
- **Failure Mode**: aborts the entire run before any source fetch — fail-fast (per FR-INGEST and NFR-SEC-001)
- **Timeout Strategy**: 10s per resolution; no retry (op is local)

### bd CLI (beads)
- **Data Flow In**: `bd list --status=open --json` (corpus build), `bd create ...` (approval dispatch)
- **Data Flow Out**: open-bead JSON list, new bead ID
- **Failure Mode**: corpus build failure aborts the run (no graceful degradation here — backlog dedup is critical). Dispatch failure leaves item in `proposed`, surfaces in run summary.
- **Timeout Strategy**: 15s per shell-out

### summarize / crwl (extracted-link enrichment)
- **Data Flow In**: URL
- **Data Flow Out**: 1-paragraph excerpt
- **Failure Mode**: per-item soft-fail with `link_fetch_failed=true`; never aborts run
- **Timeout Strategy**: 30s; no retries

---

## Section 14: Ambiguity Warnings

- **AW-1**: ~~Tier-4 ordering~~ — RESOLVED 2026-04-26: extracted link follows its parent message immediately, then next message-by-timestamp (FR-APPROVE-001 updated).
- **AW-2**: "Active member of the room" is undefined for FR-INGEST-003 — Likely agent assumption: the existing user account (Malte's MXID) has a long-lived access token created via `synapse-admin` or device login — Question: which Matrix user/device generates the access token, and is the token rotation policy documented? (see OQ-3)
- **AW-3**: ~~Bead-status set for dedup corpus~~ — RESOLVED 2026-04-26: active = `open` + `in_progress` + `blocked` + `human` (FR-CORPUS-004 updated).
- **AW-4**: Content-type detection for extracted links is unspecified — Likely agent assumption: try `crwl crawl URL -o md` first, fall back to `summarize` skill for YouTube/podcast/audio — Question: codify the routing table at implementation time; defaults are acceptable.
- **AW-5**: Cursor format for EC MCP is undocumented — Likely agent assumption: ISO8601 timestamp filter on `list_recent_posts(since=...)` — Question: does the MCP actually accept a `since` parameter, or do we need to fetch + post-filter client-side? (see OQ-1)
- **AW-6**: Polaris faker pattern is referenced but not specified — Likely agent assumption: import a faker module from polaris and apply a name/email replacement — Question: what's the exact polaris module/function/contract? (resolves with OQ-2 audit)
- **AW-7**: ~~Closed-bead awareness for dedup~~ — RESOLVED 2026-04-26: v1 ignores closed beads; same item may resurface as a fresh proposal months after the original bead closed. v2 may add closed-bead awareness.

---

## Section 15: Open Questions / Risks

- **OQ-1** (Medium): EC MCP cursor mechanism — does `list_recent_posts` accept a `since` timestamp? If not, we must fetch a fixed page and dedup client-side. **Owner**: Malte (verify with 1 manual call to MCP). **Suggested resolution**: before implementation kick-off.
- **OQ-2** (High): Polaris faker pattern audit — concrete module path, function signature, and pseudonymisation guarantees. **Owner**: Malte + spec-developer. **Suggested resolution**: 1-day spike before NFR-SEC-002 implementation.
- **OQ-3** (Medium): Matrix access token provisioning — which device/MXID, where stored in 1Password, rotation policy. **Owner**: Malte (operational decision tied to home-infra). **Suggested resolution**: before first live run.
- **OQ-4** (Low): Should the skill auto-supersede an existing prompt-kit-review bead when a newer version of the same kit appears? **Owner**: deferred to v2.
- **OQ-5** (Low): Closed-bead awareness for dedup (EC-3). v1 ignores closed beads. v2 may surface "this matches a previously-closed bead — reopen?" prompt. **Owner**: deferred.
- **OQ-6**: ~~Sonnet model alias~~ — OBSOLETE: in-session match (FR-MATCH-001) means the host model is whichever Claude Code is running. No version pin needed.

**Risk register**:
- **R-1** (Medium): Sonnet cost spike if a single run hits a backlog of 200+ items. Mitigation: NFR-PERF-002 alerts on 2× budget; user can `--source` filter or dry-run first.
- **R-2** (Low): Matrix sync token format change in a future Synapse upgrade. Mitigation: cursor-format-drift fallback (EC-5 pattern applies to Matrix too).
- **R-3** (Low): MCP rate-limit (120/min) hit during corpus build. Mitigation: corpus build only uses list/search, not get_*; estimated 5-10 calls per run.

---

## Section 16: Glossary

| Term | Definition |
|------|-----------|
| AIEC | Nate's AI Exec Circle — both the Executive Circle newsletter brand and the WhatsApp/Matrix discussion group |
| Corpus | The aggregate of skills, agents, standards, and open beads against which incoming items are matched |
| Dedup-key | The natural ID per source (MCP-ID, Matrix event_id, or canonical URL hash) used to prevent re-proposing items |
| Findings table | The in-memory ordered queue of `proposed` items shown to the user during the AUQ approval flow |
| Item | A single unit reviewed by the skill — one prompt-kit, post, guide, Matrix message, or extracted link |
| Source | One configured input channel (`ec_posts`, `ec_kits`, `ec_guides`, `matrix_aiec`) with its own cursor |
| Tier | Priority class per source (1=prompt-kits, 2=posts, 3=guides, 4=Matrix) controlling presentation order |

---

## Phase 4 Self-Review

Per the spec-developer Phase 4 protocol, the spec author identifies remaining ambiguities — see Section 14 (Ambiguity Warnings) and Section 15 (Open Questions). The most material gaps before implementation handoff:

1. **OQ-2 (polaris faker audit)** — High risk; PII handling pivots on this.
2. **OQ-1 (EC MCP cursor)** — Medium; if `since` is unsupported, FR-INGEST-001 needs a different cursor strategy (e.g. `last_seen_id` + dedup-key check).
3. **OQ-3 (Matrix token provisioning)** — Medium; blocks first live run.
4. **AW-4 (extracted-link extractor selection)** — fillable with a short decision table during implementation.

The remaining AW items are filler-with-defaults at implementation time and are not blocking.
