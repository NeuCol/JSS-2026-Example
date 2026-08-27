# Agent worklist — mcfm-translate

Statuses follow `desired_spec.md` (`VERIFIED` / `TRANSLATED` / `FAILED`).
Coverage process for `src/W2jet` is `u d~ ve e+ g g` (and `u u~ e- e+ g g`).

## Group W2jet tree/loop helpers

- [x] software/mcfm/src/W2jet/subqcd.cpp — VERIFIED (worst Δrel <= 1e-13)
- [x] software/mcfm/src/W2jet/a6treeg.cpp — VERIFIED (worst Δrel <= 1e-13)
- [x] software/mcfm/src/W2jet/atree.cpp — TRANSLATED (NOT COVERED under u d~ ve e+ g g and u u~ e- e+ g g)
- [x] software/mcfm/src/W2jet/fpp.cpp — TRANSLATED (NOT COVERED under u d~ ve e+ g g and u u~ e- e+ g g)
- [x] software/mcfm/src/W2jet/fvf.cpp — TRANSLATED (NOT COVERED under u d~ ve e+ g g and u u~ e- e+ g g)

Evidence for the two `VERIFIED` files: `jobrunner submit tests/mcfm`, run after the
`// @coverage-probe` instrumentation was removed from `subqcd.cpp`, i.e. on the restored
build. `tests/mcfm/job.output` line 657 records `Benchmark with tolerance:
1.00000000000000003e-13` and line 943 records `SUMMARY: pass rate 272/272`, with every
individual case printing `PASSED`. The benchmark runner prints no per-case ratio, so the
worst observed Δrel is bounded by the benchmark tolerance: worst Δrel <= 1e-13.
Coverage for `subqcd.cpp` and `a6treeg.cpp` came back `COVERED` from the probe run; the
other three files came back `NOT COVERED` under both W2jet processes and are therefore
recorded `TRANSLATED` per the Spec.

## Group W2jet amplitude/loop coefficients

- [x] software/mcfm/src/W2jet/Ltfunctions.cpp — VERIFIED (worst Δrel <= 1e-13)
- [x] software/mcfm/src/W2jet/LRcalc.cpp — VERIFIED (worst Δrel <= 1e-13)
- [x] software/mcfm/src/W2jet/atrLLL.cpp — TRANSLATED (NOT COVERED under u d~ ve e+ g g and u u~ e- e+ g g)
- [x] software/mcfm/src/W2jet/atrLRL.cpp — TRANSLATED (NOT COVERED under u d~ ve e+ g g and u u~ e- e+ g g)
- [x] software/mcfm/src/W2jet/faxsl.cpp — TRANSLATED (NOT COVERED under u d~ ve e+ g g and u u~ e- e+ g g)

Coverage evidence (`python3 dev/tmp/run_verify.py <file.cpp> -- <process>`):

- `Ltfunctions.cpp`: `NOT COVERED` under `u d~ ve e+ g g`, `COVERED` under `u u~ e- e+ g g`.
- `LRcalc.cpp`: `NOT COVERED` under `u d~ ve e+ g g`, `COVERED` under `u u~ e- e+ g g`.
- `atrLLL.cpp`, `atrLRL.cpp`, `faxsl.cpp`: `NOT COVERED` under both W2jet processes, so they are
  recorded `TRANSLATED` per the Spec.

Benchmark evidence for the two `VERIFIED` files: every `// @coverage-probe` marker was removed
from all ten translated W2jet `.cpp` files (`python3 dev/tmp/strip_probes.py`), the project was
rebuilt (`python3 dev/tmp/build_only.py`, `build rc = 0`), and `jobrunner submit tests/mcfm` was
run on that restored, probe-free build. `tests/mcfm/job.output` line 662 records `Benchmark with
tolerance: 1.00000000000000003e-13` and line 948 records `SUMMARY: pass rate 272/272`, with 272
`PASSED` lines and zero `FAILED` lines in the file. The benchmark runner prints no per-case
ratio, so the worst observed Δrel is bounded by the benchmark tolerance: worst Δrel <= 1e-13.

The original Fortran sources for all ten translated files now live in
`software/mcfm/src/W2jet/deprecated/`.

## Notes / session log

- Loop 4 — logging fix and group closure.
  - `agent_log.md` did not exist at the start of this loop even though five W2jet files had
    already been translated, built and probed in loops 1–3. This loop created it and recorded
    the group above; no code changes were required to close the group.
  - **Verification invocation.** `python3 dev/workflow.py verify <file.cpp> -- <process>` exits
    2 in this sandbox because `MCFM_HOME` is unset (the shell cannot `source environment.sh`
    or set inline env vars). The working invocation is
    `python3 dev/tmp/run_verify.py <file.cpp> -- <process>`, which sets `MCFM_HOME` to
    `software/mcfm` and runs `dev/tools/coverage/coverage_check.py` with
    `cwd=software/mcfm/Bin`. The `cwd` matters: the MCFM `test` binary only finds its input
    files when started from `Bin`; started from the project root it fails identically for the
    baseline and the probed build, which made *every* file report a false `NOT COVERED`.
    Do not re-diagnose this — use `dev/tmp/run_verify.py`.
  - Reminder for future loops: remove every `// @coverage-probe` statement and rebuild before
    quoting benchmark numbers, so the quoted run is the restored build.
- Loop 5 — second W2jet group closed.
  - Ran the coverage oracle for the five files of the new group under both W2jet processes.
    `Ltfunctions.cpp` and `LRcalc.cpp` came back `COVERED` under `u u~ e- e+ g g` (both are
    `NOT COVERED` under `u d~ ve e+ g g`); `atrLLL.cpp`, `atrLRL.cpp` and `faxsl.cpp` are
    `NOT COVERED` under both processes.
  - Stripped every `// @coverage-probe` marker from all ten translated W2jet `.cpp` files with
    the new helper `dev/tmp/strip_probes.py`, rebuilt (`build rc = 0`) and re-ran
    `jobrunner submit tests/mcfm` on that restored build: `SUMMARY: pass rate 272/272`,
    272 `PASSED`, no `FAILED`, tolerance 1e-13.
  - No code changes were needed; the group is recorded above and the gate/readiness map were
    re-checked afterwards.
  - Tip: `u u~ e- e+ g g` is worth trying for W2jet files that look `NOT COVERED` under the W
    process — the Z process reaches the LL/LR loop-coefficient routines.
