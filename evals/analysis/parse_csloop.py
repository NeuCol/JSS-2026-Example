"""Parse CodeScribe-loop run directories into flat rows.

Layout (experiments/08-11-2026/ onward): experiments/<day>/<run-name>/loop/metadata/
  {manifest.toml, loop_NNN_{author,review}.toml}
regardless of whether the run directory is named "csloop-*" or "codescribe-*"
(the harness's own archive_summary.json calls its source ".codescribe" either
way) — so runs are discovered by the presence of loop/metadata/manifest.toml,
not by name prefix.

Per-loop token/tool-call data lives in loop_NNN_{author,review}.toml:
  [usage]       input, output, reasoning, cache_write, cache_read, and — where
                the provider reported one — the cache-write TTL split
                cache_write_5m / cache_write_1h
  [tool_calls]  executed, ok, errors, rejected  (rejected = policy-blocked,
                                                  never executed; errors = executed
                                                  but ok=false in [[tools]])

`usage.input` follows Anthropic's convention (cached tokens excluded) in every
archive CodeScribe writes today, but the older OpenAI-compatible archives
recorded the gross `prompt_tokens` instead. The two are told apart from the
archive's own arithmetic — see _input_basis().
"""

import json
import re

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from pathlib import Path

_USAGE_LINE = re.compile(r'usage = "(.*)"\s*$')

# Written only by the CodeScribe revision that records the cache-write TTL
# split. That same revision already subtracts cached tokens from OpenAI-style
# prompt_tokens, so their presence also settles the input convention.
_TTL_AWARE_MANIFEST_KEYS = (
    "cumulative_cache_creation_5m_tokens",
    "cumulative_cache_creation_1h_tokens",
)

_BASIS_CACHE = {}


def _load_toml(path):
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def _event_log_usage(loop_dir):
    """Yield the per-request usage payloads CodeScribe logged for this run.

    loop/{author,review}.toml are event logs rather than clean TOML — one
    archive carries raw terminal escapes in a tool-output preview and fails
    tomllib outright — so the payloads are pulled out line by line.
    """
    for name in ("author.toml", "review.toml"):
        path = loop_dir / name
        if not path.exists():
            continue
        with open(path, errors="replace") as fh:
            for line in fh:
                match = _USAGE_LINE.match(line)
                if match is None:
                    continue
                try:
                    yield json.loads(match.group(1).encode().decode("unicode_escape"))
                except (ValueError, UnicodeDecodeError):
                    continue


def _detect_input_basis(loop_dir, ttl_aware):
    """Decide whether this archive's OpenAI-style input is gross or net.

    CodeScribe copies the provider's `total_tokens` through untouched while it
    subtracts cached tokens from `prompt_tokens`, so each logged request that
    actually used the cache says which convention was written:

        total == prompt + completion                 -> prompt is gross
        total == prompt + completion + read + write  -> prompt is net

    Requests with no cache activity satisfy both and carry no information.
    """
    votes = {"gross": 0, "net": 0}
    for usage in _event_log_usage(loop_dir):
        if "total_tokens" not in usage:
            continue
        prompt = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
        completion = int(
            usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0
        )
        cached = int(usage.get("cache_read_input_tokens", 0) or 0) + int(
            usage.get("cache_creation_input_tokens", 0) or 0
        )
        if cached <= 0:
            continue
        total = int(usage["total_tokens"])
        if total == prompt + completion:
            votes["gross"] += 1
        elif total == prompt + completion + cached:
            votes["net"] += 1

    if votes["gross"] and votes["net"]:
        print(
            f"  WARNING: {loop_dir} mixes gross and net prompt_tokens "
            f"({votes['gross']} vs {votes['net']} requests) — leaving input as recorded"
        )
        return "unknown"
    if votes["gross"]:
        return "gross"
    if votes["net"]:
        return "net"
    if ttl_aware:
        # Same CodeScribe revision that records the TTL split records net input.
        return "net"
    print(
        f"  WARNING: {loop_dir} has no cache-bearing usage rows to pin down whether "
        "input is gross or net — leaving input as recorded"
    )
    return "unknown"


def _input_basis(loop_dir, model, ttl_aware):
    """Return what `usage.input` counts here: native / gross / net / unknown.

    Anthropic's `input_tokens` excludes cached tokens; OpenAI's `prompt_tokens`
    includes them, so `input + cache_write + cache_read` double-counts every
    cache read on an archive that stored `prompt_tokens` raw. Both kinds of
    archive sit side by side under experiments/, and which is which is read out
    of the archive itself — never from the run date, and never from how large
    `input` looks next to `cache_read`.
    """
    if not (model.startswith("oaic-") or model.startswith("openai-")):
        return "native"  # Anthropic usage; the two conventions already agree

    key = str(loop_dir)
    if key not in _BASIS_CACHE:
        _BASIS_CACHE[key] = _detect_input_basis(loop_dir, ttl_aware)
    return _BASIS_CACHE[key]


def _normalize_gross_input(row, basis):
    """Convert a gross OpenAI-style prompt_tokens row to the uncached remainder."""
    row["input_basis"] = basis
    if basis != "gross":
        return row

    gross = int(row.get("input_tokens", 0) or 0)
    cache_read = int(row.get("cache_read_tokens", 0) or 0)
    cache_write = int(row.get("cache_write_tokens", 0) or 0)
    net = gross - cache_read - cache_write
    if net < 0:
        print(
            f"  WARNING: {row['loop_file']}: cached tokens ({cache_read + cache_write}) "
            f"exceed gross input ({gross}) — clamping uncached input to 0"
        )
        net = 0
    row["input_tokens_gross"] = gross
    row["input_tokens"] = net
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
    ttl_aware = any(key in run_info for key in _TTL_AWARE_MANIFEST_KEYS)
    loop_dir = metadata_dir.parent

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

        row_model = str(loop_data.get("model", model))
        rows.append(
            _normalize_gross_input(
                {
                    "loop_file": loop_path.name,
                    "loop_index": loop_data.get("loop_index"),
                    "phase": loop_data.get("phase", "unknown"),
                    "model": row_model,
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
                    # False means the TTL split was never recorded, so pricing
                    # falls back to the 5-minute rate for this phase's writes.
                    "cache_write_ttl_attributed": (
                        "cache_write_5m" in usage or "cache_write_1h" in usage
                    ),
                    "tool_executed": tool_calls.get("executed", len(tools)),
                    "tool_ok": tool_calls.get("ok", tool_ok),
                    "tool_errors": tool_calls.get("errors", tool_error),
                    "tool_rejected": tool_calls.get("rejected", len(rejected_calls)),
                },
                _input_basis(loop_dir, row_model, ttl_aware),
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
