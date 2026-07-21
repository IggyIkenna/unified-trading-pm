---
doc_type: plan
title: iCloud to Code Migration Checklist
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-04"
---

## Deferred work — migrated to:

**None** — successor: not applicable. Verified 2026-07-21 (batch-5 archived-plan discipline triage,
`pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md`): the 4 remaining open items are stale — the
dependency-alignment count (Stage 3) is superseded by the live `check-dependency-alignment.py` +
`canonical-dependency-manifest.json` enforcement mechanism; the iCloud symlink step (Stage 4) is a one-time Mac-side
action whose practical goal (Code-only checkouts) is demonstrably achieved independent of ever running it; Stage 5's
item is self-declared "Out of scope." No open iCloud/Apple-migration references exist in any plan from the last 4+
months.

# iCloud to Code Migration Checklist

Track progress per repo. SSOT: ICLOUD_CORRUPT_FILES_MIGRATION_REPORT.md, workspace-manifest.json.

## Stage 0: Delete Corrupt Files

- [x] Delete all corrupt files at iCloud
- [x] Verify zero corrupt
- [x] Script: delete-corrupt-files-at-icloud.sh

## Stage 1: Blind Copy (36-37 Clean Repos)

- [x] Copy clean repos
- [x] Script: copy-clean-repos.sh

## Stage 2: Copy 18 Corrupt Repos

- [x] Copy after corrupt deletion
- [x] Script: copy-corrupt-repos.sh

## Stage 3: Merge + UTL + Dependency Alignment

- [x] UTL consolidation: unified-trading-library only
- [x] External dependency alignment: fix applied; constraints resolve
- [ ] Internal manifest/pyproject alignment: 87 remaining

## Stage 4: Symlink + Push

- [ ] Symlink iCloud to Code
- [ ] Script: symlink-icloud-to-code.sh

## Stage 5: Remove Cloud (Future)

- [ ] Out of scope
