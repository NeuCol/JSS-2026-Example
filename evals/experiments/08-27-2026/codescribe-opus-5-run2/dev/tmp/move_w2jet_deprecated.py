"""Move the five translated W2jet Fortran originals into W2jet/deprecated/."""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "software", "mcfm", "src", "W2jet")
DEP = os.path.join(SRC, "deprecated")
os.makedirs(DEP, exist_ok=True)

for name in ("atree.f", "a6treeg.f", "fvf.f", "subqcd.f", "ggZZcapture.f"):
    src = os.path.join(SRC, name)
    dst = os.path.join(DEP, name)
    if os.path.isfile(src):
        shutil.move(src, dst)
        print("moved", name)
    elif os.path.isfile(dst):
        print("already in deprecated:", name)
    else:
        print("MISSING:", name)
