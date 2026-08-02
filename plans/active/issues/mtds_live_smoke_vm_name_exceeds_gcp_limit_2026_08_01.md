---
doc_type: issue
title: data-pipeline-check-mtds live-leg VM name can exceed GCP's 63-char instance-name limit
summary:
  pipeline_e2e_check.py's mtds-live-smoke VM name is built from the raw shard_spec (asset_group:venue:data_type) +
  timestamp with no length bound, so long venue/data_type combos exceed GCP's 63-char instance-name limit and the
  live-leg fails at VM creation before it can prove anything.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [mtds, vm-launcher, pipeline-e2e-check]
related: []
created: 2026-08-01
assigned_vm: planning
parent_epic: infrastructure_master
source: [market-tick-data-service/scripts/pipeline_e2e_check.py]
priority: P3
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# data-pipeline-check-mtds live-leg VM name can exceed GCP's 63-char instance-name limit

## What I found

Running
`data-pipeline-check-mtds --asset-group SPORTS --day 2025-12-20 --legs force,skip,live --require-captured --auto-day`
for real against sports hit the same failure twice on two different cells:

```
ERROR: (gcloud.compute.instances.create) Could not fetch resource:
 - Invalid value for field 'resource.name': 'mtds-live-smoke-sports-betfair-sb-uk-odds-snapshot-20260801-113100'.
   Must be a match of regex '(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)'
```

and again for `mtds-live-smoke-sports-betfair-sb-uk-arbitrage-opportunity-20260801-114654` (61 chars — right at the GCE
instance-name cap once GCE's own length ceiling is hit; both names are 62-64 chars, over the 63-char limit). Root cause:
`scripts/pipeline_e2e_check.py:2141`:

```python
vm_name = f"mtds-live-smoke-{shard_spec.replace(':', '-').replace('_', '-').lower()}-{run_ts}"
```

builds the VM name from the full, un-truncated `asset_group:venue:data_type` shard spec plus a timestamp, with no length
bound. Sports has several long venue names (`BETFAIR_SB_UK`, `BETFAIR_EX_UK`, `BETFAIR_EX_EU`) and long data_types
(`arbitrage_opportunity`, `odds_horizon_bucket`) — combinations of these push the name past GCP's 63-char
`instance-name` limit, so `gcloud compute instances create` rejects it before the live-leg can run at all. The checker
retries 3x (all fail identically, `launch-mtds-live.sh` never truncates either) then correctly marks the cell `failed`
and moves on (shard-level isolation working as intended) — but the live-leg verdict for that cell is a false negative
caused by naming, not a real pipeline finding.

## Why it matters

Every sports live-leg cell whose `venue:data_type` combination is long enough blocks `data-pipeline-check-mtds` from
ever proving the live leg for that cell, masking whatever the real live-producer health is. Confirmed on 2 of the first
~11 cells checked (BETFAIR_SB_UK/odds_snapshot, BETFAIR_SB_UK/arbitrage_opportunity) — likely recurs on every
BETFAIR_SB_UK/BETFAIR_EX_UK/BETFAIR_EX_EU cell paired with a long data_type.

## Recommended decision

Bound the generated VM name to GCP's 63-char limit — e.g. truncate/hash the `shard_spec` portion (keep the `run_ts`
suffix intact for uniqueness) once the combined name would exceed 63 chars, or switch to a shorter deterministic scheme
(e.g. a hash of `shard_spec` instead of the literal slugified string) for the live-leg name generator specifically at
`pipeline_e2e_check.py:2141`.

## Todos

- [ ] [BACKEND] P3. Bound `mtds-live-smoke-*` VM names to GCP's 63-char instance-name limit in
      `market-tick-data-service/scripts/pipeline_e2e_check.py:2141` (truncate/hash the shard_spec portion, keep `run_ts`
      for uniqueness). (repo: market-tick-data-service). **Done when**: a live-leg cell for a long venue/data_type combo
      (e.g. `SPORTS:BETFAIR_SB_UK:arbitrage_opportunity`) no longer fails at `gcloud compute instances create` with an
      `Invalid value for field 'resource.name'` error.
