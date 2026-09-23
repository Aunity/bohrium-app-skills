# Launching workflow

1. Inventory the real executable in the target environment: absolute Python and
   CLI paths, versions, system dependencies, every public subcommand, boolean
   flags, inputs, outputs, exit codes and resource behavior.
2. Prepare one minimal valid text input, one minimal valid file input when
   supported, one bad input and the cheapest parameters for every public method.
3. Group source commands by user task. Prefer a method selector when methods
   share intent, inputs and result contract; create separate submodels when the
   user goal or input/output contract differs.
4. Separate code into pure command construction, execution service and
   Launching form/runner. Keep Launching SDK imports out of the scientific core.
5. Use platform I/O types for uploaded files and output directories. Hide
   engineering controls. Apply conditional visibility and backend cross-field
   validation.
6. Run subprocesses as argument arrays, tee useful logs, forward termination,
   implement bounded timeout escalation and preserve failure outputs.
7. Generate committed, reviewable schemas and JSON replay fixtures for every
   public submodel. Check labels, order, defaults, units, ranges, required
   fields, file types and conditional metadata.
8. Validate in order: direct scientific CLI, adapter replay, schema snapshot
   and Preview locally; assemble the candidate on a CPU Node; run remote runtime
   acceptance from the immutable image; then use minimal App-page and OpenSDK
   interface canaries when programmatic use is required.

Pin the entry to the verified target interpreter and executable. Do not rely on
shell activation, user site-packages or mounted paths. The CPU Node is only an
image-assembly surface; transfer artifacts with the supported Bohrium CLI
`share/` path and do not create custom SSH keys. Only a job using the immutable
image proves its runtime, and it still does not prove saved App configuration.
