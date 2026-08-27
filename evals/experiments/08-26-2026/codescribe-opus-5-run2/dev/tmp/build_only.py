#!/usr/bin/env python3
"""Rebuild MCFM in software/mcfm/Bin only; print rc and the tail of the log."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "software" / "mcfm" / "Bin"
b = subprocess.run(["make", "-C", str(BIN), "install"], capture_output=True, text=True)
print("build rc =", b.returncode)
if b.returncode != 0:
    print(b.stdout[-6000:])
    print(b.stderr[-6000:])
    sys.exit(b.returncode)
print(b.stdout[-800:])
