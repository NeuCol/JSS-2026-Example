"""Reconstruct the doxygen-derived readiness map as it stood at the fork point.

`dev/workflow.py refresh` builds `dev/tmp/assets/roadmap_metrics.tsv` via
`dev/tools/index/build_roadmap.py --doxygen`. Columns: rel, top, deps, blind,
fanin, bench. A file is ready to rewrite when `deps == 0 and blind == 0`
(no untranslated callees, and doxygen can see it); `dev/workflow.py next`
prints ready leaves in the file's own sort order, `(deps asc, fanin desc)`,
so the map's recommendation is "unblock the most dependents first".

WHY THIS MODULE EXISTS, rather than just reading a run's archived TSV:

Every run archives its own copy, but `dev/tmp` is captured *after* the run
finishes, so the archived map has already dropped the files that run just
settled. Using a run's own map as "the map the model saw" is therefore exactly
backwards -- it is missing precisely the rows you want to ask about. Empirically
the archived maps are post-run for every run but the three earliest, whose maps
were refreshed once mid-run and so are partially stale.

All evals/* branches share one fork point (git_file_counts.BASE_REF), so the
pre-run map is identical for every run and can be recovered instead of
re-derived: `archived rows ∪ that run's settled files`. Eight of the eleven runs
carrying a map reconstruct to exactly the same 445 files, and that set is also
the union across all of them -- the three that fall short are the mid-run
refreshes, which lost rows no reconstruction can restore. So the union is used.

Per-file attributes are recovered the same way, by observing each file across
every archived map:
  - `blind` and `fanin` are invariant (measured: zero files disagree across the
    eleven maps), so any observation will do.
  - `deps` is the count of *untranslated* callees, so it falls monotonically as
    work lands. Only 41 of 445 files ever disagree, by at most 4. The largest
    observation is therefore the earliest state, and that is the one kept.

Rebuilding the map directly at BASE_REF would be more direct, but needs doxygen
and a submodule checkout at that ref; the call graph itself is not archived
(`symbol_index.json` is symbol->file only, with no edges).
"""

import csv
from pathlib import Path

# `is_blind` in build_roadmap.py: doxygen cannot resolve these, so readiness is
# unknown rather than satisfied.
READY_DEPS = 0
READY_BLIND = 0


def _run_roadmap(run_dir):
    """Rows of one run's archived roadmap, or None if it archived none."""
    tsv = Path(run_dir) / "dev" / "tmp" / "assets" / "roadmap_metrics.tsv"
    if not tsv.exists():
        return None
    with tsv.open() as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def _unit_of(rel):
    """Roadmap `rel` ("W2jet/atree.f") to the unit id git_file_counts uses
    ("W2jet/atree"), so the two sources can be joined."""
    for ext in (".f90", ".F90", ".f"):
        if rel.endswith(ext):
            return rel[: -len(ext)]
    return rel


def fork_point_roadmap(experiments_root, runs, translated_units):
    """{unit: {"deps", "blind", "fanin", "top"}} as of the shared fork point.

    `runs` is the (day, run_name, ...) registry; `translated_units` maps a run
    key to its settled units (or None). Runs that archived no map contribute
    nothing but are harmless.
    """
    attrs = {}
    for day, run_name, *_ in runs:
        rows = _run_roadmap(Path(experiments_root) / day / run_name)
        if rows is None:
            continue
        for row in rows:
            unit = _unit_of(row["rel"])
            deps = int(row["deps"])
            # Largest observed deps is the earliest state -- see module docstring.
            if unit not in attrs or deps > attrs[unit]["deps"]:
                attrs[unit] = {
                    "deps": deps,
                    "blind": int(row["blind"]),
                    "fanin": int(row["fanin"]),
                    "top": row["top"],
                }
    # Add back each run's own settled files, which its post-run map dropped.
    # Their attributes come from whichever *other* map still lists them; a file
    # every map dropped is unrecoverable and is reported by `missing_attrs`.
    for key, units in translated_units.items():
        for unit in units or []:
            attrs.setdefault(unit, None)
    return attrs


def ready_pool(attrs):
    """Units the map called ready to rewrite at the fork point."""
    return {
        u for u, a in attrs.items()
        if a is not None and a["deps"] == READY_DEPS and a["blind"] == READY_BLIND
    }


def recommendation_order(attrs):
    """Units in the order `dev/workflow.py next` would print them: the map's own
    sort, `(deps asc, fanin desc)`. Units with no recovered attributes sort last
    rather than being dropped, so the list stays a total order over the corpus."""
    known = [u for u, a in attrs.items() if a is not None]
    unknown = sorted(u for u, a in attrs.items() if a is None)
    known.sort(key=lambda u: (attrs[u]["deps"], -attrs[u]["fanin"], u))
    return known + unknown


def missing_attrs(attrs):
    """Units settled by some run that no archived map still describes."""
    return sorted(u for u, a in attrs.items() if a is None)


def post_run_ready(run_dir):
    """Ready leaves in a run's OWN archived map, i.e. the state it left behind.

    Paired with the fork-point pool this gives an outcome measure rather than a
    process one: files that were not ready before the run and are ready after
    it were unblocked BY that run's work. Returns None when the run archived no
    map.

    Caveat the caller must respect: for the three earliest runs the archived map
    was refreshed part-way through rather than at the end, so their "after"
    state is partial and undercounts. `roadmap_is_post_run` flags them.
    """
    rows = _run_roadmap(run_dir)
    if rows is None:
        return None
    return {_unit_of(r["rel"]) for r in rows
            if int(r["deps"]) == READY_DEPS and int(r["blind"]) == READY_BLIND}


def roadmap_is_post_run(run_dir, settled):
    """True when the archived map post-dates all of the run's work.

    A map written after the run has dropped every file the run settled. One
    that still lists some of them was refreshed mid-run, so anything derived
    from it is a lower bound, not a measurement.
    """
    rows = _run_roadmap(run_dir)
    if rows is None:
        return False
    listed = {_unit_of(r["rel"]) for r in rows}
    return not (set(settled or []) & listed)
