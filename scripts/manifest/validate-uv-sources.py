#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate [tool.uv.sources] entries in pyproject.toml files.

For every internal workspace dep listed in [project] dependencies,
each repo's pyproject.toml must have a matching [tool.uv.sources.<dep>]
entry with both:
  - path = "../<dep>"
  - editable = true

Reads workspace-manifest.json for the authoritative list of workspace repo names.

Usage:
    python validate-uv-sources.py
    python validate-uv-sources.py --repo instruments-service
    python validate-uv-sources.py --fix     # auto-add missing entries
    python validate-uv-sources.py --json    # machine-readable output

Exit: 0 = all OK, 1 = issues found (unfixed).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import cast

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"

JsonDict = dict[str, object]

SKIP_STATUSES = frozenset({"deprecated", "archived", "deleted"})
# These repos have no pyproject.toml (UI-only or devops)
SKIP_TYPES = frozenset({"ui"})


def _jdict(val: object) -> JsonDict | None:
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def _jstr(val: object, default: str = "") -> str:
    return str(val) if val is not None else default


def normalize(name: str) -> str:
    return name.lower().replace("_", "-").strip()


def load_manifest() -> JsonDict:
    with open(MANIFEST_PATH) as f:
        return cast(JsonDict, json.load(f))


def get_workspace_repo_names(manifest: JsonDict) -> frozenset[str]:
    """Return normalized set of all repo names in the manifest."""
    repos_raw = _jdict(manifest.get("repositories")) or {}
    return frozenset(normalize(r) for r in repos_raw)


def parse_internal_deps(pyproject_path: Path, workspace_repos: frozenset[str]) -> list[str]:
    """Extract internal dep names from [project] dependencies in pyproject.toml."""
    content = pyproject_path.read_text()
    # Extract all dep specs from [project] dependencies = [...] (flat deps — no optional-dependencies)
    # Simple line-based parse: find quoted package names and check if they're workspace repos
    found: list[str] = []
    # Match dependency lines like: "unified-foo>=0.1.0,<1.0.0" or "unified-foo[extra]>=..."
    for m in re.finditer(r'"([a-zA-Z0-9][a-zA-Z0-9._-]*?)(?:\[|>=|>|==|!=|<|,|")', content):
        raw_name = m.group(1)
        norm = normalize(raw_name)
        if norm in workspace_repos and norm not in found:
            found.append(norm)
    return found


def uses_inline_table_format(pyproject_path: Path) -> bool:
    """Return True if file uses [tool.uv.sources] inline table (not [tool.uv.sources.dep] sections)."""
    return any(re.match(r"^\[tool\.uv\.sources\]\s*$", line) for line in pyproject_path.read_text().splitlines())


def parse_uv_sources(pyproject_path: Path) -> dict[str, dict[str, str]]:
    """Parse [tool.uv.sources] entries from pyproject.toml.

    Handles both formats:
      Section:  [tool.uv.sources.dep-name] / path = "..." / editable = true
      Inline:   dep-name = { path = "...", editable = true }  under [tool.uv.sources]

    Returns mapping: dep_name -> {path: ..., editable: ...}
    """
    content = pyproject_path.read_text()
    sources: dict[str, dict[str, str]] = {}
    current_dep: str | None = None
    in_inline_table = False

    for line in content.splitlines():
        # Inline table header: [tool.uv.sources]
        if re.match(r"^\[tool\.uv\.sources\]\s*$", line):
            in_inline_table = True
            current_dep = None
            continue
        # Section header: [tool.uv.sources.dep-name]
        m = re.match(r"^\[tool\.uv\.sources\.([^\]]+)\]", line)
        if m:
            in_inline_table = False
            current_dep = normalize(m.group(1))
            sources.setdefault(current_dep, {})
            continue
        # Any other section header stops both modes
        if re.match(r"^\[", line):
            in_inline_table = False
            current_dep = None
            continue

        # Inline table entry: dep = { path = "...", editable = true }
        if in_inline_table:
            em = re.match(r"^([a-zA-Z0-9][a-zA-Z0-9._-]*)\s*=\s*\{([^}]+)\}", line)
            if em:
                dep = normalize(em.group(1))
                inner = em.group(2)
                entry: dict[str, str] = {}
                pm = re.search(r'path\s*=\s*"([^"]+)"', inner)
                if pm:
                    entry["path"] = pm.group(1)
                if "editable" in inner and "true" in inner:
                    entry["editable"] = "true"
                sources[dep] = entry
            continue

        # Section key-value: path = "..." or editable = true
        if current_dep is not None:
            kv = re.match(r"^(path|editable)\s*=\s*(.+)", line)
            if kv:
                key = kv.group(1)
                val = kv.group(2).strip().strip('"')
                sources[current_dep][key] = val

    return sources


def fix_pyproject(pyproject_path: Path, missing_entries: list[str]) -> None:
    """Add missing [tool.uv.sources.*] entries, respecting existing format."""
    repo_name = pyproject_path.parent.name
    content = pyproject_path.read_text()

    if uses_inline_table_format(pyproject_path):
        # Add inline entries into the existing [tool.uv.sources] block
        def add_inline(m: re.Match[str]) -> str:
            block = m.group(0)
            additions = "".join(f'{dep} = {{path = "../{dep}", editable = true}}\n' for dep in missing_entries)
            return block.rstrip("\n") + "\n" + additions + "\n"

        new_content = re.sub(
            r"^\[tool\.uv\.sources\]\n(?:[a-zA-Z0-9][a-zA-Z0-9._-]*\s*=\s*\{[^}]+\}\s*\n)*",
            add_inline,
            content,
            flags=re.MULTILINE,
        )
        pyproject_path.write_text(new_content)
    else:
        # Add section-format blocks before the first non-sources section
        additions: list[str] = []
        for dep in missing_entries:
            additions.append(f"\n[tool.uv.sources.{dep}]\n")
            additions.append(f'path = "../{dep}"\n')
            additions.append("editable = true\n")

        insert_patterns = [
            r"^\[tool\.setuptools",
            r"^\[project\]",
            r"^\[tool\.ruff",
            r"^\[tool\.basedpyright",
            r"^\[tool\.pytest",
            r"^\[tool\.coverage",
            r"^\[tool\.mypy",
            r"^\[tool\.quality",
        ]
        lines = content.splitlines(keepends=True)
        insert_at: int | None = None
        for i, line in enumerate(lines):
            for pat in insert_patterns:
                if re.match(pat, line):
                    insert_at = i
                    break
            if insert_at is not None:
                break

        addition_str = "".join(additions)
        if insert_at is not None:
            lines.insert(insert_at, addition_str)
            new_content = "".join(lines)
        else:
            new_content = content.rstrip("\n") + "\n" + addition_str
        pyproject_path.write_text(new_content)

    print(f"  [FIXED] {repo_name}: added {len(missing_entries)} missing source(s): {', '.join(missing_entries)}")


def check_repo(
    repo_name: str,
    workspace_repos: frozenset[str],
    fix: bool,
) -> list[dict[str, object]]:
    """Check a single repo. Returns list of issue dicts."""
    pyproject_path = WORKSPACE_ROOT / repo_name / "pyproject.toml"
    if not pyproject_path.exists():
        return []

    internal_deps = parse_internal_deps(pyproject_path, workspace_repos)
    uv_sources = parse_uv_sources(pyproject_path)

    issues: list[dict[str, object]] = []
    missing_entries: list[str] = []  # deps needing a full new [tool.uv.sources.*] block
    missing_editable: list[str] = []  # deps with path entry but missing editable = true

    for dep in internal_deps:
        if dep == normalize(repo_name):
            continue  # skip self-references
        entry = uv_sources.get(dep)
        if not entry:
            issues.append(
                {
                    "repo": repo_name,
                    "type": "missing_uv_source_entry",
                    "dep": dep,
                    "detail": f"[tool.uv.sources.{dep}] missing entirely",
                }
            )
            missing_entries.append(dep)
        elif entry.get("editable") != "true":
            issues.append(
                {
                    "repo": repo_name,
                    "type": "missing_editable_true",
                    "dep": dep,
                    "detail": f"[tool.uv.sources.{dep}] exists but editable = true missing",
                }
            )
            missing_editable.append(dep)

    if fix and (missing_entries or missing_editable):
        # For missing_editable: add editable = true (format-aware)
        if missing_editable:
            content = pyproject_path.read_text()
            if uses_inline_table_format(pyproject_path):
                # Inline format: dep = { path = "..." } → dep = { path = "...", editable = true }
                def add_editable_inline(m: re.Match[str]) -> str:
                    dep = normalize(m.group(1))
                    inner = m.group(2)
                    if dep in missing_editable and "editable" not in inner:
                        inner = inner.rstrip() + ", editable = true"
                    return f"{m.group(1)} = {{{inner}}}"

                new_content = re.sub(
                    r"([a-zA-Z0-9][a-zA-Z0-9._-]*)\s*=\s*\{([^}]+)\}",
                    add_editable_inline,
                    content,
                )
            else:
                # Section format: add editable = true after path line
                lines = content.splitlines(keepends=True)
                new_lines: list[str] = []
                in_section: str | None = None
                for line in lines:
                    m2 = re.match(r"^\[tool\.uv\.sources\.([^\]]+)\]", line)
                    if m2:
                        in_section = normalize(m2.group(1))
                    elif re.match(r"^\[", line):
                        in_section = None
                    new_lines.append(line)
                    if in_section in missing_editable and re.match(r'\s*path\s*=\s*"\.\./[^"]+"\s*$', line):
                        new_lines.append("editable = true\n")
                new_content = "".join(new_lines)
            pyproject_path.write_text(new_content)
            sources_str = ", ".join(missing_editable)
            print(f"  [FIXED] {repo_name}: added editable=true to {len(missing_editable)} source(s): {sources_str}")
        if missing_entries:
            fix_pyproject(pyproject_path, missing_entries)

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate [tool.uv.sources] editable entries")
    parser.add_argument("--repo", help="Check single repo only")
    parser.add_argument("--fix", action="store_true", help="Auto-add missing entries and editable=true")
    parser.add_argument("--json", action="store_true", dest="json_out", help="Machine-readable output")
    args = parser.parse_args()
    repo_filter: str | None = cast(str | None, args.repo)
    fix: bool = cast(bool, args.fix)
    json_out: bool = cast(bool, args.json_out)

    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    manifest = load_manifest()
    workspace_repos = get_workspace_repo_names(manifest)
    repos_raw = _jdict(manifest.get("repositories")) or {}

    target_repos: list[str]
    if repo_filter:
        if repo_filter not in repos_raw:
            print(f"ERROR: Repo not found in manifest: {repo_filter}", file=sys.stderr)
            return 1
        target_repos = [repo_filter]
    else:
        target_repos = sorted(repos_raw.keys())

    all_issues: list[dict[str, object]] = []
    for repo_name in target_repos:
        repo_info = _jdict(repos_raw.get(repo_name)) or {}
        status = _jstr(repo_info.get("status"), "active")
        repo_type = _jstr(repo_info.get("type"), "service")
        if status in SKIP_STATUSES or repo_type in SKIP_TYPES:
            continue
        pyproject = WORKSPACE_ROOT / repo_name / "pyproject.toml"
        if not pyproject.exists():
            continue
        issues = check_repo(repo_name, workspace_repos, fix=fix)
        all_issues.extend(issues)

    if json_out:
        out: dict[str, object] = {
            "valid": len(all_issues) == 0,
            "issues": all_issues,
            "count": len(all_issues),
        }
        print(json.dumps(out, indent=2))
        return 0 if not all_issues else 1

    if not all_issues:
        print("OK: All internal deps have [tool.uv.sources.*] with editable = true.")
        return 0

    remaining = [i for i in all_issues if not fix] if not fix else all_issues
    if fix:
        # Re-check after fix to see if anything remains
        all_issues_after: list[dict[str, object]] = []
        for repo_name in target_repos:
            repo_info = _jdict(repos_raw.get(repo_name)) or {}
            status = _jstr(repo_info.get("status"), "active")
            repo_type = _jstr(repo_info.get("type"), "service")
            if status in SKIP_STATUSES or repo_type in SKIP_TYPES:
                continue
            pyproject = WORKSPACE_ROOT / repo_name / "pyproject.toml"
            if not pyproject.exists():
                continue
            all_issues_after.extend(check_repo(repo_name, workspace_repos, fix=False))
        if not all_issues_after:
            print("OK: All issues fixed — [tool.uv.sources.*] with editable = true everywhere.")
            return 0
        remaining = all_issues_after

    print(f"Found {len(remaining)} uv-sources issue(s):\n")
    for i in remaining:
        print(f"  [{i['repo']}] {i['type']}: {i['dep']}")
        if "detail" in i:
            print(f"    {i['detail']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
