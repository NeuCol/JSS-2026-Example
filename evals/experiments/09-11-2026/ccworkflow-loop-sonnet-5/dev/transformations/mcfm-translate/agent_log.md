# mcfm-translate agent log

## Group 1 — W2jet BDK helicity building blocks

Provenance (captured before editing):

- ready leaves (from `python3 dev/workflow.py status`): 229
- first five lines of `python3 dev/workflow.py next mcfm-translate`:
  ```
  - Mods/types_mod.f  (fanin=8, bench=)
  - W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
  - W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
  - BDK/fvs.f  (fanin=2, bench=)
  - W2jet/ZZbox1LL.f  (fanin=2, bench=u d~ ve e+ g g)
  ```
- Not a straight top-5 slice: skipped `Mods/types_mod.f` (known untranslatable — see
  `mcfm-untranslatable-mods-units` note; it and `Modules_Interface.f90` rank as ready
  leaves but must stay Fortran) and `BDK/fvs.f` (different top-level folder). Took the
  first W2jet candidate (`atree.f`) and filled the rest of the group from W2jet's own
  ready list (`grep -P "\tW2jet\t0\t0\t" dev/tmp/assets/roadmap_metrics.tsv`): `atree.f`,
  `ggZZcapture.f`, `ZZbox1LL.f`, `a6treeg.f`, `fvf.f`.

Each file rewritten as `<base>.cpp` + `<base>.hpp` + `<base>_fi.F90`, wired into
`software/mcfm/src/W2jet/CMakeLists.txt` in place of the `.f` entry, original moved to
`software/mcfm/src/W2jet/deprecated/`. Callers of all five remain plain Fortran (atree:
a6.f/a6routine.f/atrLLL.f/atrLRL.f/Z2jet/atreez.f; ggZZcapture: docheck-gated ZZ-box
files; ZZbox1LL: ZZmassiveboxtri.f/ZZmassivebox.f; a6treeg: a6g.f/qqbZggtree.f/xzqqgg.f;
fvf: xzqqgg_v.f) — each keeps its Fortran-facing entry point via `_fi.F90` calling the
new `extern "C"` wrapper, with `character` arguments (`atree`'s `st`, `ggZZcapture`'s
`label`) marshalled across the boundary as `(pointer, length)` since callers only ever
pass string literals (no other char-passing convention existed yet in this codebase).
W2jet is not yet in the top-level `CMakeLists.txt`'s `target_include_directories` list
(only Inc/Mods/Need/loop/Z/W/Z1jet/W1jet/ggH are), so each new file's own header is
pulled in with a quoted `#include "base.hpp"` (searches the including file's own
directory first) rather than `<base.hpp>`; the existing cross-folder include of
`W1jet.hpp` (for `t()`) still uses angle brackets since W1jet is in that list.

Verify: probe process `u d~ ve e+ g g` (W2jet row in the Spec's coverage map), via
`python3 dev/workflow.py verify <file> -- u d~ ve e+ g g` (unquoted process tokens —
see `verify-probe-quoting-trap`: a single quoted string here silently reads NOT COVERED
for everything). Built from `software/mcfm/Bin` (the real out-of-source build dir —
running `cmake .`/`make` from the `software/mcfm` source root instead creates a broken
in-source qcdloop self-copy; that stray in-source build tree was cleaned up after
discovering the mistake). Coverage-probe markers placed on the wrapper's full return
value for the three functions (`atree`, `a6treeg`, `Fvf`) so any call at all is caught
regardless of which internal branch fires; for the two `void` subroutines
(`ggZZcapture`, `ZZbox1LL`) the marker sits on one representative output-array
assignment inside the routine itself.

- [x] software/mcfm/src/W2jet/atree.f — TRANSLATED (NOT COVERED by `u d~ ve e+ g g`; all
      callers — a6.f, a6routine.f, atrLLL.f, atrLRL.f, Z2jet/atreez.f — still Fortran and
      not reached by this probe)
- [x] software/mcfm/src/W2jet/ggZZcapture.f — TRANSLATED (NOT COVERED; all call sites are
      `if (docheck) call ggZZcapture(...)` debug/consistency checks, `docheck` off by
      default, and are gg-initiated ZZ-box checks unrelated to this quark-initiated probe)
- [x] software/mcfm/src/W2jet/ZZbox1LL.f — TRANSLATED (NOT COVERED; callers
      ZZmassiveboxtri.f/ZZmassivebox.f not reached by this probe)
- [x] software/mcfm/src/W2jet/a6treeg.f — TRANSLATED (NOT COVERED; callers a6g.f,
      qqbZggtree.f, xzqqgg.f not reached by this probe)
- [x] software/mcfm/src/W2jet/fvf.f — TRANSLATED (NOT COVERED; caller xzqqgg_v.f not
      reached by this probe)

Restored build after every verify cycle passes `test -b u d~ ve e+ g g` at the required
tolerance (1e-13), confirmed once more after the last verify call.

Group is complete (5/5 files settled, 0 FAILED). Per the gate, up to 3 completed groups
may accumulate before approval — this is the 1st, so no approval needed yet before
opening Group 2.

## Session log

- 2026-09-11: Opened and completed Group 1 (see above). Ran
  `python3 dev/workflow.py refresh` first (445 untranslated rows, 229 ready leaves,
  86 already translated). All 5 files build clean and the restored MCFM build still
  matches its benchmark to 1e-13; none were exercised by the W2jet probe process so all
  are TRANSLATED rather than VERIFIED. No FAILED files, no human decision needed. Ready
  set is far from empty (229 ready leaves before this group), so continuing to Group 2
  is expected next loop unless the gate blocks (it doesn't, at 1 completed group).
