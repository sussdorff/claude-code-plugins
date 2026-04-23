---
name: mail-send
model: haiku
description: Send emails with attachments via Apple Mail AppleScript automation. Prepares a visible draft for user review before sending. Use when sending emails with file attachments. Triggers on send email, mail send, email with attachment, mail schicken.
disableModelInvocation: true
---

# mail-send

Sends emails with attachments via Apple Mail (Mail.app) using AppleScript automation.

## When to Use

- User wants to send an email with one or more file attachments
- User says "send email", "mail send", "email with attachment"
- User says "e-mail senden", "mail schicken", "email verschicken"
- Fastmail MCP `send_email` cannot be used because attachments are required

## Do NOT

- Do NOT send emails without presenting the draft for user review first
- Do NOT use for emails without attachments — use Fastmail MCP tools instead

## Accounts

The user's email accounts in Apple Mail:

| Address | Purpose |
|---------|---------|
| malte.sussdorff@cognovis.de | Business / geschäftlich |
| sussdorff@sussdorff.de | Private / persönlich |

Note: Gmail is a legacy account — never use it as sender.

**IMPORTANT:** Always set the `sender` property to select the correct From address. Without it, Apple Mail defaults to the last-used account (often Gmail).

| Context | Use sender |
|---------|------------|
| Business / geschäftlich | `malte.sussdorff@cognovis.de` |
| Private / persönlich | `sussdorff@sussdorff.de` |

Default (if unclear): `malte.sussdorff@cognovis.de`

## AppleScript Template

```applescript
tell application "Mail"
    activate
    set newMessage to make new outgoing message with properties {subject:"SUBJECT", content:"BODY", visible:true, sender:"malte.sussdorff@cognovis.de"}
    tell newMessage
        make new to recipient at end of to recipients with properties {address:"recipient@example.com"}
        -- Optional CC:
        -- make new cc recipient at end of cc recipients with properties {address:"cc@example.com"}
        make new attachment with properties {file name:POSIX file "/absolute/path/to/file.pdf"}
        -- Additional attachments:
        -- make new attachment with properties {file name:POSIX file "/absolute/path/to/file2.pdf"}
    end tell
end tell
```

## Usage Pattern

Run via `osascript` heredoc:

```bash
osascript << 'APPLESCRIPT'
tell application "Mail"
    activate
    set newMessage to make new outgoing message with properties {subject:"Subject here", content:"Body text here", visible:true, sender:"malte.sussdorff@cognovis.de"}
    tell newMessage
        make new to recipient at end of to recipients with properties {address:"recipient@example.com"}
        make new attachment with properties {file name:POSIX file "/absolute/path/to/attachment.pdf"}
    end tell
end tell
APPLESCRIPT
```

## Multiple Recipients and Multiple Attachments

```bash
osascript << 'APPLESCRIPT'
tell application "Mail"
    activate
    set newMessage to make new outgoing message with properties {subject:"Subject", content:"Body", visible:true, sender:"malte.sussdorff@cognovis.de"}
    tell newMessage
        make new to recipient at end of to recipients with properties {address:"first@example.com"}
        make new to recipient at end of to recipients with properties {address:"second@example.com"}
        make new cc recipient at end of cc recipients with properties {address:"cc@example.com"}
        make new attachment with properties {file name:POSIX file "/path/to/file1.pdf"}
        make new attachment with properties {file name:POSIX file "/path/to/file2.pdf"}
    end tell
end tell
APPLESCRIPT
```

## Long Bodies and Umlauts / Special Characters (MANDATORY PATTERN)

**Problem:** Apple Mail via AppleScript is extremely sensitive to:

1. **Encoding:** `read POSIX file "..."` defaults to MacRoman. UTF-8 bytes get
   interpreted as multi-byte glyphs, producing garbled output like `√§` for `ä`,
   `‚Äî` for `—`, or `"` for `„`. German text, em-dashes, curly quotes, and
   bullets (•) all break this way.
2. **Inline heredoc quoting:** Large bodies with German punctuation or nested
   quotes frequently trip the AppleScript parser with cryptic errors like
   `syntax error: Unknown token found.` Line-length and quote-escaping are both
   fragile.

**Mandatory pattern for any body with umlauts, em-dashes, curly quotes, or > ~20 lines:**

Step 1 — write the body to a UTF-8 file via the `Write` tool (never via
`echo > file` in Bash, which may drop encoding):

```
Write → /tmp/mail-body.txt  (UTF-8, full email body)
```

Step 2 — run AppleScript that reads the file with the explicit UTF-8 class
via a separate `.applescript` file (heredoc + AppleScript heredoc + UTF-8
marker don't coexist reliably):

```bash
cat << 'EOF' > /tmp/create-draft.applescript
tell application "Mail"
    activate
    set mailContent to read POSIX file "/tmp/mail-body.txt" as «class utf8»
    set newMessage to make new outgoing message with properties {subject:"Subject with Umlauts ÄÖÜ", content:mailContent, visible:true, sender:"malte.sussdorff@cognovis.de"}
    tell newMessage
        make new to recipient at end of to recipients with properties {address:"recipient@example.com"}
    end tell
end tell
EOF
osascript /tmp/create-draft.applescript
```

**The `as «class utf8»` clause is non-optional** — omitting it produces the
MacRoman-interpretation garbage. The guillemets around `class utf8` are part of
the AppleScript syntax (option-backslash / option-shift-backslash on a German
keyboard, or pasted literally).

**Expected output:** `osascript` returns the string `missing value` on success.
This is not an error — AppleScript's `make` returns a message reference, which
`osascript` prints as `missing value` when returned to the shell.

## Rules

- Always use `visible:true` — creates a visible draft for user review, never auto-sends
- File paths must be absolute POSIX paths (e.g. `/Users/malte/Documents/file.pdf`)
- Never use relative paths in the `file name` property
- For bodies with German text, em-dashes, curly quotes, bullets, or > ~20 lines:
  **always use the file + UTF-8 pattern above**. Inline heredoc bodies are only
  safe for short ASCII-only content (subject confirmations, one-liners).

## DO NOT

- Do NOT use Spark for AppleScript automation — Spark has no AppleScript dictionary
- Do NOT auto-send emails — always create a visible draft for user review
- Do NOT use Fastmail MCP `send_email` for emails with attachments (no attachment support)
- Do NOT use relative file paths in the attachment `file name` property
- Do NOT inline long bodies with umlauts in a Bash heredoc — AppleScript will mangle
  the encoding. Use the file + `read as «class utf8»` pattern.
- Do NOT use `read POSIX file "..."` without the `as «class utf8»` clause when the
  body contains non-ASCII characters.
