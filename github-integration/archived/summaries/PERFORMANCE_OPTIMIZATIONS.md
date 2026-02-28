# Performance Optimizations: Diff Checker

**Date:** 2026-02-13  
**Status:** ✅ Complete

## Problem

The original `run-diff-checker.py` was extremely slow:

- **Duplicate detection**: Made 1,209 individual API calls (one per gap) = ~5-10 minutes
- **Issue creation**: Sequential (one after another) = ~20 minutes for 1,000+ issues
- **Total time**: ~25-30 minutes for a full run

This made dry-run impractical and real runs painfully slow.

## Solution: Batch + Parallel

### Optimization 1: Batch Fetch Existing Issues

**Before:**

```python
# Check each gap individually (1,209 API calls)
for gap in all_gaps:
    result = subprocess.run(["gh", "issue", "list", "--search", f"{gap.gap_id}"])
    # Process result...
```

**After:**

```python
# Fetch ALL issues once (1 API call)
result = subprocess.run(["gh", "issue", "list", "--limit", "1000"])
issues = json.loads(result.stdout)

# Build in-memory index
gap_id_to_issue = {}
for issue in issues:
    match = re.search(r'gap-id:\s*(\S+)', issue["body"])
    if match:
        gap_id_to_issue[match.group(1)] = issue["number"]

# Fast lookups (no API calls)
for gap in all_gaps:
    if gap.gap_id in gap_id_to_issue:
        # Already exists...
```

**Result:**

- API calls: **1,209 → 1** (99.9% reduction)
- Time: **5-10 minutes → 9 seconds** (40x faster)

### Optimization 2: Parallel Issue Creation

**Before:**

```python
# Sequential: Create one issue at a time
for gap in gaps_to_create:
    result = create_github_issue(gap)  # Wait for each to complete
    # Process result...
```

**After:**

```python
# Parallel: Create 10 issues simultaneously
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_gap = {
        executor.submit(create_github_issue, gap): gap
        for gap in gaps_to_create
    }

    for future in as_completed(future_to_gap):
        result = future.result()
        # Process result...
```

**Result:**

- Time per issue: **~1 second** (GitHub API latency)
- Sequential: 1,000 issues × 1 sec = **~17 minutes**
- Parallel (10 workers): 1,000 issues ÷ 10 × 1 sec = **~2 minutes** (8.5x faster)

## Overall Performance

| Operation                    | Before        | After       | Speedup         |
| ---------------------------- | ------------- | ----------- | --------------- |
| Duplicate detection          | 5-10 min      | 9 sec       | **40x faster**  |
| Issue creation (1000 issues) | 17 min        | 2 min       | **8.5x faster** |
| **Total (dry-run)**          | **5-10 min**  | **9 sec**   | **40x faster**  |
| **Total (real run)**         | **25-30 min** | **2-3 min** | **10x faster**  |

## Usage

### Dry-Run (Fast Preview)

```bash
cd unified-trading-codex/11-project-management/github-integration
python run-diff-checker.py --repo IggyIkenna/unified-trading-codex --dry-run

# Output in ~9 seconds:
#   Total gaps found: 1209
#   Issues that would be created: 1137 (dry-run, not actually created)
#   Issues skipped (already exist): 72
```

### Real Run (Parallel Creation)

```bash
# Default: 10 parallel workers
python run-diff-checker.py --repo IggyIkenna/unified-trading-codex

# Higher parallelism for faster creation (be mindful of rate limits)
python run-diff-checker.py --repo IggyIkenna/unified-trading-codex --max-workers 20
```

**Note:** GitHub API has rate limits:

- Authenticated: 5,000 requests/hour
- With 10 workers creating 1,000 issues: ~1,000 requests in ~2 minutes (well within limits)
- With 20 workers: ~1 minute (still safe)

## Technical Details

### Batch Fetch Algorithm

1. **Fetch all open issues** (up to 1,000 limit):

   ```bash
   gh issue list --repo OWNER/REPO --state open --limit 1000 --json number,body
   ```

2. **Parse gap-id markers** from issue bodies:

   ```
   - gap-id: COD-SIZE-execution-service-algorithms
   ```

3. **Build index** in memory:

   ```python
   {"COD-SIZE-execution-service-algorithms": "726", ...}
   ```

4. **Lookup** is O(1) dictionary access (instant)

### Parallel Creation Algorithm

1. **Separate** gaps into "already exist" vs "to create"
2. **Submit** all creation tasks to ThreadPoolExecutor
3. **Process** results as they complete (progress tracking)
4. **Aggregate** final statistics

### Thread Safety

- Each `gh issue create` call is independent (no shared state)
- ThreadPoolExecutor handles concurrency safely
- GitHub API is designed for concurrent access

## Comparison to Other Approaches

### Approach 1: GraphQL Batch Mutations

```graphql
mutation CreateMultipleIssues {
  issue1: createIssue(input: {...}) { ... }
  issue2: createIssue(input: {...}) { ... }
  issue3: createIssue(input: {...}) { ... }
}
```

**Pros:**

- Single HTTP request

**Cons:**

- Must construct entire query upfront (complex for 1,000+ issues)
- GitHub has payload size limits
- Not supported by `gh` CLI (would need raw GraphQL client)
- Still processes each mutation individually server-side

**Verdict:** Not worth the complexity for this use case.

### Approach 2: GitHub Actions Bulk Creation

Use GitHub Actions to create issues in parallel.

**Pros:**

- Runs in GitHub's infrastructure

**Cons:**

- Adds complexity
- Still limited by API rate limits
- Harder to debug
- Our ThreadPoolExecutor approach is simpler and just as fast

**Verdict:** Current solution is better.

## Future Optimizations

If we ever exceed 1,000 open issues:

1. **Pagination**: Fetch issues in multiple batches
2. **Incremental checking**: Only check files modified since last run
3. **Caching**: Store gap-id index in file between runs

Current implementation handles up to 1,000 open issues efficiently, which should cover our needs.

## Rate Limits

GitHub API limits (authenticated):

- **REST API**: 5,000 requests/hour
- **GraphQL**: 5,000 points/hour

Our usage:

- Fetch existing issues: 1 request
- Create 1,000 issues with 10 workers: ~1,000 requests in ~2 minutes
- **Total**: ~1,000 requests/run (well under limit)

Safe to run multiple times per hour if needed.
