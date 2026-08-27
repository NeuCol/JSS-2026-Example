import re

def extract(fname):
    with open(fname) as f:
        text = f.read()
    m = re.search(r"reshape\(\(/(.*?)/\)[\s&]*,[\s&]*\(/\s*([0-9,\s]+?)\s*/\)\)", text, re.S)
    if not m:
        raise SystemExit("no match in " + fname)
    data_str = m.group(1)
    shape_str = m.group(2)
    data_str = data_str.replace("&", " ")
    nums = [x.strip() for x in data_str.split(",") if x.strip() != ""]
    shape = [int(x.strip()) for x in shape_str.split(",") if x.strip() != ""]
    n = 1
    for s in shape:
        n *= s
    assert len(nums) == n, (len(nums), n, fname)
    return nums, shape

def format_block(nums, per_line=20, indent="    "):
    lines = []
    for i in range(0, len(nums), per_line):
        chunk = ", ".join(nums[i:i+per_line])
        lines.append(indent + chunk + ",")
    # remove trailing comma on very last entry
    lines[-1] = lines[-1].rstrip(",")
    return "\n".join(lines)

def gen(modname, fname):
    nums, shape = extract(fname)
    body = format_block(nums)
    cpp = f"""/*
 * Translated from {fname.split('/')[-1]}
 */
#include "{modname}.hpp"

namespace {modname} {{

  namespace {{
    const int pp_init_data[{len(nums)}] = {{
{body}
    }};
  }}

  FArray4D<int> pp(9, 9, 9, 9, -4, -4, -4, -4);

  namespace {{
    struct PPInitializer {{
      PPInitializer() {{
        for (size_t idx = 0; idx < {len(nums)}; ++idx) {{
          pp.data[idx] = pp_init_data[idx];
        }}
      }}
    }} pp_initializer_instance;
  }}

}}
"""
    return cpp

for modname, fname in [("pp_mod", "software/mcfm/src/Mods/pp_mod.f90"),
                        ("ppwp2j_mod", "software/mcfm/src/Mods/ppwp2j_mod.f90")]:
    cpp = gen(modname, fname)
    outname = f"software/mcfm/src/Mods/{modname}.cpp"
    with open(outname, "w") as f:
        f.write(cpp)
    print("wrote", outname, len(cpp), "bytes")
