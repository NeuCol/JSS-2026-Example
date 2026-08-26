# MCFM translation worklist

## Group 1 — ThreeJets five-gluon primitive amplitudes

- [x] software/mcfm/src/ThreeJets/A51mpmpp5g.f — TRANSLATED (build passed; coverage process `g g g g g` reported NOT COVERED)
- [x] software/mcfm/src/ThreeJets/A51mmppp5g.f — TRANSLATED (build passed; coverage process `g g g g g` reported NOT COVERED)

## Group 2 — ThreeJets quark-gluon primitive amplitudes

- [x] software/mcfm/src/ThreeJets/A5qbmgmqpgpgp.f — TRANSLATED (build passed; coverage process `g g g g g` reported NOT COVERED)
- [x] software/mcfm/src/ThreeJets/A5qbmgpqpgpgm.f — TRANSLATED (build passed; coverage process `g g g g g` reported NOT COVERED)
- [x] software/mcfm/src/ThreeJets/A5qbmqpgpgpgm.f — TRANSLATED (build passed; coverage process `g g g g g` reported NOT COVERED)

## Session log

- 2026-08-26: Opened Group 1 after refresh reported 229 ready leaves; translating the two related A51 five-gluon amplitudes.
- 2026-08-26: Completed Group 1. Both translations build cleanly and the exhaustive MCFM suite reports 272/272 passed; both ThreeJets coverage probes reported NOT COVERED, so both files are recorded TRANSLATED. Moved the original Fortran sources into `deprecated/`.
- 2026-08-26: Restored the missing archived `A51mmppp5g.f` and refreshed readiness (228 ready leaves). The new-group gate is open, but no new group was retained because the remaining ready ThreeJets amplitudes require substantial line-by-line translation and verification.
- 2026-08-26: Opened Group 2 after refresh reported 225 ready leaves; reviewed the three related quark-gluon primitive translations line by line against their Fortran sources.
- 2026-08-26: Completed Group 2. All three translations and shims match the original signatures and formulas, the exhaustive MCFM suite reports 272/272 passed, and all three ThreeJets coverage probes reported NOT COVERED, so they are recorded TRANSLATED. Moved the original Fortran sources into `deprecated/`.
