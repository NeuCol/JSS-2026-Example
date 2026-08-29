"""When did a run first touch each top-level `src/` module, with what tool,
and on what reasoning — joined against the doxygen-derived roadmap position of
what it eventually settled there.

Neither harness tags "which file is this tool call about" as structured
metadata, so the path is recovered the same way generate_graphs.py already
recovers ccworkflow's phase (from raw transcript text), by pattern-matching
`src/<module>/<file>.<ext>` wherever it appears in the tool arguments: verbatim
in a csloop `read`/`write`/`edit` `path` argument, or embedded in the shell
command string for ccworkflow (every ccworkflow tool call observed in this
corpus is `Bash` — there is no structured file-path tool). Matches are
restricted to the exact units the run actually settled (the caller passes
git_file_counts.translated_file_units for that run) rather than every module
its transcript merely mentions: a run reads and greps plenty of files it never
translates — rejected candidates, infrastructure it only inspects — and dating
a module's entry to one of those would measure exploration, not the work the
run committed to.

ccworkflow timestamps come from each `agent-*.jsonl`'s per-message
`timestamp` field (the same field generate_graphs._ccworkflow_wall_time_seconds
already uses for wall time). csloop timestamps come from `logs/toolusage.toml`,
which is NOT valid TOML in every archive (some tool output previews carry raw
terminal escapes that abort tomllib — the same failure parse_csloop.py already
works around for loop/{author,review}.toml) and is parsed line-by-line here for
the same reason.
"""

import json
import re
from datetime import datetime
from pathlib import Path

# Matches an explicit source-file reference, so a bare directory listing
# ("ls src/BDK/") is not read as a touch. Module names are the top-level
# src/ directories (BDK, Mods, W2jet, ...); the extension list is the set
# git_file_counts.py already treats as Fortran-or-translated-output.
MODULE_FILE_RE = re.compile(
    r"(?:^|[\s'\"(=])(?:software/mcfm/)?src/([A-Za-z0-9_]+)/(?:[A-Za-z0-9_./]*/)?"
    r"([A-Za-z0-9_]+)\.(?:f90|f|F90|F|cpp|hpp|cxx)\b"
)


def _module_matches(text):
    """[(module, basename), ...] for every source-file reference in `text`."""
    return [(m.group(1), m.group(2)) for m in MODULE_FILE_RE.finditer(text or "")]


def _parse_ts(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# ccworkflow — agent-*.jsonl
# ---------------------------------------------------------------------------
def _ccworkflow_all_timestamps(run_dir):
    timestamps = []
    for workflow_dir in Path(run_dir).glob("workflow-wf_*"):
        for agent_path in workflow_dir.glob("agent-*.jsonl"):
            with open(agent_path) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    ts = json.loads(line).get("timestamp")
                    if ts:
                        timestamps.append(_parse_ts(ts))
    return timestamps


def _ccworkflow_events(run_dir):
    """[{"ts", "tool", "matches", "rationale"}] for every tool call that names
    a source file, across every subagent in the run, unsorted."""
    events = []
    for workflow_dir in sorted(Path(run_dir).glob("workflow-wf_*")):
        for agent_path in sorted(workflow_dir.glob("agent-*.jsonl")):
            with open(agent_path) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    if record.get("type") != "assistant":
                        continue
                    ts = record.get("timestamp")
                    if not ts:
                        continue
                    content = record.get("message", {}).get("content", [])
                    if isinstance(content, str):
                        content = [{"type": "text", "text": content}]
                    text = " ".join(
                        b.get("text", "") for b in content
                        if isinstance(b, dict) and b.get("type") == "text"
                    ).strip()
                    for b in content:
                        if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                            continue
                        inp = b.get("input", {}) or {}
                        haystack = " ".join(str(v) for v in inp.values())
                        matches = _module_matches(haystack)
                        if matches:
                            events.append({
                                "ts": _parse_ts(ts),
                                "tool": b.get("name", "?"),
                                "matches": matches,
                                "rationale": text[:220],
                            })
    return events


# ---------------------------------------------------------------------------
# csloop — logs/toolusage.toml, parsed line-by-line (see module docstring)
# ---------------------------------------------------------------------------
_KV_RE = re.compile(r'^([A-Za-z_]+) = (.*)$')


def _toml_string(raw):
    """Unescape a one-line TOML basic string (with its surrounding quotes)."""
    if not (len(raw) >= 2 and raw.startswith('"') and raw.endswith('"')):
        return None
    try:
        return raw[1:-1].encode().decode("unicode_escape")
    except UnicodeDecodeError:
        return raw[1:-1]


def _csloop_blocks(path):
    """Yield one dict per `[[event]]` block, skipping triple-quoted (multiline)
    values entirely — this analysis only needs the scalar fields."""
    block = {}
    in_triple = False
    with open(path, errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")
            if in_triple:
                if line.strip() == "'''":
                    in_triple = False
                continue
            if line.strip() == "[[event]]":
                if block:
                    yield block
                block = {}
                continue
            m = _KV_RE.match(line)
            if not m:
                continue
            key, raw_val = m.group(1), m.group(2)
            if raw_val.rstrip() == "'''":
                in_triple = True
                continue
            if key in ("ts", "tool", "event", "args", "model_text"):
                block[key] = _toml_string(raw_val)
    if block:
        yield block


def _csloop_first_ts(run_dir):
    path = Path(run_dir) / "logs" / "toolusage.toml"
    if not path.exists():
        return None
    for block in _csloop_blocks(path):
        if block.get("ts"):
            return _parse_ts(block["ts"])
    return None


def _csloop_events(run_dir):
    path = Path(run_dir) / "logs" / "toolusage.toml"
    if not path.exists():
        return []
    out = []
    for block in _csloop_blocks(path):
        if block.get("event") != "tool_start" or not block.get("ts"):
            continue
        matches = _module_matches(block.get("args") or "")
        if matches:
            out.append({
                "ts": _parse_ts(block["ts"]),
                "tool": block.get("tool", "?"),
                "matches": matches,
                "rationale": (block.get("model_text") or "")[:220],
            })
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def is_ccworkflow(run_name):
    return "ccworkflow" in run_name


def run_start_ts(experiments_root, day, run_name):
    """Wall-clock start of the run, for computing elapsed time -- the minimum
    timestamp over EVERY event (not just the module-matching ones), since the
    first tool calls in every run observed are reads of the plan/spec, not of
    src/, and using the first *matched* event as t0 would understate elapsed
    time for a run that spent a while orienting itself before entering src/."""
    run_dir = Path(experiments_root) / day / run_name
    if is_ccworkflow(run_name):
        timestamps = _ccworkflow_all_timestamps(run_dir)
        return min(timestamps) if timestamps else None
    return _csloop_first_ts(run_dir)


def module_entry_order(experiments_root, day, run_name, settled_units):
    """For each top-level module among `settled_units` (git_file_counts unit
    ids, e.g. "BDK/FFPMscT" -- exactly what git_file_counts.translated_file_units
    returns for this run), when the run's transcript first touches ONE OF THE
    UNITS IT ACTUALLY SETTLED there.

    Matches are restricted to `settled_units` on purpose: both harnesses spend
    plenty of tool calls reading or grepping files that never get translated
    (candidates it rejected, infrastructure it only inspects), and counting
    those as "entering" a module would date a module's entry to whatever it
    happened to glance at first rather than to the work it actually did there.

    Returns a list of dicts, sorted by timestamp:
      {"module", "unit_hint" (the settled unit's basename -- always one of
       `settled_units`, never an abandoned candidate), "elapsed_min", "tool",
       "rationale"}
    Empty if the run has no parseable transcript or t0 can't be established.
    """
    unit_ids = set(settled_units)
    run_dir = Path(experiments_root) / day / run_name
    t0 = run_start_ts(experiments_root, day, run_name)
    if t0 is None:
        return []
    events = _ccworkflow_events(run_dir) if is_ccworkflow(run_name) else _csloop_events(run_dir)

    best = {}
    for e in events:
        for module, basename in e["matches"]:
            if f"{module}/{basename}" not in unit_ids:
                continue
            if module in best and e["ts"] >= best[module]["ts"]:
                continue
            best[module] = {
                "module": module, "unit_hint": basename, "ts": e["ts"],
                "tool": e["tool"], "rationale": e["rationale"],
            }
    ordered = sorted(best.values(), key=lambda d: d["ts"])
    for d in ordered:
        d["elapsed_min"] = (d.pop("ts") - t0).total_seconds() / 60.0
    return ordered


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from git_file_counts import translated_file_units

    experiments_root = Path(__file__).parent.parent / "experiments"
    day, run_name = sys.argv[1], sys.argv[2]
    units = translated_file_units(day, run_name) or []
    for row in module_entry_order(experiments_root, day, run_name, units):
        print(f"{row['elapsed_min']:6.1f} min  {row['module']:6s}  {row['tool']:10s}  "
              f"{row['unit_hint']:20s}  {row['rationale'][:80]}")
