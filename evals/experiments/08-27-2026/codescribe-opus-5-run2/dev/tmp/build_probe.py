"""Touch one source file, rebuild MCFM, and print the make output (diagnostic).

usage: python3 dev/tmp/build_probe.py <file>
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MCFM = os.path.join(ROOT, "software", "mcfm")
BIN = os.path.join(MCFM, "Bin")

target = os.path.join(ROOT, sys.argv[1])
os.utime(target, None)
p = subprocess.run(["make", "-C", BIN, "install"], capture_output=True, text=True)
out = p.stdout
lines = [l for l in out.splitlines() if "subqcd" in l or "Linking" in l or "Install" in l.lower()]
print("returncode:", p.returncode)
print("\n".join(lines[:40]))
print("stderr tail:", p.stderr[-1000:])
