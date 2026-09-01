"""Attribute wall time, USD and tool calls to the INDIVIDUAL translated files
of a run, rather than to the run as a whole.

Everything else in analysis/ divides a run total by files settled (see
generate_graphs.derived_metrics). That is the right normalization for comparing
runs, but it cannot answer "what did *this* file cost", and it hides the fact
that the two harnesses record effort at completely different granularities.
This module answers the per-file question and is explicit about the fact that
only one of the two harnesses can answer it exactly.

TWO METHODS, AND THEY ARE NOT INTERCHANGEABLE
---------------------------------------------
`method` is on every row this module emits, and any table or plot that mixes
the two must say so.

  "exact" (ccworkflow, R1-R3)
      ccworkflow spawns one AUTHOR subagent per unit -- its first user message
      is literally `You are an AUTHOR agent for ONE unit ...: <path>` -- so the
      unit's own transcript carries its own tokens, its own tool calls and its
      own timestamps. Nothing is apportioned.

      What this DOES NOT include is the run's shared phases: triage picks the
      units, serial integrate lands them and runs the build and the test suite,
      and a metadata agent writes agent_log.md. None of that is attributable to
      one file, so a ccworkflow per-file cost here is an AUTHOR-PHASE cost and
      is strictly lower than the run's true cost per file. `author_share` on
      the run record says how much of the run's USD the author phase actually
      was (46%-70% across R1-R3), so a reader can size what is missing instead
      of guessing.

      Two further properties of the exact rows:
        - Author agents inside a group run in PARALLEL, so per-file minutes
          overlap and do not sum to the run's wall clock. R1's author minutes
          sum to 93.3 against a run wall clock of 84.
        - A unit can get more than one author agent, when a later round retries
          it (R1 retried W2jet/atree once; R3 retried BDK/fvs three times).
          Those are summed into one row and `agents` records how many.

  "apportioned" (csloop, R4-R11)
      csloop is a single agent looping over the whole transformation. Usage is
      recorded per loop PHASE (loop/metadata/loop_NNN_{author,review}.toml),
      never per file, so there is no per-file measurement to read and one has
      to be constructed. Each executed tool call is attributed to the settled
      units its arguments name (X_fi counts as X; a call naming k settled units
      splits 1/k to each), and the run's total USD and total minutes are then
      divided across units in proportion to those attributed calls.

      Consequences a caller must not paper over:
        - 67%-88% of csloop tool calls name no settled unit at all: builds,
          `jobrunner submit tests/mcfm`, roadmap queries, git, reading the plan.
          That overhead is spread proportionally rather than dropped, so run
          totals still reconcile exactly to the per-run tables. It is a
          modelling choice -- it assumes shared overhead scales with per-file
          work -- and `unattributed_tool_fraction` on the run record reports
          how much of the run was allocated that way.
        - Because USD and minutes are both proportional to the same attributed
          call counts, for csloop those three columns carry ONE measurement
          between them, not three. Only the tool-call column is data.
        - `tool_calls` is therefore not the same quantity across methods: for
          "exact" it is every call the unit's agent made, for "apportioned" it
          is only calls that name the unit. The apportioned number is smaller
          by construction and the two must not be compared directly.

WHICH UNITS GET A ROW
---------------------
Rows are emitted for the run's git-exact settled units (git_file_counts:
retired + shadowed), which is the same population every other table here
counts. ccworkflow additionally emits rows for author agents whose unit never
landed -- R1 spent two full agents on Mods/mod_qcdloop_c and Mods/types_mod and
finished neither -- flagged `settled = False`. That work was paid for and
dropping it would understate the harness's cost; including it in a per-settled
-file average would overstate the cost of the files that did land. So it is
carried, flagged, and left out of the averages.

Costs come from pricing.cost on the same rate cards and the same token fields
as the per-run tables, so a per-file column summed over a ccworkflow run's
author agents equals that run's author-phase USD exactly, and a csloop run's
per-file column sums to the run's whole USD exactly.
"""

import json
import re
from datetime import datetime
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import parse_csloop
from pricing import cost

# The AUTHOR prompt names its unit on the line after "transformation:". The
# path is always repo-relative (software/mcfm/src/<module>/<name>.<ext>).
AUTHOR_UNIT_RE = re.compile(
    r'AUTHOR agent for ONE unit of the "[^"]+"\s*\n?'
    r"transformation: `software/mcfm/src/([^`]+)`"
)

# Any source path inside a csloop tool call's arguments. Matched over the JSON
# of the whole args table rather than a named field, because the path can be a
# `path`, a `command` substring, a `pattern` or an `old_string`.
SOURCE_PATH_RE = re.compile(r"src/([A-Za-z0-9_]+)/([A-Za-z0-9_]+)\.(?:f90|f|cpp|hpp|F90)")

# Fortran mirror emitted alongside a translation; it is the same unit of work.
_MIRROR_SUFFIX = "_fi"

_TIMESTAMP_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def unit_id(path):
    """"W2jet/atree.f" -> "W2jet/atree", matching git_file_counts._unit_id."""
    lowered = path.lower()
    for ext in (".f90", ".f", ".cpp", ".hpp"):
        if lowered.endswith(ext):
            return path[: -len(ext)]
    return path


def _normalize_model(model):
    return model.replace("anthropic-", "") if model else model


def _first_user_text(record):
    content = record.get("message", {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                return block["text"]
    return ""


def _agent_unit(records):
    """The unit an AUTHOR transcript owns, or None for any other phase."""
    for record in records:
        if record.get("type") != "user":
            continue
        text = _first_user_text(record)
        if not text:
            continue
        match = AUTHOR_UNIT_RE.search(text)
        return unit_id(match.group(1)) if match else None
    return None


def _agent_totals(records):
    """Tokens, executed tool calls, model and elapsed minutes for one agent.

    Tool calls are counted as tool_result blocks, the same convention
    generate_graphs.total_tool_calls uses for ccworkflow, so a per-file count
    sums to the run's tool-call total rather than to a slightly different
    number of issued-but-unanswered calls.
    """
    totals = {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}
    tool_calls = 0
    model = None
    timestamps = []

    for record in records:
        stamp = record.get("timestamp")
        if stamp:
            timestamps.append(stamp)
        rtype = record.get("type")
        if rtype == "user":
            content = record.get("message", {}).get("content")
            if isinstance(content, list):
                tool_calls += sum(
                    1 for b in content
                    if isinstance(b, dict) and b.get("type") == "tool_result"
                )
        elif rtype == "assistant":
            message = record.get("message", {})
            model = message.get("model", model)
            usage = message.get("usage", {})
            totals["input"] += usage.get("input_tokens", 0)
            totals["output"] += usage.get("output_tokens", 0)
            totals["cache_write"] += usage.get("cache_creation_input_tokens", 0)
            totals["cache_read"] += usage.get("cache_read_input_tokens", 0)

    minutes = None
    if len(timestamps) >= 2:
        timestamps.sort()
        span = datetime.strptime(timestamps[-1], _TIMESTAMP_FMT) - datetime.strptime(
            timestamps[0], _TIMESTAMP_FMT
        )
        minutes = span.total_seconds() / 60.0

    return totals, tool_calls, _normalize_model(model), minutes


def _ccworkflow_per_file(run_dir, settled):
    """Exact per-unit rows from the run's AUTHOR subagent transcripts."""
    units = {}
    author_usd = 0.0

    for workflow_dir in sorted(run_dir.glob("workflow-wf_*")):
        for agent_path in sorted(workflow_dir.glob("agent-*.jsonl")):
            with open(agent_path) as fh:
                records = [json.loads(line) for line in fh if line.strip()]
            unit = _agent_unit(records)
            if unit is None:
                continue
            totals, tool_calls, model, minutes = _agent_totals(records)
            usd = cost(
                model,
                totals["input"],
                totals["output"],
                totals["cache_write"],
                totals["cache_read"],
            )
            author_usd += usd
            row = units.setdefault(unit, {
                "unit": unit,
                "settled": unit in settled,
                "model": model,
                "minutes": 0.0,
                "usd": 0.0,
                "tool_calls": 0,
                "agents": 0,
                "attributed_share": None,
            })
            row["minutes"] += minutes or 0.0
            row["usd"] += usd
            row["tool_calls"] += tool_calls
            row["agents"] += 1

    return units, {"author_usd": author_usd}


def _csloop_per_file(run_dir, settled):
    """Apportioned per-unit rows: run totals split by attributed tool calls."""
    metadata_dir = run_dir / "loop" / "metadata"
    phase_rows = parse_csloop.parse_metadata_dir(metadata_dir)

    run_usd = sum(
        cost(
            _normalize_model(row["model"]),
            row["input_tokens"],
            row["output_tokens"],
            row["cache_write_tokens"],
            row["cache_read_tokens"],
            row["cache_write_5m_tokens"],
            row["cache_write_1h_tokens"],
        )
        for row in phase_rows
    )
    run_minutes = sum(row["duration_s"] for row in phase_rows) / 60.0
    model = _normalize_model(phase_rows[0]["model"]) if phase_rows else None

    attributed = {}
    executed = 0
    unattributed = 0
    for loop_path in sorted(metadata_dir.glob("loop_*_*.toml")):
        with open(loop_path, "rb") as fh:
            loop_data = tomllib.load(fh)
        for call in loop_data.get("tools", []):
            executed += 1
            blob = json.dumps(call.get("args", {}))
            named = {
                f"{module}/{name}".replace(_MIRROR_SUFFIX, "")
                for module, name in SOURCE_PATH_RE.findall(blob)
            }
            hit = named & settled
            if not hit:
                unattributed += 1
                continue
            for unit in hit:
                attributed[unit] = attributed.get(unit, 0.0) + 1.0 / len(hit)

    total_attributed = sum(attributed.values())
    units = {}
    for unit in sorted(settled):
        calls = attributed.get(unit, 0.0)
        share = (calls / total_attributed) if total_attributed else 0.0
        units[unit] = {
            "unit": unit,
            "settled": True,
            "model": model,
            "minutes": run_minutes * share,
            "usd": run_usd * share,
            "tool_calls": calls,
            "agents": None,
            "attributed_share": share,
        }

    run_info = {
        "run_usd": run_usd,
        "run_minutes": run_minutes,
        "tool_calls_executed": executed,
        "unattributed_tool_fraction": (unattributed / executed) if executed else None,
    }
    return units, run_info


def per_file_effort(experiments_root, day, run_name, settled_units):
    """Per-unit effort for one run.

    `settled_units` is the run's git-exact unit list (retired + shadowed), or
    None for a run with no archival branch — in which case there is nothing to
    attribute effort to and this returns None, the same way every other
    git-exact measure reports such a run.

    Returns {"method": "exact"|"apportioned", "units": {unit: row}, "run": {...}}.
    """
    if settled_units is None:
        return None
    run_dir = Path(experiments_root) / day / run_name
    settled = set(settled_units)

    if any(run_dir.glob("workflow-wf_*")):
        units, run_info = _ccworkflow_per_file(run_dir, settled)
        method = "exact"
    else:
        units, run_info = _csloop_per_file(run_dir, settled)
        method = "apportioned"

    settled_rows = [r for r in units.values() if r["settled"]]
    run_info.update({
        "method": method,
        "units_with_rows": len(units),
        "settled_units_with_rows": len(settled_rows),
        "settled_units": len(settled),
        "attributed_usd": sum(r["usd"] for r in settled_rows),
        "attributed_minutes": sum(r["minutes"] for r in settled_rows),
    })
    return {"method": method, "units": units, "run": run_info}
