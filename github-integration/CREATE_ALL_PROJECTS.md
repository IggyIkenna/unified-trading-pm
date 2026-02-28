# Create All GitHub Projects - Automation Script

**Script:** `create-all-projects.py`  
**Purpose:** Automate creation of 15 missing GitHub projects with labels and setup guides  
**Python:** 3.13+  
**Dependencies:** `gh` CLI, `requests` library

---

## What It Does

Creates 15 GitHub projects based on `PROJECT_STRUCTURE_REFERENCE.md`:

1. **Bugs & Issues** - Production failures
2. **Execution Services** - Live trading + backtest + UI
3. **Strategy Services** - Strategy logic + backtest + UI
4. **Position Monitoring & Risk** - P&L, risk limits
5. **Market Data Pipeline** - Tick ingestion, processing
6. **Features Engineering** - Calendar, Delta-one, Onchain, Volatility
7. **ML Training Services** - Model training
8. **ML Inference Services** - Predictions
9. **ML Deployment Analytics** - Model monitoring
10. **Settlement & Reconciliation** - Trade settlement
11. **Client Reporting** - Performance reports
12. **Infrastructure & Tooling** - Cloud services, deployment
13. **Execution Backtest & UI** - Execution backtesting
14. **Strategy Backtest & UI** - Strategy backtesting

---

## Features

### ✅ Automated

- Project creation via `gh` CLI
- Label creation in target repos
- Idempotent (safe to re-run)
- Batch operations with rate limiting
- Error handling & rollback

### 📝 Semi-Automated (Manual Steps Required)

- Project automation workflows (GitHub API limitation)
- Filtered views (GitHub API limitation)

For each project, generates a manual setup guide: `/tmp/project-{number}-manual-setup.md`

---

## Usage

### 1. Dry Run (Preview)

```bash
# Preview all 15 projects
python create-all-projects.py --org IggyIkenna --dry-run

# Preview specific projects
python create-all-projects.py --org IggyIkenna --dry-run --projects bugs execution strategy
```

### 2. Create Projects

```bash
# Create all 15 projects (interactive confirmation)
python create-all-projects.py --org IggyIkenna --apply

# Create specific projects
python create-all-projects.py --org IggyIkenna --apply --projects bugs execution strategy
```

### 3. Using manage-cods.sh Helper

```bash
# Interactive creation (all 15 projects)
bash manage-cods.sh create-all-projects

# Dry run via helper
bash manage-cods.sh create-all-projects --dry-run
```

---

## Output

### Console Output

```
================================================================================
Create All GitHub Projects - APPLY
================================================================================

Organization: IggyIkenna
Projects to create: 15

[1/15] Bugs & Issues
   ✅ Created project: Bugs & Issues (#4)
   Creating labels...
   ✅ Created 12 labels
   📝 Manual setup guide: /tmp/project-4-manual-setup.md

[2/15] Execution Services
   ✅ Created project: Execution Services (#5)
   Creating labels...
   ✅ Created 8 labels
   📝 Manual setup guide: /tmp/project-5-manual-setup.md

...

================================================================================
Summary
================================================================================

✅ Projects created: 15
❌ Projects failed: 0

📝 Manual setup required for 15 projects:
   - Bugs & Issues (#4): /tmp/project-4-manual-setup.md
   - Execution Services (#5): /tmp/project-5-manual-setup.md
   ...

Each file contains step-by-step instructions for:
   1. Configuring automation workflows (auto-add, auto-status, auto-archive)
   2. Creating filtered views
   3. Verification checklist

Estimated time: 5 minutes per project (~75 minutes total)

================================================================================

✅ Done! Check manual setup guides in /tmp/
```

### Manual Setup Guides

Each project gets a guide like `/tmp/project-4-manual-setup.md`:

```markdown
# Manual Setup Required for Project: Bugs & Issues (#4)

## 1. Configure Project Automation Workflows

Navigate to: https://github.com/users/IggyIkenna/projects/4/settings/workflows

**Add these automation rules:**

### Rule 1: Auto-add items

- **When:** Issues are created or updated
- **If:** Label = "bug"
- **Then:** Add to project

### Rule 2: Auto-status

- **When:** Item is closed
- **Then:** Set status to "Done"

### Rule 3: Auto-archive

- **When:** Item is in "Done" and closed for 30 days
- **Then:** Archive item

---

## 2. Create Filtered Views

Navigate to: https://github.com/users/IggyIkenna/projects/4

### View 1: P0 Critical

- Click "+ New view"
- Name: "P0 Critical"
- Filter: `label:bug label:P0 is:open`
- Save view

### View 2: P1 High

- Click "+ New view"
- Name: "P1 High"
- Filter: `label:bug label:P1 is:open`
- Save view

### View 3: All Open Bugs

- Click "+ New view"
- Name: "All Open Bugs"
- Filter: `label:bug is:open`
- Save view

---

## 3. Verify Setup

- [ ] Automation rules created (3 rules)
- [ ] Views created (3 views)
- [ ] Labels exist in target repos
- [ ] Test: Create issue with label, verify it appears in project

---

**Estimated time:** 5 minutes
```

---

## Project Definitions

Projects are defined in the script with full metadata:

```python
PROJECT_DEFINITIONS = {
    "bugs": {
        "title": "Bugs & Issues",
        "description": "Production failures requiring immediate attention",
        "type": "flat",  # or "hierarchy"
        "primary_label": "bug",
        "additional_labels": ["P0", "P1", "P2"],
        "filter": "label:bug is:open",
        "repos": "all",  # or list of repos
        "views": [
            {"name": "P0 Critical", "filter": "label:bug label:P0 is:open"},
            {"name": "P1 High", "filter": "label:bug label:P1 is:open"},
            {"name": "All Open Bugs", "filter": "label:bug is:open"},
        ],
    },
    # ... 14 more projects
}
```

---

## Error Handling

### Common Issues

**Issue:** `gh: command not found`  
**Fix:** Install GitHub CLI: `brew install gh`

**Issue:** `Not authenticated with GitHub`  
**Fix:** Run `gh auth login`

**Issue:** `Project already exists`  
**Behavior:** Script skips creation, reports existing project number

**Issue:** `Label already exists`  
**Behavior:** Script skips label creation (idempotent)

**Issue:** `Rate limit exceeded`  
**Fix:** Script automatically pauses 1 second between projects. For stricter limits, increase sleep time in script.

---

## Architecture

### Script Flow

```
1. Parse arguments (--org, --dry-run/--apply, --projects)
2. Get GitHub token (GITHUB_TOKEN env var or gh CLI)
3. For each project:
   a. Create project via gh CLI
   b. Create labels in target repos
   c. Generate manual setup guide
   d. Rate limit pause (1 second)
4. Print summary (created, failed, manual steps)
```

### API Usage

**GitHub CLI (gh):**

- `gh project create` - Create project
- `gh project list` - Check existing projects
- `gh label create` - Create labels
- `gh label list` - Check existing labels
- `gh repo list` - Get all repos (for "all" repos projects)

**GitHub GraphQL API:**

- Not used (planned for future workflow/view automation if API support added)

---

## Manual Steps Required

### Why Manual?

GitHub API (both REST and GraphQL) does not support:

1. **Project automation workflows** - No programmatic API
2. **Project filtered views** - No programmatic API

These must be configured via GitHub UI.

### Time Required

- **Per project:** ~5 minutes (3 rules + 2-3 views)
- **Total (15 projects):** ~75 minutes

### Can This Be Automated in Future?

**If GitHub adds API support:**

- Yes, update script to use GraphQL mutations
- Estimated LOC: +200 lines for workflow/view creation

**Until then:**

- Manual setup guides provide step-by-step instructions
- Copy/paste friendly (filter strings ready to use)

---

## Performance

### Speed

- **Dry run:** ~5 seconds (no API calls)
- **Apply (15 projects):** ~45 seconds (3 API calls per project × 1s pause = 45s)
- **Manual setup:** ~75 minutes (5 min per project)

### API Calls

Per project:

- 1 call: Check if project exists (`gh project list`)
- 1 call: Create project (`gh project create`)
- N calls: Create labels (1 per repo, ~2-4 repos per project)

Total for 15 projects: ~60 API calls

---

## Data Integrity

### Idempotency

**Safe to re-run:**

- Existing projects are detected and skipped
- Existing labels are detected and skipped
- No destructive operations

**Example:**

```bash
# Run 1: Creates all 15 projects
python create-all-projects.py --org IggyIkenna --apply

# Run 2: Skips all 15 projects (already exist)
python create-all-projects.py --org IggyIkenna --apply
```

### Rollback

**If script fails mid-execution:**

- Projects created so far remain (not deleted)
- Re-run script to continue from where it stopped
- Existing projects are skipped automatically

**Manual deletion (if needed):**

```bash
# Delete a specific project
gh project delete <project-number> --owner IggyIkenna

# Or delete via UI
https://github.com/users/IggyIkenna/projects/<number>/settings
```

---

## Success Criteria

### For Script

- ✅ All 15 projects created
- ✅ All labels created in target repos
- ✅ Manual setup guides generated
- ✅ No API errors

### For Manual Setup (per project)

- ✅ 3 automation rules configured
- ✅ 2-3 filtered views created
- ✅ Test issue appears in project when labeled

---

## Next Steps

1. **Run dry-run:** Preview what will be created
2. **Run apply:** Create all 15 projects (~45 seconds)
3. **Manual setup:** Follow guides in `/tmp/` (~75 minutes)
4. **Verify:** Create test issues with labels, check project population
5. **Iterate:** If issues found, fix and re-run (idempotent)

---

## Examples

### Create All Projects

```bash
cd unified-trading-codex/11-project-management/github-integration

# Dry run first
python create-all-projects.py --org IggyIkenna --dry-run

# Apply changes
python create-all-projects.py --org IggyIkenna --apply

# Check manual setup guides
ls -lh /tmp/project-*-manual-setup.md

# Open first guide
cat /tmp/project-4-manual-setup.md
```

### Create Specific Projects

```bash
# Only create bugs and execution projects
python create-all-projects.py --org IggyIkenna --apply --projects bugs execution

# Output: Creates 2 projects instead of 15
```

### Using Helper Script

```bash
# Via manage-cods.sh helper
bash manage-cods.sh create-all-projects

# Dry run
bash manage-cods.sh create-all-projects --dry-run
```

---

## Troubleshooting

### Script Hangs

**Cause:** Rate limiting or network issue  
**Fix:** Interrupt (Ctrl+C), re-run (idempotent)

### "Project already exists" for All Projects

**Cause:** Projects were created previously  
**Action:** Check project URLs, verify they're correct

### Labels Not Created

**Cause:** Repo issues disabled or repo doesn't exist  
**Fix:** Check repo exists and has issues enabled: `gh repo view <org>/<repo>`

### Manual Setup Guide Missing

**Cause:** Project number not returned (API error)  
**Fix:** Check console output for error message, manual create project

---

## Version History

**v1.0 (2026-02-13):**

- Initial release
- 15 project definitions
- Automated project + label creation
- Manual setup guide generation
- Idempotent, error handling
- Based on PROJECT_STRUCTURE_REFERENCE.md

---

**Related Files:**

- `PROJECT_STRUCTURE_REFERENCE.md` - Source of truth for project definitions
- `setup-cod-project.py` - COD-specific project setup (already done)
- `manage-cods.sh` - Helper script with create-all-projects command
- `AUTOMATION_STATUS.md` - What's automated, what's manual (why)

**Status:** ✅ Ready for production use
