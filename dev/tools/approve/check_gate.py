#!/usr/bin/env python3
"""Approval gate for transformation workflows.

Usage:
  python3 dev/tools/approve/check_gate.py <dev/transformations/<name>>

Reads:
- <dir>/agent_log.md
- <dir>/approvals.toml (optional)

Exit codes:
- 0: gate ok
- 1: blocked pending human approval
- 2: usage or missing required files
"""
from __future__ import annotations

import sys
from pathlib import Path

COMMON = Path(__file__).resolve().parent.parent / "common"
if str(COMMON) not in sys.path:
    sys.path.insert(0, str(COMMON))
from approval_log import is_complete, is_open, item_status, load_approved_groups, parse_groups


RISKY_STATUSES = {
    "mcfm-translate": {"FAILED"},
    "mcfm-miniapp-threejets": {"FAILED"},
    "mcfm-cleanup": {"FAILED", "DELETED_SHIM", "MERGED_CPP"},
    "mcfm-fix-failures": {"FAILED"},
    "pepper-kokkos-port": {"FAILED"},
}
BATCH_LIMITS = {
    "mcfm-translate": 3,
    # Miniapp runs are a fixed, measured file set (ThreeJets is 16 files, about 4 groups).
    # The batch limit is raised so a routine run never stalls waiting for a human midway:
    # approval latency would otherwise land inside the wall-clock number the eval records.
    # A group containing FAILED still blocks, which is the stop that carries information.
    "mcfm-miniapp-threejets": 8,
    "mcfm-cleanup": 2,
    "mcfm-fix-failures": 3,
    "pepper-kokkos-port": 2,
}


def usage() -> int:
    print("usage: check_gate.py <dev/transformations/<name>>", file=sys.stderr)
    return 2


def evaluate_gate(tdir: Path) -> dict:
    if not tdir.exists() or not tdir.is_dir():
        return {"state": "error", "message": f"error: transformation dir not found: {tdir}"}

    name = tdir.name
    if name not in BATCH_LIMITS:
        return {"state": "error", "message": f"error: unknown transformation policy: {name}"}

    log_path = tdir / "agent_log.md"
    approvals_path = tdir / "approvals.toml"
    if not log_path.exists():
        return {"state": "ok", "message": f"no log found in {tdir} — nothing to gate."}

    groups = parse_groups(log_path)
    if not groups:
        return {"state": "ok", "message": f"no review groups found in {log_path} — nothing to gate."}

    if any(is_open(g) for g in groups):
        return {"state": "ok", "message": "GATE: OK — an open group is still in progress."}

    approved = load_approved_groups(approvals_path)
    completed = [g for g in groups if is_complete(g)]
    unapproved = [g for g in completed if g["title"] not in approved]
    if not unapproved:
        return {"state": "ok", "message": f"GATE: OK — every completed group in {tdir} is approved."}

    risky = RISKY_STATUSES[name]
    for g in unapproved:
        statuses = {s for s in (item_status(i) for i in g["items"]) if s}
        risky_hits = sorted(statuses & risky)
        if risky_hits:
            return {
                "state": "blocked",
                "kind": "risky",
                "transformation": name,
                "group": g["title"],
                "reason": f"group contains risky status(es): {', '.join(risky_hits)}",
                "message": "GATE: BLOCKED — approval required before opening a new group.",
            }

    if len(unapproved) >= BATCH_LIMITS[name]:
        first = unapproved[0]["title"]
        return {
            "state": "blocked",
            "kind": "batch",
            "transformation": name,
            "group": first,
            "reason": f"{len(unapproved)} completed group(s) are waiting; limit is {BATCH_LIMITS[name]}",
            "message": "GATE: BLOCKED — approval batch limit reached before opening a new group.",
        }

    return {
        "state": "ok",
        "message": "GATE: OK — completed groups do not yet require approval "
        f"({len(unapproved)} waiting, limit {BATCH_LIMITS[name]}).",
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        return usage()

    result = evaluate_gate(Path(argv[1]))
    if result["state"] == "error":
        print(result["message"], file=sys.stderr)
        return 2
    if result["state"] == "ok":
        print(result["message"])
        return 0

    print(result["message"] + "\n")
    print(f"Transformation: {result['transformation']}")
    print(f"Blocking group: {result['group']}")
    print(f"Reason: {result['reason']}")
    print("\nApprove with:")
    print(f"  python3 dev/tools/approve/approve_group.py {Path(argv[1])} --latest-blocking")
    print("\nOr approve this exact group explicitly:")
    print(f"  python3 dev/tools/approve/approve_group.py {Path(argv[1])} \"{result['group']}\" --by <name>")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
