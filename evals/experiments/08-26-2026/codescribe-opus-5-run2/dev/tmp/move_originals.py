import os
import shutil

src = "software/mcfm/src/W2jet"
dst = os.path.join(src, "deprecated")
os.makedirs(dst, exist_ok=True)
for name in ["atree.f", "a6treeg.f", "fpp.f", "fvf.f", "subqcd.f"]:
    p = os.path.join(src, name)
    if os.path.isfile(p):
        shutil.move(p, os.path.join(dst, name))
        print("moved", p)
    else:
        print("missing", p)
