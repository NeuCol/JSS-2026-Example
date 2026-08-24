"""Index tool — build the step-1 readiness map and additive cleanup metadata.

  python3 build_roadmap.py --doxygen
  python3 build_roadmap.py

Outputs:
- `dev/tmp/assets/roadmap_metrics.tsv`
- `dev/tmp/assets/symbol_index.json`
- `dev/tmp/assets/cleanup_candidates.tsv`
- `dev/tmp/assets/cleanup_index.json`

`deps == 0` and `blind == 0` means a file is ready to rewrite. A file is treated as
translated when a sibling `.cpp` or `.hpp` exists.
"""
import os, glob, sys, json, shutil, collections, subprocess, xml.etree.ElementTree as ET
from pathlib import Path

ROOT   = os.environ.get("PROJECT_HOME") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MCFM   = os.environ.get("MCFM_HOME", ROOT + "/software/mcfm")
SRC    = MCFM + "/src"
XML    = MCFM + "/doxygen_dep/xml"
ASSETS = ROOT + "/dev/tmp/assets"
COMMON = Path(__file__).resolve().parent.parent / "common"
if str(COMMON) not in sys.path:
    sys.path.insert(0, str(COMMON))
from cleanup_index import build_cleanup_index, collect_cmake_sources, collect_header_usage

# top-level src/ directory -> the ./test -b benchmark that exercises it.
BENCH = {
    "W": "u d~ ve e+", "W1jet": "u d~ ve e+ g", "W2jet": "u d~ ve e+ g g",
    "Z": "u u~ e- e+", "Z1jet": "u u~ e- e+ g", "Z2jet": "u u~ e- e+ g g",
    "ThreeJets": "g g g g g", "ggH": "g g h", "gghgg_dep": "g g h g g",
}

# Minimal Doxygen config for the XML the roadmap reads: XML only, Fortran, with the
# cross-reference relations that make <references> edges appear. INPUT/OUTPUT are
# appended at run time from $MCFM_HOME so this stays machine-independent.
DOXYFILE = """
PROJECT_NAME           = MCFM
RECURSIVE              = YES
FILE_PATTERNS          = *.f *.F *.f90 *.F90
OPTIMIZE_FOR_FORTRAN   = YES
EXTENSION_MAPPING      = f=FortranFixed F=FortranFixed f90=FortranFree F90=FortranFree
# MCFM compiles fixed-form with unlimited line length, so past column 72 is still
# code. Doxygen's default of 72 truncates it and can abort the run outright, so use
# the 10000 maximum (ignored with a warning on 1.8.x).
FORTRAN_COMMENT_AFTER  = 10000
EXTRACT_ALL            = YES
EXTRACT_PRIVATE        = YES
EXTRACT_STATIC         = YES
EXCLUDE_PATTERNS       = */deprecated/* */Store/* */working/*
SOURCE_BROWSER         = YES
REFERENCED_BY_RELATION = YES
REFERENCES_RELATION    = YES
GENERATE_HTML          = NO
GENERATE_LATEX         = NO
GENERATE_XML           = YES
XML_OUTPUT             = xml
XML_PROGRAMLISTING     = NO
HAVE_DOT               = NO
QUIET                  = YES
WARNINGS               = NO
WARN_IF_UNDOCUMENTED   = NO
"""


def relsrc(p):
    p = p.replace("\\", "/"); i = p.find("/src/")
    return p[i + 5:] if i >= 0 else os.path.relpath(p, SRC)


def is_src(fn):
    return (fn.endswith(".f") or fn.endswith(".f90")) and "_fi." not in fn


def run_doxygen():
    """Generate $MCFM_HOME/doxygen_dep/xml from the embedded config."""
    if not shutil.which("doxygen"):
        sys.exit("error: doxygen not found on PATH (Ubuntu: sudo apt-get install -y doxygen)")
    out = os.path.dirname(XML)
    os.makedirs(out, exist_ok=True)
    print(f"Generating Doxygen XML for {SRC} -> {XML}")
    config = DOXYFILE + f"\nINPUT = {SRC}\nOUTPUT_DIRECTORY = {out}\n"
    r = subprocess.run(["doxygen", "-"], input=config, text=True,
                       stdout=subprocess.DEVNULL)
    n = len([x for x in glob.glob(XML + "/*.xml") if not x.endswith("index.xml")])
    if r.returncode < 0:
        # Aborted mid-parse; the "Error in file ... state: N" lines above are the
        # expected *_inc.f noise, not the cause.
        sys.exit(f"error: doxygen died on signal {-r.returncode} after parsing — no XML written")
    if r.returncode or n == 0:
        sys.exit("error: no XML produced — check doxygen output")
    print(f"wrote {n} XML file(s) to {XML}")


def build_roadmap(scope=None):
    """Build the readiness map. `scope` is a top-level src/ folder name (e.g. "ThreeJets").

    When scoped, the map describes a miniapp run: only files under that folder are listed,
    and `deps`/`fanin` count only edges whose other end is *also* in the folder. So
    `deps == 0` reads as "ready within this miniapp" rather than "ready in all of MCFM".
    A file whose only remaining untranslated callees sit outside the scope is ready now;
    the Spec's `extern "C"` rule covers calling them while they are still Fortran.
    """
    os.makedirs(ASSETS, exist_ok=True)

    # ---- source files and their translated state ----
    files = []
    for root, dirs, fs in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in ("deprecated", "Store", "working")]
        files += [os.path.join(root, fn) for fn in fs if is_src(fn)]

    info, translated = {}, set()
    for p in sorted(files):
        r = relsrc(p)
        info[r] = {"rel": r, "top": r.split("/")[0]}
        if os.path.exists(p.rsplit(".", 1)[0] + ".cpp") or os.path.exists(p.rsplit(".", 1)[0] + ".hpp"):
            translated.add(r)

    # ---- Doxygen call graph -> file edges + symbol -> file index ----
    cref2file, symbols, edges = {}, {}, collections.defaultdict(set)
    xmls = sorted(x for x in glob.glob(XML + "/*.xml") if not x.endswith("index.xml"))
    for x in xmls:
        try: root = ET.parse(x).getroot()
        except ET.ParseError: continue
        for cd in root.findall("compounddef"):
            loc = cd.find("location")
            if cd.get("kind") == "file" and loc is not None and loc.get("file"):
                cref2file[cd.get("id")] = relsrc(loc.get("file"))
            elif cd.get("kind") == "module":
                cn = cd.find("compoundname")
                if cn is not None and cn.text and loc is not None and loc.get("file"):
                    symbols.setdefault(cn.text.strip().lower(), relsrc(loc.get("file")))
    for x in xmls:
        try: root = ET.parse(x).getroot()
        except ET.ParseError: continue
        for md in root.iter("memberdef"):
            loc = md.find("location")
            cf = relsrc(loc.get("file")) if (loc is not None and loc.get("file")) else None
            if not cf: continue
            if md.get("kind") in ("function", "subroutine"):
                nm = md.find("name")
                if nm is not None and nm.text: symbols.setdefault(nm.text.strip().lower(), cf)
            for ref in md.findall("references"):
                g = cref2file.get(ref.get("compoundref"))
                if g and g in info and g != cf: edges[cf].add(g)

    # ---- readiness: untranslated callees (deps), fan-in, blindness ----
    def is_blind(r):
        return r.endswith("_inc.f") or r.startswith("gghgg_dep/Inc/")

    def in_scope(r):
        return scope is None or info[r]["top"] == scope

    untranslated = {r for r in info if r not in translated}
    fanin = collections.Counter()
    for r in info:
        udeps = {g for g in edges.get(r, set()) if g in untranslated and g != r and in_scope(g)}
        info[r]["deps"] = len(udeps)
        for g in udeps: fanin[g] += 1
    for r in info:
        info[r]["fanin"] = fanin.get(r, 0)
        info[r]["blind"] = int(is_blind(r))
        info[r]["bench"] = BENCH.get(info[r]["top"], "")

    # ---- additive cleanup metadata ----
    cmake_sources = collect_cmake_sources(SRC)
    header_usage, header_users = collect_header_usage(SRC)
    cleanup = build_cleanup_index(SRC, cmake_sources, header_usage, header_users)

    # ---- outputs ----
    with open(ASSETS + "/symbol_index.json", "w") as fh:
        json.dump({"root": SRC, "symbols": symbols}, fh, indent=1, sort_keys=True)

    # A scoped run's work list is exactly the untranslated files inside the miniapp.
    listed = {r for r in untranslated if in_scope(r)}

    cols = ["rel", "top", "deps", "blind", "fanin", "bench"]
    with open(ASSETS + "/roadmap_metrics.tsv", "w") as fh:
        fh.write("\t".join(cols) + "\n")
        for r in sorted(listed, key=lambda x: (info[x]["deps"], -info[x]["fanin"], x)):
            fh.write("\t".join(str(info[r][c]) for c in cols) + "\n")

    cleanup_cols = [
        "base", "dir", "fortran", "cpp", "header", "fi", "deprecated_original",
        "cmake_original", "cmake_cpp", "cmake_header", "cmake_fi",
        "header_include_count", "move_candidate", "delete_shim_candidate", "merge_candidate",
    ]
    with open(ASSETS + "/cleanup_candidates.tsv", "w") as fh:
        fh.write("\t".join(cleanup_cols) + "\n")
        for row in cleanup:
            fh.write("\t".join(str(row[c]) for c in cleanup_cols) + "\n")

    with open(ASSETS + "/cleanup_index.json", "w") as fh:
        json.dump({"root": SRC, "candidates": cleanup}, fh, indent=1, sort_keys=True)

    leaves = sum(1 for r in listed if info[r]["deps"] == 0 and not info[r]["blind"])
    cleanup_moves = sum(row["move_candidate"] for row in cleanup)
    cleanup_shims = sum(row["delete_shim_candidate"] for row in cleanup)
    cleanup_merges = sum(row["merge_candidate"] for row in cleanup)
    if scope:
        done = sum(1 for r in info if in_scope(r) and r in translated)
        print(f"scope {scope}: {len(listed)} untranslated, {done} already translated")
    print(f"source {len(info)}  translated {len(translated)}  untranslated {len(untranslated)}")
    print(f"ready leaves (deps=0, non-blind): {leaves}")
    print(f"symbol index: {len(symbols)} symbol(s)")
    print(f"cleanup candidates: move {cleanup_moves}  shim-delete {cleanup_shims}  merge {cleanup_merges}")
    print("wrote roadmap_metrics.tsv, symbol_index.json, cleanup_candidates.tsv, cleanup_index.json")


def parse_scope(argv):
    """--scope <folder> or --scope=<folder>; returns None when absent."""
    for i, a in enumerate(argv):
        if a == "--scope":
            if i + 1 >= len(argv):
                sys.exit("error: --scope needs a top-level src/ folder name, e.g. --scope ThreeJets")
            return argv[i + 1]
        if a.startswith("--scope="):
            return a.split("=", 1)[1]
    return None


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--doxygen" in argv:
        run_doxygen()
    else:
        scope = parse_scope(argv)
        if scope and not os.path.isdir(os.path.join(SRC, scope)):
            sys.exit(f"error: no such top-level source folder: {SRC}/{scope}")
        build_roadmap(scope)
