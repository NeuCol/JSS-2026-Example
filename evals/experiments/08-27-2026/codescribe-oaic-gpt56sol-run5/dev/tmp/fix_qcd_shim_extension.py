from pathlib import Path

root = Path("software/mcfm/src/Mods")
source = root / "mod_qcdloop_c_fi.f"
text = source.read_text()
for signature in (
    "        function qli4(p1,p2,p3,p4,s12,s23,m1,m2,m3,m4,mu2,ep)",
    "        function qli4c(p1,p2,p3,p4,s12,s23,m1,m2,m3,m4,mu2,ep)",
    "        function qli3q(p1,p2,p3,m1,m2,m3,mu2,ep)",
    "        function qli4q(p1,p2,p3,p4,s12,s23,m1,m2,m3,m4,mu2,ep)",
    "        function qli3qc(p1,p2,p3,m1,m2,m3,mu2,ep)",
    "        function qli4qc(p1,p2,p3,p4,s12,s23,m1,m2,m3,m4,mu2,ep)",
):
    text = text.replace(signature + "\n     &      bind", signature + " &\n             bind")
target = root / "mod_qcdloop_c_fi.F90"
target.write_text(text)
source.unlink()
cmake = root / "CMakeLists.txt"
cmake.write_text(cmake.read_text().replace("mod_qcdloop_c_fi.f\n", "mod_qcdloop_c_fi.F90\n"))
