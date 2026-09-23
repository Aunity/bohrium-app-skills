# Safety and idempotency

- Read credentials only from documented environment variables. Never accept a
  credential argument or print, persist, hash, upload or include it in errors.
- Build an offline plan before first submission or changed inputs/parameters.
- Require `--yes` for compute-consuming submission and job termination.
- Persist job ID as soon as submit returns. Network uncertainty after submission
  must trigger lookup/recovery, not an unconditional second submit.
- Treat wait timeout and local Ctrl-C as local events. Leave the remote job
  running and explain how to resume it.
- Normalize known statuses only for the verified platform/SDK version. Preserve
  unknown values and consult event details rather than guessing.
- Redact credential-bearing URLs and logs. Do not return full private paths or
  molecular/structure bodies.
- Refuse a non-empty download directory and downloaded symlinks. Validate
  artifact sizes, hashes, structured result status and expected primary outputs.
- Keep kill explicit and omit delete. Do not silently broaden an App operation
  skill into deployment, billing, License or resource-management authority.
