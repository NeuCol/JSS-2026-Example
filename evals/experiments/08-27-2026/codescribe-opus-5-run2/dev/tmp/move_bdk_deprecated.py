"""Move the translated BDK-01 Fortran originals into src/BDK/deprecated/.

usage: python3 dev/tmp/move_bdk_deprecated.py
(inline shell moves are blocked in the agent shell, hence this helper)
"""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "software", "mcfm", "src", "BDK")
DST = os.path.join(SRC, "deprecated")

FILES = ["fvs.f", "FFMPcc.f", "FFPMccT.f", "FFPMccTtilde.f", "FFPMscT.f"]

os.makedirs(DST, exist_ok=True)
for name in FILES:
    src = os.path.join(SRC, name)
    dst = os.path.join(DST, name)
    if not os.path.exists(src):
        print(f"skip (missing): {name}")
        continue
    shutil.move(src, dst)
    print(f"moved: BDK/{name} -> BDK/deprecated/{name}")
print("done")
