from pathlib import Path
source = Path("software/mcfm/src/Mods/mod_qcdloop_c_fi.F90")
target = source.with_suffix(".f")
target.write_text(source.read_text())
source.unlink()
