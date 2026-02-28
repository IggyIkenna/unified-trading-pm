# GitHub Actions Workflow Syntax Error: Duplicate `run:` Keys

## The Problem

**Error Message:**

```
Invalid workflow file: .github/workflows/quality-gates.yml#L1
(Line: X, Col: 9): There's not enough info to determine what you meant...
(Line: Y, Col: 9): 'run' is already defined
```

**Root Cause:** An agent generated workflows with **two `run:` blocks under a single step**, which is invalid YAML:

```yaml
# ❌ INVALID - Single step with duplicate run: keys
- name: Install ripgrep
  run: sudo apt-get install -y ripgrep

  run: |  # ← DUPLICATE! Not allowed
    pip install uv
    uv pip install ...
```

GitHub Actions steps can only have **ONE** `run:` block per step.

---

## How This Happened

1. An agent (likely during initial repo setup) created `.github/workflows/quality-gates.yml`
2. The agent intended to create two separate steps but mistakenly:
   - Created an empty "Install dependencies" step
   - Added the dependency installation commands to "Install ripgrep" step as a duplicate `run:`
3. This error propagated to **12 repos** across the workspace

---

## The Fix

**Correct Pattern:**

```yaml
# ✅ VALID - Two separate steps
- name: Install ripgrep (required for codex checks)
  run: sudo apt-get update && sudo apt-get install -y ripgrep

- name: Install dependencies
  run: |
    pip install uv
    uv pip install --system -e deps/unified-trading-services
    uv pip install --system -e ".[dev]"
```

**Automated Fix:**

```bash
cd unified-trading-codex/11-project-management/github-integration/scripts/automation
bash fix-all-workflows.sh  # Fixes all repos
```

---

## Prevention: Agent Guidelines

### 1. Workflow Validation Check

**Add to quality gates:**

```bash
# In scripts/quality-gates.sh or as a separate check
if [ -f ".github/workflows/quality-gates.yml" ]; then
  echo "🔍 Validating workflow syntax..."

  # Check for duplicate run: keys in a single step
  if grep -Pzo '- name:[^\n]*\n\s+run:[^\n]*\n\n\s+run:' .github/workflows/quality-gates.yml; then
    echo "❌ ERROR: Workflow has duplicate run: keys in a single step"
    echo "   Each step can only have ONE run: block"
    exit 1
  fi

  echo "✅ Workflow syntax OK"
fi
```

### 2. Agent Prompt Rules

**Add to `.cursorrules` or codex:**

````markdown
## GitHub Actions Workflow Rules

When creating or modifying `.github/workflows/*.yml` files:

1. **One `run:` per step**: A step can only have ONE `run:` block
2. **Separate steps for separate tasks**: If you need multiple commands, either:
   - Use a multi-line `run: |` block, OR
   - Create separate steps with `- name:`
3. **Validate before committing**:
   ```bash
   # Check for duplicate run: keys
   grep -Pzo '- name:[^\n]*\n\s+run:[^\n]*\n\n\s+run:' .github/workflows/quality-gates.yml && echo "❌ INVALID" || echo "✅ OK"
   ```
````

### Invalid Example:

```yaml
- name: Install tools
  run: sudo apt-get install tool1

  run: |  # ❌ ERROR: duplicate run:
    pip install package1
```

### Valid Examples:

```yaml
# Option 1: Multi-line run: block
- name: Install tools
  run: |
    sudo apt-get install tool1
    pip install package1

# Option 2: Separate steps
- name: Install system tool
  run: sudo apt-get install tool1

- name: Install Python packages
  run: pip install package1
```

````

### 3. Template Workflow

**Provide a reference template** in codex:

```yaml
# unified-trading-codex/11-project-management/github-integration/templates/quality-gates.yml
name: Quality Gates

on:
  pull_request:
    branches: [ main ]

jobs:
  quality-gates:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Clone dependencies
        run: |
          git clone https://github.com/IggyIkenna/unified-trading-services.git deps/unified-trading-services

      - name: Install ripgrep (required for codex checks)
        run: sudo apt-get update && sudo apt-get install -y ripgrep

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install --system -e deps/unified-trading-services
          uv pip install --system -e ".[dev]"

      - name: Lint and format check
        run: |
          ruff check --fix src/ tests/
          ruff format src/ tests/
          git diff --exit-code

      - name: Run tests
        run: pytest tests/ --cov=src/ --cov-report=term-missing
````

**Agent instruction:**

> When creating a workflow, use
> `unified-trading-codex/11-project-management/github-integration/templates/quality-gates.yml` as the base template.

---

## Detection

**Check if your repo has this issue:**

```bash
cd <repo>
if grep -A 5 "name: Install ripgrep" .github/workflows/quality-gates.yml | grep -c "run:" | grep -q "2"; then
  echo "❌ Has duplicate run: keys"
else
  echo "✅ OK"
fi
```

**Check all repos:**

```bash
cd unified-trading-codex/11-project-management/github-integration/scripts/automation
bash check-workflow-syntax.sh --all
```

---

## Impact

- **12 repos** had this error
- Blocked PR merges (required status check failed)
- Required manual workflow fixes
- Delayed automation pipeline testing

---

## References

- GitHub Actions syntax:
  https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#jobsjob_idstepsrun
- YAML specification: https://yaml.org/spec/1.2.2/
- Fix script: `unified-trading-codex/11-project-management/github-integration/scripts/automation/fix-all-workflows.sh`
