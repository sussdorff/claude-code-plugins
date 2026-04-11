# Brand Interview Guide

Guided discovery workflow for creating brand profiles. Ask one question group at a time, wait for answers, then proceed.

## Intent Classification

Before starting questions, classify the request:

| Signal | Type | Start at |
|--------|------|----------|
| "tone", "writing style", "how I write" | `voice` | Voice Q1 |
| "colors", "logo", "design system" | `visual` | Visual Q1 |
| "brand", "identity", both signals | `combined` | Voice Q1, then Visual Q1 |

**Skip-if-answered rule:** If the user's initial request already covers a question group, acknowledge what you captured and skip to the next group.

## Voice Questions

### Q1: Purpose & Audience

**WHY:** A brand without a defined audience drifts into generic advice. Context determines every other decision.

- Who reads content written in this voice? (developers, clients, general public?)
- What contexts does this brand appear in? (emails, proposals, docs, social?)
- What is the single most important impression readers should take away?

### Q2: Formality & Register

**WHY:** Formality is the highest-impact voice lever. Getting du/Sie or casual/formal wrong undermines everything else.

- Du or Sie? (or English: first-name basis or formal?)
- Where on the spectrum: conversational -- professional -- academic -- legal?
- How do you address groups? ("ihr", "you all", "the team"?)

### Q3: Tone & Personality

**WHY:** Tone is the emotional texture layered on top of formality. Two formal voices can feel completely different.

- Pick 2-3 adjectives: warm, neutral, authoritative, playful, direct, empathetic, analytical, encouraging?
- What emotion should the reader feel after reading? (confident, welcomed, informed, motivated?)
- What tone should this voice NEVER have? (condescending, overly casual, stiff?)

### Q4: Writing Rules

**WHY:** Without concrete structural rules, tone guidance stays vague and unenforceable.

- Sentence length preference: short and punchy, or flowing and detailed?
- Active or passive voice? (or mixed with a default?)
- Paragraph structure: one idea per paragraph? Max sentences per paragraph?
- Formatting habits: bullet lists vs prose? Headers for structure?

### Q5: Vocabulary

**WHY:** Word choice is where brand becomes tangible. Specific word lists prevent drift across sessions.

- 3-5 terms you always want to use (and why)
- 3-5 terms you want to avoid (and what to say instead)
- Jargon policy: use domain terms freely, define them, or avoid entirely?
- Any signature phrases or verbal tics that define this voice?

### Q6: Examples

**WHY:** Examples ground abstract rules in reality. They also expose contradictions between stated rules and actual preference.

- Share 2-3 real examples of writing that nails this voice (emails, docs, messages)
- If no examples exist: write a short paragraph in this voice right now, and I will reflect it back for calibration

After examples, summarize the captured voice profile and ask for corrections before generating the brand file.

## Visual Questions

### V1: Colors

**WHY:** Color is the fastest brand recognition signal. Vague color preferences lead to inconsistent output.

- Primary color (hex or name) -- used for headings, buttons, key elements
- Secondary color -- used for backgrounds, secondary elements
- Accent color -- used for highlights, calls to action
- Any colors explicitly forbidden?

### V2: Typography

**WHY:** Font choices carry personality. Serif vs sans-serif alone shifts perception significantly.

- Primary font family (headings)
- Secondary font family (body text)
- Preferred weights (bold headings? light body?)
- Monospace font for code (if relevant)

### V3: Logo Rules

**WHY:** Logo misuse is the most visible brand violation. Clear rules prevent it.

- Primary placement (top-left, centered, etc.)
- Minimum clear space around logo
- Minimum size
- What backgrounds is the logo allowed on?

### V4: Spacing & Layout

**WHY:** Consistent spacing is invisible when right and jarring when wrong. Explicit values prevent guessing.

- Standard margins (page/document level)
- Padding conventions (inside containers, cards)
- Line height preference (tight, normal, airy)
- Any grid system or column conventions?

After visual questions, summarize the captured visual profile and ask for corrections before generating.

## Workflow Summary

1. Classify intent (voice / visual / combined)
2. Ask one group at a time, skip what is already answered
3. After last group: present full summary for review
4. Generate brand profile file from confirmed answers
5. Run review checklist against the generated profile
