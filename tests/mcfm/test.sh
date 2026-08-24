#!/usr/bin/env bash
# Build MCFM and run the benchmark suite (the stage-1 verification harness).
# Requires $MCFM_HOME (set by environment.sh) and a GNU toolchain (see sites/).
set -e

# Make the harness self-contained. A restricted agent shell cannot run `source`, so if the
# caller's environment is bare we set it up here from this script's own location rather
# than failing on a missing $MCFM_HOME or, worse, silently configuring against the wrong
# compiler. environment.sh only exports paths and the per-site toolchain, so sourcing it
# again when it is already loaded is harmless.
_test_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ -z "$MCFM_HOME" ] || [ -z "$FC" ]; then
  # shellcheck source=/dev/null
  . "$_test_root/environment.sh" > /dev/null
fi
: "${PROJECT_HOME:=$_test_root}"
: "${MCFM_HOME:=$PROJECT_HOME/software/mcfm}"

cd "$MCFM_HOME/Bin"
rm -rf "$MCFM_HOME/install"

make clean || true
# FC/CC/CXX come from sites/$SiteName/config.sh so a machine whose unsuffixed gcc/g++
# are not GNU (e.g. macOS, where they are AppleClang shims MCFM's CMakeLists rejects)
# can name its real GNU toolchain. dev/tools/coverage/coverage_check.py reads the same
# three variables, so both build paths stay on one compiler set.
cmake -DCMAKE_Fortran_COMPILER="${FC:-gfortran}" -DCMAKE_C_COMPILER="${CC:-gcc}" \
      -DCMAKE_CXX_COMPILER="${CXX:-g++}" \
      -DCMAKE_INSTALL_PREFIX="$MCFM_HOME/install" ..
make install

# Benchmark processes, mapped to src/ directories (desired_spec.md §5).
#./test -b u d~ ve e+        # W
#./test -b u d~ ve e+ g      # W1jet
#./test -b u d~ ve e+ g g    # W2jet, BDK, loop
#./test -b u u~ e- e+        # Z
#./test -b u u~ e- e+ g      # Z1jet, loop
#./test -b u u~ e- e+ g g    # Z2jet, W2jet, BDK, loop
#./test -b -Pmodel=heft g g h   # ggH
#./test -b g g h             # ggH
#./test -b d d d d g         # ThreeJets
#./test -b d d~ d d~ g
#./test -b d d~ u u~ g
#./test -b d d~ g g g
#./test -b d u d u g
#./test -b d u~ d u~ g
#./test -b d g g d g
#./test -b d~ d d d~ g
#./test -b d~ d u u~ g
#./test -b d~ d g g g
#./test -b d~ d~ d~ d~ g
#./test -b d~ u u d~ g
#./test -b d~ u~ d~ u~ g
#./test -b d~ g g d~ g
#./test -b u d d u g
#./test -b u~ d~ d~ u~ g
#./test -b g d g d g
#./test -b g d~ g d~ g
#./test -b g g d d~ g
#./test -b g g g g g
#./test -b g g h g g         # gghgg_dep
./bench
