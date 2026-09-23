# MCP workflow

Evidence for MCP delivery is less mature than Launching in the current local
case set. Verify the current Bohrium control-plane contract before committing
to transport, path, SDK or billing details.

1. Define narrow tools with explicit typed inputs, bounded outputs and helpful
   descriptions. Avoid a generic arbitrary-command tool.
2. Keep scientific functions independent from MCP transport and reuse the same
   validation and result models as CLI or service entry points.
3. Run the server as a foreground process on `0.0.0.0` and the configured port.
   Make the control-plane service path exactly match the transport endpoint.
4. Treat URL tokens and headers as credentials. Never embed them in code,
   screenshots, examples, logs or committed configuration.
5. Bound payloads, execution time and concurrency. Use asynchronous job handles
   for expensive computation instead of holding one tool call indefinitely.
6. Make mutating or billable tools explicit and confirmation-aware. Design
   idempotency before adding billing or job submission.
7. Test locally with an MCP client, then through the deployed Bohrium URL using
   a non-sensitive minimal request. Verify errors do not expose credentials or
   server paths.
