#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Append a dated na-eligibility-audit verdict marker to a doc's Progress Log.

Why this exists: every /na-eligibility-audit run (scheduled every 2h per tranche,
cursor-configs/skills/na-eligibility-audit/SKILL.md) has to write one of these markers
per verdicted doc so the NEXT run's Phase-0 incremental-diff can skip it. Getting the
marker format wrong (missing/mis-shaped [body-hash:...] tag, wrong insertion point) means
every future run re-reads the doc from scratch forever -- the exact false-positive class
generate_na_doc_tranche_inventory.py's own module docstring warns about. This script
computes the hash via the SAME function the inventory script uses (imported, not
reimplemented) and inserts at the same place a hand-written marker would go, so a session
doesn't have to re-derive the format by reading generate_na_doc_tranche_inventory.py's
regex from scratch every time (as the 2026-08-17 ao-tranche run had to).

Traps hit writing this the first time:
- The hash MUST be computed on the doc's CURRENT (post-edit) content, not a stale
  Phase-0 snapshot -- body_content_hash() already excludes marker lines from its input,
  so it's safe to compute fresh right before inserting, and unsafe to reuse an
  earlier-computed value if you made any OTHER content edit to the doc in between.
- The marker format is `- **na-eligibility-audit YYYY-MM-DD** [body-hash:XXXXXXXX]: <text>`
  -- the hash tag goes between the closing `**` and the colon, not after the colon.
- Import body_content_hash() from the real script rather than reimplementing the
  frontmatter-strip + marker-strip regex -- reimplementing risks silently drifting from
  whatever the inventory script's own stripping logic currently does (it has already
  been patched twice for false-positive classes: fenced-code-block checkboxes and
  context-scout marker continuation lines).

Usage:
    python3 append_na_eligibility_audit_marker.py <YYYY-MM-DD> <tranche> <manifest.json>

Where manifest.json is {"relative/path/to/doc.md": "verdict text (no date/hash prefix)"}
paths relative to the PM repo root, and <tranche> is the tranche this run audited (e.g.
"ao", "cefi", "all") -- stamped into every marker so a later run can tell which tranche
verdicted a doc, matching the skill's own dated-marker convention. Prints a JSON result
list to stdout; exits 1 if any named path doesn't exist.
"""
import json
import sys
from pathlib import Path

PM_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_na_doc_tranche_inventory import body_content_hash


def append_marker(pm_root: Path, rel_path: str, marker_text: str, today: str, tranche: str) -> dict:
    doc_path = pm_root / rel_path
    if not doc_path.exists():
        return {"path": rel_path, "status": "MISSING"}
    text = doc_path.read_text()
    h = body_content_hash(text)
    marker_line = f"- **na-eligibility-audit {today} ({tranche} tranche)** [body-hash:{h}]: {marker_text}"

    lines = text.splitlines(keepends=True)
    pl_idx = next((i for i, line in enumerate(lines) if line.strip() == "## Progress Log"), None)

    if pl_idx is None:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n## Progress Log\n\n" + marker_line + "\n"
    else:
        end_idx = next((j for j in range(pl_idx + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
        insert_at = end_idx
        while insert_at > pl_idx + 1 and lines[insert_at - 1].strip() == "":
            insert_at -= 1
        lines[insert_at:insert_at] = [marker_line + "\n"]
        text = "".join(lines)

    doc_path.write_text(text)
    return {"path": rel_path, "status": "OK", "hash": h}


def main() -> int:
    today = sys.argv[1]
    tranche = sys.argv[2]
    manifest = json.loads(Path(sys.argv[3]).read_text())
    results = [
        append_marker(PM_ROOT, rel_path, marker_text, today, tranche) for rel_path, marker_text in manifest.items()
    ]
    print(json.dumps(results, indent=2))
    missing = [r for r in results if r["status"] != "OK"]
    if missing:
        print(f"\n{len(missing)} MISSING/FAILED entries", file=sys.stderr)
        return 1
    print(f"\n{len(results)} markers written OK", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
