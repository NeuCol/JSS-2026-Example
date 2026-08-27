import os
import shutil

src = "software/mcfm/src/W2jet"
dst = os.path.join(src, "deprecated")
os.makedirs(dst, exist_ok=True)
for name in ["atrLLL.f", "atrLRL.f", "faxsl.f", "Ltfunctions.f", "LRcalc.f"]:
    p = os.path.join(src, name)
    if os.path.isfile(p):
        shutil.move(p, os.path.join(dst, name))
        print("moved", p)
    else:
        print("missing", p)
