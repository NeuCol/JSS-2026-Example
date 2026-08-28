from pathlib import Path
p=Path('software/mcfm/src/BDK/FFPMscT.cpp')
s=p.read_text().replace('const std::complex<double> Delta3 =','const double Delta3 =').replace('pow(Delta3,2)','(Delta3*Delta3)')
p.write_text(s)
