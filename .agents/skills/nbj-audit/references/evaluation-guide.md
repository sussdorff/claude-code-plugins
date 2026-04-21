# NBJ Audit — Evaluation Guide (On Demand)

Load this when the script output is ambiguous or you need to investigate a primitive further.

## Harness Mode — Where to Look

| # | Primitive | Location | present signal | partial signal |
|---|-----------|----------|----------------|----------------|
| 1 | Tool Registry | `<skills-dir>/` | ≥20 skills with SKILL.md | 5–19 skills |
| 2 | Permission System | `<hooks-dir>/pre_tool_use.py` + conventions file | hook + ≥3 safety rules | hook OR rules |
| 3 | Session Persistence | `.beads/` + memory skill | both present | one present |
| 4 | Workflow State | `.beads/` + `bd` CLI | both available | one present |
| 5 | Token Budget | `<skills-dir>/token-cost/` + conventions file | skill + ≥2 tier refs | skill OR refs |
| 6 | Streaming Events | `<skills-dir>/cmux/` + orchestrator agents | cmux + streaming phases | cmux only |
| 7 | Event Logging | `<hooks-dir>/event-log.py` + `<skills-dir>/event-log/` | hook + skill | hook OR skill |
| 8 | Verification Harness | `<agents-dir>/review-agent`, `holdout-validator`, `verification-agent` | review agents + ≥3 total | any review agent |
| 9 | Tool Pool Assembly | `<harness-dir>/index.yml` + conventions file on-demand refs | index + refs | index OR refs |
| 10 | Transcript Compaction | conventions file PreCompact/compaction rules | ≥3 mentions | 1–2 mentions |
| 11 | Permission Audit Trail | `<skills-dir>/event-log/` + `bd audit` | both present | one present |
| 12 | Doctor + Provenance | `bd doctor` command + `.beads/` | both available | one present |

## Project Mode — Where to Look

| # | Primitive | Location | present signal | partial signal |
|---|-----------|----------|----------------|----------------|
| 1 | Tool Registry | API route files (`routes.ts`, `*.routes.ts`) | ≥3 route files | 1–2 route files |
| 2 | Permission System | Auth middleware, RBAC files, validation schemas | ≥2 auth + ≥1 validation | any auth or validation |
| 3 | Session Persistence | DB migrations, Prisma/Drizzle schemas, session files | ≥2 DB files | ≥1 DB or session file |
| 4 | Workflow State | `*workflow*`, `*state*`, `*machine*`, `*status*` files | ≥3 state files | 1–2 state files |
| 5 | Token Budget | Rate limiting (`rateLimit`, `throttle`), cost tracking | ≥2 rate limit files | 1 rate limit file |
| 6 | Streaming Events | WebSocket, SSE, EventEmitter, socket.io | ≥2 stream files | 1 stream file |
| 7 | Event Logging | winston, pino, bunyan, audit log patterns | ≥3 log files | 1–2 log files |
| 8 | Verification Harness | Test files (`*.test.ts`, `*.spec.*`) + CI config | ≥5 tests + CI | ≥2 tests |
| 9 | Tool Pool Assembly | Feature flags (LaunchDarkly, flipper) + lazy imports | ≥2 flag files | ≥1 flag or lazy |
| 10 | Transcript Compaction | N/A — harness-level only | always partial | — |
| 11 | Permission Audit Trail | Access logs (`accessLog`, `auditLog`) | ≥2 audit files | 1 audit file |
| 12 | Doctor + Provenance | Health endpoints, build info, provenance metadata | health + ≥2 provenance | health OR provenance |

## Delta Interpretation

When `.beads/nbj-audit-history.json` exists, compare current run vs last:

| Symbol | Meaning |
|--------|---------|
| ↑ | Status improved (missing→partial or partial→present) |
| ↓ | Regressed (present→partial or partial→missing) |
| = | Unchanged |
| new | Not in previous run |

## History File Format

```json
{
  "runs": [
    {
      "timestamp": "2026-04-05T19:00:00Z",
      "mode": "harness",
      "primitives": {
        "1": "present",
        "2": "partial",
        ...
      }
    }
  ]
}
```

Save results to this file after each run by constructing the JSON from the PRIMITIVE lines.
