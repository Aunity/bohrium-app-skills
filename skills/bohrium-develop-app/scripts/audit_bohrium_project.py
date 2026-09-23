#!/usr/bin/env python3
"""Produce a read-only, secret-safe inventory of a candidate Bohrium App repo."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


EXCLUDED_DIRS = {
    ".git",
    ".envs",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "build",
    "dist",
    "node_modules",
}
TEXT_SUFFIXES = {".md", ".py", ".toml", ".yaml", ".yml", ".json", ".sh"}
MAX_SCAN_BYTES = 2_000_000
LIKELY_SECRET = re.compile(
    r"(?i)(?:access[_-]?key|authorization|cookie|nodepwd|password|secret|token)"
    r'''\s*[:=]\s*["'][^"'$\{\}]{8,}["']'''
)


def _files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            continue
        if path.is_file():
            yield path


def _relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def _read_small_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_SCAN_BYTES:
            return None
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != "Dockerfile":
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def audit(root: Path) -> dict[str, object]:
    paths = list(_files(root))
    rels = [_relative(path, root) for path in paths]
    app_types: set[str] = set()
    evidence_files: list[str] = []
    stale_markers: list[dict[str, object]] = []
    secret_risk_locations: list[str] = []

    combined_hints = "\n".join(
        rel for rel in rels if rel.endswith((".py", ".toml", "Dockerfile"))
    ).lower()
    if "launching_entry.py" in combined_hints:
        app_types.add("launching")
    if "mcp" in combined_hints:
        app_types.add("mcp-candidate")

    for path in paths:
        rel = _relative(path, root)
        lower = rel.lower()
        if any(term in lower for term in ("deployment", "release", "validation", "acceptance")):
            evidence_files.append(rel)
        text = _read_small_text(path)
        if text is None:
            continue
        lowered = text.lower()
        is_runtime_source = path.suffix.lower() in {".py", ".toml"} or path.name == "Dockerfile"
        if is_runtime_source:
            if "dp.launching" in lowered or "inputfilepath" in lowered:
                app_types.add("launching")
            if any(term in lowered for term in ("fastapi", "uvicorn", "gradio", "streamlit")):
                app_types.add("custom-web-candidate")
            if "fastmcp" in lowered or "@mcp.tool" in lowered:
                app_types.add("mcp")
        marker_count = len(re.findall(r"\b(?:TODO|TBD)\b|尚未|待执行|待验证", text))
        if marker_count:
            stale_markers.append({"path": rel, "count": marker_count})
        if LIKELY_SECRET.search(text):
            secret_risk_locations.append(rel)

    key_names = {
        "pyproject.toml",
        "Dockerfile",
        "launching_entry.py",
        "AGENTS.md",
        "README.md",
    }
    key_files = sorted(rel for rel in rels if Path(rel).name in key_names)
    schemas = sorted(
        rel
        for rel in rels
        if "schema" in Path(rel).name.lower() and rel.endswith((".json", ".py"))
    )
    skills = sorted(rel for rel in rels if Path(rel).name == "SKILL.md")
    tests = sorted(rel for rel in rels if "test" in Path(rel).name.lower())

    return {
        "schema": "bohrium-project-audit/v1",
        "project": str(root),
        "app_type_signals": sorted(app_types) or ["undetermined"],
        "key_files": key_files,
        "evidence_files": sorted(evidence_files),
        "schema_files": schemas,
        "skill_files": skills,
        "test_file_count": len(tests),
        "stale_marker_locations": sorted(
            stale_markers, key=lambda item: (-int(item["count"]), str(item["path"]))
        ),
        "possible_hardcoded_secret_locations": sorted(secret_risk_locations),
        "notes": [
            "Signals are inventory hints, not proof of deployment or publication.",
            "Possible secret locations report paths only and never print matched values.",
            "Excluded build, environment, cache, VCS and node_modules directories.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = args.project.resolve()
    if not root.is_dir():
        raise SystemExit(f"project directory does not exist: {root}")
    print(
        json.dumps(
            audit(root),
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
