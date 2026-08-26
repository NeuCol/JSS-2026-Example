"""Run `dev/workflow.py verify ...` with MCFM_HOME set.

The sandboxed shell cannot `source environment.sh` or set inline env vars, so this
wrapper exports the same paths environment.sh does and forwards its arguments.

    python3 dev/tmp/verify_env.py software/mcfm/src/W2jet/atree.cpp -- u d~ ve e+ g g
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

env = dict(os.environ)
env["PROJECT_HOME"] = ROOT
env["MCFM_HOME"] = os.path.join(ROOT, "software", "mcfm")
env["PEPPER_HOME"] = os.path.join(ROOT, "software", "pepper")
env["QCDLOOP_HOME"] = os.path.join(ROOT, "software", "qcdloop")

cmd = [sys.executable, os.path.join(ROOT, "dev", "workflow.py"), "verify", *sys.argv[1:]]
sys.exit(subprocess.run(cmd, cwd=ROOT, env=env).returncode)
