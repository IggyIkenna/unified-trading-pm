#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate codex references in T0-T2 repos and cursor rules.

Phase 8: plans_to_deployable_unified_audit.md (Approach A — validator only).
- Scans PM cursor-rules (canonical) and T0-T2 .py source for CODEX:/See codex patterns
- Validates each codex path exists in unified-trading-codex
- Validates manifest codex_sections exist
- Skips refs to non-codex paths (unified-trading-pm/, etc.)

GATE: run_validators.py --check-codex-refs exits 0 when no broken codex refs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import cast

# JSON typing: json.load returns Any; cast at boundary
JsonDict = dict[str, "JsonDict | list[JsonDict] | str | int | float | bool | None"]


def _jdict(val: object) -> JsonDict | None:
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def _jlist(val: object) -> list[JsonDict] | None:
    if isinstance(val, list):
        return cast(list[JsonDict], val)
    return None


def _jstr(val: object, default: str = "") -> str:
    return str(val) if val is not None else default


CODEX_PATTERNS = [
    re.compile(r"CODEX:\s*([^\n]+?)(?:\s+CODEX:|\s*$)", re.IGNORECASE | re.DOTALL),
    re.compile(r"[Ss]ee\s+codex:\s*`([^`]+)`"),
    re.compile(r"codex-ref:\s*([^\s]+)"),
]

# Paths that are NOT in codex — skip validation
NON_CODEX_PREFIXES = (
    "unified-trading-pm/",
    "unified-trading-library/",
    "unified-trading-services/",
    ".cursor/",
    "pyrightconfig.json",  # repo-level, not codex
)


def _clean_path(p: str) -> str:
    p = p.split("#")[0].strip().strip("'`")
    p = re.sub(r"\s*\(§[^)]*\)\s*$", "", p)
    p = re.sub(r"\s*\(§.*", "", p)  # unclosed (§
    p = re.sub(r"\. See also:.*$", "", p)
    p = re.sub(r"\s*\(SSOT\)\s*$", "", p)
    return p.strip()


def extract_codex_paths(text: str) -> list[str]:
    paths: list[str] = []
    for pat in CODEX_PATTERNS:
        for m in pat.finditer(text):
            raw = m.group(1).strip()
            for part in re.split(r"\s*,\s*", raw):
                part = part.strip().rstrip(".,;")
                if not part:
                    continue
                if part.startswith(".cursor/"):
                    continue
                for skip in NON_CODEX_PREFIXES:
                    if part.startswith(skip) or part == skip:
                        part = None
                        break
                if part:
                    part = _clean_path(part)
                    if part.startswith("unified-trading-codex/"):
                        part = part[len("unified-trading-codex/") :]
                    if part:
                        paths.append(part)
    return paths


def resolve_codex_path(path: str, codex_root: Path) -> Path | None:
    path = path.strip().rstrip(".,;").split("#")[0]
    candidates = [
        codex_root / path,
        codex_root / f"{path}.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    if (codex_root / path).is_dir():
        return codex_root / path
    base = path.split("/")[-1]
    for d in ["06-coding-standards", "05-infrastructure", "04-architecture", "02-data", "03-observability"]:
        c = codex_root / d / base
        if c.exists():
            return c
    return None


def main() -> int:  # noqa: C901
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    pm_root = script_dir.parent.parent
    ws_root: Path = (cast(Path | None, args.workspace_root) or pm_root.parent).resolve()
    codex_root = ws_root / "unified-trading-codex"
    manifest_path: Path = cast(Path | None, args.manifest) or pm_root / "workspace-manifest.json"

    if not codex_root.is_dir():
        print(f"Skip: codex not found at {codex_root}", file=sys.stderr)
        return 0

    broken: list[tuple[str, int, str]] = []

    repos_to_scan: list[tuple[str, Path]] = []
    codex_sections_to_validate: set[str] = set()

    if manifest_path.is_file():
        with open(manifest_path) as f:
            manifest: JsonDict = cast(JsonDict, json.load(f))
        if "repositories" not in manifest:
            raise KeyError("repositories required in workspace-manifest.json")
        repos_obj = manifest["repositories"]
        repos_dict = _jdict(repos_obj) or {}
        for name, meta_raw in repos_dict.items():
            meta = _jdict(meta_raw)
            if meta is None:
                continue
            arch_tier: object | None = meta.get("arch_tier")
            if arch_tier is None:
                continue
            tier: str = str(arch_tier)
            if tier not in ("0", "1", "2"):
                continue
            repo_path: Path = ws_root / name
            if repo_path.is_dir():
                repos_to_scan.append((name, repo_path))
            codex_sections_raw: object = meta.get("codex_sections") or []  # optional per repo
            if isinstance(codex_sections_raw, list):
                for sec in codex_sections_raw:
                    codex_sections_to_validate.add(str(sec))

    cursor_rules = pm_root / "cursor-rules"
    if cursor_rules.is_dir():
        repos_to_scan.append(("cursor-rules", cursor_rules))

    for repo_name, repo_path in repos_to_scan:
        exts = ["*.py"] if "cursor-rules" not in repo_name else ["*.mdc"]
        for ext in exts:
            for fpath in repo_path.rglob(ext):
                if ".venv" in str(fpath) or "node_modules" in str(fpath) or "/build/" in str(fpath):
                    continue
                if repo_name != "cursor-rules" and ".cursor" in str(fpath):
                    continue
                try:
                    content = fpath.read_text()
                except OSError:
                    continue
                rel = fpath.relative_to(ws_root)
                for i, line in enumerate(content.splitlines(), 1):
                    for path_str in extract_codex_paths(line):
                        if not path_str or any(path_str.startswith(p) for p in NON_CODEX_PREFIXES):
                            continue
                        if "/" not in path_str and not path_str.endswith(".md") and not path_str.endswith(".sh"):
                            continue
                        resolved = resolve_codex_path(path_str, codex_root)
                        if resolved is None:
                            broken.append((str(rel), i, path_str))

    for sec in codex_sections_to_validate:
        if not (codex_root / sec).exists():
            broken.append(("workspace-manifest.json", 0, f"codex_sections: {sec}"))

    if broken:
        for src, line, ref in broken:
            if line:
                print(f"BROKEN: {src}:{line} -> {ref}", file=sys.stderr)
            else:
                print(f"BROKEN: {src} codex_section -> {ref}", file=sys.stderr)
        return 1

    print("OK: All codex refs valid (T0-T2 + cursor-rules + manifest codex_sections)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
