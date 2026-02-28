# GitHub Projects Board Setup Guide

This guide walks through setting up a GitHub Projects v2 board with all required custom fields for the unified trading
system workflow.

## Prerequisites

- GitHub account with admin access to the target organization/user
- `gh` CLI installed and authenticated with project scopes:

```bash
gh auth refresh --hostname github.com -s read:project -s project
```

## Option 1: Manual Setup (Recommended for First-Time Setup)

### Step 1: Create the Project

1. Navigate to https://github.com/users/YOUR_USERNAME/projects (or organization projects page)
2. Click "New project"
3. Choose "Board" template
4. Name it: "Unified Trading System - Development Board"
5. Click "Create"

### Step 2: Add Custom Fields

Navigate to your project board → Settings (top right) → Custom fields

Add the following fields:

#### 1. Status (Single select)

- **Type**: Single select
- **Options**:
  - Todo (default)
  - In Progress
  - Done
  - Blocked

#### 2. Priority (Single select)

- **Type**: Single select
- **Options**:
  - P0-critical
  - P1-high
  - P2-medium
  - P3-low

#### 3. Lane (Single select)

- **Type**: Single select
- **Options**:
  - audit-remediation
  - capability-request

#### 4. Owner Default (Single select)

- **Type**: Single select
- **Options**:
  - Ikenna
  - Harsh
  - Femi
  - Unassigned

#### 5. Readiness Tier (Single select)

- **Type**: Single select
- **Options**:
  - smoke-tested
  - scale-tested
  - audit-ready
  - production-ready

#### 6. Commercial Stage (Single select)

- **Type**: Single select
- **Options**:
  - signal-candidate
  - strategy-ready
  - client-deployable
  - production-live

#### 7. Target Cloud (Single select)

- **Type**: Single select
- **Options**:
  - GCP
  - AWS
  - Dual

#### 8. Complexity (Single select) - Optional

- **Type**: Single select
- **Options**:
  - LOW
  - MEDIUM
  - HIGH
  - CRITICAL

#### 9. Risk (Single select) - Optional

- **Type**: Single select
- **Options**:
  - TRIVIAL
  - MODERATE
  - HIGH
  - CRITICAL

### Step 3: Configure Views

Create the following views for different perspectives:

#### View 1: By Status (Default)

- Group by: Status
- Sort by: Priority (descending)

#### View 2: By Priority

- Group by: Priority
- Sort by: Created date (descending)

#### View 3: By Lane

- Group by: Lane
- Sort by: Status

#### View 4: By Service

- Group by: Labels (filter: service/\*)
- Sort by: Priority

#### View 5: Readiness Dashboard

- Group by: Readiness Tier
- Filter: Show only items with readiness tier set
- Sort by: Commercial Stage

### Step 4: Set Up Automation (Optional)

Projects v2 supports workflows. Consider:

1. **Auto-archive completed items** after 30 days
2. **Auto-set status** to "In Progress" when issue is assigned
3. **Auto-set status** to "Done" when issue is closed

## Option 2: GraphQL API Setup (For Automation)

Use the provided script to set up fields programmatically.

### Create Setup Script

Save this as `setup-project-fields.sh`:

```bash
#!/bin/bash
set -e

# Configuration
PROJECT_NUMBER=$1
OWNER=$2

if [ -z "$PROJECT_NUMBER" ] || [ -z "$OWNER" ]; then
  echo "Usage: $0 PROJECT_NUMBER OWNER"
  echo "Example: $0 1 IggyIkenna"
  exit 1
fi

echo "Setting up project fields for Project #$PROJECT_NUMBER owned by $OWNER..."

# Get project ID
PROJECT_ID=$(gh project view $PROJECT_NUMBER --owner $OWNER --format json --jq '.id')

if [ -z "$PROJECT_ID" ]; then
  echo "Error: Could not find project #$PROJECT_NUMBER"
  exit 1
fi

echo "Project ID: $PROJECT_ID"

# Function to create single-select field
create_field() {
  local field_name=$1
  shift
  local options=("$@")

  echo "Creating field: $field_name"

  # Build options JSON
  options_json="["
  for option in "${options[@]}"; do
    options_json="$options_json{\"name\": \"$option\"},"
  done
  options_json="${options_json%,}]"  # Remove trailing comma

  # Create field via GraphQL
  gh api graphql -f query="
    mutation {
      createProjectV2Field(input: {
        projectId: \"$PROJECT_ID\"
        dataType: SINGLE_SELECT
        name: \"$field_name\"
        singleSelectOptions: $options_json
      }) {
        projectV2Field {
          ... on ProjectV2SingleSelectField {
            id
            name
          }
        }
      }
    }
  "
}

# Create Status field
create_field "Status" "Todo" "In Progress" "Done" "Blocked"

# Create Priority field
create_field "Priority" "P0-critical" "P1-high" "P2-medium" "P3-low"

# Create Lane field
create_field "Lane" "audit-remediation" "capability-request"

# Create Owner Default field
create_field "Owner Default" "Ikenna" "Harsh" "Femi" "Unassigned"

# Create Readiness Tier field
create_field "Readiness Tier" "smoke-tested" "scale-tested" "audit-ready" "production-ready"

# Create Commercial Stage field
create_field "Commercial Stage" "signal-candidate" "strategy-ready" "client-deployable" "production-live"

# Create Target Cloud field
create_field "Target Cloud" "GCP" "AWS" "Dual"

# Create Complexity field (optional)
create_field "Complexity" "LOW" "MEDIUM" "HIGH" "CRITICAL"

# Create Risk field (optional)
create_field "Risk" "TRIVIAL" "MODERATE" "HIGH" "CRITICAL"

echo "✓ Project fields created successfully!"
```

### Run the Script

```bash
chmod +x setup-project-fields.sh
./setup-project-fields.sh PROJECT_NUMBER OWNER

# Example:
./setup-project-fields.sh 1 IggyIkenna
```

## Option 3: Verify Existing Project

If project already exists, verify it has all required fields:

```bash
gh project view 1 --owner IggyIkenna --format json | jq '.fields[] | {name: .name, type: .type}'
```

Expected output should include all custom fields listed above.

## Adding Issues to Project

### Manually

From issue page → Projects (right sidebar) → Add to project

### Bulk Add

```bash
# Add all issues with specific label
gh issue list --label "feature" --state open --limit 100 --json url --jq '.[].url' | \
  while read url; do
    gh project item-add PROJECT_NUMBER --owner OWNER --url "$url" 2>/dev/null || true
  done
```

### Automated (via sync-project-items.py)

The sync-project-items.py script can automatically add generated issues:

```bash
python sync-project-items.py \
  --owner IggyIkenna \
  --repo IggyIkenna/unified-trading-deployment-v2 \
  --project-title "Unified Trading System - Development Board" \
  --plan-json feature-cards-plan.json
```

## Setting Field Values

### Via UI

1. Click on any issue card in the project board
2. Click on the field dropdown
3. Select the appropriate value

### Via CLI

```bash
# Set status to "In Progress"
gh project item-edit --id ITEM_ID --field-id FIELD_ID --project-id PROJECT_ID --single-select-option-id OPTION_ID
```

### Bulk Operations

For bulk updates, create a script or use GitHub Actions workflows.

## Project URL Structure

Once created, your project will be available at:

```
https://github.com/users/YOUR_USERNAME/projects/PROJECT_NUMBER
```

Example:

```
https://github.com/users/IggyIkenna/projects/1
```

## Filtering and Queries

Use project filters to create custom views:

### By Priority and Status

```
priority:P0-critical status:"In Progress"
```

### By Lane

```
lane:audit-remediation
```

### By Readiness

```
readiness-tier:production-ready
```

### By Service

Use label filters:

```
label:service/instruments
```

## Integration with Workflow

### Issue Markers

All issues created by sync scripts include markers in their body:

```markdown
**Markers for Duplication Prevention:**

- task-ref: epic-1-task-3
- regeneration-count: 0
- completion-status: in-progress
- last-updated: 2026-02-12T10:30:00Z
```

### Workflow Integration Points

1. **Issue Creation**: sync scripts → GitHub Issues → Auto-add to project
2. **Agent Pickup**: Agent filters project board → Picks task → Sets status "In Progress"
3. **Agent Completion**: Agent completes task → Quickmerge → Auto-close (or UAT)
4. **UAT Required**: Status set to "Blocked" → Human reviews → Human closes
5. **Metrics**: Export project data for tracking (see metrics setup doc)

## Troubleshooting

### Missing Scopes Error

```
gh auth refresh --hostname github.com -s read:project -s project
```

### Cannot Create Fields

Ensure you have admin permissions on the project.

### Project Not Found

Verify project number and owner:

```bash
gh project list --owner IggyIkenna
```

### Fields Not Showing

Refresh the project page or clear browser cache.

## Related Documentation

- [projects-v2-schema.md](./projects-v2-schema.md) - Complete field schema definition
- [workflow-visuals.md](../../12-agent-workflow/workflow-visuals.md) - Diagram 11: Milestone tracking using project
  fields
- [workflow-design-decisions.md](../../12-agent-workflow/workflow-design-decisions.md) - Design decisions for workflow
  system
- [GitHub Projects v2 Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)

## Success Metrics

After setup, track:

- **Field completion rate**: % of issues with all required fields set
- **View usage**: Which views are most commonly used
- **Automation effectiveness**: % of status transitions that are automated
- **Data quality**: % of issues with accurate readiness tier and commercial stage

Target metrics:

- Field completion rate: 90%+
- Automated status transitions: 70%+
- Data quality: 95%+
