"""Move the Group 3 W2jet originals into deprecated/ (no `mv` in the restricted shell)."""
import os
import shutil

src = "software/mcfm/src/W2jet"
dst = os.path.join(src, "deprecated")
os.makedirs(dst, exist_ok=True)
for name in ["subqcd.f", "Acalc.f", "LRcalc.f", "fpp.f", "vv.f"]:
    s = os.path.join(src, name)
    if os.path.exists(s):
        shutil.move(s, os.path.join(dst, name))
        print("moved", s)
    else:
        print("missing", s)
