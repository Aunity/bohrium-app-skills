# Client contract

| Command | Network/side effect | Required behavior |
| --- | --- | --- |
| `plan` | none | Validate inputs and output a redacted deterministic plan |
| `schema` | read-only network | Summarize exact published App/submodel contract |
| `submit` | creates job | Require `--yes`, return and persist job ID immediately |
| `status` | read-only network | Query one existing job and normalize state/events |
| `wait` | read-only polling | Poll one job; timeout leaves it running |
| `logs` | read-only network | Retrieve redacted diagnostics for one job |
| `download` | local write | Require successful job and an empty destination |
| `run` | creates job, polls, writes | Require `--yes`; compose submit/wait/download without hidden resubmit |
| `kill` | stops job | Optional; require explicit request and `--yes` |

Do not expose `delete`. Keep normal stdout as one JSON value or JSONL stream and
send progress and structured expected errors to stderr. Return non-zero on
validation, remote or artifact failure.

Keep OpenSDK import lazy so offline plan works without it. Pin only the version
actually verified for the App and inspect its real signatures. Use finite
transport retries while preserving business-level idempotency.
