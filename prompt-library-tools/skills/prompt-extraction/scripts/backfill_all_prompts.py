#!/usr/bin/env python3
"""
Backfill All Prompts - Process all newsletters in output/ directory
"""

import json
from pathlib import Path
import subprocess
import sys
from config_loader import ConfigLoader


def find_prompt_directories(output_dir: Path) -> list:
    """Find all directories containing prompts subdirectories"""
    prompt_dirs = []

    for newsletter_dir in output_dir.iterdir():
        if not newsletter_dir.is_dir():
            continue

        prompts_dir = newsletter_dir / "prompts"
        if prompts_dir.exists() and prompts_dir.is_dir():
            # Check if there are markdown files
            md_files = list(prompts_dir.glob("*.md"))
            if md_files:
                prompt_dirs.append((newsletter_dir, prompts_dir))

    return prompt_dirs


def get_source_url(newsletter_dir: Path) -> tuple:
    """Extract source URL and type from newsletter metadata"""
    metadata_file = newsletter_dir / "metadata.json"

    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
                source_url = metadata.get('source_url')
                source_type = metadata.get('source_type', 'substack')
                return source_url, source_type
        except:
            pass

    # Try to extract from README
    readme_file = newsletter_dir / "README.md"
    if readme_file.exists():
        content = readme_file.read_text()
        # Look for source URL in markdown
        import re
        url_match = re.search(r'https://[^\s\)]+', content)
        if url_match:
            url = url_match.group(0)
            if 'substack' in url:
                return url, 'substack'
            elif 'notion' in url:
                return url, 'notion'
            elif 'patreon' in url:
                return url, 'patreon'
            return url, 'local'

    return None, 'local'


def run_batch_extraction(prompts_dir: Path, vault_path: str, source_url: str, source_type: str):
    """Run batch extraction on a directory"""
    cmd = [
        "python",
        "batch_extract_prompts.py",
        str(prompts_dir),
        "--source-type", source_type,
        "--min-confidence", "0.15",
        "--vault-path", vault_path
    ]

    if source_url:
        cmd.extend(["--source-url", source_url])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Backfill all prompts from newsletters")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    parser.add_argument('--vault-path', help='Override vault path from config')
    parser.add_argument('--import-path', help='Override import path from config')
    args = parser.parse_args()

    # Build CLI overrides
    cli_overrides = {}
    if args.vault_path:
        cli_overrides['vault_path'] = args.vault_path
    if args.import_path:
        cli_overrides['import_path'] = args.import_path

    # Load config
    config = ConfigLoader.load(cli_overrides)

    output_dir = Path("output")

    if not output_dir.exists():
        print("❌ Error: output/ directory not found")
        return 1

    print("🔍 Scanning for newsletter prompts directories...")
    prompt_dirs = find_prompt_directories(output_dir)
    print(f"Found {len(prompt_dirs)} newsletters with prompts\n")

    if not prompt_dirs:
        print("No prompt directories found!")
        return 0

    # List all directories that will be processed
    print("📋 Directories to process:")
    for newsletter_dir, prompts_dir in prompt_dirs:
        md_count = len(list(prompts_dir.glob("*.md")))
        source_url, source_type = get_source_url(newsletter_dir)
        print(f"  - {newsletter_dir.name} ({md_count} files) [{source_type}]")
    print()

    # Ask for confirmation unless --yes flag is provided
    if not args.yes:
        response = input(f"Process all {len(prompt_dirs)} directories? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled")
            return 0

    print("\n🚀 Starting batch extraction...\n")

    total_processed = 0
    total_extracted = 0
    failed = []

    for i, (newsletter_dir, prompts_dir) in enumerate(prompt_dirs, 1):
        print(f"[{i}/{len(prompt_dirs)}] Processing: {newsletter_dir.name}")

        source_url, source_type = get_source_url(newsletter_dir)
        success, stdout, stderr = run_batch_extraction(prompts_dir, config.vault_path, source_url, source_type)

        if success:
            # Parse output to get count
            if "Total prompts extracted:" in stdout:
                import re
                match = re.search(r'Total prompts extracted: (\d+)', stdout)
                if match:
                    count = int(match.group(1))
                    total_extracted += count
                    print(f"  ✅ Extracted {count} prompts")
            else:
                print(f"  ✅ Completed")
            total_processed += 1
        else:
            print(f"  ❌ Failed: {stderr[:100]}")
            failed.append(newsletter_dir.name)

        print()

    print("=" * 60)
    print(f"📊 Backfill Summary:")
    print(f"  Directories processed: {total_processed}/{len(prompt_dirs)}")
    print(f"  Total prompts extracted: {total_extracted}")
    if failed:
        print(f"  Failed: {len(failed)} ({', '.join(failed)})")
    print()

    # Regenerate MOCs and index
    print("📚 Regenerating Maps of Content...")
    subprocess.run(["python", "moc_generator.py", "--vault-path", config.vault_path])
    print()

    print("🔍 Regenerating search index...")
    subprocess.run(["python", "index_generator.py", "--vault-path", config.vault_path])
    print()

    print("✨ Backfill complete!")

    return 0


if __name__ == '__main__':
    exit(main())
