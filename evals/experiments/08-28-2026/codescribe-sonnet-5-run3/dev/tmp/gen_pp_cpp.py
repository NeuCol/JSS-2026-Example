import sys

def gen(data_path, out_path, mod_name):
    with open(data_path) as f:
        data = f.read().rstrip("\n")
    # strip trailing comma on the very last data line, if present
    lines = data.split("\n")
    lines[-1] = lines[-1].rstrip(",")
    data = "\n".join(lines)

    header = f"""#include <{mod_name}.hpp>

namespace {mod_name} {{

  namespace {{
    const int pp_flat[9 * 9 * 9 * 9] = {{
{data}
    }};
  }}

  FArray4D<int> pp(9, 9, 9, 9, -4, -4, -4, -4);

  namespace {{
    struct PPInit {{
      PPInit() {{
        for (size_t idx = 0; idx < 9u * 9u * 9u * 9u; ++idx) {{
          pp.data[idx] = pp_flat[idx];
        }}
      }}
    }} pp_init;
  }}

}}
"""
    with open(out_path, "w") as f:
        f.write(header)

if __name__ == "__main__":
    gen(sys.argv[1], sys.argv[2], sys.argv[3])
