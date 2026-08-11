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
living docs (`docs/**/*.md` + root `README.md`) and flags three drift classes:

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
  * ``table-duplication`` — a repo doc reproduces a codex markdown TABLE verbatim
                         (S5.11: "Never copy a codex table, contract, path template, or
                         rule into a repo doc — link it."). A repo-doc table is flagged
                         only when its CONTENT (cells, whitespace-normalized, separator
                         row excluded) is an exact match for a codex table that clears a
                         significance floor (``_MIN_TABLE_ROWS`` / ``_MIN_TABLE_CHARS`` —
                         calibrated against the live corpus, see the constants' comment).
                         The floor exists because short/generic tables (2-row toy
                         examples, common idiom shapes) are the false-positive risk the
                         Phase-5-follow-up todo called out — codex tables ARE
                         legitimately quoted/referenced in small snippets; only a
                         larger, exact, whole-table match is treated as evidence of a
                         real copy-paste. This is intentionally NOT a fuzzy/near-match
                         detector (reformatted or partially-edited copies won't be
                         caught) — exact-match keeps the false-positive rate at the same
                         low bar as the other two rules; a fuzzier pass is future work if
                         exact-match proves insufficient in practice.

``unified-trading-pm`` itself is EXCLUDED from the repo-doc walk — it IS the codex/plans
SSOT, not an audit target (plan § "Scope") — but it IS read separately to build the
codex table index the third rule matches against. Vendored mirrors (``.cursor/``),
dependency trees (``node_modules``/``.venv*``), and ``docs/archive/**`` are excluded per
the audit method (codex's own archived dirs — ``_archive``, ``_archived_pre_v2`` etc —
are excluded from the table index the same way).

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
# Matches: `<repo>-agentwork-<anything>`, `scratch-clone*`, `*-scratch-clone*`, any
# `.`/`_`-prefixed dir (`.claude`, `.tabs`, `__pycache__`), and `<repo>.stale-*` (added
# 2026-08-05, same incident CLASS as the agentwork fix above but a new naming convention:
# a fleet-wide history-rewrite operation left `<repo>.stale-pre-history-rewrite-<ts>/`
# backup copies alongside 5 repos' real checkouts, which then read as live corpus and
# false-failed `test_live_corpus_has_zero_new_drift` — same root cause (this function's
# iterdir() has no other signal than the directory name), same fix shape.
_SCRATCH_CLONE_RE = re.compile(r"(-agentwork-|(^|-)scratch-clone|\.stale-)")
# Path fragments that mark a vendored mirror / dependency tree / archived doc — excluded
# per the audit method (Appendix B: ".cursor/* symlinks excluded as vendored mirrors in
# every repo; docs/archive/* excluded").
_EXCLUDED_PARTS = ("node_modules", ".cursor")
_EXCLUDED_PART_PREFIXES = (".venv",)

_MIRROR_RE = re.compile(r"unified-trading-codex/")
# Real GCP project id (resolver-owned; S5.6 → must be {project_id}). A concrete SA email
# embedding it is caught by the same literal, so one pattern covers both S5.6 rows.
_HARDCODED_RE = re.compile(r"central-element-323112")

# table-duplication significance floor — a codex table must clear BOTH to enter the
# match index. Calibrated against the live corpus (2026-07-31, 2358 markdown tables
# across codex/): minrows=3 drops the 88 trivial 2-row (header+1) tables that are the
# dominant false-positive risk (generic 2-line idiom shapes get legitimately echoed in
# repo docs); minchars=100 is a light second filter on top (most real tables already
# clear it once minrows does). Both together still index >2200 real codex tables — the
# floor exists to exclude toy examples, not to make the rule toothless.
_MIN_TABLE_ROWS = 3  # header + >=2 data rows
_MIN_TABLE_CHARS = 100  # canonicalized text length


def _is_table_row(line: str) -> bool:
    stripped = line.strip()
    return len(stripped) > 1 and stripped.startswith("|") and stripped.endswith("|")


def _is_separator_row(line: str) -> bool:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return False
    cells = stripped[1:-1].split("|")
    return bool(cells) and all(re.fullmatch(r"\s*:?-{1,}:?\s*", c) for c in cells)


def _table_cells(line: str) -> list[str]:
    stripped = line.strip()
    inner = stripped[1:-1] if stripped.startswith("|") and stripped.endswith("|") else stripped
    return [c.strip() for c in inner.split("|")]


def _extract_tables(text: str) -> list[tuple[int, list[list[str]]]]:
    """Every markdown pipe-table in ``text``: (1-based header line, [header, *data_rows]).

    The separator row (``|---|---|``) is detected (to confirm a header) but excluded from
    the returned rows — it is pure boilerplate that would cause spurious cross-table
    collisions between differently-styled tables of the same column count.
    """
    lines = text.splitlines()
    n = len(lines)
    tables: list[tuple[int, list[list[str]]]] = []
    i = 0
    while i < n - 1:
        if _is_table_row(lines[i]) and not _is_separator_row(lines[i]) and _is_separator_row(lines[i + 1]):
            rows = [_table_cells(lines[i])]
            j = i + 2
            while j < n and _is_table_row(lines[j]) and not _is_separator_row(lines[j]):
                rows.append(_table_cells(lines[j]))
                j += 1
            tables.append((i + 1, rows))
            i = j
        else:
            i += 1
    return tables


def _canonicalize_table(rows: list[list[str]]) -> str:
    """Whitespace-normalized, case-preserving fingerprint — pipe-alignment/spacing-blind,
    content-exact (S5.11 flags VERBATIM duplication, not paraphrase)."""
    return "\n".join("\x1f".join(cell.strip() for cell in row) for row in rows)


def _iter_codex_docs(pm_root: Path) -> list[Path]:
    codex_dir = pm_root / "codex"
    if not codex_dir.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(codex_dir.rglob("*.md")):
        if not p.is_file():
            continue
        rel_parts = p.relative_to(codex_dir).parts
        if any("archiv" in part.lower() for part in rel_parts):
            continue
        out.append(p)
    return out


def _build_codex_table_index(pm_root: Path) -> dict[str, tuple[str, int]]:
    """canonical-table-text -> (codex-rel-path, 1-based header line) for every codex
    table that clears the significance floor — the verbatim-duplication oracle the
    ``table-duplication`` rule matches repo-doc tables against."""
    index: dict[str, tuple[str, int]] = {}
    for path in _iter_codex_docs(pm_root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for start_line, rows in _extract_tables(text):
            if len(rows) < _MIN_TABLE_ROWS:
                continue
            canon = _canonicalize_table(rows)
            if len(canon) < _MIN_TABLE_CHARS:
                continue
            index.setdefault(canon, (path.relative_to(pm_root).as_posix(), start_line))
    return index


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
        # Exclude PM by IDENTITY as well as by name. `_EXCLUDED_REPOS` matches the string
        # "unified-trading-pm", which silently stops working the moment PM is checked out
        # under any other directory name — exactly what `git worktree add <path>` does, and
        # what `safe-doc-push.sh` / `quickmerge --isolated` do on every run. PM then audits
        # its OWN docs as if they were a sibling repo: measured 2026-08-10, a gate run from
        # a worktree reported 14 phantom "NEW codex-SSOT drift" docs (README.md,
        # docs/BOOTSTRAP-FROM-SCRATCH.md, …) and offered `--update-baseline` as the remedy,
        # which would have written those phantoms into the shared ratchet permanently.
        # Unlike a foreign scratch clone, PM knows its own path, so name-matching is not
        # "the only signal available" here.
        if repo_dir.resolve() == PM.resolve():
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


def _scan_doc(path: Path, codex_index: dict[str, tuple[str, int]] | None = None) -> list[tuple[int, str, str]]:
    """Return (1-based line, rule, matched-literal) for every violation in one doc.

    ``codex_index`` is optional (defaults to skipping the table-duplication rule) so
    existing single-rule callers/tests are unaffected — see ``_build_codex_table_index``.
    """
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
    if codex_index:
        for start_line, rows in _extract_tables(text):
            if len(rows) < _MIN_TABLE_ROWS:
                continue
            canon = _canonicalize_table(rows)
            if len(canon) < _MIN_TABLE_CHARS:
                continue
            hit = codex_index.get(canon)
            if hit is not None:
                found.append((start_line, "table-duplication", hit[0]))
    return found


def _rel_key(path: Path, workspace_root: Path) -> str:
    """Workspace-relative baseline key, stable under symlinked repo layouts.

    Bug fixed 2026-08-10: this resolved the DOC path (following symlinks) but compared it
    against an UNRESOLVED ``workspace_root``. When a sibling repo is reached through a symlink
    -- as it is when quickmerge commits from an isolated worktree whose parent symlinks the
    real siblings -- ``.resolve()`` yields the real checkout path, which is not relative to the
    isolation workspace, so this raised ValueError and fell back to an ABSOLUTE path. Every
    pre-existing violation then missed its baseline key and was reported as NEW drift (measured:
    28 false NEW violations, against a real checkout reporting zero). Try both the literal and
    the resolved form of each side, so the key is identical whichever way the tree was reached.
    """
    for base in (workspace_root, workspace_root.resolve()):
        for candidate in (path, path.resolve()):
            try:
                return candidate.relative_to(base).as_posix()
            except ValueError:
                continue
    return path.as_posix()


def find_violations(
    paths: list[Path],
    workspace_root: Path,
    codex_index: dict[str, tuple[str, int]] | None = None,
) -> dict[str, list[tuple[int, str, str]]]:
    """Pure scan: {repo-rel-path: [(lineno, rule, literal), ...]}. Unit-testable, no baseline/CLI."""
    out: dict[str, list[tuple[int, str, str]]] = {}
    for path in paths:
        hits = _scan_doc(path, codex_index)
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
        "# in this set (a NEW mirror-ref, hardcoded resolver-owned literal, or verbatim codex-table\n"
        "# duplication in a repo doc) fails the gate. A key IN this set that no longer reproduces (the\n"
        "# drift got fixed) is harmless dead weight — remove it by re-running --update-baseline after a\n"
        "# cleanup pass.\n"
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

    codex_index = _build_codex_table_index(PM)
    scanned = find_violations(paths, workspace_root, codex_index)
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
            "    project id with the '{project_id}' placeholder (S5.6); table-duplication -> delete the\n"
            "    repo-doc table and link the cited codex doc instead (S5.11 — never copy a codex table).\n"
            "    If genuinely pre-existing debt you are not touching:\n"
            "    python3 scripts/quality_gates/check_repo_docs_ssot.py --update-baseline",
            file=sys.stderr,
        )
        return 1

    if not ns.quiet:
        print(f"✅ check_repo_docs_ssot: {len(paths)} repo docs scanned, zero NEW codex-SSOT drift")
    return 0


if __name__ == "__main__":
    sys.exit(main())
