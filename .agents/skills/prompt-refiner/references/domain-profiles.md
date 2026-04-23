# Domain Profiles

Context templates for different task domains. Injected into the HeyPresto `context`
field or into the local meta-prompting system prompt.

## Code / Engineering

```
Stack: Python 3.12+ with uv, pytest. Claude Code CLI environment.
Follow existing patterns in the codebase. Use dependency injection for testability.
Prefer editing existing files over creating new ones. Keep solutions minimal.
Include acceptance criteria as a checklist. Output should be implementable without
further clarification.
```

HeyPresto params: `mode=code, tone=technical, format=Sections, length=detailed`

## Documents / PRDs

```
Write for decision-makers who need to act on this document.
Lead with the decision or action requested. Quantify impact where possible.
Use the template structure: Problem → Options → Recommendation → Next Steps.
Keep total length under 500 words unless explicitly asked for more.
```

HeyPresto params: `mode=doc, tone=professional, format=Sections, length=medium`

## Presentations / Decks

```
One idea per slide. Lead with the headline (conclusion, not topic).
Include speaker notes with talking points. Structure: Problem → Evidence →
Solution → Ask. Limit to 10-12 slides for a 20-minute presentation.
```

HeyPresto params: `mode=deck, tone=executive, format=Outline, length=medium`

## Data / Analysis

```
Start with the question being answered, not the methodology.
Include data sources, time ranges, and sample sizes.
Show calculations explicitly. Flag assumptions with [ASSUMPTION].
Distinguish correlation from causation.
```

HeyPresto params: `mode=data, tone=technical, format=Table, length=detailed`

## Marketing / Copy

```
Know the audience segment and their pain point.
Lead with benefit, not feature. Include clear CTA.
Specify tone (brand voice), word count targets, and platform constraints.
Provide A/B test variations when relevant.
```

HeyPresto params: `mode=copy, tone=creative, format=Sections, length=medium`

## Communications / Slack / Email

```
Async-first: assume the reader has 30 seconds.
Structure: What happened → What it means for you → What to do.
Include explicit action items with owners and deadlines.
Thread-friendly: key info in first message, details in thread.
```

HeyPresto params: `mode=comms, tone=friendly, format=Email, length=concise`

## Research / Analysis

```
Lead with findings, not methodology. Cite sources with dates.
Distinguish primary sources from secondary. Flag anything unverified with [UNVERIFIED].
Include a "Limitations" section. Provide a spot-check list (3-5 claims a human should verify).
```

HeyPresto params: `mode=default, tone=professional, format=Sections, length=comprehensive`
