import shutil
import pathlib
import sys

base = pathlib.Path("software/mcfm/src/W2jet")
dep = base / "deprecated"
dep.mkdir(exist_ok=True)
names = sys.argv[1:] or ["atree.f", "a6treeg.f", "fvf.f", "subqcd.f", "ZZbox1LL.f"]
for name in names:
    src = base / name
    if src.exists():
        shutil.move(str(src), str(dep / name))
        print("moved", name)
    else:
        print("absent", name)
