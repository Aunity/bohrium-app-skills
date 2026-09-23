# Case patterns

Conformer-generation, streaming-peptide, and multi-stage-peptide operation
skills share these proven patterns:

- one App-specific client with offline validation plus remote lifecycle commands;
- environment-only credentials and project fallback;
- `plan`, `schema`, `submit`, `run`, `status`, `wait`, `logs`, `download`, and
  confirmation-protected `kill`;
- JSON stdout, progress/errors on stderr and non-zero failures;
- fixed platform output directory and real remote `outputs` download;
- immediate job ID recovery and no timeout resubmission;
- empty-directory download protection;
- concise `SKILL.md` plus parameter/output references.

Their scientific validators are intentionally different. The
conformer-generation workflow validates method-specific molecular inputs, the
streaming-peptide workflow validates explicit peptide representations and batch
limits, and the multi-stage-peptide workflow validates PDB/Bundle lineage,
chain roles and stage transitions. Reuse the lifecycle, never merge these
domain rules into a universal permissive client.
