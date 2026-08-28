# mcfm-translate worklist

Worklist for the Fortran → C++ pass. Policy: `current_plan.md`. Contract: `desired_spec.md`.

## Group 1 — Mods (module infrastructure)

Provenance (captured before any editing, from `python3 dev/workflow.py status` and
`python3 dev/workflow.py next mcfm-translate`):

- ready leaves (deps=0, non-blind): 229
- first five lines of `next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
```

The first candidate is `Mods/types_mod.f`, so this group is the `Mods` folder. The
remaining ready files in that folder are (`grep -P "\tMods\t0\t0\t" dev/tmp/assets/roadmap_metrics.tsv`):
`Mods/pp_mod.f90`, `Mods/ppwp2j_mod.f90`, `Mods/Modules_Interface.f90`, `Mods/mod_qcdloop_c.f`.

Scope note: `Mods/Modules_Interface.f90` is deliberately **not** translated in this group.
It is the Fortran interoperability layer required by the Spec's module output shape (the
`_fi` side that mirrors C++ storage with `c_f_pointer`); removing it would break every
already-translated module. It was instead extended to initialise/finalise the two modules
translated here.

Per the Spec coverage map, `Mods` is infrastructure, so files here are marked `TRANSLATED`.

Files:

- [x] software/mcfm/src/Mods/types_mod.f — TRANSLATED (Mods is infrastructure per the Spec coverage map; `types_mod.hpp` added, build passes, bench 272/272 each case explicitly PASSED)
- [x] software/mcfm/src/Mods/mod_qcdloop_c.f — TRANSLATED (interface-only module; `mod_qcdloop_c.hpp` mirrors the QCDLoop `extern "C"` entry points, no C++ caller yet; build passes, bench 272/272)
- [x] software/mcfm/src/Mods/pp_mod.f90 — TRANSLATED (data now in `pp_mod.cpp`/`pp_mod.hpp`, Fortran mirror via `c_f_pointer`; build passes, bench 272/272)
- [x] software/mcfm/src/Mods/ppwp2j_mod.f90 — TRANSLATED (data now in `ppwp2j_mod.cpp`/`ppwp2j_mod.hpp`, Fortran mirror via `c_f_pointer`; build passes, bench 272/272)

Group 1 status: complete (no FAILED entries). Oracle run: `jobrunner submit tests/mcfm`
→ `SUMMARY: pass rate 272/272`, every case printed `PASSED`, no `FAILED`/error lines.

## Group 2 — W2jet (atree family)

Provenance. This group was opened in loop 2 immediately after Group 1, from the loop-1
candidate list quoted in Group 1 above (`W2jet/atree.f` was the top **untranslated**
entry once `Mods/types_mod.f` had been settled). The provenance block was not written at
open time; it is reconstructed here from the current tooling output, captured this round
(after the code was already in place):

- ready leaves (deps=0, non-blind), from `python3 dev/workflow.py status`: 227
  (`roadmap metrics: 436 untranslated file rows, 227 ready leaves`)
- first five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/subqcd.f  (fanin=2, bench=u d~ ve e+ g g)
- gghgg_dep/gghgg_dep_params.f  (fanin=2, bench=g g h g g)
```

Why this group's files are not that list's top entries: they have already been translated,
so `next` no longer lists them. At open time the list was headed by `W2jet/atree.f`
(fanin=6) — see the Group 1 provenance block — and the rest of the group was filled from the
same `W2jet` folder per the Plan's folder-coherence rule. `W2jet/ggZZcapture.f` remains the
top candidate for the next group.

Coverage process for `W2jet` per the Spec coverage map: `u d~ ve e+ g g`.
All five probes returned `NOT COVERED` (exit code 1), so all five are `TRANSLATED`:
the bench process reaches the W2jet matrix elements only through callers that are still
Fortran, so these leaves are not exercised yet.

Files:

- [x] software/mcfm/src/W2jet/atree.f — TRANSLATED (coverage probe returned NOT COVERED for u d~ ve e+ g g)
- [x] software/mcfm/src/W2jet/a6treeg.f — TRANSLATED (coverage probe returned NOT COVERED for u d~ ve e+ g g; probe marker first had to be put on a single-line `lhs = rhs;` statement)
- [x] software/mcfm/src/W2jet/a6routine.f — TRANSLATED (coverage probe returned NOT COVERED for u d~ ve e+ g g)
- [x] software/mcfm/src/W2jet/ZZbox1LL.f — TRANSLATED (coverage probe returned NOT COVERED for u d~ ve e+ g g)
- [x] software/mcfm/src/W2jet/fvf.f — TRANSLATED (coverage probe returned NOT COVERED for u d~ ve e+ g g; probe marker first had to be put on a single-line `lhs = rhs;` statement)

Group 2 status: complete (no FAILED entries). Oracle run: `jobrunner submit tests/mcfm`
→ `SUMMARY: pass rate 272/272`, 272 `PASSED` lines counted in `tests/mcfm/job.output`,
no `FAILED` and no `error` lines.

## Group 3 — W2jet (hazard-free leaves)

Provenance (captured before any editing in this round, from `python3 dev/workflow.py refresh` /
`python3 dev/workflow.py status` and `python3 dev/workflow.py next mcfm-translate`):

- ready leaves (deps=0, non-blind): 227
  (`roadmap metrics: 436 untranslated file rows, 227 ready leaves`)
- first five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/subqcd.f  (fanin=2, bench=u d~ ve e+ g g)
- gghgg_dep/gghgg_dep_params.f  (fanin=2, bench=g g h g g)
```

Why these files are not the list's top entry: `W2jet/ggZZcapture.f` (top entry) and
`W2jet/Ftexact.f` are **deferred** — `ggZZcapture.f` writes `ggZZ_mod::res`, whose Fortran
mirror had to be repaired first (see below), and `Ftexact.f` calls the generic module
functions `loopI2`/`loopI3` which have no C++ header or C binding yet, so translating it
would violate the Spec's "never invent a called symbol" rule. The group is therefore led by
`W2jet/subqcd.f` (the next W2jet entry) and filled from the same `W2jet` folder.

Coverage process for `W2jet` per the Spec coverage map: `u d~ ve e+ g g`.
All five probes returned `RESULT: NOT COVERED` (exit code 1), so all five are `TRANSLATED`:
the bench process still reaches these W2jet leaves only through Fortran callers.

Dependency repair done first (Spec: "if a needed module dependency has no usable C binding
yet, stop and rewrite that dependency first"): `software/mcfm/src/Mods/ggZZ_mod.f90` now
associates `res` with the C++ storage instead of copying it —
`call c_f_pointer(get_res(), temp_ptr, [2*4*10*3])` followed by
`res(1:2,1:4,1:10,1:3) => temp_ptr` (rank-remapping pointer association). Before, the module
did `allocate(res(...))` and copied `temp_ptr`, so a future C++ writer of `ggZZ_mod::res`
would have updated storage no Fortran reader could see. Rebuild after the fix:
`SUMMARY: pass rate 272/272`.

Files:

- [x] software/mcfm/src/W2jet/subqcd.f — TRANSLATED (coverage probe returned NOT COVERED for u d~ ve e+ g g)
- [x] software/mcfm/src/W2jet/Acalc.f — TRANSLATED (coverage probe returned NOT COVERED for u d~ ve e+ g g)
- [x] software/mcfm/src/W2jet/LRcalc.f — TRANSLATED (coverage probe returned NOT COVERED for u d~ ve e+ g g)
- [x] software/mcfm/src/W2jet/fpp.f — TRANSLATED (coverage probe returned NOT COVERED for u d~ ve e+ g g)
- [x] software/mcfm/src/W2jet/vv.f — TRANSLATED (coverage probe returned NOT COVERED for u d~ ve e+ g g)

Group 3 status: complete (no FAILED entries). Oracle run: `jobrunner submit tests/mcfm`
→ `SUMMARY: pass rate 272/272`, 272 `PASSED` lines counted in `tests/mcfm/job.output`,
no `FAILED` and no `error` lines (re-run after the coverage probes restored the sources).

## Session log

- 2024 session 1 (loop 1): opened Group 1 (Mods). Added `types_mod.hpp` (namespace `types`,
  the four kind parameters) and `mod_qcdloop_c.hpp` (extern "C" mirror of the QCDLoop
  interface block); both Fortran files stay in the build because the remaining Fortran
  sources still `use` them. Translated the two `pp` data modules to `pp_mod.{hpp,cpp}` and
  `ppwp2j_mod.{hpp,cpp}` (flat Fortran-order storage plus the `pp_at` index helper), rewrote
  `pp_mod.f90` / `ppwp2j_mod.f90` as `c_f_pointer` mirrors that keep `ppmax` and the
  `pp(-4:4,-4:4,-4:4,-4:4)` bounds, wired both `.cpp` files into `Mods/CMakeLists.txt`, and
  registered the new `*_mod_init` / `*_mod_finalize` in `Modules_Interface.f90`.
  Verified with `jobrunner submit tests/mcfm`: rebuild succeeded (new `pp_mod.cpp.o`,
  `ppwp2j_mod.cpp.o` objects present) and the bench reported `SUMMARY: pass rate 272/272`
  with each individual case printing `PASSED`. All four files recorded `TRANSLATED`
  because `Mods` has no coverage process in the Spec's coverage map.
  Remaining in this folder: `Mods/Modules_Interface.f90` (kept Fortran on purpose, see the
  scope note above). Next round: check the gate, then open the next group from
  `python3 dev/workflow.py next mcfm-translate` (currently headed by `W2jet/atree.f`).

- 2024 session 2 (loop 2): gate passed, so Group 2 (`W2jet`, the `atree` family) was opened
  from the loop-1 candidate list, headed by `W2jet/atree.f`. Translated five files to the
  Spec's three-file shape — `atree`, `a6treeg`, `a6routine`, `ZZbox1LL`, `fvf` — each as
  `<base>.hpp` + `<base>.cpp` (with `extern "C" <base>_wrapper`) + `<base>_fi.F90` shim
  keeping the original Fortran entry name. Cross-unit C++ calls go through the siblings'
  headers (e.g. `a6routine.cpp` includes `a6treeg.hpp`, `ZZbox1LL.hpp`, `fvf.hpp`), and calls
  to still-Fortran callees stay as `extern "C"` pointer-argument declarations, per the Spec.
  Wired the new `.cpp`/`_fi.F90` files into `software/mcfm/src/W2jet/CMakeLists.txt` (and the
  include path in `software/mcfm/CMakeLists.txt`), and moved the five originals to
  `software/mcfm/src/W2jet/deprecated/`. Oracle: `jobrunner submit tests/mcfm` →
  `SUMMARY: pass rate 272/272`, no `FAILED`. Verification needed `MCFM_HOME`, which the
  restricted shell cannot export inline, so the probes were driven through small scratch
  scripts (`dev/tmp/move_w2jet.py`, `dev/tmp/verify_w2jet.py`, `dev/tmp/verify_all.py`) that
  set `MCFM_HOME=software/mcfm` via `os.environ` before calling `dev/workflow.py verify`.
  The Group 2 results were not written to this log during loop 2.

- 2024 session 3 (loop 3): finished and logged Group 2. Re-ran `refresh` (227 ready leaves,
  90 translated / 436 untranslated) and confirmed the five Group 2 files no longer appear in
  `next`. The coverage probes for `a6treeg.cpp` and `fvf.cpp` had failed with
  `error: could not scale the marked line`, because `coverage_check.py` only rewrites a
  probe that is a single-line `lhs = rhs;   // @coverage-probe` statement; the marked
  assignments spanned several lines. Joined those two assignments onto one line each (the
  expressions are unchanged) and re-ran the probes: both now report
  `RESULT: NOT COVERED` (exit 1), matching `atree`, `a6routine` and `ZZbox1LL`. So all five
  files are `TRANSLATED`; nothing in the `u d~ ve e+ g g` bench reaches them yet because
  their callers (`ggZZcapture`, `subqcd`, and the W2jet amplitude drivers) are still Fortran.
  Re-ran the oracle after the reformat: `jobrunner submit tests/mcfm` →
  `SUMMARY: pass rate 272/272` with 272 `PASSED` lines and zero `FAILED`/`error` lines in
  `tests/mcfm/job.output`. Scratch scripts under `dev/tmp/` are kept and documented here as
  the `MCFM_HOME` workaround for the restricted shell; they contain no project logic.
  Next round: check the gate (Groups 1 and 2 are both complete and pending approval, both
  free of `FAILED`), then open Group 3 from `next`, currently headed by
  `W2jet/ggZZcapture.f` with `W2jet/subqcd.f` as the folder-coherent companion.
  Gate result this round: `GATE: OK — completed groups do not yet require approval
  (2 waiting, limit 3)`, so Group 3 may be opened. It was deliberately **not** opened in
  this session (no partial group left behind) because the session budget was spent finishing
  and logging Group 2; no Group 3 heading exists yet, so the next round starts clean.

  Scouting note for Group 3 (no files edited, no group opened). Candidate set from
  `grep -P "\tW2jet\t0\t0\t" dev/tmp/assets/roadmap_metrics.tsv`, ranked:
  `ggZZcapture.f` (fanin 6), `subqcd.f` (2), then `Acalc.f`, `Ftexact.f`, `LRcalc.f`,
  `Ltfunctions.f`, ... (fanin 1). Two hazards found while reading them:
  1. `ggZZcapture.f` writes the module array `ggZZ_mod::res`. The existing mirror in
     `software/mcfm/src/Mods/ggZZ_mod.f90` does **not** alias the C++ storage: it does
     `allocate(res(1:2,1:4,1:10,1:3))` and then *copies* `temp_ptr` into it, so a C++
     writer would update the C++ array while every Fortran reader keeps looking at the
     stale copy. Per the Spec ("if a needed module dependency has no usable C binding yet,
     stop and rewrite that dependency first") `ggZZ_mod.f90` should first be changed to a
     true rank-remapping pointer association (`res(1:2,1:4,1:10,1:3) => temp_ptr`) before
     `ggZZcapture.f` is translated; otherwise that translation is silently wrong wherever
     the ggZZ path is exercised. `ggZZintegrals_mod.f90` does not have this problem
     (`D0(1:5) => temp_ptr(1:5)` is a real pointer remap), so `Acalc.f`, which only reads
     `C0`/`D0`, is safe.
  2. `Ftexact.f` calls the generic module functions `loopI2`/`loopI3` from
     `loopI2_generic`/`loopI3_generic`, which have no C++ header or C binding, so it is not
     translatable yet under the "never invent a called symbol" rule.
  Suggested Group 3 content, all `W2jet` and all free of those hazards:
  `subqcd.f`, `Acalc.f`, `LRcalc.f`, `fpp.f`, `vv.f` — with a one-line note in the group
  saying `ggZZcapture.f` (the top `next` entry) and `Ftexact.f` are deferred for the two
  reasons above.

- 2024 session 4 (loop 4): opened and completed Group 3 (`W2jet`, hazard-free leaves), with
  the provenance block written before any code edit (227 ready leaves; `next` still headed by
  `W2jet/ggZZcapture.f`). First repaired the dependency found while scouting:
  `Mods/ggZZ_mod.f90` now does `call c_f_pointer(get_res(), temp_ptr, [2*4*10*3])` +
  `res(1:2,1:4,1:10,1:3) => temp_ptr`, a true rank-remapping pointer association onto the
  C++ `FArray4D res(2,4,10,3)` storage, replacing the previous `allocate` + copy. Then
  translated `subqcd.f`, `Acalc.f`, `LRcalc.f`, `fpp.f`, `vv.f` to the Spec's three-file shape
  (`<base>.hpp` + `<base>.cpp` with `extern "C" <base>_wrapper` + `<base>_fi.F90` keeping the
  original Fortran entry name). Statement functions became lambdas, `amp(-1:1,-1:1)` became
  `FArray2D<std::complex<double>> amp(famp,3,3,-1,-1)`, and every callee already available in
  C++ is reached through its header (`Need.hpp` for `lnrat`/`L0`/`L1`/`Lsm1`/`Lsm1_2mht`,
  `W1jet.hpp` for `t`, the `Mods` headers for `s`, `C0`/`D0`, `epinv`, `epinv2`, `musq` and the
  `ZZclabels`/`ZZdlabels` index constants) — no new `extern "C"` Fortran declarations were
  needed. Wired the ten new files into `src/W2jet/CMakeLists.txt` and moved the five originals
  to `src/W2jet/deprecated/` (via `dev/tmp/move_group3.py`, since the restricted shell has no
  `mv`). Each new `.cpp` carries exactly one single-line `lhs = rhs;   // @coverage-probe`
  statement, as `coverage_check.py` cannot scale a multi-line assignment. Oracle:
  `jobrunner submit tests/mcfm` → `SUMMARY: pass rate 272/272`, 272 `PASSED` lines, no
  `FAILED`/`error` lines — both before and after the five probes (all `NOT COVERED`, exit 1,
  driven through `dev/tmp/verify_all.py`, which sets `MCFM_HOME`). Remaining W2jet blockers
  are unchanged: `ggZZcapture.f` is now unblocked by the `ggZZ_mod` repair but was left for a
  later group, and `Ftexact.f` still needs `loopI2_generic`/`loopI3_generic` C bindings.
  Human decision needed: three completed groups (1, 2, 3) are now pending approval, so the
  gate blocks opening Group 4. Gate result this round, verbatim:
  `GATE: BLOCKED — approval batch limit reached before opening a new group.` /
  `Blocking group: Group 1 — Mods (module infrastructure)` /
  `Reason: 3 completed group(s) are waiting; limit is 3`. Per the Plan's *When to stop*, work
  stops here until a human records an approval (e.g.
  `python3 dev/workflow.py approve mcfm-translate --latest-blocking`); after that, refresh the
  roadmap and open Group 4 (`W2jet/ggZZcapture.f` is now unblocked and still tops `next`).
