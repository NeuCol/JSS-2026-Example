"""Run `dev/workflow.py verify` with MCFM_HOME set (the agent shell cannot `source`).

usage: python3 dev/tmp/run_verify.py <target.cpp> -- <process args>
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env = dict(os.environ)
env["PROJECT_HOME"] = ROOT
env["MCFM_HOME"] = os.path.join(ROOT, "software", "mcfm")
env["PEPPER_HOME"] = os.path.join(ROOT, "software", "pepper")
env["QCDLOOP_HOME"] = os.path.join(ROOT, "software", "qcdloop")

cmd = [sys.executable, os.path.join(ROOT, "dev", "workflow.py"), "verify", *sys.argv[1:]]
print("+ " + " ".join(cmd), flush=True)
sys.exit(subprocess.run(cmd, cwd=ROOT, env=env).returncode)
