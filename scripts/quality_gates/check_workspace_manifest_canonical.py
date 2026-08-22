#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""check_workspace_manifest_canonical — reject a non-canonical workspace-manifest.json.

CANONICAL FORM (the ONE serialization every writer must emit):

    json.dumps(obj, indent=2, ensure_ascii=False) + "\\n"

Why this exists (local<->CI parity, cicd_mvp_ldr_to_main_pipeline_2026_06_30 Phase-2):
the manifest is written by ~17 code paths (update-repo-version / staging-to-main /
sit-unlock / merge-driver / consolidator / monitors), all of which emit the canonical
form via `json.dump(..., indent=2, ensure_ascii=False)` + an explicit trailing newline.

PRETTIER IS **NOT** ONE OF THEM — this line used to say "plus prettier on local commits",
and that was FALSE. Canonical always explodes every array element onto its own line;
prettier (printWidth=120) COLLAPSES any array that fits. They can never agree. Because
the `prettier-autostage` hook matched `json` and the file was not in `.prettierignore`,
every local commit that STAGED the manifest silently reformatted + RE-STAGED it into the
non-canonical form — AFTER the author's quality-gates.sh run had already gone green, so
no local verification could catch it. Measured 2026-07-17: 73c4449ae intended a one-line
edit and landed 95 insertions / 431 deletions, reding PM's LDR (runs 29576851453 /
29576964765 / 29577081402) until a monitor's canonical write incidentally healed it.
FIXED by adding `workspace-manifest.json` to `.prettierignore` — do not remove that rule
believing prettier is canonical here; it is not (verify: prettier --ignore-path /dev/null
--list-different workspace-manifest.json lists it).
When ONE writer disagrees on cosmetics (ascii-escaping, trailing newline), every
alternation between writers re-emits the SAME content as DIFFERENT bytes -> phantom
diffs, spurious quickmerge conflicts, and an hourly cosmetic-churn commit loop (the
ci_status_consolidator oscillation, root-caused 2026-07-02: 57 reformat-only commits).
Byte-stable serialization is what keeps "local tree clean" == "CI tree clean".

This guard makes any future non-canonical writer fail QG immediately instead of
silently churning. Key ORDER is preserved-as-loaded (writers round-trip via
json.load, so insertion order is stable); this check therefore only normalizes
FORMATTING, never reorders content.

Exit 0 = canonical. Exit 1 = drift (prints a fix hint). Exit 2 = unreadable/invalid.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def canonical_form(raw: str) -> str:
    """The canonical serialization of the manifest's parsed content."""
    return json.dumps(json.loads(raw), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="reject a non-canonical workspace-manifest.json")
    default_path = Path(__file__).resolve().parents[2] / "workspace-manifest.json"
    parser.add_argument("--manifest", type=Path, default=default_path)
    parser.add_argument("--fix", action="store_true", help="rewrite the manifest in canonical form")
    args = parser.parse_args(argv)

    manifest: Path = args.manifest
    try:
        raw = manifest.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"❌ manifest-canonical: cannot read {manifest}: {exc}", file=sys.stderr)
        return 2
    try:
        canonical = canonical_form(raw)
    except json.JSONDecodeError as exc:
        print(f"❌ manifest-canonical: {manifest} is not valid JSON: {exc}", file=sys.stderr)
        return 2

    if raw == canonical:
        print(f"✅ manifest-canonical: {manifest.name} is byte-canonical")
        return 0

    if args.fix:
        manifest.write_text(canonical, encoding="utf-8")
        print(f"🔧 manifest-canonical: rewrote {manifest.name} in canonical form")
        return 0

    # Cheap drift diagnosis for the two known cosmetic classes.
    hints: list[str] = []
    if "\\u" in raw and "\\u" not in canonical:
        hints.append("ascii-escaped unicode (writer missing ensure_ascii=False)")
    if not raw.endswith("\n"):
        hints.append("missing trailing newline")
    if not hints:
        hints.append("formatting drift (indent/spacing)")
    print(
        f"❌ manifest-canonical: {manifest.name} is NOT canonical — {'; '.join(hints)}.\n"
        f"   Canonical form: json.dumps(obj, indent=2, ensure_ascii=False) + '\\n'.\n"
        f"   Fix the WRITER that produced this (see the writer table in this checker's\n"
        f"   docstring provenance), then: python3 {Path(__file__).name} --fix",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
