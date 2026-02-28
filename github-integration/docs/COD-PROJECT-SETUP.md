# COD Project Setup Guide

## Overview

This script organizes all COD (Change of Direction) issues into a dedicated GitHub project, separating them from
epics/tasks/subtasks for better project visibility.

## Problem

With 600-700 COD issues mixed with regular work items, main projects become cluttered and it's hard to track actual
epics, tasks, and subtasks.

## Solution

1. **Dedicated COD Project** - Central place to view all CODs
2. **COD Label** - Automatic tagging for filtering
3. **Filtered Views** - Main projects exclude CODs by default
4. **Automation** - Auto-add issues with 'cod' label to COD project

---

## Quick Start

### 1. Dry Run (Preview Changes)

```bash
cd unified-trading-codex/11-project-management/github-integration

# Preview what will be done
python setup-cod-project.py --org IggyIkenna --dry-run
```

### 2. Apply Changes

```bash
# Make actual changes to GitHub
python setup-cod-project.py --org IggyIkenna --apply
```

### 3. Specific Repositories Only

```bash
# Process only specific repos
python setup-cod-project.py --org IggyIkenna --repos execution-services unified-trading-services --apply
```

---

## What the Script Does

### Step 1: Create 'cod' Label

- Creates a purple `cod` label in all repositories
- Color: `#d4c5f9` (light purple)
- Description: "Change of Direction - architectural/design pivots tracked separately"

### Step 2: Find COD Issues

**Optimized with org-wide search batching:**

- Uses 3 API calls instead of repos × 3 (e.g., 96 calls → 3 calls)
- Searches across entire org for:
  - "COD" in title
  - "change of direction" in title
  - "change-of-direction" in title
- **Savings:** ~93 fewer API calls for 32 repos

### Step 3: Apply Labels

- Bulk applies `cod` label to all identified issues
- Skips issues already labeled

### Step 4: Create Project

Creates a GitHub project titled "CODs (Change of Direction)" with:

- Description of purpose
- Usage guidelines
- Automatic issue tracking

### Step 5: Add Issues to Project

- Adds all COD issues to the new project
- Handles duplicates gracefully

### Step 6: Setup Automation (Manual)

Provides instructions for:

- Auto-add items with 'cod' label
- Auto-move closed items
- Auto-archive after 30 days

### Step 7: Update Issue Templates (Manual)

Provides template snippet to add COD checkbox to issue templates

### Step 8: Create Filters (Manual)

Provides filter examples for main projects:

- Exclude CODs: `-label:cod`
- Epics only (no CODs): `label:epic -label:cod`
- Tasks/subtasks only: `label:task,subtask -label:cod`

---

## Performance & Batching

### Optimized Operations (Batched)

**Issue Search (Step 2):**

- ✅ **Batched**: Uses org-wide search
- **API calls**: 3 (regardless of repo count)
- **Example savings**: 32 repos × 3 searches = 96 calls → 3 calls (97% reduction)

### Sequential Operations (Cannot Batch)

**Label Creation (Step 1):**

- ⚠️ **Per-repo**: GitHub doesn't support batch label creation
- **API calls**: 1 per repository
- **Workaround**: Script shows progress every 10 repos

**Label Application (Step 3):**

- ⚠️ **Per-issue**: GitHub CLI requires individual edits
- **API calls**: 1 per unlabeled issue
- **Workaround**: Script shows progress every 50 issues
- **Alternative**: GraphQL mutations could batch, but adds complexity

**Add to Project (Step 5):**

- ⚠️ **Per-issue**: GitHub requires individual project item additions
- **API calls**: 1 per issue
- **Workaround**: Script shows progress every 50 issues

### Expected Runtime

For 600 COD issues across 32 repos:

- **Label creation**: ~30 seconds (32 API calls)
- **Issue search**: ~5 seconds (3 API calls) ✅ **Batched**
- **Label application**: ~10 minutes (600 API calls)
- **Add to project**: ~10 minutes (600 API calls)
- **Total**: ~20-25 minutes

### Rate Limits

GitHub API rate limits:

- **Authenticated**: 5,000 requests/hour
- **This script**: ~1,235 requests for 600 CODs
- **Safe margin**: Uses ~25% of hourly limit

---

## Manual Steps After Running Script

### 1. Configure Project Automation

Go to: `https://github.com/orgs/IggyIkenna/projects/<PROJECT_NUMBER>/settings`

Add these workflow rules:

**Auto-add COD issues:**

- **When:** Label is added
- **If:** Label = "cod"
- **Then:** Add to project

**Auto-move closed:**

- **When:** Issue is closed
- **Then:** Set Status to "Done"

**Auto-archive:**

- **When:** Issue has been closed for 30 days
- **Then:** Archive item

### 2. Update Issue Templates

Add this snippet to `.github/ISSUE_TEMPLATE/*.md`:

```markdown
## Issue Classification

- [ ] Epic
- [ ] Task
- [ ] Subtask
- [ ] COD (Change of Direction)

> **Note:** Select 'COD' for architectural pivots, design changes, or strategic redirections. CODs are tracked
> separately in the [COD Project](https://github.com/orgs/IggyIkenna/projects/<PROJECT_NUMBER>).
```

### 3. Create Saved Filters in Main Projects

For each main project:

1. Go to project → Views → New view → Table
2. Create these saved filters:

| Filter Name        | Query                           | Purpose                     |
| ------------------ | ------------------------------- | --------------------------- |
| All Work (No CODs) | `-label:cod`                    | Default view excluding CODs |
| Epics Only         | `label:epic -label:cod`         | Epic planning               |
| Tasks & Subtasks   | `label:task,subtask -label:cod` | Sprint work                 |

3. Set "All Work (No CODs)" as default view

---

## Expected Results

### Before

```
Main Project View:
- 700 items total
- Mix of epics, tasks, subtasks, and CODs
- Hard to see actual work items
- CODs pollute sprint planning
```

### After

```
Main Project View:
- ~100 items (epics, tasks, subtasks only)
- Clear visibility of actual work
- CODs filtered out by default

COD Project View:
- ~600 COD issues centralized
- Historical design decisions visible
- Can review/close old CODs separately
```

---

## Troubleshooting

### Error: "gh: command not found"

Install GitHub CLI:

```bash
# macOS
brew install gh

# Authenticate
gh auth login
```

### Error: "Permission denied"

Ensure you have admin access to:

- Organization (for creating projects)
- Repositories (for creating labels and editing issues)

### Script finds 0 COD issues

Check:

1. Are CODs titled consistently? (e.g., "COD: ..." or "Change of Direction: ...")
2. Run manual search: `gh issue list --search "COD in:title"`
3. Adjust search terms in script if needed

### Too many issues to process

Run in batches:

```bash
# Process 5 repos at a time
python setup-cod-project.py --org IggyIkenna --repos repo1 repo2 repo3 repo4 repo5 --apply
```

---

## Maintenance

### Adding New CODs

Simply label new issues with `cod` - automation will add them to the project.

### Closing Old CODs

1. Review CODs in project quarterly
2. Close irrelevant or completed CODs
3. Automation will archive them after 30 days

### Re-running Script

Safe to re-run anytime:

- Skips existing labels
- Skips already-labeled issues
- Handles duplicates in project

---

## Files

- `setup-cod-project.py` - Main script
- `COD-PROJECT-SETUP.md` - This guide

## Support

For issues or questions, see:

- GitHub CLI docs: https://cli.github.com/manual/
- GitHub Projects docs: https://docs.github.com/en/issues/planning-and-tracking-with-projects

---

## Example Output

```
================================================================================
COD Project Setup
================================================================================

⚠️  APPLY MODE - Changes will be made to GitHub

📂 Fetching repository list...
  ✓ Found 32 repositories

📋 Step 1: Creating 'cod' label...
  Processing execution-services...
    ✓ Created 'cod' label
  Processing unified-trading-services...
    ✓ Label 'cod' already exists

🔍 Step 2: Finding COD issues...
  Searching execution-services...
  Searching unified-trading-services...
  ✓ Found 637 COD issues
    589 need labeling

🏷️  Step 3: Applying 'cod' labels...
  execution-services#1234: COD: Migrate from NautilusTrader to custom engine...
    ✓ Added 'cod' label
  [... 588 more ...]

📊 Step 4: Creating COD project...
  ✓ Created project #42

➕ Step 5: Adding issues to COD project...
  Adding execution-services#1234...
    ✓ Added
  [... 636 more ...]

⚙️  Step 6: Setting up project automation...
  ⚠️  Automation rules must be configured manually in project settings:
     https://github.com/orgs/IggyIkenna/projects/42/settings

📝 Step 7: Updating issue templates...
  💡 Manual step required:
     Add the following snippet to your issue templates:
     [... template snippet ...]

🔍 Step 8: Creating filter documentation...
  📋 Saved filters to add to main projects:
     [... filter examples ...]

================================================================================
✅ Setup complete!
================================================================================

📋 Next manual steps:
1. Configure project automation rules (see output above)
2. Update issue templates with COD option
3. Create saved filters in main projects to exclude 'cod' label
4. Share COD project: https://github.com/orgs/IggyIkenna/projects
```
