"""Parse Claude-Code-Workflow ("ccworkflow") run directories into flat rows.

Layout: experiments/<day>/ccworkflow-*/workflow-wf_*/
  - journal.jsonl        orchestration events (agent started / result)
  - agent-<id>.jsonl     one Claude Code transcript per subagent
  - agent-<id>.meta.json mostly uninformative ({"agentType": "workflow-subagent", ...})

Token usage lives on every `assistant`-type line's `message.usage`. The phase
(triage/author/integrate/metadata) isn't tagged as structured metadata anywhere
(`attributionSkill` is always the constant "transform"), so it's recovered from
the first `user` message's prompt text, which is a stable convention in every
run observed: "You are an AUTHOR agent", "You are the TRIAGE phase", "You are
the SERIAL INTEGRATE phase", or "Record this round's work..." for the metadata
phase.
"""

import json
import re
from pathlib import Path

PHASE_PATTERNS = [
    (re.compile(r"you are an? author agent", re.I), "author"),
    (re.compile(r"you are the serial integrate phase", re.I), "integrate"),
    (re.compile(r"you are the triage phase", re.I), "triage"),
    (re.compile(r"you are the bundle phase", re.I), "bundle"),
    (re.compile(r"you are the fix phase", re.I), "fix"),
    (re.compile(r"^record this round's work", re.I), "metadata"),
]


def _first_user_text(record):
    message = record.get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                return block["text"]
    return ""


def _classify_phase(first_user_text):
    for pattern, phase in PHASE_PATTERNS:
        if pattern.search(first_user_text):
            return phase
    return "unknown"


def _agent_status(agent_id, journal_events):
    """'completed' if journal has a matching result event, else 'interrupted'."""
    started = any(e.get("agentId") == agent_id and e.get("type") == "started" for e in journal_events)
    completed = any(e.get("agentId") == agent_id and e.get("type") == "result" for e in journal_events)
    if completed:
        return "completed"
    if started:
        return "interrupted"
    return "unknown"


def parse_agent_file(agent_path, journal_events):
    agent_id = agent_path.stem.split("agent-")[-1]
    first_user_text = ""
    rows = []
    tool_ok = 0
    tool_error = 0
    model = None
    effort = None

    with open(agent_path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            rtype = record.get("type")

            if rtype == "user" and not first_user_text:
                first_user_text = _first_user_text(record)
                content = record.get("message", {}).get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            if block.get("is_error"):
                                tool_error += 1
                            else:
                                tool_ok += 1

            elif rtype == "user":
                content = record.get("message", {}).get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            if block.get("is_error"):
                                tool_error += 1
                            else:
                                tool_ok += 1

            elif rtype == "assistant":
                message = record.get("message", {})
                model = message.get("model", model)
                effort = record.get("effort", effort)
                usage = message.get("usage", {})
                rows.append(
                    {
                        "agent_id": agent_id,
                        "model": model,
                        "effort": effort,
                        "input_tokens": usage.get("input_tokens", 0),
                        "output_tokens": usage.get("output_tokens", 0),
                        "cache_write_tokens": usage.get("cache_creation_input_tokens", 0),
                        "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
                    }
                )

    phase = _classify_phase(first_user_text)
    status = _agent_status(agent_id, journal_events)

    if not rows:
        return None

    agg = {
        "agent_id": agent_id,
        "phase": phase,
        "model": model,
        "effort": effort,
        "status": status,
        "n_messages": len(rows),
        "input_tokens": sum(r["input_tokens"] for r in rows),
        "output_tokens": sum(r["output_tokens"] for r in rows),
        "cache_write_tokens": sum(r["cache_write_tokens"] for r in rows),
        "cache_read_tokens": sum(r["cache_read_tokens"] for r in rows),
        "tool_ok": tool_ok,
        "tool_error": tool_error,
    }
    return agg


def parse_workflow_dir(workflow_dir):
    """Return one row per subagent found in a single workflow-wf_* directory."""
    workflow_dir = Path(workflow_dir)
    journal_path = workflow_dir / "journal.jsonl"
    journal_events = []
    if journal_path.exists():
        with open(journal_path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    journal_events.append(json.loads(line))

    rows = []
    for agent_path in sorted(workflow_dir.glob("agent-*.jsonl")):
        row = parse_agent_file(agent_path, journal_events)
        if row is not None:
            rows.append(row)
    return rows


_GATE_LIMIT_RE = re.compile(r"limit is (\d+)")


def round_summary(run_dir):
    """How many Triage -> parallel Author -> serial Integrate rounds this
    ccworkflow run completed, and the cap it was stopped at (if any).

    ccworkflow has no configured round cap the way csloop has `agent_loops`;
    every run here keeps going until Plan's own approval-batch gate
    (check_gate.py) blocks a new group. A round is counted from journal.jsonl's
    Integrate-phase result event, which carries `written` once the group's
    files land on the branch; Triage's own `opened: true` flag agrees exactly
    at every archived run, since a round only starts once Triage opens a
    group. The cap is recovered from the blocking event's `stopReason` text
    ("... limit is N") rather than hardcoded, so a change to the gate's batch
    limit shows up here automatically; a run that never hits the gate reports
    cap=None.
    """
    run_dir = Path(run_dir)
    completed = 0
    cap = None
    for workflow_dir in sorted(run_dir.glob("workflow-wf_*")):
        journal_path = workflow_dir / "journal.jsonl"
        if not journal_path.exists():
            continue
        with open(journal_path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                event = json.loads(line)
                if event.get("type") != "result":
                    continue
                result = event.get("result")
                if not isinstance(result, dict):
                    continue
                if "written" in result:
                    completed += 1
                if result.get("gateBlocked"):
                    match = _GATE_LIMIT_RE.search(result.get("stopReason") or "")
                    if match:
                        cap = int(match.group(1))
    return {"rounds_completed": completed, "cap": cap}


def parse_ccworkflow_run(run_dir):
    """A ccworkflow run dir may contain one workflow-wf_* subdir. Returns run-level rows."""
    run_dir = Path(run_dir)
    rows = []
    for workflow_dir in sorted(run_dir.glob("workflow-wf_*")):
        for row in parse_workflow_dir(workflow_dir):
            row["run_dir"] = str(run_dir)
            row["workflow_id"] = workflow_dir.name
            rows.append(row)
    return rows


def parse_all_ccworkflow(experiments_root):
    """Walk experiments/<day>/ccworkflow-*/ and return all rows across all days."""
    experiments_root = Path(experiments_root)
    all_rows = []
    for day_dir in sorted(experiments_root.iterdir()):
        if not day_dir.is_dir():
            continue
        for run_dir in sorted(day_dir.glob("ccworkflow-*")):
            for row in parse_ccworkflow_run(run_dir):
                row["day"] = day_dir.name
                row["run_name"] = run_dir.name
                all_rows.append(row)
    return all_rows


if __name__ == "__main__":
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "experiments"
    rows = parse_all_ccworkflow(root)
    print(f"Parsed {len(rows)} ccworkflow agent rows")
    for row in rows[:5]:
        print(row)
