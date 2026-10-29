---
name: bohrium-release-app
description: Audit, plan, execute, monitor, and document controlled Bohrium App releases across image build-and-push, immutable-image tests, Preview or reverse-proxy acceptance, App versions, License, OpenSDK, and rollback. Use when Codex is asked to prepare or perform an image publication, App deployment/update, release acceptance, or release recovery. Keep read-only planning separate from billable or state-changing operations and require explicit authority for each external mutation.
---

# Bohrium Release App

Release a locally accepted Bohrium App through explicit, recoverable gates.
Build and push the candidate image (`bohr image push` or `bohr image build`),
then test the immutable image. Treat source, image runtime, App page, API,
license, and scientific claims as separate evidence layers.

## Workflow

1. Inspect repository instructions, current changes, build artifacts, schemas,
   deployment ledger, last accepted image and rollback target. Do not assume Git
   recovery exists.
2. Copy [release-record.json](assets/release-record.json) into a controlled
   project path when a durable ledger is missing. Run
   `python scripts/audit_release_record.py <record>` before any mutation.
3. Select the release route using
   [release-routing.md](references/release-routing.md). Add local Docker only
   when the change or delivery route requires it.
4. Enumerate every proposed mutation, target, cost/resource impact, rollback and
   evidence to capture. Read
   [authorization-and-secrets.md](references/authorization-and-secrets.md).
5. Complete local source, tests, schema and artifact-integrity gates. Build a
   versioned wheel or immutable bundle and record its SHA-256.
6. Build and publish the image with
   [image-push-workflow.md](references/image-push-workflow.md): build locally
   with Docker and publish with `bohr image push`, or build remotely from a
   Dockerfile with `bohr image build`. Never overwrite an existing tag, and
   read the pushed image identity back before testing.
7. After an image is immutable and available, follow
   [image-and-app-acceptance.md](references/image-and-app-acceptance.md). Run
   the required remote runtime tests against that exact image before testing
   the final App surface.
8. On interruption or failure, preserve identifiers and follow
   [recovery.md](references/recovery.md). Never resubmit or recreate resources
   merely because local waiting timed out.
9. Update the release record after each verified gate. Read
   [evidence-schema.md](references/evidence-schema.md) before declaring ready.

## Mutation protocol

Before each external mutation:

1. Resolve the exact project, Node, image repository/tag, App, version, job and
   local output targets with read-only checks.
2. State the command or API operation, side effect, cost/resource impact and
   rollback.
3. Confirm that the user's current request authorizes this operation. A request
   to inspect, diagnose, plan or continue local work is not permission to create,
   stop, publish, submit, kill or delete.
4. Prefer dry-run or plan output. Require the tool's explicit confirmation flag
   for a real mutation.
5. Capture only redacted, minimal evidence and immediately persist returned
   immutable IDs.

Never combine a destructive cleanup with an unresolved or broad target. Never
overwrite an existing image tag. Do not expose deletion as a routine recovery
step.

## Release claims

Use precise claims:

- `local-ready`: local source, tests, schemas and artifacts are accepted.
- `image-ready`: a new immutable image passed the required image-based runtime tests.
- `app-ready`: saved App configuration and human-facing surface passed acceptance.
- `api-ready`: License, submit, status, logs and download passed a minimal E2E.
- `release-ready`: every required technical, security, license, rollback and
  scientific-claims gate has evidence.

Do not call a release production-ready when required gates remain `pending`,
`failed`, unsupported by evidence, or only inferred from another layer.

## Completion report

Report the route, authorized mutations actually performed, immutable source and
artifact identities, build/image/App/job IDs, gate states, rollback target,
redacted result locations, unresolved blockers and safe next operation.
Explicitly distinguish user action still required in the Bohrium console from
work already verified.
