# MCFM translation worklist

## Group 1 — Mods foundational interfaces

Ready-leaf count: 229
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
This group contains only the top-ranked file: the other ready `Mods` entries are unrelated large data or interoperability modules, so including them would not form a coherent review unit.

- [x] software/mcfm/src/Mods/types_mod.f — TRANSLATED (infrastructure module; full build and 272/272 tests passed)

## Group 2 — W2jet amplitudes

Ready-leaf count: 229
# next translation candidates
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/ZZbox1LL.f  (fanin=2, bench=u d~ ve e+ g g)
The group follows the first candidate's `W2jet` folder; `BDK/fvs.f` is skipped for folder coherence.

- [x] software/mcfm/src/W2jet/atree.f — TRANSLATED (build passed; representative process did not cover this file)
- [x] software/mcfm/src/W2jet/ggZZcapture.f — TRANSLATED (build passed; representative process did not cover this file)
- [x] software/mcfm/src/W2jet/ZZbox1LL.f — TRANSLATED (build passed; representative process did not cover this file)
- [x] software/mcfm/src/W2jet/a6routine.f — TRANSLATED (build passed; representative process did not cover this file)
- [x] software/mcfm/src/W2jet/a6treeg.f — TRANSLATED (build passed; representative process did not cover this file)

## Group 3 — BDK amplitudes

Ready-leaf count: 235
# next translation candidates
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/fvf.f  (fanin=2, bench=u d~ ve e+ g g)
- W2jet/subqcd.f  (fanin=2, bench=u d~ ve e+ g g)
- gghgg_dep/gghgg_dep_params.f  (fanin=2, bench=g g h g g)
- BDK/FFMPcc.f  (fanin=1, bench=)
The group follows the first candidate's `BDK` folder; intervening W2jet and gghgg_dep candidates are skipped for folder coherence.

- [x] software/mcfm/src/BDK/fvs.f — TRANSLATED (full build and 272/272 tests passed; representative process did not cover this file)
- [x] software/mcfm/src/BDK/FFMPcc.f — TRANSLATED (full build and 272/272 tests passed; representative process did not cover this file)
- [x] software/mcfm/src/BDK/FFPMccT.f — TRANSLATED (full build and 272/272 tests passed; representative process did not cover this file)
- [x] software/mcfm/src/BDK/FFPMccTtilde.f — TRANSLATED (full build and 272/272 tests passed; representative process did not cover this file)
- [x] software/mcfm/src/BDK/FFPMscT.f — TRANSLATED (full build and 272/272 tests passed; representative process did not cover this file)

## Session log

- 2026-08-28: Translated `types_mod.f` into a C++ header/source plus Fortran compatibility module, moved the original to `deprecated/`, and validated the full MCFM suite (272/272 passed). Remaining work is governed by the refreshed ready set and approval gate.
- 2026-08-28: Completed the five-file W2jet group, moved all originals to `deprecated/`, and ran the W2jet coverage oracle for each file. All five reported `NOT COVERED`; the restored full MCFM build/test job passed, so they are recorded as `TRANSLATED`. The next ready work starts with `BDK/fvs.f`, subject to the approval gate.
- 2026-08-28: Completed the five-file BDK group and audited the translations against their deprecated Fortran originals, including expression grouping, floating-point coefficients, array/wrapper signatures, own headers, dependencies, shims, and CMake wiring. Corrected integer coefficients that caused mixed `int`/`complex<double>` overload failures. The full MCFM suite explicitly reported 272 `PASSED` cases and `SUMMARY: pass rate 272/272`. Coverage probes with `u d~ ve e+ g g` reported `NOT COVERED` for all five files, so each is recorded as `TRANSLATED`.
