---
name: cmux
description: End-user control of cmux topology and routing (windows, workspaces, panes/surfaces, focus, moves, reorder, identify, trigger flash). Use when automation needs deterministic placement and navigation in a multi-pane cmux layout.
requires_standards: [english-only]
---

# cmux Core Control

Use this skill to control non-browser cmux topology and routing.

## Core Concepts

- Window: top-level macOS cmux window.
- Workspace: tab-like group within a window.
- Pane: split container in a workspace.
- Surface: a tab within a pane (terminal or browser panel).

## Fast Start

See [`scripts/fast-start.sh`](scripts/fast-start.sh) for the full set of identify, list, create/focus/move, and flash commands.

## Handle Model

- Default output uses short refs: `window:N`, `workspace:N`, `pane:N`, `surface:N`.
- UUIDs are still accepted as inputs.
- Request UUID output only when needed: `--id-format uuids|both`.

## Notification Routing (Stop-hook filter)

cmux's claude wrapper injects a `Stop` hook that fires `cmux claude-hook stop`
after **every** model turn — producing too many "Claude is finished" system
notifications during multi-turn work. A shim wired in via `CMUX_BUNDLED_CLI_PATH`
intercepts only the stop call, asks Claude Haiku to classify NOTIFY vs QUIET,
and forwards only when the user actually needs to act. Everything else passes
through unchanged.

Active when `CMUX_BUNDLED_CLI_PATH` points at `malte/scripts/cmux-shim.sh`.
Decisions log to `/tmp/cmux-shim.log`. See
[references/notification-routing.md](references/notification-routing.md) for
the full design, fail-safe behavior, trade-offs (sidebar state lag), and
disable instructions.

## Deep-Dive References

| Reference | When to Use |
|-----------|-------------|
| [references/handles-and-identify.md](references/handles-and-identify.md) | Handle syntax, self-identify, caller targeting |
| [references/windows-workspaces.md](references/windows-workspaces.md) | Window/workspace lifecycle and reorder/move |
| [references/panes-surfaces.md](references/panes-surfaces.md) | Splits, surfaces, move/reorder, focus routing |
| [references/trigger-flash-and-health.md](references/trigger-flash-and-health.md) | Flash cue and surface health checks |
| [references/notification-routing.md](references/notification-routing.md) | Stop-hook Haiku filter (cmux-shim.sh) |
| [../cmux-browser/SKILL.md](../cmux-browser/SKILL.md) | Browser automation on surface-backed webviews |
| [../cmux-markdown/SKILL.md](../cmux-markdown/SKILL.md) | Markdown viewer panel with live file watching |
