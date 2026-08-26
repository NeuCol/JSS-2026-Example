from pathlib import Path
root=Path.cwd()
src=root/'software/mcfm/src/BDK'
dep=src/'deprecated'; dep.mkdir(exist_ok=True)
for name in ['M3bit3','M3bit4','FPFMscT','M3bit2','M2bit2']:
 old=src/f'{name}.f'
 if old.exists(): old.replace(dep/old.name)
