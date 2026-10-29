# Failure catalog

| Symptom | Likely cause | First response |
| --- | --- | --- |
| Unknown `--no-*` option | Adapter guessed a negative boolean flag | Inspect exact CLI help; omit the flag for the default state |
| Preview raises an attribute error on a string | SDK multi-subparser preview incompatibility | Generate flat schemas and isolate a project-owned compatibility path |
| Image build or push fails | Docker/registry rejected the build or a Bohrium push step | Report the failure and stop; query the same build or name:tag; never retry under another name automatically |
| Old CLI resolves instead of the pinned one | Entry resolves an older base environment | Pin absolute interpreter and executable; record both in manifest |
| Local import passes, clean image import fails | User site or mount supplied undeclared packages | Isolate environment and test with user site disabled |
| Page works but API submit is denied | License/account/deployment gate | Check read-only schema, identity and License before changing parameters |
| Duplicate jobs after client timeout | Submission was retried instead of resumed | Persist job ID and use status/wait on the same job |
| Download contains an unexpected `s/` path | Remote result directory name is wrong | Verify real remote path and add a download regression test |
| Scientific outputs exist but task is marked failed | Report layer exception replaced the scientific outcome | Keep report failure non-fatal after a valid result contract exists |
| Web assets or editor fail only on Bohrium | Base path, CSP, WASM, iframe or lazy asset issue | Test the deployed reverse-proxy URL, not only localhost |
| CPU/GPU use exceeds allocation | Nested process and thread parallelism | Own parallelism in one layer and constrain inner libraries |
| Immutable image fails at runtime after a successful local build | Files lived in local-only paths or build hygiene removed dependencies | Install everything under ordinary image paths and diagnose by testing the exact pushed immutable image |

For remote failures, preserve immutable identifiers and the first root-cause
event. Do not edit a running or published environment until the failing image,
entry, schema, parameters and exact executable have been compared.
