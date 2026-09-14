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

  "apportioned" (csloop and ccloop)
      Both are a single agent looping over the whole transformation, so neither
      records anything per file and one has to be constructed. csloop records
      usage per loop PHASE (loop/metadata/loop_NNN_{author,review}.toml);
      ccloop records it per loop AGENT (one Claude Code transcript per author
      or review agent, workflow-wf_*/agent-*.jsonl). Either way the unit of
      record is a whole phase of work over the whole Spec/Plan, never a file.
      Each executed tool call is attributed to the settled units its arguments
      name (X_fi counts as X; a call naming k settled units splits 1/k to
      each), and the run's total USD and total minutes are then divided across
      units in proportion to those attributed calls. ccloop additionally drops
      the harness's own structured-report calls before matching, since their
      "arguments" are a prose summary of the loop rather than work on a file --
      see _REPORTING_TOOLS, which also says what that does not change.

      Reading the same method off two harnesses is the point, not an accident:
      ccloop and csloop run the same design pattern on different baseline
      agents, so their per-file columns are built from the same construction
      and can be compared to each other directly — which the exact/apportioned
      pair below explicitly cannot be. What differs between them is only where
      the raw numbers were read from, and both are noted per row.

      One measurement does differ in kind. csloop's run minutes are the sum of
      its per-phase `duration_s`; ccloop's are the span from its first to its
      last transcript timestamp, the same quantity generate_graphs reports as
      its wall time. For a strictly sequential loop those are the same thing
      (ccloop never runs two agents at once), but the span also includes any
      harness time between agents, so ccloop's minutes are the slightly more
      inclusive of the two.

      Consequences a caller must not paper over:
        - Most tool calls name no settled unit at all: builds,
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

  "timed" (all three harnesses)
      Cost and elapsed time split across files by the MEASURED duration of the
      tool calls that name them, rather than by raw call count. Where the
      durations come from differs by harness, and every row and run record
      carries `duration_source` and `phases_covered` saying which:

        csloop      duration_source="measured", phases_covered="author".
                    Real per-call duration_ms out of logs/toolusage.toml.
        ccworkflow  duration_source="derived", phases_covered="all".
        ccloop      Durations reconstructed from transcript timestamps (see
                    _transcript_iterations) — a proxy that brackets harness
                    queueing as well as execution, over every phase rather
                    than the author phase alone.

      A "derived/all" total is therefore MORE complete than a "measured/author"
      one under the same heading, and the two must not be differenced as though
      the gap were method noise.

      For ccworkflow this is not a refinement of "exact" but a different
      measurement: "exact" covers the author phase only (46%-70% of run USD),
      and "timed" covers the whole run.

      The csloop version, for the same runs as "apportioned", is built from
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
landed (only it can: a ccloop or csloop agent works the whole Plan, so it has
no per-unit agent that could fail to land one) -- R1 spent two full agents on Mods/mod_qcdloop_c and Mods/types_mod and
finished neither -- flagged `settled = False`. That work was paid for and
dropping it would understate the harness's cost; including it in a per-settled
-file average would overstate the cost of the files that did land. So it is
carried, flagged, and left out of the averages.

Costs come from pricing.cost on the same rate cards and the same token fields
as the per-run tables, so a per-file column summed over a ccworkflow run's
author agents equals that run's author-phase USD exactly, and a csloop or
ccloop run's per-file column sums to the run's whole USD exactly.
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
from cc_usage import ACCUMULATED_FIELDS, cc_usage
from harness import CCLOOP, CCWORKFLOW, harness_of
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


def _cost_kwargs(totals):
    """_agent_totals output -> pricing.cost keyword arguments.

    Passes the recorded cache-write TTL split rather than leaving it for cost()
    to bill at its 5-minute fallback, so a per-file column is priced on exactly
    the same basis as the per-run tables (see cc_usage). Reasoning tokens are
    deliberately not passed: they are a breakdown of output_tokens, and adding
    them would bill the same tokens twice.
    """
    return {
        "input_tokens": totals["input_tokens"],
        "output_tokens": totals["output_tokens"],
        "cache_write_tokens": totals["cache_write_tokens"],
        "cache_read_tokens": totals["cache_read_tokens"],
        "cache_write_5m_tokens": totals["cache_write_5m_tokens"],
        "cache_write_1h_tokens": totals["cache_write_1h_tokens"],
    }


def _agent_totals(records):
    """Tokens, executed tool calls, model and elapsed minutes for one agent.

    Tool calls are counted as tool_result blocks, the same convention
    generate_graphs.total_tool_calls uses for ccworkflow, so a per-file count
    sums to the run's tool-call total rather than to a slightly different
    number of issued-but-unanswered calls.
    """
    totals = {f: 0 for f in ACCUMULATED_FIELDS}
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
            usage = cc_usage(message)
            for field in ACCUMULATED_FIELDS:
                totals[field] += usage[field]

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
            usd = cost(model, **_cost_kwargs(totals))
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


# The workflow harness's structured-return channel, not a tool that touches
# the repository: an agent calls it once at the end of a phase to hand its
# report back, and its "arguments" are that report's prose -- a status, a
# narrative plan, quoted build output. Excluded from per-file ATTRIBUTION
# because that prose names whatever files the loop worked on, so counting it
# measures what the agent chose to write about rather than effort spent on a
# file. How much it matters depends on how much the run's loops spent
# summarising, and the corpus has both extremes. In
# 09-11-2026/ccworkflow-loop-opus-5 (out of the figure set since 2026-09-13,
# still parsed here) 10 of the 23 calls naming a settled unit were these
# reports, and they alone would have handed W2jet/w2jetsq -- the unit its last
# summaries kept discussing -- roughly half the run. In the in-scope
# 09-12-2026 run only 2 of 14 are, and dropping them moves no unit's share by
# more than about two points. The rule is kept for the first case; the second
# is why it should not be sold as a large correction in general.
#
# csloop has no equivalent -- its loop report is not a tool call at all -- so
# leaving these in would also break the like-for-like comparison that is the
# whole point of the two harnesses sharing this method.
#
# Two things this deliberately does NOT change:
#   - Run-level tool-call totals (generate_graphs.total_tool_calls) still count
#     it, for every harness. It is a real executed call and ccworkflow's
#     published counts include it; the exclusion is about attribution only.
#   - The ccworkflow "exact" method, which attributes a whole author agent's
#     transcript to its one unit and never matches per-call arguments.
_REPORTING_TOOLS = frozenset({"StructuredOutput"})


def _ccloop_agents(run_dir):
    """[(records, [args of each attributable executed tool call])] per agent.

    "Executed" means a `tool_use` block that came back with a matching
    `tool_result`, so the count agrees with generate_graphs.total_tool_calls
    (which counts tool_result blocks) rather than with the number of calls the
    model issued — the last agent of an interrupted run can issue one that is
    never answered. Calls to a tool in _REPORTING_TOOLS are dropped here; see
    that constant for why.
    """
    out = []
    for workflow_dir in sorted(run_dir.glob("workflow-wf_*")):
        for agent_path in sorted(workflow_dir.glob("agent-*.jsonl")):
            with open(agent_path) as fh:
                records = [json.loads(line) for line in fh if line.strip()]

            issued = {}
            answered = []
            for record in records:
                rtype = record.get("type")
                content = record.get("message", {}).get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if rtype == "assistant" and block.get("type") == "tool_use":
                        issued[block.get("id")] = (block.get("name"),
                                                   block.get("input", {}) or {})
                    elif rtype == "user" and block.get("type") == "tool_result":
                        call = issued.get(block.get("tool_use_id"))
                        if call is None:
                            continue
                        name, args = call
                        if name in _REPORTING_TOOLS:
                            continue
                        answered.append(args)
            out.append((records, answered))
    return out


def _ccloop_per_file(run_dir, settled):
    """Apportioned per-unit rows for a ccloop run.

    Same construction as _csloop_per_file — run totals split across units in
    proportion to the executed tool calls whose arguments name them — reading
    the Claude Code transcripts instead of CodeScribe's loop metadata. See the
    module docstring's "apportioned" entry for what that shares with csloop and
    the one place (run minutes) where the two inputs differ.
    """
    run_usd = 0.0
    timestamps = []
    models = {}
    attributed = {}
    executed = 0
    unattributed = 0

    for records, calls in _ccloop_agents(run_dir):
        totals, _tool_calls, model, _minutes = _agent_totals(records)
        if model is None:
            continue
        run_usd += cost(model, **_cost_kwargs(totals))
        models[model] = models.get(model, 0) + 1
        timestamps.extend(r["timestamp"] for r in records if r.get("timestamp"))

        for args in calls:
            executed += 1
            named = {
                f"{module}/{name}".replace(_MIRROR_SUFFIX, "")
                for module, name in SOURCE_PATH_RE.findall(json.dumps(args))
            }
            hit = named & settled
            if not hit:
                unattributed += 1
                continue
            for unit in hit:
                attributed[unit] = attributed.get(unit, 0.0) + 1.0 / len(hit)

    # First-to-last transcript timestamp, matching the run's reported wall time.
    run_minutes = 0.0
    if len(timestamps) >= 2:
        timestamps.sort()
        span = datetime.strptime(timestamps[-1], _TIMESTAMP_FMT) - datetime.strptime(
            timestamps[0], _TIMESTAMP_FMT
        )
        run_minutes = span.total_seconds() / 60.0

    # A ccloop run drives every phase with one model, so "the run's model" is
    # well defined; max() rather than [0] in case a phase override ever puts a
    # second one in the archive, in which case the dominant one is reported and
    # the per-run cost above still bills each agent at its own rate.
    model = max(models, key=models.get) if models else None

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
        # Excludes the reporting calls dropped by _ccloop_agents, so this is
        # the count the attribution actually ran over -- slightly below the
        # run-level tool-call total in the per-run tables, which counts them.
        "tool_calls_executed": executed,
        "unattributed_tool_fraction": (unattributed / executed) if executed else None,
    }
    return units, run_info


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
        # The cost of the phases this method could not measure at all, as
        # opposed to iterations it measured but could not attribute. For csloop
        # that is the whole review phase; a transcript harness has no such
        # phase and reports zero.
        "unmeasured_usd": review_usd,
        "unmeasured_minutes": review_minutes,
        "unattributed_fraction": (unattributed_usd / run_usd) if run_usd else None,
        "duration_source": "measured",
        "phases_covered": "author",
    }
    return units, run_info


def _transcript_iterations(records, settled):
    """Decompose one Claude Code transcript into timed iterations.

    Yields (iter_ms, usage, model, weights, calls_hit) per assistant message,
    where `weights` maps a settled unit to the milliseconds of tool time this
    iteration spent naming it.

    THE CLOCK. CodeScribe measures a tool call around `tool.run(args)` and a
    model response around the provider call, and writes both as `duration_ms`.
    A Claude Code transcript has no durations, but it timestamps every record,
    so the same decomposition is recovered from the gaps:

        model_ms  = ts(assistant)    - ts(end of the previous iteration)
        tool_ms   = ts(tool_result)  - ts(assistant that issued the call)

    Walking the records in order and carrying `last_ts` forward means the two
    together partition the transcript's whole span with no gap and no overlap,
    so an agent's iteration times sum to its wall clock. It is a PROXY, not
    CodeScribe's measurement: each interval brackets harness queueing and
    delivery as well as the work itself, which inflates short calls most (the
    corpus median is 57ms, where much of that is not execution). It is reported
    as `duration_source = "derived"` for exactly that reason.
    """
    result_ts = {}
    for record in records:
        if record.get("type") != "user" or not record.get("timestamp"):
            continue
        content = record.get("message", {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                result_ts[block.get("tool_use_id")] = record["timestamp"]

    stamped = [r.get("timestamp") for r in records if r.get("timestamp")]
    if not stamped:
        return
    last_ts = min(stamped)

    for record in records:
        if record.get("type") != "assistant":
            continue
        ts = record.get("timestamp")
        if not ts:
            continue
        message = record.get("message", {})
        model_ms = _ms_between(last_ts, ts)
        last_ts = ts

        weights, calls_hit = {}, {}
        tool_ms_total = 0.0
        for block in message.get("content") or []:
            if not (isinstance(block, dict) and block.get("type") == "tool_use"):
                continue
            end_ts = result_ts.get(block.get("id"))
            if end_ts is None:
                continue  # issued but never answered — no duration, no effect
            duration = _ms_between(ts, end_ts)
            tool_ms_total += duration
            if end_ts > last_ts:
                last_ts = end_ts
            # Same exclusion the apportioned method makes: the harness's own
            # structured-report call names whatever the loop wrote ABOUT.
            if block.get("name") in _REPORTING_TOOLS:
                continue
            named = {
                f"{module}/{name}".replace(_MIRROR_SUFFIX, "")
                for module, name in SOURCE_PATH_RE.findall(json.dumps(block.get("input", {}) or {}))
            }
            hit = named & settled
            for unit in hit:
                weights[unit] = weights.get(unit, 0.0) + duration / len(hit)
                calls_hit[unit] = calls_hit.get(unit, 0.0) + 1.0 / len(hit)

        yield (
            model_ms + tool_ms_total,
            cc_usage(message),
            _normalize_model(message.get("model")),
            weights,
            calls_hit,
        )


def _ms_between(start_ts, end_ts):
    """Milliseconds between two transcript timestamps, floored at zero."""
    try:
        delta = datetime.strptime(end_ts, _TIMESTAMP_FMT) - datetime.strptime(
            start_ts, _TIMESTAMP_FMT
        )
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, delta.total_seconds() * 1000.0)


def _transcript_per_file_timed(run_dir, settled):
    """Timed per-unit rows for a Claude Code run (ccworkflow or ccloop).

    Same shape as _csloop_per_file_timed: each iteration's cost and elapsed time
    are split across whatever settled files that iteration's own tool calls
    name, weighted by how long each call took, and an iteration naming nothing
    joins an unattributed pool spread by measured share.

    Two ways this differs from the csloop version, both carried on the run
    record rather than left for a reader to discover:
      - duration_source = "derived". See _transcript_iterations.
      - phases_covered = "all". logs/toolusage.toml records only csloop's author
        phase, so its timed numbers exclude review entirely; a transcript run
        has every phase on disk, so triage, integrate and metadata are all in
        here. That makes a Claude Code timed total MORE complete than a csloop
        one under the same column heading, which is why the heading is
        qualified wherever both are printed.

    For ccworkflow this is a genuinely new measurement rather than a tighter
    one: its "exact" method covers the author phase only (46%-70% of run USD),
    and this covers the rest. The two are not interchangeable and a table
    showing both must say which is which.
    """
    attributed_ms, attributed_usd, attributed_calls = {}, {}, {}
    unattributed_ms = unattributed_usd = 0.0
    models = {}

    for workflow_dir in sorted(run_dir.glob("workflow-wf_*")):
        for agent_path in sorted(workflow_dir.glob("agent-*.jsonl")):
            with open(agent_path) as fh:
                records = [json.loads(line) for line in fh if line.strip()]

            for iter_ms, usage, model, weights, calls_hit in _transcript_iterations(
                records, settled
            ):
                if model is None:
                    continue
                models[model] = models.get(model, 0) + 1
                iter_usd = cost(model, **_cost_kwargs(usage))

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

    if not models:
        return None
    model = max(models, key=models.get)

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
    run_info = {
        "run_usd": run_usd,
        # Agents inside a ccworkflow group run in PARALLEL, so these iteration
        # times overlap and sum to more than the run's wall clock — the same
        # property the exact method already reports for its per-file minutes.
        # ccloop is strictly sequential and does not have it.
        "run_minutes": (sum(attributed_ms.values()) + unattributed_ms) / 60000.0,
        "unmeasured_usd": 0.0,
        "unmeasured_minutes": 0.0,
        "unattributed_fraction": (unattributed_usd / run_usd) if run_usd else None,
        "duration_source": "derived",
        "phases_covered": "all",
    }
    return units, run_info


def per_file_effort_timed(experiments_root, day, run_name, settled_units):
    """Timed per-unit effort for one csloop run (see module docstring).

    Available for every harness, from a different source each time, and the
    run record says which: csloop reads real durations out of
    logs/toolusage.toml (`duration_source = "measured"`, author phase only),
    while ccworkflow and ccloop derive them from transcript timestamps
    (`duration_source = "derived"`, every phase). Those two are not the same
    measurement and a table printing both must qualify the heading.

    None for a run with no settled units, for a run with no parseable
    transcript, or for a csloop run whose logs/toolusage.toml is missing or
    fails the structural sanity check against loop/metadata. Callers must treat
    None as "not available for this run", the same convention per_file_effort()
    uses for a run with no archival branch.
    """
    if settled_units is None:
        return None
    run_dir = Path(experiments_root) / day / run_name
    if harness_of(run_name) in (CCWORKFLOW, CCLOOP):
        result = _transcript_per_file_timed(run_dir, set(settled_units))
    else:
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

    Returns {"method": "exact"|"apportioned", "units": {unit: row}, "run": {...}}
    — "exact" for ccworkflow, "apportioned" for csloop and ccloop alike (the
    same construction over different archives; see the module docstring).
    """
    if settled_units is None:
        return None
    run_dir = Path(experiments_root) / day / run_name
    settled = set(settled_units)

    # Dispatch on the harness, not on the presence of workflow-wf_* — ccloop
    # archives into that same directory layout but has no per-unit author
    # agent for the exact method to read, so keying off the layout would give
    # it an "exact" record with no rows in it.
    harness = harness_of(run_name)
    if harness == CCWORKFLOW:
        units, run_info = _ccworkflow_per_file(run_dir, settled)
        method = "exact"
    elif harness == CCLOOP:
        units, run_info = _ccloop_per_file(run_dir, settled)
        method = "apportioned"
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
