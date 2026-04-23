#!/usr/bin/env python3
"""Discover and build the Codex-facing skill export surface."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOTS = (
    "beads-workflow",
    "business",
    "content",
    "core",
    "dev-tools",
    "infra",
    "medical",
    "meta",
)
SKILL_FILENAMES = ("SKILL.md", "skill.md")
EXCLUDED_PATH_PARTS = {
    ".agents",
    ".claude",
    ".git",
    ".pytest_cache",
    "__pycache__",
    "fixtures",
    "tests",
}
OPENAI_REQUIRED_FIELDS = ("display_name:", "short_description:", "default_prompt:")
DISPLAY_TOKEN_OVERRIDES = {
    "api": "API",
    "bd": "bd",
    "ccu": "CCU",
    "ci": "CI",
    "cli": "CLI",
    "cmux": "cmux",
    "qa": "QA",
    "ui": "UI",
}


@dataclass(frozen=True)
class SkillRecord:
    """Single discovered skill plus Codex export metadata."""

    name: str
    source_dir: str
    skill_file: str
    description: str
    display_name: str
    default_prompt: str
    has_openai_yaml: bool
    has_claude_adapter: bool
    codex_support: str
    codex_support_reason: str

    @property
    def source_path(self) -> Path:
        return REPO_ROOT / self.source_dir

    @property
    def openai_yaml_path(self) -> Path:
        return self.source_path / "agents" / "openai.yaml"


def _normalize_ws(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse the small subset of YAML frontmatter this repo relies on."""
    if not text.startswith("---\n"):
        return {}

    end = text.find("\n---\n", 4)
    if end == -1:
        return {}

    frontmatter = text[4:end].splitlines()
    parsed: dict[str, str] = {}
    index = 0
    while index < len(frontmatter):
        line = frontmatter[index]
        if not line.strip() or line.lstrip().startswith("#") or line.startswith((" ", "\t")):
            index += 1
            continue

        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            index += 1
            continue

        key, raw_value = match.groups()
        raw_value = raw_value.strip()
        if raw_value in {"|", "|-", ">", ">-"}:
            index += 1
            block: list[str] = []
            while index < len(frontmatter):
                next_line = frontmatter[index]
                if next_line.startswith((" ", "\t")):
                    block.append(next_line.lstrip())
                    index += 1
                    continue
                if not next_line.strip():
                    block.append("")
                    index += 1
                    continue
                break

            if raw_value.startswith("|"):
                value = "\n".join(block).strip()
            else:
                value = _normalize_ws(" ".join(item for item in block if item.strip()))
            parsed[key] = value
            continue

        parsed[key] = raw_value.strip("\"'")
        index += 1

    return parsed


def _humanize_skill_name(name: str) -> str:
    words = re.split(r"[-_]+", name)
    rendered = []
    for word in words:
        lowered = word.lower()
        if lowered in DISPLAY_TOKEN_OVERRIDES:
            rendered.append(DISPLAY_TOKEN_OVERRIDES[lowered])
        elif word:
            rendered.append(word.capitalize())
    return " ".join(rendered) or name


def _short_description(frontmatter: dict[str, str], name: str) -> str:
    description = _normalize_ws(frontmatter.get("description", ""))
    if description:
        return description
    return f"Use the {name} skill for this task."


def _default_prompt(name: str, description: str) -> str:
    return f"Use the {name} skill to help with this task. {description}"


def _codex_support(frontmatter: dict[str, str]) -> tuple[str, str]:
    raw_value = frontmatter.get("codex-support", "enabled").strip().lower()
    reason = _normalize_ws(frontmatter.get("codex-support-reason", ""))
    if raw_value in {"disabled", "false", "cc-only", "claude-only"}:
        return "disabled", reason or "Marked as intentionally excluded from Codex export."
    return "enabled", reason


def discover_skills(repo_root: Path = REPO_ROOT) -> list[SkillRecord]:
    """Discover every source skill in the monorepo."""
    discovered: list[SkillRecord] = []
    seen_names: dict[str, str] = {}

    for root_name in SOURCE_ROOTS:
        base = repo_root / root_name
        if not base.is_dir():
            continue

        skill_files: list[Path] = []
        for candidate in base.rglob("*"):
            if candidate.is_file() and candidate.name in SKILL_FILENAMES:
                skill_files.append(candidate)

        for skill_file in sorted(skill_files):
            relative = skill_file.relative_to(repo_root)
            if any(part in EXCLUDED_PATH_PARTS for part in relative.parts):
                continue

            skill_dir = skill_file.parent
            skill_name = skill_dir.name
            existing = seen_names.get(skill_name)
            if existing is not None:
                raise RuntimeError(
                    f"Duplicate skill name '{skill_name}' in {existing} and {skill_dir.relative_to(repo_root)}"
                )

            content = skill_file.read_text(encoding="utf-8", errors="ignore")
            frontmatter = _parse_frontmatter(content)
            description = _short_description(frontmatter, skill_name)
            codex_support, codex_reason = _codex_support(frontmatter)

            record = SkillRecord(
                name=skill_name,
                source_dir=str(skill_dir.relative_to(repo_root)),
                skill_file=str(relative),
                description=description,
                display_name=_humanize_skill_name(skill_name),
                default_prompt=_default_prompt(skill_name, description),
                has_openai_yaml=(skill_dir / "agents" / "openai.yaml").exists(),
                has_claude_adapter=(skill_dir / "SKILL.claude-adapter.md").exists(),
                codex_support=codex_support,
                codex_support_reason=codex_reason,
            )
            discovered.append(record)
            seen_names[skill_name] = record.source_dir

    return sorted(discovered, key=lambda record: record.name)


def _render_openai_yaml(record: SkillRecord) -> str:
    display_name = record.display_name.replace('"', '\\"')
    description = record.description.replace('"', '\\"')
    default_prompt = record.default_prompt.replace('"', '\\"')
    return (
        "interface:\n"
        f'  display_name: "{display_name}"\n'
        f'  short_description: "{description}"\n'
        f'  default_prompt: "{default_prompt}"\n'
    )


def ensure_openai_metadata(export_dir: Path, record: SkillRecord) -> None:
    """Ensure the export tree contains a minimal valid agents/openai.yaml."""
    openai_yaml = export_dir / "agents" / "openai.yaml"
    if openai_yaml.exists():
        content = openai_yaml.read_text(encoding="utf-8", errors="ignore")
        if all(field in content for field in OPENAI_REQUIRED_FIELDS):
            return

    openai_yaml.parent.mkdir(parents=True, exist_ok=True)
    openai_yaml.write_text(_render_openai_yaml(record), encoding="utf-8")


def build_skill_export(record: SkillRecord, destination: Path) -> None:
    """Copy one skill into an export destination and top up Codex metadata."""
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        record.source_path,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"),
    )
    source_skill_name = Path(record.skill_file).name
    if source_skill_name == "skill.md":
        lowercase_skill = destination / "skill.md"
        canonical_skill = destination / "SKILL.md"
        if lowercase_skill.exists():
            temp_skill = destination / "__skill-export-rename__.md"
            lowercase_skill.rename(temp_skill)
            temp_skill.rename(canonical_skill)
    ensure_openai_metadata(destination, record)


def exportable_skills(records: Iterable[SkillRecord]) -> list[SkillRecord]:
    return [record for record in records if record.codex_support != "disabled"]


def _print_table(records: list[SkillRecord]) -> None:
    print(f"{'SKILL':<24} {'SOURCE':<48} {'SUPPORT':<8} {'ADAPTER':<7} {'META':<4}")
    print(f"{'-' * 24} {'-' * 48} {'-' * 8} {'-' * 7} {'-' * 4}")
    for record in records:
        support = "codex" if record.codex_support == "enabled" else "skip"
        adapter = "yes" if record.has_claude_adapter else "no"
        metadata = "yes" if record.has_openai_yaml else "gen"
        print(
            f"{record.name:<24} {record.source_dir:<48} {support:<8} {adapter:<7} {metadata:<4}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover Codex-exportable skills in this repo.")
    parser.add_argument("--json", action="store_true", help="Emit the skill inventory as JSON.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include skills marked codex-support: disabled in the output.",
    )
    args = parser.parse_args()

    records = discover_skills()
    if not args.all:
        records = exportable_skills(records)

    if args.json:
        print(json.dumps([asdict(record) for record in records], indent=2))
        return

    _print_table(records)


if __name__ == "__main__":
    main()
