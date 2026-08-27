#!/usr/bin/env python3
"""Run the MCFM `test -b <process>` binary once and print its stdout."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "software" / "mcfm" / "Bin" / "test"
r = subprocess.run([str(BIN), "-b", *sys.argv[1:]], cwd=str(BIN.parent),
                   capture_output=True, text=True)
print("rc =", r.returncode)
print("--- stdout ---")
print(r.stdout)
print("--- stderr ---")
print(r.stderr[-2000:])
