# Notes on `archive.toml` and the experiment archive

Study note written while reviewing the workflows paper
(`NeuCol-Code-Translation/papers/workflows-paper/main.tex`), which cites this
repository's `evals/` directory as the archived lab notebook (`jss_example_2026`,
a Zenodo-snapshotted directory-based experiment repository).

## What `archive.toml` is

An eval spec (chat prompt + `bash = ["python3"]` tool allowlist) that puts an
agent in the role Design Principles calls the "agentic layer": it inspects
repo state and *decides* four things it is not allowed to guess if state is
ambiguous —

- the experiment name (must match `evals/experiments` naming conventions;
  `evals/analysis` globs by name prefix, so a `.claude`-sourced run's name
  must start with `ccworkflow-` or it silently parses as zero rows)
- which `dev/transformations/<name>` directory to archive
- which artifact dir is active — `.claude` (git-tracked, so presence alone
  proves nothing), `.csloop`, or `.codescribe`
- which `software/<name>` submodule(s) get archival branches/commits

The prompt is explicit that the Python tool (`evals/tools/archive_experiment.py`)
is the "deterministic layer" and must not be reimplemented by hand — a clean
worked example of the agentic-decides / code-executes split the paper argues
for generally.

## What `archive_experiment.py` actually does

`python3 evals/tools/archive_experiment.py <name> --transformation <dir>
--loop-dir <.claude|.csloop|.codescribe> [--submodule <dir>]* [--session-logs <dir>] [--include-dev-tmp]`

1. Creates `evals/experiments/<MM-DD-YYYY>/<slugified-name>/`.
2. Copies the transformation dir, loop artifacts (`logs/toolusage.toml`,
   `loop/{run,author,review,review_output,state}.toml`, `loop/metadata/`), and
   optionally out-of-repo agent session logs (flattened to
   `workflow-wf_<id>/{journal.jsonl,agent-*.jsonl}`, the layout
   `evals/analysis/parse_ccworkflow.py` expects) and `dev/tmp`.
3. Snapshots git context: root repo HEAD/branch/status + every `software/`
   submodule's HEAD/branch/status, written as JSON/txt under `<archive>/git/`.
4. Creates/commits an `evals/<date>/<name>` branch in each named submodule
   (excluding `software/mcfm`'s `Bin`/`install` dirs).
5. Cleans the transformation dir and the loop dir (never `.claude`, since
   it's git-tracked) back to a pristine state.
6. Writes `archive_summary.json` with all of the above as a manifest.

## Why this matters for the paper

This *is* the mechanism behind Table `tab:runs`, Table `tab:coveragemap`,
Table `tab:coverage`, and Figure `fig:evalcombined` in
`main.tex` §Evaluation (`sec:evaluation`) and §Design of experiments
(`sec:doe`): all twelve `transformations/mcfm-translate` runs (R1-R12,
ccworkflow/csloop/ccloop across Opus 5 / Sonnet 5 / GPT 5.6) were archived
this way into `evals/experiments/<date>/<run-name>/`, and
`evals/analysis/*.py` (parse_ccworkflow.py, parse_csloop.py,
generate_graphs.py, per_file_effort.py, etc.) reads those archives to
produce the paper's cost/time/tool-call/token numbers.

One paper detail confirmed directly from these archives: R12's directory is
literally named `ccworkflow-loop-sonnet-5-run2` (a misleading name per the
paper's own footnote to Table `tab:coveragemap`), which is why the paper
insists on labeling/pricing runs from their transcripts' reported model
rather than from the archive folder name.
