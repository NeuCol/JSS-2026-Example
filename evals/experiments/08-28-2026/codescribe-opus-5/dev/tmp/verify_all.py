"""Run the coverage probe for the current group's translated files, sequentially."""
import os
import subprocess

os.environ.setdefault("MCFM_HOME", os.path.abspath("software/mcfm"))
targets = [
    "software/mcfm/src/W2jet/subqcd.cpp",
    "software/mcfm/src/W2jet/Acalc.cpp",
    "software/mcfm/src/W2jet/LRcalc.cpp",
    "software/mcfm/src/W2jet/fpp.cpp",
    "software/mcfm/src/W2jet/vv.cpp",
]
for t in targets:
    cmd = ["python3", "dev/workflow.py", "verify", t, "--", "u", "d~", "ve", "e+", "g", "g"]
    print("### running:", " ".join(cmd), flush=True)
    r = subprocess.run(cmd)
    print("### exit code:", r.returncode, flush=True)
