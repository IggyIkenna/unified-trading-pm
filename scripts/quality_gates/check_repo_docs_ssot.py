#!/usr/bin/env python3
# Epic: plan_hygiene_master
# Lifecycle: permanent
# Delete-when: NA
"""Repo-docs-defer-to-codex QG check (S5.11 / S5.6 enforcement — Phase 5 of
codex_vs_repo_docs_ssot_audit_2026_06_01.md).

The whole codex-vs-repo-docs SSOT audit exists to make `unified-trading-pm/codex/`
the single source of truth and stop every service repo's `docs/` from duplicating or
staling against it. Phases 1-4 audited + remediated the corpus; this check is the
Phase-5 ENFORCEMENT so the win cannot silently rot back. It walks every sibling repo's
living docs (`docs/**/*.md` + root `README.md`) and flags the two deterministic,
low-false-positive drift classes the audit found dominant across 20 repos:

  * ``mirror-ref``     — a repo doc references the ARCHIVED ``unified-trading-codex/``
                         mirror instead of the live PM ``/codex/`` SSOT. Appendix B of
                         the plan found this the single most common remediation across
                         the corpus. Remedy: repoint at ``unified-trading-pm/codex/…``
                         (or the repo-relative ``../../unified-trading-pm/codex/…``).
  * ``hardcoded-literal`` — a repo doc hardcodes a resolver-owned literal S5.6 bans:
                         the real GCP project id ``central-element-323112`` (use
                         ``{project_id}``) or a concrete ``…@central-element-323112.iam.
                         gserviceaccount.com`` service-account email (use
                         ``{service_account}``). Bucket FAMILY patterns that already
                         template the project (``…-cefi-prd-{project_id}``) are the
                         canonical documented form and are NOT flagged.

``unified-trading-pm`` itself is EXCLUDED — it IS the codex/plans SSOT, not an audit
target (plan § "Scope"). Vendored mirrors (``.cursor/``), dependency trees
(``node_modules``/``.venv*``), and ``docs/archive/**`` are excluded per the audit method.

Ratcheted against ``repo_docs_ssot_baseline.yaml`` (same shrinking-ratchet convention as
``doc_body_link_baseline.yaml``): pre-existing debt seeded at first run doesn't fail every
build — only a NEW occurrence (a key not in the baseline) fails the gate. Fix drift and
re-run ``--update-baseline`` to ratchet the tolerated set DOWN.

Usage: check_repo_docs_ssot.py [--workspace-root DIR] [file ...]
  --workspace-root DIR   workspace root holding the sibling repo clones (default: two
                         levels above the PM repo root, matching the other workspace-wide
                         PM gates).
  --quiet                suppress the success line.
  --update-baseline      regenerate repo_docs_ssot_baseline.yaml from the CURRENT full
                         scan (run after a cleanup pass; NEVER to launder a check you just
                         introduced — see the baseline file's own header).
Exit 0 = zero NEW violations. Exit 1 = new drift (each printed with its remedy).
Exit 2 = argument / IO error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).resolve().parent / "repo_docs_ssot_baseline.yaml"

# Repos that are NOT audit targets: the PM repo is the SSOT itself.
_EXCLUDED_REPOS = {"unified-trading-pm"}
# Scratch/agent-work clones sitting alongside the real sibling repos are NOT audit targets
# (added 2026-07-30). `_iter_repo_docs()` blindly `iterdir()`s every directory in the
# workspace root, so a throwaway clone like
# `instruments-service-agentwork-sports-2026-07-13/` read as a real repo owing doc-SSOT
# compliance and its frozen, weeks-old `docs/` re-entered the scan — pure noise, and a
# false gate failure nobody could fix without deleting a directory that isn't a repo.
# Same intent as check_frontmatter_schema.py's `_CLAUDE_WORKTREE_PREFIX` exclusion (a live
# agent's `.claude/worktrees/<id>/` copy is scratch space, never real corpus content) —
# mirrored here on the directory NAME, which is the only signal available at this level.
# Matches: `<repo>-agentwork-<anything>`, `scratch-clone*`, `*-scratch-clone*`, and any
# `.`/`_`-prefixed dir (`.claude`, `.tabs`, `__pycache__`).
_SCRATCH_CLONE_RE = re.compile(r"(-agentwork-|(^|-)scratch-clone)")
# Path fragments that mark a vendored mirror / dependency tree / archived doc — excluded
# per the audit method (Appendix B: ".cursor/* symlinks excluded as vendored mirrors in
# every repo; docs/archive/* excluded").
_EXCLUDED_PARTS = ("node_modules", ".cursor")
_EXCLUDED_PART_PREFIXES = (".venv",)

_MIRROR_RE = re.compile(r"unified-trading-codex/")
# Real GCP project id (resolver-owned; S5.6 → must be {project_id}). A concrete SA email
# embedding it is caught by the same literal, so one pattern covers both S5.6 rows.
_HARDCODED_RE = re.compile(r"central-element-323112")


def _is_excluded(rel_parts: tuple[str, ...]) -> bool:
    for part in rel_parts:
        if part in _EXCLUDED_PARTS:
            return True
        if any(part.startswith(pref) for pref in _EXCLUDED_PART_PREFIXES):
            return True
    # docs/archive/** — the audit method excludes archived docs.
    return "archive" in rel_parts


def _is_scratch_clone(name: str) -> bool:
    """True for a throwaway agent-work / scratch clone sitting next to the real repos.

    Name-based by necessity — at workspace-root level there is nothing else to go on. See
    `_SCRATCH_CLONE_RE` for the incident this closes.
    """
    return name.startswith((".", "_")) or bool(_SCRATCH_CLONE_RE.search(name))


def _iter_repo_docs(workspace_root: Path) -> list[Path]:
    """Every living repo doc in scope: each sibling repo's docs/**/*.md + root README.md."""
    out: list[Path] = []
    for repo_dir in sorted(workspace_root.iterdir()):
        if not repo_dir.is_dir() or repo_dir.name in _EXCLUDED_REPOS:
            continue
        if _is_scratch_clone(repo_dir.name):
            continue
        readme = repo_dir / "README.md"
        if readme.is_file():
            out.append(readme)
        docs_dir = repo_dir / "docs"
        if not docs_dir.is_dir():
            continue
        for p in sorted(docs_dir.rglob("*.md")):
            if not p.is_file():
                continue
            rel_parts = p.relative_to(repo_dir).parts
            if _is_excluded(rel_parts):
                continue
            out.append(p)
    return out


def _scan_doc(path: Path) -> list[tuple[int, str, str]]:
    """Return (1-based line, rule, matched-literal) for every violation in one doc."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    found: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if _MIRROR_RE.search(line):
            found.append((lineno, "mirror-ref", "unified-trading-codex/"))
        if _HARDCODED_RE.search(line):
            found.append((lineno, "hardcoded-literal", "central-element-323112"))
    return found


def _rel_key(path: Path, workspace_root: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root).as_posix()
    except ValueError:
        return path.as_posix()


def find_violations(paths: list[Path], workspace_root: Path) -> dict[str, list[tuple[int, str, str]]]:
    """Pure scan: {repo-rel-path: [(lineno, rule, literal), ...]}. Unit-testable, no baseline/CLI."""
    out: dict[str, list[tuple[int, str, str]]] = {}
    for path in paths:
        hits = _scan_doc(path)
        if hits:
            out[_rel_key(path, workspace_root)] = hits
    return out


def _load_baseline() -> set[str]:
    if not BASELINE.is_file():
        return set()
    data = yaml.safe_load(BASELINE.read_text()) or {}
    known = data.get("known_violations") or []
    return {str(k) for k in known}


def _write_baseline(keys: set[str]) -> None:
    BASELINE.write_text(
        "# Baseline for the repo-docs-defer-to-codex check (check_repo_docs_ssot.py).\n"
        "#\n"
        "# SHRINKING ratchet, same convention as doc_body_link_baseline.yaml. `known_violations`\n"
        '# is the exact set of "<repo-rel-doc>::<rule>::<literal>" keys tolerated today. A key NOT\n'
        "# in this set (a NEW mirror-ref or hardcoded resolver-owned literal in a repo doc) fails\n"
        "# the gate. A key IN this set that no longer reproduces (the drift got fixed) is harmless\n"
        "# dead weight — remove it by re-running --update-baseline after a cleanup pass.\n"
        "#\n"
        "# NEVER add an entry here to silence a check you introduced yourself — this baseline is for\n"
        "# PRE-EXISTING debt found at seed time (Phase 5 of codex_vs_repo_docs_ssot_audit_2026_06_01),\n"
        "# not a way to launder new drift.\n"
        "known_violations:\n"
        + "".join(f"  - {yaml.safe_dump(k, default_style=chr(34), width=float('inf')).strip()}\n" for k in sorted(keys))
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Flag repo docs that stale against / duplicate the codex SSOT.")
    parser.add_argument("--workspace-root", type=Path, default=PM.parent, help="Workspace root (default: PM parent)")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("files", nargs="*", type=Path)
    ns = parser.parse_args(argv)

    workspace_root: Path = ns.workspace_root.resolve()
    if not workspace_root.is_dir():
        print(f"ERROR: workspace-root does not exist: {workspace_root}", file=sys.stderr)
        return 2

    # --update-baseline always scans the FULL corpus (the baseline is total corpus state).
    if ns.update_baseline or not ns.files:
        paths = _iter_repo_docs(workspace_root)
    else:
        paths = [p if p.is_absolute() else (workspace_root / p) for p in ns.files]

    scanned = find_violations(paths, workspace_root)
    all_keys: set[str] = set()
    for rel, hits in scanned.items():
        for _lineno, rule, literal in hits:
            all_keys.add(f"{rel}::{rule}::{literal}")

    if ns.update_baseline:
        _write_baseline(all_keys)
        print(f"repo_docs_ssot_baseline.yaml regenerated: {len(all_keys)} known_violations entries.")
        return 0

    baseline = _load_baseline()
    bad: list[tuple[str, list[str]]] = []
    for rel, hits in sorted(scanned.items()):
        problems: list[str] = []
        seen: set[str] = set()
        for lineno, rule, literal in hits:
            key = f"{rel}::{rule}::{literal}"
            if key in baseline or key in seen:
                continue
            seen.add(key)
            problems.append(f"line {lineno}: {rule} -> '{literal}' (NEW — not in repo_docs_ssot_baseline.yaml)")
        if problems:
            bad.append((rel, problems))

    if bad:
        print(f"❌ check_repo_docs_ssot: {len(bad)} repo doc(s) with NEW codex-SSOT drift:", file=sys.stderr)
        for rel, problems in bad:
            print(f"  {rel}:", file=sys.stderr)
            for pr in problems:
                print(f"    - {pr}", file=sys.stderr)
        print(
            "  Remedy: mirror-ref -> repoint at the live 'unified-trading-pm/codex/…' SSOT (the\n"
            "    'unified-trading-codex/' mirror is ARCHIVED); hardcoded-literal -> replace the real\n"
            "    project id with the '{project_id}' placeholder (S5.6). If genuinely pre-existing debt\n"
            "    you are not touching: python3 scripts/quality_gates/check_repo_docs_ssot.py --update-baseline",
            file=sys.stderr,
        )
        return 1

    if not ns.quiet:
        print(f"✅ check_repo_docs_ssot: {len(paths)} repo docs scanned, zero NEW codex-SSOT drift")
    return 0


if __name__ == "__main__":
    sys.exit(main())
