"""Replay a Claude Code run's Bash calls against CodeScribe's bounded shell.

WHY THIS EXISTS. ccloop and csloop run the same design pattern over the same
Spec/Plan, and the headline difference between them is EXECUTION POLICY:
CodeScribe hands its author a bounded shell enforced in code, while the loop
workflow states the same restrictions as prose to an agent with an
unrestricted one (see `.claude/workflows/loop.js`, divergence #6). That
difference is the intervention, not a nuisance variable — so the figures and
tables have to size it, and sizing it by hand would go stale the first time a
ccloop run is added.

`divergence_summary` answers the one question the note needs: of the Bash calls
a ccloop run actually made, what fraction would CodeScribe's BashTool have
refused to execute? Everything here mirrors the real validator rather than
approximating it, and the mirrored constants carry their source location so a
drift in either copy is findable.

WHAT THIS IS NOT. It is a replay of the *shell gate only*, on calls that were
already issued by an agent that knew it had no gate. It does not predict what a
sandboxed agent would have done instead — an agent told `cd` is unavailable
writes root-relative paths from the start rather than issuing the same call and
losing it. So read the fraction as "how far outside the policy this run's
observed behaviour sits", never as "how much of this run would have failed".

Nor does it cover the rest of AgentPolicy (iteration caps, repeated-call
blocking, output truncation): those bound how MANY calls happen, which a replay
of recorded calls cannot observe. The shell gate is the part that is decidable
from the archive alone.

Mirrored from codescribe/lib/_tools.py, read 2026-09-12:
  BashTool._BLOCKED_CHARS        (line 283)
  BashTool._DEFAULT_ALLOWED      (line 284)
  BashTool.validate_command      (line 366) — and its ORDER, which decides which
                                 bucket a call is counted in: the blocked-character
                                 test runs BEFORE the allowlist test, so
                                 `cd foo && ls` is a syntax rejection, not a
                                 `cd` rejection.
  make_tools                     (line 707) — allowed = _DEFAULT_ALLOWED | the task
                                 file's [tools].bash. The union is the reason the
                                 mcfm-translate author's shell is thirteen commands
                                 and not the two that file names.
"""

import json
import shlex
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib

# codescribe/lib/_tools.py:283 — rejected anywhere in the command string, which
# is what takes out pipes, redirects, chaining, command substitution and
# multi-line scripts in one rule.
BLOCKED_CHARS = set("|&;><`$\n\r")

# codescribe/lib/_tools.py:284 — the base allowlist every bounded BashTool gets
# before the task file adds to it.
DEFAULT_ALLOWED = frozenset({
    "ls", "pwd", "find", "grep", "head", "tail", "wc", "git", "test", "echo", "sed",
})

# Verdicts, in the order validate_command decides them.
ALLOWED = "allowed"
BLOCKED_SYNTAX = "blocked:syntax"
BLOCKED_UNPARSEABLE = "blocked:unparseable"
BLOCKED_COMMAND = "blocked:command"
BLOCKED_FLAG = "blocked:flag"
BLOCKED_PATH = "blocked:path-escape"


def task_file_bash_allow(task_file):
    """The `[tools].bash` list from a CodeScribe task file, as a set.

    Read from the archived loop.toml rather than hardcoded, so a run whose task
    file granted a different shell is measured against ITS policy. Returns an
    empty set for a missing or malformed file — the caller still has
    DEFAULT_ALLOWED, which is what CodeScribe would fall back to.
    """
    task_file = Path(task_file)
    if not task_file.exists():
        return set()
    try:
        with open(task_file, "rb") as fh:
            meta = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return set()
    return set((meta.get("tools") or {}).get("bash") or [])


def classify_command(command, allowed, root=None):
    """One Bash command string -> a verdict constant.

    Mirrors BashTool.validate_command's order exactly; see the module docstring
    for why the order is load-bearing. `root` enables the escapes-the-workdir
    check, which is skipped when None (BashTool skips it when cwd is None).
    """
    if not command:
        return BLOCKED_UNPARSEABLE

    if any(ch in command for ch in BLOCKED_CHARS):
        return BLOCKED_SYNTAX

    try:
        parts = shlex.split(command)
    except ValueError:
        return BLOCKED_UNPARSEABLE
    if not parts:
        return BLOCKED_UNPARSEABLE

    exe = parts[0]
    if exe not in allowed:
        return BLOCKED_COMMAND

    if exe in {"find", "bfs", "gfind"} and any(
        a in {"-exec", "-execdir", "-ok", "-okdir", "-delete"} for a in parts[1:]
    ):
        return BLOCKED_FLAG
    if exe == "rg" and any(
        a in {"--pre", "--pre-glob"} or a.startswith(("--pre=", "--pre-glob="))
        for a in parts[1:]
    ):
        return BLOCKED_FLAG
    if exe == "git":
        if "config" in parts[1:]:
            return BLOCKED_FLAG
        git_flag_prefixes = (
            "--exec-path", "--git-dir", "--work-tree", "--namespace",
            "--upload-pack", "--receive-pack", "--upload-archive",
        )
        if any(
            a in {"-c", "-p", "--paginate"} or a.startswith(git_flag_prefixes)
            or "ext::" in a or "fd::" in a
            for a in parts[1:]
        ):
            return BLOCKED_FLAG

    if root is not None:
        root = Path(root).resolve()
        for arg in parts[1:]:
            if arg.startswith("-"):
                continue
            candidate = Path(arg)
            candidate = (root / candidate).resolve() if not candidate.is_absolute() \
                else candidate.resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                return BLOCKED_PATH

    return ALLOWED


def _bash_commands(run_dir):
    """Every Bash command string issued in a Claude Code run's transcripts.

    Counts ISSUED calls, not answered ones: the question is what the agent
    tried to run, and a call the harness never answered was still a call the
    policy would have had to judge.
    """
    commands = []
    for workflow_dir in sorted(Path(run_dir).glob("workflow-wf_*")):
        for agent_path in sorted(workflow_dir.glob("agent-*.jsonl")):
            with open(agent_path) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    if record.get("type") != "assistant":
                        continue
                    content = record.get("message", {}).get("content")
                    if not isinstance(content, list):
                        continue
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "tool_use" and block.get("name") == "Bash":
                            command = (block.get("input") or {}).get("command")
                            if command:
                                commands.append(command)
    return commands


def replay_run(run_dir, task_file=None, root=None):
    """{verdict: count, "total": n, "blocked_fraction": f} for one run.

    `task_file` is the run's archived CodeScribe task file, whose [tools].bash
    is unioned with DEFAULT_ALLOWED. When None, the archived
    `dev/transformations/*/loop.toml` inside the run is used if there is
    exactly one — the archives carry it even for ccloop runs, which never read
    it, precisely so the comparison policy is recoverable from the run itself.
    """
    run_dir = Path(run_dir)
    if task_file is None:
        candidates = sorted(run_dir.glob("dev/transformations/*/loop.toml"))
        task_file = candidates[0] if len(candidates) == 1 else None

    allowed = set(DEFAULT_ALLOWED)
    if task_file is not None:
        allowed |= task_file_bash_allow(task_file)

    counts = {}
    commands = _bash_commands(run_dir)
    for command in commands:
        verdict = classify_command(command, allowed, root=root)
        counts[verdict] = counts.get(verdict, 0) + 1

    total = len(commands)
    allowed_n = counts.get(ALLOWED, 0)
    counts["total"] = total
    counts["allowed_commands"] = sorted(allowed)
    counts["blocked_fraction"] = (total - allowed_n) / total if total else 0.0
    return counts


def divergence_summary(experiments_root, runs):
    """{run_name: replay} for every run in `runs`, plus a "range" key.

    `runs` is a (day, run_name, ...) registry; runs with no Bash calls at all
    (every csloop run — its shell calls are in loop/metadata, not a Claude Code
    transcript) are skipped rather than reported as 0%, since "no transcript"
    and "nothing blocked" are not the same statement.
    """
    experiments_root = Path(experiments_root)
    out = {}
    for day, run_name, *_ in runs:
        replay = replay_run(experiments_root / day / run_name)
        if replay["total"]:
            out[run_name] = replay
    fractions = [r["blocked_fraction"] for r in out.values()]
    out["range"] = (min(fractions), max(fractions)) if fractions else None
    return out


if __name__ == "__main__":
    import sys

    _HERE = Path(__file__).resolve().parent
    sys.path.insert(0, str(_HERE))
    from generate_graphs import RUNS  # the registry, so this matches the figures

    root = _HERE.parent / "experiments"
    summary = divergence_summary(root, RUNS)
    span = summary.pop("range")
    for run_name, replay in summary.items():
        total = replay["total"]
        print(f"{run_name}: {total} Bash calls, "
              f"{replay['blocked_fraction']:.0%} outside CodeScribe's bounded shell")
        for verdict in (ALLOWED, BLOCKED_SYNTAX, BLOCKED_COMMAND, BLOCKED_FLAG,
                        BLOCKED_PATH, BLOCKED_UNPARSEABLE):
            if replay.get(verdict):
                print(f"    {verdict:22s} {replay[verdict]:4d}")
        print(f"    allowlist ({len(replay['allowed_commands'])}): "
              f"{' '.join(replay['allowed_commands'])}")
    if span:
        print(f"\nrange across runs with a transcript: {span[0]:.0%}-{span[1]:.0%}")
