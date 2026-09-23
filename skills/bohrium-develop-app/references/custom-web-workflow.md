# Custom Web workflow

1. Define the interactive unit, session state, persistence promise, maximum
   input, response-time budget and behavior under concurrent users.
2. Serve the frontend and API from one origin when practical. Run one foreground
   process, listen on `0.0.0.0` and use the configured service port.
3. Support reverse-proxy base paths. Avoid root-relative frontend assets and API
   URLs unless the platform contract guarantees a root mount.
4. Provide liveness, readiness and version endpoints. Keep readiness meaningful
   by checking required local assets without performing expensive computation.
5. Treat uploads as untrusted. Bound bytes and records, reject traversal and
   unsafe archives, isolate temporary directories and clean them after success,
   failure and disconnect.
6. Keep long or GPU-heavy computation out of web requests. Submit a separate
   asynchronous task when the latency or resources exceed the web budget.
7. Use `/data` only after defining multi-version migration, backup, concurrency
   and user isolation. Do not imply persistence when the App is stateless.
8. Validate CSP, iframe behavior, WASM/workers, lazy assets, forwarded headers,
   HTTPS URL generation, upload/download, cold wake-up and concurrency behind
   the actual Bohrium reverse proxy.

Never implement a second account system when platform identity is sufficient.
If OAuth or platform cookies are used, keep them server-side, validate them
through the supported SDK and never log or return them to the browser.
