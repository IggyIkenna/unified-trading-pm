---
doc_type: issue
title:
  "plans/audit/results/available_at_fill_rate_audit_2026_07_13.py has no per-bucket memory release — RSS hit ~39GB
  across the shared host (44GB used / 27GB swapped) before being killed"
summary: >-
  While gathering a BEFORE-state fill-rate baseline for `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s -001
  todo (prediction apply), ran the plan's own referenced audit script
  (`plans/audit/results/available_at_fill_rate_audit_2026_07_13.py`), which loops `read_availability_index()` over 11
  buckets (cefi/defi/tradfi/sports market-data x2 kinds, prediction, strategy-store) in ONE process with no per-bucket
  DataFrame release. RSS climbed to ~39GB (60.5% of host memory) within ~1 minute, on a host already under real memory
  pressure (44GB/61GB used, 27GB/47GB swap in use, only 5.5GB free at observation time). Killed by exact PID (`kill
  -TERM 3258825`) before it risked OOMing other slots' concurrent work; host recovered to 14GB used / 35GB free within
  seconds of the kill. This is the same "ad-hoc script materializing large corpora in-memory on a shared host" pattern
  as `mtds_manifest_rebuild_scripts_unbounded_memory_no_chunking_2026_07_31.md`, but for a DIFFERENT script (a read-only
  audit tool, not a rebuild/backfill writer) that doc's fix did not cover.
status: open
nature: issue
asset_group: [meta]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [data-correctness, available-at, memory-safety, shared-host, audit-script, heavy-compute]
related:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/active/issues/mtds_manifest_rebuild_scripts_unbounded_memory_no_chunking_2026_07_31.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-07-31"
parent_epic: manifest_master
source: [mtds_available_at_cross_asset_backfill-006, slot 12]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# `available_at_fill_rate_audit_2026_07_13.py` has unbounded memory across its bucket loop

## What I found

Ran (from `market-tick-data-service`, whose `.venv` has `unified_trading_library` installed as an editable path dep —
`unified-trading-library` itself carries no `.venv` of its own):

```
GCP_PROJECT_ID=central-element-323112 .venv/bin/python \
  ../unified-trading-pm/plans/audit/results/available_at_fill_rate_audit_2026_07_13.py
```

Observed via `ps aux` ~1 minute in: PID 3258825, RSS 39,240,516 KB (~39GB), 60.5% of the host's 61GB total. `free -h` at
the same moment: `Mem: 61Gi total, 44Gi used, 5.5Gi free, 12Gi buff/cache`, `Swap: 47Gi total, 27Gi used` — the host was
already deep into swap before this process's growth is even isolated out, meaning this run was actively pushing a
shared, already-stressed host toward OOM. Killed by exact PID (`kill -TERM 3258825`, per the RULES.md exact-PID-only
guardrail — no `pkill` pattern used). Host recovered to `14Gi used / 35Gi free / 15Gi swap` within seconds, confirming
this ONE process was the dominant consumer.

Root cause (not yet code-read in detail — flagging for whoever picks this up): the script's `TARGETS` list loops 11
`(kind, asset_group)` pairs, calling `read_availability_index(bucket)` for each and holding the resulting `pd.DataFrame`
(plus a `by_service` groupby copy) in the `results` list for the WHOLE run before printing the final summary at the end
— nothing is released between buckets. `market-data`'s tradfi (1.6M captured rows, per this plan's own Progress Log) and
defi (3.0M captured rows) targets are almost certainly the dominant contributors; `market-data-tick-prediction` (895,900
rows) alone would not plausibly produce 39GB.

## Why it matters

Same class as `mtds_manifest_rebuild_scripts_unbounded_memory_no_chunking_2026_07_31.md`: an ad-hoc script materializing
multiple large corpora in memory on a shared interactive/planning host, not a dedicated/memory-provisioned VM, risking
an OOM that takes out OTHER slots' concurrent work — and this script is REFERENCED BY NAME in
`mtds_available_at_cross_asset_backfill_2026_07_13.md`'s own todos ("re-run `available_at_fill_rate_audit_2026_07_13.py`
(or its successor) to confirm fill rate rose from 0%") for the prediction/tradfi apply-verification steps still open in
that plan, so this is a live landmine for whoever runs those verification todos next, not just a one-off encounter.

## What I did NOT do

Did not profile which specific bucket(s) dominate (my working hypothesis above is untested), did not read
`read_availability_index()`'s own memory profile, did not attempt a per-bucket-scoped rerun in THIS touch (used a
narrower, single-bucket-only inline read instead to get my needed prediction baseline safely — see the parent plan's
Progress Log). Did not modify the audit script.

## Recommended decision

- [ ] [SCRIPT] P2. Refactor `available_at_fill_rate_audit_2026_07_13.py`'s `main()` loop to print+discard each bucket's
      result immediately (drop the `results` accumulator, or at minimum `del df`/`del captured`/`del by_service` after
      each `audit_bucket()` call returns and before the next iteration) so peak RSS is bounded by the SINGLE largest
      bucket's index, not the sum of all 11. Add a `--bucket-kind`/`--asset-group` CLI filter (mirroring this plan's own
      rebuild scripts' `--venue` pattern) so a caller who only needs one bucket (e.g. prediction verification) never
      loads the rest. Repo: unified-trading-pm. Done when: a full run's peak RSS (measured via `ps` sampling during the
      run) is bounded to roughly the largest single bucket's index size, not the cumulative sum, and a
      `--asset-group     prediction --kind market-data-tick-prediction`-style scoped invocation completes without
      touching the tradfi/defi/cefi/sports targets at all.

## Progress Log

- 2026-07-31 (data_engineering slot-12): found + filed while gathering `-001`'s BEFORE-state baseline. Killed the
  runaway process by exact PID, host recovered. Worked around it this touch via a narrow single-bucket read (see parent
  plan's Progress Log for the actual baseline evidence). Not fixed here — script-hygiene follow-up, not blocking on the
  parent plan's apply/resume todos (which don't need the OTHER 10 buckets, only prediction's own).
