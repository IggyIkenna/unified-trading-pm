# One-Time Scripts

These scripts were used for **one-time migrations or setup tasks** and are preserved here for reference when setting up
new projects or performing similar migrations in the future.

## Scripts

### create-initial-cleanup-project.sh

**Purpose**: Create "Initial Cleanup" project with one task per repo  
**When Used**: Feb 2026 (initial COD cleanup before granular tracking)  
**Reusable For**:

- Creating cleanup/chore projects for bulk fixes
- One-issue-per-repo strategy for large-scale cleanup
- Temporary projects before transitioning to per-service tracking

**Key Patterns**:

```bash
# Create project + 14 issues (one per repo)
# Each issue: "Fix ALL COD violations in [repo-name]"
gh api graphql -f query='mutation { createProjectV2(...) }'
gh issue create --title "[CLEANUP] Fix all COD violations in repo"
```

**Strategy**:

- **Simple**: 14 issues (not 200+)
- **Clear ownership**: 1 worker = 1 repo
- **Sequential fixes**: Within repo (easier to verify)
- **Clean slate**: Per repo before moving on

**When to Reuse**:

- Large-scale refactoring across all repos
- Breaking changes requiring bulk updates
- Initial setup before granular tracking
- Temporary "mega-task" approach

---

### setup-cod-project-workflows.py

**Purpose**: Set up GitHub Project workflows for the COD project  
**When Used**: Jan 2026 (one-time setup)  
**Reusable For**:

- Setting up project workflows for new service-level projects
- Configuring automated issue routing based on labels
- Creating filtered views for different issue types

**Key Patterns**:

```python
# Set up workflow that auto-adds issues with "cod" label
workflow = {
    "filters": "label:cod",
    "auto_add": True
}
```

**When to Reuse**:

- Creating 32 service-level projects (each needs similar workflows)
- Setting up cross-cutting concern projects (Waves, CODs)
- Migrating to new organizations

---

### update-all-quickmerge.py

**Purpose**: Update quickmerge scripts across all 30 repos  
**When Used**: Feb 2026 (quality gates standardization)  
**Reusable For**:

- Bulk updates to scripts across many repos
- Standardizing tooling across services
- Migrating scripts to new patterns

**Key Patterns**:

```python
# Clone all repos, update files, commit, push
for repo in all_repos:
    clone(repo)
    update_files(repo, pattern)
    commit_and_push(repo, message)
```

**When to Reuse**:

- Updating pre-commit hooks across all repos
- Migrating from ruff 0.1.x to 0.8.x
- Standardizing Dockerfile patterns

---

### update-cod-size-threshold.sh

**Purpose**: Update COD-SIZE threshold from 2000 to 1500 lines  
**When Used**: Feb 2026 (stricter SRP enforcement)  
**Reusable For**:

- Updating issue thresholds
- Bulk closing/updating issues based on criteria
- Policy changes requiring issue updates

**Key Patterns**:

```bash
# Find all issues with COD-SIZE label, update threshold
gh issue list --label "COD-SIZE" --json number \
  | xargs -I {} gh issue edit {} --body "New threshold: 1500 lines"
```

**When to Reuse**:

- Updating P0/P1/P2 priority definitions
- Changing Epic/Task/Subtask hierarchy
- Bulk updating issue metadata

---

### update-quickmerge-pr-body.sh

**Purpose**: Update PR body template in quickmerge scripts  
**When Used**: Feb 2026 (improved PR descriptions)  
**Reusable For**:

- Standardizing PR templates
- Adding quality gate status to PR bodies
- Improving PR descriptions for better review

**Key Patterns**:

```bash
# Find all quickmerge.sh scripts, update PR body section
find . -name "quickmerge.sh" \
  | xargs -I {} sed -i '' 's/OLD_TEMPLATE/NEW_TEMPLATE/g' {}
```

**When to Reuse**:

- Updating PR templates across repos
- Adding new sections to quickmerge scripts
- Standardizing commit message formats

---

### bulk-close-cod-size.sh

**Purpose**: Close all COD-SIZE issues after threshold change  
**When Used**: Feb 2026 (cleanup after threshold update)  
**Reusable For**:

- Bulk closing stale issues
- Cleaning up after policy changes
- Resetting project state

**Key Patterns**:

```bash
# Close all issues with specific label
gh issue list --label "COD-SIZE" --json number \
  | xargs -P 20 -I {} gh issue close {} --comment "Threshold updated to 1500"
```

**When to Reuse**:

- Closing Wave 1 issues after completion
- Bulk archiving old issues
- Project cleanup before regeneration

## When to Use These Scripts

### Setting Up New Service-Level Projects (32 projects)

Use: `setup-cod-project-workflows.py`

- Adapt to create workflows for each service project
- Configure label-based routing (CODs, Waves)
- Set up filtered views

### Bulk Updates Across All Repos

Use: `update-all-quickmerge.py`

- Pattern for updating any script/config across 30 repos
- Git automation (clone, update, commit, push)
- Error handling for large-scale changes

### Policy Changes Requiring Issue Updates

Use: `update-cod-size-threshold.sh` + `bulk-close-cod-size.sh`

- Pattern for updating existing issues
- Bulk closing/updating based on criteria
- Communication via issue comments

### Template Standardization

Use: `update-quickmerge-pr-body.sh`

- Pattern for finding and updating templates
- Sed-based text replacement
- Validation of changes

## Best Practices

### Before Running One-Time Scripts:

1. **Dry-run first**: Test on a single repo/issue
2. **Backup critical data**: Export issues, projects before bulk operations
3. **Rate limiting**: Use `sleep` or `xargs -P` limits to avoid GitHub API throttling
4. **Idempotency**: Check if operation already done before executing
5. **Logging**: Save output for debugging if something goes wrong

### Example Dry-Run Pattern:

```bash
# Add --dry-run flag to preview changes
python3 script.py --dry-run

# Or manually test on one item first
gh issue close 1234 --comment "Test"

# Then run in parallel on all items
gh issue list --label "test" --json number \
  | xargs -P 20 -I {} gh issue close {}
```

## Migration Checklist

When adapting these scripts for new projects or organizations:

- [ ] Update `ORG` variable (currently `IggyIkenna`)
- [ ] Update `REPO` variable (currently `unified-trading-codex`)
- [ ] Update project numbers (currently #1, #3)
- [ ] Update label names if different
- [ ] Test on single item first
- [ ] Run dry-run mode
- [ ] Execute on full dataset
- [ ] Verify results
- [ ] Document any changes

## Historical Context

These scripts were created during:

- **Jan 2026**: Initial COD project setup
- **Feb 2026**: Quality gates standardization, COD-SIZE threshold change

They represent:

- **Bulk operations** (updating 30 repos at once)
- **Policy enforcement** (new thresholds, standards)
- **Template standardization** (quickmerge, PR bodies)
- **Project setup** (workflows, views, automation)

## Why These Are One-Time

These scripts are **one-time** because:

- They modify existing state (close old issues, update thresholds)
- They were needed for a specific migration (ruff 0.1.x → 0.8.x)
- They set up infrastructure that doesn't change (project workflows)

However, the **patterns** are reusable:

- Bulk operations across repos
- Issue state transitions
- Project setup automation
- Template standardization

Keep them as **reference implementations** for future similar tasks.
