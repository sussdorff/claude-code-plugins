---
name: binary-explorer
description: Reverse-engineer any desktop application to understand how it works behind the scenes — the APIs it calls, the internal flow, the models/providers it uses, its feature flags, config constants, embedded prompts, IPC protocols. Works on Electron apps (Wispr Flow, Slack, Discord, VS Code, Cursor, Notion, Linear…), native macOS .app bundles, single-executable bundles (Bun/Node/Deno/Go SEA), and raw Mach-O / ELF / PE binaries. Use this skill whenever the user points at a desktop app and wants to know "how does X work under the hood", "what API does it call", "how does it do Y", "what's the flow for Z", "reverse engineer this app", "figure out how this feature works", "what endpoints does it hit", "does it run locally or in the cloud", "what model does it use", or names a specific app path (.app, .exe, a binary). Also trigger when the user wants to audit an app's network behavior, understand its architecture, or extract embedded strings/prompts/secrets. Do NOT use for the user's *own* source code (just read it), for web apps without a desktop client, or for the Claude Code binary specifically (use claude-binary-explorer for that — it knows Claude Code's mangled variable conventions).
---

# App Reverser

Reverse-engineer any desktop application by extracting its readable content — strings, embedded bundles, config, network endpoints — and tracing the code paths that matter to the user's question.

## Why this works

Most shipped desktop apps leak their architecture in their binary. Electron apps carry their full JavaScript bundle in `app.asar` as plain text after extraction. Native binaries contain log messages, format strings, URL literals, API keys, and symbol names that `strings` dumps verbatim. Single-executable bundles (Bun/Node/Deno SEA, Go) embed their source scripts directly. You rarely need a real disassembler — you just need to know where the readable content lives.

## Step 0: Identify the app

The user will usually give you a path — `/Applications/Foo.app`, `/path/to/binary`, or a running process. Before anything else, figure out **what kind of artifact you're dealing with**, because the extraction strategy differs:

```bash
bash <skill-dir>/scripts/extract.sh <path-to-app-or-binary>
```

This script auto-detects the type and extracts everything searchable into a workspace, printing the paths. Common artifact types:

| Type | Tell | What to extract |
|---|---|---|
| **macOS .app bundle** | `Foo.app/Contents/MacOS/Foo` is a Mach-O | Walk `Contents/`: main binary, Frameworks, Resources (often contains `app.asar` for Electron, or a nested helper .app) |
| **Electron app** | `Contents/Resources/app.asar` exists | Extract asar with `npx --yes @electron/asar extract` — gives you the full JS bundle (usually in `.webpack/main/index.js` and `.webpack/renderer/*`) |
| **Single-executable JS** | `file <bin>` says Mach-O/ELF but the binary is large (>50 MB) and `strings` yields JS syntax | Treat strings dump as the source — it's all there |
| **Native binary** | Mach-O/ELF/PE, modest size | Strings dump catches logs, URLs, class names; use `nm`/`otool -L`/`objdump` for deeper work |
| **Windows .exe / .dll** | PE format | Same as native — `strings` works fine on macOS/Linux against the file |
| **Flutter app** | Has `libflutter.so` / `App.framework` | Hard mode — Dart compiles to native; usually only string literals survive |

The script handles the mechanical parts (asar extraction, strings dump, listing frameworks). Your job is to reason about where the interesting code lives.

## Step 1: Map the architecture

Before searching for a specific feature, spend a minute on the shape of the app. Read:

- `package.json` (Electron) — name, version, main entry, dependencies. Dependencies tell you the stack (which ML libs, which auth, which networking).
- `Info.plist` (macOS) — bundle IDs, permissions, helper processes.
- The Frameworks directory — which native libraries ship? Sentry? Whisper? ONNX?
- For Electron: the list of files in `.webpack/` — presence of `main`, `renderer`, `preload`, and per-window subdirs (`hub/`, `settings/`, `meeting_recorder/`) tells you the window structure.
- Any helper apps (e.g., `Wispr Flow Helper.app`, `Signal Helper.app`) — these usually handle native-only duties like accessibility, audio capture, or text insertion, and talk to the main process over local IPC.

A rough mental model of the process tree helps you pick the right binary to dig into.

## Step 2: Find the endpoints the app talks to

This is almost always the fastest way to understand a cloud-backed feature. Grep the strings for URLs, hostnames, and WebSocket URIs:

```bash
grep -oE 'https?://[a-zA-Z0-9.-]+(/[a-zA-Z0-9._/-]*)?' <strings_or_bundle> | sort -u
grep -oE 'wss?://[a-zA-Z0-9.${}/_-]+' <strings_or_bundle> | sort -u
grep -oE '"/[a-zA-Z_][a-zA-Z0-9_/-]{3,80}"' <strings_or_bundle> | sort -u   # path literals
```

From the endpoint list you can usually tell:
- Which cloud providers are in play (AWS, Baseten, Modal, Replicate, OpenAI, Anthropic, Supabase, Auth0, Stripe…).
- Whether inference is local or remote.
- Streaming (WebSocket / gRPC) vs. batch (HTTP POST) paths.
- Auth/telemetry endpoints (often PostHog, Sentry, Segment, Amplitude).

Record these as the "outbound surface" of the app — you'll refer back to it.

## Step 3: Search for the feature or flow

Now tailor the search to the user's actual question. Some tested recipes:

**If they name a feature by marketing name** ("Push to Talk", "Agent Mode", "Personal Dictionary")
- Grep for the name directly and its camelCase/snake_case forms.
- Follow function names the grep surfaces, then search those.

**If they want the transcription/inference/generation flow**
- Grep for the obvious verb: `transcribe`, `complete`, `generate`, `embed`, `rerank`.
- Grep for audio/data-format helpers: `WAV`, `Opus`, `base64`, `ArrayBuffer`, `Float32`, `sampleRate`.
- Look for streaming primitives: `sendAudioPackets`, `AppendPackets`, `commit`, `finalize`, message-type enums with values like `{AUTH, APPEND, COMMIT}`.

**If they want auth / session / billing**
- Look for known SDKs: `Supabase`, `auth0`, `cognito`, `stripe`, `revenuecat`, `paddle`.
- API keys sometimes hard-coded next to endpoints (`Api-Key`, `Bearer`, `x-api-key`).

**If they want feature flags / remote config**
- `unleash`, `growthbook`, `launchdarkly`, `statsig`, `optimizely` are the usual suspects.
- Look for enum-looking objects with snake-case string values — that's often the flag registry.

**If they want embedded prompts**
- Long backtick-joined strings, often with `\n` separators.
- Grep for `You are`, `Your job`, `Assistant`, `system:` — common prompt openers.

**Telemetry → behavior map**
- Grep for `posthog`, `amplitude`, `segment`, `mixpanel`, `heap`, `capture(`, `track(`.
- Event names are extremely descriptive by design — `"dictation.started"`, `"chunk_received"`, `"fallback.groq"` — and map cleanly to code paths.

## Step 4: Pattern recognition in minified code

Webpack/esbuild-minified bundles still leak structure. Useful recognizer patterns:

- `99593(e,t,r){"use strict";r.d(t,{q:()=>_});` — webpack module definition. The number is the module ID, the `r.d` block lists exports.
- `{ASR:"asr",FORMAT:"format"}` — TypeScript enums survive minification as plain object literals.
- `class _{static FOO=...}` — static class fields survive with their original names.
- `let i=function(e){return e.TRANSCRIBE="transcribe",...,e}({})` — another enum shape.
- `(0,E.dS)(audio)` — calling an imported function. Search for `dS:` (export) to find the definition.
- `r(59725)` — a webpack require. The number is the target module's ID; search for it to jump there.
- `static async warmupConnection()` — static methods keep their names.
- `lT("<flag>", null)`, `getFeatureFlagData("<flag>")` — feature-flag reads.

When you find a mangled identifier (`Fe.o`, `M.ZZ`, `kt.ZZ`), grep for it to find the definition — usually a `class` or `const` that survived with descriptive property names.

## Step 5: Trace the flow

For "how does X work" questions, you need a directed trace, not just a grep dump. A good technique:

1. Find the **entry point** — the function that kicks off X (hotkey handler, button click, IPC listener).
2. Find the **exit point** — where the result is written/rendered/sent.
3. Walk the middle — each identifier references the next. Minified code reads poorly line-by-line but the control flow stays intact.

Constants are gold. Search for numeric literals with obvious units (`16000`, `48000` = sample rates; `1024`, `4096` = chunk sizes; `60_000`, `3600_000` = timeouts) and see where they're used — they anchor otherwise-anonymous code.

## Step 6: Synthesize and present

Report findings as a structured breakdown. The user almost always wants some subset of:

1. **The architecture** — which processes talk to which, via what transport.
2. **The endpoints and providers** — who does the heavy lifting (is it local or cloud, which vendor).
3. **The exact pipeline** — step by step, with real function/endpoint names quoted from the binary.
4. **The constants that govern behavior** — sample rates, chunk sizes, timeouts, retry limits.
5. **The feature flags that could change it** — which toggles are live, what they control.
6. **Quoted evidence** — short snippets from the binary, not paraphrases. "The bundle contains `basetenChunkSizeSeconds = 28`" beats "chunks are about half a minute."

Favor concrete over hand-wavy. You're giving the user specifics they couldn't otherwise see.

## Tips and pitfalls

- **Noise is real.** The strings file contains every string literal from every bundled dependency. Filter by context: if you find `transcribe`, the neighbors (5 lines before/after) tell you whether it's the app's code or a library's docs.
- **Prefer the bundle to the binary for Electron apps.** A 7 MB `index.js` is much more searchable than a 200 MB strings dump. Only fall back to strings if the bundle doesn't have what you need.
- **Two paths are common.** Many apps ship both a streaming and a batch path (WebSocket + HTTP fallback, or gRPC + WebSocket fallback). If you find one, look for the other — the enum and state machine usually name them.
- **Feature flags hide behavior.** A function may have three branches gated by flags. Don't assume the default path is the only path; check every `if (flag)` you find.
- **Don't publish extracted secrets.** API keys and tokens hardcoded in shipped binaries are common but still the developer's property. Note them for analysis; don't paste them into public writeups.
- **Large grep results drown you.** `grep -c` first to count, then narrow. Chain greps rather than writing huge regexes.
- **For JS bundles on one giant line:** line-based grep loses context. Use a small Python script (see `scripts/search.py`) to pull a character-window around matches.
- **Subagents excel at this.** If the user has multiple questions, spawn a Haiku subagent per question with the strings path in its prompt — keeps your main context clean.

## When the readable content runs out

If an app's important logic is in compiled code (Flutter/Dart, Rust, Swift with optimizations on, obfuscated JS), strings only gets you the edges — URLs, logs, class names. At that point the honest move is to say so and suggest dynamic analysis instead (mitmproxy for traffic, Instruments for runtime, Hopper/Ghidra for real disassembly). Don't fabricate internals you can't see.
