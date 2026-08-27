from pathlib import Path
root = Path('software/mcfm/src/BDK')
destination = root / 'deprecated'
for name in ('M1bit1.f', 'FFPMccTtilde.f', 'fvs.f'):
    source = root / name
    if source.exists():
        source.replace(destination / name)
