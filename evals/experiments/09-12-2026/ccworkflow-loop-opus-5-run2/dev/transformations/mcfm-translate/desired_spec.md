# Fortran → C++: target output for one MCFM file

This file defines the rewrite target and correctness bar for step 1. The workflow lives in
`current_plan.md`.

Paths are written as `software/mcfm/src/...`.

---

## Contract

This step advances by *settling* source files one at a time: each file is rewritten, then
recorded in `agent_log.md` with a status `σ` once the oracle `V` confirms the invariants `I`
still hold. A file is ready when its callees are already available in C++.

Objective `f`. Translate every source file to verified C++. Progress = fraction VERIFIED of
translatable files (`python3 dev/workflow.py status`).

Invariants `I` (hold after every settled unit):

- The restored build passes and matches to 1e-13.
- No called symbol is invented; each `.cpp` includes its own header; cross-unit calls go
  through headers, not translation-era forward declarations.

Oracle `V`. `jobrunner submit tests/mcfm` + coverage probe (`python3 dev/workflow.py verify`).

Status set `Σ`.

| σ          | class | reversible | runner sets | evidence in log              |
|------------|-------|------------|-------------|------------------------------|
| VERIFIED   | good  | yes        | yes         | covered + worst Δrel ≤ 1e-13 |
| TRANSLATED | good  | yes        | yes         | build pass (not covered)     |
| FAILED     | bad   | —          | yes         | symptom                      |

Risky `σ` = FAILED. Up to 3 completed groups may accumulate before approval. The sections
below elaborate this contract; on conflict the contract governs.

---

## Output shape

One Fortran file becomes one C++ translation unit set, and the folder's `CMakeLists.txt` swaps
its `.f`/`.f90` entry for the new files:

- **`<base>.cpp`** — translated code plus `extern "C" <base>_wrapper(...)`; when a matching header exists, this file should include `<base>.hpp>`
- **`<base>.hpp`** — direct C++ declaration for the translated C++ entry points used outside the translation unit
- **`<base>_fi.F90`** — Fortran shim with the original entry name calling the wrapper

A Fortran module instead becomes a `.hpp`, a `.cpp`, and a `_fi.f90` that mirrors variables via
`c_f_pointer`. Follow existing rewritten modules in `src/Mods`.

## Rewrite rules

Rewrite line by line. Do not add a `main`, extra declarations, or invented names.

| Fortran | C++ |
|---|---|
| `subroutine`/`function` | free function + `<name>_wrapper` in `extern "C"`; declare the reusable C++ function in `<base>.hpp` when it is used outside its own `.cpp` |
| `use <mod>` | `#include <mod.hpp>` + `using namespace <mod>;` |
| `real(dp)` / `complex(dp)` | `double` / `std::complex<double>` |
| `dimension(nx,ny)` array | `FArray2D<double> a(nx, ny)` |
| `intent(in/inout)` scalar | pass by reference |
| statement function | C++ lambda |
| `x**n` | `pow(x, n)` |
| `return` | `return;` |

### Never invent a called symbol

Keep every call already present in the source.

- If the callee is already rewritten, include its `.hpp` and call the C++ function.
- If the callee is still Fortran, declare the plain Fortran symbol in `extern "C"` and call it
  with pointer arguments.
- If a needed module dependency has no usable C binding yet, stop and rewrite that dependency
  first.

The readiness map exists so a file is only rewritten when its callees are already available.
Use the Draft tool's hints and seed examples when needed.

## Header / source structure

Follow normal C++ structure for translated code.

1. If a translated unit has a `<base>.hpp`, the matching `<base>.cpp` should include it as the normal declaration point for that unit's C++ interface.
2. Treat the generated header/source pair as the default structure for translated C++: declarations live in the header, definitions live in the `.cpp`, and the `.cpp` includes its own header.
3. If one translated `.cpp` calls a C++ function defined in another translated `.cpp`, include the callee's header rather than adding a local forward declaration.
4. Use local forward declarations only when there is intentionally no reusable header yet and introducing one would not make the interface clearer.
5. Put declarations for reusable cross-translation-unit C++ functions in headers before they are used from other `.cpp` files.
6. Keep `extern "C"` declarations only for true Fortran or C interoperability boundaries, not as a substitute for ordinary C++ headers.

## Silent traps

Check these explicitly:

1. Dropped calls, especially near-duplicate paired calls.
2. Missing parentheses around denominators after translating chained `*` and `/`.
3. Wrong `FArray` sizes or bounds.
4. Accidental 0-based indexing for 1-based Fortran arrays.
5. Missing module or `Need.hpp` includes.
6. A translated `.cpp` failing to include its own matching header when one exists.
7. Calling a translated C++ sibling without including its header when one exists.
8. Keeping translation-era forward declarations even though a proper header interface exists.
9. **Silent segfault**: the test process crashes without printing output, leaving no `FAILED` marker but also no `passed` marker. A test is only acceptable if each individual test case is confirmed **passed** in the output — the absence of `FAILED` is not sufficient.

If numbers still disagree after checking, mark the file `FAILED` with the symptom.

---

## Coverage map

A file is only verified if a test actually runs it.

One representative process per directory for coverage probing. `software/mcfm/Bin/bench` is the
exhaustive runner and covers many more variants per directory.

| Process | Directory |
|---------|-----------|
| `u d~ ve e+` | W |
| `u d~ ve e+ g` | W1jet |
| `u d~ ve e+ g g` | W2jet / BDK / loop |
| `u u~ e- e+` | Z |
| `u u~ e- e+ g` | Z1jet / loop |
| `u u~ e- e+ g g` | Z2jet / W2jet / BDK / loop |
| `-Pmodel=heft g g h` | ggH |
| `g g h` | ggH |
| `g g g g g` | ThreeJets (any variant works) |
| `g g h g g` | gghgg_dep |
| — | Mods / Need / Inc / Procdep — infrastructure, mark `TRANSLATED` |

This mapping is also built into `dev/tools/index/build_roadmap.py`.

---

## Correctness bar

A passing MCFM test must match to **1e-13**. That alone is not enough: the test must also be
shown to exercise the rewritten file via `dev/tools/coverage/coverage_check.py`.

Each test case must explicitly show **passed** in its output. Confirming the absence of `FAILED`
is not sufficient — a silent segfault produces no output at all and would pass that check
incorrectly. If any test case does not show a `passed` result, treat it as `FAILED`.

The status set `Σ`, its classes, reversibility, and required evidence are defined once in the
`## Contract` above. Record results in `agent_log.md`, not here.
