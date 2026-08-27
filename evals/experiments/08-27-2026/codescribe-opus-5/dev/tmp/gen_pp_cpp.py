"""Generate the C++ data translation units for pp_mod / ppwp2j_mod.

Reads the original Fortran module (kept in Mods/deprecated) and emits the
translated <base>.cpp holding the same integer table in the same
(column-major) order.
"""
import os
import re

SRC = "software/mcfm/src/Mods"

MODULES = [
    ("pp_mod", "pp", "pp_mod_pp"),
    ("ppwp2j_mod", "pp", "ppwp2j_mod_pp"),
]


def values_of(path):
    text = open(path).read()
    start = text.index("reshape((/")
    end = text.index("/)", start + len("reshape((/"))
    body = text[start + len("reshape((/"):end]
    body = body.replace("&", " ").replace("\n", " ")
    vals = [v.strip() for v in body.split(",") if v.strip()]
    assert len(vals) == 9 * 9 * 9 * 9, (path, len(vals))
    for v in vals:
        assert re.fullmatch(r"-?\d+", v), v
    return vals


def emit(base, var, accessor):
    vals = values_of(os.path.join(SRC, "deprecated", base + ".f90"))
    lines = []
    lines.append("#include <%s.hpp>" % base)
    lines.append("#include <FArray.hpp>")
    lines.append("")
    lines.append("namespace %s {" % base)
    lines.append("  // integer, save :: %s(-4:4,-4:4,-4:4,-4:4) = reshape((/ ... /), (/ 9,9,9,9 /))" % var)
    lines.append("  static int %s_storage[9*9*9*9] = {" % var)
    for i in range(0, len(vals), 27):
        chunk = ", ".join("%2s" % v for v in vals[i:i + 27])
        comma = "," if i + 27 < len(vals) else ""
        lines.append("    " + chunk + comma)
    lines.append("  };")
    lines.append("  FArray4D<int> %s(%s_storage, 9, 9, 9, 9, -4, -4, -4, -4);" % (var, var))
    lines.append("}")
    lines.append("")
    lines.append("extern \"C\" {")
    lines.append("  int* %s() {" % accessor)
    lines.append("    return %s::%s.data;" % (base, var))
    lines.append("  }")
    lines.append("}")
    lines.append("")
    out = os.path.join(SRC, base + ".cpp")
    open(out, "w").write("\n".join(lines))
    print("wrote", out, len(vals), "values")


for base, var, accessor in MODULES:
    emit(base, var, accessor)
