#!/usr/bin/env python3
"""
Batch Prompt Extraction - Process entire directories of prompts or articles
"""

import argparse
from pathlib import Path
from typing import List
import json

from prompt_extractor import PromptExtractor
from config_loader import ConfigLoader


def extract_from_directory(
    directory: Path,
    vault_path: str,
    source_url: str = None,
    source_type: str = "local",
    recursive: bool = False,
    min_confidence: float = 0.15  # Lower threshold for known prompt files
) -> List:
    """
    Extract prompts from all markdown files in a directory

    Args:
        directory: Directory containing markdown files
        vault_path: Path to Obsidian vault
        source_url: Optional base URL for the source
        source_type: Type of source (substack, notion, etc.)
        recursive: Whether to search recursively
        min_confidence: Minimum confidence threshold

    Returns:
        List of all extracted prompt metadata
    """
    extractor = PromptExtractor(vault_path=vault_path)

    # Find all markdown files
    if recursive:
        markdown_files = list(directory.rglob("*.md"))
    else:
        markdown_files = list(directory.glob("*.md"))

    # Filter out README files
    markdown_files = [f for f in markdown_files if f.name.lower() not in ['readme.md', 'index.md']]

    print(f"📁 Found {len(markdown_files)} markdown files in {directory}")
    print(f"🎯 Using confidence threshold: {min_confidence}")
    print()

    all_results = []
    processed = 0
    skipped = 0

    for file_path in sorted(markdown_files):
        print(f"Processing: {file_path.name}...", end=" ")

        try:
            # Use detector with lower threshold for directory extraction
            from prompt_detector import PromptDetector
            detector = PromptDetector()

            content = file_path.read_text()
            prompts = detector.detect_prompts(content, min_confidence=min_confidence)

            if prompts:
                # Extract using the extractor
                results = extractor.extract_from_file(
                    file_path,
                    source_url=source_url,
                    source_type=source_type
                )

                all_results.extend(results)
                processed += 1
                print(f"✅ {len(results)} prompt(s)")
            else:
                skipped += 1
                print("⏭️  No prompts detected")

        except Exception as e:
            print(f"❌ Error: {e}")
            skipped += 1

    print()
    print(f"📊 Summary:")
    print(f"  Files processed: {processed}")
    print(f"  Files skipped: {skipped}")
    print(f"  Total prompts extracted: {len(all_results)}")

    if all_results:
        avg_quality = sum(r.quality_score for r in all_results) / len(all_results)
        avg_confidence = sum(r.confidence for r in all_results) / len(all_results)
        print(f"  Average quality: {avg_quality:.2f}")
        print(f"  Average confidence: {avg_confidence:.2f}")

    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Batch extract prompts from directories"
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing markdown files"
    )
    parser.add_argument(
        "--source-url",
        type=str,
        help="Base URL for the source (optional)"
    )
    parser.add_argument(
        "--source-type",
        type=str,
        default="local",
        choices=["substack", "notion", "patreon", "local"],
        help="Type of source"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search recursively in subdirectories"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.15,
        help="Minimum confidence threshold (default: 0.15)"
    )
    parser.add_argument('--vault-path', help='Override vault path from config')
    parser.add_argument('--import-path', help='Override import path from config')

    args = parser.parse_args()

    if not args.directory.exists():
        print(f"Error: Directory not found: {args.directory}")
        return 1

    if not args.directory.is_dir():
        print(f"Error: Not a directory: {args.directory}")
        return 1

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

    extract_from_directory(
        args.directory,
        vault_path=config.vault_path,
        source_url=args.source_url,
        source_type=args.source_type,
        recursive=args.recursive,
        min_confidence=args.min_confidence
    )

    return 0


if __name__ == '__main__':
    exit(main())
