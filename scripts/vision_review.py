#!/usr/bin/env python3
"""
vision-review: Non-interactive file I/O and computation for /vision-review skill.

Handles the automated parts of the vision review workflow:
- Computing the Vision Health Score (% principles confirmed unchanged)
- Generating draft ADR files in docs/adr/drafts/ for contested principles
- Generating the vision review report

Interactive per-principle dialog is handled by SKILL.md (Claude), NOT by this script.
This script is called by SKILL.md after Claude has collected per-principle results.

Public API:
    compute_health_score(confirmed: list[str], total: int) -> float
        Returns health score 0-100 (% of principles confirmed unchanged).

    generate_draft_adr(principle, evidence, council_finding, run_date, adr_dir) -> Path
        Writes a draft ADR for a contested principle. Returns path to created file.

    generate_review_report(vision_path, results, health_score, council_mode, report_dir) -> Path
        Writes the vision review report. Returns path to created file.

    PrincipleResult dataclass
        Holds per-principle dialog outcome.

CLI interface:
    python3 scripts/vision_review.py <vision_path> --output-dir docs/ [options]

    Options:
      --yes              Assume all principles confirmed (Y), no interactive dialog
      --mock-council [FIXTURE_JSON]  Use mock council fixture instead of real council
      --output-dir DIR   Where to write review report (default: docs/)
      --adr-dir DIR      Where to write draft ADRs (default: docs/adr/drafts/)
      --max-principles N Hard-fail if more than N principles (default: 5)
"""

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    # Direct execution or scripts/ directory on sys.path
    from vision_parser import Principle, VisionParseError, parse_vision
except ImportError:
    # Imported as scripts.vision_review (e.g. from tests with repo root on sys.path)
    from scripts.vision_parser import Principle, VisionParseError, parse_vision  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------

@dataclass
class PrincipleResult:
    """Outcome of the per-principle review dialog.

    Attributes:
        principle_id:     Authored ID, e.g. "P1".
        principle_text:   The principle text.
        confirmed:        True if principle is confirmed unchanged (Y), False if contested (N).
        evidence:         User-provided evidence for the assessment.
        council_finding:  Council critique, or None if not contested or council skipped.
        council_mode:     "full" | "degraded" | "skipped" | "mock".
    """

    principle_id: str
    principle_text: str
    confirmed: bool
    evidence: str
    council_finding: str | None
    council_mode: str


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------

def compute_health_score(confirmed: list[str], total: int) -> float:
    """Compute vision health score as % of principles confirmed unchanged.

    Args:
        confirmed: List of principle IDs confirmed as unchanged.
        total:     Total number of principles reviewed.

    Returns:
        Float 0.0-100.0. Returns 0.0 if total is 0 (avoids division by zero).

    Examples:
        compute_health_score(["P1", "P2"], 3) -> 66.67
        compute_health_score(["P1", "P2", "P3"], 3) -> 100.0
        compute_health_score([], 3) -> 0.0
    """
    if total == 0:
        return 0.0
    return round(len(confirmed) / total * 100, 2)


def generate_draft_adr(
    principle: Principle,
    evidence: str,
    council_finding: str | None,
    run_date: str,
    adr_dir: Path,
    council_mode: str = "skipped",
) -> Path:
    """Write a draft ADR for a contested principle.

    Creates docs/adr/drafts/vision-mutation-<rule_id>-<run_date>.md.
    The 'supersedes' field uses the authored rule_id (e.g. P1), NOT a positional index.

    Args:
        principle:       The contested Principle object.
        evidence:        User-provided evidence that the principle may need revision.
        council_finding: Council critique, or None if council was unavailable.
        run_date:        Timestamp string in YYYYMMDD-HHMMSS format.
        adr_dir:         Directory to write the draft ADR into (created if missing).
        council_mode:    Caller-authoritative council mode string.

    Returns:
        Path to the created draft ADR file.
    """
    adr_dir.mkdir(parents=True, exist_ok=True)

    rule_id = principle.id
    filename = f"vision-mutation-{rule_id}-{run_date}.md"
    adr_path = adr_dir / filename

    council_text = council_finding if council_finding is not None else "Council not available (degraded mode)."

    # Use YAML literal block scalars for user-supplied text to handle colons, quotes, newlines
    def _yaml_literal(text: str, indent: int = 2) -> str:
        """Format text as a YAML literal block scalar with given indent."""
        pad = " " * indent
        indented_lines = "\n".join(pad + line for line in text.splitlines())
        return "|\n" + indented_lines

    evidence_yaml = _yaml_literal(evidence)
    council_yaml_value = _yaml_literal(council_text)

    content = f"""---
type: vision-mutation
status: draft
supersedes: vision.md#{rule_id}
evidence: {evidence_yaml}
council_finding: {council_yaml_value}
council_mode: {council_mode}
---

# Vision Mutation: {rule_id} — {principle.text[:60]}{"..." if len(principle.text) > 60 else ""}

## Current Principle

**{rule_id}**: {principle.text}

## Contested Evidence

{evidence}

## Council Critique

{council_text}

## Proposed Action

[ ] Accept current principle (no change needed)
[ ] Revise principle text
[ ] Remove principle
[ ] Create follow-up bead

## Architecture Contracts Touched

- Supersedes: `vision.md#{rule_id}`
"""

    adr_path.write_text(content, encoding="utf-8")
    return adr_path


def generate_review_report(
    vision_path: Path,
    results: list[PrincipleResult],
    health_score: float,
    council_mode: str,
    report_dir: Path,
) -> Path:
    """Write the vision review report.

    Creates docs/vision-review-<YYYYMMDD-HHMMSS>.md with:
    - YAML frontmatter including council_mode and health_score
    - Per-principle results table
    - Re-author suggestion if health_score < 80
    - Degraded mode warning if council_mode == "degraded"

    Args:
        vision_path:  Path to the reviewed vision.md file.
        results:      List of PrincipleResult from per-principle dialog.
        health_score: Computed health score (0-100).
        council_mode: "full" | "degraded" | "mock".
        report_dir:   Directory to write the report into.

    Returns:
        Path to the created report file.
    """
    report_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(tz=timezone.utc)
    run_date = now.strftime("%Y%m%d-%H%M%S")
    iso_date = now.strftime("%Y-%m-%d")

    filename = f"vision-review-{run_date}.md"
    report_path = report_dir / filename

    total = len(results)
    confirmed_count = sum(1 for r in results if r.confirmed)
    contested_count = total - confirmed_count

    # Per-principle table rows
    table_rows = ""
    for r in results:
        status_icon = "✅ Y" if r.confirmed else "❌ N"
        # Sanitize: collapse whitespace (removes newlines), then truncate
        principle_text = " ".join(r.principle_text.split())
        principle_snippet = principle_text[:40] + ("..." if len(principle_text) > 40 else "")
        evidence_flat = " ".join(r.evidence.split())
        evidence_snippet = evidence_flat[:60].replace("|", "\\|")
        table_rows += f"| {r.principle_id} | {principle_snippet} | {status_icon} | {evidence_snippet} |\n"

    # Conditional re-author suggestion
    reauthor_section = ""
    if health_score < 80:
        reauthor_section = (
            "\n> ⚠️ Health score is below 80%. "
            "Consider invoking `/vision-author --refresh` for a full re-author session.\n"
        )

    # Degraded mode warning
    degraded_warning = ""
    if council_mode == "degraded":
        degraded_warning = (
            " ⚠️ Council (CCP-bw6) was unavailable. "
            "Degraded mode used (single-perspective Haiku critique)."
        )

    content = f"""---
document_type: vision-review
vision_path: {vision_path}
review_date: {iso_date}
council_mode: {council_mode}
health_score: {health_score}
---

# Vision Review — {iso_date}

## Summary

- Principles reviewed: {total}
- Confirmed unchanged: {confirmed_count}
- Contested: {contested_count}
- **Vision Health Score: {health_score}%**
{reauthor_section}
## Per-Principle Results

| Principle | Text | Confirmed | Evidence |
|-----------|------|-----------|---------|
{table_rows}
## Council Mode

`council_mode: {council_mode}`{degraded_warning}
"""

    report_path.write_text(content, encoding="utf-8")
    return report_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _load_mock_council(fixture_path: Path) -> dict[str, str]:
    """Load mock council findings from a JSON fixture file.

    Returns a dict mapping principle_id -> finding text.
    """
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    return data.get("findings", {})


def _run_cli(argv: list[str]) -> int:
    """Main CLI logic. Returns exit code 0 or 1."""
    parser = argparse.ArgumentParser(
        description="Vision review file I/O and computation (non-interactive parts).",
        prog="vision_review.py",
    )
    parser.add_argument("vision_path", help="Path to vision.md to review")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Assume all principles confirmed (Y), no interactive dialog",
    )
    parser.add_argument(
        "--mock-council",
        metavar="FIXTURE_JSON",
        nargs="?",
        const="",
        help="Use mock council fixture instead of spawning real council",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/",
        help="Where to write review report (default: docs/)",
    )
    parser.add_argument(
        "--adr-dir",
        default="docs/adr/drafts/",
        help="Where to write draft ADRs (default: docs/adr/drafts/)",
    )
    parser.add_argument(
        "--max-principles",
        type=int,
        default=5,
        help="Hard-fail if more than N principles (default: 5)",
    )

    args = parser.parse_args(argv)

    vision_path = Path(args.vision_path)
    output_dir = Path(args.output_dir)
    adr_dir = Path(args.adr_dir)

    # Parse vision
    try:
        vision = parse_vision(vision_path)
    except VisionParseError as exc:
        print(f"vision-review: parse error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"vision-review: file not found: {vision_path}", file=sys.stderr)
        return 1

    # Guard: max principles
    if len(vision.principles) > args.max_principles:
        print(
            f"vision-review: too many principles ({len(vision.principles)} > {args.max_principles}). "
            f"Override with --max-principles.",
            file=sys.stderr,
        )
        return 1

    # Determine council mode
    if args.mock_council is not None:
        council_mode = "mock"
        if args.mock_council:
            mock_findings = _load_mock_council(Path(args.mock_council))
        else:
            mock_findings = {}
    else:
        council_mode = "skipped"
        mock_findings = {}

    # Build results (--yes assumes all confirmed)
    now = datetime.now(tz=timezone.utc)
    run_date = now.strftime("%Y%m%d-%H%M%S")

    results: list[PrincipleResult] = []
    draft_adrs: list[Path] = []

    for principle in vision.principles:
        if args.yes:
            confirmed = True
            evidence = "Auto-confirmed (--yes flag)."
        else:
            # Interactive mode: read from stdin
            print(f"\n[{principle.id}] {principle.text}")
            print("Is this principle still accurate? [Y/n] ", end="", flush=True)
            answer = input().strip().lower()
            confirmed = answer != "n"
            print("Evidence (brief): ", end="", flush=True)
            evidence = input().strip() or "No evidence provided."

        council_finding = mock_findings.get(principle.id)

        result = PrincipleResult(
            principle_id=principle.id,
            principle_text=principle.text,
            confirmed=confirmed,
            evidence=evidence,
            council_finding=council_finding,
            council_mode=council_mode,
        )
        results.append(result)

        # Generate draft ADR for contested principles
        if not confirmed:
            adr_path = generate_draft_adr(
                principle=principle,
                evidence=evidence,
                council_finding=council_finding,
                run_date=run_date,
                adr_dir=adr_dir,
                council_mode=council_mode,
            )
            draft_adrs.append(adr_path)
            print(f"  Draft ADR: {adr_path}")

    # Compute health score
    confirmed_ids = [r.principle_id for r in results if r.confirmed]
    health_score = compute_health_score(confirmed_ids, len(results))

    # Generate review report
    report_path = generate_review_report(
        vision_path=vision_path,
        results=results,
        health_score=health_score,
        council_mode=council_mode,
        report_dir=output_dir,
    )

    print(f"\nVision Health Score: {health_score}%")
    print(f"Review report: {report_path}")

    if health_score < 80:
        print(
            "⚠️  Health score below 80%. Consider running /vision-author --refresh.",
            file=sys.stderr,
        )

    return 0


def main() -> None:
    """CLI entry point."""
    sys.exit(_run_cli(sys.argv[1:]))


if __name__ == "__main__":
    main()
