from pathlib import Path
for name in ("a6treeg.f", "subqcd.f"):
    source = Path("software/mcfm/src/W2jet") / name
    if source.exists():
        target = source.parent / "deprecated" / name
        target.parent.mkdir(exist_ok=True)
        source.rename(target)
