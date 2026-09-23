---
name: bohrium-develop-app
description: Plan, implement, review, and locally validate Bohrium Apps that wrap scientific CLIs, algorithm images, Python packages, web services, or MCP tools. Use when Codex must choose between Launching, Custom Web, and MCP delivery; design Bohrium forms and adapters; build result and provenance contracts; prepare schemas, images, tests, documentation, or release evidence; or diagnose an App before live publication. Do not use merely to submit jobs to an already published App when an App-specific operation skill exists.
---

# Bohrium Develop App

Develop the smallest Bohrium delivery that preserves the scientific program's
real contract. Separate product decisions, platform adaptation, scientific
execution, and release evidence so that success at one layer is never mistaken
for success at another.

## Workflow

1. Inspect repository instructions, current changes, primary documentation,
   executable help, tests, schemas, and deployment records. Run
   `python scripts/audit_bohrium_project.py <project>` for a safe first inventory.
2. Classify every claim as current fact, user decision, inference, historical
   evidence, or unresolved conflict. Read
   [evidence-and-freshness.md](references/evidence-and-freshness.md).
3. Select Launching, Custom Web, MCP, or a deliberate combination by reading
   [app-selection.md](references/app-selection.md). Do not choose from the
   existing code shape alone.
4. Define the user task, input semantics, scientific limits, outputs, resource
   envelope, expected failures, and Definition of Done. Copy
   [app-development-brief.md](assets/app-development-brief.md) into the target
   project only when a durable brief is useful.
5. Keep the scientific core independent from Bohrium. Add an adapter rather
   than reimplementing algorithm logic in a form, web route, or MCP tool.
6. Follow exactly one primary implementation path:
   - Launching: read [launching-workflow.md](references/launching-workflow.md).
   - Custom Web: read [custom-web-workflow.md](references/custom-web-workflow.md).
   - MCP: read [mcp-workflow.md](references/mcp-workflow.md).
7. Implement a stable machine-readable result and provenance boundary. Read
   [result-contract.md](references/result-contract.md) before naming outputs or
   writing manifests.
8. Validate from cheapest to most platform-specific. Read
   [testing-gates.md](references/testing-gates.md) and never substitute a lower
   gate for a higher one.
9. Consult [failure-catalog.md](references/failure-catalog.md) before changing
   SDK versions, boolean flags, executable paths, preview code, output paths,
   CSP, or job retry behavior.
10. Use [case-studies.md](references/case-studies.md) for transferable patterns,
    not for copying App keys, domain parameters, image names, or old status.
11. After local implementation and evidence are accepted, hand release planning
    and external mutations to `$bohrium-release-app`; do not broaden this skill's
    authority implicitly.

## Engineering rules

- Organize features around user tasks, not the source CLI command tree.
- Expose scientific choices; hide executable paths, process counts, temporary
  directories, credentials, and scheduler details unless they are truly part
  of the supported product contract.
- Enforce conditional form visibility and the same cross-field constraints in
  backend validation.
- Construct subprocess commands as argument arrays with `shell=False`.
- Resolve uploaded files to validated regular files and write deliverables only
  to the platform output boundary.
- Pin and report the actual Python, CLI, SDK, algorithm, image, model, and data
  versions used. Prefer immutable digests over mutable labels.
- Treat generated scientific results as computational outputs, not validation
  of efficacy, safety, activity, or experimental success.
- Preserve unrelated user changes. Never assume Git recovery exists.

## Safety and authority

Perform source inspection, local tests, schema generation, offline plans, and
read-only platform queries when they are in scope. Require explicit authority
before creating or stopping Nodes, installing into shared environments,
submitting compute, snapshotting or pushing images, changing App versions,
altering License or price, publishing, killing jobs, or deleting anything.

Never copy raw transcripts or HAR files into an App or skill. Never print or
persist AccessKeys, cookies, authorization headers, node passwords, user tokens,
private molecular inputs, or secret-bearing URLs. If a command can echo secrets
on failure, filter its output before displaying or storing it.

## Completion report

Report the selected App type, implemented scope, files changed, validation gates
actually passed, evidence identifiers, unresolved platform checks, scientific
limitations, security or license blockers, and the exact safe next action. Use
`pending` rather than implying that local success equals Bohrium publication.
