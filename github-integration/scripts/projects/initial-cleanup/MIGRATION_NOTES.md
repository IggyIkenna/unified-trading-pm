# Migration Notes: Project Housekeeping (2026-02-14)

## Scripts Moved to Project Directory

The following scripts were moved from scattered locations into this project directory:

### From `scripts/core/`

- `02-run-diff-checker.py` → `utilities/check-codex-violations.py`
  - Core violation checker for all 8 codex checks
  - Used by 06-generate-manifests.py
  - Project-specific (Initial Cleanup only checks standard violations)

### From `scripts/one-time/`

- `generate-codex-violation-manifests.py` → `06-generate-manifests.py`
  - Generates CODEX_VIOLATIONS_MANIFEST.md for each repo
  - Numbered to fit project script sequence
  - Path updated to reference utilities/check-codex-violations.py

### Still in `scripts/core/` (Will Move Later)

- `05-check-file-size-cods.py`
  - Checks for COD-SIZE violations (files >1500 lines)
  - Will move to `scripts/projects/cod-size-refactoring/` when Project #6 is created

## Why This Reorganization?

1. **Project-focused**: All Initial Cleanup scripts in one place
2. **Maintainability**: Clear which scripts belong to which project
3. **Discoverability**: Easy to find compliance checkers for this project
4. **Template**: Establishes pattern for future projects
5. **No duplication**: `utilities/` subdirectory for helper scripts

## Path Updates Required

### In issue bodies (02-create-issues.sh):

```bash
# Old path:
python3 unified-trading-codex/.../scripts/one-time/generate-codex-violation-manifests.py

# New path:
cd unified-trading-codex/.../scripts/projects/initial-cleanup
python3 06-generate-manifests.py
```

### In manifest generator (06-generate-manifests.py):

```python
# Old path:
scripts/core/02-run-diff-checker.py

# New path:
scripts/projects/initial-cleanup/utilities/check-codex-violations.py
```

## Backward Compatibility

**Old scripts remain in original locations** (for now):

- `scripts/core/02-run-diff-checker.py` - Still exists
- `scripts/one-time/generate-codex-violation-manifests.py` - Still exists

**Deprecation plan:**

- Add deprecation notices to old scripts pointing to new locations
- Update all references in documentation
- Remove old scripts in future cleanup (after verifying no external dependencies)

## Future Projects

This pattern will be replicated for COD-SIZE Refactoring (Project #6):

```
scripts/projects/cod-size-refactoring/
├── utilities/
│   └── check-file-size-violations.py  (from core/05-check-file-size-cods.py)
├── 01-create-project.sh
├── 02-create-issues.sh
├── 03-link-issues-to-project.sh
├── 04-run-batch-fix.sh
├── 05-verify-completion.sh
├── 06-generate-manifests.py
├── AGENT_PROMPT.md
├── WORKFLOW.md
└── README.md
```

## Testing

To verify the migration worked:

```bash
cd scripts/projects/initial-cleanup

# Test manifest generation
python3 06-generate-manifests.py --dry-run --repos "unified-trading-services"

# Should output violations found (or none if already fixed)
# Should NOT error with "file not found"
```

## References

- Initial Cleanup README: `./README.md` (updated with new scripts)
- Projects README: `../README.md` (documents migration)
- Workspace rules: `.cursorrules` (no changes needed)
