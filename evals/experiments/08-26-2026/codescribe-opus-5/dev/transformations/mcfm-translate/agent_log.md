# Agent log — mcfm-translate

Worklist and per-file status for step 1 (Fortran → C++). Statuses follow `desired_spec.md`.

## Group W2jet-1

Folder: `software/mcfm/src/W2jet` — coverage process from the Spec map: `u d~ ve e+ g g`.

Files in this group:

- [x] software/mcfm/src/W2jet/atree.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/fvf.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/a6treeg.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/subqcd.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/ZZbox1LL.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`; also not covered by the alternate W2jet process `u u~ e- e+ g g`)

Evidence: full MCFM build + test run `jobrunner submit tests/mcfm` reports
`SUMMARY: pass rate 272/272` with 272 individual `PASSED` test-case lines (no `FAILED`,
no silent segfault). Each file carries exactly one `// @coverage-probe` marker and was
run through `python3 dev/workflow.py verify <file> -- u d~ ve e+ g g`; every probe came
back `NOT COVERED`, so all five are recorded `TRANSLATED` rather than `VERIFIED`.

## Group W2jet-2

Folder: `software/mcfm/src/W2jet` — coverage process from the Spec map: `u d~ ve e+ g g`.

Ready leaves selected from `dev/tmp/assets/roadmap_metrics.tsv` (deps=0, blind=0, no generated
`.cpp` yet): `w2jetsq.f`, `qqbZggtree.f`, `vv.f`, `fpp.f`, `Ltfunctions.f`.

Files in this group:

- [x] software/mcfm/src/W2jet/w2jetsq.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/qqbZggtree.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/vv.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/fpp.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/Ltfunctions.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)

Evidence: after wiring the five new `.cpp`/`_fi.f90` pairs into
`software/mcfm/src/W2jet/CMakeLists.txt` and moving the original `.f` files into
`software/mcfm/src/W2jet/deprecated/`, `jobrunner submit tests/mcfm` reports
`SUMMARY: pass rate 272/272` with 272 individual `PASSED` test-case lines and no
`FAILED` line (no silent segfault). Each new `.cpp` carries exactly one
`// @coverage-probe` and was run through
`python3 dev/workflow.py verify <file> -- u d~ ve e+ g g`; every probe returned
`NOT COVERED`, so all five are recorded `TRANSLATED` rather than `VERIFIED`.

## Group W2jet-3

Folder: `software/mcfm/src/W2jet` — coverage process from the Spec map: `u d~ ve e+ g g`.

Ready leaves selected from `dev/tmp/assets/roadmap_metrics.tsv` (deps=0, blind=0, no generated
`.cpp` yet): `atrLLL.f`, `atrLRL.f`, `faxsl.f`, `Acalc.f`, `LRcalc.f`.

Files in this group:

- [x] software/mcfm/src/W2jet/atrLLL.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/atrLRL.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/faxsl.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/Acalc.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/LRcalc.cpp — TRANSLATED (not covered by `u d~ ve e+ g g`)

Evidence: the five `.cpp`/`.hpp`/`_fi.f90` triples are wired into
`software/mcfm/src/W2jet/CMakeLists.txt` and the original `.f` files were moved into
`software/mcfm/src/W2jet/deprecated/`. `jobrunner submit tests/mcfm` reports
`SUMMARY: pass rate 272/272` with 272 individual `PASSED` test-case lines and no
`FAILED` line (no silent segfault). Each new `.cpp` carries exactly one
`// @coverage-probe` and was run through
`python3 dev/tmp/verify_env.py <file> -- u d~ ve e+ g g`; all five probes returned
`RESULT: NOT COVERED`, so all five are recorded `TRANSLATED` rather than `VERIFIED`.

## Notes / session log

- Loop 2: the five W2jet translations (`atree`, `fvf`, `a6treeg`, `subqcd`, `ZZbox1LL`)
  from earlier loops were built, tested, and coverage-probed. The build is green
  (272/272) and every probe reported `NOT COVERED`, so the group is completed with five
  `TRANSLATED` entries and no `FAILED` entries.
- The sandboxed shell cannot `source environment.sh` or set inline env vars, so
  `dev/tmp/verify_env.py` was added as a thin wrapper that exports `MCFM_HOME` and
  forwards its arguments to `python3 dev/workflow.py verify`.
- Retry the coverage probes for these files once a caller in `W2jet` (for example
  `qqb_w2jet_v.f` / `xwqqgg_v.f` for `fvf`/`subqcd`, or `ZZmassivebox.f` for `ZZbox1LL`)
  has been rewritten; coverage may then flip to `COVERED`.
- No human decision is needed for this group beyond the normal approval gate.
- Loop 3: opened and completed `Group W2jet-2` with the next five ready leaves
  (`w2jetsq`, `qqbZggtree`, `vv`, `fpp`, `Ltfunctions`). `w2jetsq.cpp` includes
  `subqcd.hpp` and calls the C++ `subqcd` directly (no Fortran round trip);
  `vv.cpp` and `fpp.cpp` use `Need.hpp` (`lnrat`, `L0`, `L1`, `Lsm1`, `Lsm1_2mht`)
  plus `W1jet.hpp` for `t(...)`, and the `scale`/`epinv`/`epinv2`/`constants`
  module headers; `Ltfunctions` became one header/source/shim triple carrying all
  three functions (`Ltm1`, `Lt0`, `Lt1`), with `Lt0`/`Lt1` calling their C++
  siblings through the shared header.
- The coverage probe must be a single-line `lhs = rhs;   // @coverage-probe`
  statement; the first `qqbZggtree` probe spanned several lines and the checker
  refused to scale it, so those assignments were reflowed onto one line each.
- All five probes came back `NOT COVERED` under `u d~ ve e+ g g`. Retry once a
  caller is rewritten: `a6.f` (calls `vv` and `fpp`), `xwqqgg_v.f` / `qqb_w2jet_v.f`
  (reach `w2jetsq`), `qqbZgg_floop.f` (calls `qqbZggtree`), `A6axBDK.f`
  (calls `Ltm1`/`Lt0`/`Lt1`).
- Two completed groups are now pending approval (limit is 3), so a third group may
  still be opened without human approval.
- Loop 4: opened `Group W2jet-3` with the next five ready leaves (`atrLLL`, `atrLRL`,
  `faxsl`, `Acalc`, `LRcalc`), wired them into the folder `CMakeLists.txt`, and got a
  green build: `SUMMARY: pass rate 272/272`, 272 `PASSED` lines, no `FAILED`.
- `git mv` of the five original `.f` sources into `W2jet/deprecated/` failed under the
  sandboxed shell (exit 128), so `dev/tmp/move_deprecated3.py` was added as a small
  Python helper that performs the moves directly; the originals now live in
  `software/mcfm/src/W2jet/deprecated/`.
- Loop 5: ran the coverage probe for all five Group W2jet-3 files
  (`python3 dev/tmp/verify_env.py software/mcfm/src/W2jet/<file>.cpp -- u d~ ve e+ g g`).
  Every probe printed `RESULT: NOT COVERED`, so the group is completed with five
  `TRANSLATED` entries and no `FAILED` entries.
- Retry those probes once a caller is rewritten: `a61LLL.f`/`a61LRL.f` reach
  `atrLLL`/`atrLRL`, `fax.f`/`fsl.f` and `qqbggAxslCoeffs.f` reach `faxsl`, and
  `A6axBDK.f` / `BDKqqbggAxAmp.f` reach `Acalc`/`LRcalc`.
- Three completed groups (`W2jet-1`, `W2jet-2`, `W2jet-3`) are now pending approval,
  which is the configured limit, so human approval is required before `Group W2jet-4`
  can be opened. Stopping here per the Plan's *When to stop* rule.
- Human decision needed: run
  `python3 dev/workflow.py approve mcfm-translate --latest-blocking` (or `--latest`)
  to release the gate for the next group.
- Loop 5 closing state: `python3 dev/workflow.py refresh` reports
  `source 516  translated 86  untranslated 430` and `ready leaves (deps=0, non-blind): 224`;
  a final `jobrunner submit tests/mcfm` after the probes restored the tree gives
  `SUMMARY: pass rate 272/272` with 272 `PASSED` lines and no `FAILED` line, and
  `python3 dev/workflow.py gate mcfm-translate` reports
  `GATE: BLOCKED — approval batch limit reached before opening a new group`
  (blocking group: `Group W2jet-1`).
