#!/usr/bin/env python3
"""Rebuild MCFM in software/mcfm/Bin and run `test -b <process>`; summarise output."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "software" / "mcfm" / "Bin"
b = subprocess.run(["make", "-C", str(BIN), "install"], capture_output=True, text=True)
print("build rc =", b.returncode)
if b.returncode != 0:
    print(b.stdout[-4000:])
    print(b.stderr[-4000:])
    sys.exit(b.returncode)
r = subprocess.run([str(BIN / "test"), "-b", *sys.argv[1:]], cwd=str(BIN),
                   capture_output=True, text=True)
out = r.stdout
print("test rc =", r.returncode)
for line in out.splitlines():
    if "MCFM =" in line or "ratio" in line or "PASSED" in line or "FAILED" in line:
        print(line)
marks = [l for l in r.stderr.splitlines() if "PROBE_CALLED" in l]
print("stderr PROBE_CALLED count =", len(marks))
