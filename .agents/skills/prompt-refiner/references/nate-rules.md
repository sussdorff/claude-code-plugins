# Nate's 15 Prompt Structure Rules

Extracted from 724 prompts by Nate Jones (natesnewsletter.substack.com).
Use as context injection: pick 3-5 rules relevant to the task domain.

## Rules

### R1: Role = Identity + Activity
Every prompt needs a role sentence combining WHO + WHAT THEY'RE DOING NOW.
Bad: "You are an expert." Good: "You are a senior engineering manager conducting a quarterly technical debt review."

### R2: Quantified Constraints
Constraints must be specific and measurable, never qualitative.
Bad: "Keep it concise." Good: "Total length: 500 words maximum." "Exactly 3 options."

### R3: Named Anti-Hallucination Guards
Name the specific failure mode, not the abstract quality.
Bad: "Be accurate." Good: "Do not invent sources, links, quotes, or citations. If you can't verify, say so plainly."

### R4: Output as Fillable Template
Provide the exact structure with bracketed placeholders, not a description of what to produce.
Bad: "Provide a prioritized list with impact analysis."
Good: Provide the actual template with [bracketed fields] showing exactly what goes where.

### R5: One Question at a Time
Missing info triggers ONE question (most important first), not a halt.
"If I don't know, propose 2-3 reasonable options and ask me to pick. Once you have enough, start immediately."

### R6: Explicit START Protocol
End prompts with: "Restate understanding. List missing info. Ask single most important question. If nothing missing, begin."

### R7: Named Anti-Patterns
Name the specific bad patterns, not the desired quality.
Bad: "Write clearly." Good: "Never use: SWOT with vague entries, lists without prioritization, analysis that treats all factors equally."

### R8: Self-Verification Checklist
Pre-output verification: "QUALITY CHECKS - Before outputting, verify: [checklist]. If any check fails, revise before outputting."

### R9: Do-NOT/Instead Pairs
Every prohibition gets an explicit alternative.
"DO NOT hedge" pairs with "Use active voice ('We should approve X' not 'X could be approved')."

### R10: Inline Uncertainty Tags
Give the AI a mechanism to flag uncertainty: [VERIFY], [ASSUMPTION], [PLACEHOLDER], [REVIEW], [UNVERIFIED].

### R11: Decision Formulas over Adjectives
Bad: "Prioritize by importance."
Good: "Priority Score = (Business Impact x Urgency) / Engineering Cost. Show calculation for top 3."

### R12: Stop Conditions for Irreversible Actions
"If anything is destructive (delete/overwrite/migrate), STOP and ask for explicit confirmation first."

### R13: When-to-Use Metadata Outside the Prompt
Separate header explaining the use case, distinct from the instructions the AI sees.

### R14: Scope to Failure Mode
Name the specific way the output typically goes wrong. Design the prompt to prevent that failure.

### R15: Goldilocks Length (400-500 tokens)
Domain-specific behavioral guidance: "specific enough to guide behavior, flexible enough to let the model think."

## Quick-Pick Guide

| Domain | Prioritize Rules |
|--------|-----------------|
| Code/Engineering | R1, R2, R4, R8, R12 |
| Documents/PRDs | R1, R4, R6, R8, R14 |
| Research/Analysis | R1, R3, R10, R11, R14 |
| Creative/Copy | R1, R7, R9, R15 |
| Communications | R1, R2, R5, R9 |
| Delegation/Tasks | R1, R5, R6, R8, R12 |
