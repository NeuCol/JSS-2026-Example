import os
import sys

os.environ["MCFM_HOME"] = os.path.abspath("software/mcfm")

sys.path.insert(0, os.path.join("dev", "tools", "coverage"))
import coverage_check

target = sys.argv[1]
process = sys.argv[2:]
rc = coverage_check.main([target, "--", *process])
sys.exit(rc)
