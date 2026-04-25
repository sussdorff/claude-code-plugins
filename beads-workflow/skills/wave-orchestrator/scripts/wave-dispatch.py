#!/usr/bin/env python3
"""
wave-dispatch.py — Set up cmux panes and dispatch cld -b for a wave.

Usage: wave-dispatch.py <bead-id1> <bead-id2> ... --workspace <id> --base-pane <id>
         [--wave-id <id>] [--quick <id>] [--skip-scenarios]

Creates ONE pane per bead (1-pane mode). Renames each surface, dispatches cld -b or cld -bq,
and outputs wave config JSON.

The output JSON can be fed directly into wave-status.py for monitoring.

**--workspace and --base-pane are REQUIRED.** The orchestrator MUST determine its own
cmux context (via `cmux identify --json` from within the orchestrator's pane) and pass
both values explicitly. This prevents the script from silently falling back to an
unrelated workspace (e.g. the user's currently focused pane, or a stale "last active"
workspace) and dispatching beads into the wrong location.
"""

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_surface(output: str) -> str:
    """Extract 'surface:N' from cmux output."""
    m = re.search(r"surface:[0-9]+", output)
    return m.group(0) if m else ""


# ---------------------------------------------------------------------------
# WaveDispatcher — core dispatch logic with optional runner DI
# ---------------------------------------------------------------------------


class WaveDispatcher:
    """Orchestrates cmux pane creation and cld dispatch for a wave.

    Args:
        runner: Optional callable with the same signature as subprocess.run.
                Defaults to subprocess.run. Inject a mock for testing.
    """

    def __init__(self, runner=None):
        self._runner = runner if runner is not None else subprocess.run

    def bd_show_json(self, bead_id: str) -> dict | None:
        """Call bd show <id> --json and return parsed JSON."""
        try:
            result = self._runner(
                ["bd", "show", bead_id, "--json"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                return None
            data = json.loads(result.stdout)
            if isinstance(data, list) and data:
                return data[0]
            if isinstance(data, dict):
                return data
            return None
        except Exception:
            return None

    def check_scenario(self, bead_id: str) -> bool:
        """Return True if bead has a ## Scenario section."""
        try:
            result = self._runner(
                ["bd", "show", bead_id],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return bool(re.search(r"^## (Scenario|Szenario)", result.stdout, re.MULTILINE))
        except Exception:
            return False

    def check_already_running(self, bead_id: str) -> dict | None:
        """Check if bead is already dispatched in a live session.

        Returns a dict {"pids": [...], "worktree_path": str} if already running, else None.
        A bead is considered already running if:
        - A process with '--worktree bead-<bead_id>' is in the process list, OR
        - A git worktree at path '*/bead-<bead_id>' exists
        """
        pids: list[str] = []
        worktree_path = ""

        # Check 1: live claude process with --worktree bead-<id>
        try:
            result = self._runner(
                ["pgrep", "-f", f"worktree bead-{re.escape(bead_id)}( |$)"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = [p.strip() for p in result.stdout.strip().splitlines() if p.strip()]
        except Exception as e:
            print(f"Warning: check_already_running failed for {bead_id}: {e}", file=sys.stderr)

        # Check 2: git worktree exists for this bead
        try:
            result = self._runner(
                ["git", "worktree", "list", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("worktree ") and f"bead-{bead_id}" in line:
                        worktree_path = line.split(" ", 1)[1].strip()
                        break
        except Exception as e:
            print(f"Warning: check_already_running failed for {bead_id}: {e}", file=sys.stderr)

        if pids or worktree_path:
            return {"pids": pids, "worktree_path": worktree_path}
        return None

    def dispatch(
        self,
        bead_ids: list[str],
        quick_ids: list[str],
        workspace: str,
        base_surface: str,
        wave_id: str,
        skip_scenarios: bool = False,
    ) -> tuple[int, dict]:
        """Dispatch all beads. Returns (exit_code, output_dict).

        exit_code 0 = success, 1 = error (e.g. missing scenarios, empty bead list).
        output_dict is the wave config JSON (empty on error).
        """
        all_ids = bead_ids + quick_ids
        quick_set = set(quick_ids)

        if not all_ids:
            print("Error: no bead IDs provided", file=sys.stderr)
            print(
                "Usage: wave-dispatch.py <bead-id1> ... [--quick <id>] ... "
                "[--workspace <id>] [--base-pane <id>] [--skip-scenarios]",
                file=sys.stderr,
            )
            return 1, {}

        # Scenario gate
        if not skip_scenarios:
            missing_scenarios: list[str] = []
            for bid in all_ids:
                bead_data = self.bd_show_json(bid)
                bead_type = ""
                if bead_data:
                    bead_type = bead_data.get("type", "") or bead_data.get("issue_type", "")
                if bead_type == "feature" and not self.check_scenario(bid):
                    missing_scenarios.append(bid)
            if missing_scenarios:
                print(
                    "Error: the following feature bead(s) are missing a ## Scenario section:",
                    file=sys.stderr,
                )
                for bid in missing_scenarios:
                    print(f"  - {bid}", file=sys.stderr)
                print("", file=sys.stderr)
                print("Run the scenario generator for each bead, then retry:", file=sys.stderr)
                print(
                    f"  Agent(subagent_type='dev-tools:scenario-generator', "
                    f"prompt='Generate scenarios for {' '.join(missing_scenarios)}')",
                    file=sys.stderr,
                )
                print("", file=sys.stderr)
                print("To bypass this check (not recommended): add --skip-scenarios", file=sys.stderr)
                return 1, {}

        print(f"Workspace: {workspace}, Base surface: {base_surface}", file=sys.stderr)

        dispatch_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        beads_json: list[dict] = []

        for bid in all_ids:
            is_quick = bid in quick_set
            cld_flag = "-bq" if is_quick else "-b"
            surface_suffix = "qf" if is_quick else "impl"
            short_id = bid.split("-")[-1] if "-" in bid else bid
            mode = "quick" if is_quick else "full"

            # Duplicate-dispatch guard
            already = self.check_already_running(bid)
            if already is not None:
                pid_list = ", ".join(already["pids"]) if already["pids"] else "none"
                wt_path = already["worktree_path"] or "none"
                print(
                    f"ALREADY-RUNNING: {bid} — worktree={wt_path}, pids=[{pid_list}] "
                    f"— skipping dispatch to avoid duplicate session",
                    file=sys.stderr,
                )
                beads_json.append({
                    "id": bid,
                    "surface": "",
                    "mode": mode,
                    "status": "already-running",
                    "pids": already["pids"],
                    "worktree_path": already["worktree_path"],
                })
                continue

            # Create new split
            try:
                split_result = self._runner(
                    ["cmux", "new-split", "right", "--surface", base_surface, "--workspace", workspace],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                split_output = split_result.stdout + split_result.stderr
            except Exception as e:
                print(f"Error: failed to create split for bead {bid}: {e}", file=sys.stderr)
                continue

            surface = _extract_surface(split_output)
            if not surface:
                print(
                    f"Error: failed to create split for bead {bid}. Output: {split_output!r}",
                    file=sys.stderr,
                )
                continue

            # Wait for surface to be ready
            time.sleep(3)

            # Rename tab
            try:
                self._runner(
                    ["cmux", "rename-tab", "--surface", surface, f"{short_id}-{surface_suffix}"],
                    capture_output=True,
                    timeout=10,
                )
            except Exception:
                pass

            # Dispatch
            try:
                self._runner(
                    ["cmux", "send", "--surface", surface, f"WAVE_ID={wave_id} cld {cld_flag} {bid}"],
                    capture_output=True,
                    timeout=10,
                )
                self._runner(
                    ["cmux", "send-key", "--surface", surface, "enter"],
                    capture_output=True,
                    timeout=10,
                )
            except Exception as e:
                print(f"Warning: failed to send command to {surface} for bead {bid}: {e}", file=sys.stderr)
                continue

            beads_json.append({"id": bid, "surface": surface, "mode": mode, "status": "dispatched"})
            print(
                f"Dispatched ({cld_flag}): {bid} → {surface} ({short_id}-{surface_suffix})",
                file=sys.stderr,
            )

        output = {
            "dispatch_time": dispatch_time,
            "workspace": workspace,
            "wave_id": wave_id,
            "beads": beads_json,
        }
        return 0, output


# ---------------------------------------------------------------------------
# Main (CLI entry point)
# ---------------------------------------------------------------------------


def main() -> int:
    args = sys.argv[1:]

    bead_ids: list[str] = []
    quick_ids: list[str] = []
    workspace = ""
    base_surface = ""
    wave_id = ""
    skip_scenarios = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--workspace", "--base-pane", "--wave-id", "--quick"):
            if i + 1 >= len(args):
                print(f"Error: {arg} requires a value", file=sys.stderr)
                sys.exit(1)
        if arg == "--workspace":
            workspace = args[i + 1]
            i += 2
        elif arg == "--base-pane":
            base_surface = args[i + 1]
            i += 2
        elif arg == "--wave-id":
            wave_id = args[i + 1]
            i += 2
        elif arg == "--quick":
            quick_ids.append(args[i + 1])
            i += 2
        elif arg == "--skip-scenarios":
            skip_scenarios = True
            i += 1
        else:
            bead_ids.append(arg)
            i += 1

    # Auto-generate wave_id
    if not wave_id:
        wave_id = f"wave-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    dispatcher = WaveDispatcher()

    # Require explicit workspace and base-pane.
    #
    # Rationale: auto-detection via `cmux identify` was unreliable — when the
    # orchestrator ran as an Agent subagent, the cmux caller context was not
    # guaranteed to match the orchestrator's actual pane, and the fallback
    # silently picked unrelated workspaces (e.g. the last active one) and
    # dispatched beads there. Forcing the orchestrator to determine and pass
    # its own cmux context up-front makes workspace mis-routing impossible.
    if not workspace:
        print(
            "Error: --workspace is required. The wave-orchestrator must call "
            "`cmux identify --json` from within its own pane and pass "
            "`--workspace <caller.workspace_ref>` explicitly.",
            file=sys.stderr,
        )
        return 2

    if not base_surface:
        print(
            "Error: --base-pane is required. The wave-orchestrator must call "
            "`cmux identify --json` from within its own pane and pass "
            "`--base-pane <caller.surface_ref>` explicitly.",
            file=sys.stderr,
        )
        return 2

    exit_code, output = dispatcher.dispatch(
        bead_ids=bead_ids,
        quick_ids=quick_ids,
        workspace=workspace,
        base_surface=base_surface,
        wave_id=wave_id,
        skip_scenarios=skip_scenarios,
    )

    if exit_code != 0:
        return exit_code

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
