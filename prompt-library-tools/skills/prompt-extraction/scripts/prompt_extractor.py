#!/usr/bin/env python3
"""
Prompt Extractor - Generate Obsidian-compatible markdown files from detected prompts
"""

import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import hashlib

from prompt_detector import PromptDetector, PromptMatch
from config_loader import ConfigLoader


@dataclass
class PromptMetadata:
    """Metadata for an extracted prompt"""
    id: str
    title: str
    category: str
    tags: List[str]
    source_url: Optional[str]
    source_type: str  # 'substack', 'notion', 'patreon', 'local'
    source_file: str
    extracted_date: str
    quality_score: float
    confidence: float
    related_prompts: List[str]
    aliases: List[str]
    start_line: int
    end_line: int


class QualityScorer:
    """Score prompt quality based on completeness and structure"""

    @staticmethod
    def score_prompt(prompt: PromptMatch) -> float:
        """
        Calculate quality score (0.0-1.0) based on prompt characteristics

        Criteria:
        - Completeness: Has context, task, output specs (30%)
        - Structure: Well-organized sections (25%)
        - Clarity: Uses placeholders, examples (20%)
        - Length: Substantial content (15%)
        - Specificity: Detailed instructions (10%)
        """
        score = 0.0
        content = prompt.content.lower()

        # Completeness (30 points)
        completeness = 0.0
        if re.search(r'(context|background|situation)', content):
            completeness += 0.10
        if re.search(r'(task|objective|goal|purpose)', content):
            completeness += 0.10
        if re.search(r'(output|deliverable|result|format)', content):
            completeness += 0.10
        score += completeness

        # Structure (25 points)
        structure = 0.0
        # Has multiple sections
        section_count = len(re.findall(r'#{2,3}\s+\w+', prompt.content))
        structure += min(0.15, section_count * 0.03)
        # Has lists
        list_count = len(re.findall(r'^\s*[-*]\s+', prompt.content, re.MULTILINE))
        structure += min(0.10, list_count * 0.01)
        score += structure

        # Clarity (20 points)
        clarity = 0.0
        # Uses placeholders
        placeholder_count = len(re.findall(r'\[[A-Z_\s]+\]|\{[a-z_]+\}', prompt.content))
        clarity += min(0.10, placeholder_count * 0.02)
        # Has examples
        if re.search(r'(example|sample|demonstration|for instance)', content):
            clarity += 0.10
        score += clarity

        # Length (15 points)
        length_score = 0.0
        char_count = len(prompt.content)
        if char_count >= 2000:
            length_score = 0.15
        elif char_count >= 1000:
            length_score = 0.10
        elif char_count >= 500:
            length_score = 0.05
        score += length_score

        # Specificity (10 points)
        specificity = 0.0
        # Has constraints
        if re.search(r'(must|should|never|always|do not|avoid)', content):
            specificity += 0.05
        # Has success criteria
        if re.search(r'(success|criteria|acceptance|quality)', content):
            specificity += 0.05
        score += specificity

        return min(1.0, score)


class PromptExtractor:
    """Extract prompts and generate Obsidian-compatible files"""

    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path).expanduser()
        self.library_path = self.vault_path / "library"
        self.detector = PromptDetector()
        self.quality_scorer = QualityScorer()

        # Ensure directories exist
        self.library_path.mkdir(parents=True, exist_ok=True)

    def extract_from_file(
        self,
        file_path: Path,
        source_url: Optional[str] = None,
        source_type: str = "local"
    ) -> List[PromptMetadata]:
        """
        Extract prompts from a markdown file

        Args:
            file_path: Path to markdown file
            source_url: Original URL if from web
            source_type: Type of source (substack, notion, patreon, local)

        Returns:
            List of extracted prompt metadata
        """
        content = file_path.read_text()
        prompts = self.detector.detect_prompts(content)

        extracted = []
        for prompt in prompts:
            # Calculate quality score
            quality = self.quality_scorer.score_prompt(prompt)

            # Infer category from matched patterns and content
            category = self._infer_category(prompt)

            # Generate tags
            tags = self._generate_tags(prompt, category)

            # Create metadata
            metadata = PromptMetadata(
                id=prompt.id,
                title=prompt.title or "Untitled Prompt",
                category=category,
                tags=tags,
                source_url=source_url,
                source_type=source_type,
                source_file=str(file_path),
                extracted_date=datetime.now().strftime("%Y-%m-%d"),
                quality_score=quality,
                confidence=prompt.confidence,
                related_prompts=[],  # Will be populated later
                aliases=self._generate_aliases(prompt.title or "Untitled"),
                start_line=prompt.start_line,
                end_line=prompt.end_line
            )

            # Write to vault
            self._write_prompt_file(prompt, metadata)
            extracted.append(metadata)

        return extracted

    def _infer_category(self, prompt: PromptMatch) -> str:
        """Infer category from prompt content"""
        content = prompt.content.lower()

        categories = {
            'engineering': [
                'software', 'code', 'programming', 'development', 'technical',
                'architecture', 'api', 'database', 'algorithm', 'debug'
            ],
            'product': [
                'product', 'feature', 'roadmap', 'specification', 'requirements',
                'user story', 'backlog', 'sprint', 'agile'
            ],
            'marketing': [
                'marketing', 'campaign', 'audience', 'brand', 'content marketing',
                'social media', 'seo', 'advertising', 'copywriting'
            ],
            'sales': [
                'sales', 'pitch', 'proposal', 'deal', 'prospect', 'customer',
                'revenue', 'quota', 'pipeline'
            ],
            'operations': [
                'operations', 'process', 'workflow', 'efficiency', 'automation',
                'logistics', 'supply chain', 'infrastructure'
            ],
            'strategy': [
                'strategy', 'planning', 'vision', 'goals', 'objectives',
                'competitive', 'market analysis', 'business model'
            ],
            'analytics': [
                'analytics', 'data', 'metrics', 'kpi', 'dashboard', 'reporting',
                'analysis', 'insights', 'statistics'
            ],
            'writing': [
                'writing', 'content', 'blog', 'article', 'documentation',
                'email', 'communication', 'editing'
            ]
        }

        # Count matches for each category
        scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > 0:
                scores[category] = score

        # Return category with highest score, or 'general' if none
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return 'general'

    def _generate_tags(self, prompt: PromptMatch, category: str) -> List[str]:
        """Generate tags for the prompt"""
        tags = [category]

        # Add pattern-based tags
        pattern_tags = {
            'structured_sections': 'structured',
            'role_assignment': 'role-based',
            'multi_step': 'multi-step',
            'examples': 'with-examples'
        }

        for pattern in prompt.matched_patterns:
            if pattern in pattern_tags:
                tags.append(pattern_tags[pattern])

        # Add quality-based tags
        if prompt.confidence >= 0.8:
            tags.append('high-confidence')

        return tags

    def _generate_aliases(self, title: str) -> List[str]:
        """Generate aliases from title"""
        # Create slug version
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)

        # Create short version (first 3-4 words)
        words = title.split()[:4]
        short = ' '.join(words)

        aliases = []
        if slug != title.lower():
            aliases.append(slug)
        if short != title and len(words) > 4:
            aliases.append(short)

        return aliases[:3]  # Limit to 3 aliases

    def _write_prompt_file(self, prompt: PromptMatch, metadata: PromptMetadata):
        """Write prompt to Obsidian-compatible markdown file"""
        file_path = self.library_path / f"{metadata.id}.md"

        # Prepare frontmatter
        frontmatter = {
            'id': metadata.id,
            'title': metadata.title,
            'category': metadata.category,
            'tags': metadata.tags,
            'source_url': metadata.source_url,
            'source_type': metadata.source_type,
            'extracted_date': metadata.extracted_date,
            'quality_score': round(metadata.quality_score, 2),
            'confidence': round(metadata.confidence, 2),
            'related_prompts': metadata.related_prompts,
            'aliases': metadata.aliases
        }

        # Build markdown content
        lines = [
            '---',
            yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip(),
            '---',
            '',
            f'# {metadata.title}',
            ''
        ]

        # Add source info
        if metadata.source_url:
            lines.append(f'**Source**: [{metadata.source_type.title()}]({metadata.source_url})')
        else:
            lines.append(f'**Source**: Local file - `{Path(metadata.source_file).name}`')

        lines.extend([
            f'**Category**: #{metadata.category}',
            '',
            '## Prompt',
            '',
            prompt.content.strip(),
            ''
        ])

        # Add related prompts section (placeholder for now)
        if metadata.related_prompts:
            lines.extend([
                '## Related Prompts',
                ''
            ])
            for related in metadata.related_prompts:
                lines.append(f'- {related}')
            lines.append('')

        # Add metadata footer
        lines.extend([
            '---',
            f'*Extracted on {metadata.extracted_date} | '
            f'Confidence: {metadata.confidence:.2f} | '
            f'Quality: {metadata.quality_score:.2f}*'
        ])

        # Write file
        file_path.write_text('\n'.join(lines))

        print(f"✅ Extracted: {metadata.id} - {metadata.title[:50]}")


def main():
    """Extract prompts from markdown files"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract prompts from markdown files and save to Obsidian vault'
    )
    parser.add_argument('markdown_file', help='Path to markdown file to extract from')
    parser.add_argument('source_url', nargs='?', help='Source URL (optional)')
    parser.add_argument('--vault-path', help='Override vault path from config')
    parser.add_argument('--import-path', help='Override import path from config')
    parser.add_argument('--min-confidence', type=float, help='Override min confidence from config')
    parser.add_argument('--source-type', default=None, help='Source type (substack, notion, patreon, local)')

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

    # Determine source type
    source_type = args.source_type
    if not source_type and args.source_url:
        if "substack" in args.source_url:
            source_type = "substack"
        elif "notion" in args.source_url:
            source_type = "notion"
        elif "patreon" in args.source_url:
            source_type = "patreon"
        else:
            source_type = "web"
    elif not source_type:
        source_type = "local"

    # Extract prompts
    file_path = Path(args.markdown_file)
    extractor = PromptExtractor(vault_path=config.vault_path)
    results = extractor.extract_from_file(
        file_path,
        source_url=args.source_url,
        source_type=source_type
    )

    print(f"\n📊 Summary:")
    print(f"  Total prompts extracted: {len(results)}")
    if results:
        avg_quality = sum(r.quality_score for r in results) / len(results)
        avg_confidence = sum(r.confidence for r in results) / len(results)
        print(f"  Average quality: {avg_quality:.2f}")
        print(f"  Average confidence: {avg_confidence:.2f}")


if __name__ == '__main__':
    main()
