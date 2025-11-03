# Obsidian Integration Guide

Complete guide for using the prompt library vault in Obsidian.

## Opening the Vault

1. Launch Obsidian
2. File → Open folder as vault
3. Navigate to and select: `~/prompts`
4. Click "Open"

The vault will open with your extracted prompts.

## Navigation

### Main Entry Points

1. **[[00-index]]** - Start here for overview of all prompts
   - Total prompts count
   - Categories with counts
   - Quality distribution
   - Recent additions

2. **Category MOCs**
   - [[analytics]] - Data analysis and metrics prompts
   - [[engineering]] - Software development prompts
   - [[product]] - Product management prompts
   - [[sales]] - Sales and pipeline prompts
   - And more...

3. **[[sources]]** - Prompts organized by source
   - Groups by source type (Substack, Notion, etc.)
   - Shows prompts per source
   - Links to top prompts from each source

### Quick Navigation

- **Cmd/Ctrl + O** - Quick switcher (search prompts by name)
- **Cmd/Ctrl + P** - Command palette
- **Cmd/Ctrl + Shift + F** - Full-text search across all prompts
- **Cmd/Ctrl + G** - Toggle graph view

## Search and Filter

### By Tag

Use Obsidian search with tag filters:

```
tag:#engineering
tag:#structured
tag:#high-confidence
```

Combine tags:
```
tag:#engineering tag:#structured
```

### By Quality

Search in files:
```
quality_score: 0.8
```

Or use file explorer to browse MOCs organized by quality tier.

### By Category

Navigate to category MOC:
- Click `[[engineering]]` from index
- Or use quick switcher: Cmd/Ctrl + O → type "engineering"

## Graph View

### Open Graph View

1. Cmd/Ctrl + G to toggle
2. Or click graph icon in left sidebar

### Understanding Connections

- **Nodes** - Each prompt is a node
- **Lines** - Wiki-links between related prompts
- **Clusters** - Prompts in same category tend to cluster
- **Size** - More connections = larger node

### Graph Filters

Use graph controls to filter:
- By tag: Show only `#engineering` prompts
- By path: Show only `library/` files
- Depth: How many link levels to show

### Navigation in Graph

- Click node → Opens prompt
- Hover node → Shows preview
- Drag nodes → Rearrange layout
- Zoom → Mouse wheel or pinch

## Using Prompts

### Embed in Notes

To embed full prompt in a note:

```markdown
![[prompt-abc123]]
```

This includes the entire prompt content.

### Link to Prompts

To link with custom text:

```markdown
See the [[prompt-abc123|Technical Debt Guide]] for details.
```

### Create Prompt Collections

Create a note with prompts for a specific workflow:

```markdown
# Weekly Review Prompts

## Planning
- [[prompt-abc123|Implementation Planner]]
- [[prompt-def456|Roadmap Prioritizer]]

## Analysis
- [[prompt-ghi789|Metrics Dashboard]]
- [[prompt-jkl012|Performance Review]]
```

## Daily Notes Integration

### Use Template

1. Open Settings → Core plugins → Enable "Templates"
2. Set template folder: `templates`
3. Create daily note
4. Insert template: Cmd/Ctrl + P → "Templates: Insert template"
5. Select `daily-note-with-prompts`

### Track Usage

In daily notes:

```markdown
# 2025-11-03

## Prompts Used Today

- [[prompt-abc123|Tech Debt Assessment]] - Used for: Sprint planning
  - Results: Identified 3 critical items
  - Refinements: Added specific team context

## Prompts to Try

- [ ] [[prompt-def456|API Review Guide]] - For: New endpoint design
```

### Link Projects

```markdown
# Project: Database Migration

**Prompts Used:**
- [[prompt-abc123|Schema Analysis]]
- [[prompt-def456|Migration Plan]]

**Context:**
Migrating from MySQL to PostgreSQL for performance improvement.

**Results:**
Schema analyzer identified 12 compatibility issues, migration planner created 4-phase approach.
```

## Adding Prompts Manually

### Use Template

1. Cmd/Ctrl + O → "prompt-template"
2. Copy template to new note
3. Fill in frontmatter:
   - Set unique ID (use timestamp: `prompt-20251103123045`)
   - Add title, category, tags
   - Set quality_score (estimate 0.5-0.8 for manual entry)
4. Add prompt content
5. Save to `library/` directory
6. Regenerate index and MOCs

### Frontmatter Fields

```yaml
---
id: prompt-20251103123045
title: Your Prompt Title
category: engineering  # or product, sales, analytics, etc.
tags:
  - engineering
  - custom-tag
source_url: https://source.com  # Optional
source_type: manual
extracted_date: 2025-11-03
quality_score: 0.7  # Your assessment
confidence: 1.0  # Always 1.0 for manual entries
related_prompts:
  - "[[prompt-abc123|Related Prompt]]"
aliases:
  - alternative-name
---
```

## Backlinks

### View Backlinks

- Open any prompt
- Click "Open backlinks" in right sidebar
- See all notes that reference this prompt

### Use Backlinks to Track Usage

Each time you link a prompt in a daily note or project note, it appears in backlinks.

This shows:
- How often you use each prompt
- In what contexts
- What results you achieved

## Tags Panel

### Open Tags Panel

1. Settings → Core plugins → Enable "Tag pane"
2. Click tag icon in right sidebar
3. See all tags with counts

### Click Tags

Clicking a tag shows all notes with that tag.

Useful for:
- Finding all `#engineering` prompts
- Seeing `#high-confidence` prompts across categories
- Discovering `#with-examples` prompts

## Search Tips

### Basic Search

In search (Cmd/Ctrl + Shift + F):

```
Technical debt
```

Finds all prompts mentioning "technical debt".

### Advanced Search

```
category: engineering quality_score
```

Finds engineering prompts and shows quality scores.

### Regular Expressions

Enable regex in search settings:

```
/\[.+\]/
```

Finds all placeholders like `[DESCRIPTION]`.

## Plugins to Enhance

### Recommended Obsidian Plugins

1. **DataView** - Query prompts dynamically
   ```dataview
   TABLE quality_score, category
   FROM "library"
   WHERE quality_score >= 0.8
   SORT quality_score DESC
   ```

2. **Advanced Tables** - Format prompt metadata
3. **Templater** - More powerful templates
4. **Calendar** - Track daily prompt usage
5. **Graph Analysis** - Enhanced graph view

### Installing Plugins

1. Settings → Community plugins
2. Browse → Search for plugin
3. Install → Enable

## Maintenance

### Regenerate After Changes

After adding prompts manually or extracting new content:

```bash
# Regenerate MOCs
python ~/.claude/plugins/prompt-library-tools/skills/prompt-extraction/scripts/moc_generator.py ~/prompts

# Regenerate index
python ~/.claude/plugins/prompt-library-tools/skills/prompt-extraction/scripts/index_generator.py ~/prompts
```

Then refresh Obsidian (Cmd/Ctrl + R).

### Backup Vault

Obsidian vaults are just folders. Backup with:

```bash
cp -r ~/prompts ~/prompts-backup-$(date +%Y%m%d)
```

Or use git:

```bash
cd ~/prompts
git init
git add .
git commit -m "Backup prompts"
```

### Sync Across Devices

Options:
1. **Obsidian Sync** - Official paid sync service
2. **Git** - Free, requires technical setup
3. **iCloud/Dropbox** - Simple but can have conflicts
4. **Syncthing** - Free, open-source, peer-to-peer

## Tips and Tricks

### Quick Add Prompt

1. Cmd/Ctrl + N (new note)
2. Start typing prompt
3. Add to `library/` when done
4. Regenerate MOCs

### Prompt Variants

For prompt variations:

```markdown
# Original Prompt

[[prompt-abc123]]

## My Variant

[Your modifications...]

Changes:
- Added specific industry context
- Included company values
- Adjusted tone for executives
```

### Workspace Layouts

Save layouts for different uses:

1. **Browse Layout** - Left sidebar (file explorer), right sidebar (graph)
2. **Work Layout** - Center (prompt), right (backlinks)
3. **Review Layout** - Center (MOC), right (local graph)

### Hotkeys

Set custom hotkeys in Settings:
- Quick switch to `[[00-index]]`
- Toggle graph for current prompt only
- Insert prompt template

## Troubleshooting

### Prompts Not Showing

**Check:**
- File is in `library/` directory
- File has `.md` extension
- YAML frontmatter is valid
- Obsidian has indexed the vault (Cmd/Ctrl + R to refresh)

### Links Not Working

**Check:**
- Target prompt exists in `library/`
- ID matches exactly (case-sensitive)
- Using double square brackets: `[[prompt-id]]`

### Graph Not Showing Connections

**Check:**
- Related prompts use wiki-link format: `[[id|name]]`
- Prompts have `related_prompts` in frontmatter
- Graph filters aren't excluding prompts

### Search Not Finding Prompts

**Check:**
- Obsidian search is case-insensitive by default
- Search includes file content, not just titles
- Index is up to date (Cmd/Ctrl + R)

## Resources

- Obsidian Documentation: https://help.obsidian.md
- Obsidian Forum: https://forum.obsidian.md
- Plugin creator's vault README: `~/prompts/README.md`

---

*For questions about the prompt library system, see the plugin README.*
