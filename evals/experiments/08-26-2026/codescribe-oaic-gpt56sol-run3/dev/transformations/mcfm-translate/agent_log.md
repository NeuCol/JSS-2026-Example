# MCFM translation worklist

## Group 1 — Mods foundational types

- [x] software/mcfm/src/Mods/types_mod.f — TRANSLATED (infrastructure module; full build and all 272 tests passed)

## Group 2 — BDK M2 bit functions

- [x] software/mcfm/src/BDK/M2bit1.f — TRANSLATED (build passed; coverage probe with `u d~ ve e+ g g` returned NOT COVERED)
- [x] software/mcfm/src/BDK/M2bit2.f — TRANSLATED (build passed; coverage probe with `u d~ ve e+ g g` returned NOT COVERED)
- [x] software/mcfm/src/BDK/M2bit3.f — TRANSLATED (build passed; coverage probe with `u d~ ve e+ g g` returned NOT COVERED)

## Group 3 — BDK ready leaf functions

- [x] software/mcfm/src/BDK/fvs.f — TRANSLATED (full build and all 272 tests passed; coverage probe with `u d~ ve e+ g g` returned NOT COVERED)
- [x] software/mcfm/src/BDK/M1bit1.f — TRANSLATED (build passed; coverage probe with `u d~ ve e+ g g` returned NOT COVERED)
- [x] software/mcfm/src/BDK/FFPMccTtilde.f — TRANSLATED (build passed; coverage probe with `u d~ ve e+ g g` returned NOT COVERED)

## Session log

- 2026-08-27: Opened Group 1 for the highest-fan-in ready infrastructure module. Replaced it with a C++ header/source pair plus a Fortran compatibility shim, moved the original to `deprecated/`, and confirmed the exhaustive suite reports `SUMMARY: pass rate 272/272`. No coverage process applies to Mods.
- 2026-08-27: Completed Group 2 after reviewing all three translations against their original Fortran sources and the M2bit2 draft hints. Each `u d~ ve e+ g g` coverage probe reported `NOT COVERED`; the restored exhaustive build/test run succeeded with `SUMMARY: pass rate 272/272`.
- 2026-08-27: Completed Group 3. Translated all three functions in `fvs.f` into a C++ header/source and Fortran interoperability shim, used `Need.hpp` for the existing special functions, wired CMake, and moved the original source to `deprecated/`. The exhaustive suite reported `SUMMARY: pass rate 272/272`; coverage probes for all three group members returned `NOT COVERED`, so they are recorded as TRANSLATED.
- 2026-08-27: `python3 dev/workflow.py refresh` printed `ready leaves (deps=0, non-blind): 224` and exited 0. `python3 dev/tmp/run_mcfm_verify.py software/mcfm/src/BDK/M1bit1.cpp -- u d~ ve e+ g g` printed `RESULT: NOT COVERED — the numbers did not change, so the test never ran this file.` and exited 1. `python3 dev/tmp/run_mcfm_verify.py software/mcfm/src/BDK/FFPMccTtilde.cpp -- u d~ ve e+ g g` printed `RESULT: NOT COVERED — the numbers did not change, so the test never ran this file.` and exited 1. `python3 dev/tmp/run_mcfm_verify.py software/mcfm/src/BDK/fvs.cpp -- u d~ ve e+ g g` printed `RESULT: NOT COVERED — the numbers did not change, so the test never ran this file.` and exited 1. Inspection of `approvals.toml` showed only `version = 1`, with no approval record or review guidance. `python3 dev/workflow.py gate mcfm-translate` printed `GATE: BLOCKED — approval batch limit reached before opening a new group.`, identified `Group 1 — Mods foundational types`, and exited 1. Human approval is required before another group can be opened.
- 2026-08-27: `python3 dev/workflow.py refresh` exited 0 and reported `source 524  translated 86  untranslated 438`, `ready leaves (deps=0, non-blind): 224`, `symbol index: 915 symbol(s)`, and `cleanup candidates: move 74  shim-delete 17  merge 38`. `python3 dev/tmp/run_mcfm_verify.py software/mcfm/src/BDK/M1bit1.cpp -- u d~ ve e+ g g` exited 1 with output `RESULT: NOT COVERED — the numbers did not change, so the test never ran this file.` and `Mark it TRANSLATED. Check again after a routine that calls it is rewritten.` `python3 dev/tmp/run_mcfm_verify.py software/mcfm/src/BDK/FFPMccTtilde.cpp -- u d~ ve e+ g g` exited 1 with the same NOT COVERED result and instruction. `python3 dev/tmp/run_mcfm_verify.py software/mcfm/src/BDK/fvs.cpp -- u d~ ve e+ g g` exited 1 with the same NOT COVERED result and instruction. Group 3 remains correctly recorded as TRANSLATED. `python3 dev/workflow.py gate mcfm-translate` exited 1 with `GATE: BLOCKED — approval batch limit reached before opening a new group.`, naming `Group 1 — Mods foundational types` as the blocking group because 3 completed groups are waiting and the limit is 3. Human approval is required before a new group can be opened.
- 2026-08-27: Repeated the required exact Group 3 probes. Command `python3 dev/tmp/run_mcfm_verify.py software/mcfm/src/BDK/M1bit1.cpp -- u d~ ve e+ g g` exited 1 with stdout:
  ```text
  == coverage check: software/mcfm/src/BDK/M1bit1.cpp ==
  process : u d~ ve e+ g g
  factor  : 1.5
  -- baseline build + test --
  -- scaling the marked output by 1.5 --
  -- probed build + test --

  RESULT: NOT COVERED — the numbers did not change, so the test never ran this file.
    Mark it TRANSLATED. Check again after a routine that calls it is rewritten.
  ```
  Stderr was empty. Command `python3 dev/tmp/run_mcfm_verify.py software/mcfm/src/BDK/FFPMccTtilde.cpp -- u d~ ve e+ g g` exited 1 with stdout:
  ```text
  == coverage check: software/mcfm/src/BDK/FFPMccTtilde.cpp ==
  process : u d~ ve e+ g g
  factor  : 1.5
  -- baseline build + test --
  -- scaling the marked output by 1.5 --
  -- probed build + test --

  RESULT: NOT COVERED — the numbers did not change, so the test never ran this file.
    Mark it TRANSLATED. Check again after a routine that calls it is rewritten.
  ```
  Stderr was empty. Command `python3 dev/tmp/run_mcfm_verify.py software/mcfm/src/BDK/fvs.cpp -- u d~ ve e+ g g` exited 1 with stdout:
  ```text
  == coverage check: software/mcfm/src/BDK/fvs.cpp ==
  process : u d~ ve e+ g g
  factor  : 1.5
  -- baseline build + test --
  -- scaling the marked output by 1.5 --
  -- probed build + test --

  RESULT: NOT COVERED — the numbers did not change, so the test never ran this file.
    Mark it TRANSLATED. Check again after a routine that calls it is rewritten.
  ```
  Stderr was empty. All statuses remain TRANSLATED as required by the oracle.
- 2026-08-27: `python3 dev/workflow.py gate mcfm-translate` exited 1 with stdout:
  ```text
  GATE: BLOCKED — approval batch limit reached before opening a new group.

  Transformation: mcfm-translate
  Blocking group: Group 1 — Mods foundational types
  Reason: 3 completed group(s) are waiting; limit is 3

  Approve with:
    python3 dev/tools/approve/approve_group.py /home/user/JSS-2026-Example/dev/transformations/mcfm-translate --latest-blocking

  Or approve this exact group explicitly:
    python3 dev/tools/approve/approve_group.py /home/user/JSS-2026-Example/dev/transformations/mcfm-translate "Group 1 — Mods foundational types" --by <name>
  ```
  Stderr was empty. No new group was opened because human approval is required by policy.
