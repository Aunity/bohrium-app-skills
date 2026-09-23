# Parameter modeling

Model operations from the published App schema and scientific intent, not from
another client or stale source form.

- Use named operations that match user tasks and exact submodels.
- Define type, default, allowed values, numerical bounds, units and applicability.
- Validate mutually exclusive inputs and method-specific requirements offline.
- Upload a file only to its exact schema field and keep the corresponding input
  placeholder required by the verified SDK contract.
- Keep platform-managed output directory fixed.
- Reject unknown `--set` keys. If generic overrides are supported, allowlist
  every public key per operation and reserve input/output/internal fields.
- Do not infer chemistry, chain roles, cyclization, stereochemistry, hotspots,
  caps or file format when ambiguity changes scientific meaning.
- Summarize sensitive text by count, size, digest or safe parsed metadata rather
  than copying it into plans or logs.
- Keep process/thread counts, checkpoint paths, environment variables, arbitrary
  Hydra/CLI fragments, raw scripts and debug controls out of user parameters.

Place detailed parameters and outputs in one or more direct references from the
generated `SKILL.md`; keep the core workflow short.
