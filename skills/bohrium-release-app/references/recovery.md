# Recovery

- Preserve the Node, image, App and job IDs immediately after creation.
- On local interruption, query existing state before taking another mutation.
- If CPU Node creation returns a definite failure, report it and stop. Do not
  retry creation or silently select a different Node. If creation outcome is
  unknown, query only the same request or Node identity before reporting.
- On snapshot timeout, search for the unique requested tag and continue
  monitoring it; do not create a second image.
- On job wait timeout, resume status/wait for the same job ID; do not resubmit.
- On failed image-test or App jobs, compare exact image identity, entry,
  interpreter, saved schema/config and first failed event before modifying code.
- On uncertain Node shutdown, query the same Node. Stop it only with authority.
- On a bad deployment, route back to the last fully accepted immutable image
  and App version. Do not repair an old tag in place.
- Treat delete as a separate explicit decision after recovery evidence is safe.

Update the release record with failure state and next action. Never change a
failed gate to passed merely because a later unrelated layer succeeded.
