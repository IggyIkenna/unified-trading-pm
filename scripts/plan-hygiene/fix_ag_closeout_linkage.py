#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Auto-remediate check_ag_closeout_linkage.py orphans: for every single-AG plan/issue
doc with no findable path to its asset_group's consolidated-closeout family, append a
`related:` entry pointing at a representative doc in that family (preferring the base
`<prefix>_consolidated_closeout_*.md` doc when the family has one), so the checker's
graph-reachability signal picks it up.

Reuses check_ag_closeout_linkage.py's own orphan-detection (target_files/closeout_family_for/
build_related_graph/bfs_reaches/mentions_stem) rather than re-deriving it, so this stays in
lockstep with the checker's own notion of "orphan" — never a second, driftable definition.

Handles the corpus's four observed `related:` frontmatter shapes (confirmed by direct survey,
2026-08-08): `related: [a, b]` single-line (incl. empty `related: []`), `related:\\n  [a, b]`
(bracket content on the line after the key), `related:\\n  [\\n    a,\\n  ]` multi-line bracket
(one item per line), and `related:\\n  - a\\n  - b` dash-list. A file whose `related:` block
doesn't match any of these (or has no `related:` field at all) is reported as SKIPPED, never
silently mis-edited — this is a text-surgery tool, not a YAML round-trip, specifically to avoid
reformatting unrelated frontmatter (block scalars, comments, key order) as a side effect.

Trap hit building this (2026-08-08): inserting a NEW `resolved_by:`/`effort:`-style key with a
naive `sed -i '/^somekey:/a newkey: val'` silently DUPLICATES the key if the target file already
has that key elsewhere in its frontmatter (YAML doesn't error on a dup key here, but downstream
parsers may only see the last one) — this script's related: insertion doesn't have that failure
mode (it only ever appends INTO the existing `related:` value), but any future extension of this
pattern to a different field must re-read the file immediately before editing and grep for the
target key count before AND after, not assume single-insertion-point sed is safe.

Usage:
  python3 scripts/plan-hygiene/fix_ag_closeout_linkage.py [--dry-run]
Exit 0 always (a remediation helper, not a gate) — re-run check_ag_closeout_linkage.py after to
verify the ratchet is back at/under baseline.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_ag_closeout_linkage as gate  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs"))
import docspec  # noqa: E402

PM_DIR = gate.PM_DIR


def _find_orphans() -> list[tuple[Path, str, Path]]:
    """Returns (orphan_path, asset_group, chosen_target_path) tuples — mirrors
    check_ag_closeout_linkage.main()'s violation-detection loop exactly, but returns the
    resolved closeout-family TARGET instead of a formatted violation string."""
    files = gate.target_files()
    all_docs: dict[Path, dict] = {}
    all_bodies: dict[Path, str] = {}
    for p in files:
        text = p.read_text(encoding="utf-8")
        fm, body = docspec.parse_frontmatter(text)
        if fm is None:
            continue
        all_docs[p] = fm
        all_bodies[p] = body

    search_paths = gate.closeout_search_paths()
    closeout_family = {ag: gate.closeout_family_for(ag, search_paths) for ag in gate.COVERED_ASSET_GROUPS}
    closeout_targets = frozenset(p for fam in closeout_family.values() for p in fam)
    graph = gate.build_related_graph(all_docs, extra_nodes=closeout_targets)

    closeout_body_blob: dict[str, str] = {}
    for ag, fam in closeout_family.items():
        bodies = [all_bodies.get(p) or "" for p in fam]
        closeout_body_blob[ag] = "\n".join(bodies)

    orphans: list[tuple[Path, str, Path]] = []
    for path, fm in all_docs.items():
        if fm.get("status") in gate.EXCLUDED_STATUS:
            continue
        ag_values = [v for v in docspec._as_list(fm.get("asset_group")) if isinstance(v, str)]
        if len(ag_values) != 1 or ag_values[0] not in gate.COVERED_ASSET_GROUPS:
            continue
        ag = ag_values[0]
        family = closeout_family[ag]
        if not family or path in family:
            continue
        if gate.bfs_reaches(graph, path, family, gate.MAX_HOPS):
            continue
        if gate.mentions_stem(closeout_body_blob[ag], path.stem):
            continue

        # Prefer the base "<prefix>_consolidated_closeout_*" doc (the canonical hub) when
        # present; else any family member — either satisfies the checker's graph-reachability
        # signal, which only needs ONE edge into the family set.
        prefix = gate._CLOSEOUT_FILENAME_PREFIX.get(ag, ag)
        base_candidates = sorted(p for p in family if p.stem.startswith(f"{prefix}_consolidated_closeout"))
        target = base_candidates[0] if base_candidates else sorted(family)[0]
        orphans.append((path, ag, target))

    return orphans


def _insert_related_entry(lines: list[str], target_ref: str) -> bool:
    """In-place text-surgery insert of `target_ref` into the file's `related:` block.
    Returns True if handled, False if the format wasn't recognized (caller must not write)."""
    rel_idx = next((i for i, ln in enumerate(lines) if ln.startswith("related:")), None)
    if rel_idx is None:
        return False

    rest = lines[rel_idx][len("related:") :].strip()

    if rest.startswith("[") and rest.endswith("]"):
        inner = rest[1:-1].strip()
        new_rest = f"[{inner}, {target_ref}]" if inner else f"[{target_ref}]"
        lines[rel_idx] = f"related: {new_rest}"
        return True

    if rest != "":
        return False  # unrecognized single-line non-bracket form — don't guess

    nxt = lines[rel_idx + 1] if rel_idx + 1 < len(lines) else ""
    nxt_stripped = nxt.strip()

    if nxt_stripped.startswith("[") and nxt_stripped.endswith("]") and nxt_stripped != "[":
        inner = nxt_stripped[1:-1].strip()
        indent = nxt[: len(nxt) - len(nxt.lstrip())]
        new_inner = f"{inner}, {target_ref}" if inner else target_ref
        lines[rel_idx + 1] = f"{indent}[{new_inner}]"
        return True

    if nxt_stripped == "[":
        item_indent = "    "
        for j in range(rel_idx + 2, min(rel_idx + 40, len(lines))):
            s = lines[j].strip()
            if s == "]":
                lines.insert(j, f"{item_indent}{target_ref},")
                return True
            if s and s != "[":
                item_indent = lines[j][: len(lines[j]) - len(lines[j].lstrip())]
        return False

    if nxt_stripped.startswith("- "):
        dash_indent = nxt[: len(nxt) - len(nxt.lstrip())]
        last_dash_idx = rel_idx + 1
        for j in range(rel_idx + 1, min(rel_idx + 40, len(lines))):
            if lines[j].strip().startswith("- "):
                last_dash_idx = j
            else:
                break
        lines.insert(last_dash_idx + 1, f"{dash_indent}- {target_ref}")
        return True

    return False


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    orphans = _find_orphans()
    if not orphans:
        print("fix_ag_closeout_linkage: no orphans found — nothing to do.")
        return 0

    fixed, skipped = [], []
    for path, ag, target in orphans:
        rel = path.relative_to(PM_DIR).as_posix()
        target_ref = "/" + target.relative_to(PM_DIR).as_posix()

        lines = path.read_text(encoding="utf-8").split("\n")
        block = "\n".join(lines[:20])
        if target_ref in block:
            skipped.append((rel, "ALREADY_LINKED"))
            continue

        if not _insert_related_entry(lines, target_ref):
            skipped.append((rel, "UNHANDLED_RELATED_FORMAT"))
            continue

        fixed.append((rel, ag, target_ref))
        if not dry_run:
            path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Fixed: {len(fixed)}")
    for rel, ag, target_ref in fixed:
        print(f"  OK [{ag}] {rel} -> {target_ref}")
    print(f"Skipped: {len(skipped)}")
    for rel, reason in skipped:
        print(f"  SKIP [{reason}] {rel}")

    if dry_run:
        print("\n(--dry-run: no files written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
