# Prompt Library Tools

Extract AI prompts from markdown content into an Obsidian-compatible vault with automated categorization, quality scoring, and searchable indexing.

## Overview

This plugin provides a complete system for building and managing a searchable library of AI prompts. It extracts prompts from newsletters, articles, and documents, organizes them into an Obsidian vault with wiki-links and Maps of Content, and generates a machine-readable JSON index for programmatic access.

**Perfect for:**
- Building a personal prompt library from newsletters and articles
- Organizing AI prompts by category and quality
- Creating an Obsidian knowledge base for prompts
- Enabling LLM-powered prompt search and retrieval
- Tracking prompt sources and maintaining attribution

## Features

- **🔍 Pattern Detection**: 12+ patterns detect prompts with role assignments, structured sections, placeholders, and multi-step instructions
- **📊 Quality Scoring**: Automatic 0-1.0 scoring based on completeness, structure, clarity, length, and specificity
- **🔗 Wiki-Linking**: Related prompts connected via Obsidian wiki-links for graph view
- **🗂️ Auto-Categorization**: Prompts sorted into 7 categories (Engineering, Product, Sales, Analytics, etc.)
- **📚 Maps of Content**: Auto-generated MOCs for categories, sources, and quality tiers
- **🔎 Searchable Index**: JSON index with category, tag, and source indices for fast filtering
- **📝 Obsidian Templates**: Templates for manual prompt additions and daily notes
- **⚡ Batch Processing**: Extract from single files, directories, or entire newsletter collections

## Installation

```bash
# From your Claude Code plugins marketplace
/plugin install prompt-library-tools@your-marketplace
```

Or add to your local marketplace:

```json
{
  "name": "local-dev",
  "plugins": [
    {
      "name": "prompt-library-tools",
      "source": "./prompt-library-tools"
    }
  ]
}
```

## Quick Start

###1. Extract from a Single File

```bash
/extract-prompts
```

Then select the file and provide the source URL when prompted.

### 2. Extract from a Directory

For a directory of known prompts (like a `prompts/` folder from a newsletter):

```python
python ~/.claude/plugins/prompt-library-tools/skills/prompt-extraction/scripts/batch_extract_prompts.py \
  output/newsletter-name/prompts \
  --source-url "https://source.com/article" \
  --source-type substack \
  --min-confidence 0.15
```

### 3. Backfill All Newsletters

To process all newsletters in your `output/` directory:

```python
python ~/.claude/plugins/prompt-library-tools/skills/prompt-extraction/scripts/backfill_all_prompts.py --yes
```

### 4. Open in Obsidian

In Obsidian:
1. File → Open folder as vault
2. Select `~/prompts`
3. Start at `[[00-index]]` to browse all prompts

## Commands

### `/extract-prompts`

Interactive prompt extraction command.

**Usage:**
- Single file: Provide path and source URL
- Directory: Process entire directories of prompts
- Backfill: Extract from all newsletters automatically

**Options:**
- `--min-confidence` - Adjust detection threshold (default: 0.15)
- `--source-type` - Source platform (substack, notion, patreon, local)

## Skills

### `prompt-extraction`

Automatically invoked when working with prompt extraction, vault organization, or library management.

**Triggers on:**
- "Extract prompts from..."
- "Build a prompt library..."
- "Organize prompts into categories..."
- "Create searchable prompt index..."

**Provides:**
- Pattern detection scripts
- Quality scoring system
- MOC generation
- Index creation
- Obsidian integration

## Vault Structure

The plugin creates a vault at `~/prompts/`:

```
~/prompts/
├── library/              # All extracted prompts (one file per prompt)
│   ├── prompt-abc123.md
│   ├── prompt-def456.md
│   └── ...
├── mocs/                 # Maps of Content
│   ├── 00-index.md      # Main library index
│   ├── analytics.md     # Category MOCs
│   ├── engineering.md
│   ├── product.md
│   ├── sales.md
│   ├── sources.md       # Organized by source
│   └── ...
├── templates/           # Obsidian templates
│   ├── prompt-template.md
│   └── daily-note-with-prompts.md
├── prompts-index.json   # Machine-readable search index
└── README.md           # Vault documentation
```

## Prompt Format

Each prompt file contains:

```markdown
---
id: prompt-abc123
title: Technical Debt Prioritization
category: engineering
tags:
  - engineering
  - structured
  - role-based
source_url: https://natesnewsletter.substack.com/p/article
source_type: substack
extracted_date: 2025-11-02
quality_score: 0.85
confidence: 0.92
related_prompts:
  - "[[prompt-def456|API Review Guide]]"
aliases:
  - tech-debt-planner
---

# Technical Debt Prioritization

**Source**: [Substack](https://natesnewsletter.substack.com/p/article)
**Category**: #engineering

## Prompt

You are a senior engineering manager conducting a quarterly technical debt review...

[Full prompt content]

## Related Prompts

- [[prompt-def456|API Review Guide]]

---
*Extracted on 2025-11-02 | Confidence: 0.92 | Quality: 0.85*
```

## Categories

Prompts are automatically categorized:

- **Analytics** (15+): Data analysis, metrics, KPIs, dashboards, reporting
- **Engineering** (15+): Software development, architecture, technical debt, APIs
- **Operations** (3+): Process optimization, workflow automation, efficiency
- **Product** (14+): Product management, requirements, competitive analysis
- **Sales** (14+): Pipeline management, discovery, proposals, deal analysis
- **Strategy** (1+): Strategic planning, M&A, market analysis
- **Writing** (1+): Content creation, documentation, communication

## Quality Scoring

Prompts are scored 0.0-1.0 based on:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Completeness | 30% | Has context, task, and output specifications |
| Structure | 25% | Well-organized sections, lists, formatting |
| Clarity | 20% | Uses placeholders, examples, clear instructions |
| Length | 15% | Substantial content (500+ characters) |
| Specificity | 10% | Constraints, success criteria, details |

**Quality Tiers:**
- **Excellent (≥0.8)**: Production-ready, comprehensive prompts
- **Good (0.6-0.8)**: Solid prompts, may need minor refinement
- **Standard (<0.6)**: Basic prompts, may need customization

## Search Index

The `prompts-index.json` file provides programmatic access:

```json
{
  "version": "1.0",
  "total_prompts": 63,
  "prompts": [
    {
      "id": "prompt-abc123",
      "title": "Technical Debt Prioritization",
      "category": "engineering",
      "tags": ["engineering", "structured"],
      "quality_score": 0.85,
      "content_preview": "First 500 chars...",
      "file_path": "library/prompt-abc123.md"
    }
  ],
  "categories": {
    "engineering": {
      "count": 15,
      "avg_quality": 0.69,
      "prompt_ids": ["prompt-abc123", "..."]
    }
  },
  "tags": {
    "structured": ["prompt-abc123", "..."]
  }
}
```

## Usage Examples

### Example 1: Extract from Newsletter

You have a newsletter in `output/openai-templates/prompts/`:

```bash
python ~/.claude/plugins/prompt-library-tools/skills/prompt-extraction/scripts/batch_extract_prompts.py \
  output/openai-templates/prompts \
  --source-url "https://natesnewsletter.substack.com/p/openai-templates" \
  --source-type substack

# Regenerate MOCs and index
python ~/.claude/plugins/prompt-library-tools/skills/prompt-extraction/scripts/moc_generator.py ~/prompts
python ~/.claude/plugins/prompt-library-tools/skills/prompt-extraction/scripts/index_generator.py ~/prompts
```

### Example 2: Filter by Quality

Find all high-quality engineering prompts:

```python
import json

with open(os.path.expanduser('~/prompts/prompts-index.json')) as f:
    index = json.load(f)

eng_high_quality = [
    p for p in index['prompts']
    if p['category'] == 'engineering' and p['quality_score'] >= 0.8
]

print(f"Found {len(eng_high_quality)} high-quality engineering prompts")
```

### Example 3: Use in Obsidian

1. Open `~/prompts` as vault
2. Navigate to `[[00-index]]`
3. Browse category: `[[engineering]]`
4. View graph: Cmd/Ctrl + G
5. Search: Cmd/Ctrl + O
6. Embed in note: `![[prompt-abc123]]`

## Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `prompt_detector.py` | Pattern matching | Detects prompts with confidence scoring |
| `prompt_extractor.py` | Single file extraction | Extracts one file at a time with quality scoring |
| `batch_extract_prompts.py` | Directory extraction | Processes entire directories |
| `backfill_all_prompts.py` | Full backfill | Scans and processes all newsletters |
| `moc_generator.py` | MOC generation | Creates Maps of Content for categories |
| `index_generator.py` | Index creation | Generates `prompts-index.json` |

## Configuration

### Vault Location

Default: `~/prompts`

To change, modify the `vault_path` parameter in script calls.

### Detection Threshold

Default: `0.15` for directories of known prompts

Lower for more permissive detection:
```bash
--min-confidence 0.10
```

Higher for stricter detection:
```bash
--min-confidence 0.30
```

### Categories

To customize category keywords, edit `prompt_extractor.py` `_infer_category()` method.

## Requirements

- Python 3.8+
- PyYAML (`pip install pyyaml`)
- Obsidian (optional, for vault browsing)

All scripts use standard library except PyYAML for frontmatter parsing.

## Troubleshooting

### Prompts Not Detected

**Symptoms**: Low or zero prompts extracted

**Solutions**:
- Lower threshold: `--min-confidence 0.10`
- Check if content is actually prompts (has instructions, placeholders)
- Run with debug: Add `--debug` flag to `prompt_detector.py`

### Wrong Categories

**Symptoms**: Prompts categorized incorrectly

**Solutions**:
- Edit `prompt_extractor.py` `_infer_category()` method
- Add domain-specific keywords
- Manually edit frontmatter `category` field

### Missing Index

**Symptoms**: `prompts-index.json` not found

**Solutions**:
```bash
python ~/.claude/plugins/prompt-library-tools/skills/prompt-extraction/scripts/index_generator.py ~/prompts
```

### MOCs Out of Date

**Symptoms**: New prompts not showing in MOCs

**Solutions**:
```bash
python ~/.claude/plugins/prompt-library-tools/skills/prompt-extraction/scripts/moc_generator.py ~/prompts
```

## Best Practices

1. **Test First**: Run on single file before batch processing
2. **Adjust Threshold**: Use `0.15` for known prompts, `0.20+` for general content
3. **Regenerate Regularly**: Update MOCs and index after new extractions
4. **Quality Check**: Review prompts with score < 0.6
5. **Use Obsidian**: Graph view reveals prompt relationships
6. **Track Sources**: Always provide source URLs for attribution
7. **Customize**: Modify category keywords for your domain

## Contributing

Contributions welcome! To improve the plugin:

1. Fork the repository
2. Create a feature branch
3. Add/improve detection patterns in `prompt_detector.py`
4. Enhance quality scoring in `prompt_extractor.py`
5. Add new categories or refine existing ones
6. Submit a pull request

## License

MIT License - See LICENSE file for details

## Author

Created by Malte

## Version

**Current**: 1.0.0

**Changelog:**
- 1.0.0 (2025-11-02): Initial release
  - Core extraction with 12+ detection patterns
  - Quality scoring system
  - Obsidian integration with wiki-links and MOCs
  - JSON search index
  - Batch processing and backfill support
  - Templates and documentation

---

**Support**: For issues or questions, please open an issue in the repository.
