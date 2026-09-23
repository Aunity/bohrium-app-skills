# bohrium-app-skills

Reusable Codex skills for Bohrium App work.

This repository contains the skill source and a small npm installer. The installer copies complete skill directories into a Codex user or project skill directory; it does not use an npm `postinstall` hook and does not create credentials or Bohrium resources.

## Included skills

The first stable channel contains:

- `bohrium-app-info-brief`
- `bohrium-create-app-skill`
- `bohrium-develop-app`
- `bohrium-orchestrate-app`
- `bohrium-release-app`

## Install from npm

```bash
npx bohrium-app-skills install --scope user
npx bohrium-app-skills doctor
```

For a project-local installation:

```bash
npx bohrium-app-skills install --scope project
```

Install selected skills or preview the operation:

```bash
npx bohrium-app-skills install \
  --scope user \
  --skills bohrium-develop-app,bohrium-release-app \
  --dry-run
```

Existing skill directories are never replaced unless `--force` is supplied. A forced replacement is moved to a timestamped backup first.

## Repository boundary

Only reusable skill instructions, their references/scripts/assets, the installer, and release metadata belong in this package. Project Brain pages, transcripts, credentials, temporary Bohrium IDs, and app-specific private data do not belong here.
