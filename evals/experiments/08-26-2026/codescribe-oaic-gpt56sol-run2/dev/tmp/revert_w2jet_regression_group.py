from pathlib import Path

src = Path("software/mcfm/src/W2jet")
dep = src / "deprecated"
for name in ["ggZZcapture", "ZZbox1LL", "w2jetsq", "a6treeg", "qqbggAxslCoeffs"]:
    original = dep / f"{name}.f"
    if original.exists():
        original.replace(src / original.name)
    for suffix in (".cpp", ".hpp", "_fi.f90"):
        generated = src / f"{name}{suffix}"
        if generated.exists():
            generated.unlink()
