# Fortran → C++ plan

This file says how to run step 1. The rewrite rules and correctness bar are in
`desired_spec.md`.

> This Plan is the policy: it selects and orders the work over the ready set (see *When to
> stop*). The correctness contract — objective `f`, invariants `I`, oracle `V`, and status set
> `Σ` — lives in `desired_spec.md`; on conflict the Spec governs.
>
> Authority: the AI may modify only `agent_log.md`; `current_plan.md` and `desired_spec.md` are
> human-owned.

## Each round

1. Refresh readiness (see Tools).
2. Continue the open group if one exists. Otherwise check the gate (see Approval gate) before
   opening a new group.
3. Rewrite ready files and wire them in (see Resolution; the rewrite rules are the Spec).
4. Build and verify each file (see Verify); record each result in `agent_log.md` (see Log file).
5. Stop per When to stop; otherwise keep going.

## Log file

Keep the changing worklist in `agent_log.md` in this folder. Create it if missing and
keep it current. Use it for ready files, review groups, and per-file status. Keep durable prose
notes in the session log at the end of this file.

Record each finished file as:

- `- [x] <file> — VERIFIED (worst Δrel <value>)`
- `- [x] <file> — TRANSLATED (<reason>)`
- `- [x] <file> — FAILED (<what went wrong>)`

Use paths like `software/mcfm/src/...`.

## Approval gate

Review groups live under headings starting with `Group` in `agent_log.md`. Humans do not edit
`agent_log.md`. Human approvals live in `approvals.toml` in this folder and should normally be
recorded with:

```
python3 dev/workflow.py approve mcfm-translate --latest-blocking
```

or, to approve the oldest pending completed group,

```
python3 dev/workflow.py approve mcfm-translate --latest
```

or, for an explicit group,

```
python3 dev/workflow.py approve mcfm-translate "Group ..." --by <name>
```

Use the gate only when deciding whether to start a new group:

```
python3 dev/workflow.py gate mcfm-translate
```

Interpret it this way:

- If a group is still open, you may keep working inside that same group.
- A completed group containing `FAILED` requires approval before the next group starts.
- Otherwise, up to 3 completed groups may accumulate before approval is required.
- A gate failure blocks new-group creation, not builds, fixes, or verification inside the
  current open group.
- The gate checks only whether a group is approved; it does not interpret `approvals.toml`
  `review_note` text.
- After a group is approved, agents should read any matching approval record in
  `approvals.toml` before continuing work related to that group.
- Treat review notes as binding human guidance for that group unless a later human
  instruction supersedes them.
- If a review note changes scope or forbids an action, revise that same approved group
  rather than opening a replacement group just to apply the review note.
- A revision keeps the original approval logic unchanged: the group remains the same group,
  but the agent must update code and `agent_log.md` so the final recorded outcome matches the
  approved human guidance.
- If a review note conflicts with an already-logged result, treat the group as follow-up work
  in place: fix the affected files, update that group's entries, and add a session-log note
  describing the revision before starting unrelated new-group work.

Stop for human review only when the gate blocks the next group.

## Tools

Run these from the project root. Prefer the unified workflow interface:

- `python3 dev/workflow.py refresh`
  - refresh the readiness map and symbol index
- `python3 dev/workflow.py draft <file.f>`
  - make a rough draft and dependency hints
- `python3 dev/workflow.py verify <file.cpp> -- <process>`
  - decide VERIFIED vs TRANSLATED
- `python3 dev/workflow.py gate mcfm-translate`
  - enforce the human approval policy between completed groups
- `python3 dev/workflow.py approve mcfm-translate --latest-blocking`
  - approve the exact group currently blocking the gate
- `python3 dev/workflow.py approve mcfm-translate --latest`
  - approve the oldest pending completed group
- `python3 dev/workflow.py approve mcfm-translate --list-pending`
  - show pending completed groups waiting for approval
- `python3 dev/workflow.py approve mcfm-translate "Group ..." --by <name>`
  - record a human approval for a specific group in `approvals.toml`
- `python3 dev/workflow.py approvals mcfm-translate --group "Group ..."`
  - show the approval record, including any review note, for a specific group
- `python3 dev/workflow.py approvals mcfm-translate --latest-approved`
  - show the most recent approved group and its review note for revision follow-up
- `jobrunner submit tests/mcfm`
  - full MCFM build + test run; run this before verification if MCFM is not yet built

The low-level scripts under `dev/tools/` remain available, but `dev/workflow.py` is the preferred interface.

## Resolution: which files to do next

1. Only rewrite **ready** files from `dev/tmp/assets/roadmap_metrics.tsv`:
   - `deps == 0`
   - `blind == 0`
   - no generated `.cpp` yet
2. Optional: limit one run to one top-level `src/` folder.
3. Group ready files for review:
   - same folder or test topic
   - about 5 files per group
   - headings must start with `Group`
4. If there is already an open group, keep filling and fixing that group before opening another.
5. Rewrite the group, wire it into the folder's `CMakeLists.txt`, build, and verify each file.
   - After converting a Fortran source, move the original `.f`/`.F` into `deprecated/` under the
     same directory.
   - Follow the Spec's Output shape and Header/source structure for the translated files.
6. After a group is completed, check the gate before opening the next one.
7. After any required approval, refresh the roadmap again before picking more work.

The map exists so a file is only rewritten after its callees are already available in C++.

## Shell notes

CodeScribe bash is restricted. In practice:

- use plain relative paths like `software/mcfm/src/...`
- no `cd`, pipes, redirects, or `$VARIABLES`

## Verify

Mark the statement that writes the file's main output with `// @coverage-probe`, then run:

```
python3 dev/workflow.py verify <file.cpp> -- <process>
```

Use the process mapped from the file's top-level folder in the Spec. If verification work is
needed and MCFM is not built yet, run `jobrunner submit tests/mcfm` first.

Interpret results as:

- `COVERED` → mark `VERIFIED` once the restored build still matches
- `NOT COVERED` → mark `TRANSLATED`

If build or verification fails, keep fixing the current group unless the gate is blocking the
start of a later group.

## When to stop

The *ready set* is the set of ready, not-yet-settled files. Each settled file leaves the
ready set and the readiness graph is acyclic, so the pass terminates. Stop only when one of
these is true:

- a completed group needs human approval before the next group can start
- the ready set is empty (no ready file to work on)
- a real blocker requires a person

Otherwise continue editing, building, testing, and verifying.

## Notes / session log

- Header/source structure and the infrastructure-folder coverage mapping (mark `TRANSLATED`)
  follow the Spec.
- If coverage shows no change, retry after a caller is rewritten.
- If numbers disagree, mark `FAILED` with the symptom instead of guessing.
- Add a dated note per session: what you changed, what remains, and any human decision needed.
