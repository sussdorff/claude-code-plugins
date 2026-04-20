#!/usr/bin/env python3
"""render-summary.py - Render the Technical Summary block for session-close Step 17.

Reads session state from JSON (via --state <file> or stdin) and emits the
formatted Technical Summary block to stdout.

Usage:
  python3 render-summary.py --state <file.json>
  echo '{"commit_sha": "abc123", ...}' | python3 render-summary.py

State schema (all fields optional — missing fields render as "unknown"):
  commit_sha              (str)  - Short or full git SHA of the session commit
  commit_msg              (str)  - Commit message
  version_tag             (str)  - Version tag created (e.g. "v2026.04.47"), or ""
  changelog_updated       (bool) - Whether CHANGELOG.md was updated
  doc_gaps                (list) - List of documentation gap strings (may be empty)
  learnings_extracted     (bool) - Whether learnings extraction ran
  session_summary_saved   (bool) - Whether session summary was saved to open-brain
  turn_log_status         (str)  - One of: uploaded_deleted, empty_deleted,
                                   skipped_no_file, skipped_dry_run, error_kept,
                                   or any error_kept parse_error=... variant
  merge_from_main_first   (str)  - Result of first merge: success, skipped, conflict, unknown
  merge_from_main_second  (str)  - Result of second merge: success, skipped, conflict, unknown
  worktree_merged         (bool) - Whether feature branch was merged into main
  push_status             (str)  - success, skipped, failed, or unknown
  pipeline_status         (str)  - passed, failed, skipped_no_gh, skipped_not_authed,
                                   skipped_no_workflow, skipped_flag, skipped_dry_run, unknown
  pipeline_run_url        (str)  - URL to the CI run (only on passed/failed)
"""

import argparse
import json
import sys


def _yn(val) -> str:
    """Convert a boolean-ish value to Y/N."""
    if isinstance(val, bool):
        return "Y" if val else "N"
    if isinstance(val, str):
        return "Y" if val.lower() in ("true", "yes", "1", "y") else "N"
    return "N"


def _str(val, default: str = "unknown") -> str:
    """Return a non-empty string or the default."""
    return str(val).strip() if val else default


def render(state: dict) -> str:
    commit_sha = _str(state.get("commit_sha"), "unknown")
    commit_msg = _str(state.get("commit_msg"), "")
    version_tag = _str(state.get("version_tag"), "")
    changelog = _yn(state.get("changelog_updated"))
    doc_gaps = state.get("doc_gaps") or []
    learnings = _yn(state.get("learnings_extracted"))
    summary_saved = _yn(state.get("session_summary_saved"))
    turn_log = _str(state.get("turn_log_status"), "skipped_no_file")
    merge1 = _str(state.get("merge_from_main_first"), "unknown")
    merge2 = _str(state.get("merge_from_main_second"), "unknown")
    worktree_merged = _yn(state.get("worktree_merged"))
    push_status = _str(state.get("push_status"), "unknown")
    pipeline_status = _str(state.get("pipeline_status"), "unknown")
    pipeline_run_url = _str(state.get("pipeline_run_url"), "")

    # Format turn-log status for readability
    turn_log_display = turn_log.replace("_", " ")
    if "error_kept" in turn_log:
        turn_log_display = f"ERROR: kept ({turn_log})"
    elif turn_log == "uploaded_deleted":
        turn_log_display = "uploaded + deleted"
    elif turn_log == "empty_deleted":
        turn_log_display = "empty + deleted"
    elif turn_log == "skipped_no_file":
        turn_log_display = "skipped (no file)"
    elif turn_log == "skipped_dry_run":
        turn_log_display = "skipped (dry-run)"

    # Format pipeline status for readability
    pipeline_display = pipeline_status
    if pipeline_run_url and pipeline_status in ("passed", "failed"):
        pipeline_display = f"{pipeline_status} — {pipeline_run_url}"

    # Format doc gaps
    if doc_gaps:
        doc_gaps_display = ", ".join(str(g) for g in doc_gaps)
    else:
        doc_gaps_display = "none"

    # Format version tag
    version_display = version_tag if version_tag else "none"

    # Build commit line
    commit_line = commit_sha
    if commit_msg:
        # Truncate long messages
        msg = commit_msg if len(commit_msg) <= 72 else commit_msg[:69] + "..."
        commit_line = f"{commit_sha} {msg}"

    lines = [
        "### Technical Summary",
        f"- Commit:               {commit_line}",
        f"- Version tag:          {version_display}",
        f"- Changelog updated:    {changelog}",
        f"- Doc gaps:             {doc_gaps_display}",
        f"- Learnings extracted:  {learnings}",
        f"- Session summary:      {summary_saved}",
        f"- Turn-log:             {turn_log_display}",
        f"- First merge (main):   {merge1}",
        f"- Second merge (main):  {merge2}",
        f"- Worktree merged:      {worktree_merged}",
        f"- Push:                 {push_status}",
        f"- Pipeline:             {pipeline_display}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render session-close Technical Summary from JSON state."
    )
    parser.add_argument(
        "--state",
        metavar="FILE",
        help="Path to JSON state file. If omitted, reads from stdin.",
    )
    args = parser.parse_args()

    try:
        if args.state:
            with open(args.state, encoding="utf-8") as f:
                state = json.load(f)
        else:
            state = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"render-summary: JSON parse error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"render-summary: cannot read state file: {exc}", file=sys.stderr)
        return 1

    print(render(state))
    return 0


if __name__ == "__main__":
    sys.exit(main())
