#!/usr/bin/env python3
"""
Prompt Detector - Extract prompts from markdown content
Detects prompts using pattern matching and generates Obsidian-compatible output
"""

import re
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import json


@dataclass
class DetectionPattern:
    """A pattern used to detect prompts"""
    name: str
    pattern: re.Pattern
    weight: float  # Contribution to confidence score (0.0-1.0)
    description: str


@dataclass
class PromptMatch:
    """A detected prompt with metadata"""
    content: str
    start_line: int
    end_line: int
    confidence: float
    matched_patterns: List[str]
    title: Optional[str] = None
    category: Optional[str] = None

    def __post_init__(self):
        """Generate ID from content hash"""
        content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:8]
        self.id = f"prompt-{content_hash}"


class PromptDetector:
    """Detects and extracts prompts from markdown content"""

    def __init__(self):
        self.patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> List[DetectionPattern]:
        """Initialize all detection patterns"""
        return [
            # Structural markers (high confidence)
            DetectionPattern(
                name="structured_sections",
                pattern=re.compile(
                    r'#{2,3}\s+(TASK|OBJECTIVE|INPUT|OUTPUT|CONTEXT|INSTRUCTIONS?|PROTOCOL|REQUIREMENTS?|DELIVERABLES?)',
                    re.IGNORECASE | re.MULTILINE
                ),
                weight=0.20,
                description="Section headers indicating structured prompt"
            ),

            # Role assignment (high confidence)
            DetectionPattern(
                name="role_assignment",
                pattern=re.compile(
                    r'^(You are|Act as|Role:|As a|Your role is|You will be) (a |an )?[\w\s]{5,50}',
                    re.IGNORECASE | re.MULTILINE
                ),
                weight=0.18,
                description="Role assignment for AI"
            ),

            # Placeholders (medium-high confidence)
            DetectionPattern(
                name="placeholders_brackets",
                pattern=re.compile(r'\[([A-Z_\s]{3,})\]'),
                weight=0.12,
                description="Bracket placeholders like [DESCRIPTION]"
            ),

            DetectionPattern(
                name="placeholders_curly",
                pattern=re.compile(r'\{([a-z_]{3,})\}'),
                weight=0.10,
                description="Curly brace placeholders like {variable_name}"
            ),

            # Multi-step instructions (medium confidence)
            DetectionPattern(
                name="multi_step",
                pattern=re.compile(
                    r'^(Step \d+|Phase \d+|\d+\.)\s*[:)]?',
                    re.MULTILINE
                ),
                weight=0.10,
                description="Multi-step numbered instructions"
            ),

            # Output format specifications (medium confidence)
            DetectionPattern(
                name="output_format",
                pattern=re.compile(
                    r'(Required output|Output format|Expected deliverable|Provide|Generate|Return)[:]\s',
                    re.IGNORECASE | re.MULTILINE
                ),
                weight=0.10,
                description="Output format specifications"
            ),

            # Constraint language (low-medium confidence)
            DetectionPattern(
                name="constraints",
                pattern=re.compile(
                    r'\b(Must|Should|Never|Always|Do not|Don\'t|Avoid|Ensure)\s+(include|use|assume|exceed|contain)',
                    re.IGNORECASE
                ),
                weight=0.08,
                description="Constraint and requirement language"
            ),

            # Meta-instructions (medium confidence)
            DetectionPattern(
                name="meta_instructions",
                pattern=re.compile(
                    r'(This prompt|Use this|Copy.*into|Paste this into|Example prompt|Prompt template)',
                    re.IGNORECASE
                ),
                weight=0.06,
                description="Meta-instructions about the prompt"
            ),

            # Example sections (low confidence)
            DetectionPattern(
                name="examples",
                pattern=re.compile(
                    r'#{2,3}\s*(Examples?|Sample|Demonstration|Illustration)',
                    re.IGNORECASE | re.MULTILINE
                ),
                weight=0.04,
                description="Example sections"
            ),

            # Success criteria (low confidence)
            DetectionPattern(
                name="success_criteria",
                pattern=re.compile(
                    r'(Success criteria|Expected outcome|Acceptance criteria|Quality standards?)',
                    re.IGNORECASE
                ),
                weight=0.02,
                description="Success criteria and outcomes"
            ),

            # Numbered options/alternatives (medium confidence)
            DetectionPattern(
                name="options_alternatives",
                pattern=re.compile(
                    r'^(OPTION|Option|Alternative|Scenario|Path)\s+\d+',
                    re.MULTILINE
                ),
                weight=0.15,
                description="Numbered options or alternatives"
            ),

            # Analyze/Recommend directive (medium confidence)
            DetectionPattern(
                name="analysis_directive",
                pattern=re.compile(
                    r'(Analyze|Evaluate|Assess|Compare|Recommend|Determine).*through',
                    re.IGNORECASE
                ),
                weight=0.10,
                description="Analysis or recommendation directive"
            )
        ]

    def detect_prompts(self, content: str, min_length: int = 500,
                      min_confidence: float = 0.2, debug: bool = False) -> List[PromptMatch]:
        """
        Detect prompts in markdown content

        Args:
            content: Markdown content to analyze
            min_length: Minimum character length for a prompt
            min_confidence: Minimum confidence threshold (0.0-1.0)
            debug: Print debug information

        Returns:
            List of detected prompts
        """
        lines = content.split('\n')

        # Find potential prompt boundaries
        boundaries = self._find_boundaries(content, lines)

        if debug:
            print(f"DEBUG: Found {len(boundaries)} potential boundaries")

        # Score each potential prompt
        prompts = []
        for start, end in boundaries:
            prompt_content = '\n'.join(lines[start:end+1])

            if debug:
                print(f"DEBUG: Boundary {start}-{end}: {len(prompt_content)} chars")

            # Skip if too short
            if len(prompt_content) < min_length:
                if debug:
                    print(f"DEBUG: Skipped (too short)")
                continue

            # Calculate confidence score
            confidence, matched = self._score_content(prompt_content)

            if debug:
                print(f"DEBUG: Confidence: {confidence:.2f}, Patterns: {matched}")

            # Skip if confidence too low
            if confidence < min_confidence:
                if debug:
                    print(f"DEBUG: Skipped (confidence {confidence:.2f} < {min_confidence})")
                continue

            # Extract title if possible
            title = self._extract_title(prompt_content, lines[start] if start < len(lines) else "")

            prompts.append(PromptMatch(
                content=prompt_content.strip(),
                start_line=start + 1,  # 1-indexed
                end_line=end + 1,
                confidence=confidence,
                matched_patterns=matched,
                title=title
            ))

        return prompts

    def _find_boundaries(self, content: str, lines: List[str]) -> List[Tuple[int, int]]:
        """
        Find potential prompt boundaries in content

        Returns list of (start_line, end_line) tuples
        """
        boundaries = []

        # Strategy 1: Look for role assignments as start markers
        role_pattern = re.compile(
            r'^(You are|Act as|Role:|As a|Your role is)',
            re.IGNORECASE
        )

        # Strategy 2: Look for horizontal rules as delimiters
        hr_pattern = re.compile(r'^(\*{3,}|-{3,}|_{3,})$')

        # Strategy 3: Look for heading changes (h1, h2)
        heading_pattern = re.compile(r'^#{1,2}\s+')

        current_start = None
        hr_positions = []
        heading_positions = []

        for i, line in enumerate(lines):
            # Track horizontal rules
            if hr_pattern.match(line):
                hr_positions.append(i)

            # Track headings
            if heading_pattern.match(line):
                heading_positions.append(i)

            # Detect role assignments as potential starts
            if role_pattern.match(line) and current_start is None:
                current_start = i

        # Create boundaries from markers
        # If we found a role assignment, use it as start
        if current_start is not None:
            # Find end using next major heading or HR
            end = len(lines) - 1

            for pos in heading_positions + hr_positions:
                if pos > current_start + 10:  # At least 10 lines of content
                    end = pos - 1
                    break

            boundaries.append((current_start, end))

        # If no role assignment, try to identify large blocks between HRs
        if not boundaries and len(hr_positions) >= 2:
            for i in range(len(hr_positions) - 1):
                start = hr_positions[i] + 1
                end = hr_positions[i + 1] - 1
                if end - start > 20:  # At least 20 lines
                    boundaries.append((start, end))

        # Fallback: treat entire document as one potential prompt
        if not boundaries:
            boundaries.append((0, len(lines) - 1))

        return boundaries

    def _score_content(self, content: str) -> Tuple[float, List[str]]:
        """
        Score content for prompt likelihood

        Returns:
            (confidence_score, list_of_matched_patterns)
        """
        score = 0.0
        matched = []

        for pattern_def in self.patterns:
            matches = pattern_def.pattern.findall(content)
            if matches:
                # Scale weight by number of matches (with diminishing returns)
                match_count = len(matches)
                contribution = pattern_def.weight * min(1.0, match_count / 3)
                score += contribution
                matched.append(pattern_def.name)

        # Normalize score to 0.0-1.0 range
        # Maximum possible score if all patterns match multiple times
        max_score = sum(p.weight for p in self.patterns)
        normalized_score = min(1.0, score / max_score * 1.5)  # Boost factor

        return normalized_score, matched

    def _extract_title(self, content: str, first_line: str) -> Optional[str]:
        """Extract a title from the prompt content"""
        # Try to get from first heading
        heading_match = re.match(r'^#{1,3}\s+(.+)$', first_line)
        if heading_match:
            return heading_match.group(1).strip()

        # Try to get from role assignment
        role_match = re.search(
            r'^(?:You are|Act as|Role:|As a)\s+(?:a |an )?(.+?)(?:\.|$)',
            content,
            re.IGNORECASE | re.MULTILINE
        )
        if role_match:
            role = role_match.group(1).strip()
            return f"{role[:50]}..."  # Truncate long roles

        # Try to get from first TASK/OBJECTIVE section
        task_match = re.search(
            r'#{2,3}\s+(?:TASK|OBJECTIVE).*?\n(.+?)(?:\n|$)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        if task_match:
            task = task_match.group(1).strip()
            return task[:60] + "..." if len(task) > 60 else task

        return None


def main():
    """Test the prompt detector"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python prompt_detector.py <markdown_file> [--debug]")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    debug = "--debug" in sys.argv

    content = file_path.read_text()
    detector = PromptDetector()
    prompts = detector.detect_prompts(content, debug=debug)

    print(f"\n🔍 Found {len(prompts)} prompt(s) in {file_path.name}\n")

    for i, prompt in enumerate(prompts, 1):
        print(f"Prompt #{i}: {prompt.id}")
        print(f"  Title: {prompt.title or '(untitled)'}")
        print(f"  Lines: {prompt.start_line}-{prompt.end_line}")
        print(f"  Confidence: {prompt.confidence:.2f}")
        print(f"  Patterns: {', '.join(prompt.matched_patterns)}")
        print(f"  Length: {len(prompt.content)} chars")
        print()


if __name__ == '__main__':
    main()
