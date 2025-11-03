# Configuration Guide

## Configuration File Locations

The prompt-library-tools plugin uses a hierarchical configuration system with the following priority (highest to lowest):

1. **CLI Arguments** - Passed directly to scripts
2. **Project Config** - `.prompt-library-config.json` in current working directory
3. **Global Config** - `~/.prompt-library-config.json` in home directory
4. **Default Values** - Built-in defaults

## Setup Instructions

### First-Time Setup

1. Copy the template to your home directory:
   ```bash
   cp assets/config-template.json ~/.prompt-library-config.json
   ```

2. Edit `~/.prompt-library-config.json` with your paths:
   ```json
   {
     "vault_path": "~/my-obsidian-vault",
     "import_path": "~/Downloads/newsletters",
     "min_confidence": 0.15
   }
   ```

### Project-Specific Configuration

For project-specific settings, create `.prompt-library-config.json` in your project directory:

```bash
cp assets/config-template.json .prompt-library-config.json
# Edit with project-specific paths
```

## Configuration Options

### Required Settings

- **vault_path** (string): Path to your Obsidian vault
  - Example: `"~/prompts"` or `"/Users/username/Documents/Obsidian/MyVault"`
  - Default: `"~/prompts"`

- **import_path** (string): Path to source files for import
  - Example: `"~/Downloads/newsletters"`
  - Default: `"~/Downloads/newsletters"`

### Optional Settings

- **min_confidence** (float): Minimum confidence threshold for prompt detection
  - Range: 0.0 to 1.0
  - Default: `0.15`

- **templates** (object): Template file paths
  - `prompt_template`: Path to prompt template
  - `daily_note_template`: Path to daily note template

- **extraction** (object): Extraction behavior settings
  - `auto_tag` (boolean): Automatically tag extracted prompts
  - `default_tags` (array): Default tags to apply
  - `preserve_markdown` (boolean): Preserve original markdown formatting

## CLI Override Examples

Override config values from command line:

```bash
# Override vault path
python scripts/prompt_extractor.py --vault-path ~/different-vault

# Override import path
python scripts/moc_generator.py --import-path ~/custom-source

# Override multiple values
python scripts/prompt_extractor.py \
  --vault-path ~/vault \
  --import-path ~/source \
  --min-confidence 0.2
```

## Troubleshooting

### Config Not Found

If no config file is found, the scripts will use default values:
- `vault_path`: `~/prompts`
- `import_path`: `~/Downloads/newsletters`

### Path Expansion

- Tilde (`~`) will be expanded to your home directory
- Relative paths are resolved from the working directory
- Absolute paths are used as-is

### Validation

Run validation to check your config:
```bash
python scripts/config_loader.py --validate ~/.prompt-library-config.json
```
