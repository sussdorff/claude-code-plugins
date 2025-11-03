#!/usr/bin/env python3
"""
Configuration Loader - Hierarchical configuration management for prompt-library-tools

Configuration priority (highest to lowest):
1. CLI arguments
2. Project-local config (.prompt-library-config.json in current directory)
3. Global config (~/.prompt-library-config.json)
4. Default values
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Config:
    """Configuration for prompt-library-tools"""
    vault_path: str = "~/prompts"
    import_path: str = "~/Downloads/newsletters"
    min_confidence: float = 0.15
    templates: Optional[Dict[str, str]] = None
    extraction: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Set default values for optional fields"""
        if self.templates is None:
            self.templates = {
                "prompt_template": "assets/templates/prompt-template.md",
                "daily_note_template": "assets/templates/daily-note-with-prompts.md"
            }
        if self.extraction is None:
            self.extraction = {
                "auto_tag": True,
                "default_tags": ["prompt", "imported"],
                "preserve_markdown": True
            }

    def expand_paths(self) -> 'Config':
        """Expand ~ and relative paths to absolute paths"""
        self.vault_path = str(Path(self.vault_path).expanduser().resolve())
        self.import_path = str(Path(self.import_path).expanduser().resolve())

        # Expand template paths if they're relative
        if self.templates:
            for key, path in self.templates.items():
                self.templates[key] = str(Path(path).expanduser())

        return self

    def merge(self, other: Dict[str, Any]) -> 'Config':
        """Merge another config dict into this config, overriding values"""
        config_dict = asdict(self)

        for key, value in other.items():
            if key in config_dict and value is not None:
                # For nested dicts, merge instead of replace
                if isinstance(config_dict[key], dict) and isinstance(value, dict):
                    config_dict[key].update(value)
                else:
                    config_dict[key] = value

        return Config(**config_dict)


class ConfigLoader:
    """Load configuration from multiple sources with priority"""

    PROJECT_CONFIG_NAME = ".prompt-library-config.json"
    GLOBAL_CONFIG_NAME = ".prompt-library-config.json"

    @staticmethod
    def find_config_file() -> Optional[Path]:
        """
        Find config file in order of priority:
        1. Project-local (.prompt-library-config.json in current directory)
        2. Global (~/.prompt-library-config.json)

        Returns:
            Path to config file, or None if not found
        """
        # Check project-local config
        project_config = Path.cwd() / ConfigLoader.PROJECT_CONFIG_NAME
        if project_config.exists():
            return project_config

        # Check global config
        global_config = Path.home() / ConfigLoader.GLOBAL_CONFIG_NAME
        if global_config.exists():
            return global_config

        return None

    @staticmethod
    def load_config_file(config_path: Path) -> Dict[str, Any]:
        """
        Load and parse a JSON config file

        Args:
            config_path: Path to config file

        Returns:
            Config dictionary

        Raises:
            ValueError: If config file is invalid JSON
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Remove JSON schema field if present (not part of config)
            config.pop('$schema', None)
            config.pop('description', None)

            return config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {config_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading config file {config_path}: {e}")

    @staticmethod
    def load(cli_overrides: Optional[Dict[str, Any]] = None) -> Config:
        """
        Load configuration from all sources with proper priority

        Args:
            cli_overrides: Dictionary of CLI argument overrides

        Returns:
            Merged configuration with all values set
        """
        # Start with defaults
        config = Config()

        # Load from config file (if exists)
        config_file = ConfigLoader.find_config_file()
        if config_file:
            try:
                file_config = ConfigLoader.load_config_file(config_file)
                config = config.merge(file_config)
                print(f"📋 Loaded config from: {config_file}", file=sys.stderr)
            except ValueError as e:
                print(f"⚠️  Warning: {e}", file=sys.stderr)
                print(f"⚠️  Using default configuration", file=sys.stderr)

        # Apply CLI overrides (highest priority)
        if cli_overrides:
            config = config.merge(cli_overrides)

        # Expand paths
        config = config.expand_paths()

        return config

    @staticmethod
    def validate_config(config_path: Path) -> bool:
        """
        Validate a config file

        Args:
            config_path: Path to config file to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            config_dict = ConfigLoader.load_config_file(config_path)
            config = Config(**config_dict)

            print(f"✅ Config file is valid: {config_path}")
            print(f"\nConfiguration:")
            print(f"  vault_path: {config.vault_path}")
            print(f"  import_path: {config.import_path}")
            print(f"  min_confidence: {config.min_confidence}")

            return True
        except Exception as e:
            print(f"❌ Config file is invalid: {e}")
            return False


def main():
    """Test config loader or validate a config file"""
    import argparse

    parser = argparse.ArgumentParser(description="Config loader utility")
    parser.add_argument('--validate', metavar='CONFIG_FILE',
                        help='Validate a config file')
    parser.add_argument('--show', action='store_true',
                        help='Show current configuration')
    parser.add_argument('--vault-path', help='Override vault path')
    parser.add_argument('--import-path', help='Override import path')
    parser.add_argument('--min-confidence', type=float, help='Override min confidence')

    args = parser.parse_args()

    if args.validate:
        config_path = Path(args.validate).expanduser()
        if not config_path.exists():
            print(f"❌ Config file not found: {config_path}")
            sys.exit(1)

        valid = ConfigLoader.validate_config(config_path)
        sys.exit(0 if valid else 1)

    if args.show:
        # Build CLI overrides
        cli_overrides = {}
        if args.vault_path:
            cli_overrides['vault_path'] = args.vault_path
        if args.import_path:
            cli_overrides['import_path'] = args.import_path
        if args.min_confidence is not None:
            cli_overrides['min_confidence'] = args.min_confidence

        # Load config
        config = ConfigLoader.load(cli_overrides)

        print("\n📋 Current Configuration:")
        print(f"  vault_path: {config.vault_path}")
        print(f"  import_path: {config.import_path}")
        print(f"  min_confidence: {config.min_confidence}")
        print(f"\nTemplates:")
        for key, value in config.templates.items():
            print(f"  {key}: {value}")
        print(f"\nExtraction settings:")
        for key, value in config.extraction.items():
            print(f"  {key}: {value}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
