"""Bash tool-call error rate, per run, on one definition across all three harnesses.

WHY THIS EXISTS. Section~evalloop's tool-call comparison covers every tool a
run called; the model-level story sits specifically in the Bash calls (csloop's
bounded shell, ccworkflow/ccloop's unrestricted one), so it needs its own
narrower count: of the Bash calls a run actually executed, what fraction came
back an error. csloop's own per-tool [[tools]] records already carry this
(the same "ok" field parse_csloop.py reads generically, filtered here to
name == "bash"); a Claude Code run (ccworkflow, ccloop) has no such record, so
its Bash calls and their outcomes have to be reconstructed by matching each
`tool_use` block to the `tool_result` that answers it.

This double-counts nothing csloop's rejected_calls already excludes: a
policy-blocked call there never reaches [[tools]] at all, so it is out of
scope for an error rate the same way it is out of scope for parse_csloop's
tool_executed count. A Claude Code run has no such pre-execution gate (that is
the point of Section~evalpolicy), so every issued Bash call it made counts here.
"""

import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib

from harness import CCWORKFLOW, CCLOOP, CSLOOP, harness_of


def _load_toml(path):
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def csloop_bash_calls(run_dir):
    """(total, errors) for every Bash call in a csloop run's loop/metadata/*.toml."""
    total, errors = 0, 0
    metadata_dir = Path(run_dir) / "loop" / "metadata"
    for loop_path in sorted(metadata_dir.glob("loop_*.toml")):
        try:
            loop_data = _load_toml(loop_path)
        except Exception:
            continue
        for tool in loop_data.get("tools", []):
            if tool.get("name") != "bash":
                continue
            total += 1
            if not tool.get("ok", True):
                errors += 1
    return total, errors


def cc_bash_calls(run_dir):
    """(total, errors) for every Bash call across a ccworkflow/ccloop run's transcripts.

    A call counts once it has been answered: each `tool_use` block named
    "Bash" is matched to the `tool_result` block carrying the same
    `tool_use_id`, and `is_error` on that result decides the outcome. A call
    issued but never answered (the agent was interrupted mid-call) has no
    matching result and is not counted, mirroring shell_policy._bash_commands'
    choice to count issued-not-answered calls only where the question is what
    the agent tried, not what happened to it.
    """
    total, errors = 0, 0
    for workflow_dir in sorted(Path(run_dir).glob("workflow-wf_*")):
        for agent_path in sorted(workflow_dir.glob("agent-*.jsonl")):
            pending = set()
            with open(agent_path) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    rtype = record.get("type")
                    if rtype == "assistant":
                        content = record.get("message", {}).get("content")
                        if isinstance(content, list):
                            for block in content:
                                if (isinstance(block, dict) and block.get("type") == "tool_use"
                                        and block.get("name") == "Bash"):
                                    pending.add(block.get("id"))
                    elif rtype == "user":
                        content = record.get("message", {}).get("content")
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "tool_result":
                                    tool_use_id = block.get("tool_use_id")
                                    if tool_use_id in pending:
                                        total += 1
                                        if block.get("is_error"):
                                            errors += 1
                                        pending.discard(tool_use_id)
    return total, errors


def bash_error_rate_for_run(run_dir, run_name):
    """{'total': n, 'errors': n, 'rate': errors/total or None} for one run directory."""
    if harness_of(run_name) == CSLOOP:
        total, errors = csloop_bash_calls(run_dir)
    else:  # CCWORKFLOW and CCLOOP archive into the same transcript layout
        total, errors = cc_bash_calls(run_dir)
    return {"total": total, "errors": errors, "rate": (errors / total) if total else None}


def bash_error_rates(experiments_root, runs):
    """{(day, run_name): result} for every (day, run_name, ...) in `runs`."""
    experiments_root = Path(experiments_root)
    return {
        (day, run_name): bash_error_rate_for_run(experiments_root / day / run_name, run_name)
        for day, run_name, *_ in runs
    }


if __name__ == "__main__":
    _HERE = Path(__file__).resolve().parent
    import sys
    sys.path.insert(0, str(_HERE))
    from generate_graphs import RUNS, RUN_CODES  # the registry, so this matches the figures

    root = _HERE.parent / "experiments"
    for day, run_name, *_ in RUNS:
        key = (day, run_name)
        result = bash_error_rate_for_run(root / day / run_name, run_name)
        code = RUN_CODES.get(key, "?")
        rate = f"{result['rate']:.1%}" if result["rate"] is not None else "n/a"
        print(f"{code:4s} {run_name:45s} bash={result['total']:4d} errors={result['errors']:4d} rate={rate}")
