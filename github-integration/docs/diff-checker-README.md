# Daily Diff Checker

Automated daily checker that compares codex documentation against actual codebase implementation and creates GitHub
issues for drift.

## Purpose

Prevents design drift by:

- Detecting standards violations (coding, architecture, observability)
- Identifying missing implementations described in docs
- Creating actionable GitHub issues for remediation
- Running daily to catch drift immediately

## Usage

### Basic Usage

```bash
cd unified-trading-codex/11-project-management/github-integration

# Preview what would be created (dry run) - FAST: ~9 seconds
python run-diff-checker.py --repo IggyIkenna/unified-trading-codex --dry-run

# Create issues in codex repo (parallel execution: ~1-2 minutes for 1000+ issues)
python run-diff-checker.py --repo IggyIkenna/unified-trading-codex

# Increase parallelism for faster creation (20 workers instead of default 10)
python run-diff-checker.py --repo IggyIkenna/unified-trading-codex --max-workers 20

# Save results to JSON
python run-diff-checker.py --repo IggyIkenna/unified-trading-codex --output-json diff-results.json
```

**Performance:**

- ✅ **Batch fetch existing issues**: 1 API call to load all issues (~1 sec)
- ✅ **Parallel issue creation**: 10 workers by default (customize with `--max-workers`)
- ✅ **Dry-run**: ~9 seconds (was 5-10 minutes)
- ✅ **Real run**: ~1-2 minutes for 1,000+ issues (was ~20 minutes sequential)

### Daily Automation

Set up daily cron job:

```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * cd /path/to/unified-trading-codex && python 11-project-management/github-integration/run-diff-checker.py --output-json /path/to/logs/diff-$(date +\%Y-\%m-\%d).json
```

Or use GitHub Actions:

```yaml
# .github/workflows/daily-diff-checker.yml
name: Daily Diff Checker

on:
  schedule:
    - cron: "0 2 * * *" # 2 AM daily
  workflow_dispatch: # Manual trigger

jobs:
  diff-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Install dependencies
        run: pip install pyyaml
      - name: Run diff checker
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python unified-trading-codex/11-project-management/github-integration/run-diff-checker.py \
            --output-json diff-results.json
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: diff-results
          path: diff-results.json
```

## What It Checks

### 1. Coding Standards (06-coding-standards/)

- **Bare except clauses**: Should use `@handle_api_errors` or specific exceptions
- **os.getenv() usage**: Should use config classes extending UnifiedCloudServicesConfig
- **datetime.now() without UTC**: Should use `datetime.now(timezone.utc)`
- **Imports inside functions**: All imports should be at top of file
- **Print statements**: Should use `logger.info()` instead
- **Files >1500 lines**: Should split by Single Responsibility Principle (1500 is max for centralized scripts; aim for
  <500 for most modules)

### 2. Event Logging (03-observability/)

- **Missing test_event_logging.py**: All services MUST test 3-tier event logging
- **Missing log_event("STARTED")**: Entry points must log START event
- **Missing log_event("STOPPED"/"FAILED")**: Must log completion event

### 3. Architecture (04-architecture/)

- **Missing --mode batch|live**: Services should support batch-live symmetry
- **Missing MAX_WORKERS**: Services should have configurable concurrency

## Output Format

### Console Output

```
Codex root: /path/to/unified-trading-codex
Workspace root: /path/to/workspace
Target repo: IggyIkenna/unified-trading-deployment-v2
Dry run: False

Running diff checks...
  - Checking coding standards...
  - Checking event logging...
  - Checking architecture...

Found 42 gaps
  P0-critical: 0
  P1-high: 8
  P2-medium: 15
  P3-low: 19

Processing gaps...
  ✓  COD-BARE-instruments-service-handler: Creating issue...
  ⏭  COD-GETENV-market-data-config: Already exists (#123)
  ✓  OBS-EVENT-START-strategy-service: Creating issue...

Summary:
  Total gaps found: 42
  Issues created: 35
  Issues skipped (already exist): 7
```

### JSON Output

```json
{
  "timestamp": "2026-02-12T10:30:00Z",
  "codex_root": "/path/to/unified-trading-codex",
  "workspace_root": "/path/to/workspace",
  "target_repo": "IggyIkenna/unified-trading-deployment-v2",
  "dry_run": false,
  "total_gaps": 42,
  "gaps_by_priority": {
    "P1-high": 8,
    "P2-medium": 15,
    "P3-low": 19
  },
  "created_count": 35,
  "skipped_count": 7,
  "results": [
    {
      "action": "created",
      "issue_number": "456",
      "issue_url": "https://github.com/IggyIkenna/unified-trading-deployment-v2/issues/456",
      "gap_id": "COD-BARE-instruments-service-handler",
      "service": "instruments-service"
    }
  ]
}
```

## GitHub Issue Format

Issues created by diff checker include:

```markdown
[instruments-service] COD-BARE-handler: Bare except clause in instruments_service/handler.py

## Gap Type: standards_violation

File contains bare `except:` clause which violates coding standards. Should use `@handle_api_errors` decorator or
specific exception types.

## Details

- **Category**: coding_standards
- **Service**: instruments-service
- **Priority**: P2-medium
- **Auto-fixable**: No
- **Codex Reference**: 06-coding-standards/README.md#error-handling

## Affected Files

- instruments_service/handler.py

## Standards Reference

See codex: `06-coding-standards/README.md#error-handling`

---

**Markers for Drift Checker:**

- gap-id: COD-BARE-instruments-service-handler
- gap-type: standards_violation
- category: coding_standards
- auto-fixable: false
- detected: 2026-02-12T10:30:00Z
```

## Labels Applied

- `issue` - Work item type
- `P0-critical` / `P1-high` / `P2-medium` / `P3-low` - Priority
- `area/coding-standards` / `area/observability` / `area/architecture` - Category
- `service/instruments` / `service/market-tick` / etc. - Target service
- `auto-fixable` - Can be auto-fixed by agent (optional)

## Deduplication

Diff checker prevents duplicates by:

1. **Searching before creating**: Uses `gap-id` marker to find existing issues
2. **Skipping existing**: If open issue found with same gap-id, skips creation
3. **Markers in body**: Every issue includes unique gap-id for tracking

## Agent Pickup

Agents can filter issues created by diff checker:

```bash
# List all drift gaps
gh issue list --label "issue" --search "gap-id in:body"

# List auto-fixable drift gaps
gh issue list --label "auto-fixable"

# List by category
gh issue list --label "area/coding-standards"

# List by service
gh issue list --label "service/instruments"

# List by priority
gh issue list --label "P1-high"
```

## Extending Checks

To add new drift checks:

1. Create new function in `run-diff-checker.py`:

```python
def find_my_new_check(codex_root: Path, workspace_root: Path) -> list[DriftGap]:
    """Check for my new gap type."""
    gaps: list[DriftGap] = []

    # Your check logic here
    # Create DriftGap objects for each violation found

    return gaps
```

2. Add to main() function:

```python
print("  - Checking my new check...")
all_gaps.extend(find_my_new_check(codex_root, workspace_root))
```

3. Document in this README

## Dependencies

- Python 3.13+
- `gh` CLI authenticated (`gh auth login`)
- `pyyaml` library (`pip install pyyaml`)

## Limitations

Current checks focus on most common violations. Future enhancements:

- **Data schema validation**: Check Parquet schema compliance
- **Domain model checks**: Verify signal-based strategy patterns
- **Infrastructure checks**: Verify deployment configs
- **Documentation completeness**: Check for missing docstrings

## Related Documentation

- [workflow-visuals.md](../../12-agent-workflow/workflow-visuals.md) - Diagram 8: Daily Diff Checker Feedback Loop
- [workflow-design-decisions.md](../../12-agent-workflow/workflow-design-decisions.md) - Section 4: Docs-First Approach
- [06-coding-standards/](../../06-coding-standards/) - Coding standards checked
- [03-observability/](../../03-observability/) - Observability standards checked
- [04-architecture/](../../04-architecture/) - Architecture standards checked

## Troubleshooting

### "gh: command not found"

Install GitHub CLI:

```bash
# macOS
brew install gh

# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Then authenticate
gh auth login
```

### "PyYAML required"

```bash
pip install pyyaml
```

### "Could not find codex"

Ensure you're running from workspace root or provide paths:

```bash
python run-diff-checker.py \
  --codex-dir /path/to/unified-trading-codex \
  --workspace-dir /path/to/workspace
```

### Rate Limiting

If hitting GitHub rate limits with many issues:

- Use `--dry-run` to preview first
- Run during off-peak hours
- Use GitHub App token with higher limits

## Success Metrics

Track these metrics weekly:

- **Drift detection rate**: % of violations caught before human review
- **Auto-fix rate**: % of gaps marked auto-fixable
- **Resolution time**: Average time from gap detection to closure
- **Regeneration frequency**: How often same gap reappears

Target metrics:

- Drift detection rate: 90%+
- Auto-fix rate: 40%+
- Resolution time: <7 days for P1-high
- Regeneration frequency: <5% (same gap should not reappear often)
