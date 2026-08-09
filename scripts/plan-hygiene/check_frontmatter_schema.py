#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""THE comprehensive BLOCKING frontmatter gate — docspec-backed (2026-07-04).

End-state of the two-checks lifecycle (codex/11-project-management/doc-frontmatter-schema.md):
this gate calls `docspec.validate_frontmatter()` (the schema's machine SSOT — never a second
hand-rolled validator) over the LIVE doc trees and fails on ANY violation, HARD (structure /
enum / registry) or SOFT (needs-content), so the 2026-07-04 zero-violations corpus cannot rot.

Corpus = the live trees only. `plans/archive/**` is deliberately OUT of scope (operator
decision 2026-07-04: archives are closed records, backfilled opportunistically — do not gate
shipping on them). The warn-only `check_docspec_coverage.py` is retired; this is the sole
frontmatter gate.

Supplementary check preserved from the retired narrow gate (not in the docspec field specs):
an audit-result must carry a non-empty `instructions_ref`.

Also runs docspec.validate_doc_references() (existence-only check for frontmatter fields that
reference OTHER docs by relative path — `related`, `codex_ssots`, `supersedes`, etc.), ratcheted
against doc_reference_baseline.yaml so PRE-EXISTING dead links (91 seeded 2026-07-22) don't fail
every run — only a reference NOT in the baseline (genuinely NEW breakage) fails the gate.

Usage: check_frontmatter_schema.py [file ...]   # no args -> full live corpus
  --quiet                    suppress the success line
  --update-doc-ref-baseline  regenerate doc_reference_baseline.yaml from the CURRENT full-corpus
                              scan (run after a cleanup pass; NEVER to launder a check you just
                              introduced — see the baseline file's own header)
Exit 0 = zero violations. Exit 1 = violations (each printed with its remedy).
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]
DOC_REF_BASELINE = Path(__file__).resolve().parent / "doc_reference_baseline.yaml"

# Live doc trees (glob patterns relative to the PM root). plans/archive is EXCLUDED by design.
DOC_TREES: tuple[str, ...] = (
    "plans/active/*.md",
    "plans/active/issues/*.md",
    "plans/epics/*.md",
    "plans/audit/results/**/*.md",
    "plans/audit/instructions/**/*.md",
    "codex/**/*.md",
    "agents/*.md",
    "**/*.mdc",
)
_ARCHIVE_PREFIX = "plans/archive/"
# Per-agent worktree scratch space (see the Agent tool's `isolation: "worktree"` mode) — never
# real corpus content. The unscoped "**/*.mdc" DOC_TREES pattern below would otherwise sweep up
# a live agent's `.claude/worktrees/<id>/.cursor/rules/**/*.mdc` copy and false-flag it against
# the real `.cursor/rules/...` original's already-seeded baseline entry.
_CLAUDE_WORKTREE_PREFIX = ".claude/"


def _load_docspec():
    spec = importlib.util.spec_from_file_location("docspec", PM / "scripts" / "docs" / "docspec.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/docs/docspec.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["docspec"] = mod
    spec.loader.exec_module(mod)
    return mod


def _iter_docs() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for pat in DOC_TREES:
        for p in PM.glob(pat):
            rel = p.relative_to(PM).as_posix()
            if (
                p.is_file()
                and p not in seen
                and not rel.startswith(_ARCHIVE_PREFIX)
                and not rel.startswith(_CLAUDE_WORKTREE_PREFIX)
            ):
                seen.add(p)
                out.append(p)
    return sorted(out)


def _load_doc_ref_baseline() -> set[str]:
    if not DOC_REF_BASELINE.is_file():
        return set()
    data = yaml.safe_load(DOC_REF_BASELINE.read_text()) or {}
    return set(data.get("known_broken") or [])


def _doc_ref_key(rel_path: str, field: str, message: str) -> str:
    m = re.search(r"referenced doc '([^']+)' does not exist", message)
    entry = m.group(1) if m else message
    return f"{rel_path}::{field}::{entry}"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    quiet = "--quiet" in args
    update_baseline = "--update-doc-ref-baseline" in args
    files = [Path(a) for a in args if not a.startswith("--")]

    ds = _load_docspec()
    reg = ds.load_registries(PM)
    # --update-doc-ref-baseline always scans the FULL corpus — the baseline represents total
    # corpus state, not whatever subset happened to be passed as file args.
    paths = _iter_docs() if update_baseline else (files if files else _iter_docs())
    baseline = _load_doc_ref_baseline()

    checked = 0
    bad: list[tuple[Path, list[str]]] = []
    new_doc_ref_keys: set[str] = set()
    for path in paths:
        if ds.is_exempt(str(path)):
            continue
        dt = ds.doc_type_for_path(str(path))
        if dt is None:  # outside the schema's scope
            continue
        checked += 1
        problems: list[str] = []
        try:
            fm, _ = ds.parse_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
            bad.append((path, [f"frontmatter is not valid YAML: {exc}"]))
            continue
        if fm is None:
            bad.append((path, ["no --- frontmatter block"]))
            continue
        problems.extend(f"{v.field}: {v.message}" for v in ds.validate_frontmatter(dt, fm, reg))
        # exact legacy contract: keyed on the legacy `type:` field, not the path-derived doc_type
        # (path-keying would newly fail ~15 pre-existing verdict-pack docs — widen only via worklist)
        if fm.get("type") == "audit-result" and not fm.get("instructions_ref"):
            problems.append("instructions_ref: required non-empty on audit-results")

        # Doc-reference existence — ratcheted against the baseline (see doc_reference_baseline.yaml
        # header): a key already in the baseline is pre-existing debt, tolerated; anything else is a
        # NEW broken reference and fails the gate same as any other HARD violation.
        rel = path.resolve().relative_to(PM).as_posix()
        for v in ds.validate_doc_references(path, fm, dt):
            key = _doc_ref_key(rel, v.field, v.message)
            if update_baseline:
                new_doc_ref_keys.add(key)
            elif key not in baseline:
                problems.append(f"{v.field}: {v.message} (NEW — not in doc_reference_baseline.yaml)")

        if problems:
            bad.append((path, problems))

    if update_baseline:
        DOC_REF_BASELINE.write_text(
            DOC_REF_BASELINE.read_text().split("known_broken:")[0]
            + "known_broken:\n"
            + "".join(f"  - {yaml.safe_dump(k, default_style=chr(34)).strip()}\n" for k in sorted(new_doc_ref_keys))
        )
        print(f"doc_reference_baseline.yaml regenerated: {len(new_doc_ref_keys)} known_broken entries.")
        return 0

    if bad:
        print(f"❌ check_frontmatter_schema: {len(bad)} doc(s) with frontmatter violations:", file=sys.stderr)
        for path, problems in bad:
            rel = path.relative_to(PM) if path.is_absolute() else path
            print(f"  {rel}:", file=sys.stderr)
            for pr in problems:
                print(f"    - {pr}", file=sys.stderr)
        print(
            "  Remedy: python3 scripts/docs/seed_frontmatter.py --apply <path> (derivable fields), then fill"
            " content fields by hand. Schema: codex/11-project-management/doc-frontmatter-schema.md",
            file=sys.stderr,
        )
        return 1
    if not quiet:
        print(f"✅ check_frontmatter_schema: {checked} docs, zero frontmatter violations (docspec HARD+SOFT)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
