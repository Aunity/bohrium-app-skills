# Changelog

## 0.2.0

- Replaced the CPU-Node image-assembly release route with local Docker build +
  `bohr image push` (or remote `bohr image build`); removed
  `node-snapshot-workflow.md` in favor of `image-push-workflow.md`.
- Redefined S5 as "Image Build & Push" and S6 as "Immutable Image Identity";
  removed the `node-ready` claim.
- Bumped the release ledger to `bohrium-release-record/v3` (`image_build` /
  `image_push` gates, `build_id` identity); the auditor still accepts v1/v2
  ledgers as historical evidence.
- Renamed the orchestration `runtime` worker role to `image_builder`.

## 0.1.0

- Defined the `bohrium-app-skills` repository/package boundary.
- Added the first stable Bohrium App skill channel.
- Added an explicit npm installer with user and project scopes.
- Added package integrity checks and dry-run installation.
