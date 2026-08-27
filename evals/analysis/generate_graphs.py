#!/usr/bin/env python3.10
"""Generate the paper figures + summary tables for the 08-11-2026 → 08-26-2026
evaluation of the mcfm-translate transformation.

Runs covered (see RUNS below for the authoritative list): ccworkflow (sonnet-5
author / opus-5 integrate) vs. csloop across opus-5, sonnet-5, Kimi K3 and the
two oaic-gpt56 variants (sol / terra). Only
the layouts written from 08-11-2026 onward are parseable — the 07-24/07-25-2026
run directories use the older on-disk layout and are deliberately out of scope.

Three further runs are excluded from RUNS on data-quality grounds, not because
their archives are unreadable:
  - csloop opus-5 (08-11) and csloop opus-5 (run2, 08-12) logged no model
    reasoning text at all in logs/toolusage.toml (zero model_reasoning entries,
    against 78-136 for every other Anthropic run), so they cannot be compared
    against the runs that did.
  - csloop Kimi K3 (08-14) has no archival git branch in this clone, so it has
    no git-exact files-settled count and no per-file metric of any kind.
  - ccworkflow opus-5 (single session, 08-13) and csloop sonnet-5 +reasoning
    (08-12) were withdrawn from the comparison. Both archives are intact and
    still parse; nothing here judges them unusable.
Dropping the opus-5 run2 arm also retires the "+reasoning vs. run2" figure that
used to sit at panels (c)/(d): its control condition is one of the excluded
runs, and no surviving run pairs against the +reasoning arm.

"Files settled" throughout is the exact count from git_file_counts.py (the
software/mcfm submodule branch for each run), not the agent's own in-loop
checklist in agent_log.md — the two can disagree (see git_file_counts.py's
docstring), and the submodule diff is ground truth. Two consequences visible in
the output, both deliberate:
  - a run whose archival branch never reached this clone has *no* git-exact
    count. That is None, not zero, and is drawn as an explicit "n/a (no branch)"
    everywhere rather than as an empty bar.
  - a round that adds a .cpp beside a *retained* Fortran original retires no
    file, so it can settle 4 units by its own checklist and 1 by git. A run in
    that position gets correspondingly extreme per-file metrics, and the
    per-file panels clip it with its true value printed (see capped_limit).

Run with: python3.10 analysis/generate_graphs.py
(Needs Python 3.10+ for tomllib, or `pip install tomli` on older Pythons.)

Reads only from experiments/ (read-only). Writes, under analysis/figures/:
  fig1_cost_and_cache.png        - standalone, compact
  fig3_coverage.png              - standalone, compact
  fig4_wall_time.png             - standalone, compact
  fig5_tool_calls_per_file.png   - standalone, compact
  fig_combined.png               - the six panels used as the paper's single figure
(the fig2 slot held the retired reasoning comparison; the remaining files keep
their names so existing \includegraphics paths in the paper still resolve)
and analysis/summary_tables.md (the numeric source of truth behind every panel).

fig_combined.png deliberately does NOT mirror the summary table column-for-
column. A table already reports per-run totals better than a bar chart can, so
the combined figure carries only what a table reads poorly: normalized cost and
throughput, the cost/speed frontier, the cost split by model tier, and the
input-token composition that explains the cache-share differences. One panel
that earlier versions carried was dropped on purpose:
  - self-reported correctness: 272/272 for every run that reported at all,
    including a run that translated zero files (the suite passes trivially when
    nothing changed), so the bar chart was flat and the metric near-vacuous.

Every plotting function below draws onto an Axes it's given (draw_*), so the
same code builds both the small standalone figures and the one combined
figure — no logic is duplicated between them.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.insert(0, str(Path(__file__).parent))

from parse_ccworkflow import parse_all_ccworkflow
from parse_csloop import parse_all_csloop
from parse_coverage import coverage_for_run
from pricing import cost, PRICING
from git_file_counts import translated_file_count, translated_file_units, module_of
from parse_roadmap import (fork_point_roadmap, ready_pool, post_run_ready,
                           roadmap_is_post_run)

REPO_ROOT = Path(__file__).parent.parent
EXPERIMENTS = REPO_ROOT / "experiments"
FIGURES_DIR = Path(__file__).parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Style — validated default palette from the dataviz skill (references/palette.md)
# ---------------------------------------------------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

CAT = {
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "magenta": "#e87ba4",
    "green": "#008300",
    "violet": "#4a3aa7",
    "red": "#e34948",
}
STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

FONT = "DejaVu Sans"  # pinned to one concrete font (not a fallback list) so every
                      # text element in every figure — titles included — renders
                      # in exactly the same typeface.

TITLE_SIZE = 9.5
TICK_SIZE = 8
LABEL_SIZE = 8.3
LEGEND_SIZE = 7.3
ANNOT_SIZE = 7.3
SUPTITLE_SIZE = 12.5
CAPTION_SIZE = 7.3

plt.rcParams.update(
    {
        "font.family": FONT,
        "font.size": LABEL_SIZE,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK_SECONDARY,
        "axes.labelsize": LABEL_SIZE,
        "axes.titlesize": TITLE_SIZE,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": TICK_SIZE,
        "ytick.labelsize": TICK_SIZE,
        "legend.fontsize": LEGEND_SIZE,
        "grid.color": GRID,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
    }
)

# ---------------------------------------------------------------------------
# Run identity / labeling — 08-11-2026 through 08-26-2026
#
# One ordered registry of (day, run_dir, code, label); KEYS, RUN_LABELS,
# RUN_CODES and the figure captions are all derived from it, so adding a run is
# a one-line change here and nowhere else.
#
# The codes are stable identifiers quoted by the paper text: APPEND new runs,
# never renumber the existing ones. Runs are grouped by day and, within a day,
# by model family rather than by wall-clock start, so neighbouring bars compare
# like with like.
# ---------------------------------------------------------------------------
RUNS = [
    ("08-11-2026", "csloop-opus-5-with-reasoning", "R1", "csloop opus-5 +reasoning (08-11)"),
    ("08-12-2026", "ccworkflow-sonnet-5-opus-5-integrate", "R2",
     "ccworkflow (sonnet-5 author, opus-5 integrate)"),
    ("08-12-2026", "ccworkflow-sonnet-5-opus-5-integrate-run2", "R3",
     "ccworkflow (sonnet-5 author, opus-5 integrate, run2)"),
    ("08-12-2026", "codescribe-opus-5-with-reasoning", "R4", "csloop opus-5 +reasoning (08-12)"),
    ("08-12-2026", "codescribe-sonnet-5-with-reasoning-run2", "R5",
     "csloop sonnet-5 +reasoning (run2, 08-12)"),
    ("08-12-2026", "codescribe-kimi-k3-5", "R6", "csloop Kimi K3 (08-12)"),
    ("08-26-2026", "codescribe-opus-5", "R7", "csloop opus-5 (08-26)"),
    ("08-26-2026", "codescribe-opus-5-run2", "R12", "csloop opus-5 (run2, 08-26)"),
    ("08-26-2026", "codescribe-sonnet-5", "R8", "csloop sonnet-5 (08-26)"),
    ("08-26-2026", "codescribe-oaic-gpt56sol", "R9", "csloop oaic-gpt56sol (08-26)"),
    ("08-26-2026", "codescribe-oaic-gpt56sol-run2", "R10", "csloop oaic-gpt56sol (run2, 08-26)"),
    ("08-26-2026", "codescribe-oaic-gpt56terra", "R11", "csloop oaic-gpt56terra (08-26)"),
]

KEYS = [(day, run_name) for day, run_name, _, _ in RUNS]
RUN_LABELS = {(day, run_name): label for day, run_name, _, label in RUNS}
# Short x-axis codes — keeps bars legible even in the compact standalone
# figures; each figure captions the full mapping once, below the plot.
RUN_CODES = {(day, run_name): code for day, run_name, code, _ in RUNS}


def run_code_caption(fig_width_in, fontsize=None):
    """The code→configuration mapping, wrapped to the figure it sits under.

    Returned as a list of lines rather than one string: at 16 runs the mapping
    is far wider than any figure, and a single un-wrapped line makes
    `bbox_inches="tight"` grow the saved canvas to the width of the *text*,
    which strands the panels in the middle of a very wide image.
    """
    import textwrap

    fontsize = fontsize or CAPTION_SIZE
    text = "  |  ".join(f"{code} = {label}" for _, _, code, label in RUNS)
    # ~0.52 em per character is the measured average for DejaVu Sans at these
    # sizes; close enough to keep the wrapped text inside the axes width.
    chars = max(40, int(fig_width_in * 72 / (0.52 * fontsize)))
    return textwrap.wrap(text, chars)


# Every Anthropic csloop run in this table ran with adaptive thinking active:
# Opus 5 and Sonnet 5 both think by default when the thinking parameter is
# omitted, so none of these runs is a reasoning-OFF arm. "+reasoning" in a label
# therefore means only that CODESCRIBE_AGENT_REASONING was set explicitly for
# that run, and the runs without the suffix are not its control.
REASONING_NOTE = (
    "All Anthropic csloop runs think adaptively (on by default); \"+reasoning\" marks runs that "
    "set the flag explicitly, not an ON/OFF pair."
)
EXCLUDED_NOTE = (
    "Excluded: csloop opus-5 (08-11) and (run2, 08-12) logged no model reasoning text; "
    "csloop Kimi K3 (08-14) has no archival git branch; ccworkflow opus-5 (single session, "
    "08-13) and csloop sonnet-5 +reasoning (08-12) withdrawn from the comparison."
)
UNPRICED_NOTE = (
    "Kimi K3 and the oaic-gpt56 deployments are not Anthropic models and carry no rate card, so "
    "they are excluded from every USD figure."
)

MODEL_COLOR = {
    "claude-sonnet-5": CAT["blue"],
    "claude-opus-5": CAT["violet"],
}
UNPRICED_COLOR = MUTED


def normalize_model(model):
    return model.replace("anthropic-", "") if model else model


def run_key(day, run_name):
    return (day, run_name)


def _title(text, letter):
    return f"{letter} {text}" if letter else text


# ---------------------------------------------------------------------------
# Shared bar-panel mechanics
#
# Sixteen runs no longer fit the "one horizontal label per bar" layout the
# nine-run version used: both the tick labels and the value annotations are set
# vertically now, which costs nothing in legibility for three-character codes
# and keeps every panel readable at the printed size.
# ---------------------------------------------------------------------------
def _run_xticks(ax, keys=None):
    keys = keys if keys is not None else KEYS
    ax.set_xticks(list(range(len(keys))))
    ax.set_xticklabels([RUN_CODES[k] for k in keys], rotation=90)


def _annotate_bars(ax, values, labels, top, fontsize=None, inside=()):
    """Vertical value labels sitting just above each bar.

    A bar in `inside` is one the axis clips: it runs to the top of the panel, so
    there is no room above it and its label is set inside the bar instead.
    """
    for xi, (v, text) in enumerate(zip(values, labels)):
        if text is None:
            continue
        if xi in inside:
            ax.text(xi, top * 0.5, text, ha="center", va="center", rotation=90,
                    fontsize=fontsize or ANNOT_SIZE, color=SURFACE)
            continue
        ax.text(xi, (v or 0) + top * 0.02, text, ha="center", va="bottom", rotation=90,
                fontsize=fontsize or ANNOT_SIZE, color=INK_SECONDARY)


def capped_limit(values, headroom=1.45, clip_ratio=2.0):
    """Axis maximum for a bar panel, plus the values it deliberately clips.

    A single run (R10) settled one git-exact file, so every per-file metric it
    appears in is several times the next largest value. Scaling those panels to
    it would flatten the fifteen bars the panel exists to compare, so when the
    largest value is more than `clip_ratio` times the second largest, the axis
    is scaled to the second largest instead and the outlier is drawn clipped
    with its true value printed above it. Panels of plain per-run totals pass
    clip_ratio=None and are never clipped.

    Returns (ymax, {index: value}) for the clipped entries.
    """
    numeric = [(i, v) for i, v in enumerate(values) if v is not None]
    if not numeric:
        return 1.0, {}
    ordered = sorted(numeric, key=lambda p: -p[1])
    top = ordered[0][1]
    if clip_ratio and len(ordered) > 1:
        second = ordered[1][1]
        if second > 0 and top > clip_ratio * second:
            ymax = second * headroom
            return ymax, {i: v for i, v in numeric if v > ymax}
    return (top * headroom) or 1.0, {}


# ---------------------------------------------------------------------------
# Load + aggregate
# ---------------------------------------------------------------------------
def load_run_aggregates():
    cc_rows = parse_all_ccworkflow(EXPERIMENTS)
    cs_rows = parse_all_csloop(EXPERIMENTS)

    runs = {}
    for key in KEYS:
        runs[key] = {
            "harness": "ccworkflow" if "ccworkflow" in key[1] else "csloop",
            "input": 0,
            "output": 0,
            "cache_write": 0,
            "cache_read": 0,
            "cost": 0.0,
            "cost_by_model": {},
            "unpriced_models": set(),
        }

    for row in cc_rows + cs_rows:
        key = run_key(row["day"], row["run_name"])
        if key not in runs:
            continue
        r = runs[key]
        model = normalize_model(row["model"])
        r["input"] += row["input_tokens"]
        r["output"] += row["output_tokens"]
        r["cache_write"] += row["cache_write_tokens"]
        r["cache_read"] += row["cache_read_tokens"]
        try:
            c = cost(
                model,
                row["input_tokens"],
                row["output_tokens"],
                row["cache_write_tokens"],
                row["cache_read_tokens"],
                row.get("cache_write_5m_tokens", 0),
                row.get("cache_write_1h_tokens", 0),
            )
        except KeyError:
            r["unpriced_models"].add(model)
            continue
        r["cost"] += c
        r["cost_by_model"][model] = r["cost_by_model"].get(model, 0.0) + c

    return runs, cc_rows, cs_rows


def _ccworkflow_wall_time_seconds(day, run_name):
    """Span between the first and last assistant-message timestamp across all
    agent-*.jsonl files in the run's workflow-wf_* dir."""
    import json as _json
    from datetime import datetime as _dt

    run_dir = EXPERIMENTS / day / run_name
    timestamps = []
    for workflow_dir in run_dir.glob("workflow-wf_*"):
        for agent_path in workflow_dir.glob("agent-*.jsonl"):
            with open(agent_path) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    ts = _json.loads(line).get("timestamp")
                    if ts:
                        timestamps.append(ts)
    if len(timestamps) < 2:
        return None
    timestamps.sort()
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
    t0 = _dt.strptime(timestamps[0], fmt)
    t1 = _dt.strptime(timestamps[-1], fmt)
    return (t1 - t0).total_seconds()


def _csloop_wall_time_seconds(cs_rows, day, run_name):
    """Sum of per-loop duration_s across author+review phases. csloop runs
    one loop at a time (no intra-run parallelism), so this sum approximates
    true elapsed engine time within a session."""
    return sum(r["duration_s"] for r in cs_rows if r["day"] == day and r["run_name"] == run_name)


def load_wall_times(cs_rows):
    wall_times = {}
    for day, run_name in KEYS:
        if "ccworkflow" in run_name:
            wall_times[(day, run_name)] = _ccworkflow_wall_time_seconds(day, run_name)
        else:
            wall_times[(day, run_name)] = _csloop_wall_time_seconds(cs_rows, day, run_name)
    return wall_times


def total_tool_calls(cc_rows, cs_rows, day, run_name):
    """Executed tool calls (ok + error), excluding policy-rejected calls that
    never ran, so the count is comparable across harnesses."""
    if "ccworkflow" in run_name:
        return sum(
            r["tool_ok"] + r["tool_error"]
            for r in cc_rows
            if r["day"] == day and r["run_name"] == run_name
        )
    return sum(
        r["tool_executed"]
        for r in cs_rows
        if r["day"] == day and r["run_name"] == run_name
    )


def load_files_settled():
    """Exact translated-file count per run, from the software/mcfm submodule
    branch (git_file_counts.py) — not the agent's self-reported checklist."""
    return {key: translated_file_count(*key) for key in KEYS}


def load_translated_units():
    """Exact list of translated-file identities per run (e.g. "BDK/M1bit1"),
    used to compare which specific files different runs picked."""
    return {key: translated_file_units(*key) for key in KEYS}


def modules_touched(translated_units):
    """{run: {module: file_count}} — which top-level src/ directories each
    run's translated files came from."""
    from collections import Counter
    return {k: Counter(module_of(u) for u in (units or [])) for k, units in translated_units.items()}


# The phase whose agent chooses which units a round works on. In ccworkflow
# that decision is the TRIAGE agent's: its prompt has it read the plan and the
# worklist and then "decide" the group and its units, while author agents are
# handed units already chosen and the integrate agent only lands them. So a
# ccworkflow run's file-selection behaviour belongs to its triage model, NOT to
# the author model its label leads with, and not to the more expensive
# integrate model. (There is no separate "dispatch" phase on disk -- triage
# both triages and dispatches.)
DECIDING_PHASE = "triage"

MODEL_DISPLAY = {
    "claude-opus-5": "opus-5",
    "claude-sonnet-5": "sonnet-5",
    "oaic-moonshotai/Kimi-K3": "Kimi K3",
    "oaic-gpt56sol": "gpt56sol",
    "oaic-gpt56terra": "gpt56terra",
}


def _display_model(model):
    return MODEL_DISPLAY.get(model, model)


def decision_model_per_run(cc_rows, cs_rows):
    """{run: model} — the model that chose which files the run translated.

    Derived from the archives rather than from the run label, so a new run
    needs no entry here: csloop drives every phase with one model, so that
    model is the decider; ccworkflow splits phases across models, so the
    decider is whichever model ran DECIDING_PHASE.

    This deliberately reattributes the ccworkflow runs. Their labels lead with
    "sonnet-5 author, opus-5 integrate", but opus-5 never picks a file there --
    it lands work that triage already selected. Counting those runs as opus-5
    decisions would credit opus-5 with choices it did not make.
    """
    from collections import Counter, defaultdict

    per_run = defaultdict(Counter)
    triage_per_run = defaultdict(Counter)
    for row in list(cc_rows) + list(cs_rows):
        key = run_key(row["day"], row["run_name"])
        if key not in RUN_CODES:
            continue
        model = normalize_model(row["model"])
        per_run[key][model] += 1
        if row.get("phase") == DECIDING_PHASE:
            triage_per_run[key][model] += 1

    deciders = {}
    for key in KEYS:
        if triage_per_run[key]:
            deciders[key] = triage_per_run[key].most_common(1)[0][0]
        elif per_run[key]:
            # csloop, or a ccworkflow run whose triage transcript is missing:
            # the model that ran the most agents is the only sensible stand-in.
            deciders[key] = per_run[key].most_common(1)[0][0]
        else:
            deciders[key] = None
    return deciders


def files_by_decision_model(translated_units, decision_models):
    """{model: {"runs": [...], "union": set, "core": set, "modules": Counter}}.

    `core` is the set of files EVERY run of that model settled -- intra-model
    reproducibility. It is only meaningful against `runs`: a model with one run
    trivially has core == union, so the row count has to be read alongside it.
    Runs with no archival branch contribute nothing and are dropped from the
    model's run list, for the same reason they are dropped everywhere else.
    """
    from collections import Counter, defaultdict

    grouped = defaultdict(list)
    for key in KEYS:
        units = translated_units[key]
        if units is None:
            continue
        grouped[decision_models[key]].append((key, set(units)))

    out = {}
    for model, entries in grouped.items():
        sets = [s for _, s in entries]
        union = set().union(*sets)
        out[model] = {
            "runs": [k for k, _ in entries],
            "union": union,
            "core": set.intersection(*sets),
            "modules": Counter(module_of(f) for f in union),
            "harnesses": sorted({"ccworkflow" if "ccworkflow" in k[1] else "csloop" for k, _ in entries}),
        }
    return out


def model_settlement_frequency(translated_units, decision_models):
    """({n_models: sorted[file]}, n_models_total) — like
    file_settlement_frequency, but counting DISTINCT DECIDING MODELS rather
    than runs.

    This is the stricter convergence measure of the two. A file settled by four
    runs of one model is that model reproducing itself; a file settled by four
    models is agreement across models. The run-level table cannot tell those
    apart, and with opus-5 contributing four of the twelve runs it will read
    the first as if it were the second.
    """
    from collections import Counter, defaultdict

    by_model = files_by_decision_model(translated_units, decision_models)
    freq = Counter()
    for info in by_model.values():
        freq.update(info["union"])
    buckets = defaultdict(list)
    for unit, n in freq.items():
        buckets[n].append(unit)
    return {n: sorted(v) for n, v in buckets.items()}, len(by_model)


def file_settlement_frequency(translated_units):
    """({n_runs: sorted[file]}, n_measured) — every distinct file any run
    retired, grouped by how many runs retired it.

    Runs whose archival branch is absent from this clone contribute no unit
    list and are left out of the denominator entirely: such a run did not
    decline to settle these files, it was never measured, and counting it as a
    non-settler would understate agreement. `n_measured` is therefore the
    number of runs this distribution is actually over, and the top bucket
    (n == n_measured) is the set of files every measured run settled.

    Grouping by count rather than listing per-file rows is what makes the shape
    readable: the interesting quantity is how the 70-odd distinct files
    *distribute* across levels of agreement, not which run picked what — the
    module table and the pairwise-overlap table already answer that.
    """
    from collections import Counter, defaultdict

    measured = {k: set(u) for k, u in translated_units.items() if u is not None}
    freq = Counter()
    for units in measured.values():
        freq.update(units)
    by_count = defaultdict(list)
    for unit, n in freq.items():
        by_count[n].append(unit)
    return {n: sorted(units) for n, units in by_count.items()}, len(measured)


def pairwise_file_overlap(translated_units):
    """For every pair of runs that share at least one top-level module, the
    exact and set-based overlap of which files they translated. Pairs with no
    module in common are skipped — there's nothing to compare."""
    keys = list(translated_units.keys())
    pairs = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            set_a = set(translated_units[a] or [])
            set_b = set(translated_units[b] or [])
            modules_a = {module_of(u) for u in set_a}
            modules_b = {module_of(u) for u in set_b}
            shared_modules = sorted(modules_a & modules_b)
            if not shared_modules:
                continue
            overlap = set_a & set_b
            pairs.append({
                "a": a, "b": b,
                "shared_modules": shared_modules,
                "files_a": len(set_a), "files_b": len(set_b),
                "overlap": len(overlap),
                "overlap_files": sorted(overlap),
            })
    return pairs


def load_tool_calls_per_file(cc_rows, cs_rows, files_settled):
    result = {}
    for key in KEYS:
        day, run_name = key
        calls = total_tool_calls(cc_rows, cs_rows, day, run_name)
        files = files_settled[key]
        result[key] = {
            "tool_calls": calls,
            "files_settled": files,
            "per_file": (calls / files) if files else None,
        }
    return result


# ---------------------------------------------------------------------------
# Panel A — total cost by model
# ---------------------------------------------------------------------------
def draw_cost_panel(ax, runs, letter=None):
    x = range(len(KEYS))

    all_models_seen = []
    for k in KEYS:
        for m in runs[k]["cost_by_model"]:
            if m not in all_models_seen:
                all_models_seen.append(m)

    bottoms = [0.0] * len(KEYS)
    for model in all_models_seen:
        heights = [runs[k]["cost_by_model"].get(model, 0.0) for k in KEYS]
        ax.bar(x, heights, bottom=bottoms, width=0.6, color=MODEL_COLOR.get(model, CAT["aqua"]),
               edgecolor=SURFACE, linewidth=1)
        bottoms = [b + h for b, h in zip(bottoms, heights)]

    # An unpriced run has no rate card at all, so its bar is empty. Labelling it
    # "$0.00" would read as "this run was free"; it gets an explicit n/a.
    texts = [
        "n/a (unpriced)" if runs[k]["unpriced_models"] else f"${bottoms[xi]:.2f}"
        for xi, k in zip(x, KEYS)
    ]
    ymax, _ = capped_limit(bottoms, clip_ratio=None)
    _annotate_bars(ax, bottoms, texts, ymax)

    _run_xticks(ax)
    ax.set_ylabel("USD (proxy rates)")
    ax.set_title(_title("Total cost by model", letter))
    ax.set_ylim(0, ymax)
    handles = [mpatches.Patch(color=MODEL_COLOR.get(m, CAT["aqua"]), label=m) for m in all_models_seen]
    ax.legend(handles=handles, loc="upper center", frameon=False)


# ---------------------------------------------------------------------------
# Panel B — cache-read share of input-side tokens
# ---------------------------------------------------------------------------
def draw_cache_panel(ax, runs, letter=None):
    x = range(len(KEYS))

    shares = []
    for k in KEYS:
        r = runs[k]
        total_input_side = r["input"] + r["cache_write"] + r["cache_read"]
        shares.append(100.0 * r["cache_read"] / total_input_side if total_input_side else 0.0)

    ax.bar(x, shares, width=0.6, color=CAT["aqua"], edgecolor=SURFACE, linewidth=1)
    _annotate_bars(ax, shares, [f"{s:.0f}%" for s in shares], 100)
    _run_xticks(ax)
    ax.set_ylabel("Cache-read share (%)")
    ax.set_ylim(0, 118)
    ax.set_title(_title("Cache efficiency", letter))


# ---------------------------------------------------------------------------
# Panel E — files translated
# ---------------------------------------------------------------------------
def draw_files_panel(ax, files_settled, letter=None):
    x = list(range(len(KEYS)))
    harness_color = {"ccworkflow": CAT["blue"], "csloop": CAT["orange"]}
    # None = the run's archival branch is not in this clone, so there is no
    # ground truth to plot. Zero = the branch is there and retired no file. The
    # two are opposite outcomes and must not share a bar height.
    settled = [files_settled[k] for k in KEYS]
    colors = [harness_color["ccworkflow"] if "ccworkflow" in k[1] else harness_color["csloop"] for k in KEYS]

    ax.bar(x, [s or 0 for s in settled], width=0.6, color=colors, edgecolor=SURFACE, linewidth=1)
    ymax, _ = capped_limit(settled, clip_ratio=None)
    _annotate_bars(ax, [s or 0 for s in settled],
                   [str(s) if s is not None else "no branch" for s in settled], ymax)
    _run_xticks(ax)
    ax.set_ylabel("Files settled (git-exact)")
    ax.set_ylim(0, ymax)
    ax.set_title(_title("Files translated", letter))
    handles = [
        mpatches.Patch(color=harness_color["ccworkflow"], label="ccworkflow"),
        mpatches.Patch(color=harness_color["csloop"], label="csloop"),
    ]
    ax.legend(handles=handles, frameon=False, loc="upper left")


# ---------------------------------------------------------------------------
# Panel F — claimed correctness (self-reported; no human_review present for
# these runs, so there's no verified-vs-claimed comparison to draw here)
# ---------------------------------------------------------------------------
def draw_correctness_panel(ax, coverage, letter=None):
    plot_keys = [k for k in KEYS if coverage[k]["self_reported_pass"]]

    for i, k in enumerate(plot_keys):
        sp = coverage[k]["self_reported_pass"]
        pct = 100 * sp[0] / sp[1]
        ax.bar(i, pct, width=0.5, color=CAT["blue"], edgecolor=SURFACE, linewidth=0.5)
        ax.text(i, pct + 3, f"{sp[0]}/{sp[1]}", ha="center", va="bottom", rotation=90,
                fontsize=ANNOT_SIZE, color=INK_SECONDARY)

    _run_xticks(ax, plot_keys)
    ax.set_ylabel("mcfm test pass rate (%)")
    # Headroom for the vertical n/m labels above bars that are all at ~100%.
    ax.set_ylim(0, 155)
    ax.set_title(_title("Self-reported correctness", letter))


# ---------------------------------------------------------------------------
# Panel G — wall-clock time by run
# ---------------------------------------------------------------------------
def draw_wall_time_panel(ax, wall_times, letter=None):
    x = list(range(len(KEYS)))
    minutes = [(wall_times[k] or 0) / 60.0 for k in KEYS]
    harness_color = {"ccworkflow": CAT["blue"], "csloop": CAT["orange"]}
    colors = [harness_color["ccworkflow"] if "ccworkflow" in k[1] else harness_color["csloop"] for k in KEYS]

    ax.bar(x, minutes, width=0.5, color=colors, edgecolor=SURFACE, linewidth=1)
    ymax, _ = capped_limit(minutes, clip_ratio=None)
    _annotate_bars(ax, minutes, [f"{m:.0f} min" for m in minutes], ymax)
    _run_xticks(ax)
    ax.set_ylabel("Wall-clock minutes")
    ax.set_ylim(0, ymax)
    ax.set_title(_title("Wall-clock time", letter))
    handles = [
        mpatches.Patch(color=harness_color["ccworkflow"], label="ccworkflow"),
        mpatches.Patch(color=harness_color["csloop"], label="csloop"),
    ]
    ax.legend(handles=handles, loc="upper right", frameon=False, ncol=2)


# ---------------------------------------------------------------------------
# Panel H — tool calls per file settled
# ---------------------------------------------------------------------------
def draw_tool_calls_per_file_panel(ax, tool_calls_per_file, letter=None):
    x = list(range(len(KEYS)))
    harness_color = {"ccworkflow": CAT["blue"], "csloop": CAT["orange"]}
    per_file = [tool_calls_per_file[k]["per_file"] for k in KEYS]
    colors = [harness_color["ccworkflow"] if "ccworkflow" in k[1] else harness_color["csloop"] for k in KEYS]

    ymax, clipped = capped_limit(per_file)
    heights = [min(v, ymax) if v is not None else 0 for v in per_file]
    ax.bar(x, heights, width=0.5, color=colors, edgecolor=SURFACE, linewidth=1)
    texts = []
    for i, (k, v) in enumerate(zip(KEYS, per_file)):
        if v is None:
            texts.append("0 files settled" if tool_calls_per_file[k]["files_settled"] == 0
                         else "no branch")
        else:
            texts.append(f"{v:.0f}" + (" ↑" if i in clipped else ""))
    _annotate_bars(ax, heights, texts, ymax, inside=set(clipped))
    _run_xticks(ax)
    ax.set_ylabel("Tool calls per file settled")
    ax.set_ylim(0, ymax)
    ax.set_title(_title("Tool-call cost per file", letter))
    handles = [
        mpatches.Patch(color=harness_color["ccworkflow"], label="ccworkflow"),
        mpatches.Patch(color=harness_color["csloop"], label="csloop"),
    ]
    # Upper-left: the clipped R10 bar owns the middle and the gpt56 runs on the
    # right are tall, so the short early runs are the only clear space left.
    ax.legend(handles=handles, loc="upper left", frameon=False, ncol=2)


# ---------------------------------------------------------------------------
# Standalone compact figures
# ---------------------------------------------------------------------------
def save_fig(fig, name, caption_lines, width_in=None):
    """Save with the caption block below the axes.

    `tight_layout`'s rect reserves the bottom strip, and the strip has to grow
    with the caption: the code→configuration mapping is six lines at 16 runs
    where it was one at nine, and a fixed rect would run the panels straight
    through it.
    """
    line_gap = 0.032
    for i, line in enumerate(reversed(caption_lines)):
        fig.text(0.5, 0.008 + i * line_gap, line, ha="center", fontsize=CAPTION_SIZE, color=INK)
    out = FIGURES_DIR / name
    fig.savefig(out, dpi=170, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def _caption_rect(n_lines, top=0.90):
    """tight_layout rect leaving room for `n_lines` of caption underneath."""
    return [0, min(0.45, 0.06 + 0.033 * n_lines), 1, top]


def make_standalone_figures(runs, coverage, files_settled, wall_times, tool_calls_per_file):
    # Fig 1 — cost & cache
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.4, 4.4))
    fig.suptitle("Token cost & cache efficiency", fontsize=SUPTITLE_SIZE)
    draw_cost_panel(a1, runs)
    draw_cache_panel(a2, runs)
    caption = run_code_caption(9.4) + [UNPRICED_NOTE, REASONING_NOTE, EXCLUDED_NOTE]
    fig.tight_layout(rect=_caption_rect(len(caption)))
    save_fig(fig, "fig1_cost_and_cache.png", caption)

    # Fig 3 — coverage
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.4, 4.4))
    fig.suptitle("Coverage & correctness", fontsize=SUPTITLE_SIZE)
    draw_files_panel(a1, files_settled)
    draw_correctness_panel(a2, coverage)
    caption = run_code_caption(9.4) + [
        "No human_review files exist for these runs, so only self-reported pass rates are shown; "
        "runs that reported none are omitted from the right-hand panel.",
        EXCLUDED_NOTE,
    ]
    fig.tight_layout(rect=_caption_rect(len(caption)))
    save_fig(fig, "fig3_coverage.png", caption)

    # Fig 4 — wall time
    fig, a1 = plt.subplots(figsize=(7.2, 4.2))
    fig.suptitle("Wall-clock time", fontsize=SUPTITLE_SIZE)
    draw_wall_time_panel(a1, wall_times)
    a1.set_title("")
    caption = run_code_caption(7.2) + [
        "ccworkflow: span of first-to-last agent timestamp. csloop: sum of per-loop duration_s.",
        EXCLUDED_NOTE,
    ]
    fig.tight_layout(rect=_caption_rect(len(caption)))
    save_fig(fig, "fig4_wall_time.png", caption)

    # Fig 5 — tool calls per file
    fig, a1 = plt.subplots(figsize=(7.2, 4.2))
    fig.suptitle("Tool-call cost per file", fontsize=SUPTITLE_SIZE)
    draw_tool_calls_per_file_panel(a1, tool_calls_per_file)
    a1.set_title("")
    caption = run_code_caption(7.2) + [
        "Executed tool calls (ok + error) divided by files settled (git-exact count, git_file_counts.py).",
        "↑ marks a bar clipped by the axis; its true value is printed above it.",
        EXCLUDED_NOTE,
    ]
    fig.tight_layout(rect=_caption_rect(len(caption)))
    save_fig(fig, "fig5_tool_calls_per_file.png", caption)


# ---------------------------------------------------------------------------
# Combined single figure
# ---------------------------------------------------------------------------
def _bump_fonts_for_combined(scale=1.15):
    global ANNOT_SIZE
    plt.rcParams.update({
        "font.size": LABEL_SIZE * scale,
        "axes.titlesize": TITLE_SIZE * scale,
        "axes.labelsize": LABEL_SIZE * scale,
        "axes.labelcolor": INK,
        "xtick.labelsize": TICK_SIZE * scale,
        "ytick.labelsize": TICK_SIZE * scale,
        "xtick.color": INK,
        "ytick.color": INK,
        "legend.fontsize": LEGEND_SIZE * scale,
        "legend.labelcolor": INK,
    })
    ANNOT_SIZE = ANNOT_SIZE * scale


def make_combined_figure(runs, coverage, files_settled, wall_times, tool_calls_per_file):
    # Three rows at the same 3in/row the four-row layout used, plus the same
    # absolute caption band (~2.2in) and top margin (~0.8in).
    fig = plt.figure(figsize=(11, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.62, wspace=0.32, top=0.931, bottom=0.181, left=0.09, right=0.98)

    draw_cost_panel(fig.add_subplot(gs[0, 0]), runs, letter="(a)")
    draw_cache_panel(fig.add_subplot(gs[0, 1]), runs, letter="(b)")
    draw_files_panel(fig.add_subplot(gs[1, 0]), files_settled, letter="(c)")
    draw_wall_time_panel(fig.add_subplot(gs[1, 1]), wall_times, letter="(d)")
    draw_tool_calls_per_file_panel(fig.add_subplot(gs[2, 0]), tool_calls_per_file, letter="(e)")
    draw_correctness_panel(fig.add_subplot(gs[2, 1]), coverage, letter="(f)")

    fig.suptitle(
        "08-11-2026 → 08-26-2026: ccworkflow vs. csloop on mcfm-translate — cost, cache, tool calls & coverage",
        fontsize=SUPTITLE_SIZE + 2,
        y=0.985,
    )
    caption_size = CAPTION_SIZE * 1.35
    caption = run_code_caption(10.4, caption_size) + [UNPRICED_NOTE, REASONING_NOTE, EXCLUDED_NOTE]
    for i, line in enumerate(reversed(caption)):
        fig.text(0.5, 0.008 + i * 0.0135, line, ha="center", fontsize=caption_size, color=INK)

    out = FIGURES_DIR / "fig_combined.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# ---------------------------------------------------------------------------
# Summary tables (markdown) — single source of numeric truth for the write-up
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Decision-making figure
#
# The question these panels answer is not "how much did a run get through"
# (tab_runs and the cost/throughput panels already do that) but "what did the
# model CHOOSE, and was the choice a good one". Runs are therefore collapsed to
# their deciding model -- for ccworkflow that is the triage model, see
# decision_model_per_run -- and every quantity is over DISTINCT files, so a
# model with four runs cannot out-vote one with a single run by repeating
# itself.
#
# Sequential blue (one hue, light->dark) for magnitude in (a); one accent hue
# plus a gray reference in (b); the ordinal ramp for the three ordered bins in
# (c). Palette steps are the dataviz reference instance, and the (c) ramp was
# checked with validate_palette.js --ordinal.
# ---------------------------------------------------------------------------
SEQ_BLUE = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
            "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
# Ordinal steps 250/400/550 -- the light end clears the 2:1 floor against the
# light surface, so the lightest bin is still visible rather than receding.
ORD_BLUE = ["#86b6ef", "#3987e5", "#1c5cab"]


def _seq_color(value, vmax):
    """Sequential step for `value`. Zero is not a step -- an empty cell means
    "this model never entered this module", which is categorically different
    from "entered it and settled nothing" and is drawn as bare surface."""
    if not value:
        return None
    frac = value / vmax if vmax else 0.0
    # Start a third of the way up the ramp: the palest steps are reserved for
    # near-zero, and every cell drawn here is a nonzero count.
    idx = int(round((0.34 + 0.66 * frac) * (len(SEQ_BLUE) - 1)))
    return SEQ_BLUE[min(idx, len(SEQ_BLUE) - 1)]


def draw_model_module_panel(ax, by_model, attrs, letter=None):
    """(a) Which part of the tree each deciding model chose to work in."""
    models = sorted(by_model, key=lambda m: -len(by_model[m]["union"]))
    modules = sorted({attrs[u]["top"] for i in by_model.values() for u in i["union"]
                      if attrs.get(u)})
    counts = [[sum(1 for u in by_model[m]["union"] if attrs.get(u) and attrs[u]["top"] == mod)
               for mod in modules] for m in models]
    vmax = max(max(row) for row in counts)

    ax.grid(False)
    ax.set_xlim(0, len(modules))
    ax.set_ylim(0, len(models))
    ax.invert_yaxis()
    for i, row in enumerate(counts):
        for j, v in enumerate(row):
            color = _seq_color(v, vmax)
            if color is None:
                continue
            # 2px surface gap between fills: inset each cell rather than tiling.
            ax.add_patch(mpatches.Rectangle((j + 0.04, i + 0.04), 0.92, 0.92,
                                            facecolor=color, edgecolor="none"))
            # Value labels wear ink tokens, not the fill colour -- except where
            # the fill is dark enough that ink would not read.
            dark = SEQ_BLUE.index(color) >= 8
            ax.text(j + 0.5, i + 0.5, str(v), ha="center", va="center",
                    fontsize=ANNOT_SIZE, color=SURFACE if dark else INK)
    ax.set_xticks([j + 0.5 for j in range(len(modules))])
    ax.set_xticklabels(modules, rotation=45, ha="right")
    ax.set_yticks([i + 0.5 for i in range(len(models))])
    ax.set_yticklabels([_display_model(m) for m in models])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title(_title("Where each model chose to work", letter))
    return models


def draw_targeting_panel(ax, by_model, attrs, pool, letter=None):
    """(b) Fan-in of the files a model chose, against the pool it chose from.

    Fan-in is how many still-untranslated files depend on this one, so it is
    the roadmap's own notion of value: `dev/workflow.py next` sorts ready files
    by it. Each row is a dumbbell from the mean over every ready file available
    at the fork point (the gray reference every model faced) to the mean over
    the files that model actually took. Right of the reference means the model
    picked higher-leverage work than drawing at random from the pool would.
    """
    import statistics

    pool_mean = statistics.mean(attrs[u]["fanin"] for u in pool)
    models = sorted(by_model, key=lambda m: -len(by_model[m]["union"]))
    ax.grid(False)
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    ax.axvline(pool_mean, color=MUTED, lw=0.8, zorder=1)

    for i, m in enumerate(models):
        units = [u for u in by_model[m]["union"] if attrs.get(u)]
        mean = statistics.mean(attrs[u]["fanin"] for u in units)
        y = len(models) - 1 - i
        ax.plot([pool_mean, mean], [y, y], color=CAT["blue"], lw=1.6, zorder=2,
                solid_capstyle="round")
        ax.plot([pool_mean], [y], "o", ms=5, color=MUTED, zorder=3)
        # 2px surface ring so the accent mark reads where it overlaps the line.
        ax.plot([mean], [y], "o", ms=8, color=CAT["blue"], zorder=4,
                markeredgecolor=SURFACE, markeredgewidth=1.4)
        ax.annotate(f"{mean/pool_mean:.1f}x  (n={len(units)})", (mean, y),
                    textcoords="offset points", xytext=(11, 0), va="center",
                    fontsize=ANNOT_SIZE, color=INK_SECONDARY)

    ax.set_yticks(range(len(models)))
    ax.set_yticklabels([_display_model(m) for m in reversed(models)])
    ax.set_ylim(-0.7, len(models) - 0.3)
    ax.set_xlim(0, max(6.2, ax.get_xlim()[1] * 1.5))
    ax.set_xlabel("Mean fan-in of files chosen")
    ax.annotate("ready pool\n(all models)", (pool_mean, len(models) - 0.62),
                textcoords="offset points", xytext=(4, 0), va="center",
                fontsize=CAPTION_SIZE, color=MUTED)
    ax.set_title(_title("Was the choice well-targeted?", letter))


def draw_agreement_panel(ax, buckets, n_models, letter=None):
    """(c) How many distinct models independently settled the same file."""
    ns = sorted(buckets, reverse=True)
    total = sum(len(v) for v in buckets.values())
    ax.grid(False)
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    for i, n in enumerate(ns):
        v = len(buckets[n])
        y = len(ns) - 1 - i
        ax.barh(y, v, height=0.62, color=ORD_BLUE[min(n - 1, len(ORD_BLUE) - 1)],
                edgecolor="none")
        ax.text(v + total * 0.02, y, f"{v}  ({100*v/total:.0f}%)", va="center",
                fontsize=ANNOT_SIZE, color=INK_SECONDARY)
    ax.set_yticks(range(len(ns)))
    ax.set_yticklabels([f"{n} of {n_models}" for n in reversed(ns)])
    ax.set_ylim(-0.7, len(ns) - 0.3)
    ax.set_xlim(0, total * 1.22)
    ax.set_xlabel("Distinct files")
    ax.set_ylabel("Models settling it")
    ax.set_title(_title("Do models agree on files?", letter))


def unblocking_per_run(translated_units):
    """{run: (settled, newly_ready, trustworthy)} -- the outcome measure.

    Every run started from the same fork-point pool, so a file that was not
    ready then and is ready in the run's own post-run map was unblocked BY that
    run. This is the only outcome in the corpus not defined by the same map it
    scores: fan-in is the roadmap's own notion of value, so scoring choices by
    fan-in and then rewarding high fan-in is circular. Unblocking is downstream
    of the choice and measured independently of it.

    `trustworthy` is False where the archived map was refreshed mid-run, which
    makes the count a lower bound rather than a measurement.
    """
    attrs = fork_point_roadmap(EXPERIMENTS, RUNS, translated_units)
    pre = ready_pool(attrs)
    out = {}
    for key in KEYS:
        run_dir = EXPERIMENTS / key[0] / key[1]
        post = post_run_ready(run_dir)
        settled = translated_units[key] or []
        if post is None or not settled:
            continue
        out[key] = (len(settled), len(post - pre),
                    roadmap_is_post_run(run_dir, settled))
    return out


def draw_unblocking_panel(ax, unblocking, decision_models, letter=None):
    """(d) Files unblocked downstream, per file settled -- the outcome."""
    order = [k for k in KEYS if k in unblocking]
    rates, labels, hollow = [], [], []
    for k in order:
        settled, newly, ok = unblocking[k]
        rates.append(newly / settled)
        labels.append(RUN_CODES[k])
        hollow.append(not ok)
    ax.grid(False)
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    for i, (v, faded) in enumerate(zip(rates, hollow)):
        # A partial "after" state is a lower bound, not a measurement; drawn
        # hollow so it cannot be read as a low outcome.
        ax.bar(i, v, width=0.62, facecolor=SURFACE if faded else CAT["blue"],
               edgecolor=CAT["blue"] if faded else "none", linewidth=1.1)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(labels, rotation=90)
    ax.set_ylabel("Files unblocked / file settled")
    ax.set_xlim(-0.7, len(order) - 0.3)
    ax.set_title(_title("Did the choice unblock work?", letter))
    ax.set_ylim(0, max(rates) * 1.18)


def make_decision_figure(translated_units, decision_models):
    by_model = files_by_decision_model(translated_units, decision_models)
    attrs = fork_point_roadmap(EXPERIMENTS, RUNS, translated_units)
    pool = ready_pool(attrs)
    buckets, n_models = model_settlement_frequency(translated_units, decision_models)

    unblocking = unblocking_per_run(translated_units)
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.4))
    draw_model_module_panel(axes[0][0], by_model, attrs, letter="(a)")
    draw_targeting_panel(axes[0][1], by_model, attrs, pool, letter="(b)")
    draw_agreement_panel(axes[1][0], buckets, n_models, letter="(c)")
    draw_unblocking_panel(axes[1][1], unblocking, decision_models, letter="(d)")

    caption = [
        "In (a) an empty cell means the model never entered that module at all -- not that it entered "
        "and settled nothing.",
        "Runs collapsed to the model that CHOSE the files: the run's own model for csloop, the triage "
        "model for ccworkflow (author/integrate agents do not select).",
        "In (d), open bars are runs whose map was refreshed mid-run: "
        "their after-state is partial, so the value is a lower bound, not a measurement.",
        "(d) is the one outcome measure here: fan-in in (b) is the roadmap's own notion of value, so it "
        "cannot also score adherence to that roadmap without circularity.",
        "Counts are over distinct files, so a model with four runs cannot out-vote one with a single run "
        f"by repeating itself. Fan-in and readiness come from the doxygen map reconstructed at the shared "
        f"fork point ({len(attrs)} untranslated files, {len(pool)} ready leaves).",
    ]
    line_h = 0.042
    fig.tight_layout(rect=(0, line_h * len(caption) + 0.02, 1, 1))
    for i, line in enumerate(reversed(caption)):
        fig.text(0.5, 0.018 + i * line_h, line, ha="center", fontsize=CAPTION_SIZE, color=INK)
    out = FIGURES_DIR / "fig6_decision_making.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"wrote {out}")


def _row_label(k):
    """Run code + configuration, so a table row can be matched to a figure bar."""
    return f"{RUN_CODES[k]} — {RUN_LABELS[k]}".replace(chr(10), " ")


def _files_cell(files):
    """git-exact files settled: 0 and "no archival branch here" are different."""
    return "n/a (no branch)" if files is None else str(files)


def write_summary_tables(runs, coverage, files_settled, translated_units, wall_times, tool_calls_per_file,
                         decision_models):
    lines = ["# Summary tables (generated by analysis/generate_graphs.py — do not hand-edit)\n"]
    lines.append(f"{UNPRICED_NOTE}\n")
    lines.append(f"{REASONING_NOTE}\n")
    lines.append(f"{EXCLUDED_NOTE}\n")

    lines.append("## Run comparison: cost, cache, wall time, tool calls & files settled\n")
    lines.append(
        "| Run | Cost (USD, proxy rates) | Cache-read share | Wall time | Tool calls / file | "
        "Files settled (git-exact) | Time / file | Cost / file |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k in KEYS:
        r = runs[k]
        wt = wall_times.get(k)
        t = tool_calls_per_file[k]
        files = files_settled[k]
        total_input_side = r["input"] + r["cache_write"] + r["cache_read"]
        share = 100.0 * r["cache_read"] / total_input_side if total_input_side else 0.0
        cost_str = f"${r['cost']:.2f}"
        if r["unpriced_models"]:
            cost_str += " (n/a, non-Anthropic)"
        wt_str = f"{wt/60:.0f} min" if wt else "unknown"
        per_file_str = f"{t['per_file']:.1f}" if t["per_file"] is not None else "—"
        time_per_file_str = f"{wt/60/files:.1f} min" if (wt and files) else "—"
        if files and not r["unpriced_models"]:
            cost_per_file_str = f"${r['cost']/files:.2f}"
        elif r["unpriced_models"]:
            cost_per_file_str = "n/a"
        else:
            cost_per_file_str = "—"
        lines.append(
            f"| {_row_label(k)} | {cost_str} | {share:.0f}% | {wt_str} | "
            f"{per_file_str} | {_files_cell(files)} | {time_per_file_str} | {cost_per_file_str} |"
        )
    lines.append("")

    lines.append("## Token usage, cost, cache & wall time detail\n")
    lines.append("| Run | Input | Output | Cache write | Cache read | Cache-read share | Cost (USD, proxy rates) | Wall time |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k in KEYS:
        r = runs[k]
        wt = wall_times.get(k)
        wt_str = f"{wt/60:.0f} min" if wt else "unknown"
        total_input_side = r["input"] + r["cache_write"] + r["cache_read"]
        share = 100.0 * r["cache_read"] / total_input_side if total_input_side else 0.0
        cost_str = f"${r['cost']:.2f}"
        if r["unpriced_models"]:
            cost_str += f" (+ tokens from {', '.join(sorted(r['unpriced_models']))}, not priced)"
        lines.append(
            f"| {_row_label(k)} | {r['input']:,} | {r['output']:,} | "
            f"{r['cache_write']:,} | {r['cache_read']:,} | {share:.0f}% | {cost_str} | {wt_str} |"
        )
    lines.append("")

    lines.append("## Cost by model\n")
    lines.append("| Run | " + " | ".join(sorted(PRICING.keys())) + " |")
    lines.append("|---|" + "---:|" * len(PRICING))
    for k in KEYS:
        r = runs[k]
        cells = [f"${r['cost_by_model'].get(m, 0.0):.2f}" for m in sorted(PRICING.keys())]
        lines.append(f"| {_row_label(k)} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Status, coverage claim & self-reported correctness\n")
    lines.append(
        "`Files (git)` is ground truth — originals actually retired on the run's archival branch. "
        "`Checklist` is the run's own `- [x]` count in agent_log.md. They diverge when a round adds a "
        "`.cpp` beside a Fortran original it keeps (no file retired, so git counts none of it) or when "
        "the log was not archived with the run.\n"
    )
    lines.append("| Run | Status | Files (git) | Checklist | Open | Self-reported pass |")
    lines.append("|---|---|---:|---:|---:|---|")
    for k in KEYS:
        c = coverage[k]
        sp = f"{c['self_reported_pass'][0]}/{c['self_reported_pass'][1]}" if c["self_reported_pass"] else "—"
        has_log = c["final_status"] != "not-executed" and (c["files_settled"] or c["files_open"] or sp != "—")
        lines.append(
            f"| {_row_label(k)} | {c['final_status']} | {_files_cell(files_settled[k])} | "
            f"{c['files_settled'] if has_log else '—'} | {c['files_open'] if has_log else '—'} | {sp} |"
        )
    lines.append("")

    mods = modules_touched(translated_units)
    all_modules = sorted({m for counts in mods.values() for m in counts})
    lines.append("## Which src/ module each run translated files from (git-exact)\n")
    lines.append(
        "Which top-level `software/mcfm/src/` directory each run's translated files came from — "
        "shows whether runs converged on the same module or scattered across different ones.\n"
    )
    lines.append("| Run | " + " | ".join(all_modules) + " | Total |")
    lines.append("|---|" + "---:|" * (len(all_modules) + 1))
    for k in KEYS:
        if translated_units[k] is None:
            cells = ["n/a"] * len(all_modules)
            lines.append(f"| {_row_label(k)} | " + " | ".join(cells) + " | n/a (no branch) |")
            continue
        counts = mods[k]
        cells = [str(counts.get(m, 0) or "") for m in all_modules]
        lines.append(f"| {_row_label(k)} | " + " | ".join(cells) + f" | {sum(counts.values())} |")
    lines.append("")

    overlaps = pairwise_file_overlap(translated_units)
    lines.append("## File-level overlap between runs sharing a module (git-exact)\n")
    lines.append(
        "For every pair of runs that translated files from at least one of the same modules: how many of "
        "the *exact same files* they both picked, vs. how many files each translated in total. High overlap "
        "relative to the smaller run's total means the two runs converged on the same files; low overlap "
        "despite a shared module means they diverged within it.\n"
    )
    lines.append("| Run A | Run B | Shared module(s) | Files (A) | Files (B) | Overlap | Overlap / min(A,B) |")
    lines.append("|---|---|---|---:|---:|---:|---:|")
    for p in sorted(overlaps, key=lambda p: -p["overlap"]):
        denom = min(p["files_a"], p["files_b"]) or 1
        lines.append(
            f"| {_row_label(p['a'])} | {_row_label(p['b'])} | "
            f"{', '.join(p['shared_modules'])} | {p['files_a']} | {p['files_b']} | {p['overlap']} | "
            f"{100*p['overlap']/denom:.0f}% |"
        )
    lines.append("")

    by_count, n_measured = file_settlement_frequency(translated_units)
    total_distinct = sum(len(v) for v in by_count.values())
    universal = by_count.get(n_measured, [])
    lines.append("## How many runs settled each file (git-exact)\n")
    lines.append(
        f"Every distinct file any run retired ({total_distinct} of them), bucketed by how many of the "
        f"{n_measured} measured runs retired it. The module table above shows whether runs landed in the "
        "same *area*; this shows whether they landed on the same *files*, which is the stricter question.\n"
    )
    if universal:
        lines.append(
            f"Settled by all {n_measured} runs: {len(universal)} "
            f"({', '.join('`' + u + '`' for u in universal)}).\n"
        )
    else:
        lines.append(
            f"**No file was settled by all {n_measured} runs — the all-run intersection is empty.** That is "
            "a property of the corpus rather than a near-miss: the runs split across top-level modules that "
            "do not overlap at all, so most pairs had no opportunity to agree. Read the rows below as "
            "levels of partial agreement, not as a ranking against a reachable maximum.\n"
        )
    # Naming files is only useful while the list is short enough to scan; past
    # that the cell is a wall of identifiers that hides the distribution the
    # table exists to show.
    NAME_LIMIT = 8
    lines.append("| Runs settling it | Files | Share | Cumulative | Which files |")
    lines.append("|---:|---:|---:|---:|---|")
    cumulative = 0
    for n in sorted(by_count, reverse=True):
        units = by_count[n]
        cumulative += len(units)
        named = ", ".join(f"`{u}`" for u in units) if len(units) <= NAME_LIMIT else "—"
        lines.append(
            f"| {n} | {len(units)} | {100*len(units)/total_distinct:.0f}% | "
            f"{100*cumulative/total_distinct:.0f}% | {named} |"
        )
    lines.append("")

    by_model = files_by_decision_model(translated_units, decision_models)
    lines.append("## Which files each *model* chose (git-exact)\n")
    lines.append(
        "Runs grouped by the model that made the file-selection decision, not by harness. For csloop that "
        "is the run's only model. For ccworkflow it is the **triage** model — triage reads the plan and "
        f"picks the round's units, while author agents are handed units already chosen and integrate only "
        "lands them. So R2/R3 count as sonnet-5 decisions despite their labels leading with "
        "\"opus-5 integrate\": opus-5 never picked a file in those runs.\n"
    )
    lines.append(
        "`Core` is the set of files settled in *every* run of that model — intra-model reproducibility. "
        "Read it against the run count: a model with one run trivially has core = union.\n"
    )
    lines.append("| Decision model | Runs | Harness | Modules entered | Files (union) | Core | Core files |")
    lines.append("|---|---|---|---|---:|---:|---|")
    for model, info in sorted(by_model.items(), key=lambda kv: (-len(kv[1]["runs"]), kv[0])):
        codes = ", ".join(RUN_CODES[k] for k in info["runs"])
        mods = ", ".join(f"{m} ({n})" for m, n in sorted(info["modules"].items(), key=lambda kv: -kv[1]))
        core = ", ".join(f"`{f}`" for f in sorted(info["core"])) if info["core"] else "—"
        if len(info["core"]) > 6:
            core = f"{len(info['core'])} files"
        lines.append(
            f"| {_display_model(model)} | {codes} | {', '.join(info['harnesses'])} | {mods} | "
            f"{len(info['union'])} | {len(info['core'])} | {core} |"
        )
    lines.append("")

    mbuckets, n_models = model_settlement_frequency(translated_units, decision_models)
    m_total = sum(len(v) for v in mbuckets.values())
    lines.append("## How many *models* settled each file (git-exact)\n")
    lines.append(
        "The stricter companion to the run-level table above. A file settled by four runs of one model is "
        "that model reproducing itself; a file settled by four models is cross-model agreement. The "
        "run-level counts cannot separate those, and with opus-5 supplying four of the twelve runs they "
        "will read the first as though it were the second.\n"
    )
    lines.append("| Models settling it | Files | Share | Which files |")
    lines.append("|---:|---:|---:|---|")
    for n in sorted(mbuckets, reverse=True):
        units = mbuckets[n]
        named = ", ".join(f"`{u}`" for u in units) if len(units) <= NAME_LIMIT else "—"
        lines.append(f"| {n} of {n_models} | {len(units)} | {100*len(units)/m_total:.0f}% | {named} |")
    lines.append("")

    out = Path(__file__).parent / "summary_tables.md"
    out.write_text("\n".join(lines))
    print(f"wrote {out}")


# ---------------------------------------------------------------------------
# LaTeX / TikZ output — the paper renders its evaluation figure as pgfplots
# rather than an imported PNG, so it picks up the document's own fonts and
# stays vector. Emitted from the same parsed data as the PNGs and the summary
# tables above, so there is exactly one numeric source of truth; the .tex files
# below are generated artifacts and carry a do-not-hand-edit banner.
# ---------------------------------------------------------------------------
TEX_DIR = Path(__file__).parent / "tex"

TEX_BANNER = (
    "%% GENERATED by evals/analysis/generate_graphs.py -- DO NOT HAND-EDIT.\n"
    "%% Regenerate with: python3 analysis/generate_graphs.py\n"
    "%% Numbers are identical to analysis/summary_tables.md.\n"
)

# Only the data-bearing .tex files carry this; the colour definitions have no
# run set to qualify.
TEX_DATA_BANNER = TEX_BANNER + (
    "%% Excluded runs: csloop opus-5 (08-11) and (run2, 08-12) logged no model\n"
    "%% reasoning text; csloop Kimi K3 (08-14) has no archival git branch;\n"
    "%% ccworkflow opus-5 (single session, 08-13) and csloop sonnet-5\n"
    "%% +reasoning (08-12) withdrawn from the comparison.\n"
)

# Palette mirrored into LaTeX so the figure matches the PNG version exactly.
TEX_COLORS = [
    ("evalBlue", CAT["blue"]),
    ("evalOrange", CAT["orange"]),
    ("evalAqua", CAT["aqua"]),
    ("evalViolet", CAT["violet"]),
    ("evalYellow", CAT["yellow"]),
    ("evalGrid", GRID),
    ("evalAxis", AXIS),
    ("evalInk", INK_SECONDARY),
    # Used for value labels printed inside a bar, where ink-on-fill would not read.
    ("evalSurface", SURFACE),
    # Sequential + ordinal steps for the decision figure's heatmap and bins.
    # Emitted in full rather than only the steps this dataset happens to reach,
    # so the .tex stays valid when the run set changes the maxima.
    *[(f"evalSeq{i}", c) for i, c in enumerate(SEQ_BLUE)],
    *[(f"evalOrd{i}", c) for i, c in enumerate(ORD_BLUE)],
]


def _tex_escape(text):
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                 ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"),
                 ("^", r"\textasciicircum{}")]:
        text = text.replace(a, b)
    return text


def derived_metrics(runs, files_settled, wall_times, tool_calls_per_file):
    """Per-run normalized metrics used by both the TikZ figure and the tables.

    Every "per file" metric is undefined when a run settled zero files; those
    come back as None and are rendered as an explicit n/a rather than a zero
    bar, because "settled nothing" and "settled something cheaply" are opposite
    outcomes that a zero-height bar would conflate.

    `files` itself is None — a third state — when the run's archival branch is
    absent from this clone: nothing was measured, as opposed to nothing being
    settled.
    """
    out = {}
    for k in KEYS:
        r = runs[k]
        files = files_settled[k]
        wt = wall_times.get(k)
        input_side = r["input"] + r["cache_write"] + r["cache_read"]
        priced = not r["unpriced_models"]
        out[k] = {
            "code": RUN_CODES[k],
            "label": RUN_LABELS[k],
            "harness": r["harness"],
            "files": files,
            "cost": r["cost"] if priced else None,
            "priced": priced,
            "cost_by_model": r["cost_by_model"],
            "minutes": (wt / 60.0) if wt else None,
            "tool_calls": tool_calls_per_file[k]["tool_calls"],
            "calls_per_file": tool_calls_per_file[k]["per_file"],
            "cost_per_file": (r["cost"] / files) if (priced and files) else None,
            "min_per_file": (wt / 60.0 / files) if (wt and files) else None,
            "input_side": input_side,
            "tokens_per_file": (input_side / files) if files else None,
            "raw_share": 100.0 * r["input"] / input_side if input_side else 0.0,
            "write_share": 100.0 * r["cache_write"] / input_side if input_side else 0.0,
            "read_share": 100.0 * r["cache_read"] / input_side if input_side else 0.0,
        }
    return out


# pgfplots counts tick and axis labels inside `width`, so three panels plus the
# group separations must fit \textwidth of a two-column page: 3 x 0.27 = 0.81
# \textwidth plus 2 x 1.05cm of separation clears a 17.8cm text block.
# Panel geometry. Three panels across leave room to spare: at the 469pt text
# width these render to ~88% of the text block, so the figure can grow a
# little without the group running into the margin. Both dimensions feed
# every panel — tools/preview_tikz.sh measures the result.
def _axis_common(width="0.29\\textwidth", height="3.7cm"):
    return (
        f"width={width}, height={height},\n"
        "  axis lines=left, axis line style={draw=evalAxis, line width=0.4pt},\n"
        "  ymajorgrids, grid style={draw=evalGrid, line width=0.4pt},\n"
        "  tick label style={font=\\scriptsize, /pgf/number format/assume math mode=true},\n"
        "  label style={font=\\scriptsize, color=evalInk},\n"
        # Default y-label placement reserves room for the widest possible tick
        # labels, which in a tight group leaves the label floating far enough
        # left to look attached to the previous panel. Pinning it to the actual
        # tick extent closes that gap; the labels themselves are kept short for
        # the same reason.
        "  ylabel near ticks,\n"
        # `ylabel near ticks` redefines `every axis y label` wholesale, which
        # discards the font `label style` set above — the y label came out at
        # the document's \normalsize, dwarfing the \scriptsize ticks and title
        # next to it. Restating the font here, *after* that key, is what makes
        # it stick. The negative yshift is a rightward nudge: the label node is
        # rotated 90 degrees, so its local -y points at the axis, and pulling it
        # in closes the gap `near ticks` still leaves in a group this tight.
        "  ylabel style={font=\\scriptsize, yshift=-6pt},\n"
        "  title style={font=\\scriptsize\\bfseries, yshift=-1pt},\n"
        # \tiny, not \scriptsize: "ccworkflow" set at \scriptsize is nearly half
        # the width of a 0.27\textwidth panel, so the legend box crowds the bars
        # it is supposed to explain.
        "  legend style={font=\\tiny, draw=none, fill=none, inner sep=1pt},\n"
        "  legend image code/.code={\\draw[##1] (0cm,-0.05cm) rectangle (0.18cm,0.09cm);},\n"
        "  every axis plot/.append style={line width=0.4pt},\n"
        "  xtick style={draw=none}, ytick style={draw=none},\n"
        "  enlarge x limits=0.08, ymin=0,\n"
    )


def _bar_coords(metrics, field, scale=1.0):
    """`(code, value)` pairs for the runs where `field` is defined, plus the
    list of codes where it is not (rendered as an n/a annotation)."""
    pts, missing = [], []
    for k in KEYS:
        m = metrics[k]
        v = m[field]
        if v is None:
            missing.append(m["code"])
        else:
            pts.append((m["code"], v * scale))
    return pts, missing


def _coord_str(pts, fmt="{:.4g}"):
    return " ".join("(%s,%s)" % (c, fmt.format(v)) for c, v in pts)


def _symbolic_x():
    """Symbolic x axis listing every run code explicitly.

    xtick is enumerated rather than left as `xtick=data`: several panels split
    their bars into two harness series covering disjoint subsets of the runs,
    and `xtick=data` then labels only the runs present in one series, silently
    dropping the rest of the tick labels.

    Labels are set vertically: sixteen codes across a 0.27\\textwidth panel give
    each tick about 2.5mm, which horizontal \\tiny text overruns.
    """
    codes = ",".join(RUN_CODES[k] for k in KEYS)
    return (
        f"symbolic x coords={{{codes}}}, xtick={{{codes}}},\n"
        "  x tick label style={rotate=90, anchor=east, font=\\tiny, yshift=1pt},\n"
    )


def _tex_axis_max(values, clip_ratio=2.0, headroom=1.45):
    """capped_limit in the units the .tex needs: (ymax, {code: true value})."""
    ymax, clipped = capped_limit(values, headroom=headroom, clip_ratio=clip_ratio)
    codes = [RUN_CODES[k] for k in KEYS]
    return ymax, {codes[i]: v for i, v in clipped.items()}


def _explicit_labels():
    """Print the label carried by each coordinate instead of its plotted value.

    A clipped bar is drawn at the axis maximum, so pgfplots' automatic
    `nodes near coords` would print the axis maximum and quietly turn a clipped
    outlier into a false reading. With explicit symbolic point meta the bar can
    be cut off while the printed number stays the true one.
    """
    return (
        "  point meta=explicit symbolic,\n"
        "  nodes near coords={\\pgfplotspointmeta},\n"
        "  nodes near coords style={font=\\tiny, color=evalInk, rotate=90, anchor=west},\n"
    )


def _clip_plot(color, pts):
    """The clipped bars, as their own series with the label set *inside* the bar.

    A clipped bar runs to the axis maximum, so an above-the-bar node would land
    outside the axis: pgfplots clips it away and the reader is left with a bar
    that stops at the top edge for no stated reason. The label is therefore
    drawn as a plain node at mid-bar, in the surface colour so it reads against
    the fill. `forget plot` keeps the series out of the panel legend, and
    `nodes near coords=` empties the automatic label that would otherwise still
    be emitted from the axis-level style.
    """
    if not pts:
        return ""
    bars = " ".join(f"({c},{v:.4g})" for c, v, _ in pts)
    labels = "".join(
        f"\\node[font=\\tiny, color=evalSurface, rotate=90, anchor=center] "
        f"at (axis cs:{c},{v / 2:.4g}) {{{lbl}}};\n"
        for c, v, lbl in pts
    )
    return (
        f"\\addplot[fill={color}, draw=none, bar shift=0pt, forget plot,\n"
        "  nodes near coords={}] coordinates {" + bars + "};\n" + labels
    )


def _coord_str_meta(pts):
    """`(code,value) [label]` triples for a plot using explicit symbolic meta."""
    return " ".join(f"({c},{v:.4g}) [{lbl}]" for c, v, lbl in pts)


def _na_nodes(missing, note="n/a"):
    """Explicit n/a marks where a metric is undefined, so a missing bar is
    never read as a zero."""
    return "".join(
        f"\\node[font=\\tiny, color=evalInk, rotate=90, anchor=west] at (axis cs:{c},0) "
        f"{{\\,{note}}};\n"
        for c in missing
    )


def _panel_files(metrics):
    cc = [(metrics[k]["code"], metrics[k]["files"]) for k in KEYS
          if metrics[k]["harness"] == "ccworkflow" and metrics[k]["files"] is not None]
    cs = [(metrics[k]["code"], metrics[k]["files"]) for k in KEYS
          if metrics[k]["harness"] == "csloop" and metrics[k]["files"] is not None]
    ymax, _ = _tex_axis_max([metrics[k]["files"] for k in KEYS], clip_ratio=None, headroom=1.30)
    unmeasured = [metrics[k]["code"] for k in KEYS if metrics[k]["files"] is None]
    return (
        "\\nextgroupplot[" + _axis_common() + _symbolic_x() +
        # `area legend` after `ybar`: a non-stacked ybar plot installs its own
        # bar-shaped legend image on top of the axis-level one, so each entry
        # came out with two swatches. The stacked panels are already area-style
        # and need no such override.
        "  ybar, bar width=3pt, area legend,\n"
        "  title={(a) Files settled (git-exact)},\n"
        f"  ylabel={{Files}}, ymax={ymax:.0f},\n"
        "  nodes near coords, nodes near coords style={font=\\tiny, color=evalInk,\n"
        "    rotate=90, anchor=west},\n"
        # At 16 runs there is no free interior space left for it — R3 owns the
        # top, the right-hand runs own the rest — so the harness legend goes
        # under the axis. It covers panels (d) and (f) too, which use the same
        # two colours for the same two harnesses.
        "  legend style={at={(0.5,-0.42)}, anchor=north}, legend columns=2,\n"
        "]\n"
        # The two harness series cover disjoint x values, so bar shift=0pt keeps
        # every bar centred on its own tick instead of offsetting it into a
        # two-series slot and leaving a phantom gap beside it.
        "\\addplot[fill=evalBlue, draw=none, bar shift=0pt] coordinates {" + _coord_str(cc, "{:.0f}") + "};\n"
        "\\addplot[fill=evalOrange, draw=none, bar shift=0pt] coordinates {" + _coord_str(cs, "{:.0f}") + "};\n"
        "\\legend{ccworkflow, csloop}\n"
        # A run whose archival branch never reached this clone has no ground
        # truth at all; without this it would read as a run that settled zero.
        + _na_nodes(unmeasured, "no branch")
    )


def _panel_cost_by_model(metrics):
    models = ["claude-sonnet-5", "claude-opus-5"]
    colors = {"claude-sonnet-5": "evalBlue", "claude-opus-5": "evalViolet"}
    totals = [sum(metrics[k]["cost_by_model"].values()) for k in KEYS]
    ymax, _ = _tex_axis_max(totals, clip_ratio=None, headroom=1.16)
    lines = [
        "\\nextgroupplot[" + _axis_common() + _symbolic_x() +
        "  ybar stacked, bar width=3pt, title={(b) Total cost by model tier},\n"
        f"  ylabel={{USD}}, ymax={ymax:.0f},\n"
        # No interior corner survives: R2 is now the tallest stack by a wide
        # margin, the right-hand runs carry the vertical "unpriced" marks, and
        # a top-left legend lands on R2's bar. Below the axis, as in (a).
        "  legend style={at={(0.5,-0.42)}, anchor=north}, legend columns=2,\n"
        "]\n"
    ]
    for m in models:
        pts = [(metrics[k]["code"], metrics[k]["cost_by_model"].get(m, 0.0)) for k in KEYS]
        lines.append(f"\\addplot[fill={colors[m]}, draw=none] coordinates {{" + _coord_str(pts, "{:.2f}") + "};\n")
    lines.append("\\legend{sonnet-5, opus-5}\n")
    # Kimi and the two gpt56 deployments carry no rate card; mark them so a
    # zero-height stack is not read as "this run was free".
    unpriced = [metrics[k]["code"] for k in KEYS if not metrics[k]["priced"]]
    lines.append(_na_nodes(unpriced, "unpriced"))
    return "".join(lines)


def _compact_codes(codes):
    """["R10", "R11", "R12"] -> "10--12"; non-consecutive stay comma-separated."""
    nums = sorted(int(c.lstrip("R")) for c in codes)
    groups, start, prev = [], nums[0], nums[0]
    for n in nums[1:] + [None]:
        if n == prev + 1:
            prev = n
            continue
        groups.append(str(start) if start == prev else f"{start}--{prev}")
        start = prev = n
    return ", ".join(groups)


def _panel_frontier(metrics):
    """Cost per file against minutes per file — the one panel that shows a
    relationship rather than a per-run value, so it earns space a table cannot."""
    ordered = sorted(
        (
            (metrics[k]["min_per_file"], metrics[k]["cost_per_file"],
             metrics[k]["code"], metrics[k]["harness"])
            for k in KEYS
            if metrics[k]["min_per_file"] is not None
            and metrics[k]["cost_per_file"] is not None
        ),
        key=lambda p: p[0],
    )

    # R10 settled a single git-exact file, which puts it an order of magnitude
    # out on both axes. Scaling to it would collapse the other points into one
    # blob in the corner, so the axes are scaled to the rest and it is called
    # out by name as off-scale instead of being silently clipped away.
    def _limit(values):
        ymax, clipped = capped_limit(values, headroom=1.12)
        return ymax, clipped

    xmax, _ = _limit([p[0] for p in ordered])
    ymax, _ = _limit([p[1] for p in ordered])
    on_scale = [p for p in ordered if p[0] <= xmax and p[1] <= ymax]
    off_scale = [p for p in ordered if p not in on_scale]

    lines = [
        "\\nextgroupplot[" + _axis_common() +
        "  title={(c) Cost--time frontier},\n"
        "  xlabel={Minutes per file}, ylabel={USD per file},\n"
        f"  xmin=0.4, xmax={xmax:.3g}, ymin=0, ymax={ymax:.3g}, enlarge x limits=false,\n"
        "]\n"
    ]

    # The csloop points cluster tightly around (2.6-3.5 min, $0.5-1.0), so a
    # single fixed label anchor overprints them. Anchors alternate around the
    # x-ordered points, which pushes each label away from its nearest neighbour.
    # The labels drop the "R" as well: at 16 runs the cluster is dense enough
    # that a two-character label is the difference between readable and not,
    # and the panel is captioned as carrying run codes.
    # Neighbouring cluster points sit ~1mm apart horizontally at the printed
    # panel width, which is narrower than a label, so the labels alternate
    # *vertically* (above / below the mark) rather than around it: that is the
    # only direction with room left.
    PLACEMENTS = [("south", "3pt"), ("north", "-3pt")]

    def _placement(index, y):
        """Alternate, except against the panel's floor and ceiling.

        A label anchored below its mark falls outside the axis when the mark
        sits near ymin — the cheapest run per file is exactly that case, and its
        label was being clipped away, leaving an unidentified dot. Points in the
        top and bottom bands are therefore forced inward; the rest alternate."""
        if y <= 0.12 * ymax:
            return PLACEMENTS[0]
        if y >= 0.88 * ymax:
            return PLACEMENTS[1]
        return PLACEMENTS[index % len(PLACEMENTS)]

    place_of = {code: _placement(i, y) for i, (_, y, code, _) in enumerate(on_scale)}

    for harness, color in [("ccworkflow", "evalBlue"), ("csloop", "evalOrange")]:
        pts = [p for p in on_scale if p[3] == harness]
        lines.append(
            f"\\addplot[only marks, mark=*, mark size=1.7pt, color={color}] coordinates {{"
            + " ".join(f"({x:.3g},{y:.3g})" for x, y, _, _ in pts)
            + "};\n"
        )
        for x, y, code, _ in pts:
            anchor, yshift = place_of[code]
            lines.append(
                f"\\node[font=\\tiny, color=evalInk, anchor={anchor}, yshift={yshift}, inner sep=0.8pt]\n"
                f"  at (axis cs:{x:.3g},{y:.3g}) {{{code.lstrip('R')}}};\n"
            )

    # Top-left is the one region with no data in it (the fast-and-expensive
    # corner nothing landed in), and the note is set over two lines because a
    # single line of it is wider than the panel and gets clipped mid-word. The
    # "lower-left is better" hint the nine-run version carried is gone: at this
    # density it printed straight through the csloop cluster, and the two axis
    # labels already say which direction is which.
    notes = [
        f"{code} off scale:\\\\{x:.0f}\\,min, \\${y:.0f}/file" for x, y, code, _ in off_scale
    ]

    # A run needs both a per-file cost and a per-file time to be a point here,
    # so runs that settled nothing or carry no rate card cannot appear at all.
    # Listing them stops a reader from reading absence as "not measured" — or,
    # worse, as a point hidden under another.
    absent = {}
    for k in KEYS:
        m = metrics[k]
        if m["min_per_file"] is not None and m["cost_per_file"] is not None:
            continue
        if not m["priced"]:
            reason = "unpriced"
        elif m["files"] is None:
            reason = "no branch"
        else:
            reason = "0 files"
        absent.setdefault(reason, []).append(m["code"])
    if absent:
        # ~26 characters is all a \tiny line gets inside a panel this narrow
        # before the text runs past the axis and is clipped mid-word, so the
        # codes are compacted the same way the point labels are (drop the "R",
        # collapse runs into ranges) and the heading gets a line to itself.
        notes.append("not plotted:")
        notes.extend(f"{_compact_codes(codes)} ({reason})" for reason, codes in absent.items())

    if notes:
        lines.append(
            "\\node[font=\\tiny, color=evalInk, anchor=north west, align=left]\n"
            f"  at (axis cs:0.55,{ymax * 0.99:.3g})\n"
            "  {" + "\\\\".join(notes) + "};\n"
        )
    return "".join(lines)


def _panel_calls_per_file(metrics):
    ymax, clipped = _tex_axis_max([metrics[k]["calls_per_file"] for k in KEYS])
    cc, cs, over, missing = [], [], [], []
    for k in KEYS:
        m = metrics[k]
        v = m["calls_per_file"]
        if v is None:
            missing.append((m["code"], "no branch" if m["files"] is None else "0 files"))
            continue
        if m["code"] in clipped:
            over.append((m["harness"], (m["code"], ymax, f"{v:.0f}\\,$\\uparrow$")))
            continue
        (cc if m["harness"] == "ccworkflow" else cs).append((m["code"], v, f"{v:.0f}"))
    return (
        "\\nextgroupplot[" + _axis_common() + _symbolic_x() + _explicit_labels() +
        "  ybar, bar width=3pt, title={(d) Tool calls per file settled},\n"
        f"  ylabel={{Calls / file}}, ymax={ymax:.0f},\n"
        "]\n"
        "\\addplot[fill=evalBlue, draw=none, bar shift=0pt] coordinates {" + _coord_str_meta(cc) + "};\n"
        "\\addplot[fill=evalOrange, draw=none, bar shift=0pt] coordinates {" + _coord_str_meta(cs) + "};\n"
        + _clip_plot("evalBlue", [p for h, p in over if h == "ccworkflow"])
        + _clip_plot("evalOrange", [p for h, p in over if h == "csloop"])
        + "".join(_na_nodes([c], note) for c, note in missing)
    )


def _panel_input_composition(metrics):
    """100\\% stacked input-side token mix. This is the panel that explains the
    cache-share column in the table: a run with no cache-write at all cannot
    reach the read share the others do."""
    lines = [
        "\\nextgroupplot[" + _axis_common() + _symbolic_x() +
        "  ybar stacked, bar width=3pt, title={(e) Input-side token mix},\n"
        "  ylabel={Input share (\\%)}, ymax=104, ytick={0,25,50,75,100},\n"
        # Every bar is full height here, so there is no interior space at all:
        # the legend has to go under the axis.
        "  legend style={at={(0.5,-0.30)}, anchor=north}, legend columns=3,\n"
        "]\n"
    ]
    for field, color in [("read_share", "evalAqua"), ("write_share", "evalViolet"), ("raw_share", "evalOrange")]:
        pts = [(metrics[k]["code"], metrics[k][field]) for k in KEYS]
        lines.append(f"\\addplot[fill={color}, draw=none] coordinates {{" + _coord_str(pts, "{:.2f}") + "};\n")
    lines.append("\\legend{cache read, cache write, uncached}\n")
    return "".join(lines)


def _panel_tokens_per_file(metrics):
    """Input-side tokens per file settled, log scale. A model-agnostic cost
    proxy: it is the only efficiency panel that can include the non-Anthropic
    run, which has no rate card and therefore no USD figure anywhere else."""
    ymax, clipped = _tex_axis_max(
        [(metrics[k]["tokens_per_file"] / 1e6) if metrics[k]["tokens_per_file"] else None for k in KEYS]
    )
    cc, cs, over, missing = [], [], [], []
    for k in KEYS:
        m = metrics[k]
        if m["tokens_per_file"] is None:
            missing.append((m["code"], "no branch" if m["files"] is None else "0 files"))
            continue
        v = m["tokens_per_file"] / 1e6
        if m["code"] in clipped:
            over.append((m["harness"], (m["code"], ymax, f"{v:.2f}\\,$\\uparrow$")))
            continue
        (cc if m["harness"] == "ccworkflow" else cs).append((m["code"], v, f"{v:.2f}"))
    # Linear, not log. Across the runs that are on scale the spread is about
    # 27x, which a linear axis shows honestly; a log axis would both flatten the
    # very gap the panel exists to show and make the value labels read as log10.
    return (
        "\\nextgroupplot[" + _axis_common() + _symbolic_x() + _explicit_labels() +
        "  ybar, bar width=3pt,\n"
        "  title={(f) Input tokens per file settled},\n"
        f"  ylabel={{M tok / file}}, ymax={ymax:.3g},\n"
        "]\n"
        "\\addplot[fill=evalBlue, draw=none, bar shift=0pt] coordinates {" + _coord_str_meta(cc) + "};\n"
        "\\addplot[fill=evalOrange, draw=none, bar shift=0pt] coordinates {" + _coord_str_meta(cs) + "};\n"
        + _clip_plot("evalBlue", [p for h, p in over if h == "ccworkflow"])
        + _clip_plot("evalOrange", [p for h, p in over if h == "csloop"])
        + "".join(_na_nodes([c], note) for c, note in missing)
    )


def write_tikz_figure(metrics):
    TEX_DIR.mkdir(exist_ok=True)
    body = [
        TEX_DATA_BANNER,
        "%% Six-panel evaluation figure. Requires pgfplots + the groupplots\n"
        "%% library and the evalXxx colors, both set up in jss-submission.sty.\n",
        "\\begin{tikzpicture}\n",
        # vertical sep has to clear a rotated tick-label column plus, under
        # panel (a), the harness legend that no longer fits inside its axis.
        "\\begin{groupplot}[group style={group size=3 by 2, horizontal sep=1.3cm,\n"
        "    vertical sep=2.1cm}]\n",
        _panel_files(metrics),
        _panel_cost_by_model(metrics),
        _panel_frontier(metrics),
        _panel_calls_per_file(metrics),
        _panel_input_composition(metrics),
        _panel_tokens_per_file(metrics),
        "\\end{groupplot}\n",
        "\\end{tikzpicture}\n",
    ]
    out = TEX_DIR / "fig_eval.tex"
    out.write_text("".join(body))
    print(f"wrote {out}")


def write_tikz_colors():
    TEX_DIR.mkdir(exist_ok=True)
    lines = [TEX_BANNER, "%% \\input this in the preamble (or paste into jss-submission.sty).\n"]
    for name, hexval in TEX_COLORS:
        lines.append(f"\\definecolor{{{name}}}{{HTML}}{{{hexval.lstrip('#').upper()}}}\n")
    out = TEX_DIR / "eval_colors.tex"
    out.write_text("".join(lines))
    print(f"wrote {out}")


def write_tex_tables(metrics, coverage, translated_units, decision_models):
    TEX_DIR.mkdir(exist_ok=True)

    # --- Table 1: the per-run numbers the figure deliberately does not repeat.
    rows = []
    for k in KEYS:
        m = metrics[k]
        cost = f"{m['cost']:.2f}" if m["priced"] else "n/a"
        cpf = f"{m['cost_per_file']:.2f}" if m["cost_per_file"] is not None else "--"
        mpf = f"{m['min_per_file']:.1f}" if m["min_per_file"] is not None else "--"
        cpfile = f"{m['calls_per_file']:.1f}" if m["calls_per_file"] is not None else "--"
        # "--" is a metric that does not exist for this run (it settled nothing);
        # "n/a" is one that was not measured (no archival branch in this clone).
        files = m["files"] if m["files"] is not None else "n/a"
        rows.append(
            f"    {m['code']} & {_tex_escape(m['label'])} & {files} & "
            f"{m['minutes']:.0f} & {cost} & {cpf} & {mpf} & {cpfile} & {m['read_share']:.0f} \\\\\n"
        )
    # Column map: 1 code, 2 configuration, 3-5 run totals (files, minutes, USD),
    # 6-8 per-file (USD, minutes, tool calls), 9 cache-read share. The USD total
    # belongs under "Run totals", so the spans are 3-5 and 6-8; cache share sits
    # under neither.
    tbl1 = [
        TEX_DATA_BANNER,
        "\\begin{tabular}{@{}llrrrrrrr@{}}\n",
        "  \\toprule\n",
        "  & & \\multicolumn{3}{c}{Run totals} & \\multicolumn{3}{c}{Per file settled} & \\\\\n",
        "  \\cmidrule(lr){3-5}\\cmidrule(lr){6-8}\n",
        "  & Configuration & Files & Min & USD & USD & Min & Tool calls & Cache \\%\\\\\n",
        "  \\midrule\n",
        *rows,
        "  \\bottomrule\n",
        "\\end{tabular}\n",
    ]
    (TEX_DIR / "tab_runs.tex").write_text("".join(tbl1))
    print(f"wrote {TEX_DIR / 'tab_runs.tex'}")

    # --- Table 2: module coverage (which part of the tree each run reached).
    mods = modules_touched(translated_units)
    all_modules = sorted({m for counts in mods.values() for m in counts})
    cov_rows = []
    for k in KEYS:
        if translated_units[k] is None:
            cells = " & ".join(["n/a"] * len(all_modules))
            cov_rows.append(f"    {RUN_CODES[k]} & {cells} & n/a \\\\\n")
            continue
        counts = mods[k]
        cells = " & ".join(str(counts.get(m, "")) or "--" for m in all_modules)
        cov_rows.append(f"    {RUN_CODES[k]} & {cells} & {sum(counts.values())} \\\\\n")
    tbl2 = [
        TEX_DATA_BANNER,
        "\\begin{tabular}{@{}l" + "r" * (len(all_modules) + 1) + "@{}}\n",
        "  \\toprule\n",
        "  & " + " & ".join(_tex_escape(m) for m in all_modules) + " & Total \\\\\n",
        "  \\midrule\n",
        *cov_rows,
        "  \\bottomrule\n",
        "\\end{tabular}\n",
    ]
    (TEX_DIR / "tab_coverage.tex").write_text("".join(tbl2))
    print(f"wrote {TEX_DIR / 'tab_coverage.tex'}")



def _tikz_decision_axis(width, height):
    """Chrome shared by the three decision panels: no frame, recessive ticks."""
    return (
        f"width={width}, height={height},\n"
        "  axis lines=left, axis line style={draw=none},\n"
        "  tick label style={font=\\scriptsize, /pgf/number format/assume math mode=true},\n"
        "  label style={font=\\scriptsize, color=evalInk},\n"
        "  title style={font=\\scriptsize\\bfseries, yshift=-1pt},\n"
        "  xtick style={draw=none}, ytick style={draw=none},\n"
    )


def _tikz_panel_model_module(by_model, attrs):
    """(a) Model x module heatmap, drawn as explicit cells.

    A numeric axis with hand-written tick labels rather than pgfplots'
    `matrix plot`: cells are inset by 0.04 on each side to keep the 2pt surface
    gap between fills, and a module a model never entered is simply not drawn.
    `matrix plot` would tile the grid edge-to-edge and paint those absences as
    the ramp's lightest step, which is exactly the reading the panel must not
    allow.
    """
    models = sorted(by_model, key=lambda m: -len(by_model[m]["union"]))
    modules = sorted({attrs[u]["top"] for i in by_model.values() for u in i["union"]
                      if attrs.get(u)})
    counts = [[sum(1 for u in by_model[m]["union"]
                   if attrs.get(u) and attrs[u]["top"] == mod)
               for mod in modules] for m in models]
    vmax = max(max(row) for row in counts)

    cells = []
    for i, row in enumerate(counts):
        for j, v in enumerate(row):
            if not v:
                continue
            step = min(int(round((0.34 + 0.66 * v / vmax) * (len(SEQ_BLUE) - 1))),
                       len(SEQ_BLUE) - 1)
            ink = "evalSurface" if step >= 8 else "evalInk"
            cells.append(
                f"\\draw[fill=evalSeq{step}, draw=none] (axis cs:{j + 0.04:.2f},{i + 0.04:.2f})"
                f" rectangle (axis cs:{j + 0.96:.2f},{i + 0.96:.2f});\n"
                f"\\node[font=\\tiny, color={ink}] at (axis cs:{j + 0.5:.2f},{i + 0.5:.2f}) {{{v}}};\n"
            )

    xt = ",".join(f"{j + 0.5:.1f}" for j in range(len(modules)))
    xl = ",".join(_tex_escape(m) for m in modules)
    yt = ",".join(f"{i + 0.5:.1f}" for i in range(len(models)))
    yl = ",".join(_tex_escape(_display_model(m)) for m in models)
    return (
        "\\nextgroupplot[" + _tikz_decision_axis("0.29\\textwidth", "4.3cm") +
        f"  xmin=0, xmax={len(modules)}, ymin=0, ymax={len(models)}, y dir=reverse,\n"
        f"  xtick={{{xt}}}, xticklabels={{{xl}}},\n"
        "  x tick label style={rotate=90, anchor=east, font=\\tiny},\n"
        f"  ytick={{{yt}}}, yticklabels={{{yl}}},\n"
        "  title={(a) Module choice},\n"
        "]\n" + "".join(cells)
    )


def _tikz_panel_targeting(by_model, attrs, pool):
    """(b) Dumbbell: the ready pool's mean fan-in vs each model's own."""
    import statistics

    pool_mean = statistics.mean(attrs[u]["fanin"] for u in pool)
    models = sorted(by_model, key=lambda m: -len(by_model[m]["union"]))
    n = len(models)
    lines, pool_pts, model_pts, labels = [], [], [], []
    xmax = 0.0
    for i, m in enumerate(models):
        units = [u for u in by_model[m]["union"] if attrs.get(u)]
        mean = statistics.mean(attrs[u]["fanin"] for u in units)
        y = n - 1 - i
        xmax = max(xmax, mean)
        lines.append(f"\\draw[evalBlue, line width=1pt] (axis cs:{pool_mean:.3f},{y})"
                     f" -- (axis cs:{mean:.3f},{y});\n")
        pool_pts.append(f"({pool_mean:.3f},{y})")
        model_pts.append(f"({mean:.3f},{y})")
        labels.append(
            f"\\node[font=\\tiny, color=evalInk, anchor=west] at (axis cs:{mean:.3f},{y})"
            f" {{\\hspace{{4pt}}{mean / pool_mean:.1f}$\\times$ (n={len(units)})}};\n"
        )
    yl = ",".join(_tex_escape(_display_model(m)) for m in reversed(models))
    return (
        "\\nextgroupplot[" + _tikz_decision_axis("0.28\\textwidth", "4.3cm") +
        "  xmajorgrids, grid style={draw=evalGrid, line width=0.4pt},\n"
        # ymin is pulled well below the last row on purpose: the reference-line
        # label lives in that band, and anywhere higher it collides with either
        # the bottom dumbbell or the title.
        f"  xmin=0, xmax={max(7.5, xmax * 2.0):.1f}, xtick={{0,2,4,6}}, ymin=-1.25, ymax={n - 0.3},\n"
        f"  ytick={{{','.join(str(i) for i in range(n))}}}, yticklabels={{{yl}}},\n"
        "  xlabel={Mean fan-in of files chosen},\n"
        "  title={(b) Targeting vs.\\ roadmap},\n"
        "]\n"
        # Reference first, so the dumbbells sit over it.
        f"\\draw[evalAxis, line width=0.5pt] (axis cs:{pool_mean:.3f},-1.25)"
        f" -- (axis cs:{pool_mean:.3f},{n - 0.3});\n"
        f"\\node[font=\\tiny, color=evalInk, anchor=south west, align=left]"
        f" at (axis cs:{pool_mean:.3f},-1.18) {{\\hspace{{2pt}}ready pool}};\n"
        + "".join(lines)
        + "\\addplot[only marks, mark=*, mark size=1.3pt, color=evalAxis, forget plot]\n"
          "  coordinates {" + " ".join(pool_pts) + "};\n"
        + "\\addplot[only marks, mark=*, mark size=2.1pt, color=evalBlue, forget plot]\n"
          "  coordinates {" + " ".join(model_pts) + "};\n"
        + "".join(labels)
    )


def _tikz_panel_agreement(buckets, n_models):
    """(c) Distinct files by how many models independently settled them."""
    ns = sorted(buckets, reverse=True)
    total = sum(len(v) for v in buckets.values())
    n = len(ns)
    bars, labels = [], []
    for i, k in enumerate(ns):
        v = len(buckets[k])
        y = n - 1 - i
        step = min(k - 1, len(ORD_BLUE) - 1)
        bars.append(f"\\addplot[xbar, fill=evalOrd{step}, draw=none, bar width=7pt,"
                    f" forget plot] coordinates {{({v},{y})}};\n")
        labels.append(
            f"\\node[font=\\tiny, color=evalInk, anchor=west] at (axis cs:{v},{y})"
            f" {{\\hspace{{3pt}}{v} ({100 * v / total:.0f}\\%)}};\n"
        )
    yl = ",".join(f"{k} of {n_models}" for k in reversed(ns))
    return (
        "\\nextgroupplot[" + _tikz_decision_axis("0.22\\textwidth", "4.3cm") +
        "  xmajorgrids, grid style={draw=evalGrid, line width=0.4pt},\n"
        f"  xmin=0, xmax={total * 1.55:.0f}, xtick={{0,25,50}}, ymin=-0.7, ymax={n - 0.3},\n"
        f"  ytick={{{','.join(str(i) for i in range(n))}}}, yticklabels={{{yl}}},\n"
        "  xlabel={Distinct files},\n"
        "  title={(c) Cross-model agreement},\n"
        "]\n" + "".join(bars) + "".join(labels)
    )


def _tikz_panel_unblocking(unblocking):
    """(d) Files unblocked downstream per file settled -- the outcome panel.

    Open bars rather than a pattern fill for the lower-bound runs: pgfplots
    would need the patterns library for a hatch, and an unfilled bar carries
    the same "not a measurement" reading without adding a package the paper
    would have to load.
    """
    order = [k for k in KEYS if k in unblocking]
    solid, open_ = [], []
    vmax = 0.0
    for k in order:
        settled, newly, ok = unblocking[k]
        v = newly / settled
        vmax = max(vmax, v)
        (solid if ok else open_).append(f"({RUN_CODES[k]},{v:.3f})")
    codes = ",".join(RUN_CODES[k] for k in order)
    plots = ""
    if solid:
        plots += ("\\addplot[ybar, fill=evalBlue, draw=none, bar width=4pt, bar shift=0pt]\n"
                  "  coordinates {" + " ".join(solid) + "};\n")
    if open_:
        plots += ("\\addplot[ybar, fill=none, draw=evalBlue, line width=0.6pt, bar width=4pt,\n"
                  "  bar shift=0pt] coordinates {" + " ".join(open_) + "};\n")
    return (
        "\\nextgroupplot[" + _tikz_decision_axis("0.29\\textwidth", "4.3cm") +
        "  ymajorgrids, grid style={draw=evalGrid, line width=0.4pt},\n"
        f"  symbolic x coords={{{codes}}}, xtick={{{codes}}},\n"
        "  x tick label style={rotate=90, anchor=east, font=\\tiny},\n"
        f"  ymin=0, ymax={vmax * 1.18:.2f}, enlarge x limits=0.06,\n"
        "  ylabel={Unblocked / file}, ylabel near ticks,\n"
        "  ylabel style={font=\\scriptsize, yshift=-6pt},\n"
        "  title={(d) Did the choice unblock work?},\n"
        "]\n" + plots
    )


def write_tikz_decision_figure(translated_units, decision_models):
    """The decision-making figure as pgfplots, mirroring fig6_decision_making.png.

    Same numbers, same palette steps, same panel order as the PNG -- the paper
    gets a vector copy that picks up the document's fonts, and there is still
    one source of truth behind both.
    """
    by_model = files_by_decision_model(translated_units, decision_models)
    attrs = fork_point_roadmap(EXPERIMENTS, RUNS, translated_units)
    pool = ready_pool(attrs)
    buckets, n_models = model_settlement_frequency(translated_units, decision_models)
    unblocking = unblocking_per_run(translated_units)

    body = [
        TEX_DATA_BANNER,
        "%% Decision-making figure. Requires pgfplots + the groupplots library\n"
        "%% and the evalXxx colours, both set up in jss-submission.sty.\n"
        "%% Runs are collapsed to the model that CHOSE the files: the run's own\n"
        "%% model for csloop, the TRIAGE model for ccworkflow (author and\n"
        "%% integrate agents do not select). Counts are over DISTINCT files, so a\n"
        "%% model with four runs cannot out-vote one with a single run by\n"
        f"%% repeating itself. Fan-in and readiness come from the doxygen map\n"
        f"%% reconstructed at the shared fork point: {len(attrs)} untranslated files,\n"
        f"%% {len(pool)} ready leaves. In (a) an empty cell means the model never\n"
        "%% entered that module at all, not that it entered and settled nothing.\n",
        "\\begin{tikzpicture}\n",
        "\\begin{groupplot}[group style={group size=2 by 2, horizontal sep=1.5cm,\n"
        "    vertical sep=1.9cm}]\n",
        _tikz_panel_model_module(by_model, attrs),
        _tikz_panel_targeting(by_model, attrs, pool),
        _tikz_panel_agreement(buckets, n_models),
        _tikz_panel_unblocking(unblocking),
        "\\end{groupplot}\n",
        "\\end{tikzpicture}\n",
    ]
    out = TEX_DIR / "fig_decision.tex"
    out.write_text("".join(body))
    print(f"wrote {out}")


def main():
    runs, cc_rows, cs_rows = load_run_aggregates()
    print(f"ccworkflow rows: {len(cc_rows)}, csloop rows: {len(cs_rows)}")

    coverage = {k: coverage_for_run(EXPERIMENTS / k[0] / k[1]) for k in KEYS}
    for k, c in coverage.items():
        print(f"{k}: {c}")

    files_settled = load_files_settled()
    for k, f in files_settled.items():
        print(f"{k}: files settled (git-exact) = {f}")

    translated_units = load_translated_units()
    decision_models = decision_model_per_run(cc_rows, cs_rows)
    for k in KEYS:
        print(f"{k}: decided by {decision_models[k]}")

    wall_times = load_wall_times(cs_rows)
    for k, s in wall_times.items():
        print(f"{k}: wall time {s/60:.1f} min" if s else f"{k}: wall time unknown")

    tool_calls_per_file = load_tool_calls_per_file(cc_rows, cs_rows, files_settled)
    for k, t in tool_calls_per_file.items():
        print(f"{k}: {t}")

    metrics = derived_metrics(runs, files_settled, wall_times, tool_calls_per_file)

    make_standalone_figures(runs, coverage, files_settled, wall_times, tool_calls_per_file)
    _bump_fonts_for_combined()
    make_combined_figure(runs, coverage, files_settled, wall_times, tool_calls_per_file)
    make_decision_figure(translated_units, decision_models)
    write_summary_tables(runs, coverage, files_settled, translated_units, wall_times, tool_calls_per_file,
                         decision_models)

    # LaTeX/TikZ artifacts consumed directly by the paper.
    write_tikz_colors()
    write_tikz_figure(metrics)
    write_tikz_decision_figure(translated_units, decision_models)
    write_tex_tables(metrics, coverage, translated_units, decision_models)


if __name__ == "__main__":
    main()
