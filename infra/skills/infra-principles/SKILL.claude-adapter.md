---
harness: claude
skill: infra-principles
---

# Infrastructure Principles — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific notes.
A Codex user does NOT need to read this file.

## No Claude-Specific Adaptations Required

`infra-principles` contains no harness-specific paths, MCP tool calls, or slash-command syntax.
The portable `SKILL.md` is complete as-is for Claude Code users.

## Note on `playwright-cli` Reference

The reference to `playwright-cli` in the skill is to the CLI tool (not a harness MCP tool),
so it remains valid across runtimes that have the `playwright-cli` binary available.
