# mcfm-translate worklist

## Session notes

- Loop 4: closed out **Group W2jet batch 1**. All five files were re-verified with
  `python3 dev/workflow.py verify software/mcfm/src/W2jet/<name>.cpp -- u d~ ve e+ g g`;
  every run printed `RESULT: NOT COVERED` (inner exit code 1), so all five are TRANSLATED,
  not VERIFIED. Full suite re-run afterwards: `jobrunner submit tests/mcfm` → SUCCESS,
  `SUMMARY: pass rate 272/272`, 0 `FAILED`, 272 explicit `PASSED` lines.
- **Root cause of `verify` exiting 2 when invoked directly**: `dev/workflow.py verify` just
  forwards to `dev/tools/coverage/coverage_check.py`, which starts with
  `mcfm = os.environ.get("MCFM_HOME") or die("set MCFM_HOME first (source environment.sh)")`
  and `die()` calls `sys.exit(2)`. Exit 2 is documented in that tool as "usage/setup error";
  it is not a translation failure. The workflow wrapper never sets `MCFM_HOME` itself.
  Required invocation from the project root (the sandboxed shell cannot `source`
  `environment.sh` or use `VAR=... cmd`, hence the tiny wrapper):
  `python3 dev/tmp/run_verify.py software/mcfm/src/<dir>/<file>.cpp -- <process>`
  which sets `MCFM_HOME=<root>/software/mcfm`, `PROJECT_HOME=<root>`, and now propagates the
  child's exit code via `sys.exit(res.returncode)` (0 = COVERED, 1 = NOT COVERED, 2 = setup error).
- Gate after recording the group: `python3 dev/workflow.py gate mcfm-translate` →
  `GATE: OK — completed groups do not yet require approval (2 waiting, limit 3)`.
  Roadmap refreshed afterwards: 435 untranslated rows, 228 ready leaves; the top candidate is
  `W2jet/ggZZcapture.f`, which is the natural first file of the next group (W2jet batch 2,
  filled with `a6routine`, `w2jetsq`, `Acalc`, `Ftexact`). Dependency check done for that group:
  every needed module already has a `.hpp` (`constants_mod`, `ZZclabels_mod`, `ZZdlabels_mod`,
  `first_mod`, `ggZZ_mod` [`res(2,4,10,3)`], `ggZZintegrals_mod`, `mxpart_mod`, `sprods_com_mod`,
  `lc_mod`, `mmsq_cs_mod` [`FArray3D<double>(3,2,2, 0,1,1)`], `nf_mod`, `scale_mod`, `masses_mod`,
  `epinv_mod`, `toploops_mod`), `subqcd` is already C++ in `W2jet.hpp`, `loopI2`/`loopI3` are
  already C++ in `src/loop/Loop.hpp`, and `Lnrat`/`A6texact` are still Fortran so they must be
  called through `extern "C"` with pointer arguments. That group was **not** opened this round
  (no heading created, no sources touched) to avoid leaving a half-translated group behind.

## Group W2jet batch 2 (ggZZcapture, a6routine, w2jetsq, Acalc, Ftexact, A6texact)

Provenance (recorded before editing in this round):

- `python3 dev/workflow.py status` → `roadmap metrics: 435 untranslated file rows, 228 ready leaves`
- First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/a6routine.f  (fanin=2, bench=u d~ ve e+ g g)
- W2jet/w2jetsq.f  (fanin=2, bench=u d~ ve e+ g g)
```

The group's first file is the list's top entry (`W2jet/ggZZcapture.f`); the rest of the group is
filled from that file's own folder (`src/W2jet`), taking the next W2jet entries of the same ranked
list (`a6routine`, `w2jetsq`, `Acalc`, `Ftexact`). `BDK/fvs.f` (rank 2) is skipped because it is in
a different folder. `W2jet/A6texact.f` is added as a sixth file: it is ready in the same folder
(`grep -P "\tW2jet\t0\t0\t" dev/tmp/assets/roadmap_metrics.tsv` lists it) and `a6routine` calls it,
so translating it in the same group keeps that call an ordinary C++ header call instead of a new
Fortran `extern "C"` boundary.

### Files

(in progress)

## Group W2jet batch 1 (atree, a6treeg, fvf, subqcd, ZZbox1LL)

Provenance (recorded before editing in this round):

- `python3 dev/workflow.py status` → `roadmap metrics: 440 untranslated file rows, 225 ready leaves`
- First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/ZZbox1LL.f  (fanin=2, bench=u d~ ve e+ g g)
```

The group's first file is the list's top entry (`W2jet/atree.f`); the rest of the group is
filled from that file's own folder (`src/W2jet`): `ZZbox1LL`, `a6treeg`, `fvf`, `subqcd` — the
next W2jet entries in the same ranked list. `W2jet/ggZZcapture.f` (rank 2) is held back so the
group stays at about five files; it is the natural first file of the next W2jet group.

### Files

- [x] software/mcfm/src/W2jet/atree.cpp — TRANSLATED (`verify ... -- u d~ ve e+ g g` → `RESULT: NOT COVERED`, inner exit 1; build passes, original moved to `W2jet/deprecated/atree.f`)
- [x] software/mcfm/src/W2jet/a6treeg.cpp — TRANSLATED (`verify ... -- u d~ ve e+ g g` → `RESULT: NOT COVERED`, inner exit 1; build passes, original moved to `W2jet/deprecated/a6treeg.f`)
- [x] software/mcfm/src/W2jet/fvf.cpp — TRANSLATED (`verify ... -- u d~ ve e+ g g` → `RESULT: NOT COVERED`, inner exit 1; build passes, original moved to `W2jet/deprecated/fvf.f`)
- [x] software/mcfm/src/W2jet/subqcd.cpp — TRANSLATED (`verify ... -- u d~ ve e+ g g` → `RESULT: NOT COVERED`, inner exit 1; build passes, original moved to `W2jet/deprecated/subqcd.f`)
- [x] software/mcfm/src/W2jet/ZZbox1LL.cpp — TRANSLATED (`verify ... -- u d~ ve e+ g g` → `RESULT: NOT COVERED`, inner exit 1; build passes, original moved to `W2jet/deprecated/ZZbox1LL.f`)

No file in this group reached VERIFIED: the `u d~ ve e+ g g` bench process does not execute any of
these five routines (all five probes left the numbers unchanged), so per the Plan's Verify section
(`NOT COVERED` → mark `TRANSLATED`) they are all TRANSLATED. Re-check after a caller
(e.g. `W2jet/qqb_w2jet.f`, `W2jet/ggZZcapture.f`) is rewritten.

Evidence: `jobrunner submit tests/mcfm` → SUCCESS, `SUMMARY: pass rate 272/272`,
`grep -c FAILED tests/mcfm/job.output` → 0, `grep -c PASSED tests/mcfm/job.output` → 272
(each of the 272 cases prints an explicit `PASSED`, so this is not a silent segfault).
CMake in `src/W2jet/CMakeLists.txt` lists the five `.cpp` + `_fi.F90` pairs; all five originals
now live in `software/mcfm/src/W2jet/deprecated/`.

## Group Mods batch 1 (types_mod, mod_qcdloop_c, pp_mod, ppwp2j_mod)

Provenance (recorded before editing in this round):

- `python3 dev/workflow.py status` → `roadmap metrics: 445 untranslated file rows, 229 ready leaves`
- First five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
```

The group's first file is the list's top entry (`Mods/types_mod.f`); the rest of the group is
filled from that file's own folder (`src/Mods`): `mod_qcdloop_c`, `pp_mod`, `ppwp2j_mod`.

### Files

- [x] software/mcfm/src/Mods/types_mod.f90 — TRANSLATED (kind/parameter module: `types_mod.hpp` + Fortran mirror; Mods is infrastructure, no runtime statement to probe; original moved to `Mods/deprecated/types_mod.f`)
- [x] software/mcfm/src/Mods/mod_qcdloop_c.f90 — TRANSLATED (C-binding interface module: `mod_qcdloop_c.hpp` + Fortran mirror; infrastructure, not coverage-probeable; original moved to `Mods/deprecated/mod_qcdloop_c.f`)
- [x] software/mcfm/src/Mods/pp_mod.cpp — TRANSLATED (data-only module: `FArray4D<int> pp(-4:4,...)` table + `extern "C"` accessor; `verify` refuses it — "no '// @coverage-probe' marker ... mark the statement that writes the main output" — there is no executable statement, and the Spec maps Mods to infrastructure → TRANSLATED)
- [x] software/mcfm/src/Mods/ppwp2j_mod.cpp — TRANSLATED (same shape as pp_mod: static table + accessor; infrastructure, nothing to probe)

Evidence: `jobrunner submit tests/mcfm` → SUCCESS, `SUMMARY: pass rate 272/272`, `grep -c FAILED tests/mcfm/job.output` → 0.
CMake in `src/Mods/CMakeLists.txt` lists `types_mod.f90`, `mod_qcdloop_c.f90`, `pp_mod.f90`/`pp_mod.cpp`, `ppwp2j_mod.f90`/`ppwp2j_mod.cpp`; all four originals now live in `src/Mods/deprecated/`.
