from pathlib import Path

root = Path("software/mcfm/src/BDK")
destination = root / "deprecated"
destination.mkdir(exist_ok=True)
for name in ("M2bit1.f", "M2bit2.f", "M2bit3.f"):
    (root / name).replace(destination / name)
