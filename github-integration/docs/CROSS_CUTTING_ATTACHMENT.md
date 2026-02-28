# Cross-Cutting Attachment Strategy

## Overview

Cross-cutting concerns (CODs, Waves) span multiple services. This document explains how they attach to **both**
cross-cutting projects AND service-level projects without duplication.

## The Problem

- **COD issues** affect multiple services (e.g., file size violations, coding standards)
- **Wave issues** span multiple services (e.g., Wave 1 new features)
- **Challenge:** How to show these issues in:
  - Cross-cutting projects (COD Project #3, Wave 1 Project #1)
  - Service-level projects (32 service projects)
  - WITHOUT duplicating issues or manual dual-tagging

## The Solution: Label-Based Dual Attachment

GitHub Project Workflows automatically attach issues to multiple projects based on labels and milestones.

### Key Concept

**Single Issue → Multiple Project Views**

- Issue exists ONCE in repository
- Appears in MULTIPLE projects via filters
- Close issue once → disappears from all projects
- No manual dual-tagging required

## How It Works

### For CODs (Code-Owned Debt)

#### Step 1: Issue Created with `cod` Label

```bash
# check-file-size-cods.py creates issue
gh issue create --repo IggyIkenna/execution-services \
  --title "[COD-SIZE] execution_services/engine.py (2340 lines)" \
  --label "cod,COD-SIZE,P1-high" \
  --body "..."
```

#### Step 2: GitHub Project Workflows Auto-Add

**COD Project (#3):**

- Workflow filter: `label:cod`
- Issue automatically added to COD Project

**Service Project (Execution Services):**

- Workflow filter: `repo:execution-services`
- Issue automatically added to Service Project

#### Result: Issue Appears in BOTH Projects

```
Issue #123: [COD-SIZE] execution_services/engine.py (2340 lines)

Appears in:
  - Project #3 (CODs) ✅ via label:cod
  - Project #4 (Execution Services) ✅ via repo:execution-services
```

### For Waves (Milestone-Based Features)

#### Step 1: Issue Created with `milestone:Wave1`

```bash
# Delta audit creates issue
gh issue create --repo IggyIkenna/execution-services \
  --title "[Gap] execution-services: Add dYdX support" \
  --label "execution,missing_implementation,P1-high" \
  --milestone "Wave1"
```

#### Step 2: GitHub Project Workflows Auto-Add

**Wave 1 Project (#1):**

- Workflow filter: `milestone:Wave1`
- Issue automatically added to Wave 1 Project

**Service Project (Execution Services):**

- Workflow filter: `repo:execution-services`
- Issue automatically added to Service Project

#### Result: Issue Appears in BOTH Projects

```
Issue #456: [Gap] execution-services: Add dYdX support

Appears in:
  - Project #1 (Wave 1) ✅ via milestone:Wave1
  - Project #4 (Execution Services) ✅ via repo:execution-services
```

## Project Structure

### Cross-Cutting Projects (2)

#### Project #1: Wave 1 - Unified Board

- **Filter:** `milestone:Wave1`
- **Scope:** All Wave 1 issues across all services
- **Issues:** ~300 (Wave 1 features, gaps)

#### Project #3: CODs (Change of Direction)

- **Filter:** `label:cod`
- **Scope:** All COD issues across all services
- **Issues:** ~200 (file size, coding standards, architectural changes)

### Service-Level Projects (32)

**One project per service** from `service-registry.yaml`:

#### Example: Project #4 - Execution Services

- **Filter:** `repo:execution-services`
- **Scope:** All issues for execution-services
- **Views:**
  - **Work Items:** `repo:execution-services -label:cod` (regular work)
  - **CODs Only:** `repo:execution-services label:cod` (CODs for this service)
  - **Wave 1 Items:** `repo:execution-services milestone:Wave1` (Wave 1 for this service)
  - **Epics Only:** `repo:execution-services label:epic -label:cod` (Epic-level work)

## Benefits

### ✅ No Manual Dual-Tagging

- Issues automatically appear in multiple projects
- No need to manually add issues to both projects
- GitHub Project Workflows handle it

### ✅ Single Source Issue

- Close issue once → disappears from all projects
- Update issue once → updates in all projects
- No data inconsistencies

### ✅ Filter Flexibility

- Service projects can show:
  - All work (`repo:service`)
  - CODs only (`repo:service label:cod`)
  - Wave 1 only (`repo:service milestone:Wave1`)
  - Regular work only (`repo:service -label:cod -milestone:Wave1`)

### ✅ Correct Cross-Cutting Concerns

- CODs tracked centrally (Project #3) AND per-service
- Waves tracked centrally (Project #1) AND per-service
- No duplication

## Example Workflows

### Workflow 1: Create COD Issue

```bash
# 1. Script creates issue with cod label
python3 check-file-size-cods.py --repo execution-services

# 2. GitHub automatically adds to:
#    - COD Project (#3) via label:cod
#    - Execution Services Project (#4) via repo:execution-services

# 3. Developer works on issue in either project view

# 4. Close issue once:
gh issue close 123 --repo IggyIkenna/execution-services

# 5. Issue disappears from BOTH projects
```

### Workflow 2: Create Wave 1 Issue

```bash
# 1. Delta audit creates issue with Wave1 milestone
python3 run-diff-checker.py --repo execution-services

# 2. GitHub automatically adds to:
#    - Wave 1 Project (#1) via milestone:Wave1
#    - Execution Services Project (#4) via repo:execution-services

# 3. PM tracks progress in Wave 1 Project
# 4. Developer works in Service Project
# 5. Both see same issue, same updates
```

### Workflow 3: Service-Level View

From Execution Services Project (#4):

**View: All Work**

- Filter: `repo:execution-services`
- Shows: CODs, Waves, regular work, epics

**View: CODs Only**

- Filter: `repo:execution-services label:cod`
- Shows: Only CODs for this service

**View: Wave 1 Only**

- Filter: `repo:execution-services milestone:Wave1`
- Shows: Only Wave 1 work for this service

**View: Regular Work**

- Filter: `repo:execution-services -label:cod -milestone:Wave1`
- Shows: Only non-COD, non-Wave work

## Setup Instructions

### 1. Create Cross-Cutting Projects (Done)

- ✅ Project #1: Wave 1 - Unified Board
- ✅ Project #3: CODs

### 2. Create Service-Level Projects (32 total)

```bash
python3 scripts/utilities/create-all-service-projects.py --all-services --dry-run
python3 scripts/utilities/create-all-service-projects.py --all-services
```

### 3. Configure Project Workflows

For each service project:

1. Go to project settings
2. Navigate to "Workflows"
3. Create workflow: "Auto-add issues from repo"
   - **Trigger:** Issue opened/reopened
   - **Filter:** `repo:service-name`
   - **Action:** Add to this project

### 4. Create Filtered Views

For each service project:

1. **Work Items View:**
   - Filter: `repo:service-name -label:cod`
   - Layout: Table
   - Fields: Title, Status, Priority, Assignees

2. **CODs Only View:**
   - Filter: `repo:service-name label:cod`
   - Layout: Table
   - Fields: Title, Status, Priority, File Path

3. **Wave 1 Items View:**
   - Filter: `repo:service-name milestone:Wave1`
   - Layout: Roadmap
   - Group by: Status

4. **Epics Only View:**
   - Filter: `repo:service-name label:epic -label:cod`
   - Layout: Table
   - Fields: Title, Status, Priority, Tasks

## Validation

### Test Cross-Cutting Attachment

```bash
# 1. Create test COD issue
gh issue create --repo IggyIkenna/instruments-service \
  --title "[TEST] COD Issue" \
  --label "cod,COD-SIZE" \
  --body "Test cross-cutting attachment"

# 2. Verify issue appears in:
#    - COD Project (#3)
#    - Instruments Service Project (if created)

# 3. Clean up:
gh issue close <issue-number> --repo IggyIkenna/instruments-service
```

## FAQ

### Q: What if I close a COD issue? Does it disappear from both projects?

**A:** Yes! Closing the issue removes it from all projects. GitHub Project Workflows respect issue state.

### Q: Can I manually add an issue to a project without labels?

**A:** Yes, but it won't benefit from automatic cross-cutting attachment. Best practice: Always use appropriate labels
(cod, epic, etc.) and milestones (Wave1, Wave2).

### Q: What if a service has NO CODs or Wave 1 work?

**A:** The filtered views will simply be empty. This is expected and correct.

### Q: How do I see ALL CODs across all services?

**A:** Use COD Project (#3) with filter `label:cod`. It shows CODs from all repos.

### Q: How do I see ONLY CODs for a specific service?

**A:** Use that service's project with "CODs Only" view: `repo:service-name label:cod`

## Related Documentation

- [Service-Level Epic Approach](../SERVICE_LEVEL_EPIC_APPROACH.md)
- [Project Structure Reference](../../12-presentations/PROJECT_STRUCTURE_REFERENCE.md)
- [GitHub Projects v2 Schema](../projects-v2-schema.md)
- [E2E Workflow Unified](../../00-getting-started/E2E_WORKFLOW_UNIFIED.md)

---

**Last Updated:** 2026-02-13  
**Status:** ✅ Active Strategy
