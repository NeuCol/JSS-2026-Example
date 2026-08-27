#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
env = os.environ.copy()
env["MCFM_HOME"] = str(root / "software" / "mcfm")
raise SystemExit(subprocess.run([sys.executable, "dev/workflow.py", "verify", *sys.argv[1:]], cwd=root, env=env).returncode)
