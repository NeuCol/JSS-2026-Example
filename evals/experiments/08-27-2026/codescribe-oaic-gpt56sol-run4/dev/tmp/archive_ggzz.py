from pathlib import Path
p=Path("software/mcfm/src/W2jet/ggZZcapture.f")
p.rename(p.parent / "deprecated" / p.name)
