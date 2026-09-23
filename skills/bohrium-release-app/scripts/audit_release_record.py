#!/usr/bin/env python3
"""Validate a Bohrium release ledger without printing credential-like values."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterator


SCHEMA = "bohrium-release-record/v2"
STATUSES = {"pending", "passed", "failed", "not_applicable"}
APP_TYPES = {"launching", "custom-web", "mcp", "combination"}
COMMON_GATES = {
    "source_identity", "local_tests", "artifact_integrity",
    "environment_inventory", "immutable_image", "preview_or_proxy",
    "app_page", "api_e2e", "license", "security", "scientific_claims",
    "rollback",
}
SCHEMA_GATES = {
    "bohrium-release-record/v1": COMMON_GATES
    | {"node_smoke", "cleanup_resmoke", "clean_image_job"},
    SCHEMA: COMMON_GATES
    | {"node_assembly", "snapshot_hygiene", "image_runtime_tests"},
}
SENSITIVE_KEY = re.compile(
    r"(?i)(access.?key|authorization|cookie|node.?pwd|password|secret|token)"
)
SENSITIVE_VALUE = re.compile(
    r"(?i)(accesskey=|authorization:|cookie:|bearer\s+[A-Za-z0-9._-]{8,}|"
    r"https?://[^/@\s]+:[^/@\s]+@)"
)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _walk(value: Any, path: str = "$") -> Iterator[tuple[str, str | None, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, str(key), child
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, None, child
            yield from _walk(child, child_path)


def _error(errors: list[dict[str, str]], path: str, code: str) -> None:
    errors.append({"path": path, "code": code})


def audit_record(record: Any) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    blockers: list[dict[str, str]] = []
    advisories: list[dict[str, str]] = []

    if not isinstance(record, dict):
        return {
            "schema": "bohrium-release-audit/v1",
            "valid": False,
            "release_ready": False,
            "errors": [{"path": "$", "code": "record_must_be_object"}],
            "blockers": [],
            "advisories": [],
        }

    record_schema = record.get("schema")
    if record_schema not in SCHEMA_GATES:
        _error(errors, "$.schema", "unsupported_schema")

    for path, key, value in _walk(record):
        if key is not None and SENSITIVE_KEY.search(key):
            _error(errors, path, "credential_like_key_forbidden")
        if isinstance(value, str) and SENSITIVE_VALUE.search(value):
            _error(errors, path, "credential_like_value_forbidden")
        if key is not None and key.lower().endswith("sha256") and value is not None:
            if not isinstance(value, str) or SHA256.fullmatch(value) is None:
                _error(errors, path, "invalid_sha256")

    created_at = record.get("created_at")
    if not isinstance(created_at, str) or not created_at.strip():
        blockers.append({"field": "created_at", "status": "missing"})

    app = record.get("app")
    if not isinstance(app, dict):
        _error(errors, "$.app", "app_must_be_object")
    else:
        for field in ("name", "type", "version", "adapter_version", "algorithm_version"):
            if not isinstance(app.get(field), str) or not app[field].strip():
                blockers.append({"field": f"app.{field}", "status": "missing"})
        app_type = app.get("type")
        if isinstance(app_type, str) and app_type not in APP_TYPES:
            _error(errors, "$.app.type", "unsupported_app_type")

    identities = record.get("identities")
    if not isinstance(identities, dict):
        _error(errors, "$.identities", "identities_must_be_object")
    else:
        if not identities.get("source_revision") and not identities.get("source_sha256"):
            blockers.append({"field": "identities.source", "status": "missing"})
        for field in ("artifact_sha256", "candidate_image", "rollback_image"):
            if not identities.get(field):
                blockers.append({"field": f"identities.{field}", "status": "missing"})
        if not identities.get("candidate_image_digest") and not identities.get(
            "candidate_image_id"
        ):
            blockers.append(
                {"field": "identities.candidate_image_identity", "status": "missing"}
            )
        if isinstance(app, dict) and app.get("type") in {"launching", "combination"}:
            if not identities.get("schema_sha256"):
                blockers.append({"field": "identities.schema_sha256", "status": "missing"})

    gates = record.get("gates")
    if not isinstance(gates, dict):
        _error(errors, "$.gates", "gates_must_be_object")
    else:
        required_gates = SCHEMA_GATES.get(record_schema, set())
        missing_gates = sorted(required_gates - set(gates))
        for gate_name in missing_gates:
            _error(errors, f"$.gates.{gate_name}", "missing_gate")
        for gate_name, gate in gates.items():
            path = f"$.gates.{gate_name}"
            if not isinstance(gate, dict):
                _error(errors, path, "gate_must_be_object")
                continue
            required = gate.get("required")
            status = gate.get("status")
            evidence = gate.get("evidence")
            note = gate.get("note")
            if not isinstance(required, bool):
                _error(errors, f"{path}.required", "required_must_be_boolean")
            if status not in STATUSES:
                _error(errors, f"{path}.status", "invalid_gate_status")
                continue
            if not isinstance(evidence, list) or not all(
                isinstance(item, str) and item.strip() for item in evidence
            ):
                _error(errors, f"{path}.evidence", "evidence_must_be_string_list")
                evidence = []
            if status == "passed" and not evidence:
                _error(errors, f"{path}.evidence", "passed_gate_requires_evidence")
            if status == "not_applicable":
                if required is True:
                    _error(errors, path, "required_gate_cannot_be_not_applicable")
                if not isinstance(note, str) or not note.strip():
                    _error(errors, f"{path}.note", "not_applicable_requires_note")
            if required is True and status != "passed":
                blockers.append({"gate": gate_name, "status": str(status)})
            elif required is False and status in {"pending", "failed"}:
                advisories.append({"gate": gate_name, "status": str(status)})

    valid = not errors
    return {
        "schema": "bohrium-release-audit/v1",
        "valid": valid,
        "release_ready": valid and not blockers,
        "errors": errors,
        "blockers": blockers,
        "advisories": advisories,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Return a non-zero status unless all required release gates pass.",
    )
    args = parser.parse_args()
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"cannot read release record: {type(exc).__name__}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"release record is invalid JSON at line {exc.lineno}") from exc

    result = audit_record(record)
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    if not result["valid"]:
        return 2
    if args.require_ready and not result["release_ready"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
