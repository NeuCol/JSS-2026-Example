from pathlib import Path

source = Path("software/mcfm/src/Mods/types_mod.f")
destination = Path("software/mcfm/src/Mods/deprecated/types_mod.f")
source.replace(destination)
