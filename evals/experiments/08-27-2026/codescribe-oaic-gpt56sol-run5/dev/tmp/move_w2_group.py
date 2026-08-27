from pathlib import Path
root=Path('software/mcfm/src/W2jet')
d=root/'deprecated'
d.mkdir(exist_ok=True)
for name in ['atree.f','ggZZcapture.f','ZZbox1LL.f','a6routine.f','a6treeg.f']:
 p=root/name
 if p.exists(): p.rename(d/name)
