# Release routing

| Change | Local tests | Local Docker | CPU staging Node | Immutable-image test |
| --- | --- | --- | --- | --- |
| Documentation only | document checks | no | no | no |
| Python logic, form or help; Node snapshot delivery | required | usually optional | assemble only | required |
| Dockerfile, base image, system library, CUDA, Python or SDK | required | required or strongly justified equivalent | assemble only | required |
| Registry-direct image delivery | required | required | optional | required |
| Custom Web frontend/backend bundle | required | required unless using a reproducible Node bundle | assemble only for Node snapshot route | cold start and deployed reverse-proxy acceptance required |
| MCP runtime/transport change | required with real client | depends on delivery route | depends on route | deployed client acceptance required |

Prefer an incremental Node snapshot from the last accepted image for a
Python-only change when it preserves the verified scientific stack. The Node
is a build surface, not the runtime acceptance surface. Return to a public base
image when the base or dependency baseline must be rebuilt. Never use a mutable
development Node as the rollback target.
