#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Cross-cloud egress cost watcher for the May-23 DeFi cutover soak period.
#
# Queries AWS Cost Explorer (inter-region + DataTransfer-Out-Bytes) and
# GCP Billing API (egress line items) for the past N days and alerts if
# combined cross-cloud egress cost exceeds ALERT_THRESHOLD_USD/day.
#
# Designed to catch accidental cross-cloud reads (e.g. AWS service reading
# from GCS, or GCP service reading from S3) during the cutover soak window.
#
# Usage:
#   # One-shot check (last 7 days):
#   bash cross-cloud-egress-watch.sh
#
#   # Custom threshold + window:
#   ALERT_THRESHOLD_USD=5 LOOKBACK_DAYS=14 bash cross-cloud-egress-watch.sh
#
#   # CI/cron mode (exits 1 if threshold exceeded):
#   bash cross-cloud-egress-watch.sh --ci
#
# Prerequisites:
#   AWS: AWS CLI configured; Cost Explorer access (us-east-1 endpoint)
#   GCP: gcloud configured; Billing API enabled; bigquery billing export
#        (GOOGLE_BILLING_PROJECT + GOOGLE_BILLING_DATASET env vars)
#
# Outputs: cost_egress_report_YYYYMMDD.json in current directory.
#
set -euo pipefail

ALERT_THRESHOLD_USD="${ALERT_THRESHOLD_USD:-10}"
LOOKBACK_DAYS="${LOOKBACK_DAYS:-7}"
CI_MODE=false
REPORT_FILE="cost_egress_report_$(date +%Y%m%d).json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ci) CI_MODE=true; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

START_DATE=$(date -d "$LOOKBACK_DAYS days ago" +%Y-%m-%d 2>/dev/null \
  || date -v-${LOOKBACK_DAYS}d +%Y-%m-%d)  # macOS fallback
END_DATE=$(date +%Y-%m-%d)

echo "=== Cross-cloud egress watch ==="
echo "  Period:    $START_DATE → $END_DATE ($LOOKBACK_DAYS days)"
echo "  Threshold: \$${ALERT_THRESHOLD_USD}/day"
echo ""

AWS_EGRESS_USD=0
GCP_EGRESS_USD=0
ALERT=false

# ── AWS Cost Explorer: DataTransfer-Out-Bytes ─────────────────────────────────

echo "[1/2] Querying AWS Cost Explorer (us-east-1)..."
if command -v aws &>/dev/null && aws sts get-caller-identity &>/dev/null 2>&1; then
  AWS_CE_JSON=$(aws ce get-cost-and-usage \
    --region us-east-1 \
    --time-period Start="$START_DATE",End="$END_DATE" \
    --granularity DAILY \
    --metrics "UnblendedCost" \
    --filter '{
      "Dimensions": {
        "Key": "USAGE_TYPE_GROUP",
        "Values": ["EC2: Data Transfer - Internet", "EC2: Data Transfer - Inter Region"]
      }
    }' \
    --group-by '[{"Type":"DIMENSION","Key":"SERVICE"}]' \
    --output json 2>/dev/null || echo '{"ResultsByTime":[]}')

  AWS_EGRESS_USD=$(echo "$AWS_CE_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = sum(
    float(group['Metrics']['UnblendedCost']['Amount'])
    for day in data.get('ResultsByTime', [])
    for group in day.get('Groups', [])
)
print(f'{total:.4f}')
" 2>/dev/null || echo "0")

  echo "  AWS egress: \$$AWS_EGRESS_USD (total ${LOOKBACK_DAYS}d)"
else
  echo "  AWS: skipped (no credentials)"
fi

# ── GCP Billing API: DataTransfer egress line items ───────────────────────────

echo "[2/2] Querying GCP Billing export (BigQuery)..."
GCP_PROJECT="${GOOGLE_BILLING_PROJECT:-}"
GCP_DATASET="${GOOGLE_BILLING_DATASET:-}"

if [[ -n "$GCP_PROJECT" && -n "$GCP_DATASET" ]] && command -v bq &>/dev/null; then
  GCP_QUERY="SELECT ROUND(SUM(cost),4) AS egress_usd
FROM \`${GCP_PROJECT}.${GCP_DATASET}.gcp_billing_export_v1_*\`
WHERE service.description LIKE '%Network%'
  AND sku.description LIKE '%Egress%'
  AND DATE(usage_start_time) >= '${START_DATE}'
  AND DATE(usage_start_time) < '${END_DATE}'"

  GCP_EGRESS_USD=$(bq query \
    --project_id="$GCP_PROJECT" \
    --nouse_legacy_sql \
    --format=csv \
    --quiet \
    "$GCP_QUERY" 2>/dev/null | tail -1 | tr -d ' ' || echo "0")
  [[ -z "$GCP_EGRESS_USD" || "$GCP_EGRESS_USD" == "null" ]] && GCP_EGRESS_USD=0

  echo "  GCP egress: \$$GCP_EGRESS_USD (total ${LOOKBACK_DAYS}d)"
else
  echo "  GCP: skipped (GOOGLE_BILLING_PROJECT / GOOGLE_BILLING_DATASET not set, or bq not available)"
fi

# ── Compute per-day average and compare to threshold ─────────────────────────

TOTAL_USD=$(python3 -c "print(f'{${AWS_EGRESS_USD} + ${GCP_EGRESS_USD}:.4f}')" 2>/dev/null \
  || echo "$AWS_EGRESS_USD")
DAILY_AVG=$(python3 -c "print(f'{${TOTAL_USD} / ${LOOKBACK_DAYS}:.4f}')" 2>/dev/null \
  || echo "$TOTAL_USD")

echo ""
echo "  Total cross-cloud egress: \$$TOTAL_USD (${LOOKBACK_DAYS}d)"
echo "  Daily average:            \$$DAILY_AVG/day"
echo "  Alert threshold:          \$$ALERT_THRESHOLD_USD/day"

if python3 -c "exit(0 if float('${DAILY_AVG}') > float('${ALERT_THRESHOLD_USD}') else 1)" 2>/dev/null; then
  echo ""
  echo "⚠️  ALERT: cross-cloud egress \$$DAILY_AVG/day exceeds threshold \$$ALERT_THRESHOLD_USD/day"
  echo "   Likely cause: service reading data from wrong-cloud bucket."
  echo "   Check: grep CLOUD_PROVIDER in service configs; verify bucket routing."
  ALERT=true
else
  echo ""
  echo "✅ OK: cross-cloud egress \$$DAILY_AVG/day is within threshold."
fi

# ── Write JSON report ─────────────────────────────────────────────────────────

python3 - <<PYEOF
import json, datetime
report = {
    "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    "period_start": "$START_DATE",
    "period_end": "$END_DATE",
    "lookback_days": $LOOKBACK_DAYS,
    "alert_threshold_usd_per_day": $ALERT_THRESHOLD_USD,
    "aws_egress_usd_total": float("${AWS_EGRESS_USD}"),
    "gcp_egress_usd_total": float("${GCP_EGRESS_USD}"),
    "combined_egress_usd_total": float("${TOTAL_USD}"),
    "daily_average_usd": float("${DAILY_AVG}"),
    "alert": $( [[ "$ALERT" == "true" ]] && echo "true" || echo "false" ),
}
with open("${REPORT_FILE}", "w") as f:
    json.dump(report, f, indent=2)
print(f"Report written: ${REPORT_FILE}")
PYEOF

# ── CI exit code ──────────────────────────────────────────────────────────────

if $CI_MODE && [[ "$ALERT" == "true" ]]; then
  echo "CI mode: exiting 1 (threshold exceeded)"
  exit 1
fi
