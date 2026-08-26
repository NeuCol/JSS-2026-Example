# MCFM translation worklist

## Group W2jet leaf functions

- [x] software/mcfm/src/W2jet/atree.cpp — TRANSLATED (NOT COVERED; restored build passed)
- [x] software/mcfm/src/W2jet/fvf.cpp — TRANSLATED (NOT COVERED; restored build passed)
- [x] software/mcfm/src/W2jet/subqcd.cpp — TRANSLATED (NOT COVERED; restored build passed)
- [x] software/mcfm/src/W2jet/vv.cpp — TRANSLATED (NOT COVERED; restored build passed)
- [x] software/mcfm/src/W2jet/vvg.cpp — TRANSLATED (NOT COVERED; restored build passed)

## Group W2jet coefficients and matrix elements — REOPENED

- [ ] software/mcfm/src/W2jet/ggZZcapture.f — FAILED (group reverted after 28 Z+2-jet oracle mismatches)
- [ ] software/mcfm/src/W2jet/ZZbox1LL.f — FAILED (group reverted after 28 Z+2-jet oracle mismatches)
- [ ] software/mcfm/src/W2jet/w2jetsq.f — FAILED (group reverted after 28 Z+2-jet oracle mismatches)
- [ ] software/mcfm/src/W2jet/a6treeg.f — FAILED (group reverted after 28 Z+2-jet oracle mismatches)
- [ ] software/mcfm/src/W2jet/qqbggAxslCoeffs.f — FAILED (group reverted after 28 Z+2-jet oracle mismatches)

## Group BDK compact coefficient functions — REOPENED

- [ ] software/mcfm/src/BDK/M3bit3.f — FAILED (translation reverted while isolating 28 Z+2-jet oracle mismatches)
- [ ] software/mcfm/src/BDK/M3bit4.f — FAILED (translation reverted while isolating 28 Z+2-jet oracle mismatches)
- [ ] software/mcfm/src/BDK/FPFMscT.f — FAILED (translation reverted while isolating 28 Z+2-jet oracle mismatches)
- [ ] software/mcfm/src/BDK/M3bit2.f — FAILED (translation reverted while isolating 28 Z+2-jet oracle mismatches)
- [ ] software/mcfm/src/BDK/M2bit2.f — FAILED (translation reverted while isolating 28 Z+2-jet oracle mismatches)

## Session log

- 2026-08-26: Completed the W2jet group after translation and wiring. All five files were NOT COVERED by `u d~ ve e+ g g`; every verification run completed its restored build successfully. Adjusted the vv and vvg probe markers to plain output assignments so the coverage oracle could instrument them. The final full MCFM build/test passed 272/272 cases.
- 2026-08-26: Translated and wired ggZZcapture, ZZbox1LL, w2jetsq, a6treeg, and qqbggAxslCoeffs, moving their Fortran originals to W2jet/deprecated. All five coverage probes were NOT COVERED by `u d~ ve e+ g g`; later exhaustive testing exposed 28 Z+2-jet mismatches, so this group was reopened and reverted.
- 2026-08-26: The BDK translations were reverted and their Fortran originals restored, but the exhaustive suite still reported the identical 28 Z+2-jet failures (244/272). This disproved attribution to the BDK group and showed the regression was already present in the preceding W2jet coefficients/matrix-elements group. That W2jet group was therefore also reverted and its Fortran originals restored. With only the W2jet leaf-function group retained, the exhaustive oracle explicitly passed all 272/272 cases. Both reverted groups are reopened as FAILED rather than left as settled TRANSLATED work.
