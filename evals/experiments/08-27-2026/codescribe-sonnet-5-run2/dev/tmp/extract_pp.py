import re

def extract(fname, outname):
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
    lines = []
    for i in range(0, len(nums), 20):
        chunk = ", ".join(nums[i:i+20])
        if i + 20 < len(nums):
            chunk += ","
        lines.append("    " + chunk)
    body = "\n".join(lines)
    print(fname, "-> total", len(nums), "shape", shape)
    with open(outname, "w") as f:
        f.write(body)

extract("software/mcfm/src/Mods/pp_mod.f90", "dev/tmp/pp_data.txt")
extract("software/mcfm/src/Mods/ppwp2j_mod.f90", "dev/tmp/ppwp2j_data.txt")
