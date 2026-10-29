# Release evidence schema

Use the bundled `release-record.json` as a minimal ledger. Keep identities and
gate evidence free of credentials and private scientific content.

For every release record:

- identify App name/type and creation time;
- identify source by immutable revision or archive SHA-256;
- record artifact, schema and release-bundle SHA-256 values;
- record previous accepted and candidate image identities; use a digest when
  available, otherwise record the immutable platform image ID;
- record the image build ID, owning project ID, image-test Job, App version
  and API Job identifiers when used;
- store rollback image/version;
- mark every gate `pending`, `passed`, `failed`, or `not_applicable`;
- require at least one concise evidence reference for every passed gate;
- explain why any gate is not applicable;
- leave unknown values `null`; never invent placeholders that resemble facts.

Run the bundled auditor normally to inspect structural errors and blockers. Add
`--require-ready` only when a workflow must fail unless every required gate is
passed. Structural validity does not imply release readiness.

Version 3 replaces the version 2 `node_assembly` and `snapshot_hygiene` gates
with `image_build` and `image_push`, and renames the `node_id` identity field
to `build_id`. The image is assembled by a local Docker build published with
`bohr image push`, or built remotely with `bohr image build`; development
Nodes, `bohr file upload` share transfers and on-Node snapshots are no longer
release steps. The auditor accepts version 1 and version 2 ledgers as
historical evidence, but new releases must use version 3 and must not infer
image runtime acceptance from anything other than tests run against the
pushed immutable image.
