#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Append a na-eligibility-audit verdict marker to a PM doc, with a correct [body-hash:...] tag.

Why this exists: hand-writing a `- **na-eligibility-audit <date>** [body-hash:...]: ...` marker risks
getting the hash wrong, since it must exactly match what generate_na_doc_tranche_inventory.py's
body_content_hash() computes (frontmatter-stripped, marker-family-stripped SHA-256, first 16 hex
chars). A wrong hash doesn't error -- it silently breaks Phase 0's incremental-skip detection on
every future /na-eligibility-audit run: the doc looks "changed" forever even though it isn't,
defeating the whole point of the incremental design (re-reading the full ~390-doc corpus every run
instead of only what actually changed). This tool reuses body_content_hash()/the marker-stripping
logic from the real inventory script (imported, not reimplemented) so the hash it writes is
guaranteed to match what that script computes on its next run -- eliminating that whole bug class
rather than hoping a hand-copied regex stays in sync.

Trap already hit and designed around: the hash MUST be computed on the doc's content BEFORE this
tool's own marker line is inserted, not after -- computing pre-insert avoids ever depending on the
strip regex correctly recognizing the just-added line in the same pass it's adding it.

Usage:
  python3 na_marker_helper.py hash <pm_relative_path>
  python3 na_marker_helper.py append <pm_relative_path> <date YYYY-MM-DD> <marker_suffix_text>
  python3 na_marker_helper.py batch <path to JSON: [{"path":...,"date":...,"suffix":...}, ...]>

"append"/"batch" insert:  - **na-eligibility-audit <date>** [body-hash:<hash>]: <marker_suffix_text>
as the last bullet of the doc's "## Progress Log" section (creating the section if absent).
"""

import importlib.util
import json
import sys
from pathlib import Path

PM = Path("/home/ubuntu/unified-trading-system-repos/unified-trading-pm")
INVENTORY_SCRIPT = PM / "scripts" / "plan-hygiene" / "generate_na_doc_tranche_inventory.py"


def _load_inventory_module():
    spec = importlib.util.spec_from_file_location("na_doc_inventory", INVENTORY_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {INVENTORY_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_progress_log_insert_point(text: str) -> tuple[int, bool]:
    """Return (byte_offset_to_insert_at, section_exists).

    If '## Progress Log' exists: insert just before the next '^## ' heading after it, or at
    end-of-file if none. If it doesn't exist: insert at end-of-file (caller adds the heading).
    """
    lines = text.splitlines(keepends=True)
    pl_idx = None
    for i, line in enumerate(lines):
        if line.rstrip("\n") == "## Progress Log":
            pl_idx = i
    if pl_idx is None:
        return len(text), False
    offset = sum(len(ln) for ln in lines[: pl_idx + 1])
    for line in lines[pl_idx + 1 :]:
        if line.startswith("## "):
            break
        offset += len(line)
    return offset, True


def append_one(mod, rel_path: str, date: str, suffix: str) -> str:
    full_path = PM / rel_path
    text = full_path.read_text(encoding="utf-8")
    h = mod.body_content_hash(text)
    marker_line = f"- **na-eligibility-audit {date}** [body-hash:{h}]: {suffix}\n"
    offset, exists = find_progress_log_insert_point(text)
    if exists:
        new_text = text[:offset] + marker_line + text[offset:]
    else:
        sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        new_text = text + sep + "## Progress Log\n\n" + marker_line
    full_path.write_text(new_text, encoding="utf-8")
    return h


def main():
    mod = _load_inventory_module()
    cmd = sys.argv[1]

    if cmd == "hash":
        rel_path = sys.argv[2]
        text = (PM / rel_path).read_text(encoding="utf-8")
        print(mod.body_content_hash(text))
        return

    if cmd == "append":
        rel_path = sys.argv[2]
        date = sys.argv[3]
        suffix = sys.argv[4]
        h = append_one(mod, rel_path, date, suffix)
        print(f"OK hash={h} path={rel_path}")
        return

    if cmd == "batch":
        # sys.argv[2] = path to a JSON file: [{"path": ..., "date": "YYYY-MM-DD", "suffix": ...}, ...]
        batch_path = Path(sys.argv[2])
        entries = json.loads(batch_path.read_text(encoding="utf-8"))
        ok, failed = 0, []
        for e in entries:
            try:
                h = append_one(mod, e["path"], e["date"], e["suffix"])
                print(f"OK hash={h} path={e['path']}")
                ok += 1
            except Exception as exc:  # noqa: broad-except — one bad entry must not abort the rest of the batch
                print(f"FAIL path={e['path']} error={exc}")
                failed.append(e["path"])
        print(f"--- batch done: {ok}/{len(entries)} ok, {len(failed)} failed ---")
        if failed:
            print("FAILED PATHS: " + ", ".join(failed))
        return

    raise SystemExit(f"unknown cmd {cmd}")


if __name__ == "__main__":
    main()
