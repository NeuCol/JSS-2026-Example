from pathlib import Path
import re

root = Path("software/mcfm/src/Mods")
for base in ("pp_mod", "ppwp2j_mod"):
    source = (root / f"{base}.f90").read_text()
    body = source.split("reshape((/", 1)[1].split("/)", 1)[0]
    values = [int(value) for value in re.findall(r"-?\d+", body)]
    if len(values) != 9 ** 4:
        raise RuntimeError(f"{base}: expected 6561 entries, got {len(values)}")

    wrapped = []
    for start in range(0, len(values), 18):
        wrapped.append("    " + ", ".join(map(str, values[start:start + 18])))
    initializer = ",\n".join(wrapped)

    (root / f"{base}.hpp").write_text(f'''#ifndef {base.upper()}_HPP
#define {base.upper()}_HPP

#include <array>

namespace {base} {{
inline constexpr int extent = 9;
inline constexpr int size = extent * extent * extent * extent;
extern std::array<int, size> pp;
}}

extern "C" int* {base}_pp();

#endif
''')
    (root / f"{base}.cpp").write_text(f'''#include <{base}.hpp>

namespace {base} {{
std::array<int, size> pp = {{{{
{initializer}
}}}};
}}

extern "C" int* {base}_pp() {{
    return {base}::pp.data(); // @coverage-probe
}}
''')
    (root / f"{base}_fi.F90").write_text(f'''module {base}
  use, intrinsic :: iso_c_binding
  implicit none

  private
  public :: pp

  integer(c_int), pointer :: pp(:,:,:,:) => null()

  interface
    function {base}_pp() bind(C, name="{base}_pp") result(address)
      import :: c_ptr
      type(c_ptr) :: address
    end function {base}_pp
  end interface

contains
  subroutine {base}_initialize()
    integer(c_int), pointer :: storage(:,:,:,:)
    call c_f_pointer({base}_pp(), storage, [9, 9, 9, 9])
    pp(-4:4,-4:4,-4:4,-4:4) => storage
  end subroutine {base}_initialize

  subroutine {base}_finalize()
    nullify(pp)
  end subroutine {base}_finalize
end module {base}
''')

    # Module initialization is required before ordinary Fortran users access pp.
    # A DATA-initialized pointer cannot call C, so expose explicit init/finalize
    # and add them to the central bridge in a subsequent edit.
