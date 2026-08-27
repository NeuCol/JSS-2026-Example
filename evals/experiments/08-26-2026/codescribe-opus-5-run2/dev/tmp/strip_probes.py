#!/usr/bin/env python3
"""Remove every `// @coverage-probe` marker from the translated W2jet .cpp files."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "software" / "mcfm" / "src" / "W2jet"
names = ["atrLLL", "atrLRL", "faxsl", "Ltfunctions", "LRcalc",
         "subqcd", "a6treeg", "atree", "fpp", "fvf"]
for n in names:
    p = D / (n + ".cpp")
    text = p.read_text()
    new = re.sub(r"[ \t]*//[ \t]*@coverage-probe[ \t]*(?=\n|$)", "", text)
    if new != text:
        p.write_text(new)
        print("stripped:", p.relative_to(ROOT))
    else:
        print("no marker:", p.relative_to(ROOT))
