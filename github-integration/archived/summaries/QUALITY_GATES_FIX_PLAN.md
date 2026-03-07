# Quality Gates Fix Plan - All Services

**Status:** Branch protection DISABLED for 10 repos **Backup:** `/tmp/branch-protection-backup-20260214-134431`

---

## Execution Order (by Priority)

### CRITICAL (Blocking All Tests)

#### 1. execution-service - Python Version Fix

**Issue:** Python 3.13 installed, needs 3.11.x for NautilusTrader

**Files to fix:**

- `pyproject.toml` line 21: `requires-python = ">=3.13,<3.14"` → `">=3.11,<3.12"`
- `pyproject.toml` line 19: `"Programming Language :: Python :: 3.13"` → `"Programming Language :: Python :: 3.11"`
- `.python-version`: `3.13` → `3.11.9`

**Commands:**

```bash
cd execution-service
# Fix pyproject.toml and .python-version
pyenv install 3.11.9
pyenv local 3.11.9
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
bash scripts/quality-gates.sh --no-fix
bash scripts/quickmerge.sh "Fix: Use Python 3.11.x for NautilusTrader compatibility" --files "pyproject.toml .python-version"
```

---

### HIGH PRIORITY (Test Failures)

#### 2. features-delta-one-service - Missing venues.yaml

#### 3. features-volatility-service - Missing venues.yaml

#### 4. features-calendar-service - Missing venues.yaml

#### 5. features-onchain-service - Missing venues.yaml

**Issue:** Smoke tests fail looking for `deps/unified-trading-deployment-v2/configs/venues.yaml`

**Solution:** Create symlink to actual venues.yaml location

**Commands (for each service):**

```bash
cd features-{SERVICE}-service
mkdir -p deps/unified-trading-deployment-v2/configs
ln -s ../../../../../unified-trading-deployment-v2/configs/venues.yaml \
      deps/unified-trading-deployment-v2/configs/venues.yaml
bash scripts/quality-gates.sh --no-fix
bash scripts/quickmerge.sh "Fix: Add venues.yaml symlink for smoke tests" --files "deps/unified-trading-deployment-v2/configs/venues.yaml"
```

---

#### 6. market-data-processing-service - Invalid Workflow YAML

**Issue:** `.github/workflows/quality-gates.yml` line 65 has duplicate 'run' property

**Commands:**

```bash
cd market-data-processing-service
# Edit .github/workflows/quality-gates.yml - remove duplicate 'run' at line 65
bash scripts/quality-gates.sh --no-fix
bash scripts/quickmerge.sh "Fix: Remove duplicate 'run' in quality-gates.yml" --files ".github/workflows/quality-gates.yml"
```

---

#### 7. instruments-service - Test Failure

**Issue:** `test_bucket_resolution_fixture_integration` expects 'cefi' in bucket name

**Commands:**

```bash
cd instruments-service
# Review test and fix bucket configuration expectation
bash scripts/quality-gates.sh --no-fix
bash scripts/quickmerge.sh "Fix: Update bucket resolution test expectations" --files "tests/unit/test_bucket_config.py"
```

---

### MEDIUM PRIORITY (Codex Violations)

#### 8. execution-service - Codex Violations in deps/

**Issue:** print(), os.getenv(), requests in `deps/unified-trading-deployment-v2/`

**Note:** These are in deps/ subdirectory. Consider if these should be fixed here or in the source repo.

---

#### 9. features-onchain-service - Codex Violations

**Issue:**

- print() in `features_onchain_service/examples/fear_greed_parser.py`
- requests library in examples/ and scripts/

**Commands:**

```bash
cd features-onchain-service
# Fix print() → logger.info() in examples
# Fix requests → aiohttp in async code
bash scripts/quality-gates.sh --no-fix
bash scripts/quickmerge.sh "Fix: Replace print() and requests in examples" --files "features_onchain_service/examples/fear_greed_parser.py ..."
```

---

### QUESTIONS / REVIEW

#### 10. strategy-service - Windows Quality Gates

**Question:** Why does strategy-service have both Ubuntu and Windows quality gates?

- Server deployment is Linux-only
- Unless running locally on Windows (but then why in CI?)
- Recommend: Remove Windows quality gates, keep Linux only

**Commands:**

```bash
cd strategy-service
# Review .github/workflows/ for Windows matrix
# Remove Windows from test matrix if not needed
```

---

#### 11. ml-training-service & ml-inference-service

**Question:** What are the specific quality gate failures? **Action:** Need to view actual CI logs to diagnose

---

## Workflow for Each Fix

1. **Fix the issue** (edit files as described above)
2. **Run quality gates locally:**
   ```bash
   bash scripts/quality-gates.sh --no-fix
   ```
3. **If pass:** Quickmerge
   ```bash
   bash scripts/quickmerge.sh "Fix: [description]" --files "[list of files]"
   ```
4. **If fail:** Fix issues, repeat step 2
5. **Monitor PR:** Check GitHub Actions pass
6. **If CI fails:** Diagnose infrastructure mismatch, fix, force push

---

## After All Fixes Complete

**Re-enable branch protection:**

```bash
cd unified-trading-codex/11-project-management/github-integration/scripts/one-time
bash enable-branch-protection.sh --restore /tmp/branch-protection-backup-20260214-134431
```

---

## Summary of Changes Needed

| Service                | Issue               | Files                                       | Est. Time |
| ---------------------- | ------------------- | ------------------------------------------- | --------- |
| execution-service      | Python 3.11         | pyproject.toml, .python-version             | 15min     |
| features-delta-one     | venues.yaml         | deps/unified-trading-deployment-v2/configs/ | 5min      |
| features-volatility    | venues.yaml         | deps/unified-trading-deployment-v2/configs/ | 5min      |
| features-calendar      | venues.yaml         | deps/unified-trading-deployment-v2/configs/ | 5min      |
| features-onchain       | venues.yaml + codex | deps/, examples/                            | 10min     |
| market-data-processing | YAML syntax         | .github/workflows/quality-gates.yml         | 5min      |
| instruments-service    | Test fix            | tests/unit/test_bucket_config.py            | 10min     |
| strategy-service       | Review Windows CI   | .github/workflows/                          | 5min      |
| ml-training            | TBD                 | TBD                                         | TBD       |
| ml-inference           | TBD                 | TBD                                         | TBD       |

**Total estimated time:** ~1-2 hours (with quality gates + PR monitoring)

---

## Notes

- Branch protection is DISABLED - be careful with direct pushes
- All changes should go through quality gates first
- Use quickmerge for proper PR creation
- Monitor CI to ensure GitHub Actions pass
- If CI fails but local passes: Fix infrastructure (workflow YAML, Dockerfile)
- Don't forget to re-enable branch protection when done!
