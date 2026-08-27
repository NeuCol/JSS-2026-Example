import os
import subprocess
from pathlib import Path
root=Path.cwd()
os.environ['PROJECT_HOME']=str(root)
os.environ['MCFM_HOME']=str(root/'software/mcfm')
files=['atree.cpp','ggZZcapture.cpp','ZZbox1LL.cpp','a6routine.cpp','a6treeg.cpp']
for name in files:
 print(f'=== {name} ===',flush=True)
 result=subprocess.run(['python3','dev/workflow.py','verify',f'software/mcfm/src/W2jet/{name}','--','u','d~','ve','e+','g','g'])
 print(f'exit_code: {result.returncode}',flush=True)
