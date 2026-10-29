# Image and App acceptance

## Immutable-image runtime tests

Run remote runtime acceptance against the exact pushed immutable image, not
the local Docker build that produced it. Start with the cheapest representative
job and expand only to the public methods, changed paths, input modes and
resource probes required by the App contract. Verify cold start, absolute entry
and interpreter, declared dependencies, absence of runtime dependencies on
`/share`, `/personal` or `/bohr`, success and structured failure behavior,
returned artifacts, hashes and logs. Persist every submitted job ID.

Do not repeat an unchanged full scientific matrix at later layers. The image
gate proves the runtime; App-page and API gates prove their own interface and
saved-configuration contracts.

## Saved App surface

For Launching, verify the saved schema, submodel order, conditional fields,
defaults, file injection, resource selection, result files and report on the App
test page with one minimal interface canary. For Custom Web, verify the real base path, static assets, API and
download URLs, CSP/iframe/WASM, forwarded headers, health, cold wake-up, upload
limits and concurrent isolation. For MCP, verify the deployed transport/path
with a real client and bounded non-sensitive request.

Reuse accepted image-test evidence when the image, entry, schema and relevant
input mapping are unchanged. Rerun the affected image tests when any of those
identities changes; do not reuse evidence by date or mutable tag alone.

## Programmatic API

When required, separately verify identity, License, published schema, exact App
key/submodel, upload mapping and, when programmatic use is required, one minimal
submit with persistent job ID, terminal event, logs and remote result download.
Do not rerun the complete scientific suite through the API. A local wait timeout
stops only local waiting. Resume the same job and never submit a replacement
automatically.

Record platform elapsed time separately from algorithm elapsed time and cost.
Neither technical E2E nor a low-cost smoke is a scientific benchmark.
