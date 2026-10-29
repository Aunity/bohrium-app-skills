---
name: bohrium-orchestrate-app
description: Orchestrate a Bohrium App from program discovery through adapter implementation, local review, image build and release, App configuration and acceptance, License/OpenSDK checks, publication, and App-specific skillization by supervising bounded sub-agents across multiple sessions. Use when a main Codex agent must coordinate, verify, resume, or audit an end-to-end Bohrium App delivery without placing all work in one session. Do not use merely to operate jobs for an already published App.
---

# Bohrium Orchestrate App

Act as the single supervisory agent. Persist continuity in repository files,
delegate bounded work to sub-agents, independently verify their evidence, and
advance gates only through the workflow state tool.

## Start or resume

1. Resolve the repository root. Read repository instructions and preserve
   unrelated user changes.
2. Locate `docs/bohrium/workflow-state.json`.
   - If it exists, run `python <skill-dir>/scripts/workflow.py check --state
     <repo>/docs/bohrium/workflow-state.json --release-record
     <repo>/docs/bohrium/release-record.json` and then `status --state ...`
     before dispatching work.
   - If it is missing and the user requested implementation, initialize with
     `workflow.py init --state <repo>/docs/bohrium/workflow-state.json
     --release-record <repo>/docs/bohrium/release-record.json --project-name
     <name> --repository <repo> --create-dirs [--delivery-shape <shape>]`.
   - If the user requested only an audit or plan, do not initialize without
     permission; report the missing durable state.
3. Read the App brief, release record, latest handoff, current source identity
   and only the references needed for the current stage.
4. Read [orchestration-contract.md](references/orchestration-contract.md) for
   the supervisory loop and [stages.md](references/stages.md) for the stage DAG.
5. Reconcile any active assignment or external mutation before creating new
   work. Resume immutable IDs; never infer failure from a lost local session.

## Own the control plane

- Only the main Orchestrator may update `workflow-state.json` or its claims.
- Only one designated Release Operator may update `release-record.json` during
  a platform mutation.
- Workers may modify only explicitly assigned, non-overlapping paths.
- Reviewers remain independent and do not repair the work they review.
- At most one sub-agent may perform an external mutation at a time.
- Never delegate user authorization. Pass an exact authorization reference and
  target to a Release Operator only after the user approved that mutation.
- Never place credentials, login state, verification codes, cookies, complete
  environment dumps or private scientific inputs in a sub-agent prompt.

## Plan one dispatch wave

1. Select the earliest ready stage and decompose only its independent tasks.
2. Use available sub-agent slots for tasks that can run concurrently without
   shared file writes or platform mutations. Keep release mutations serial.
3. Build one `bohrium-agent-task/v1` envelope per Worker from
   [agent-task.schema.json](assets/agent-task.schema.json).
4. Read [subagent-prompts.md](references/subagent-prompts.md) and combine the
   common Worker contract with the role-specific prompt.
5. Include the exact repository, task ID, attempt, workflow revision, source
   identity, required inputs, allowed and forbidden paths, required skills,
   exit gates, evidence paths and external authority.
6. Spawn workers with `fork_turns="none"` or the smallest useful context fork.
   Do not rely on inherited conversation history. Forbid workers from spawning
   further agents unless a task explicitly requires a nested, bounded review.

Route stages to existing skills:

- Discovery, adapter and local validation: `$bohrium-develop-app`.
- Image build/push, Job, App, License and publication: `$bohrium-release-app`.
- Published-App operation skill: `$bohrium-create-app-skill`, then
  `$skill-creator` for its package.

For the image route, S5 builds and publishes the candidate image: a local
Docker build published with `bohr image push`, or a remote build with
`bohr image build`. Use an existing CLI profile; never create SSH identities,
temporary keys or custom credentials, and never overwrite an existing tag.
S7, not S5, runs remote runtime tests against the immutable image.

## Supervise and ingest

1. Monitor active workers and handle user changes by interrupting or narrowing
   work when necessary.
2. Require one `bohrium-agent-result/v1` object matching
   [agent-result.schema.json](assets/agent-result.schema.json).
3. Verify, rather than trust, every result:
   - task ID, role, stage, attempt and starting workflow revision;
   - changed paths against the write allowlist;
   - file SHA-256 and current source identity;
   - commands, exit codes, timestamps and evidence paths;
   - zero unauthorized mutations and at most one authorized mutation;
   - immutable resource ID plus read-back after a mutation;
   - no credential-like output or prohibited files.
4. Reject `passed` when a required gate lacks evidence, a Worker changed control
   files, or a lower gate is used to infer a higher gate.
5. Send code, schema and candidate gate results to an independent Reviewer.
   When review fails, issue a new repair task to a Worker; do not ask the
   Reviewer to silently fix its own findings.
6. Save durable evidence and an append-only handoff. Then use `workflow.py
   transition` with the expected state revision. A Worker result never changes
   stage state by itself.

## Handle external mutations

Before image build/push, Job, App, License, price or publication changes:

1. Resolve the exact current target with read-only checks.
2. Present action, target, effect, expected cost/duration, recovery and evidence
   plan to the user.
3. After explicit approval, dispatch exactly one Release Operator task for one
   mutation. Do not bundle later mutations under the same approval.
4. Persist the returned immutable ID immediately and read back the same object.
5. On timeout or interruption, keep the mutation active and query the same ID
   or unique tag. Do not create or submit a replacement automatically.

If an image build or push returns a definite failure, stop the stage and
report the error immediately. Do not retry under a different name or push a
replacement. If the outcome is unknown, query only the same build or
name:tag identity (`bohr image status`, `bohr image build-log`) before
stopping.

Login and verification challenges are human checkpoints. Generate a complete
console handoff, mark the stage `awaiting_human`, and resume with read-only
verification after the user saves the form. Do not request credential values.

## Continue or stop

Continue dispatch/review/transition waves while a safe in-scope stage is ready.
Stop and hand control to the user only when:

- an exact billable or state-changing mutation needs approval;
- a product, License, price, visibility or scientific choice is required;
- a login or verification checkpoint requires a human;
- required input or authority is genuinely missing;
- every applicable gate has passed.

At every stop, run `workflow.py check`, write a new handoff, and report the exact
claim reached (`local-ready`, `image-ready`, `app-ready`,
`api-ready`, `release-ready` or `skill-ready`) plus one next action. Never use
the unqualified phrase “released” while required gates remain pending.

## Tool quick reference

```bash
python <skill-dir>/scripts/workflow.py init \
  --state <repo>/docs/bohrium/workflow-state.json \
  --release-record <repo>/docs/bohrium/release-record.json \
  --project-name <name> --repository <repo> --create-dirs
python <skill-dir>/scripts/workflow.py status \
  --state <repo>/docs/bohrium/workflow-state.json
python <skill-dir>/scripts/workflow.py check \
  --state <repo>/docs/bohrium/workflow-state.json \
  --release-record <repo>/docs/bohrium/release-record.json
python <skill-dir>/scripts/workflow.py transition \
  --state <repo>/docs/bohrium/workflow-state.json \
  --stage S0 --to in_progress --actor orchestrator \
  --expect-revision 0
```

Use `workflow.py --help` for the complete deterministic interface. The tool
modifies only local workflow control files; it never calls Bohrium APIs.
