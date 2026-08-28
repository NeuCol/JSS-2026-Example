"""Run `dev/workflow.py verify` with MCFM_HOME set (bash tool cannot source environment.sh)."""
import os
import subprocess
import sys

os.environ.setdefault("MCFM_HOME", os.path.abspath("software/mcfm"))
target = sys.argv[1]
process = sys.argv[2:] or ["u", "d~", "ve", "e+", "g", "g"]
cmd = ["python3", "dev/workflow.py", "verify", target, "--"] + process
print("running:", " ".join(cmd))
sys.exit(subprocess.run(cmd).returncode)
