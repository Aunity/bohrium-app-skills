# Release routing

| Change | Local tests | Build route | Immutable-image test |
| --- | --- | --- | --- |
| Documentation only | document checks | no | no |
| Python logic, form or help | required | local Docker build + `bohr image push`, or `bohr image build` | required |
| Dockerfile, base image, system library, CUDA, Python or SDK | required | local Docker build + `bohr image push` (or `bohr image build` for a rebuildable Dockerfile) | required |
| Registry-direct image delivery | required | `bohr image pull`, extend locally, `bohr image push` | required |
| Custom Web frontend/backend bundle | required | local Docker build + `bohr image push` (bundle baked into the image) | cold start and deployed reverse-proxy acceptance required |
| MCP runtime/transport change | required with real client | route per delivery shape | deployed client acceptance required |

Prefer extending the last accepted immutable image (`bohr image pull`, local
change, `bohr image push` under a new version tag) for a Python-only change
when it preserves the verified scientific stack. Return to a public base image
when the base or dependency baseline must be rebuilt. The historical
CPU-Node assembly route (create Node, `bohr file upload` to `share/`,
on-Node snapshot) is obsolete and must not be used for new releases.
