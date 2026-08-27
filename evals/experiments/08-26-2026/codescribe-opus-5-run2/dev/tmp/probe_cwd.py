#!/usr/bin/env python3
"""Run Bin/test from the project ROOT (as coverage_check.py does) and report output size."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "software" / "mcfm" / "Bin" / "test"
r = subprocess.run([str(BIN), "-b", *sys.argv[1:]], cwd=str(ROOT),
                   capture_output=True, text=True)
print("rc =", r.returncode)
print("stdout bytes =", len(r.stdout))
for line in r.stdout.splitlines():
    if "MCFM =" in line or "ratio" in line or "PASSED" in line or "FAILED" in line:
        print(line)
print("stderr tail:", r.stderr[-500:])
