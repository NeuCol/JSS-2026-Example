"""Which harness produced a run — the one place that decides.

Three harnesses appear in this corpus, and every other module in analysis/
dispatches on the answer (how tokens are recorded, what a "loop" is, whether
per-file effort can be measured or only apportioned):

  csloop      CodeScribe's own prompt_loop. One agent loops over the whole
              transformation; usage is recorded per loop phase under
              `loop/metadata/`. Run directories are named `codescribe-*` or
              `csloop-*` — the same harness either way (its own
              archive_summary.json calls the source ".codescribe" for both),
              and always called "csloop" in analysis output.
  ccworkflow  The Claude Code `transform` workflow. A five-phase,
              group-at-a-time, approval-gated pipeline that fans out one AUTHOR
              subagent per unit. Telemetry is one Claude Code transcript per
              subagent under `workflow-wf_*/`.
  ccloop      The Claude Code `loop` workflow (`.claude/workflows/loop.js`),
              added 09-11-2026. Same author->review shape as csloop — one agent
              per loop working the whole Spec/Plan, no per-unit fan-out — but
              running on Claude Code's baseline agent instead of CodeScribe's.
              Telemetry is the same `workflow-wf_*/` transcript layout
              ccworkflow uses, which is exactly why it needs naming apart:
              a `workflow-wf_*` directory no longer implies "ccworkflow".

WHY THE THIRD HARNESS EXISTS, i.e. what its runs are a control for. The corpus
now spans two design patterns (a bounded author->review loop, and a
multi-agent group-at-a-time workflow) across two agent baselines (CodeScribe's
and Claude Code's), and ccloop is the cell that makes both comparisons
one-variable:

                      | CodeScribe baseline | Claude Code baseline
    loop pattern      | csloop              | ccloop
    multi-agent flow  | (none)              | ccworkflow

  ccloop vs csloop      same design pattern, different baseline agent — the
                        bare-metal agent comparison.
  ccloop vs ccworkflow  same baseline agent, different design pattern — loop
                        against multi-agent workflow.
Neither comparison was available before 09-11-2026: every earlier ccworkflow /
csloop pair differs in both dimensions at once.

NAMES ARE THE CONVENTION, THE LAYOUT IS THE CHECK. `harness_of` reads the run
directory name, because that is all most callers have. Directory names are an
operator convention and can drift, so `verify_harness_names` re-derives the
same answer from what is actually on disk and reports any run where the two
disagree — a rename that quietly reclassified a run would otherwise show up
only as a number moving in a table.
"""

from pathlib import Path

CCWORKFLOW = "ccworkflow"
CCLOOP = "ccloop"
CSLOOP = "csloop"

# Display order wherever all three appear (legends, group tables): the two
# Claude Code harnesses adjacent, then csloop.
HARNESSES = (CCWORKFLOW, CCLOOP, CSLOOP)

# Run-directory prefixes that mean ccloop. Every ccloop run so far (the two
# 09-11-2026 ones and the 09-12-2026 one) is archived as `ccworkflow-loop-*`
# (they came out of the same .claude loop source as the ccworkflow runs), which
# is a `ccworkflow-` prefix and would otherwise be swept up as ccworkflow — so
# this is checked FIRST, before any other rule. `ccloop-*` is accepted too, for
# runs archived under the shorter name.
#
# Directory names carry no reliable MODEL either: 09-12-2026's run was
# archived as `ccworkflow-loop-sonnet-5-run2` even though every author and
# review agent in it ran opus-5 (fixed 2026-09-26 -- see generate_graphs.py's
# RUNS comment). That is why nothing here parses a model out of a name, and
# why generate_graphs labels every run from its transcripts instead, even now
# that this particular directory name agrees with them.
_CCLOOP_PREFIXES = ("ccworkflow-loop-", "ccloop-")


def harness_of(run_name):
    """"ccworkflow" | "ccloop" | "csloop" for a run directory name.

    csloop is the default rather than an explicit prefix match: its runs are
    named `codescribe-*` in this corpus and `csloop-*` in an earlier one, and
    parse_csloop already discovers them structurally (by
    `loop/metadata/manifest.toml`) rather than by name. Anything that is not
    one of the two Claude Code harnesses is csloop here, and
    verify_harness_names is what catches a name that lands in that default by
    accident.
    """
    if run_name.startswith(_CCLOOP_PREFIXES):
        return CCLOOP
    if run_name.startswith("ccworkflow-"):
        return CCWORKFLOW
    return CSLOOP


def is_claude_code(run_name):
    """True when the run's telemetry is Claude Code `workflow-wf_*` transcripts
    rather than CodeScribe's `loop/metadata/` TOML — i.e. ccworkflow or ccloop.

    This is the test for "can I read per-message timestamps and per-agent token
    usage out of agent-*.jsonl", which is what wall time, the module-entry
    timeline and per-file effort all actually need. It is NOT a test for which
    design pattern the run used; that is `harness_of`.
    """
    return harness_of(run_name) in (CCWORKFLOW, CCLOOP)


def detect_harness(run_dir):
    """The harness a run's own archive says it is, or None if it says nothing.

    Structural, so it cannot be fooled by a rename:
      - `loop/metadata/manifest.toml`            -> csloop
      - `workflow-wf_*/journal.jsonl` whose events carry a `phase` of Author or
        Review                                   -> ccloop
      - any other `workflow-wf_*`                -> ccworkflow

    The ccloop discriminator is the loop workflow's own phase labels. transform.js
    emits no `phase` on its journal events at all (its phase has to be recovered
    from prompt text — see parse_ccworkflow), so "the journal names an Author or
    Review phase" is present in every ccloop archive and absent from every
    ccworkflow one.
    """
    import json

    run_dir = Path(run_dir)
    if (run_dir / "loop" / "metadata" / "manifest.toml").exists():
        return CSLOOP

    workflow_dirs = sorted(run_dir.glob("workflow-wf_*"))
    if not workflow_dirs:
        return None
    for workflow_dir in workflow_dirs:
        journal = workflow_dir / "journal.jsonl"
        if not journal.exists():
            continue
        with open(journal) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                if json.loads(line).get("phase") in ("Author", "Review"):
                    return CCLOOP
    return CCWORKFLOW


def verify_harness_names(experiments_root, runs=None):
    """[(day, run_name, name_says, disk_says)] for every run the two disagree on.

    `runs` optionally restricts the check to a (day, run_name, ...) registry;
    None walks the whole corpus. A run whose archive is too thin to classify
    (detect_harness returns None) is skipped rather than reported — that is a
    missing archive, not a misnamed one, and every other module already reports
    it in its own terms.
    """
    experiments_root = Path(experiments_root)
    if runs is None:
        pairs = [
            (day.name, run.name)
            for day in sorted(experiments_root.iterdir()) if day.is_dir()
            for run in sorted(r for r in day.iterdir() if r.is_dir())
        ]
    else:
        pairs = [(day, run_name) for day, run_name, *_ in runs]

    mismatches = []
    for day, run_name in pairs:
        on_disk = detect_harness(experiments_root / day / run_name)
        if on_disk is None:
            continue
        by_name = harness_of(run_name)
        if on_disk != by_name:
            mismatches.append((day, run_name, by_name, on_disk))
    return mismatches


if __name__ == "__main__":
    experiments = Path(__file__).resolve().parent.parent / "experiments"
    for day in sorted(p for p in experiments.iterdir() if p.is_dir()):
        for run in sorted(p for p in day.iterdir() if p.is_dir()):
            on_disk = detect_harness(run)
            flag = "" if on_disk in (None, harness_of(run.name)) else f"  << disk says {on_disk}"
            print(f"{day.name}/{run.name}: {harness_of(run.name)}{flag}")
