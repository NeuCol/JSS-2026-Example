#!/usr/bin/env python3
"""Collapse operator PII in evals/experiments/ to the corpus convention.

Lives here, next to archive_experiment.py, rather than under dev/tmp/: it is a
corpus tool, and dev/tmp is scratch that the transformation runner wipes on
cleanup (this script has been lost to that twice).

Convention (experiments/ was first scrubbed 2026-08-13; new runs copied in must
match or the corpus becomes inconsistent):
  - every operator repo root collapses to /home/user/JSS-2026-Example, project
    name included -- the goal is that no operator-specific path survives, not
    merely that the username is gone
  - Claude session slugs take the same collapse with "-" for "/"
  - akash / adhruv / adubey anywhere (ls -l owner columns included) -> user
  - the Convert_to_c++ branch namespace loses its username (it hides there)

Upstream MCFM/QCDloop author credit (R.K. Ellis, J. Campbell, and the CERN and
Durham addresses) is deliberately KEPT -- published academic attribution in
quoted third-party source, not operator data -- and no rule below matches it.

Truncated paths matter: archived `output_preview` fields are cut at a fixed
character budget, so a root can end mid-component ("/home/akash/Desktop/Akash/
Projects/J"). A plain full-root rule misses those and leaves "/home/akash"
fragments behind, so every prefix of the root is mapped too, to the canonical
root shortened by the same number of characters. That keeps "this was cut off"
visible instead of fabricating path that was never in the file.

Idempotent. Dry run by default; pass --apply to write.

Verify afterwards with:
    grep -rho "adhruv\\|/home/[a-z]*" experiments/ | sort | uniq -c
anything but /home/user (and short truncations of it) is a miss.
"""

import argparse
import re
import sys
from pathlib import Path

CANON = "/home/user/JSS-2026-Example"

ROOTS = [
    "/home/akash/Desktop/Akash/Projects/JSS-Paper-Example",
    "/home/akash/Desktop/Akash/Projects/Agentic-Workflow-Design",
    "/home/akash/Desktop/Akash/Projects/NeuCol-Code-Translation",
    "/home/adubey/JSS-2026-Example",
]
SLUG_CANON = "-home-user-JSS-2026-Example"


def _rules():
    """(source, replacement) pairs, longest source first.

    Order is load-bearing: the bare-username rules at the end would otherwise
    rewrite "/home/akash/..." to "/home/user/..." and stop the full-root rules
    from ever matching, leaving the operator's directory layout intact.
    """
    rules = []
    for root in ROOTS:
        rules.append((root.replace("/", "-"), SLUG_CANON))
        rules.append((root, CANON))
        # Prefixes of the root, for previews cut mid-path. Shortened by however
        # many characters the source lost, floored at "/home/user" so even a
        # badly truncated fragment still loses the username.
        for cut in range(1, len(root) - len("/home/")):
            src = root[:-cut]
            if not src.startswith("/home/") or src == "/home/":
                break
            rules.append((src, CANON[: max(len("/home/user"), len(CANON) - cut)]))

    rules += [
        ("Akash Dhruv <akashdhruv@gwmail.gwu.edu>", "User <user@example.com>"),
        ("akashdhruv@gwmail.gwu.edu", "user@example.com"),
        ("Akash Dhruv", "User"),
        ("akashdhruv", "user"),
        ("adhruv", "user"),
        ("adubey", "user"),
        ("akash", "user"),
        ("Akash", "User"),
    ]
    rules.sort(key=lambda r: len(r[0]), reverse=True)
    # Fragments too short for any rule above (a preview cut inside the username
    # itself). Appended after the sort: they must run last, on what is left.
    rules += [("/home/ak", "/home/us"), ("/home/a", "/home/u")]
    return rules


RULES = _rules()

# What "clean" is checked against, and what the per-file count reports.
TOKENS = re.compile(r"akashdhruv|akash|Akash|adhruv|adubey|gwmail|/home/ak?(?![a-z])")


def scrub(text):
    for src, dst in RULES:
        text = text.replace(src, dst)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", type=Path)
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args()

    files = sorted(p for p in args.target.rglob("*") if p.is_file())
    changed = 0
    for path in files:
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable: nothing text-shaped to scrub
        scrubbed = scrub(original)
        if scrubbed == original:
            continue
        changed += 1
        # Count PII tokens, not rule matches: the prefix rules overlap, so
        # summing per-rule hits reports several times the real occurrence count.
        print(f"{'scrub' if args.apply else 'would scrub'} {path} "
              f"({len(TOKENS.findall(original))} matches)")
        if args.apply:
            path.write_text(scrubbed, encoding="utf-8")

    print(f"\n{changed} file(s) {'changed' if args.apply else 'would change'} "
          f"of {len(files)} scanned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
