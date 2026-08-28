import os
import runpy
import sys

os.environ["MCFM_HOME"] = os.path.abspath("software/mcfm")
sys.argv = ["dev/workflow.py", *sys.argv[1:]]
runpy.run_path("dev/workflow.py", run_name="__main__")
