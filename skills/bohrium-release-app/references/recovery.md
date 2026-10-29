# Recovery

- Preserve the build, image, App and job IDs immediately after the operation
  returns.
- On local interruption, query existing state before taking another mutation.
- If an image build or push returns a definite failure, report it and stop.
  Do not retry under a different name or silently re-run the operation.
- If a build or push outcome is unknown (local timeout, Ctrl-C, lost
  session), query the same object only: `bohr image status` for the build,
  `bohr image get` / `bohr image list` for the exact name:tag, and
  `bohr image build-log` for diagnostics. Never submit a duplicate build or
  push a replacement name.
- On job wait timeout, resume status/wait for the same job ID; do not resubmit.
- On failed image-test or App jobs, compare exact image identity, entry,
  interpreter, saved schema/config and first failed event before modifying code.
- On a bad deployment, route back to the last fully accepted immutable image
  and App version. Do not repair an old tag in place.
- Treat delete as a separate explicit decision after recovery evidence is safe.

Update the release record with failure state and next action. Never change a
failed gate to passed merely because a later unrelated layer succeeded.
