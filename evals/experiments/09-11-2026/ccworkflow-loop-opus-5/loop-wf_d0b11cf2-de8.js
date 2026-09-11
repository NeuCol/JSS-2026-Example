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
// 3. Iteration cap. `agent_iterations` (and the review agent's max(6, n/2)) is a hard stop
//    in CodeScribe. Here it is stated to the agent as a tool-call budget — advisory.
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
// ---------------------------------------------------------------------------
// Config (args): transformation (required — a folder under dev/transformations/),
//                agentLoops (5), agentIterations (30), workdir ('.'), loopDir ('.claude'),
//                archive (true — run the Metadata phase),
//                model / authorModel / reviewModel / metadataModel, effort.
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
const AGENT_ITERATIONS = cfg.agentIterations ?? 30
// _loop.py: max_iterations=max(6, agent_iterations // 2) for the review agent.
const REVIEW_ITERATIONS = Math.max(6, Math.floor(AGENT_ITERATIONS / 2))

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
const METADATA_MODEL = cfg.metadataModel || cfg.model
const EFFORT = cfg.effort // analog of _loop.py's `reason` / reasoning_effort

const ARCHIVE_SPEC = 'evals/archive.toml'
const ARCHIVE_TOOL = 'evals/tools/archive_experiment.py'

// Repeated in every prompt below — the same note transform.js gives its agents. The Plans in
// this repo were written with CodeScribe (a different, more restricted runner) in mind, and
// loop.toml is CodeScribe's own config — not ours, and never read by this workflow.
const NOTES = `You have normal Bash tool access (cd, pipes, redirects, variables all work) —
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
    },
    required: ['status', 'plan', 'checkOutput'],
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

// _loop.py passes this as `system=` to both agents. Subagent system prompts are not
// settable here, so it is prepended to each task string instead.
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
- Use edit for targeted changes; use write only when creating new files or doing full rewrites.`

// Port of format_loop_context(): the injected block that replaces the agent having to read
// state/history/plan files. Accumulates the full file inventory across ALL prior loops.
const formatLoopContext = (loopIdx, loopSummaries, pendingItems) => {
    const lines = [`Loop ${loopIdx} of ${AGENT_LOOPS}.`]

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
const buildAuthorTask = (loopIdx, loopSummaries, pendingItems) => {
    const context = formatLoopContext(loopIdx, loopSummaries, pendingItems)

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

Budget: aim to finish within about ${AGENT_ITERATIONS} tool-calling turns. Treat that as a
target, not a licence to stop early — and never as a reason to report work you did not do.

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
${SPEC} or ${PLAN}, and do not touch anything outside ${WORKDIR}. Aim to finish within about
${REVIEW_ITERATIONS} tool-calling turns.

Return the same assessment as the structured object, with wrote=true once the file is on disk.`
}

// ---------------------------------------------------------------------------
// Result normalisation — the JS side of loop_summary_from_result() plus
// extract_status() / extract_pending_items()'s [:5] cap.
// ---------------------------------------------------------------------------

const asList = (v) => (Array.isArray(v) ? v.filter((x) => typeof x === 'string' && x.trim()) : [])

const loopSummaryFrom = (loopIndex, a) => ({
    loopIndex,
    filesWritten: asList(a?.filesWritten),
    filesEdited: asList(a?.filesEdited),
    filesRead: asList(a?.filesRead),
    commandsRun: asList(a?.commandsRun),
    errors: asList(a?.errors),
    rejected: asList(a?.rejected),
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

const tokensAtStart = budget.spent()

for (let loopIdx = 1; loopIdx <= AGENT_LOOPS; loopIdx++) {
    // --- Author phase ----------------------------------------------------------
    phase('Author')

    const authored = await agent(
        buildAuthorTask(loopIdx, loopSummaries, pendingItems), {
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

    const status = extractStatus(authored)
    log(
        `Loop ${loopIdx} [author]: STATUS ${status || 'UNREPORTED'} — ` +
        `${summary.filesWritten.length} written, ${summary.filesEdited.length} edited, ` +
        `${summary.commandsRun.length} command(s), ${summary.errors.length} error(s)` +
        (summary.rejected.length ? `, ${summary.rejected.length} rejected` : '') + '.'
    )

    if (status === 'COMPLETE') {
        finalStatus = 'COMPLETE'
        pendingItems = []
        stopReason = `author agent reported STATUS: COMPLETE after loop ${loopIdx}`
        log(`✓ ${stopReason} — task complete, stopping early (review skipped).`)
        break
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

log(
    `Done: completed ${loopsCompleted}/${AGENT_LOOPS} loop(s) — ${stopReason} — ` +
    `${finalStatus}${pendingItems.length ? `, ${pendingItems.length} item(s) still pending` : ''} ` +
    `(~${Math.round(outputTokens / 1000)}k output tokens).`
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
