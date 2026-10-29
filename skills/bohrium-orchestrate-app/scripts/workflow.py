#!/usr/bin/env python3
"""Small, fail-closed state machine for the Bohrium App orchestrator skill."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Iterable


SCHEMA = "bohrium-app-workflow-state/v1"
STAGE_IDS = tuple(f"S{index}" for index in range(13))
ACTIVE_STATUSES = {
    "in_progress",
    "review",
    "awaiting_authority",
    "awaiting_human",
}
TERMINAL_FOR_DEPENDENCY = {"passed", "not_applicable"}
VALID_STATUSES = {
    "pending",
    "ready",
    "in_progress",
    "review",
    "passed",
    "failed",
    "blocked",
    "awaiting_authority",
    "awaiting_human",
    "not_applicable",
    "superseded",
}
TRANSITIONS = {
    "pending": {"ready", "not_applicable", "superseded"},
    "ready": {
        "in_progress",
        "blocked",
        "awaiting_authority",
        "awaiting_human",
        "superseded",
    },
    "in_progress": {
        "review",
        "failed",
        "blocked",
        "awaiting_authority",
        "awaiting_human",
        "superseded",
    },
    "review": {
        "passed",
        "failed",
        "in_progress",
        "blocked",
        "awaiting_authority",
        "awaiting_human",
    },
    "awaiting_authority": {"ready", "in_progress", "blocked", "superseded"},
    "awaiting_human": {"ready", "in_progress", "blocked", "superseded"},
    "blocked": {"ready", "in_progress", "superseded"},
    "failed": {"ready", "in_progress", "superseded"},
    "passed": set(),
    "not_applicable": set(),
    "superseded": set(),
}
CLAIM_STAGES = {
    "local_ready": "S4",
    "image_ready": "S7",
    "app_ready": "S9",
    "api_ready": "S10",
    "release_ready": "S10",
    "skill_ready": "S11",
}

DENIED_KEYS = {
    "password",
    "passwd",
    "pwd",
    "token",
    "accesskey",
    "access_key",
    "client_secret",
    "private_key",
    "cookie",
    "set_cookie",
    "authorization_header",
    "bearer",
    "credentials",
}
SECRET_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(
        r"(?i)\bauthorization\s*:\s*(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"
    ),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)[?&](?:token|access[_-]?key|password|passwd|pwd|secret)=[^&\s]+"),
    re.compile(r"(?i)\b(?:cookie|set-cookie)\s*:\s*[^\s]+"),
)
FORBIDDEN_EVIDENCE_NAMES = {".env", ".bashrc", ".zshrc", ".profile"}
SAFE_REFERENCE_PREFIXES = (
    "platform:",
    "job:",
    "image:",
    "node:",
    "app:",
    "human:",
    "sha256:",
)


class WorkflowError(Exception):
    """Expected command failure with a stable process exit code."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _normalise_key(key: object) -> str:
    return str(key).strip().lower().replace("-", "_")


def reject_secrets(value: Any, pointer: str = "") -> None:
    """Reject secret-like keys and values without echoing the matched value."""

    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{pointer}/{key}"
            normalised = _normalise_key(key)
            if normalised in DENIED_KEYS:
                raise WorkflowError(f"secret-like field rejected at {child}", 4)
            reject_secrets(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_secrets(item, f"{pointer}/{index}")
    elif isinstance(value, str):
        if any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS):
            raise WorkflowError(f"secret-like value rejected at {pointer or '/'}", 4)


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError as exc:
        raise WorkflowError(f"file not found: {path}", 5) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"cannot read valid JSON from {path}: {exc}", 5) from exc
    if not isinstance(value, dict):
        raise WorkflowError(f"JSON root must be an object: {path}", 5)
    reject_secrets(value)
    return value


def _serialise(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_new_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    reject_secrets(value)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise WorkflowError(f"refusing to overwrite existing file: {path}", 3) from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_serialise(value))
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    reject_secrets(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_serialise(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


class StateLock:
    def __init__(self, state_path: Path):
        self.path = Path(f"{state_path}.lock")
        self.descriptor: int | None = None

    def __enter__(self) -> "StateLock":
        try:
            self.descriptor = os.open(
                self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
            )
        except FileExistsError as exc:
            raise WorkflowError(f"workflow state is locked: {self.path}", 3) from exc
        payload = json.dumps({"pid": os.getpid(), "created_at": utc_now()}).encode()
        os.write(self.descriptor, payload)
        os.fsync(self.descriptor)
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.descriptor is not None:
            os.close(self.descriptor)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def expected_claims(state: dict[str, Any]) -> dict[str, bool]:
    stages = state.get("stages", {})
    claims = {
        claim: stages.get(stage, {}).get("status") == "passed"
        for claim, stage in CLAIM_STAGES.items()
    }
    claims["api_ready"] = bool(
        claims["api_ready"]
        and state.get("external_resources", {}).get("api_job_id")
    )
    return claims


def derive_current_stage(state: dict[str, Any]) -> str:
    stages = state["stages"]
    active = [stage for stage in STAGE_IDS if stages[stage]["status"] in ACTIVE_STATUSES]
    if active:
        return active[0]
    for stage in STAGE_IDS:
        if stages[stage]["status"] not in {
            "passed",
            "not_applicable",
            "superseded",
        }:
            return stage
    return STAGE_IDS[-1]


def validate_state(state: dict[str, Any]) -> list[str]:
    reject_secrets(state)
    errors: list[str] = []
    if state.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    revision = state.get("state_revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        errors.append("state_revision must be a non-negative integer")
    stages = state.get("stages")
    if not isinstance(stages, dict):
        return errors + ["stages must be an object"]
    missing = [stage for stage in STAGE_IDS if stage not in stages]
    extra = [stage for stage in stages if stage not in STAGE_IDS]
    if missing:
        errors.append(f"missing stages: {', '.join(missing)}")
    if extra:
        errors.append(f"unknown stages: {', '.join(extra)}")
    if missing:
        return errors

    active: list[str] = []
    for stage_id in STAGE_IDS:
        stage = stages[stage_id]
        if not isinstance(stage, dict):
            errors.append(f"{stage_id} must be an object")
            continue
        status = stage.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{stage_id} has invalid status: {status!r}")
            continue
        if status in ACTIVE_STATUSES:
            active.append(stage_id)
        evidence = stage.get("evidence")
        stale = stage.get("stale_evidence")
        blockers = stage.get("blockers")
        if not isinstance(evidence, list):
            errors.append(f"{stage_id}.evidence must be a list")
        if not isinstance(stale, list):
            errors.append(f"{stage_id}.stale_evidence must be a list")
        if not isinstance(blockers, list):
            errors.append(f"{stage_id}.blockers must be a list")
        if status == "passed" and not evidence:
            errors.append(f"{stage_id} is passed without evidence")
        if status in ACTIVE_STATUSES | {"ready", "passed"}:
            for dependency in stage.get("depends_on", []):
                dependency_status = stages.get(dependency, {}).get("status")
                if dependency_status not in TERMINAL_FOR_DEPENDENCY:
                    errors.append(
                        f"{stage_id} requires {dependency} to be passed or not_applicable"
                    )
    if len(active) > 1:
        errors.append(f"multiple active stages: {', '.join(active)}")

    current_stage = state.get("current_stage")
    if current_stage not in STAGE_IDS:
        errors.append("current_stage is invalid")
    elif current_stage != derive_current_stage(state):
        errors.append(
            f"current_stage must be {derive_current_stage(state)}, got {current_stage}"
        )

    claims = state.get("claims")
    if claims != expected_claims(state):
        errors.append("claims do not match their stage-derived values")

    active_mutation = state.get("active_mutation")
    if active_mutation is not None:
        if not isinstance(active_mutation, dict):
            errors.append("active_mutation must be null or an object")
        else:
            required = {
                "mutation_id",
                "stage",
                "kind",
                "exact_target",
                "expected_effect",
                "expected_cost",
                "rollback_or_recovery",
                "authorization_ref",
            }
            absent = sorted(required - set(active_mutation))
            if absent:
                errors.append(f"active_mutation missing fields: {', '.join(absent)}")
            mutation_stage = active_mutation.get("stage")
            if mutation_stage != current_stage:
                errors.append("active_mutation.stage must equal current_stage")
            if stages.get(mutation_stage, {}).get("status") != "in_progress":
                errors.append("active_mutation stage must be in_progress")
    if not isinstance(state.get("mutation_history"), list):
        errors.append("mutation_history must be a list")
    return errors


def require_valid_state(state: dict[str, Any]) -> None:
    errors = validate_state(state)
    if errors:
        raise WorkflowError("; ".join(errors), 1)


def repository_root(state: dict[str, Any], state_path: Path) -> Path:
    repository = state.get("project", {}).get("repository")
    if repository:
        path = Path(repository)
        if not path.is_absolute():
            path = state_path.parent / path
        return path.resolve()
    return Path.cwd().resolve()


def validate_evidence_reference(
    reference: str, state: dict[str, Any], state_path: Path
) -> None:
    if not reference or "\x00" in reference:
        raise WorkflowError("evidence reference must be non-empty", 1)
    reject_secrets(reference, "/evidence")
    lower = reference.lower()
    if lower.startswith(SAFE_REFERENCE_PREFIXES):
        return
    raw = Path(reference)
    name = raw.name.lower()
    if (
        name in FORBIDDEN_EVIDENCE_NAMES
        or name.endswith(".har")
        or "credential" in name
    ):
        raise WorkflowError("unsafe evidence path rejected", 4)
    root = repository_root(state, state_path)
    candidate = raw if raw.is_absolute() else root / raw
    try:
        resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise WorkflowError(f"evidence file does not exist: {reference}", 1) from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise WorkflowError("evidence path escapes the repository", 4) from exc
    if not resolved.is_file():
        raise WorkflowError(f"evidence path is not a regular file: {reference}", 1)


def evidence_entries(references: Iterable[str], actor: str) -> list[dict[str, str]]:
    timestamp = utc_now()
    return [
        {"ref": reference, "actor": actor, "recorded_at": timestamp}
        for reference in references
    ]


def command_init(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    if state_path.exists():
        raise WorkflowError(f"refusing to overwrite existing file: {state_path}", 3)
    if not state_path.parent.exists() and not args.create_dirs:
        raise WorkflowError(
            f"parent directory does not exist: {state_path.parent}; use --create-dirs", 5
        )
    asset_root = Path(__file__).resolve().parent.parent / "assets"
    template = load_json(asset_root / "workflow-state.json")
    state = copy.deepcopy(template)
    state["state_revision"] = 0
    state["project"]["name"] = args.project_name
    state["project"]["repository"] = str(Path(args.repository).resolve())
    state["project"]["delivery_shape"] = args.delivery_shape
    state["updated_at"] = utc_now()
    state["claims"] = expected_claims(state)
    state["current_stage"] = derive_current_stage(state)
    require_valid_state(state)

    release_path: Path | None = None
    release: dict[str, Any] | None = None
    if args.release_record:
        release_path = Path(args.release_record)
        if release_path.exists():
            raise WorkflowError(
                f"refusing to overwrite existing file: {release_path}", 3
            )
        if not release_path.parent.exists() and not args.create_dirs:
            raise WorkflowError(
                f"parent directory does not exist: {release_path.parent}; use --create-dirs",
                5,
            )
        release = load_json(asset_root / "release-record.json")
        state["baseline"]["release_record_path"] = str(release_path)

    handoff_template = state_path.parent / "session-handoff.template.md"
    if handoff_template.exists():
        raise WorkflowError(
            f"refusing to overwrite existing file: {handoff_template}", 3
        )

    write_new_json(state_path, state)
    if release_path is not None and release is not None:
        try:
            write_new_json(release_path, release)
        except Exception:
            try:
                state_path.unlink()
            except OSError:
                pass
            raise
    try:
        with handoff_template.open("xb") as handle:
            handle.write((asset_root / "session-handoff.md").read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        for category in ("local", "image", "app", "api", "skill"):
            (state_path.parent / "evidence" / category).mkdir(parents=True)
        (state_path.parent / "handoffs").mkdir(parents=True)
    except Exception:
        for created in (handoff_template, release_path, state_path):
            if created is not None:
                try:
                    created.unlink()
                except OSError:
                    pass
        raise
    print(f"initialized {state_path}")
    return 0


def safe_status(state: dict[str, Any]) -> dict[str, Any]:
    current = state["current_stage"]
    stage = state["stages"][current]
    mutation = state.get("active_mutation")
    safe_mutation = None
    if isinstance(mutation, dict):
        safe_mutation = {
            key: mutation.get(key)
            for key in ("mutation_id", "stage", "kind", "exact_target", "started_at")
        }
    return {
        "schema": state["schema"],
        "state_revision": state["state_revision"],
        "current_stage": current,
        "stage_status": stage["status"],
        "stage_owner": stage.get("owner"),
        "claims": state["claims"],
        "blockers": stage.get("blockers", []) + state.get("blockers", []),
        "pending_authorizations": state.get("pending_authorizations", []),
        "active_mutation": safe_mutation,
        "next_action": state.get("next_action"),
        "updated_at": state.get("updated_at"),
    }


def command_status(args: argparse.Namespace) -> int:
    state = load_json(Path(args.state))
    require_valid_state(state)
    projection = safe_status(state)
    if args.json:
        print(json.dumps(projection, ensure_ascii=False, indent=2))
    else:
        print(
            f"revision={projection['state_revision']} "
            f"stage={projection['current_stage']} "
            f"status={projection['stage_status']} "
            f"owner={projection['stage_owner'] or '-'}"
        )
        ready = [name for name, value in projection["claims"].items() if value]
        print(f"claims={','.join(ready) if ready else '-'}")
        print(f"next_action={projection['next_action'] or '-'}")
    return 0


def command_check(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    state = load_json(state_path)
    errors = validate_state(state)
    if args.stage:
        if args.stage not in STAGE_IDS:
            errors.append(f"unknown stage: {args.stage}")
        elif args.for_status:
            source = state["stages"][args.stage]["status"]
            if args.for_status not in TRANSITIONS.get(source, set()):
                errors.append(f"illegal transition: {source} -> {args.for_status}")
            if args.for_status == "passed" and not state["stages"][args.stage][
                "evidence"
            ]:
                errors.append(f"{args.stage} cannot pass without evidence")
    if args.release_record:
        release = load_json(Path(args.release_record))
        candidate = state.get("external_resources", {}).get("candidate_image_id")
        recorded = release.get("identities", {}).get("candidate_image_id")
        if candidate is not None and recorded is not None and candidate != recorded:
            errors.append("candidate_image_id differs from release record")
    if errors:
        raise WorkflowError("; ".join(errors), 1)
    print("workflow state is valid")
    return 0


def _load_mutation(path: str, state_path: Path) -> dict[str, Any]:
    mutation_path = Path(path)
    if not mutation_path.is_absolute():
        mutation_path = repository_root(load_json(state_path), state_path) / mutation_path
    mutation = load_json(mutation_path)
    required = {
        "mutation_id",
        "stage",
        "kind",
        "exact_target",
        "expected_effect",
        "expected_cost",
        "rollback_or_recovery",
        "authorization_ref",
    }
    absent = sorted(required - set(mutation))
    if absent:
        raise WorkflowError(f"mutation plan missing fields: {', '.join(absent)}", 1)
    return mutation


def _invalidate_from(
    state: dict[str, Any], stage_id: str, reason: str, actor: str
) -> None:
    if state.get("active_mutation") is not None:
        raise WorkflowError("cannot invalidate while an external mutation is active", 1)
    timestamp = utc_now()
    start = STAGE_IDS.index(stage_id)
    for downstream in STAGE_IDS[start:]:
        stage = state["stages"][downstream]
        for evidence in stage.get("evidence", []):
            stage["stale_evidence"].append(
                {
                    "evidence": evidence,
                    "invalidated_at": timestamp,
                    "invalidated_by": actor,
                    "reason": reason,
                }
            )
        stage["evidence"] = []
        stage["status"] = "pending"
        stage["owner"] = None
        stage["blockers"] = []


def command_transition(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    with StateLock(state_path):
        state = load_json(state_path)
        require_valid_state(state)
        if state["state_revision"] != args.expect_revision:
            raise WorkflowError(
                f"state revision conflict: expected {args.expect_revision}, "
                f"found {state['state_revision']}",
                3,
            )
        if args.stage not in STAGE_IDS:
            raise WorkflowError(f"unknown stage: {args.stage}", 2)
        if args.to not in VALID_STATUSES:
            raise WorkflowError(f"unknown target status: {args.to}", 2)
        if args.invalidate_downstream:
            if args.to != "pending":
                raise WorkflowError("invalidation target status must be pending", 2)
            if not args.reason:
                raise WorkflowError("invalidation requires --reason", 2)
            _invalidate_from(state, args.stage, args.reason, args.actor)
        else:
            stage = state["stages"][args.stage]
            source = stage["status"]
            if args.stage != state["current_stage"]:
                raise WorkflowError(
                    f"only current_stage {state['current_stage']} may transition", 1
                )
            if args.to not in TRANSITIONS[source]:
                raise WorkflowError(f"illegal transition: {source} -> {args.to}", 1)
            if args.to in {"not_applicable", "blocked", "failed", "superseded"} and not args.reason:
                raise WorkflowError(f"transition to {args.to} requires --reason", 2)
            if args.to in ACTIVE_STATUSES:
                other_active = [
                    stage_id
                    for stage_id in STAGE_IDS
                    if stage_id != args.stage
                    and state["stages"][stage_id]["status"] in ACTIVE_STATUSES
                ]
                if other_active:
                    raise WorkflowError(
                        f"another stage is active: {', '.join(other_active)}", 1
                    )
            if args.to in ACTIVE_STATUSES | {"ready", "passed"}:
                for dependency in stage.get("depends_on", []):
                    if (
                        state["stages"][dependency]["status"]
                        not in TERMINAL_FOR_DEPENDENCY
                    ):
                        raise WorkflowError(
                            f"{args.stage} requires {dependency} to pass first", 1
                        )
            for reference in args.evidence:
                validate_evidence_reference(reference, state, state_path)
            stage["evidence"].extend(evidence_entries(args.evidence, args.actor))
            if args.to == "passed" and not stage["evidence"]:
                raise WorkflowError(f"{args.stage} cannot pass without evidence", 1)
            stage["status"] = args.to
            if args.to == "in_progress":
                stage["owner"] = args.owner or args.actor
            if args.reason and args.to in {"blocked", "failed"}:
                stage["blockers"] = [args.reason]
            elif args.to not in {"blocked", "failed"}:
                stage["blockers"] = []

        if args.begin_mutation:
            if state.get("active_mutation") is not None:
                raise WorkflowError("an external mutation is already active", 1)
            if state["stages"][args.stage]["status"] != "in_progress":
                raise WorkflowError("mutation stage must be in_progress", 1)
            mutation = _load_mutation(args.begin_mutation, state_path)
            if mutation["stage"] != args.stage:
                raise WorkflowError("mutation plan stage does not match transition stage", 1)
            mutation["started_at"] = utc_now()
            state["active_mutation"] = mutation

        if args.finish_mutation:
            mutation = state.get("active_mutation")
            if mutation is None:
                raise WorkflowError("there is no active mutation to finish", 1)
            if mutation.get("mutation_id") != args.finish_mutation:
                raise WorkflowError("active mutation ID does not match", 1)
            if not args.evidence:
                raise WorkflowError("finishing a mutation requires read-back evidence", 1)
            completed = copy.deepcopy(mutation)
            completed["finished_at"] = utc_now()
            completed["readback_evidence"] = list(args.evidence)
            state["mutation_history"].append(completed)
            state["active_mutation"] = None

        state["claims"] = expected_claims(state)
        state["current_stage"] = derive_current_stage(state)
        old_revision = state["state_revision"]
        state["state_revision"] = old_revision + 1
        timestamp = utc_now()
        state["updated_at"] = timestamp
        state.setdefault("transition_history", []).append(
            {
                "from_revision": old_revision,
                "to_revision": old_revision + 1,
                "stage": args.stage,
                "to": args.to,
                "actor": args.actor,
                "reason": args.reason,
                "at": timestamp,
            }
        )
        require_valid_state(state)
        atomic_write_json(state_path, state)
    print(
        f"transitioned {args.stage} to {args.to}; "
        f"state_revision={state['state_revision']}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="initialize state from skill assets")
    init.add_argument("--state", required=True)
    init.add_argument("--release-record")
    init.add_argument("--project-name", required=True)
    init.add_argument("--repository", default=".")
    init.add_argument(
        "--delivery-shape",
        choices=("launching", "custom-web", "mcp", "hybrid"),
        default="launching",
    )
    init.add_argument("--create-dirs", action="store_true")
    init.set_defaults(function=command_init)

    status = subparsers.add_parser("status", help="print a safe scheduler summary")
    status.add_argument("--state", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(function=command_status)

    check = subparsers.add_parser("check", help="validate state and gate invariants")
    check.add_argument("--state", required=True)
    check.add_argument("--release-record")
    check.add_argument("--stage")
    check.add_argument("--for-status", choices=tuple(sorted(VALID_STATUSES)))
    check.add_argument("--strict", action="store_true")
    check.set_defaults(function=command_check)

    transition = subparsers.add_parser(
        "transition", help="perform one checked state transition"
    )
    transition.add_argument("--state", required=True)
    transition.add_argument("--stage", required=True)
    transition.add_argument("--to", required=True)
    transition.add_argument("--actor", required=True)
    transition.add_argument("--owner")
    transition.add_argument("--expect-revision", required=True, type=int)
    transition.add_argument("--reason")
    transition.add_argument("--evidence", action="append", default=[])
    transition.add_argument("--invalidate-downstream", action="store_true")
    transition.add_argument("--begin-mutation")
    transition.add_argument("--finish-mutation")
    transition.set_defaults(function=command_transition)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return int(args.function(args))
    except WorkflowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
