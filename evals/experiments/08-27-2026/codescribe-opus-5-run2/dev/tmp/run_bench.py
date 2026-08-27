"""Run the built MCFM test binary for one process and print its output.

usage: python3 dev/tmp/run_bench.py <process args...>
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BIN = os.path.join(ROOT, "software", "mcfm", "Bin")
proc = subprocess.run([os.path.join(BIN, "test"), "-b", *sys.argv[1:]],
                      capture_output=True, text=True, cwd=BIN)
print("exit:", proc.returncode)
print(proc.stdout)
print("STDERR:", proc.stderr[-2000:])
