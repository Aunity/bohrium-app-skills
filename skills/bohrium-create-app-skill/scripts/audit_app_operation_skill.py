#!/usr/bin/env python3
"""Audit a Bohrium App operation skill without executing its client code."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any


AUDIT_SCHEMA = "bohrium-app-operation-skill-audit/v1"
REQUIRED_COMMANDS = {
    "schema",
    "plan",
    "submit",
    "run",
    "status",
    "wait",
    "logs",
    "download",
}
KNOWN_COMMANDS = REQUIRED_COMMANDS | {"kill", "delete"}
CREDENTIAL_ARGUMENTS = {
    "--access-key",
    "--access_key",
    "--authorization",
    "--cookie",
    "--password",
    "--token",
}
HARD_CODED_SECRET = re.compile(
    r"(?i)(bearer\s+[a-z0-9._-]{12,}|accesskey=[^&\s]{8,}|"
    r"https?://[^/@\s]+:[^/@\s]+@|sk-[a-z0-9_-]{12,})"
)
FRONTMATTER_FIELD = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
MAX_SOURCE_BYTES = 2 * 1024 * 1024


def _issue(items: list[dict[str, str]], path: Path | str, code: str) -> None:
    items.append({"path": str(path), "code": code})


def _read_text(path: Path, errors: list[dict[str, str]]) -> str | None:
    try:
        if path.is_symlink():
            _issue(errors, path, "symlink_not_audited")
            return None
        if path.stat().st_size > MAX_SOURCE_BYTES:
            _issue(errors, path, "file_too_large")
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        _issue(errors, path, "file_unreadable")
        return None


def _frontmatter(text: str) -> tuple[dict[str, str], str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return None
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        match = FRONTMATTER_FIELD.fullmatch(line)
        if match:
            fields[match.group(1)] = match.group(2).strip("'\"")
    return fields, "\n".join(lines[end + 1 :])


class ClientVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.strings: set[str] = set()
        self.attributes: set[str] = set()
        self.shell_true = False
        self.hard_coded_secret = False

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            self.strings.add(node.value)
            if HARD_CODED_SECRET.search(node.value):
                self.hard_coded_secret = True
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.attributes.add(node.attr)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        for keyword in node.keywords:
            if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant):
                if keyword.value.value is True:
                    self.shell_true = True
        self.generic_visit(node)


def _audit_client(
    script: Path,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> set[str]:
    source = _read_text(script, errors)
    if source is None:
        return set()
    try:
        tree = ast.parse(source, filename=str(script))
    except SyntaxError:
        _issue(errors, script, "python_syntax_error")
        return set()

    visitor = ClientVisitor()
    visitor.visit(tree)
    commands = KNOWN_COMMANDS & visitor.strings

    missing = sorted(REQUIRED_COMMANDS - commands)
    for command in missing:
        _issue(errors, script, f"missing_command:{command}")
    if "delete" in commands or "delete" in visitor.attributes:
        _issue(errors, script, "delete_operation_forbidden")
    if visitor.shell_true:
        _issue(errors, script, "shell_true_forbidden")
    if visitor.hard_coded_secret:
        _issue(errors, script, "hard_coded_secret_like_literal")
    for argument in sorted(CREDENTIAL_ARGUMENTS & visitor.strings):
        _issue(errors, script, f"credential_cli_argument_forbidden:{argument}")
    if {"submit", "run", "kill"} & commands and "--yes" not in visitor.strings:
        _issue(errors, script, "mutating_commands_require_yes")

    checks = {
        "json_stdout_pattern_not_detected": "_json_print" in source,
        "stderr_pattern_not_detected": "sys.stderr" in source,
        "offline_plan_marker_not_detected": "network_used" in source,
        "nonempty_download_guard_not_detected": "iterdir" in source,
        "outputs_download_mapping_not_detected": '"outputs"' in source
        or "'outputs'" in source,
    }
    for code, detected in checks.items():
        if not detected:
            _issue(warnings, script, code)
    return commands


def audit_skill(skill_dir: Path) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    name: str | None = None

    if not skill_dir.is_dir():
        _issue(errors, skill_dir, "skill_directory_missing")
        return {
            "schema": AUDIT_SCHEMA,
            "valid": False,
            "skill_name": None,
            "client_scripts": [],
            "commands": [],
            "errors": errors,
            "warnings": warnings,
        }

    skill_file = skill_dir / "SKILL.md"
    skill_text = _read_text(skill_file, errors) if skill_file.is_file() else None
    if skill_text is None:
        if not skill_file.exists():
            _issue(errors, skill_file, "skill_file_missing")
    else:
        parsed = _frontmatter(skill_text)
        if parsed is None:
            _issue(errors, skill_file, "invalid_frontmatter")
        else:
            metadata, body = parsed
            name = metadata.get("name")
            if name != skill_dir.name:
                _issue(errors, skill_file, "skill_name_must_match_directory")
            if not metadata.get("description"):
                _issue(errors, skill_file, "description_missing")
            if len(body.splitlines()) > 500:
                _issue(errors, skill_file, "skill_body_too_long")

        for raw_target in MARKDOWN_LINK.findall(skill_text):
            target = raw_target.strip().strip("<>").split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if target.startswith("/"):
                _issue(errors, skill_file, "absolute_local_link_forbidden")
                continue
            linked = skill_dir / target
            if not linked.exists():
                _issue(errors, linked, "linked_resource_missing")

    metadata_file = skill_dir / "agents" / "openai.yaml"
    metadata_text = (
        _read_text(metadata_file, errors) if metadata_file.is_file() else None
    )
    if metadata_text is None:
        if not metadata_file.exists():
            _issue(errors, metadata_file, "openai_yaml_missing")
    elif name and f"${name}" not in metadata_text:
        _issue(errors, metadata_file, "default_prompt_must_mention_skill")

    scripts_dir = skill_dir / "scripts"
    scripts = sorted(scripts_dir.glob("*.py")) if scripts_dir.is_dir() else []
    if not scripts:
        _issue(errors, scripts_dir, "client_script_missing")
    all_commands: set[str] = set()
    for script in scripts:
        all_commands.update(_audit_client(script, errors, warnings))

    errors.sort(key=lambda item: (item["path"], item["code"]))
    warnings.sort(key=lambda item: (item["path"], item["code"]))
    return {
        "schema": AUDIT_SCHEMA,
        "valid": not errors,
        "skill_name": name,
        "client_scripts": [str(path) for path in scripts],
        "commands": sorted(all_commands),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    result = audit_skill(args.skill_dir)
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
