---
name: prompt-extraction
description: Extract AI prompts from markdown files into an Obsidian-compatible vault. Use when the user wants to extract prompts from newsletters, articles, or documents, organize prompts into categories, or build a searchable prompt library. Handles pattern detection, quality scoring, wiki-linking, and index generation.
---

# Prompt Extraction Skill

## Overview

This skill provides tools for extracting AI prompts from markdown content and organizing them into an Obsidian-compatible vault with automated categorization, quality scoring, and searchable indexing.

## When to Use

Use this skill when the user wants to:
- Extract prompts from Substack newsletters, articles, or markdown files
- Build a searchable library of AI prompts
- Organize prompts by category (engineering, product, sales, etc.)
- Create an Obsidian vault for prompt management
- Generate wiki-linked Maps of Content (MOCs) for prompts
- Score and filter prompts by quality
- Process entire directories or backfill multiple sources

## Key Capabilities

### 1. Pattern Detection
- 12+ detection patterns for identifying prompts in markdown
- Role assignments, structural markers, placeholders
- Confidence scoring (0.0-1.0)
- Adjustable thresholds for different content types

### 2. Quality Scoring
- Automatic quality assessment based on 5 criteria:
  - Completeness (context, task, output)
  - Structure (sections, lists, formatting)
  - Clarity (placeholders, examples)
  - Length (substantial content)
  - Specificity (constraints, success criteria)
- Scores range from 0.0 to 1.0

### 3. Obsidian Integration
- YAML frontmatter with metadata
- Wiki-links for related prompts
- Tags for filtering (#engineering, #product, etc.)
- Maps of Content (MOCs) for organization
- Graph view support
- Templates for manual additions

### 4. LLM Search Index
- Machine-readable `prompts-index.json`
- Category, tag, and source indices
- Content previews and metadata
- Fast filtering and lookup

## Configuration

All scripts use a hierarchical configuration system with the following priority (highest to lowest):

1. **CLI Arguments** - Passed directly to scripts (highest priority)
2. **Project Config** - `.prompt-library-config.json` in current directory
3. **Global Config** - `~/.prompt-library-config.json` in home directory
4. **Default Values** - Built-in defaults (lowest priority)

### Setup Configuration

**First-time setup:**
```bash
# Copy config template to home directory
cp ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/assets/config-template.json \
  ~/.prompt-library-config.json

# Edit with your paths
nano ~/.prompt-library-config.json
```

**Example configuration:**
```json
{
  "vault_path": "~/my-prompts",
  "import_path": "~/Downloads/newsletters",
  "min_confidence": 0.15
}
```

**Project-specific configuration:**
```bash
# Create project-local config (overrides global)
cp ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/assets/config-template.json \
  .prompt-library-config.json
```

### Configuration Options

- **vault_path** (string): Path to Obsidian vault (default: `~/prompts`)
- **import_path** (string): Path to source files (default: `~/Downloads/newsletters`)
- **min_confidence** (float): Minimum confidence threshold (default: `0.15`)

See `assets/CONFIG_README.md` for complete configuration guide.

## How to Use

### Extract from Single File

```bash
# Uses config file settings
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/prompt_extractor.py \
  path/to/file.md \
  "https://source-url.com/article"

# Override vault path
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/prompt_extractor.py \
  path/to/file.md \
  "https://source-url.com/article" \
  --vault-path ~/custom-vault
```

### Extract from Directory (Batch)

```bash
# Uses config file settings
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/batch_extract_prompts.py \
  path/to/prompts/ \
  --source-url "https://source.com" \
  --source-type substack \
  --min-confidence 0.15

# Override config values
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/batch_extract_prompts.py \
  path/to/prompts/ \
  --vault-path ~/custom-vault \
  --min-confidence 0.2
```

### Backfill All Newsletters

```bash
# Uses config file settings
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/backfill_all_prompts.py \
  --yes

# Override vault path
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/backfill_all_prompts.py \
  --yes \
  --vault-path ~/custom-vault
```

### Regenerate MOCs and Index

```bash
# Uses config file settings
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/moc_generator.py

# Override vault path
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/moc_generator.py \
  --vault-path ~/custom-vault

# Generate search index
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/index_generator.py

# Override vault path
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/index_generator.py \
  --vault-path ~/custom-vault
```

### Check Configuration

```bash
# Show current configuration
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/config_loader.py --show

# Validate a config file
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/config_loader.py \
  --validate ~/.prompt-library-config.json
```

## Vault Structure

The tools create an Obsidian vault at `~/prompts/` with:

```
~/prompts/
├── library/              # All extracted prompts
│   ├── prompt-abc123.md
│   └── ...
├── mocs/                 # Maps of Content
│   ├── 00-index.md      # Main library index
│   ├── engineering.md   # Category MOCs
│   ├── product.md
│   ├── sales.md
│   └── sources.md       # By source
├── templates/           # Obsidian templates
│   ├── prompt-template.md
│   └── daily-note-with-prompts.md
├── prompts-index.json   # Machine-readable index
└── README.md           # Documentation
```

## Prompt File Format

Each extracted prompt has:

```markdown
---
id: prompt-abc123
title: Prompt Title
category: engineering
tags:
  - engineering
  - structured
  - role-based
source_url: https://source.com/article
source_type: substack
extracted_date: 2025-11-02
quality_score: 0.85
confidence: 0.92
related_prompts:
  - "[[prompt-def456|Related Prompt]]"
aliases:
  - alternative-name
---

# Prompt Title

**Source**: [Substack](https://source.com/article)
**Category**: #engineering

## Prompt

[Full prompt content...]

## Related Prompts

- [[prompt-def456|Related Prompt Name]]

---
*Extracted on 2025-11-02 | Confidence: 0.92 | Quality: 0.85*
```

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `config_loader.py` | Configuration management and validation |
| `prompt_detector.py` | Core pattern matching and detection |
| `prompt_extractor.py` | Single file extraction with quality scoring |
| `batch_extract_prompts.py` | Directory-level batch extraction |
| `backfill_all_prompts.py` | Process all newsletters automatically |
| `moc_generator.py` | Generate Maps of Content for Obsidian |
| `index_generator.py` | Create searchable JSON index |

## Categories

Prompts are automatically categorized into:
- **Analytics**: Data analysis, metrics, KPIs, dashboards
- **Engineering**: Software development, architecture, APIs
- **Operations**: Process optimization, automation
- **Product**: Product management, requirements, roadmaps
- **Sales**: Pipeline management, discovery, proposals
- **Strategy**: Strategic planning, market analysis
- **Writing**: Content creation, documentation

## Tags

Common tags automatically applied:
- `#structured` - Well-organized sections
- `#role-based` - Starts with role assignment
- `#multi-step` - Sequential instructions
- `#with-examples` - Includes examples
- `#high-confidence` - Confidence ≥0.8

## Examples

### Example 1: Extract from Newsletter Directory

User: "Extract prompts from the OpenAI newsletter"

```bash
# Uses config file for vault_path
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/batch_extract_prompts.py \
  output/OpenAI-Prompt-Templates/prompts \
  --source-url "https://natesnewsletter.substack.com/p/openai-templates" \
  --source-type substack \
  --min-confidence 0.15

# Then regenerate MOCs and index (uses config file)
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/moc_generator.py
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/index_generator.py
```

### Example 2: Backfill All Content

User: "Process all newsletters and extract all prompts"

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/backfill_all_prompts.py --yes
```

This automatically:
1. Scans `output/` for newsletters with prompts
2. Extracts from each
3. Regenerates MOCs and index
4. Provides summary statistics

### Example 3: Manual Testing

User: "Test extraction on a single file first"

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/prompt-extraction/scripts/prompt_extractor.py \
  "output/some-article/main-article.md" \
  "https://source.com/article"
```

## Integration with Obsidian

### Open Vault

In Obsidian: File → Open folder as vault → Select `~/prompts`

### Browse Prompts

- Start at `[[00-index]]` for all categories
- Browse by category: `[[engineering]]`, `[[product]]`, `[[sales]]`
- View by source: `[[sources]]`

### Use Graph View

- Cmd/Ctrl + G to visualize prompt relationships
- Related prompts are wiki-linked

### Search and Filter

- Cmd/Ctrl + O for quick switcher
- Cmd/Ctrl + Shift + F for full-text search
- Filter by tags: `tag:#engineering`
- Filter by quality in search: `quality_score >= 0.8`

### Embed Prompts

In daily notes or project notes:
```markdown
![[prompt-abc123]]  # Embeds full prompt
[[prompt-abc123|Custom Name]]  # Links with custom text
```

## Programmatic Access

### Load Index

```python
import json

with open(os.path.expanduser('~/prompts/prompts-index.json')) as f:
    index = json.load(f)

# Filter by category
eng_prompts = [p for p in index['prompts'] if p['category'] == 'engineering']

# Filter by quality
high_quality = [p for p in index['prompts'] if p['quality_score'] >= 0.8]

# Get prompt IDs by tag
structured_ids = index['tags'].get('structured', [])
```

### Read Prompt Content

```python
from pathlib import Path

prompt_id = "prompt-abc123"
vault_path = Path.home() / "prompts"
prompt_file = vault_path / "library" / f"{prompt_id}.md"
content = prompt_file.read_text()
```

## Templates

### Prompt Template

Use `assets/templates/prompt-template.md` for manually adding prompts to the vault.

### Daily Note Template

Use `assets/templates/daily-note-with-prompts.md` to track prompt usage in daily notes.

## Troubleshooting

### Low Confidence Scores

If prompts aren't being detected (confidence < 0.2):
- Lower threshold: `--min-confidence 0.10`
- Check if content is actually a prompt (has instructions, placeholders, etc.)
- Review detection patterns in `prompt_detector.py`

### Wrong Category

Categories are inferred from content keywords. To customize:
- Edit `prompt_extractor.py` `_infer_category()` method
- Add domain-specific keywords

### Missing Wiki-Links

Related prompts aren't automatically linked in v1.0. To add manually:
- Edit prompt files
- Add to `related_prompts` in frontmatter
- Add links in "Related Prompts" section

## Best Practices

1. **Start Small**: Test on one file before batch processing
2. **Adjust Threshold**: Use `--min-confidence 0.15` for known prompt directories
3. **Regenerate Regularly**: Update MOCs and index after new extractions
4. **Quality Check**: Review prompts with quality < 0.6 for accuracy
5. **Customize**: Modify category keywords and detection patterns for your domain

## Resources

All scripts are executable Python with minimal dependencies (PyYAML only).

- **Scripts**: `scripts/` directory
- **Templates**: `assets/templates/` directory
- **Documentation**: Check the vault's `README.md` after first extraction

## Version

Current version: 1.0.0
- Initial release with core extraction, quality scoring, and Obsidian integration
