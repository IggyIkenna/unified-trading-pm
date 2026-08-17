---
doc_type: codex-ssot
title: GCS Lifecycle Policies — Cost + List-Latency Controls
summary: "SSOT for GCS bucket lifecycle rules: deployment-scripts has 3 delete rules (vm-logs/ @14d, vm-heartbeat/ @15d,
  logs/recon-logs/audit-results/etc @30d); central-element-323112-deployment-events + central-element-323112-events
  are now bucket-wide STANDARD→COLDLINE storage-class-transition rules (@14d, @60d respectively) — NOT delete rules,
  superseding the original delete-after-30/90-days design. Bounds storage cost + list-latency (vm_zombie_watchdog walks
  vm-logs/). Honest-coverage + strategy/execution/manifest buckets intentionally NOT lifecycle'd. Includes apply/
  re-apply + drift-detection commands."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-service]
scope: [admin, engineer]
tags: [infrastructure, cost, gcs, monitoring, deployment-service, runbook]
related:
  [
    /codex/05-infrastructure/gcs-object-operations.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/live-deployment-monitoring.md,
  ]
created: 2026-05-16
authoritative_for: [gcs bucket lifecycle rules (delete + storage-class-transition)]
referenced_by: [/codex/05-infrastructure/gcs-object-operations.md]
owner:
last_reviewed: 2026-08-17
code_refs:
type: reference
---

# GCS Lifecycle Policies — Cost + List-Latency Controls

> SSOT for lifecycle rules across the workspace's GCS buckets. Originally applied 2026-05-16 by slot-8 per
> [`plans/active/issues/deployment_events_lifecycle_audit_2026_05_15.md`](../../plans/archive/issues/deployment_events_lifecycle_audit_2026_05_15.md)
> (operator-acked: ADC admin perms on `central-element-323112` cover GCS lifecycle ops per CLAUDE.md "Plans Run To
> Actual Completion" HARD RULE). **Re-verified live 2026-08-17 (slot-18 codex-freshness sweep) — the deployment-events
> and events buckets have DRIFTED from the original delete-after-N-days design to bucket-wide storage-class-transition
> rules (see below); this doc's "Applied policies" section now reflects the LIVE state, not the original design.**

## Why lifecycle policies

1. **Storage cost**: unbounded accumulation grows GCS bill linearly. `vm-logs/` alone was 4145 dirs as of 2026-05-16.
2. **List-bucket latency**: `gsutil ls` on directories with 4k+ entries takes 4+ seconds. `vm_zombie_watchdog.py` walks
   `vm-logs/` paths; bounded directory size keeps watchdog response fast.
3. **Audit trail clarity**: snapshots / event logs older than the documented retention window have no operational value;
   deletion is itself a form of "we know what we keep and why."
4. **Not every rule below is delete-only anymore** (see the two drifted buckets) — a storage-class transition never
   deletes data, but still bounds STANDARD-class cost the same way a delete rule bounds total object count.

## Applied policies (LIVE state, re-verified via `gsutil lifecycle get` — 2026-08-17)

### `gs://deployment-scripts-central-element-323112/` — 3 delete rules

```json
{
  "rule": [
    { "action": { "type": "Delete" }, "condition": { "age": 14, "matchesPrefix": ["vm-logs/"] } },
    { "action": { "type": "Delete" }, "condition": { "age": 15, "matchesPrefix": ["vm-heartbeat/"] } },
    {
      "action": { "type": "Delete" },
      "condition": {
        "age": 30,
        "matchesPrefix": [
          "logs/",
          "recon-logs/",
          "audit-results/",
          "migration-bundle/staging/",
          "log-archive/",
          "deployments/archive/"
        ]
      }
    }
  ]
}
```

- **Why 14 days on `vm-logs/`**: covers the typical debugging window after a VM run. Beyond 14 days, logs are
  forensic-only and GCS bucket access cost > grep'ing the log.
- **`vm-heartbeat/` @15 days and the 6-prefix @30-days rule are ADDITIONS since the original 2026-05-16 design** (not
  yet traced to a specific plan/commit as of this re-verification — if you land the provenance, cite it here).
- **What's protected**: `code/` tarballs (no lifecycle — they roll naturally per CI push).
- **Apply / re-apply** (full 3-rule set, matching live):
  ```bash
  gsutil lifecycle set <(echo '{"rule":[
    {"action":{"type":"Delete"},"condition":{"age":14,"matchesPrefix":["vm-logs/"]}},
    {"action":{"type":"Delete"},"condition":{"age":15,"matchesPrefix":["vm-heartbeat/"]}},
    {"action":{"type":"Delete"},"condition":{"age":30,"matchesPrefix":["logs/","recon-logs/","audit-results/","migration-bundle/staging/","log-archive/","deployments/archive/"]}}
  ]}') gs://deployment-scripts-central-element-323112/
  ```
- **Verify**: `gsutil lifecycle get gs://deployment-scripts-central-element-323112/`

### `gs://central-element-323112-deployment-events/` — bucket-wide STANDARD→COLDLINE @14 days (NOT a delete rule)

```json
{
  "rule": [
    {
      "action": { "type": "SetStorageClass", "storageClass": "COLDLINE" },
      "condition": { "age": 14, "matchesStorageClass": ["STANDARD"] }
    }
  ]
}
```

- **DRIFTED from the original design.** The doc originally specified a 30-day DELETE on `quality_gates_snapshot/` only.
  The live rule is a bucket-wide (no `matchesPrefix`) storage-class transition at 14 days — objects are demoted to
  COLDLINE, never deleted, and the transition applies to every prefix, not just `quality_gates_snapshot/`.
  `deployment-api /api/repos/deploy-ready` still reads only the latest snapshot per repo, so this doesn't break reads,
  but COLDLINE has a higher per-op read cost + 90-day minimum storage duration — worth knowing before scripting bulk
  reads over this bucket.
- **Apply / re-apply** (matches live):
  ```bash
  gsutil lifecycle set <(echo '{"rule":[{"action":{"type":"SetStorageClass","storageClass":"COLDLINE"},"condition":{"age":14,"matchesStorageClass":["STANDARD"]}}]}') \
    gs://central-element-323112-deployment-events/
  ```

### `gs://central-element-323112-events/` — bucket-wide STANDARD→COLDLINE @60 days (NOT a delete rule)

```json
{ "rule": [{ "action": { "type": "SetStorageClass", "storageClass": "COLDLINE" }, "condition": { "age": 60 } }] }
```

- **DRIFTED from the original design.** The doc originally specified a 90-day DELETE on `events/`. The live rule is a
  bucket-wide storage-class transition at 60 days (no `matchesPrefix`, no `matchesStorageClass` condition — applies to
  every object regardless of current class) — objects are demoted to COLDLINE, never deleted. Service-event JSONL is
  never purged under the current live rule; the original "why 90 days" cost-bound rationale (delete after 90 days) no
  longer describes reality — the bucket now grows unbounded in object count, just cheaper per-object after 60 days.
- **Apply / re-apply** (matches live):
  ```bash
  gsutil lifecycle set <(echo '{"rule":[{"action":{"type":"SetStorageClass","storageClass":"COLDLINE"},"condition":{"age":60}}]}') \
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

To check the 3 policies' LIVE shape (workspace-QG-runnable) — note two of them are now storage-class-transition rules,
not delete rules, so "a rule exists" is the invariant to check, not "objects get deleted":

```bash
for bucket in \
  gs://deployment-scripts-central-element-323112/ \
  gs://central-element-323112-deployment-events/ \
  gs://central-element-323112-events/; do
  echo "=== $bucket ==="
  gsutil lifecycle get "$bucket" 2>&1 | head -5
done
```

Expected (as of 2026-08-17): `deployment-scripts-*` prints a 3-rule `Delete` JSON; the other two each print a
single-rule `SetStorageClass`→`COLDLINE` JSON (age 14 and 60 respectively). Missing or empty → re-apply per §
"Applied policies". A rule shape that differs from what's printed above is itself a drift signal — update this doc
rather than assuming the doc is still right.

## References

- Issue doc:
  [`plans/active/issues/deployment_events_lifecycle_audit_2026_05_15.md`](../../plans/archive/issues/deployment_events_lifecycle_audit_2026_05_15.md)
- VM watchdog: `deployment-service/scripts/vm/vm_zombie_watchdog.py` (consumer of `vm-logs/`)
- QG snapshot cron: `deployment-service/scripts/vm/launch-qg-snapshot-vm.sh` (producer of `quality_gates_snapshot/`)
- Event-stream HARD RULE: CLAUDE.md "No fire-and-forget VM launches (CRITICAL)" — STARTED + ≥1 progress/hr + STOPPED.
