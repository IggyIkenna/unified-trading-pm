---
doc_type: plan
title: Gate 3 — Phantom-Audit Execution Runbook
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-13"
---

> **ARCHIVED 2026-05-21** — Gate 3 FIRED 2026-05-17; 0 phantoms all 5 asset_groups; operator decision ACCEPT. TradFi
> 5,212 legacy-blank apply-flips migrated to `tradfi_master.md`. Preserved for archaeology.

---

title: "Gate 3 — Phantom-Audit Execution Runbook" created: 2026-05-13 execution: owner: "Ikenna Slot 1 main (operational
runbook owner; actual execution may be Slot 1 or Slot 6)" cadence: "one-shot (Gate 3 phase of 5-gate DAG; expected fire
before 2026-05-15 freeze-gate)" verifier: "event-stream receipt (triage.jsonl row count vs manifest phantom count;
manifest row state post-reconciliation)" last_executed: "2026-05-17 14:32-14:42 UTC — FIRED ✅ (0 phantoms all 5
asset_groups)" estimate_class: infra estimate_baseline_ai_days: 1 estimate_calibrated_ai_days: 0.8
estimate_calibration_note: | Backfilled 2026-05-15 per CLAUDE.md HARD RULE (post-2026-05-11 plans require
estimate_class). One-shot operational runbook (VM launch + manifest reconciliation + verifier check); infra class
multiplier 0.8x. Baseline 1 AI-day. Calibrated 0.8 AI-day. parent_epic: manifest_master priority: P2 status: active
locked_by: live-defi-rollout locked_since: 2026-05-21

---

# Gate 3 — Phantom-Audit Execution Runbook

> **✅ Gate 3 FIRED — 2026-05-17 14:42 UTC. All 5 asset_groups: 0 phantoms. Operator decision: ACCEPT.** cefi 0 / defi 0
> / tradfi 0 / sports 0 / prediction 0. All VMs: rc=0, DEPLOYMENT_COMPLETED, self-deleted. No triage JSONLs written (0
> phantoms = no records to write). Side-finding: TradFi 5,212 legacy-blank rows need
> `reconcile_legacy_blank_to_typed_reason --apply-flips` (see § "TradFi Side-Finding" below).

## Overview

**Purpose**: Verify manifest phantom count across all 5 asset_groups is acceptable for Gate 4 (writegate Phase 6.x
sweep + freeze-gate June).

**Gate 3 condition**: Run
`reconcile_phantom_manifest_rows_all.py --asset-group {cefi|defi|tradfi|sports|prediction} --dry-run` across all 5 asset
groups on a **real GCE VM** (not local) in **staging environment**, collect phantom counts from each run, aggregate
triage JSONLs, make operator disposition decision: **accept** (phantoms are known false-positives) vs **reject** (real
data-quality issue requiring pre-freeze mitigation).

**Why a real VM**: CLAUDE.md § "Plans Run To Actual Completion" requires every backfill / reconciliation / migration to
"run to natural shutdown with manifest-verified rows + sample-inspected parquets." Local smoke-test is not sufficient.

---

## Prerequisites

1. **GCS bucket exists and is readable**: `gs://{pid}-manifest/manifest.parquet` on all 5 asset_group partitions
   (verified by prior Gate 2 fire — STS transfers complete + parity verified).
2. **Launcher script exists**: `deployment-service/scripts/vm/launch-phantom-audit-vm.sh` (if not, use generic launcher
   pattern below).
3. **Manifest snapshot timestamp known**: UNIX timestamp of the manifest snapshot you're auditing (typically `date +%s`
   at reconciliation time, or use latest-write timestamp of `manifest.parquet`).
4. **Operator consent for VM cost**: Phantom audit VM runs reconciliation for all 5 asset_groups sequentially (~15–30min
   total, ~$0.50–1.00 cost on c2-standard-4 instance).

---

## Execution Steps

### Step 1: Bootstrap GCE VM (staging environment)

**Launcher command** (use canonical pattern from `deployment-service/scripts/vm/launch-phantom-audit-vm.sh` or construct
manually):

```bash
# If launcher exists (preferred):
cd deployment-service/scripts/vm
bash launch-phantom-audit-vm.sh

# Else, construct manual launcher (c2-standard-4, 30-min timeout, auto-shutdown on completion):
gcloud compute instances create phantom-audit-manifest-$(date +%s) \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --machine-type=c2-standard-4 \
  --zone=asia-northeast1-c \
  --boot-disk-size=50GB \
  --metadata=startup-script-url=gs://deployment-scripts-central-element-323112/startup/setup-data-pipeline-vm.sh,\
VM_ASSET_GROUP=cefi,\
DEPLOYMENT_ENV=staging,\
MANIFEST_SNAPSHOT_TIME=$(date +%s),\
VM_NAME=phantom-audit-manifest-$(date +%s),\
VM_SHUTDOWN_ON_COMPLETION=true \
  --scopes=cloud-platform \
  --no-address
```

**Verify launch**: Check `gcloud compute instances list --filter="name:phantom-audit-manifest"` — should show RUNNING
status within 30s.

---

### Step 2: Monitor Event Stream

**Event stream location**:
`gs://{pid}-events/events/instruments-service/{YYYY-MM-DD}/phantom-audit-manifest-*/hour={H}/*.jsonl`

**Expected sequence**:

1. **STARTED** event within 60s of launch (VM heartbeat).
2. **PROGRESS** events every ~30s from each asset_group (lines like
   `"event_type": "RECONCILIATION_STARTED", "asset_group": "cefi", ...`).
3. **Per-asset-group result events** (one per asset_group):
   ```json
   {
     "event_type": "RECONCILIATION_COMPLETED",
     "asset_group": "cefi",
     "phantom_count": 127,
     "rows_scanned": 1_850_000,
     "rows_in_triage_jsonl": 42,
     "triage_gcs_path": "gs://central-element-323112-phantom-triage/triage_cefi_2026_05_13_143022.jsonl",
     "return_code": 0
   }
   ```
4. **STOPPED** event at VM shutdown.

**Monitoring loop** (run in background terminal):

```bash
# Stream events for 30 minutes (sufficient for all 5 asset_groups to complete)
gcloud storage cp gs://{pid}-events/events/instruments-service/$(date +%Y-%m-%d)/phantom-audit-manifest-*/hour=*/*.jsonl - \
  2>/dev/null | jq -r 'select(.event_type | test("PROGRESS|COMPLETED|STARTED|STOPPED")) | "\(.timestamp) \(.event_type): \(.asset_group // "VM-level")"'
```

---

### Step 3: Collect Triage JSON Results

**Per-asset-group triage files** are written to GCS during the run. Retrieve them:

```bash
# Create local collection directory
mkdir -p /tmp/phantom_triage_$(date +%Y%m%d_%H%M%S)
TRIAGE_DIR=/tmp/phantom_triage_$(date +%Y%m%d_%H%M%S)

# Copy all triage files from GCS (5 total, one per asset_group)
for AG in cefi defi tradfi sports prediction; do
  TRIAGE_FILE=$(gcloud storage ls gs://central-element-323112-phantom-triage/triage_${AG}_*.jsonl 2>/dev/null | tail -1)
  if [ -n "$TRIAGE_FILE" ]; then
    gcloud storage cp "$TRIAGE_FILE" "$TRIAGE_DIR/"
    echo "✅ Retrieved $AG: $TRIAGE_FILE"
  else
    echo "⚠️ No triage file found for $AG (check event stream for errors)"
  fi
done

# Aggregate phantom counts
echo "Phantom count summary:"
for AF in $TRIAGE_DIR/triage_*.jsonl; do
  ASSET_GROUP=$(basename $AF | cut -d_ -f2)
  COUNT=$(wc -l < $AF)
  echo "  $ASSET_GROUP: $COUNT phantoms"
done
```

---

### Step 4: Assess Phantom Legitimacy

**Triage JSON schema** (each line is a phantom record):

```json
{
  "venue": "BINANCE",
  "data_type": "ohlcv_1h",
  "date": "2023-04-15",
  "instrument_id": "BTC/USDT",
  "manifest_status": "captured",
  "manifest_capture_time": "2023-04-15T12:00:00Z",
  "parquet_row_count": 0,
  "reason": "zero_activity_bar_written_placeholder",
  "confidence": 0.95,
  "recommendation": "accept"
}
```

**Per-record decision**:

- `recommendation: "accept"` — known data-quality pattern (e.g., venue-halted day, zero-activity bar, pre-launch). **DO
  NOT fix.**
- `recommendation: "reject"` — real data corruption. Requires pre-freeze investigation + fix.
- `confidence < 0.8` — uncertain; requires manual spot-check.

**Spot-check high-confidence REJECT entries**:

```bash
# For each high-confidence rejection:
cd instruments-service
python -c "
import pandas as pd
# Read the parquet file for the phantom's (venue, date, data_type)
df = pd.read_parquet('gs://central-element-323112/cefi/ohlcv_1h/by_date/2023-04-15/BINANCE.parquet')
print(f'Rows in parquet: {len(df)}')
if len(df) > 0:
    print(df.head(10)[['instrument_id', 'timestamp', 'open', 'close']])
else:
    print('Parquet is empty — phantom is real')
"
```

---

### Step 5: Operator Disposition Decision

**Collect phantom summary**:

```
Phantom Audit Summary — 2026-05-13 Gate 3 Run
==============================================

Asset Group | Phantom Count | Recommendation | Notes
------------|---------------|-----------------|-------
cefi        | 127           | ACCEPT          | All zero-activity bars (known pattern)
defi        | 89            | ACCEPT          | 88 pre-launch (Uniswap V4), 1 under investigation
tradfi      | 342           | REJECT (1)      | 341 accept; 1 real gap (CME missing 2026-04-03)
sports      | 0             | —               | Clean
prediction  | 0             | —               | Clean

AGGREGATE: 558 phantoms | 557 ACCEPT | 1 REJECT (needs pre-freeze fix)
Gate 3 Condition: ACCEPT or REJECT?
Operator Call: ACCEPT IF 1-CME fix is scoped to pre-freeze; REJECT IF deferred post-freeze.
```

**Operator calls** (coordinate via Slack or ping ledger):

- If all phantoms are ACCEPT → **Gate 3 FIRES** ✅. Proceed to Phase 6.x sweep + freeze-gate.
- If any REJECT with high confidence → **Operator decides**: (A) pre-freeze mitigation (pull into active plan) OR (B)
  descope to post-freeze + accept risk (not recommended for TradFi venue).

---

## Success Criteria

✅ **Gate 3 FIRED** when:

1. Phantom-audit VM ran to completion across all 5 asset_groups (STOPPED event received).
2. Triage JSONL for each asset_group collected + reviewed.
3. All phantoms classified as ACCEPT OR high-confidence REJECT are scoped to pre-freeze fix.
4. Operator disposition decision documented in this runbook § "Operator Disposition Decision" and in ping ledger.
5. Plan body (`master_to_live_defi_2026_05_23.md` § "Gate status") updated with Gate 3 decision + phantom summary.

✅ **Successor gate unblocked**: Gate 4 (Phase 6.3-6.9 push + workspace flip) once Gate 3 + freeze-gate Phase 1 both
complete.

---

## Runbook Execution Record

| Date       | Operator     | Status                    | Phantom Count                                                                | Operator Decision  | Notes                                                                                                                                                                                                                                                                                                                                                                                              |
| ---------- | ------------ | ------------------------- | ---------------------------------------------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-11 | ikenna       | PARTIAL — no triage JSONL | cefi 2223 / defi 0 (false-pos) / tradfi 3976 / prediction 71 / sports 115524 | PENDING            | Ran via `launch-defi-phantom-recon-vm.sh` dry-run. Script lacked `--triage-output-gcs` feature at this time; triage JSONLs NOT written. Full analysis in `code_freeze_migrate_backfill_sequencing_2026_05_10.md` § DONE-2026-05-11 phantom-audit.                                                                                                                                                  |
| 2026-05-17 | ikenna-slot1 | FIRED ✅                  | cefi 0 / defi 0 / tradfi 0 / sports 0 / prediction 0                         | ACCEPT (all clean) | All 5 VMs: rc=0, DEPLOYMENT_COMPLETED, self-deleted. 0 phantoms across all asset_groups (manifests fully clean). No triage JSONLs written (0 phantom records). Side-finding: TradFi 5,212 legacy-blank rows (5,099 → LegacyBlankErrorReasonError + 113 → EXPECTED_PARTIAL_HALF_DAY) found by reconcile_legacy_blank_to_typed_reason scan-only; apply-flips run needed (todo filed in tradfi plan). |

---

## TradFi Side-Finding — Legacy Blank Rows Need Apply-Flips Run

**Finding (2026-05-17 Gate 3 run)**: `reconcile_legacy_blank_to_typed_reason` scan-only found 5,212 TradFi rows that
would upgrade if `--apply-flips` were passed:

| Transition                                                                            | Count |
| ------------------------------------------------------------------------------------- | ----- |
| `empty_confirmed/SOURCE_RETURNED_ZERO → attempted_failed/LegacyBlankErrorReasonError` | 5,099 |
| `SOURCE_RETURNED_ZERO → EXPECTED_PARTIAL_HALF_DAY`                                    | 113   |

**Required action**: Run `reconcile_legacy_blank_to_typed_reason --asset-group tradfi --apply-flips` on a VM.

**Status**:
`- [x] ✅ [MIGRATED] P2. TradFi 5,212 legacy-blank apply-flips run — migrated to tradfi_master.md § "TradFi 5,212 legacy-blank apply-flips run" (pm@ca914697). pm@<flip-sha>.`

**Why not done now**: The CSV report was on the VM (now self-deleted). A fresh VM run with `--apply-flips` is safe
(scan-only already confirmed the upgrade logic is correct; 0 uncertain cases).

---

## Appendix: Reconciliation Script Reference

**Location**: `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`

**Usage**: `python reconcile_phantom_manifest_rows_all.py --asset-group {cefi|defi|tradfi|sports|prediction} --dry-run`

**Key arguments**:

- `--asset-group`: Required. Single asset group per run.
- `--dry-run`: Do NOT apply flips to manifest; collect triage JSONL only (safe for Gate 3).
- `--manifest-snapshot-time`: (Optional) ISO timestamp of manifest snapshot. If absent, uses current timestamp.
- `--triage-output-gcs`: (Optional) GCS path to write triage JSONL. Defaults to
  `gs://central-element-323112-phantom-triage/triage_{asset_group}_{timestamp}.jsonl` when in `--dry-run` mode. Shipped:
  instruments-service@9e2c4bb (2026-05-17).

**Script guarantees** (per CLAUDE.md):

- **Readonly on manifest**: `--dry-run` flag prevents any manifest writes.
- **Cluster-validation enabled**: Script validates instrument-cluster consistency for bundled data_types.
- **Per-shard isolation** (if multi-worker): `VM_NAME` + `MANIFEST_PER_VM_SHARDS=true` prevent manifest write races.

---

## Deferred work — migrated to

| Item                                      | Migrated To                                                                  | Status                                                                                                                                                                  |
| ----------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TradFi 5,212 legacy-blank apply-flips run | `plans/epics/tradfi_master.md` § "TradFi 5,212 legacy-blank apply-flips run" | `- [ ] [SCRIPT] P2` — **BLOCKED-OPERATOR 2026-05-20 slot-6**: requires VM run with `--apply-flips`; operator must schedule + approve VM launch; ping filed `slot_6.md`. |

---

## References

- **5-gate DAG**: `work_split_2026_05_12_ikenna.md` line 494–502.
- **Manifest schema + phantom audit**: `/codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit".
- **Execution ownership**: `plans/active/issues/runbook_execution_governance_gaps_2026_05_08.md` (runbook-ownership
  SSOT).
- **Master plan Gate 3 status**: `master_to_live_defi_2026_05_23.md` § "Gate status" (update row with runbook-execution
  result).
