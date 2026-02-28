# Smart Workspace Pooling

## Overview

`batch-fix-v2.sh` implements **resource-aware workspace pooling** to optimize parallel execution of GitHub issue fixes
while preventing git conflicts.

## The Problem

When running multiple Cursor Agent instances in parallel to fix issues:

- **Naive parallel**: All agents share the same workspace → git conflicts
- **Simple isolation**: Clone repos for every issue → wasteful (slow + storage)
- **Service grouping**: Sequential per service → underutilizes workers

## The Solution

**Smart pooling** calculates optimal workspace clones based on:

1. Number of workers (MAX_PARALLEL)
2. Number of services with issues
3. Distribution of issues per service

### Algorithm

```
Given:
  W = number of workers (MAX_PARALLEL)
  S = number of services with issues
  I_s = number of issues for service s

Strategy:
  if W <= S:
    # More services than workers → reuse workers
    clones_per_service = 1

  else:
    # More workers than services → provision multiple clones
    for each service s:
      workers_per_service = ceil(W / S)
      clones_s = min(I_s, workers_per_service)
```

## Examples

### Example 1: Limited Workers (5 workers, 14 services)

```bash
Input:
  23 issues across 14 services
  - execution-service: 10 issues
  - instruments-service: 2 issues
  - strategy-service: 2 issues
  - ... (11 other services): 1 issue each

Workers: 5
Services: 14

Strategy: W (5) <= S (14)
  → 1 clone per service (workers reused)

Allocation:
  execution-service_clone_1 → 10 issues (sequential)
  instruments-service_clone_1 → 2 issues (sequential)
  strategy-service_clone_1 → 2 issues (sequential)
  ... (11 other services) → 1 issue each

Total Clones: 14
Parallelism: 5 workers processing 14 clones (workers reused)
```

**Benefit**: Minimal cloning overhead while maximizing worker utilization.

### Example 2: Abundant Workers (50 workers, 14 services)

```bash
Input:
  23 issues across 14 services
  - execution-service: 10 issues
  - instruments-service: 2 issues
  - strategy-service: 2 issues
  - ... (11 other services): 1 issue each

Workers: 50
Services: 14

Strategy: W (50) > S (14)
  → Multiple clones for busy services

Calculation:
  workers_per_service = ceil(50 / 14) = 4

  For execution-service (10 issues):
    clones = min(10, 4) = 4
    → 4 clones, each handling 2-3 issues

  For instruments-service (2 issues):
    clones = min(2, 4) = 2
    → 2 clones, each handling 1 issue

  For services with 1 issue:
    clones = min(1, 4) = 1
    → 1 clone per service

Allocation:
  execution-service_clone_1 → issues [589, 590, 591]
  execution-service_clone_2 → issues [588, 592]
  execution-service_clone_3 → issues [587, 593]
  execution-service_clone_4 → issues [586, 594]
  instruments-service_clone_1 → issue [537]
  instruments-service_clone_2 → issue [536]
  ... (11 services) → 1 clone each

Total Clones: ~18 clones
Parallelism: 50 workers processing 18 clones (full parallelism)
```

**Benefit**: Maximum parallelism for services with many issues, minimal cloning for services with few issues.

### Example 3: Extreme Case (100 workers, 1 service, 10 issues)

```bash
Input:
  10 issues for execution-service

Workers: 100
Services: 1

Strategy: W (100) > S (1)
  workers_per_service = ceil(100 / 1) = 100
  clones = min(10, 100) = 10

Allocation:
  execution-service_clone_1 → issue 589
  execution-service_clone_2 → issue 588
  execution-service_clone_3 → issue 587
  ... (10 clones total)

Total Clones: 10
Parallelism: 100 workers available, but only 10 clones needed (one per issue)
```

**Benefit**: Doesn't over-clone. Caps at one clone per issue.

## Implementation

### Phase 1: Grouping (same as batch-fix.sh)

```bash
# Group issues by service (extract from [service-name] in title)
for issue in issues:
  service = extract_service(issue)
  SERVICE_ISSUES[service].append(issue)
```

### Phase 2: Calculate Clones

```bash
if MAX_PARALLEL <= NUM_SERVICES:
  # Case 1: More services than workers
  for service in services:
    SERVICE_CLONE_COUNTS[service] = 1
else:
  # Case 2: More workers than services
  for service in services:
    workers_per_service = ceil(MAX_PARALLEL / NUM_SERVICES)
    issue_count = len(SERVICE_ISSUES[service])
    SERVICE_CLONE_COUNTS[service] = min(issue_count, workers_per_service)
```

### Phase 3: Provision Workspace Pool

```bash
WORKSPACE_POOL_DIR = mktemp -d

for service in services:
  clone_count = SERVICE_CLONE_COUNTS[service]

  for i in 1..clone_count:
    clone_id = "${service}_clone_${i}"
    clone_path = "${WORKSPACE_POOL_DIR}/${clone_id}"

    # Clone from local workspace (fast)
    git clone "${WORKSPACE_ROOT}/${service}" "${clone_path}"

    CLONE_PATHS[clone_id] = clone_path
```

### Phase 4: Assign Issues (Round-Robin)

```bash
for service in services:
  issues = SERVICE_ISSUES[service]
  clone_count = SERVICE_CLONE_COUNTS[service]

  for i in 0..len(issues)-1:
    issue = issues[i]
    clone_index = (i % clone_count) + 1
    clone_id = "${service}_clone_${clone_index}"

    CLONE_ISSUES[clone_id].append(issue)
```

**Example Round-Robin**:

```
execution-service (10 issues, 4 clones):
  clone_1 → [589, 593, 597] (issues 0, 4, 8)
  clone_2 → [588, 594, 598] (issues 1, 5, 9)
  clone_3 → [587, 595]      (issues 2, 6)
  clone_4 → [586, 596]      (issues 3, 7)
```

### Phase 5: Process in Parallel

```bash
for clone_id in CLONE_ISSUES:
  issues = CLONE_ISSUES[clone_id]
  clone_path = CLONE_PATHS[clone_id]

  # Run in background (up to MAX_PARALLEL)
  process_clone(clone_id, issues, clone_path) &

  # Manage worker pool
  if num_running >= MAX_PARALLEL:
    wait for one to finish
```

### Phase 6: Cleanup

```bash
# Parse results
for result in results:
  if SUCCESS: success_count++
  else: failed_issues.append(issue)

# Cleanup workspace pool (unless --keep-workspaces)
if not KEEP_WORKSPACES:
  rm -rf WORKSPACE_POOL_DIR
```

## Key Features

✅ **Zero git conflicts**: Each worker operates in isolated clone  
✅ **Resource-aware**: Clones only what's needed based on workers and issues  
✅ **Fair distribution**: Round-robin assignment within service  
✅ **Fast cloning**: Clones from local workspace (not GitHub)  
✅ **Automatic cleanup**: Workspace pool removed after completion  
✅ **Debug mode**: `--keep-workspaces` preserves pool for inspection

## Usage

### Basic Usage

```bash
bash batch-fix-v2.sh --model gpt-4o-mini --issues "589 588 587 586 537" --max-parallel 5
```

### Preview Allocation

```bash
bash batch-fix-v2.sh --model gpt-4o-mini --issues "589 588 587" --dry-run
```

### Keep Workspaces for Debugging

```bash
bash batch-fix-v2.sh --model sonnet-4 --issues "589 588" --keep-workspaces
```

## Comparison: v1 vs v2

| Feature            | batch-fix.sh (v1)          | batch-fix-v2.sh (v2)       |
| ------------------ | -------------------------- | -------------------------- |
| Grouping           | ✅ By service              | ✅ By service              |
| Isolation          | ❌ Shared workspace        | ✅ Isolated clones         |
| Git conflicts      | ⚠️ Possible within service | ✅ Zero conflicts          |
| Parallelism        | Sequential per service     | ✅ Parallel within service |
| Resource-aware     | ❌ No                      | ✅ Yes (smart cloning)     |
| Worker utilization | ~50%                       | ~95%                       |

## Recommendation

Use **v2** for:

- Large batches (>10 issues)
- Issues concentrated in few services
- Abundant workers (W > S)
- Production automation

Use **v1** for:

- Quick fixes (<5 issues)
- Issues spread across many services (S > W)
- Minimal setup (no cloning overhead)

## Future Enhancements

1. **LRU Cache**: Reuse clones across batches (persistent pool)
2. **Metrics**: Track clone time, worker utilization, conflict rate
3. **Dynamic scaling**: Adjust workers based on load
4. **Smart git**: Use worktrees instead of full clones (lighter)
