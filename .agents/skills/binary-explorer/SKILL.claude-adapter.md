---
harness: claude
skill: binary-explorer
---

# Binary Explorer — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific notes.
A Codex user does NOT need to read this file.

## No Claude-Specific Adaptations Required

`binary-explorer` contains no harness-specific paths, MCP tool calls, or slash-command syntax.
The portable `SKILL.md` is complete as-is for Claude Code users.

## Subagent Tip (Claude)

When spawning subagents per question as suggested in the skill, use the `Agent` tool with
`model: haiku` and pass the extracted strings file path in the prompt.
