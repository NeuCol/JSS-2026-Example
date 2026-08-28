# MCFM Translate Agent Log

## Group 1: W2jet — Fortran → C++ translation

Provenance (recorded before any editing):

- Ready leaves at group open: 229 (`python3 dev/workflow.py status`: `roadmap metrics: 445 untranslated file rows, 229 ready leaves`)
- First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
```

Deviation from the printed top entries: `Mods/types_mod.f` ranks first but is a known
untranslatable Mods unit and is skipped, so the first usable candidate is `W2jet/atree.f`; per
Resolution step 2 the rest of the group is filled from that file's own `W2jet/` folder in rank
order, which is why `BDK/fvs.f` is not included.

- [x] software/mcfm/src/W2jet/atree.f — TRANSLATED (NOT COVERED under u d~ ve e+ g g; also NOT COVERED under u u~ e- e+ g g — callers a6.f / a6routine.f never reach it in either bench process)
- [x] software/mcfm/src/W2jet/ggZZcapture.f — TRANSLATED (NOT COVERED under u d~ ve e+ g g; every call site is guarded by `docheck`, which is false in the test path)
- [x] software/mcfm/src/W2jet/ZZbox1LL.f — VERIFIED (worst Δrel 0 — COVERED under u u~ e- e+ g g; all four benchmark ratios print exactly 1 at tolerance 1e-13)
- [x] software/mcfm/src/W2jet/a6treeg.f — VERIFIED (worst Δrel 0 — COVERED under u d~ ve e+ g g; all four benchmark ratios print exactly 1 at tolerance 1e-13)
- [x] software/mcfm/src/W2jet/fvf.f — TRANSLATED (NOT COVERED under u d~ ve e+ g g or u u~ e- e+ g g — Fvf is entered 96x under the Z process but its return value does not move the benchmark numbers)

### Session note — 2026-08-28 (integrate)

- Wired all five units into `software/mcfm/src/W2jet/CMakeLists.txt`: each `<base>.f` entry
  replaced by `<base>.cpp` + `<base>_fi.F90`. No other build file changed — `src/W2jet` was
  **not** added to `target_include_directories` in `software/mcfm/CMakeLists.txt` because every
  unit includes only its own header, quoted; no cross-W2jet header include exists yet. A future
  translated W2jet caller wanting `<atree.hpp>`/`<ZZbox1LL.hpp>` etc. will need that entry added.
- Oracle run: `jobrunner submit tests/mcfm` → **272/272, every case explicitly PASSED, zero
  FAILED** (checked for `passed` markers, not just absence of `FAILED`). Re-run after the final
  restore; the tree builds clean.
- Coverage probes run with `python3 dev/workflow.py verify <file>.cpp -- <process>` using the
  Spec's coverage map for W2jet, which lists both `u d~ ve e+ g g` and `u u~ e- e+ g g`.
- `fvf.cpp`: the `// @coverage-probe` marker was on the `hqpqbmgpgp` branch only, so it could
  never probe the other branch. Moved to the common return path in `fvf_wrapper`
  (comment-only relocation, no semantic change). Still NOT COVERED — confirmed independently.
- **Tool fix, needs a human's eye:** `dev/tools/coverage/coverage_check.py::run_test` invoked
  `Bin/test` with no `cwd=`, and `dev/workflow.py::run` forces `cwd=ROOT`, so the test binary
  ran from the repo root, could not find `process.DAT` / `params.lh`, and printed
  "Process not available in MCFM." identically for the baseline and probed builds — making
  **every** probe report NOT COVERED. Added `cwd=bin` (matching `tests/mcfm/test.sh`, which does
  `cd "$MCFM_HOME/Bin"`). Without this fix a6treeg and ZZbox1LL would have been mis-recorded as
  TRANSLATED. This is the long-standing bug noted as `coverage-check-missing-cwd`; it is a
  shared dev tool outside this transformation's product, so a human should confirm the change.
- Not-covered results were cross-checked against a non-mutating `gdb` breakpoint trace on the
  five `*_wrapper` symbols: `u d~ ve e+ g g` reaches only `a6treeg_wrapper` (144 hits);
  `u u~ e- e+ g g` reaches `a6treeg_wrapper` (576), `fvf_wrapper` (96), `ZZbox1LL_wrapper` (12);
  `atree_wrapper` and `ggZZcapture_wrapper` are reached by neither.
- Author-flagged item left as-is (deliberate): the shims are `_fi.F90` per the Spec's Output
  shape, while every pre-existing shim in the repo is lowercase `_fi.f90`. Both compile and both
  build here. A human may want to pick one convention.
- Approval not recorded by this step. `approvals.toml` / `approve_group.py` remain human-only.

## Group 2: BDK — Fortran → C++ translation

Provenance (recorded before any editing):

- Ready leaves at group open: 235 (`python3 dev/workflow.py status`: `roadmap metrics: 440 untranslated file rows, 235 ready leaves`)
- Gate at group open: `python3 dev/workflow.py gate mcfm-translate` → `GATE: OK — completed groups do not yet require approval (1 waiting, limit 3).`
- First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/subqcd.f  (fanin=2, bench=u d~ ve e+ g g)
- gghgg_dep/gghgg_dep_params.f  (fanin=2, bench=g g h g g)
```

Deviation from the printed top entries: `Mods/types_mod.f` ranks first but is a known
untranslatable Mods unit and is skipped, so the first usable candidate is `BDK/fvs.f`; per
Resolution step 2 the rest of the group is filled from that file's own `BDK/` folder in rank
order, which is why `W2jet/subqcd.f` and `gghgg_dep/gghgg_dep_params.f` are not included.

- [x] software/mcfm/src/BDK/fvs.f — TRANSLATED (build pass, not covered: NOT COVERED under both BDK bench processes `u d~ ve e+ g g` and `u u~ e- e+ g g`)
- [x] software/mcfm/src/BDK/FFMPcc.f — TRANSLATED (build pass, not covered: NOT COVERED under both `u d~ ve e+ g g` and `u u~ e- e+ g g`)
- [x] software/mcfm/src/BDK/FFPMccT.f — TRANSLATED (build pass, not covered: NOT COVERED under both `u d~ ve e+ g g` and `u u~ e- e+ g g`)
- [x] software/mcfm/src/BDK/FFPMccTtilde.f — TRANSLATED (build pass, not covered: NOT COVERED under both `u d~ ve e+ g g` and `u u~ e- e+ g g`)
- [x] software/mcfm/src/BDK/FFPMscT.f — TRANSLATED (build pass, not covered: NOT COVERED under both `u d~ ve e+ g g` and `u u~ e- e+ g g`)

### Session note — 2026-08-28 (integrate)

- Wired all five units into `software/mcfm/src/BDK/CMakeLists.txt`: each `<base>.f` entry
  replaced by `<base>.cpp` + `<base>_fi.F90`. No other build file changed. `src/BDK` was **not**
  added to `target_include_directories` in `software/mcfm/CMakeLists.txt`: every unit includes
  only its own header, quoted, and the cross-folder callee headers they do use
  (`W1jet.hpp`, `Need.hpp`, `sprods_com_mod.hpp`, `mxpart_mod.hpp`, `heldefs_mod.hpp`,
  `FArray.hpp`) are already on the objlib include path. A future translated BDK caller wanting
  `<FFPMccT.hpp>` etc. by angle include will need that entry added.
- Oracle run: `jobrunner submit tests/mcfm` → **272/272, every case explicitly PASSED, zero
  FAILED** (counted `PASSED` markers, not just absence of `FAILED`, per the Spec's silent-segfault
  trap). Re-run after the final coverage restore: still 272/272 PASSED; the tree builds clean.
- Coverage probes run with `python3 dev/workflow.py verify <file>.cpp -- <process>` for **both**
  processes the Spec's coverage map lists for BDK. All five report NOT COVERED under both, so all
  five are `TRANSLATED`, not `VERIFIED`. These BDK one-loop bits are reached only through
  `FFPMcc.f` / `FFPMsc.f` / `fcc.f` / `xzqqgg_v.f` paths that the two bench processes do not enter.
- `FFMPcc.cpp`: the `// @coverage-probe` marker sat on the last continuation line of a multi-line
  `FFMPcc_res = A + B;` statement inside `FFMPcc`, which `coverage_check.py`'s single-line
  `lhs = rhs;  // @coverage-probe` regex could not scale (it died with "could not scale the marked
  line"). Moved the marker to a new single-line result statement in `FFMPcc_wrapper`, matching the
  other four units and the W2jet precedent. Comment/formatting-only relocation, no semantic change;
  the probe then ran and independently reported NOT COVERED.
- The `dev/tools/coverage/coverage_check.py` `cwd=bin` fix from Group 1 is still an uncommitted
  working-tree change and is still required — without it every probe here would have reported
  NOT COVERED for the wrong reason. **Still needs a human's eye**, as flagged in Group 1: it is a
  shared dev tool outside this transformation's product.
- Author-flagged item left as-is (deliberate, same as Group 1): the shims are `_fi.F90` per the
  Spec's Output shape, while pre-existing repo shims are lowercase `_fi.f90`. Both build. A human
  should still pick one convention.
- The known embedded "LLM INSTRUCTIONS" prompt-injection block in `mxpart_mod.hpp` was present and
  ignored.
- Approval not recorded by this step. `approvals.toml` / `approve_group.py` remain human-only.

## Group 3: W2jet — Fortran → C++ translation

Provenance (recorded before any editing):

- Ready leaves at group open: 231 (`python3 dev/workflow.py status`: `roadmap metrics: 435 untranslated file rows, 231 ready leaves`)
- Gate at group open: `python3 dev/workflow.py gate mcfm-translate` → `GATE: OK — completed groups do not yet require approval (2 waiting, limit 3).`
- First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/subqcd.f  (fanin=2, bench=u d~ ve e+ g g)
- gghgg_dep/gghgg_dep_params.f  (fanin=2, bench=g g h g g)
- BDK/FFPMscTtilde.f  (fanin=1, bench=)
```

Deviation from the printed top entries: `Mods/types_mod.f` ranks first but is a known
untranslatable Mods unit and is skipped, so the first usable candidate is `W2jet/subqcd.f`; per
Resolution step 2 the rest of the group is filled from that file's own `W2jet/` folder in rank
order (`grep -P "\tW2jet\t0\t0\t" dev/tmp/assets/roadmap_metrics.tsv`), which is why
`gghgg_dep/gghgg_dep_params.f` and the `BDK/` entries are not included.

- [x] software/mcfm/src/W2jet/subqcd.f — VERIFIED (worst Δrel 0 — COVERED under u d~ ve e+ g g; all four benchmark ratios print exactly 1 at tolerance 1e-13)
- [x] software/mcfm/src/W2jet/Acalc.f — VERIFIED (worst Δrel 0 — COVERED under u u~ e- e+ g g, NOT COVERED under u d~ ve e+ g g; all four benchmark ratios print exactly 1 at tolerance 1e-13)
- [x] software/mcfm/src/W2jet/Ftexact.f — VERIFIED (worst Δrel 0 — COVERED under both u d~ ve e+ g g and u u~ e- e+ g g; all four benchmark ratios print exactly 1 at tolerance 1e-13)
- [x] software/mcfm/src/W2jet/LRcalc.f — VERIFIED (worst Δrel 0 — COVERED under u u~ e- e+ g g, NOT COVERED under u d~ ve e+ g g; all four benchmark ratios print exactly 1 at tolerance 1e-13)
- [x] software/mcfm/src/W2jet/Ltfunctions.f — VERIFIED (worst Δrel 0 — COVERED under u u~ e- e+ g g, NOT COVERED under u d~ ve e+ g g; all four benchmark ratios print exactly 1 at tolerance 1e-13)

### Session note — 2026-08-28 (integrate)

- Wired all five units into `software/mcfm/src/W2jet/CMakeLists.txt`: each `<base>.f` entry
  replaced by `<base>.cpp` + `<base>_fi.F90` (`Acalc`, `Ftexact`, `Ltfunctions`, `LRcalc`,
  `subqcd`). No other build file changed. `src/W2jet` was again **not** added to
  `target_include_directories` in `software/mcfm/CMakeLists.txt`: each `.cpp` includes only its
  own header, quoted, and every angle include it uses (`FArray.hpp`, `constants_mod.hpp`,
  `mxpart_mod.hpp`, `sprods_com_mod.hpp`, `ZZclabels_mod.hpp`, `ZZdlabels_mod.hpp`,
  `ggZZintegrals_mod.hpp`, `scalarselect_mod.hpp`, `loop/Loop.hpp`) already resolves through
  `src/Inc`, `src/Mods`, or `src/loop`.
- Oracle run: `jobrunner submit tests/mcfm` → **272/272, every case explicitly PASSED, zero
  FAILED** (counted `PASSED` markers, not just absence of `FAILED`, per the Spec's
  silent-segfault trap). Re-run after the final coverage restore: still 272/272 PASSED and the
  tree builds clean. No `* 1.5` scaling left in any W2jet `.cpp`.
- Δrel evidence for the five VERIFIED entries: on the restored build,
  `./test -b u d~ ve e+ g g` and `./test -b u u~ e- e+ g g` each print
  `Finite / IR / IR2 / Born ratio = 1` at tolerance 1e-13 → worst Δrel 0.
- **Probe-invocation trap, worth a human's eye.** `python3 dev/workflow.py verify <f>.cpp --
  "u d~ ve e+ g g"` (process quoted as ONE argument) makes `coverage_check.py` pass a single
  argv element to `Bin/test -b`, which never matches a process. Baseline and probed runs then
  produce identical output and **every** probe reports NOT COVERED — no error, no warning. The
  first pass of this round ran that way and mis-read all five units as TRANSLATED. Caught with a
  positive control: `a6treeg.cpp` (recorded COVERED in Group 1) also reported NOT COVERED when
  quoted, and COVERED when the process is passed unquoted as separate words, exactly as
  `dev/workflow.py`'s own usage line shows. All ten probes above were re-run unquoted. Anyone
  probing in future should keep a known-covered control in the batch.
- Group 2 spot-check under the corrected invocation: `software/mcfm/src/BDK/fvs.cpp` still reports
  NOT COVERED under both `u d~ ve e+ g g` and `u u~ e- e+ g g`, so that group's verdicts look
  sound. The other four BDK units were not re-probed here; a human may want them re-checked
  unquoted before approving Group 2.
- The `dev/tools/coverage/coverage_check.py` `cwd=bin` fix from Group 1 is still an uncommitted
  working-tree change and is still required for any probe to mean anything. **Still needs a
  human's eye**, as flagged in Groups 1 and 2.
- Author-flagged item left as-is (deliberate, same as Groups 1 and 2): the shims are `_fi.F90`
  per the Spec's Output shape, while pre-existing repo shims are lowercase `_fi.f90`. Both
  build. A human should still pick one convention.
- `software/mcfm` is a git submodule, so the originals were moved into
  `src/W2jet/deprecated/` with plain `mv` where `git mv` from the superproject failed; all five
  `.f` files are in `deprecated/` and out of the build.
- Approval not recorded by this step. `approvals.toml` / `approve_group.py` remain human-only.
