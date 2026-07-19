---
doc_type: codex-ssot
title: GCS Lifecycle Policies — Cost + List-Latency Controls
summary:
  "SSOT for delete-after-N-days GCS bucket lifecycle rules: deployment-scripts vm-logs/ purged at 14 days,
  central-element-323112-deployment-events quality_gates_snapshot/ at 30 days, central-element-323112-events events/ at
  90 days. Bounds storage cost + list-latency (vm_zombie_watchdog walks vm-logs/). Honest-coverage + strategy/
  execution/manifest buckets intentionally NOT lifecycle'd. Includes apply/re-apply + drift-detection commands."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-service]
scope: [admin, engineer]
tags: [infrastructure, cost, gcs, monitoring, deployment-service, runbook]
related: [gcs-object-operations.md, manifest-consolidator-ssot.md, live-deployment-monitoring.md]
created: 2026-05-16
authoritative_for: [gcs bucket delete-after-N-days lifecycle rules]
referenced_by: [codex/05-infrastructure/gcs-object-operations.md]
owner:
last_reviewed: 2026-05-16
code_refs:
type: reference
---

# GCS Lifecycle Policies — Cost + List-Latency Controls

> SSOT for delete-after-N-days lifecycle rules across the workspace's GCS buckets. Applied 2026-05-16 by slot-8 per
> [`plans/active/issues/deployment_events_lifecycle_audit_2026_05_15.md`](../../plans/archive/issues/deployment_events_lifecycle_audit_2026_05_15.md)
> (operator-acked: ADC admin perms on `central-element-323112` cover GCS lifecycle ops per CLAUDE.md "Plans Run To
> Actual Completion" HARD RULE).

## Why lifecycle policies

1. **Storage cost**: unbounded accumulation grows GCS bill linearly. `vm-logs/` alone was 4145 dirs as of 2026-05-16.
2. **List-bucket latency**: `gsutil ls` on directories with 4k+ entries takes 4+ seconds. `vm_zombie_watchdog.py` walks
   `vm-logs/` paths; bounded directory size keeps watchdog response fast.
3. **Audit trail clarity**: snapshots / event logs older than the documented retention window have no operational value;
   deletion is itself a form of "we know what we keep and why."
4. **GCS lifecycle is delete-only**: rules never modify in-flight data. Lowest-risk infra op in the workspace.

## Applied policies (current state — 2026-05-16)

### `gs://deployment-scripts-central-element-323112/` — 14-day `vm-logs/` purge

```json
{ "rule": [{ "action": { "type": "Delete" }, "condition": { "age": 14, "matchesPrefix": ["vm-logs/"] } }] }
```

- **Why 14 days**: covers the typical debugging window after a VM run. Beyond 14 days, logs are forensic-only and GCS
  bucket access cost > grep'ing the log.
- **What's protected**: `code/` tarballs (no lifecycle — they roll naturally per CI push).
- **Apply / re-apply**:
  ```bash
  gsutil lifecycle set <(echo '{"rule":[{"action":{"type":"Delete"},"condition":{"age":14,"matchesPrefix":["vm-logs/"]}}]}') \
    gs://deployment-scripts-central-element-323112/
  ```
- **Verify**: `gsutil lifecycle get gs://deployment-scripts-central-element-323112/`

### `gs://central-element-323112-deployment-events/` — 30-day QG snapshot retention

```json
{
  "rule": [{ "action": { "type": "Delete" }, "condition": { "age": 30, "matchesPrefix": ["quality_gates_snapshot/"] } }]
}
```

- **Why 30 days**: the `deployment-api /api/repos/deploy-ready` endpoint reads only the latest snapshot per repo. 30-day
  history covers ad-hoc trend queries; deeper analysis can be repointed to a BigQuery sink (post-cutover).
- **Apply / re-apply**:
  ```bash
  gsutil lifecycle set <(echo '{"rule":[{"action":{"type":"Delete"},"condition":{"age":30,"matchesPrefix":["quality_gates_snapshot/"]}}]}') \
    gs://central-element-323112-deployment-events/
  ```

### `gs://central-element-323112-events/` — 90-day service-event retention

```json
{ "rule": [{ "action": { "type": "Delete" }, "condition": { "age": 90, "matchesPrefix": ["events/"] } }] }
```

- **Why 90 days**: covers cross-quarter ops debugging + post-mortem windows. Service-event JSONL is high-volume (every
  VM emits STARTED + PROGRESS + STOPPED + FAILED).
- **What's protected**: bucket root + non-`events/` prefixes are untouched.
- **Apply / re-apply**:
  ```bash
  gsutil lifecycle set <(echo '{"rule":[{"action":{"type":"Delete"},"condition":{"age":90,"matchesPrefix":["events/"]}}]}') \
    gs://central-element-323112-events/
  ```

## Buckets intentionally NOT lifecycle'd (and why)

- **`gs://central-element-323112-honest-coverage/`** — only 287 KB/day; 1-year retention by default supports
  year-over-year coverage drift analysis. Scheduled re-evaluation: 2027-05.
- **`gs://*-store-*` strategy / execution / risk / pnl-store buckets** — strategy outputs are durable artifacts;
  lifecycle is owned by the strategy / strategy-store retention spec, not deployment-service.
  > **Updated 2026-07-19 (Wave-3 folds)**: the folded Group B buckets (`features-{ag}`, `ml-store`, `execution-store`,
  > `strategy-store`, `portfolio-state`) were **provisioned with a `STANDARD → COLDLINE @ 60d` lifecycle by default**
  > (the canonical folded-bucket default, applied at `gcloud storage buckets create` time). Exception:
  > **`portfolio-state-{prd}` is a confirm-before-COLDLINE case** — live position/pnl/risk snapshots may need STANDARD
  > longer than 60d; the 60d default is applied but flagged for operator retention confirmation
  > (`bucket_fold_portfolio_state_2026_07_17.md` § IAM + lifecycle todo, design §2.E). So these buckets ARE
  > lifecycle-managed (COLDLINE class-transition), NOT delete-expired — the "durable artifacts, no expiry" intent holds
  > for object _deletion_; only the storage class transitions.
- **`gs://market-data-tick-*` / `gs://instruments-store-*`** — manifest snapshot retention is governed by the manifest
  consolidator's `_index/snapshots/` retention spec, not generic lifecycle.

## Drift detection

To check that all 3 policies remain applied (workspace-QG-runnable):

```bash
for bucket in \
  gs://deployment-scripts-central-element-323112/ \
  gs://central-element-323112-deployment-events/ \
  gs://central-element-323112-events/; do
  echo "=== $bucket ==="
  gsutil lifecycle get "$bucket" 2>&1 | head -5
done
```

Expected: each prints a single `{"rule":[...]}` line. Missing or empty → re-apply per § "Applied policies".

## References

- Issue doc:
  [`plans/active/issues/deployment_events_lifecycle_audit_2026_05_15.md`](../../plans/archive/issues/deployment_events_lifecycle_audit_2026_05_15.md)
- VM watchdog: `deployment-service/scripts/vm/vm_zombie_watchdog.py` (consumer of `vm-logs/`)
- QG snapshot cron: `deployment-service/scripts/vm/launch-qg-snapshot-vm.sh` (producer of `quality_gates_snapshot/`)
- Event-stream HARD RULE: CLAUDE.md "No fire-and-forget VM launches (CRITICAL)" — STARTED + ≥1 progress/hr + STOPPED.
