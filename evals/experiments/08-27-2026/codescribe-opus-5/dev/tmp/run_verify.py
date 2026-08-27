"""Run `dev/workflow.py verify` with MCFM_HOME/PROJECT_HOME set.

coverage_check.py requires MCFM_HOME (normally exported by
`software/mcfm/environment.sh`); without it the tool dies with exit 2
("set MCFM_HOME first"). This wrapper sets it and forwards the child's
exit code so the caller sees the real result (0 covered, 1 not covered,
2 usage/setup error).
"""
import os
import subprocess
import sys

root = os.path.abspath(".")
env = dict(os.environ)
env.setdefault("PROJECT_HOME", root)
env["MCFM_HOME"] = os.path.join(root, "software", "mcfm")

cmd = [sys.executable, "dev/workflow.py", "verify"] + sys.argv[1:]
print("RUN:", " ".join(cmd))
res = subprocess.run(cmd, env=env)
print("exit:", res.returncode)
sys.exit(res.returncode)
