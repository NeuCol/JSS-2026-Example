"""Coverage / correctness facts per run: files settled, self-reported test
status, human-verified test status, and run status.

Everything here is derived from the actual log text, not hardcoded:
  - "files settled" = count of `- [x]` checklist items in
    dev/transformations/mcfm-translate/agent_log.md for the run.
  - "self-reported pass fraction" = the last `N/M ... PASS(ED)` match anywhere
    in that agent_log.md (the agent's own in-loop correctness claim).
  - "human-verified pass fraction" = the `SUMMARY: pass rate N/M` line a human
    appended after manually running the real MCFM regression suite, wherever a
    human_review file contains one.
"""

import re
from pathlib import Path

# Two ways a run's log states its self-reported pass fraction:
#  - "pass(es) [rate] N/M" - the number follows the word (this is the literal
#    phrasing of the jobrunner tool's own "SUMMARY: pass rate N/M" output,
#    which agent logs usually quote directly or paraphrase as "passes N/M").
#  - "N/M ... PASS(ED)" - the number precedes the word, within a short window
#    (used for terser phrasings like "272/272 PASSED").
# A single fixed-width \D{0,N} window in either direction alone isn't enough:
# too narrow misses real summaries buried in a longer sentence; too wide
# starts pairing a number with an unrelated PASS mentioned paragraphs later.
SELF_REPORT_RE = re.compile(
    r"\bpass(?:es)?(?:\s+rate)?\s*[:\-]?\s*(\d+)\s*/\s*(\d+)"
    r"|(\d+)\s*/\s*(\d+)\D{0,20}PASS(?:ED)?",
    re.I,
)
VERIFIED_RE = re.compile(r"SUMMARY:\s*pass rate\s*(\d+)\s*/\s*(\d+)", re.I)
CHECKED_RE = re.compile(r"^\s*-\s*\[x\]", re.I | re.M)
UNCHECKED_RE = re.compile(r"^\s*-\s*\[ \]", re.M)


def _read(path):
    try:
        return Path(path).read_text(errors="replace")
    except FileNotFoundError:
        return ""


def _agent_log_path(run_dir):
    return Path(run_dir) / "dev" / "transformations" / "mcfm-translate" / "agent_log.md"


def _human_review_path(run_dir):
    return Path(run_dir) / "human_review"


def _run_produced_artifacts(run_dir):
    """Whether the archive contains engine output for this run at all.

    A run directory can carry a full loop/metadata (or workflow-wf_*) record and
    still have no agent_log.md, when the log was not copied in at archive time —
    08-26-2026/codescribe-sonnet-5 is that case. That is a missing *log*, not a
    run that never happened, and the two must not report the same status.
    """
    run_dir = Path(run_dir)
    return (run_dir / "loop" / "metadata" / "manifest.toml").exists() or any(
        run_dir.glob("workflow-wf_*")
    )


def coverage_for_run(run_dir):
    run_dir = Path(run_dir)
    agent_log_path = _agent_log_path(run_dir)
    has_log = agent_log_path.exists()

    settled = 0
    open_items = 0
    self_reported = None
    if has_log:
        text = _read(agent_log_path)
        settled = len(CHECKED_RE.findall(text))
        open_items = len(UNCHECKED_RE.findall(text))
        matches = list(SELF_REPORT_RE.finditer(text))
        if matches:
            last = matches[-1]
            n = last.group(1) or last.group(3)
            m = last.group(2) or last.group(4)
            self_reported = (int(n), int(m))

    human_verified = None
    review_text = _read(_human_review_path(run_dir))
    m = VERIFIED_RE.search(review_text)
    if m:
        human_verified = (int(m.group(1)), int(m.group(2)))

    if not has_log:
        status = "no agent_log archived" if _run_produced_artifacts(run_dir) else "not-executed"
    elif "manually terminated" in review_text.lower():
        status = "manually-terminated"
    elif review_text.strip():
        status = "stopped (see human_review)"
    else:
        status = "stopped-at-gate"

    return {
        "run_dir": str(run_dir),
        "files_settled": settled,
        "files_open": open_items,
        "self_reported_pass": self_reported,
        "human_verified_pass": human_verified,
        "final_status": status,
    }


if __name__ == "__main__":
    import sys
    from pprint import pprint

    pprint(coverage_for_run(sys.argv[1]))
