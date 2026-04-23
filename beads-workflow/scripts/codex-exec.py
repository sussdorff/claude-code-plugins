#!/usr/bin/env python3
"""
codex-exec.py — Thin wrapper around 'codex exec --json' that records usage
from turn.completed events into metrics.db via metrics.insert_agent_call().

Required env vars (when metrics recording is desired):
  RUN_ID       — bead_runs.run_id this Codex call belongs to
  BEAD_ID      — for denormalized query convenience
  PHASE_LABEL  — one of: codex-adversarial | codex-review | codex-fix-check

Optional env vars:
  WAVE_ID      — if set, forwarded to insert_agent_call
  ITERATION    — integer, default 1

Timeout control:
  CODEX_EXEC_TIMEOUT          — hard timeout in seconds (default: 300)
  CODEX_EXEC_MAX_PROMPT_CHARS — max chars for prompt (default: 32000)
  CODEX_EXEC_TAIL_BUFFER      — chars to preserve at end when truncating (default: 1024)

Other:
  METRICS_DIR_OVERRIDE — path to lib/orchestrator directory
  METRICS_DB_PATH      — path to metrics.db
  CODEX_CONFIG_PATH    — path to codex config.toml

Degraded mode: if RUN_ID is empty or the metrics module is unavailable,
codex still runs — only metrics recording is skipped (WARNING to stderr).

Exit code: propagates codex's exact exit code (or 124 on timeout).
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIMEOUT_EXIT_CODE = 124
DEFAULT_TIMEOUT = 300
DEFAULT_MAX_PROMPT_CHARS = 32000
DEFAULT_TAIL_BUFFER = 1024


# ---------------------------------------------------------------------------
# Model detection
# ---------------------------------------------------------------------------


def _detect_model(codex_config_path: str | None) -> str:
    """Read model from ~/.codex/config.toml or CODEX_CONFIG_PATH."""
    config_path: Path
    if codex_config_path:
        config_path = Path(codex_config_path)
    else:
        config_path = Path.home() / ".codex" / "config.toml"

    model = "codex"
    if config_path.is_file():
        for line in config_path.read_text().splitlines():
            m = re.match(r'^model\s*=\s*"([^"]+)"', line)
            if m:
                model = m.group(1)
                break

    # Normalize: if model doesn't contain 'codex', 'o1', or 'o3', prefix with "codex/"
    if "codex" not in model and "o1" not in model and "o3" not in model:
        model = f"codex/{model}"

    return model


# ---------------------------------------------------------------------------
# Diff resolution
# ---------------------------------------------------------------------------


def _resolve_diff(diff_range: str, prompt: str) -> str:
    """Resolve {{DIFF}} placeholder in the prompt for the given diff range."""
    max_inline_files = 2
    max_inline_bytes = 262144  # 256 KB

    try:
        names_result = subprocess.run(
            ["git", "diff", diff_range, "--name-only"],
            capture_output=True,
            text=True,
            check=False,
        )
        file_count = len([l for l in names_result.stdout.splitlines() if l.strip()])

        bytes_result = subprocess.run(
            ["git", "diff", diff_range],
            capture_output=True,
            check=False,
        )
        diff_bytes = len(bytes_result.stdout)

        if file_count <= max_inline_files and diff_bytes <= max_inline_bytes:
            diff_content = bytes_result.stdout.decode("utf-8", errors="replace")
        else:
            stat_result = subprocess.run(
                ["git", "diff", diff_range, "--stat"],
                capture_output=True,
                text=True,
                check=False,
            )
            diff_content = (
                f"{stat_result.stdout}\n\n"
                f"The diff is too large to inline ({file_count} files, {diff_bytes} bytes). "
                f"Inspect it directly:\n  git diff {diff_range}"
            )
    except Exception as e:
        diff_content = f"[Error resolving diff: {e}]"

    return prompt.replace("{{DIFF}}", diff_content)


# ---------------------------------------------------------------------------
# Prompt truncation
# ---------------------------------------------------------------------------


def _truncate_prompt(prompt: str, max_chars: int, tail_buffer: int) -> str:
    """Truncate the middle of the prompt if it exceeds max_chars."""
    if len(prompt) <= max_chars:
        return prompt

    print(
        f"codex-exec.py: WARNING: prompt is {len(prompt)} chars — truncating middle to fit "
        f"{max_chars} chars (override via CODEX_EXEC_MAX_PROMPT_CHARS; tail buffer: {tail_buffer} chars)",
        file=sys.stderr,
    )

    head_len = max_chars - tail_buffer
    head = prompt[:head_len]
    tail = prompt[-tail_buffer:]
    notice = (
        f"\n\n[TRUNCATED: prompt exceeded {max_chars} chars ({len(prompt)} total). "
        "Middle section removed to preserve format instructions.]\n\n"
    )
    return head + notice + tail


# ---------------------------------------------------------------------------
# Parse turn.completed events
# ---------------------------------------------------------------------------


def _parse_token_usage(lines: list[str]) -> tuple[int, int, int, int]:
    """Parse turn.completed events and sum token usage fields.

    Returns: (input_tokens, cached_input_tokens, output_tokens, reasoning_output_tokens)
    """
    total_input = 0
    total_cached = 0
    total_output = 0
    total_reasoning = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            usage = event.get("usage", {})
            total_input += usage.get("input_tokens", 0)
            total_cached += usage.get("cached_input_tokens", 0)
            total_output += usage.get("output_tokens", 0)
            total_reasoning += usage.get("reasoning_output_tokens", 0)

    return total_input, total_cached, total_output, total_reasoning


# ---------------------------------------------------------------------------
# Run codex with streaming + timeout
# ---------------------------------------------------------------------------


def _run_codex(
    args: list[str],
    timeout_secs: int,
) -> tuple[int, list[str]]:
    """
    Run 'codex exec --json <args>' streaming output to stdout.
    Returns (exit_code, buffered_lines).

    On timeout, kills the process and returns TIMEOUT_EXIT_CODE.
    """
    cmd = ["codex", "exec", "--json"] + args
    buffered_lines: list[str] = []
    exit_code = 0
    timed_out = False

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=None,  # inherit stderr
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print("codex-exec.py: ERROR: 'codex' not found on PATH", file=sys.stderr)
        return 1, []

    def _kill_on_timeout():
        nonlocal timed_out
        timed_out = True
        proc.kill()

    timer = threading.Timer(timeout_secs, _kill_on_timeout)
    timer.start()

    try:
        assert proc.stdout is not None
        for raw_line in proc.stdout:
            line = raw_line.decode("utf-8", errors="replace")
            sys.stdout.write(line)
            sys.stdout.flush()
            buffered_lines.append(line)
        proc.wait()
    finally:
        timer.cancel()

    if timed_out:
        return TIMEOUT_EXIT_CODE, buffered_lines

    exit_code = proc.returncode if proc.returncode is not None else 0
    return exit_code, buffered_lines


# ---------------------------------------------------------------------------
# Metrics recording
# ---------------------------------------------------------------------------


def _record_metrics(
    *,
    metrics_dir: Path,
    db_env: str,
    run_id: str,
    bead_id: str,
    phase_label: str,
    wave_id: str | None,
    iteration: int,
    model: str,
    duration_ms: int,
    exit_code: int,
    buffered_lines: list[str],
) -> int:
    """Parse tokens and insert agent_call row. Returns 0 on success, non-zero on failure."""
    sys.path.insert(0, str(metrics_dir))
    try:
        from metrics import DB_PATH, insert_agent_call  # type: ignore[import]
    except ImportError as e:
        print(
            f"codex-exec.py: WARNING: Cannot import metrics module from {metrics_dir} — "
            f"metrics recording skipped ({e})",
            file=sys.stderr,
        )
        return 0

    db_path = Path(db_env) if db_env else DB_PATH

    total_input, total_cached, total_output, total_reasoning = _parse_token_usage(buffered_lines)
    total_tokens = total_input + total_cached + total_output + total_reasoning

    if total_tokens == 0:
        print(
            "codex-exec.py: WARNING: no turn.completed events found — no DB record written",
            file=sys.stderr,
        )
        return 0

    try:
        insert_agent_call(
            run_id=run_id,
            bead_id=bead_id,
            phase_label=phase_label,
            agent_label="codex",
            model=model,
            iteration=iteration,
            input_tokens=total_input,
            cached_input_tokens=total_cached,
            output_tokens=total_output,
            reasoning_output_tokens=total_reasoning,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
            exit_code=exit_code,
            wave_id=wave_id,
            db_path=db_path,
        )
        return 0
    except Exception as e:
        print(f"codex-exec.py: ERROR: metrics recording failed: {e}", file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # ---------------------------------------------------------------------------
    # Resolve paths
    # ---------------------------------------------------------------------------
    script_dir = Path(__file__).resolve().parent
    metrics_dir_override = os.environ.get("METRICS_DIR_OVERRIDE", "")
    if metrics_dir_override:
        metrics_dir = Path(metrics_dir_override)
    else:
        metrics_dir = script_dir.parent / "lib" / "orchestrator"

    # ---------------------------------------------------------------------------
    # Validate env vars and determine whether metrics recording is possible
    # ---------------------------------------------------------------------------
    run_id = os.environ.get("RUN_ID", "")
    skip_metrics = False

    if not run_id:
        print(
            "codex-exec.py: WARNING: RUN_ID is not set — metrics recording skipped",
            file=sys.stderr,
        )
        skip_metrics = True

    iteration = int(os.environ.get("ITERATION", "1"))
    wave_id_env = os.environ.get("WAVE_ID", "") or None

    if not skip_metrics:
        bead_id = os.environ.get("BEAD_ID", "")
        phase_label = os.environ.get("PHASE_LABEL", "")

        if not bead_id:
            print("codex-exec.py: ERROR: BEAD_ID is not set", file=sys.stderr)
            return 1
        if not phase_label:
            print("codex-exec.py: ERROR: PHASE_LABEL is not set", file=sys.stderr)
            return 1

        # Validate metrics module availability
        sys.path.insert(0, str(metrics_dir))
        try:
            import importlib
            spec = importlib.util.find_spec("metrics")
            if spec is None:
                raise ImportError("metrics module not found")
        except (ImportError, ValueError):
            print(
                f"codex-exec.py: WARNING: Cannot import metrics module from {metrics_dir} — "
                "metrics recording skipped",
                file=sys.stderr,
            )
            skip_metrics = True

    # ---------------------------------------------------------------------------
    # Read model from config
    # ---------------------------------------------------------------------------
    codex_config_path = os.environ.get("CODEX_CONFIG_PATH", "")
    model = _detect_model(codex_config_path or None)

    # ---------------------------------------------------------------------------
    # Timeout / prompt size settings
    # ---------------------------------------------------------------------------
    timeout_secs = int(os.environ.get("CODEX_EXEC_TIMEOUT", str(DEFAULT_TIMEOUT)))
    max_prompt_chars = int(os.environ.get("CODEX_EXEC_MAX_PROMPT_CHARS", str(DEFAULT_MAX_PROMPT_CHARS)))
    tail_buffer = int(os.environ.get("CODEX_EXEC_TAIL_BUFFER", str(DEFAULT_TAIL_BUFFER)))

    # ---------------------------------------------------------------------------
    # Parse --diff-range option
    # ---------------------------------------------------------------------------
    args = list(argv)
    if args and args[0] == "--diff-range":
        if len(args) < 2 or not args[1]:
            print(
                "codex-exec.py: ERROR: --diff-range requires a value (e.g. sha...HEAD)",
                file=sys.stderr,
            )
            return 1
        diff_range = args[1]
        args = args[2:]

        if args:
            args[0] = _resolve_diff(diff_range, args[0])

    # ---------------------------------------------------------------------------
    # Prompt size guard
    # ---------------------------------------------------------------------------
    if args:
        args[0] = _truncate_prompt(args[0], max_prompt_chars, tail_buffer)

    # ---------------------------------------------------------------------------
    # Run codex
    # ---------------------------------------------------------------------------
    db_env = os.environ.get("METRICS_DB_PATH", "")
    start_ms = int(time.time() * 1000)

    codex_exit, buffered_lines = _run_codex(args, timeout_secs)

    end_ms = int(time.time() * 1000)
    duration_ms = end_ms - start_ms

    # ---------------------------------------------------------------------------
    # Metrics recording (skip if degraded)
    # ---------------------------------------------------------------------------
    if skip_metrics:
        return codex_exit

    bead_id = os.environ.get("BEAD_ID", "")
    phase_label = os.environ.get("PHASE_LABEL", "")

    python_exit = _record_metrics(
        metrics_dir=metrics_dir,
        db_env=db_env,
        run_id=run_id,
        bead_id=bead_id,
        phase_label=phase_label,
        wave_id=wave_id_env,
        iteration=iteration,
        model=model,
        duration_ms=duration_ms,
        exit_code=codex_exit,
        buffered_lines=buffered_lines,
    )

    if python_exit != 0:
        return python_exit

    return codex_exit


if __name__ == "__main__":
    sys.exit(main())
