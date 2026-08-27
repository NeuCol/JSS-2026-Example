from pathlib import Path

root = Path("software/mcfm/src/Mods")
deprecated = root / "deprecated"

# Modules_Interface remains responsible for sequencing the Fortran module pointer
# shims, but its externally visible entry points are now defined in C++.
source = root / "Modules_Interface.f90"
original = source.read_text()
(deprecated / "Modules_Interface.f90").write_text(original)
shim = original.replace(
    'subroutine modules_fi_init() bind(C, name="modules_fi_init_")',
    'subroutine modules_fi_init_impl() bind(C, name="modules_fi_init_impl")',
).replace(
    'end subroutine modules_fi_init',
    'end subroutine modules_fi_init_impl',
).replace(
    'subroutine modules_fi_finalize() bind(C, name="modules_fi_finalize_")',
    'subroutine modules_fi_finalize_impl() bind(C, name="modules_fi_finalize_impl")',
).replace(
    'end subroutine modules_fi_finalize',
    'end subroutine modules_fi_finalize_impl',
)
(root / "Modules_Interface_fi.F90").write_text(shim)
source.unlink()
(root / "Modules_Interface.hpp").write_text('''#ifndef MODULES_INTERFACE_HPP
#define MODULES_INTERFACE_HPP

void modules_fi_init();
void modules_fi_finalize();

extern "C" void modules_fi_init_();
extern "C" void modules_fi_finalize_();

#endif
''')
(root / "Modules_Interface.cpp").write_text('''#include <Modules_Interface.hpp>

extern "C" void modules_fi_init_impl();
extern "C" void modules_fi_finalize_impl();

void modules_fi_init() {
    modules_fi_init_impl();
}

void modules_fi_finalize() {
    modules_fi_finalize_impl();
}

extern "C" void modules_fi_init_() {
    modules_fi_init(); // @coverage-probe
}

extern "C" void modules_fi_finalize_() {
    modules_fi_finalize();
}
''')

# This source is itself only a Fortran declaration module for QCDLoop's C API.
# Preserve that API as the required shim and provide the C++ declaration point.
source = root / "mod_qcdloop_c.f"
original = source.read_text()
(deprecated / "mod_qcdloop_c.f").write_text(original)
(root / "mod_qcdloop_c_fi.F90").write_text(original)
source.unlink()
(root / "mod_qcdloop_c.hpp").write_text('''#ifndef MOD_QCDLOOP_C_HPP
#define MOD_QCDLOOP_C_HPP

#include <complex>

namespace mod_qcdloop_c {
using complex = std::complex<double>;

extern "C" {
void qlcachesize(const int& csize);
complex cln(const complex& x, const double& isig);
bool qlzero(const double& x);
bool qlnonzero(const double& x);
complex qli1(const double& m1, const double& mu2, const int& ep);
complex qli1c(const complex& m1, const double& mu2, const int& ep);
complex qli2(const double& p1, const double& m1, const double& m2, const double& mu2, const int& ep);
complex qli2c(const double& p1, const complex& m1, const complex& m2, const double& mu2, const int& ep);
complex qli2p(const double& p1, const double& m1, const double& m2, const double& mu2, const int& ep);
complex qli2pc(const double& p1, const complex& m1, const complex& m2, const double& mu2, const int& ep);
complex qli3(const double& p1, const double& p2, const double& p3, const double& m1, const double& m2, const double& m3, const double& mu2, const int& ep);
complex qli3c(const double& p1, const double& p2, const double& p3, const complex& m1, const complex& m2, const complex& m3, const double& mu2, const int& ep);
complex qli4(const double& p1, const double& p2, const double& p3, const double& p4, const double& s12, const double& s23, const double& m1, const double& m2, const double& m3, const double& m4, const double& mu2, const int& ep);
complex qli4c(const double& p1, const double& p2, const double& p3, const double& p4, const double& s12, const double& s23, const complex& m1, const complex& m2, const complex& m3, const complex& m4, const double& mu2, const int& ep);
}
}

#endif
''')
(root / "mod_qcdloop_c.cpp").write_text('''#include <mod_qcdloop_c.hpp>

// QCDLoop owns the C-linkage definitions.  This translated declaration module
// supplies the normal C++ header consumed by translated callers.
''')

cmake = root / "CMakeLists.txt"
text = cmake.read_text()
text = text.replace("mod_qcdloop_c.f\n", "mod_qcdloop_c_fi.F90\nmod_qcdloop_c.cpp\n")
text = text.replace("Modules_Interface.f90\n", "Modules_Interface_fi.F90\nModules_Interface.cpp\n")
cmake.write_text(text)
