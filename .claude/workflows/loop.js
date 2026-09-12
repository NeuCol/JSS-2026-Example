// Workflow: loop — a bounded author→review loop over one dev/transformations/<name> step,
// shaped after CodeScribe's prompt_loop (codescribe/lib/_loop.py) but configured the way
// transform.js is: point it at a transformation folder and it reads that folder's own
// desired_spec.md (Spec) and current_plan.md (Plan) — never dev/transformations/*/loop.toml,
// which belongs to CodeScribe and is a different orchestrator's config, not a task file for
// this workflow. Ignoring loop.toml here follows the same repo-wide rule transform.js states
// (and CLAUDE.md/AGENTS.md restate): it is not read, ever.
//
//   for loop = 1..agentLoops:
//     AUTHOR   one agent reads the Spec/Plan (or trusts the injected summary after loop 1),
//              does the work, and reports STATUS + PLAN + check output + NEXT STEPS
//              if STATUS: COMPLETE  → stop early, REVIEW is skipped entirely
//     REVIEW   one agent cross-references the author's claims against the harness-held
//              action summary and writes review_output.toml
//              if no pending items and no blocker → stop early
//
// This is still deliberately NOT transform.js: transform.js is a five-phase, group-at-a-time,
// approval-gated pipeline that fans out one author agent per unit, with per-run state re-read
// from agent_log.md every triage. This workflow keeps _loop.py's simpler shape instead — one
// author agent working the whole Spec/Plan per loop, cross-loop state held in memory rather
// than re-derived from a worklist file — for the cases where that shape fits better: quick
// iteration on a transformation, or a step whose Plan does not define discrete parallel units.
//
// State relay, mirroring the original's design note:
//   - Within a loop (iteration → iteration): the agent's own message history.
//   - Across loops (loop N → loop N+1): plain JS objects held right here in this script.
//     The harness builds the LoopSummary and injects it into the next loop's task string.
//     Agents never read state files to orient themselves.
//
// ---------------------------------------------------------------------------
// Known divergences from _loop.py (each one is forced by the harness, not a choice):
//
// 1. LoopSummary provenance. In CodeScribe the summary is computed by the harness from
//    RunResult.tool_results — the agent cannot misreport what it did. A workflow script
//    cannot see its subagents' tool calls, so the author agent SELF-REPORTS the same
//    fields through AUTHOR_SCHEMA. Everything downstream (the injected context block, the
//    review agent's "verified actions" block) is byte-for-byte the same shape; only the
//    trust level differs. Treat the review phase's cross-referencing as weaker here, and
//    say so when reporting results.
// 2. Tool restriction. _loop.py hands the review agent a narrowed tool list (read/glob/
//    write + a bounded bash allowlist) and enforces a protected task file and a writable
//    root. This harness has no per-agent tool policy, so the same restrictions are stated
//    as hard rules in the review prompt. RunResult.rejected_calls therefore has no
//    equivalent: `rejected` is reported by the agent (tool calls the user or a hook denied)
//    and may simply be empty.
// 3. Execution policy. CodeScribe's Agent (codescribe/lib/_agent.py) enforces a whole
//    AgentPolicy per phase, in code: max_iterations MODEL TURNS (30 for author,
//    max(6, n/2)=15 for review), max_tool_calls_total=120 EXECUTIONS, max_calls_per_
//    iteration=10, identical (tool,args) blocked after max_repeated_calls=2 (x3 for
//    `read`), a BLOCKED nudge after 3 all-failing iterations, and single tool outputs
//    truncated into history at 8000 chars. This harness exposes no policy knobs on
//    agent(), so all of it is stated to the agent instead and only the total tool budget
//    is enforced — and only as a recorded overrun at the loop boundary, since a workflow
//    script cannot interrupt a subagent mid-flight. Note the scope: max_tool_calls_total
//    is PER PHASE (Agent.run() creates a fresh RunState each call), so it refreshes every
//    loop rather than bounding the run.
//
//    An earlier revision of this file called agent_iterations "a tool-call budget". It is
//    not: it bounds MODEL TURNS, and a CodeScribe turn carries up to 10 tool calls. Measured
//    over the 38 archived author and review phases in the 08-27/08-28-2026 figure scope
//    (evals/experiments/*/codescribe-*/loop/metadata/loop_*.toml): mean 2.41 calls per turn,
//    range 0.50-4.60. So "30" buys a csloop author around 71 tool executions per loop
//    (observed author-phase totals 25-89). Claude Code emits exactly ONE tool call per turn,
//    so stating "30 turns" here imposed a ~2-3x TIGHTER budget than csloop actually runs
//    under. The comparable bound is the one AgentPolicy states in a harness-independent
//    unit — tool executions — so that is what this file now states and tracks.
//
//    Two corrections to what an earlier revision of this note asserted, both checked against
//    the archives rather than assumed:
//      - "every archived csloop author phase runs to max_iterations and is hard-cut there"
//        is false. 25 of 38 phases stop on `max_iterations`; the other 13 stop on
//        `final_text`, i.e. the agent finished early. The cap binds often, not always.
//      - max_tool_calls_total=120 never actually binds in the archived corpus: no phase
//        records stop_reason `tool_budget`. For csloop the operative limit is
//        max_iterations; 120 is a ceiling above observed behaviour, which is why it is a
//        safe number to copy here rather than a tight one.
//
//    THE RUNS ARCHIVED ON 09-11-2026 DID NOT RUN UNDER THIS. They ran the revision that said
//    "about 30 tool-calling turns", with no maxToolCalls at all, and the two models read it
//    very differently: the opus-5 run averaged 34 tool calls per loop across its five loops
//    (49/42/44/22/14), while the sonnet-5 run spent 139 in its single loop. An advisory
//    budget is not a budget, and it is not a like-for-like substitute for one enforced in
//    code. Treat those two runs' throughput and per-file numbers as measured under a tighter
//    and unevenly applied budget than csloop's — a calibration error, and separate from the
//    execution-policy difference in #6, which is the intended contrast.
// 4. Task source. _loop.py reads a single task file (its own chat-template format) and
//    pre-injects it on loop 1 so that loop skips an orientation round-trip. This workflow
//    has no single task file to pre-inject — the Spec and Plan are two separate, often long,
//    plain-Markdown files, the same ones transform.js reads — so every loop tells the author
//    to read them itself, exactly like transform.js's own Triage prompt does. There is
//    therefore no injectTask option here; it would have nothing to inject.
// 5. Persistence. CodeScribe writes run.toml / state.toml / author.toml / metadata/ under
//    .codescribe/loop/. This script cannot write files, and archive_experiment.py skips
//    loop artifacts entirely when --loop-dir is .claude (this run's real telemetry is the
//    session jsonl transcripts). Only review_output.toml is still written, by the review
//    agent itself, as an operator-facing artifact for this run — it is no longer trying to
//    match CodeScribe's on-disk layout for cross-harness comparison, since the two harnesses
//    no longer consume the same task file. Token accounting comes from budget.spent()
//    instead of run.toml's cumulative counters.
//
// 6. Author tool policy. _loop.py builds the AUTHOR's tools with
//    make_tools(workdir, bash_allow=<the task file's [tools].bash>, protected_paths=
//    {task_file}), through a bounded BashTool.
//
//    An earlier revision of this note said that allowlist "is exactly ['jobrunner',
//    'python3']" and called the result "a two-command shell". That is wrong, and the error
//    is in the direction that overstates the gap: make_tools UNIONS the task file's list
//    with BashTool._DEFAULT_ALLOWED (codescribe/lib/_tools.py:718), so the mcfm-translate
//    author actually gets THIRTEEN commands —
//        ls pwd find grep head tail wc git test echo sed   (the default set)
//      + jobrunner python3                                 (this task file's [tools].bash)
//    — plus per-command hardening (find -exec/-delete rejected, sed forced to --sandbox,
//    git config/-c/--git-dir/ext:: rejected, rg --pre rejected).
//
//    What actually does the work is not the command list but the other two rules:
//      - _BLOCKED_CHARS = "|&;><`$\n\r" rejected anywhere in the command string, which bans
//        pipes, redirects, chaining, command substitution and multi-line scripts outright;
//      - a fixed cwd with no `cd`, plus every non-flag argument required to resolve inside
//        the workdir.
//    Replaying the 09-11-2026 runs' Bash calls through that validator (see
//    evals/analysis/shell_policy.py, which mirrors it) rejects 95% of the opus-5 run's 216
//    calls and 91% of the sonnet-5 run's 113 — in both cases mostly on shell syntax, then
//    on `cd`. So this remains by far the largest difference between the two arms; only the
//    description of it was wrong.
//
//    Read that as the INTERVENTION, not as noise to be eliminated. Enforced bounded
//    execution is what CodeScribe is for, and a ccloop run with an unrestricted shell is the
//    control it is measured against. `bashAllow` below exists so a matched-policy run can be
//    done deliberately (see "Running a file-by-file comparison"), and it is OFF by default
//    precisely because turning it on changes what the experiment measures.
//
//    It cannot be ENFORCED here (no per-agent tool policy, as #2 says) — `bashAllow` states
//    the restriction to the author as a hard rule, the way #2 already does for the reviewer.
//    A prose rule and a validator are not the same instrument, and #3 shows what happens
//    when they are treated as one.
//
// ---------------------------------------------------------------------------
// RUNNING A FILE-BY-FILE COMPARISON against a csloop run
//
// evals/analysis attributes cost, minutes and tool calls to individual source files, and
// compares those per-file columns across harnesses (see per_file_effort.py). A ccloop run
// only lands in that comparison if it satisfies the conditions below. They are listed here
// because every one of them is a property of how the RUN is set up, not of the analysis.
//
// A. Same work, or the per-file numbers do not divide comparable work.
//    - Same transformation folder, and the same Spec/Plan content as the csloop arm. Note
//      the two harnesses reach the same text by different routes: csloop is handed
//      loop.toml, whose whole body is "read current_plan.md, then desired_spec.md" (its
//      author's first two tool calls in every archived run are exactly those reads), while
//      this workflow names the two files directly. Same instructions, different envelope —
//      so #4's "no single task file to pre-inject" costs less than it sounds like.
//    - Same submodule fork point. generate_graphs checks every run's branch merge-base
//      against git_file_counts.BASE_REF, and a run that forked elsewhere is out of scope.
//    - Archive with evals/tools/archive_experiment.py so the run gets a branch under
//      evals/<day>/<name>; `files settled` is the git diff of that branch, never the
//      agent's own checklist.
//
// B. Name the run so the harness classifies it.
//    evals/analysis/harness.py keys off the directory name, and `ccworkflow-loop-*` and
//    `ccloop-*` both mean ccloop. Anything else beginning `ccworkflow-` is read as the
//    multi-agent workflow and will be parsed with the wrong module. `harness.detect_harness`
//    re-derives the answer from the journal's Author/Review phase labels and
//    `verify_harness_names` reports any run where the two disagree — so a misnamed run is
//    caught, but only after it has already been mis-parsed once.
//
// C. Write file paths the attributor can see. THIS IS THE ONE MOST EASILY GOT WRONG.
//    ccloop effort is APPORTIONED: per_file_effort matches each executed tool call's
//    arguments against `src/<Module>/<name>.<ext>` (SOURCE_PATH_RE) and splits the run's
//    cost across whichever settled units the call names. A call that names no unit falls
//    into the unattributed pool and is spread proportionally.
//    A `cd software/mcfm/src/W2jet` followed by bare filenames therefore attributes
//    NOTHING, even though every one of those calls is doing per-file work. In the 09-11
//    runs, counted over the attributable executed calls per_file_effort sees:
//      opus-5    219 calls, 94% unattributed → ~13 carry the whole per-file split.
//                It issued `cd` 77 times, and 54 further calls name a settled unit by
//                basename only, so most of its real file work is invisible to the matcher.
//      sonnet-5  160 calls, 74% unattributed → ~41 carry the split. It worked through
//                Read/Write/Edit with full paths; only 10 calls are basename-only.
//    Both numbers are honest, but C6's per-file column rests on ~13 calls and C7's on ~41,
//    and they are not equally trustworthy — which is a difference in how the two models
//    drove the shell, not a difference the analysis introduced.
//    Worth noticing WHY csloop does not have this problem: its BashTool has a fixed cwd and
//    no `cd`, so every path it writes is already root-relative and matchable. Bounded
//    execution buys attributable telemetry as a side effect. If you want a ccloop run whose
//    per-file split is as tight as csloop's, `bashAllow` is the knob that gets you there —
//    which is also why a matched-policy run is worth doing even though it is no longer the
//    control.
//
// D. Match the budget in the unit both harnesses share.
//    csloop's author does ~71 tool EXECUTIONS per loop (see #3). Set `maxToolCalls` to the
//    same order and leave `agentIterations` alone; do not assume a turn means the same thing
//    on both sides. A run whose budget was stated in the wrong unit is not comparable on
//    files-settled or on any per-file column, and nothing downstream can correct for it.
//
// E. Decide, and record, whether you are running the control or the matched arm.
//      bashAllow: null                      → the control. Unrestricted shell; this is what
//                                             R12/R13 are, and what the published
//                                             ccloop-vs-csloop gap measures.
//      bashAllow: ["jobrunner","python3"]   → the matched arm. Note this reproduces the same
//                                             THIRTEEN-command shell csloop gets, because
//                                             the prompt text built from it also states the
//                                             default set; it does not reproduce enforcement.
//    Say which in the run name. The two are different configurations and averaging them
//    would answer neither question.
//
// F. What still will not match, even with A-E done.
//    - Enforcement itself: every AgentPolicy rule here is prose, so compliance is the
//      model's choice and varies by model (#3).
//    - LoopSummary provenance: self-reported here, harness-computed there (#1).
//    - Attribution method for ccworkflow only: "exact" per-unit author agents, versus the
//      apportioned split ccloop and csloop share. ccloop-vs-csloop per-file columns ARE
//      like-for-like; neither is like-for-like against ccworkflow.
//    - Review-phase telemetry: csloop's logs/toolusage.toml covers the author phase only,
//      while a Claude Code transcript timestamps every phase. per_file_effort's "timed"
//      method reports which via `duration_source`/`phases_covered`; do not difference a
//      measured/author total against a derived/all one.
//
// ---------------------------------------------------------------------------
// Config (args): transformation (required — a folder under dev/transformations/),
//                agentLoops (5), agentIterations (30), maxToolCalls (120),
//                bashAllow (null = unrestricted, the control arm; e.g. ["jobrunner",
//                "python3"] for the matched arm — it EXTENDS CodeScribe's default set the
//                way make_tools does, giving the same thirteen commands csloop gets, and
//                also states the no-cd / no-pipes / root-relative-paths rules. See
//                "Running a file-by-file comparison" above before choosing),
//                workdir ('.'), loopDir ('.claude'),
//                archive (true — run the Metadata phase),
//                model / authorModel / reviewModel / metadataModel,
//                effort ('high' — explicit, not inherited from the session).
//
// Start it with:
//   Run loop for dev/transformations/<name>

export const meta = {
    name: 'loop',
    description: 'Bounded author→review loop over one dev/transformations/<name> step\'s desired_spec.md + current_plan.md, shaped after CodeScribe\'s prompt_loop (codescribe/lib/_loop.py). Never reads that folder\'s loop.toml — that belongs to CodeScribe.',
    whenToUse: 'Point it at a transformation folder via args:{transformation:"mcfm-translate"} for a single-agent-per-loop author→review cycle over its Spec/Plan, instead of transform.js\'s parallel-units-per-group pipeline. Good for quick iteration or a step with no discrete parallel units. Optional: agentLoops, agentIterations, model/authorModel/reviewModel, effort, archive:false.',
    phases: [{
            title: 'Author'
        },
        {
            title: 'Review'
        },
        {
            title: 'Metadata',
            model: 'claude-sonnet-5'
        },
    ],
}

// ---------------------------------------------------------------------------
// Config  (mirrors PromptLoopRunner's fields / __post_init__, but sourced like transform.js)
// ---------------------------------------------------------------------------

const cfg = typeof args === 'string' ? JSON.parse(args) : args || {}

const TRANSFORMATION = (cfg.transformation || '')
    .replace(/^dev\/transformations\//, '')
    .replace(/\/$/, '')
if (!TRANSFORMATION) {
    throw new Error(
        'args.transformation is required — a folder under dev/transformations/, e.g. "mcfm-translate"'
    )
}

const DIR = `dev/transformations/${TRANSFORMATION}`
const SPEC = `${DIR}/desired_spec.md`
const PLAN = `${DIR}/current_plan.md`
const LOG = `${DIR}/agent_log.md`

const WORKDIR = cfg.workdir || '.'
const AGENT_LOOPS = cfg.agentLoops ?? 5
// MODEL TURNS, not tool calls — _agent.py's `for iteration in range(max_iterations)`.
const AGENT_ITERATIONS = cfg.agentIterations ?? 30
// _loop.py: max_iterations=max(6, agent_iterations // 2) for the review agent.
const REVIEW_ITERATIONS = Math.max(6, Math.floor(AGENT_ITERATIONS / 2))

// AgentPolicy (codescribe/lib/_agent.py) — the execution bounds every CodeScribe phase
// runs under. Only MAX_TOOL_CALLS is enforceable here, and only between loops; the rest
// are stated to the agent, since this harness has no policy knobs on agent(). They are
// named and defaulted to CodeScribe's own values so a change there is a one-line change
// here rather than a silent drift in what "the same loop" means.
// PER LOOP, not per run. Agent.run() builds a fresh RunState() every call and _loop.py
// builds a fresh author Agent every loop, so tool_calls_total resets at each phase; a
// 5-loop csloop run may spend up to 5x this. Making it a run ceiling would have been ~5x
// TIGHTER than the harness it is meant to match.
const MAX_TOOL_CALLS = cfg.maxToolCalls ?? 120 // AgentPolicy.max_tool_calls_total
const MAX_CALLS_PER_ITERATION = 10 // AgentPolicy.max_calls_per_iteration
const MAX_REPEATED_CALLS = 2 // AgentPolicy.max_repeated_calls
const READ_REPEAT_MULTIPLIER = 3 // AgentPolicy.read_repeat_multiplier

// null = unrestricted (this harness's default). An array states csloop's own bash
// allowlist to the author as a hard rule — see divergence #6.
// CodeScribe's make_tools does `allowed = BashTool._DEFAULT_ALLOWED | bash_allow` — the task
// file's list EXTENDS a default set, it does not replace it (codescribe/lib/_tools.py:718).
// Mirroring that here matters: passing bashAllow:["jobrunner","python3"] to match
// mcfm-translate's task file must produce csloop's actual thirteen-command shell, not a
// two-command one that is stricter than anything csloop ever enforced. Kept verbatim from
// _tools.py:284 so a drift in either copy is greppable.
const CS_DEFAULT_BASH_ALLOW = [
    'ls', 'pwd', 'find', 'grep', 'head', 'tail', 'wc', 'git', 'test', 'echo', 'sed',
]
const BASH_ALLOW = Array.isArray(cfg.bashAllow) && cfg.bashAllow.length ?
    [...new Set([...CS_DEFAULT_BASH_ALLOW, ...cfg.bashAllow])].sort() :
    null

// End the run when a loop overruns its per-loop tool budget. Off by default: see the
// overrun handling in the main loop for why recording beats stopping.
const STOP_ON_OVERRUN = cfg.stopOnOverrun ?? false

// This workflow's own operator-facing artifact directory — unrelated to loop.toml, and not
// an attempt to mirror CodeScribe's .codescribe/loop/ layout (see divergence #5 above).
const LOOP_DIR = (cfg.loopDir || '.claude').replace(/\/$/, '')
const RUN_DIR = `${LOOP_DIR}/loop`
const REVIEW_OUTPUT = `${RUN_DIR}/review_output.toml`

const DO_ARCHIVE = cfg.archive ?? true

// Both phases inherit the session model unless overridden — the original runs author and
// review on the SAME neural model, so keep them equal unless you are deliberately varying
// one of them as the independent variable of a comparison.
const AUTHOR_MODEL = cfg.model || cfg.authorModel
const REVIEW_MODEL = cfg.model || cfg.reviewModel
// Pinned, NOT inherited from cfg.model. Archival is instrumentation, not the thing being
// measured, and letting it follow the arm under test makes the cheap arm's overhead cheap
// and the expensive arm's expensive — on 09-11-2026 the same archival phase cost $2.07 on
// the opus arm and $1.15 on the sonnet one, 4% and 9% of their runs. This also makes the
// code agree with meta.phases above, which already declares sonnet-5 for this phase and
// was being silently overridden by cfg.model.
const METADATA_MODEL = cfg.metadataModel || 'claude-sonnet-5'
// Analog of _loop.py's `reason` / reasoning_effort — and DEFAULTED, not left
// undefined. Both 09-11-2026 runs passed no effort and every one of their
// assistant messages came back at `effort: high`, inherited from the session
// rather than chosen: the runs were configured by whatever the operator's
// session happened to be set to, and nothing in the archive said so. Naming a
// default makes the setting a recorded run parameter that the manifest carries.
//
// Note this does NOT make the arms equal. CodeScribe reaches "reasoning on" via
// reason=true -> thinking=display:summarized,type:adaptive; there is no
// documented mapping from an effort level onto that, so adaptive-vs-high stays
// an uncontrolled difference between the harnesses. It is now at least an
// explicit one. Pass effort to vary it deliberately.
const EFFORT = cfg.effort ?? 'high'

const ARCHIVE_SPEC = 'evals/archive.toml'
const ARCHIVE_TOOL = 'evals/tools/archive_experiment.py'

// Repeated in every prompt below — the same note transform.js gives its agents. The Plans in
// this repo were written with CodeScribe (a different, more restricted runner) in mind, and
// loop.toml is CodeScribe's own config — not ours, and never read by this workflow.
const NOTES = BASH_ALLOW ?
    `Shell policy for this run: through the Bash tool you may ONLY invoke
${BASH_ALLOW.map((c) => `\`${c}\``).join(', ')} — nothing else, and in particular no \`cd\`
and no \`cat\`. Every command must be a single simple command: no pipes, redirects, shell
variables, command substitution, \`&&\`/\`;\` chaining or multi-line scripts. Paths are always
written relative to the repository root (\`software/mcfm/src/W2jet/atree.f\`, never a bare
\`atree.f\` after moving directory), because there is no moving directory. This mirrors the
bounded shell the comparison harness enforces in code; treat it as a hard rule, and if
something cannot be done within it, say so rather than working around it. Do not read
or follow ${DIR}/loop.toml — it belongs to that other orchestrator (CodeScribe) and has
nothing to do with this run.` :
    `You have normal Bash tool access (cd, pipes, redirects, variables all work) —
ignore any note in the Plan about a restricted shell; that applies to a different runner, not
you. Do not read or follow ${DIR}/loop.toml — it belongs to that other orchestrator
(CodeScribe) and has nothing to do with this run.`

// ---------------------------------------------------------------------------
// Schemas — the structured channel that stands in for RunResult
// ---------------------------------------------------------------------------

// Mirrors LoopSummary's action fields plus the parts of the final_answer that _loop.py
// parses out of free text (extract_status / extract_pending_items).
const AUTHOR_SCHEMA = {
    type: 'object',
    properties: {
        status: {
            type: 'string',
            enum: ['COMPLETE', 'INCOMPLETE'],
            description: 'COMPLETE only if every task is implemented AND all checks pass',
        },
        plan: {
            type: 'string',
            description: 'the PLAN you followed, final form, 3–7 bullets'
        },
        checkOutput: {
            type: 'string',
            description: 'exact verbatim output of the checks you ran — never paraphrased, never invented',
        },
        nextSteps: {
            type: 'array',
            items: {
                type: 'string'
            },
            description: 'ONLY when status is INCOMPLETE: 3–5 concrete next steps for the following loop',
        },
        filesWritten: {
            type: 'array',
            items: {
                type: 'string'
            },
            description: 'paths you CREATED with a write, one per write call'
        },
        filesEdited: {
            type: 'array',
            items: {
                type: 'string'
            },
            description: 'paths you MODIFIED with an edit, one per edit call'
        },
        filesRead: {
            type: 'array',
            items: {
                type: 'string'
            },
            description: 'paths you read'
        },
        commandsRun: {
            type: 'array',
            items: {
                type: 'string'
            },
            description: 'one per command, in the exact form "<command, ≤80 chars>  →  <first line of its output, ≤60 chars>"',
        },
        errors: {
            type: 'array',
            items: {
                type: 'string'
            },
            description: 'one per failed tool call, in the form "tool(arg): error message"',
        },
        rejected: {
            type: 'array',
            items: {
                type: 'string'
            },
            description: 'tool calls that were DENIED and never executed, in the form "tool(arg): reason" — empty if none',
        },
        // The three fields _agent.py's RunResult carries and this harness does not
        // expose. Self-reported, like everything else here (divergence #1), but they are
        // what makes a ccloop loop and a csloop loop comparable units of work — and the
        // transcript can be counted afterwards to check the report.
        toolCalls: {
            type: 'integer',
            description: 'total number of tool calls you executed this loop (count them; do not estimate)',
        },
        iterations: {
            type: 'integer',
            description: 'number of your own assistant turns that issued at least one tool call',
        },
        stopReason: {
            type: 'string',
            enum: ['final_text', 'max_iterations', 'tool_budget'],
            description: 'final_text = you finished on your own; max_iterations = you ran out of turns; tool_budget = you hit the tool-call budget',
        },
    },
    required: ['status', 'plan', 'checkOutput', 'toolCalls', 'stopReason'],
}

// Mirrors the TOML the review agent writes in _loop.py (loop / summary / blocker / [[pending]]).
const REVIEW_SCHEMA = {
    type: 'object',
    properties: {
        loop: {
            type: 'integer'
        },
        summary: {
            type: 'string',
            description: 'one paragraph describing what actually happened'
        },
        blocker: {
            type: 'string',
            description: 'main current blocker, or an empty string if none'
        },
        pending: {
            type: 'array',
            items: {
                type: 'string'
            },
            description: 'concrete, actionable next steps — max 5, empty if the work is done',
        },
        wrote: {
            type: 'boolean',
            description: `true once ${REVIEW_OUTPUT} on disk contains this assessment`,
        },
    },
    required: ['summary', 'blocker', 'pending'],
}

// ---------------------------------------------------------------------------
// Prompt builders — ports of build_system_prompt / format_loop_context /
// build_author_task / build_review_task. Text kept as close to the original as
// the harness allows; every deviation is one of the divergences listed at the top.
// ---------------------------------------------------------------------------

// _loop.py passes build_system_prompt() as `system=` to both agents — but that is only
// HALF of what a CodeScribe agent actually receives. Agent.run() (_agent.py) appends
// _REACT_NUDGE to the system message on every run, so the real system prompt is
// build_system_prompt() + _REACT_NUDGE. This file used to port only the first half, which
// silently dropped the tool-discipline rules — no repeated identical calls, stay inside the
// listed tools, stop as soon as the work is done. Both halves are here now, in the same
// order and wording the Python builds them in.
//
// Subagent system prompts are not settable in this harness, so this is prepended to each
// task string instead.
const SYSTEM = `You are an autonomous coding agent specializing in test-driven development and repair.

Core rules:
- NEVER fabricate command results, test output, or file contents — always call a tool.
- Determine project state by reading files and running commands; never assume or infer.
- Only access files and paths within the working directory; never target system directories.
- In bash commands, only use relative paths or paths under the working directory.

Efficiency rules (critical for speed):
- Batch ALL independent reads and globs into the first turn — fetch everything you need before acting.
- Once you have identified the changes needed, implement them immediately without further exploration.
- Do not re-read files you have already read unless they were modified since your last read.
- Prefer a single comprehensive edit over multiple small edits to the same file.
- Run tests after each meaningful code change — do not defer validation to the end.
- When all tests pass and all pending items are resolved, stop immediately — do not invent further work.

Tool guidance:
- Use glob to discover structure, read for content, bash for running commands and tests.
- Use edit for targeted changes; use write only when creating new files or doing full rewrites.

You are a coding agent with access to tools.

Rules:
- Be concise and practical.
- Use tools whenever you need to inspect files, run commands, or change the filesystem.
- Do NOT fabricate tool outputs. If you need info, call a tool.
- Batch ALL independent reads and globs into a single turn before acting — gather everything you need first, then implement.
- Once you have the information needed, implement immediately without further exploration.
- Do not re-read files you have already read unless they were modified since your last read.
- Prefer one comprehensive edit over multiple small edits to the same file.
- IMPORTANT: Only use the tools listed here. For shell work, ONLY use the bash tool and ONLY run commands that succeed under the bash tool's safety policy. If a command is blocked, pick an allowed alternative.
- Avoid repeating identical tool calls with the same arguments unless the workspace changed (e.g., after an edit).
- Before using edit, ensure you have read the exact file region you are changing.
- When all required actions are complete, respond with the final answer immediately — do not do additional cleanup or exploration.`

// Port of format_loop_context(): the injected block that replaces the agent having to read
// state/history/plan files. Accumulates the full file inventory across ALL prior loops.
const formatLoopContext = (loopIdx, loopSummaries, pendingItems, toolCallsUsed) => {
    const lines = [`Loop ${loopIdx} of ${AGENT_LOOPS}.`]
    // _agent.py re-injects a WORKSPACE CONTEXT block every ITERATION carrying
    // "tool_calls_total: N/120", so a CodeScribe agent always knows how much of its budget
    // it has spent. Nothing here can inject per-iteration, so the budget is restated at the
    // top of each loop instead — coarser, but it is the difference between an agent that
    // knows a cap exists and one that does not. The cap is per loop; the run total is
    // carried alongside it purely as context.
    lines.push(
        `Tool-call budget: ${MAX_TOOL_CALLS} for THIS loop` +
        (toolCallsUsed ? ` (${toolCallsUsed} used across previous loops).` : '.')
    )

    const allWritten = []
    const allEdited = []
    const seenW = new Set()
    const seenE = new Set()
    for (const s of loopSummaries) {
        for (const f of s.filesWritten) {
            if (!seenW.has(f)) {
                seenW.add(f)
                allWritten.push(f)
            }
        }
        for (const f of s.filesEdited) {
            if (!seenE.has(f)) {
                seenE.add(f)
                allEdited.push(f)
            }
        }
    }

    if (allWritten.length) lines.push('Files created across all prior loops: ' + allWritten.join(', '))
    if (allEdited.length) lines.push('Files edited across all prior loops: ' + allEdited.join(', '))

    // Last loop's commands/errors, for immediate context.
    if (loopSummaries.length) {
        const last = loopSummaries[loopSummaries.length - 1]
        const parts = []
        if (last.commandsRun.length) parts.push('ran: ' + last.commandsRun.slice(0, 3).join('; '))
        if (last.errors.length) parts.push('errors: ' + last.errors.slice(0, 3).join('; '))
        if (parts.length) lines.push('Last loop — ' + parts.join(' | ') + '.')
    }

    if (pendingItems.length) {
        lines.push('Pending next steps:')
        for (const item of pendingItems.slice(0, 5)) lines.push(`  - ${item}`)
    } else {
        lines.push('No pending steps recorded — determine next action from the Spec and Plan.')
    }

    return lines.join('\n')
}

// Port of build_author_task(), sourced from this transformation's Spec + Plan (transform.js's
// SPEC/PLAN) instead of a single CodeScribe task file.
const buildAuthorTask = (loopIdx, loopSummaries, pendingItems, toolCallsUsed) => {
    const context = formatLoopContext(loopIdx, loopSummaries, pendingItems, toolCallsUsed)

    const orientStep = loopIdx === 1 ?
        `1. Read ${PLAN} — how this step is run: its conventions, its tool list, and its
   "Resolution" section for what is ready to work on — then ${SPEC} — the rules and
   correctness bar this step must satisfy. If ${LOG} exists, skim it for what prior runs
   have already settled, but do not treat it as this loop's own state.\n` :
        `1. The specification and all prior work this loop are already summarised above — do
   NOT re-read ${SPEC} or ${PLAN} to orient yourself unless something you did this loop
   requires re-checking one of them.\n`

    return `${SYSTEM}

${NOTES}

${context}

Working directory: ${WORKDIR}
Transformation: ${TRANSFORMATION}
Spec: ${SPEC} (read-only — the rules and correctness bar)
Plan: ${PLAN} (read-only — how this step is run and what is ready)

PHASE: AUTHOR

Goal: COMPLETE the task in this single session if at all possible. Implement every
remaining item you can, verify it, and only stop when the task is fully done or you
are genuinely blocked. Do NOT implement just one item and defer the rest to a later
loop — keep working until everything that can be done this session is done.

Protocol:
${orientStep}2. Write a short PLAN (3–7 bullets) covering everything you intend to complete now.
3. Execute the plan autonomously and to completion — do NOT ask for confirmation, and
   do NOT stop after a single change while more work remains.
4. Before each set of tool calls, write one or two sentences stating what you are about to do and why.
5. Inspect the current state of relevant files before editing them.
6. After each meaningful change, run the closest available check (tests, lint, typecheck).
   If none exists, run \`python -m compileall .\`. Do not defer all validation to the end.
7. Continue until every task is implemented AND the checks pass, or you hit a hard blocker.
8. If the Plan's own log conventions call for it, update ${LOG} to reflect what you settled —
   follow its heading/line format exactly rather than inventing your own.

Execution policy — these are the bounds the comparison harness enforces in code, and this
run is only comparable to it if you hold to them:
- At most ${MAX_TOOL_CALLS} tool calls in THIS loop (the budget refreshes each loop). If
  you reach it, stop and report stopReason "tool_budget" rather than pressing on.
- At most ${AGENT_ITERATIONS} of your own turns this loop, and at most
  ${MAX_CALLS_PER_ITERATION} tool calls in any single turn — so batch independent reads and
  globs rather than issuing them one per turn.
- Do not repeat an identical tool call with identical arguments more than
  ${MAX_REPEATED_CALLS} times (${MAX_REPEATED_CALLS * READ_REPEAT_MULTIPLIER} for plain
  file reads) unless the workspace changed in between. Change the arguments or the approach.
- If every tool call fails for three turns running, stop and report the blocker rather than
  continuing to retry.
Treat these as bounds, not as a licence to stop early — and never as a reason to report work
you did not do.

${SPEC} and ${PLAN} are read-only: never edit them, and never edit anything outside
${WORKDIR}.

Return the structured object. Fill it as follows — this is the ONLY channel the harness has
into what happened this loop, and the next loop's prompt plus the review agent's verified-
actions block are built verbatim from it:
- status: EXACTLY "COMPLETE" if every task is implemented and all checks pass, else "INCOMPLETE".
- plan: the PLAN you followed, final form.
- checkOutput: exact output of the checks you ran (verbatim, not paraphrased).
- nextSteps: ONLY when status is INCOMPLETE — 3–5 concrete items for the following loop.
- filesWritten / filesEdited / filesRead / commandsRun / errors / rejected: a faithful,
  complete record of your actual tool calls. Do not summarise, do not omit failures, and do
  not list a file or command you did not actually touch or run.`
}

// The author's report as the review agent sees it — assembled here from the structured
// result, in the same order _loop.py's final_answer contract prescribes.
const authorReportText = (a) => {
    const parts = [`STATUS: ${a.status}`, '', 'PLAN:', a.plan || '(none reported)', '', 'CHECK OUTPUT:', a.checkOutput || '(none reported)']
    if (a.status !== 'COMPLETE' && (a.nextSteps || []).length) {
        parts.push('', 'NEXT STEPS:')
        for (const s of a.nextSteps.slice(0, 5)) parts.push(`- ${s}`)
    }
    return parts.join('\n')
}

// Port of build_review_task().
const buildReviewTask = (loopIdx, s, execAnswer) => {
    const summaryLines = [`## Verified actions from loop ${loopIdx} (harness-computed)`]
    if (s.filesRead.length) summaryLines.push('Files read: ' + s.filesRead.join(', '))
    if (s.filesWritten.length) summaryLines.push('Files written: ' + s.filesWritten.join(', '))
    if (s.filesEdited.length) summaryLines.push('Files edited: ' + s.filesEdited.join(', '))
    if (s.commandsRun.length) {
        summaryLines.push('Commands run:')
        for (const c of s.commandsRun) summaryLines.push(`  ${c}`)
    }
    if (s.errors.length) {
        summaryLines.push('Errors:')
        for (const e of s.errors) summaryLines.push(`  ${e}`)
    }
    if (!(s.filesRead.length || s.filesWritten.length || s.filesEdited.length || s.commandsRun.length || s.errors.length)) {
        summaryLines.push('  (no verified actions)')
    }
    const verifiedBlock = summaryLines.join('\n')

    let rejectedBlock = ''
    if (s.rejected.length) {
        const rl = ['## Attempted but NOT executed (harness-rejected — no workspace effect)']
        for (const r of s.rejected) rl.push(`  ${r}`)
        rejectedBlock = rl.join('\n')
    }

    return `${SYSTEM}

${NOTES}

Working directory: ${WORKDIR}
Transformation: ${TRANSFORMATION}
Spec: ${SPEC} (read-only)
Plan: ${PLAN} (read-only)
Review output: ${REVIEW_OUTPUT} (write here)

PHASE: REVIEW

${verifiedBlock}

${rejectedBlock ? rejectedBlock + '\n\n' : ''}${execAnswer ? `\n[Author agent report — loop ${loopIdx}]\n\n${execAnswer}\n\n` : ''}Caveat this harness adds: the action list above was reported by the author agent itself, not
extracted from its tool calls by the harness. Where it is cheap to confirm a claim by reading
a file or running a read-only command, do so rather than taking the list on faith.

Your job:
1. Cross-reference the author report's claims against the verified actions above.
   File reads listed above are verified — treat the agent's claims about those
   files as trustworthy. Only flag claims about files NOT in the verified list.
   Any claim that relies on an 'Attempted but NOT executed' call did NOT actually
   happen — flag it as unverified and carry the underlying work into pending items.
2. Write your assessment to the review output file in TOML format:

   \`\`\`toml
   loop = ${loopIdx}
   summary = "One paragraph describing what actually happened."
   blocker = "Main current blocker, or empty string if none."

   [[pending]]
   item = "First concrete next step"
   \`\`\`

Rules:
- If tests passed and no errors are listed above, set blocker = "" and leave pending empty.
- pending items must be concrete and actionable (not 'continue working').
- Limit to 5 pending items maximum.

You are a REVIEWER, not an author. Restrict yourself to: reading files, globbing, read-only
shell (ls, stat, pwd, find, grep, head, tail, which, env, rg) and writing the single file
${REVIEW_OUTPUT}. Do NOT edit source, do NOT run builds or tests, do NOT modify
${SPEC} or ${PLAN}, and do not touch anything outside ${WORKDIR}. Stay within
${REVIEW_ITERATIONS} of your own turns and ${MAX_TOOL_CALLS} tool calls — the same bounds the
comparison harness gives its reviewer (max(6, author_iterations/2) turns, one shared tool
budget).

Return the same assessment as the structured object, with wrote=true once the file is on disk.`
}

// ---------------------------------------------------------------------------
// Result normalisation — the JS side of loop_summary_from_result() plus
// extract_status() / extract_pending_items()'s [:5] cap.
// ---------------------------------------------------------------------------

const asList = (v) => (Array.isArray(v) ? v.filter((x) => typeof x === 'string' && x.trim()) : [])

const asCount = (v) => (Number.isInteger(v) && v >= 0 ? v : 0)

const loopSummaryFrom = (loopIndex, a) => ({
    loopIndex,
    filesWritten: asList(a?.filesWritten),
    filesEdited: asList(a?.filesEdited),
    filesRead: asList(a?.filesRead),
    commandsRun: asList(a?.commandsRun),
    errors: asList(a?.errors),
    rejected: asList(a?.rejected),
    // Self-reported (divergence #1). commandsRun is a lower bound on the same quantity —
    // every bash call appears there — so a toolCalls that is SMALLER than commandsRun is
    // provably wrong and is corrected upward rather than trusted.
    toolCalls: Math.max(asCount(a?.toolCalls), asList(a?.commandsRun).length),
    iterations: asCount(a?.iterations),
    stopReason: typeof a?.stopReason === 'string' ? a.stopReason : 'unknown',
})

const extractStatus = (a) => {
    const v = (a?.status || '').trim().toUpperCase()
    if (v.startsWith('COMPLETE')) return 'COMPLETE'
    if (v.startsWith('INCOMPLETE')) return 'INCOMPLETE'
    return null
}

// ---------------------------------------------------------------------------
// Main loop — port of PromptLoopRunner.run()
//   1) AUTHOR: work + STATUS + NEXT STEPS. STATUS: COMPLETE exits early, review skipped.
//   2) REVIEW: harness-held action summary in, review_output.toml out. Empty pending and
//      no blocker exits early.
// Cross-loop state lives in loopSummaries / pendingItems — nothing is read back off disk.
// ---------------------------------------------------------------------------

const loopSummaries = []
const reviewSummaries = []
let pendingItems = []
let loopsCompleted = 0
let stopReason = `exhausted all ${AGENT_LOOPS} loop(s)`
let finalStatus = 'INCOMPLETE'
// _agent.py enforces AgentPolicy.max_tool_calls_total INSIDE a phase: handle_tool_calls
// returns "tool_budget" the moment the count is reached and Agent.run stops there. A
// workflow script cannot interrupt a subagent mid-flight, so the budget is enforced at the
// only boundary this file controls — between loops. That makes it a ceiling on the RUN
// rather than on each phase, which is looser than CodeScribe in one direction (a single
// loop can overshoot) and tighter in another (the budget is not refreshed per loop). Both
// are recorded, so an over-budget loop is visible in the log rather than silently absorbed.
let toolCallsUsed = 0

const tokensAtStart = budget.spent()

for (let loopIdx = 1; loopIdx <= AGENT_LOOPS; loopIdx++) {
    // --- Author phase ----------------------------------------------------------
    phase('Author')

    const authored = await agent(
        buildAuthorTask(loopIdx, loopSummaries, pendingItems, toolCallsUsed), {
            label: `author:loop${loopIdx}`,
            phase: 'Author',
            schema: AUTHOR_SCHEMA,
            model: AUTHOR_MODEL,
            effort: EFFORT,
        }
    )

    if (!authored) {
        stopReason = `author agent returned nothing in loop ${loopIdx}`
        log(`Loop ${loopIdx} [author]: no result — stopping.`)
        break
    }

    const summary = loopSummaryFrom(loopIdx, authored)
    loopSummaries.push(summary)
    pendingItems = asList(authored.nextSteps).slice(0, 5)
    loopsCompleted = loopIdx
    toolCallsUsed += summary.toolCalls

    const status = extractStatus(authored)
    log(
        `Loop ${loopIdx} [author]: STATUS ${status || 'UNREPORTED'} — ` +
        `${summary.filesWritten.length} written, ${summary.filesEdited.length} edited, ` +
        `${summary.commandsRun.length} command(s), ${summary.errors.length} error(s)` +
        (summary.rejected.length ? `, ${summary.rejected.length} rejected` : '') +
        ` — ${summary.toolCalls}/${MAX_TOOL_CALLS} tool call(s) this loop ` +
        `(${toolCallsUsed} run total), ${summary.iterations} turn(s), stop: ${summary.stopReason}.`
    )
    const overranBudget = summary.toolCalls > MAX_TOOL_CALLS
    if (summary.iterations > AGENT_ITERATIONS) {
        log(
            `  note: loop ${loopIdx} used ${summary.iterations} turns against a stated cap of ` +
            `${AGENT_ITERATIONS} — CodeScribe would have hard-stopped this phase. (Its turns ` +
            'carry up to ' + MAX_CALLS_PER_ITERATION + ' tool calls each, so compare tool ' +
            'calls, not turns.)'
        )
    }

    if (status === 'COMPLETE') {
        finalStatus = 'COMPLETE'
        pendingItems = []
        stopReason = `author agent reported STATUS: COMPLETE after loop ${loopIdx}`
        log(`✓ ${stopReason} — task complete, stopping early (review skipped).`)
        break
    }

    // A loop that overran its own budget already did work CodeScribe would have cut, and
    // stopping the run now cannot undo that — it would only add a divergence of its own
    // (csloop keeps looping after a tool_budget stop; run() calls run_review_phase
    // regardless). So the default is to record it and continue, and STOP_ON_OVERRUN is
    // there for the operator who would rather lose the run than the comparability.
    if (overranBudget) {
        log(
            `  note: loop ${loopIdx} used ${summary.toolCalls} tool calls against a stated ` +
            `per-loop budget of ${MAX_TOOL_CALLS} — CodeScribe would have stopped this ` +
            'phase with stop_reason="tool_budget".'
        )
        if (STOP_ON_OVERRUN) {
            stopReason = `per-loop tool-call budget exceeded in loop ${loopIdx} ` +
                `(${summary.toolCalls}/${MAX_TOOL_CALLS})`
            log(`✗ ${stopReason} — stopping (stopOnOverrun).`)
            break
        }
    }

    // --- Review phase ----------------------------------------------------------
    phase('Review')

    const reviewed = await agent(
        buildReviewTask(loopIdx, summary, authorReportText(authored)), {
            label: `review:loop${loopIdx}`,
            phase: 'Review',
            schema: REVIEW_SCHEMA,
            model: REVIEW_MODEL,
            effort: EFFORT,
        }
    )

    // _loop.py: a missing/unreadable review_output.toml is not a stop condition — the loop
    // simply carries the author's own NEXT STEPS into the next iteration.
    if (!reviewed) {
        log(`Loop ${loopIdx} [review]: no review output — carrying author's next steps forward.`)
        continue
    }

    reviewSummaries.push({
        loopIndex: loopIdx,
        summary: reviewed.summary || '',
        blocker: reviewed.blocker || '',
        pending: asList(reviewed.pending).slice(0, 5),
        wrote: !!reviewed.wrote,
    })

    // Port of apply_review_data(): the review's pending list REPLACES the author's.
    pendingItems = asList(reviewed.pending).slice(0, 5)
    const blocker = (reviewed.blocker || '').trim()

    log(
        `Loop ${loopIdx} [review]: ${pendingItems.length} pending, ` +
        `blocker: ${blocker || '(none)'}` + (reviewed.wrote ? '' : ` — WARNING: ${REVIEW_OUTPUT} not confirmed written`) + '.'
    )

    if (!pendingItems.length && !blocker) {
        finalStatus = 'COMPLETE'
        stopReason = `no pending items and no blocker after loop ${loopIdx}`
        log(`✓ ${stopReason} — task complete, stopping early.`)
        break
    }
}

// ---------------------------------------------------------------------------
// Final summary — port of the run() return string, plus the token roll-up that
// run.toml's cumulative_* fields carry in CodeScribe.
// ---------------------------------------------------------------------------

const outputTokens = budget.spent() - tokensAtStart

const overrunLoops = loopSummaries.filter((s) => s.toolCalls > MAX_TOOL_CALLS).length

log(
    `Done: completed ${loopsCompleted}/${AGENT_LOOPS} loop(s) — ${stopReason} — ` +
    `${finalStatus}${pendingItems.length ? `, ${pendingItems.length} item(s) still pending` : ''} ` +
    `— ${toolCallsUsed} tool call(s) over ${loopsCompleted} loop(s), budget ${MAX_TOOL_CALLS}/loop` +
    (overrunLoops ? `, ${overrunLoops} over it` : '') +
    ` (~${Math.round(outputTokens / 1000)}k output tokens).`
)

// ---------------------------------------------------------------------------
// Metadata / archive handoff — same phase as the transform workflow, so a loop run and a
// transform run land in evals/experiments/ the same way and stay comparable. Delegates to
// the agentic layer in evals/archive.toml, so updates to that file and its Python tool
// automatically affect this phase.
// ---------------------------------------------------------------------------

if (DO_ARCHIVE && loopsCompleted > 0) {
    phase('Metadata')

    const resultJson = JSON.stringify({
            transformation: TRANSFORMATION,
            spec: SPEC,
            plan: PLAN,
            agentLoops: AGENT_LOOPS,
            loopsCompleted,
            finalStatus,
            stopReason,
            // The run's own configuration, so the archive answers "what were the bounds"
            // without anyone parsing it back out of a prompt. CodeScribe writes the same
            // facts to loop/metadata/manifest.toml; recovering ccloop's loop cap by
            // regexing "Loop N of M" out of an author prompt was the alternative, and the
            // archived copy of this script records the DEFAULT rather than the args it was
            // actually invoked with.
            config: {
                agentIterations: AGENT_ITERATIONS,
                reviewIterations: REVIEW_ITERATIONS,
                maxToolCallsPerLoop: MAX_TOOL_CALLS,
                stopOnOverrun: STOP_ON_OVERRUN,
                maxCallsPerIteration: MAX_CALLS_PER_ITERATION,
                maxRepeatedCalls: MAX_REPEATED_CALLS,
                bashAllow: BASH_ALLOW,
                authorModel: AUTHOR_MODEL || null,
                reviewModel: REVIEW_MODEL || null,
                metadataModel: METADATA_MODEL,
                // The reasoning setting this run actually requested. csloop's
                // run.toml records `reason` / `reasoning_config` for the same
                // purpose; the two are different knobs (see EFFORT above).
                effort: EFFORT,
            },
            toolCallsUsed, // across the whole run
            toolCallsBudgetPerLoop: MAX_TOOL_CALLS,
            loops: loopSummaries.map((s) => {
                const rev = reviewSummaries.find((r) => r.loopIndex === s.loopIndex) || null
                return {
                    loopIndex: s.loopIndex,
                    filesWritten: s.filesWritten,
                    filesEdited: s.filesEdited,
                    filesReadCount: s.filesRead.length,
                    commandsRun: s.commandsRun,
                    errors: s.errors,
                    rejected: s.rejected,
                    toolCalls: s.toolCalls,
                    iterations: s.iterations,
                    stopReason: s.stopReason,
                    review: rev ? {
                        blocker: rev.blocker,
                        pending: rev.pending,
                        wrote: rev.wrote
                    } : null,
                }
            }),
            pendingAtEnd: pendingItems,
        },
        null,
        2
    )

    // A string distinctive enough to grep this run's own transcripts out of the sibling
    // sessions under ~/.claude/projects/<slug>/. Workflow scripts have no clock or RNG, so
    // it is built from facts unique to this run instead.
    const MARKER = `ARCHIVE-RUN-MARKER/loop/${TRANSFORMATION}/${loopsCompleted}of${AGENT_LOOPS}L-${finalStatus}`

    const metadataPrompt = `You are the metadata/archive agent for a just-completed run of the "loop"
workflow — a bounded author→review loop over the "${TRANSFORMATION}" transformation's own
Spec/Plan, shaped after CodeScribe's prompt_loop. ${NOTES}

Read ${ARCHIVE_SPEC} and follow its workflow exactly. It is harness-agnostic and is the source of
truth for this phase; ${ARCHIVE_TOOL} is the deterministic layer it calls. Do not reimplement
either one — changes to them take effect here automatically.

Everything below is what ${ARCHIVE_SPEC} cannot know: the Claude-specific facts about this run.

Loop-run context to consider while applying the archive workflow:
- transformation: ${TRANSFORMATION}
- spec: ${SPEC}
- plan: ${PLAN}
- loops completed: ${loopsCompleted} of ${AGENT_LOOPS}
- final status: ${finalStatus}
- stop reason: ${stopReason}
- author model: ${AUTHOR_MODEL || '(session default)'}
- review model: ${REVIEW_MODEL || '(session default)'}

Per-loop results (JSON):
${resultJson}

Use repository state to make the archive workflow's decisions, with the run context above as
supporting evidence for identifying the transformation. Three of those decisions are already fixed
by the fact that a Claude workflow ran this:
- --loop-dir is ${LOOP_DIR} — .csloop and .codescribe may still be lying around from earlier runs
- the experiment name starts with "ccworkflow-" (the tool rejects anything else). This run used the
  LOOP harness, not the transform pipeline — pick a name that keeps them apart under
  ${ARCHIVE_SPEC}'s own naming conventions, and never reuse a name.
- --session-logs is this run's session directory, described next

This run's logs are jsonl transcripts under ~/.claude/projects/, not files in the repo, and they
must reach the archive. You are a subagent of this run, so your own transcript is being written
right now to <session-id>/subagents/workflows/<workflow-id>/agent-<your-id>.jsonl. Find it by
grepping that project's log tree for this run's marker, ${MARKER}, and pass the <session-id>
directory (three levels above the match) as --session-logs. If the grep finds no match, say so and
stop rather than picking a session by timestamp.

Then execute the archive workflow described by ${ARCHIVE_SPEC}.`

    await agent(metadataPrompt, {
        label: 'archive-metadata',
        phase: 'Metadata',
        model: METADATA_MODEL,
    })

    log(`Metadata/archive phase completed via ${ARCHIVE_SPEC}.`)
}

return {
    harness: 'claude-code-workflow',
    shapedAfter: 'codescribe/lib/_loop.py prompt_loop',
    transformation: TRANSFORMATION,
    spec: SPEC,
    plan: PLAN,
    agentLoops: AGENT_LOOPS,
    loopsCompleted,
    finalStatus,
    stopReason,
    pendingAtEnd: pendingItems,
    outputTokens,
    loops: loopSummaries,
    reviews: reviewSummaries,
}
