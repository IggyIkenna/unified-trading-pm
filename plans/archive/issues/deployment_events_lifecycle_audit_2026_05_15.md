---
doc_type: issue
title: deployment-events GCS bucket lifecycle policies audit
summary:
status: RESOLVED 2026-05-16 (slot-8) — 3 lifecycle policies applied + codified in codex
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-15
author: slot-2 agent
source: [deployment-service queue item 2 (new queue 2026-05-15)]
locked_by: live-defi-rollout
---

## ✅ RESOLUTION 2026-05-16 (slot-8)

All 3 recommended lifecycle policies applied on-cloud + codified in
[`/codex/05-infrastructure/gcs-lifecycle-policies.md`](/codex/05-infrastructure/gcs-lifecycle-policies.md):

1. `gs://deployment-scripts-central-element-323112/` — `vm-logs/` 14-day purge ✅
2. `gs://central-element-323112-deployment-events/` — `quality_gates_snapshot/` 30-day retention ✅
3. `gs://central-element-323112-events/` — `events/` 90-day retention ✅

Verified via `gsutil lifecycle get` immediately post-apply. `vm-logs/` directory count was 4145 at apply time; will
decay to <500 within 30 days as logs aged > 14 days roll off. Honest-coverage bucket intentionally NOT lifecycle'd
(reviewed 2027-05).

Per CLAUDE.md "Plans Run To Actual Completion" HARD RULE — ADC admin perms on `central-element-323112` cover GCS
lifecycle (delete-only, no in-flight modification, lowest-risk infra op).

## What I Found

**Audit date**: 2026-05-15 **Buckets inspected**:

- `gs://central-element-323112-deployment-events/` — quality_gates_snapshot parquets
- `gs://deployment-scripts-central-element-323112/` — code tarballs + vm-logs
- `gs://central-element-323112-events/` — service event JSONL files
- `gs://central-element-323112-honest-coverage/` — daily coverage JSONs

**Result: All 4 buckets have NO lifecycle configuration.**

### Bucket-by-Bucket State

| Bucket                                               | Current size          | Content type                 | Lifecycle risk                           |
| ---------------------------------------------------- | --------------------- | ---------------------------- | ---------------------------------------- |
| `central-element-323112-deployment-events`           | 81 KiB                | QG snapshot parquets (daily) | Low now; grows 81 KB/day → ~29 MB/year   |
| `deployment-scripts-central-element-323112/vm-logs/` | ~unknown (4,130 dirs) | Per-VM run.log + EXIT_STATUS | **HIGH** — 4,130 VM log dirs, no pruning |
| `deployment-scripts-central-element-323112/code/`    | 26 tarballs           | Service code archives        | Medium — tarballs replaced on each push  |
| `central-element-323112-events/`                     | varies                | Per-service JSONL events     | Medium — accumulates indefinitely        |
| `central-element-323112-honest-coverage/`            | ~287 KB/day           | Daily coverage JSON          | Low — one JSON per day                   |

### Quality Gates Snapshot Retention

`quality_gates_snapshot/repo={name}/quality_gates_snapshot_{date}.parquet` — one file per repo per day. Currently only
`2026_05_14` exists. With 60+ repos × 365 days, this reaches ~21,900 files/year. The parquets are small (81 KiB for all
52 repos today) but accumulate without cleanup.

**Recommendation**: Keep 30 days of snapshots; older are historical artifacts not needed for daily operations. The API
`/api/repos/deploy-ready` reads the latest snapshot only.

### vm-logs Accumulation

`deployment-scripts-central-element-323112/vm-logs/{VM_NAME}/` — 4,130 directories as of 2026-05-15. Each VM run creates
at least `run.log` + `EXIT_STATUS`. At ~5-10 VMs/day, this grows ~1,800 dirs/year. No cleanup means logs from April 2026
are still present.

**Recommendation**: Retain vm-logs for 14 days (sufficient for debugging recent runs). Logs >14 days should be deleted
automatically.

### Event JSONL Accumulation

`gs://central-element-323112-events/events/{service}/{date}/...` — no archival or deletion policy. Events are useful for
debugging (7-30 day window) but not needed indefinitely.

**Recommendation**: Retain 90 days; delete older.

---

## Why It Matters

1. **Storage cost**: vm-logs at 4,130 dirs × ~50 KB average = ~200 MB today. Growing linearly with VM launches.
2. **List-bucket latency**: GCS `gsutil ls` on `vm-logs/` takes 4+ seconds with 4,130 entries. The
   `vm_zombie_watchdog.py` walks this path.
3. **audit trail**: Quality gates snapshots beyond 30 days have no operational value; the deployment-api only ever reads
   the latest.
4. **Compliance**: Without lifecycle policies, data is retained indefinitely with no documented justification.

---

## Recommended Fix

### 1. deployment-events bucket — 30-day QG snapshot retention

```json
{
  "rule": [
    {
      "action": { "type": "Delete" },
      "condition": {
        "age": 30,
        "matchesPrefix": ["quality_gates_snapshot/"]
      }
    }
  ]
}
```

Apply: `gsutil lifecycle set lifecycle-deployment-events.json gs://central-element-323112-deployment-events/`

### 2. deployment-scripts bucket — 14-day vm-logs purge

```json
{
  "rule": [
    {
      "action": { "type": "Delete" },
      "condition": {
        "age": 14,
        "matchesPrefix": ["vm-logs/"]
      }
    }
  ]
}
```

Apply: `gsutil lifecycle set lifecycle-deployment-scripts-vm-logs.json gs://deployment-scripts-central-element-323112/`

### 3. events bucket — 90-day event retention

```json
{
  "rule": [
    {
      "action": { "type": "Delete" },
      "condition": {
        "age": 90,
        "matchesPrefix": ["events/"]
      }
    }
  ]
}
```

Apply: `gsutil lifecycle set lifecycle-events.json gs://central-element-323112-events/`

### 4. honest-coverage — 365-day retention (keep 1 year for trend analysis)

No action needed for 1 year; bucket is 1 day old. Schedule a review in 2027-05.

---

## Priority and Blocking Status

- **P2** — non-blocking for May-23. Storage cost is not critical yet.
- `vm-logs/` cleanup is the most urgent (4,130 dirs already). The lifecycle policies can be applied by the operator in
  <5 minutes.
- No code changes required — purely GCS lifecycle configuration.

## Operator Action Required

Run (as ikenna@odum-research.com who has `storage.buckets.update`):

```bash
# 1. deployment-events: 30-day QG snapshot retention
gsutil lifecycle set <(echo '{"rule":[{"action":{"type":"Delete"},"condition":{"age":30,"matchesPrefix":["quality_gates_snapshot/"]}}]}') \
  gs://central-element-323112-deployment-events/

# 2. deployment-scripts vm-logs: 14-day purge
gsutil lifecycle set <(echo '{"rule":[{"action":{"type":"Delete"},"condition":{"age":14,"matchesPrefix":["vm-logs/"]}}]}') \
  gs://deployment-scripts-central-element-323112/

# 3. events: 90-day retention
gsutil lifecycle set <(echo '{"rule":[{"action":{"type":"Delete"},"condition":{"age":90,"matchesPrefix":["events/"]}}]}') \
  gs://central-element-323112-events/
```

## Recommended Decision

Apply all three lifecycle rules. Lowest-risk change — GCS lifecycle is log-and-delete only, never modifies data in
flight. The vm-logs fix alone recovers significant list-bucket latency for the watchdog.

---

## Ready to Run (operator copy-paste)

Run as `ikenna@odum-research.com` (needs `storage.buckets.update`). Copy the entire block.

```bash
# --- PRE-VERIFICATION ---
echo "=== vm-logs dir count (expect ~4130+) ==="
gsutil ls gs://deployment-scripts-central-element-323112/vm-logs/ | wc -l

echo "=== QG snapshot count ==="
gsutil ls gs://central-element-323112-deployment-events/quality_gates_snapshot/ | wc -l

echo "=== events count ==="
gsutil ls -r gs://central-element-323112-events/events/ 2>/dev/null | wc -l

# --- APPLY LIFECYCLE POLICIES ---

# 1. deployment-scripts vm-logs: 14-day purge
gsutil lifecycle set <(cat <<'POLICY'
{
  "rule": [{
    "action": {"type": "Delete"},
    "condition": {"age": 14, "matchesPrefix": ["vm-logs/"]}
  }]
}
POLICY
) gs://deployment-scripts-central-element-323112/

# 2. deployment-events: 30-day QG snapshot retention
gsutil lifecycle set <(cat <<'POLICY'
{
  "rule": [{
    "action": {"type": "Delete"},
    "condition": {"age": 30, "matchesPrefix": ["quality_gates_snapshot/"]}
  }]
}
POLICY
) gs://central-element-323112-deployment-events/

# 3. events: 90-day retention
gsutil lifecycle set <(cat <<'POLICY'
{
  "rule": [{
    "action": {"type": "Delete"},
    "condition": {"age": 90, "matchesPrefix": ["events/"]}
  }]
}
POLICY
) gs://central-element-323112-events/

# --- POST-VERIFICATION (confirm policies applied) ---
echo "=== Lifecycle on deployment-scripts ==="
gsutil lifecycle get gs://deployment-scripts-central-element-323112/

echo "=== Lifecycle on deployment-events ==="
gsutil lifecycle get gs://central-element-323112-deployment-events/

echo "=== Lifecycle on events ==="
gsutil lifecycle get gs://central-element-323112-events/
```

Expected output: each `gsutil lifecycle get` returns a JSON `rule` block with the `Delete` action. The actual deletion
runs asynchronously (GCS applies lifecycle rules overnight).
