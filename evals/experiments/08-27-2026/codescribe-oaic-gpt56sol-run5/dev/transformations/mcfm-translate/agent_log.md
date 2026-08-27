# MCFM translation worklist

## Group 1 — Mods ready leaves

Ready-leaf count: 229

```text
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
```

Folder-coherent selection: after the first-ranked `Mods/types_mod.f`, the group is filled with the remaining ready files from `Mods`.

- [x] software/mcfm/src/Mods/types_mod.f — TRANSLATED (infrastructure module; full MCFM build and tests passed)
- [x] software/mcfm/src/Mods/pp_mod.f90 — TRANSLATED (infrastructure module; full MCFM build and tests passed)
- [x] software/mcfm/src/Mods/ppwp2j_mod.f90 — TRANSLATED (infrastructure module; full MCFM build and tests passed)
- [x] software/mcfm/src/Mods/Modules_Interface.f90 — TRANSLATED (infrastructure bridge; full MCFM build and tests passed)
- [x] software/mcfm/src/Mods/mod_qcdloop_c.f — TRANSLATED (QCDLoop interoperability declarations; full MCFM build and tests passed)

## Group 2 — W2jet ready leaves

Ready-leaf count: 225

```text
# next translation candidates
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/ZZbox1LL.f  (fanin=2, bench=u d~ ve e+ g g)
```

Folder-coherent selection: after the first-ranked `W2jet/atree.f`, the group is filled with ready files from `W2jet`.

- [x] software/mcfm/src/W2jet/atree.f — TRANSLATED (build passed; representative process did not cover it)
- [x] software/mcfm/src/W2jet/ggZZcapture.f — TRANSLATED (build passed; representative process did not cover it)
- [x] software/mcfm/src/W2jet/ZZbox1LL.f — TRANSLATED (build passed; representative process did not cover it)
- [x] software/mcfm/src/W2jet/a6routine.f — TRANSLATED (build passed; representative process did not cover it)
- [x] software/mcfm/src/W2jet/a6treeg.f — TRANSLATED (build passed; representative process did not cover it)

## Session log

- 2026-08-27: Opened Group 1 from 229 ready leaves; translating the five currently ready `Mods` files.
- 2026-08-27: Translated `types_mod.f` to a C++ header/source plus Fortran interoperability module, moved the original to `deprecated/`, and passed `jobrunner submit tests/mcfm`.
- 2026-08-27: Completed Group 1: translated the `pp_mod` and `ppwp2j_mod` data modules, the central module initialization bridge, and the QCDLoop C declaration module; moved originals to `deprecated/`; and passed the full MCFM build and tests.
- 2026-08-27: Completed Group 2 translations and wiring, moved originals to `W2jet/deprecated/`, and confirmed 272 `PASSED` results. Coverage reported NOT COVERED for all five files, including the final corrected `a6treeg.cpp` probe; each remains TRANSLATED pending coverage through a rewritten caller.
- 2026-08-27: Retried the corrected `a6treeg.cpp` coverage probe and confirmed NOT COVERED, then reran the restored full MCFM suite: `SUMMARY: pass rate 272/272` with 272 `PASSED` lines and zero `FAILED` lines.
