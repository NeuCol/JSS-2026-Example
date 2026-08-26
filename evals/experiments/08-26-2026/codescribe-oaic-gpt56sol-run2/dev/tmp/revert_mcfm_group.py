from pathlib import Path
src=Path('software/mcfm/src/BDK')
dep=src/'deprecated'
for name in ['M3bit3','M3bit4','FPFMscT','M3bit2','M2bit2']:
 old=dep/f'{name}.f'
 if old.exists(): old.replace(src/old.name)
 for suffix in ('.cpp','.hpp','_fi.f90'):
  path=src/f'{name}{suffix}'
  if path.exists(): path.unlink()
