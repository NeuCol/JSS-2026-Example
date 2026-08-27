"""Exact (git ground-truth) count of Fortran source files translated per run,
cross-checked against the self-reported `- [x]` checklist counts in
agent_log.md (parse_coverage.coverage_for_run), which can drift from what
actually landed in the submodule (see MISMATCHES below).

Each translated routine in software/mcfm follows one of two patterns relative
to the shared fork point (BASE_REF):
  - rename:  src/<mod>/X.f -> src/<mod>/deprecated/X.f   (git sees this as R100)
  - delete:  src/<mod>/X.f removed outright (no matching rename pair, but a
             new src/<mod>/X.cpp appears alongside it)
Both replace the original with new src/<mod>/{X.cpp, X_fi.F90, and often a
shared X.hpp or per-module .hpp}. We count ONE original file's removal as ONE
translated file — the new .cpp/.hpp/_fi.F90 outputs of that same translation
are not counted again, and shared-infrastructure edits (CMakeLists.txt,
Modules_Interface.f90 etc., which never remove an original source file) count
as zero.

Do not trust archive_summary.json's "archive_branch" field as the branch
name — for at least one run (08-11-2026/csloop-opus-5) it names a branch that
doesn't exist ("codescribe-opus-5"); the branch that actually exists is named
after the run directory itself ("csloop-opus-5"). Branch names are resolved
here from the run directory name, with an explicit existence check.
"""

import subprocess
from pathlib import Path

MCFM_DIR = Path(__file__).parent.parent.parent / "software" / "mcfm"
BASE_REF = "1abdcddaad89582552edc41de68e4a6e1ac75f1d"  # shared fork point for every evals/* branch seen so far


def _git(*args):
    result = subprocess.run(
        ["git", "-C", str(MCFM_DIR), *args],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def _resolve_branch_ref(day, run_name):
    """Prefer the remote ref (always present); fall back to a local branch of
    the same name if origin/... doesn't resolve."""
    for candidate in (f"origin/evals/{day}/{run_name}", f"evals/{day}/{run_name}"):
        try:
            _git("rev-parse", "--verify", candidate)
            return candidate
        except subprocess.CalledProcessError:
            continue
    return None


def translated_file_units(day, run_name):
    """Sorted list of unit identifiers for original Fortran files retired
    (renamed to deprecated/ or deleted outright) under src/, relative to
    BASE_REF — e.g. "BDK/M1bit1", "W2jet/fpp". One entry per translated file;
    the .cpp/.hpp/_fi.F90 outputs of that translation are not separate
    entries. Returns None if the branch can't be found."""
    ref = _resolve_branch_ref(day, run_name)
    if ref is None:
        return None
    diff = _git("diff", "--name-status", BASE_REF, ref, "--", "src/")
    units = []
    for line in diff.splitlines():
        parts = line.split("\t")
        status, path = parts[0], parts[1]
        if status.startswith("R") and status != "R100":
            continue  # partial-similarity renames aren't seen in practice; be conservative
        if status == "R100":
            units.append(path)
        elif status == "D" and path.rstrip().lower().endswith((".f", ".f90")):
            units.append(path)
    # Strip "src/" prefix and extension so the identifier is stable whether
    # the file was found via a deprecated/ rename or a plain delete.
    cleaned = []
    for u in units:
        u = u[len("src/"):] if u.startswith("src/") else u
        for ext in (".f90", ".F90", ".f"):
            if u.endswith(ext):
                u = u[: -len(ext)]
                break
        cleaned.append(u)
    return sorted(cleaned)


def translated_file_count(day, run_name):
    """Exact count of original Fortran files retired, relative to BASE_REF.
    Returns None if the branch can't be found."""
    units = translated_file_units(day, run_name)
    return None if units is None else len(units)


def module_of(unit):
    """Top-level src/ subdirectory a unit belongs to, e.g. "BDK" for
    "BDK/M1bit1". Units are built from the pre-rename path (see
    translated_file_units), so this is always the module the file lived in
    before translation, never "deprecated"."""
    return unit.split("/")[0]


def discover_runs(experiments_root):
    """Every run directory in the corpus, oldest day first.

    Deliberately not the figure set: which runs the paper plots is
    generate_graphs.RUNS's business, and importing it here would be circular
    (generate_graphs imports this module). A hand-copied list drifts out of
    date the moment a run is added or dropped, so the CLI below enumerates the
    corpus instead — including runs the figures exclude, since "no archival
    branch" is one of the things this tool exists to report.
    """
    return [
        (day.name, run.name)
        for day in sorted(experiments_root.iterdir())
        if day.is_dir()
        for run in sorted(r for r in day.iterdir() if r.is_dir())
    ]


if __name__ == "__main__":
    import sys

    experiments = Path(__file__).parent.parent / "experiments"
    args = sys.argv[1:]
    runs = [tuple(a.split("/", 1)) for a in args] if args else discover_runs(experiments)

    for day, run_name in runs:
        units = translated_file_units(day, run_name)
        if units is None:
            print(f"{day}/{run_name}: no archival branch — no git-exact count")
        else:
            print(f"{day}/{run_name}: {len(units)} {units}")
