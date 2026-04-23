#!/usr/bin/env python3
"""Discover tracked Codex agent sources and their export targets."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "dev-tools" / "codex-agents"


@dataclass(frozen=True)
class AgentRecord:
    """Single tracked Codex agent source.

    This repository is dev-only. Runtime consumers read from ~/.codex/agents/.
    See docs/architecture/dev-repo-principle.md.
    """

    name: str
    source_file: str

    @property
    def source_path(self) -> Path:
        return REPO_ROOT / self.source_file


def discover_agents(repo_root: Path = REPO_ROOT) -> list[AgentRecord]:
    """Discover every tracked Codex agent source."""
    source_dir = repo_root / "dev-tools" / "codex-agents"
    discovered: list[AgentRecord] = []
    for path in sorted(source_dir.glob("*.toml")):
        if not path.is_file():
            continue
        discovered.append(
            AgentRecord(
                name=path.stem,
                source_file=str(path.relative_to(repo_root)),
            )
        )
    return discovered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List tracked Codex agent sources and their export targets."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = discover_agents()
    if args.json:
        print(json.dumps([asdict(record) for record in records], indent=2))
        return

    for record in records:
        print(f"{record.name}\t{record.source_file}")


if __name__ == "__main__":
    main()
