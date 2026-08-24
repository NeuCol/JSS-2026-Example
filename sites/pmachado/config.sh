# macOS (arm64), MPI via Homebrew. No module system, no CUDA/NVHPC on this machine.

export MPI_HOME=$(which mpicc | sed s/'\/bin\/mpicc'//)

# dev/tools needs Python >= 3.11 (tomllib, used by dev/tools/common/approval_log.py), and
# the Plan tells agents to invoke it as plain `python3`. macOS ships 3.9.6 at
# /usr/bin/python3, which /usr/bin puts ahead of the miniforge 3.13 already on PATH, so
# reorder rather than add. The only tool this shadows is a bare `gfortran`; FC below names
# gfortran-16 explicitly, which miniforge does not provide, so the build is unaffected.
export PATH="/opt/homebrew/Caskroom/miniforge/base/bin:$PATH"

# MCFM's CMakeLists.txt accepts only GNU (or Intel) for C, C++ and Fortran, and adds
# -fopenmp to all three. On macOS the unsuffixed gcc/g++ are AppleClang shims, which
# CMake rejects with "Unsupported C++ compiler AppleClang", so point at Homebrew GCC.
# tests/mcfm/test.sh and dev/tools/coverage/coverage_check.py both honour FC/CC/CXX.
export FC=gfortran-16
export CC=gcc-16
export CXX=g++-16

# The miniforge base environment exports Clang-targeted build flags (CXXFLAGS carries
# -stdlib=libc++, which GNU g++ does not accept, and everything gets -isystem
# $CONDA_PREFIX/include plus conda's -L/-rpath in LDFLAGS). CMake picks these up as the
# initial CMAKE_<LANG>_FLAGS and forwards them into MCFM's bundled qcdloop
# ExternalProject, where they break the libstdc++ header search outright:
#   fatal error: vector: No such file or directory
# Clear them so MCFM builds against the Homebrew GCC toolchain named above. This is
# scoped to shells that source environment.sh; it does not touch the conda install.
unset CFLAGS CXXFLAGS FFLAGS FCFLAGS CPPFLAGS LDFLAGS DEBUG_CFLAGS DEBUG_CXXFLAGS DEBUG_FFLAGS

# MCFM's bundled qcdloop uses __float128, so it needs libquadmath (sqrtq,
# quadmath_snprintf). Its CMakeLists does not add -lquadmath, which is fine with the
# glibc toolchains it was written for but leaves libqcdloop.dylib with undefined
# symbols when linking on macOS. Homebrew GCC ships libquadmath next to its own
# runtime, so the bare -l is enough; no -L is needed. CMake seeds the exe, shared and
# module linker flags from LDFLAGS at first configure, and the qcdloop ExternalProject
# inherits it through the environment.
export LDFLAGS="-lquadmath"

# Numerical reproducibility. On aarch64 GCC defaults to -ffp-contract=fast, which fuses
# a*b+c into a single FMA with one rounding instead of two. In MCFM's long amplitude
# expressions that shifts results by a few times 1e-13, and the benchmark tolerance is
# 1e-13, so two gghgg_dep cases (d d~ h g g, d~ d h g g) miss the bar on an otherwise
# untouched tree. Turning contraction off reproduces the reference 272/272.
export FFLAGS="-ffp-contract=off"
export CFLAGS="-ffp-contract=off"
export CXXFLAGS="-ffp-contract=off"

# Homebrew ships CMake 4.x, which dropped compatibility with cmake_minimum_required
# < 3.5. MCFM's bundled lib/qcdloop-2.0.5 still declares one, and it is configured as
# an ExternalProject, so the flag has to reach a nested cmake we do not invoke
# ourselves. CMake 4.0+ reads this as an environment variable, which the sub-configure
# inherits. Only relaxes the policy floor; it does not change compiler flags.
export CMAKE_POLICY_VERSION_MINIMUM=3.5

#module load nvhpc-nompi/21.3
#module load nvhpc/21.3

# Set NVHPC_HOME by quering path
#export NVHPC_HOME=$(which nvcc | sed s/'\/bin\/nvcc'//)
