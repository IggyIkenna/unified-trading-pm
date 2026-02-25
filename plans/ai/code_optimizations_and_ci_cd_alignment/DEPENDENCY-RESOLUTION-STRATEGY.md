# Dependency Resolution Strategy - Topological Sort for Cascade

## The Problem: DAG, Not Tree

Dependencies form a **Directed Acyclic Graph (DAG)**, not a simple tree:

```
instruments-service depends on:
  ├─> api-contracts (level 0)
  ├─> unified-config-interface (level 0)
  ├─> unified-events-interface (level 0)
  ├─> unified-domain-services (level 2)
  │   ├─> unified-cloud-services (level 1)
  │   ├─> unified-config-interface (level 0) ← SHARED
  │   └─> unified-events-interface (level 0) ← SHARED
  └─> unified-market-interface (level 3)
      ├─> unified-domain-services (level 2) ← SHARED
      └─> unified-config-interface (level 0) ← SHARED
```

**Key insight**: Multiple repos share the same dependencies (config, events) → We need topological sort, not simple tree traversal.

---

## Solution: Kahn's Algorithm (Topological Sort)

### Algorithm

```python
def topological_sort(dependency_matrix):
    """
    Returns list of repo lists, where each inner list contains repos
    that can be processed in parallel (same level).
    
    Example: [
        ["api-contracts", "unified-config-interface", "unified-events-interface"],  # Level 0
        ["unified-cloud-services"],  # Level 1
        ["unified-domain-services"],  # Level 2
        ["unified-market-interface"],  # Level 3
        ["instruments-service"]  # Level 5
    ]
    """
    # 1. Build in-degree map (how many deps each repo has)
    in_degree = {}
    graph = {}
    
    for repo, data in dependency_matrix.items():
        in_degree[repo] = len(data["dependencies"])
        graph[repo] = [dep["name"] for dep in data["dependencies"]]
    
    # 2. Find all repos with no dependencies (level 0)
    queue = [repo for repo, degree in in_degree.items() if degree == 0]
    result = []
    
    # 3. Process level by level
    while queue:
        current_level = queue.copy()  # All repos at this level (can run in parallel)
        result.append(current_level)
        queue = []
        
        # Process each repo at this level
        for repo in current_level:
            # Find repos that depend on this one
            for dependent_repo, deps in graph.items():
                if repo in deps:
                    in_degree[dependent_repo] -= 1
                    if in_degree[dependent_repo] == 0:
                        queue.append(dependent_repo)
    
    return result
```

### For instruments-service dependency chain:

**Level 0** (no dependencies - parallel):
- `api-contracts`
- `unified-config-interface`
- `unified-events-interface`

**Level 1** (depends only on level 0):
- `unified-cloud-services` (depends on: domain, but circular → runtime only)

**Level 2** (depends on level 0-1):
- `unified-domain-services` (depends on: cloud, config, events)

**Level 3** (depends on level 0-2):
- `unified-market-interface` (depends on: domain, config)

**Level 5** (depends on all above):
- `instruments-service`

---

## Cascade Execution Strategy

### Stage 1: Detect Diffs (Current - Works ✅)

```bash
# In instruments-service quickmerge
for dep in $(jq -r '.dependencies[].name' .dependency-matrix.json); do
    cd "$WORKSPACE_ROOT/$dep"
    if ! git diff origin/main --quiet; then
        REPOS_WITH_DIFF+=("$dep")
    fi
done
```

**Result**: `["api-contracts", "unified-config-interface", "unified-events-interface", "unified-domain-services", "unified-market-interface"]`

---

### Stage 2: Build Global Dependency Graph (NEW - To Implement)

```bash
# Read all .dependency-matrix.json files in workspace
build_global_graph() {
    local workspace_root="$1"
    local temp_graph="/tmp/cascade-dep-graph.json"
    
    echo "{}" > "$temp_graph"
    
    # Scan all repos for .dependency-matrix.json
    for repo_dir in "$workspace_root"/*/; do
        if [ -f "$repo_dir/.dependency-matrix.json" ]; then
            repo_name=$(basename "$repo_dir")
            deps=$(jq -c ".dependencies" "$repo_dir/.dependency-matrix.json")
            
            # Merge into global graph
            jq --arg repo "$repo_name" --argjson deps "$deps" \
               '.[$repo] = $deps' "$temp_graph" > "$temp_graph.tmp"
            mv "$temp_graph.tmp" "$temp_graph"
        fi
    done
    
    echo "$temp_graph"
}
```

---

### Stage 3: Topological Sort (NEW - To Implement)

```bash
topological_sort() {
    local graph_file="$1"
    local repos_with_diff="$2"  # JSON array
    
    # Python script to do topological sort
    python3 <<EOF
import json
from collections import defaultdict, deque

with open("$graph_file") as f:
    graph = json.load(f)

repos_with_diff = json.loads('$repos_with_diff')

# Build in-degree and adjacency
in_degree = defaultdict(int)
adjacency = defaultdict(list)

for repo, deps in graph.items():
    if repo not in repos_with_diff:
        continue
    for dep in deps:
        dep_name = dep["name"]
        if dep_name in repos_with_diff:
            in_degree[repo] += 1
            adjacency[dep_name].append(repo)

# Kahn's algorithm
queue = deque([r for r in repos_with_diff if in_degree[r] == 0])
levels = []

while queue:
    current_level = list(queue)
    levels.append(current_level)
    queue.clear()
    
    for repo in current_level:
        for dependent in adjacency[repo]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

# Output as JSON
print(json.dumps(levels))
EOF
}
```

**Output**:
```json
[
  ["api-contracts", "unified-config-interface", "unified-events-interface"],
  ["unified-cloud-services"],
  ["unified-domain-services"],
  ["unified-market-interface"]
]
```

---

### Stage 4: Cascade Quickmerge (NEW - To Implement)

```bash
cascade_quickmerge() {
    local levels="$1"  # JSON array of arrays
    local dep_branch="$2"
    
    echo "Cascading quickmerge across $(echo "$levels" | jq 'length') levels..."
    
    level_count=$(echo "$levels" | jq 'length')
    
    for ((i=0; i<level_count; i++)); do
        level_repos=$(echo "$levels" | jq -r ".[$i][]")
        
        echo ""
        echo "=========================================="
        echo "CASCADE LEVEL $i"
        echo "=========================================="
        
        # Process all repos at this level in parallel
        pids=()
        for repo in $level_repos; do
            (
                cd "$WORKSPACE_ROOT/$repo"
                echo "[$repo] Starting quickmerge @ $dep_branch"
                bash scripts/quickmerge.sh "cascade: $dep_branch" --dep-branch "$dep_branch" 2>&1 | \
                    tee "/tmp/cascade-$repo.log"
                echo "[$repo] Quickmerge complete"
            ) &
            pids+=($!)
        done
        
        # Wait for all repos at this level to complete
        for pid in "${pids[@]}"; do
            wait "$pid" || {
                echo "❌ Cascade failed at level $i"
                exit 1
            }
        done
        
        echo "✅ Level $i complete"
    done
    
    echo ""
    echo "✅ All dependency levels cascaded successfully"
}
```

---

## Race Conditions & Edge Cases

### 1. Concurrent Quickmerge at Same Level ✅ SAFE

**Scenario**: `api-contracts`, `unified-config-interface`, `unified-events-interface` all quickmerge simultaneously.

**Safe because**:
- Each repo creates its own branch (`cascade-test-2024`)
- Each repo pushes to its own remote
- Each repo creates its own PR
- No shared state between repos

**Parallel execution** is actually IDEAL here - saves time!

---

### 2. Circular Dependencies (UCS ↔ UDS) ✅ HANDLED

**Problem**: unified-cloud-services imports from unified-domain-services, and vice versa.

**Solution**: Runtime installation only
- Docker has tools only (ruff, pytest, basedpyright)
- Dependencies installed at runtime from workspace paths
- Stage 1 validation ensures committed before cascading

**Order**: UCS before UDS (UCS is lower level, provides cloud primitives)

---

### 3. Shared Dependencies ✅ OPTIMAL

**Scenario**: Both `unified-domain-services` and `unified-market-interface` depend on `unified-config-interface`.

**Topological sort ensures**:
- `unified-config-interface` quickmerges FIRST (level 0)
- Then `unified-domain-services` (level 2) - sees config already on branch
- Then `unified-market-interface` (level 3) - sees BOTH config and domain on branch

**No race condition** - proper ordering guaranteed!

---

### 4. PR Creation Timing ✅ SAFE

**Scenario**: Does GitHub Actions for level 0 repos start before level 1 repos finish?

**Yes, but safe**:
- Level 0 repos create PRs immediately after quickmerge
- GitHub Actions runs quality gates with dependencies from workspace
- Each level waits for previous level to complete before starting
- Auto-merge waits for CI to pass

**Worst case**: GitHub Actions re-runs if dependency changes (that's fine)

---

## Implementation Status

### ✅ Completed
- Stage 1: Differential detection (working in current quickmerge)
- Dependency matrices created for instruments-service chain
- Manual cascade validation (instruments → UMI → UDS → UCS works)

### 🚧 To Implement
- **Stage 2**: Global dependency graph builder
- **Stage 3**: Topological sort algorithm
- **Stage 4**: Parallel cascade execution

### 📝 To Document
- Codex: Dependency resolution strategy
- Cursor rules: How to use `--dep-branch` with cascade
- Service READMEs: Reference canonical dependency matrix

---

## Success Validation

### Test Case: instruments-service

**Command**:
```bash
cd instruments-service
bash scripts/quickmerge.sh "test: cascade" --dep-branch "my-feature"
```

**Expected cascade order**:
1. **Parallel** (level 0): api-contracts, config, events
2. **Serial** (level 1): unified-cloud-services
3. **Serial** (level 2): unified-domain-services
4. **Serial** (level 3): unified-market-interface
5. **Serial** (level 5): instruments-service

**Total time** (estimated):
- Level 0: ~2 min (parallel, 3 repos × 2 min each = 2 min wall time)
- Level 1: ~2 min (serial, UCS)
- Level 2: ~2 min (serial, UDS)
- Level 3: ~2 min (serial, UMI)
- Level 5: ~3 min (serial, instruments-service - largest repo)

**Total: ~11 minutes** for 5-level cascade (vs ~30+ min if all serial)

---

## References

- **Canonical Dependency Matrix**: `.cursor/plans/code_optimizations_and_ci_cd_alignment/DEPENDENCY-MATRIX-CANONICAL.json`
- **Master CI/CD Plan**: `.cursor/plans/code_optimizations_and_ci_cd_alignment/00-MASTER-CICD-PLAN.md`
- **Topological Sort**: https://en.wikipedia.org/wiki/Topological_sorting (Kahn's algorithm)
