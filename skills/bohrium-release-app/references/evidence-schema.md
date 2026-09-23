# Release evidence schema

Use the bundled `release-record.json` as a minimal ledger. Keep identities and
gate evidence free of credentials and private scientific content.

For every release record:

- identify App name/type and creation time;
- identify source by immutable revision or archive SHA-256;
- record artifact, schema and release-bundle SHA-256 values;
- record previous accepted and candidate image identities; use a digest when
  available, otherwise record the immutable platform image ID;
- record the CPU assembly Node, image-test Job, App version and API Job
  identifiers when used;
- store rollback image/version;
- mark every gate `pending`, `passed`, `failed`, or `not_applicable`;
- require at least one concise evidence reference for every passed gate;
- explain why any gate is not applicable;
- leave unknown values `null`; never invent placeholders that resemble facts.

Run the bundled auditor normally to inspect structural errors and blockers. Add
`--require-ready` only when a workflow must fail unless every required gate is
passed. Structural validity does not imply release readiness.

Version 2 replaces the old `node_smoke`, `cleanup_resmoke` and
`clean_image_job` gates with `node_assembly`, `snapshot_hygiene` and
`image_runtime_tests`. It also renames `clean_image_job_id` to
`image_test_job_id`. The auditor continues to accept version 1 ledgers as
historical evidence, but new releases must use version 2 and must not infer
image runtime acceptance from mutable-Node checks.
