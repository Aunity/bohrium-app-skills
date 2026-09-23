# Result and provenance contract

For offline tasks, prefer a stable output boundary:

```text
outputs/
├── <primary-scientific-artifacts>
├── result.json
├── manifest.json
├── run.log
└── index.launching_report
```

`result.json` is the program-facing outcome. Include a schema version, run ID,
operation/method, status, return code, duration, core counts, warnings/issues
and artifact list. Distinguish `success`, `completed_with_issues`, valid empty
scientific results such as `no_candidates`, validation failure, runtime failure,
timeout and termination.

`manifest.json` is the reproducibility and audit record. Include UTC times,
App/adapter/algorithm/SDK/image versions, non-secret scientific parameters,
input filename/size/digest, a redacted command representation and each artifact
size/digest. Hash sensitive pasted structures rather than copying them.

`run.log` should identify stages and actionable errors without credentials,
complete private inputs or unnecessary absolute paths. A presentation report is
derived output: if report rendering fails after scientific success, preserve the
scientific artifacts and machine-readable result and report a warning.

For Web or MCP, preserve the same semantic fields in API/tool responses and
downloadable provenance, even when no Launching report exists.
