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

- [x] ✅ [DATA] P0. **Already fixed — features-service@9e94485e ("fix(sports): arb-detect historical backfill uses
      record_captured_from_counts"), landed on `origin/live-defi-rollout` 2026-08-22T16:04:13Z, before this slot
      picked up the task.** `_run_historical_backfill`/`_record_arb_day` now call
      `ManifestWriter.record_captured_from_counts()` for the bundled `arbitrage_opportunity` data_type; the banned
      `.add()` call is gone. Re-launched the full 2020-06-06→2026-08-22 campaign per the fix's own instruction
      (`launch-features-sports-arb-backfill.sh`, VM `features-arb-backfill-20260822-161439`, `RESUME_START_DATE
      2020-06-06 RESUME_END_DATE 2026-08-22`). Verified via TARGET ARTIFACT within ~1 min of launch, not
      exit_code/activity: `run.log` shows real `sports-arb-detect: wrote N opportunity row(s) ->
      gs://features-sports-prd-central-element-323112/sports_arb/by_date/day=2020-06-1{3,6,7,9}/...` writes for
      6+ distinct dates, zero `ValueError`/traceback — the exact failure signature the original audit found is
      gone. Campaign left running (multi-hour full-window job); continued-to-floor monitoring is the separate
      still-open REVIEW todos' job, not duplicated here (repo: features-service, deployment-service).
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

## Addendum — `/vm-preemption-billing-waste-audit` pass (2026-08-22, slot-16, review)

Ran the standing preemption/billing-waste audit (plan REVIEW P1 todo, line 221) over this same campaign. Confirms this
doc's findings and adds two items this doc didn't cover:

1. **Preemption confirmed genuine.** `gcloud compute operations list
   --filter="operationType=compute.instances.preempted"` confirms `mdps-sports-bucket-20260821-060513` was genuinely
   GCP-preempted at `2026-08-21T07:51:04Z` (not a crash/OOM/other kill) — the finding #2 gap above is a real
   spot-preemption-without-auto-recovery, matching the `spot-vms-for-backfill.md` contract's failure mode exactly.
   The relaunch (slot-23, `[DATA] P0` entry above) landed concurrently with this audit and already confirms the
   checkpoint-resume mechanism worked correctly (tail-resumed from `2023-05-15`, not a `START_DATE`/`2022-01-01`
   replay) — no further re-verification needed from this pass. The only real gap is the absent automated watcher
   finding #2 above already names (nothing currently running to detect/relaunch a preemption on its own).
   (Two other sports-tagged preemptions turned up in the same lookback — `sports-manifest-rescan-20260817-144852` and
   `mtds-backfill-sports-pipelinecheck-20260820-204800-e83df5` — neither is part of this campaign's two named VM
   prefixes and neither was investigated further; noted, not evidenced either way.)

2. **NEW finding — the arb-backfill's 1,323 `attempted_failed` days will re-fail identically on every future wave
   until the code fix lands, because the preflight-skip never treats them as already-attempted.**
   `features-service/features_service/sports/cli/handlers/arb_detect_handler.py`'s `_arb_preflight_skip()` (~line 72)
   only skips a day whose manifest row is already `captured`/`empty_confirmed` — it does **not** skip
   `attempted_failed` rows, and `_run_historical_backfill`'s exception handler (line ~168-172) does call
   `writer.record_failed(...)` on every one of the 1,323 banned-`.add()` days, so they ARE recorded
   `attempted_failed` in the manifest. Net effect: this is not a venue/data classification the existing
   `classify_venue_error()` retriable/non-retriable taxonomy covers at all — it's a 4th class, an **application bug
   with a 100%-deterministic failure signature**, but it behaves exactly like the codex contract's "structurally
   non-retriable shard re-attempted every wave" pattern: any relaunch of this campaign BEFORE the `.add()` →
   `record_captured_from_counts()` fix (already tracked as the `[DATA] P0` todo above) lands will burn ~1,323
   shard-days of compute for a guaranteed identical re-failure, with no `--force` needed to trigger the re-attempt.
   - [x] ✅ [DATA] P1. **Resolved 2026-08-22 (slot-23, data_engineering) — the fix landed and the relaunch has been
         verified, so the guard this todo names is now satisfied, not open.** `arb_detect_handler.py`'s
         `.add()`→`record_captured_from_counts()` fix was already on `origin/live-defi-rollout`
         (features-service@9e94485e, 2026-08-22T16:04:13Z) before this slot picked up the task; no premature
         relaunch occurred in the gap. See the `[DATA] P0` todo above for the relaunch + target-artifact
         verification evidence (repo: features-service, deployment-service).

3. **Alerting check (Step 3, inconclusive) — DP-FETCH-009 (`check_high_attempted_failed`, `abs>=500` threshold)
   should have fired for this cell** (1,323 far exceeds the 500 floor), but a check of the `#data-pipeline-alerts`
   Slack channel (last 100 messages, spanning back to 2026-08-18) found no `DP-FETCH-009`/`DP_RUN_MOSTLY_EMPTY`
   mention for `arbitrage_opportunity`/sports. `check_high_attempted_failed` is a scheduled/cron-based post-run
   manifest scan (not real-time), and the campaign that produced these rows only ran 2026-08-22 (today) — so this
   may simply mean the scan hasn't run its next cycle yet rather than a genuine coverage gap. Not confirmed either
   way within this audit's scope.
   - [x] ✅ [SCRIPT] P2. **Re-checked 2026-08-22 15:44 UTC (slot-5, backend_engineer) — still hasn't fired, and the
         root cause is now CONFIRMED as a structural alerting-coverage gap, not a timing delay.**
         - **Re-check performed** (>6.5h after the campaign started at 09:00:11 UTC — well past the `*/15` cron, the
           2-consecutive-miss (~30 min) paging gate, and the 30-min re-nag cooldown): `#data-pipeline-alerts` Slack
           channel, last 200 messages — zero `DP-FETCH-009`/`DP_RUN_MOSTLY_EMPTY`/`arbitrage_opportunity`/`sports`
           hits. Cross-checked the Cloud Run job's own run history (`gcloud run jobs executions list
           --project=central-element-323112 --region=asia-northeast1 --job=uts-prod-dp-meta-watchers`): 15
           consecutive successful `*/15` executions from 12:15-15:45 UTC today, each completing in 5-7 min (well
           inside the 900s timeout) — the watcher itself is healthy, not OOM'ing/timing out.
         - **Root cause CONFIRMED**: `check_high_attempted_failed`'s target list (`high_attempted_failed_targets()`,
           `deployment_service/data_pipeline_monitors/meta_targets.py:129-150`) builds exactly one `FreshnessTarget`
           per asset_group, using ONLY `market_data_bucket(ag)` (line 66:
           `resolve_bucket_name(kind="market-data", asset_group=ag)`). But `arb_detect_handler.py`'s
           `_run_historical_backfill` (features-service) constructs its `ManifestWriter` with
           `catalogue_bucket=config.get_instruments_bucket()` — the INSTRUMENTS-STORE-sports bucket, not
           market-data-sports. `ManifestWriter.__init__`'s own docstring
           (`unified_trading_library/manifest_writer/_writer.py:112`) states `catalogue_bucket` IS "the GCS bucket
           holding `_index/availability_index.parquet`", and every per-VM shard write
           (`_write_per_vm_shard`/`_flush_per_vm_pending`, `_writer_io.py`) targets `self.catalogue_bucket`
           exclusively — so the arb campaign's 1,323 `attempted_failed` rows consolidate into a bucket
           `check_high_attempted_failed` never queries. This is a STRUCTURAL blind spot: DP-FETCH-009 cannot fire
           for this cell regardless of how many `*/15` cycles run.
         - **Filed as a genuine alerting-coverage gap** — see the new `[DATA] P1` todo in the 2026-08-22 addendum
           below.

Evidence: `gcloud compute operations list --project=central-element-323112 --filter="operationType=compute.instances.preempted AND targetLink~mdps-sports"` (single preemption hit, `mdps-sports-bucket-20260821-060513`, `2026-08-21T07:51:04Z`);
`gcloud compute instances describe mdps-sports-bucket-20260822-{150734,150914} --format="value(metadata.items)"` (relaunch args showing checkpoint-resume, not replay); `features-service/features_service/sports/cli/handlers/arb_detect_handler.py:72-180` (`_arb_preflight_skip` / `_run_historical_backfill` read); `scripts/dev/slack-read-channel.py --channel data-pipeline-alerts --limit 100` (no DP-FETCH-009/arbitrage hit).

## Addendum — DP-FETCH-009 bucket-scope blind spot confirmed (2026-08-22, slot-5, backend_engineer)

Closing the `[SCRIPT] P2` re-check todo above (Step 3 of the `/vm-preemption-billing-waste-audit` pass) found a
confirmed, structural root cause rather than a timing delay — see that todo's write-up for the full evidence chain.
Summary: `high_attempted_failed_targets()` only ever resolves `market_data_bucket(ag)`, one bucket per asset_group,
while a `ManifestWriter` constructed against a DIFFERENT `catalogue_bucket` (here, `config.get_instruments_bucket()`
— the sports arb handler's actual writer) is invisible to DP-FETCH-009 no matter how long it runs. The
already-existing `instruments_store_bucket(ag)` resolver (`meta_targets.py:69-79`, the same one `catalogue_targets()`
already uses) is the ready-made fix ingredient for at least this bucket class.

**Generalization risk (unverified beyond this one confirmed case)**: any data_type across ANY asset_group whose
`ManifestWriter` is constructed with a `catalogue_bucket` other than that asset_group's `market_data_bucket(ag)` —
i.e., any features-tier or instruments-tier derived data_type, not just sports/`arbitrage_opportunity` — has the same
structural blind spot against this 🔴 CRITICAL/paging alert class. Not audited fleet-wide within this task's scope.

- [ ] [DATA] P1. Extend `high_attempted_failed_targets()`
      (`deployment_service/data_pipeline_monitors/meta_targets.py:129-150`) to also emit a `FreshnessTarget` per
      asset_group using the existing `instruments_store_bucket(ag)` resolver (mirrors `catalogue_targets()`'s
      pattern, `meta_targets.py:95-124`), so DP-FETCH-009 covers `ManifestWriter` instances constructed against the
      instruments-store bucket (confirmed case:
      `features-service/features_service/sports/cli/handlers/arb_detect_handler.py`'s arb writer) — not just
      market-data-tier writers. While there, audit whether a THIRD bucket class (a features-tier bucket, e.g.
      `features-sports-{env}` — no `features_bucket()` resolver currently exists in `meta_targets.py`) also needs its
      own target, by checking whether any live `ManifestWriter` construction across the fleet passes a
      `catalogue_bucket` that resolves to neither `market_data_bucket(ag)` nor `instruments_store_bucket(ag)`. Verify
      the fix by confirming a DP-FETCH-009 page actually fires for the still-open sports/`arbitrage_opportunity` cell
      (1,323 `attempted_failed`, unchanged until the separate `.add()`→`record_captured_from_counts()` fix lands)
      once deployed (repo: deployment-service).

Evidence: `deployment_service/data_pipeline_monitors/meta_targets.py:54-150` (`market_data_bucket`,
`instruments_store_bucket`, `high_attempted_failed_targets`);
`unified_trading_library/manifest_writer/_writer.py:93-128` (`ManifestWriter.__init__` docstring);
`unified_trading_library/manifest_writer/_writer_io.py` (per-VM shard write methods, all
`self.catalogue_bucket`-scoped); `features-service/features_service/sports/cli/handlers/arb_detect_handler.py:147-150`
(writer construction); `gcloud run jobs executions list --project=central-element-323112 --region=asia-northeast1
--job=uts-prod-dp-meta-watchers --limit=15` (15/15 healthy `*/15` executions, 2026-08-22T12:15-15:45Z);
`scripts/dev/slack-read-channel.py --channel data-pipeline-alerts --limit 200` (zero DP-FETCH-009/arbitrage/sports
hits as of 2026-08-22T15:44Z).
