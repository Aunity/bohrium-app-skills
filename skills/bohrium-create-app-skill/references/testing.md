# Testing an App operation skill

1. Validate frontmatter, UI metadata and all direct reference links.
2. Run offline `plan` without OpenSDK installed or network access.
3. Test every representation, operation, allowed parameter and cross-field rule,
   including suffix, size, NUL, symlink and unsafe archive paths.
4. Verify plans redact content while preserving filename, size, digest and safe
   summaries.
5. Mock schema, submit, detail, events, logs, kill and download for success,
   failure, unknown status, timeout, interruption and malformed response.
6. Assert submit/run/kill fail without `--yes`; ensure delete is absent.
7. Assert timeout does not invoke submit again and download rejects non-empty
   paths and symlinks.
8. Query the real published schema read-only after deployment changes.
9. With explicit compute authority, run the cheapest representative task once,
   persist its job ID, download `outputs` and validate result/manifest/artifacts.
10. Start a fresh session and confirm the skill triggers and can execute an
    offline plan without relying on prior conversation context.

Keep real compute tests separate from ordinary unit tests and never make a paid
job an import-time or default test side effect.
