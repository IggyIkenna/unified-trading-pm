# Archived Scripts

These scripts have been **replaced** by the unified `manage-project.sh` script but are preserved here for historical reference.

## Replaced By: `../scripts/project-management/manage-project.sh`

The new unified script consolidates all 6 of these scripts into one tool with best practices from each:

```bash
# Create project
bash manage-project.sh create --name "Project Name" --org IggyIkenna

# Wipe project (30sec for 650 issues)
bash manage-project.sh wipe --project-number 3 --no-confirm

# Regenerate
bash manage-project.sh regenerate --project-number 3

# Delete project
bash manage-project.sh delete --project-number 3
```

## Archived Scripts

### wipe-project-background.sh

**Replaced**: Feb 2026  
**Best Feature**: Parallel deletion with `xargs -P 20` (10x faster)  
**Performance**: 30 seconds to wipe 650 issues (vs 5 minutes sequential)

### clear-github-project.sh

**Replaced**: Feb 2026  
**Best Feature**: Flexible CLI with `--repo`, `--all`, `--close|--delete` options  
**Feature**: Interactive mode for user-friendly operation

### wipe-and-regenerate-project.sh

**Replaced**: Feb 2026  
**Best Feature**: Safety confirmations before destructive operations  
**Feature**: Orchestration of wipe + regenerate workflow

### create-project-fully-automated.sh

**Replaced**: Feb 2026  
**Best Feature**: GraphQL API for project creation (faster, more reliable)  
**Feature**: Idempotent design (checks if project exists before creating)

### delete-and-recreate-project.sh

**Replaced**: Feb 2026  
**Best Feature**: Comprehensive prerequisite checks  
**Feature**: Complete project deletion with confirmations

### run-full-regeneration.sh

**Replaced**: Feb 2026  
**Best Feature**: Orchestration of multiple scripts  
**Feature**: Progress tracking and error handling

## Why These Were Replaced

### Problems:

- **6 overlapping scripts** doing similar things
- **Inconsistent CLI interfaces** (some use positional args, some use flags)
- **No idempotency** (would fail or double-create)
- **Sequential operations** (5 minutes to wipe 650 issues)
- **Duplicate code** across all scripts

### Solution:

The unified `manage-project.sh` script takes the **best feature from each**:

- ✅ Parallel operations (10x faster)
- ✅ Idempotent (safe to re-run)
- ✅ Consistent CLI interface
- ✅ All features in one place
- ✅ DRY principles (no duplicate code)

## Historical Context

These scripts were created between Jan-Feb 2026 during the Wave 1 project setup. They evolved organically as needs changed:

1. **wipe-project-background.sh** - First attempt at fast deletion
2. **clear-github-project.sh** - Added flexibility and safety
3. **create-project-fully-automated.sh** - Removed manual steps
4. **wipe-and-regenerate-project.sh** - Combined wipe + create
5. **delete-and-recreate-project.sh** - Full lifecycle management
6. **run-full-regeneration.sh** - Orchestration wrapper

By Feb 2026, it became clear that consolidation was needed to reduce maintenance burden and improve consistency.

## Reference for Future Projects

If you need to set up similar workflows for other organizations or projects, refer to:

- **Final unified version**: `../scripts/project-management/manage-project.sh`
- **Evolution history**: These 6 scripts show the iteration process
- **Best practices**: Parallel operations, idempotency, GraphQL API, safety confirmations
