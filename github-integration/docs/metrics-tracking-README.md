# Workflow Metrics Tracking

Comprehensive metrics system for measuring workflow effectiveness and identifying areas for improvement.

## Purpose

Track six key success metrics:

1. **Drift Detection Rate** - % of standards violations caught by diff checker before human review
2. **Duplication Rate** - % of duplicate issues created
3. **Automation Rate** - % of tasks completed with total automation
4. **Cycle Time** - Average time from inception to merged PR (by automation type)
5. **Quality Gate Pass Rate** - % of first-time quality gate passes
6. **Regeneration Frequency** - Average regenerations per epic

## Usage

### Generate Weekly Report

```bash
cd unified-trading-codex/11-project-management/github-integration

# Markdown report for last 7 days
python track-metrics.py \
  --repo IggyIkenna/unified-trading-deployment-v2 \
  --period-days 7 \
  --report-format markdown \
  --output metrics-weekly.md

# JSON data for last 30 days
python track-metrics.py \
  --repo IggyIkenna/unified-trading-deployment-v2 \
  --period-days 30 \
  --report-format json \
  --output metrics-monthly.json
```

### Automated Weekly Reports

Set up GitHub Action to generate weekly reports:

```yaml
# .github/workflows/weekly-metrics.yml
name: Weekly Metrics Report

on:
  schedule:
    - cron: "0 9 * * 1" # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  generate-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Generate metrics report
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python unified-trading-codex/11-project-management/github-integration/track-metrics.py \
            --repo ${{ github.repository }} \
            --period-days 7 \
            --report-format markdown \
            --output metrics-report.md

      - name: Create issue with report
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue create \
            --title "Weekly Metrics Report - $(date +%Y-%m-%d)" \
            --body-file metrics-report.md \
            --label "metrics" \
            --label "weekly-report"

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: metrics-report
          path: metrics-report.md
```

## Metrics Definitions

### 1. Drift Detection Rate

**Formula:** `(gaps_caught_by_diff_checker / total_gaps_found) × 100`

**Target:** 90%+

**Interpretation:**

- High rate (90%+): Diff checker catching most violations automatically
- Low rate (<90%): Humans finding violations before diff checker runs
- **Action if low**: Expand diff checker coverage, run more frequently

### 2. Duplication Rate

**Formula:** `(duplicate_issues_created / total_issues_created) × 100`

**Target:** <2%

**Interpretation:**

- Low rate (<2%): Marker system working well
- High rate (>2%): Marker system failing or scripts not using it
- **Action if high**: Review sync scripts, ensure consistent marker usage

### 3. Automation Rate

**Formula:** `(total_automation_tasks / total_tasks_completed) × 100`

**Target:** 60%+

**Breakdown by Quadrant:**

- Total Automation: Auto-pickup + Auto-close
- Semi-Auto Front: Human pickup + Auto-close
- Semi-Auto Back: Auto-pickup + Human UAT
- Full Human Loop: Human pickup + Human UAT

**Interpretation:**

- High rate (60%+): Good balance of automation and oversight
- Low rate (<60%): Too much human involvement, review auto-pickup criteria
- **Action if low**: Review tasks in full-human quadrant, identify patterns that could be automated

### 4. Cycle Time

**Measured separately for:**

- Total automation: Target <2 days
- Semi-automation: Target <5 days
- Full human loop: Target <10 days

**Interpretation:**

- Fast cycle times: Efficient workflow
- Slow cycle times: Bottlenecks in review or implementation
- **Action if slow**: Identify bottleneck stage (pickup, implementation, UAT)

### 5. Quality Gate Pass Rate

**Formula:** `(first_time_passes / total_quickmerge_attempts) × 100`

**Target:** 90%+

**Interpretation:**

- High rate (90%+): Agents understanding standards well
- Low rate (<90%): Common mistakes, need better guidance
- **Action if low**: Analyze failure patterns, update agent instructions

### 6. Regeneration Frequency

**Formula:** `total_regenerations / num_epics`

**Target:** <1.5 average per epic

**Interpretation:**

- Low frequency (<1.5): Stable epic generation
- High frequency (>1.5): Too much churn, requirements changing
- **Action if high**: Review epic stability, freeze requirements earlier

## Sample Reports

### Markdown Report Example

```markdown
# Workflow Metrics Report

**Generated:** 2026-02-12T10:30:00Z **Repository:** IggyIkenna/unified-trading-deployment-v2 **Period:** Last 7 days

---

## 1. Drift Detection

- **Gaps found:** 42
- **Caught before human review:** 39
- **Detection rate:** 92.9% ✅ (target: 90%+)

**Analysis:** Strong drift prevention

---

## 2. Duplication Prevention

- **Total issues created:** 156
- **Duplicate issues:** 2
- **Duplication rate:** 1.3% ✅ (target: <2%)

**Analysis:** Excellent duplication prevention

---

[... rest of metrics ...]

## Overall Health Score

🟢 HEALTHY

**Passing targets:** 5/5

---

## Recommendations

- All metrics healthy - continue current practices
```

### JSON Report Example

```json
{
  "timestamp": "2026-02-12T10:30:00Z",
  "repo": "IggyIkenna/unified-trading-deployment-v2",
  "period_days": 7,
  "drift_gaps_found": 42,
  "drift_gaps_caught_before_review": 39,
  "drift_detection_rate": 92.9,
  "total_issues_created": 156,
  "duplicate_issues_created": 2,
  "duplication_rate": 1.3,
  "total_tasks_completed": 89,
  "total_automation_tasks": 58,
  "semi_auto_front_tasks": 12,
  "semi_auto_back_tasks": 15,
  "full_human_loop_tasks": 4,
  "automation_rate": 65.2,
  "avg_cycle_time_total_auto": 1.5,
  "avg_cycle_time_semi_auto": 3.8,
  "avg_cycle_time_full_human": 7.2,
  "avg_cycle_time_overall": 2.9,
  "total_quickmerge_attempts": 95,
  "first_time_pass": 87,
  "quality_gate_pass_rate": 91.6,
  "total_regenerations": 18,
  "avg_regenerations_per_epic": 1.2,
  "max_regeneration_hit_count": 1
}
```

## Dashboard Setup

### Option 1: Weekly Email Report

Set up automated email:

```bash
# Add to crontab
0 9 * * 1 cd /path/to/codex && python track-metrics.py --repo OWNER/REPO --report-format markdown | mail -s "Weekly Workflow Metrics" team@example.com
```

### Option 2: Grafana Dashboard

Export metrics to time-series database:

```python
# In track-metrics.py, add export to Prometheus/InfluxDB
# Or use GitHub API + Grafana GitHub datasource
```

### Option 3: Spreadsheet Export

```bash
# Export to CSV
python track-metrics.py --repo OWNER/REPO --report-format json | \
  jq -r '[.drift_detection_rate, .duplication_rate, .automation_rate, .quality_gate_pass_rate, .avg_regenerations_per_epic] | @csv' \
  >> metrics-history.csv
```

## Metric Trends

Track metrics over time to identify trends:

```bash
# Collect daily
python track-metrics.py --repo OWNER/REPO --period-days 1 --output metrics-$(date +%Y-%m-%d).json

# Weekly comparison
python compare-metrics.py metrics-2026-02-05.json metrics-2026-02-12.json
```

## Alerting Thresholds

Set up alerts when metrics fall below thresholds:

| Metric                     | Warning Threshold | Critical Threshold |
| -------------------------- | ----------------- | ------------------ |
| Drift detection rate       | <85%              | <75%               |
| Duplication rate           | >3%               | >5%                |
| Automation rate            | <50%              | <40%               |
| Quality gate pass rate     | <85%              | <75%               |
| Avg regenerations per epic | >2.0              | >3.0               |

### Alert Script Example

```bash
#!/bin/bash
# alert-on-metrics.sh

METRICS=$(python track-metrics.py --repo "$REPO" --report-format json)

DRIFT_RATE=$(echo "$METRICS" | jq -r '.drift_detection_rate')
QG_PASS_RATE=$(echo "$METRICS" | jq -r '.quality_gate_pass_rate')

if (( $(echo "$DRIFT_RATE < 85" | bc -l) )); then
  echo "⚠️  ALERT: Drift detection rate below 85%: $DRIFT_RATE%"
  # Send alert to Slack/email
fi

if (( $(echo "$QG_PASS_RATE < 85" | bc -l) )); then
  echo "⚠️  ALERT: Quality gate pass rate below 85%: $QG_PASS_RATE%"
  # Send alert to Slack/email
fi
```

## Dependencies

- Python 3.13+
- `gh` CLI authenticated
- `jq` (for JSON processing in shell scripts)
- `bc` (for floating point math in shell scripts)

## Extending Metrics

To add new metrics:

1. Add new fields to `WorkflowMetrics` dataclass
2. Create calculation function following existing patterns
3. Call from `collect_metrics()`
4. Update markdown formatting in `format_markdown_report()`
5. Document in this README

Example:

```python
def calculate_my_new_metric(issues: list[dict]) -> float:
    """Calculate my new metric."""
    # Your calculation logic
    return metric_value

# Add to collect_metrics():
my_metric = calculate_my_new_metric(issues)
```

## Related Documentation

- [workflow-visuals.md](../../12-agent-workflow/workflow-visuals.md) - Visual representation of workflow system
- [workflow-design-decisions.md](../../12-agent-workflow/workflow-design-decisions.md) - Design rationale and success
  criteria
- [diff-checker-README.md](./diff-checker-README.md) - Drift detection system
- [setup-project-board.md](./setup-project-board.md) - Project board configuration

## Troubleshooting

### "gh: command not found"

Install GitHub CLI:

```bash
brew install gh  # macOS
gh auth login
```

### "No data for period"

Increase `--period-days` or check that issues exist in repo.

### Incorrect calculations

Verify issue markers are being added correctly by sync scripts. Check issue bodies for:

- `regeneration-count:`
- `completion-status:`
- `gap-id:`
- `auto-fixable:`

## Success Criteria

All metrics should trend positively over time:

- ✅ Drift detection rate increasing toward 95%+
- ✅ Duplication rate decreasing toward 1%
- ✅ Automation rate stabilizing at 60-70%
- ✅ Cycle times decreasing as agents learn
- ✅ Quality gate pass rate increasing toward 95%+
- ✅ Regeneration frequency decreasing toward <1.0
