---
doc_type: issue
title: Sports P4 backfill — progress-metric audit found the arb campaign wrote zero real rows and the MDPS bucket campaign has unresumed gaps
summary: >-
  A progress-metric (not activity-signal) audit of the sports P4 derived-layer backfill found the full arb-backfill
  campaign wrote zero real rows (banned ManifestWriter.add() on every date) and the MDPS bucket/movement/snapshot
  campaign has two unresumed date-range gaps, despite both prior todos being flipped done on exit_code=0.
nature: issue
asset_group: [sports]
stage: [data]
repos: [features-service, market-data-processing-service, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [sports, backfill, progress-metric, manifest, spot-preemption]
related:
  [
    /plans/active/sports_taxonomy_p4_backfill_2026_08_08.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
parent_epic: sports_master
priority: P0
context_scope: [/codex/12-agent-workflow/async-wait-and-poll-discipline.md, /codex/02-data/sports-2020-06-data-floor.md]
resolved_by:
locked_by:
assigned_vm: planning
created: 2026-08-22
author: slot-25 (review)
source: ["/plans/active/sports_taxonomy_p4_backfill_2026_08_08.md REVIEW P0 todo #7 (progress-metric monitor)"]
status: open
---

## What I found

Auditing the two campaigns this plan's prior todos claimed as landed, by reading each VM's `run.log`/`EXIT_STATUS`
via UTL `get_storage_client()` (never `gsutil`) rather than trusting `exit_code=0` alone — this is exactly the
activity-vs-target-artifact gap the REVIEW todo warns about:

**1. `features-arb-backfill-20260822-090011` (the full 2020-06-06→2026-08-22 arb campaign, todo marked done
2026-08-22) wrote ZERO real rows.** `exit_code=0` at the `[vm-exec]` wrapper level, but the log shows a
`ValueError` raised inside `_run_historical_backfill` on every date: `ManifestWriter.add() with bundled
data_type='arbitrage_opportunity' is banned; use record_captured_from_counts() instead — add() bypasses the
cluster-coverage gate mandatory for bundled shards.` (see `wave2_polymarket_record_captured_from_counts_2026_05_09`
plan for the origin of that gate). Final tally: `days=2269 opportunities=0 written_days=0 skipped_days=0
failed_days=1323` — i.e. every single date failed the same way, and the wrapper still reported success because the
per-day exception is caught, not fatal to the process. `features-service/features_service/sports/cli/handlers/
arb_detect_handler.py:99` is the offending `writer.add(...)` call (the same code path the 2026-08-22 slot-21
session's 13-day bounded validation exercised — that window apparently didn't hit the bundled-shard gate, or ran
against a pre-gate manifest state; either way the full campaign now reproduces it on every date).

**2. `mdps-sports-bucket-*` consolidated campaign (bucket + movement + snapshot, todo marked done 2026-08-21) has
two unresolved gaps, not the "actively processing full range" state the plan banner still claims:**
- `2020-06-06 → 2021-12-31`: DONE (`mdps-sports-bucket-20260821-055605`, exit_code=0, 254 days captured).
- `2022-01-01 → 2023-06-30`: **INCOMPLETE.** VM `mdps-sports-bucket-20260821-060513` was launched for this exact
  range but its last log line is `2023-05-15` (~07:48 UTC 2026-08-21) and its `EXIT_STATUS` object still reads
  `RUNNING` — over 24h stale, and `gcloud compute instances list` confirms no instance by this name is in the
  live fleet. This is a SPOT-preemption-without-recovery: the range was never resumed/relaunched.
- `2023-07-01 → 2024-12-31`: DONE (`mdps-sports-bucket-20260821-060933`, exit_code=0, 446 days captured).
- `2025-01-01 → 2026-08-06`: **NEVER LAUNCHED.** No VM under `vm-logs/mdps-sports-bucket-*` covers this range at
  all.

The plan's own `> 🟢 CAMPAIGN IN PROGRESS 2026-08-21` banner ("~35 hours remaining from 2021-11-16") is now stale —
no VM for this task is currently running (`gcloud compute instances list --filter="name~mdps-sports-bucket"`
returns empty), and the campaign as actually executed covers roughly half the target window with two real gaps.

## Why it matters

Two of this plan's [x]-flipped P0/P1 todos (arb backfill full launch, consolidated bucket backfill) certified
completion on `exit_code=0` / "VM RUNNING" activity signals, not on the target-artifact count the plan's own REVIEW
todo requires. The honest state is: the arb derived layer (`arbitrage_opportunity`) has ZERO real historical rows
beyond the earlier 13-day bounded validation window, and the MDPS bucket/movement/snapshot layer is missing
2022-01-01→2023-06-30 (partial) and 2025-01-01→2026-08-06 (untouched) — roughly 40% of the intended 2020-06-06→
2026-08-06 floor window.

## Recommended decision

- [ ] [DATA] P0. Fix `features-service/features_service/sports/cli/handlers/arb_detect_handler.py`'s
      `_run_historical_backfill` to use `ManifestWriter.record_captured_from_counts()` instead of the banned
      `.add()` for the bundled `arbitrage_opportunity` data_type (see `wave2_polymarket_record_captured_from_counts_2026_05_09`
      for the reference pattern), then re-launch the full 2020-06-06→present campaign via
      `launch-features-sports-arb-backfill.sh` (repo: features-service, deployment-service).
- [x] ✅ [DATA] P0. **Relaunched 2026-08-22 (slot-23, data_engineering)** — both unresolved MDPS
      bucket/movement/snapshot windows, via the existing `launch-mdps-sports-bucket-vm.sh` pattern (the same 4-way
      sharding this campaign was originally run with), `force` mode on both (matches the two already-completed
      sibling shards — the launcher's own header documents `force` as the only mode that re-attempts a day whose
      COARSE per-day manifest key is already captured but is still missing fine-grained (league_id, timeframe)
      shards):
      - `2022-01-01 → 2023-06-30` tail resume — re-ran `2023-05-15 → 2023-06-30` only (the range the interrupted VM's
        log stopped mid-processing), not the whole chunk: the earlier days were already force-processed in one
        continuous run before the SPOT preemption, so re-forcing them would be pure waste, not a correctness gain.
        VM `mdps-sports-bucket-20260822-150734`.
      - `2025-01-01 → 2026-08-06` (never launched) — full range. VM `mdps-sports-bucket-20260822-150914`.
      **Verified via the TARGET ARTIFACT, not activity/exit_code — the exact gap this issue doc exists to close.**
      Confirmed no pre-existing `mdps-sports-bucket-*`/`features-arb-backfill-*` VM was already running before
      launch (`gcloud compute instances list` empty for both prefixes — no collision risk). ~5 min after launch,
      read both VMs' `run.log` via UTL `download_from_storage()` (never `gsutil`/`gcloud storage` — blocked by the
      workspace's own guardrail hook) and parsed for the exact failure signature the arb campaign hit (a per-date
      exception silently swallowed while exit_code stays 0): VM1 — 19 distinct dates processed (latest 19/47,
      2023-06-02), 20 `LOSS_GUARD_PASS` writes, 0 tracebacks, 0 `attempted_failed`, 0 `LOSS_GUARD_BLOCKED`. VM2 — 23
      distinct dates processed (latest 23/583, 2025-01-23), 34 `LOSS_GUARD_PASS` writes, 0 tracebacks, 0
      `attempted_failed`, 0 `LOSS_GUARD_BLOCKED`. Both are genuinely writing real bucket/movement/snapshot shards,
      not silently failing like the sibling arb campaign did. Did NOT wait for full campaign completion (VM2's
      ~583-day range is a multi-hour run) — continued-to-floor monitoring is the separate still-open [REVIEW] P0/P1
      todos' job (terminal honest-coverage verdict; preemption/billing-waste audit), not duplicated here.
- [x] ✅ [SCRIPT] P2. **Already done — same commit that filed this issue doc.** The stale `🟢 CAMPAIGN IN
      PROGRESS 2026-08-21` banner in `sports_taxonomy_p4_backfill_2026_08_08.md` was replaced (not just removed)
      with an accurate `🟡 CAMPAIGN STALLED 2026-08-22` banner citing this issue doc, at the same time the REVIEW
      P0 todo that found the stale state was landed — `unified-trading-pm@fe5640f967`. Verified current: plan file
      line 61 reads `🟡 CAMPAIGN STALLED 2026-08-22 (see issue doc)`, no `🟢 CAMPAIGN IN PROGRESS` text remains in
      the file, tree clean, commit on `origin/live-defi-rollout`. No further edit needed — the above two [DATA] P0
      relaunch todos remain open and unaffected by this.

## Evidence

- `gs://deployment-scripts-central-element-323112/vm-logs/features-arb-backfill-20260822-090011/run.log` (traceback
  + `days=2269 opportunities=0 written_days=0 skipped_days=0 failed_days=1323` summary line).
- `gs://deployment-scripts-central-element-323112/vm-logs/mdps-sports-bucket-20260821-060513/run.log`
  (`EXIT_STATUS=RUNNING`, last log line dated 2023-05-15, range flag `--start-date 2022-01-01 --end-date
  2023-06-30`).
- `gs://deployment-scripts-central-element-323112/vm-logs/mdps-sports-bucket-20260821-{055605,060933}/run.log`
  (`Range:` summary lines confirming the two completed chunks).
- `gcloud compute instances list --project=central-element-323112 --filter="name~mdps-sports-bucket OR
  name~features-arb-backfill"` → empty (neither campaign has a live VM).
- `gs://deployment-scripts-central-element-323112/vm-logs/mdps-sports-bucket-20260822-150734/run.log` (tail-resume
  relaunch, `2023-05-15 → 2023-06-30 force`; 19 distinct dates + 20 `LOSS_GUARD_PASS` confirmed within 5 min).
- `gs://deployment-scripts-central-element-323112/vm-logs/mdps-sports-bucket-20260822-150914/run.log` (fresh
  relaunch, `2025-01-01 → 2026-08-06 force`; 23 distinct dates + 34 `LOSS_GUARD_PASS` confirmed within 5 min).
