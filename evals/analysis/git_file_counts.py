"""Exact (git ground-truth) count of Fortran source files translated per run,
cross-checked against the self-reported `- [x]` checklist counts in
agent_log.md (parse_coverage.coverage_for_run), which can drift from what
actually landed in the submodule (see MISMATCHES below).

A translated routine in software/mcfm reaches the run's archival branch in one
of three shapes, relative to the shared fork point (BASE_REF). All three count
as one translated file; the new src/<mod>/{X.cpp, X_fi.F90, X.hpp} outputs of
that same translation are never counted again, and shared-infrastructure edits
(CMakeLists.txt, Inc/FArray.hpp, BLHA/CXX_Interface.cxx) count as zero:

  retired / rename   src/<mod>/X.f -> src/<mod>/deprecated/X.f
  retired / delete   src/<mod>/X.f removed outright, a new src/<mod>/X.cpp
                     appearing alongside it
  shadowed           src/<mod>/X.cpp added while src/<mod>/X.{f,f90} is STILL
                     PRESENT on the branch — the translation landed but the
                     original was never retired

Two things about this that earlier versions of this module got wrong, both of
which changed the numbers:

  1. Renames are matched on their DESTINATION, not on their similarity index.
     The previous rule counted only R100 and skipped anything below it as "not
     seen in practice". It is seen in practice: 08-27-2026's two gpt56sol runs
     move a lightly-edited original into deprecated/ (R095 W2jet/atree.f, R096
     Mods/Modules_Interface.f90), which is the retirement pattern exactly, just
     with the file touched on the way. Both were silently dropped. Any rename
     whose destination lands under a deprecated/ directory is a retirement now;
     a rename to anywhere else is still skipped, since that is a move, not a
     translation.

  2. Shadowed translations count. A run that writes X.cpp and leaves X.f90 in
     the tree did the translation work and pays for it in tokens, so scoring it
     zero makes cost-per-file meaningless for that run — 08-27-2026's
     ccworkflow-opus-5 and codescribe-sonnet-5-run2 each land two such units
     (Mods/pp_mod, Mods/ppwp2j_mod) and used to report 0 files settled apiece.
     THE CAVEAT MATTERS THOUGH, and callers should surface it: the original is
     still compiled, so the module has two live implementations and the
     transformation is not actually finished for that unit. `unit_breakdown`
     keeps the two sets apart so a table can report "13 (2 not retired)"
     instead of burying it; only `translated_file_units` unions them.
     A .cpp with no surviving original AND no retirement record is not a
     shadow — it is a new file, and it counts for nothing.

Note that a .hpp alone is never a translation. 08-27-2026/ccworkflow-opus-5
copies Mods/mod_qcdloop_c.f into deprecated/ (git sees an ADD, not a rename,
because the original is still there) and writes mod_qcdloop_c.hpp with no .cpp
behind it. That unit is neither retired nor shadowed and is counted nowhere.

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

# Extensions that make a path an original Fortran source. Matched
# case-insensitively — the corpus mixes .f, .f90 and .F90 for the same role.
FORTRAN_EXTS = (".f", ".f90")
# The directory a retired original is moved into.
DEPRECATED_SEGMENT = "/deprecated/"


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


def _unit_id(path):
    """Path -> stable unit identifier: "src/W2jet/atree.f" -> "W2jet/atree".

    Extension-insensitive on purpose, so the same routine is one unit whether
    it was found as a retired .f, a deleted .f90 or an added .cpp.
    """
    unit = path[len("src/"):] if path.startswith("src/") else path
    lowered = unit.lower()
    for ext in (".f90", ".f", ".cpp"):
        if lowered.endswith(ext):
            return unit[: -len(ext)]
    return unit


def _is_fortran(path):
    return path.rstrip().lower().endswith(FORTRAN_EXTS)


def unit_breakdown(day, run_name):
    """The run's translated units, split by whether the original was retired.

    Returns {"retired": [...], "shadowed": [...]} with both lists sorted and
    disjoint, or None if the run has no archival branch in this clone. Units
    are built from the PRE-rename path, so the module in a unit id is always
    where the file lived before translation, never "deprecated".
    """
    ref = _resolve_branch_ref(day, run_name)
    if ref is None:
        return None

    retired, added_cpp = set(), set()
    for line in _git("diff", "--name-status", "-M", BASE_REF, ref, "--", "src/").splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], parts[1]
        if status.startswith("R"):
            # Matched on destination, not similarity — see the module docstring.
            if len(parts) > 2 and DEPRECATED_SEGMENT in parts[2]:
                retired.add(_unit_id(path))
        elif status == "D" and _is_fortran(path):
            retired.add(_unit_id(path))
        elif status == "A" and path.lower().endswith(".cpp"):
            added_cpp.add(path)

    # A .cpp whose Fortran original is still on the branch is a translation
    # that landed without retiring what it replaced.
    tree = set(_git("ls-tree", "-r", "--name-only", ref, "--", "src/").splitlines())
    shadowed = set()
    for path in added_cpp:
        unit = _unit_id(path)
        if unit in retired:
            continue
        if any(f"src/{unit}{ext}" in tree for ext in (".f", ".f90", ".F", ".F90")):
            shadowed.add(unit)

    return {"retired": sorted(retired), "shadowed": sorted(shadowed)}


def translated_file_units(day, run_name):
    """Sorted list of every unit the run translated — retired originals and
    shadowed ones together (see unit_breakdown for the split, which callers
    reporting a headline count should surface). None if there is no branch."""
    breakdown = unit_breakdown(day, run_name)
    if breakdown is None:
        return None
    return sorted(set(breakdown["retired"]) | set(breakdown["shadowed"]))


def translated_file_count(day, run_name):
    """Exact count of files translated, relative to BASE_REF.
    Returns None if the branch can't be found."""
    units = translated_file_units(day, run_name)
    return None if units is None else len(units)


def shadowed_file_count(day, run_name):
    """How many of translated_file_count's units left their original in place.
    Returns None if the branch can't be found."""
    breakdown = unit_breakdown(day, run_name)
    return None if breakdown is None else len(breakdown["shadowed"])


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
        breakdown = unit_breakdown(day, run_name)
        if breakdown is None:
            print(f"{day}/{run_name}: no archival branch — no git-exact count")
            continue
        retired, shadowed = breakdown["retired"], breakdown["shadowed"]
        total = len(retired) + len(shadowed)
        suffix = f"  [{len(shadowed)} not retired: {', '.join(shadowed)}]" if shadowed else ""
        print(f"{day}/{run_name}: {total} {sorted(retired + shadowed)}{suffix}")
