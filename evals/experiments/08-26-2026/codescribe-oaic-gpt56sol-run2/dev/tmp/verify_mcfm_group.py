import os, subprocess
from pathlib import Path
root=Path.cwd(); env=os.environ.copy(); env['MCFM_HOME']=str(root/'software/mcfm')
files=['M3bit3','M3bit4','FPFMscT','M3bit2','M2bit2']
failed=False
for name in files:
 cmd=['python3','dev/workflow.py','verify',f'software/mcfm/src/BDK/{name}.cpp','--','u','u~','e-','e+','g','g']
 print('$ '+' '.join(cmd),flush=True)
 r=subprocess.run(cmd,env=env,text=True)
 print(f'verify exit code ({name}): {r.returncode}',flush=True)
 if r.returncode not in (0,1): failed=True
raise SystemExit(1 if failed else 0)
