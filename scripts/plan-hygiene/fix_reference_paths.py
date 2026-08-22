#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Normalize cross-doc references to the leading-slash, PM-repo-root-relative
convention (operator ruling 2026-07-23): /codex/... and /plans/....

Two independent, safe passes — both touch only free-text/documentation content,
never a machine-parsed identifier field:

1. Codex refs, ANYWHERE in file content (bare `codex/...`, relative `../codex/...`,
   or already-correct `/codex/...`) -> normalized to `/codex/...`.
2. Bare `.md` filenames inside the `related:` frontmatter field -> resolved against
   the actual corpus (plans/active, plans/active/issues, plans/epics, plans/archive/**)
   and rewritten to `/plans/<found-relative-path>`. Ambiguous (multiple matches) or
   unresolvable (zero matches) entries are left untouched and reported — never guessed.

Deliberately OUT of scope (machine-parsed bare-slug fields, PLAN_FORMAT.md's documented
format — a path/extension here changes backend parsing semantics, not just doc hygiene):
  depends_on, parent_epic, supersedes, superseded_by, entry_point_for

Usage:
  python3 scripts/plan-hygiene/fix_reference_paths.py [--dry-run]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PM_DIR = Path(__file__).resolve().parents[2]

TARGET_GLOBS = [
    "plans/**/*.md",
    "codex/**/*.md",
    "cursor-configs/**/*.md",
]

# Pre-existing frontmatter defects unrelated to this migration (confirmed BROKEN/absent in
# HEAD before it ever touched them — see plans/active/issues/reference_path_convention_2026_07_23.md):
# 8 have structural YAML syntax errors (indentation-based block-mapping breaks, not simple
# colons); 3 have no `---` frontmatter block at all (scratch scenario docs). Skipped so
# re-running this script (needed every time new content lands mid-migration) doesn't keep
# re-touching them and dragging them back into a staged diff the commit-hook's frontmatter
# checks then block on. Remove an entry once its underlying frontmatter defect is fixed.
SKIP_PRE_EXISTING_FRONTMATTER_DEFECTS = {
    "plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md",
    "plans/archive/2026_06/cicd_v2_latency_reduction_2026_06_10.md",
    "plans/archive/api_keys_and_auth.plan.md",
    "plans/archive/carry_staked_basis_structure_axis_2026_05_04.plan.md",
    "plans/archive/cross_asset_group_catalogue_audit_2026_05_10.md",
    "codex/15-runbooks/alerting/README.md",
    "codex/15-runbooks/alerting/_template.md",
    "codex/15-runbooks/incidents/README.md",
    "plans/active/scratch_scenarios_day1/03_defi_liquidity_drain_lending_pool.md",
    "plans/active/scratch_scenarios_day1/06_defi_mempool_congestion.md",
    "plans/active/scratch_scenarios_day1/11_handshake_integration.md",
}

# Two shapes both normalize to /codex/<rest>: an explicit `codex/` prefix (bare, relative,
# or already-leading-slash), OR a codex-INTERNAL relative ref with the `codex/` segment
# elided (one codex doc citing a sibling numbered section, e.g. `../06-coding-standards/
# foo.md` written from inside codex/ — the `NN-lowercase-words/` shape is codex's own
# subdirectory convention, not used anywhere under plans/, so it's an unambiguous signal
# even without a literal "codex/" in the match).
CODEX_RE = re.compile(r"(?<![\w/])(?:\.\./)*/?codex/([0-9]{2}-[a-z-]+/[A-Za-z0-9_./-]+\.md)")
CODEX_RELATIVE_RE = re.compile(r"(?<![\w/])\.\./([0-9]{2}-[a-z-]+/[A-Za-z0-9_./-]+\.md)")

# A bare filename (no path separator) ending .md, used to scan inside `related:` blocks.
# Lookbehind excludes word-char / slash / hyphen / dot so a hyphenated or dotted filename
# (e.g. "data-engine-selection.md", "foo.HANDOVER.md") is never mistakenly split into a
# false match starting mid-filename at one of its own hyphens or dots.
BARE_MD_RE = re.compile(r"(?<![\w/.-])([A-Za-z0-9_-]+\.md)")


def build_filename_index() -> dict[str, list[str]]:
    """basename -> [relpath-from-PM_DIR, ...] for every .md anywhere under plans/ (the
    whole tree — active, active/issues, epics, archive/**, audit/**, ai, cicd, handover,
    ops, prompts, questions, tasks, top-level) AND codex/ (so a codex doc's `related:`
    field citing another bare codex filename, e.g. archived strategy docs cross-citing
    each other, also resolves) — a plan filename and a codex filename sharing an exact
    basename is not expected in practice, so one merged index is safe."""
    index: dict[str, list[str]] = {}
    for top in ("plans", "codex"):
        base = PM_DIR / top
        if not base.exists():
            continue
        for p in base.rglob("*.md"):
            rel = p.relative_to(PM_DIR).as_posix()
            index.setdefault(p.name, []).append(rel)
    return index


def normalize_codex_refs(text: str, is_codex_file: bool) -> tuple[str, int]:
    matches = CODEX_RE.findall(text)
    new_text = CODEX_RE.sub(lambda m: f"/codex/{m.group(1)}", text)
    if is_codex_file:
        # Only within codex/ itself — see CODEX_RELATIVE_RE's comment for why this shape
        # is unambiguous there but not assumed corpus-wide.
        matches += CODEX_RELATIVE_RE.findall(new_text)
        new_text = CODEX_RELATIVE_RE.sub(lambda m: f"/codex/{m.group(1)}", new_text)
    return new_text, len(matches)


def extract_related_block(text: str) -> tuple[int, int] | None:
    """Return (start, end) char offsets of the `related:` field's VALUE within the
    frontmatter block (between the first two `---` lines), or None if absent."""
    fm_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not fm_match:
        return None
    fm_start, fm_end = fm_match.start(1), fm_match.end(1)
    fm_text = text[fm_start:fm_end]
    rel_match = re.search(r"^related:\s*(\[.*?\]|(?:\n(?:[ \t]+.*\n?)*))", fm_text, re.MULTILINE)
    if not rel_match:
        return None
    return fm_start + rel_match.start(1), fm_start + rel_match.end(1)


def normalize_related_field(
    text: str, index: dict[str, list[str]], unresolved: list[str], filepath: str
) -> tuple[str, int]:
    span = extract_related_block(text)
    if span is None:
        return text, 0
    start, end = span
    block = text[start:end]

    fixed_count = 0

    def _sub(m: re.Match) -> str:
        nonlocal fixed_count
        name = m.group(1)
        # Already-normalized codex refs inside related: are handled by the codex pass;
        # a bare .md with no preceding '/' here is a plan/issue doc reference.
        preceding = block[: m.start()]
        if preceding.endswith("/"):
            return name  # already has a path prefix immediately before it — leave alone
        matches = index.get(name, [])
        if len(matches) == 1:
            fixed_count += 1
            return f"/{matches[0]}"
        if len(matches) == 0:
            unresolved.append(f"{filepath}: '{name}' not found anywhere under plans/ or codex/")
        else:
            unresolved.append(f"{filepath}: '{name}' AMBIGUOUS — matches {matches}")
        return name

    new_block = BARE_MD_RE.sub(_sub, block)
    if new_block == block:
        return text, 0
    return text[:start] + new_block + text[end:], fixed_count


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    index = build_filename_index()
    unresolved: list[str] = []
    files_changed = 0
    total_codex_fixed = 0
    total_related_fixed = 0

    seen: set[Path] = set()
    for pattern in TARGET_GLOBS:
        for p in PM_DIR.glob(pattern):
            if p in seen or not p.is_file():
                continue
            seen.add(p)
            relpath = p.relative_to(PM_DIR).as_posix()
            if relpath in SKIP_PRE_EXISTING_FRONTMATTER_DEFECTS:
                continue
            original = p.read_text(encoding="utf-8")
            text, codex_fixed = normalize_codex_refs(original, relpath.startswith("codex/"))
            text, related_fixed = normalize_related_field(text, index, unresolved, relpath)
            if text != original:
                files_changed += 1
                total_codex_fixed += codex_fixed
                total_related_fixed += related_fixed
                if not dry_run:
                    p.write_text(text, encoding="utf-8")

    print(f"Files changed: {files_changed}")
    print(f"Codex refs normalized (occurrences, incl. no-op already-correct ones re-matched): {total_codex_fixed}")
    print(f"related: bare filenames resolved to full path: {total_related_fixed}")
    print(f"Unresolved related: entries needing manual attention: {len(unresolved)}")
    for line in unresolved:
        print(f"  UNRESOLVED  {line}")
    if dry_run:
        print("\n(--dry-run: no files were written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
