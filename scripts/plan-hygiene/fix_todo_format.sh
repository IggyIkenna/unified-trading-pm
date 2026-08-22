#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Auto-rewrite non-canonical todo lines in plans/active/ to canonical form:
#   - [ ] [TAG] P<0-3>. <description>
#
# Handles these mechanical-rewrite patterns:
#   - [ ] [TAG][P<n>] body         → - [ ] [TAG] P<n>. body
#   - [ ] [TAG] [P<n>] body        → - [ ] [TAG] P<n>. body
#   - [ ] [P<n>][TAG] body         → - [ ] [TAG] P<n>. body
#   - [ ] [P<n>] [TAG] body        → - [ ] [TAG] P<n>. body
#   - [ ] [TAG1][TAG2][P<n>] body  → - [ ] [TAG1] [TAG2] P<n>. body
#
# Does NOT touch:
#   - todos with no P-priority anywhere (operator must choose priority)
#   - lines already canonical (no-op)
#   - emoji-prefixed todos like '- [ ] 🟠 [TAG] P<n>.' (leaves emoji in place;
#     regen is tolerant of this, and the emoji conveys status)
#
# Usage:
#   bash scripts/plan-hygiene/fix_todo_format.sh           # dry-run, prints diff
#   bash scripts/plan-hygiene/fix_todo_format.sh --apply   # write changes in place

set -euo pipefail
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

python3 - "$PM_DIR" "$APPLY" <<'PY'
import re, sys, glob, pathlib, os

pm = pathlib.Path(sys.argv[1])
apply = sys.argv[2] == "1"

scan = list((pm / "plans/active").glob("*.md")) + list((pm / "plans/active/issues").glob("*.md"))
scan = [p for p in scan if p.name != "_agent_pings.md"]

TAG = r"[A-Z][A-Z0-9_-]*"
PRI = r"P[0-3](?:\.[0-9]+)*"

# Patterns: ordered by specificity. Each maps a non-canonical capture to
# canonical "[TAG] [optional second tag] P<n>. <rest>".
RULES = [
    # Edge case A: [TAG — inline qualifier] [SECOND_TAG] P<n>. body
    #   → [TAG] [SECOND_TAG] P<n>. body — inline qualifier
    # Decision: move qualifier to description (plan Phase 4 option b).
    # Covers BLOCKED-CREDENTIALS and similar annotated blocked tags.
    (re.compile(rf"^(- \[ \] )\[({TAG}) — ([^\]]+)\] \[({TAG})\] ({PRI})\.\s*(.*)$"),
     lambda m: f"{m.group(1)}[{m.group(2)}] [{m.group(4)}] {m.group(5)}. {m.group(6).rstrip()} — {m.group(3).strip()}"),
    # Edge case A (no second tag): [TAG — inline qualifier] P<n>. body
    #   → [TAG] P<n>. body — inline qualifier
    (re.compile(rf"^(- \[ \] )\[({TAG}) — ([^\]]+)\] ({PRI})\.\s*(.*)$"),
     lambda m: f"{m.group(1)}[{m.group(2)}] {m.group(4)}. {m.group(5).rstrip()} — {m.group(3).strip()}"),
    # Edge case B: [CLAUDE.md] P<n>. body  → [CLAUDE-MD] P<n>. body
    # Decision: rename tag — dots break the tag regex.
    (re.compile(rf"^(- \[ \] )\[CLAUDE\.md\] ({PRI})\.\s*(.*)$"),
     lambda m: f"{m.group(1)}[CLAUDE-MD] {m.group(2)}. {m.group(3)}"),
    # [TAG1][TAG2][P<n>] body   → [TAG1] [TAG2] P<n>. body
    (re.compile(rf"^(- \[ \] )\[({TAG})\]\s*\[({TAG})\]\s*\[({PRI})\]\s*(.*)$"),
     lambda m: f"{m.group(1)}[{m.group(2)}] [{m.group(3)}] {m.group(4)}. {m.group(5)}"),
    # [TAG][P<n>][SECOND] body  → [TAG] [SECOND] P<n>. body
    (re.compile(rf"^(- \[ \] )\[({TAG})\]\s*\[({PRI})\]\s*\[({TAG})\]\s*(.*)$"),
     lambda m: f"{m.group(1)}[{m.group(2)}] [{m.group(4)}] {m.group(3)}. {m.group(5)}"),
    # [P<n>][TAG] body          → [TAG] P<n>. body
    (re.compile(rf"^(- \[ \] )\[({PRI})\]\s*\[({TAG})\]\s*(.*)$"),
     lambda m: f"{m.group(1)}[{m.group(3)}] {m.group(2)}. {m.group(4)}"),
    # [TAG][P<n>] body          → [TAG] P<n>. body
    (re.compile(rf"^(- \[ \] )\[({TAG})\]\s*\[({PRI})\]\s*(.*)$"),
     lambda m: f"{m.group(1)}[{m.group(2)}] {m.group(3)}. {m.group(4)}"),
    # [P<n>] body  (no tag)     → [AGENT] P<n>. body   (default tag for tag-less todos)
    (re.compile(rf"^(- \[ \] )\[({PRI})\]\s+(.*)$"),
     lambda m: f"{m.group(1)}[AGENT] {m.group(2)}. {m.group(3)}"),
]

# Skip lines already canonical (single or double tag + bare P<n>.)
canonical = re.compile(rf"^- \[ \] \[{TAG}\] ?(\[{TAG}\] ?)?{PRI}\.")

total_files = 0
total_lines = 0
changes_by_file = []

for f in scan:
    text = f.read_text()
    new_lines = []
    file_changes = []
    for i, line in enumerate(text.split("\n"), 1):
        if not line.startswith("- [ ] "):
            new_lines.append(line)
            continue
        if canonical.match(line):
            new_lines.append(line)
            continue
        rewritten = line
        for rx, fn in RULES:
            m = rx.match(rewritten)
            if m:
                rewritten = fn(m)
                # don't double-apply other rules; one fix per line
                break
        if rewritten != line:
            file_changes.append((i, line, rewritten))
            total_lines += 1
        new_lines.append(rewritten)
    if file_changes:
        total_files += 1
        changes_by_file.append((f, file_changes))
        if apply:
            f.write_text("\n".join(new_lines))

print(f"# fix_todo_format: {total_lines} line(s) in {total_files} file(s) {'rewritten' if apply else 'would be rewritten (dry-run; pass --apply)'}")
for f, changes in changes_by_file:
    rel = f.relative_to(pm)
    print(f"\n--- {rel} ({len(changes)} change(s)) ---")
    for ln, before, after in changes[:5]:  # show first 5 per file
        print(f"  L{ln}")
        print(f"    BEFORE: {before[:140]}")
        print(f"    AFTER : {after[:140]}")
    if len(changes) > 5:
        print(f"  ... and {len(changes) - 5} more")
PY
