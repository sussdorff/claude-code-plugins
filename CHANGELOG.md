## [unreleased]

### 📚 Documentation

- *(CCP-pof)* UAT audit of 44 projects, cross-repo fixture design strategy, and per-project-type UAT standard (`docs/architecture/uat-audit-2026.md`, `standards/workflow/uat-fixtures.md`)

### 🚀 Features

- *(CCP-6n3)* **Daily-brief auto-discovery** — `scripts/discover-projects.py` detects active projects not in config by scanning ~/.claude/projects/ JSONL files and ~/code/ git repos modified within the time window. `orchestrate-brief.py --all-active` flag bypasses config and uses only discovery heuristics. Active-but-unconfigured projects surface as a warning block at the top of the brief. Does not auto-add to config. Robust against malformed JSONL and unreadable repos (logs warning, continues). 41 tests pass.
- *(CCP-51k)* **Daily-brief orchestration CLI** — `scripts/orchestrate-brief.py` ties config + query + render into a usable `/daily-brief` skill. Supports all CLI args (`--since=Nd`, `--date=YYYY-MM-DD`, `--range=START..END`, `--detailed`, positional project name). Implements backfill no-op (brief_exists check prevents re-writing already-persisted days). Saves each new brief to open-brain as `type=daily_brief` with idempotent `session_ref`. Range rollup delegates to render-brief.py range mode. SKILL.md updated with triggers (daily brief, tagesbericht, was hatte ich gestern gemacht). 31 tests. Also fixes render-brief.py persist bug (brief_path was called with wrong signature).
- *(CCP-lx2)* **Daily-brief capability extractor + diary-style renderer** — `capability-extractor.py` parses closed bead titles/descriptions and session summaries (New:/Fixed:/Internal: prefixes) for capability signals (both feature and task beads qualify); `render-brief.py` renders v1.0 Chief-of-Staff markdown in Voice B (German, journalistic narrator, past tense) with 6 sections: Executive Summary, Was sich verändert hat, Warum es zählt, Offene Fäden, Nächste sinnvolle Schritte (max 3 items with source citation), Belege; range mode with compressed rollup; 77 tests.
- *(CCP-top)* **Daily-brief data aggregator** (query-sources.py) collects closed/open beads, git commits, session summaries, decisions, and rework signals from open-brain and bd; deterministic JSON output conforming to execution-result envelope
- *(CCP-ijh)* Daily-brief config schema + per-project brief storage layout
- *(CCP-h8h)* Eliminate in-repo Codex mirrors: enforce dev-repo principle (`rm -rf` invariant). Delete `.agents/` (72 skill mirrors) and `.codex/` (3 agent mirrors). Rewrite `sync-codex-skills` and `sync-codex-agents` to target user-scoped dirs only. Fix CI: skill-audit.yml now uses canonical `meta/skills/skill-auditor/` validator. Add `docs/architecture/dev-repo-principle.md` and `tests/test_dev_repo_principle.py`.

### 🐛 Bug Fixes

- *(CCP-scw5)* **Daily-brief open-brain auth fix** — `_OBClient.search()` in `query-sources.py` and `_async_save_memory()` in `orchestrate-brief.py` now send `x-api-key` header instead of `Authorization: Bearer`. The open-brain HTTP MCP endpoint validates Bearer tokens as JWTs; raw `ob_` api_keys are opaque strings that must go in `x-api-key`. Also adds 401-specific `PermissionError` with actionable guidance pointing to `~/.open-brain/config.json`. Regression tests: happy-path (header assertion via `httpx.MockTransport`) + 401-path (actionable warning propagation). 95 tests passing.
- *(CCP-die)* **Codex diff resolution** now uses size-based budgeting instead of file-count cap, with bounded guidance for large-diff fallback
- *(CCP-b9d)* Use ${CLAUDE_PLUGIN_ROOT} for plugin script paths + add lint gate
- *(CCP-ijh)* Remove unused 'field' import from dataclasses
- *(CCP-0ho)* Correct council-roles.yml default path from malte/ to business/ in bead-orchestrator Phase 3
- *(CCP-ahs)* Code-layer claim gate: prevent double-launch via claim.py + cld/wave pre-flight
- *(CCP-yosw)* **Daily-brief open-brain integration** — `query-sources.py` and `orchestrate-brief.py` now instantiate `ob_client` automatically from `~/.open-brain/config.json` when OB_TOKEN env var and token file are not present. Live briefs include session/learning/decision data from open-brain. Writing a brief creates idempotent `type=daily_brief` observation in open-brain per session_ref. URL resolution independent of token source. 89 tests passing.

### 🧪 Testing

- *(CCP-i8g)* **Daily-brief integration test** — validates live data across all 4 configured projects with `--since=7d`, range behavior (compressed rollup output), and persistence. Reference docs: `data-sources.md` (canonical field→source map, dedup rules, fallback behavior), `config-schema.md` (full schema with examples), and sample output (`docs/examples/daily-brief-sample.md`) reviewed against Product Contract.
- *(verification-provenance)* Update stale tests to match renumbered phases

### 🚜 Refactor

- *(CCP-4h1)* Extract inline code to scripts across 6 business skills (amazon, collmex-cli, google-invoice, mail-send, mm-cli, op-credentials) — 17 scripts extracted, 0 CI violations
- *(CCP-9t5)* Extract inline shell code from core skills (cmux, dolt, event-log) to scripts — fixes EXTRACTABLE_CODE validation failures
- *(CCP-tox)* Extract inline code from dev-tools skills (codex, playwright-cli, vision-author) to scripts — fixes EXTRACTABLE_CODE validation failures

### ⚙️ Miscellaneous Tasks

- Bump actions to Node 24 (checkout@v5, setup-python@v6)
- Re-trigger workflow on its own YAML changes
- *(CCP-xib)* Remove unreliable screen-lock check from session-close; treat git push failure as notification

## [2026.04.100] - 2026-04-22

### 🚀 Features

- *(CCP-67x)* Codex bead-orchestrator and wave-orchestrator TOML agents + evidence

### 🐛 Bug Fixes

- *(CCP-67x)* Address review findings — version-control TOMLs, Phase 3, WAVE_ID, evidence doc

### ⚙️ Miscellaneous Tasks

- Preserve unreleased changelog entry before merge
- *(CCP-67x)* Update changelog
- *(CCP-67x)* Stage bead state updates to issues.jsonl
- *(CCP-67x)* Sync issues.jsonl after main merge
- *(CCP-67x)* Re-export issues.jsonl (memory order normalisation)
- *(CCP-67x)* Final issues.jsonl sync before ship
## [2026.04.99] - 2026-04-22

### 🐛 Bug Fixes

- HANDLERS_DIR path bug + ci-monitor + git-state helpers for session-close

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.99 and release changelog
## [2026.04.98] - 2026-04-22

### 🐛 Bug Fixes

- *(CCP-1bo)* Wave-dispatch --surface flag, scenario pre-flight gate

### ⚙️ Miscellaneous Tasks

- Add embeddeddolt/ to .gitignore + skill-audit CI workflow
- *(CCP-1bo)* Bump version to 2026.04.98 and release changelog
## [2026.04.97] - 2026-04-22

### ⚙️ Miscellaneous Tasks

- *(CCP-o4z)* Bump version to 2026.04.97 and release changelog
## [2026.04.96] - 2026-04-22

### 🚀 Features

- Session-close serializer + wave-orchestrator single-instance guard
- Skill-auditor validator, wave-dispatch workspace fix, planning docs

### ⚙️ Miscellaneous Tasks

- *(CCP-28l)* Update bead state for session close
- Bump version to 2026.04.96 and release changelog
## [2026.04.95] - 2026-04-22

### ⚙️ Miscellaneous Tasks

- Merge origin/main into worktree-bead-CCP-28l (resolve issues.jsonl conflict)
- *(CCP-28l)* Bump version to 2026.04.95 and release changelog
## [2026.04.94] - 2026-04-22

### 🚀 Features

- *(CCP-o4z)* Green — session-end Stop hook for beads-workflow
- *(CCP-6s1)* Add --exclude-pattern flag to check-debrief-adherence.py

### 🐛 Bug Fixes

- *(wave-monitor)* Reduce poll interval from 270s to 60s
- *(CCP-o4z)* Address review findings iteration 1
- *(CCP-o4z)* Address codex adversarial findings
- *(CCP-28l)* Fix prompt tail-truncation and document timeout Bash wrapper alignment
- *(CCP-6s1)* Match exclude-pattern against relative path not absolute

### 📚 Documentation

- *(CCP-28l)* Document Codex timeout threshold and add pre-truncation guard

### 🧪 Testing

- *(CCP-o4z)* Red — session-end hook test suite

### ⚙️ Miscellaneous Tasks

- *(CCP-6s1)* Update bead state for session close
- *(CCP-6s1)* Bump version to 2026.04.94 and release changelog
## [2026.04.93] - 2026-04-22

### 🐛 Bug Fixes

- *(CCP-4gi)* Sync TOML port with session-close.md handoff and metadata.source changes

### 🚜 Refactor

- *(CCP-4gi)* Enrich session-close debrief with handoff aggregation and metadata.source

### ⚙️ Miscellaneous Tasks

- *(CCP-4gi)* Bump version to 2026.04.93 and release changelog
## [2026.04.92] - 2026-04-22

### ⚙️ Miscellaneous Tasks

- *(CCP-5xe)* Bump version to 2026.04.92 and release changelog
## [2026.04.91] - 2026-04-22

### 🐛 Bug Fixes

- *(codex-exec)* Redirect stdin from /dev/null to prevent interactive wait

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.91
## [2026.04.90] - 2026-04-22

### 🚀 Features

- *(codex-exec)* Add --diff-range flag for inline vs self-collect diff handling

### 🐛 Bug Fixes

- *(CCP-e7a)* Remove debrief from strict-output agents, exempt in standard, fix scout fence

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.90
## [2026.04.89] - 2026-04-22

### ⚙️ Miscellaneous Tasks

- *(CCP-e7a)* Bump version to 2026.04.89 and release changelog
## [2026.04.88] - 2026-04-22

### 🚀 Features

- *(CCP-e7a)* Add debrief template to all non-exempt agent prompts

### 🐛 Bug Fixes

- *(CCP-5xe)* Fix shell-unsafe debrief piping and handoff file cleanup
- *(CCP-5xe)* Safe JSON serialization via tempfile, preserve handoff for debrief-only retries

### 🚜 Refactor

- *(CCP-5xe)* Bead-orchestrator aggregates subagent debriefs via parse_debrief.py and handoff file

### ⚙️ Miscellaneous Tasks

- *(CCP-5xe)* Bump version to 2026.04.88 and release changelog
## [2026.04.87] - 2026-04-22

### ⚙️ Miscellaneous Tasks

- *(CCP-9bm)* Merge main into feature branch, resolve changelog conflict
- *(CCP-9bm)* Bump version to 2026.04.87 and release changelog
## [2026.04.86] - 2026-04-22

### 🚀 Features

- *(CCP-9bm)* Green — parse_debrief.py stdlib parser for subagent debrief sections
- *(CCP-9bm)* Green — check-debrief-adherence.py lint script + test import fix
- *(CCP-9bm)* Green — add debrief template to 5 required agent prompts
- *(CCP-k1m)* Non-interactive session-close mode with resume support

### 🐛 Bug Fixes

- *(CCP-k1m)* Address review findings iteration 1

### 📚 Documentation

- *(CCP-9bm)* Add changelog entry for debrief return contract

### 🧪 Testing

- *(CCP-9bm)* Red — parse_debrief test suite (all 4 headings, embedded, empty sections, CLI)
- *(CCP-9bm)* Red — check-debrief-adherence test suite (conforming, missing, exempt, CLI)
- *(CCP-k1m)* Red — non-interactive session-close mode test suite

### ⚙️ Miscellaneous Tasks

- *(CCP-k1m)* Bump version to 2026.04.86 and release changelog
## [2026.04.85] - 2026-04-22

### 🐛 Bug Fixes

- *(CCP-6up.5)* Address review findings iteration 1
- *(CCP-6up.5)* Address auto-fixable verification disputes
- *(CCP-6up.5)* Correct bead-metrics inventory row and remove obsolete __future__ import

### 🚜 Refactor

- *(CCP-6up.5)* Green — add increment_auto_decisions to metrics.py
- *(CCP-6up.5)* Green — extract wave-monitor bash to wave-poll.py
- *(CCP-6up.5)* Green — update agents and smoke test to use extracted helpers

### 🧪 Testing

- *(CCP-6up.5)* Red — increment_auto_decisions tests
- *(CCP-6up.5)* Red — wave-poll.py unit tests

### ⚙️ Miscellaneous Tasks

- *(CCP-6up.5)* Update bead state for session close
- Bump version to 2026.04.85
## [2026.04.84] - 2026-04-22

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.84
## [2026.04.83] - 2026-04-22

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.83
## [2026.04.82] - 2026-04-22

### 🚀 Features

- *(CCP-hf1)* Green — vision_renderer.py and vision_conformance.py
- *(CCP-hf1)* Green — vision-author skill, template, smoke-test checklist
- *(CCP-6up.3)* Green — add validate-skill.py for EXTRACTABLE_CODE enforcement in SKILL.md
- *(CCP-6up.3)* Green — wire validate-skill into skill-auditor SKILL.md and agent
- *(CCP-a67)* Green — vision_review.py + mock_council fixture (22 tests passing)
- *(CCP-a67)* Add vision-review SKILL.md with trinity_role enforcer-reactive

### 🐛 Bug Fixes

- *(CCP-hf1)* Address review findings iteration 1
- *(CCP-6up.3)* Address review findings iteration 1
- *(wave-dispatch)* Propagate WAVE_ID into bead_runs.wave_id
- *(wave-completion)* Fix metrics sanity check defaults and safety
- *(CCP-a67)* Address review findings iteration 1

### 📚 Documentation

- *(CCP-hf1)* Update changelog with vision-author skill
- Update changelog for CCP-6up.3 (skill-authoring Enforcer-Reactive)

### 🧪 Testing

- *(CCP-hf1)* Red — vision-author unit tests (renderer, conformance, tense-gate)
- *(CCP-6up.3)* Red — EXTRACTABLE_CODE enforcement tests for validate-skill.py
- *(CCP-a67)* Red — vision-review test suite (health score, ADR gen, report gen, smoke)

### ⚙️ Miscellaneous Tasks

- *(open-brain-7lz)* Bump version to 2026.04.81, update changelog
- *(CCP-a67)* Update bead state and changelog
- *(CCP-a67)* Add changelog entry for vision-review skill
- *(CCP-a67)* Update bead state for session close
- Bump version to 2026.04.82
## [2026.04.80] - 2026-04-22

### 🚀 Features

- Add script-first execution result contract

### 🐛 Bug Fixes

- *(codex-exec)* Degrade gracefully when metrics DB unavailable

### 🚜 Refactor

- *(beads-workflow)* Extract inline metrics code into dedicated shell scripts

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.80
## [2026.04.79] - 2026-04-22

### 🚀 Features

- *(CCP-9yd)* Add Codex session-close agent TOML with gap documentation

### 🐛 Bug Fixes

- *(CCP-9yd)* Address review findings iteration 1

### ⚙️ Miscellaneous Tasks

- Sync issues.jsonl from main merge
- Merge worktree-bead-CCP-9yd (resolve evidence file conflict)
- Bump version to 2026.04.79
## [2026.04.78] - 2026-04-22

### 🚀 Features

- *(CCP-9yd)* Green — create Codex session-close agent TOML
- *(CCP-e2r)* Collapse session-close step-handlers into phase-level batch handlers
- *(CCP-9yd)* Add E2E evidence for Codex session-close agent run

### 🐛 Bug Fixes

- *(CCP-e2r)* Address review findings — idempotency, error handling, regex fixes
- *(CCP-9yd)* Address review findings iteration 1

### 🧪 Testing

- *(CCP-9yd)* Red — validate codex session-close agent TOML structure

### ⚙️ Miscellaneous Tasks

- Update changelog for CCP-e2r
- Bump version to 2026.04.78
## [2026.04.77] - 2026-04-22

### ⚙️ Miscellaneous Tasks

- *(CCP-8tb)* Sync trampoline stub to .agents/skills/skill-auditor
- Bump version to 2026.04.77
## [2026.04.76] - 2026-04-22

### 🚀 Features

- *(CCP-dnk)* Port wave-orchestrator to Sonnet subagent, wire in wave-monitor

### ⚙️ Miscellaneous Tasks

- *(CCP-dnk)* Update changelog for wave-orchestrator agent migration
## [2026.04.75] - 2026-04-22

### 🚀 Features

- *(session-close)* Auto-deploy codex skills after CC plugin update

### 🐛 Bug Fixes

- *(CCP-793)* Harden quick-fix session-close handoff
- *(skill-auditor)* Flag description overflow >1024 chars as blocking

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.75
## [2026.04.74] - 2026-04-22

### 🚀 Features

- *(CCP-aoc)* Add wave-monitor Haiku agent for wave polling

### 🧪 Testing

- *(CCP-aoc)* Add smoke test for wave-monitor verdict routing

### ⚙️ Miscellaneous Tasks

- *(CCP-aoc)* Update changelog for wave-monitor agent
- Bump version to 2026.04.74
## [2026.04.73] - 2026-04-21

### 🚀 Features

- *(CCP-8tb)* Convert skill-auditor to Opus subagent with trampoline skill

### 💼 Other

- *(CCP-ar0)* Document parent-session parking spike verdict

### ⚙️ Miscellaneous Tasks

- *(CCP-8tb)* Update changelog for skill-auditor subagent migration
- Bump version to 2026.04.73
## [2026.04.72] - 2026-04-21

### 🐛 Bug Fixes

- *(CCP-9xy)* Harden bead agents against mid-flow stops and session-close handoff failures
- *(CCP-1m6)* Address codex adversarial findings — non-hermetic test, namespace filter, orchestrator_handled

### 💼 Other

- Worktree-bead-CCP-1m6

### 🧪 Testing

- *(CCP-1m6)* Add structural coverage test for agent-standards.yml

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.72 and update changelog for CCP-9xy
- *(CCP-1m6)* Update changelog
- Bump version to 2026.04.72
## [2026.04.71] - 2026-04-21

### 💼 Other

- Worktree-bead-CCP-imb

### ⚙️ Miscellaneous Tasks

- *(CCP-imb)* Sync issues.jsonl post-merge
- *(CCP-imb)* Absorb issues.jsonl auto-export drift
- *(CCP-imb)* Stabilize issues.jsonl export
- *(CCP-imb)* Add CHANGELOG entry for rollup_run null-safety
- Bump version to 2026.04.71
## [2026.04.70] - 2026-04-21

### 💼 Other

- Worktree-bead-CCP-2hd.1

### ⚙️ Miscellaneous Tasks

- *(CCP-2hd.1)* Move changelog entry to [unreleased] after folded merge from main
- Bump version to 2026.04.70
## [2026.04.69] - 2026-04-21

### 💼 Other

- Worktree-bead-CCP-dzp

### ⚙️ Miscellaneous Tasks

- *(CCP-dzp)* Sync issues.jsonl after merge
- Bump version to 2026.04.69
## [2026.04.68] - 2026-04-21

### 🐛 Bug Fixes

- *(CCP-dzk)* Address codex adversarial findings

### ⚙️ Miscellaneous Tasks

- *(CCP-dzk)* Update changelog
- Bump version to 2026.04.68
## [2026.04.67] - 2026-04-21

### 💼 Other

- Sync issues.jsonl from origin/main
- Worktree-bead-CCP-2n7

### ⚙️ Miscellaneous Tasks

- Refresh issues.jsonl export
- Update changelog for CCP-2n7
- Bump version to 2026.04.67
## [2026.04.66] - 2026-04-21

### 🚀 Features

- *(CCP-2hd.1)* Normalize touched_paths to canonical packages before vision boundary check
- *(CCP-2n7)* Green — SubagentStop adhoc metrics implementation
- *(CCP-dzk)* Green — fix fnmatch normalization and test runner for subagent hook

### 🐛 Bug Fixes

- *(CCP-imb)* Guard rollup_run against null run_id + log orphan agent_calls
- *(CCP-2hd.1)* Address review findings iteration 1
- *(CCP-dzp)* Green — propagate codex exec timeout via CODEX_EXEC_TIMEOUT wrapper
- *(CCP-2n7)* Address review findings iteration 1
- *(CCP-dzk)* Address review findings iteration 1
- *(CCP-mit)* Use subshell cd for bd dolt start in worktree hook
- *(CCP-mit)* Handle WorktreeCreate payload format (cwd+name fallback)
- *(CCP-mit)* Exclude worktrees/ from .claude rsync to prevent recursive copies

### 💼 Other

- Worktree-bead-CCP-mit

### 🧪 Testing

- *(CCP-imb)* Red — rollup_run drops silently on null run_id
- *(CCP-dzp)* Red — codex-exec.sh must exit non-zero on timeout
- *(CCP-2n7)* Red — failing tests for SubagentStop adhoc metrics hook
- *(CCP-dzk)* Red — inject-subagent-standards hook tests

### ⚙️ Miscellaneous Tasks

- *(CCP-imb)* Update beads issues.jsonl with close-reason note
- *(CCP-imb)* Sync issues.jsonl pre-merge (bd auto-export)
- *(CCP-imb)* Sync issues.jsonl after bd dolt pull
- *(CCP-imb)* Final sync issues.jsonl before merge
- *(CCP-2hd.1)* Add changelog entry
- *(CCP-2hd.1)* Reconcile issues.jsonl before merge from main
- *(CCP-dzp)* Refresh issues.jsonl after bd updates
- *(CCP-mit)* Add WorktreeCreate hook, deprecate worktree-manager
- *(CCP-mit)* Sync issues.jsonl from main merge
- Bump version to 2026.04.66
## [2026.04.65] - 2026-04-21

### 💼 Other

- Worktree-bead-CCP-50y

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.65
## [2026.04.64] - 2026-04-21

### 🚀 Features

- *(CCP-50y)* Green — extend sync-codex-skills with multi-directory registry
- *(CCP-50y)* Green — convert 10 candidate skills to portable format
- *(CCP-50y)* Green — sync 10 converted skills to .agents/skills
- *(CCP-rjq)* Add Phase 1.25 wave-review-gate to wave-orchestrator
- *(CCP-rjq)* Add Phase 1.25 wave-review-gate to wave-orchestrator

### 🐛 Bug Fixes

- *(CCP-50y)* Address review findings iteration 1
- *(CCP-rjq)* Address adversarial findings — initialize PHASE_125_ARCH_FINDINGS, dry-run path-B guard, re-review trigger

### 💼 Other

- Worktree-bead-CCP-rjq

### 🧪 Testing

- *(CCP-50y)* Red — portability tests for 10 candidate skills

### ⚙️ Miscellaneous Tasks

- *(CCP-50y)* Add changelog entry
- Update changelog (pre-merge commit from main)
- *(CCP-rjq)* Update bead tracker state
- *(CCP-rjq)* Reconcile issues.jsonl after first merge from main
- Update changelog
- Bump version to 2026.04.64
## [2026.04.63] - 2026-04-21

### 💼 Other

- Worktree-bead-CCP-pvw

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.63
## [2026.04.62] - 2026-04-21

### 🚀 Features

- *(CCP-5d0)* Load CLAUDE.md and AGENTS.md when both exist in project-context skill

### 🐛 Bug Fixes

- *(CCP-pvw)* Correct quality-B trigger, B/C ambiguity, and output ordering

### 💼 Other

- *(CCP-pvw)* Absorb factory-check quality criteria into wave-reviewer
- Worktree-bead-CCP-5d0

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.62
## [2026.04.61] - 2026-04-21

### 🐛 Bug Fixes

- *(CCP-2vo.10)* Update model-strategy.yml comment after cmux-reviewer removal

### 💼 Other

- *(CCP-2vo.10)* Delete 2-pane review infrastructure (cmux-reviewer + cld -br + codex-watch.sh)

### ⚙️ Miscellaneous Tasks

- *(CCP-2vo.10)* Delete 2-pane review infrastructure
## [2026.04.60] - 2026-04-20

### 🐛 Bug Fixes

- *(CCP-2vo.8)* Restore issues.jsonl drift, fix non-existent bd metrics commands
- *(CCP-2vo.8)* Replace non-existent wall_clock_s with impl_duration_ms in dispatch query

### 💼 Other

- Worktree-bead-CCP-2vo.7
- *(CCP-2vo.8)* Add validation infrastructure — canonical beads, sibling dispatch, retrospective template
- Worktree-bead-CCP-2vo.8

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.60
## [2026.04.59] - 2026-04-20

### 💼 Other

- Worktree-bead-CCP-2vo.7

### ⚙️ Miscellaneous Tasks

- Sync issues.jsonl bead state
- Sync issues.jsonl bead state (close CCP-2vo.7)
- Bump version to 2026.04.59
## [2026.04.58] - 2026-04-20

### 🚀 Features

- *(CCP-c2p)* Green — 3 pilot skills synced; openai.yaml metadata; decisions locked; evidence captured

### 🐛 Bug Fixes

- *(CCP-c2p)* Address review findings iteration 1 — hermetic tests + stronger evidence scope
- *(CCP-c2p)* Address review findings iteration 2 — honest evidence scope (Option B)

### 💼 Other

- *(CCP-2vo.7)* Add auto-decisions + token breakdown to Phase 7 learnings report
- Worktree-bead-CCP-c2p

### 🧪 Testing

- *(CCP-c2p)* Red — pilot skill surface, sync, evidence, decisions

### ⚙️ Miscellaneous Tasks

- *(beads)* Sync issues.jsonl state
- *(beads)* Sync issues.jsonl state
- Bump version to 2026.04.58
## [2026.04.57] - 2026-04-20

### 💼 Other

- Worktree-bead-CCP-2vo.5

### ⚙️ Miscellaneous Tasks

- Update changelog
- Sync issues.jsonl bead state
- Update changelog
- Bump version to 2026.04.57
## [2026.04.56] - 2026-04-20

### 🐛 Bug Fixes

- *(CCP-2vo.5)* Agent_calls from metrics.db, idempotent stall notes
- *(CCP-2vo.5)* Epoch-second sqlite comparison, temp-file stall idempotency
- *(CCP-2vo.6)* Address codex adversarial findings — LAST_SHA, RUN_ID fallback, phase2 metrics

### 💼 Other

- *(CCP-2vo.5)* Wave-orchestrator 1-pane budget + stall detection

### ⚙️ Miscellaneous Tasks

- *(CCP-2vo.6)* Migrate quick-fix to codex-exec.sh, fix session-close handoff
- Sync issues.jsonl bead state
- Bump version to 2026.04.56
## [2026.04.55] - 2026-04-20

### 🚀 Features

- *(CCP-2vo.4)* Rewrite bead-orchestrator flat 0-16, single-pane, inline Codex via codex-exec.sh

### 🐛 Bug Fixes

- *(CCP-2vo.4)* Address review findings — stale phase refs in frontmatter, error table, constraints

### 💼 Other

- Worktree-bead-CCP-2vo.4

### 🧪 Testing

- *(CCP-2vo.4)* Add forced-path fixture specs A/B/C/D for flat 0-16 orchestrator

### ⚙️ Miscellaneous Tasks

- Sync issues.jsonl bead state
- Sync issues.jsonl bead state
- Sync issues.jsonl bead state
- Bump version to 2026.04.55
## [2026.04.54] - 2026-04-20

### 💼 Other

- Worktree-bead-CCP-2vo.9

### ⚙️ Miscellaneous Tasks

- Sync issues.jsonl bead state
- Bump version to 2026.04.54
## [2026.04.53] - 2026-04-20

### 💼 Other

- Worktree-bead-CCP-tkd

### ⚙️ Miscellaneous Tasks

- *(beads)* Sync issues.jsonl state
- Bump version to 2026.04.53
## [2026.04.52] - 2026-04-20

### 🚀 Features

- *(CCP-2vo.9)* Green — add Provenance Compliance Checks, upgrade model to opus
- *(CCP-tkd)* Green — extract portable skill cores + Claude harness adapters

### 🐛 Bug Fixes

- *(CCP-2vo.9)* Address review findings iteration 1
- *(CCP-2vo.9)* Address review findings iteration 2
- *(CCP-2vo.9)* Cmux review iter 1 — VETO integrity, docs state consistency, empty provenance normalization
- *(CCP-2vo.9)* Cmux review iter 2 — missing-file fixability: human → auto
- *(CCP-tkd)* Address review findings iteration 1
- *(CCP-tkd)* Address review findings iteration 2 — polish
- *(CCP-tkd)* Update test_skill_structure to reflect portability split (adapter owns argument-hint)
- *(CCP-tkd)* Restore runtime frontmatter (model, disable-model-invocation) to spec-developer SKILL.md
- *(CCP-tkd)* Remove Claude tool name leaks from portable cores; add Rule 6 + test patterns (F3)
- *(CCP-2vo.3)* Normalize model name for rollup + capture python exit code
- *(CCP-2vo.3)* Use additive total_tokens formula + capture reasoning_output_tokens

### 💼 Other

- *(CCP-2vo.3)* Add codex-exec.sh wrapper with turn.completed token capture
- Worktree-bead-CCP-2vo.3

### 🧪 Testing

- *(CCP-2vo.9)* Red — TestModelUpgrade, TestVetoChecks, TestAdvisoryCheck, TestOutputFormatUpdated, TestInformationBarriersUpdated
- *(CCP-tkd)* Red — portability split assertions for 3 pilot skills

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.52
## [2026.04.51] - 2026-04-20

### 💼 Other

- Bring in origin/main (first merge — resolve metrics.py import conflict)
- Worktree-bead-CCP-2vo.1

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.51
## [2026.04.50] - 2026-04-20

### 💼 Other

- Worktree-bead-CCP-u01

### ⚙️ Miscellaneous Tasks

- *(beads)* Sync issues.jsonl with main branch state
- Bump version to 2026.04.50
## [2026.04.49] - 2026-04-20

### 🚀 Features

- *(metrics)* Backfill_codex.py retroactive Codex attribution tool
- *(CCP-2vo.1)* Fix verification_tokens silent-fail + provenance contract
- *(CCP-2vo.2)* Add run_id identity, agent_calls table, Python insert API
- *(CCP-u01)* Add sync-codex-skills script with --check and --user modes

### 🐛 Bug Fixes

- *(CCP-2vo.1)* Address review findings iteration 1
- *(CCP-2vo.1)* Address review findings iteration 2
- *(CCP-2vo.1)* Harden verification token capture against special chars
- *(CCP-2vo.2)* Thread run_id through insert_bead_run, upsert_ccusage_row, update_phase2_metrics
- *(CCP-u01)* Guard empty skills tokens and fatal-error on missing sources
- *(CCP-u01)* Restore issues.jsonl to pre-implementation snapshot

### 📚 Documentation

- *(codex-skills)* Align rollout plan with machine-state and refined wave

### 🧪 Testing

- *(CCP-2vo.1)* Red — verification provenance contract

### ⚙️ Miscellaneous Tasks

- *(beads)* Untrack .beads/issues.jsonl — Dolt is canonical
- Update changelog and bump version to 2026.04.49
## [2026.04.48] - 2026-04-20

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.48
## [2026.04.47] - 2026-04-20

### 🚀 Features

- *(agents)* Add Step 16a pipeline watch to session-close
- *(agents)* Distinguish no-workflow from no-run-registered in pipeline watch
- *(metrics)* Ingest Claude Code + Codex tokens via ccusage

### 🚜 Refactor

- *(agents)* Extract turn-log/merge handlers from session-close

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.47
## [2026.04.46] - 2026-04-20

### 🚀 Features

- *(skills)* Add wave-reviewer skill

### ⚙️ Miscellaneous Tasks

- *(skills)* Tighten wave-reviewer structure
- *(skills)* Polish wave-reviewer structure (advisory fixes)
- Bump version to 2026.04.46
## [2026.04.45] - 2026-04-20

### ⚙️ Miscellaneous Tasks

- Update changelog
- *(beads)* Sync bead state — wave 1+2a complete, vision skill chain unblocked
- Update changelog
- Bump version to 2026.04.45
## [2026.04.44] - 2026-04-19

### 🚀 Features

- *(CCP-xpr)* Green — implement vision_parser module

### 🐛 Bug Fixes

- *(CCP-xpr)* Address review findings iteration 1
- *(CCP-xpr)* Address review findings iteration 2
- *(CCP-xpr)* Address review findings iteration 3

### 💼 Other

- Worktree-bead-CCP-xpr

### 🧪 Testing

- *(CCP-xpr)* Red — vision_parser tests + fixtures

### ⚙️ Miscellaneous Tasks

- Sync bead state
- Sync bead state for CCP-xpr session close
- Bump version to 2026.04.44
## [2026.04.43] - 2026-04-19

### 🚀 Features

- *(CCP-qrg)* Add PATH-shim bd wrapper so bd lint --check=architecture-contracts works without sourcing shell extension

### 🐛 Bug Fixes

- *(CCP-qrg)* Address Codex review regressions in bd-wrapper and installer
- *(CCP-qrg)* Detect and skip other bd-wrapper copies in PATH walk to prevent exec loop
- *(CCP-qrg)* Address review findings iteration 1

### 💼 Other

- Worktree-bead-CCP-qrg

### ⚙️ Miscellaneous Tasks

- Sync bead state
- *(CCP-qrg)* Sync bead state
- *(CCP-qrg)* Sync bead state
- *(CCP-qrg)* Update issues.jsonl bead state
- *(CCP-qrg)* Update issues.jsonl bead state
- Final issues.jsonl sync
- Bump version to 2026.04.43
## [2026.04.42] - 2026-04-19

### 🐛 Bug Fixes

- *(CCP-2q2)* Handle quoted document_type and skip fenced code blocks in tense-gate

### 💼 Other

- *(CCP-2q2)* Add tense-gate lint script for prescriptive-present enforcement
- Worktree-bead-CCP-2q2

### ⚙️ Miscellaneous Tasks

- *(beads)* Sync bead state before CCP-2q2 merge
- *(beads)* Sync bead state for CCP-2q2 session
- *(beads)* Sync issues.jsonl export
- Bump version to 2026.04.42
## [2026.04.41] - 2026-04-19

### 🚀 Features

- *(CCP-9yh)* Enforce mutual exclusion of None with gap markers in bd-lint-contracts

### 💼 Other

- Worktree-bead-CCP-9yh

### ⚙️ Miscellaneous Tasks

- *(beads)* Sync bead state — Trinity waves 1-3, vision skills, CCP-w56 superseded
- *(beads)* Sync bead state before CCP-9yh merge
- *(beads)* Sync bead state for CCP-9yh session
- Bump version to 2026.04.41
## [2026.04.40] - 2026-04-19

### 💼 Other

- Worktree-bead-CCP-uy2

### ⚙️ Miscellaneous Tasks

- *(CCP-uy2)* Sync bead state and remove stale issues.jsonl symlink
- *(CCP-uy2)* Remove issues.jsonl from git tracking
- Bump version to 2026.04.40
## [2026.04.39] - 2026-04-19

### 💼 Other

- Resolve conflicts from origin/main for CCP-2hd
- Worktree-bead-CCP-2hd

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.39
## [2026.04.38] - 2026-04-19

### 🚀 Features

- *(CCP-uy2)* Green — implement adr-hoist-check.py
- *(CCP-uy2)* Add /adr-gap skill, SKILL.md, adr-gap.sh, and adr-frontmatter.md reference
- *(CCP-2hd)* Add architecture-scout agent definition with coverage matrix output
- *(CCP-2hd)* Add example-matrix reference for architecture-scout
- *(CCP-2hd)* Extend mira-adapters fixture for architecture-scout test scenarios
- *(CCP-2hd)* Integrate architecture-scout into /plan and /epic-init skills

### 🐛 Bug Fixes

- *(CCP-uy2)* Address review findings iteration 1
- *(CCP-uy2)* Address review findings iteration 2
- *(CCP-uy2)* Fix 3 regressions from adversarial review + 4 new tests
- *(CCP-2hd)* Update tests and golden file to match new full-trinity fixture state
- *(CCP-2hd)* Address review findings iteration 1
- *(CCP-2hd)* Address review findings iteration 2 — fix line numbers, ADR status, vision grep pattern, conformance_skip passthrough
- *(CCP-2hd)* Add per-package matrix axis and fix epic-init scout timing/gate-mode
- *(CCP-2hd)* Strict touched_paths scoping for vision boundary + move scout to Phase 4
- *(CCP-0ql)* Fix bead-dropping and timezone bugs in wave-status.sh

### 💼 Other

- Worktree-bead-CCP-0ql

### 📚 Documentation

- *(CCP-uy2)* Update architecture-trinity README with feature docs

### 🧪 Testing

- *(CCP-uy2)* Red — failing tests for adr-hoist-check.py

### ⚙️ Miscellaneous Tasks

- *(CCP-uy2)* Untrack issues.jsonl (gitignored)
- Sync bead state
- Sync bead state for CCP-0ql
- Bump version to 2026.04.38
## [2026.04.37] - 2026-04-19

### 💼 Other

- Resolve conflicts from origin/main for CCP-0hr
- Worktree-bead-CCP-0hr

### ⚙️ Miscellaneous Tasks

- Sync bead state after merge resolution
- Remove issues.jsonl from git tracking (gitignored)
- Bump version to 2026.04.37
## [2026.04.36] - 2026-04-19

### 🚀 Features

- *(CCP-0hr)* Green — bd_lint_contracts.py linter (stdlib, 30 tests pass)
- *(CCP-0hr)* Shell wrapper bd-lint-extension.sh for bd lint --check=architecture-contracts
- *(CCP-0hr)* Update create SKILL.md with Phase 3.5 contract-label check and Phase 4.5 smoke-check
- *(CCP-0hr)* Add contract-sections.md reference documentation

### 📚 Documentation

- *(wave-orchestrator)* Align monitoring to 270s cache-warm poll cadence

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.36
## [2026.04.35] - 2026-04-19

### 🚀 Features

- *(CCP-0hr)* Green — bd-lint-contracts linter + shell extension + skill + docs
- *(CCP-vwg)* Green — enforcement matrix scanner, fixtures, SKILL.md update

### 🐛 Bug Fixes

- *(CCP-0hr)* Address review findings iteration 1
- *(CCP-0hr)* Address review findings iteration 2 — fence-strip in validate, bd-unavailable exit-1, untrack issues.jsonl
- *(CCP-0hr)* Address review findings iteration 1 (phase2)
- *(CCP-0hr)* Address review findings iteration 2 (phase2) — require description after NEEDED markers
- *(CCP-vwg)* Address review findings iteration 1
- *(CCP-vwg)* Address review findings iteration 2
- *(CCP-vwg)* Address review findings iteration 2
- *(CCP-vwg)* Address review findings iteration 3 — inline-list comment ordering and false-pass test

### 💼 Other

- Worktree-bead-CCP-vwg

### 🧪 Testing

- *(CCP-0hr)* Red — fixture-based test suite for bd-lint-contracts
- *(CCP-0hr)* Red — fixture-based test suite for bd-lint-contracts
- *(CCP-vwg)* Red — enforcement matrix tests (all failing, scanner not yet created)

### ⚙️ Miscellaneous Tasks

- *(CCP-0hr)* Untrack issues.jsonl (covered by .gitignore)
- *(CCP-0hr)* Untrack root issues.jsonl from git index
- *(CCP-vwg)* Remove issues.jsonl from tracking (gitignore)
- *(CCP-vwg)* Update bead state and untrack issues.jsonl
- Untrack issues.jsonl (covered by .gitignore)
- Bump version to 2026.04.35
## [2026.04.34] - 2026-04-19

### 🐛 Bug Fixes

- *(CCP-089)* Remove duplicate issues.jsonl from tracking
- *(CCP-089)* Align summary text to four-term vocabulary (advisory)

### 💼 Other

- Resolve conflict from origin/main — keep four-term vocabulary
- Worktree-bead-CCP-089

### ⚙️ Miscellaneous Tasks

- Update changelog
- *(CCP-089)* Update bead status to in_progress
- *(CCP-089)* Introduce Architecture Trinity vocabulary in docs
- Remove issues.jsonl from tracking (covered by .gitignore)
- Bump version to 2026.04.34
## [2026.04.33] - 2026-04-19

### 🚀 Features

- *(CCP-3oy)* Wire Turn-Log consumer in session-close and worktree-manager
- *(dev-tools)* Add binary-explorer skill for reverse-engineering desktop apps

### ⚙️ Miscellaneous Tasks

- *(beads)* Create Trinity-Harness epic and 10 subtask beads
- *(CCP-089)* Introduce Architecture Trinity vocabulary in docs
- Update changelog
- Bump version to 2026.04.33
## [2026.04.32] - 2026-04-16

### 🚀 Features

- *(dev-tools)* Add codex-guide agent for Codex CLI documentation queries

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.32
## [2026.04.31] - 2026-04-15

### 💼 Other

- Worktree-bead-CCP-a81

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.31
## [2026.04.30] - 2026-04-15

### 🐛 Bug Fixes

- *(codex)* Switch cmux-reviewer and quick-fix to blocking review invocation

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.30
## [2026.04.29] - 2026-04-15

### 🚀 Features

- *(CCP-a81)* Green — canonical-catalog detection in council + Phase 6.5 integration-verification

### 🐛 Bug Fixes

- *(CCP-a81)* Address review findings iteration 1
- *(CCP-a81)* Address review findings iteration 2
- *(CCP-a81)* Address review findings iteration 3
- *(CCP-a81)* Address review findings iteration 4

### 📚 Documentation

- Add Codex skills rollout plan
- *(dolt)* Document bd v1.0.0 auto-start and update red flags

### 🧪 Testing

- *(CCP-a81)* Red — regression scenario for canonical-catalog and integration-verification gap

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.29
## [2026.04.28] - 2026-04-15

### 🐛 Bug Fixes

- *(CCP-nxy)* Guard idle detection against active Claude thinking markers
- *(CCP-nxy)* Position-based idle detection, guard against stale terminal history
- *(CCP-nxy)* Check 2 preceding lines for thinking markers, not just 1

### 💼 Other

- Worktree-bead-CCP-nxy

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.28
## [2026.04.27] - 2026-04-15

### 🚀 Features

- *(CCP-2a2)* Add Phase 2.6 Module Impact Analysis to bead-orchestrator

### 🐛 Bug Fixes

- *(CCP-2a2)* Promote Module Impact/Existing Patterns to first-class sections in Codex template; add new-file fallback to Phase 2.6
- *(wave-orchestrator)* Detect dead cmux panes via error pattern
- *(quick-fix)* Trigger session-close via Agent tool, not cmux send

### 💼 Other

- Worktree-bead-CCP-2a2

### 📚 Documentation

- Add project-context.md and refresh README for 8-plugin bundle layout

### ⚙️ Miscellaneous Tasks

- *(CCP-qo0)* Set project-context skill model to inherit
- *(beads-workflow)* Clarify cmux surface detection in quick-fix agent
- Update changelog
- Update changelog
- Bump version to 2026.04.27
## [2026.04.26] - 2026-04-15

### 💼 Other

- Worktree-bead-CCP-qo0

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.26
## [2026.04.25] - 2026-04-15

### 🚀 Features

- *(CCP-qo0)* Green — /project-context skill with output template and plugin registration
- *(CCP-1ul)* Inject project architecture context block into subagent prompt

### 🐛 Bug Fixes

- *(CCP-1ul)* Add arch context to codex template, use json field for design

### 💼 Other

- Worktree-bead-CCP-1ul

### 🧪 Testing

- *(CCP-qo0)* Red — structural tests for /project-context skill

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.25
## [2026.04.24] - 2026-04-15

### 🐛 Bug Fixes

- *(CCP-asr)* Replace blind background wait with Monitor-based event loop
- *(CCP-asr)* Address Codex review regressions in codex-watch.sh
- *(CCP-asr)* Remove mktemp dep from poll loop to fix locked-down env crash
- *(CCP-asr)* Restore actionable error reason in CODEX_WATCH_ERROR

### 💼 Other

- Worktree-bead-CCP-asr

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.24
## [2026.04.23] - 2026-04-15

### 🐛 Bug Fixes

- *(beads-workflow)* Self-locate metrics lib without CLAUDE_PLUGIN_ROOT

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.23
## [2026.04.22] - 2026-04-15

### 📚 Documentation

- *(cmux-reviewer)* Add test-code finding policy for iter 2+

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.22
## [2026.04.21] - 2026-04-14

### 🐛 Bug Fixes

- *(CCP-8t0)* Add mcp__open-brain__* tools to agent allowlists

### ⚙️ Miscellaneous Tasks

- Update changelog
## [2026.04.20] - 2026-04-14

### 🐛 Bug Fixes

- *(session-close)* Add MCP tool names to agent tools: allowlist

### 📚 Documentation

- *(mira-aidbox)* Document /fhir-only rule and aidbox-format NPE bug

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.20
## [2026.04.19] - 2026-04-14

### 📚 Documentation

- Add 2026-04-14 architecture session documents

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.19
## [2026.04.18] - 2026-04-14

### 📚 Documentation

- *(home-infra)* Document LXC 119 kaji GitHub Actions runner

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.18
## [2026.04.17] - 2026-04-13

### 🐛 Bug Fixes

- *(session-close)* Create version tag after bump commit, not before

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.16
- Bump version to 2026.04.17
## [2026.04.16] - 2026-04-13

### 🚀 Features

- *(beads-workflow)* Add smart bead creation skill with type coaching and feature scenario gate
## [2026.04.15] - 2026-04-13

### 🐛 Bug Fixes

- *(bead-orchestrator)* Enforce hard stop on REROUTE_QUICK_FIX with no escape hatch

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.15
## [2026.04.14] - 2026-04-13

### 🚀 Features

- *(bead-orchestrator)* Add effort estimation and quick-fix reroute in Phase 0

### 🚜 Refactor

- *(bead-workflow)* Establish opus/sonnet/codex tier architecture

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.14
## [2026.04.13] - 2026-04-12

### 🚀 Features

- *(wave-orchestrator)* Add effort estimation for unset beads in Phase 1

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.12
- Update changelog
- Bump version to 2026.04.13
## [2026.04.12] - 2026-04-12

### 🚀 Features

- *(beads-workflow)* Add quick-fix agent for lightweight XS/S bead orchestration

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.11
- Update changelog
## [2026.04.11] - 2026-04-12

### 🐛 Bug Fixes

- *(cmux)* Replace literal \n with send-key enter pattern across all agents

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.10
- Update changelog
## [2026.04.10] - 2026-04-12

### 🚀 Features

- *(wave-orchestrator)* Add Phase 1.5b architecture review gate (CCP-b96)
- *(plugins)* Add version field to all plugin.json and extend version.sh for multi-plugin sync
## [2026.04.9] - 2026-04-12

### 🚀 Features

- *(beads-workflow)* Add test quality gates, scope analysis, and learnings report
- *(beads-workflow)* Implement multi-model orchestration strategy (CCP-80r)

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.9
## [2026.04.8] - 2026-04-12

### 🐛 Bug Fixes

- *(cmux-reviewer)* Drop hard 30-line fix-prompt cap
- *(cmux-reviewer)* Use single-call send+newline with retry to fix race condition

### 📚 Documentation

- *(cmux-reviewer)* Strip historical rationale from LEARN bullet

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.8
## [2026.04.7] - 2026-04-11

### 🐛 Bug Fixes

- *(beads-workflow)* Route cmux-reviewer through codex-companion runtime

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.7
## [2026.04.6] - 2026-04-11

### 🐛 Bug Fixes

- *(beads-workflow)* Bundle orchestrator library into plugin

### ⚙️ Miscellaneous Tasks

- Update changelog
- Bump version to 2026.04.6
## [2026.04.5] - 2026-04-11

### 📚 Documentation

- *(beads-workflow)* Add three-stage escalation ladder to cmux-reviewer

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.5
## [2026.04.4] - 2026-04-11

### 🐛 Bug Fixes

- *(beads-workflow)* Use fully qualified plugin namespace for subagent_type references

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.3
- Update changelog
- Bump version to 2026.04.4
## [2026.04.3] - 2026-04-11

### 🚀 Features

- *(session-close)* Sync plugin.json version when bumping VERSION file

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.2
- *(plugins)* Remove version field from plugin.json and VERSION file
## [2026.04.2] - 2026-04-11

### 🚀 Features

- *(hooks)* Migrate hooks to plugin namespaces and update cmux-reviewer

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.1
## [2026.04.1] - 2026-04-11

### 🚀 Features

- *(agents)* Migrate all agents from malte/agents to plugin namespaces

### 🐛 Bug Fixes

- *(session-close)* Migrate handler scripts and update path reference
- *(session-close)* Update HANDLERS_DIR path to plugin cache location

### ⚙️ Miscellaneous Tasks

- Bump version to 2026.04.0
## [2026.04.0] - 2026-04-11

### 🚀 Features

- Add reference-file-compactor skill
- Add plugin-tester for local plugin development workflow
- Add plugin-developer plugin with marketplace-manager skill
- Add hook-creator skill for plugin-developer
- Add slash-command-creator skill to plugin-developer
- Add agent-creator skill for plugin-developer
- Add reference files and automation scripts to command-creator
- Add timing-matcher skill for Timing app export processing
- Add playwright-mcp plugin for browser automation
- Configure repository as official Claude Code marketplace
- Add /install-plugin command to plugin-developer
- Update /install-plugin to handle complete plugin unpacking
- Add prompt-library-tools plugin for Obsidian prompt extraction
- Add skill-forge plugin for skill quality scoring, auditing, and refactoring
- Restructure marketplace into 8 thematic plugin bundles
- *(dev-tools)* Add prd-generator, pester-test-engineer, feedback-extractor, spellcheck agents
- *(beads)* Set up CCP issue tracking and improve dolt new-project docs

### 🐛 Bug Fixes

- Ignore .claude symlink in addition to directory
- Remove invalid 'category' field from all plugin.json files

### 🚜 Refactor

- Restructure reference-file-compactor as Claude Code plugin
- Replace bash script with Python for plugin installation
- Migrate bash/zsh scripts to Python for better portability
- Adopt pragmatic Python dependency approach
- Rename slash-command-creator to command-creator
- Streamline command-creator skill (28% reduction)
- Convert standalone skills to proper plugin structure
- *(command-creator)* Use model family names instead of version numbers

### 📚 Documentation

- Document plugin skills discovery bug and workarounds
- *(sync-cache)* Clarify manual vs automated plugin cache sync

### ⚙️ Miscellaneous Tasks

- Remove duplicate .claude/ entry from gitignore
- Add sync-cache.sh script for manual plugin cache sync
