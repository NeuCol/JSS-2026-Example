"""Attribute wall time, USD and tool calls to the INDIVIDUAL translated files
of a run, rather than to the run as a whole.

Everything else in analysis/ divides a run total by files settled (see
generate_graphs.derived_metrics). That is the right normalization for comparing
runs, but it cannot answer "what did *this* file cost", and it hides the fact
that the two harnesses record effort at completely different granularities.
This module answers the per-file question and is explicit about the fact that
only one of the two harnesses can answer it exactly.

THREE METHODS, AND THEY ARE NOT INTERCHANGEABLE
------------------------------------------------
`method` is on every row this module emits, and any table or plot that mixes
them must say so.

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

  "timed" (csloop, same runs as "apportioned")
      A tighter apportionment for the same harness, built from
      logs/toolusage.toml instead of the loop-phase totals in
      loop/metadata/loop_NNN_*.toml. That file is the harness's raw event log
      -- one [[event]] block per iteration_start/model_response/tool_start/
      tool_end -- and it carries two things the phase totals don't: the real
      duration_ms of every individual tool call, and the real per-iteration
      token usage behind every model_response. "apportioned" splits a whole
      PHASE's total duration/USD across files by raw call count, i.e. it
      treats a `read` and a full test-suite `bash` call as equally expensive.
      "timed" instead measures each tool call's own duration and each
      iteration's own tokens, and splits only that iteration's cost across
      whatever settled files its own tool calls name.

      What "timed" can measure and what it still can't:
        - logs/toolusage.toml records the AUTHOR phase only -- verified
          against three separate runs by matching each toolusage.toml run_id's
          iteration and tool-call counts, in order, against the run's
          loop_NNN_author.toml files; review-phase tool calls never appear in
          it at all. This is a small loss: review tool calls almost never
          name a settled file (0-1 of 9-14 calls per phase, versus 54%-62%
          for author), so the review phase was already mostly overhead by the
          apportioned method's own accounting.
        - Within an author phase, an iteration's tool calls are timed exactly,
          but the model's "thinking" time between them (its model_response
          duration and tokens -- the majority of a phase's wall clock, 83% in
          one run checked) is still not tied to one file. It is split across
          whatever files that SAME iteration's own tool calls name, weighted
          by each call's measured duration -- iteration-level apportionment
          with real weights, rather than whole-phase apportionment with
          assumed-equal weights.
        - An iteration whose tool calls name no settled file, plus the run's
          whole review phase, are folded into one unattributed pool and
          spread across files in proportion to each file's measured share --
          the same "spread proportionally" policy "apportioned" already uses,
          just driven by a better per-file weight. `unattributed_fraction` on
          the run record reports how much of the run's USD was spread this
          way rather than measured.
        - Because a run's "apportioned" and "timed" totals both reconcile
          exactly to the same run USD and minutes, the two methods will never
          disagree on a run's grand total -- only on how that total is split
          across files. A table showing both for the same run is there to
          show that split changing, not a discrepancy to explain away.

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


def _normalize_iteration_usage(usage):
    """One model_response event's raw provider usage -> the field names
    parse_csloop.parse_metadata_dir already normalizes phase totals to.

    Anthropic responses carry input_tokens/output_tokens/
    cache_creation_input_tokens/cache_read_input_tokens (and, when the
    provider reports the TTL split, cache_creation_{5m,1h}_input_tokens);
    OpenAI-compatible responses carry prompt_tokens/completion_tokens
    instead. Reasoning tokens are read by parse_csloop but never billed
    anywhere in this codebase, so they are dropped here too.
    """
    return {
        "input": usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0,
        "output": usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0,
        "cache_write": usage.get("cache_creation_input_tokens", 0) or 0,
        "cache_read": usage.get("cache_read_input_tokens", 0) or 0,
        "cache_write_5m": usage.get("cache_creation_5m_input_tokens", 0) or 0,
        "cache_write_1h": usage.get("cache_creation_1h_input_tokens", 0) or 0,
    }


def _group_iterations(events):
    """Bucket one author-phase run_id's toolusage events by iteration.

    Returns a list, in iteration order, of {"model_response": event|None,
    "tools": [(tool_start_event, tool_end_event), ...]}. tool_start/tool_end
    are paired by simple arrival order -- verified strictly sequential and
    non-overlapping (never two calls in flight at once) in every archive
    checked, since the loop issues one tool call at a time.
    """
    iterations = []
    current = None
    pending_start = None
    for event in events:
        etype = event.get("event")
        if etype == "iteration_start":
            current = {"model_response": None, "tools": []}
            iterations.append(current)
        elif current is None:
            continue
        elif etype == "model_response":
            current["model_response"] = event
        elif etype == "tool_start":
            pending_start = event
        elif etype == "tool_end":
            current["tools"].append((pending_start, event))
            pending_start = None
    return iterations


def _csloop_per_file_timed(run_dir, settled):
    """Timed per-unit rows: author-phase iterations measured from
    logs/toolusage.toml (real per-call duration, real per-iteration tokens),
    review phase and any iteration naming no settled file spread by measured
    share. Returns None if toolusage.toml is missing, or if its run/iteration/
    tool-call structure doesn't line up with loop/metadata -- see the module
    docstring's "timed" method for what that structure is and why a mismatch
    means "don't trust this" rather than "drop the mismatched part".
    """
    toolusage_path = run_dir / "logs" / "toolusage.toml"
    metadata_dir = run_dir / "loop" / "metadata"
    manifest_path = metadata_dir / "manifest.toml"
    if not toolusage_path.exists() or not manifest_path.exists():
        return None

    with open(manifest_path, "rb") as fh:
        manifest_run = tomllib.load(fh).get("run", {})
    fallback_model = manifest_run.get("model", "unknown")
    ttl_aware = any(
        key in manifest_run for key in parse_csloop._TTL_AWARE_MANIFEST_KEYS
    )
    loop_dir = metadata_dir.parent

    author_phases = []
    for path in sorted(metadata_dir.glob("loop_*_author.toml")):
        with open(path, "rb") as fh:
            author_phases.append(tomllib.load(fh))
    if not author_phases:
        return None

    events_by_run = {}
    run_id_order = []
    for event in parse_csloop.parse_toolusage(toolusage_path):
        rid = event.get("run_id")
        if rid is None:
            continue
        if rid not in events_by_run:
            events_by_run[rid] = []
            run_id_order.append(rid)
        events_by_run[rid].append(event)

    if len(run_id_order) != len(author_phases):
        print(
            f"  WARNING: {run_dir}: toolusage.toml has {len(run_id_order)} run(s) but "
            f"loop/metadata has {len(author_phases)} author phase(s) -- skipping timed method"
        )
        return None

    model = _normalize_model(str(fallback_model))
    attributed_ms = {}
    attributed_usd = {}
    attributed_calls = {}
    unattributed_ms = 0.0
    unattributed_usd = 0.0

    for run_id, phase in zip(run_id_order, author_phases):
        phase_events = events_by_run[run_id]
        expected_calls = len(phase.get("tools", []))
        # Count by tool_end, not tool_start: at least one archive logs a
        # tool_start that never arrives (its tool_end fires twice instead,
        # back to back, for what loop/metadata still records as a single
        # call) -- tool_end count is the one that reconciles with it exactly
        # in every case checked. _group_iterations pairs the resulting
        # orphaned tool_end with a null start, which correctly falls out as
        # unnamed (no args to match a file against) rather than mis-attributed.
        actual_calls = sum(1 for e in phase_events if e.get("event") == "tool_end")
        if actual_calls != expected_calls:
            print(
                f"  WARNING: {run_dir}: toolusage.toml run {run_id} has {actual_calls} "
                f"tool_end event(s), matching author phase has {expected_calls} tool "
                "call(s) -- skipping timed method"
            )
            return None

        row_model = _normalize_model(str(phase.get("model", fallback_model)))
        basis = parse_csloop._input_basis(loop_dir, row_model, ttl_aware)

        for iteration in _group_iterations(phase_events):
            mr = iteration["model_response"]
            usage = _normalize_iteration_usage(mr.get("usage", {}) if mr else {})
            model_ms = mr.get("duration_ms", 0.0) if mr else 0.0

            net_input = usage["input"]
            if basis == "gross":
                net_input = max(0, net_input - usage["cache_read"] - usage["cache_write"])
            iter_usd = cost(
                row_model,
                net_input,
                usage["output"],
                usage["cache_write"],
                usage["cache_read"],
                usage["cache_write_5m"],
                usage["cache_write_1h"],
            )

            weights = {}
            calls_hit = {}
            tool_ms_total = 0.0
            for start, end in iteration["tools"]:
                tool_ms_total += end.get("duration_ms", 0.0) if end else 0.0
                blob = json.dumps(start.get("args", {}) if start else {})
                named = {
                    f"{module}/{name}".replace(_MIRROR_SUFFIX, "")
                    for module, name in SOURCE_PATH_RE.findall(blob)
                }
                hit = named & settled
                if not hit:
                    continue
                duration = end.get("duration_ms", 0.0) if end else 0.0
                for unit in hit:
                    weights[unit] = weights.get(unit, 0.0) + duration / len(hit)
                    calls_hit[unit] = calls_hit.get(unit, 0.0) + 1.0 / len(hit)

            iter_ms = model_ms + tool_ms_total
            total_weight = sum(weights.values())
            if total_weight <= 0:
                unattributed_ms += iter_ms
                unattributed_usd += iter_usd
                continue
            for unit, weight in weights.items():
                share = weight / total_weight
                attributed_ms[unit] = attributed_ms.get(unit, 0.0) + iter_ms * share
                attributed_usd[unit] = attributed_usd.get(unit, 0.0) + iter_usd * share
            for unit, calls in calls_hit.items():
                attributed_calls[unit] = attributed_calls.get(unit, 0.0) + calls

    # Review phase never appears in logs/toolusage.toml (see module docstring),
    # so its whole cost/time joins the same unattributed pool that an author
    # iteration naming no settled file already feeds.
    review_usd = 0.0
    review_minutes = 0.0
    for row in parse_csloop.parse_metadata_dir(metadata_dir):
        if row["phase"] != "review":
            continue
        review_usd += cost(
            _normalize_model(row["model"]),
            row["input_tokens"],
            row["output_tokens"],
            row["cache_write_tokens"],
            row["cache_read_tokens"],
            row["cache_write_5m_tokens"],
            row["cache_write_1h_tokens"],
        )
        review_minutes += row["duration_s"] / 60.0
    unattributed_usd += review_usd
    unattributed_ms += review_minutes * 60000.0

    total_attributed_ms = sum(attributed_ms.values())
    units = {}
    for unit in sorted(settled):
        share = (attributed_ms.get(unit, 0.0) / total_attributed_ms) if total_attributed_ms else 0.0
        units[unit] = {
            "unit": unit,
            "settled": True,
            "model": model,
            "minutes": (attributed_ms.get(unit, 0.0) + unattributed_ms * share) / 60000.0,
            "usd": attributed_usd.get(unit, 0.0) + unattributed_usd * share,
            "tool_calls": attributed_calls.get(unit, 0.0),
            "agents": None,
            "attributed_share": share,
        }

    run_usd = sum(attributed_usd.values()) + unattributed_usd
    run_minutes = (sum(attributed_ms.values()) + unattributed_ms) / 60000.0
    run_info = {
        "run_usd": run_usd,
        "run_minutes": run_minutes,
        "review_usd": review_usd,
        "review_minutes": review_minutes,
        "unattributed_fraction": (unattributed_usd / run_usd) if run_usd else None,
    }
    return units, run_info


def per_file_effort_timed(experiments_root, day, run_name, settled_units):
    """Timed per-unit effort for one csloop run (see module docstring).

    None for a ccworkflow run (already exact -- no apportionment to tighten),
    a run with no settled units, or a csloop run whose logs/toolusage.toml is
    missing or fails the structural sanity check against loop/metadata.
    Callers must treat None as "not available for this run", the same
    convention per_file_effort() uses for a run with no archival branch.
    """
    if settled_units is None:
        return None
    run_dir = Path(experiments_root) / day / run_name
    if any(run_dir.glob("workflow-wf_*")):
        return None
    result = _csloop_per_file_timed(run_dir, set(settled_units))
    if result is None:
        return None
    units, run_info = result
    settled_rows = [r for r in units.values() if r["settled"]]
    run_info.update({
        "method": "timed",
        "settled_units_with_rows": len(settled_rows),
        "settled_units": len(settled_units),
        "attributed_usd": sum(r["usd"] for r in settled_rows),
        "attributed_minutes": sum(r["minutes"] for r in settled_rows),
    })
    return {"method": "timed", "units": units, "run": run_info}


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
