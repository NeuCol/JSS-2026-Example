from pathlib import Path

for path in (
    Path("software/mcfm/src/Mods/pp_mod.f90"),
    Path("software/mcfm/src/Mods/ppwp2j_mod.f90"),
):
    path.unlink()
