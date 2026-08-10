#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Doc retrieval-layer parity QG check (L0 index <-> schema; cross-agent doctrine).

Guards the two things nothing else in the fleet currently checks about the grep-native
L0->L1->L2->L3 doc-retrieval design (codex/11-project-management/doc-frontmatter-schema.md):

1. Schema<->generator parity — `scripts/docs/gen_doc_index.py` hand-maintains a
   `_PER_TYPE_FACETS` dict mapping each `doc_type` to the extra facet keys worth surfacing
   on its L0 index line. `scripts/docs/docspec.py` is the schema's machine SSOT
   (`DOC_TYPES`, `PER_TYPE`). Nothing enforced that the two stay in lockstep — a new
   `doc_type` added to the schema, or a per-type field rename, would silently leave the L0
   generator producing a stale/incomplete index line for that type, with no failure anywhere.
   This check asserts every non-exempt `doc_type` has a `_PER_TYPE_FACETS` entry, every
   entry's facet names are real fields for that type (per `docspec.PER_TYPE` /
   `docspec.UNIVERSAL_CORE`), and no entry references a `doc_type` outside the schema's enum.

2. Cross-agent doctrine parity — the "grep DOC_INDEX.generated.md first" retrieval doctrine
   must be discoverable by every agent surface it is meant to govern. Real regression found
   2026-07-23: the doctrine lived ONLY in `cursor-configs/CLAUDE.md` (Claude Code's own file)
   despite `AGENTS.md` being documented as "Shared instructions for all agents (Claude Code,
   Codex, Cursor)" — so Codex/Cursor agents never received it. This check asserts both
   `cursor-configs/CLAUDE.md` and `AGENTS.md` reference `DOC_INDEX`.

Exit-code semantics:
  0 - clean (no violations)
  1 - violations found (each printed with its remedy)
  2 - argument / IO error (missing workspace root, unloadable module)

SSOT: codex/11-project-management/doc-frontmatter-schema.md (schema) +
      plans/active/docs_retrieval_layer_reconcile_2026_07_23.md (this check's origin).
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import types
from pathlib import Path


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


# doc_type values that deliberately have no L0-facet entry (cursor-rule is Cursor-governed;
# its `description` field serves as `summary` per doc-frontmatter-schema.md §9/§3 note, and it
# carries no per-type facets worth surfacing).
EXEMPT_DOC_TYPES = frozenset({"cursor-rule"})

# The two surfaces every agent reads at session start; both must carry the retrieval doctrine.
DOCTRINE_TOKEN = "DOC_INDEX"
DOCTRINE_SURFACES: tuple[str, ...] = ("cursor-configs/CLAUDE.md", "AGENTS.md")


def _load_module(path: Path, name: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def check_schema_generator_parity(pm_root: Path) -> list[str]:
    """Return violation strings for gen_doc_index<->docspec drift. Empty = clean."""
    docspec = _load_module(pm_root / "scripts" / "docs" / "docspec.py", "docspec")
    gen_doc_index = _load_module(pm_root / "scripts" / "docs" / "gen_doc_index.py", "gen_doc_index")

    doc_types: frozenset[str] = docspec.DOC_TYPES
    per_type: dict[str, list] = docspec.PER_TYPE
    universal_names = {fs.name for fs in docspec.UNIVERSAL_CORE}
    facets: dict[str, list[str]] = gen_doc_index._PER_TYPE_FACETS

    violations: list[str] = []

    for dt in sorted(doc_types - EXEMPT_DOC_TYPES):
        if dt not in facets:
            violations.append(
                f"gen_doc_index._PER_TYPE_FACETS is missing an entry for doc_type '{dt}' "
                f"(present in docspec.DOC_TYPES, not in EXEMPT_DOC_TYPES). "
                f"Remedy: add '{dt}': [<facet names from docspec.PER_TYPE['{dt}']>] to _PER_TYPE_FACETS."
            )

    for dt, dt_facets in facets.items():
        if dt not in doc_types:
            violations.append(
                f"gen_doc_index._PER_TYPE_FACETS has a stale entry for '{dt}' — not a valid docspec.DOC_TYPES "
                f"value. Remedy: remove it (the doc_type was likely renamed/retired in docspec.py)."
            )
            continue
        valid_names = universal_names | {fs.name for fs in per_type.get(dt, [])}
        for facet in dt_facets:
            if facet not in valid_names:
                violations.append(
                    f"gen_doc_index._PER_TYPE_FACETS['{dt}'] references '{facet}', which is not a real field for "
                    f"doc_type '{dt}' in docspec.PER_TYPE/UNIVERSAL_CORE. Remedy: fix the facet name (likely a stale "
                    f"reference to a field renamed in docspec.py)."
                )

    return violations


def check_doctrine_cross_surface_parity(pm_root: Path) -> list[str]:
    """Return violation strings if the DOC_INDEX retrieval doctrine is missing from a surface."""
    violations: list[str] = []
    for rel in DOCTRINE_SURFACES:
        path = pm_root / rel
        if not path.is_file():
            violations.append(f"doctrine surface missing entirely: {rel} does not exist under {pm_root}.")
            continue
        text = path.read_text(encoding="utf-8")
        if DOCTRINE_TOKEN not in text:
            violations.append(
                f"{rel} has zero mentions of '{DOCTRINE_TOKEN}' — agents reading this file will never learn to "
                f"grep the L0 index first. Remedy: add a 'Doc retrieval' section pointing at "
                f"unified-trading-pm/DOC_INDEX.generated.md (mirror the section in cursor-configs/CLAUDE.md)."
            )
    return violations


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(__file__).resolve().parents[2].parent,
        help="Workspace root containing unified-trading-pm/ (default: derived from this file's location)",
    )
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    workspace_root: Path = ns.workspace_root.resolve()
    pm_root = _pm_root_or_legacy(workspace_root)
    if not pm_root.is_dir():
        # Also allow running with --workspace-root pointed AT the PM repo directly (as this
        # script's own directory implies when parents[2] already IS the PM root).
        pm_root = workspace_root if (workspace_root / "scripts" / "docs" / "docspec.py").is_file() else pm_root
    if not pm_root.is_dir():
        print(f"ERROR: cannot locate unified-trading-pm under {workspace_root}", file=sys.stderr)
        return 2

    try:
        violations = check_schema_generator_parity(pm_root) + check_doctrine_cross_surface_parity(pm_root)
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not violations:
        print("Doc retrieval-layer parity check passed — schema<->generator + cross-agent doctrine both clean.")
        return 0

    print(f"❌ {len(violations)} doc retrieval-layer parity violation(s):\n")
    for v in violations:
        print(f"  - {v}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
