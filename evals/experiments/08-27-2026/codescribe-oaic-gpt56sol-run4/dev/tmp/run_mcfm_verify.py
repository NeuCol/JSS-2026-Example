import os
import subprocess
import sys

os.environ["MCFM_HOME"] = os.path.abspath("software/mcfm")
raise SystemExit(subprocess.call([sys.executable, "dev/workflow.py", "verify", *sys.argv[1:]]))
