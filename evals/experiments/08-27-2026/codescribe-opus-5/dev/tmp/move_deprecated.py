import shutil
import pathlib

base = pathlib.Path("software/mcfm/src/Mods")
dep = base / "deprecated"
for name in ["types_mod.f", "mod_qcdloop_c.f"]:
    src = base / name
    if src.exists():
        shutil.move(str(src), str(dep / name))
        print("moved", name)
    else:
        print("absent", name)
