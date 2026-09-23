# Testing gates

| Gate | Primary evidence | Cannot prove |
| --- | --- | --- |
| Pure unit/command tests | flags, validation, shell safety, deterministic mapping | real scientific executable or platform |
| Service integration | subprocess, timeout, logs, results, overwrite protection | form rendering or image completeness |
| Schema snapshot | fields, order, defaults, visibility metadata | live Preview rendering |
| Direct scientific CLI | target executable and system dependencies | adapter correctness |
| Adapter JSON replay | real command and output contract | immutable image or saved App config |
| Preview | actual form layout and conditional fields | computation, License or API |
| CPU Node assembly | artifact transfer, install path and snapshot contents | immutable-image runtime behavior |
| Immutable-image runtime tests | cold start, entry, dependencies, public methods and output return | App page schema or License |
| App page test | saved form, resource and report behavior | programmatic API behavior |
| OpenSDK schema | App key, deployment, submodel and License visibility | upload, compute or download |
| OpenSDK minimal E2E | authentication, upload, submit, status and download | scientific benchmark or production scale |

Select the smallest sufficient local tests while iterating, but complete every
applicable higher gate before claiming release. Include a minimal success, every
public method, each input mode, conditional on/off cases, invalid input,
timeout/termination, target resource, artifact validation and secret scanning.

Do not execute that complete matrix at every layer. Run logic and adapter tests
locally, use a CPU Node only to assemble a snapshot, and run the required remote
runtime matrix from the exact immutable image. Later App-page and API checks
should use minimal interface canaries unless a changed interface transforms the
scientific input or selects a different image.

Keep engineering smoke thresholds separate from scientific acceptance. Report
platform elapsed time and algorithm elapsed time independently.
