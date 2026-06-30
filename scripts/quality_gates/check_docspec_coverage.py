#!/usr/bin/env python3
"""check_docspec_coverage — the anti-rot frontmatter check (W5).

Runs the docspec validator (scripts/docs/docspec.py — the machine mirror of
codex/11-project-management/doc-frontmatter-schema.md) over every PM-resident doc tree and reports
HARD violations. This is what keeps frontmatter from rotting: frontmatter is the grep-native L1
index agents use to find docs + code<->codex drift, so a doc that loses its doc_type / required
fields / valid enum value silently drops out of every search. SOFT (empty summary/tags/
authoritative_for — the deferred content pass) is not reported here.

WIRING: PM quality-gates runs this WARN-ONLY (non-blocking) — HARD rot is surfaced but does NOT
fail QG (operator decision 2026-06-30: clean up rot periodically, don't block every ship on it).
The script itself still exits 1 on HARD so it stays usable as a standalone strict check / for a
future flip to blocking.

Scope = PM-resident trees only (this runs in PM CI, which checks out PM):
  plans/active, plans/active/issues, plans/epics, plans/audit/{results,instructions}, codex, **/*.mdc.
agent-orchestrator/agents (agent-role) lives in a separate repo -> covered by that repo's gate.

Exit 0 = no HARD violations; exit 1 = at least one (offending files + reasons printed).
Remedy for a missing/derivable field: `python3 scripts/docs/seed_frontmatter.py --apply <path>`.

# Epic: agent_operating_framework_master
# Lifecycle: permanent
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PM_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PM_ROOT / "scripts" / "docs"))

import docspec as ds  # type: ignore[import-not-found]

# PM-resident doc trees (glob patterns relative to the PM root). agent-orchestrator/agents is a
# SEPARATE repo and is intentionally excluded — its agent-role docs are enforced by that repo's gate.
DOC_TREES: tuple[str, ...] = (
    "plans/active/*.md",
    "plans/active/issues/*.md",
    "plans/epics/*.md",
    "plans/audit/results/**/*.md",
    "plans/audit/instructions/**/*.md",
    "codex/**/*.md",
    "**/*.mdc",
)


def _iter_docs() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for pat in DOC_TREES:
        for p in _PM_ROOT.glob(pat):
            if p.is_file() and p not in seen:
                seen.add(p)
                out.append(p)
    return sorted(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Anti-rot frontmatter coverage gate (docspec HARD==0).")
    ap.add_argument("--quiet", action="store_true", help="suppress the per-tree OK summary")
    ap.add_argument("--soft", action="store_true", help="also list SOFT (needs-content) findings")
    args = ap.parse_args(argv)

    reg = ds.load_registries(_PM_ROOT)
    hard_files: list[tuple[Path, list[tuple[str, str]]]] = []
    checked = soft_total = 0

    for path in _iter_docs():
        if ds.is_exempt(str(path)):
            continue
        dt = ds.doc_type_for_path(str(path))
        if dt is None:  # outside the schema's scope (e.g. archive/ai) — not this gate's business
            continue
        checked += 1
        try:
            fm, _ = ds.parse_frontmatter(path.read_text(encoding="utf-8"))
        except Exception as exc:  # malformed YAML frontmatter == unparseable == HARD
            hard_files.append((path, [("frontmatter", f"unparseable YAML: {exc}")]))
            continue
        if fm is None:
            hard_files.append((path, [("frontmatter", "no --- frontmatter block")]))
            continue
        violations = ds.validate_frontmatter(dt, fm, reg)
        hard = [(v.field, v.message) for v in violations if v.severity == ds.Sev.HARD]
        soft_total += sum(1 for v in violations if v.severity == ds.Sev.SOFT)
        if hard:
            hard_files.append((path, hard))

    rel = lambda p: p.relative_to(_PM_ROOT)  # noqa: E731
    if hard_files:
        print(f"❌ docspec coverage: {len(hard_files)} doc(s) with HARD frontmatter violations:", file=sys.stderr)
        for path, hard in hard_files:
            print(f"  {rel(path)}:", file=sys.stderr)
            for field, msg in hard:
                print(f"    - {field}: {msg}", file=sys.stderr)
        print(
            "\n  Remedy: python3 scripts/docs/seed_frontmatter.py --apply <path>  (fills derivable fields),\n"
            "  then set any enum/parent_epic value by hand.\n"
            "  Schema: codex/11-project-management/doc-frontmatter-schema.md",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print(f"✅ docspec coverage: {checked} docs HARD-green across {len(DOC_TREES)} PM doc trees "
              f"({soft_total} SOFT/needs-content — deferred, not enforced)")
        if args.soft and soft_total:
            print("   (run with the validator's --soft to list the deferred content fields)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
