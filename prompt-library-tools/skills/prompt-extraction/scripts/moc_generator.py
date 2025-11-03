#!/usr/bin/env python3
"""
MOC Generator - Create Maps of Content for Obsidian vault
"""

import yaml
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
from config_loader import ConfigLoader


@dataclass
class PromptInfo:
    """Information about a prompt from its frontmatter"""
    id: str
    title: str
    category: str
    tags: List[str]
    source_url: str
    source_type: str
    quality_score: float
    confidence: float
    file_path: Path


class MOCGenerator:
    """Generate Maps of Content for the prompt library"""

    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path).expanduser()
        self.library_path = self.vault_path / "library"
        self.mocs_path = self.vault_path / "mocs"

        # Ensure mocs directory exists
        self.mocs_path.mkdir(parents=True, exist_ok=True)

    def scan_prompts(self) -> List[PromptInfo]:
        """Scan library and extract metadata from all prompts"""
        prompts = []

        for file_path in self.library_path.glob("*.md"):
            try:
                content = file_path.read_text()

                # Extract YAML frontmatter
                if content.startswith("---"):
                    # Find end of frontmatter
                    end_idx = content.find("---", 3)
                    if end_idx > 0:
                        frontmatter_str = content[3:end_idx].strip()
                        frontmatter = yaml.safe_load(frontmatter_str)

                        prompts.append(PromptInfo(
                            id=frontmatter.get('id', file_path.stem),
                            title=frontmatter.get('title', 'Untitled'),
                            category=frontmatter.get('category', 'general'),
                            tags=frontmatter.get('tags', []),
                            source_url=frontmatter.get('source_url'),
                            source_type=frontmatter.get('source_type', 'local'),
                            quality_score=frontmatter.get('quality_score', 0.0),
                            confidence=frontmatter.get('confidence', 0.0),
                            file_path=file_path
                        ))
            except Exception as e:
                print(f"⚠️  Warning: Could not parse {file_path.name}: {e}")

        return prompts

    def generate_category_mocs(self, prompts: List[PromptInfo]):
        """Generate a MOC file for each category"""
        # Group prompts by category
        by_category = defaultdict(list)
        for prompt in prompts:
            by_category[prompt.category].append(prompt)

        # Generate MOC for each category
        for category, category_prompts in sorted(by_category.items()):
            self._generate_category_moc(category, category_prompts)

    def _generate_category_moc(self, category: str, prompts: List[PromptInfo]):
        """Generate a single category MOC file"""
        file_path = self.mocs_path / f"{category}.md"

        # Sort prompts by quality score (descending)
        prompts_sorted = sorted(prompts, key=lambda p: p.quality_score, reverse=True)

        # Calculate stats
        total = len(prompts)
        avg_quality = sum(p.quality_score for p in prompts) / total if total > 0 else 0
        high_quality = sum(1 for p in prompts if p.quality_score >= 0.8)

        lines = [
            f"# {category.title()} Prompts",
            "",
            f"**Total Prompts**: {total} | **Avg Quality**: {avg_quality:.2f} | **High Quality (≥0.8)**: {high_quality}",
            "",
            "## Overview",
            "",
            f"This collection contains {total} prompts related to {category}.",
            "",
            "## Prompts",
            ""
        ]

        # Group by quality tiers
        tiers = {
            "Excellent (≥0.8)": [p for p in prompts_sorted if p.quality_score >= 0.8],
            "Good (0.6-0.8)": [p for p in prompts_sorted if 0.6 <= p.quality_score < 0.8],
            "Standard (<0.6)": [p for p in prompts_sorted if p.quality_score < 0.6]
        }

        for tier_name, tier_prompts in tiers.items():
            if tier_prompts:
                lines.extend([
                    f"### {tier_name}",
                    ""
                ])

                for prompt in tier_prompts:
                    # Create wiki-link with display text
                    title_display = prompt.title[:60] + "..." if len(prompt.title) > 60 else prompt.title
                    lines.append(f"- [[{prompt.id}|{title_display}]] (Q: {prompt.quality_score:.2f})")

                lines.append("")

        # Add tags section
        all_tags = set()
        for prompt in prompts:
            all_tags.update(prompt.tags)

        if all_tags:
            lines.extend([
                "## Common Tags",
                ""
            ])
            for tag in sorted(all_tags):
                tag_count = sum(1 for p in prompts if tag in p.tags)
                lines.append(f"- #{tag} ({tag_count})")
            lines.append("")

        # Add footer
        lines.extend([
            "---",
            f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*"
        ])

        file_path.write_text('\n'.join(lines))
        print(f"✅ Generated MOC: {category}.md ({total} prompts)")

    def generate_main_index(self, prompts: List[PromptInfo]):
        """Generate the main index (00-index.md)"""
        file_path = self.mocs_path / "00-index.md"

        # Calculate overall stats
        total = len(prompts)
        categories = set(p.category for p in prompts)
        avg_quality = sum(p.quality_score for p in prompts) / total if total > 0 else 0

        # Group by category for summary
        by_category = defaultdict(list)
        for prompt in prompts:
            by_category[prompt.category].append(prompt)

        lines = [
            "# Prompt Library Index",
            "",
            f"**Total Prompts**: {total} | **Categories**: {len(categories)} | **Avg Quality**: {avg_quality:.2f}",
            "",
            "## Categories",
            ""
        ]

        # List categories with counts
        for category in sorted(categories):
            count = len(by_category[category])
            avg_cat_quality = sum(p.quality_score for p in by_category[category]) / count
            lines.append(f"- [[{category}|{category.title()}]] ({count} prompts, avg quality: {avg_cat_quality:.2f})")

        lines.extend([
            "",
            "## Other Maps",
            "",
            "- [[sources|Sources]] - Prompts organized by source",
            "",
            "## Quality Distribution",
            ""
        ])

        # Quality distribution
        excellent = sum(1 for p in prompts if p.quality_score >= 0.8)
        good = sum(1 for p in prompts if 0.6 <= p.quality_score < 0.8)
        standard = sum(1 for p in prompts if p.quality_score < 0.6)

        lines.extend([
            f"- Excellent (≥0.8): {excellent}",
            f"- Good (0.6-0.8): {good}",
            f"- Standard (<0.6): {standard}",
            "",
            "## Recent Additions",
            ""
        ])

        # Sort by file modification time (most recent first)
        recent = sorted(prompts, key=lambda p: p.file_path.stat().st_mtime, reverse=True)[:10]
        for prompt in recent:
            title_display = prompt.title[:60] + "..." if len(prompt.title) > 60 else prompt.title
            lines.append(f"- [[{prompt.id}|{title_display}]] ({prompt.category})")

        lines.extend([
            "",
            "---",
            f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
        ])

        file_path.write_text('\n'.join(lines))
        print(f"✅ Generated main index: 00-index.md")

    def generate_sources_moc(self, prompts: List[PromptInfo]):
        """Generate sources MOC"""
        file_path = self.mocs_path / "sources.md"

        # Group by source type and URL
        by_source = defaultdict(list)
        for prompt in prompts:
            key = (prompt.source_type, prompt.source_url or "local")
            by_source[key].append(prompt)

        lines = [
            "# Prompt Sources",
            "",
            f"**Total Sources**: {len(by_source)}",
            "",
            "## By Source Type",
            ""
        ]

        # Group by source type
        by_type = defaultdict(list)
        for (source_type, source_url), prompts_list in by_source.items():
            by_type[source_type].append((source_url, prompts_list))

        for source_type in sorted(by_type.keys()):
            lines.extend([
                f"### {source_type.title()}",
                ""
            ])

            for source_url, source_prompts in sorted(by_type[source_type], key=lambda x: len(x[1]), reverse=True):
                count = len(source_prompts)
                if source_url and source_url != "local":
                    # Extract a readable name from URL
                    url_parts = source_url.split('/')
                    source_name = url_parts[-1] or url_parts[-2] or "Unknown"
                    lines.append(f"#### [{source_name}]({source_url})")
                else:
                    lines.append(f"#### Local Files")

                lines.append(f"")
                lines.append(f"**Prompts**: {count}")
                lines.append(f"")

                for prompt in sorted(source_prompts, key=lambda p: p.quality_score, reverse=True)[:5]:
                    title_display = prompt.title[:50] + "..." if len(prompt.title) > 50 else prompt.title
                    lines.append(f"- [[{prompt.id}|{title_display}]] (Q: {prompt.quality_score:.2f})")

                if len(source_prompts) > 5:
                    lines.append(f"- *(and {len(source_prompts) - 5} more...)*")

                lines.append("")

        lines.extend([
            "---",
            f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*"
        ])

        file_path.write_text('\n'.join(lines))
        print(f"✅ Generated sources MOC: sources.md")

    def generate_all(self):
        """Generate all MOCs"""
        print("📚 Scanning prompt library...")
        prompts = self.scan_prompts()
        print(f"Found {len(prompts)} prompts")
        print()

        print("📝 Generating MOCs...")
        self.generate_category_mocs(prompts)
        self.generate_main_index(prompts)
        self.generate_sources_moc(prompts)

        print()
        print("✨ MOC generation complete!")


def main():
    """Generate all MOCs"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate Maps of Content (MOCs) for prompt library'
    )
    parser.add_argument('--vault-path', help='Override vault path from config')
    parser.add_argument('--import-path', help='Override import path from config')
    parser.add_argument('--min-confidence', type=float, help='Override min confidence from config')

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

    generator = MOCGenerator(config.vault_path)
    generator.generate_all()


if __name__ == '__main__':
    main()
