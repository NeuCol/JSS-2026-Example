"""Parse CodeScribe-loop run directories into flat rows.

Layout (experiments/08-11-2026/ onward): experiments/<day>/<run-name>/loop/metadata/
  {manifest.toml, loop_NNN_{author,review}.toml}
regardless of whether the run directory is named "csloop-*" or "codescribe-*"
(the harness's own archive_summary.json calls its source ".codescribe" either
way) — so runs are discovered by the presence of loop/metadata/manifest.toml,
not by name prefix.

Per-loop token/tool-call data lives in loop_NNN_{author,review}.toml:
  [usage]       input, output, reasoning, cache_write, cache_read
  [tool_calls]  executed, ok, errors, rejected  (rejected = policy-blocked,
                                                  never executed; errors = executed
                                                  but ok=false in [[tools]])
"""

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from pathlib import Path


def _load_toml(path):
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def _normalize_gross_input(row):
    """Convert gross OpenAI-style prompt_tokens to the uncached remainder.

    CodeScribe before 2026-08-26 recorded the OpenAI-compatible `prompt_tokens`
    verbatim. That field already contains the cached tokens, while Anthropic's
    `input_tokens` excludes them, so those archives double-count cache reads.
    Detected structurally: a gross row has input >= cache_read > 0, a corrected
    row has input far below cache_read.
    """
    model = str(row.get("model", ""))
    if not (model.startswith("oaic-") or model.startswith("openai-")):
        return row
    cache_read = int(row.get("cache_read_tokens", 0) or 0)
    cache_write = int(row.get("cache_write_tokens", 0) or 0)
    gross = int(row.get("input_tokens", 0) or 0)
    if cache_read <= 0 or gross < cache_read:
        return row
    row["input_tokens_gross"] = gross
    row["input_tokens"] = max(0, gross - cache_read - cache_write)
    row["input_gross_corrected"] = True
    return row


def parse_metadata_dir(metadata_dir):
    """Return one row per loop_*.toml file (per phase per loop) in this metadata dir."""
    manifest_path = metadata_dir / "manifest.toml"
    if not manifest_path.exists():
        return []

    manifest = _load_toml(manifest_path)
    run_info = manifest.get("run", {})
    model = run_info.get("model", "unknown")

    rows = []
    for loop_path in sorted(metadata_dir.glob("loop_*.toml")):
        try:
            loop_data = _load_toml(loop_path)
        except Exception as exc:
            print(f"  WARNING: failed to parse {loop_path}: {exc}")
            continue

        usage = loop_data.get("usage", {})
        tool_calls = loop_data.get("tool_calls", {})
        tools = loop_data.get("tools", [])
        rejected_calls = loop_data.get("rejected_calls", [])

        tool_ok = sum(1 for t in tools if t.get("ok"))
        tool_error = sum(1 for t in tools if not t.get("ok"))

        rows.append(
            _normalize_gross_input(
                {
                    "loop_file": loop_path.name,
                    "loop_index": loop_data.get("loop_index"),
                    "phase": loop_data.get("phase", "unknown"),
                    "model": loop_data.get("model", model),
                    "stop_reason": loop_data.get("stop_reason"),
                    "iterations": loop_data.get("iterations"),
                    "duration_s": loop_data.get("duration_s", 0.0),
                    "input_tokens": usage.get("input", 0),
                    "output_tokens": usage.get("output", 0),
                    "reasoning_tokens": usage.get("reasoning", 0),
                    "cache_write_tokens": usage.get("cache_write", 0),
                    "cache_read_tokens": usage.get("cache_read", 0),
                    "cache_write_5m_tokens": usage.get("cache_write_5m", 0),
                    "cache_write_1h_tokens": usage.get("cache_write_1h", 0),
                    "tool_executed": tool_calls.get("executed", len(tools)),
                    "tool_ok": tool_calls.get("ok", tool_ok),
                    "tool_errors": tool_calls.get("errors", tool_error),
                    "tool_rejected": tool_calls.get("rejected", len(rejected_calls)),
                }
            )
        )
    return rows


def parse_csloop_run(run_dir):
    run_dir = Path(run_dir)
    metadata_dir = run_dir / "loop" / "metadata"
    rows = []
    for row in parse_metadata_dir(metadata_dir):
        row["run_dir"] = str(run_dir)
        rows.append(row)
    return rows


def parse_all_csloop(experiments_root):
    experiments_root = Path(experiments_root)
    all_rows = []
    for day_dir in sorted(experiments_root.iterdir()):
        if not day_dir.is_dir():
            continue
        for run_dir in sorted(day_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            if not (run_dir / "loop" / "metadata" / "manifest.toml").exists():
                continue
            rows = parse_csloop_run(run_dir)
            if not rows:
                print(f"  (skipping {run_dir} — no usable metadata found)")
                continue
            for row in rows:
                row["day"] = day_dir.name
                row["run_name"] = run_dir.name
                all_rows.append(row)
    return all_rows


if __name__ == "__main__":
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "experiments"
    rows = parse_all_csloop(root)
    print(f"Parsed {len(rows)} csloop loop rows")
    for row in rows[:5]:
        print(row)
