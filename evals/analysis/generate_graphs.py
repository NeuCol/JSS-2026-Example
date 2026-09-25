#!/usr/bin/env python3.10
"""Generate the paper figures + summary tables for the 08-27/08-28-2026 and
09-12-2026 evaluation of the mcfm-translate transformation.

Scope is three days on purpose, and it is what makes the cost comparison mean
anything. All twelve branches in RUNS below fork from the same submodule
commit (git merge-base against git_file_counts.BASE_REF is that commit exactly
for every one of them, the 09-12 run included), and their fork-point roadmaps
reconstruct to the same 445-file candidate set, agreeing to within three rows
run-to-run. So cost, wall time and tokens divide by a files-settled number
drawn from one shared pool of work, which is the premise a cost-per-file number
needs and does not survive being computed across days that forked from
different roadmap states. The earlier corpus (07-24/07-25-2026 and 08-11-2026
through 08-26-2026) is still on disk under experiments/ and still parses where
its layout allows, but it is out of scope here for exactly that reason.

WHICH ccloop RUN IS IN SCOPE, AND WHY IT REPLACED TWO. The 2026-09-11 revision
of this file carried the first two ccloop runs,
09-11-2026/ccworkflow-loop-opus-5 and .../ccworkflow-loop-sonnet-5. Both are
superseded here by the single
09-12-2026 run, on the choice recorded in RUNS: the 09-12 run is the only
ccloop run that took the loop pattern to its designed stopping point -- five
loops against a five-loop cap, three groups completed, every one of its 15
units retired, and the last three loops spent holding at a blocked approval
gate rather than translating. The 09-11 opus-5 run ran the same five loops but
settled 9 units, all in W2jet, so it never entered a second module; the 09-11
sonnet-5 run exited after a single loop on the reviewer's no-pending-items
condition and is one loop of work, not a run. Both remain on disk under
experiments/09-11-2026/ and both still parse, exactly like the earlier
out-of-scope corpus; nothing was deleted. The cost of this choice
is sample size, and it is stated everywhere it bites: ccloop is now ONE run, so
every ccloop number in every figure and table is a single observation, and no
ccloop claim below is a claim about a distribution.

THREE HARNESSES, TWO VARIABLES. The corpus covers two design patterns across
two baseline agents, and which pair you read tells you which variable is held
fixed:

                      | CodeScribe baseline | Claude Code baseline
    loop pattern      | csloop              | ccloop
    multi-agent flow  | (none)              | ccworkflow

  ccloop vs. csloop      one design pattern over one task, varying EXECUTION
                         POLICY. Both are a bounded author->review loop; the
                         loop workflow (.claude/workflows/loop.js) is
                         deliberately shaped after CodeScribe's prompt_loop,
                         and both authors work the same Spec and Plan (csloop's
                         task file only tells it to read those two files, and
                         its author's first two tool calls are those reads). The
                         difference under test is that CodeScribe ENFORCES its
                         shell allowlist, per-phase iteration and tool caps,
                         repeated-call blocking and a protected task file in
                         code, while the loop workflow states the same rules as
                         prose to an agent with an unrestricted shell. Replaying
                         the Claude Code runs' Bash calls against CodeScribe's
                         own validator rejects 93-96% of them, 96% for the
                         ccloop run R12 (shell_policy.py), so this is a large
                         intervention rather than a detail. Read
                         a gap here as the cost of bounded execution -- with the
                         budget caveat in BUDGET_NOTE, which is a calibration
                         error on top of it.
  ccloop vs. ccworkflow  one baseline agent, two design patterns. Same Claude
                         Code agent, same transformation, one running a loop
                         and one running the five-phase group-at-a-time
                         approval-gated workflow.
Neither comparison existed before 09-11-2026: every ccworkflow/csloop pair in
the corpus differs in both dimensions at once, so nothing in it could separate
"a better agent" from "a better design pattern". The ccloop cell is what closes
that.

Read both comparisons with their sample sizes in view. ccloop is ONE run;
ccworkflow is three and csloop eight. Every ccloop bar, row and C6 column below
is a single observation, and the opus-5 comparisons it supports (C6 against C3
for execution policy, R12 against R2 for design pattern) are one-against-three
and one-against-one. Direction is worth reading; magnitude is not worth more
than a sentence of hedging.

R12 ran its full budget of five author->review loops and did not stop early.
The shape of that budget matters for reading its totals: loops 1 and 2 opened
and completed all three of its groups, and loops 3-5 found the approval gate
blocked (three completed groups against a limit of three), so they re-verified
the settled tree, audited it, and translated nothing. Three of the run's five
loops and 81 of its 238 tool calls (34%) are that hold, and $14.72 of its
$53.16. It is the loop pattern meeting the same human-approval gate ccworkflow
meets, not idle time -- but it does mean R12's cost-per-file is not its cost
divided by five loops of translation.

Runs covered: three ccworkflow arms (opus-5 triage/dispatch x2, sonnet-5
triage/dispatch with opus-5 integrate x2 -- one of each is 08-27, one is
08-28), eight csloop arms (opus-5 x3, sonnet-5 x2, gpt-5.6 x3), and one ccloop
arm (opus-5, 09-12).
08-27-2026/ccworkflow-opus-5 ("R1" in that older single-day corpus's own
numbering -- NOT the current R1 below, which is a different run) was dropped
from this set: at 2 files settled it was a clear outlier for its own config,
and 08-28-2026/ccworkflow-opus-5 -- same triage/dispatch model, same fork
point -- settled 15, which is what motivated pulling in the whole 08-28-2026
day rather than trying to patch the one run. Every other archive
carries a complete loop/metadata or workflow-wf_* record, an agent_log.md, and
an archival git branch in this clone; the one exception is
08-28-2026/codescribe-sonnet-5-run3, which ran five loop iterations but never
had an agent_log.md archived (`parse_coverage.coverage_for_run` reports it as
"no agent_log archived", the same status the corpus already has a code path
for). It is kept in the corpus rather than dropped, since its git-exact count
is still real ground truth (2 files, both shadowed -- see SHADOW_NOTE), but it
carries no self-reported checklist or pass rate. The two gpt-5.6 runs log no
model reasoning text, which is a property of the OpenAI-compatible gateway
rather than of the run, and is true of every gpt56 run in the corpus.

"Files settled" throughout is the git-exact count from git_file_counts.py (the
software/mcfm submodule branch for each run), not the agent's own in-loop
checklist in agent_log.md — the two can disagree (see git_file_counts.py's
docstring), and the submodule diff is ground truth. That count unions two
shapes of translation, and the difference is reported rather than buried:
  - retired: the Fortran original was moved into deprecated/ or deleted, which
    is the transformation actually completing for that unit.
  - shadowed: the .cpp landed but the original is still in the tree, so the
    module now has two live implementations. The work was done and paid for in
    tokens, so it counts toward files settled and the run's cost-per-file; but
    the unit is not finished, and the `not retired` column in the coverage
    table is where that shows up. Most runs that shadow anything shadow exactly
    the same two units (Mods/pp_mod, Mods/ppwp2j_mod) — see summary_tables.md
    for the exact count, which is generated, not hand-maintained here — so this
    is a property of how that pair of Fortran modules is written, not a
    per-model failure.
A run whose archival branch never reached this clone would have no git-exact
count at all — None, not zero, drawn as an explicit "n/a (no branch)". No run
in the current scope is in that position.

Run with: python3.10 analysis/generate_graphs.py
(Needs Python 3.10+ for tomllib, or `pip install tomli` on older Pythons.)

Reads only from experiments/ (read-only). Writes, under analysis/figures/:
  fig1_cost_and_cache.png        - standalone, compact
  fig3_coverage.png              - standalone, compact
  fig4_wall_time.png             - standalone, compact
  fig5_tool_calls_per_file.png   - standalone, compact
  fig_combined.png               - the six panels used as the paper's single figure
(the fig2 slot held a retired reasoning comparison; the remaining files keep
their names so existing \includegraphics paths in the paper still resolve)
and analysis/summary_tables.md (the numeric source of truth behind every panel).

Also writes, under analysis/data/, the machine-readable per-file effort tables
that per_file_effort.py builds -- per_file_effort.csv (one row per run and
translated file), per_file_effort_by_config.csv (one row per configuration and
file) and per_file_effort_runs.csv (per-run attribution method and its
caveats). Those exist so plotting code reads a number rather than re-deriving
an attribution, and so a figure and a table cannot disagree. Read
per_file_effort.py before using them: ccworkflow effort is measured per file
while csloop and ccloop effort is apportioned to files, the two are not the
same measurement, and every exported row carries a `method` column saying which
it is. ccloop and csloop share the apportioned method exactly, which is what
makes their per-file columns directly comparable to each other.

The per-run CSV exports cover exactly the runs in RUNS, so dropping the 09-11
ccloop pair from scope drops their rows from data/ as well; they come back only
by being re-added to RUNS and regenerating.

For the csloop runs only, per_file_effort.py also has a third, tighter method,
"timed" -- it reads logs/toolusage.toml for real per-tool-call durations and
per-iteration token usage instead of splitting a whole loop phase's totals by
raw call count. It is exported alongside the apportioned tables as
per_file_effort_timed.csv and per_file_effort_timed_runs.csv, and shown next
to the apportioned numbers in summary_tables.md's per-file section -- see that
module's docstring for exactly what "timed" can and can't measure.

There are two six-panel figures and they are not the same figure. The PNG
(fig_combined.png) shows per-run totals: cost by model, cache share, files,
wall time, tool calls per file, and self-reported correctness. The pgfplots
version the paper actually renders (write_tikz_figure -> tex/fig_eval.tex)
deliberately does NOT mirror those, because a table already reports per-run
totals better than a bar chart can; it carries what a table reads poorly, namely
normalized cost and throughput, the cost/speed frontier, the cost split by model
tier, and the input-token composition behind the cache-share differences.

The PNG keeps its self-reported-correctness panel, and it should be read for
what it is worth, which is little: every run that reported at all reported
272/272, including two runs that retired no Fortran source, so the suite is
passing because nothing it covers changed. The panel is flat by construction.
The pgfplots figure omits it for that reason.

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
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import (CCLOOP, CCWORKFLOW, CSLOOP, HARNESSES, harness_of,
                     is_claude_code, verify_harness_names)
from parse_ccworkflow import parse_all_ccworkflow, round_summary
from parse_ccloop import parse_all_ccloop, loop_summary
from parse_csloop import parse_all_csloop, manifest_run_info
from parse_coverage import coverage_for_run
from pricing import cost, PRICING, NON_ANTHROPIC
from git_file_counts import (translated_file_count, translated_file_units, module_of,
                             unit_breakdown)
from parse_roadmap import fork_point_roadmap
from per_file_effort import per_file_effort, per_file_effort_timed
from parse_decision_timeline import module_entry_order
import shell_policy
from bash_error_rates import bash_error_rates as load_bash_error_rates_raw

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = REPO_ROOT / "experiments"
FIGURES_DIR = Path(__file__).resolve().parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)
# Machine-readable exports of numbers the summary tables round for reading.
# Plotting code (here or elsewhere) should read these rather than re-deriving
# an attribution, so a figure and a table can never disagree.
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

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
# Run identity / labeling — the 08-27/08-28-2026 corpus
#
# One ordered registry of (day, run_dir, code, label); KEYS, RUN_LABELS,
# RUN_CODES and the figure captions are all derived from it, so adding a run is
# a one-line change here and nowhere else. Each run's folder (day/run_dir under
# experiments/) is also the source of the "Run manifest" table in
# summary_tables.md, so a reader can go from a bar/row straight back to the
# archive on disk.
#
# Codes are sequential (R1..R12) and grouped by harness/decision-model rather
# than by wall-clock start or archival day: all three ccworkflow runs first,
# then the three csloop opus-5 runs, then the two csloop sonnet-5 runs, then
# the three csloop gpt-5.6 runs, then the one ccloop run (see RUN_GROUPS) — so
# a same-config replicate always sits next to the run(s) it replicates,
# regardless of which day it was archived on. Renumbered to this
# grouped-sequential scheme on 2026-08-31; earlier revisions of this file used a
# sparser R2/R8/R9/... scheme left over from when a run was dropped from a
# larger corpus (see the module docstring) — the codes here are NOT
# position-comparable with that older scheme.
#
# The ccloop block is appended at the END rather than slotted next to the other
# Claude Code harness, which grouping alone would argue for. R1..R11 are cited
# by code in the paper and in the archived Zenodo snapshot, and renumbering them
# to make room would silently repoint every one of those references; a new group
# at the tail is the only addition that leaves existing codes meaning what they
# already meant. Read the ordering as "groups, in the order they entered the
# corpus", not as a claim that ccloop belongs furthest from ccworkflow.
#
# R12 IS NOT THE R12 OF THE 2026-09-11 REVISION. That revision carried two
# ccloop runs, 09-11-2026/ccworkflow-loop-opus-5 (R12) and
# .../ccworkflow-loop-sonnet-5 (R13); both were superseded on 2026-09-13 by the
# single 09-12-2026 run below, which is the same loop design driven by the same
# model as the old R12 but settles more of the shared roadmap (15 files across
# W2jet and BDK, against the old R12's 9 in W2jet alone). The old pair is
# still on disk under experiments/09-11-2026/ and still parses; out of the figure
# set, not deleted. R13 no longer exists as a code. Anything citing R12 or R13
# from before 2026-09-13 is citing different runs.
#
# THE 09-12 RUN'S DIRECTORY NAME IS WRONG AND THE LABEL HERE DELIBERATELY
# DISAGREES WITH IT. The archive is named `ccworkflow-loop-sonnet-5-run2` and
# its archive_summary.json repeats that as `experiment_name`, but every Author
# and Review agent in its transcripts reports `"model":"claude-opus-5"` (the
# only sonnet-5 agent is the archival Metadata agent, which translates nothing
# and decides nothing). The run is an opus-5 run mis-titled at archival time,
# the way 08-11-2026/csloop-opus-5's archive_summary names a branch that does
# not exist (see git_file_counts). The directory keeps its name, because that
# name is also its archival git branch in software/mcfm; every label, config
# and model attribution in this analysis follows the transcripts instead —
# `decision_model_per_run` reads the model off the archive, so nothing but this
# hand-written label ever depended on the folder.
#
# The ccworkflow labels name the TRIAGE model, because triage is what picks the
# files (see DECIDING_PHASE below). R1 and R3 also run opus-5 as their
# integrate model, which is where most of their cost lands but none of their
# file choices; R2 runs opus-5 for every phase. ccloop and csloop each drive
# every phase with one model, so their labels name it without qualification.
# ---------------------------------------------------------------------------
RUNS = [
    ("08-27-2026", "ccworkflow-sonnet-5-opus-5-integrate-run3", "R1",
     "ccworkflow (sonnet-5 triage and dispatch, opus-5 integrate)"),
    ("08-28-2026", "ccworkflow-opus-5", "R2",
     "ccworkflow (opus-5 triage and dispatch)"),
    ("08-28-2026", "ccworkflow-sonnet-5-opus-5-integrate-run4", "R3",
     "ccworkflow (sonnet-5 triage and dispatch, opus-5 integrate, run2)"),
    ("08-27-2026", "codescribe-opus-5", "R4", "csloop opus-5"),
    ("08-27-2026", "codescribe-opus-5-run2", "R5", "csloop opus-5 (run2)"),
    ("08-28-2026", "codescribe-opus-5", "R6", "csloop opus-5 (run3)"),
    ("08-27-2026", "codescribe-sonnet-5-run2", "R7", "csloop sonnet-5 (run2)"),
    ("08-28-2026", "codescribe-sonnet-5-run3", "R8",
     "csloop sonnet-5 (run3, incomplete — no agent_log archived)"),
    ("08-27-2026", "codescribe-oaic-gpt56sol-run4", "R9", "csloop gpt-5.6 (run4)"),
    ("08-27-2026", "codescribe-oaic-gpt56sol-run5", "R10", "csloop gpt-5.6 (run5)"),
    ("08-28-2026", "codescribe-oaic-gpt56sol-run6", "R11", "csloop gpt-5.6 (run6)"),
    ("09-12-2026", "ccworkflow-loop-sonnet-5-run2", "R12", "ccloop opus-5"),
]

# Group boundaries, in the same order as RUNS above — used to build the
# "Run manifest" table in summary_tables.md. A run's folder path lets a reader
# go straight from a table row or figure bar back to the archive on disk.
RUN_GROUPS = [
    ("ccworkflow", 3),
    ("csloop opus-5", 3),
    ("csloop sonnet-5", 2),
    ("csloop gpt-5.6", 3),
    ("ccloop", 1),
]

# Replicate sets. RUN_GROUPS above buckets by harness and author model, which
# puts all three ccworkflow runs in one bucket even though R2 drives every
# phase with opus-5 while R1/R3 author on sonnet-5 and only integrate on
# opus-5. Those are different configurations, not replicates of each other, so
# anything that averages over "the same setup run twice" -- per-file effort in
# particular -- has to split them. CONFIGS is that finer partition: two runs
# share a config only if the same models ran the same phases.
#
# C2 and C6 each have a single member. C2's would-be replicate,
# 08-27-2026/ccworkflow-opus-5, is the run the module docstring explains was
# dropped from the corpus; C6 is the only ccloop run in scope. "core" or "mean"
# for either is one observation and must be read as such.
CONFIGS = [
    ("C1", "ccworkflow (sonnet-5 triage and dispatch, opus-5 integrate)", ["R1", "R3"]),
    ("C2", "ccworkflow (opus-5 all phases)", ["R2"]),
    ("C3", "csloop opus-5", ["R4", "R5", "R6"]),
    ("C4", "csloop sonnet-5", ["R7", "R8"]),
    ("C5", "csloop gpt-5.6", ["R9", "R10", "R11"]),
    ("C6", "ccloop opus-5", ["R12"]),
]

KEYS = [(day, run_name) for day, run_name, _, _ in RUNS]
RUN_LABELS = {(day, run_name): label for day, run_name, _, label in RUNS}
# Short x-axis codes — keeps bars legible even in the compact standalone
# figures; each figure captions the full mapping once, below the plot.
RUN_CODES = {(day, run_name): code for day, run_name, code, _ in RUNS}
KEY_BY_CODE = {code: (day, run_name) for day, run_name, code, _ in RUNS}
CONFIG_LABELS = {code: label for code, label, _ in CONFIGS}
CONFIG_KEYS = {code: [KEY_BY_CODE[r] for r in members] for code, _, members in CONFIGS}
CONFIG_OF_RUN = {
    KEY_BY_CODE[r]: code for code, _, members in CONFIGS for r in members
}
CONFIGS_BY_CODE = [(code, members) for code, _, members in CONFIGS]

# Which configurations the per-file effort comparison intersects, and which it
# prints. Both are explicit rather than derived, because the two exclusions are
# judgements about the corpus and not facts a rule could read off it:
#   - C2 and C6 are printed but not intersected: each has one run, so requiring
#     either would let a single run decide the comparison set. Their columns
#     are one observation and the tables label them as such.
#   - C4 is neither intersected nor printed: it settled only Mods/pp_mod and
#     Mods/ppwp2j_mod, so intersecting it collapses the comparison to two rows
#     and printing it leaves a column that is empty on every other row. Its
#     per-file numbers are still in both CSV exports.
# C6 worked only in W2jet and BDK, so its column is blank on the Mods rows.
# That is a real difference in where the run went, not a gap in the
# measurement, and the per-configuration table prints it for the rows where a
# like-for-like comparison against C1/C3/C5 does exist.
PER_FILE_COMPARISON_CONFIGS = ["C1", "C3", "C5"]
PER_FILE_DISPLAY_CONFIGS = ["C1", "C2", "C3", "C5", "C6"]


def _wrap_to_figure(text, fig_width_in, fontsize=None):
    """One caption string -> lines that fit inside `fig_width_in`.

    A single un-wrapped line makes `bbox_inches="tight"` grow the saved canvas
    to the width of the *text*, which strands the panels in the middle of a very
    wide image. That used to be a risk only for the run-code mapping; it became
    a live one for the prose notes too once DESIGN_NOTE grew, so every caption
    line goes through this now rather than just the mapping.
    """
    import textwrap

    fontsize = fontsize or CAPTION_SIZE
    # ~0.52 em per character is the measured average for DejaVu Sans at these
    # sizes; close enough to keep the wrapped text inside the axes width.
    chars = max(40, int(fig_width_in * 72 / (0.52 * fontsize)))
    return textwrap.wrap(text, chars)


def wrap_notes(fig_width_in, notes, fontsize=None):
    """Several caption strings -> one flat list of wrapped lines.

    Callers size the caption strip from `len()` of this, so the wrapping has to
    happen here at assembly time and not inside save_fig — by then the rect is
    already reserved and extra lines would run under the panels.
    """
    lines = []
    for note in notes:
        lines.extend(_wrap_to_figure(note, fig_width_in, fontsize))
    return lines


def run_code_caption(fig_width_in, fontsize=None):
    """The code→configuration mapping, wrapped to the figure it sits under."""
    text = "  |  ".join(f"{code} = {label}" for _, _, code, label in RUNS)
    return _wrap_to_figure(text, fig_width_in, fontsize)


# No run here is another run's reasoning ON/OFF control -- but the runs do NOT
# all reach "reasoning on" through the same knob, and saying only the former hid
# that. Read off the archives, the corpus splits in two:
#   thinking, adaptive   the eight Anthropic csloop runs (R4-R8), which set
#                        `reason=true` and record
#                        `thinking=display:summarized,type:adaptive`.
#   effort=high          every ccworkflow and ccloop run (an `effort` on each
#                        assistant message -- including the 09-12 run, which
#                        passed no effort argument and took the session default),
#                        AND the gpt-5.6 csloop runs (R9-R11), whose manifests
#                        record `reasoning_effort=high`.
# So the split is not harness-shaped: it separates the Anthropic csloop arm from
# everything else. That is an uncontrolled difference between arms rather than a
# control within one, and the run manifest prints the setting per run.
REASONING_NOTE = (
    "Reasoning is on everywhere it can be, but not via one knob: the Anthropic csloop runs use "
    "adaptive thinking, while every Claude Code run and the gpt-5.6 runs use effort=high (per-run "
    "settings are in the manifest table). No run is another run's reasoning ON/OFF control."
)
SCOPE_NOTE = (
    "Scope: the twelve 08-27/08-28-2026 and 09-12-2026 runs. All fork from one submodule "
    "commit and one 445-file roadmap, so per-file cost divides comparable work; earlier days "
    "did not and are out of scope. ccloop is a single run (R12), so read every ccloop bar as "
    "one observation."
)
# What the three harnesses are a design for, and which pair isolates what.
# Repeated on the figures because the run codes alone do not say it, and a
# reader comparing two bars needs to know which variable is being held fixed.
#
# An earlier revision of this note said ccloop vs. csloop varied "the baseline
# agent", which named the wrong variable and undersold the comparison. The two
# arms run the same design pattern over the same Spec and Plan -- csloop's task
# file is eighteen lines whose content is "read current_plan.md, then
# desired_spec.md", and its author's first two tool calls in every archived run
# are those two reads. What actually separates them is EXECUTION POLICY:
# CodeScribe enforces a bounded shell, per-phase iteration and tool caps,
# repeated-call blocking and a protected task file in code (codescribe/lib/
# _agent.py AgentPolicy, _tools.py BashTool), while the loop workflow states the
# same rules as prose to an agent holding an unrestricted shell. That is the
# intervention under test, not a nuisance variable, and shell_policy.py sizes it
# from the archives rather than asserting it here.
DESIGN_NOTE = (
    "Three harnesses, two variables: ccloop vs. csloop is one design pattern (a bounded "
    "author-review loop) over one Spec/Plan, varying execution policy -- csloop enforces a "
    "bounded shell and per-phase caps in code, ccloop states the same rules as prose to an "
    "unrestricted agent; ccloop vs. ccworkflow is one baseline agent (Claude Code) under two "
    "design patterns (loop vs. multi-agent workflow)."
)


def _ccloop_shell_divergence():
    """(low, high) share of ccloop Bash calls CodeScribe's shell would refuse.

    Computed from the archives by shell_policy.py, not asserted, so adding a
    ccloop run moves the number in the note. Cached because the notes are
    emitted into several figures and the tables.
    """
    global _SHELL_DIVERGENCE
    if _SHELL_DIVERGENCE is None:
        ccloop_runs = [r for r in RUNS if harness_of(r[1]) == CCLOOP]
        summary = shell_policy.divergence_summary(EXPERIMENTS, ccloop_runs)
        _SHELL_DIVERGENCE = summary["range"]
    return _SHELL_DIVERGENCE


_SHELL_DIVERGENCE = None


def policy_note():
    """POLICY_NOTE with the measured divergence filled in.

    Emitted into summary_tables.md only, not onto the figures: the figure
    captions are already a stack of unwrapped single lines wide enough to
    stretch the saved canvas past the panels, and this is the longest note of
    the set. The tables are where a reader goes for the caveat anyway.
    """
    span = _ccloop_shell_divergence()
    if span is None:
        return (
            "ccloop vs. csloop varies execution policy: CodeScribe enforces its shell and "
            "per-phase caps in code, the loop workflow states them as prose. No ccloop "
            "transcript in scope, so the size of the difference is not measured here."
        )
    low, high = span
    # One ccloop run in scope collapses the range to a point, and printing
    # "96%-96%" would invent a spread the corpus does not have.
    rejected = f"{low:.0%}" if low == high else f"{low:.0%}-{high:.0%}"
    return (
        "Execution policy is the variable in ccloop vs. csloop, and it is large: replaying the "
        f"ccloop run's Bash calls against CodeScribe's own bounded shell rejects {rejected} "
        "of them (shell_policy.py; mostly pipes, redirects and chaining, which that shell bans "
        "outright, plus `cd`, which it has no need for). CodeScribe also enforces per-phase "
        "iteration and tool-call caps, repeated-call blocking and a protected task file in code; "
        "the loop workflow states all of it as prose. Read a ccloop-vs-csloop gap as the cost of "
        "that policy, not as a property of the baseline agent."
    )


# The one part of the ccloop/csloop contrast that is an error rather than the
# intervention, and the figures cannot show it, so it is stated once here.
#
# A clean enforced-vs-advisory contrast states the SAME budget in the SAME unit
# and varies only whether it is enforced. R12 did not get that. csloop's binding
# constraint is AgentPolicy.max_iterations = 30 MODEL TURNS, and a CodeScribe
# turn carries several tool calls (measured over all 72 archived phases in scope
# -- 38 author and 34 review: mean 2.40, range 0.50-4.60). A csloop opus author
# executes about 71 tool calls per loop; that figure is measured directly rather
# than derived from the ratio above (mean 71.3 over its 14 author phases). The loop.js revision that ran R12 told its author
# to "finish within about 30 tool-calling turns", and Claude Code emits exactly
# one tool call per turn -- so the same number meant roughly a third of the work.
# R12 averaged 37 author tool calls per loop against that ~71, and the average
# understates how front-loaded it is: its two translating loops spent 71 and 61,
# i.e. right at csloop's per-loop figure and well past the stated 30, while the
# three gate-blocked loops spent 22, 18 and 12. So the budget was advisory in
# practice as well as in wording -- the author overran it exactly when it had
# work to do. `maxToolCalls` was added to loop.js afterwards and is not what this
# run ran under. Note also that csloop's own 120-call ceiling never bound: no
# archived phase stops on `tool_budget`: of the 38 author phases, 25 stop at
# max_iterations and 13 finish early, and all 34 review phases end on final text.
BUDGET_NOTE = (
    "Budget caveat on ccloop: the loop.js revision that produced R12 stated its per-loop "
    "budget in Claude Code turns (one tool call each) against a number calibrated for CodeScribe "
    "turns (2.40 tool calls each, measured), so the stated budget was roughly a third of csloop's "
    "per-loop work. It was advisory and the author overran it when it had work to do: R12 "
    "averaged 37 author tool calls per loop, but spent 71 and 61 in its two translating loops "
    "(against csloop opus-5's ~71) and 22/18/12 in the three loops that found the approval gate "
    "blocked. Read ccloop's per-loop figures as measured under a miscalibrated advisory budget, "
    "which is an error on top of the policy contrast above rather than part of it."
)
SHADOW_NOTE = (
    "Files settled counts a unit whose .cpp landed but whose Fortran original was never retired; "
    "the coverage table's \"not retired\" column says how many of a run\'s units are in that state."
)
# Every model in the current corpus has a rate card, so the "unpriced" caption
# is emitted only when some run in RUNS actually lacks one. Kept rather than
# deleted because the corpus has carried unpriced runs before (Kimi K3) and
# will again the next time a model without published rates is tried.
UNPRICED_NOTE = (
    "Runs on a model with no published rate card are excluded from every USD figure."
)
RATE_CARD_NOTE = (
    "USD figures mix two rate cards: Anthropic's for Opus 5 / Sonnet 5, OpenAI's gpt-5.6-sol "
    "standard short-context rates for the gpt-5.6 runs (see pricing.py for the tier assumptions). "
    "Reference costs for comparison, not charges incurred."
)


def unpriced_caption(runs):
    """UNPRICED_NOTE, but only when a run in the current set is unpriced."""
    return [UNPRICED_NOTE] if any(runs[k]["unpriced_models"] for k in KEYS) else []

# Harness identity, in categorical slots 1-3 of the validated default palette
# (blue, orange, aqua) — the three-slot set that clears the all-pairs CVD and
# normal-vision floors, which matters because one panel (the cost-time
# frontier) is a scatter and therefore an all-pairs form. Aqua sits under 3:1
# against the surface, so the relief rule applies: every panel using these
# colours carries direct value labels, and summary_tables.md is the table view.
#
# ccworkflow and ccloop are deliberately NOT two steps of one hue. They share a
# baseline agent but run different design patterns, and the figures are read
# for the pattern comparison as often as for the agent one; a shared hue would
# assert the grouping that half the comparisons exist to question.
HARNESS_COLOR = {
    CCWORKFLOW: CAT["blue"],
    CCLOOP: CAT["aqua"],
    CSLOOP: CAT["orange"],
}


def harness_legend_handles(harnesses=None):
    """Legend patches for the harnesses in a panel, in HARNESSES order.

    Panels pass the harnesses they actually drew: a legend entry for a harness
    with no bar in the panel is a promise the reader then hunts for.
    """
    present = [h for h in HARNESSES if harnesses is None or h in harnesses]
    return [mpatches.Patch(color=HARNESS_COLOR[h], label=h) for h in present]


# Model tier, a scale independent of HARNESS_COLOR above. gpt-5.6-sol moved
# from aqua to green on 2026-09-11, when ccloop took aqua as the third harness:
# the combined figure puts the cost-by-model panel next to three
# harness-coloured panels, and aqua meaning "ccloop" in one and "gpt-5.6" in
# the other is at its worst here — the gpt-5.6 stack is exactly zero for the
# two runs drawn in aqua next door. Green is the highest free slot that keeps
# this scale's adjacent-pair CVD separation passing (checked with the dataviz
# validator; the greens that fail do so against orange, which this scale does
# not use). Blue still does double duty as "ccworkflow" and "sonnet-5"; that
# predates this corpus, the two panels legend themselves separately, and
# repainting it would change every already-published figure for no new reason.
MODEL_COLOR = {
    "claude-sonnet-5": CAT["blue"],
    "claude-opus-5": CAT["violet"],
    "oaic-gpt56sol": CAT["green"],
    "oaic-gpt56terra": CAT["yellow"],
}
UNPRICED_COLOR = MUTED

# Categorical, fixed order (never assigned by a module's rank in a given run) —
# every top-level src/ module the corpus has ever entered gets a slot here, so
# a run entering a new one needs a one-line addition rather than a fallback
# hue. Assigned in the module-timeline figure and its .tex twin.
MODULE_COLOR = {
    "BDK": CAT["blue"],
    "Mods": CAT["orange"],
    "W2jet": CAT["aqua"],
    "Z2jet": CAT["magenta"],
    "W1jet": CAT["green"],
    "Z": CAT["yellow"],
}


def normalize_model(model):
    return model.replace("anthropic-", "") if model else model


def run_key(day, run_name):
    return (day, run_name)


def key_harness(key):
    """Harness for a (day, run_name) key — the substring test this file used to
    do inline ("ccworkflow" in run_name) is wrong now that ccloop runs are
    archived under a `ccworkflow-loop-*` name."""
    return harness_of(key[1])


def _title(text, letter):
    return f"{letter} {text}" if letter else text


# ---------------------------------------------------------------------------
# Shared bar-panel mechanics
#
# Tick labels and value annotations are both set vertically. At seven runs the
# codes would fit horizontally, but the value annotations above the bars do not,
# and mixing the two orientations reads worse than committing to one. Vertical
# costs nothing in legibility for two-character codes.
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

    A run that settles very few files has per-file metrics several times the
    next largest value (in this corpus R7 and R8, at two units apiece). Scaling
    those panels to it would flatten the bars the panel exists to compare, so
    when the largest value is more than `clip_ratio` times the second largest,
    the axis is scaled to the second largest instead and the outlier is drawn
    clipped with its true value printed above it. Panels of plain per-run totals
    pass clip_ratio=None and are never clipped.

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
    """Per-run token/cost aggregates, plus the raw rows each parser produced.

    Three parsers, one per harness. They are kept apart rather than unified
    because they read genuinely different archives (see each module's
    docstring); everything downstream works off the concatenation and the
    `harness` field, not off which list a row came from.
    """
    cc_rows = parse_all_ccworkflow(EXPERIMENTS)
    cl_rows = parse_all_ccloop(EXPERIMENTS)
    cs_rows = parse_all_csloop(EXPERIMENTS)

    runs = {}
    for key in KEYS:
        runs[key] = {
            "harness": key_harness(key),
            "input": 0,
            "output": 0,
            "cache_write": 0,
            "cache_read": 0,
            "cost": 0.0,
            "cost_by_model": {},
            "unpriced_models": set(),
        }

    for row in cc_rows + cl_rows + cs_rows:
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

    return runs, cc_rows, cl_rows, cs_rows


def loop_progress(day, run_name):
    """(completed, cap) for the Loops column -- what "loop" means differs by
    harness, so this is the one place that reconciles them into a single
    completed/cap pair per run. Either side is None when the run's archive
    doesn't carry the field (e.g. no manifest, or a ccworkflow run that never
    hit the approval-batch gate).

    The three are NOT the same quantity, and a reader comparing the column
    across harnesses needs to know which they are looking at:
      csloop      run.loops_completed / run.agent_loops from the archived
                  manifest -- a configured cap, and a real one.
      ccloop      completed author->review loops / the cap the author prompt
                  itself states ("Loop N of M"). Same shape and same meaning as
                  csloop's: both are a bounded loop that can also stop early on
                  its own stop condition. These two are directly comparable.
      ccworkflow  completed Triage-Author-Integrate rounds. There is no
                  configured cap at all, so the denominator is instead the
                  approval-batch gate limit the run was actually stopped at.
                  Comparable to neither of the above as a ratio; it is a count
                  of rounds against a gate, not progress through a budget.
    """
    run_dir = EXPERIMENTS / day / run_name
    harness = harness_of(run_name)
    if harness == CCWORKFLOW:
        info = round_summary(run_dir)
        return info["rounds_completed"], info["cap"]
    if harness == CCLOOP:
        info = loop_summary(run_dir)
        return info["loops_completed"], info["cap"]
    info = manifest_run_info(run_dir)
    return info.get("loops_completed"), info.get("agent_loops")


def _transcript_wall_time_seconds(day, run_name):
    """Span between the first and last assistant-message timestamp across all
    agent-*.jsonl files in the run's workflow-wf_* dir. Used for both Claude
    Code harnesses, which share that transcript layout."""
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
    """{run: seconds}. Two definitions, and the table caption says which:
    a transcript span for the Claude Code harnesses, the sum of per-loop
    duration_s for csloop. Both are engine time for a harness that runs one
    thing at a time; the span additionally includes harness time between
    agents, so it is the marginally more inclusive of the two."""
    wall_times = {}
    for day, run_name in KEYS:
        if is_claude_code(run_name):
            wall_times[(day, run_name)] = _transcript_wall_time_seconds(day, run_name)
        else:
            wall_times[(day, run_name)] = _csloop_wall_time_seconds(cs_rows, day, run_name)
    return wall_times


def total_tool_calls(transcript_rows, cs_rows, day, run_name):
    """Executed tool calls (ok + error), excluding policy-rejected calls that
    never ran, so the count is comparable across harnesses.

    `transcript_rows` is the ccworkflow and ccloop rows together: both count
    tool_result blocks out of a Claude Code transcript, so the same sum works
    for either and a row can only belong to one run.
    """
    if is_claude_code(run_name):
        return sum(
            r["tool_ok"] + r["tool_error"]
            for r in transcript_rows
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


def load_shadowed_units():
    """{run: [unit]} — the subset of a run's translated units whose Fortran
    original is still in the tree, so the module carries two live
    implementations and the unit is not actually finished. Counted in files
    settled (the work was done and billed) but reported separately, because a
    run that shadows most of its units has not delivered what its file count
    suggests. Empty list, not None, for a run with an archival branch and no
    shadowed units; None when there is no branch."""
    out = {}
    for key in KEYS:
        breakdown = unit_breakdown(*key)
        out[key] = None if breakdown is None else breakdown["shadowed"]
    return out


def modules_touched(translated_units):
    """{run: {module: file_count}} — which top-level src/ directories each
    run's translated files came from."""
    from collections import Counter
    return {k: Counter(module_of(u) for u in (units or [])) for k, units in translated_units.items()}


# The phase whose agent chooses which units a round works on, per harness.
#
# ccworkflow: the TRIAGE agent's. Its prompt has it read the plan and the
# worklist and then "decide" the group and its units, while author agents are
# handed units already chosen and the integrate agent only lands them. So a
# ccworkflow run's file-selection behaviour belongs to its triage model, NOT to
# the author model its label leads with, and not to the more expensive
# integrate model. (There is no separate "dispatch" phase on disk -- triage
# both triages and dispatches.)
#
# ccloop: the AUTHOR agent's. There is no triage: the author reads the Spec and
# Plan, queries the roadmap and picks its own group, then does the work. Review
# only cross-references what the author reports and cannot select anything.
#
# csloop: no entry. One model drives every phase, so the decider is that model
# whichever phase is asked, and decision_model_per_run falls through to it.
DECIDING_PHASE = {
    CCWORKFLOW: "triage",
    CCLOOP: "author",
}

MODEL_DISPLAY = {
    "claude-opus-5": "opus-5",
    "claude-sonnet-5": "sonnet-5",
    "oaic-moonshotai/Kimi-K3": "Kimi K3",
    "oaic-gpt56sol": "gpt-5.6",
    "oaic-gpt56terra": "gpt56terra",
}


def _display_model(model):
    return MODEL_DISPLAY.get(model, model)


def reasoning_config_per_run(transcript_rows):
    """{run: str} — how reasoning was configured, in each harness's own terms.

    Read from the archive rather than from the run label: the Claude Code
    harnesses record an `effort` on every assistant message, csloop records
    `reasoning_config` (and `reason`) in its manifest. The two are different
    knobs and the cell says which, rather than flattening both to "on".
    """
    from collections import Counter, defaultdict

    efforts = defaultdict(Counter)
    for row in transcript_rows:
        key = run_key(row["day"], row["run_name"])
        if key in RUN_CODES and row.get("effort"):
            efforts[key][row["effort"]] += 1

    out = {}
    for key in KEYS:
        if efforts[key]:
            out[key] = f"effort={efforts[key].most_common(1)[0][0]}"
            continue
        info = manifest_run_info(EXPERIMENTS / key[0] / key[1])
        config = info.get("reasoning_config")
        if config:
            out[key] = str(config).replace("thinking=", "thinking ")
        elif info:
            out[key] = f"reason={info.get('reason')}"
        else:
            out[key] = "—"
    return out


def decision_model_per_run(cc_rows, cs_rows):
    # cc_rows here is every transcript-harness row (ccworkflow + ccloop); see
    # main(), which concatenates them before calling.
    """{run: model} — the model that chose which files the run translated.

    Derived from the archives rather than from the run label, so a new run
    needs no entry here: csloop and ccloop each drive every phase with one
    model, so that model is the decider either way; ccworkflow splits phases
    across models, so the decider is whichever model ran its DECIDING_PHASE.

    This deliberately reattributes the ccworkflow runs. Their labels lead with
    "sonnet-5 author, opus-5 integrate", but opus-5 never picks a file there --
    it lands work that triage already selected. Counting those runs as opus-5
    decisions would credit opus-5 with choices it did not make.
    """
    from collections import Counter, defaultdict

    per_run = defaultdict(Counter)
    deciding_per_run = defaultdict(Counter)
    for row in list(cc_rows) + list(cs_rows):
        key = run_key(row["day"], row["run_name"])
        if key not in RUN_CODES:
            continue
        model = normalize_model(row["model"])
        per_run[key][model] += 1
        if row.get("phase") == DECIDING_PHASE.get(key_harness(key)):
            deciding_per_run[key][model] += 1

    deciders = {}
    for key in KEYS:
        if deciding_per_run[key]:
            deciders[key] = deciding_per_run[key].most_common(1)[0][0]
        elif per_run[key]:
            # csloop, or a run whose deciding-phase transcript is missing: the
            # model that ran the most agents is the only sensible stand-in.
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
            "harnesses": sorted({key_harness(k) for k, _ in entries}),
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


def load_tool_calls_per_file(transcript_rows, cs_rows, files_settled):
    result = {}
    for key in KEYS:
        day, run_name = key
        calls = total_tool_calls(transcript_rows, cs_rows, day, run_name)
        files = files_settled[key]
        result[key] = {
            "tool_calls": calls,
            "files_settled": files,
            "per_file": (calls / files) if files else None,
        }
    return result


def load_bash_error_rates():
    """{key: {"total", "errors", "rate"}} — see bash_error_rates.py for the count."""
    return load_bash_error_rates_raw(EXPERIMENTS, RUNS)


def load_per_file_effort(translated_units):
    """{run: per_file_effort record} — wall time, USD and tool calls attributed
    to individual translated files rather than to the run as a whole.

    Exact for ccworkflow (one AUTHOR subagent per unit, author phase only) and
    apportioned for csloop (no per-file record exists; run totals split by the
    tool calls whose arguments name each unit). The two are not the same kind
    of number and per_file_effort.py's docstring is where that is spelled out;
    every row and every aggregate below carries `method` so the distinction
    survives into the tables and, later, into any plot.
    """
    return {
        key: per_file_effort(EXPERIMENTS, key[0], key[1], translated_units[key])
        for key in KEYS
    }


def load_per_file_effort_timed(translated_units):
    """{run: per_file_effort_timed record or None} — the "timed" method (see
    per_file_effort.py), keyed the same way as load_per_file_effort().

    Available for all three harnesses, from two different sources: real
    per-call durations out of logs/toolusage.toml for csloop (author phase
    only), and durations derived from transcript timestamps for ccworkflow and
    ccloop (every phase). Each record carries `duration_source` and
    `phases_covered`; a table printing both kinds must qualify the heading,
    because a derived/all total is more complete than a measured/author one.
    None for a run with no settled units or no parseable telemetry.
    """
    return {
        key: per_file_effort_timed(EXPERIMENTS, key[0], key[1], translated_units[key])
        for key in KEYS
    }


def per_file_effort_rows(effort_by_run):
    """Flat, export-shaped rows: one per (run, unit) with a row in `effort_by_run`.

    Sorted by config then run then unit so the CSV reads in the same order as
    the tables, and so a diff between two regenerations is legible.
    """
    rows = []
    for key in KEYS:
        record = effort_by_run.get(key)
        if record is None:
            continue
        code = RUN_CODES[key]
        config = CONFIG_OF_RUN[key]
        info = record.get("run", {})
        for unit in sorted(record["units"]):
            entry = record["units"][unit]
            rows.append({
                "config": config,
                "config_label": CONFIG_LABELS[config],
                "run": code,
                "day": key[0],
                "run_name": key[1],
                "harness": key_harness(key),
                "method": record["method"],
                # Empty for exact/apportioned; set for timed, where the two
                # sources are not the same measurement (see per_file_effort).
                "duration_source": info.get("duration_source", ""),
                "phases_covered": info.get("phases_covered", ""),
                "unit": unit,
                "module": module_of(unit),
                "settled": entry["settled"],
                "model": entry["model"],
                "minutes": entry["minutes"],
                "usd": entry["usd"],
                "tool_calls": entry["tool_calls"],
                "agents": entry["agents"],
                "attributed_share": entry["attributed_share"],
            })
    rows.sort(key=lambda r: (r["config"], r["run"], r["unit"]))
    return rows


def _config_method(effort_by_run, code):
    """The attribution method for a configuration — a property of its harness,
    so it is the same for every replicate; None if none of them was measured."""
    for run_code in dict(CONFIGS_BY_CODE)[code]:
        record = effort_by_run.get(KEY_BY_CODE[run_code])
        if record is not None:
            return record["method"]
    return None


def per_file_effort_by_config(effort_by_run, units=None):
    """{config: {unit: {metric: mean over the replicates that settled it}}}.

    A unit is averaged over the replicates of that configuration which actually
    settled it, NOT over all replicates of the configuration — a run that never
    picked a file did not do it cheaply, it did not do it at all, and padding
    the mean with zeros would read as the opposite. `n` on each cell is how
    many replicates the mean is over, and it has to be printed next to the
    value: a C2 cell is always one run, and a C1 cell can be either one or two.

    Unsettled rows (a ccworkflow author agent whose unit never landed) are
    excluded: their cost is real and stays in the flat export, but averaging it
    in would charge a file that landed with the cost of one that did not.

    `units` optionally restricts the result to a chosen file set; None keeps
    every unit any replicate of the configuration settled.
    """
    out = {}
    for code, _, members in CONFIGS:
        method = _config_method(effort_by_run, code)
        per_unit = {}
        for run_code in members:
            record = effort_by_run.get(KEY_BY_CODE[run_code])
            if record is None:
                continue
            for unit, entry in record["units"].items():
                if not entry["settled"]:
                    continue
                if units is not None and unit not in units:
                    continue
                per_unit.setdefault(unit, []).append((run_code, entry))
        out[code] = {
            unit: {
                "method": method,
                "n": len(entries),
                "runs": [c for c, _ in entries],
                "minutes": sum(e["minutes"] for _, e in entries) / len(entries),
                "usd": sum(e["usd"] for _, e in entries) / len(entries),
                "tool_calls": sum(e["tool_calls"] for _, e in entries) / len(entries),
            }
            for unit, entries in sorted(per_unit.items())
        }
    return out


def config_settled_union(effort_by_run, code):
    """Every unit at least one replicate of this configuration settled."""
    union = set()
    for run_code in dict(CONFIGS_BY_CODE)[code]:
        record = effort_by_run.get(KEY_BY_CODE[run_code])
        if record is None:
            continue
        union |= {u for u, e in record["units"].items() if e["settled"]}
    return union


def config_shared_units(effort_by_run, codes):
    """Units settled by at least one replicate of EVERY configuration in `codes`.

    The per-config union is the right thing to intersect here, not the
    per-config core: the question is which files can be compared across these
    configurations at all, and a file one replicate settled is a file that
    configuration produced. Whether its replicates agreed is the separate
    question the run-level agreement tables already answer.

    C4 (csloop sonnet-5) settles only Mods/pp_mod and Mods/ppwp2j_mod, so
    including it collapses any intersection to those two files. The comparison
    tables therefore intersect the configurations that reached the shared body
    of work and say so, rather than reporting a two-row table.
    """
    unions = [config_settled_union(effort_by_run, code) for code in codes]
    return sorted(set.intersection(*unions)) if unions else []


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
    # None = the run's archival branch is not in this clone, so there is no
    # ground truth to plot. Zero = the branch is there and retired no file. The
    # two are opposite outcomes and must not share a bar height.
    settled = [files_settled[k] for k in KEYS]
    colors = [HARNESS_COLOR[key_harness(k)] for k in KEYS]

    ax.bar(x, [s or 0 for s in settled], width=0.6, color=colors, edgecolor=SURFACE, linewidth=1)
    ymax, _ = capped_limit(settled, clip_ratio=None)
    _annotate_bars(ax, [s or 0 for s in settled],
                   [str(s) if s is not None else "no branch" for s in settled], ymax)
    _run_xticks(ax)
    ax.set_ylabel("Files settled (git-exact)")
    ax.set_ylim(0, ymax)
    ax.set_title(_title("Files translated", letter))
    ax.legend(handles=harness_legend_handles(), frameon=False, loc="upper left", ncol=3)


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
    colors = [HARNESS_COLOR[key_harness(k)] for k in KEYS]

    ax.bar(x, minutes, width=0.5, color=colors, edgecolor=SURFACE, linewidth=1)
    ymax, _ = capped_limit(minutes, clip_ratio=None)
    _annotate_bars(ax, minutes, [f"{m:.0f} min" for m in minutes], ymax)
    _run_xticks(ax)
    ax.set_ylabel("Wall-clock minutes")
    ax.set_ylim(0, ymax)
    ax.set_title(_title("Wall-clock time", letter))
    ax.legend(handles=harness_legend_handles(), loc="upper right", frameon=False, ncol=3)


# ---------------------------------------------------------------------------
# Panel H — tool calls per file settled
# ---------------------------------------------------------------------------
def draw_tool_calls_per_file_panel(ax, tool_calls_per_file, letter=None):
    x = list(range(len(KEYS)))
    per_file = [tool_calls_per_file[k]["per_file"] for k in KEYS]
    colors = [HARNESS_COLOR[key_harness(k)] for k in KEYS]

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
    # Upper-left: the clipped low-throughput bars own the middle and the gpt56
    # runs on the right are tall, so this is the only reliably clear space.
    ax.legend(handles=harness_legend_handles(), loc="upper left", frameon=False, ncol=3)


# ---------------------------------------------------------------------------
# Panel I — bash tool-call error rate
#
# Coloured by decision_models rather than HARNESS_COLOR: the point of this
# panel is the model-level split inside csloop (Section~evalloop), which a
# harness colouring would hide behind one orange for all eight csloop bars.
# decision_models already attributes exactly one model per run the same way
# Figure~fig:decision does (a run's own model for csloop/ccloop, the triage
# model for ccworkflow), so this panel and that one never disagree about which
# model a run is read as.
# ---------------------------------------------------------------------------
def draw_bash_error_rate_panel(ax, error_rates, decision_models, letter=None):
    x = list(range(len(KEYS)))
    rates = [
        (error_rates[k]["rate"] * 100) if error_rates[k]["rate"] is not None else None
        for k in KEYS
    ]
    colors = [MODEL_COLOR.get(decision_models[k], MUTED) for k in KEYS]

    ymax, clipped = capped_limit(rates, clip_ratio=None)
    heights = [v if v is not None else 0 for v in rates]
    ax.bar(x, heights, width=0.5, color=colors, edgecolor=SURFACE, linewidth=1)
    texts = [f"{v:.0f}%" if v is not None else "no bash calls" for v in rates]
    _annotate_bars(ax, heights, texts, ymax)
    _run_xticks(ax)
    ax.set_ylabel("Bash calls that errored (%)")
    ax.set_ylim(0, ymax)
    ax.set_title(_title("Bash tool-call error rate", letter))

    models_seen = [decision_models[k] for k in KEYS if decision_models[k] in MODEL_COLOR]
    models_present = [m for m in MODEL_COLOR if m in models_seen]
    handles = [mpatches.Patch(color=MODEL_COLOR[m], label=m) for m in models_present]
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


def make_standalone_figures(runs, coverage, files_settled, wall_times, tool_calls_per_file,
                             error_rates, decision_models):
    # Fig 1 — cost & cache
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.4, 4.4))
    fig.suptitle("Token cost & cache efficiency", fontsize=SUPTITLE_SIZE)
    draw_cost_panel(a1, runs)
    draw_cache_panel(a2, runs)
    caption = (run_code_caption(9.4)
               + wrap_notes(9.4, unpriced_caption(runs)
                            + [RATE_CARD_NOTE, REASONING_NOTE, SCOPE_NOTE, SHADOW_NOTE]))
    fig.tight_layout(rect=_caption_rect(len(caption)))
    save_fig(fig, "fig1_cost_and_cache.png", caption)

    # Fig 3 — coverage
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.4, 4.4))
    fig.suptitle("Coverage & correctness", fontsize=SUPTITLE_SIZE)
    draw_files_panel(a1, files_settled)
    draw_correctness_panel(a2, coverage)
    caption = run_code_caption(9.4) + wrap_notes(9.4, [
        "No human_review files exist for these runs, so only self-reported pass rates are shown; "
        "runs that reported none are omitted from the right-hand panel.",
        DESIGN_NOTE,
        SCOPE_NOTE,
        SHADOW_NOTE,
    ])
    fig.tight_layout(rect=_caption_rect(len(caption)))
    save_fig(fig, "fig3_coverage.png", caption)

    # Fig 4 — wall time
    fig, a1 = plt.subplots(figsize=(7.2, 4.2))
    fig.suptitle("Wall-clock time", fontsize=SUPTITLE_SIZE)
    draw_wall_time_panel(a1, wall_times)
    a1.set_title("")
    caption = run_code_caption(7.2) + wrap_notes(7.2, [
        "ccworkflow and ccloop: span of first-to-last agent timestamp. csloop: sum of per-loop "
        "duration_s.",
        DESIGN_NOTE,
        SCOPE_NOTE,
        SHADOW_NOTE,
    ])
    fig.tight_layout(rect=_caption_rect(len(caption)))
    save_fig(fig, "fig4_wall_time.png", caption)

    # Fig 5 — tool calls per file
    fig, a1 = plt.subplots(figsize=(7.2, 4.2))
    fig.suptitle("Tool-call cost per file", fontsize=SUPTITLE_SIZE)
    draw_tool_calls_per_file_panel(a1, tool_calls_per_file)
    a1.set_title("")
    caption = run_code_caption(7.2) + wrap_notes(7.2, [
        "Executed tool calls (ok + error) divided by files settled (git-exact count, git_file_counts.py).",
        "↑ marks a bar clipped by the axis; its true value is printed above it.",
        DESIGN_NOTE,
        SCOPE_NOTE,
        SHADOW_NOTE,
    ])
    fig.tight_layout(rect=_caption_rect(len(caption)))
    save_fig(fig, "fig5_tool_calls_per_file.png", caption)

    # Fig 6 — bash tool-call error rate
    fig, a1 = plt.subplots(figsize=(7.2, 4.2))
    fig.suptitle("Bash tool-call error rate", fontsize=SUPTITLE_SIZE)
    draw_bash_error_rate_panel(a1, error_rates, decision_models)
    a1.set_title("")
    caption = run_code_caption(7.2) + wrap_notes(7.2, [
        "Bash calls that returned an error, divided by Bash calls executed (bash_error_rates.py); "
        "csloop reads this from loop/metadata/*.toml's per-tool ok field, ccworkflow/ccloop by "
        "matching each Bash tool_use to its tool_result.",
        "Coloured by the model that chose the run's files (decision_model_per_run), not by "
        "harness, so the csloop model split (Section~evalloop) is legible bar-by-bar.",
        SCOPE_NOTE,
    ])
    fig.tight_layout(rect=_caption_rect(len(caption)))
    save_fig(fig, "fig6_bash_error_rate.png", caption)


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
    # Three rows at the same 3in/row the four-row layout used, plus a caption
    # band sized to the caption and a top margin (~0.8in).
    #
    # The caption is built BEFORE the gridspec because the band is derived from
    # its line count. It used to be a fixed bottom=0.181, which held only as
    # long as the notes happened to wrap to the same number of lines; when
    # DESIGN_NOTE grew, the extra lines ran straight up through panels (e) and
    # (f). Deriving it means a longer note costs canvas, never legibility.
    fig = plt.figure(figsize=(11, 12))

    caption_size = CAPTION_SIZE * 1.35
    caption = (run_code_caption(10.4, caption_size)
               + wrap_notes(10.4, unpriced_caption(runs)
                            + [RATE_CARD_NOTE, REASONING_NOTE, DESIGN_NOTE, SCOPE_NOTE,
                               SHADOW_NOTE],
                            fontsize=caption_size))
    line_gap, first_line_y = 0.0135, 0.008
    # The 0.035 is clearance for the bottom row's rotated run-code tick labels,
    # which hang below their axes box and are not counted in `bottom`.
    caption_bottom = first_line_y + len(caption) * line_gap + 0.035

    gs = fig.add_gridspec(3, 2, hspace=0.62, wspace=0.32, top=0.931,
                          bottom=caption_bottom, left=0.09, right=0.98)

    draw_cost_panel(fig.add_subplot(gs[0, 0]), runs, letter="(a)")
    draw_cache_panel(fig.add_subplot(gs[0, 1]), runs, letter="(b)")
    draw_files_panel(fig.add_subplot(gs[1, 0]), files_settled, letter="(c)")
    draw_wall_time_panel(fig.add_subplot(gs[1, 1]), wall_times, letter="(d)")
    draw_tool_calls_per_file_panel(fig.add_subplot(gs[2, 0]), tool_calls_per_file, letter="(e)")
    draw_correctness_panel(fig.add_subplot(gs[2, 1]), coverage, letter="(f)")

    fig.suptitle(
        "ccworkflow vs. ccloop vs. csloop on mcfm-translate — cost, cache, tool calls & coverage",
        fontsize=SUPTITLE_SIZE + 2,
        y=0.985,
    )
    for i, line in enumerate(reversed(caption)):
        fig.text(0.5, first_line_y + i * line_gap, line, ha="center",
                 fontsize=caption_size, color=INK)

    out = FIGURES_DIR / "fig_combined.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# ---------------------------------------------------------------------------
# Summary tables (markdown) — single source of numeric truth for the write-up
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Decision-making + module-entry timeline figure
#
# The question this figure answers is not "how much did a run get through"
# (tab_runs and the cost/throughput panels already do that) but "what did the
# model CHOOSE, when, and did other models agree". Two panel ideas that also
# answer that question -- a model x module heatmap of where each deciding
# model chose to work, and a dumbbell of chosen-file fan-in against the ready
# pool -- were tried and dropped from this figure for being harder to read at
# a glance than the two kept below; the data behind them
# (files_by_decision_model, fork_point_roadmap/ready_pool) still backs the
# "Which files each model chose" table in summary_tables.md. Runs are
# collapsed to their deciding model -- for ccworkflow that is the triage
# model, see decision_model_per_run -- and every quantity is over DISTINCT
# files, so a model with four runs cannot out-vote one with a single run by
# repeating itself.
#
# The ordinal ramp below is the dataviz reference instance for three ordered
# bins, checked with validate_palette.js --ordinal.
# ---------------------------------------------------------------------------
# Ordinal steps 250/400/550 -- the light end clears the 2:1 floor against the
# light surface, so the lightest bin is still visible rather than receding.
ORD_BLUE = ["#86b6ef", "#3987e5", "#1c5cab"]


def draw_agreement_panel(ax, buckets, n_models, letter=None):
    """How many distinct models independently settled the same file."""
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


# ---------------------------------------------------------------------------
# Module-entry timeline
#
# Answers "when, with what tool, and having entered a module how ready was
# it" -- order and timing, which the per-run totals elsewhere in this file
# cannot show, and the companion half of the decision-making figure below.
#
# A run's transcript never tags "this tool call is about module X" as
# structured metadata (see parse_decision_timeline's module docstring for why
# both harnesses have to be pattern-matched instead), so the WHEN/WHAT here is
# necessarily best-effort: it is the first tool call in the run's own
# transcript that names a file inside a module the run went on to settle
# something in. The doxygen position, in contrast, is exact -- it is looked up
# against the same fork_point_roadmap map used for the "Which files each
# model chose" table, for the units git_file_counts confirms the run actually
# settled there.
# ---------------------------------------------------------------------------
def load_module_timelines(translated_units, attrs):
    """{run: [{"module", "unit_hint", "elapsed_min", "tool", "rationale",
               "n_settled", "n_ready_leaf", "fanin_mean"}, ...]}, sorted by
    elapsed_min. Empty list for a run that settled nothing, or whose
    transcript this parser could not establish a start time for.
    """
    import statistics

    out = {}
    for key in KEYS:
        day, run_name = key
        units = translated_units[key] or []
        if not units:
            out[key] = []
            continue
        entries = module_entry_order(EXPERIMENTS, day, run_name, units)
        for e in entries:
            mod_units = [u for u in units if module_of(u) == e["module"]]
            known = [attrs[u] for u in mod_units if attrs.get(u)]
            e["n_settled"] = len(mod_units)
            e["n_ready_leaf"] = sum(1 for a in known if a["deps"] == 0 and a["blind"] == 0)
            e["fanin_mean"] = statistics.mean(a["fanin"] for a in known) if known else None
        out[key] = entries
    return out


TIMELINE_MARKER_SIZE = 60
"""Scatter `s` (points^2), constant across markers. Fan-in used to set marker
area (sqrt-scaled) as a third encoded dimension alongside color (module) and
fill/hollow (ready-leaf); dropped because three simultaneous encodings on one
small scatter read as clutter rather than signal, and the fan-in values
themselves are already discussed in the surrounding text."""


def draw_module_timeline_panel(ax, timelines, letter=None):
    modules_seen = sorted({e["module"] for v in timelines.values() for e in v})
    all_x = [e["elapsed_min"] for v in timelines.values() for e in v]
    xmax = (max(all_x) if all_x else 1.0) * 1.14

    ax.grid(False)
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)

    for row, k in enumerate(KEYS):
        y = len(KEYS) - 1 - row
        entries = timelines[k]
        if not entries:
            ax.text(xmax * 0.98, y, "n/a", va="center", ha="right",
                     fontsize=ANNOT_SIZE, color=MUTED)
            continue
        xs = [e["elapsed_min"] for e in entries]
        ax.plot(xs, [y] * len(xs), color=AXIS, lw=0.8, zorder=1)
        for e in entries:
            color = MODULE_COLOR.get(e["module"], MUTED)
            all_ready = e["n_settled"] > 0 and e["n_ready_leaf"] == e["n_settled"]
            if all_ready:
                ax.scatter([e["elapsed_min"]], [y], s=TIMELINE_MARKER_SIZE, color=color, zorder=3,
                           edgecolor=SURFACE, linewidth=0.8)
            else:
                ax.scatter([e["elapsed_min"]], [y], s=TIMELINE_MARKER_SIZE, facecolor=SURFACE, zorder=3,
                           edgecolor=color, linewidth=1.6)

    ax.set_yticks(range(len(KEYS)))
    ax.set_yticklabels([RUN_CODES[k] for k in reversed(KEYS)])
    ax.set_ylim(-0.7, len(KEYS) - 0.3)
    ax.set_xlim(0, xmax)
    ax.set_xlabel("Elapsed minutes since run start")
    ax.set_title(_title("Module entry order over time", letter))

    # Every row has a marker within the first few minutes (Mods/W2jet both tend
    # to be entered early — see the figure), so the top-left corner a legend
    # would normally take is the densest part of the plot, not the emptiest.
    # Both legends go outside the axes instead: the module key above (in the
    # margin `tight_layout` already reserves for the axis title), the style
    # key below the x-axis label, mirroring how the harness legend sits under
    # the axis in the pgfplots panels elsewhere in this file.
    module_handles = [mpatches.Patch(color=MODULE_COLOR.get(m, MUTED), label=m) for m in modules_seen]
    style_handles = [
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=INK_SECONDARY,
               markeredgecolor=SURFACE, markersize=7,
               label="all settled units there were ready leaves at fork"),
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=SURFACE,
               markeredgecolor=INK_SECONDARY, markersize=7,
               label="≥ 1 settled unit was still blocked at fork"),
    ]
    leg1 = ax.legend(handles=module_handles, title="Module", loc="lower center",
                      bbox_to_anchor=(0.24, 1.0), ncol=len(module_handles),
                      frameon=False, fontsize=LEGEND_SIZE)
    ax.add_artist(leg1)
    ax.legend(handles=style_handles, loc="lower center", bbox_to_anchor=(0.78, 1.0),
              ncol=1, frameon=False, fontsize=LEGEND_SIZE * 0.92)


def make_decision_figure(translated_units, decision_models, module_timelines):
    """Top: module-entry timeline. Bottom: cross-model file agreement.

    The two decision-making measures kept as a single straightforward figure:
    the timeline is ground truth per run (when its own transcript first
    touched a module it went on to settle in), and agreement is the
    strictest cross-run comparison in the corpus (distinct files, not
    distinct runs, so a model that ran four times cannot out-vote one that
    ran once). See the module comment above for the two panel ideas this
    figure tried and dropped.
    """
    buckets, n_models = model_settlement_frequency(translated_units, decision_models)

    n = len(KEYS)
    fig = plt.figure(figsize=(9.6, 0.42 * n + 2.6 + 3.2))

    caption = (
        run_code_caption(9.6)
        + wrap_notes(9.6, [
            "Top: module-entry timeline. Runs collapsed to the model that CHOSE the files: the run's own "
            "model for csloop and ccloop, the triage model for ccworkflow (its author/integrate agents "
            "do not select).",
        ])
        + _wrap_to_figure(
            "Marker = first tool call in the run's own transcript that names a file inside that module "
            "(Bash command text for ccworkflow and ccloop, or a read/write/edit path argument "
            "for csloop). Filled vs. "
            "hollow marks whether every settled unit there was a ready leaf (deps=0, blind=0) at the "
            "shared fork point, or the run entered while at least one of them still had an untranslated "
            "callee. n/a: the run settled no files in any module, or its transcript could not be parsed "
            "for a start time.", 9.6)
        + wrap_notes(9.6, [
            "Bottom: how many distinct models independently settled the same file. Counts are over "
            "distinct files, so a model with four runs cannot out-vote one with a single run by "
            "repeating itself.",
            SCOPE_NOTE,
        ])
    )

    # Manual axis placement rather than tight_layout: the timeline panel's two
    # legends are separate artists placed via bbox_to_anchor above its own
    # axes box (see draw_module_timeline_panel), which tight_layout cannot
    # account for across a multi-axes figure -- it warns "not compatible" and
    # produces a huge blank gap between the two panels instead.
    top_margin, gap = 0.12, 0.11
    bottom_margin = _caption_rect(len(caption))[1] + 0.03
    plot_h = (1 - top_margin) - bottom_margin
    h1 = plot_h * n / (n + 4.2) - gap / 2
    h2 = plot_h * 4.2 / (n + 4.2) - gap / 2
    ax_timeline = fig.add_axes((0.09, 1 - top_margin - h1, 0.88, h1))
    ax_agree = fig.add_axes((0.09, bottom_margin, 0.88, h2))

    fig.suptitle("Model decision-making: module-entry timing & cross-model agreement",
                 fontsize=SUPTITLE_SIZE, y=0.995)
    draw_module_timeline_panel(ax_timeline, module_timelines)
    ax_timeline.set_title("")  # redundant with the suptitle; the space it would
                               # occupy is where the two legends sit instead
    draw_agreement_panel(ax_agree, buckets, n_models)

    save_fig(fig, "fig6_decision_making.png", caption)


def write_per_file_exports(effort_by_run, effort_by_config, shared_units, runs,
                            effort_by_run_timed=None):
    """Write the per-file effort data to analysis/data/ as CSV.

    Three files, because they answer three different questions and flattening
    them into one would force a reader to filter before plotting anything:

      per_file_effort.csv
          One row per (run, unit). The raw attribution, including ccworkflow
          author agents whose unit never landed (`settled` = False). This is
          the file to plot distributions from.
      per_file_effort_by_config.csv
          One row per (config, unit): the mean over the replicates of that
          configuration which settled the unit, with `n` alongside. `shared`
          marks the units in the cross-configuration comparison set.
      per_file_effort_runs.csv
          One row per run: the attribution method, what it captured, and — for
          csloop — the share of tool calls that named no settled unit and was
          therefore spread proportionally. Any plot built on the other two
          files needs these caveats in its caption.

    `method` is on every row of all three. A plot that puts an exact bar next
    to an apportioned one without saying which is which is a wrong plot; see
    per_file_effort.py.

    If `effort_by_run_timed` is given, two more files cover the csloop-only
    "timed" method (see per_file_effort.py): per_file_effort_timed.csv (same
    row shape as per_file_effort.csv, one row per run+unit, only for runs
    where "timed" is available) and per_file_effort_timed_runs.csv (per-run
    measured vs. spread split). These are additive -- they never replace the
    three files above, which keep reporting "apportioned" for csloop exactly
    as before.
    """
    import csv

    flat = per_file_effort_rows(effort_by_run)
    path = DATA_DIR / "per_file_effort.csv"
    fields = ["config", "config_label", "run", "day", "run_name", "harness", "method",
              "duration_source", "phases_covered",
              "unit", "module", "settled", "model", "minutes", "usd", "tool_calls",
              "agents", "attributed_share"]
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in flat:
            out = dict(row)
            for field in ("minutes", "usd", "attributed_share"):
                if out[field] is not None:
                    out[field] = f"{out[field]:.4f}"
            out["tool_calls"] = f"{out['tool_calls']:.4f}" if isinstance(out["tool_calls"], float) else out["tool_calls"]
            writer.writerow(out)
    print(f"Wrote {path} ({len(flat)} rows)")

    # Reconciliation, printed rather than asserted so a corpus change reports
    # itself instead of aborting the whole generation. A csloop run's per-file
    # USD must sum to the run's USD exactly (the apportionment is a partition);
    # a ccworkflow run's must sum to its author phase, which is strictly less.
    for key in KEYS:
        record = effort_by_run.get(key)
        if record is None or record["method"] != "apportioned":
            continue
        total = sum(r["usd"] for r in record["units"].values())
        if abs(total - runs[key]["cost"]) > 0.01:
            print(f"  WARNING: {RUN_CODES[key]} per-file USD sums to {total:.2f}, "
                  f"run total is {runs[key]['cost']:.2f}")

    path = DATA_DIR / "per_file_effort_by_config.csv"
    shared = set(shared_units)
    n_rows = 0
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["config", "config_label", "method", "unit", "module",
                         "n_runs", "runs", "minutes_mean", "usd_mean",
                         "tool_calls_mean", "shared"])
        for code, label, _ in CONFIGS:
            for unit, cell in effort_by_config[code].items():
                writer.writerow([code, label, cell["method"], unit, module_of(unit),
                                 cell["n"], " ".join(cell["runs"]),
                                 f"{cell['minutes']:.4f}", f"{cell['usd']:.4f}",
                                 f"{cell['tool_calls']:.4f}",
                                 unit in shared])
                n_rows += 1
    print(f"Wrote {path} ({n_rows} rows)")

    path = DATA_DIR / "per_file_effort_runs.csv"
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["run", "config", "harness", "method", "settled_units",
                         "attributed_usd", "attributed_minutes", "run_usd",
                         "author_usd", "author_share_of_run_usd",
                         "tool_calls_executed", "unattributed_tool_fraction"])
        for key in KEYS:
            record = effort_by_run.get(key)
            if record is None:
                continue
            info = record["run"]
            # The run's whole USD comes from the same aggregate the per-run
            # tables use, so `author_share_of_run_usd` says exactly how much of
            # a ccworkflow run the exact per-file rows actually cover. For
            # csloop the attribution spans the whole run and there is no author
            # phase to separate, so the column is blank rather than 1.0.
            run_usd = runs[key]["cost"]
            author_usd = info.get("author_usd")
            share = (author_usd / run_usd) if (run_usd and author_usd) else ""
            writer.writerow([
                RUN_CODES[key], CONFIG_OF_RUN[key],
                key_harness(key),
                info["method"], info["settled_units"],
                f"{info['attributed_usd']:.4f}", f"{info['attributed_minutes']:.4f}",
                "" if run_usd is None else f"{run_usd:.4f}",
                "" if author_usd is None else f"{author_usd:.4f}",
                "" if share == "" else f"{share:.4f}",
                info.get("tool_calls_executed", ""),
                "" if info.get("unattributed_tool_fraction") is None
                else f"{info['unattributed_tool_fraction']:.4f}",
            ])
    print(f"Wrote {path}")

    if effort_by_run_timed is None:
        return

    timed_flat = per_file_effort_rows(effort_by_run_timed)
    path = DATA_DIR / "per_file_effort_timed.csv"
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in timed_flat:
            out = dict(row)
            for field in ("minutes", "usd", "attributed_share"):
                if out[field] is not None:
                    out[field] = f"{out[field]:.4f}"
            out["tool_calls"] = f"{out['tool_calls']:.4f}" if isinstance(out["tool_calls"], float) else out["tool_calls"]
            writer.writerow(out)
    print(f"Wrote {path} ({len(timed_flat)} rows)")

    # Same reconciliation check as the apportioned export above: "timed"
    # redistributes the same run USD across files differently, it does not
    # change the total, so this must also sum to the run's whole cost exactly.
    for key in KEYS:
        record = effort_by_run_timed.get(key)
        if record is None:
            continue
        total = sum(r["usd"] for r in record["units"].values())
        if abs(total - runs[key]["cost"]) > 0.01:
            print(f"  WARNING: {RUN_CODES[key]} timed per-file USD sums to {total:.2f}, "
                  f"run total is {runs[key]['cost']:.2f}")

    path = DATA_DIR / "per_file_effort_timed_runs.csv"
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["run", "config", "harness", "method", "duration_source",
                         "phases_covered", "settled_units",
                         "attributed_usd", "attributed_minutes", "run_usd",
                         "unmeasured_usd", "unmeasured_minutes", "unattributed_fraction"])
        for key in KEYS:
            record = effort_by_run_timed.get(key)
            if record is None:
                continue
            info = record["run"]
            writer.writerow([
                RUN_CODES[key], CONFIG_OF_RUN[key], key_harness(key), info["method"],
                info["duration_source"], info["phases_covered"], info["settled_units"],
                f"{info['attributed_usd']:.4f}", f"{info['attributed_minutes']:.4f}",
                f"{info['run_usd']:.4f}", f"{info['unmeasured_usd']:.4f}",
                f"{info['unmeasured_minutes']:.4f}",
                "" if info.get("unattributed_fraction") is None
                else f"{info['unattributed_fraction']:.4f}",
            ])
    print(f"Wrote {path}")


def _row_label(k):
    """Run code + configuration, so a table row can be matched to a figure bar."""
    return f"{RUN_CODES[k]} — {RUN_LABELS[k]}".replace(chr(10), " ")


def _run_group_label(idx):
    """Which RUN_GROUPS bucket the idx-th (0-based) entry of RUNS falls in."""
    i = idx
    for name, count in RUN_GROUPS:
        if i < count:
            return name
        i -= count
    return "?"


def _run_folder(day, run_name):
    """Path to the run's archive, relative to the repository root."""
    return f"evals/experiments/{day}/{run_name}"


def _files_cell(files):
    """git-exact files settled: 0 and "no archival branch here" are different."""
    return "n/a (no branch)" if files is None else str(files)


def _loops_cell(k, loop_progress_by_run):
    """completed/cap for the Loops column, or "n/a" when either side is unknown."""
    completed, cap = loop_progress_by_run[k]
    return f"{completed}/{cap}" if completed is not None and cap is not None else "n/a"


def write_summary_tables(runs, coverage, files_settled, translated_units, wall_times, tool_calls_per_file,
                         decision_models, shadowed_units, module_timelines, loop_progress_by_run,
                         effort_by_run, effort_by_config, shared_units, effort_by_run_timed=None,
                         reasoning_configs=None):
    reasoning_configs = reasoning_configs or {}
    lines = ["# Summary tables (generated by analysis/generate_graphs.py — do not hand-edit)\n"]
    for note in unpriced_caption(runs):
        lines.append(f"{note}\n")
    lines.append(f"{RATE_CARD_NOTE}\n")
    lines.append(f"{REASONING_NOTE}\n")
    lines.append(f"{DESIGN_NOTE}\n")
    lines.append(f"{policy_note()}\n")
    lines.append(f"{BUDGET_NOTE}\n")
    lines.append(f"{SCOPE_NOTE}\n")
    lines.append(f"{SHADOW_NOTE}\n")

    lines.append("## Run manifest\n")
    lines.append(
        "Runs grouped sequentially by harness and decision model — all ccworkflow runs, then all "
        "csloop opus-5 runs, then all csloop sonnet-5 runs, then all csloop gpt-5.6 runs, then "
        "the ccloop run — so R1..R12 read as one block per group rather than by archival day. "
        "ccloop is appended last rather than placed beside the other Claude Code harness so that "
        "R1..R11 keep the codes they already carry in the paper and in the archived snapshot; read "
        "the order as the order groups entered the corpus. `Model` is the decision model (the "
        "model that chose which files the run translated; see \"Which files each model chose\" below). "
        "`Folder` is the run's archive, relative to the repository root.\n"
    )
    lines.append(
        "`Reasoning` is the setting as each harness records it, not a normalization of the two: "
        "csloop archives `reasoning_config` in its manifest, the Claude Code harnesses carry an "
        "`effort` level on every assistant message. Adaptive and effort=high are different knobs, "
        "and the difference between the arms is uncontrolled.\n"
    )
    lines.append("| Run | Group | Model | Reasoning | Folder |")
    lines.append("|---|---|---|---|---|")
    for idx, (day, run_name, code, _label) in enumerate(RUNS):
        k = (day, run_name)
        model = decision_models.get(k)
        lines.append(
            f"| {code} | {_run_group_label(idx)} | {_display_model(model) if model else '—'} | "
            f"{reasoning_configs.get(k, '—')} | `{_run_folder(day, run_name)}` |"
        )
    lines.append("")

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

    # Only the models this corpus actually billed. Iterating PRICING instead
    # would add an all-zero column for every rate card that happens to be on
    # file, which grows every time one is added and says nothing.
    billed = sorted({m for k in KEYS for m in runs[k]["cost_by_model"]})
    lines.append("## Cost by model\n")
    lines.append("| Run | " + " | ".join(billed) + " |")
    lines.append("|---|" + "---:|" * len(billed))
    for k in KEYS:
        r = runs[k]
        cells = [f"${r['cost_by_model'].get(m, 0.0):.2f}" for m in billed]
        lines.append(f"| {_row_label(k)} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Status, coverage claim & self-reported correctness\n")
    lines.append(
        "`Files (git)` is ground truth — every unit the run translated on its archival branch. "
        "`Not retired` is how many of those left the Fortran original in the tree beside the new "
        "`.cpp`: the work was done and billed, so it counts, but the module now has two live "
        "implementations and the unit is not finished. `Checklist` is the run's own `- [x]` count in "
        "agent_log.md; it diverges from git when the run claimed a unit it did not land, or when the "
        "log was not archived with the run.\n"
    )
    lines.append("| Run | Status | Files (git) | of which not retired | Checklist | Open | Self-reported pass |")
    lines.append("|---|---|---:|---:|---:|---:|---|")
    for k in KEYS:
        c = coverage[k]
        sp = f"{c['self_reported_pass'][0]}/{c['self_reported_pass'][1]}" if c["self_reported_pass"] else "—"
        has_log = c["final_status"] != "not-executed" and (c["files_settled"] or c["files_open"] or sp != "—")
        shadowed = shadowed_units[k]
        shadow_cell = "n/a" if shadowed is None else (str(len(shadowed)) if shadowed else "—")
        lines.append(
            f"| {_row_label(k)} | {c['final_status']} | {_files_cell(files_settled[k])} | {shadow_cell} | "
            f"{c['files_settled'] if has_log else '—'} | {c['files_open'] if has_log else '—'} | {sp} |"
        )
    lines.append("")

    shadow_rows = {k: v for k, v in shadowed_units.items() if v}
    if shadow_rows:
        every = set.intersection(*(set(v) for v in shadow_rows.values()))
        lines.append(
            f"{len(shadow_rows)} of {len(KEYS)} runs left at least one original in place. "
            + (f"All of them shadow the same units (`{'`, `'.join(sorted(every))}`), which points at "
               "those Fortran modules rather than at any one model.\n" if every else
               "They do not agree on which units, so this is per-run behaviour.\n")
        )

    mods = modules_touched(translated_units)
    all_modules = sorted({m for counts in mods.values() for m in counts})
    lines.append("## Which src/ module each run translated files from (git-exact)\n")
    lines.append(
        "Which top-level `software/mcfm/src/` directory each run's translated files came from — "
        "shows whether runs converged on the same module or scattered across different ones. `Loops` "
        "is completed/cap, and it is not one quantity across harnesses. For csloop it is "
        "`run.loops_completed`/`run.agent_loops` from the run's archived "
        "`loop/metadata/manifest.toml`. For ccloop it is completed author→review loops against the "
        "cap the author prompt itself states (\"Loop N of M\"); that is the same shape and the same "
        "meaning as csloop's, so those two columns compare directly. ccworkflow has no configured cap "
        "at all, so it instead reports completed Triage-Author-Integrate rounds against the "
        "approval-batch gate limit each run was stopped at (recovered from the blocking event's own "
        "message, not a run parameter) — a count of rounds against a gate, not progress through a "
        "budget, and not a ratio to compare with the other two.\n"
    )
    lines.append("| Run | " + " | ".join(all_modules) + " | Total | Loops |")
    lines.append("|---|" + "---:|" * (len(all_modules) + 1) + "---:|")
    for k in KEYS:
        if translated_units[k] is None:
            cells = ["n/a"] * len(all_modules)
            lines.append(f"| {_row_label(k)} | " + " | ".join(cells) +
                         f" | n/a (no branch) | {_loops_cell(k, loop_progress_by_run)} |")
            continue
        counts = mods[k]
        cells = [str(counts.get(m, 0) or "") for m in all_modules]
        lines.append(f"| {_row_label(k)} | " + " | ".join(cells) +
                     f" | {sum(counts.values())} | {_loops_cell(k, loop_progress_by_run)} |")
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
        f"Every distinct file any run translated ({total_distinct} of them), bucketed by how many of the "
        f"{n_measured} measured runs translated it. The module table above shows whether runs landed in "
        "the same *area*; this shows whether they landed on the same *files*, which is the stricter "
        "question.\n"
    )
    if universal:
        lines.append(
            f"Settled by all {n_measured} runs: {len(universal)} "
            f"({', '.join('`' + u + '`' for u in universal)}).\n"
        )
    else:
        # How close the top bucket came matters more than the bare fact that
        # the intersection is empty: "no file in all 7, but 2 files in 6 of 7"
        # is convergence, while a top bucket of 2 of 7 is not. Derived, because
        # a sentence hardcoding either reading goes stale the next time the run
        # set changes.
        best = max(by_count)
        lines.append(
            f"**No file was settled by all {n_measured} runs.** The intersection is empty because the "
            f"smallest runs settled only a handful of files each, not because the runs worked on unrelated "
            f"things: the top bucket is {len(by_count[best])} file(s) settled by {best} of {n_measured} "
            "runs, and the module table above shows where the rest of the disagreement sits. Read the rows "
            "below as levels of partial agreement.\n"
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
        "Runs grouped by the model that made the file-selection decision, not by harness. For csloop and "
        "ccloop that is the run's only model (ccloop's author picks its own group; its reviewer only "
        "cross-references). For ccworkflow it is the **triage** model — triage reads the plan and "
        "picks the round's units, while author agents are handed units already chosen and integrate only "
        "lands them. So R1 counts as a sonnet-5 decision even though opus-5 is its integrate model and "
        "carries most of its cost: opus-5 never picked a file in that run.\n"
    )
    lines.append(
        "`Core` is the set of files settled in *every* run of that model — intra-model reproducibility. "
        "Read it against the run count: a model with one run trivially has core = union.\n"
    )
    lines.append("| Decision model | Runs | Harness | Modules entered | Files (union) | Core | Core files |")
    lines.append("|---|---|---|---|---:|---:|---|")
    for model, info in sorted(by_model.items(), key=lambda kv: (-len(kv[1]["runs"]), kv[0])):
        codes = ", ".join(RUN_CODES[k] for k in info["runs"])
        mods = ", ".join(f"{m} ({n})" for m, n in sorted(info["modules"].items(), key=lambda kv: (-kv[1], kv[0])))
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
        "The stricter companion to the run-level table above. A file settled by several runs of one model "
        "is that model reproducing itself; a file settled by several distinct models is cross-model "
        "agreement. The run-level counts cannot separate those, and with one model deciding more runs "
        "than the others they will read the first as though it were the second.\n"
    )
    lines.append("| Models settling it | Files | Share | Which files |")
    lines.append("|---:|---:|---:|---|")
    for n in sorted(mbuckets, reverse=True):
        units = mbuckets[n]
        named = ", ".join(f"`{u}`" for u in units) if len(units) <= NAME_LIMIT else "—"
        lines.append(f"| {n} of {n_models} | {len(units)} | {100*len(units)/m_total:.0f}% | {named} |")
    lines.append("")

    lines.append("## Per-file effort: configurations and how effort is attributed\n")
    lines.append(
        "The tables above divide a run total by files settled. The tables below attribute wall time, "
        "USD and tool calls to *individual files*. Runs are grouped into configurations (two runs share "
        "one only if the same models ran the same phases), which splits the ccworkflow block: R2 drives "
        "every phase with opus-5, while R1 and R3 author on sonnet-5 and only integrate on opus-5. "
        "C6 (ccloop) is a single run, as is C2.\n"
    )
    lines.append("| Config | Runs | Harness | Attribution |")
    lines.append("|---|---|---|---|")
    for code, label, members in CONFIGS:
        method = _config_method(effort_by_run, code) or "—"
        harness = key_harness(KEY_BY_CODE[members[0]])
        lines.append(f"| {code} — {label} | {', '.join(members)} | {harness} | {method} |")
    lines.append("")
    lines.append(
        "**The two attribution methods are not the same measurement and must not be compared "
        "column-for-column without this caveat.** The one comparison that *is* clean is ccloop "
        "against csloop: both are apportioned, by the same construction, so their per-file columns "
        "differ only in what the runs did.\n"
    )
    lines.append(
        "- *exact* (ccworkflow): each unit has its own AUTHOR subagent, so its tokens, tool calls and "
        "timestamps are its own. It covers the **author phase only** — triage picks the units, serial "
        "integrate lands them and runs the build and test suite, and a metadata agent writes the log, "
        "none of which is attributable to one file. `Author phase / run` below sizes what is missing: it "
        "is every author agent's USD over the run's total, including agents whose unit never landed, so "
        "it sits slightly above the attributed column beside it. Author agents in a group run in "
        "parallel, so per-file minutes overlap and do "
        "not sum to the run's wall clock. A unit retried in a later round is one row, with `agents` "
        "counting the retries.\n"
    )
    lines.append(
        "- *apportioned* (csloop and ccloop): a single agent loops over the whole transformation and "
        "usage is recorded per loop phase (csloop) or per loop agent (ccloop), never per file. "
        "Each executed tool call is attributed to the settled "
        "units its arguments name (`X_fi` counts as `X`; a call naming k units splits 1/k to each), and "
        "the run's USD and minutes are divided in proportion. Because USD and minutes are both "
        "proportional to the same call counts, those three columns carry one measurement between them, "
        "not three. `Unattributed` is the share of the run's tool calls that named no settled unit — "
        "builds, the test suite, roadmap queries, git — which is spread proportionally rather than "
        "dropped, so run totals still reconcile exactly. The one input that differs between the two "
        "harnesses is run minutes: csloop sums its per-phase `duration_s`, ccloop takes the span of "
        "its transcript timestamps (the same number reported as its wall time above), which also "
        "covers harness time between agents.\n"
    )
    lines.append(
        "- The tool-call column is not one quantity across methods: *exact* counts every call the unit's "
        "agent made, *apportioned* counts only calls naming the unit, which is smaller by construction.\n"
    )
    # Derived, not hardcoded: which run leans hardest on the proportional
    # spread is a property of the corpus and moves when a run is added.
    unattr = [(effort_by_run[k]["run"].get("unattributed_tool_fraction"), k)
              for k in KEYS
              if effort_by_run.get(k)
              and effort_by_run[k]["run"].get("unattributed_tool_fraction") is not None]
    if unattr:
        worst_frac, worst_key = max(unattr)
        worst = effort_by_run[worst_key]["run"]
        named = worst["tool_calls_executed"] - round(worst_frac * worst["tool_calls_executed"])
        lines.append(
            f"- `Unattributed` is also the honest read on how coarse a run's per-file split is. "
            f"{RUN_CODES[worst_key]} is the highest in the corpus at {100*worst_frac:.0f}%: only about "
            f"{named} of its {worst['tool_calls_executed']} attributable calls name a settled unit at "
            f"all, the rest being builds, the benchmark, roadmap queries and the approval gate, so its "
            f"columns rest on that handful and the rest is spread proportionally. For ccloop the count "
            f"also excludes the harness's own end-of-loop report calls, whose prose names files it only "
            f"wrote *about* rather than worked on (see `per_file_effort.py` for why, and for the "
            f"out-of-scope run where leaving them in would have handed one unit roughly half the run).\n"
        )
    lines.append("| Run | Config | Method | Units attributed | Attributed USD | Attributed min | Author phase / run | Unattributed |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|")
    for k in KEYS:
        record = effort_by_run.get(k)
        if record is None:
            lines.append(f"| {RUN_CODES[k]} | {CONFIG_OF_RUN[k]} | n/a (no branch) | — | — | — | — | — |")
            continue
        info = record["run"]
        author_usd = info.get("author_usd")
        run_usd = runs[k]["cost"]
        share = f"{100*author_usd/run_usd:.0f}%" if (author_usd and run_usd) else "—"
        unattr = info.get("unattributed_tool_fraction")
        lines.append(
            f"| {RUN_CODES[k]} | {CONFIG_OF_RUN[k]} | {info['method']} | {info['settled_units']} | "
            f"${info['attributed_usd']:.2f} | {info['attributed_minutes']:.1f} | {share} | "
            f"{'—' if unattr is None else f'{100*unattr:.0f}%'} |"
        )
    lines.append("")
    lines.append(
        "Unsettled work is carried but not averaged: R1 spent two full author agents on "
        "`Mods/mod_qcdloop_c` and `Mods/types_mod` and landed neither (a `.hpp` with no `.cpp` behind it "
        "is not a translation — see `git_file_counts.py`). Those rows are in `data/per_file_effort.csv` "
        "with `settled = False` and are excluded from every mean below.\n"
    )

    if effort_by_run_timed is not None:
        lines.append("## Per-file effort (timed): attribution weighted by measured duration\n")
        lines.append(
            "A third attribution, available for **every** harness: an iteration's cost is split across "
            "whatever settled files its own tool calls name, weighted by how long each call actually took — "
            "rather than by raw call count, which treats a `read` and a full test-suite `bash` call as "
            "equally expensive. See `per_file_effort.py`'s docstring for the exact method.\n"
        )
        lines.append(
            "**The durations do not come from the same place, and the two kinds are not interchangeable.** "
            "`Source / phases` on each row says which:\n"
        )
        lines.append(
            "- *measured / author* (csloop): real `duration_ms` per tool call and real per-iteration tokens "
            "from `logs/toolusage.toml`. That file records the **author phase only** — review-phase tool "
            "calls never appear in it — so review is excluded from the measurement and folded into the "
            "unattributed pool.\n"
        )
        lines.append(
            "- *derived / all* (ccworkflow, ccloop): Claude Code writes no durations, but it timestamps "
            "every transcript record, so tool time is `ts(tool_result) − ts(assistant)` and model time is "
            "the gap before each turn. Walking the records in order partitions the whole span with no gap "
            "or overlap. It is a **proxy**: each interval brackets harness queueing as well as execution, "
            "which inflates short calls most (the corpus median call is 57 ms). It does cover **every** "
            "phase.\n"
        )
        lines.append(
            "So a *derived / all* total is more complete than a *measured / author* one under the same "
            "heading. Do not difference them and read the gap as method noise.\n"
        )
        lines.append(
            "For the ccworkflow runs this is not a refinement of *exact* but a different measurement: "
            "*exact* covers the author phase only (see `Author phase / run` above), and *timed* covers the "
            "whole run. Their per-file minutes also overlap, because author agents inside a group run in "
            "parallel.\n"
        )
        lines.append(
            "It is still not *exact* for anyone: a model's \"thinking\" time between tool calls — the "
            "majority of a phase's wall clock — is not tied to one file either way; it is split across "
            "whichever files that same iteration's tool calls name. Any iteration whose tool calls name no "
            "settled file (plus, for csloop, the whole review phase) is folded into one unattributed pool "
            "and spread across files in proportion to each file's measured share. `Unattributed` below is "
            "how much of the run's USD was spread that way rather than measured — and weighting by duration "
            "rather than call count *raises* it for a run whose long calls are builds and test suites, "
            "which name no unit.\n"
        )
        lines.append(
            "Per-file rows differ between `data/per_file_effort.csv` (exact / apportioned) and "
            "`data/per_file_effort_timed.csv` (timed); both carry `method`, and the timed export also "
            "carries `duration_source` and `phases_covered` on every row.\n"
        )
        lines.append(
            "| Run | Config | Source / phases | Primary method | Primary USD | Timed USD | "
            "Unmeasured USD | Timed: unattributed |"
        )
        lines.append("|---|---|---|---|---:|---:|---:|---:|")
        for k in KEYS:
            timed = effort_by_run_timed.get(k)
            if timed is None:
                continue
            primary = effort_by_run.get(k)
            primary_method = primary["run"]["method"] if primary is not None else "—"
            primary_total = f"${primary['run']['attributed_usd']:.2f}" if primary is not None else "—"
            info = timed["run"]
            unattr = info.get("unattributed_fraction")
            lines.append(
                f"| {RUN_CODES[k]} | {CONFIG_OF_RUN[k]} | {info['duration_source']} / "
                f"{info['phases_covered']} | {primary_method} | {primary_total} | "
                f"${info['attributed_usd']:.2f} | ${info['unmeasured_usd']:.2f} | "
                f"{'—' if unattr is None else f'{100*unattr:.0f}%'} |"
            )
        lines.append("")
        lines.append(
            "`Primary USD` is the run's other method — *exact* for ccworkflow (author phase only), "
            "*apportioned* for csloop and ccloop (whole run). Where the primary method is *apportioned*, "
            "it and *timed* reconcile to the same run total by construction and differ only in how that "
            "total is split across files; where it is *exact*, the two cover different phases and the "
            "totals are not meant to match. `Unmeasured USD` is the cost of phases the timed method could "
            "not see at all — csloop's review phase, and nothing for a transcript harness.\n"
        )
        lines.append(
            "A run missing from this table has no settled units or no parseable telemetry; its primary-method "
            "row above is unaffected.\n"
        )
        lines.append(
            "Machine-readable versions: `analysis/data/per_file_effort_timed.csv` (one row per run and "
            "unit, each carrying `duration_source` and `phases_covered`) and "
            "`analysis/data/per_file_effort_timed_runs.csv` (per-run source, coverage, unmeasured and "
            "unattributed split).\n"
        )

    lines.append("## Per-file effort by configuration (shared file set)\n")
    comparison = ", ".join(PER_FILE_COMPARISON_CONFIGS)
    single = ", ".join(c for c in PER_FILE_DISPLAY_CONFIGS if c not in PER_FILE_COMPARISON_CONFIGS)
    lines.append(
        f"Files settled by at least one replicate of every configuration with more than one replicate "
        f"({comparison}); {single} are shown where they settled the same file but are not required, "
        f"since a single run should not decide the comparison set. C6 worked only in W2jet and BDK, so "
        f"its column is blank on every Mods row — that is where that run went, not a hole "
        f"in the measurement. C4 is left out entirely: it settled only "
        f"`Mods/pp_mod` and `Mods/ppwp2j_mod`, so intersecting it would collapse this to two rows. "
        f"Each cell is the mean over the replicates of that configuration **that settled the file**, with "
        f"the replicate count in brackets — a file no replicate settled is blank, not zero.\n"
    )
    lines.append(
        "The bottom row of each table is likewise a mean over the shared files **that column reached**, "
        "and `[nf]` says how many that was. Columns with different counts are not like-for-like: C6 "
        "averages its W2jet and BDK rows only, where C1, C3 and C5 average Mods rows too. Compare a "
        "column against another on the individual rows both actually have, not on the bottom row.\n"
    )
    if not shared_units:
        lines.append("No file is common to those configurations.\n")
    else:
        for field, heading, fmt in (
            ("minutes", "Minutes per file", "{:.1f}"),
            ("usd", "USD per file", "{:.2f}"),
            ("tool_calls", "Tool calls per file", "{:.0f}"),
        ):
            lines.append(f"### {heading}\n")
            header = " | ".join(
                f"{c} ({_config_method(effort_by_run, c)})" for c in PER_FILE_DISPLAY_CONFIGS
            )
            lines.append(f"| File | {header} |")
            lines.append("|---|" + "---:|" * len(PER_FILE_DISPLAY_CONFIGS))
            for unit in shared_units:
                cells = []
                for code in PER_FILE_DISPLAY_CONFIGS:
                    cell = effort_by_config[code].get(unit)
                    cells.append("—" if cell is None else f"{fmt.format(cell[field])} ({cell['n']})")
                lines.append(f"| `{unit}` | " + " | ".join(cells) + " |")
            # Each column's mean is over the shared files THAT COLUMN settled,
            # so the denominators differ — C6 reaches only the W2jet and BDK
            # rows. The count travels with the number: without it, C6's mean
            # reads as a like-for-like figure against C3's when the two are
            # over different files.
            means = []
            for code in PER_FILE_DISPLAY_CONFIGS:
                vals = [effort_by_config[code][u][field] for u in shared_units
                        if u in effort_by_config[code]]
                means.append(f"{fmt.format(sum(vals) / len(vals))} [{len(vals)}f]"
                             if vals else "—")
            lines.append(f"| **Mean over the shared files** [of {len(shared_units)}] | "
                         + " | ".join(means) + " |")
            lines.append("")

    lines.append(
        "Machine-readable versions, for plotting: `analysis/data/per_file_effort.csv` (one row per run "
        "and file, unsettled rows included), `analysis/data/per_file_effort_by_config.csv` (one row per "
        "configuration and file, with `shared` marking this comparison set) and "
        "`analysis/data/per_file_effort_runs.csv` (per-run method, coverage and caveats). Every row in "
        "all three carries `method`.\n"
    )

    lines.append("## Module entry order, tooling & doxygen position at fork (first tool-touch)\n")
    lines.append(
        "Per run, the order it first touched a file it actually went on to settle in each module — not "
        "the order it merely explored, so a candidate it read and rejected does not date a module's entry. "
        "`Elapsed` is minutes since the run's first tool call of any kind. `Ready leaves / settled` counts, "
        "of the units the run settled in that module, how many were ready to rewrite (deps=0, blind=0) at "
        "the shared fork point versus how many it entered while something else there was still untranslated. "
        "`Rationale` is the model's own text immediately before the first such tool call, truncated; empty "
        "for a tool call with no preceding assistant text.\n"
    )
    lines.append("| Run | # | Module | Elapsed | Tool | First unit touched | Ready leaves / settled | Mean fan-in | Rationale |")
    lines.append("|---|---:|---|---:|---|---|---:|---:|---|")
    for k in KEYS:
        entries = module_timelines[k]
        if not entries:
            lines.append(f"| {_row_label(k)} | — | — | — | — | — | — | — | n/a |")
            continue
        for i, e in enumerate(entries, 1):
            fanin = f"{e['fanin_mean']:.1f}" if e["fanin_mean"] is not None else "—"
            rationale = e["rationale"].replace("\n", " ").replace("|", "/").strip() or "—"
            if len(rationale) > 140:
                rationale = rationale[:137] + "..."
            lines.append(
                f"| {_row_label(k)} | {i} | {e['module']} | {e['elapsed_min']:.1f} min | {e['tool']} | "
                f"`{e['module']}/{e['unit_hint']}` | {e['n_ready_leaf']}/{e['n_settled']} | {fanin} | {rationale} |"
            )
    lines.append("")

    out = Path(__file__).resolve().parent / "summary_tables.md"
    out.write_text("\n".join(lines))
    print(f"wrote {out}")


# ---------------------------------------------------------------------------
# LaTeX / TikZ output — the paper renders its evaluation figure as pgfplots
# rather than an imported PNG, so it picks up the document's own fonts and
# stays vector. Emitted from the same parsed data as the PNGs and the summary
# tables above, so there is exactly one numeric source of truth; the .tex files
# below are generated artifacts and carry a do-not-hand-edit banner.
# ---------------------------------------------------------------------------
TEX_DIR = Path(__file__).resolve().parent / "tex"

TEX_BANNER = (
    "%% GENERATED by evals/analysis/generate_graphs.py -- DO NOT HAND-EDIT.\n"
    "%% Regenerate with: python3 analysis/generate_graphs.py\n"
    "%% Numbers are identical to analysis/summary_tables.md.\n"
)

# Only the data-bearing .tex files carry this; the colour definitions have no
# run set to qualify.
TEX_DATA_BANNER = TEX_BANNER + (
    "%% Corpus: the twelve 08-27/08-28-2026 and 09-12-2026 runs, all forked from\n"
    "%% one submodule commit and one 445-file roadmap. Three harnesses: ccworkflow\n"
    "%% (multi-agent workflow on Claude Code), ccloop (loop on Claude Code) and\n"
    "%% csloop (loop on CodeScribe) -- ccloop vs csloop isolates execution policy,\n"
    "%% ccloop vs ccworkflow isolates the design pattern. ccloop is a SINGLE run\n"
    "%% (R12, 09-12-2026): read every ccloop number as one observation. The two\n"
    "%% earlier ccloop runs (09-11-2026) are still on disk but out of scope -- see\n"
    "%% generate_graphs.py. One run (08-28-2026/codescribe-sonnet-5-run3) has no\n"
    "%% archived agent_log.md and is kept with its git-exact count only. Earlier\n"
    "%% days (07-24/07-25, 08-11..08-26) forked from different roadmap states and\n"
    "%% are deliberately out of scope.\n"
)

# Palette mirrored into LaTeX so the figure matches the PNG version exactly.
TEX_COLORS = [
    ("evalBlue", CAT["blue"]),
    ("evalOrange", CAT["orange"]),
    ("evalAqua", CAT["aqua"]),
    ("evalViolet", CAT["violet"]),
    ("evalYellow", CAT["yellow"]),
    ("evalMagenta", CAT["magenta"]),
    ("evalGreen", CAT["green"]),
    ("evalGrid", GRID),
    ("evalAxis", AXIS),
    ("evalInk", INK_SECONDARY),
    # Primary ink, for value labels sitting on a mid-tone fill where the
    # secondary ink drops under 3:1, and the fallback module colour in the
    # decision figure's timeline panel.
    ("evalInkStrong", INK),
    # Used for value labels printed inside a bar, where ink-on-fill would not read.
    ("evalSurface", SURFACE),
    # Ordinal steps for the decision figure's cross-model-agreement bins.
    # Emitted in full rather than only the steps this dataset happens to reach,
    # so the .tex stays valid when the run set changes the maxima.
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
def _axis_common(width="0.305\\textwidth", height="4.4cm"):
    return (
        f"width={width}, height={height},\n"
        "  axis lines=left, axis line style={draw=evalAxis, line width=0.4pt},\n"
        "  ymajorgrids, grid style={draw=evalGrid, line width=0.4pt},\n"
        "  tick label style={font=\\footnotesize, /pgf/number format/assume math mode=true},\n"
        "  label style={font=\\footnotesize, color=evalInk},\n"
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
        "  ylabel style={font=\\footnotesize, yshift=-7pt},\n"
        "  title style={font=\\small\\bfseries, yshift=-1pt},\n"
        # \scriptsize, not \footnotesize: "ccworkflow" set at \footnotesize is
        # nearly half the width of a 0.3\textwidth panel, so the legend box would
        # crowd the bars it is supposed to explain. One step under the ticks is
        # the most this panel width can carry.
        "  legend style={font=\\scriptsize, draw=none, fill=none, inner sep=1pt},\n"
        "  legend image code/.code={\\draw[##1] (0cm,-0.05cm) rectangle (0.18cm,0.09cm);},\n"
        "  every axis plot/.append style={line width=0.5pt},\n"
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
        "  x tick label style={rotate=90, anchor=east, font=\\scriptsize, yshift=1pt},\n"
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
        "  nodes near coords style={font=\\scriptsize, color=evalInk, rotate=90, anchor=west},\n"
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
        f"\\node[font=\\scriptsize, color=evalSurface, rotate=90, anchor=center] "
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
        f"\\node[font=\\scriptsize, color=evalInk, rotate=90, anchor=west] at (axis cs:{c},0) "
        f"{{\\,{note}}};\n"
        for c in missing
    )


# Harness -> LaTeX colour name, mirroring HARNESS_COLOR. Every panel that
# splits its bars by harness iterates HARNESSES against this, rather than
# naming two series inline: a hardcoded [ccworkflow, csloop] pair silently drew
# NO bar at all for a third harness (its runs match neither filter), which
# reads as "these runs settled nothing" instead of "this panel forgot them".
TEX_HARNESS_COLOR = {
    CCWORKFLOW: "evalBlue",
    CCLOOP: "evalAqua",
    CSLOOP: "evalOrange",
}


def _harness_series(metrics, keys=None):
    """[(harness, tex colour)] for the harnesses present in the run set, in
    HARNESSES order — the series a harness-split panel should emit."""
    keys = KEYS if keys is None else keys
    present = {metrics[k]["harness"] for k in keys}
    return [(h, TEX_HARNESS_COLOR[h]) for h in HARNESSES if h in present]


def _tex_harness_legend(series):
    """`\legend{...}` naming exactly the harness series that were emitted."""
    return "\\legend{" + ", ".join(h for h, _ in series) + "}\n"


def _panel_files(metrics):
    series = _harness_series(metrics)
    ymax, _ = _tex_axis_max([metrics[k]["files"] for k in KEYS], clip_ratio=None, headroom=1.30)
    unmeasured = [metrics[k]["code"] for k in KEYS if metrics[k]["files"] is None]
    plots = "".join(
        f"\\addplot[fill={color}, draw=none, bar shift=0pt] coordinates {{"
        + _coord_str([(metrics[k]["code"], metrics[k]["files"]) for k in KEYS
                      if metrics[k]["harness"] == harness and metrics[k]["files"] is not None],
                     "{:.0f}")
        + "};\n"
        for harness, color in series
    )
    return (
        "\\nextgroupplot[" + _axis_common() + _symbolic_x() +
        # `area legend` after `ybar`: a non-stacked ybar plot installs its own
        # bar-shaped legend image on top of the axis-level one, so each entry
        # came out with two swatches. The stacked panels are already area-style
        # and need no such override.
        "  ybar, bar width=5pt, area legend,\n"
        "  title={(a) Files settled (git-exact)},\n"
        f"  ylabel={{Files}}, ymax={ymax:.0f},\n"
        "  nodes near coords, nodes near coords style={font=\\scriptsize, color=evalInk,\n"
        "    rotate=90, anchor=west},\n"
        # There is no free interior space left for it — R3 owns the top, the
        # right-hand runs own the rest — so the harness legend goes under the
        # axis. It covers panels (d) and (f) too, which use the same colours
        # for the same harnesses.
        f"  legend style={{at={{(0.5,-0.42)}}, anchor=north}}, legend columns={len(series)},\n"
        "]\n"
        # The harness series cover disjoint x values, so bar shift=0pt keeps
        # every bar centred on its own tick instead of offsetting it into a
        # multi-series slot and leaving a phantom gap beside it.
        + plots
        + _tex_harness_legend(series)
        # A run whose archival branch never reached this clone has no ground
        # truth at all; without this it would read as a run that settled zero.
        + _na_nodes(unmeasured, "no branch")
    )


# Stable model -> LaTeX colour name, mirroring MODEL_COLOR so the .tex and the
# PNG agree. Only models the corpus actually billed reach the panel, but the
# mapping covers every priced model so adding a run needs no edit here.
TEX_MODEL_COLOR = {
    "claude-sonnet-5": "evalBlue",
    "claude-opus-5": "evalViolet",
    "oaic-gpt56sol": "evalGreen",
    "oaic-gpt56terra": "evalYellow",
}

# Mirrors MODULE_COLOR (module-timeline figure) into LaTeX colour names.
TEX_MODULE_COLOR = {
    "BDK": "evalBlue",
    "Mods": "evalOrange",
    "W2jet": "evalAqua",
    "Z2jet": "evalMagenta",
    "W1jet": "evalGreen",
    "Z": "evalYellow",
}


def _panel_cost_by_model(metrics):
    # Derived, not hardcoded: a hardcoded ["sonnet","opus"] silently drew a
    # zero-height stack for every run billed on a third rate card, which reads
    # as "this run was free" rather than "this panel forgot it".
    models = [m for m in TEX_MODEL_COLOR
              if any(metrics[k]["cost_by_model"].get(m) for k in KEYS)]
    colors = TEX_MODEL_COLOR
    totals = [sum(metrics[k]["cost_by_model"].values()) for k in KEYS]
    ymax, _ = _tex_axis_max(totals, clip_ratio=None, headroom=1.16)
    lines = [
        "\\nextgroupplot[" + _axis_common() + _symbolic_x() +
        "  ybar stacked, bar width=5pt, title={(b) Total cost by model tier},\n"
        f"  ylabel={{USD}}, ymax={ymax:.0f},\n"
        # No interior corner survives: R1 is the tallest stack by a wide margin,
        # the right-hand runs may carry vertical "unpriced" marks, and a
        # top-left legend lands on R1's bar. Below the axis, as in (a).
        #
        # One row, however many rate cards the corpus used. At a fixed two
        # columns a third model wrapped onto a second row, which sits low
        # enough to print through the title of the panel underneath.
        f"  legend style={{at={{(0.5,-0.42)}}, anchor=north}}, legend columns={len(models)},\n"
        "]\n"
    ]
    for m in models:
        pts = [(metrics[k]["code"], metrics[k]["cost_by_model"].get(m, 0.0)) for k in KEYS]
        lines.append(f"\\addplot[fill={colors[m]}, draw=none] coordinates {{" + _coord_str(pts, "{:.2f}") + "};\n")
    lines.append("\\legend{" + ", ".join(_display_model(m) for m in models) + "}\n")
    # A run with no rate card at all still has an empty bar; mark it so the gap
    # is not read as "this run was free".
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


# Escapes that cost source characters but print as one glyph or none. Used to
# size a note box: len() of the LaTeX source overstates a line carrying "\$",
# "\," and "--" by enough to make a note look unplaceable and send it to a
# corner it does not fit.
_TEX_PRINTED = ((r"\,", ""), (r"\%", "%"), (r"\$", "$"), ("---", "-"), ("--", "-"))


def _printed_len(text):
    """Glyphs in the widest line a LaTeX fragment sets.

    Splits on `\\\\` first: a note entry may itself carry a line break, and
    measuring it as one long line would size the note box for a width it never
    reaches.
    """
    for src, printed in _TEX_PRINTED:
        text = text.replace(src, printed)
    return max(len(line) for line in text.split("\\\\"))


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

    # A run that settles very few files lands an order of magnitude out on both
    # axes (here R7 and R8, at two units each). Scaling to it would collapse the
    # other points into one blob in the corner, so the axes are scaled to the
    # rest and the outlier is called out by name as off-scale instead of being
    # silently clipped away.
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

    # Six csloop runs land within about a tenth of the axis range of each
    # other -- individually legible labels for all six is not a placement
    # problem to solve harder, it is a claim the panel cannot back: at this
    # scale the six really are indistinguishable, which is exactly what the
    # text says about them. So a tight group (>=3 points within CLUSTER_TOL
    # of each other in both dimensions, Chebyshev-style) gets its marks
    # plotted but not individually labeled; one compact note names the group
    # instead, the same mechanism already used below for off-scale and
    # unplotted runs.
    CLUSTER_TOL = 0.1

    def _norm(x, y):
        return x / xmax, y / ymax

    def _cluster_group(points):
        n = len(points)
        parent = list(range(n))

        def find(a):
            while parent[a] != a:
                a = parent[a]
            return a

        for i in range(n):
            xi, yi = _norm(points[i][0], points[i][1])
            for j in range(i + 1, n):
                xj, yj = _norm(points[j][0], points[j][1])
                if abs(xi - xj) < CLUSTER_TOL and abs(yi - yj) < CLUSTER_TOL:
                    ra, rb = find(i), find(j)
                    if ra != rb:
                        parent[ra] = rb
        groups = {}
        for i in range(n):
            groups.setdefault(find(i), []).append(i)
        clustered = set()
        for g in groups.values():
            if len(g) >= 3:
                clustered.update(g)
        return clustered

    cluster_idx = _cluster_group(on_scale)
    cluster_pts = [on_scale[i] for i in sorted(cluster_idx)]
    labeled_scale = [p for i, p in enumerate(on_scale) if i not in cluster_idx]

    def _overlaps(box, other):
        ax0, ay0, ax1, ay1 = box
        bx0, by0, bx1, by1 = other
        return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1

    # Box geometry, shared by the note placement below and the label packer
    # under it: the measured size of a two-character bold \scriptsize code, one
    # text line, and a plotted mark, all in axis fractions so x and y are
    # comparable. A three-character code (R10..R12) gets a proportionally wider
    # box from _label_w.
    LABEL_W, LABEL_H, MARK_R = 0.075, 0.085, 0.022

    marks = [_norm(x, y) for x, y, _, _ in on_scale]

    # The note text, built before the point labels are placed so its box
    # can be reserved against them (below). A note placed afterwards can
    # only dodge labels that are already down, which in a panel this
    # crowded means landing on them anyway; reserving it first lets the
    # label packer route around the note instead.
    notes = [
        f"{code} off scale:\\\\{x:.0f}\\,min, \\${y:.0f}/file" for x, y, code, _ in off_scale
    ]

    if cluster_pts:
        # Broken into short lines on purpose, and it is WIDTH that is being
        # bought, not tidiness. This note is placed by fitting its box into a
        # corner (below); the panel's empty space is a narrow column beside the
        # points, so a wide note has no corner to fit into and lands on the
        # labels wherever it goes. The previous phrasing ("... cluster (not /
        # individually labeled): ... $0.91--$1.28/file") ran to most of the
        # panel width and did exactly that. Trading a line of height for a
        # third of the width is the right trade in this panel.
        cluster_codes = [code for _, _, code, _ in cluster_pts]
        cxs = [x for x, _, _, _ in cluster_pts]
        cys = [y for _, y, _, _ in cluster_pts]
        notes.append("cluster, unlabeled:")
        notes.append(f"R{_compact_codes(cluster_codes).replace(', ', ', R')}")
        notes.append(f"{min(cxs):.1f}\\,--\\,{max(cxs):.1f}\\,min")
        notes.append(f"\\${min(cys):.2f}\\,--\\,\\${max(cys):.2f}")
        notes.append("per file")

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

    note_box = None
    if notes:
        # Where the note goes is the same packing problem as a point label, and
        # is solved the same way: build the box the note will actually occupy,
        # try it in each corner, and keep whichever overlaps the fewest marks.
        # Only marks are considered -- the labels are not placed yet, by
        # design -- and the winning box is then handed to the label placer as
        # an obstacle.
        #
        # The rule this replaced compared the two TOP corners by distance to
        # the nearest point, and failed twice over. It never considered the
        # bottom, so with expensive-and-slow runs owning the top right and
        # expensive-and-fast ones the top left it had to pick a bad corner even
        # though the cheap-and-slow corner was empty. And distance-to-nearest-
        # point says nothing about a note several lines tall and a third of the
        # panel wide: the top-right corner is the FURTHEST from any single
        # point and still put the note squarely on the labels in the middle.
        #
        # NOTE_CHAR_W / NOTE_LINE_H are the printed size of one \scriptsize
        # character and one line in axis fractions, from the same measurements
        # LABEL_W / LABEL_H already encode for a code at that font size.
        # NOTE_MARGIN pads the result: these are estimates, and an
        # underestimate reads as "this corner is clear" right up until the
        # rendered note touches something.
        NOTE_CHAR_W, NOTE_LINE_H, NOTE_MARGIN = LABEL_W / 2, LABEL_H, 1.15
        note_w = min(0.9, NOTE_CHAR_W * max(_printed_len(n) for n in notes) * NOTE_MARGIN)
        note_h = min(0.9, NOTE_LINE_H * len(notes) * NOTE_MARGIN)

        corners = []
        for note_anchor, note_align, fx, fy in [
            ("north west", "left", 0.0, 1.0), ("north east", "right", 1.0, 1.0),
            ("south west", "left", 0.0, 0.0), ("south east", "right", 1.0, 0.0),
        ]:
            x0 = fx * (1.0 - note_w)          # the box grows inward from its corner
            y0 = fy - note_h if fy else 0.0
            box = (x0, y0, x0 + note_w, y0 + note_h)
            hits = sum(1 for m in marks
                       if _overlaps(box, (m[0] - MARK_R, m[1] - MARK_R,
                                          m[0] + MARK_R, m[1] + MARK_R)))
            # Distance to the nearest mark breaks ties between clear corners.
            clear = min((abs(mx - fx) + abs(my - fy) for mx, my in marks),
                        default=1.0)
            corners.append((hits, -clear, note_anchor, note_align,
                            xmax * 0.99 if fx else 0.55,
                            ymax * (0.99 if fy else 0.02), box))

        _h, _c, note_anchor, note_align, note_x, note_y, note_box = min(corners)

    # Label placement is a small packing problem, not an alternation. A fixed
    # rule (all labels above, or above/below by x order) puts two labels in
    # the same place whenever the y ordering disagrees with the x ordering.
    # Instead each label tries eight positions around its mark and takes the
    # first that hits neither another mark nor an already-placed label.
    #
    # Labels carry the full bold run code ("R3", not "3"). An earlier version
    # dropped the "R" to fit sixteen runs into this panel; at seven there is
    # room, and a bare digit reads as a data value in a panel whose axes are
    # both numeric.
    #
    # A three-character code (R10..R12) gets a proportionally wider box from
    # _label_w below, so it doesn't sit closer to its neighbors or the axis
    # than its printed width actually is. LABEL_W / LABEL_H / MARK_R are
    # defined above, since the note placement sizes its own box from them too.
    def _label_w(code):
        return LABEL_W if len(code) <= 2 else LABEL_W * len(code) / 2
    # (anchor, dx, dy) in half-box units, in preference order: directly above or
    # below first, since those keep the label over its own x position.
    CANDIDATES = [
        ("south", 0.0, 1.0), ("north", 0.0, -1.0),
        ("west", 1.0, 0.0), ("east", -1.0, 0.0),
        ("south west", 0.8, 0.8), ("south east", -0.8, 0.8),
        ("north west", 0.8, -0.8), ("north east", -0.8, -0.8),
    ]
    # csloop's opus-5/gpt-5.6 runs (R4, R9, R10, R11) land within a few percent
    # of xmax/ymax of each other, close enough that no candidate at the base
    # reach clears both the marks and one another. Rather than accept the
    # overlap, each ring below pushes the label twice as far from its mark as
    # the last; a label placed beyond the first ring gets a thin leader line
    # back to its mark so it still reads as that point's label rather than a
    # stray number floating nearby.
    RING_MULTS = [1.0, 2.0, 3.5, 5.0]

    # The note is an obstacle like any other: seeding it here is what keeps a
    # label off it, rather than the other way round.
    placed_boxes = [note_box] if note_box is not None else []
    place_of = {}
    leader_of = {}
    for (px, py, code, _) in labeled_scale:
        nx, ny = _norm(px, py)
        lw = _label_w(code)
        best, best_cost, best_mult = None, None, 1.0
        for mult in RING_MULTS:
            ring_best, ring_cost = None, None
            for anchor, dx, dy in CANDIDATES:
                cx = nx + dx * (lw / 2 + MARK_R) * mult
                cy = ny + dy * (LABEL_H / 2 + MARK_R) * mult
                box = (cx - lw / 2, cy - LABEL_H / 2, cx + lw / 2, cy + LABEL_H / 2)
                # Off-axis placements are unusable: the label gets clipped.
                if box[0] < 0 or box[2] > 1.0 or box[1] < 0 or box[3] > 1.0:
                    continue
                hits = sum(1 for m in marks
                           if _overlaps(box, (m[0] - MARK_R, m[1] - MARK_R,
                                              m[0] + MARK_R, m[1] + MARK_R)))
                hits += sum(1 for b in placed_boxes if _overlaps(box, b))
                if hits == 0:
                    ring_best, ring_cost = (anchor, dx, dy, box, cx, cy), 0
                    break
                if ring_cost is None or hits < ring_cost:
                    ring_best, ring_cost = (anchor, dx, dy, box, cx, cy), hits
            if ring_best is not None and (best_cost is None or ring_cost < best_cost):
                best, best_cost, best_mult = ring_best, ring_cost, mult
            if best_cost == 0:
                break
        if best is None:
            best = (CANDIDATES[0][0], 0.0, 1.0,
                    (nx - lw / 2, ny, nx + lw / 2, ny + LABEL_H),
                    nx, ny + LABEL_H / 2 + MARK_R)
        anchor, dx, dy, box, cx, cy = best
        placed_boxes.append(box)
        # pgfplots shifts from the mark, so convert the half-box offset back
        # into points along each axis.
        place_of[code] = (anchor,
                          f"{dx * 2.2 * best_mult:.2g}pt",
                          f"{dy * 2.2 * best_mult:.2g}pt")
        if best_mult > 1.0:
            leader_of[code] = (cx * xmax, cy * ymax)

    for harness, color in _harness_series(metrics):
        pts = [p for p in on_scale if p[3] == harness]
        lines.append(
            f"\\addplot[only marks, mark=*, mark size=1.7pt, color={color}] coordinates {{"
            + " ".join(f"({x:.3g},{y:.3g})" for x, y, _, _ in pts)
            + "};\n"
        )
        for x, y, code, _ in pts:
            if code not in place_of:
                continue  # part of the dense cluster; named in the note instead
            if code in leader_of:
                lx, ly = leader_of[code]
                lines.append(
                    f"\\draw[evalGrid, line width=0.3pt] (axis cs:{x:.3g},{y:.3g}) -- "
                    f"(axis cs:{lx:.3g},{ly:.3g});\n"
                )
            anchor, xshift, yshift = place_of[code]
            lines.append(
                f"\\node[font=\\scriptsize\\bfseries, color=evalInk, anchor={anchor}, "
                f"xshift={xshift}, yshift={yshift}, inner sep=0.8pt]\n"
                f"  at (axis cs:{x:.3g},{y:.3g}) {{{code}}};\n"
            )

    if notes:
        lines.append(
            f"\\node[font=\\scriptsize, color=evalInk, anchor={note_anchor}, align={note_align}]\n"
            f"  at (axis cs:{note_x:.3g},{note_y:.3g})\n"
            "  {" + "\\\\".join(notes) + "};\n"
        )
    return "".join(lines)


def _panel_calls_per_file(metrics):
    ymax, clipped = _tex_axis_max([metrics[k]["calls_per_file"] for k in KEYS])
    series = _harness_series(metrics)
    on_scale = {h: [] for h, _ in series}
    over = {h: [] for h, _ in series}
    missing = []
    for k in KEYS:
        m = metrics[k]
        v = m["calls_per_file"]
        if v is None:
            missing.append((m["code"], "no branch" if m["files"] is None else "0 files"))
            continue
        if m["code"] in clipped:
            over[m["harness"]].append((m["code"], ymax, f"{v:.0f}\\,$\\uparrow$"))
            continue
        on_scale[m["harness"]].append((m["code"], v, f"{v:.0f}"))
    return (
        "\\nextgroupplot[" + _axis_common() + _symbolic_x() + _explicit_labels() +
        "  ybar, bar width=5pt, title={(d) Tool calls per file settled},\n"
        f"  ylabel={{Calls / file}}, ymax={ymax:.0f},\n"
        "]\n"
        + "".join(
            f"\\addplot[fill={color}, draw=none, bar shift=0pt] coordinates {{"
            + _coord_str_meta(on_scale[harness]) + "};\n"
            for harness, color in series
        )
        + "".join(_clip_plot(color, over[harness]) for harness, color in series)
        + "".join(_na_nodes([c], note) for c, note in missing)
    )


def _panel_input_composition(metrics):
    """100\\% stacked input-side token mix. This is the panel that explains the
    cache-share column in the table: a run with no cache-write at all cannot
    reach the read share the others do.

    This is a third independent categorical scale in the same figure, and it
    shares hues with the other two (aqua also marks ccloop in the harness
    panels, orange also marks csloop, violet also marks opus-5). Left as is:
    every segment here is non-zero for every run, so there is no run whose
    colour in this panel could be mistaken for a claim about it in another —
    unlike the cost-by-model panel, whose gpt-5.6 series was repainted for
    exactly that reason (see MODEL_COLOR)."""
    lines = [
        "\\nextgroupplot[" + _axis_common() + _symbolic_x() +
        "  ybar stacked, bar width=5pt, title={(e) Input-side token mix},\n"
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
    series = _harness_series(metrics)
    on_scale = {h: [] for h, _ in series}
    over = {h: [] for h, _ in series}
    missing = []
    for k in KEYS:
        m = metrics[k]
        if m["tokens_per_file"] is None:
            missing.append((m["code"], "no branch" if m["files"] is None else "0 files"))
            continue
        v = m["tokens_per_file"] / 1e6
        if m["code"] in clipped:
            over[m["harness"]].append((m["code"], ymax, f"{v:.2f}\\,$\\uparrow$"))
            continue
        on_scale[m["harness"]].append((m["code"], v, f"{v:.2f}"))
    # Linear, not log. Across the runs that are on scale the spread is about
    # 27x, which a linear axis shows honestly; a log axis would both flatten the
    # very gap the panel exists to show and make the value labels read as log10.
    return (
        "\\nextgroupplot[" + _axis_common() + _symbolic_x() + _explicit_labels() +
        "  ybar, bar width=5pt,\n"
        "  title={(f) Input tokens per file settled},\n"
        f"  ylabel={{M tok / file}}, ymax={ymax:.3g},\n"
        "]\n"
        + "".join(
            f"\\addplot[fill={color}, draw=none, bar shift=0pt] coordinates {{"
            + _coord_str_meta(on_scale[harness]) + "};\n"
            for harness, color in series
        )
        + "".join(_clip_plot(color, over[harness]) for harness, color in series)
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
        "\\begin{groupplot}[group style={group size=3 by 2, horizontal sep=1.15cm,\n"
        "    vertical sep=2.35cm}]\n",
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


def write_tex_tables(metrics, coverage, translated_units, decision_models, loop_progress_by_run):
    TEX_DIR.mkdir(exist_ok=True)

    # --- Table 1: the per-run numbers the figure deliberately does not repeat
    # (tab_runs.tex, unrelated to the coverage split below). Loops (completed/cap)
    # sits right after Configuration: csloop's cap is a real run parameter
    # (run.agent_loops); ccworkflow has none, so its "cap" is the approval-batch
    # gate limit the run was actually stopped at (see round_summary).
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
        loops = _loops_cell(k, loop_progress_by_run)
        rows.append(
            f"    {m['code']} & {_tex_escape(m['label'])} & {loops} & {files} & "
            f"{m['minutes']:.0f} & {cost} & {cpf} & {mpf} & {cpfile} & {m['read_share']:.0f} \\\\\n"
        )
    # Column map: 1 code, 2 configuration, 3 loops, 4-6 run totals (files,
    # minutes, USD), 7-9 per-file (USD, minutes, tool calls), 10 cache-read
    # share. The USD total belongs under "Run totals", so the spans are 4-6
    # and 7-9; loops and cache share sit under neither.
    tbl1 = [
        TEX_DATA_BANNER,
        "%% Loops: completed/cap, and NOT one quantity across harnesses.\n"
        "%% csloop (R4-R11): run.loops_completed / run.agent_loops from\n"
        "%% loop/metadata/manifest.toml -- a configured budget.\n"
        "%% ccloop (R12): completed author-review loops / the cap stated in the\n"
        "%% author prompt itself (Loop N of M). Same meaning as csloop's, so those two\n"
        "%% are directly comparable; R12 ran its full budget, with its last three loops\n"
        "%% held at a blocked approval gate rather than translating.\n"
        "%% ccworkflow (R1-R3): completed Triage-Author-Integrate rounds counted from\n"
        "%% journal.jsonl; these runs are uncapped by configuration, so the cap shown\n"
        "%% is the approval-batch gate limit each run was actually stopped at (parsed\n"
        "%% from the blocking event's own message). Not a ratio to compare with the\n"
        "%% other two.\n",
        "\\begin{tabular}{@{}llrrrrrrrr@{}}\n",
        "  \\toprule\n",
        "  & & & \\multicolumn{3}{c}{Run totals} & \\multicolumn{3}{c}{Per file settled} & \\\\\n",
        "  \\cmidrule(lr){4-6}\\cmidrule(lr){7-9}\n",
        "  & Configuration & Loops & Files & Min & USD & USD & Min & Tool calls & Cache \\%\\\\\n",
        "  \\midrule\n",
        *rows,
        "  \\bottomrule\n",
        "\\end{tabular}\n",
    ]
    (TEX_DIR / "tab_runs.tex").write_text("".join(tbl1))
    print(f"wrote {TEX_DIR / 'tab_runs.tex'}")

    # --- Table 2a: run manifest -- links each run code and configuration to
    # its exact folder in the archived experiment repository (the Zenodo
    # snapshot cited in the paper as akash_dhruv_2026_21925035), so a reader
    # can go from a code in Table 2b straight back to the run's own archive.
    # Paths are relative to that repository's root, e.g.
    # evals/experiments/08-27-2026/ccworkflow-sonnet-5-opus-5-integrate-run3.
    map_rows = []
    for day, run_name, code, label in RUNS:
        # "evals/" is common to every row and stated once in the caption, so
        # dropping it from each cell buys back column width for the part that
        # actually varies (day and run folder).
        directory = f"experiments/{day}/{run_name}"
        map_rows.append(
            f"    {code} & {_tex_escape(label)} & \\texttt{{{_tex_escape(directory)}}} \\\\\n"
        )
    tbl_map = [
        TEX_DATA_BANNER,
        "\\setlength{\\tabcolsep}{3.2pt}\n",
        "\\begin{tabular}{@{}lll@{}}\n",
        "  \\toprule\n",
        "  Run & Configuration & Directory (under {\\ttfamily evals/} in the archived repository) \\\\\n",
        "  \\midrule\n",
        *map_rows,
        "  \\bottomrule\n",
        "\\end{tabular}\n",
    ]
    (TEX_DIR / "tab_coverage_map.tex").write_text("".join(tbl_map))
    print(f"wrote {TEX_DIR / 'tab_coverage_map.tex'}")

    # --- Table 2b: module coverage (which part of the tree each run reached).
    # Loops moved to Table 1 (tab_runs.tex), right after Configuration --
    # loop progress is a run-total-shaped stat, not a module one.
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
        "  tick label style={font=\\footnotesize, /pgf/number format/assume math mode=true},\n"
        "  label style={font=\\footnotesize, color=evalInk},\n"
        "  title style={font=\\small\\bfseries, yshift=-1pt},\n"
        "  xtick style={draw=none}, ytick style={draw=none},\n"
    )


def _tikz_panel_agreement(buckets, n_models):
    """Distinct files by how many models independently settled them."""
    ns = sorted(buckets, reverse=True)
    total = sum(len(v) for v in buckets.values())
    n = len(ns)
    bars, labels = [], []
    for i, k in enumerate(ns):
        v = len(buckets[k])
        y = n - 1 - i
        step = min(k - 1, len(ORD_BLUE) - 1)
        bars.append(f"\\addplot[xbar, fill=evalOrd{step}, draw=none, bar width=10pt,"
                    f" forget plot] coordinates {{({v},{y})}};\n")
        labels.append(
            f"\\node[font=\\scriptsize, color=evalInk, anchor=west] at (axis cs:{v},{y})"
            f" {{\\hspace{{3pt}}{v} ({100 * v / total:.0f}\\%)}};\n"
        )
    yl = ",".join(f"{k} of {n_models}" for k in reversed(ns))
    return (
        "\\nextgroupplot[" + _tikz_decision_axis("0.55\\textwidth", "4.6cm") +
        "  xmajorgrids, grid style={draw=evalGrid, line width=0.4pt},\n"
        f"  xmin=0, xmax={total * 1.55:.0f}, xtick={{0,25,50}}, ymin=-0.7, ymax={n - 0.3},\n"
        f"  ytick={{{','.join(str(i) for i in range(n))}}}, yticklabels={{{yl}}},\n"
        "  xlabel={Distinct files},\n"
        "  title={Cross-model agreement},\n"
        "]\n" + "".join(bars) + "".join(labels)
    )


TIKZ_TIMELINE_MARKER_SIZE_PT = 8.5
"""Node `minimum size` in pt, constant across markers -- see
TIMELINE_MARKER_SIZE for why the fan-in-scaled size was dropped."""


def _tikz_panel_timeline(module_timelines):
    """Module-entry timeline, drawn with raw \\node/\\draw primitives at `axis
    cs` coordinates rather than pgfplots' own scatter machinery -- pgfplots
    has no first-class per-point variable marker size outside its `scatter`
    mode, and standalone timeline correctness matters more here than fitting
    that mode.
    """
    keys_order = list(reversed(KEYS))  # row 0 at the bottom, R1 at the top
    n = len(KEYS)
    all_x = [e["elapsed_min"] for v in module_timelines.values() for e in v]
    xmax = (max(all_x) if all_x else 1.0) * 1.14
    modules_seen = sorted({e["module"] for v in module_timelines.values() for e in v})

    body_lines = []
    for row, k in enumerate(keys_order):
        y = row
        entries = module_timelines[k]
        if not entries:
            body_lines.append(
                f"\\node[font=\\scriptsize, color=evalInk, anchor=east] "
                f"at (axis cs:{xmax * 0.98:.3g},{y}) {{n/a}};\n"
            )
            continue
        if len(entries) > 1:
            coord_str = " -- ".join(f"(axis cs:{e['elapsed_min']:.3g},{y})" for e in entries)
            body_lines.append(f"\\draw[evalAxis, line width=0.5pt] {coord_str};\n")
        for e in entries:
            color = TEX_MODULE_COLOR.get(e["module"], "evalInkStrong")
            all_ready = e["n_settled"] > 0 and e["n_ready_leaf"] == e["n_settled"]
            style = (f"fill={color}, draw=evalSurface, line width=0.6pt" if all_ready
                     else f"fill=evalSurface, draw={color}, line width=1.1pt")
            body_lines.append(
                f"\\node[circle, {style}, minimum size={TIKZ_TIMELINE_MARKER_SIZE_PT:.2f}pt, inner sep=0pt] "
                f"at (axis cs:{e['elapsed_min']:.3g},{y}) {{}};\n"
            )

    # Legend swatches drawn in `axis cs` at y > n-1 (a headroom band reserved
    # in ymax below, above every real row) rather than at `rel axis cs` y>1:
    # a groupplot's `\node ... at (rel axis cs:x,y>1)` renders outside the
    # axis's own bounding box, which this document's style clips away, so the
    # only reliable way to put a legend "above" the data is to reserve real
    # data-coordinate space for it and never let a marker be plotted there.
    legend_y0 = n + 0.3
    legend_x = xmax * 0.72
    legend_lines = "".join(
        f"\\node[circle, fill={TEX_MODULE_COLOR.get(m, 'evalInkStrong')}, minimum size=7pt, inner sep=0pt] "
        f"at (axis cs:{legend_x:.3g},{legend_y0 + 0.7 * i:.3f}) {{}};\n"
        f"\\node[font=\\scriptsize, color=evalInk, anchor=west, xshift=6pt] "
        f"at (axis cs:{legend_x:.3g},{legend_y0 + 0.7 * i:.3f}) {{{_tex_escape(m)}}};\n"
        for i, m in enumerate(modules_seen)
    )

    yticklabels = ",".join(_tex_escape(RUN_CODES[k]) for k in keys_order)
    ymax = n + 0.3 + 0.7 * len(modules_seen)
    return (
        "\\nextgroupplot[\n"
        "  width=0.92\\textwidth, height=" + f"{0.34 * ymax + 1.6:.2f}cm,\n"
        "  axis lines=left, axis line style={draw=evalAxis, line width=0.4pt},\n"
        "  xmajorgrids, grid style={draw=evalGrid, line width=0.4pt},\n"
        "  tick label style={font=\\footnotesize}, label style={font=\\footnotesize, color=evalInk},\n"
        f"  xmin=0, xmax={xmax:.3g}, ymin=-0.7, ymax={ymax:.3f},\n"
        f"  ytick={{{','.join(str(i) for i in range(n))}}}, yticklabels={{{yticklabels}}},\n"
        "  y tick label style={font=\\scriptsize}, xtick style={draw=none}, ytick style={draw=none},\n"
        "  xlabel={Elapsed minutes since run start},\n"
        "]\n" + "".join(body_lines) + legend_lines
    )


def write_tikz_decision_figure(translated_units, decision_models, module_timelines):
    """Decision-making figure as pgfplots, mirroring fig6_decision_making.png:
    the module-entry timeline on top, cross-model file agreement below.

    Same numbers, same palette steps, same panel order as the PNG -- the paper
    gets a vector copy that picks up the document's fonts, and there is still
    one source of truth behind both.
    """
    buckets, n_models = model_settlement_frequency(translated_units, decision_models)

    body = [
        TEX_DATA_BANNER,
        "%% Decision-making figure. Requires pgfplots + the groupplots library\n"
        "%% and the evalXxx colours, both set up in jss-submission.sty. Top panel:\n"
        "%% module-entry timeline -- marker color is the module; filled = every\n"
        "%% settled unit there was a ready leaf (deps=0, blind=0) at the shared\n"
        "%% fork point, hollow = at least one was entered while something else\n"
        "%% there still had an untranslated callee (see parse_decision_timeline.py\n"
        "%% for what counts as \"settled\" here). Bottom panel: runs are\n"
        "%% collapsed to the model that CHOSE the files (the run's own model for\n"
        "%% csloop and ccloop, the TRIAGE model for ccworkflow), and counts are over\n"
        "%% DISTINCT\n"
        "%% files, so a model with four runs cannot out-vote one with a single run\n"
        "%% by repeating itself.\n",
        "\\begin{tikzpicture}\n",
        "\\begin{groupplot}[group style={group size=1 by 2, vertical sep=2.4cm}]\n",
        _tikz_panel_timeline(module_timelines),
        _tikz_panel_agreement(buckets, n_models),
        "\\end{groupplot}\n",
        "\\end{tikzpicture}\n",
    ]
    out = TEX_DIR / "fig_decision.tex"
    out.write_text("".join(body))
    print(f"wrote {out}")


def main():
    # A run misnamed relative to its own archive would be silently reclassified
    # into another harness's numbers, so the naming convention harness_of reads
    # is checked against what is actually on disk before anything is parsed.
    for day, run_name, by_name, on_disk in verify_harness_names(EXPERIMENTS, RUNS):
        print(f"  WARNING: {day}/{run_name} is named like {by_name} but its "
              f"archive is {on_disk}")

    runs, cc_rows, cl_rows, cs_rows = load_run_aggregates()
    print(f"ccworkflow rows: {len(cc_rows)}, ccloop rows: {len(cl_rows)}, "
          f"csloop rows: {len(cs_rows)}")
    # ccworkflow and ccloop rows have the same shape and are read the same way
    # everywhere downstream; only the parser that produced them differs.
    transcript_rows = cc_rows + cl_rows

    coverage = {k: coverage_for_run(EXPERIMENTS / k[0] / k[1]) for k in KEYS}
    for k, c in coverage.items():
        print(f"{k}: {c}")

    files_settled = load_files_settled()
    for k, f in files_settled.items():
        print(f"{k}: files settled (git-exact) = {f}")

    translated_units = load_translated_units()
    shadowed_units = load_shadowed_units()
    for k in KEYS:
        shadowed = shadowed_units[k]
        if shadowed:
            print(f"{k}: {len(shadowed)} translated but not retired: {', '.join(shadowed)}")

    decision_models = decision_model_per_run(transcript_rows, cs_rows)
    reasoning_configs = reasoning_config_per_run(transcript_rows)
    for k in KEYS:
        print(f"{k}: reasoning {reasoning_configs[k]}")
    for k in KEYS:
        print(f"{k}: decided by {decision_models[k]}")

    wall_times = load_wall_times(cs_rows)
    for k, s in wall_times.items():
        print(f"{k}: wall time {s/60:.1f} min" if s else f"{k}: wall time unknown")

    tool_calls_per_file = load_tool_calls_per_file(transcript_rows, cs_rows, files_settled)
    for k, t in tool_calls_per_file.items():
        print(f"{k}: {t}")

    loop_progress_by_run = {k: loop_progress(*k) for k in KEYS}
    for k, lp in loop_progress_by_run.items():
        print(f"{k}: loops {lp[0]}/{lp[1]} ({key_harness(k)} sense)")

    metrics = derived_metrics(runs, files_settled, wall_times, tool_calls_per_file)

    attrs = fork_point_roadmap(EXPERIMENTS, RUNS, translated_units)
    module_timelines = load_module_timelines(translated_units, attrs)
    for k, entries in module_timelines.items():
        print(f"{k}: module entry order = {[(e['module'], round(e['elapsed_min'], 1)) for e in entries]}")

    effort_by_run = load_per_file_effort(translated_units)
    shared_units = config_shared_units(effort_by_run, PER_FILE_COMPARISON_CONFIGS)
    effort_by_config = per_file_effort_by_config(effort_by_run)
    for k in KEYS:
        record = effort_by_run.get(k)
        if record is None:
            continue
        info = record["run"]
        print(f"{k}: per-file effort {info['method']}, {info['settled_units']} units, "
              f"${info['attributed_usd']:.2f} attributed")
    print(f"per-file comparison set ({'/'.join(PER_FILE_COMPARISON_CONFIGS)}): "
          f"{len(shared_units)} files")

    effort_by_run_timed = load_per_file_effort_timed(translated_units)
    for k in KEYS:
        record = effort_by_run_timed.get(k)
        if record is None:
            continue
        info = record["run"]
        print(f"{k}: per-file effort timed, {info['settled_units']} units, "
              f"${info['attributed_usd']:.2f} attributed, {info['unattributed_fraction']:.0%} unattributed")

    error_rates = load_bash_error_rates()
    for k, r in error_rates.items():
        rate = f"{r['rate']:.1%}" if r["rate"] is not None else "n/a"
        print(f"{k}: bash calls {r['total']}, errors {r['errors']}, rate {rate}")

    make_standalone_figures(runs, coverage, files_settled, wall_times, tool_calls_per_file,
                             error_rates, decision_models)
    _bump_fonts_for_combined()
    make_combined_figure(runs, coverage, files_settled, wall_times, tool_calls_per_file)
    make_decision_figure(translated_units, decision_models, module_timelines)
    write_summary_tables(runs, coverage, files_settled, translated_units, wall_times, tool_calls_per_file,
                         decision_models, shadowed_units, module_timelines, loop_progress_by_run,
                         effort_by_run, effort_by_config, shared_units, effort_by_run_timed,
                         reasoning_configs)
    write_per_file_exports(effort_by_run, effort_by_config, shared_units, runs, effort_by_run_timed)

    # LaTeX/TikZ artifacts consumed directly by the paper.
    write_tikz_colors()
    write_tikz_figure(metrics)
    write_tikz_decision_figure(translated_units, decision_models, module_timelines)
    write_tex_tables(metrics, coverage, translated_units, decision_models, loop_progress_by_run)


if __name__ == "__main__":
    main()
