# Quality Gates: Local vs GitHub Actions vs Cloud Build

## TL;DR

**After your changes, all three environments now run the SAME command:**

```bash
bash scripts/quality-gates.sh --no-fix
```

The **only differences** are:

1. **Where it runs** (your machine vs VM vs container)
2. **What tests are excluded** (external APIs, real data downloads)
3. **Environment variables** (real vs mocked credentials)

---

## Side-by-Side Comparison

### Command Executed

| Environment        | Command                                          | Flags                        |
| ------------------ | ------------------------------------------------ | ---------------------------- |
| **Local**          | `bash scripts/quality-gates.sh`                  | Auto-fix enabled             |
| **GitHub Actions** | `bash scripts/quality-gates.sh --no-fix`         | No auto-fix (fail if issues) |
| **Cloud Build**    | `bash scripts/quality-gates.sh --no-fix --quick` | No auto-fix, skip slow tests |

### Where It Runs

| Environment        | Location                     | Ephemeral?              | Setup Time             |
| ------------------ | ---------------------------- | ----------------------- | ---------------------- |
| **Local**          | Your Mac/Linux machine       | ❌ No (persistent)      | 0s (already set up)    |
| **GitHub Actions** | Ubuntu 22.04 VM              | ✅ Yes (fresh each run) | ~30-60s (deps install) |
| **Cloud Build**    | Python 3.13 Docker container | ✅ Yes (from image)     | ~5-10s (image pull)    |

### Environment Setup

#### Local

```bash
# One-time setup
python3.13 -m venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run quality gates
bash scripts/quality-gates.sh

# Environment
- Real credentials from ~/.config/gcloud or service account key
- Real GCP project (test-project)
- Can access real GCS buckets, BigQuery, etc.
```

#### GitHub Actions

```yaml
# Fresh VM every run
steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5
    with:
      python-version: "3.13"

  - name: Install dependencies
    run: |
      pip install uv
      uv pip install --system -e deps/unified-trading-services
      uv pip install --system -e ".[dev]"

  - name: Run quality gates
    env:
      CLOUD_MOCK_MODE: "true" # ← Mock GCS/BigQuery
      GCP_PROJECT_ID: "test-project" # ← Fake project
    run: bash scripts/quality-gates.sh --no-fix
```

**Key differences:**

- `--system` flag (no venv, install globally in VM)
- `CLOUD_MOCK_MODE=true` (no real GCP calls)
- Installs deps fresh every run (~30-60s)

#### Cloud Build

```yaml
# Runs inside pre-built Docker image
steps:
  - name: build
    args: ["build", "-t", "my-service:latest", "."]

  - name: quality-gates
    run: |
      docker run --rm \
        -e CLOUD_MOCK_MODE=true \
        -e GCP_PROJECT_ID=$PROJECT_ID \
        my-service:latest \
        bash -c "scripts/quality-gates.sh --no-fix --quick"
```

**Key differences:**

- Runs inside the service's Docker image (tests the artifact you deploy)
- Dependencies already installed in image (fast startup ~5-10s)
- `--quick` flag skips slow integration tests

---

## What Tests Run Where

### All Three Run These

```bash
✅ Config validation       (syntax check pyproject.toml, .env.example)
✅ Linting                 (ruff check + ruff format)
✅ Unit tests              (synthetic fixtures, no external deps)
✅ Import sanity check     (can the module be imported?)
✅ Codex compliance        (print(), os.getenv(), datetime.now())
```

### Conditional Tests

| Test Type                       | Local                   | GitHub Actions                 | Cloud Build                   | Reason                                   |
| ------------------------------- | ----------------------- | ------------------------------ | ----------------------------- | ---------------------------------------- |
| **Integration (external APIs)** | ✅ With `--integration` | ❌ Skipped `-k "not api"`      | ❌ Skipped `-k "not api"`     | No API keys in CI                        |
| **Integration (downloads)**     | ✅ With `--integration` | ❌ Skipped `-k "not download"` | ❌ Skipped `--quick`          | Too slow, needs credentials              |
| **E2E (full pipeline)**         | ✅ Yes                  | ✅ Yes (mocked GCS)            | ⚠️ With `--quick` (selective) | Full e2e slow in CI                      |
| **Smoke tests**                 | ✅ Yes                  | ✅ Yes                         | ✅ Yes                        | Always run (fast, just CLI combinations) |

### Test Exclusion Patterns

**GitHub Actions:**

```bash
# In pytest commands
-k "not api and not live and not download"
--ignore=tests/integration/test_tardis_downloader.py
--ignore=tests/integration/test_live_stream.py
```

**Cloud Build:**

```bash
# Via --quick flag in quality-gates.sh
if [ "$QUICK_MODE" = true ]; then
  PYTEST_ARGS="$PYTEST_ARGS -k 'not slow and not download and not api'"
fi
```

**Local:**

```bash
# No exclusions by default
# Add --quick or --skip-integration to exclude
```

---

## Environment Variables

### Local (Real Credentials)

```bash
# From gcloud auth or service account key
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
export GCP_PROJECT_ID=test-project
export UNIFIED_CLOUD_SERVICES_GCS_BUCKET=unified-market-data

# Tests can:
- Write to real GCS buckets
- Query real BigQuery tables
- Call real APIs (with credentials)
```

### GitHub Actions (Mocked)

```yaml
env:
  CLOUD_MOCK_MODE: "true"                    # ← unified-trading-services uses in-memory mock
  GCP_PROJECT_ID: "test-project"       # ← Fake project ID
  DEPLOYMENT_CONFIG_DIR: "${{ github.workspace }}/deps/..."

# Tests will:
- Use in-memory storage (no real GCS)
- Skip external API calls
- Use synthetic data only
```

### Cloud Build (Mocked + Service Account)

```bash
# Cloud Build provides Workload Identity
export CLOUD_MOCK_MODE=true
export GCP_PROJECT_ID=$PROJECT_ID  # Real project, but mocked APIs
export DEPLOYMENT_CONFIG_DIR=/workspace/deps/...

# Tests will:
- Use in-memory storage (no real GCS)
- Skip external API calls
- Can call GCP APIs if needed (but usually mocked)
```

---

## Output: Before vs After Your Changes

### BEFORE: GitHub Actions (Individual Steps)

```
✅ Lint and format check
   ruff check passed
   ruff format passed

✅ Run unit tests
   167 tests passed in 8.2s

✅ Run integration tests
   45 tests passed in 12.5s

✅ Run e2e tests
   12 tests passed in 6.1s

✅ Run smoke tests
   8 tests passed in 2.3s
```

**Problems:**

- No Config validation shown
- No Codex compliance shown
- Hard to see overall status at a glance

### AFTER: GitHub Actions (quality-gates.sh)

```
[1/4] CONFIG VALIDATION
----------------------------------------------------------------------
Checking pyproject.toml syntax... PASS
Checking .env.example format... PASS
✅ Config validation PASSED

[2/4] LINTING & FORMATTING
----------------------------------------------------------------------
Running ruff check... PASS (0 errors)
Running ruff format... PASS (no changes needed)
✅ Linting PASSED

[3/4] TESTING (Unit, Integration, E2E, Smoke)
----------------------------------------------------------------------
Running unit tests...
✅ Unit tests PASSED (167 passed in 8.2s)

Running integration tests...
✅ Integration tests PASSED (45 passed in 12.5s)

Running e2e tests...
✅ E2E tests PASSED (12 passed in 6.1s)

Running smoke tests...
✅ Smoke tests PASSED (8 passed in 2.3s)

Running import sanity check...
✅ Import check PASSED

[4/4] CODEX COMPLIANCE (Coding Standards)
----------------------------------------------------------------------
Checking for print() statements... PASS
Checking for os.getenv() usage... PASS
Checking for datetime.now() without UTC... PASS
Checking for bare except clauses... PASS
✅ Codex compliance PASSED

======================================================================
QUALITY GATES SUMMARY
======================================================================
Config:   ✅ PASSED
Linting:  ✅ PASSED
Tests:    ✅ PASSED (232 total: 167 unit, 45 integration, 12 e2e, 8 smoke)
Codex:    ✅ PASSED (0 violations)
======================================================================

✅ ALL QUALITY GATES PASSED
```

**Benefits:**

- ✅ Clear 4-section breakdown
- ✅ Shows Config and Codex (previously hidden)
- ✅ Overall summary at a glance
- ✅ Consistent with Cloud Build output

---

## Monitoring Output in Real-Time

### 1. Local Scripts

**Option A: Direct output**

```bash
bash scripts/quality-gates.sh
# Output shows in real-time automatically
```

**Option B: Save AND view**

```bash
bash scripts/quality-gates.sh 2>&1 | tee quality-gates.log
# See output in real-time AND save to file
```

### 2. GitHub Actions

**Option A: Web UI**

1. Go to: https://github.com/IggyIkenna/<repo>/actions
2. Click on workflow run
3. Output updates every few seconds

**Option B: Terminal (requires gh CLI)**

```bash
# Watch latest run in real-time
gh run watch

# View specific run
gh run view <run-id> --log

# Follow logs (poll every 3 seconds)
gh run view <run-id> --log --exit-status
```

**Option C: Get live updates**

```bash
# In a loop
while true; do
  clear
  gh run view --log | tail -50
  sleep 5
done
```

### 3. Cloud Build

**Option A: Stream logs**

```bash
# When submitting
gcloud builds submit --config cloudbuild.yaml --project=test-project

# For existing build
gcloud builds log <BUILD_ID> --stream --project=test-project
```

**Option B: Follow in terminal**

```bash
# Poll every 5 seconds
BUILD_ID="d800373f-f2af-4796-aa5c-f0be17059ca8"

while true; do
  clear
  gcloud builds log $BUILD_ID --project=test-project | tail -30
  STATUS=$(gcloud builds describe $BUILD_ID --project=test-project --format="value(status)")
  echo ""
  echo "Status: $STATUS"

  if [ "$STATUS" != "WORKING" ] && [ "$STATUS" != "QUEUED" ]; then
    break
  fi

  sleep 5
done
```

**Option C: Web UI**

1. Go to: https://console.cloud.google.com/cloud-build/builds
2. Click on build
3. Auto-updates every few seconds

---

## Quick Reference Table

| Feature             | Local                 | GitHub Actions                   | Cloud Build                         |
| ------------------- | --------------------- | -------------------------------- | ----------------------------------- |
| **Command**         | `quality-gates.sh`    | `quality-gates.sh --no-fix`      | `quality-gates.sh --no-fix --quick` |
| **Environment**     | Your machine          | Ubuntu 22.04 VM                  | Python 3.13 container               |
| **Python**          | Your version          | 3.13 from setup-python           | 3.13 from Dockerfile                |
| **Dependencies**    | Your .venv            | Installed fresh (~30-60s)        | Built into image (~5-10s)           |
| **Credentials**     | Real (gcloud auth)    | Mocked (CLOUD_MOCK_MODE)         | Mocked (CLOUD_MOCK_MODE)            |
| **GCS writes**      | ✅ Real               | ❌ Mocked (in-memory)            | ❌ Mocked (in-memory)               |
| **External APIs**   | ✅ Allowed            | ❌ Skipped (`-k "not api"`)      | ❌ Skipped (`--quick`)              |
| **Data downloads**  | ✅ Allowed            | ❌ Skipped (`-k "not download"`) | ❌ Skipped (`--quick`)              |
| **Live WebSockets** | ✅ Allowed            | ❌ Skipped (`-k "not live"`)     | ❌ Skipped (`--quick`)              |
| **Output**          | ✅ 4-section summary  | ✅ 4-section summary (NEW!)      | ✅ 4-section summary                |
| **Speed**           | Varies                | ~2-5 min (with -n auto)          | ~1-3 min (image cached)             |
| **Parallelization** | `-n auto` (all cores) | `-n auto` (2 cores)              | `-n auto` (varies by machine type)  |

---

## Summary

**Before your changes:**

- ❌ GitHub Actions: 5+ separate steps, no summary, no Codex check visible
- ✅ Cloud Build: Single quality-gates.sh call, nice summary

**After your changes:**

- ✅ All three: Same command, same output format
- ✅ Only differences: Environment setup and test exclusions
- ✅ Consistent 4-section summary everywhere

**The differences are ONLY setup-related:**

- Dependencies installation method
- Credential mocking
- Which optional tests to skip

**Everything else is identical!**
