import os, shutil

src = "software/mcfm/src/W2jet"
dst = os.path.join(src, "deprecated")
os.makedirs(dst, exist_ok=True)
for f in ["atree.f", "a6treeg.f", "fvf.f", "subqcd.f", "ZZbox1LL.f"]:
    p = os.path.join(src, f)
    if os.path.isfile(p):
        shutil.move(p, os.path.join(dst, f))
        print("moved", f)
    else:
        print("missing", f)
