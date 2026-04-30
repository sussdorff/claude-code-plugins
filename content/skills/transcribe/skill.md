---
name: transcribe
description: "Transcribe audio files with speaker diarization via AssemblyAI. Supports local files and Plaud AI cloud recordings."
triggers: transcribe, transkribiere, transcription, transkription, plaud, diarization, speaker recognition
requires_standards: [english-only]
---

# /transcribe

Transcribe audio with speaker diarization via AssemblyAI API. Supports local files and Plaud AI cloud recordings.

## Workflow

### Step 1: Run transcription

```bash
# Local file
transcribe ~/recording.mp3

# With language hint
transcribe ~/meeting.mp3 --language de

# Plaud AI: list recordings
transcribe --plaud

# Plaud AI: transcribe specific recording
transcribe --plaud --id a8747e81
```

### Step 2: Ask user about speakers

After the transcription completes, the CLI outputs the transcript with generic labels (Speaker A, Speaker B, ...) and saves it to `~/.local/share/transcribe/`.

**Always ask the user:**

> X Speaker erkannt. Wer ist wer?
> - Speaker A: (erster Satz zitieren)
> - Speaker B: (erster Satz zitieren)

### Step 3: Replace speaker labels in saved file

Once the user provides names, use `Edit` to replace labels in the saved transcript file:

```
Speaker A → Malte
Speaker B → Stefan
```

Replace all occurrences of `Speaker A` and `Speaker B` in the saved markdown file.

**Alternative:** If the user already knows the speakers upfront, pass them directly:

```bash
transcribe ~/meeting.mp3 --speakers "Malte,Stefan"
```

This maps Speaker A → first name, Speaker B → second name (in order of first appearance).

## Storage

Transcripts are auto-saved to `~/.local/share/transcribe/`:

```
~/.local/share/transcribe/
├── 2026-03-27_combined-recording.md
├── 2026-03-28_besprechung-praxissoftware.md
└── ...
```

## Credentials

Stored in `~/.config/transcribe/.env` (primary) with 1Password fallback:

| Secret | Env Var | 1Password Path |
|--------|---------|---------------|
| AssemblyAI API Key | `ASSEMBLYAI_API_KEY` | `op://API Keys/AssemblyAI/API Key` |
| Plaud AI Token | `PLAUD_TOKEN` | `op://API Keys/Plaud AI/API Key` |

## CLI Location

`~/.local/bin/transcribe`

## Supported Formats

MP3, WAV, OGG/Opus, M4A, FLAC, WebM, MP4 (audio track)

## Pricing

- AssemblyAI Universal-3 Pro + Diarization = $0.23/h
- With Speaker ID add-on = $0.25/h
- Free tier: 185h pre-recorded
- 80-min meeting costs ~$0.33
- Cost is shown in the transcript header

## Plaud AI Notes

- EU region (api-euc1.plaud.ai) — auto-detected from JWT
- Plaud token is a long-lived JWT (~10 months), extracted from web.plaud.ai localStorage
- Short IDs supported (e.g. `a8747e81` matches full UUID)
