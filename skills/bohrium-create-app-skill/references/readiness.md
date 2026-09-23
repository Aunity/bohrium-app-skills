# App-skill readiness

Before enabling remote commands, verify:

- the App is published or available to the intended account;
- the exact App key, deployment, submodel names and recommended/default SKU;
- the account and credential path can satisfy the App's License gate;
- the current published schema matches the adapter and user documentation;
- each public operation has explicit input, parameter and output rules;
- upload fields and the remote result directory have been observed;
- terminal success/failure evidence and job detail shape are known;
- at least one minimal real task can submit, reach terminal state and download;
- scientific, privacy, cost and runtime limitations are documented.

When some items are missing, create a draft with offline `plan` and mock tests,
but fail closed before submission. Never fill unknown App keys, submodels,
statuses, paths or parameters from another App.
