#!/usr/bin/env python3
"""Run the coverage oracle (`dev/tools/coverage/coverage_check.py`) for one file.

The sandboxed shell cannot `source environment.sh` or set env vars inline, so this
wrapper sets MCFM_HOME exactly as environment.sh does and forwards the arguments.

It also runs the checker with cwd = $MCFM_HOME/Bin, which is what tests/mcfm/test.sh
does (`cd "$MCFM_HOME/Bin"`).  The MCFM `test` binary only finds its input files when
it is started from that directory; started from the project root it exits with rc=1
and prints an identical error banner for the baseline and the probed build, which
made every file look `NOT COVERED`.  The target path is made absolute so the checker
still finds the source file from that working directory.

Usage: python3 dev/tmp/run_verify.py <file.cpp> -- <process args>
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MCFM = ROOT / "software" / "mcfm"
CHECKER = ROOT / "dev" / "tools" / "coverage" / "coverage_check.py"

args = list(sys.argv[1:])
if args:
    args[0] = str((ROOT / args[0]).resolve()) if not os.path.isabs(args[0]) else args[0]

env = dict(os.environ)
env["MCFM_HOME"] = str(MCFM)
cmd = [sys.executable, str(CHECKER), *args]
print("+ coverage_check.py " + " ".join(args) + "   (cwd=" + str(MCFM / "Bin") + ")")
sys.exit(subprocess.run(cmd, cwd=str(MCFM / "Bin"), env=env).returncode)
