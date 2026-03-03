# Enhanced Batch Fix - Label & State Filtering

## Overview

`enhanced-cleanup-batch-fix.sh` extends `run-cleanup-batch-fix.sh` with label and state filtering to avoid processing
blocked or closed issues.

## Usage

```bash
bash enhanced-cleanup-batch-fix.sh \
  --model auto \
  --state open \
  --require-labels "cleanup" \
  --exclude-labels "blocked,wip" \
  --max-parallel 4 \
  --dry-run
```

## Options

| Option                        | Description                           | Default |
| ----------------------------- | ------------------------------------- | ------- |
| `--model <model>`             | Model to use (required)               | -       |
| `--max-parallel <n>`          | Max parallel agents                   | 5       |
| `--repos <r1,r2>`             | Filter by repos                       | all     |
| `--state <open\|closed\|all>` | Filter by issue state                 | `open`  |
| `--require-labels <l1,l2>`    | Only process issues with these labels | -       |
| `--exclude-labels <l1,l2>`    | Skip issues with these labels         | -       |
| `--dry-run`                   | Show what would be processed          | false   |

## Examples

### 1. Process Only Open Cleanup Issues

```bash
bash enhanced-cleanup-batch-fix.sh \
  --model auto \
  --state open \
  --require-labels "cleanup" \
  --max-parallel 4
```

**Result:** Processes 11 issues, skips 2 closed (#48, #51)

### 2. Process COD-SIZE Issues (Exclude Blocked)

```bash
bash enhanced-cleanup-batch-fix.sh \
  --model auto \
  --state open \
  --require-labels "COD-SIZE" \
  --exclude-labels "blocked" \
  --max-parallel 2
```

**Result:** Processes only unified-trading-services #52 and market-tick-data-handler #54 (skips 4 blocked issues)

### 3. Process Specific Repos Only

```bash
bash enhanced-cleanup-batch-fix.sh \
  --model auto \
  --repos "execution-service,instruments-service" \
  --state open
```

### 4. Dry Run (Preview)

```bash
bash enhanced-cleanup-batch-fix.sh \
  --model auto \
  --require-labels "cleanup" \
  --dry-run
```

**Output:**

```
🔍 Filtering issues...
  State: OPEN
  Require labels: cleanup

  ✅ execution-service #147 - Will process (labels: cod,cleanup)
  ✅ strategy-service #23 - Will process (labels: cod,cleanup)
  ⏭️  unified-trading-services #48 - Skipped (state: CLOSED)
  🔒 instruments-service #59 - Skipped (has 'blocked' label)

📋 Issues to process: 11
```

## Current Issue Status

### Cleanup Issues (cod, cleanup labels)

| Repo                           | Issue | State  | Blocked? |
| ------------------------------ | ----- | ------ | -------- |
| execution-service              | #147  | OPEN   | No       |
| strategy-service               | #23   | OPEN   | No       |
| instruments-service            | #58   | OPEN   | No       |
| unified-trading-services       | #48   | CLOSED | N/A      |
| market-data-processing-service | #46   | OPEN   | No       |
| ml-training-service            | #38   | OPEN   | No       |
| ml-inference-service           | #28   | OPEN   | No       |
| features-delta-one-service     | #34   | OPEN   | No       |
| features-volatility-service    | #25   | OPEN   | No       |
| features-calendar-service      | #37   | OPEN   | No       |
| features-onchain-service       | #27   | OPEN   | No       |
| market-tick-data-handler       | #51   | CLOSED | N/A      |
| unified-trading-deployment-v2  | #126  | OPEN   | No       |

**Ready to process:** 11 issues

### COD-SIZE Issues (cod, COD-SIZE, blocked labels)

| Repo                          | Issue | State | Blocked? |
| ----------------------------- | ----- | ----- | -------- |
| unified-trading-services      | #52   | OPEN  | No ✅    |
| instruments-service           | #59   | OPEN  | Yes 🔒   |
| strategy-service              | #25   | OPEN  | Yes 🔒   |
| execution-service             | #150  | OPEN  | Yes 🔒   |
| unified-trading-deployment-v2 | #127  | OPEN  | Yes 🔒   |
| market-tick-data-handler      | #54   | OPEN  | No ✅    |

**Ready to process:** 2 issues (4 blocked by cleanup issues)

## Integration with GitHub Projects

While this script doesn't directly query GitHub Projects API, you can use labels as project markers:

1. **Tag issues in your project** with custom labels (e.g., `sprint-1`, `priority-high`)
2. **Filter by those labels** using `--require-labels` or `--exclude-labels`

Example:

```bash
bash enhanced-cleanup-batch-fix.sh \
  --model auto \
  --require-labels "sprint-1,P1-high" \
  --max-parallel 4
```

## Why This Matters

**Problem:** Running batch automation on blocked issues wastes resources and creates conflicts.

**Solution:** Label-based filtering ensures:

- ✅ Only process unblocked issues
- ✅ Skip closed issues automatically
- ✅ Respect dependencies (e.g., COD-SIZE waits for cleanup)
- ✅ Coordinate across multiple parallel agents

## Recommended Workflow

1. **Initial Cleanup (First Pass)**

   ```bash
   bash enhanced-cleanup-batch-fix.sh \
     --model auto \
     --require-labels "cleanup" \
     --state open \
     --max-parallel 4
   ```

2. **Monitor PRs** - Wait for cleanup PRs to merge

3. **Unblock COD-SIZE Issues** - Remove `blocked` label once cleanup completes

4. **COD-SIZE Refactoring (Second Pass)**
   ```bash
   bash enhanced-cleanup-batch-fix.sh \
     --model auto \
     --require-labels "COD-SIZE" \
     --exclude-labels "blocked" \
     --max-parallel 2  # Fewer parallel for large refactors
   ```

## See Also

- `run-cleanup-batch-fix.sh` - Base script (no filtering)
- `batch-fix-v2.sh` - Core batch processing logic
- `unified-trading-codex/11-project-management/github-integration/` - GitHub automation docs
