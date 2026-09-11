# mcfm-translate worklist

## Group W2jet-1

Provenance (recorded at group open, after `python3 dev/workflow.py refresh`):

- ready-leaf count from `python3 dev/workflow.py status`: 229 ready leaves (445 untranslated file rows)
- first five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/atree.f  (fanin=6, bench=u d~ ve e+ g g)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
```

Why the group is not that list's top entries: the top candidate `Mods/types_mod.f` is not
translatable (four `selected_real_kind` parameters; a kind must be a compile-time constant, so
the `c_f_pointer` module mirror is illegal Fortran, and the rewrite table already absorbs
`real(dp)` into `double`), so it was skipped. The first translatable candidate is
`W2jet/atree.f`, and the rest of the group was filled folder-coherently from `src/W2jet` per
Resolution step 2, taking the tree-amplitude/coupling-factor cluster (`a6.f` calls
`atree`+`vv`; `a6g.f` calls `a6treeg`+`vvg`). `W2jet/ggZZcapture.f` was left for a later group:
it is a `character*(*)`-dispatch routine writing the `ggZZ_mod` 4-D `res` array and wants its
own group.

Results:

- [x] software/mcfm/src/W2jet/a6treeg.cpp — VERIFIED (worst Δrel 0)
- [x] software/mcfm/src/W2jet/vvg.cpp — VERIFIED (worst Δrel 0)
- [x] software/mcfm/src/W2jet/atree.cpp — TRANSLATED (build passes; probe NOT COVERED by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/vv.cpp — TRANSLATED (build passes; probe NOT COVERED by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/fvf.cpp — TRANSLATED (build passes; probe NOT COVERED by `u d~ ve e+ g g`)

Group status: completed, awaiting human approval before the next group starts.

## Group W2jet-2

Provenance (recorded at group open, after `python3 dev/workflow.py refresh`):

- ready-leaf count from `python3 dev/workflow.py status`: 230 ready leaves (440 untranslated file rows)
- first five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/ZZbox1LL.f  (fanin=2, bench=u d~ ve e+ g g)
```

Why the group is not that list's top entries: `Mods/types_mod.f` is still the untranslatable
`selected_real_kind` module skipped in Group W2jet-1. `W2jet/ggZZcapture.f` is the first
translatable candidate but was deferred again for a newly-found reason, recorded below: its
output array `res` lives in `ggZZ_mod`, whose Fortran side is **not** aliased to the C++
storage. `BDK/fvs.f` is outside `src/W2jet`, so per Resolution step 2 the group stays
folder-coherent and takes `ZZbox1LL.f` plus `subqcd.f`, the two remaining fanin=2 W2jet leaves.

Results:

- [x] software/mcfm/src/W2jet/subqcd.cpp — VERIFIED (worst Δrel 0)
- [x] software/mcfm/src/W2jet/ZZbox1LL.cpp — VERIFIED (worst Δrel 0)

Group status: completed, awaiting human approval before the next group starts.

## Group W2jet-3

Provenance (recorded at group open, after `python3 dev/workflow.py refresh`):

- ready-leaf count from `python3 dev/workflow.py status`: 230 ready leaves (438 untranslated file rows)
- first five lines of `python3 dev/workflow.py next mcfm-translate`, verbatim:

```
# next translation candidates
- Mods/types_mod.f  (fanin=8, bench=)
- W2jet/ggZZcapture.f  (fanin=6, bench=u d~ ve e+ g g)
- BDK/fvs.f  (fanin=2, bench=)
- W2jet/w2jetsq.f  (fanin=2, bench=u d~ ve e+ g g)
```

Why the group is not that list's top entries: `Mods/types_mod.f` is still the untranslatable
`selected_real_kind` module skipped in Groups W2jet-1 and W2jet-2. `W2jet/ggZZcapture.f` is the
first translatable candidate and is taken this time, its `ggZZ_mod` blocker resolved (below).
`BDK/fvs.f` is outside `src/W2jet`, so per Resolution step 2 the group stays folder-coherent and
takes `w2jetsq.f`, the next `src/W2jet` entry. `ZZmbc.f` was considered as the natural pairing
for the ZZ cluster but dropped: at 692 lines it is mostly commented-out derivations plus four
helper functions, and a grep shows it uses `ggZZ_mod` only for `ggZZuse6d`, never for `res`, so
it adds no coverage of the `res` contract this group exists to settle.

Results:

- [x] software/mcfm/src/W2jet/ggZZcapture.cpp — TRANSLATED (build passes; probe NOT COVERED by `u d~ ve e+ g g`)
- [x] software/mcfm/src/W2jet/w2jetsq.cpp — TRANSLATED (build passes; probe NOT COVERED by `u d~ ve e+ g g`)

Group status: completed, awaiting human approval before the next group starts.

## Notes / session log

### 2026-09-11

Changed: translated five `src/W2jet` ready leaves — `atree.f`, `a6treeg.f`, `fvf.f`, `vv.f`,
`vvg.f` — each into `<base>.cpp` + `<base>.hpp` + `<base>_fi.F90`. Each `.cpp` includes its own
header; cross-unit calls go through headers (`<W1jet.hpp>` for `t`, `<Need.hpp>` for `lnrat`,
`i3m`, `Lsm1_2mh`, `Lsm1_2me`), with no translation-era forward declarations. `src/W2jet` is not
on the compiler include path, so each unit includes its own header with quotes; cross-folder
headers keep angle brackets. Wired the new files into `src/W2jet/CMakeLists.txt` and moved the
five originals into `src/W2jet/deprecated/`.

`atree` and `vv` take a `character(len=2)` selector and `Fvf`/`a6treeg`/`vvg` take the
`heldefs_mod` integer selector; the character ones pass a 2-element `character(kind=c_char)`
array through the shim so no hidden-length argument is involved.

Verification: `jobrunner submit tests/mcfm` SUCCESS — 272 PASSED, 0 FAILED, every case showing
an explicit PASSED marker (checked rather than inferring from the absence of FAILED). The
`u d~ ve e+ g g` benchmark reports all four ratios exactly 1 at tolerance 1e-13.

Coverage probes ran with the process passed as separate argv words (quoting the whole process
as one argument silently reports NOT COVERED). `a6treeg` and `vvg` came back COVERED, which
serves as the positive control proving the probe harness works, so the NOT COVERED verdicts for
`atree`, `vv` and `fvf` are genuine and those three are recorded TRANSLATED. Re-probe them once
a caller (`a6.f`, `a6routine.f`, `atrLLL.f`, `atrLRL.f`, `xzqqgg.f`) is itself rewritten.

Repair needed before verification could be trusted: `dev/tools/coverage/coverage_check.py`
`run_test` was again missing `cwd=bin`, so the MCFM `test` binary ran outside `Bin/` and every
probe would have reported NOT COVERED. Re-added `cwd=bin` (line 33). This keeps regressing and
is still uncommitted — a person should decide whether to commit it.

Remains: `W2jet/ggZZcapture.f`, `W2jet/ZZbox1LL.f` and the rest of the `src/W2jet` ready set.

Human decision needed: this completed group needs approval before a new group starts
(`python3 dev/workflow.py approve mcfm-translate --latest-blocking`), and the recurring
`coverage_check.py` `cwd=` fix should be committed upstream rather than re-applied each run.

### 2026-09-11 (loop 2)

Re-probed the three Group W2jet-1 units left at TRANSLATED against the *second* W2jet process
from the Spec coverage map, `u u~ e- e+ g g`: `atree.cpp`, `vv.cpp` and `fvf.cpp` all came back
NOT COVERED again. Ran `a6treeg.cpp` and `vvg.cpp` under the same process as an independent
positive control — both COVERED — so the harness works for this process and the three
TRANSLATED verdicts are genuine, not a probe artefact. They stay TRANSLATED; re-probe once a
caller (`a6.f`, `a6routine.f`, `atrLLL.f`, `atrLRL.f`, `xzqqgg.f`) is itself rewritten.

Changed: translated two more `src/W2jet` ready leaves — `subqcd.f` and `ZZbox1LL.f` — each into
`<base>.cpp` + `<base>.hpp` + `<base>_fi.F90`, wired into `src/W2jet/CMakeLists.txt`, originals
moved to `src/W2jet/deprecated/`. `ZZbox1LLcore` has no caller outside `ZZbox1LL.f`, so it is a
file-local `static` function in `ZZbox1LL.cpp` rather than a second exported unit with a shim.
`subqcd`'s `amp(-1:1,-1:1)` maps onto `FArray2D<...>(famp, 3, 3, -1, -1)`; its shim declares
`amp` `intent(inout)`, not `intent(out)`, because the routine only ever assigns the four `±1`
corners and the caller's `(0,*)`/`(*,0)` elements must survive the call unchanged.

Verification: `jobrunner submit tests/mcfm` SUCCESS — 272 PASSED, 0 FAILED, `SUMMARY: pass rate
272/272`, every case carrying an explicit PASSED marker (counted, not inferred from the absence
of FAILED). Benchmark tolerance 1e-13. Coverage probes with the process passed as separate argv
words: `subqcd.cpp` COVERED and `ZZbox1LL.cpp` COVERED under `u u~ e- e+ g g`, and the restored
build re-passes 272/272, so both are recorded VERIFIED.

`coverage_check.py` still carried the `cwd=bin` repair from the previous loop and needed no
re-application this loop; `git diff` confirms it remains the only tracked working-tree change
and it is still uncommitted.

Blocker found for `W2jet/ggZZcapture.f` (deferred, not attempted): `ggZZ_mod` is not a shared
mirror. `src/Mods/ggZZ_mod.f90` does

```
allocate(res(1:2,1:4,1:10,1:3))
call c_f_pointer(get_res(), temp_ptr, [2,4,10,3])
res(1:2,1:4,1:10,1:3) = temp_ptr(1:2,1:4,1:10,1:3)
```

i.e. the Fortran `res` is a *separately allocated copy* taken once at init, unlike
`sprods_com_mod%s` and `first_mod%first`, which are true `c_f_pointer` aliases onto the C++
storage. So a C++ `ggZZcapture` writing `ggZZ_mod::res` would be invisible to the Fortran
readers of `res` (`ggZZmassamp_new.f` and the ZZ coefficient routines) — silently wrong, and
the probe would not necessarily catch it. The fix is for `ggZZcapture_fi.F90` to `use ggZZ_mod`
and pass `res` through to the wrapper as an explicit array argument so C++ writes the Fortran
storage directly; that shim also needs the padded `character(kind=c_char)` buffer plus explicit
length argument for the `character*(*)` label. Pair it with the remaining ZZ cluster.

Remains: `W2jet/ggZZcapture.f` and the other 30 `src/W2jet` ready leaves.

Human decision needed: two completed groups now await approval
(`python3 dev/workflow.py approve mcfm-translate --latest-blocking`); the gate still reports OK
(2 waiting, limit 3), so the next loop may open one more group before it blocks. The recurring
`coverage_check.py` `cwd=` fix should be committed upstream rather than re-applied each run.

### 2026-09-11 (loop 3)

Changed: translated the two `src/W2jet` ready leaves of Group W2jet-3 — `ggZZcapture.f` and
`w2jetsq.f` — each into `<base>.cpp` + `<base>.hpp` + `<base>_fi.F90`, wired into
`src/W2jet/CMakeLists.txt`, originals moved to `src/W2jet/deprecated/`.

`ggZZcapture` resolves the `ggZZ_mod` blocker recorded in loop 2 exactly as planned there:
`ggZZcapture_fi.F90` does `use ggZZ_mod` and passes `res` to the wrapper as an explicit
`complex(c_double_complex) :: res(2,4,10,3)` argument, so C++ writes the Fortran storage that the
Fortran readers see, rather than the unrelated C++ `ggZZ_mod::res` allocation. `ggZZcapture.cpp`
therefore does *not* include `ggZZ_mod.hpp`; a comment in the file records why. `first` is a true
`c_f_pointer` alias, so it is read and cleared through `first_mod::first` in C++ as in the original.

The `character*(*) label` crosses the shim as a blank-padded 32-character
`character(kind=c_char)` buffer plus an explicit `label_len`. C++ reconstructs `trim(label)` from
the first `label_len` characters with trailing blanks removed, and takes the `label(1:5)` /
`label(6:6)` substrings of the `bubmp`/`bubpp` branches from the padded buffer. That last point is
a deliberate small divergence: the original indexes `label(1:5)` even when the actual argument is
shorter (every current caller passes a 3-to-8 character literal), which reads off the end of the
string; against the padded buffer the comparison is well defined and simply does not match.
`amp0`/`amp2`/`amp4` stay pass-by-reference `intent(inout)` because the permuted branches
overwrite them with `conjg`, which the original propagates back to the caller.

`w2jetsq` calls the already-translated C++ `subqcd` directly through `"subqcd.hpp"` (same folder,
so quoted) rather than through its Fortran shim. `mmsq_cs_mod` was checked before writing to it
and *is* a true alias — `mmsq_cs(0:,1:,1:) => fptr` is pointer rank remapping onto the C++
storage, not the copy that `ggZZ_mod` makes — so writing `mmsq_cs` from C++ is visible to Fortran.
Fortran `abs(z)**2` is translated as `std::abs(z)*std::abs(z)`, not `std::norm(z)`: `norm` sums
the squares while the original squares the modulus, and the two differ in the last bits at a 1e-13
benchmark tolerance.

Verification: `jobrunner submit tests/mcfm` SUCCESS — 272 PASSED, 0 FAILED, `SUMMARY: pass rate
272/272`, counted from explicit PASSED markers rather than inferred from the absence of FAILED.
Benchmark tolerance 1e-13. Coverage probes with the process passed as separate argv words: both
`ggZZcapture.cpp` and `w2jetsq.cpp` came back NOT COVERED under `u d~ ve e+ g g`, and `a6treeg.cpp`
probed under the same process as an independent positive control came back COVERED, so the harness
works for this process and both NOT COVERED verdicts are genuine. Both are recorded TRANSLATED.
The restored build re-passes 272/272.

Why these two are not covered: `ggZZcapture` writes only the `res` debug-capture buffer and every
call site is guarded by `if (docheck)`, so it cannot move a cross-section — grep confirms no
routine, Fortran or C++, ever reads `res` back. Re-probe `w2jetsq` once its caller
`qqb_wp2jetx_new.f` is rewritten.

`coverage_check.py` still carried the `cwd=bin` repair from loop 1 and needed no re-application
this loop; `git diff` confirms it remains the only tracked working-tree change and it is still
uncommitted.

Remains: the other 30 `src/W2jet` ready leaves (`ZZmbc.f`, `ZZbox2LL.f`, `ZZC012x34LLmp.f`,
`ZZintegraleval.f`, `ZZtri12_34LL.f`, `ZZtri1_2LL.f` and the rest of the ZZ cluster; `Acalc.f`,
`Ftexact.f`, `LRcalc.f`, `Ltfunctions.f`, the `f*`/`qqbggAx*` families).

Human decision needed: three completed groups now await approval, which reaches the gate limit —
`python3 dev/tools/approve/check_gate.py dev/transformations/mcfm-translate` reported OK (2
waiting, limit 3) when Group W2jet-3 was opened, so the *next* loop must run
`python3 dev/workflow.py approve mcfm-translate --latest-blocking` before any further group can
open. Two standing items are unchanged and both need a person: the recurring `coverage_check.py`
`cwd=` fix should be committed upstream rather than re-applied each run, and `Mods/types_mod.f`
plus `Mods/Modules_Interface.f90` rank as ready leaves on every refresh but are untranslatable —
an explicit never-translate list in `current_plan.md` would remove that triage cost from the top
of every candidate list.

### 2026-09-11 (loop 4)

No group opened and no file translated: the gate is genuinely blocking.
`python3 dev/tools/approve/check_gate.py dev/transformations/mcfm-translate` reports
`GATE: BLOCKED — approval batch limit reached before opening a new group`, blocking group
`Group W2jet-1`, reason `3 completed group(s) are waiting; limit is 3`.
`python3 dev/workflow.py status` agrees: `groups: 3 total, 0 open, 3 completed, 3 pending
approval`. With 0 open groups there is no in-group work the gate would still allow, so per the
Plan's "When to stop" this loop stops for human review rather than opening `Group W2jet-4`.

Verification of the existing tree was re-run anyway (the gate blocks new groups, not builds or
verification): `jobrunner submit tests/mcfm` SUCCESS in 1:31.8, and counting explicit markers in
`tests/mcfm/job.output` gives 272 `PASSED` / 0 `FAILED` with `SUMMARY: pass rate 272/272` at
benchmark tolerance 1e-13. The nine translated files from Groups W2jet-1..3 are therefore still
good; nothing regressed while waiting for approval.

Roadmap was stale and has been refreshed. Before `python3 dev/workflow.py refresh`, both
`W2jet/ggZZcapture.f` and `W2jet/w2jetsq.f` still appeared as ready leaves and as the #2/#4
entries of `next`, even though loop 3 translated both; the index had not been rebuilt since. After
refresh: `source 522  translated 86  untranslated 436`, `ready leaves (deps=0, non-blind): 234`,
and both files correctly leave the ready set. W2jet ready leaves went 31 -> 35, because loop 3's
work unblocked four new ones (`ZZC01x2LLmp.f`, `ZZC01x34LLmp.f`, `ZZD02x1x34LLmp.f`,
`ZZD062x1x34LLmp.f`).

**The planned "Group W2jet-4 over the ZZ cluster" is now the wrong next group.** Resolution step 2
says to take the *first* candidate `next` prints and fill the group from that file's own folder.
Post-refresh `next` prints no W2jet file at all in its top ten; after skipping the untranslatable
`Mods/types_mod.f` the first translatable candidate is `BDK/fvs.f` (fanin=2), so the next group is
a **BDK** group seeded by `BDK/fvs.f` and filled folder-coherently from `src/BDK` (29 BDK ready
leaves, the `FF*`/`F*F*` bracket-function family plus `M1bit1.f`, `M2abit1.f`, `M2abit2.f`).
The ZZ cluster stays valid work but is no longer the ranked front of the queue.

Trap recorded for that group: `roadmap_metrics.tsv` leaves the bench column **empty** for every
BDK row, which reads as "infrastructure, mark TRANSLATED". That is wrong. The Spec's coverage map
maps BDK explicitly — `u d~ ve e+ g g` (W2jet / BDK / loop) and `u u~ e- e+ g g` (Z2jet / W2jet /
BDK / loop). BDK files are coverage-probeable and can reach VERIFIED; do not downgrade them to
TRANSLATED on the strength of the blank column. Keep pairing every probe with a known-COVERED
positive control in the same process.

`coverage_check.py` still carries the `cwd=bin` repair on line 33 and it is still the only tracked
working-tree change (`git diff` confirms). It was not committed here: committing a shared tool
outside this transformation is a human's call, and it is now escalated rather than left as an open
question for a fifth loop. The exact patch a person needs to apply upstream is, in `run_test`:
`subprocess.run([bin + "/test", "-b", *process], capture_output=True, text=True, cwd=bin)` — the
`cwd=bin` is the whole fix. Without it every coverage probe silently returns NOT COVERED.

Still needing a person, unchanged from loop 3: approval of the three waiting groups; a ruling on
whether `ggZZcapture.cpp` (writes only the `docheck`-guarded `res` buffer that nothing reads back)
needs an explicit exemption from the VERIFIED bar; and whether `current_plan.md` should carry a
never-translate list covering `Mods/types_mod.f` and `Mods/Modules_Interface.f90`, which cost
triage at the top of every candidate list.

### 2026-09-11 (loop 5)

No group opened and no file translated — the gate is still blocking, unchanged since loop 4.
`python3 dev/tools/approve/check_gate.py dev/transformations/mcfm-translate` reports
`GATE: BLOCKED — approval batch limit reached before opening a new group`, blocking group
`Group W2jet-1`, reason `3 completed group(s) are waiting; limit is 3`.
`python3 dev/workflow.py status` agrees: `groups: 3 total, 0 open, 3 completed, 3 pending
approval`. With 0 open groups there is no in-group work the gate would still permit, so per the
Plan's "When to stop" this loop again stops for human review. Approval is a person's call and was
not self-issued here; the unblock command remains
`python3 dev/tools/approve/approve_group.py dev/transformations/mcfm-translate --latest-blocking`
(the script takes the transformation *directory path*, not the bare name).

Regression check re-run while waiting: `jobrunner submit tests/mcfm` SUCCESS in 1:31.5, and
counting explicit markers in `tests/mcfm/job.output` gives 272 `PASSED` / 0 `FAILED` with
`SUMMARY: pass rate 272/272`. The nine translated files from Groups W2jet-1..3 remain good across
two consecutive waiting loops; nothing has drifted.

BDK group pre-staged so the next unblocked loop can open it without re-deriving. `python3
dev/workflow.py next mcfm-translate` still ranks `Mods/types_mod.f` (fanin=8) first — untranslatable,
skip it — making `BDK/fvs.f` (fanin=2) the seed, exactly as loop 4 concluded. The ZZ cluster of the
originally-planned "Group W2jet-4" is still *not* the ranked front of the queue.

Correction to loop 4's count of that group: the 29 BDK ready leaves (deps=0, blind=0, verified by
`awk` over `roadmap_metrics.tsv`) are **17 F-family + 12 M-family**, not "the FF*/F*F* family plus
M1bit1.f, M2abit1.f, M2abit2.f" — loop 4 undercounted the M-family by nine. Full list:
- F-family (17): `fvs.f`, `FFMPcc.f`, `FFPMccT.f`, `FFPMccTtilde.f`, `FFPMscT.f`,
  `FFPMscTtilde.f`, `FFPPcc.f`, `FFPPsc.f`, `FMPFsc.f`, `FPFMccTtilde.f`, `FPFMscT.f`,
  `FPFPcc.f`, `FPFPsc.f`, `FPMFcc.f`, `FPMFsc.f`, `FPPFcc.f`, `FPPFsc.f`
- M-family (12): `M1bit1.f`, `M2abit1.f`, `M2abit2.f`, `M2bit1.f`, `M2bit2.f`, `M2bit3.f`,
  `M3abit1.f`, `M3abit2.f`, `M3bit1.f`, `M3bit2.f`, `M3bit3.f`, `M3bit4.f`
The `Master*.f` files and `FMPFcc.f`/`FFMPsc.f`/`FPFMsc.f`/`FFPMcc.f`/`FPFMcc.f`/`FFPMsc.f` are
*not* leaves yet (deps 1-5) and must wait on the leaves above.

The empty-bench trap is re-confirmed quantitatively: all 29 BDK ready leaves have an empty `bench`
column (`nonempty bench: 0`). That still does **not** mean "infrastructure, mark TRANSLATED" — the
Spec's coverage map reaches BDK via `u d~ ve e+ g g` and `u u~ e- e+ g g`, so these files are
coverage-probeable and can reach VERIFIED. Pair every probe with a known-COVERED positive control
in the same process.

`coverage_check.py` still carries the `cwd=bin` repair on line 33 and `git diff` confirms it is
still the only tracked working-tree change — now uncommitted across five loops. It was again not
committed here: committing a shared tool outside this transformation is a human's call, and the
loop-4 escalation stands rather than being force-resolved on the last loop. The exact upstream
patch, in `run_test`:
`subprocess.run([bin + "/test", "-b", *process], capture_output=True, text=True, cwd=bin)`.
Without it every coverage probe silently returns NOT COVERED.

Carried to human review, all unchanged and none resolvable by an agent: (1) approve the three
waiting groups; (2) commit the `coverage_check.py` `cwd=` fix upstream; (3) rule on whether
`ggZZcapture.cpp` (writes only the `docheck`-guarded `res` buffer that nothing reads back) needs an
explicit exemption from the VERIFIED bar; (4) decide whether `current_plan.md` should carry a
never-translate list for `Mods/types_mod.f` and `Mods/Modules_Interface.f90`, which cost triage at
the top of every candidate list; (5) re-probe `software/mcfm/src/W2jet/w2jetsq.cpp` once its only
caller `src/W2jet/qqb_wp2jetx_new.f` is translated.
