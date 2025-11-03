---
description: Extract prompts from markdown files and add to Obsidian vault
---

You are helping the user extract prompts from markdown files into their Obsidian-compatible prompt library.

## Context

The user has a prompt extraction system with the following components:

1. **Prompt Detector** (`prompt_detector.py`): Detects prompts in markdown using pattern matching
2. **Prompt Extractor** (`prompt_extractor.py`): Extracts individual files
3. **Batch Extractor** (`batch_extract_prompts.py`): Processes entire directories
4. **MOC Generator** (`moc_generator.py`): Generates Maps of Content for Obsidian
5. **Index Generator** (`index_generator.py`): Creates `prompts-index.json` for LLM search

The vault is located at `~/prompts/` with structure:
- `library/` - extracted prompts as markdown with YAML frontmatter
- `mocs/` - Maps of Content (category MOCs, main index, sources)
- `templates/` - Obsidian templates

## Task

Based on the user's request, perform one of these operations:

### Single File Extraction
If the user provides a single markdown file:
1. Use `python prompt_extractor.py <file> [source_url]` to extract
2. Report results (prompts found, quality scores)

### Directory Extraction
If the user provides a directory (especially `prompts/` subdirectories):
1. Use `python batch_extract_prompts.py <directory> --source-url <url> --source-type <type> --min-confidence 0.15`
2. Report results

### Full Backfill (all newsletters)
If the user wants to process all newsletters in `output/`:
1. Find all directories in `output/` that contain `prompts/` subdirectories
2. For each, run batch extraction with appropriate source URL
3. After all extractions, regenerate MOCs and index

### Regenerate MOCs and Index
After extracting prompts:
1. Run `python moc_generator.py ~/prompts` to update Maps of Content
2. Run `python index_generator.py ~/prompts` to update search index
3. Report statistics

## Important Notes

- Use `--min-confidence 0.15` for directories of known prompts
- Extract source URL from newsletter metadata if available
- Always regenerate MOCs and index after batch extractions
- Report quality and confidence statistics

## Example Workflows

**Extract from single directory:**
```bash
python batch_extract_prompts.py output/newsletter-name/prompts --source-url "https://..." --source-type substack --min-confidence 0.15
python moc_generator.py ~/prompts
python index_generator.py ~/prompts
```

**Full backfill:**
1. Find all `output/*/prompts` directories
2. Batch extract from each
3. Regenerate MOCs and index
4. Report final statistics

Proceed with the user's request.
