# Evidence and freshness

## Evidence order

1. Inspect current source, generated schemas, tests and machine-readable run outputs.
2. Inspect dated deployment records containing immutable image IDs or digests and job IDs.
3. Use maintained platform guidance and record its last verification date.
4. Use root user transcripts to recover product intent and explicit decisions.
5. Use subagent transcripts only as supporting investigation evidence.
6. Treat READMEs and copied playbooks as historical when later evidence conflicts.

Classify claims as `fact`, `decision`, `inference`, `historical`, or `unknown`.
Do not silently merge conflicts. State the evidence needed to resolve them.

## Time-sensitive facts

Recheck installed package signatures, CLI help and live read-only schema before
depending on:

- Launching or OpenSDK versions and method signatures;
- status integers, retry behavior and remote result paths;
- available SKUs, resource quotas, ports, upload limits and log retention;
- pricing, License, collaboration and publishing policies;
- CLI support for Node, image, job or App operations.

Record `observed_at`, package/CLI version and evidence source with versioned
facts. Avoid phrases such as "currently supported" without a date.

## Transcript handling

Index sessions from `session_meta.cwd`, `thread_source`, parent thread ID and
timestamp. Do not copy message bodies by default. Root sessions form the user
decision timeline; spawned sessions are evidence branches and often repeat
inherited prompts. Extract only decisions, failures, fixes, validation evidence
and open gates after redaction. Never load all large JSONL files into memory.
