#!/usr/bin/env python3
"""
Index Generator - Create prompts-index.json for LLM search
"""

import json
import yaml
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from config_loader import ConfigLoader


class IndexGenerator:
    """Generate LLM-searchable index of prompts"""

    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path).expanduser()
        self.library_path = self.vault_path / "library"

    def generate_index(self) -> Dict:
        """Generate complete search index"""
        prompts = []

        for file_path in sorted(self.library_path.glob("*.md")):
            try:
                prompt_data = self._extract_prompt_data(file_path)
                if prompt_data:
                    prompts.append(prompt_data)
            except Exception as e:
                print(f"⚠️  Warning: Could not index {file_path.name}: {e}")

        # Build index structure
        index = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "total_prompts": len(prompts),
            "prompts": prompts,
            "categories": self._build_category_index(prompts),
            "tags": self._build_tag_index(prompts),
            "sources": self._build_source_index(prompts)
        }

        return index

    def _extract_prompt_data(self, file_path: Path) -> Dict:
        """Extract searchable data from a prompt file"""
        content = file_path.read_text()

        # Extract YAML frontmatter
        if not content.startswith("---"):
            return None

        end_idx = content.find("---", 3)
        if end_idx <= 0:
            return None

        frontmatter_str = content[3:end_idx].strip()
        frontmatter = yaml.safe_load(frontmatter_str)

        # Extract prompt content (after second ---)
        prompt_start = content.find("## Prompt", end_idx)
        if prompt_start > 0:
            # Find next ## section or end of file
            next_section = content.find("\n## ", prompt_start + 10)
            if next_section > 0:
                prompt_content = content[prompt_start + 10:next_section].strip()
            else:
                # Find the footer (---)
                footer = content.find("\n---\n", prompt_start)
                if footer > 0:
                    prompt_content = content[prompt_start + 10:footer].strip()
                else:
                    prompt_content = content[prompt_start + 10:].strip()
        else:
            prompt_content = ""

        # Build searchable data
        return {
            "id": frontmatter.get('id'),
            "title": frontmatter.get('title'),
            "category": frontmatter.get('category'),
            "tags": frontmatter.get('tags', []),
            "source_url": frontmatter.get('source_url'),
            "source_type": frontmatter.get('source_type'),
            "quality_score": frontmatter.get('quality_score', 0.0),
            "confidence": frontmatter.get('confidence', 0.0),
            "extracted_date": frontmatter.get('extracted_date'),
            "file_path": str(file_path.relative_to(self.vault_path)),
            "content_preview": prompt_content[:500] if prompt_content else "",
            "content_length": len(prompt_content),
            "related_prompts": frontmatter.get('related_prompts', [])
        }

    def _build_category_index(self, prompts: List[Dict]) -> Dict:
        """Build category index for fast filtering"""
        categories = {}
        for prompt in prompts:
            category = prompt['category']
            if category not in categories:
                categories[category] = {
                    "count": 0,
                    "avg_quality": 0.0,
                    "prompt_ids": []
                }

            categories[category]["count"] += 1
            categories[category]["prompt_ids"].append(prompt['id'])

        # Calculate average quality for each category
        for category, data in categories.items():
            cat_prompts = [p for p in prompts if p['category'] == category]
            data["avg_quality"] = sum(p['quality_score'] for p in cat_prompts) / len(cat_prompts)

        return categories

    def _build_tag_index(self, prompts: List[Dict]) -> Dict:
        """Build tag index for fast filtering"""
        tags = {}
        for prompt in prompts:
            for tag in prompt['tags']:
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(prompt['id'])

        return {tag: sorted(ids) for tag, ids in sorted(tags.items())}

    def _build_source_index(self, prompts: List[Dict]) -> Dict:
        """Build source index for fast filtering"""
        sources = {}
        for prompt in prompts:
            source_key = f"{prompt['source_type']}:{prompt['source_url'] or 'local'}"
            if source_key not in sources:
                sources[source_key] = []
            sources[source_key].append(prompt['id'])

        return sources

    def save_index(self, output_path: Path = None):
        """Generate and save index to JSON file"""
        if output_path is None:
            output_path = self.vault_path / "prompts-index.json"

        print("🔍 Generating search index...")
        index = self.generate_index()

        print(f"📊 Index Statistics:")
        print(f"  Total prompts: {index['total_prompts']}")
        print(f"  Categories: {len(index['categories'])}")
        print(f"  Tags: {len(index['tags'])}")
        print(f"  Sources: {len(index['sources'])}")
        print()

        # Save to file
        with open(output_path, 'w') as f:
            json.dump(index, f, indent=2, sort_keys=True)

        print(f"✅ Index saved to: {output_path}")

        return index


def main():
    """Generate index"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate search index for prompt library'
    )
    parser.add_argument('--vault-path', help='Override vault path from config')
    parser.add_argument('--import-path', help='Override import path from config')
    parser.add_argument('--min-confidence', type=float, help='Override min confidence from config')
    parser.add_argument('--output', help='Override output path for index file')

    args = parser.parse_args()

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

    generator = IndexGenerator(config.vault_path)

    output_path = Path(args.output) if args.output else None
    generator.save_index(output_path)


if __name__ == '__main__':
    main()
