"""Parse Claude-Code-loop ("ccloop") run directories into flat rows.

Layout: experiments/<day>/<ccloop run>/workflow-wf_*/
  - journal.jsonl        orchestration events
  - agent-<id>.jsonl     one Claude Code transcript per subagent
  - agent-<id>.meta.json {"agentType", "description", "workflowPhase", ...}

Same on-disk shape as ccworkflow (see parse_ccworkflow), and the token
accounting is identical — usage lives on every `assistant` line's
`message.usage`, read through the shared cc_usage reader so the TTL split,
thinking tokens and service tier reach the row. Two things differ, and they are
why this is its own module rather than a flag on that one:

PHASE IS STRUCTURED HERE, NOT GUESSED. ccworkflow's phase has to be recovered
by pattern-matching the first user message, because nothing on disk records it.
The loop workflow declares its phases to the harness, so every ccloop agent
carries `workflowPhase` ("Author" / "Review" / "Metadata") in its .meta.json
AND a `phase` on its journal `started` event, plus a `label` naming the loop it
belongs to ("author:loop3"). Reading those is exact; pattern-matching would in
fact FAIL here, since every author and review agent opens with the same shared
preamble ("You are an autonomous coding agent specializing in test-driven
development and repair"), which names no phase at all.

A "LOOP" HERE MEANS WHAT IT MEANS FOR csloop, NOT FOR ccworkflow. ccworkflow
counts Triage->Author->Integrate rounds against an approval-batch gate it has
no configured cap for. ccloop runs `for loop = 1..agentLoops` with a real
configured cap, exactly like CodeScribe's prompt_loop, so `loop_summary`
reports completed/cap in the same sense `parse_csloop.manifest_run_info` does
and the two are directly comparable. The cap is read out of the author prompt's
own "Loop N of M" line rather than out of the archived loop-wf_*.js: the script
records the DEFAULT (`cfg.agentLoops ?? 5`) but not the args it was invoked
with, so a run started with an explicit override would be misreported by the
script and is reported correctly by the prompt the agent actually received.

A run can stop before the cap. The loop exits early when the author reports
STATUS: COMPLETE, or when review comes back with no pending items and no
blocker — 09-11-2026/ccworkflow-loop-sonnet-5 stops that way after one loop.
`loop_summary` reports that as 1/5, the same shape a csloop run that
self-terminates gets, and `stopped_early` says it was not the cap that ended it.
"""

import json
import re
from pathlib import Path

from cc_usage import ACCUMULATED_FIELDS, cc_usage

# "Loop 3 of 5" — the loop workflow states the budget in every author prompt.
_LOOP_BUDGET_RE = re.compile(r"\bLoop\s+(\d+)\s+of\s+(\d+)\b")
# "author:loop3" / "review:loop3" — the journal/meta label for a phase agent.
_LOOP_LABEL_RE = re.compile(r"^(author|review):loop(\d+)$")


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


def _journal_events(workflow_dir):
    journal_path = Path(workflow_dir) / "journal.jsonl"
    if not journal_path.exists():
        return []
    events = []
    with open(journal_path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def _agent_labels(workflow_dir, journal_events):
    """{agent_id: (phase, label)} from the journal, backfilled from .meta.json.

    The journal's `started` event is the primary source; .meta.json carries the
    same two fields (`workflowPhase`, `description`) and covers an agent whose
    start event is missing from a truncated journal.
    """
    out = {}
    for event in journal_events:
        agent_id = event.get("agentId")
        if event.get("type") == "started" and agent_id:
            out[agent_id] = (event.get("phase"), event.get("label"))

    for meta_path in sorted(Path(workflow_dir).glob("agent-*.meta.json")):
        agent_id = meta_path.name[len("agent-"):-len(".meta.json")]
        if agent_id in out and out[agent_id][0]:
            continue
        try:
            with open(meta_path) as fh:
                meta = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        out[agent_id] = (meta.get("workflowPhase"), meta.get("description"))
    return out


def _agent_status(agent_id, journal_events):
    """'completed' if the journal carries a result for this agent, else
    'interrupted'.

    The metadata agent is routinely 'interrupted' here and that is not a
    failure to hide: it is the last thing the workflow runs, and archival can
    be cut short (see the run notes in generate_graphs). Its tokens are real
    and are counted either way.
    """
    started = any(e.get("agentId") == agent_id and e.get("type") == "started" for e in journal_events)
    completed = any(e.get("agentId") == agent_id and e.get("type") == "result" for e in journal_events)
    if completed:
        return "completed"
    if started:
        return "interrupted"
    return "unknown"


def parse_agent_file(agent_path, journal_events, labels):
    agent_id = agent_path.stem.split("agent-")[-1]
    phase_raw, label = labels.get(agent_id, (None, None))
    phase = (phase_raw or "unknown").lower()

    loop_index = None
    match = _LOOP_LABEL_RE.match(label or "")
    if match:
        loop_index = int(match.group(2))

    rows = []
    tool_ok = 0
    tool_error = 0
    model = None
    effort = None
    service_tier = None
    ttl_attributed = True
    loop_cap = None

    with open(agent_path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            rtype = record.get("type")

            if rtype == "user":
                if loop_cap is None:
                    budget = _LOOP_BUDGET_RE.search(_first_user_text(record))
                    if budget:
                        loop_cap = int(budget.group(2))
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
                usage = cc_usage(message)
                service_tier = usage["service_tier"] or service_tier
                if usage["cache_write_tokens"] and not usage["cache_write_ttl_attributed"]:
                    ttl_attributed = False
                rows.append(usage)

    if not rows:
        return None

    agg = {
        "agent_id": agent_id,
        "phase": phase,
        "label": label,
        "loop_index": loop_index,
        "loop_cap": loop_cap,
        "model": model,
        "effort": effort,
        "service_tier": service_tier,
        "status": _agent_status(agent_id, journal_events),
        "n_messages": len(rows),
        "cache_write_ttl_attributed": ttl_attributed,
        "tool_ok": tool_ok,
        "tool_error": tool_error,
    }
    agg.update({f: sum(r[f] for r in rows) for f in ACCUMULATED_FIELDS})
    return agg


def parse_workflow_dir(workflow_dir):
    """One row per subagent in a single workflow-wf_* directory."""
    workflow_dir = Path(workflow_dir)
    journal_events = _journal_events(workflow_dir)
    labels = _agent_labels(workflow_dir, journal_events)

    rows = []
    for agent_path in sorted(workflow_dir.glob("agent-*.jsonl")):
        row = parse_agent_file(agent_path, journal_events, labels)
        if row is not None:
            rows.append(row)
    return rows


def parse_ccloop_run(run_dir):
    run_dir = Path(run_dir)
    rows = []
    for workflow_dir in sorted(run_dir.glob("workflow-wf_*")):
        for row in parse_workflow_dir(workflow_dir):
            row["run_dir"] = str(run_dir)
            row["workflow_id"] = workflow_dir.name
            rows.append(row)
    return rows


def loop_summary(run_dir):
    """{"loops_completed", "cap", "stopped_early"} for one ccloop run.

    `loops_completed` counts distinct AUTHOR loop indices that produced a
    result event — an author agent that started and never reported did not
    complete its loop. Review is not counted separately: it is the back half of
    the same loop, and is skipped by design when the author reports COMPLETE,
    so counting phases rather than loops would make an early-finishing loop
    look like half a loop.

    `cap` is the M in the author prompt's "Loop N of M" (see module docstring);
    None if no author prompt carried one. `stopped_early` is True when the run
    ended below its cap, i.e. the loop's own stop condition fired rather than
    the budget running out.
    """
    run_dir = Path(run_dir)
    completed_loops = set()
    cap = None

    for workflow_dir in sorted(run_dir.glob("workflow-wf_*")):
        journal_events = _journal_events(workflow_dir)
        resulted = {e.get("agentId") for e in journal_events if e.get("type") == "result"}
        for row in parse_workflow_dir(workflow_dir):
            if row["loop_cap"] is not None:
                cap = row["loop_cap"] if cap is None else max(cap, row["loop_cap"])
            if row["phase"] == "author" and row["loop_index"] is not None \
                    and row["agent_id"] in resulted:
                completed_loops.add(row["loop_index"])

    completed = len(completed_loops)
    return {
        "loops_completed": completed,
        "cap": cap,
        "stopped_early": (cap is not None and completed < cap),
    }


def parse_all_ccloop(experiments_root):
    """Walk experiments/<day>/ and return rows for every ccloop run."""
    from harness import harness_of, CCLOOP

    experiments_root = Path(experiments_root)
    all_rows = []
    for day_dir in sorted(experiments_root.iterdir()):
        if not day_dir.is_dir():
            continue
        for run_dir in sorted(r for r in day_dir.iterdir() if r.is_dir()):
            if harness_of(run_dir.name) != CCLOOP:
                continue
            for row in parse_ccloop_run(run_dir):
                row["day"] = day_dir.name
                row["run_name"] = run_dir.name
                all_rows.append(row)
    return all_rows


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    root = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parent.parent / "experiments")
    rows = parse_all_ccloop(root)
    print(f"Parsed {len(rows)} ccloop agent rows")
    for row in rows:
        print(f"  {row['day']}/{row['run_name']:28s} {row['label'] or '?':18s} "
              f"{row['phase']:9s} {row['model']:16s} {row['status']:12s} "
              f"in={row['input_tokens']:7d} out={row['output_tokens']:6d} "
              f"tools={row['tool_ok'] + row['tool_error']:4d}")
    seen = []
    for row in rows:
        key = (row["day"], row["run_name"])
        if key not in seen:
            seen.append(key)
    for day, run_name in seen:
        print(f"{day}/{run_name}: {loop_summary(Path(root) / day / run_name)}")
