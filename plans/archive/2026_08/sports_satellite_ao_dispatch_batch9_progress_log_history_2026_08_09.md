---
doc_type: issue
title: Sports satellite AO batch 9 — Progress Log history (Transfermarkt PLAYER_VALUES backfill, 2026-08-07..08)
summary:
  Line-cap remediation extraction from plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md's Progress Log —
  the three intermediate status-snapshot entries for VM `tm-backfill-20260807-233040` (launch + two pre-compact
  checkpoints while it cycled through Transfermarkt 502 retries), moved verbatim so the live doc stays under the
  1000-line hard cap. Fully superseded by the live doc's terminal "Todo 2 — BLOCKED-UPSTREAM-OUTAGE" entry (the VM was
  killed and the outcome recorded there); read this only if a deeper citation on the intermediate polling detail is
  needed.
status: archived
nature: notes
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [sports, ao-dispatch, batch-9, history, line-cap-remediation, progress-log]
related: [/plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md]
created: 2026-08-09
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
last_updated: 2026-08-09
supersedes:
superseded_by:
locked_by:
locked_since:
depends_on: []
source: [plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md, line-cap remediation 2026-08-09]
assigned_role: project_management
drift_direction: none
---

# Sports satellite AO batch 9 — Progress Log history

> Extracted verbatim 2026-08-09 (line-cap remediation — live doc had grown to 1015/1000 lines after a stale-duplicate
> checkbox flip needed to land) from `/plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md`'s Progress Log.
> Covers the three intermediate status-snapshot entries for VM `tm-backfill-20260807-233040` between its launch and the
> live doc's own terminal "BLOCKED-UPSTREAM-OUTAGE" entry, which already captures the outcome (VM killed 2026-08-08
> after a confirmed 15h+ vendor-endpoint outage) — these entries add no information not already superseded by that final
> entry.

### 2026-08-07 — P2 PLAYER_VALUES Transfermarkt backfill launched (slot 14)

VM `tm-backfill-20260807-233040` (SPOT e2-standard-8, `asia-northeast1-c`) launched 2026-08-07T23:30:40Z via
`bash deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh --entity PLAYER_VALUES 2025-09-01 2025-11-30`.
All 4 tarballs confirmed fresh at launch time.

**Status at pre-compact (2026-08-07T23:36Z):** VM RUNNING. GCS log at
`gs://deployment-scripts-central-element-323112/vm-logs/tm-backfill-20260807-233040/run.log` shows:

- Service started, PLAYER_VALUES+TRANSFERMARKT filters applied
- `TRANSFERMARKT short-circuit: skipping orchestrator for date=2025-09-01` — skip-fresh working correctly (captured
  dates skipped, only `attempted_failed` cells re-attempted)
- 502 retry from `transfermarkt-football-data-api.p.rapidapi.com` in progress (attempt 1/10, backoff 3.0s)

**Next step after VM completes (exit_code=0):** run manifest re-measurement to count PLAYER_VALUES `attempted_failed`
cells in 2025-09-01..2025-11-30 (baseline=256), then flip this todo's checkbox citing VM name + measurement result.
Measurement script pattern: 3-col read (`date`, `data_type`, `capture_status`) from
`instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, filter
`data_type==PLAYER_VALUES AND date∈[START,END]`. Run via `run-bounded-analysis.sh` per memory-bounding rule.

### 2026-08-07T23:50Z — second pre-compact (slot 14); VM still active

**VM status at 23:50Z:** RUNNING — at attempt 4/10 (backoff 24.0s) for Transfermarkt 502 retries at 23:37Z; within
normal 10-attempt retry envelope. Background 5-min poll armed (up to 90 min).

**Updated at 23:42Z (third pre-compact):** VM at attempt 7/10 (backoff capped at 48.0s since attempt 5) on
`/api/v1/competitions/standings`. Attempts 8–10 also at ~48s each — VM may exit non-zero ~23:44–23:46Z if API stays
down.

**Resume steps (pick up from repo, zero session memory needed):**

1. Check VM:
   `gcloud compute instances list --filter="name=tm-backfill-20260807-233040" --zones=asia-northeast1-c --format='value(name,status)'`
2. If gone:
   `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/tm-backfill-20260807-233040/run.log | tail -30`
   and look for `[[VM_PROGRESS]] last_completed_date=2025-11-30` (success) or final `exit` line.
3. If exit_code=0: create `measure_pv_golden.py` with the snippet below, run via
   `cd instruments-service && bash scripts/dev/run-bounded-analysis.sh python <path>/measure_pv_golden.py`.
4. Flip P2 checkbox (`- [ ] → - [x] ✅`), commit `docs(plans):`, POST `/api/slots/14/done`
   `{"task_id":"sports_satellite_ao_dispatch_batch9-002","sha":"<sha>","evidence":"<measurement output>"}`.
5. **If exit_code≠0 (API exhaustion):** wait 15–30 min for Transfermarkt API recovery, then re-launch:
   `bash deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh --entity PLAYER_VALUES 2025-09-01 2025-11-30`
   (skip-fresh is default — already-captured cells won't be re-attempted; idempotent re-launch is safe).

**Measurement script (inline — scratchpad not durable):**

```python
#!/usr/bin/env python3
"""Measure PLAYER_VALUES attempted_failed in golden window 2025-09-01..2025-11-30."""
from __future__ import annotations
import io
from datetime import UTC, datetime
import pandas as pd
from unified_trading_library import get_storage_client

BUCKET = "instruments-store-sports-prd-central-element-323112"
START, END, TARGET = "2025-09-01", "2025-11-30", "PLAYER_VALUES"

def main() -> int:
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")
    client = get_storage_client()
    raw = client.download_bytes(BUCKET, "_index/availability_index.parquet")
    manifest = pd.read_parquet(io.BytesIO(raw), columns=["date", "data_type", "capture_status"])
    mask = (manifest["data_type"] == TARGET) & (manifest["date"] >= START) & (manifest["date"] <= END)
    counts = manifest[mask]["capture_status"].value_counts().to_dict()
    af = counts.get("attempted_failed", 0)
    print(f"[{ts}] PLAYER_VALUES {START}..{END}: attempted_failed={af} (baseline=256); counts={counts}")
    verdict = "PASS — dropped from 256" if af < 256 else "WARN — unchanged or higher"
    print(f"VERDICT: {verdict}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

### 2026-08-08T00:18Z — sustained Transfermarkt API outage; VM still cycling (slot 14)

**VM `tm-backfill-20260807-233040` RUNNING at 00:18Z** (48+ min since first 502 at 23:34Z). API is returning 502 on
`competitions/standings` continuously. Service handles each `attempted_failed` date by exhausting its 10-attempt retry
window (~9 min), writing `attempted_failed` to the manifest, then moving on — no outer exit on per-date exhaustion.

**Progress as of 00:18Z:** 5 date-batches cycled (~45 min × 1 date/9 min). Zero captures. `attempted_failed` cells are
being re-stamped as `attempted_failed` for each date processed.

**Path forward:** VM will continue cycling through all `attempted_failed` dates. Either:

- **(A) API recovers mid-run** → remaining dates capture successfully; VM exits 0; run measurement (script inline
  above); if `attempted_failed < 256` → flip P2 checkbox + `docs(plans):` commit + POST `/api/slots/14/done`.
- **(B) API stays down; VM cycles to completion** → VM exits (likely exit_code=0 having processed all dates); run
  measurement expecting `attempted_failed ≈ 256`; wait 20–30 min for API recovery; re-launch:
  `bash deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh --entity PLAYER_VALUES 2025-09-01 2025-11-30`
  (idempotent — skip-fresh re-attempts `attempted_failed` cells).

**Do NOT launch a new VM while `tm-backfill-20260807-233040` is still RUNNING** — singleton lock will reject it.

> **Outcome** (recorded in full in the live doc): the VM was found still cycling with zero productive progress against a
> confirmed vendor outage and was killed 2026-08-08 — see the live doc's "Todo 2 — BLOCKED-UPSTREAM-OUTAGE" Progress Log
> entry.
