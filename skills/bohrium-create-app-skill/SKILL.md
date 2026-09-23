---
name: bohrium-create-app-skill
description: Create or update an App-specific Codex skill that safely plans, submits, monitors, diagnoses, and downloads jobs for a published Bohrium App. Use when a Bohrium App has a known App key, submodels, parameter schema, result contract, License behavior, and OpenSDK or equivalent API path, and Codex must turn that contract into a reusable operation skill. Do not use to build the App itself or to perform its platform release.
---

# Bohrium Create App Skill

Turn one published Bohrium App into a narrow, executable and recoverable skill.
Keep scientific input validation App-specific while preserving a shared job
lifecycle and safety contract.

## Workflow

1. Confirm readiness with [readiness.md](references/readiness.md). If the App is
   not published or its schema/API path is unverified, build only an offline
   draft and mark remote commands unverified.
2. Inspect the published schema, exact App key and submodels, user help,
   scientific limits, result files, status/events, upload mapping, License and a
   real minimal download when available. Never infer a missing identifier.
3. Use `$skill-creator` and its `init_skill.py` to create the App skill in the
   App repository. Keep it versioned beside the adapter and result contract.
4. Copy [app-operation-contract.json](assets/app-operation-contract.json) into a
   temporary or project-controlled design location and fill only verified facts.
5. Implement the command surface in
   [client-contract.md](references/client-contract.md). Make `plan` network-free
   and usable without OpenSDK.
6. Encode only public scientific parameters and cross-field rules. Read
   [parameter-modeling.md](references/parameter-modeling.md). Do not expose raw
   arbitrary overrides, executable paths or runtime internals.
7. Apply [safety-and-idempotency.md](references/safety-and-idempotency.md) to
   credentials, confirmation, job IDs, timeouts, logs and downloads.
8. Write a concise `SKILL.md`, App-specific parameter/output references, one
   client script and tests. Use [testing.md](references/testing.md).
9. Run `python scripts/audit_app_operation_skill.py <skill-dir>` and the system
   skill validator. Fix every error; review heuristic warnings manually.
10. Use [case-patterns.md](references/case-patterns.md) for common structure,
    never for copying another App's identifiers or scientific rules.

## Required behavior

- Validate representation, file type/size, method-specific parameters and
  cross-field constraints before network access.
- Emit normal machine-readable results as JSON on stdout and progress/errors on
  stderr.
- Show only redacted plans: filename, size, SHA-256 and safe structural summary;
  do not echo private molecular or structure contents.
- Require explicit `--yes` for submit, run and kill. Keep deletion unavailable.
- Persist and report the job ID immediately after submission.
- On local timeout or interruption, leave the remote job running and resume the
  same ID with status/wait. Never submit a replacement automatically.
- Refuse downloads into a non-empty destination and reject downloaded symlinks.
- Inspect structured result and manifest content after download rather than
  inferring success from file presence alone.
- Treat calculated designs, structures, scores and properties as computational
  outputs with the App's documented scientific limitations.

## Skill boundary

The generated skill may query a published schema and operate existing jobs when
authorized. It must not create Nodes, images, App versions, Licenses or prices.
Use `$bohrium-release-app` for platform release work and an App-specific skill
only for that App's user-facing jobs.

Install or symlink the finished skill into a discovery directory only when the
user requests it. Confirm in a fresh session that metadata triggers correctly;
repository validation alone does not prove discovery.
