# MCFM Translate Agent Log

## Group 1: Mods (part 1) — core module translation and coverage assessment

Ready-leaf count (`python3 dev/workflow.py status`): 229 ready leaves.

First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
```

Only the first entry (`Mods/types_mod.f`) is a top candidate from that list; the remaining
four files below are not — they fill out `Mods/types_mod.f`'s own top-level `src/` folder
(`Mods`) per Resolution rule 2, for folder coherence.

- [x] software/mcfm/src/Mods/types_mod.f — TRANSLATED (Mods = infrastructure per Spec coverage map, no process maps to it, so no coverage probe; build pass. Header-only outcome: `types.hpp` declares an empty `namespace types` because module `types` holds only KIND parameters (sp/dp/ex/qp) — the Spec's rewrite table turns `real(dp)`/`complex(dp)` into `double`/`std::complex<double>` at each call site, so there is nothing to mirror via `c_f_pointer` and no `.cpp`/`_fi` is possible. Same shape as the existing `constants_mod`/`blabels_mod` precedent in this folder. `types_mod.f` deliberately stays in `Mods/CMakeLists.txt` and is NOT moved to `deprecated/`: ~100 still-untranslated Fortran files `use types` and need the compiled module. Header compiles standalone (`g++ -std=c++17 -fsyntax-only`). NOTE for the human reviewer: `dev/workflow.py next` still lists `Mods/types_mod.f` as a candidate because the index keys off a generated `.cpp`; the header-only outcome is deliberate and needs a human to confirm it counts as settled.)
- [x] software/mcfm/src/Mods/pp_mod.f90 — TRANSLATED (Mods infrastructure per Spec coverage map, no coverage probe applicable; build pass. `pp_mod.hpp`/`pp_mod.cpp` hold `FArray4D<int> pp(9,9,9,9,-4,-4,-4,-4)` filled from a 6561-entry literal — Integrate re-verified all 6561 values element-by-element against the `reshape` literal in `deprecated/pp_mod.f90`: identical, 80 non-zero entries in both. `pp_mod.f90` is now a `c_f_pointer` shim re-exporting `pp` with bounds `(-4:,-4:,-4:,-4:)` plus the original `include 'ppmax.f'`/`ppmax`, which `Z2jet/qqb_z2jetx_new.f` still needs via `use pp_mod`. Wired in by Integrate: `pp_mod.cpp` added to `src/Mods/CMakeLists.txt`, and `pp_mod_init`/`pp_mod_finalize` added to `Modules_Interface.cpp` (the original `.f90` never listed pp_mod — its table used to be a `save`d Fortran array needing no setup; without the init call the Fortran view would stay null). Exercised at runtime: the Zjj bench processes pass.)
- [x] software/mcfm/src/Mods/ppwp2j_mod.f90 — TRANSLATED (Mods infrastructure per Spec coverage map, no coverage probe applicable; build pass. `ppwp2j_mod.hpp`/`ppwp2j_mod.cpp` hold `FArray4D<int> pp(9,9,9,9,-4,-4,-4,-4)`; Integrate re-verified all 6561 literal values element-by-element against `deprecated/ppwp2j_mod.f90`: identical, 72 non-zero entries in both. `ppwp2j_mod.f90` is the matching `c_f_pointer` shim, keeping `ppmax = 80` public because `W2jet/qqb_wp2jetx_new.f` still does `use ppwp2j_mod` and references bare `ppmax`. Wired in by Integrate: `ppwp2j_mod.cpp` added to `src/Mods/CMakeLists.txt` and `ppwp2j_mod_init`/`ppwp2j_mod_finalize` added to `Modules_Interface.cpp` for the same reason as pp_mod. Exercised at runtime: the W+jj/W-jj bench processes pass.)
- [x] software/mcfm/src/Mods/Modules_Interface.f90 — TRANSLATED (Mods infrastructure per Spec coverage map, no coverage probe applicable; build pass. Original moved to `deprecated/Modules_Interface.f90`; `src/Mods/CMakeLists.txt` now lists `Modules_Interface.cpp` in its place. The source was not a Fortran module but two `bind(C, name="modules_fi_init_"/"modules_fi_finalize_")` subroutines, so no `_fi.F90` shim was created — a shim re-declaring those bind(C) names would define the same linker symbols twice; the `extern "C" modules_fi_init_()/modules_fi_finalize_()` definitions live directly in the `.cpp`, which is exactly what `BLHA/CXX_Interface.cxx` already declares and calls. The 58 `<mod>_init`/`<mod>_finalize` callees are still genuine Fortran, so they are declared by their gfortran mangled names per the Spec's "callee is still Fortran" rule, in the source's original order; pp_mod/ppwp2j_mod appended by Integrate as described above.)
- [x] software/mcfm/src/Mods/mod_qcdloop_c.f — TRANSLATED (Mods infrastructure per Spec coverage map, no coverage probe applicable; build pass. Header-only: the module is purely a `bind(C)` interface block forwarding to the external QCDLoop 2.0.5 C library — no module state and no executable bodies — so `mod_qcdloop_c.hpp` mirrors each interface entry 1:1 with no invented symbol, and there is no `.cpp`/`_fi.f90` to write. `mod_qcdloop_c.f` deliberately stays in `Mods/CMakeLists.txt` and is NOT moved to `deprecated/`: `Procdep/chooser.f` and `gghgg_dep/ggHgg.f` still call `qli1..qli4` through `use mod_qcdloop_c`. Same header-only precedent as `blabels_mod`/`constants_mod`. Header compiles standalone (`g++ -std=c++17 -fsyntax-only`); nothing includes it yet, so the quad-precision `qli*q` entries mapped to `__float128` are unexercised — flagged for the human reviewer.)

### Integrate round — 2026-08-27

Wiring applied here (authors were forbidden to touch build/shared files):

- `software/mcfm/src/Mods/CMakeLists.txt`: added `pp_mod.cpp` and `ppwp2j_mod.cpp`; replaced
  `Modules_Interface.f90` with `Modules_Interface.cpp`. `types_mod.f` and `mod_qcdloop_c.f`
  intentionally left as Fortran entries (still-untranslated callers depend on them).
- `software/mcfm/src/Mods/Modules_Interface.cpp`: appended `pp_mod_init`/`ppwp2j_mod_init` and
  the matching finalizers — the one cross-unit change this round needed, made once, here.

Correctness bar (`desired_spec.md` → Oracle `V`): `jobrunner submit tests/mcfm` — full clean
CMake build plus `Bin/bench`. Result: **SUCCESS, pass rate 272/272**, every case printing an
explicit `PASSED` (checked for the silent-segfault trap: no case is silent, no `FAILED`
marker, and the summary line accounts for all 272). Zjj and W+jj/W-jj sections pass, which is
what actually exercises the new `pp`/`ppwp2j` `c_f_pointer` tables through
`Z2jet/qqb_z2jetx_new.f` and `W2jet/qqb_wp2jetx_new.f`.

The coverage half of `V` (`dev/workflow.py verify <file.cpp> -- <process>`) was **not** run: the
Spec's coverage map maps no process to `Mods` and states outright that `Mods` is
infrastructure to be marked `TRANSLATED`. No unit here is claiming `VERIFIED`, so no unit is
claiming a coverage result that did not fire.

Remaining for a human: confirm the two header-only outcomes (`types_mod.f`,
`mod_qcdloop_c.f`) count as settled, since `dev/workflow.py next` still lists
`Mods/types_mod.f` as a candidate (the index keys off a generated `.cpp`). Approval itself is
a human action — no `approve_group.py` run and no `approvals.toml` edit was made here.

## Group 2: W2jet (part 1) — tree and box-function amplitude translation

Ready-leaf count (`python3 dev/workflow.py status`): 225 ready leaves.

First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
```

This group's files are not that list's top entries: entry 1 (`Mods/types_mod.f`) was already
settled in Group 1 (header-only outcome, deliberately left un-moved so still-Fortran callers
can `use` it, which is why the `.cpp`-keyed index still lists it as a candidate), and entry 4
(`BDK/fvs.f`) sits in a different top-level folder. Per Resolution rule 2, the anchor is the
next actionable entry, `W2jet/atree.f` (fanin=6), with the rest of the group filled from that
file's own top-level `src/` folder (`W2jet`), in the same ranked order `next` prints them.

- [x] software/mcfm/src/W2jet/atree.f — TRANSLATED (build pass, not covered: `coverage_check.py` reports `NOT COVERED` under **both** processes the Spec's coverage map assigns to `W2jet` — `u d~ ve e+ g g` and `u u~ e- e+ g g`. Scaling the marked `atree_value` by 1.5 leaves every printed number bit-identical, so no bench case reaches this file yet. Re-probe once a caller (`a6.f`, `a6routine.f`, `atrLLL.f`, `atrLRL.f`) is rewritten. C++ entry point plus `atree_fi.f90` shim keep the still-Fortran callers linking; `character(len=2) st` crosses the boundary as `trim(st)//c_null_char` → `const char*`.)
- [x] software/mcfm/src/W2jet/ggZZcapture.f — TRANSLATED (build pass, not covered: `NOT COVERED` under both `W2jet`-mapped processes. Integrate moved this unit's `// @coverage-probe` marker onto the `res(htag,ltag,itag,imt0) = amp0;` statement — the author had left it on a line of its own, which `coverage_check.py` cannot scale (it rewrites `lhs = rhs; // @coverage-probe` on one line and aborts otherwise), so as delivered the probe could not have fired at all. With the marker fixed the probe runs and still reports no change, so `TRANSLATED` is the honest status. Re-probe when a ggZZ coefficient routine (`ZZmbc.f`, `ZZmassivebub.f`, …) is rewritten.)
- [x] software/mcfm/src/W2jet/ZZbox1LL.f — VERIFIED (worst Δrel < 1e-13 — `u u~ e- e+ g g` prints `Finite/IR/IR2/Born ratio = 1` exactly at the harness's 1e-13 tolerance, and the full restored suite is 272/272. `coverage_check.py … -- u u~ e- e+ g g` reports `COVERED`: scaling `Xpp(h3,h5)` moves Finite from 3.1535139416645479e-09 to 3.1648325962327528e-09. Note this file is covered by the Spec's *second* `W2jet` row, not the first — it reports `NOT COVERED` under `u d~ ve e+ g g`. Required the shared `FArray.hpp` fix recorded below; before that fix this unit alone regressed 28 Zjj cases.)
- [x] software/mcfm/src/W2jet/a6treeg.f — VERIFIED (worst Δrel < 1e-13 — `u d~ ve e+ g g` prints all four ratios as exactly 1 at 1e-13 tolerance, full restored suite 272/272. `coverage_check.py … -- u d~ ve e+ g g` reports `COVERED`. All 8 helicity branches plus the `unimplemented st` fallback translated line-by-line; `t()` resolves to the already-translated `W1jet/t.cpp` via `W1jet.hpp`, no invented symbol.)
- [x] software/mcfm/src/W2jet/fvf.f — TRANSLATED (build pass, not covered: `NOT COVERED` under both `W2jet`-mapped processes. Integrate had to **add** the `// @coverage-probe` marker (as `Fvf_res = Fvf_res;` before the return, matching the sibling `atree.cpp`/`a6treeg.cpp` pattern) — the author shipped none, and `coverage_check.py` exits 2 on a file with no marker, so this unit could not have been probed as delivered. Independently confirmed non-coverage by bisect: relinking the original `deprecated/fvf.f` in place of `fvf.cpp` reproduces `u u~ e- e+ g g` bit-for-bit. Its only caller, `W2jet/xzqqgg_v.f` → `a64v`, is not reached by these benches; re-probe when that is rewritten.)

### Integrate round — 2026-08-27

Wiring applied here (authors were forbidden to touch build/shared files):

- `software/mcfm/src/W2jet/CMakeLists.txt`: swapped all five `.f` entries for their
  `.cpp` + `_fi` pairs (`atree`, `a6treeg`, `fvf`, `ggZZcapture`, `ZZbox1LL`).
- `software/mcfm/CMakeLists.txt`: added `src/W2jet` to the `objlib`, `libmcfm` and `test`
  `target_include_directories` lists, and an `install(DIRECTORY src/W2jet/ …)` block beside the
  `src/W1jet/` one. Every unit this round includes its own header angle-bracketed
  (`#include <atree.hpp>`), matching the `src/W1jet` convention, so the folder had to join the
  include path. Flagged by the `fvf` author; done once, here.
- `software/mcfm/src/Inc/FArray.hpp`: **shared bug fix** — see below.

Shared fix: `FArray4D`'s attach-to-Fortran-array constructor was missing its `nl` parameter:

```
FArray4D(T* fortranArray, size_t ni, size_t nj, size_t nk, int start_i=1, …)
    : ni(ni), nj(nj), nk(nk), nl(nl), …
```

so `nl(nl)` self-initialised to garbage, and `ZZbox1LL.cpp`'s correct-looking
`FArray4D<…> Xrat(fXrat, 2, 2, 2, 2)` silently bound its fourth `2` to `start_i`. Every
`Xrat(i,…)` access was then off by one, and `Xrat(1,…)` indexed element `-1` — an
out-of-bounds write into `ZZmassivebox`'s neighbouring stack arrays. Symptom: 244/272, with 28
Zjj `g g` cases failing at `Finite ratio = 1.0005068664092713` while Born/IR/IR2 stayed exact.
Isolated by relinking the five units one at a time against their `deprecated/` originals
(all-Fortran baseline passed; the regression appeared only with `ZZbox1LL.cpp` in the link).
Added the missing `size_t nl`. `ZZbox1LL.cpp` was already written against the intended
signature and needed no change. The other four `FArray4D` users (`pp_mod`, `ppwp2j_mod`,
`ggZZ_mod`) use the allocating constructor and were never affected.

Correctness bar (`desired_spec.md` → Oracle `V`), both halves run:

1. `jobrunner submit tests/mcfm` — full `make clean` + CMake configure + build + `Bin/bench`.
   Result: **SUCCESS, pass rate 272/272**, all 272 printing an explicit `PASSED` and zero
   `FAILED` markers. Checked for the silent-segfault trap: the summary accounts for all 272
   cases, so no case produced no output. Both mapped probe processes pass by name
   (`u d~ ve e+ g g`, `u u~ e- e+ g g`).
2. `dev/tools/coverage/coverage_check.py <file.cpp> -- <process>` per unit, against both
   processes the Spec's coverage map assigns to `W2jet`. `COVERED`: `a6treeg` (first process),
   `ZZbox1LL` (second). `NOT COVERED` under both: `atree`, `fvf`, `ggZZcapture`.

Two tooling notes for a human — neither changes a status above, but both silently produce
false `NOT COVERED` verdicts and will mislead the next round:

- `python3 dev/workflow.py verify …` **cannot ever report `COVERED`**. `workflow.py`'s `run()`
  launches every subprocess with `cwd=ROOT`, but `Bin/test` only finds `process.DAT` /
  `params.lh` when run from `$MCFM_HOME/Bin`; from the project root it prints
  `Process not available in MCFM.` for baseline and probed alike, so the two outputs match and
  the tool concludes the file was never executed. All five units reported `NOT COVERED`
  through `workflow.py`. Re-running the same oracle as `dev/tools/coverage/coverage_check.py`
  with `cwd=$MCFM_HOME/Bin` (explicitly sanctioned by the Plan's Tools section) flipped
  `a6treeg` and `ZZbox1LL` to `COVERED`; hand-scaling `Xpp` and diffing the bench output
  confirmed `ZZbox1LL` independently. The Plan's "run these from the project root" is wrong for
  `verify`, or `workflow.py` should pass `cwd=$MCFM_HOME/Bin` for this subcommand.
- The Spec maps `W2jet` to two processes on two separate rows, and the choice matters: each
  `COVERED` unit this round is covered by exactly one of them and reports `NOT COVERED` under
  the other. `roadmap_metrics.tsv`'s `bench` column lists only the first. Probing a single
  process would have downgraded `ZZbox1LL` to `TRANSLATED`.

Also worth a human's attention: two of the five units could not have been probed as authored —
`ggZZcapture.cpp` had its `@coverage-probe` on a standalone comment line (unscalable by the
regex) and `fvf.cpp` had no marker at all (`coverage_check.py` exits 2). Integrate placed both,
following the `a6treeg.cpp` pattern already established in this folder. Worth restating in the
Plan that the marker must sit on a single-line `lhs = rhs;` statement.

Group 2 is now complete with no `FAILED` unit. Approval is a human action — no
`approve_group.py` run and no `approvals.toml` edit was made here.

## Group 3: BDK (part 1) — one-loop helicity coefficient-function translation

Ready-leaf count (`python3 dev/workflow.py status`): 231 ready leaves.

First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/subqcd.f  (fanin=2, bench=u d~ ve e+ g g)
- gghgg_dep/gghgg_dep_params.f  (fanin=2, bench=g g h g g)
```

Entry 1 (`Mods/types_mod.f`) was already settled in Group 1 (header-only outcome, deliberately
left un-moved so still-Fortran callers can `use` it, which is why the `.cpp`-keyed index still
lists it as a candidate). Per Resolution rule 2, the anchor is the next actionable entry,
`BDK/fvs.f` (fanin=2), with the rest of the group filled from that file's own top-level `src/`
folder (`BDK`), in the same ranked order `next` prints them.

- [x] software/mcfm/src/BDK/fvs.f — TRANSLATED (build pass, not covered: `coverage_check.py` reports `NOT COVERED` under **both** processes the Spec's coverage map assigns to `BDK` — `u d~ ve e+ g g` and `u u~ e- e+ g g`. Scaling `Fvs_res` by 1.5 leaves every printed number bit-identical. Same cause as `W2jet/fvf.f` in Group 2: the only caller is `W2jet/xzqqgg_v.f` → `a64v`, which no bench case reaches (`Tri3masscoeff.f`'s `Fvs` is a local variable, not this symbol). Re-probe once `xzqqgg_v.f` is rewritten. C++ entry point plus `fvs_fi.f90` shim keep the still-Fortran caller linking; `Brackpm`/`Brackpma` stay file-local `static`, `Brackppa`/`Brackpp` and `t()` became lambdas.)
- [x] software/mcfm/src/BDK/FFMPcc.f — VERIFIED (worst Δrel < 1e-13 — both BDK-mapped processes print `Finite/IR/IR2/Born ratio = 1` at the harness's 1e-13 tolerance, and the full restored suite is 272/272 with an explicit `PASSED` on every case. `coverage_check.py` reports `COVERED` under **both** `u d~ ve e+ g g` and `u u~ e- e+ g g`. Only `FFMPcc` is exported; `FFMPcc_unsym`/`FFMPcc1`/`FFMPcc2` stay file-local `static`. `t()` resolves to the already-translated `W1jet/t.cpp` via `W1jet.hpp`, `i3m`/`L0`/`Lsm1*` via `Need.hpp` — no invented symbol.)
- [x] software/mcfm/src/BDK/FFPMccT.f — VERIFIED (worst Δrel < 1e-13 — ratios exactly 1 at 1e-13 tolerance on both BDK-mapped processes, full restored suite 272/272. `coverage_check.py` reports `COVERED` under both. Integrate fix: six integer literals multiplying `std::complex<double>` (`4*zab`, `-2*zba`, `+5*zab`, `+2*zab`, `+3*(…)`, `-2*(…)`) had no viable `operator*` and broke the build; changed to `4.0`/`2.0`/`5.0`/`3.0` — value-preserving, no reparenthesisation.)
- [x] software/mcfm/src/BDK/FFPMccTtilde.f — VERIFIED (worst Δrel < 1e-13 — ratios exactly 1 at 1e-13 tolerance on both BDK-mapped processes, full restored suite 272/272. `coverage_check.py` reports `COVERED` under both, even though its only named caller `BDK/FFPMcc.f` is still Fortran — it reaches this unit through the `FFPMccTtilde_fi.f90` shim, which is exactly what the shim is for. Compiled clean as authored.)
- [x] software/mcfm/src/BDK/FFPMscT.f — VERIFIED (worst Δrel < 1e-13 — ratios exactly 1 at 1e-13 tolerance on both BDK-mapped processes, full restored suite 272/272. `coverage_check.py` reports `COVERED` under both. Integrate fix: three `3 * <complex>` products (lines 57, 73, 84) had no viable `operator*` and broke the build; changed to `3.0 *`. The `3 * s(...)` and `2 * s(...)` products on real `s`/`Delta3` were left alone.)

### Integrate notes (Group 3)

Shared wiring done once here, as the Plan's Resolution step 6 requires:

- `src/BDK/CMakeLists.txt` — each of the five `.f` entries replaced in place by its `.cpp` +
  `_fi.f90` pair (`FFPMscT_fi.F90` keeps the author's capital-F extension).
- `software/mcfm/CMakeLists.txt` — `src/BDK` added to all three
  `target_include_directories` lines (`objlib`, `libmcfm`, `test`) and a matching
  `install(DIRECTORY src/BDK/ …)` header rule added. Without this the new `#include <FFMPcc.hpp>`
  style angle-bracket includes do not resolve, since `.` alone does not put `src/BDK` on the
  search path. This is the same shared change Group 2 made for `src/W2jet`; expect one more
  per folder as new folders are opened.

Two authored units did not compile as delivered. Both failures are the same one-line C++ rule:
`int * std::complex<double>` has no viable `operator*` (the standard only provides
`T * complex<T>`), so a bare integer coefficient that is legal in Fortran is a hard compile
error in C++. Nine literals across `FFPMccT.cpp` and `FFPMscT.cpp` were promoted to `double`
literals; no expression was otherwise re-associated or reparenthesised. Worth adding to the
Spec's rewrite table — the current table covers `x**n` but says nothing about integer literals
in mixed-mode arithmetic, and it will recur in every remaining BDK coefficient file.

Correctness bar (`desired_spec.md` → Oracle `V`), both halves run after the fixes:

1. `jobrunner submit tests/mcfm` — full `make clean` + CMake configure + build + `Bin/bench`.
   Result: **SUCCESS, pass rate 272/272**, every one of the 272 cases printing an explicit
   `PASSED`, zero `FAILED` markers, harness tolerance `1.0e-13`. Silent-segfault trap checked:
   the summary accounts for all 272 cases, so no case produced no output. Both BDK-mapped probe
   processes pass by name (`u d~ ve e+ g g`, `u u~ e- e+ g g`). Re-run once more after the last
   coverage probe restored its file, to confirm the restored build is what passes.
2. `dev/tools/coverage/coverage_check.py <file.cpp> -- <process>` per unit, against both
   processes the Spec's coverage map assigns to `BDK`. `COVERED` under both: `FFMPcc`,
   `FFPMccT`, `FFPMccTtilde`, `FFPMscT`. `NOT COVERED` under both: `fvs`.

The `dev/workflow.py verify` cwd bug reported at the end of Group 2 is **still present** and was
re-confirmed this round: `python3 dev/workflow.py verify software/mcfm/src/BDK/FFPMccT.cpp --
u d~ ve e+ g g` reports `NOT COVERED`, while the identical oracle run as
`dev/tools/coverage/coverage_check.py` from `$MCFM_HOME/Bin` reports `COVERED` for the same
file. `workflow.py` launches `Bin/test` with `cwd=ROOT`, where it cannot find `process.DAT` /
`params.lh` and prints `Process not available in MCFM.` for baseline and probed alike, so the
two outputs match and every file looks uncovered. Taking `verify` at face value would have
downgraded four VERIFIED units to TRANSLATED this round. A human should either fix
`workflow.py` to pass `cwd=$MCFM_HOME/Bin` or change the Plan's Verify section to call
`coverage_check.py` directly.

Unlike Group 2, coverage here was decided by the unit, not by the process: all four covered BDK
units are covered by *both* mapped processes, so a single-process probe would have been
sufficient this round. That is not a general rule — `ZZbox1LL` in Group 2 needed the second row.

Group 3 is complete with no `FAILED` unit. Approval is a human action — no `approve_group.py`
run and no `approvals.toml` edit was made here.
