# Image build and push workflow

Assemble the candidate image without a development Node: build locally (or in
CI) with Docker and publish it with `bohr image push`, or let Bohrium build it
remotely with `bohr image build`. Facts below were verified against `bohr 2.9.5` CLI help on 2026-10-29;
recheck `bohr image --help` before relying on a signature.

## Route A — local Docker build, then push

Preferred when the build needs a context (COPY a wheel, fixtures, model
files) or when a Docker daemon is available.

```bash
docker build -t APP:VERSION .          # .dockerignore excludes dev debris and secrets
bohr image push APP:VERSION APP:VERSION \
  --project-id PROJECT_ID --desc "APP VERSION" --timeout 2h
```

`bohr image push` performs prepare → `docker tag` → `docker login` (Bohrium
AccessKey) → `docker push` → complete. The prepare API returns the canonical
registry URL; only that address is used. Credentials come from the existing
bohr profile; never pass keys on the command line or bake them into layers.

## Route B — remote build from a Dockerfile

Preferred when no local Docker daemon exists (agent, sandbox, CI).

```bash
bohr image build --dockerfile ./Dockerfile --name APP:VERSION \
  --project-id PROJECT_ID --wait -o json
```

Constraints: only the Dockerfile text is sent (max 64 KiB) and there is **no
build context** — `COPY`/`ADD` of local files cannot find them. Fetch inputs
with `RUN` (curl, git, pip) or `ADD <url>`, or start `FROM` an image that
already has them. To deliver a wheel this way, publish it somewhere the
Dockerfile can fetch (project share, package index, object storage URL) and
verify its SHA-256 inside the build.

## Route C — extend an existing image

```bash
bohr image pull registry.dp.tech/dptech/BASE:TAG     # rewrites to the AccessKey-enabled face
# local Docker changes on top of the pulled base
bohr image pull / docker build / bohr image push as above
```

Use this for incremental Python-only changes that preserve the verified
scientific stack. For other registries, `docker pull` directly.

## Image hygiene

- Build from a reviewed Dockerfile with a `.dockerignore`; never `COPY` shell
  history, credentials, HAR files, caches, test fixtures or private data into
  a layer.
- Do not pass build secrets through `--build-arg`; they persist in image
  history. Use runtime environment injection by the platform instead.
- Pin base image digests where practical and record the resolved digest.

## Tag and identity rules

- Use a new immutable version tag for every release. Never overwrite or
  re-push an existing tag; a changed image under an old tag is a provenance
  break, not a release.
- Record the returned image identity (name:tag plus image ID/digest when
  provided) and the owning `--project-id` in the release record immediately.
- Read the image back (`bohr image get` / `bohr image list`) and confirm the
  identity and status before submitting any test Job against it.

## Interruption and recovery

- If push or build fails definitively, stop and report; do not retry under a
  different name or silently re-run.
- If the outcome is unknown (local timeout, Ctrl-C, lost session), query the
  same object only: `bohr image status` for a build, `bohr image list` /
  `bohr image get` for the exact name:tag, `bohr image build-log` for build
  diagnostics. Never submit a duplicate build or push a replacement name.
- Local wait timeout ends only local waiting; the platform operation may still
  be running.
- `bohr image delete` is destructive. It is never a routine recovery step and
  requires its own explicit, per-object authorization.

## Relation to other gates

A completed push proves the image exists and is immutable. It does **not**
prove the runtime works: runtime acceptance runs against the exact pushed
image as described in
[image-and-app-acceptance.md](image-and-app-acceptance.md). Node creation,
`bohr file upload` share transfer, and on-Node assembly are obsolete release
steps and must not be reintroduced as workarounds.
