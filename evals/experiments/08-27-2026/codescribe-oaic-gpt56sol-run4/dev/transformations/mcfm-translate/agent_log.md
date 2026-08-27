# MCFM translation worklist

## Group 1 — Mods type-kind infrastructure

Ready-leaf count: 229

```text
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
```

- [x] software/mcfm/src/Mods/types_mod.f — TRANSLATED (Mods infrastructure; build passed 272/272)

## Group 2 — W2jet amplitudes

Ready-leaf count: 229

```text
# next translation candidates
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/ZZbox1LL.f  (fanin=2, bench=u d~ ve e+ g g)
```

- [x] software/mcfm/src/W2jet/atree.f — TRANSLATED (exhaustive suite passed 272/272; `u d~ ve e+ g g` coverage probe reported NOT COVERED)
- [x] software/mcfm/src/W2jet/a6treeg.f — TRANSLATED (exhaustive suite passed 272/272; `u d~ ve e+ g g` coverage probe reported NOT COVERED)
- [x] software/mcfm/src/W2jet/subqcd.f — TRANSLATED (exhaustive suite passed 272/272; `u d~ ve e+ g g` coverage probe reported NOT COVERED)

## Group 3 — W2jet coefficient capture

Ready-leaf count: 234

```text
# next translation candidates
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/ZZbox1LL.f  (fanin=2, bench=u d~ ve e+ g g)
- W2jet/a6routine.f  (fanin=2, bench=u d~ ve e+ g g)
```

- [x] software/mcfm/src/W2jet/ggZZcapture.f — TRANSLATED (exhaustive suite passed 272/272; `u d~ ve e+ g g` coverage probe reported NOT COVERED)

## Session log

- 2026-08-27: Completed Group 1 by translating the `types` kind module to a C++ header/source pair, retaining a Fortran compatibility module, wiring CMake, and archiving the original. The exhaustive MCFM suite passed 272/272.
- 2026-08-27: Opened Group 2 from the highest-ranked ready W2jet leaf.
- 2026-08-27: Verified the restored `atree` build and found the representative W2jet process did not cover it; continued Group 2 with ready, self-contained W2jet amplitudes.
- 2026-08-27: Translated `a6treeg` and `subqcd`, archived their Fortran sources, and verified the exhaustive build/test suite. Coverage probes reported both routines not covered by the representative process. Group 2 is complete.
- 2026-08-27: Fixed the `ggZZcapture` Fortran shim's mixed-case C binding name, after the exhaustive build exposed an undefined lowercase linker symbol. The rerun explicitly passed all 272/272 cases. Official `u d~ ve e+ g g` probes reported `atree`, `a6treeg`, `subqcd`, and `ggZZcapture` NOT COVERED, so Groups 2 and 3 remain TRANSLATED rather than VERIFIED. Group 3 is complete; further work is subject to the approval gate.
- 2026-08-27: Refreshed the roadmap (440 untranslated rows, 238 ready leaves) and checked the new-group gate. It is blocked because three completed groups await human approval; Group 1 is the exact blocking group. No Group 4 was opened and no unrelated source work was started.
- 2026-08-27: Final-loop follow-up confirmed that `approvals.toml` still has no Group 1 approval or review note. The gate remains blocked on Group 1, so no Group 4 was opened; a human must run the latest-blocking approval command before translation may continue.
