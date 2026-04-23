"""
council.py — Python helpers for the /council skill.

Functions:
    load_role_profiles(yaml_path, profile_type) -> list[dict]
    classify_severity(text) -> str
    consolidate_findings(agent_outputs) -> str
    consolidate_findings_cross_bead(findings_by_bead) -> str
    has_critical_findings(agent_outputs) -> bool
    parse_council_input(arg, bd_runner) -> dict
    detect_missing_scenario(bead_description) -> bool
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Callable, Union

import yaml

__all__ = [
    "load_role_profiles",
    "classify_severity",
    "consolidate_findings",
    "consolidate_findings_cross_bead",
    "has_critical_findings",
    "parse_council_input",
    "detect_missing_scenario",
]

# Severity ordering (highest first)
_SEVERITY_ORDER = ["CRITICAL", "WARNING", "NOTE"]


def load_role_profiles(yaml_path: Union[str, Path], profile_type: str = "requirements") -> list[dict]:
    """Load role profiles from a YAML file for the given profile type.

    Args:
        yaml_path: Absolute or relative path to the YAML roles file.
        profile_type: Key in the YAML file to load (e.g. 'requirements', 'training').

    Returns:
        List of role dicts, each with keys: name, description, focus.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        KeyError: If the profile_type is not found in the YAML.
    """
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Role profiles file not found: {yaml_path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    profiles = data[profile_type]

    if not isinstance(profiles, list):
        raise ValueError(
            f"Profile type '{profile_type}' must be a list, got {type(profiles).__name__}"
        )
    required_keys = {"name", "description", "focus"}
    for i, entry in enumerate(profiles):
        missing = required_keys - set(entry.keys())
        if missing:
            raise ValueError(
                f"Profile entry {i} in '{profile_type}' is missing required keys: {sorted(missing)}"
            )

    return profiles


def classify_severity(text: str) -> str:
    """Extract the highest severity level from text.

    Looks for [CRITICAL], [WARNING], or [NOTE] tags in the text.

    Args:
        text: The agent output text to scan.

    Returns:
        'CRITICAL', 'WARNING', 'NOTE', or 'NONE' if no tags found.
    """
    for severity in _SEVERITY_ORDER:
        if f"[{severity}]" in text:
            return severity
    return "NONE"


def _parse_findings_from_output(agent_output: str) -> list[dict]:
    """Parse individual findings from a single agent output.

    Expected format per finding line:
        - [SEVERITY] Topic: Description. Recommendation.

    Returns:
        List of dicts with keys: severity, agent, topic, finding, recommendation.
    """
    findings = []

    # Extract agent name from COUNCIL-REVIEW header
    agent_name = "Unknown"
    header_match = re.search(r"COUNCIL-REVIEW:\s*(.+)", agent_output)
    if header_match:
        agent_name = header_match.group(1).strip()

    # Find finding lines: - [SEVERITY] Topic: rest
    pattern = re.compile(
        r"-\s*\[(CRITICAL|WARNING|NOTE)\]\s*([^:]+):\s*(.+)"
    )
    for match in pattern.finditer(agent_output):
        severity = match.group(1)
        topic = match.group(2).strip()
        rest = match.group(3).strip()

        # Split rest into finding and recommendation at " → " separator first,
        # falling back to ". " as a secondary heuristic
        if " → " in rest:
            arrow_parts = rest.split(" → ", 1)
            finding_text = arrow_parts[0].strip()
            recommendation = arrow_parts[1].strip()
        else:
            parts = rest.split(". ", 1)
            if len(parts) == 2:
                finding_text = parts[0].strip() + "."
                recommendation = parts[1].strip()
            else:
                finding_text = rest
                recommendation = "—"

        findings.append(
            {
                "severity": severity,
                "agent": agent_name,
                "topic": topic,
                "finding": finding_text,
                "recommendation": recommendation,
            }
        )

    return findings


def consolidate_findings(agent_outputs: list[str]) -> str:
    """Parse all agent outputs and produce a sorted markdown findings table.

    Findings are sorted: CRITICAL first, then WARNING, then NOTE.

    Args:
        agent_outputs: List of raw agent output strings.

    Returns:
        Markdown string containing a findings table sorted by severity.
    """
    all_findings: list[dict] = []
    for output in agent_outputs:
        all_findings.extend(_parse_findings_from_output(output))

    # Sort by severity order
    severity_rank = {s: i for i, s in enumerate(_SEVERITY_ORDER)}
    all_findings.sort(key=lambda f: severity_rank.get(f["severity"], 99))

    # Build markdown table
    header = "| # | Severity | Agent | Thema | Finding | Empfehlung |"
    separator = "|---|----------|-------|-------|---------|------------|"
    rows = [header, separator]

    for idx, f in enumerate(all_findings, start=1):
        row = (
            f"| {idx} | {f['severity']} | {f['agent']} | {f['topic']} "
            f"| {f['finding']} | {f['recommendation']} |"
        )
        rows.append(row)

    return "\n".join(rows)


def has_critical_findings(agent_outputs: list[str]) -> bool:
    """Return True if any agent output contains a CRITICAL finding.

    Args:
        agent_outputs: List of raw agent output strings.

    Returns:
        True if at least one output has a [CRITICAL] tag, False otherwise.
    """
    return any(classify_severity(output) == "CRITICAL" for output in agent_outputs)


# ---------------------------------------------------------------------------
# Input parsing (AK1-AK4)
# ---------------------------------------------------------------------------

def _default_bd_runner(bead_id: str) -> dict:
    """Run `bd show <bead_id> --json` via subprocess and return parsed JSON."""
    result = subprocess.run(
        ["bd", "show", bead_id, "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"bd show {bead_id} failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"bd show {bead_id} returned invalid JSON: {result.stdout[:200]}"
        ) from exc


def parse_council_input(
    arg: str,
    bd_runner: Callable[[str], dict] | None = None,
) -> dict:
    """Parse the council input argument and determine the mode.

    Args:
        arg: The raw argument string (file path, bead ID, label:name, etc.).
        bd_runner: Optional callable that takes a bead_id and returns its JSON data.
                   Defaults to calling `bd show <id> --json` via subprocess.

    Returns:
        Dict with keys:
            mode: "file" | "bead" | "epic" | "label"
            value: The parsed value (path, bead ID, or label name)
            bead_data: (only for bead/epic modes) The bead JSON data

    Raises:
        ValueError: If the argument is not a file, not a known bead, and not a label.
    """
    if bd_runner is None:
        bd_runner = _default_bd_runner

    # Label mode: explicit prefix required
    if arg.startswith("label:"):
        return {"mode": "label", "value": arg.removeprefix("label:")}

    # File mode: contains .md or /
    if arg.endswith(".md") or "/" in arg:
        return {"mode": "file", "value": arg}

    # Fallback: check if arg is an existing file
    if Path(arg).is_file():
        return {"mode": "file", "value": arg}

    # Try as bead ID
    try:
        bead_data = bd_runner(arg)
    except RuntimeError as exc:
        raise ValueError(
            "Not a file, not a known bead ID. Use label:<name> for labels."
        ) from exc

    # Check for children to determine bead vs epic
    children = bead_data.get("children", [])
    if children:
        return {"mode": "epic", "value": arg, "bead_data": bead_data}
    else:
        return {"mode": "bead", "value": arg, "bead_data": bead_data}


# ---------------------------------------------------------------------------
# Scenario pre-flight (AK5)
# ---------------------------------------------------------------------------

def detect_missing_scenario(bead_description: str) -> bool:
    """Return True if the bead description has no ## Szenario or ## Scenario heading.

    Args:
        bead_description: The full bead description/markdown text.

    Returns:
        True if no scenario heading is found, False if one exists.
    """
    return not bool(re.search(r"^##\s+(?:Szenario|Scenario)\b", bead_description, re.MULTILINE))


# ---------------------------------------------------------------------------
# Cross-bead findings table (AK6)
# ---------------------------------------------------------------------------

def consolidate_findings_cross_bead(findings_by_bead: dict[str, list[str]]) -> str:
    """Parse agent outputs per bead and produce a cross-bead findings table.

    The table includes a Bead column to identify which bead each finding belongs to.

    Args:
        findings_by_bead: Dict mapping bead_id -> list of raw agent output strings.

    Returns:
        Markdown string with a findings table including a Bead column.
    """
    all_findings: list[dict] = []
    for bead_id, outputs in findings_by_bead.items():
        for output in outputs:
            parsed = _parse_findings_from_output(output)
            for finding in parsed:
                finding["bead"] = bead_id
            all_findings.extend(parsed)

    if not all_findings:
        return "No findings."

    # Sort by severity order
    severity_rank = {s: i for i, s in enumerate(_SEVERITY_ORDER)}
    all_findings.sort(key=lambda f: severity_rank.get(f["severity"], 99))

    # Build markdown table with Bead column
    header = "| # | Bead | Severity | Agent | Thema | Finding | Empfehlung |"
    separator = "|---|------|----------|-------|-------|---------|------------|"
    rows = [header, separator]

    for idx, f in enumerate(all_findings, start=1):
        row = (
            f"| {idx} | {f['bead']} | {f['severity']} | {f['agent']} | {f['topic']} "
            f"| {f['finding']} | {f['recommendation']} |"
        )
        rows.append(row)

    return "\n".join(rows)
