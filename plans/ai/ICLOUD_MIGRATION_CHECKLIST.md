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
