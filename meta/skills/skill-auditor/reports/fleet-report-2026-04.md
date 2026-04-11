# Skill Fleet Audit — April 2026

## Fleet Scan (SKILL.md only)

Output from `malte/skills/skill-auditor/scripts/scan-skills.sh malte/skills/`:

```
SKILL                      LINES  TOKENS~  REFS SCRIPTS  DESC
------------------------- ------ -------- ----- ------- -----
playwright-cli               269     1244   yes      no   248
inject-standards             244     1115    no      no   237
learnings-pipeline            13      106    no      no   242
hass-cli                     233     1193   yes      no   220
ai-readiness                 265     2204    no      no   227
mm-cli                       263     1820    no      no   241
prompt-refiner               139      946   yes     yes   458
amazon                       102      579   yes      no   237
epic-init                    275     1859    no      no   247
home-infra                   258     2206    no      no   238
cmux-browser                 199     1314   yes      no   161
hetzner-cloud                297     2263    no      no   233
career-check                 226     1540    no      no   242
ui-cli                       158     1097   yes      no   227
brand-forge                  132      939   yes     yes   236
sync-standards               239     1294    no     yes     0
portless                     218     1600    no      no   248
plugin-management            179     1060   yes      no   238
skill-auditor                114      850    no     yes   303
spec-developer               144     1114   yes      no   229
claude-config-handler        196     1181    no     yes   160
claude-md-pruner             117      835    no      no   250
cmux-markdown                125      707   yes      no   208
local-vm                      47      377    no     yes   231
project-setup                248     1700   yes      no   625
memory-heartbeat             230     1625    no      no   256
google-invoice               147      865    no      no   190
billing-reviewer             184     1175    no      no   225
agent-forge                  238     1696   yes     yes   411
profile                      226     1882    no      no   235
aidbox                       156     1086   yes     yes  1096
beads                         39      226   yes      no   242
youtube-music-updater        146      891    no     yes   235
collmex-cli                  291     1805    no      no   233
hook-creator                 206     1367   yes      no   222
ccu-cli                      313     1888    no      no   239
compound                     163     1111   yes      no   273
paperless-cli                119      718   yes     yes   244
aidbox-fhir.replaced-by-aidbox    290     1950    no      no   236
angebotserstellung           262     1145   yes      no   246
op-credentials               140      869   yes     yes   296
cmux                          54      304   yes      no   226
pencil                       198     1280   yes     yes   223
linkedin                     175     1423   yes     yes   242
mail-send                    107      708    no      no   244
piler-cli                     97      715    no      no   246
standards                    450     2076    no      no   340
dolt                         636     5203   yes     yes  1285

=== Fleet System Prompt Cost ===
Total skills:            48 (unique)
Total description chars: ~13871
Est. description tokens: ~3468
Avg description length:  288 chars

Bloated descriptions (>300 chars):
  dolt         1285 chars
  aidbox       1096 chars
  project-setup 625 chars
  prompt-refiner 458 chars
  agent-forge  411 chars
  standards    340 chars
  skill-auditor 303 chars
```

## Total Token Footprint (SKILL.md + references/)

Measured 2026-04-05 using `wc -w × 1.33` approximation. Only skills with a `references/` directory are included; skills without refs have total = SKILL.md tokens only.

> **Note:** This table was computed separately from the Fleet Scan above. `wave-orchestrator` (rank 11) and `nanobanana` (rank 17) appear here but not in the Fleet Scan because `scan-skills.sh` de-duplicates by resolved symlink path — these skills were present in a secondary scan path and deduplicated out of the primary output. Their reference measurements below are accurate.

| Rank | Skill | SKILL.md tokens | Ref tokens | Total | Tier | Status |
|------|-------|-----------------|------------|-------|------|--------|
| 1 | plugin-management | 1,085 | 6,628 | 7,713 | heavy | OK (< 8k) |
| 2 | agent-forge | 1,735 | 5,728 | 7,463 | heavy | OK (< 8k) |
| 3 | hook-creator | 1,399 | 5,458 | 6,857 | heavy | OK (< 8k) |
| 4 | pencil | 1,310 | 4,958 | 6,268 | heavy | OK (< 8k) |
| 5 | playwright-cli | 1,272 | 4,752 | 6,024 | heavy | OK (< 8k) |
| 6 | dolt | 5,323 | 546 | 5,869 | heavy | **VIOLATION** (SKILL.md > 2k) |
| 7 | aidbox | 1,111 | 3,835 | 4,946 | heavy | OK |
| 8 | brand-forge | 961 | 3,335 | 4,296 | heavy | OK |
| 9 | spec-developer | 1,139 | 2,922 | 4,061 | medium | OK |
| 10 | linkedin | 1,456 | 2,532 | 3,988 | medium | OK |
| 11 | wave-orchestrator | 3,188 | 621 | 3,809 | medium | **VIOLATION** (SKILL.md > 3k) |
| 12 | cmux-browser | 1,344 | 2,288 | 3,632 | medium | OK |
| 13 | hass-cli | 1,220 | 2,191 | 3,411 | medium | OK |
| 14 | project-setup | 1,739 | 1,361 | 3,100 | medium | OK |
| 15 | compound | 1,137 | 1,881 | 3,018 | medium | OK |
| 16 | angebotserstellung | 1,171 | 1,762 | 2,933 | medium | OK |
| 17 | nanobanana | 897 | 1,582 | 2,479 | medium | OK |
| 18 | prompt-refiner | 968 | 1,131 | 2,099 | medium | OK |
| 19 | cmux-markdown | 723 | 950 | 1,673 | medium | OK |
| 20 | ui-cli | 1,122 | 518 | 1,640 | medium | OK |
| 21 | amazon | 593 | 994 | 1,587 | light | OK |
| 22 | beads | 231 | 1,091 | 1,322 | light | OK |
| 23 | cmux | 311 | 441 | 752 | light | OK |

## Skills Exceeding 5,000 Tokens Total

The following skills exceed 5,000 total tokens (SKILL.md + references/):

| Skill | Total tokens | Violation type |
|-------|-------------|----------------|
| plugin-management | 7,713 | None — within heavy tier budget (< 8k) |
| agent-forge | 7,463 | None — within heavy tier budget (< 8k) |
| hook-creator | 6,857 | None — within heavy tier budget (< 8k) |
| pencil | 6,268 | None — within heavy tier budget (< 8k) |
| playwright-cli | 6,024 | None — within heavy tier budget (< 8k) |
| dolt | 5,869 | **SKILL.md violation** — 5,323 tokens in SKILL.md exceeds heavy tier SKILL.md budget of 2,000 tokens |

**Note:** All skills exceeding 5k total tokens are within the heavy tier total budget (< 8k). The only active violation is `dolt` where the SKILL.md itself is oversized (5,323 tokens); reference material should carry the bulk for heavy-tier skills, not the SKILL.md.

## After Trimming (Post-Implementation)

The three heaviest skills were trimmed as part of this bead. Actual measured values from current files:

| Skill | Before (measured from original file sizes) | After (actual) | Reduction |
|-------|---------------------------------------------|----------------|-----------|
| plugin-management | ~12,858 | 7,713 | -40% |
| agent-forge | ~14,336 | 7,463 | -48% |
| hook-creator | ~10,184 | 6,857 | -33% |

Before values measured from git history; after values measured from current files.

All three now sit within the heavy tier budget (< 8,000 tokens total).

## Deferred Violations

The following tier violations were identified but are outside this bead's scope (top-3 by total token count):

| Skill | Violation | Total tokens | Note |
|-------|-----------|--------------|------|
| dolt | SKILL.md 5,323 tokens (heavy-tier SKILL.md limit: 2,000) | 5,869 total | High-priority — SKILL.md carries reference material that should move to refs/ |
| wave-orchestrator | SKILL.md >3,000 tokens (medium-tier limit: 3,000) | SKILL.md only | Needs classification check |

Recommend follow-up beads for each.

## Documentation

- Token budget standard: `malte/standards/skills/token-budget-tiers.md`
- The three tiers:
  - **Light**: < 1,000 tokens (SKILL.md only, no refs needed)
  - **Medium**: < 3,000 tokens SKILL.md / < 5,000 tokens total (SKILL.md + refs)
  - **Heavy**: < 2,000 tokens SKILL.md / < 8,000 tokens total (SKILL.md + refs)
- Note: `~/.claude/CLAUDE.md` was updated with a `## Skills` section referencing this standard. This edit targets the shared CLAUDE.md (outside this worktree's diff scope) and will be visible after merge.
