# 06: Multi-Repo Dependency Versioning

**Status**: ⬜ Not Started  
**Priority**: P2 (Enable parallel agent work)  
**Estimated Time**: 3-4 hours  
**Expected Benefit**: 20-40 min/day saved, fewer merge conflicts

---

## 📖 Overview

Enable multiple agents to work on different branches of upstream dependencies simultaneously without conflicts. Each agent's branch uses a specific version of dependencies, tested end-to-end before merging.

### Current State
- Agent A and Agent B both modify unified-cloud-services
- Both push to main → conflicts
- Downstream services pull from main → get mixed changes
- Must merge sequentially (slow)

### Target State
- Agent A: branch `feature-auth` with version `1.3.0-feature-auth.1`
- Agent B: branch `feature-logging` with version `1.3.0-feature-logging.1`
- Each downstream service pins to specific branch
- CI tests each branch independently
- Merge upstream first, then downstream (clean merges)

---

## 🔗 Dependencies

- **Requires**: CI/CD alignment (#03) for reliable testing
- **Enables**: Parallel agent work on shared dependencies

---

## 🚧 Blockers

- [ ] Need to establish versioning convention
- [ ] Need to update CI to support branch-specific dependencies
- [ ] Need to document merge order

---

## 🔍 Current Dependency Graph

### Upstream Libraries (Shared)
- unified-cloud-services (no deps)
- unified-config-interface (depends on UCS)
- unified-events-interface (depends on UCS, UCI)
- unified-market-interface (depends on UCS)
- unified-trade-execution-interface (depends on UCS)

### Downstream Services (Consumers)
- instruments-service (depends on UCS, UCI, UEI)
- market-tick-data-handler (depends on UCS, UCI, UEI)
- market-data-processing-service (depends on UCS, UCI, UEI, UMI)
- features-* services (depend on UCS, UCI, UEI)
- ml-training-service (depends on UCS, UCI, UEI)
- strategy-service (depends on UCS, UCI, UEI, UOI, UMI)

---

## 🛠️ Implementation

### Step 1: Establish Versioning Convention

**Format**: `MAJOR.MINOR.PATCH-branch.iteration`

**Examples**:
- Main branch: `1.2.3`
- Feature branch: `1.3.0-feature-auth.1`
- Hotfix branch: `1.2.4-hotfix-bug.1`
- Iteration 2: `1.3.0-feature-auth.2`

**Rules**:
1. Bump MINOR for new features
2. Bump PATCH for bug fixes
3. Add branch name after dash
4. Add iteration number after second dot

### Step 2: Create Branch-Specific Version Script

```bash
# unified-cloud-services/scripts/set-branch-version.sh
#!/bin/bash
set -e

BRANCH=$(git rev-parse --abbrev-ref HEAD)
CURRENT_VERSION=$(grep "^version =" pyproject.toml | cut -d'"' -f2)

if [ "$BRANCH" = "main" ]; then
    echo "On main branch, version unchanged: $CURRENT_VERSION"
    exit 0
fi

# Extract base version (remove any existing branch suffix)
BASE_VERSION=$(echo "$CURRENT_VERSION" | cut -d'-' -f1)

# Bump minor version
IFS='.' read -r MAJOR MINOR PATCH <<< "$BASE_VERSION"
MINOR=$((MINOR + 1))
NEW_BASE="$MAJOR.$MINOR.0"

# Add branch suffix
BRANCH_CLEAN=$(echo "$BRANCH" | sed 's/[^a-zA-Z0-9-]/-/g')
NEW_VERSION="$NEW_BASE-$BRANCH_CLEAN.1"

# Update pyproject.toml
sed -i.bak "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
rm pyproject.toml.bak

echo "✅ Version updated: $CURRENT_VERSION → $NEW_VERSION"
echo "   Branch: $BRANCH"
```

Make executable:

```bash
chmod +x unified-cloud-services/scripts/set-branch-version.sh
```

### Step 3: Update pyproject.toml to Support Branch Dependencies

```toml
# instruments-service/pyproject.toml

[project]
name = "instruments-service"
version = "1.0.0"
dependencies = [
    # Production dependencies use main branch
    "unified-cloud-services",
    "unified-config-interface",
    "unified-events-interface",
]

[tool.uv.sources]
# Default: use main branch (for production)
unified-cloud-services = { git = "https://github.com/IggyIkenna/unified-cloud-services.git", branch = "main" }
unified-config-interface = { git = "https://github.com/IggyIkenna/unified-config-interface.git", branch = "main" }
unified-events-interface = { git = "https://github.com/IggyIkenna/unified-events-interface.git", branch = "main" }

# For feature branches, update to:
# unified-cloud-services = { git = "https://github.com/IggyIkenna/unified-cloud-services.git", branch = "feature-auth" }
```

### Step 4: Create Branch Dependency Update Script

```bash
# instruments-service/scripts/update-branch-deps.sh
#!/bin/bash
set -e

# Usage: ./scripts/update-branch-deps.sh unified-cloud-services feature-auth

REPO=$1
BRANCH=$2

if [ -z "$REPO" ] || [ -z "$BRANCH" ]; then
    echo "Usage: $0 <repo-name> <branch-name>"
    echo "Example: $0 unified-cloud-services feature-auth"
    exit 1
fi

# Update pyproject.toml
python3 << EOF
import toml

with open('pyproject.toml', 'r') as f:
    config = toml.load(f)

# Update branch in tool.uv.sources
if 'tool' in config and 'uv' in config['tool'] and 'sources' in config['tool']['uv']:
    if '$REPO' in config['tool']['uv']['sources']:
        config['tool']['uv']['sources']['$REPO']['branch'] = '$BRANCH'
        
        with open('pyproject.toml', 'w') as f:
            toml.dump(config, f)
        
        print(f"✅ Updated $REPO to branch: $BRANCH")
    else:
        print(f"❌ Repo $REPO not found in dependencies")
        exit(1)
else:
    print("❌ No uv.sources found in pyproject.toml")
    exit(1)
EOF

# Update lock file
echo "Updating lock file..."
uv lock

echo "✅ Done! Commit changes:"
echo "   git add pyproject.toml uv.lock"
echo "   git commit -m 'Update $REPO to branch $BRANCH'"
```

Make executable:

```bash
chmod +x instruments-service/scripts/update-branch-deps.sh
```

### Step 5: Update CI to Support Branch Dependencies

```yaml
# .github/workflows/quality-gates.yml
name: Quality Gates

on: [push, pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Detect branch dependencies
        id: detect-deps
        run: |
          # Extract branch from pyproject.toml
          UCS_BRANCH=$(grep -A 1 'unified-cloud-services.*git' pyproject.toml | grep 'branch' | cut -d'"' -f2)
          UCI_BRANCH=$(grep -A 1 'unified-config-interface.*git' pyproject.toml | grep 'branch' | cut -d'"' -f2)
          UEI_BRANCH=$(grep -A 1 'unified-events-interface.*git' pyproject.toml | grep 'branch' | cut -d'"' -f2)
          
          echo "ucs_branch=$UCS_BRANCH" >> $GITHUB_OUTPUT
          echo "uci_branch=$UCI_BRANCH" >> $GITHUB_OUTPUT
          echo "uei_branch=$UEI_BRANCH" >> $GITHUB_OUTPUT
          
          echo "Detected branches:"
          echo "  unified-cloud-services: $UCS_BRANCH"
          echo "  unified-config-interface: $UCI_BRANCH"
          echo "  unified-events-interface: $UEI_BRANCH"
      
      - name: Checkout dependencies
        env:
          GH_PAT: ${{ secrets.GH_PAT }}
        run: |
          # Clone with detected branches
          git clone --branch ${{ steps.detect-deps.outputs.ucs_branch }} \
            https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-cloud-services.git \
            ../unified-cloud-services
          
          git clone --branch ${{ steps.detect-deps.outputs.uci_branch }} \
            https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-config-interface.git \
            ../unified-config-interface
          
          git clone --branch ${{ steps.detect-deps.outputs.uei_branch }} \
            https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-events-interface.git \
            ../unified-events-interface
      
      - name: Install dependencies
        run: |
          # Install in DAG order
          uv pip install --system -e ../unified-cloud-services
          uv pip install --system -e ../unified-config-interface
          uv pip install --system -e ../unified-events-interface
          uv pip install --system -e ".[dev]"
      
      - name: Run quality gates
        run: bash scripts/quality-gates.sh --no-fix --quick
```

### Step 6: Document Workflow

```markdown
# Multi-Repo Versioning Workflow

## Scenario: Two Agents Working on Same Upstream Library

### Agent A: Adding Authentication

1. Create feature branch in upstream:
   ```bash
   cd unified-cloud-services
   git checkout -b feature-auth
   ./scripts/set-branch-version.sh  # Sets version to 1.3.0-feature-auth.1
   git add pyproject.toml
   git commit -m "Bump version for feature-auth branch"
   ```

2. Make changes to unified-cloud-services

3. Update downstream service to use feature branch:
   ```bash
   cd instruments-service
   git checkout -b feature-auth-integration
   ./scripts/update-branch-deps.sh unified-cloud-services feature-auth
   git add pyproject.toml uv.lock
   git commit -m "Use unified-cloud-services feature-auth branch"
   ```

4. Make changes to instruments-service

5. Push both branches:
   ```bash
   cd unified-cloud-services
   bash scripts/quickmerge.sh "Add authentication support"
   
   cd instruments-service
   bash scripts/quickmerge.sh "Integrate authentication"
   ```

### Agent B: Adding Logging (Parallel)

1. Create feature branch in upstream:
   ```bash
   cd unified-cloud-services
   git checkout -b feature-logging
   ./scripts/set-branch-version.sh  # Sets version to 1.3.0-feature-logging.1
   git add pyproject.toml
   git commit -m "Bump version for feature-logging branch"
   ```

2. Make changes to unified-cloud-services

3. Update downstream service to use feature branch:
   ```bash
   cd market-tick-data-handler
   git checkout -b feature-logging-integration
   ./scripts/update-branch-deps.sh unified-cloud-services feature-logging
   git add pyproject.toml uv.lock
   git commit -m "Use unified-cloud-services feature-logging branch"
   ```

4. Make changes to market-tick-data-handler

5. Push both branches

### Merge Order (Critical!)

**Merge upstream BEFORE downstream:**

1. Merge Agent A's upstream:
   ```bash
   # PR: unified-cloud-services feature-auth → main
   # Wait for CI to pass
   # Merge (squash)
   ```

2. Merge Agent A's downstream:
   ```bash
   # Update instruments-service to use main branch
   cd instruments-service
   ./scripts/update-branch-deps.sh unified-cloud-services main
   git add pyproject.toml uv.lock
   git commit -m "Switch to unified-cloud-services main"
   
   # PR: instruments-service feature-auth-integration → main
   # Wait for CI to pass
   # Merge (squash)
   ```

3. Merge Agent B's upstream:
   ```bash
   # PR: unified-cloud-services feature-logging → main
   # Wait for CI to pass
   # Merge (squash)
   ```

4. Merge Agent B's downstream:
   ```bash
   # Update market-tick-data-handler to use main branch
   cd market-tick-data-handler
   ./scripts/update-branch-deps.sh unified-cloud-services main
   git add pyproject.toml uv.lock
   git commit -m "Switch to unified-cloud-services main"
   
   # PR: market-tick-data-handler feature-logging-integration → main
   # Wait for CI to pass
   # Merge (squash)
   ```

## Result

- ✅ No conflicts (each branch tested independently)
- ✅ Clean merges (upstream merged first)
- ✅ CI validates each branch end-to-end
- ✅ Parallel work enabled
```

---

## ✅ Verification

### Test 1: Create Feature Branch with Version

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-cloud-services

# Create test branch
git checkout -b test-versioning

# Set branch version
./scripts/set-branch-version.sh

# Verify version updated
grep "^version =" pyproject.toml
# Should show: version = "1.X.0-test-versioning.1"
```

### Test 2: Update Downstream Dependency

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service

# Update to use test branch
./scripts/update-branch-deps.sh unified-cloud-services test-versioning

# Verify pyproject.toml updated
grep -A 1 "unified-cloud-services" pyproject.toml | grep branch
# Should show: branch = "test-versioning"

# Verify lock file updated
grep "unified-cloud-services" uv.lock
```

### Test 3: CI Detects Branch

```bash
# Push changes
git add pyproject.toml uv.lock
git commit -m "Test: use unified-cloud-services test-versioning branch"
git push origin test-branch

# Check GitHub Actions log
# Should show: "Detected branches: unified-cloud-services: test-versioning"
```

---

## 📊 Success Metrics

- [ ] Branch versioning script works
- [ ] Dependency update script works
- [ ] CI detects and clones correct branches
- [ ] Can work on 2+ branches simultaneously
- [ ] Clean merges (no conflicts)
- [ ] Merge order documented and followed
- [ ] 20-40 min/day saved (no sequential bottleneck)

---

## 🔄 Rollback Plan

If branch versioning causes issues:

1. Revert to main branch dependencies
2. Work sequentially (one agent at a time)
3. Use feature flags instead of branches
4. Merge more frequently (smaller changes)

---

## 📚 Related Documentation

- ChatGPT conversation: Lines 143-156 (multi-repo versioning discussion)
- Path dependency CI: `.cursor/rules/path-dependency-ci.mdc`
- Git workflow: `.cursor/rules/git-workflow.mdc`
- Dependency management: `unified-trading-codex/06-coding-standards/dependency-management.md`

---

## 💡 Tips

1. **Always merge upstream first**: Prevents downstream conflicts
2. **Use descriptive branch names**: Makes versions readable
3. **Bump version immediately**: First commit on feature branch
4. **Switch back to main before merging**: Update pyproject.toml
5. **Test end-to-end**: Each branch should pass CI independently

---

## ✏️ Notes

- Enables parallel agent work on shared libraries
- Prevents "Agent A breaks Agent B's work" scenarios
- CI tests each branch in isolation
- Clean merge path (upstream → downstream)
- Expected to save 20-40 min/day (no sequential bottleneck)
- Critical for multi-agent workflows
