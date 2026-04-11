"""
Bead Orchestrator Routing
=========================

Determines whether a bead should run in GSD (Get Stuff Done) or PAUL
(Process Aligned, UAT Locked) mode.

GSD mode: fast path, no UAT validation.
PAUL mode: full pipeline including Phase 4b UAT validation.
"""

from __future__ import annotations


def decide_mode(
    bead_type: str,
    priority: int,
    effort: str,
    moc_types: list[str],
    title: str,
) -> str:
    """Determine the execution mode for a bead.

    Args:
        bead_type: One of "bug", "feature", "task", "chore", "refactor"
        priority: Integer 0-4 (0 = critical, 4 = low)
        effort: One of "micro", "small", "medium", "large", or "" (unknown)
        moc_types: List of MoC type strings (e.g. ["unit", "e2e", "integ", "demo"])
        title: Bead title string

    Returns:
        "gsd" or "paul"
    """
    # Rule 1: Any MoC type that requires integration/e2e/demo testing → PAUL
    paul_moc_types = {"e2e", "demo", "integ"}
    if paul_moc_types.intersection(set(moc_types)):
        return "paul"

    # Rule 2: Critical/high-priority bugs → GSD (fast fix path)
    if bead_type == "bug" and priority <= 1:
        return "gsd"

    # Rule 3: Refactoring tasks → GSD (no user-visible behavior change)
    if "[REFACTOR]" in title or bead_type in {"chore", "refactor"}:
        return "gsd"

    # Rule 4: Small scope → GSD
    if effort in {"micro", "small"}:
        return "gsd"

    # Rule 5: All features get UAT by default → PAUL
    if bead_type == "feature":
        return "paul"

    # Rule 6: Significant effort → PAUL
    if effort in {"medium", "large"}:
        return "paul"

    # Default: GSD (unknown/unclassified beads get fast path)
    return "gsd"
