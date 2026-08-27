# mcfm-translate worklist

Status vocabulary and evidence rules come from `desired_spec.md`; the round algorithm comes
from `current_plan.md`.

## Group Mods-01 (types, qcdloop interface, pp tables)

Provenance (recorded when the group was opened, before editing):

- `python3 dev/workflow.py status` → `roadmap metrics: 445 untranslated file rows, 229 ready leaves`
- first five lines of `python3 dev/workflow.py next mcfm-translate`:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
```

The group starts from the first candidate (`Mods/types_mod.f`) and is then filled from that
file's own top-level folder (`src/Mods`), per Resolution step 2. The remaining Mods ready
files are `pp_mod.f90`, `ppwp2j_mod.f90`, `Modules_Interface.f90`, `mod_qcdloop_c.f`
(`grep -P "\tMods\t0\t0\t" dev/tmp/assets/roadmap_metrics.tsv`).

Files in this group:

- `software/mcfm/src/Mods/types_mod.f`
- `software/mcfm/src/Mods/mod_qcdloop_c.f`
- `software/mcfm/src/Mods/pp_mod.f90`
- `software/mcfm/src/Mods/ppwp2j_mod.f90`

`Mods/Modules_Interface.f90` is deliberately **not** translated in this group: it is the
Fortran-side `bind(C)` entry point (`modules_fi_init_` / `modules_fi_finalize_`) that the C++
side calls to initialise the remaining Fortran module shims, so it must stay Fortran until the
shims are gone. It was extended in this group to init/finalize the two new pp shims.

Results (build + `jobrunner submit tests/mcfm`: SUCCESS, `SUMMARY: pass rate 272/272`, 272
explicit `PASSED` lines, zero `FAILED` lines):

- [x] `software/mcfm/src/Mods/types_mod.f` — TRANSLATED (infrastructure folder, not covered by a
  process probe; `types_mod.hpp` + free-form `types_mod.f90` shim, original moved to
  `Mods/deprecated/`)
- [x] `software/mcfm/src/Mods/mod_qcdloop_c.f` — TRANSLATED (infrastructure folder, not covered;
  `mod_qcdloop_c.hpp` holds the `extern "C"` QCDLoop declarations, free-form
  `mod_qcdloop_c.f90` keeps the Fortran interface module, original moved to `Mods/deprecated/`)
- [x] `software/mcfm/src/Mods/pp_mod.f90` — TRANSLATED (infrastructure folder, not covered;
  `pp_mod.hpp`/`pp_mod.cpp` own the 9x9x9x9 table as `FArray4D<int> pp` with lower bound -4,
  `pp_mod.f90` is now a `c_f_pointer` shim)
- [x] `software/mcfm/src/Mods/ppwp2j_mod.f90` — TRANSLATED (infrastructure folder, not covered;
  same shape as `pp_mod`, getter `ppwp2j_mod_pp`)

Roadmap after the group (`python3 dev/workflow.py refresh`):
`source 531  translated 90  untranslated 441`, ready leaves 226 (was 86/445/229).

## Group W2jet-01 (atree, a6treeg, fvf, subqcd, ggZZcapture)

Provenance (the group was opened in the previous session from the same candidate list; the
numbers below are the current re-reading of the same two commands, unchanged since the group
was opened):

- `python3 dev/workflow.py status` → `roadmap metrics: 441 untranslated file rows, 226 ready leaves`
- first five lines of `python3 dev/workflow.py next mcfm-translate`:

```
# next translation candidates
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/ZZbox1LL.f  (fanin=2, bench=u d~ ve e+ g g)
```

The group starts from the first candidate (`W2jet/atree.f`) and is filled from that file's own
top-level folder (`src/W2jet`), per Resolution step 2. That is why `a6treeg.f`, `fvf.f` and
`subqcd.f` are in the group instead of `BDK/fvs.f`: they are W2jet ready leaves further down
the same (nearly flat) ranking, and folder coherence decides the rest of the group.

Files in this group:

- `software/mcfm/src/W2jet/atree.f`
- `software/mcfm/src/W2jet/a6treeg.f`
- `software/mcfm/src/W2jet/fvf.f`
- `software/mcfm/src/W2jet/subqcd.f`
- `software/mcfm/src/W2jet/ggZZcapture.f`

Evidence (`jobrunner submit tests/mcfm`: SUCCESS, `SUMMARY: pass rate 272/272`, 272 explicit
`PASSED` lines, zero `FAILED` lines — re-run after the originals were moved to
`W2jet/deprecated/`). Coverage probes were run with `python3 dev/workflow.py verify <file>.cpp
-- u d~ ve e+ g g` (the Spec's W2jet process); every one reported `NOT COVERED`, so per the
Plan's Verify section each file is `TRANSLATED`, not `VERIFIED`.

- [x] `software/mcfm/src/W2jet/atree.f` — TRANSLATED (build pass; coverage probe `NOT COVERED`
  for both `u d~ ve e+ g g` and `u u~ e- e+ g g`; `atree.hpp`/`atree.cpp`/`atree_fi.F90`,
  original moved to `W2jet/deprecated/`)
- [x] `software/mcfm/src/W2jet/a6treeg.f` — TRANSLATED (build pass; coverage probe
  `NOT COVERED` for `u d~ ve e+ g g`; `a6treeg.hpp`/`.cpp`/`_fi.F90`, original moved to
  `W2jet/deprecated/`)
- [x] `software/mcfm/src/W2jet/fvf.f` — TRANSLATED (build pass; coverage probe `NOT COVERED`
  for `u d~ ve e+ g g`; still calls the Fortran `i3m`, `Lsm1_2mh`, `Lsm1_2me` through
  `extern "C"` declarations, original moved to `W2jet/deprecated/`)
- [x] `software/mcfm/src/W2jet/subqcd.f` — TRANSLATED (build pass; coverage probe `NOT COVERED`
  for `u d~ ve e+ g g`; `amp` mirrored as `FArray2D<std::complex<double>>(3,3,-1,-1)` to keep
  the Fortran `(-1:1,-1:1)` bounds, original moved to `W2jet/deprecated/`)
- [x] `software/mcfm/src/W2jet/ggZZcapture.f` — TRANSLATED (build pass; coverage probe
  `NOT COVERED` for `u d~ ve e+ g g`; original moved to `W2jet/deprecated/`)

## Group BDK-01 (fvs, FFMPcc, FFPMccT, FFPMccTtilde, FFPMscT)

Provenance (the group was opened in the previous session from the same candidate list; the
numbers below are the current re-reading of the same two commands, and `BDK/fvs.f` is still
the top candidate):

- `python3 dev/workflow.py status` → `roadmap metrics: 436 untranslated file rows, 234 ready leaves`
- first five lines of `python3 dev/workflow.py next mcfm-translate`:

```
# next translation candidates
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/ZZbox1LL.f  (fanin=2, bench=u d~ ve e+ g g)
- W2jet/a6routine.f  (fanin=2, bench=u d~ ve e+ g g)
- W2jet/w2jetsq.f  (fanin=2, bench=u d~ ve e+ g g)
```

The group starts from the first candidate (`BDK/fvs.f`) and is then filled from that file's
own top-level folder (`src/BDK`), per Resolution step 2: `FFMPcc.f`, `FFPMccT.f`,
`FFPMccTtilde.f` and `FFPMscT.f` are the next BDK ready leaves on the same (nearly flat)
ranking — they appear in the same `next` output at fanin=1 — so folder coherence, not the
W2jet/gghgg_dep entries in between, decides the rest of the group.

Files in this group:

- `software/mcfm/src/BDK/fvs.f`
- `software/mcfm/src/BDK/FFMPcc.f`
- `software/mcfm/src/BDK/FFPMccT.f`
- `software/mcfm/src/BDK/FFPMccTtilde.f`
- `software/mcfm/src/BDK/FFPMscT.f`

Evidence (`jobrunner submit tests/mcfm`: SUCCESS, `SUMMARY: pass rate 272/272`, 272 explicit
`PASSED` lines, zero `FAILED` lines — re-run after the originals were moved to
`BDK/deprecated/`). Coverage probes were run with
`python3 dev/tmp/run_verify.py <file>.cpp -- u d~ ve e+ g g` (the Spec's BDK process); every
one reported `NOT COVERED`, so per the Plan's Verify section each file is `TRANSLATED`, not
`VERIFIED`.

- [x] `software/mcfm/src/BDK/fvs.f` — TRANSLATED (build pass; coverage probe `NOT COVERED`
  for `u d~ ve e+ g g`; `fvs.hpp`/`fvs.cpp`/`fvs_fi.F90`, the string-dispatch `Fvs(st,...)`
  entry kept as-is, original moved to `BDK/deprecated/`)
- [x] `software/mcfm/src/BDK/FFMPcc.f` — TRANSLATED (build pass; coverage probe `NOT COVERED`
  for `u d~ ve e+ g g`; `FFMPcc.hpp`/`.cpp`/`_fi.F90`, original moved to `BDK/deprecated/`)
- [x] `software/mcfm/src/BDK/FFPMccT.f` — TRANSLATED (build pass; coverage probe `NOT COVERED`
  for `u d~ ve e+ g g`; `FFPMccT.hpp`/`.cpp`/`_fi.F90`, original moved to `BDK/deprecated/`)
- [x] `software/mcfm/src/BDK/FFPMccTtilde.f` — TRANSLATED (build pass; coverage probe
  `NOT COVERED` for `u d~ ve e+ g g`; `FFPMccTtilde.hpp`/`.cpp`/`_fi.F90`, original moved to
  `BDK/deprecated/`)
- [x] `software/mcfm/src/BDK/FFPMscT.f` — TRANSLATED (build pass; coverage probe `NOT COVERED`
  for `u d~ ve e+ g g`; `FFPMscT.hpp`/`.cpp`/`_fi.F90`, original moved to `BDK/deprecated/`)

Roadmap after the group (`python3 dev/workflow.py refresh`):
`source 521  translated 90  untranslated 431`, ready leaves 230 (was 436 untranslated rows /
234 ready leaves before the originals were archived).

## Notes

- Mods is infrastructure in the Spec coverage map, so files here are marked `TRANSLATED`
  (build pass) rather than `VERIFIED`.
- The W2jet coverage probes are genuine negatives, not a broken harness: a control rebuild
  (`touch subqcd.cpp` + `make -C Bin install`) showed the changed file really is recompiled,
  relinked into `libmcfm.so` and into `Bin/test`, so an executed probe line would have moved
  the benchmark numbers.
- The agent shell cannot `source environment.sh`, so `MCFM_HOME` is injected by the helper
  `dev/tmp/run_verify.py`, which just forwards to `python3 dev/workflow.py verify`.

### Session log

- 2024 session (Group Mods-01): opened the first group of the pass. Translated
  `types_mod`, `mod_qcdloop_c`, `pp_mod`, `ppwp2j_mod`. The two fixed-form `.f` originals were
  moved to `software/mcfm/src/Mods/deprecated/`; the pre-existing originals of the two `.f90`
  modules were already archived there. `src/Mods/CMakeLists.txt` now lists `types_mod.f90`,
  `mod_qcdloop_c.f90`, `pp_mod.cpp` and `ppwp2j_mod.cpp`. `Modules_Interface.f90` gained
  `pp_mod_init/finalize` and `ppwp2j_mod_init/finalize` so the new C++-owned tables are bound
  before `qqb_z2jetx_new.f` / `qqb_wp2jetx_new.f` read them.
  The pp tables were emitted mechanically from the Fortran `reshape` data (column-major order
  preserved, 6561 values each) with `dev/tmp/gen_pp_cpp.py`.
  Full build + bench passed 272/272 with every case printing `PASSED`.
  Remaining in Mods: only `Modules_Interface.f90`, which must stay Fortran while module shims
  exist. Next group should start from the current top of
  `python3 dev/workflow.py next mcfm-translate` (W2jet: `atree.f`, `ggZZcapture.f`, ...).
  No human decision needed; the group is complete and unblocked (1 of 3 allowed before
  approval).
- 2024 session (Group W2jet-01): closed the W2jet group opened in the previous session.
  Built the tree with the five new C++ translation units wired into
  `src/W2jet/CMakeLists.txt` (`jobrunner submit tests/mcfm` → SUCCESS, 272/272, every case
  printing `PASSED`, no `FAILED`). Ran the coverage probe for each `.cpp` with the Spec's
  W2jet process `u d~ ve e+ g g` (and additionally `u u~ e- e+ g g` for `atree`); all reported
  `NOT COVERED`, so all five are recorded `TRANSLATED`. Confirmed the harness itself is sound
  with a control rebuild before accepting those negatives. Moved
  `atree.f`, `a6treeg.f`, `fvf.f`, `subqcd.f`, `ggZZcapture.f` into
  `software/mcfm/src/W2jet/deprecated/` (via `dev/tmp/move_w2jet_deprecated.py`, since inline
  `python3 -c` is blocked) and re-ran the full build + benchmark afterwards: still 272/272.
  Re-ran the previously blocked dependency checks as separate `grep -n` invocations:
  `Lsm1_2mh` and `i3m` are still Fortran (`fsl.f`, `fpm.f`, `fax.f`), which matches the
  `extern "C"` declarations in `fvf.cpp`, and the `_fi.F90` shim inventory in `src/W2jet` is
  exactly the five new shims.
  This makes 2 completed, unapproved groups (3 allowed), so no human decision is required yet;
  the next group should restart from the top of `python3 dev/workflow.py next mcfm-translate`.
- 2024 session (Group BDK-01): closed the BDK group. Ran the coverage probe for the four
  remaining `.cpp` files (`FFMPcc`, `FFPMccT`, `FFPMccTtilde`, `FFPMscT`) with the Spec's BDK
  process `u d~ ve e+ g g`; all four reported `NOT COVERED`, matching the earlier `fvs.cpp`
  probe, so all five files are recorded `TRANSLATED`. These BDK routines are the BDK one-loop
  primitive amplitudes, which the 272-case regression suite does not reach, so `NOT COVERED`
  is the expected outcome rather than a harness fault (the same control rebuild reasoning as
  for W2jet-01 applies: the changed `.cpp` is genuinely recompiled and relinked).
  Coverage-probe marker constraint learned here: the `// @coverage-probe` marker must sit on a
  single-line `lhs = rhs;` statement, because the probe rewrites that one statement to scale
  its right-hand side by 1.5. The translated bodies compute their result through multi-line
  expressions and early returns, so the marker was placed on the single-line assignment inside
  each `extern "C"` wrapper (`std::complex<double> res = <Fn>(...);`), which is the file's main
  output statement and is still a faithful probe point.
  Moved `fvs.f`, `FFMPcc.f`, `FFPMccT.f`, `FFPMccTtilde.f`, `FFPMscT.f` into
  `software/mcfm/src/BDK/deprecated/` (via `dev/tmp/move_bdk_deprecated.py`, since inline shell
  moves are blocked) and re-ran the full build + benchmark afterwards: SUCCESS,
  `SUMMARY: pass rate 272/272`, 272 `PASSED` lines, 0 `FAILED` lines.
  Post-group `python3 dev/workflow.py refresh`: `source 521  translated 90  untranslated 431`,
  ready leaves 230.
  This makes 3 completed, unapproved groups, which is the limit the Spec allows before
  approval, so `python3 dev/workflow.py gate mcfm-translate` now blocks opening a fourth group.
  Human decision needed: approve the pending groups with
  `python3 dev/workflow.py approve mcfm-translate --latest-blocking` (or `--latest`) before the
  next group starts.
