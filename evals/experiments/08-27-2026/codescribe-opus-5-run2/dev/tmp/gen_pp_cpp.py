"""Generate the C++ data translation unit for a Fortran pp-table module.

Usage: python3 dev/tmp/gen_pp_cpp.py <fortran-module> <namespace> <out.cpp>
"""
import re
import sys


def main():
    src, ns, out = sys.argv[1], sys.argv[2], sys.argv[3]
    text = open(src).read()
    start = text.index("reshape((/")
    end = text.index("/)", start + len("reshape((/"))
    body = text[start + len("reshape((/"):end]
    body = body.replace("&", " ").replace("\n", " ")
    values = [v.strip() for v in body.split(",") if v.strip()]
    if len(values) != 9 * 9 * 9 * 9:
        raise SystemExit("unexpected element count: %d" % len(values))

    lines = []
    for i in range(0, len(values), 27):
        lines.append("    " + ", ".join("%2s" % v for v in values[i:i + 27]) + ",")
    lines[-1] = lines[-1][:-1]

    with open(out, "w") as fh:
        fh.write("#include <%s.hpp>\n\n" % ns)
        fh.write("namespace %s {\n" % ns)
        fh.write("  // Fortran reshape() data, in column-major (Fortran) storage order.\n")
        fh.write("  static const int pp_values[9*9*9*9] = {\n")
        fh.write("\n".join(lines))
        fh.write("\n  };\n\n")
        fh.write("  FArray4D<int> pp(9, 9, 9, 9, -4, -4, -4, -4);\n\n")
        fh.write("  static bool fill_pp() {\n")
        fh.write("    for (int n = 0; n < 9*9*9*9; n++) {\n")
        fh.write("      pp.data[n] = pp_values[n];\n")
        fh.write("    }\n")
        fh.write("    return true;\n")
        fh.write("  }\n\n")
        fh.write("  static const bool pp_filled = fill_pp();\n")
        fh.write("}\n\n")
        fh.write("extern \"C\" {\n")
        fh.write("  int* %s_pp() {\n" % ns)
        fh.write("    return %s::pp.data;\n" % ns)
        fh.write("  }\n")
        fh.write("}\n")
    print("wrote %s (%d values)" % (out, len(values)))


main()
