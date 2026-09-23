# Select the delivery shape

| Shape | Choose when | Reject when |
| --- | --- | --- |
| Launching standard offline task | One submission has bounded inputs, long or batch compute, downloadable outputs, and a terminal state | The normal experience requires continuous interaction in one browser session |
| Custom Web App | Users need an interactive workspace, custom UI, immediate visualization, session behavior, or application-owned storage | A request would block a web worker for long scientific compute; submit that work as a separate task |
| MCP service | The primary consumer is an AI client calling small, explicit tools | The workflow mainly needs a human form or large asynchronous artifacts without a tool-safe orchestration layer |
| Web plus Launching/OpenSDK | Web gathers and displays state while independent jobs perform expensive compute | The web request can safely and quickly complete the entire calculation |

Decide from user intent, latency, state, input size, compute resources, result
shape, concurrency, cost and failure recovery. Do not assume that an existing
CLI must become Launching or that an existing local website should become a
Custom Web App unchanged.

For all shapes:

- keep core scientific code platform-independent;
- define explicit schemas and stable result semantics;
- isolate users, inputs, outputs, logs and task IDs;
- record versions and provenance;
- establish scientific, technical, operational, legal and product gates separately.
