# mcfm-translate worklist

## Group 1 — W2jet tree/box amplitudes

Provenance (recorded at group open, before editing):

- Ready-leaf count from `python3 dev/workflow.py status`: **229 ready leaves**
  (445 untranslated file rows; taken right after `python3 dev/workflow.py refresh`).
- First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
```

Why this group is not simply that list's top entries:

- `Mods/types_mod.f` (rank 1) was skipped: it only defines `selected_real_kind` kind
  parameters. A Fortran kind must be a compile-time constant, so the Spec's `c_f_pointer`
  module mirror cannot be written for it, and the rewrite table already absorbs `real(dp)`
  into `double`. It is a deletion candidate, not a translation candidate.
- `W2jet/ggZZcapture.f` (rank 3) was skipped: its only output is the `res` array of
  `ggZZ_mod`, and `Mods/ggZZ_mod.f90`'s `ggZZ_mod_init` **copies** the C++ array into a
  separately allocated Fortran array (`res(1:2,1:4,1:10,1:3) = temp_ptr(...)`) instead of
  aliasing it. Writes made from C++ would therefore never be seen by its Fortran reader
  `W2jet/ZZmbc.f`. Per the Spec ("if a needed module dependency has no usable C binding
  yet, stop and rewrite that dependency first") this needs `ggZZ_mod` fixed first.
- `BDK/fvs.f` (rank 4) is in a different top-level folder; per Resolution step 2 the group
  is filled from the first translated candidate's own folder (`W2jet`).

The group therefore takes the first workable candidate, `W2jet/atree.f`, and fills the rest
from `W2jet`'s remaining ready leaves in rank order: `ZZbox1LL.f`, `a6treeg.f`, `fvf.f`,
`subqcd.f` (all `deps=0 blind=0`, bench `u d~ ve e+ g g`).

Coverage process used: `u d~ ve e+ g g` (Spec coverage map, W2jet).
Positive control for the probe batch: `a6treeg.cpp` reported COVERED with the process passed
unquoted, so the uniformly-negative probe failure modes are ruled out for this batch.

Results:

- [x] software/mcfm/src/W2jet/a6treeg.f — VERIFIED (worst Δrel ≤1e-13; bench 272/272 passed)
- [x] software/mcfm/src/W2jet/subqcd.f — VERIFIED (worst Δrel ≤1e-13; bench 272/272 passed)
- [x] software/mcfm/src/W2jet/atree.f — TRANSLATED (build passes, probe NOT COVERED under both `u d~ ve e+ g g` and `u u~ e- e+ g g` — re-probed 2026-09-12)
- [x] software/mcfm/src/W2jet/fvf.f — TRANSLATED (build passes, probe NOT COVERED under both `u d~ ve e+ g g` and `u u~ e- e+ g g` — re-probed 2026-09-12)
- [x] software/mcfm/src/W2jet/ZZbox1LL.f — VERIFIED (worst Drel <=1e-13; bench 272/272 passed; COVERED under `u u~ e- e+ g g` — see the 2026-09-12 revision note)

Group 1 is complete: 5 files settled, 0 FAILED.

## Group 2 — BDK finite virtual pieces

Provenance (recorded at group open, before editing):

- Ready-leaf count from `python3 dev/workflow.py status`: **232 ready leaves**
  (440 untranslated file rows; taken right after `python3 dev/workflow.py refresh`).
- First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/w2jetsq.f  (fanin=2, bench=u d~ ve e+ g g)
```

Why this group is not simply that list's top entries: ranks 1 and 2 are the same two
permanent skips recorded under Group 1 (`Mods/types_mod.f` is untranslatable; the
`ggZZ_mod` mirror copies rather than aliases `res`, so `W2jet/ggZZcapture.f` cannot be
moved to C++ yet). The first workable candidate is therefore `BDK/fvs.f`, and per
Resolution step 2 the rest of the group comes from its own folder, `BDK`, taking that
folder's next ready leaves: `FFPMccT.f`, `FFPMccTtilde.f`, `FFPMscT.f`, `FFPMscTtilde.f`
(all `deps=0 blind=0`).

Coverage process used: `u d~ ve e+ g g` (Spec coverage map, BDK). Four of the five probes
came back COVERED, which is itself the positive control for this batch — the uniformly
negative probe failure modes are ruled out.

Results:

- [x] software/mcfm/src/BDK/FFPMccT.f — VERIFIED (worst Drel <=1e-13; bench 272/272 passed)
- [x] software/mcfm/src/BDK/FFPMccTtilde.f — VERIFIED (worst Drel <=1e-13; bench 272/272 passed)
- [x] software/mcfm/src/BDK/FFPMscT.f — VERIFIED (worst Drel <=1e-13; bench 272/272 passed)
- [x] software/mcfm/src/BDK/FFPMscTtilde.f — VERIFIED (worst Drel <=1e-13; bench 272/272 passed)
- [x] software/mcfm/src/BDK/fvs.f — TRANSLATED (build passes, probe NOT COVERED under both `u d~ ve e+ g g` and `u u~ e- e+ g g` — re-probed 2026-09-12)

Group 2 is complete: 5 files settled, 0 FAILED.

## Group 3 — W2jet ggZZ coefficients and tree square

Provenance (recorded at group open, before editing):

- Ready-leaf count from `python3 dev/workflow.py status`: **228 ready leaves**
  (435 untranslated file rows; taken right after `python3 dev/workflow.py refresh`).
- First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/w2jetsq.f  (fanin=2, bench=u d~ ve e+ g g)
- gghgg_dep/gghgg_dep_params.f  (fanin=2, bench=g g h g g)
```

Why this group is not simply that list's top entries: ranks 1 and 2 are the same two
permanent skips recorded under Group 1 — `Mods/types_mod.f` is untranslatable (kind
parameters must be compile-time constants), and `W2jet/ggZZcapture.f` writes the `res`
array of `ggZZ_mod`, whose Fortran mirror **copies** rather than aliases it, so a C++
writer would never be seen by its Fortran reader `W2jet/ZZmbc.f`. The first workable
candidate is therefore `W2jet/w2jetsq.f`, and per Resolution step 2 the rest of the group
comes from its own folder, `W2jet`, taking that folder's next ready leaves in rank order:
`Acalc.f`, `Ftexact.f`, `LRcalc.f`, `Ltfunctions.f` (all `deps=0 blind=0`).

Coverage process used: both W2jet rows of the Spec coverage map. `u d~ ve e+ g g` covers
the W-sector unit (`Ftexact`); the ggZZ/axial units (`Acalc`, `LRcalc`, `Ltfunctions`) are
Z-sector code reached only by `u u~ e- e+ g g`, which the coverage map lists for W2jet as
well. Four of the five probes came back COVERED, which is itself the positive control for
this batch — the uniformly-negative probe failure modes are ruled out.

Results:

- [x] software/mcfm/src/W2jet/Acalc.f — VERIFIED (worst Drel <=1e-13; bench 272/272 passed)
- [x] software/mcfm/src/W2jet/Ftexact.f — VERIFIED (worst Drel <=1e-13; bench 272/272 passed)
- [x] software/mcfm/src/W2jet/LRcalc.f — VERIFIED (worst Drel <=1e-13; bench 272/272 passed)
- [x] software/mcfm/src/W2jet/Ltfunctions.f — VERIFIED (worst Drel <=1e-13; bench 272/272 passed)
- [x] software/mcfm/src/W2jet/w2jetsq.f — TRANSLATED (build passes, probe NOT COVERED under both `u d~ ve e+ g g` and `u u~ e- e+ g g`)

Group 3 is complete: 5 files settled, 0 FAILED.

## Notes / session log

### 2026-09-12

- Opened and completed Group 1 (five `W2jet` files). Each Fortran source became
  `<base>.cpp` + `<base>.hpp` + `<base>_fi.F90`; every `.cpp` includes its own header,
  and the originals were moved to `software/mcfm/src/W2jet/deprecated/`.
  `software/mcfm/src/W2jet/CMakeLists.txt` swaps each `.f` entry for the `.cpp` + `_fi.F90`
  pair.
- Cross-unit calls go through headers: `atree`, `a6treeg` and `fvf` call the already
  translated `t` via `<W1jet.hpp>`, and `fvf` calls `i3m`, `Lsm1_2mh`, `Lsm1_2me` via
  `<Need.hpp>`. No Fortran forward declarations were added and no called symbol was invented.
  `ZZbox1LLcore` has no caller outside `ZZbox1LL.f`, so it stays an internal (`static`)
  function of `ZZbox1LL.cpp` rather than gaining a header entry or a shim.
- `src/W2jet` is not on the CMake include path, so W2jet units include their own headers
  with quotes (`#include "atree.hpp"`) and module/Need headers with angle brackets.
- Verification: `jobrunner submit tests/mcfm` → `SUMMARY: pass rate 272/272`, 0 FAILED, with
  every case showing an explicit `PASSED` (checked for the silent-segfault trap). The suite
  was re-run after the probes restored the sources, and still reports 272/272.
- Human decision needed: `Mods/ggZZ_mod.f90` mirrors `res` by copy, not by `c_f_pointer`
  alias, which blocks translating any routine that writes a `ggZZ_mod` variable
  (`W2jet/ggZZcapture.f` today). The same pattern should be audited for other
  mutable-module mirrors before those callers are picked up.
- Tooling note: `dev/tools/coverage/coverage_check.py::run_test` was again missing
  `cwd=bin`, which makes `Bin/test` run from the repo root, print
  "Process not available in MCFM." for both the baseline and the probed build, and report
  every probe as NOT COVERED. It was re-applied before any probe in this session (the
  `a6treeg` positive control confirms the tool now works). This fix is still uncommitted and
  keeps regressing; it should be committed permanently.
- Remaining: `W2jet` still has ~25 ready leaves; `Mods/types_mod.f` and
  `Mods/Modules_Interface.f90` keep ranking as ready leaves but are not translatable and
  should be put on an explicit never-translate list by the Plan owner.
- Opened and completed Group 2 (five `BDK` files) in the same session. `Fvs` keeps its two
  file-local helpers `Brackpm` and `Brackpma` as internal (`static`) functions of
  `fvs.cpp` — neither has a caller outside `fvs.f`, so neither needs a header entry or a
  Fortran shim. `Fvs` itself has no Fortran caller left in the tree, which is consistent
  with its NOT COVERED probe.
- In `BDK`, `t` is the external W1jet function for `FFPMccT`, `FFPMccTtilde` and `FFPMscT`
  (included via `<W1jet.hpp>`), but inside `fvs.f` `t` is a *statement function*; that one
  is translated as a local lambda, and `fvs.cpp` deliberately does not include
  `<W1jet.hpp>` so the two cannot be confused.
- Integer literals multiplying complex values (`4*zab(...)`, `5*zab(...)`) were written as
  `4.0`/`5.0`: `int * std::complex<double>` does not compile, and silently promoting them
  elsewhere would be the kind of change the Spec forbids.
- Gate after Group 2: still OK (2 completed groups, limit 3), so a third group may be
  opened by the next round without human approval.
- Opened and completed Group 3 (five more `W2jet` files: `w2jetsq`, `Acalc`, `Ftexact`,
  `LRcalc`, `Ltfunctions`) in the same session. Same output shape as Groups 1 and 2:
  `<base>.cpp` + `<base>.hpp` + `<base>_fi.F90`, originals moved to
  `software/mcfm/src/W2jet/deprecated/`, and `src/W2jet/CMakeLists.txt` swapping each `.f`
  entry for the `.cpp` + `_fi.F90` pair.
- `w2jetsq.cpp` calls the already translated `subqcd` through `"subqcd.hpp"` (quoted, since
  `src/W2jet` is not on the CMake include path) rather than through a Fortran declaration.
  It is the first unit in this step that writes a mutable module mirror: `mmsq_cs` of
  `mmsq_cs_mod`. That mirror was checked before the file was picked up and it **aliases**
  correctly (`mmsq_cs(0:,1:,1:) => fptr` after `c_f_pointer`), unlike `ggZZ_mod`'s `res`,
  so writes from C++ are visible to Fortran readers. `lc_mod::colourchoice` and
  `ggZZintegrals_mod`'s `C0`/`D0` were checked the same way and also alias.
- `Ftexact.cpp` calls `loopI2`/`loopI3` as ordinary C++ overloads via `<Loop.hpp>` — those
  two are already C++ (`src/loop/loopI2_generic.cpp`, `loopI3_generic.cpp`), so no
  `extern "C"` Fortran boundary was introduced for them.
- `Ltfunctions.f` holds three entry points (`Ltm1`, `Lt0`, `Lt1`), so its one translation
  unit set carries three C++ functions, three wrappers in `Ltfunctions.hpp`, and three
  shims in `Ltfunctions_fi.F90`. `Lt0` and `Lt1` call their siblings as direct C++ calls
  inside the same `.cpp`, not through the Fortran shims.
- `LRcalc.cpp` keeps `zab2`/`zba2` as lambdas capturing only `za`/`zb`, so the statement
  functions' dummy names shadowing the enclosing `k1..k4` is harmless, as in `subqcd`.
- Coverage-map finding, which changes how W2jet units should be probed: the Spec lists
  **two** processes against `W2jet` (`u d~ ve e+ g g` and `u u~ e- e+ g g`). Groups 1 and 2
  probed only the first. The ggZZ / axial code in `W2jet` is Z-sector and is reached only
  by `u u~ e- e+ g g`: `Acalc`, `LRcalc` and `Ltfunctions` all came back NOT COVERED or
  untried under the W process and COVERED under the Z process.
- Revision to Group 1 on that finding: `W2jet/ZZbox1LL.f` was re-probed under
  `u u~ e- e+ g g`, came back COVERED, and its Group 1 entry was upgraded in place from
  TRANSLATED to VERIFIED. `W2jet/atree.f`, `W2jet/fvf.f` and `BDK/fvs.f` were re-probed the
  same way and stayed NOT COVERED under both processes, so they remain TRANSLATED and still
  need their callers (`ZZmassivebox.f`, the `a6`/`fcc` family) in C++ before they can move.
- `W2jet/w2jetsq.f` is NOT COVERED under both W2jet processes, so it is TRANSLATED, not
  FAILED. Its only callers are `qqb_w2jet.f` and `qqb_wp2jetx_new.f`, neither of which the
  benchmark reaches for these two processes.
- Verification: `jobrunner submit tests/mcfm` → `SUMMARY: pass rate 272/272`, 0 FAILED, with
  272 explicit `PASSED` lines (checked for the silent-segfault trap). The suite was run once
  after the translations, and again after the probes restored every source and the build was
  remade clean; both runs report 272/272 and no `* 1.5` probe residue is left in any `.cpp`.
- Tooling note: `dev/tools/coverage/coverage_check.py::run_test` already had its `cwd=bin`
  argument at the start of this session, so no re-application was needed. It is now **staged**
  (`git add`) together with the 45 new C++/shim files in the `software/mcfm` submodule, which
  were previously untracked while their `.f` originals were already staged as renames into
  `deprecated/`. Staging was as far as an agent should go here: the repo is on its default
  branch `main`, so the actual `git commit` is left to a human. Until that commit lands, the
  `cwd=bin` fix can still be lost, and a clean checkout of the submodule still would not build.
- Gate after Group 3: `python3 dev/tools/approve/check_gate.py dev/transformations/mcfm-translate`
  reported `GATE: OK — completed groups do not yet require approval (2 waiting, limit 3)`
  before the group was opened. With Group 3 completed there are now 3 unapproved completed
  groups, which is the limit, so **a human must approve before a fourth group is opened**.
- Stopped at the approval gate without opening Group 4. `python3 dev/workflow.py gate
  mcfm-translate` reports `GATE: BLOCKED — approval batch limit reached before opening a new
  group`, blocking group `Group 1 — W2jet tree/box amplitudes`, and
  `approve mcfm-translate --list-pending` lists all three completed groups (1, 2 and 3) as
  pending. `approvals.toml` still contains only `version = 1` — no approval has ever been
  recorded. Per the Plan (`current_plan.md`: approvals are human-owned, "Stop for human review
  only when the gate blocks the next group") an agent must not record its own approval, so no
  `approve_group.py` call was made. A human must approve before a fourth group is opened.
- Re-verified the settled state of Groups 1–3 rather than starting new work, which the Plan
  permits ("A gate failure blocks new-group creation, not builds, fixes, or verification
  inside the current group"). `jobrunner submit tests/mcfm` → `SUCCESS` in 1:35.2 with
  `SUMMARY: pass rate 272/272` and 272 explicit `PASSED` lines (counted, per the
  silent-segfault trap), no `FAILED`. The 45 translated files still leave the tree green.
- `dev/tools/coverage/coverage_check.py::run_test` still carries its `cwd=bin` argument
  (line 33), so the regression that keeps reappearing has not returned. It remains staged and
  uncommitted.
- Roadmap refreshed: `source 516  translated 86  untranslated 430`, `ready leaves (deps=0,
  non-blind): 225`, symbol index 915 symbols. The refresh prints Doxygen parse errors on
  `src/loop/loopI4_inc.f`, `src/loop/loopI4c_inc.f` and
  `src/W1jet/gpt-4o-conversions/A52_fi.f90`; these are pre-existing and unrelated to this
  step's output.
- Group 4 composition confirmed still valid after the refresh: `grep -P "\tW2jet\t0\t0\t"`
  lists 31 remaining W2jet ready leaves, including `ZZC012x34LLmp.f`, `ZZbox2LL.f`,
  `ZZintegraleval.f`, `ZZmbc.f` and `ZZtri12_34LL.f` — the five named as next by rank last
  session. `W2jet/ggZZcapture.f` and `Mods/types_mod.f` still head the `next` output and are
  still the logged permanent skips.
- Nothing was committed. The repo is on its default branch `main` and no human asked for a
  commit, so the 45 new files, the 15 `deprecated/` renames, both `CMakeLists.txt`, the
  `coverage_check.py` fix and this log all remain staged/uncommitted and can still be lost.
- Gate re-checked at the start of this session and is **still blocked**:
  `check_gate.py` reports `GATE: BLOCKED — approval batch limit reached before opening a new
  group`, blocking group `Group 1 — W2jet tree/box amplitudes`, and
  `workflow.py approve mcfm-translate --list-pending` lists Groups 1, 2 and 3 as pending.
  `approvals.toml` still contains only `version = 1`. No approval has landed since last
  session, so Group 4 was **not** opened and no `approve_group.py` call was made — approvals
  are human-owned per the Plan. No new units were translated this session.
- Corrected an error in the entry above: the staged rename count was logged as 10, but
  `git -C software/mcfm status --short` reports **15** renames into `deprecated/`
  (10 in `W2jet`, 5 in `BDK`), alongside 45 additions and 2 modified `CMakeLists.txt`.
  The line has been fixed in place; the "45 new files" figure was already correct.
- Structural audit of the settled Groups 1–3 output, all clean:
  every one of the 15 deprecated originals has its full `<base>.cpp` + `<base>.hpp` +
  `<base>_fi.F90` trio present; no `CMakeLists.txt` in `W2jet` or `BDK` still references a
  moved `.f`; and no translated `.cpp` is missing its `.cpp`/`_fi.F90` entry. No `* 1.5`
  probe residue remains in any translated `.cpp` in either directory.
- `dev/tools/coverage/coverage_check.py::run_test` still carries its `cwd=bin` argument, so
  the recurring regression has not returned. Still staged and uncommitted.
- Verification re-run: `jobrunner submit tests/mcfm` → `SUCCESS` in 1:34.9,
  `SUMMARY: pass rate 272/272`, 272 `PASSED` lines counted, 0 `FAILED`, and no
  segfault/"core dumped" text in `tests/mcfm/job.output`. Counting note for future sessions:
  the pass lines are `<process>: PASSED` with ANSI colour codes, so an anchored
  `grep -c '^PASSED'` returns 0 and looks like a silent failure — match `PASS` unanchored.
- Nothing was committed again this session: the repo is still on its default branch `main`
  and no human go-ahead was given, so the whole staged set remains uncommitted.
- Gate checked again at session start and is **still blocked**: `check_gate.py` reports
  `GATE: BLOCKED — approval batch limit reached before opening a new group`, blocking group
  `Group 1 — W2jet tree/box amplitudes` (reason: "3 completed group(s) are waiting; limit is
  3"). `workflow.py approve mcfm-translate --list-pending` lists Groups 1, 2 and 3 as pending
  and `approvals.toml` still contains only `version = 1`. No approval has landed, so Group 4
  was **not** opened and no `approve_group.py` call was made — approvals are human-owned per
  the Plan. No new units were translated this session.
- Group 4 must be re-derived, not reused. The five units named by rank in earlier sessions
  (`ZZC012x34LLmp.f`, `ZZbox2LL.f`, `ZZintegraleval.f`, `ZZmbc.f`, `ZZtri12_34LL.f`) are
  **absent** from the current `dev/workflow.py next mcfm-translate` output, which now heads
  with `Mods/types_mod.f`, `W2jet/ggZZcapture.f`, `gghgg_dep/gghgg_dep_params.f` and seven
  fanin=1 `BDK/FF*`/`FM*`/`FP*` units. After approval, run `dev/workflow.py refresh` first and
  re-derive the group from the refreshed output, still skipping the logged permanent skips
  `Mods/types_mod.f`, `Mods/Modules_Interface.f90` and `W2jet/ggZZcapture.f`.
- Structural audit of settled Groups 1–3 re-run, all clean: all 15 deprecated originals
  (10 `W2jet`, 5 `BDK`) each have their full `<base>.cpp` + `<base>.hpp` + `<base>_fi.F90`
  trio present; no `CMakeLists.txt` in either directory still references a moved `.f`; and no
  `* 1.5` probe residue remains in any translated `.cpp`.
- `dev/tools/coverage/coverage_check.py::run_test` still carries its `cwd=bin` argument
  (line 33), so the recurring regression has not returned. Still staged and uncommitted.
- Verification re-run: `jobrunner submit tests/mcfm` → `SUCCESS` in 1:34.8,
  `SUMMARY: pass rate 272/272`, 272 `PASS` lines counted unanchored (the anchored form returns
  0 — see the ANSI note above), 0 `FAILED`, and no segfault/"core dumped" text in
  `tests/mcfm/job.output`.
- Nothing was committed again this session: still on default branch `main` with no human
  go-ahead, so the 45 additions, 15 `deprecated/` renames, 2 `CMakeLists.txt`, the
  `coverage_check.py` `cwd=bin` fix and this log all remain staged and uncommitted.
