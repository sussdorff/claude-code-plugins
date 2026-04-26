# ADR-0004: Disable Claude Code Sandbox for Single-User Development

## Status

Accepted (2026-04-26)

## Context

CCP-15j (under the Security Hardening epic CCP-k1t5) enabled Claude Code's
built-in OS-level sandbox in `~/.claude/settings.json`:

```json
"sandbox": {
  "enabled": true,
  "failIfUnavailable": true,
  "filesystem": { "denyRead": [".env*", "~/.ssh"] },
  "network": { "allowMachLookup": false }
}
```

Within hours of activation we observed cascading friction in normal development
workflows:

- `bd` (beads CLI) failed with `connect: operation not permitted` on
  `127.0.0.1:3308`. The shared Dolt server was running fine; the sandbox blocked
  outbound TCP from sandboxed bash subprocesses. `bd dolt start` could not even
  create its lock file (`operation not permitted`).
- `git commit` failed with `Konnte '.git/index.lock' nicht erstellen: Operation
  not permitted` — the sandbox's filesystem default-deny extends to
  `.git/` writes.
- `bun -e "..."`, `bun test ...`, `bun install ...`, `bun x tsc` — every test
  iteration in `~/code/polaris` (Bun-workspace monorepo with workspace tests,
  builds, typecheck) triggered either a permission prompt or a sandbox block.
- The same surface existed for `uv`, `pip`, `python3`, `npm`, `pnpm` — every
  language stack in active use.

We responded by adding patterns to `sandbox.excludedCommands`:

```
"bd", "bd *", "bun *", "git", "git *",
"uv *", "pip *", "pip3 *", "python *", "python3 *", "npm *", "pnpm *"
```

At that point the question became visible: **what is the sandbox actually still
protecting?**

The Anthropic-built sandbox provides four protections that matter:

| Protection | Status after our allowlist |
|---|---|
| `filesystem.denyRead: [".env*", "~/.ssh"]` | Only enforced for *sandboxed* commands. `bun -e "console.log(await Bun.file('~/.ssh/id_rsa').text())"` bypasses it because `bun *` is in `excludedCommands`. The denyRead becomes nominal. |
| Outbound network restrictions | Same logic. `bun fetch(...)`, `git clone http://...`, `python3 -c "import urllib"` all bypass network rules now. |
| Default-deny on filesystem writes outside CWD | Same — every common dev tool is on the bypass list. |
| Default-deny on **unknown** commands | Still active. New unfamiliar tools still trigger. This is the only remaining real value. |

The Anthropic sandbox is engineered for an **agentic-runner threat model**:
Claude executes commands unattended at scale; the operator cannot review every
bash invocation; the OS layer is the last line of defense.

That is not the operating model in this repository. This is a **single-user
interactive development workstation**. Every Bash tool call appears in
conversation context with its full argument string before the operator
authorises it. The operator (Malte) is the supervisor, not the OS.

We considered three paths forward:

1. **A — Disable the sandbox entirely.** Accept that the sandbox no longer
   provides defense-in-depth in this context. Rely on the operator's review of
   bash blocks plus any complementary hook-based controls.
2. **B — Keep the sandbox on, freeze the allowlist.** Accept ongoing prompt
   friction as a security tax for default-deny on unknown tools. Every new
   stack (cargo, go, kubectl, docker, …) re-introduces friction.
3. **C — Sandbox off, push specific protections (`.env*` / `~/.ssh` read
   blocking) into the existing PreToolUse hook (`/Users/malte/.local/bin/dcg`,
   the Destructive Command Guard from CCP-jel).** Real protection survives;
   no allowlist sprawl.

## Decision

Choose **A**: disable Claude Code's built-in sandbox in
`~/.claude/settings.json`:

```json
"sandbox": {
  "enabled": false
}
```

The `permissions.allow` list (broad allowlists for `git *`, `bun *`, `uv *`,
`pip *`, `pip3 *`, `python *`, `python3 *`, `npm *`, `pnpm *`,
`mcp__pencil`) remains in place. It still serves a purpose: skipping
permission prompts for routine commands when a future change re-introduces
prompting (e.g. another setting, a hook, a model update).

Path C remains an option for the future. If the gaps left by sandbox-off
become a measurable problem (incidents, near-misses, audit findings), we
revisit by implementing read-deny rules for `.env*` and `~/.ssh` in the DCG
hook (CCP-jel scope already includes destructive-command interception, the
extension is incremental).

## Consequences

### Positive

- Zero sandbox-induced prompts and `operation not permitted` errors during
  normal development. `bd`, `git`, `bun`, `uv`, `pip`, `npm`, `python3`,
  ad-hoc inline scripts (`bun -e`, `python3 -c`) all run frictionlessly.
- No allowlist maintenance burden. New stacks (cargo, go, kubectl, etc.)
  do not require config updates.
- No false sense of security. The actual security model is now explicit:
  *the operator reviews bash blocks in the conversation before authorising
  them.* The OS sandbox no longer creates the illusion of additional safety.

### Negative

- Loss of `filesystem.denyRead: [".env*", "~/.ssh"]` enforcement. Note: this
  protection was already nominal because every common dev tool was on the
  bypass list — so the practical change is small. But unsandboxed tools can
  read those paths now without a hard stop at the OS layer.
- Loss of default-deny on outbound network calls. Same caveat: nearly all
  common tools were already excluded.
- Loss of default-deny on unknown commands. This was the one remaining
  real protection. New unfamiliar tooling now runs without a sandbox layer.
- Re-enabling the sandbox in the future will require re-establishing the
  allowlist if the friction model changes.

### Neutral

- The `permissions.allow` list (prompt suppression) is independent of the
  sandbox. It remains in effect.
- The Destructive Command Guard hook (CCP-jel, `dcg` at
  `/Users/malte/.local/bin/dcg`) continues to run as a `PreToolUse Bash`
  hook — its interception of `rm -rf`, force-pushes, etc. is unaffected.

## Alternatives Considered

### Alternative B: Sandbox on, allowlist frozen
Rejected. Friction tax is high (every new stack re-introduces prompts) and
the protection is shallow once the dev-stack allowlist exists. The operator
would learn to mute prompts cognitively rather than evaluate each one — the
worst of both worlds.

### Alternative C: Sandbox off, hook-based read-deny
Deferred. Strictly better than A on paper, but requires writing and testing
hook logic for `.env*` and `~/.ssh` read interception. We are willing to do
this if a real incident or audit finding shows the gap matters; until then,
A is sufficient.

### Alternative D: Bypass sandbox per-call via `dangerouslyDisableSandbox`
Rejected as a long-term pattern. Forces every Bash call to remember the flag,
clutters tool calls, and does not generalise to non-Claude callers (e.g. a
subagent invoking the same command). The pattern was used briefly during
diagnosis; not viable as policy.

## When to Reconsider

Re-enable the sandbox (or implement Path C) if any of the following becomes
true:

- The harness moves to **unattended / agentic-runner** operation where the
  operator does not review each Bash block in real time.
- The harness becomes **multi-user / multi-tenant** (shared installation,
  service accounts, CI runners).
- A **real security incident** traces back to a missing OS-level guard
  that the sandbox would have prevented.
- A **compliance / audit requirement** (e.g. SOC2 controls, customer
  requirement) mandates OS-level filesystem isolation for AI agents.

In any of those cases, the trade-off shifts and the sandbox is back on the
table.

## References

- Security Hardening epic: `CCP-k1t5`
- Sandbox enablement: `CCP-15j` (commit 78c05be5 in `~/.claude` repo)
- Destructive Command Guard (PreToolUse hook): `CCP-jel`
- Anthropic Claude Code sandbox documentation:
  https://code.claude.com/docs/en/settings (sandbox section)
- Settings change rolled out in: ~/.claude commit `<see CCP-9pny>` (2026-04-26)
