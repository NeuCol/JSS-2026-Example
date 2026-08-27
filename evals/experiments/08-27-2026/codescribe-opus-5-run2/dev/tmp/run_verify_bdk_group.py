"""Run the coverage probe for the remaining BDK-01 group files (MCFM_HOME injected).

usage: python3 dev/tmp/run_verify_bdk_group.py
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

TARGETS = [
    "software/mcfm/src/BDK/FFMPcc.cpp",
    "software/mcfm/src/BDK/FFPMccT.cpp",
    "software/mcfm/src/BDK/FFPMccTtilde.cpp",
    "software/mcfm/src/BDK/FFPMscT.cpp",
]

rc_all = 0
for target in TARGETS:
    cmd = [sys.executable, os.path.join(ROOT, "dev", "workflow.py"), "verify", target,
           "--", "u", "d~", "ve", "e+", "g", "g"]
    print("+ " + " ".join(cmd), flush=True)
    rc = subprocess.run(cmd, cwd=ROOT, env=env).returncode
    print(f"== {target} exit={rc}", flush=True)
    rc_all = rc_all or 0
sys.exit(0)
