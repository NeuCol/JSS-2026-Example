"""Coverage check — decide VERIFIED vs TRANSLATED for one rewritten MCFM file.

  python3 coverage_check.py <target.cpp> -- <process args>

Builds and tests once, scales the marked output statement, rebuilds and retests, then
restores the file and rebuilds clean. Changed output means `COVERED`; unchanged output
means `NOT COVERED`.

Mark exactly one output statement with `// @coverage-probe`.
Uses `MCFM_HOME`, falling back to `$PROJECT_HOME/software/mcfm` and then to this file's
own location, so it works in a sandbox that cannot `source environment.sh`.
Exit: 0 covered, 1 not covered, 2 usage/setup error.
"""
import os, re, sys, shutil, tempfile, subprocess

# Same fallback chain as dev/tools/index/build_roadmap.py and
# dev/tools/closure/calltree_closure.py. Without it this tool was the only one in dev/tools
# that hard-required MCFM_HOME, so a restricted agent shell that cannot export environment
# variables (no `source`, no `$VAR` expansion) could never run the coverage probe: verify
# exited 2 every time and every file it touched was stuck at TRANSLATED regardless of
# whether the C++ was correct.
ROOT = os.environ.get("PROJECT_HOME") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MCFM_DEFAULT = os.path.join(ROOT, "software", "mcfm")

FACTOR = os.environ.get("FACTOR", "1.5")


def die(msg):
    print(f"error: {msg}", file=sys.stderr); sys.exit(2)


def build(bin, mcfm):
    if not os.path.isfile(bin + "/CMakeCache.txt"):
        subprocess.run(["cmake",
                        "-DCMAKE_Fortran_COMPILER=" + os.environ.get("FC", "gfortran"),
                        "-DCMAKE_C_COMPILER=" + os.environ.get("CC", "gcc"),
                        "-DCMAKE_CXX_COMPILER=" + os.environ.get("CXX", "g++"),
                        "-DCMAKE_INSTALL_PREFIX=" + mcfm + "/install",
                        "-S", mcfm, "-B", bin], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["make", "-C", bin, "install"], check=True, stdout=subprocess.DEVNULL)


def run_test(bin, process):
    return subprocess.run([bin + "/test", "-b", *process], capture_output=True, text=True).stdout


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        die("usage: coverage_check.py <target.cpp> -- <process args>")
    target = argv[0]
    if len(argv) < 2 or argv[1] != "--":
        die("put the test process after --, e.g. -- u u~ e- e+")
    process = argv[2:]
    if not process:
        die("no test process given after --")

    mcfm = os.environ.get("MCFM_HOME") or MCFM_DEFAULT
    if not os.path.isdir(mcfm):
        die(f"no MCFM tree at {mcfm} — set MCFM_HOME or PROJECT_HOME")
    if not os.path.isfile(target):
        die("target file not found: " + target)
    text = open(target).read()
    if text.count("@coverage-probe") == 0:
        die(f"no '// @coverage-probe' marker in {target} — mark the statement that writes the main output")
    if text.count("@coverage-probe") != 1:
        die(f"found more than one '@coverage-probe' marker in {target} — keep exactly one")

    bin = mcfm + "/Bin"
    if not os.path.isdir(bin):
        die(f"no MCFM build dir at {bin} — build MCFM once first (jobrunner submit tests/mcfm)")

    snapshot = tempfile.mktemp()
    shutil.copy(target, snapshot)
    print(f"== coverage check: {target} ==\nprocess : {' '.join(process)}\nfactor  : {FACTOR}")
    try:
        print("-- baseline build + test --")
        build(bin, mcfm)
        baseline = run_test(bin, process)

        print(f"-- scaling the marked output by {FACTOR} --")
        # On the marked line only: lhs = rhs;  // @coverage-probe -> lhs = (rhs) * FACTOR;  // ...
        scaled = re.sub(r"(=\s*)(.*);(\s*//.*@coverage-probe.*)$",
                        rf"\1(\2) * {FACTOR};\3", text, flags=re.M)
        open(target, "w").write(scaled)
        if f"* {FACTOR};" not in scaled:
            die("could not scale the marked line — is it a plain 'lhs = rhs;   // @coverage-probe' statement?")

        print("-- probed build + test --")
        build(bin, mcfm)
        probed = run_test(bin, process)
    finally:
        shutil.copy(snapshot, target)
        os.remove(snapshot)
        try:
            build(bin, mcfm)  # rebuild from restored source so the tree is left correct
        except subprocess.CalledProcessError:
            print("warning: final rebuild after restore failed — rebuild MCFM before trusting the binary", file=sys.stderr)

    print()
    if baseline == probed:
        print("RESULT: NOT COVERED — the numbers did not change, so the test never ran this file.")
        print("  Mark it TRANSLATED. Check again after a routine that calls it is rewritten.")
        return 1
    print("RESULT: COVERED — the numbers changed, so the test exercised this file.")
    print("  If the restored build now PASSES its match, this file is VERIFIED-eligible.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
