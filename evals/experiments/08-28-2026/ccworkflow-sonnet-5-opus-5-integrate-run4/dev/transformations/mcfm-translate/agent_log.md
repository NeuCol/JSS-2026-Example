# MCFM Translate Agent Log

## Group 1: W2jet (part 1) — tree and box amplitude translation

Ready leaves (from `python3 dev/workflow.py status`): 229

First five lines of `python3 dev/workflow.py next mcfm-translate`:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
```

The list's top entry, `Mods/types_mod.f`, is a known-untranslatable Mods unit and is skipped
(see prior session notes); `W2jet/atree.f` is the first translatable candidate, so it anchors
this group, filled out with the rest of the ready `W2jet` files per the folder-coherence rule.

- [x] software/mcfm/src/W2jet/atree.f — TRANSLATED (build passes; probe NOT COVERED under both W2jet processes)
- [x] software/mcfm/src/W2jet/ggZZcapture.f — TRANSLATED (build passes; probe NOT COVERED — `ggZZ_mod::res` is write-only, see note)
- [x] software/mcfm/src/W2jet/ZZbox1LL.f — VERIFIED (worst Δrel ≤ 1e-13; COVERED under `u u~ e- e+ g g`)
- [x] software/mcfm/src/W2jet/a6treeg.f — VERIFIED (worst Δrel ≤ 1e-13; COVERED under `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/fvf.f — TRANSLATED (build passes; probe NOT COVERED under both W2jet processes)
- [x] software/mcfm/src/W2jet/subqcd.f — VERIFIED (worst Δrel ≤ 1e-13; COVERED under `u d~ ve e+ g g`)

### Session note — 2026-08-28 (serial integrate for Group 1)

**Wiring.** All six units wired in `software/mcfm/src/W2jet/CMakeLists.txt`: each `<base>.f`
entry replaced by `<base>.cpp` + `<base>_fi.F90`. Two shared changes were needed once, here:

1. `software/mcfm/CMakeLists.txt` — added `src/W2jet` to the three
   `target_include_directories` lists (`objlib`, `libmcfm`, `test`). Without it the new
   `#include <a6treeg.hpp>` / `<fvf.hpp>` / `<ggZZcapture.hpp>` do not resolve.
2. `software/mcfm/src/Inc/FArray.hpp` — the `FArray4D` "use existing Fortran array"
   constructor took `(T*, ni, nj, nk, start_i…)`, omitting `nl` and self-initialising the
   member (`nl(nl)`). `ZZbox1LL.cpp`'s `FArray4D Xrat(ptr, 2,2,2,2)` therefore bound the last
   `2` to `start_i`, silently shifting every `Xrat` index by one (Spec silent trap #4). Added
   the missing `size_t nl` parameter, matching `FArray3D`. `ZZbox1LL.cpp` was the only caller
   of that constructor in the tree, so nothing else changed behaviour.

**Shim extension reconciled.** Authors split 3/3 between `_fi.f90` and `_fi.F90`. Normalised
all six to `_fi.F90`, per the Spec's *Output shape*. Note for a human: every other shim
already in the tree (18 files, e.g. `W1jet/t_fi.f90`) uses `.f90`, so either the Spec text or
those older files should eventually be reconciled; both extensions compile.

**Coverage probe added.** `fvf.cpp` arrived with no `// @coverage-probe`, so the oracle could
not run on it. Added `Fvf_result = Fvf_result;  // @coverage-probe` before the return,
mirroring the same pattern already used in `a6treeg.cpp` (the real output is built across
branches, so there is no single plain `lhs = rhs;` output statement to mark).

**Correctness bar.** `jobrunner submit tests/mcfm` — full clean rebuild + `Bin/bench`:
**272/272 PASSED**, benchmark tolerance `1e-13`, zero `FAILED` and zero silent/no-output
cases. Re-run after the probe passes on the restored tree: still 272/272. `bench` reports
pass/fail against the 1e-13 tolerance rather than printing a per-case Δrel, so the VERIFIED
evidence above is "all cases PASSED at tolerance 1e-13", i.e. worst Δrel ≤ 1e-13.

**Human decision needed — `dev/workflow.py verify` cannot fire the probe.**
`dev/tools/coverage/coverage_check.py::run_test` still calls `subprocess.run` on `Bin/test`
with no `cwd=`, and `dev/workflow.py::run` forces `cwd=ROOT`, so the binary runs from the repo
root, cannot find `process.DAT` / `params.lh`, and prints `Process not available in MCFM.`
identically for the baseline and probed builds — making **every** probe report NOT COVERED.
Confirmed here with a positive control: `dev/workflow.py verify …/a6treeg.cpp -- u d~ ve e+ g g`
reported NOT COVERED, while the *same* `coverage_check.py` invoked from `$MCFM_HOME/Bin`
(the cwd `tests/mcfm/test.sh` uses) reported COVERED. All six verdicts above therefore come
from `coverage_check.py` run from `$MCFM_HOME/Bin`; the dev tool itself was **not** edited,
since it is shared tooling outside this transformation's product. A human should decide
whether to land `cwd=bin` in `run_test` so the Spec's own `dev/workflow.py verify` command
works as written.

**Why the four TRANSLATED units are not covered.**
- `atree` / `fvf`: their only remaining callers (`atrLRL.f`, `atrLLL.f`, `a6.f`,
  `a6routine.f`, `xzqqgg_v.f`) are reached only by benchmark variants that `test -b` does not
  drive for either mapped W2jet process. Re-probe once a caller is rewritten.
- `ggZZcapture`: writes only `ggZZ_mod::res`, and nothing in the tree reads `res` back — it is
  debug/check storage guarded by `docheck`. Scaling its output cannot move any number, so this
  unit is structurally unprobeable by the current oracle and cannot reach VERIFIED on coverage
  alone. Separately worth a human eye: `Mods/ggZZ_mod.f90::ggZZ_mod_init` *copies* the C++
  storage into a freshly `allocate`d Fortran `res` rather than aliasing it via `c_f_pointer`,
  so the C++ and Fortran `res` are different arrays. Harmless today because `res` has no
  readers, but it will bite if one is ever added.
- `ZZbox1LL` was NOT COVERED under `u d~ ve e+ g g` but COVERED under `u u~ e- e+ g g`; the
  Spec's coverage map lists both processes for W2jet.

**Author judgement calls checked at first build (all clean).** `atree`'s `character(len=2)`
argument crossing the boundary via an explicit-shape `character(kind=c_char,len=1)` dummy of
size 2 with raw `st[0]`/`st[1]` comparison, and `ggZZcapture`'s `character*(*)` threaded as
`character(kind=c_char), dimension(*)` plus an explicit `label_len` — both compile and run
with the bench green. Neither pattern is exercised elsewhere in the tree yet, and neither is
covered by a probe, so both remain worth a human read before approval.

**Tree state.** Clean and building: `jobrunner submit tests/mcfm` green, no `.cpp` left in a
probed/scaled state, all six originals `git mv`'d to `src/W2jet/deprecated/`. Approval is a
human action and was not recorded here.

## Group 2: BDK (part 1) — one-loop amplitude helper translation

Ready leaves (from `python3 dev/workflow.py status`): 236

First five lines of `python3 dev/workflow.py next mcfm-translate`:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/w2jetsq.f  (fanin=2, bench=u d~ ve e+ g g)
- gghgg_dep/gghgg_dep_params.f  (fanin=2, bench=g g h g g)
```

The list's top entry, `Mods/types_mod.f`, is a known-untranslatable Mods unit and is skipped
(see prior session notes); `BDK/fvs.f` is the first translatable candidate, so it anchors this
group, filled out with the rest of the ready `BDK` files per the folder-coherence rule.

- [x] software/mcfm/src/BDK/fvs.f — TRANSLATED (build passes; probe NOT COVERED under both BDK processes)
- [x] software/mcfm/src/BDK/FFMPcc.f — VERIFIED (worst Δrel ≤ 1e-13; COVERED under `u d~ ve e+ g g`)
- [x] software/mcfm/src/BDK/FFPMccT.f — VERIFIED (worst Δrel ≤ 1e-13; COVERED under `u d~ ve e+ g g`)
- [x] software/mcfm/src/BDK/FFPMccTtilde.f — VERIFIED (worst Δrel ≤ 1e-13; COVERED under `u d~ ve e+ g g`)
- [x] software/mcfm/src/BDK/FFPMscT.f — VERIFIED (worst Δrel ≤ 1e-13; COVERED under `u d~ ve e+ g g`)

### Session note — 2026-08-28 (serial integrate for Group 2)

**Wiring.** All five units wired in `software/mcfm/src/BDK/CMakeLists.txt`: each `<base>.f`
entry replaced by `<base>.cpp` + `<base>_fi.F90`. Care was needed on the name prefixes — the
folder also contains the *untranslated* `FFPMcc.f`, `FFPMscTtilde.f` and `FPFMccT*.f`, none of
which were touched. One shared change was needed once, here:

1. `software/mcfm/CMakeLists.txt` — added `src/BDK` to the three `target_include_directories`
   lists (`objlib`, `libmcfm`, `test`), alongside the `src/W2jet` entry Group 1 added. All five
   new `.cpp` files include their own header with angle brackets (`#include <fvs.hpp>` etc.),
   so without this the build does not resolve them.

**Shim extension reconciled.** `FFPMscT_fi.f90` arrived lowercase; renamed to `FFPMscT_fi.F90`
so all five match the Spec's *Output shape* and the Group 1 precedent. The wider tree/Spec
`.f90`-vs-`.F90` inconsistency flagged in the Group 1 note still stands for a human.

**Coverage probe fixed.** `FFMPcc.cpp` carried its `// @coverage-probe` on a *continuation*
line (`+ FFMPcc_unsym(...);  // @coverage-probe`) with no `=` on it. `coverage_check.py` scales
the marked line with the regex `(=\s*)(.*);(\s*//.*@coverage-probe.*)$`, so that placement makes
the tool `die("could not scale the marked line")` rather than probe. Joined the assignment onto
one line; the statement is unchanged. The other four probes already matched the regex (checked
all five against the tool's own regex before running the oracle).

**Correctness bar.** `jobrunner submit tests/mcfm` — full clean rebuild + `Bin/bench`:
**272/272 PASSED**, benchmark tolerance `1e-13`, zero `FAILED`, and 272 explicit `PASSED` lines
matching the 272/272 summary, so no silent/no-output case (Spec silent trap #9). Re-run after
all probing on the restored tree: still **272/272**, no scaled residue left in any `.cpp`.
`bench` reports pass/fail against the 1e-13 tolerance rather than a per-case Δrel, so the
VERIFIED evidence above is "all cases PASSED at tolerance 1e-13", i.e. worst Δrel ≤ 1e-13.

**`dev/workflow.py verify` still cannot fire the probe (unchanged since Group 1).** Ran the
Spec's command verbatim first: `python3 dev/workflow.py verify software/mcfm/src/BDK/fvs.cpp
-- u d~ ve e+ g g` → NOT COVERED. `dev/tools/coverage/coverage_check.py::run_test` still calls
`subprocess.run` on `Bin/test` with no `cwd=`, and `dev/workflow.py::run` forces `cwd=ROOT`, so
the binary runs from the repo root, cannot find `process.DAT` / `params.lh`, and prints the
same `Process not available in MCFM.` for baseline and probed builds — making **every** probe
report NOT COVERED. Confirmed again with a positive control: the *same* `coverage_check.py`
invoked from `$MCFM_HOME/Bin` (the cwd `tests/mcfm/test.sh` uses) reported **COVERED** for
`W2jet/a6treeg.cpp`, the file Group 1 already established as covered. All five verdicts above
therefore come from `coverage_check.py` run from `$MCFM_HOME/Bin`; the dev tool itself was
**not** edited, since it is shared tooling outside this transformation's product. This is the
second group to need the workaround — a human should decide whether to land `cwd=bin` in
`run_test` so the Spec's own command works as written.

**Why `fvs` is not covered.** Probed under both BDK processes (`u d~ ve e+ g g` and
`u u~ e- e+ g g`) — NOT COVERED in both. Its only callers are `W2jet/xzqqgg_v.f` and
`W2jet/Tri3masscoeff.f`, both still Fortran and both reached only by benchmark variants that
`test -b` does not drive for either mapped process — the same situation as Group 1's `atree`
and `fvf`. Re-probe once a caller is rewritten. The other four were COVERED on the first
mapped process, so no second process was needed.

**Unprobed-unit risk note for the reviewer.** `fvs` is the one unit in this group whose numbers
the oracle never exercised, so its `TRANSLATED` status rests on the build alone. Two author
judgement calls in it are worth a human read: (a) `Fvs_result` is declared as a bare
`std::complex<double>` (value-initialised to 0) where Fortran left `Fvs` undefined if neither
`st` branch fires — a deliberate, output-neutral deviation for real call sites, which always
pass one of the two defined `st` values; (b) `Brackpm` and `Brackpma` are plain external-linkage
top-level C++ functions with no header entry (the internal-helper convention from
`Need/i3m.cpp`), so their fairly generic names now sit in the global namespace — harmless today
(links clean), but a future translated unit defining either name would collide.

**Tree state.** Clean and building: `jobrunner submit tests/mcfm` green at 272/272, no `.cpp`
left in a probed/scaled state, all five originals `git mv`'d to `src/BDK/deprecated/`, and all
new files staged in the `software/mcfm` submodule. Approval is a human action and was not
recorded here.

## Group 3: W2jet (part 2) — loop coefficient and squared-matrix-element helper translation

Ready leaves (from `python3 dev/workflow.py status`): 232

First five lines of `python3 dev/workflow.py next mcfm-translate`:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/w2jetsq.f  (fanin=2, bench=u d~ ve e+ g g)
- gghgg_dep/gghgg_dep_params.f  (fanin=2, bench=g g h g g)
- BDK/FFPMscTtilde.f  (fanin=1, bench=)
```

The list's top entry, `Mods/types_mod.f`, is a known-untranslatable Mods unit and is skipped
(see prior session notes); `W2jet/w2jetsq.f` is the first translatable candidate, so it anchors
this group, filled out with the rest of the ready `W2jet` files per the folder-coherence rule.

- [x] software/mcfm/src/W2jet/w2jetsq.f — TRANSLATED (build passes; probe NOT COVERED under both W2jet processes)
- [x] software/mcfm/src/W2jet/Acalc.f — VERIFIED (worst Δrel ≤ 1e-13; COVERED under `u u~ e- e+ g g`)
- [x] software/mcfm/src/W2jet/Ftexact.f — VERIFIED (worst Δrel ≤ 1e-13; COVERED under `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/LRcalc.f — VERIFIED (worst Δrel ≤ 1e-13; COVERED under `u u~ e- e+ g g`)
- [x] software/mcfm/src/W2jet/Ltfunctions.f — VERIFIED (worst Δrel ≤ 1e-13; COVERED under `u u~ e- e+ g g`)

### Group 3 integration notes (2026-08-28)

**Build wiring.** `src/W2jet/CMakeLists.txt` swapped all five `.f` entries for their
`.cpp` + `_fi.F90` pairs (`Acalc`, `Ftexact`, `Ltfunctions`, `LRcalc`, `w2jetsq`). No shared
build change was needed this round: the top-level `CMakeLists.txt` already carries `src/W2jet`
and `src/BDK` on the three `target_include_directories` lines (added in Group 2), which is what
lets the new `#include <…​.hpp>` angle-bracket includes resolve. The `src/Inc/FArray.hpp`
`FArray4D` fix and the top-level `CMakeLists.txt` edit already in the tree are Group 1/2 work
and were left as-is.

**`subqcd.hpp` added (invariant `I` fix).** `w2jetsq.cpp` arrived calling its sibling
`subqcd.cpp` through a local forward declaration, because Group 1 deliberately gave `subqcd` no
header (nothing called it from C++ then). The Contract's invariant `I` says cross-unit calls go
through headers, not translation-era forward declarations, and the Spec's Header/source rule 5
says to add the header *before* the function is used from another `.cpp` — so `w2jetsq` calling
it is exactly the trigger. Added `src/W2jet/subqcd.hpp`, made `subqcd.cpp` include its own
header, and replaced the forward declaration in `w2jetsq.cpp` with `#include <subqcd.hpp>`.
Signature unchanged; `subqcd`'s own VERIFIED status from Group 1 is unaffected (still COVERED,
still 272/272).

**Two coverage probes were unscalable as authored.** `Acalc.cpp` and `LRcalc.cpp` both carried
`// @coverage-probe` on the *closing continuation line* of a multi-line assignment (`); //…` and
`)/s34/s56/s12; //…`), with no `=` on the marked line. `coverage_check.py` scales with the
line-anchored regex `(=\s*)(.*);(\s*//.*@coverage-probe.*)$`, so both would have hit
`die("could not scale the marked line")` — the same trap `FFMPcc.cpp` hit in Group 2. Joined
each assignment onto one line; the expressions are byte-identical otherwise. Checked all five
markers against the tool's own regex before running the oracle; all five now scale.

**Correctness bar.** `jobrunner submit tests/mcfm` — full clean rebuild + `Bin/bench`:
**272/272 PASSED**, benchmark tolerance `1.00000000000000003e-13`, zero `FAILED`, and 272
explicit `PASSED` lines matching the 272/272 summary, so no silent/no-output case (Spec silent
trap #9). Re-run after all probing on the restored tree: still **272/272**, and no `* 1.5;`
residue anywhere under `software/mcfm/src/`. `bench` reports pass/fail against the tolerance
rather than a per-case Δrel, so the VERIFIED evidence above is "all cases PASSED at tolerance
1e-13", i.e. worst Δrel ≤ 1e-13.

**`dev/workflow.py verify` still cannot fire the probe (third group running).** Ran the Spec's
command verbatim first: `python3 dev/workflow.py verify software/mcfm/src/W2jet/w2jetsq.cpp --
u d~ ve e+ g g` → NOT COVERED. `dev/tools/coverage/coverage_check.py::run_test` still calls
`subprocess.run` on `Bin/test` with no `cwd=`, and `dev/workflow.py::run` forces `cwd=ROOT`, so
the binary runs from the repo root, cannot find `process.DAT` / `params.lh`, and prints the same
`Process not available in MCFM.` for baseline and probed builds — making **every** probe report
NOT COVERED. Confirmed again with a positive control: the same `coverage_check.py` invoked from
`$MCFM_HOME/Bin` reported **COVERED** for `W2jet/a6treeg.cpp`, the file Group 1 established as
covered. All five verdicts above therefore come from `coverage_check.py` run from
`$MCFM_HOME/Bin`; the dev tool itself was **not** edited, since it is shared tooling outside
this transformation's product. This is now the third group needing the workaround — a human
should decide whether to land `cwd=bin` in `run_test` so the Spec's own command works as
written.

**Why `w2jetsq` is not covered.** Probed under both W2jet processes (`u d~ ve e+ g g` and
`u u~ e- e+ g g`) — NOT COVERED in both, same as Group 1's `atree` and `fvf`. Its only two
callers, `W2jet/qqb_w2jet.f` and `W2jet/qqb_wp2jetx_new.f`, are still Fortran and are reached
only by benchmark variants `test -b` does not drive for either mapped process. Re-probe once a
caller is rewritten. `Ltfunctions` needed the second process: NOT COVERED under
`u d~ ve e+ g g`, COVERED under `u u~ e- e+ g g`. `Acalc`, `Ftexact` and `LRcalc` were COVERED
on their first mapped process.

**Unprobed-unit risk note for the reviewer.** `w2jetsq` is the one unit here the oracle never
exercised numerically, so its `TRANSLATED` status rests on the build alone. One author judgement
call is worth a human read: it declares `qcd1`/`qcd2`/`qed` as `FArray2D<complex<double>>`
`(3, 3, -1, -1)` to mirror Fortran's `(-1:1,-1:1)`, and only the four corner elements
`(±1, ±1)` are ever written or read — the `0` row/column stays uninitialised, exactly as in the
Fortran, so this is faithful but relies on no future edit reading the middle band.

**Tree state.** Clean and building: `jobrunner submit tests/mcfm` green at 272/272, no `.cpp`
left in a probed/scaled state, all five originals now under `src/W2jet/deprecated/`
(`Acalc.f` and `LRcalc.f` were plain deletions rather than `git mv` renames — staged here so the
submodule records them the same way as the other three). Approval is a human action and was not
recorded here; this is the third completed group, so the gate will require it before Group 4.
