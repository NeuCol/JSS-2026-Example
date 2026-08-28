# MCFM Fortran → C++ Agent Log

## Group 1: Mods — ready leaves (types/pp/ppwp2j/Modules_Interface/qcdloop_c)

Provenance (recorded before any editing):

- Ready leaves (deps=0, non-blind) from `python3 dev/workflow.py status`: **229**
- First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
```

Why the group is not this list's top entries: per Resolution step 2 the group takes the first
candidate (`Mods/types_mod.f`) and is then filled from that file's own top-level folder, so the
remaining four are the other ready `Mods` leaves (`grep -P "\tMods\t0\t0\t"`) rather than the
W2jet/BDK entries ranked 2–5.

- [ ] software/mcfm/src/Mods/types_mod.f
- [x] software/mcfm/src/Mods/pp_mod.f90 — TRANSLATED (Mods is infrastructure per the Spec
  coverage map, so no coverage probe applies; clean build + `jobrunner submit tests/mcfm` bench 272/272 PASSED)
- [x] software/mcfm/src/Mods/ppwp2j_mod.f90 — TRANSLATED (Mods is infrastructure per the
  Spec coverage map, so no coverage probe applies; clean build + `jobrunner submit tests/mcfm` bench 272/272 PASSED)
- [ ] software/mcfm/src/Mods/Modules_Interface.f90
- [x] software/mcfm/src/Mods/mod_qcdloop_c.f — TRANSLATED (declaration-only `bind(C)`
  interface block; header-only per the existing Mods convention, original stays live for its
  5 Fortran users; Mods is infrastructure per the Spec coverage map; clean build + `jobrunner submit tests/mcfm` bench 272/272 PASSED)

## Notes / session log

- 2026-08-27: Opened Group 1 (Mods ready leaves) and recorded provenance before editing. No
  files translated yet in this round; all five units are unchecked. Mods is infrastructure, so
  per the Spec's coverage map these units are expected to settle as `TRANSLATED`.

- 2026-08-27 (Integrate, serial): wired this round's units into the build and ran the Spec's
  oracle. Build wiring — added `src/Mods/pp_mod.cpp` and `src/Mods/ppwp2j_mod.cpp` to
  `src/Mods/CMakeLists.txt`; registered `pp_mod_init/_finalize` and `ppwp2j_mod_init/_finalize`
  in `src/Mods/Modules_Interface.f90` (both the `use ..., only:` lines and the `call` lines, in
  `modules_fi_init` and `modules_fi_finalize`). Without that registration the Fortran `pp`
  pointers stay null and `Z2jet/qqb_z2jetx_new.f` / `W2jet/qqb_wp2jetx_new.f` would hit the
  Spec's silent-segfault trap #9. Also deleted a stray build artifact `src/Mods/pp_mod.mod` that
  an author's out-of-tree syntax check had left in the source dir (gitignored, but `src/Mods` is
  on the compiler's module search path). `mod_qcdloop_c` needs no CMake change: it is
  header-only and headers are not listed in `CMakeLists.txt`.
- 2026-08-27 (Integrate, evidence): `jobrunner submit tests/mcfm` = SUCCESS. Full clean
  reconfigure + `make install` + `./bench`: `SUMMARY: pass rate 272/272`, 272 explicit `PASSED`
  markers and zero `FAILED`, unchanged from the pre-round baseline. The two processes that
  actually consume the new pointers both show an explicit `PASSED`: `u u~ e- e+ g g` (Z2jet →
  `pp_mod`) and `u d~ ve e+ g g` (W2jet → `ppwp2j_mod`). Independently re-checked at Integrate:
  all 6561 constants in `pp_mod.cpp` and `ppwp2j_mod.cpp` are element-for-element identical to
  the `reshape` lists in `deprecated/pp_mod.f90` and `deprecated/ppwp2j_mod.f90` (80 and 72
  nonzero respectively); all 22 `bind(C,name=)` symbols in `deprecated/mod_qcdloop_c.f` match
  `mod_qcdloop_c.hpp` exactly, and a scratch TU including both `Loop.hpp` and
  `mod_qcdloop_c.hpp` compiles clean.
- 2026-08-27 (Integrate, group still open): `software/mcfm/src/Mods/types_mod.f` and
  `software/mcfm/src/Mods/Modules_Interface.f90` remain unchecked. Their authors produced no
  code and no build change for them this round, so neither has settled; they are deliberately
  *not* recorded as `FAILED` (nothing was built or disagreed numerically) and *not* as
  `TRANSLATED` (there is no translated code). `Σ` in the Spec has no status for "attempted, not
  translatable yet", so the lines are left as `- [ ]` rather than inventing one, and Group 1
  stays open. Reasons, for the Plan/Spec owner:
  - `types_mod.f` is nothing but four `selected_real_kind` `parameter`s. A `c_f_pointer` mirror
    is illegal Fortran (a kind must be a compile-time constant), every generated Mods header
    already carries `#include <types.hpp>` commented out with the instruction "Ignore the `use
    types` statement", and the Spec's own rewrite table absorbs `real(dp)` straight into
    `double`. 166 live files still `use types`, 21 of them Fortran-only Mods modules listed in
    `CMakeLists.txt`. It can only retire after the last `use types` disappears. Suggest the
    Spec/Plan owner add it to an explicit never-translate list: `next` ranks it first purely
    because `build_roadmap.py` models callees and not dependents, so it will keep consuming a
    group slot.
  - `Modules_Interface.f90` is itself the Fortran-side interop shim that C++ calls into
    (`BLHA/CXX_Interface.cxx:35-36,171,175` declare and call `modules_fi_init_` /
    `modules_fi_finalize_`), and all 60 of its callees are Fortran *module* procedures with no
    `bind(C)` name. Translating it would require writing gfortran-mangled symbols that appear
    nowhere in the source, and would leave every Fortran module pointer null — the Spec's trap
    #9 again. It becomes actionable only once the Fortran halves of the Mods modules retire, at
    which point these two routines should be deleted rather than translated. Note also that
    `dev/tmp/assets/roadmap_metrics.tsv` scores it `deps=0 blind=0 fanin=0`: the indexer does
    not count `use <mod>, only: <proc>` + `call <proc>()` as a dependency, so a file made
    entirely of such calls looks like a ready leaf.

- 2026-08-27 (Author round, recorded before editing): this round re-attempts the two units still
  unchecked in the open Group 1 — `software/mcfm/src/Mods/types_mod.f` and
  `software/mcfm/src/Mods/Modules_Interface.f90`. No new group was opened and no provenance was
  re-recorded: Group 1 is still open, both units were already listed under it from the prior
  round, and their existing `- [ ]` lines are left as-is (Resolution step 5 — keep filling and
  fixing the open group; the group stays at its 5 same-folder `Mods` units). Verification for
  both is `jobrunner submit tests/mcfm`, build/oracle only: `Mods` is infrastructure in the
  Spec's coverage map and no process maps to it, so no `python3 dev/workflow.py verify` coverage
  probe applies and a settled unit here is `TRANSLATED`, never `VERIFIED`. Per Spec trap #9 the
  bench evidence must be an explicit `passed`/`PASSED` marker per case — absence of `FAILED` is
  not sufficient. The prior round's blockers recorded above (types kinds cannot be mirrored while
  166 files still `use types`; `Modules_Interface` is the Fortran-side shim C++ calls into, with
  60 non-`bind(C)` module-procedure callees) still stand and are the open question for the
  Plan/Spec owner.
