# Integration Test: Tier Violation Detection

> **This is a manual verification specification, not an automated test. Execute by invoking the skill-auditor skill manually as described below.**

**AK4 evidence** — demonstrates that skill-auditor correctly identifies and reports tier violations.

## Scenario

A skill is classified as **Light** tier (single-purpose, one action, fixed output) but its SKILL.md
has grown to 1,500 tokens — 50% over the Light-tier budget of 1,000 tokens.

### Fixture: oversized-light-skill (hypothetical)

The fixture path `malte/skills/oversized-light-skill/SKILL.md` does not exist on disk — it is a
hypothetical example. To run this test manually, create the fixture first:

```bash
mkdir -p malte/skills/oversized-light-skill
```

Then create `malte/skills/oversized-light-skill/SKILL.md` with approximately 1,130 words of
content (which × 1.33 ≈ 1,500 tokens). A minimal fixture that achieves this is a skill that does
one thing (e.g., formats a date) with extensive inline examples padding it to the required word
count. The skill must have no `references/` directory so it is clearly Light-tier by intent.

Once the fixture is created, verify the token count:

```bash
wc -w malte/skills/oversized-light-skill/SKILL.md | awk '{print int($1*1.33)}'
# → should output ~1500
```

Then run the audit as described in Invocation below. After the test, remove the fixture:

```bash
rm -rf malte/skills/oversized-light-skill
```

## Invocation

```
/skill-auditor
```

The auditor loads `~/.claude/standards/skills/token-budget-tiers.md`, assigns
`oversized-light-skill` to the **Light** tier (budget: 1,000 tokens), measures 1,500 tokens,
and emits a tier violation.

## Expected Output

The fleet report must include a **Tier Violations** section:

```
### Tier Violations
- oversized-light-skill: TIER VIOLATION — light-tier but uses 1500 tokens (budget: 1000)
```

The skill also loses Token Efficiency points:

- Exceeds budget by 500 tokens (50% over) → **Partial 6 pts** (not full 12 pts)

The fleet table row reflects the violation:

```
| oversized-light-skill | B | light | 120 | 1500 | n | Token budget exceeded (1500/1000) |
```

## Pass Criteria

1. The `TIER VIOLATION` line appears in the **Tier Violations** section.
2. The violation message follows the exact format:
   `{skill-name}: TIER VIOLATION — {tier}-tier but uses {N} tokens (budget: {limit})`
3. Token Efficiency score is reduced (partial or zero, not full 12 pts).
4. Skills within their tier budget produce **no** Tier Violations entry.
