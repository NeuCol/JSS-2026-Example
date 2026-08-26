import os
import shutil

base = "software/mcfm/src/W2jet"
dep = os.path.join(base, "deprecated")
os.makedirs(dep, exist_ok=True)
for name in ["atrLLL.f", "atrLRL.f", "Acalc.f", "faxsl.f", "LRcalc.f"]:
    src = os.path.join(base, name)
    dst = os.path.join(dep, name)
    if os.path.exists(src):
        shutil.move(src, dst)
        print("moved", src, "->", dst)
    else:
        print("missing", src)
