#!/usr/bin/env python3
# Epic: data_completion_to_100_all_ag
# Lifecycle: permanent
# Delete-when: NA
"""
Ratchet checker: blank asset_group at record_captured callsites.

Scans Python source in <workspace>/<scope>/ for lines that assign a blank
string to the `asset_group` keyword argument (i.e. asset_group equal to empty
string).  Per-line opt-out: add `# noqa: blank-asset-group` with
a one-line reason on the SAME source line.

Counts must stay <= the per-repo baseline.  Run with --update-baseline to
ratchet the stored count down to the current scan result.

Exit codes:
  0 -- count <= baseline (pass)
  1 -- count > baseline (fail -- new blank asset_group found)
  2 -- argument / IO error
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml  # pyyaml -- available in the QG venv


def _pm_root_or_legacy(workspace_root):
    """PM checkout root resolved by CONTENT, not by directory NAME (F7, 2026-08-10).

    See scripts/quality_gates/_pm_root.py for why. Behaviour-preserving in a canonically
    named checkout; fixes resolution when running from a git worktree."""
    import pathlib as _pathlib
    import sys as _sys

    _d = str(_pathlib.Path(__file__).resolve().parent)
    if _d not in _sys.path:
        _sys.path.insert(0, _d)
    from _pm_root import pm_root_or_legacy as _impl

    return _impl(workspace_root)


BASELINE_FILENAME = "no_blank_asset_group_baseline.yaml"
NOQA_MARKER = "noqa: blank-asset-group"

# Matches asset_group equal to empty string with optional whitespace
_BLANK_PATTERN = re.compile(r"""asset_group\s*=\s*(?:""|'')""")


def _load_baseline(baseline_path: Path) -> dict[str, int]:
    if not baseline_path.exists():
        return {}
    with baseline_path.open() as fh:
        raw = yaml.safe_load(fh)
    data = raw if isinstance(raw, dict) else {}
    repos_raw = data.get("repos")
    repos_map = repos_raw if isinstance(repos_raw, dict) else {}
    result: dict[str, int] = {}
    for repo, info in repos_map.items():
        repo_info = info if isinstance(info, dict) else {}
        result[str(repo)] = int(repo_info.get("count", 0))
    return result


def _save_baseline(
    baseline_path: Path,
    repo: str,
    count: int,
    existing: dict[str, int],
) -> None:
    existing[repo] = count
    if baseline_path.exists():
        with baseline_path.open() as fh:
            raw = yaml.safe_load(fh)
        data = raw if isinstance(raw, dict) else {}
    else:
        data = {}
    if "repos" not in data:
        data["repos"] = {}
    repos = data["repos"]
    if repo not in repos:
        repos[repo] = {}
    repos[repo]["count"] = count
    with baseline_path.open("w") as fh:
        yaml.safe_dump(data, fh, default_flow_style=False, sort_keys=True)


def _scan(source_root: Path) -> list[tuple[Path, int, str]]:
    """Return (file, lineno, line_content) for each flagged line."""
    hits: list[tuple[Path, int, str]] = []
    for py_file in sorted(source_root.rglob("*.py")):
        parts = py_file.parts
        if any(
            seg in parts
            for seg in (
                ".venv",
                ".venv-workspace",
                "node_modules",
                "build",
                "dist",
                "__pycache__",
            )
        ):
            continue
        rel = py_file.relative_to(source_root)
        if rel.parts and rel.parts[0] == "tests":
            continue
        try:
            lines = py_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, raw_line in enumerate(lines, start=1):
            if not _BLANK_PATTERN.search(raw_line):
                continue
            if NOQA_MARKER in raw_line:
                continue
            hits.append((py_file, lineno, raw_line.rstrip()))
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ratchet: blank asset_group at source callsites")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", required=True, help="Repo directory name under workspace-root")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Write the current count as the new baseline (ratchet down)",
    )
    ns = parser.parse_args(argv)
    workspace_root: Path = Path(str(ns.workspace_root)).resolve()
    scope: str = str(ns.scope)
    update_baseline: bool = ns.update_baseline is True

    source_root = workspace_root / scope
    if not source_root.is_dir():
        print(f"ERROR: source root does not exist: {source_root}", file=sys.stderr)
        return 2

    baseline_path = (_pm_root_or_legacy(workspace_root)) / "scripts" / "quality_gates" / BASELINE_FILENAME

    baselines = _load_baseline(baseline_path)
    baseline_count = baselines.get(scope, 0)

    hits = _scan(source_root)
    current_count = len(hits)

    if update_baseline:
        _save_baseline(baseline_path, scope, current_count, baselines)
        print(f"STEP 5.96: baseline updated -- {scope}: {baseline_count} -> {current_count}")
        return 0

    if current_count > baseline_count:
        print(
            f"STEP 5.96 FAIL: {scope} has {current_count} blank asset_group callsite(s)"
            f" (baseline={baseline_count}). New violations:"
        )
        for path, lineno, content in hits:
            print(f"  {path.relative_to(workspace_root / scope)}:{lineno}: {content}")
        print("\nFix: use a non-blank asset_group, or add `# noqa: blank-asset-group  <reason>` on the same line.")
        print(
            f"To ratchet the baseline down after fixing:"
            f" python {Path(__file__).name} --workspace-root <ws> --scope {scope} --update-baseline"
        )
        return 1

    print(f"STEP 5.96 OK: {scope} blank asset_group callsites = {current_count} (baseline={baseline_count})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
