// Workflow: transform — run review groups of any dev/transformations/<name> step until the
// approval gate blocks.
//
// This repo's transformations (mcfm-translate, mcfm-cleanup, pepper-kokkos-port, and any
// future one) each live in dev/transformations/<name>/ as two plain files: a Spec
// (desired_spec.md — the rules and correctness bar) and a Plan (current_plan.md — how to
// run it: log conventions, an approval gate, a tool list, and a "Resolution" section for
// picking the next targets). A third file, agent_log.md, is the running worklist a runner
// writes and keeps current. Human approvals live separately in approvals.toml, recorded
// with dev/tools/approve/approve_group.py — never by editing agent_log.md by hand.
//
// This script is transformation-agnostic on purpose: it never hardcodes a status word, a
// tool name, or a domain rule. Every prompt below tells the agent to read that
// transformation's own Spec/Plan and follow it exactly; the script only supplies the
// structure (what runs in parallel vs. serially, when the approval gate is checked, and
// what happens to a failure). The same file works for any step — point it at a different
// folder. Start it with:
//   Run transform for dev/transformations/<name>
//
// dev/transformations/*/loop.toml belongs to a different orchestrator (CodeScribe) and is
// not used here — do not read it.
//
// Groups loop until the gate blocks. dev/tools/approve/check_gate.py decides whether a new
// group may open: some transformations allow a small backlog of completed-but-unapproved
// groups (see each Plan's "Approval gate" section for the exact risky-status list and batch
// limit), but a risky completed group always blocks immediately. The workflow continues an
// already-open group, or opens a new group when the gate allows, looping until the gate
// blocks or there is nothing left to do. After the gate blocks, a human runs approve_group.py
// to unblock, then re-invokes this workflow.
//
// Five phases per group. The two ideas worth noticing are "write the intent down before the
// work, write the group's own outcome after it" and "write in parallel, combine one at a time":
//   Triage     decide what to work on (open group, or a new one if the gate allows),
//              following the Plan's own Resolution rule and tools — no edits yet
//   Bundle     write the group heading + one unchecked line per unit to the log, so the
//              intent is on disk even if a later phase fails
//   Author     IN PARALLEL, one agent per unit, touching only that unit's own files
//   Integrate  ONE AT A TIME: one agent owns the shared build tree, runs the Spec's own
//              correctness-bar command(s), and records each unit's result
//   Fix        a FAILED unit goes to a stronger model, then gets integrated again
//
// Config (args): transformation (required — a folder under dev/transformations/),
//                scope (optional hint, e.g. a src/ subfolder; ignored if the Spec has no
//                notion of scope), maxUnits (safety cap on ready candidates fetched, 40),
//                bundleSize (override the group size; default: use the Plan's own stated
//                size), fixRounds (escalation rounds over FAILED units, 1),
//                model / triageModel / authorModel / integrateModel / fixModel.

export const meta = {
    name: 'transform',
    description: 'Run review groups of a dev/transformations/<name> step until the approval gate blocks: continue an open group or open new ones (subject to the gate), author units in parallel, integrate and verify them serially, escalate failures, and record everything in agent_log.md. Loops across groups until the gate blocks or work runs out. Transformation-agnostic — every rule comes from that step\'s own desired_spec.md and current_plan.md, never from this script.',
    whenToUse: 'Point it at any folder under dev/transformations/ via args:{transformation:"mcfm-translate"|"mcfm-cleanup"|"pepper-kokkos-port"|...}. Loops across groups until the approval gate blocks (dev/tools/approve/check_gate.py). After the gate blocks, a human runs approve_group.py then re-invokes. Optional: scope, maxUnits, bundleSize, fixRounds, model overrides.',
    phases: [{
            title: 'Triage'
        },
        {
            title: 'Bundle'
        },
        {
            title: 'Author',
            model: 'claude-sonnet-5'
        },
        {
            title: 'Integrate',
            model: 'claude-opus-5'
        },
        {
            title: 'Fix',
            model: 'claude-opus-5'
        },
        {
            title: 'Metadata',
            model: 'claude-sonnet-5'
        },
    ],
}

// ---------------------------------------------------------------------------
// Config
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
const ARCHIVE_SPEC = `evals/archive.toml`
const ARCHIVE_TOOL = `evals/tools/archive_experiment.py`

const SCOPE = cfg.scope || 'all'
const MAXUNITS = cfg.maxUnits || 40
const BUNDLESIZE = cfg.bundleSize || null // null => let the agent use the Plan's own stated group size
const FIXROUNDS = cfg.fixRounds ?? 1

// Triage/Bundle/Author inherit the session model unless overridden. Integrate is the
// serial verification trust anchor and Fix is failure escalation, so both default to a
// stronger model — override per-phase or globally with args.model.
const TRIAGE_MODEL = cfg.model || cfg.triageModel
const AUTHOR_MODEL = cfg.model || cfg.authorModel
const INTEGRATE_MODEL = cfg.model || cfg.integrateModel || 'claude-opus-5'
const FIX_MODEL = cfg.model || cfg.fixModel || 'claude-opus-5'

// Repeated in every prompt below: two things this repo's Plans mention that do not apply
// to us. The Plans were written with CodeScribe (a different, more restricted runner) in
// mind, and loop.toml is CodeScribe's own config — not ours.
const NOTES = `You have normal Bash tool access (cd, pipes, redirects, variables all work) —
ignore any note in the Plan about a restricted shell; that applies to a different runner,
not you. Do not read or follow dev/transformations/*/loop.toml — it belongs to that other
orchestrator (CodeScribe) and has nothing to do with this run.`

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const TRIAGE_SCHEMA = {
    type: 'object',
    properties: {
        stop: {
            type: 'boolean',
            description: 'true if there is nothing safe to do this round'
        },
        stopReason: {
            type: 'string',
            description: 'why: gate blocked, gate errored, no ready units, or a real blocker needing a person',
        },
        gateChecked: {
            type: 'boolean',
            description: 'true if check_gate.py was run because a new group needed to be opened',
        },
        gateBlocked: {
            type: 'boolean'
        },
        opened: {
            type: 'boolean',
            description: 'true if this round needs to open a brand-new group (gate allowed it, or no log/groups exist yet)',
        },
        groupId: {
            type: 'string',
            description: 'the existing OPEN group heading to continue, if any (omit/empty if opening a new one)',
        },
        units: {
            type: 'array',
            items: {
                type: 'object',
                properties: {
                    unit: {
                        type: 'string',
                        description: 'path or id of the thing to work on, in the vocabulary the Spec/Plan use'
                    },
                    verify: {
                        type: 'string',
                        description: 'verification handle for this unit (bench/process/oracle), per the Plan/Spec, or "" if none'
                    },
                    notes: {
                        type: 'string'
                    },
                },
                required: ['unit'],
            },
        },
        layerSize: {
            type: 'integer',
            description: 'total ready candidates in scope before the maxUnits cap'
        },
    },
    required: ['stop', 'units'],
}

const BUNDLE_SCHEMA = {
    type: 'object',
    properties: {
        groupId: {
            type: 'string',
            description: 'the heading text now in effect for this round\'s units'
        },
        written: {
            type: 'boolean'
        },
    },
    required: ['written', 'groupId'],
}

const AUTHOR_SCHEMA = {
    type: 'object',
    properties: {
        unit: {
            type: 'string'
        },
        done: {
            type: 'string',
            enum: ['yes', 'deferred', 'failed']
        },
        notes: {
            type: 'string',
            description: 'missing shared symbol, deferral reason, or suspected mistake'
        },
    },
    required: ['unit', 'done'],
}

const INTEGRATE_SCHEMA = {
    type: 'object',
    properties: {
        verifyOk: {
            type: 'boolean',
            description: 'true if the Spec\'s correctness-bar command(s) passed for this round\'s units'
        },
        rows: {
            type: 'array',
            items: {
                type: 'object',
                properties: {
                    unit: {
                        type: 'string'
                    },
                    status: {
                        type: 'string',
                        description: 'the EXACT status word from the Spec\'s own vocabulary — never invented, never a status the Spec reserves for a human',
                    },
                    notes: {
                        type: 'string'
                    },
                },
                required: ['unit', 'status'],
            },
        },
        groupClosed: {
            type: 'boolean',
            description: 'true only if EVERY unit in the full group (not just this round) now has a non-FAILED status',
        },
    },
    required: ['verifyOk', 'rows'],
}

// ---------------------------------------------------------------------------
// Prompt builders — parameterized on per-group state so the loop can call them
// each iteration. Constants (TRANSFORMATION, SPEC, PLAN, LOG, SCOPE, …) are
// captured from the outer scope; per-group values are explicit arguments.
// ---------------------------------------------------------------------------

const triagePrompt = `You are the TRIAGE phase for the "${TRANSFORMATION}" transformation. ${NOTES}

Read, in this order:
1. ${PLAN} — how this step is run: its log conventions, its approval-gate rule, its tool
   list, and its "Resolution" section (which targets are ready and how to group them).
2. ${SPEC} — the rules and correctness bar this step must satisfy.
3. ${LOG} — the running worklist. It may not exist yet; that just means this is the first
   round for this step.

Then decide, in order:

A. Is there an OPEN group in ${LOG} — a heading starting with "Group" that has any line not
   yet checked off, or checked off as FAILED? If so, set groupId to that heading and
   continue filling/fixing it. Do NOT check the approval gate in this case — the gate only
   matters when opening a brand-new group.

B. Otherwise (every existing group is fully settled with a non-FAILED status, or there are
   no groups yet), a new group may be needed, which the gate decides. Run:
     python3 dev/tools/approve/check_gate.py ${DIR}
   - exit 0 means GATE: OK — proceed to open a new group (set opened=true). This covers a
     fresh run with no log yet, every completed group already approved, and a small backlog
     of non-risky completed groups still within this transformation's batch limit (the
     Plan's "Approval gate" section names the exact risky statuses and the limit).
   - exit 1 means GATE: BLOCKED — do not open a new group. Set gateBlocked=true, stop=true,
     and stopReason to the tool's own message (it names the blocking group and the exact
     \`approve_group.py\` command a human should run). Never run approve_group.py or edit
     approvals.toml yourself — recording approval is a human action.
   - exit 2 means a real error (a bad transformation path, or this transformation is not
     yet known to the gate's policy tables). Set stop=true and stopReason to the tool's
     stderr message — do not silently proceed as if the gate passed.

C. When you may proceed (an open group to continue, or the gate allowed a new one), pick
   this round's units by following the Plan's "Resolution" section EXACTLY, including
   whatever tool it names to rank/refresh readiness (do not guess at readiness yourself).
   Restrict to scope ${SCOPE === 'all' ? '(no restriction)' : `"${SCOPE}"`} if the Plan's
   Resolution section supports scoping; ignore the scope hint otherwise. Skip anything
   already recorded with a non-FAILED status in the log. Cap the units you return at
   ${MAXUNITS}, but report the true number of ready candidates in 'layerSize'.

D. If there is genuinely no ready unit and no open group, set units=[], stop=true, and
   stopReason explaining why (e.g. "no ready leaves this run" or "the only ready work
   depends on a file not yet translated").

Return ONLY the structured object. Do not edit any file and do not author/translate/clean
up/port anything yet.`

const makeBundlePrompt = (triaged) => `Record this round's work in ${LOG} before any editing
starts, so the group exists on disk even if a later step fails. ${NOTES}
Follow ${PLAN}'s log conventions exactly (heading style, one line per unit, and the
group-sizing/topic rule from its "Resolution" section${
  BUNDLESIZE ? `, capped at ${BUNDLESIZE} units for this round` : ''
}).

${
  triaged.opened
    ? `Open a NEW group heading (must start with "Group", numbered/named after the last
existing group per the Plan's convention) and add one UNCHECKED line per unit below,
grouped/ordered the way the Plan's Resolution section prescribes.`
    : `Add these units to the existing OPEN group "${triaged.groupId}" — do not open a new
heading. If a unit is already listed there, leave its line alone.`
}

Units for this round:
${triaged.units.map((u) => `  - ${u.unit}${u.verify ? ` (verify: ${u.verify})` : ''}`).join('\n')}

Return the heading text now in effect as groupId, and written=true once the log file
reflects these units.`

const authorPrompt = (u) => `You are an AUTHOR agent for ONE unit of the "${TRANSFORMATION}"
transformation: \`${u.unit}\`. ${NOTES}

READ ${SPEC} in full and follow it exactly for this one unit — its output shape, rewrite/
cleanup rules, and any named silent traps, do-not-merge conditions, or conservative
fallback. If ${PLAN} names a per-unit scaffold/draft tool, run it first and use its hints.

Hard constraints:
- Touch ONLY this unit's own files (plus, if the Spec calls for it, moving its own obsolete
  source into a sibling deprecated/ directory). Do NOT build, run tests, or edit any
  CMakeLists.txt — even one that looks local to this unit's own directory, since another
  unit running in this same round may share it — or any shared header. The serial
  Integrate step wires every one of this round's units into the build afterward, once.
- Never invent a symbol, call, or interface the source does not already have.
- If a dependency this unit needs is not ready yet, return done="deferred" with why instead
  of guessing.

Verification handle for this unit, if any (per the Plan/Spec): ${u.verify || '(none reported — see Spec)'}
${u.notes ? `Triage notes: ${u.notes}` : ''}

Return ONE structured row. No file contents.`

const makeIntegratePrompt = (units, notes, group) => `You are the SERIAL INTEGRATE phase for
the "${TRANSFORMATION}" transformation — you alone own the shared build tree, any shared/
top-level build files, and ${LOG} right now; no other agent is running. ${NOTES}

Units to integrate (already authored, on disk): ${units.join(', ')}
Author notes to resolve once, if any: ${notes.length ? notes.join('; ') : '(none)'}

Do, in order, following ${SPEC} and ${PLAN} exactly:
1. Wire every one of this round's units into the build — add/replace their entries in
   whichever CMakeLists.txt (local or shared) the Plan/Spec says owns them — and apply any
   other shared wiring change they need (e.g. a shared constant), once, here. Authors were
   forbidden from touching build files precisely so this step can do it without conflicts.
2. Run this step's correctness-bar command(s) exactly as ${SPEC} defines them (e.g.
   \`jobrunner submit tests/<suite>\`, a coverage/validate script, a roadmap refresh) — do
   not substitute a different check of your own.
3. Decide each unit's status using the EXACT status vocabulary ${SPEC} defines (its "Status
   meanings" / "Correctness bar" section) — never invent a status word, and never grant a
   status gated on a check the Spec requires (e.g. a coverage probe) without that check
   having actually fired. If the Spec reserves a status for a human to grant (a runner may
   never assign it), use the runner-appropriate status instead and say in notes what a
   human still needs to confirm.
4. Update ${LOG}: check off each unit's line with its status, in the exact line format
   ${PLAN} prescribes. Never call approve_group.py or edit approvals.toml yourself —
   recording approval is a human action.
5. Leave the tree building clean whether or not every unit passed.

Return the compact status table only (one row per unit). Set groupClosed=true only if
EVERY unit currently listed under group "${group}" in ${LOG} (not just this round's units)
now has a non-FAILED status.`

const fixPrompt = (r) => `Repair the FAILED "${TRANSFORMATION}" unit \`${r.unit}\`. ${NOTES}
Integrate's symptom: ${r.notes || "(diagnose from source and the Spec's silent-traps / conservative-fallback guidance)"}.

READ ${SPEC} first; compare against a verified sibling unit. Edit ONLY this unit's own
outputs — do NOT build, run tests, or touch any CMakeLists.txt (re-integrate does that,
since another unit being fixed in this same round may share the file). If it truly cannot
be fixed without a dependency that is not ready, return done="deferred" with why instead of
guessing.

Return ONE row: unit | done(yes/deferred/failed) | notes (what changed and why).`

// ---------------------------------------------------------------------------
// Main loop — run groups until the gate blocks, work runs out, or nothing authors.
// Each iteration is one full group: Triage → Bundle → Author → Integrate → Fix.
// The gate check lives inside Triage, so the loop stops naturally when it blocks.
// ---------------------------------------------------------------------------

const allResults = []

while (true) {
    const gNum = allResults.length + 1

    // --- Phase 1: Triage -------------------------------------------------------
    phase('Triage')

    const triaged = await agent(triagePrompt, {
        label: `triage:g${gNum}`,
        phase: 'Triage',
        schema: TRIAGE_SCHEMA,
        model: TRIAGE_MODEL,
    })

    if (!triaged || triaged.stop || !triaged.units?.length) {
        log(`Triage (g${gNum}): ${triaged?.stopReason || 'nothing to do this round'}.`)
        break
    }

    // --- Phase 2: Bundle -------------------------------------------------------
    phase('Bundle')

    const bundled = await agent(makeBundlePrompt(triaged), {
        label: `bundle:g${gNum}`,
        phase: 'Bundle',
        schema: BUNDLE_SCHEMA,
        model: TRIAGE_MODEL,
    })
    const GROUP = bundled?.groupId || triaged.groupId || '(unlabeled group)'

    log(
        `${triaged.opened ? 'Opened' : 'Continuing'} ${GROUP}: ${triaged.units.length} unit(s) this round` +
        (triaged.layerSize > triaged.units.length ?
            ` (${triaged.layerSize} ready in scope "${SCOPE}" — raise maxUnits to widen)` :
            '') +
        '.'
    )

    // --- Phase 3: Author -------------------------------------------------------
    phase('Author')

    const authored = await parallel(
        triaged.units.map((u) => () =>
            agent(authorPrompt(u), {
                label: `author:${u.unit}`,
                phase: 'Author',
                schema: AUTHOR_SCHEMA,
                model: AUTHOR_MODEL,
            })
        )
    )
    const ok = authored.filter(Boolean).filter((r) => r.done === 'yes')
    const notOk = authored.filter(Boolean).filter((r) => r.done !== 'yes')
    log(`Authored ${ok.length}/${triaged.units.length}.` + (notOk.length ? ` ${notOk.length} deferred/failed.` : ''))

    if (!ok.length) {
        log('Nothing authored successfully; stopping loop.')
        allResults.push({ group: GROUP, triaged, bundled, authored, integrated: null })
        break
    }

    // --- Phase 4: Integrate ----------------------------------------------------
    phase('Integrate')

    let integrated = await agent(
        makeIntegratePrompt(
            ok.map((r) => r.unit),
            authored.map((r) => r?.notes).filter(Boolean),
            GROUP
        ), {
            label: `integrate:${GROUP}`,
            phase: 'Integrate',
            schema: INTEGRATE_SCHEMA,
            model: INTEGRATE_MODEL,
        }
    )

    // --- Phase 5: Fix ----------------------------------------------------------
    for (let round = 1; round <= FIXROUNDS; round++) {
        const failedRows = (integrated?.rows || []).filter((r) => r.status === 'FAILED')
        if (!failedRows.length) break

        phase('Fix')
        log(`Fix round ${round}/${FIXROUNDS}: escalating ${failedRows.length} FAILED unit(s) to ${FIX_MODEL}.`)

        const repaired = (
            await parallel(
                failedRows.map((r) => () =>
                    agent(fixPrompt(r), {
                        label: `fix:${r.unit}`,
                        phase: 'Fix',
                        schema: AUTHOR_SCHEMA,
                        model: FIX_MODEL,
                    })
                )
            )
        ).filter(Boolean)

        const refixUnits = repaired.filter((r) => r.done === 'yes').map((r) => r.unit)
        if (!refixUnits.length) {
            log('Fix produced no repaired units; ending escalation.')
            break
        }

        const reInt = await agent(makeIntegratePrompt(refixUnits, [], GROUP), {
            label: `re-integrate:r${round}`,
            phase: 'Integrate',
            schema: INTEGRATE_SCHEMA,
            model: INTEGRATE_MODEL,
        })

        const byUnit = new Map((integrated?.rows || []).map((r) => [r.unit, r]))
        for (const r of reInt?.rows || []) byUnit.set(r.unit, r)
        integrated = {
            verifyOk: reInt?.verifyOk ?? integrated?.verifyOk,
            rows: [...byUnit.values()],
            groupClosed: reInt?.groupClosed ?? integrated?.groupClosed,
        }
    }

    // --- Per-group summary -----------------------------------------------------
    const gRows = integrated?.rows || []
    const gFailed = gRows.filter((r) => r.status === 'FAILED')
    const gSettled = gRows.filter((r) => r.status !== 'FAILED')

    log(
        `${GROUP}: ${gSettled.length} settled, ${gFailed.length} FAILED. ` +
        (integrated?.groupClosed ?
            'Group closed — continuing to next group if gate allows.' :
            'Group still open — next iteration continues it.')
    )

    allResults.push({ group: GROUP, triaged, bundled, authored, integrated })
}

// ---------------------------------------------------------------------------
// Final summary
// ---------------------------------------------------------------------------

const totalSettled = allResults.reduce(
    (n, r) => n + (r.integrated?.rows || []).filter((x) => x.status !== 'FAILED').length, 0
)
const totalFailed = allResults.reduce(
    (n, r) => n + (r.integrated?.rows || []).filter((x) => x.status === 'FAILED').length, 0
)

log(`Done: ${allResults.length} group(s) processed, ${totalSettled} settled, ${totalFailed} FAILED.`)

// ---------------------------------------------------------------------------
// Metadata / archive handoff — delegate to the agentic layer in evals/archive.toml
// so updates to that file and its Python tool automatically affect this phase.
// ---------------------------------------------------------------------------

if (allResults.length > 0) {
    phase('Metadata')

    const resultJson = JSON.stringify(allResults.map((r, i) => ({
        groupIndex: i + 1,
        group: r.group,
        opened: r.triaged?.opened ?? true,
        units: (r.triaged?.units || []).map((u) => u.unit),
        authored: (r.authored || []).filter(Boolean).map((a) => ({ unit: a.unit, done: a.done, notes: a.notes || '' })),
        integrated: (r.integrated?.rows || []).map((row) => ({ unit: row.unit, status: row.status, notes: row.notes || '' })),
        groupClosed: r.integrated?.groupClosed ?? false,
        verifyOk: r.integrated?.verifyOk ?? null,
    })), null, 2)

    // A string distinctive enough to grep this run's own transcripts out of the sibling
    // sessions under ~/.claude/projects/<slug>/. Workflow scripts have no clock or RNG, so
    // it is built from facts unique to this run instead.
    const MARKER = `ARCHIVE-RUN-MARKER/${TRANSFORMATION}/${allResults.length}g-${totalSettled}s-${totalFailed}f/${
        String(allResults[0].group || 'group').replace(/[^A-Za-z0-9]+/g, '-').slice(0, 48)
    }`

    const metadataPrompt = `You are the metadata/archive agent for the just-completed "${TRANSFORMATION}" transform run. ${NOTES}

Read ${ARCHIVE_SPEC} and follow its workflow exactly. It is harness-agnostic and is the source of
truth for this phase; ${ARCHIVE_TOOL} is the deterministic layer it calls. Do not reimplement
either one — changes to them take effect here automatically.

Everything below is what ${ARCHIVE_SPEC} cannot know: the Claude-specific facts about this run.

Transform-run context to consider while applying the archive workflow:
- transformation: ${TRANSFORMATION}
- groups processed this run: ${allResults.length}
- units settled this run: ${totalSettled}
- units failed this run: ${totalFailed}
- triage/bundle/author model: ${TRIAGE_MODEL || '(session default)'}
- integrate/fix model: ${INTEGRATE_MODEL}

Per-group results (JSON):
${resultJson}

Use repository state to make the archive workflow's decisions, with the run context above as
supporting evidence for identifying the transformation. Three of those decisions are already fixed
by the fact that a Claude workflow ran this:
- --loop-dir is .claude — .csloop and .codescribe may still be lying around from earlier runs
- the experiment name starts with "ccworkflow-" (the tool rejects anything else)
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
        model: TRIAGE_MODEL,
    })

    log(`Metadata/archive phase completed via ${ARCHIVE_SPEC}.`)
}

return {
    transformation: TRANSFORMATION,
    scope: SCOPE,
    groupCount: allResults.length,
    groups: allResults.map((r) => r.group),
    totalSettled,
    totalFailed,
    results: allResults,
}
