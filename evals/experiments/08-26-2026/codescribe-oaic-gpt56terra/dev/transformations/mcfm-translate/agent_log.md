# MCFM Fortran → C++ worklist

## Group Mods foundational type module
- [x] software/mcfm/src/Mods/types_mod.f — TRANSLATED (infrastructure; full restored build passed, 272/272 test cases PASSED)

## Group BDK ready amplitudes
- [x] software/mcfm/src/BDK/M3bit4.f — TRANSLATED (moved to `BDK/deprecated/`; restored build passed, 272/272 test cases PASSED; `u d~ ve e+ g g` coverage result NOT COVERED)

## Session log
- 2026-08-26: Translated `types_mod.f` to `types_mod.hpp`/`.cpp` plus `types_mod_fi.f90`, wired the new sources, and moved the original to `Mods/deprecated/`. The restored MCFM build and full test suite passed (272/272); infrastructure coverage is not applicable, so it is recorded TRANSLATED.
- 2026-08-26: Settled `BDK/M3bit4.f`: moved the original to `BDK/deprecated/`, and the restored build passed all 272/272 cases. The required BDK coverage probe for `u d~ ve e+ g g` was NOT COVERED, so it is recorded TRANSLATED.
