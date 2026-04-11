# Brand Examples

Annotated examples of brand profiles demonstrating key patterns.

## Example 1: Standalone Voice Brand

`malte-professional` — a base brand used independently or as parent.

**Key patterns:**
- No `inherits` field — standalone brand
- Concrete vocabulary rules with rationale ("Validierung" over "Test" — implies structured verification)
- Writing rules include formatting specifics (German number format, Umlaut rules)
- Good/bad examples show the same content in contrasting styles

**What makes it work:**
- Every Avoid entry has a replacement, not just "don't use X"
- Examples are realistic — actual proposal text, not lorem ipsum
- Token-efficient at ~340 tokens — leaves headroom for inheritance

## Example 2: Inherited Voice Brand

`cognovis-proposals` — extends `malte-professional` with proposal-specific rules.

**Key patterns:**
- `inherits: malte-professional` — only defines what differs from parent
- Adds domain vocabulary (Stufenmodell, Festpreis, Abnahmekriterien)
- Writing rules extend parent's with structural requirements (Kurzuebersicht table)
- Examples demonstrate the Stufenmodell pattern specifically

**What makes it work:**
- Doesn't repeat parent's tone rules — only adds "customer perspective" framing
- Vocabulary Avoid section focuses on proposal-specific traps (concrete customer metrics)
- Combined resolution ~680 tokens — well within 3000 budget

## Anti-Patterns

### Too Vague
```markdown
### Tone & Register
- Be professional
- Use appropriate language
```
**Fix:** Specify formality level (Sie/du), emotional register (warm/neutral), and concrete constraints.

### Too Long
```markdown
### Vocabulary
#### Prefer
- "Investition" over "Kosten"
- "Loesung" over "Produkt"
- [50 more entries...]
```
**Fix:** Keep vocabulary to 5-10 high-impact entries. More granular rules belong in a reference file, not the brand profile.

### Contradictory
```markdown
### Tone & Register
- Casual and friendly

### Writing Rules
- Always use Sie-Form
```
**Fix:** Sie-Form is formal, not casual. Align tone description with actual rules.

### Missing Examples
A brand without `<example-good>` blocks forces skills to interpret rules subjectively. Always include at least one good/bad pair showing the brand in practice.
