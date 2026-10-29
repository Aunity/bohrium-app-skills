# Authorization and secrets

## Read-only by default

- inspect source, schemas, artifacts, CLI help and installed signatures;
- build an offline release plan;
- list or describe existing projects, Nodes, images and jobs when in scope;
- query existing status, redacted logs and published schema;
- validate a local release record.

## Require explicit authority

- build and publish an image (`bohr image push`, `bohr image build`) or
  overwrite any existing image tag;
- create, start, stop or resize a Node (legacy maintenance only; not part of
  the image release route);
- install or upgrade software in a shared or remote runtime;
- snapshot, build, push, retag or delete an image;
- submit, kill or delete a compute job;
- create or change an App version, service, License, price or publication state;
- write user persistent data or overwrite downloaded results.

Resolve exact targets before requesting authority. Do not treat approval for one
Node, image, job or App as blanket permission for later mutations.

Never output AccessKeys, authorization headers, cookies, node passwords, user
tokens, secret URLs or full environment dumps. Some CLI error paths can embed
credentials in URLs; sanitize before display or persistence. Let the supported
CLI or SDK obtain credentials from its environment rather than passing them on
the command line. Reject release records containing credential-like fields.
