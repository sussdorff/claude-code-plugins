---
name: prompt-refiner
description: >
  Refine raw, unstructured, or dictated user input into a structured prompt via HeyPresto MCP,
  then EXECUTE the refined prompt immediately. Use when the user provides messy dictated text,
  vague task descriptions, or says "expand prompt", "refine prompt", "use heypresto",
  "prompt verbessern". Also triggers on "Expand Prompt." at the start of a message followed
  by stream-of-consciousness text. Do NOT use for simple direct questions or already-clear prompts.
---

# Prompt Refiner

Refine raw input via HeyPresto, then execute the result. No stopping, no presenting — the
refined prompt IS the task.

## The Workflow (4 steps, no exceptions)

### 1. Clean Up Raw Input

Take the user's raw input (often dictated, with filler words, repetition, and corrections).
Briefly clean it up:
- Fix obvious speech-to-text errors
- Remove filler ("ich sag mal", "also", "nichtsdestotrotz")
- Preserve the actual intent and all concrete details
- Keep the user's language (German stays German, English stays English)

This is a light pass — don't rewrite, just clean.

### 2. Analyze Intent & Build Context

**Context** — assemble from what you already know:
- Current project (CLAUDE.md, memory, conversation history)
- Stack/framework constraints
- User preferences and domain expertise

**Mode** — detect from the content:

| Domain | Mode |
|--------|------|
| Code, architecture, infra | `code` |
| Documentation, specs | `doc` |
| Presentations, pitches | `deck` |
| Data analysis | `data` |
| Marketing, copy | `copy` |
| Emails, messages | `comms` |
| Everything else | `default` |

**Tone** — infer from context and content:

| Signal | Tone |
|--------|------|
| Architecture docs, specs, API design | `technical` |
| Business proposals, pitches, stakeholder comms | `professional` |
| Internal team discussion, brainstorming | `casual` |
| User-facing copy, marketing | `creative` |
| Community, open-source, meetups | `friendly` |
| Strategy papers, executive summaries | `authoritative` |

**Length** — match to task complexity:

| Task | Length |
|------|--------|
| Quick question, single action | `concise` |
| Feature spec, multi-step task | `medium` |
| Architecture plan, deep analysis | `detailed` |
| Full project spec, strategy doc | `comprehensive` |

**Format** — usually `Sections` unless the content suggests otherwise (e.g., `Steps` for
workflows, `Bullets` for quick lists, `Table` for comparisons).

### 3. Call HeyPresto

Call the HeyPresto `expand_prompt` operation with all detected parameters:

```json
{
  "expandedPrompt": {
    "prompt": "<cleaned user input>",
    "context": "<assembled project/domain context>",
    "mode": "<detected mode>",
    "tone": "<detected tone>",
    "length": "<detected length>",
    "format": "<detected format, default: Sections>",
    "stripMetaCommentary": true,
    "includeChangesSummary": true
  }
}
```

Every field matters — HeyPresto produces significantly better output when mode, tone, and
length are set correctly. Don't skip them.

If HeyPresto MCP is unavailable, fall back to local meta-prompting using a subagent
with `references/nate-rules.md`.

### 4. EXECUTE the Refined Prompt

This is the critical step. Do NOT:
- Show the refined prompt to the user in a markdown block
- Ask "should I execute this?"
- Add a model recommendation footer
- Wait for confirmation

Instead: **treat the HeyPresto output as your new task and execute it immediately.**
The whole point is that the user gave you messy input, you refined it, and now you do the work.

The only output the user should see is the RESULT of executing the refined prompt —
not the prompt itself.

## Logging (silent, in background)

Append to `<agent-state-dir>/prompt-refiner-log.jsonl` after execution:

```json
{"timestamp": "...", "backend": "heypresto", "input_raw": "...", "context": "...", "params": {"mode": "...", "tone": "...", "length": "..."}, "output_refined": "..."}
```

This log is training data for an eventual local model replacement. Capture all parameters
that went into the HeyPresto call so we can reproduce the mapping.

Don't let logging delay execution. If it fails, move on.

## Refinement (only if user asks)

If the user says "refine further" or gives feedback on the HeyPresto output, use the
`previousPrompt` + `refinementInstruction` fields to iterate, then execute again.

## Do NOT

- Present the refined prompt as output — the user wants results, not prompts
- Add model-routing recommendations — the user is already talking to the right model
- Add ceremony (headers, footers, "Key improvements" lists)
- Use this for simple, already-clear prompts — just answer those directly
- Inject Nate rules into HeyPresto context — HeyPresto has them built in

## Resources

- `references/nate-rules.md` — Structural rules for local fallback only
- `references/domain-profiles.md` — Domain-specific context templates
