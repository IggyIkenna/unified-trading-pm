---
doc_type: plan
title:
  MVP backfill — DeFi all on-chain data_types — operational log, Part 4 of 6 (extracted from
  mvp_backfill_defi_onchain_v10)
summary: >-
  Verbatim historical operational log extracted from mvp_backfill_defi_onchain_v10_2026_06_27.md's G1.5 nested
  sub-history and Progress Log sections, split out solely to bring the parent plan back under the line-cap (pure hygiene
  move — no todo/gate/state content changed). Re-chunked 2026-07-24 from an original 3-part split into 6 parts to comply
  with the operator's same-day ruling removing the umbrella:true line-cap exemption (flat 1000L hard cap, no
  exceptions). This is Part 4 of 6 in strict chronological order — read all 6 parts in filename order for full context.
  Part 1's filename is kept stable across both the original 2026-07-24 split and this re-chunk so existing external
  references keep resolving to real content.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [deployment-service, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [mvp, backfill, defi, on-chain, dex, lending, lst, perp-funding, oracle, spot-vm, v10, progress-log, plan-hygiene]
related:
  [
    /plans/active/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md,
    /plans/active/mvp_backfill_defi_onchain_v10_operational_log_part2_2026_07_24.md,
    /plans/active/mvp_backfill_defi_onchain_v10_operational_log_part3_2026_07_24.md,
    /plans/active/mvp_backfill_defi_onchain_v10_operational_log_part5_2026_07_24.md,
    /plans/active/mvp_backfill_defi_onchain_v10_operational_log_part6_2026_07_24.md,
    /plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: defi_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Plan line-cap hygiene remediation, /plans/active/issues/plan_line_cap_remediation_2026_07_23.md row 21 — pure
  extraction of already-written historical narrative out of mvp_backfill_defi_onchain_v10_2026_06_27.md, operator
  approved 2026-07-23 (locked plan, unlock+extract authorized); re-chunked from 3 to 6 parts 2026-07-24 per the same-day
  umbrella-exemption-removal ruling (plans/active/issues/plan_line_cap_remediation_2026_07_23.md).
assigned_role: data_engineering
drift_direction: advance-code
---

# MVP backfill — DeFi on-chain — operational log (Part 4 of 6)

**All 3 VMs RUNNING** (`mtds-drift-sig-walker-gap-20260714-134501`, `mtds-drift-sig-walker-resume-20260714-134435`,
`mtds-solana-drift-backfill`), none self-deleted, none showing the false-positive `"Walk complete: 0 new sigs"` rc=0
death this time.

- **Gap walker** (`_parts_gap/`): T+~8min = 39 parts (oldest=2025-06-30); T+~22min = **204 parts** (oldest=2025-06-19).
  Continuous `page=/collected=/Flushed part-NNNNNN` log lines throughout, zero 429/error lines. Real, sustained progress
  walking backward from its 2025-07-01T23:00Z anchor toward its `--back-to 2025-01-15` floor.
- **Resume walker** (`_parts/`): flat at the 6,293 baseline through T+~8min (still inside its known
  `_load_parts_summary()` sequential metadata-scan of all 6,293 existing parts — this is expected pre-walk overhead, not
  stall, per the 12:50Z entry's own diagnosis of this exact phase). By T+~22min it had finished the scan and started
  real walking: **6,391 parts** (oldest=2025-12-22, down from its 2025-12-23 resume-seed), continuous
  `page=/Flushed part` lines, zero 429/error lines.
- **Backfill VM** (`mtds-solana-drift-backfill`): resource-sampling only (bootstrap) through T+~8min; by 14:00:10Z it
  loaded the sig index (7,291 parts across 3 prefixes: `_parts/`=6,293, `_parts_b/`=876, `_parts_gap/`=122) and began
  processing **1,209,478 sigs for the already-indexed 2025-01-09 window** (SOL-PERP) — genuine backfill activity, zero
  Helius-error lines, steady low-CPU/rising-RSS pattern consistent with in-memory sig processing (not a hang).

**Verdict: the operator's quota-restored ruling is CONFIRMED correct — this is a clean relaunch, not a repeat of the
12:39Z 429-exhaust death.** Both walker segments are demonstrably moving their `oldest` sig-date backward with real
Helius calls succeeding; the backfill VM is doing genuine sig-resolution work. **Gate NOT yet met** (todo sub-item 4:
`measure_honest_coverage.py --asset-group defi` would still show DRIFT perp_funding `attempted_failed>0` — not re-run
this check since nothing has changed there yet) — per this plan's own drain-math estimate the walkers need 1.7-9 more
days to reach their floors (resume: 2025-12-22→2025-07-01 ≈ 174 days of chain-history remaining; gap:
2025-06-19→2025-01-15 ≈ 155 days remaining), so this is expected, not a defect. Checkbox NOT flipped — todo sub-items 1
and 4 are still not satisfiable within a single dispatch session for a multi-day drain. **No new `/blocked` needed**
(the operator's ruling already covers continuing to drain); `/skip-current-task` so this todo returns to the queue for
the next check-in, per the established cadence (slot-6 → slot-3 → slot-2 → this entry).

### 2026-07-14T14:14Z — data_engineering slot-4 (T+~29min post-relaunch: fleet still healthy, no preemption, gate still not met)

**Re-dispatched to the same "Verify the DRIFT fleet drains" todo** (~7min after the slot-2 14:07Z entry above).
Fresh-pulled clean, then re-ran the same measured checks (`gcloud compute instances list` via
`/home/ubuntu/google-cloud-sdk/bin/` — snap `gcloud`/`gsutil` still broken in this sandbox; direct `gsutil cat`/`ls` for
parts counts + log tails):

**All 3 VMs still RUNNING** (`mtds-drift-sig-walker-gap-20260714-134501`,
`mtds-drift-sig-walker-resume-20260714-134435`, `mtds-solana-drift-backfill`), same `creationTimestamp` as the relaunch
— no preemption, no self-delete, no repeat of the 12:39Z false-completion death.

- **Gap walker** (`_parts_gap/`): 204→**276** parts (+72 in ~7min), oldest sig 2025-06-19→**2025-06-13**. Continuous
  `page=/collected=/Flushed part-NNNNNN` lines through 14:14:53Z, zero genuine 429/error/exhaust lines (grep hits were
  substring false-positives inside part numbers like `part-000110`/`page=16800`, verified by inspection).
- **Resume walker** (`_parts/`): 6,391→**6,469** parts (+78 in ~7min), oldest sig 2025-12-22→**2025-12-20**. Same
  continuous real-progress log pattern, same false-positive-only grep result.
- **Backfill VM** (`mtds-solana-drift-backfill`): still bootstrap-phase `RESOURCE_SAMPLE` heartbeats only (cpu 0.8-2.0%,
  RSS climbing 955MiB→1016MiB) — still in-memory processing the 1,209,478-sig 2025-01-09 window from the 14:00Z entry,
  no new capture/flush lines yet. Not a stall (rising RSS + steady low CPU matches the prior session's own diagnosis of
  this phase), just genuinely long per-day sig resolution.

**Verdict: fleet continues to genuinely drain, consistent with the slot-2 14:07Z checkpoint — no incident, nothing to
intervene on.** Gate still NOT met (did not re-run `measure_honest_coverage.py` — the backfill VM has not flushed a new
capture since the last check, so the manifest is expected byte-identical; re-running it would burn a corpus-scale read
for zero new signal). Per the plan's own drain-math estimate (1.7-9 days from the 13:45Z relaunch), a 29-minute window
is expected to show exactly this: steady part-count growth, zero errors, gate unmet. Checkbox NOT flipped — todo
sub-items 1 and 4 remain unsatisfiable within a single dispatch session. No new `/blocked` needed (operator's
quota-restored ruling already covers continuing to drain). `/skip-current-task` so this todo returns to the queue for
the next check-in, per the established cadence (slot-6 → slot-3 → slot-2 → slot-4 → next).

### 2026-07-14T14:46Z — data_engineering slot-8 (T+~26min post-relaunch, wider window: sustained real drain confirmed, gate still not met)

**Re-dispatched to the same "Verify the DRIFT fleet drains" todo.** Fresh-pulled all 24 slot repos clean. Given the
prior check cadence (slot-6→slot-3→slot-2→slot-4) had been re-checking every ~7-10min against a multi-day drain estimate
— too short a window to show meaningful signal beyond "still alive" — this session captured a baseline (14:20:55Z) then
armed a single 25-min background watch (`run_in_background`, no busy-poll) to get a wider, more informative delta before
writing a verdict, per the async-wait-discipline HARD RULE (`ScheduleWakeup`/polling discouraged in favor of a
self-armed watchdog on a real progress metric).

**Baseline (14:20:55Z)** — all 3 VMs RUNNING (`mtds-drift-sig-walker-gap-20260714-134501`,
`mtds-drift-sig-walker-resume-20260714-134435`, `mtds-solana-drift-backfill`), same `creationTimestamp` as the
13:43-13:45Z relaunch (no preemption): gap walker 342 parts (oldest 2025-06-08), resume walker 6,535 parts (oldest
2025-12-19), backfill VM still in-memory processing the 2025-01-09 window (RSS climbing, no new capture lines).

**T+~26min (14:46:52Z)** — all 3 VMs still RUNNING, identical `creationTimestamp`, zero preemption:

- **Gap walker** (`_parts_gap/`): 342→**598** parts (+256 in ~26.5min), oldest sig 2025-06-08→**2025-05-23** (16
  chain-days advanced). Continuous `page=/collected=/Flushed part-NNNNNN` lines through 14:46:54Z.
- **Resume walker** (`_parts/`): 6,535→**6,813** parts (+278 in ~26.5min), oldest sig 2025-12-19→**2025-12-15** (4
  chain-days advanced — lower density window than the gap walker's). Same continuous real-progress log pattern.
- **Backfill VM**: still bootstrap/in-memory-processing the 2025-01-09 window (RSS 1068MiB→1354MiB rising, CPU 1.4-2.0%,
  zero capture/flush lines yet) — same long-per-day-resolution phase every prior check has diagnosed, not a stall.
- **Zero genuine 429/error/exhaust/false-completion lines** across all 3 logs for the full 26.5min window — grepped
  `429|error|exhaust|walk complete` on each; every hit was a substring false-positive inside page/part counters (e.g.
  `page=42900`, `parts=429`), verified by inspection, same false-positive class slot-4's 14:14Z entry already
  identified. No repeat of the 12:39Z false-completion death signature.

**Verdict: sustained real drain over the widest single-session window checked so far (26.5min vs the prior ~7-10min
checks) — both walker segments are demonstrably advancing their `oldest` sig-date backward at a steady rate, with the
gap walker (anchored, no pre-walk metadata-scan overhead) running roughly 4x the resume walker's part-growth rate in raw
part-count terms (though the resume walker also had to work through part-writes at higher per-part row density given its
later chain window) — consistent with, not contradicting, the plan's own drain-math estimate. Gate NOT met** (todo
sub-item 4: `measure_honest_coverage.py --asset-group defi` would still show DRIFT perp_funding `attempted_failed>0` —
not re-run, no new capture has landed since the last measurement so the result would be byte-identical, and a
corpus-scale manifest read for zero new signal is exactly the wasteful re-scan the craft's efficiency north-star warns
against). Per the plan's own drain-math estimate (1.7-9 days from the 13:45Z relaunch), this is expected, not a defect:
resume walker has ~167 more chain-days to its 2025-07-01 floor (from 2025-12-15, down from ~174 remaining at the 14:14Z
check); gap walker has ~128 more chain-days to its 2025-01-15 floor (from 2025-05-23, down from ~155 remaining at the
14:14Z check). Checkbox NOT flipped — todo sub-items 1 and 4 remain unsatisfiable within a single dispatch session for a
multi-day drain. No new `/blocked` needed (operator's quota-restored ruling already covers continuing to drain).
**Recommendation for the next check-in**: keep armed 25-30min background watches (not ~7-10min re-dispatches) to keep
each session's delta meaningful — the fleet does not need more frequent observation than that, and over-frequent
re-checks burn dispatch slots for near-zero incremental signal on a multi-day process. `/skip-current-task` so this todo
returns to the queue for the next check-in, per the established cadence (slot-6 → slot-3 → slot-2 → slot-4 → slot-8 →
next).

### 2026-07-14T15:18Z — data_engineering slot-15 (T+~26min armed watch, following slot-8's recommended cadence: sustained real drain confirmed, gate still not met)

**Dispatched to the same "Verify the DRIFT fleet drains" todo.** Fresh-pulled all 24 slot repos clean. Following
slot-8's explicit recommendation (immediately above), armed a single 26-min background watch (`run_in_background`, no
busy-poll — heartbeats sent to the orchestrator every check-in while waiting for the async-wait-discipline watchdog to
land, per RULES.md) instead of re-dispatching every few minutes:

**Baseline (14:52:15Z)**: all 3 VMs RUNNING, same `creationTimestamp` as the 13:43-13:45Z relaunch (no preemption since
slot-8's 14:46:52Z check, only ~5.4min earlier): gap walker 651 parts, resume walker 6,873 parts.

**T+~26min (15:18:36Z)** — all 3 VMs still RUNNING, identical `creationTimestamp`, zero preemption:

- **Gap walker** (`_parts_gap/`): 651→**911** parts (+260 in ~26.4min), oldest sig advanced from ~2025-05-2x (baseline,
  not captured precisely) to **2025-05-02** — consistent with slot-8's 14:46Z reading of oldest=2025-05-23, i.e. ~21
  chain-days advanced over the ~32min since that checkpoint. Continuous `page=/collected=/Flushed part-NNNNNN` log lines
  through 15:16:55Z, zero error/exhaust lines.
- **Resume walker** (`_parts/`): 6,873→**7,163** parts (+290 in ~26.4min), oldest sig 2025-12-15 (slot-8's 14:46Z
  reading) → **2025-12-09** (~6 chain-days advanced over the same ~32min window). Continuous `Flushed part-NNNNNN` /
  `page=` lines through 15:18:12Z, zero error/exhaust lines.
- **Backfill VM** (`mtds-solana-drift-backfill`): still in the same long in-memory bootstrap/resolution phase for the
  2025-01-09 window — `RESOURCE_SAMPLE` heartbeats only (RSS climbing 1669→1690MiB, CPU 1.4-11%), zero new capture/flush
  lines since the 14:00Z entry. Same pattern every prior check (14:07Z-14:46Z) has diagnosed as genuine-long-resolution,
  not a stall — no new evidence changes that read.

**Verdict: sustained real drain continues, no repeat of the 12:39Z false-completion death, no preemption.** Gate NOT met
(todo sub-item 4 — `measure_honest_coverage.py --asset-group defi` not re-run: the backfill VM has flushed nothing new
since 14:00Z, so the manifest read would be byte-identical; a corpus-scale re-scan for zero new signal is exactly the
wasteful re-check the craft's efficiency north-star warns against, consistent with every prior session's same call).
Remaining distance: gap walker ~2025-05-02→2025-01-15 floor ≈ 107 chain-days; resume walker ~2025-12-09→2025-07-01 floor
≈ 161 chain-days — both within the plan's own 1.7-9 day drain-math estimate, no acceleration or degradation signal
either way. Checkbox NOT flipped — todo sub-items 1 and 4 remain unsatisfiable within a single dispatch session for a
multi-day drain. No new `/blocked` needed. `/skip-current-task` so this todo returns to the queue for the next check-in,
per the established cadence (slot-6 → slot-3 → slot-2 → slot-4 → slot-8 → this session → next), continuing to favor a
single armed 25-30min watch per session over frequent short re-dispatches.

### 2026-07-14T15:28Z — data_engineering slot-14 (short re-check, sustained real drain confirmed, gate still not met)

**Re-dispatched to the same "Verify the DRIFT fleet drains" todo.** Fresh-pulled all 24 slot repos clean. Armed a 26-min
background watch per slot-8/slot-15's recommended cadence, but was directed to proceed immediately rather than wait out
the full window, so this check-in uses a shorter ~5min delta instead (still evidence-based, not a guess):

**15:23:34Z** — all 3 VMs RUNNING (`mtds-drift-sig-walker-gap-20260714-134501`,
`mtds-drift-sig-walker-resume-20260714-134435`, `mtds-solana-drift-backfill`), identical `creationTimestamp` to the
13:43-13:45Z relaunch (no preemption): gap walker 959 parts (oldest 2025-04-27), resume walker 7,217 parts (oldest
2025-12-08).

**15:28:27Z (~5min later)** — all 3 VMs still RUNNING, identical `creationTimestamp`, zero preemption:

- **Gap walker** (`_parts_gap/`): 959→**1,009** parts (+50 in ~5min), oldest sig 2025-04-27→**2025-04-23** (4 chain-days
  advanced). Continuous `page=/collected=/Flushed part-NNNNNN` lines through 15:26:55Z, zero error/exhaust lines
  (grepped `error|exhaust|walk complete`, zero real hits after excluding page/parts-counter false positives).
- **Resume walker** (`_parts/`): 7,217→**7,271** parts (+54 in ~5min), oldest sig 2025-12-08→**2025-12-07** (1 chain-day
  advanced). Same continuous real-progress log pattern through 15:28:12Z, zero error/exhaust lines.
- **Backfill VM** (`mtds-solana-drift-backfill`): still the same long in-memory bootstrap/resolution phase for the
  2025-01-09 window — `RESOURCE_SAMPLE` heartbeats only (RSS 1779→1790MiB rising, CPU 1.2-1.6%), zero new capture/flush
  lines — same pattern every prior check since 14:00Z has diagnosed as genuine-long-resolution, not a stall.

**Verdict: sustained real drain continues, consistent with every check since the 13:45Z relaunch — no incident, no
preemption, no repeat of the 12:39Z false-completion death.** Gate NOT met (todo sub-item 4:
`measure_honest_coverage.py --asset-group defi` not re-run — the backfill VM has flushed nothing new since 14:00Z, so a
corpus-scale manifest read would be byte-identical for zero new signal, exactly the wasteful re-scan the craft's
efficiency north-star warns against). Checkbox NOT flipped — todo sub-items 1 and 4 remain unsatisfiable within a single
dispatch session for a multi-day drain. No new `/blocked` needed (operator's quota-restored ruling already covers
continuing to drain). `/skip-current-task` so this todo returns to the queue for the next check-in, per the established
cadence (slot-6 → slot-3 → slot-2 → slot-4 → slot-8 → slot-15 → this session → next).

### 2026-07-14T16:08Z — data_engineering slot-9 (T+~27min armed watch, following the established cadence: sustained real drain confirmed, gate still not met)

**Dispatched to the same "Verify the DRIFT fleet drains" todo.** Fresh-pulled all 24 slot repos clean (one repo,
`unified-trading-pm`, needed a separate un-timed-out fetch after the batch loop hit the 2-min tool timeout partway
through — confirmed clean afterward). Following the slot-8/slot-15 recommended cadence, armed a single ~27min background
watch (`run_in_background`, no busy-poll — heartbeats sent to the orchestrator throughout) instead of re-dispatching
every few minutes:

**Baseline (15:41:23Z)**: all 3 VMs RUNNING (`mtds-drift-sig-walker-gap-20260714-134501`,
`mtds-drift-sig-walker-resume-20260714-134435`, `mtds-solana-drift-backfill`), same `creationTimestamp` as the
13:43-13:45Z relaunch (no preemption): gap walker 1,133 parts (oldest 2025-04-14), resume walker 7,413 parts (oldest
2025-12-05).

**T+~27min (16:07:53Z)** — all 3 VMs still RUNNING, identical `creationTimestamp`, zero preemption:

- **Gap walker** (`_parts_gap/`): 1,133→**1,392** parts (+259 in ~26.5min), oldest sig 2025-04-14→**2025-03-30** (15
  chain-days advanced). Continuous `page=/collected=/Flushed part-NNNNNN` log lines through 16:06:56Z.
- **Resume walker** (`_parts/`): 7,413→**7,709** parts (+296 in ~26.5min), oldest sig 2025-12-05→**2025-11-30** (5
  chain-days advanced). Same continuous real-progress log pattern through 16:06:10Z.
- **Backfill VM** (`mtds-solana-drift-backfill`): still the same long in-memory bootstrap/resolution phase for the
  2025-01-09 window — `RESOURCE_SAMPLE` heartbeats only (RSS 1890MiB→2197MiB rising, CPU 1.2-2.2%), zero new
  capture/flush lines since the 14:00Z entry. Same pattern every prior check since 14:00Z has diagnosed as
  genuine-long-resolution, not a stall.
- **Zero genuine 429/error/exhaust/false-completion lines** — grepped `429|exhaust|walk complete` on both walker logs,
  excluding page/parts-counter false positives (e.g. `page=429xx`); zero real hits. No repeat of the 12:39Z
  false-completion death signature.

**Verdict: sustained real drain continues, consistent with every check since the 13:45Z relaunch — no incident, no
preemption, no repeat of the 12:39Z false-completion death.** Gate NOT met (todo sub-item 4:
`measure_honest_coverage.py --asset-group defi` not re-run — the backfill VM has flushed nothing new since 14:00Z, so a
corpus-scale manifest read would be byte-identical for zero new signal, exactly the wasteful re-scan the craft's
efficiency north-star warns against). Remaining distance: gap walker ~2025-03-30→2025-01-15 floor ≈ 74 chain-days;
resume walker ~2025-11-30→2025-07-01 floor ≈ 152 chain-days — both within the plan's own 1.7-9 day drain-math estimate,
no acceleration or degradation signal either way (rate is broadly consistent with the slot-14 15:28Z checkpoint's
per-minute rate). Checkbox NOT flipped — todo sub-items 1 and 4 remain unsatisfiable within a single dispatch session
for a multi-day drain. No new `/blocked` needed (operator's quota-restored ruling already covers continuing to drain).
`/skip-current-task` so this todo returns to the queue for the next check-in, per the established cadence (slot-6 →
slot-3 → slot-2 → slot-4 → slot-8 → slot-15 → slot-14 → slot-9 → next).

### 2026-07-14T16:48Z — data_engineering slot-10 (T+~27min armed watch: sustained real drain confirmed, gate still not met)

**Re-dispatched to the same "Verify the DRIFT fleet drains" todo.** Fresh-pulled all 24 slot repos clean. Following the
established cadence, armed a single ~27min background watch (`run_in_background`, no busy-poll — heartbeats sent to the
orchestrator throughout, plus a mid-watch `/progress` heartbeat at ~T+12min) instead of re-dispatching every few
minutes:

**Baseline (16:21:44Z)**: all 3 VMs RUNNING (`mtds-drift-sig-walker-gap-20260714-134501`,
`mtds-drift-sig-walker-resume-20260714-134435`, `mtds-solana-drift-backfill`), same `creationTimestamp` as the
13:43-13:45Z relaunch (no preemption since slot-9's 16:07:53Z check): gap walker 1,530 parts (oldest 2025-03-20), resume
walker 7,862 parts (oldest 2025-11-27).

**T+~27min (16:48:30Z)** — all 3 VMs still RUNNING, identical `creationTimestamp`, zero preemption:

- **Gap walker** (`_parts_gap/`): 1,530→**1,806** parts (+276 in ~26.75min), oldest sig 2025-03-20→**2025-02-28** (20
  chain-days advanced). Continuous `page=/collected=/Flushed part-NNNNNN` log lines through 16:46:58Z, zero genuine
  error/exhaust/false-completion lines.
- **Resume walker** (`_parts/`): 7,862→**8,167** parts (+305 in ~26.75min), oldest sig 2025-11-27→**2025-11-22** (5
  chain-days advanced). Same continuous real-progress log pattern through 16:48:15Z, zero genuine error lines.
- **Backfill VM** (`mtds-solana-drift-backfill`): still the same long in-memory bootstrap/resolution phase for the
  2025-01-09 window — `RESOURCE_SAMPLE` heartbeats only (RSS steady at 3770MiB, CPU 1.6-2.4%), zero new capture/flush
  lines since the 14:00Z entry. Same pattern every prior check since 14:00Z has diagnosed as genuine-long-resolution,
  not a stall.
- **Zero genuine 429/error/exhaust/false-completion lines**: grepped `429|exhaust|walk complete` on both walker logs;
  every hit was a substring false-positive inside log timestamps (e.g. `16:10:42,**429**`) or part/page counters, not a
  real HTTP 429 — verified by inspection, same false-positive class every prior session has flagged.

**Verdict: sustained real drain continues, consistent with every check since the 13:45Z relaunch — no incident, no
preemption, no repeat of the 12:39Z false-completion death.** Gate NOT met (todo sub-item 4:
`measure_honest_coverage.py --asset-group defi` not re-run — the backfill VM has flushed nothing new since 14:00Z, so a
corpus-scale manifest read would be byte-identical for zero new signal, exactly the wasteful re-scan the craft's
efficiency north-star warns against). Remaining distance: gap walker ~2025-02-28→2025-01-15 floor ≈ 44 chain-days;
resume walker ~2025-11-22→2025-07-01 floor ≈ 144 chain-days — both within the plan's own 1.7-9 day drain-math estimate,
no acceleration or degradation signal either way (rate broadly consistent with every prior checkpoint since 13:45Z).
Checkbox NOT flipped — todo sub-items 1 and 4 remain unsatisfiable within a single dispatch session for a multi-day
drain. No new `/blocked` needed (operator's quota-restored ruling already covers continuing to drain).
`/skip-current-task` so this todo returns to the queue for the next check-in, per the established cadence (slot-6 →
slot-3 → slot-2 → slot-4 → slot-8 → slot-15 → slot-14 → slot-9 → slot-10 → next).

### 2026-07-14T17:17Z — data_engineering slot-10 (cycle 2, T+~29min armed watch: sustained real drain confirmed, gate still not met)

**Same slot-10 session continuing to hold this todo** (operator directed continued monitoring rather than
skip-and-requeue between checks). Armed a second ~29min background watch back-to-back with the first (baseline 16:48:30Z
→ this check 17:17:12Z):

**Baseline (16:48:30Z, from this session's first cycle)**: gap walker 1,806 parts (oldest 2025-02-28), resume walker
8,167 parts (oldest 2025-11-22).

**T+~29min (17:17:12Z)** — all 3 VMs still RUNNING (`mtds-drift-sig-walker-gap-20260714-134501`,
`mtds-drift-sig-walker-resume-20260714-134435`, `mtds-solana-drift-backfill`), identical `creationTimestamp`, zero
preemption:

- **Gap walker** (`_parts_gap/`): 1,806→**2,105** parts (+299 in ~28.7min), oldest sig 2025-02-28→**2025-02-02** (26
  chain-days advanced). Continuous `page=/collected=/Flushed part-NNNNNN` log lines through 17:16:59Z, zero genuine
  error/exhaust lines.
- **Resume walker** (`_parts/`): 8,167→**8,488** parts (+321 in ~28.7min), oldest sig 2025-11-22→**2025-11-17** (5
  chain-days advanced). Same continuous real-progress log pattern through 17:16:15Z.
- **Backfill VM** (`mtds-solana-drift-backfill`): still the same long in-memory bootstrap/resolution phase for the
  2025-01-09 window — `RESOURCE_SAMPLE` heartbeats only (RSS slowly climbing 3770→3839MiB, CPU 1.4-2.4%), zero new
  capture/flush lines since the 14:00Z entry. Same pattern every prior check since 14:00Z has diagnosed as
  genuine-long-resolution, not a stall.

**Verdict: sustained real drain continues, consistent with every check since the 13:45Z relaunch — no incident, no
preemption, no repeat of the 12:39Z false-completion death.** Gate NOT met (todo sub-item 4 not re-run — the backfill VM
has flushed nothing new since 14:00Z, byte-identical manifest, wasteful re-scan avoided per the craft's efficiency
north-star). Remaining distance: gap walker ~2025-02-02→2025-01-15 floor ≈ 18 chain-days (close to its floor); resume
walker ~2025-11-17→2025-07-01 floor ≈ 139 chain-days. Checkbox NOT flipped — todo sub-items 1 and 4 remain unsatisfiable
within a single dispatch session for a multi-day drain. No new `/blocked` needed. Continuing to hold this todo per
operator direction; arming a further watch cycle rather than `/skip-current-task`.

### 2026-07-14T16:03-16:14Z — data_engineering slot-11 — relaunched perp-funding + dex-swaps (OOM fix P2), DRIFT fleet still draining, NEW finding: dex-swaps crashes with a DIFFERENT root cause

Picked up `mvp_backfill_defi_onchain_v10-002` on `/boot`. Fresh-pulled all 25 slot repos to `origin/live-defi-rollout`
clean.

**DRIFT fleet (G1.5) — unchanged, consistent with slot-9's concurrent 16:08Z check above**:
`gcloud compute instances list` confirms all 3 VMs still RUNNING (`mtds-drift-sig-walker-gap-20260714-134501`,
`mtds-drift-sig-walker-resume-20260714-134435`, `mtds-solana-drift-backfill`), same `creationTimestamp` as the
13:43-13:45Z relaunch — no preemption. Not re-timing a separate delta window this session (slot-9's concurrent check
already covers it); no new signal to add beyond "still alive, multi-day drain in progress as expected."

**OOM issue doc P2 todo (`mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`) — actioned, mixed result**: confirmed the
fix `market-tick-data-service@d6846f1c` is on `origin/live-defi-rollout` (ancestor-verified) AND the floating
`mtds-code.manifest.json` tarball was refreshed 3 min before this check (`ecd3a4d4` @ 16:00:48Z, matching HEAD) — fix is
genuinely deployable, not just committed. Relaunched both VMs via the canonical launchers (using the working
`/home/ubuntu/google-cloud-sdk/bin/gcloud` — the snap `gcloud`/`gsutil` remain broken in this sandbox, same
`cap_dac_override`/`snap-confine` issue every prior slot hit; exporting `PATH` before invoking the launcher script is
required or its internal tarball-freshness check silently falls back to the broken snap binary and false-reports all 4
tarballs MISSING):

- **`mtds-perp-funding-backfill`** (`--start 2023-11-01 --end 2026-07-14`): launched, tarball-freshness check passed
  (`lc_verify_tarball_freshness: all 4 tarball(s) current`). T+~5min watch: VM RUNNING, past the crash point, and
  **genuinely capturing** — `Perp funding collection complete for 2024-04-03: 2 records across 3 protocols`, per-VM
  manifest shard writes flowing (620 entries, 4 new). **The catalog-registration fix works for this handler.** Issue doc
  P2 todo flipped ✅ for the perp-funding side.
- **`mtds-dex-swaps-backfill`** (`--start 2023-01-01 --end 2026-07-14`): launched, same tarball-freshness pass. T+~4min
  watch: VM **already gone** — crashed `rc=137` (SIGKILL) again, ~25s after process start (`TheGraph key pool loaded` →
  `DEX swaps handler initialized` → one `RESOURCE_SAMPLE rss=666MiB mem=10.3%` → `Killed` → self-deleted). Since this
  used the SAME fresh tarball that let perp-funding survive, **this is a different defect than the one this issue
  fixed** — not the `_register_all_catalog_readers()` all-4-groups load. Quick code read (not a full RSS repro — scoping
  a fresh investigation todo instead, per craft-scoped-verification brief, matching slot-14's precedent of filing rather
  than absorbing unplanned implementation scope): `DexSwapsHandler.process()`
  (`market_tick_data_service/cli/handlers/dex_swaps_handler.py`) is a single 900-line monolithic method; leading
  hypothesis is an eager in-memory accumulation across the full ~3.5yr × 9-protocol range before any flush (this plan's
  own G0.2 gap report shows `dex_pool_swaps` UNISWAP_V3/BALANCER/PANCAKESWAP_V3 alone carry hundreds of thousands of
  `expected_unattempted` cells — a plausible bulk-materialization site), not the small DeFi-only `prod/catalog.parquet`
  cache used by `_catalogue_filter.py` (checked, much smaller than the 4-group combined catalogue the original fix
  targeted). Filed as a new `[SCRIPT] P0` todo in the issue doc with full evidence + a recommended RSS-instrumentation
  approach for whichever fix-worker picks it up next. **Do not re-relaunch `mtds-dex-swaps-backfill` again until
  root-caused** (now 2/2 reproducible: pre-fix and post-fix).

**Net effect on G2**: gate still FAILS on all 6 data_types — DRIFT perp_funding blocked on the multi-day sig-walker
drain (unchanged), `dex_pool_swaps` now blocked on this NEW handler-specific crash (was blocked on the fleet-wide OOM,
which is now understood to be two separate defects), the other 4 data_types' remaining gaps (dex_pool_state Solana
venues per G1.6, lending_indices MORPHO per run #3, lst_rates/oracle_prices minor residuals per the G0.2 gap report)
were not re-measured this session (no re-run of `measure_honest_coverage.py` — no new capture has landed for those since
the last measurement that would move the numbers, same reasoning as every prior session since run #6: a corpus-scale
manifest re-read for zero new signal is the wasteful re-scan the craft's efficiency north-star warns against). Checkbox
NOT flipped. This is a **big finding** (data-pipeline-correctness, blocks G2, handler-specific defect distinct from the
one already believed fixed) — flagged in the issue doc for operator/main visibility rather than a duplicate `/blocked`
(no operator decision needed, this is an implementation-scope fix-worker task). `/skip-current-task` so this todo
returns to the queue for the next check-in, per the established cadence (… → slot-14 → this session → next).

### 2026-07-14T16:25-16:51Z — data_engineering slot-15 (2nd session, T+26min armed watch: sustained real drain confirmed, gate still not met)

**Re-dispatched to the same "Verify the DRIFT fleet drains" todo.** Fresh-pulled all 24 slot repos clean. Armed a single
26-min background watch (`run_in_background`, no busy-poll — periodic orchestrator heartbeats sent throughout while
waiting) per the slot-8/slot-15/slot-9 established cadence.

**Baseline (16:25:05Z)**: all 3 VMs RUNNING (`mtds-drift-sig-walker-gap-20260714-134501`,
`mtds-drift-sig-walker-resume-20260714-134435`, `mtds-solana-drift-backfill`), same `creationTimestamp` as the
13:43-13:45Z relaunch (no preemption): gap walker 1,563 parts (oldest 2025-03-17), resume walker 7,900 parts (oldest
2025-11-27).

**T+26min (16:51:52Z)** — all 3 VMs still RUNNING, identical `creationTimestamp`, zero preemption:

- **Gap walker** (`_parts_gap/`): 1,563→**1,842** parts (+279 in ~26.8min), oldest sig 2025-03-17→**2025-02-25** (20
  chain-days advanced). Continuous `page=/collected=/Flushed part-NNNNNN` log lines through 16:50:58Z.
- **Resume walker** (`_parts/`): 7,900→**8,204** parts (+304 in ~26.8min), oldest sig 2025-11-27→**2025-11-22** (5
  chain-days advanced). Same continuous real-progress log pattern through 16:50:15Z.
- **Backfill VM** (`mtds-solana-drift-backfill`): not re-checked separately this session (still `RUNNING`, same
  `creationTimestamp` per the VM-list check) — no reason to expect a state change absent a new capture signal.
- **Zero genuine 429/error/exhaust/walk-complete lines** — grepped `429|exhaust|walk complete` on both walker logs;
  every hit was the same false-positive class every prior session flagged (millisecond timestamps ending in `,429`, e.g.
  `16:50:27,429`, not HTTP 429s — verified by inspection, none contain the literal words "Too Many Requests" or
  "exhausted").

**Verdict: sustained real drain continues, consistent with every check since the 13:45Z relaunch — no incident, no
preemption, no repeat of the 12:39Z false-completion death.** Gate NOT met (todo sub-item 4:
`measure_honest_coverage.py --asset-group defi` not re-run — no new capture has landed since the last measurement, so a
corpus-scale manifest read would be byte-identical for zero new signal, same reasoning as every prior session since run
#6). Remaining distance: gap walker ~2025-02-25→2025-01-15 floor ≈ 41 chain-days; resume walker ~2025-11-22→2025-07-01
floor ≈ 144 chain-days — both continuing to close, consistent with the plan's own 1.7-9 day drain-math estimate, no
acceleration or degradation signal either way. Checkbox NOT flipped — todo sub-items 1 and 4 remain unsatisfiable within
a single dispatch session for a multi-day drain. No new `/blocked` needed (operator's quota-restored ruling already
covers continuing to drain). `/skip-current-task` so this todo returns to the queue for the next check-in, per the
established cadence (… → slot-9 → slot-11 → this session → next).

### 2026-07-14T17:00-17:22Z — data_engineering slot-6 (2nd session, armed 20min watch: DRIFT fleet healthy, NEW finding — perp-funding VM silently hung at kalshi_perp genesis boundary)

**Re-dispatched to `mvp_backfill_defi_onchain_v10-002`** (`/heartbeat` returned `dispatch_reason: resume` — same task as
this slot's earlier boot). Fresh-pulled all repos clean (done at session start).

**DRIFT fleet — healthy, sustained drain confirmed, consistent with every check since the 13:45Z relaunch**: baseline
17:00:10Z (gap walker 1,928 parts, resume walker 8,296 parts) → T+~21.6min 17:21:44Z (gap walker **2,151** parts [+223],
resume walker **8,538** parts [+242]). Both walkers + the backfill VM confirmed `RUNNING`, zero preemption, zero genuine
error/429/exhaust lines in either walker's log tail. No new signal beyond continued steady-state drain — not re-deriving
remaining chain-days (same math every prior check has already established, no acceleration/degradation).

**NEW FINDING — `mtds-perp-funding-backfill` (the OOM-fix-relaunched VM from slot-11's 16:03-16:14Z session) is silently
HUNG, not draining.** Opportunistically checked its log while tailing the DRIFT fleet (this VM directly gates the
`perp_funding` data_type alongside DRIFT): it collected cleanly from `2023-11-01` through **`2026-05-28`** (last "Perp
funding collection complete" line at `16:28:37Z`), then went completely silent — zero collection/error/traceback lines,
only flat `RESOURCE_SAMPLE`/`PIPELINE_HEARTBEAT` heartbeats — for **53+ minutes** across two independent checks (~17:00Z
and 17:21:44Z, byte-identical last-progress timestamp both times, ruling out "just a slow date"). VM confirmed `RUNNING`
both times (not crashed/preempted — a true hang, distinct from the sibling `rc=137` OOM-kill pattern in
`mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`). Root-cause hypothesis: the immediately preceding log lines show
`kalshi_perp`'s launch date is exactly **2026-05-29** (the date right after the last processed date) — every prior date
took the cheap `EXPECTED_PRE_VENUE_LAUNCH` honest-absence branch for `kalshi_perp`, so 2026-05-29 is the first date
forcing a real live-fetch call for that venue in this VM's entire run, suggesting a missing-timeout hang in
`kalshi_perp`'s collector (mirrors `polymarket_perp`'s already-handled DNS-outage case, but without a timeout/fallback
wrapper). Not SSH-confirmed (out of this craft's sandbox access, same constraint as the sibling OOM issue). **Filed
`issues/mtds_perp_funding_backfill_hang_2026_07_14.md`** with full evidence, root-cause hypothesis, and todos ([BACKEND]
confirm + fix the timeout, [INFRA] relaunch-and-verify once fixed — VM launches are out of data_engineering craft scope
— [SCRIPT] grep other venues for the same missing-timeout pattern).

**Net effect on G2**: gate still FAILS on all 6 data_types. `perp_funding` now has TWO independent blockers instead of
one: (1) DRIFT sig-index walker multi-day drain (unchanged, tracked on the sibling G1.5 todo), (2) this NEW
`kalshi_perp` genesis-date hang (blocks the VM from ever reaching dates past 2026-05-28 regardless of DRIFT's progress).
The other 5 data_types' gaps are unchanged from run #6's reading (not re-measured — no new capture has landed for those
since the last measurement, same reasoning as every prior session since run #6). Checkbox NOT flipped. No new `/blocked`
filed — this is an implementation-scope fix (timeout + relaunch), not an operator decision, consistent with how the
sibling OOM issue was triaged. `/skip-current-task` so this todo returns to the queue for the next check-in, per the
established cadence (… → slot-9 → slot-11 → this session → next).

### 2026-07-14T17:27-17:31Z — data_engineering slot-4 (fresh FULL corpus re-measurement, first since 13:13Z: gate FAILS across all 6 data_types with materially larger gaps; perp-funding hang confirmed still live 60+ min later)

**Dispatched to `mvp_backfill_defi_onchain_v10-002`** (G2 final verify). Fresh-pulled all 24 slot repos clean. Rather
than repeat another short-window DRIFT-only VM check (12+ prior sessions today already established that exact pattern),
ran a genuinely fresh full-corpus `measure_honest_coverage.py --asset-group defi` — the last full run was at 13:13Z
(slot-2), over 4 hours stale, and multiple non-DRIFT VMs (dex-pools, solana-defi, lending-indices, lst-rates, oracle,
perp-funding) have been running independently in that window, so this was not the "wasteful re-scan for zero new signal"
every prior session correctly avoided.

**Manifest**: `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, 27,445,013 rows
(blob updated 2026-07-14T12:56:34Z) — up from ~9.8M rows at the 2026-06-28 phantom-reconcile baseline. Aggregated the 6
MVP data_types across all venues from the fresh JSON (`/tmp/defi_coverage_1727z.json`, not committed — scratch output):

| data_type       | captured  | attempted_failed | expected_unattempted | coverage | gate |
| --------------- | --------- | ---------------- | -------------------- | -------- | ---- |
| dex_pool_state  | 1,580,941 | 2,109            | 2,305,986            | 40.65%   | FAIL |
| dex_pool_swaps  | 642,747   | 21,624           | 3,928,084            | 14.00%   | FAIL |
| lending_indices | 133,695   | 1,010            | 606,864              | 18.03%   | FAIL |
| lst_rates       | 14,979    | 851              | 12,392               | 53.08%   | FAIL |
| perp_funding    | 3,365     | 214              | 81,724               | 3.94%    | FAIL |
| oracle_prices   | 29,884    | 873              | 209,934              | 12.42%   | FAIL |

**All 6 gates FAIL — none newly close.** Notably the `expected_unattempted` denominators are now substantially LARGER
than the 2026-06-27 G0.2 baseline (e.g. dex_pool_state UNISWAP_V3 expected_unattempted 138,799→669,447; dex_pool_swaps
UNISWAP_V3 191,711→1,631,694; lending_indices MORPHO 55,506→416,522) even though `captured` also grew — the MVP
catalogue's expected-cell skeleton is still expanding (more shard-dates/instruments registered over time), so this is
not evidence of regression, but it does mean the "% coverage" figures from earlier in this Progress Log are stale and
understate the remaining gap in absolute-cell terms. Full per-venue gap list captured in this session's tool output for
any follow-up worker (not reproduced here — see the script re-run instructions in the G2 todo).

**Noted, not investigated further (out of this task's verification scope, already touches existing tracked docs)**:
`oracle_prices`/`perp_funding` expected-skeleton cells exist for LIGHTER/EXTENDED/PACIFICA — venues this plan's own top
banner explicitly rules OUT of DeFi scope ("v10 decision #4"). These already surface in
`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` and
`cross_ag_never_seeded_backlog_scan_2026_07_06.md`'s territory — not filing a duplicate; flagging only so a future G2
verification doesn't mistake it for a fresh regression.

**DRIFT fleet — still healthy, sustained drain, consistent with every check since 13:45Z**:
`gcloud compute instances list` confirms `mtds-drift-sig-walker-gap-20260714-134501` +
`mtds-drift-sig-walker-resume-20260714-134435` + `mtds-solana-drift-backfill` all RUNNING, same `creationTimestamp` as
the relaunch (no preemption). Parts counts vs slot-6's 17:21:44Z reading: gap walker 2,151→**2,256** (+105 in ~10min),
resume walker 8,538→**8,652** (+114 in ~10min) — both still closing on their floors at the established rate.

**`mtds-perp-funding-backfill` hang CONFIRMED STILL LIVE** (slot-6's 17:00-17:22Z finding, `kalshi_perp` genesis-date
hang, `issues/mtds_perp_funding_backfill_hang_2026_07_14.md`): log tail at 17:31Z shows the identical flat
`RESOURCE_SAMPLE`/`PIPELINE_HEARTBEAT`-only pattern with zero collection lines since the same 16:28:37Z last-progress
timestamp — now 60+ minutes hung, not a transient stall. Confirms the issue doc's diagnosis rather than adding a new
finding; no fix attempted (VM relaunch + timeout fix are out of data_engineering craft scope per that doc's own task
split, [BACKEND]/[INFRA] tagged).

**`mtds-dex-swaps-backfill` — confirmed ABSENT** (`gcloud compute instances list` shows no instance): consistent with
slot-11's 16:03-16:14Z finding that it crashed `rc=137` a second time and was deliberately NOT relaunched pending
root-cause (issue doc todo still open, single monolithic-method eager-accumulation hypothesis, not yet fixed).

**Verdict: gate unambiguously NOT met on any of the 6 data_types — multiple independent, already-tracked blockers (DRIFT
multi-day drain, perp-funding hang, dex-swaps crash, dex_pool_state/lst_rates/oracle_prices residual gaps).** None
resolvable within a single dispatch session. Checkbox NOT flipped. No new `/blocked` — every open blocker already has
either an operator ruling (Helius quota) or an actionable issue-doc todo (perp-funding hang, dex-swaps crash) that a
fix-scoped worker will pick up separately; this session's contribution is confirming, with fresh full-corpus evidence
(not just the DRIFT-only lens), that none of them have silently resolved. `/skip-current-task` so this todo returns to
the queue for the next check-in, per the established cadence (… → slot-9 → slot-11 → slot-6 → this session → next).

### 2026-07-14T17:44Z — data_engineering slot-10 (cycle 3 — MILESTONE: gap walker GENUINELY reached its `--back-to` floor)

**Same slot-10 session, cycle 3 of its continued-monitoring watch** (baseline 17:17:12Z → this check 17:44:23Z).

**`mtds-drift-sig-walker-gap-20260714-134501` — COMPLETED, genuinely, not the 12:39Z false-positive pattern.** Log shows
the explicit termination condition:
`page=229625 oldest=2025-01-14 ... "Crossed back-to floor (2025-01-14 < 2025-01-15) at page=229625 — terminating"`, then
`"Walk complete: 229625000 new sigs in 13649.0s (~16824 sigs/s) across 2297 new parts"`, exit `rc=0`, self-deleted
cleanly (`gcloud compute instances list` now shows only `mtds-drift-sig-walker-resume-20260714-134435` +
`mtds-solana-drift-backfill`, the gap walker instance is gone). **This is the first genuine walker completion in this
todo's entire history** — distinguished from the 12:39Z death by the explicit `"Crossed back-to floor"` log line
(present here, absent in every 429-exhaust death) and by having processed 2,297 real parts (229.6M sigs) over its
~3h51min run, vs. 0 parts in ~20s for the false-completion case. `_index/drift_v2_sig_index_parts_gap/` final count:
2,297 parts, spanning 2025-07-01T23:00Z → 2025-01-14 — the full gap segment is now indexed.

**`mtds-drift-sig-walker-resume-20260714-134435` — still RUNNING, still draining normally.** 8,488→**8,798** parts (+310
since the 17:17Z check, ~27min), oldest sig 2025-11-17→**2025-11-12** (5 chain-days). Continuous `page=/Flushed part`
lines through 17:44:17Z, zero error lines. Remaining distance to its `--back-to 2025-07-01` floor: ~134 chain-days — at
the sustained ~5-6 chain-days/~27min rate observed across every cycle this session, that's roughly 10-12 more hours, not
the original multi-day worst case (the gap walker's completion in ~3h51min against its ~167-day span suggests both
walkers are running faster than the plan's original pessimistic density estimate).

**`mtds-solana-drift-backfill` — still RUNNING, same long bootstrap/in-memory phase**, RSS climbing 3839→3940MiB, CPU
1.6-2.2%, zero new capture/flush lines since 14:00Z — same pattern every check since 14:00Z has diagnosed as
genuine-long-resolution, not a stall.

**Todo sub-item 1 status: HALF met** — gap walker floor reached; resume walker not yet. **Todo sub-item 3** ("after
walkers complete, re-run the backfill VM for the newly-indexed window") does not yet apply — only one of two walkers is
done, and the backfill VM itself hasn't finished its current window either; revisit once the resume walker also
completes. **Todo sub-item 4** (honest-coverage gate) not re-run — no capture has landed yet from either walker's
newly-indexed range (that requires the backfill VM to actually process 2025-01-15→2025-12-23, which hasn't started).
Checkbox NOT flipped — sub-items 1 and 4 remain unmet. Continuing to hold this todo per operator direction; next watch
cycle narrows focus to the resume walker (now the sole gating segment) and the backfill VM's progress.

### G2 final verification run (2026-07-14 18:10-18:35Z, data_engineering slot-16) — GATE NOT MET, checkbox NOT flipped

Ran this todo's own checklist fresh (no reliance on stale numbers):
`python scripts/measure_honest_coverage.py --asset-group defi` (instruments-service, 18:10-18:12Z; manifest
`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, 27,445,013 rows,
`blob.updated=2026-07-14T12:56:34Z`).

**Overall defi: 19.71% honest coverage** (captured=3,010,913 / reachable=15,277,756; `all_shards_coverage_pct=10.97%`).
Tool's own caveat: `denominator_status: INCOMPLETE` — Layer-1 catalogue alignment is only 86.21% (EXPECTED=87,
ENUMERATED=244, matched=75, missing=12, stray=169 post-align) and "MERGE DISABLED for defi: legacy bucket(s) unreachable
(`market-data-tick-defi-central-element-323112`), expected_unattempted skeleton may be incomplete" — so these numbers
are a **lower bound**, not necessarily the full picture.

**Per-data_type aggregate (summed across all venues, `by_venue_data_type` in the coverage JSON) — Gate =
`attempted_failed=0 AND expected_unattempted=0`:**

| data_type       | captured  | attempted_failed | expected_unattempted | gate |
| --------------- | --------- | ---------------- | -------------------- | ---- |
| dex_pool_state  | 1,580,941 | 2,109            | 2,305,986            | FAIL |
| dex_pool_swaps  | 642,747   | 21,624           | 3,928,084            | FAIL |
| lending_indices | 133,695   | 1,010            | 606,864              | FAIL |
| lst_rates       | 14,979    | 851              | 12,392               | FAIL |
| oracle_prices   | 29,884    | 873              | 209,934              | FAIL |
| perp_funding    | 3,365     | 214              | 81,724               | FAIL |

**All 6 MVP data_types FAIL the gate** — this is not close; `expected_unattempted` alone totals ~7.1M rows across the 6
types, with the largest single contributors being `UNISWAP_V3` (`dex_pool_swaps` expected_unattempted=1,631,694;
`dex_pool_state` expected_unattempted=669,447), `BALANCER` (`dex_pool_swaps`=954,070), `MORPHO`
(`lending_indices`=416,522), and the Solana REST-only venues `ORCA`/`RAYDIUM`/`KAMINO`/`TRADER_JOE_V2`/`VELODROME_V2` (0
captured each, still draining per the `mtds-solana-defi-backfill` VM launched in G1.6 — see that section; a
single-day-run VM against a multi-year window cannot close a multi-million-row gap in one pass, more waves needed).
DRIFT perp_funding specifically: `captured=8, attempted_failed=39, expected_unattempted=51,301` — **NOTE**: this
`expected_unattempted` figure is materially different from the 13:15Z banner's `expected_unattempted=0` claim for the
same cell; not reconciled in this pass (possible Layer-1 catalogue-expansion effect vs a real regression — flagged for
whoever next touches G1.5, not chased down here to keep this verification task in scope).

Also ran the phantom-reconcile dry-run directly
(`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run`, required
`GCP_PROJECT_ID=central-element-323112` in-shell — bucket-name template resolution needs it and it isn't set in this
agent sandbox by default) — launched at 18:32Z, still running a full-manifest load (27M rows) as of this writing; result
to follow in a subsequent Progress Log entry once it completes (single-walk discipline: not re-running this again once
done, and not blocking this checkbox decision on it since the primary coverage gate above already fails by orders of
magnitude regardless of the phantom count).

**Fleet status cross-check** (GCS heartbeat blobs, since `gcloud`/`gsutil` CLI are unavailable in this sandbox —
snap-confine blocked — used the `google.cloud.storage` Python client directly):
`mtds-drift-sig-walker-resume-20260714-134435` and `mtds-solana-drift-backfill` heartbeats fresh at 18:34:58-59Z (both
still RUNNING); `mtds-drift-sig-walker-gap-20260714-134501` heartbeat stale since 17:35:33Z, consistent with this plan's
own 17:44Z note that the gap walker already reached its floor and self-deleted. No fleet action taken — backfill is
progressing per the existing watch cadence, nothing here changes that.

**Two tooling defects found and NOT fixed inline (out of this task's scope, filed as their own issue)**: (1) running the
audit orchestrator `e2e-testing/scripts/audit/manifest_hygiene_daily.py --asset-group defi --mode full` almost clobbered
the ALREADY-RESOLVED `plans/active/issues/manifest_hygiene_red_2026_07_14.md` (a same-day `cefi`-only run by another
slot) — the escalation-issue filename is date-keyed only, not asset_group-keyed; caught via `git diff` before it
committed, restored via `git restore`, nothing lost. (2) that same run's internal phantom-reconcile subprocess call
failed on the same missing-`GCP_PROJECT_ID` issue and was mis-recorded as a genuine
`phantom_captured_no_parquet: count=1` finding instead of a harness error. Both filed as P2 actionable todos in
`issues/manifest_hygiene_daily_tooling_defects_2026_07_14.md` (repo: e2e-testing).

**Verdict: G2 gate NOT met for any of the 6 MVP data_types. Checkbox NOT flipped.** This is expected given the backfill
fleet (G1/G1.5/G1.6) is still actively draining multi-year, multi-venue history — re-run this same verification once the
fleet reports all VMs TERMINATED/complete rather than RUNNING.

**Follow-up (18:55Z): the phantom-reconcile dry-run launched above never completed** — killed by the agent sandbox's own
process timeout after 20+ min still stuck on the initial manifest load (no progress past
`Loading manifest from gcp://.../availability_index.parquet`), consistent with this plan's own prior sessions recording
20-35+ min for a full-corpus phantom listing. Not re-attempted this session (single-walk discipline + the primary
coverage gate above already fails unambiguously) — leaving the phantom/dual-key-ghost count as an open item for
whichever session next has the time budget for a full run.

### 2026-07-14T18:12-19:00Z — data_engineering slot-10 (cycle 4: resume walker + backfill VM both draining well; own coverage remeasure attempt stalled, superseded by slot-16's concurrent fresh numbers)

**Same slot-10 session, cycle 4.** Baseline 17:44:23Z (from cycle 3) → this check spans 18:12:26Z through ~19:00Z.

**`mtds-drift-sig-walker-resume-20260714-134435` — still RUNNING, still draining well.** 8,798→**9,653** parts (+855
across the ~75min elapsed this cycle, including the extended coverage-script wait below), oldest sig
2025-11-12→**2025-10-28** (15 chain-days). Continuous `page=/Flushed part` lines throughout, zero error lines. Now the
sole gating walker segment (gap walker completed in cycle 3).

**`mtds-solana-drift-backfill` — exited its long bootstrap phase and produced its FIRST genuine capture** since the
13:45Z relaunch: `"Solana DeFi collection for 2025-01-10: 968079 total records"` (18:09:55Z), then began processing
`"Drift Helius backfill: 760705 sigs in window [2025-01-11, 2025-01-11] for SOL-PERP"` (18:09:57Z). After that burst it
returned to `RESOURCE_SAMPLE`-only heartbeats (RSS steady ~3317-3340MiB) for the rest of the cycle — consistent with the
same heavy per-day sig-index dedup-load cost diagnosed in every earlier check, just now interleaved with actual capture
instead of pure bootstrap. This is the first non-bootstrap activity from this VM in ~5 hours of monitoring.

**This session's own `measure_honest_coverage.py --asset-group defi` re-run STALLED and was killed.** Launched 18:15Z
(justified at the time: the backfill VM had just started genuine capture, making a remeasure informative rather than
wasteful). It progressed normally through manifest load (27,445,013 rows) and the Layer-1 completeness check (completed
18:25:09Z, INCOMPLETE 86.2% — same as every recent run), then produced ZERO further log lines for 42+ minutes at process
state `Dl` (uninterruptible I/O wait, ~4% CPU, ~75MB RSS) — genuinely stalled, not computing. Killed (`kill -9`) at
18:57Z rather than waiting indefinitely. **Superseded**: slot-16 ran the identical script concurrently at 18:10-18:12Z
(see the G2 final verification entry immediately above) and got a clean result — DRIFT
`perp_funding: captured=8, attempted_failed=39, expected_unattempted=51,301` (gate FAIL), overall defi 19.71% coverage,
all 6 MVP data_types FAIL. Per single-walk discipline, not re-attempting a third full-corpus run for the same
~10-minute-old data; this stall (Layer-1 completes but Layer-2 aggregation occasionally hangs) is worth a future
session's attention if it recurs, but is not filed as a fresh issue here (unconfirmed whether reproducible vs. a one-off
resource contention on a shared host already running slot-16's own full pass minutes earlier).

**Verdict: fleet continues to genuinely drain (now 1 of 2 walker segments complete), backfill VM producing its first
real capture, gate still NOT met** per slot-16's concurrently-fresh numbers (DRIFT perp_funding attempted_failed=39,
expected_unattempted=51,301, both nonzero). Checkbox NOT flipped — todo sub-items 1 (both walkers) and 4 (gate) remain
unmet. Continuing to hold this todo per operator direction.

### 2026-07-14 ~18:49Z — perp_funding `kalshi_perp`-hang blocker cleared; DRIFT drain ETA ~10.8h

`mtds-perp-funding-backfill` no longer hangs at the `kalshi_perp` 2026-05-29 genesis boundary
(`issues/mtds_perp_funding_backfill_hang_2026_07_14.md`, `[INFRA] P2` — flipped by slot-3,
`unified-trading-pm@5a448b524`, independently re-corroborated on live infra this session): relaunched
`--start 2026-05-29 --end 2026-07-14` onto the fix-composed tarball (`market-tick-data-service@56efdd7d` +
`unified-api-contracts@ea68ef46`, republished 18:13Z), completed `Batch complete: 47 results collected` at 18:29:09Z
(rc=0, clean self-delete) — `kalshi_perp` wrote real funding rows for all 47/47 dates via the correct margin-API host,
zero ticker-discovery churn. `perp_funding`'s other blocker, the DRIFT sig-index resume walker
(`mtds-drift-sig-walker-resume-20260714-134435`), is still draining: parts count 8,798 (17:45Z) → 9,549 (18:49:13Z),
+751 parts/64.2min ≈ 11.7 parts/min; `oldest=` reached 2025-10-30 against a `--back-to 2025-07-01` floor, ≈121 days of
history remaining at the observed ~11.2 days/hour pace → **extrapolated ~10.8h to floor**. Sibling gap walker already
reached its own floor and self-deleted (17:35:21Z, exit_code=0) — not part of this ETA. G2 gate itself still FAILS
pending that drain (see the fresh full-corpus re-measurement above); this entry only closes out the independent
`kalshi_perp`-hang axis of `perp_funding`'s blockers.

### 2026-07-14T19:26Z — data_engineering slot-10 (cycle 5: resume walker continues on ETA, backfill VM idle since its one capture burst)

**Same slot-10 session, cycle 5.** Baseline 18:57Z (9,653 parts, oldest 2025-10-28) → this check 19:26:29Z:

- **Resume walker** (`_parts/`): 9,653→**9,984** parts (+331 in ~29min), oldest sig 2025-10-28→**2025-10-22** (6
  chain-days). Continuous `page=/Flushed part` lines through 19:26:21Z, zero error lines — consistent with the
  ~10.8h-to-floor ETA another session computed independently above (this session's own rate: ~11.4 chain-days/hour, in
  the same ballpark).
- **Backfill VM** (`mtds-solana-drift-backfill`): back to `RESOURCE_SAMPLE`-only heartbeats since its 18:09-18:10Z
  capture burst (2025-01-10/2025-01-11) — RSS flat at 3317MiB, no new capture/flush lines in ~76min. Not yet calling
  this a stall: the 2025-01-11 window's 760,705-sig resolution (logged at 18:09:57Z) may simply still be in progress,
  matching every prior long-per-day-resolution diagnosis this todo has made; worth a closer look if it's still flat next
  cycle.
- All 3-VM-turned-2-VM fleet still RUNNING, zero preemption.

**Verdict: sustained real drain continues on the resume walker, consistent with the ~10.8h ETA.** Gate still not met.
Checkbox NOT flipped. Continuing to hold this todo per operator direction.

### 2026-07-14T19:55Z — data_engineering slot-10 (cycle 6 — IMPORTANT FINDING: backfill VM's real ETA is materially longer than the sig-walker ETA; two distinct clocks, not one)

**Same slot-10 session, cycle 6.** Resume walker: 9,984→**10,312** parts (+328 in ~29min), oldest sig
2025-10-22→**2025-10-16** (6 chain-days) — still on the ~10.8h ETA track.

**Backfill VM investigation — this session filtered out the `RESOURCE_SAMPLE`/`PIPELINE_HEARTBEAT` noise to find the
actual state transitions**, since the last 3 cycles all reported it "idle since its one capture burst" without digging
further. The real picture (from `mtds-solana-drift-backfill`'s full log, filtered):

| day        | index loaded | capture written | wall time |
| ---------- | ------------ | --------------- | --------- |
| 2025-01-09 | 14:00:11Z    | 16:17:25Z       | ~2h17min  |
| 2025-01-10 | 16:17:29Z    | 18:09:53Z       | ~1h52min  |
| 2025-01-11 | 18:09:57Z    | 19:37:28Z       | ~1h27min  |
| 2025-01-12 | 19:37:32Z    | (in progress)   | —         |

**This VM is NOT idle between bursts — it's genuinely spending 1.5-2.3 HOURS PER DAY** resolving that day's Drift sigs
via the Helius batch endpoint (`POST /v0/transactions`, 100 sigs/batch), and every prior cycle's "back to
RESOURCE_SAMPLE-only, not calling it a stall yet" note was correctly cautious but understated how slow this genuinely
is. Root cause read from `solana_defi_drift_helius.py`: `_HELIUS_BATCH_REQUESTS_PER_SECOND = 5.0`, `batch_size = 100` →
a hard 500 sigs/s theoretical ceiling via the shared `VenueRateLimiter` singleton (`HELIUS-SOLANA`) — the SAME limiter
key the resume walker's `getSignaturesForAddress` calls also draw from, so the two processes are contending for the same
rate budget. Observed throughput is well below even that 500 sigs/s cap (2025-01-09: 1,209,478 sigs in ~8,240s ≈ 147
sigs/s), consistent with walker contention plus per-batch response latency.

**This VM was launched for the FULL window `--start 2025-01-09 --end 2026-07-14`** (per the 13:45Z relaunch entry above)
— not just the newly-indexed 2025-01-15→2025-12-23 gap. At the observed ~1.5-2.3h/day rate, if a meaningful fraction of
that ~552-day window still needs real Helius resolution (consistent with `perp_funding`'s tiny `captured=8` count as of
the 18:10Z coverage remeasure — 3 real days captured so far, this is day 4), **completing the full backfill leg could
take many days of wall-clock, materially longer than the ~10.8h walker ETA another session computed.** The two are
DIFFERENT clocks: (1) sig-index walker ETA (~10.8h, on track) builds the _index_ the backfill VM reads from; (2)
backfill VM throughput (~1.5-2.3h/day × however many uncaptured days remain) is the actual gate denominator — todo
sub-item 4 cannot pass until day 2 finishes, independent of walker completion.

**Not filing a separate issue doc for this** — it's squarely within this todo's own verification scope (the backfill VM
IS one of the 3 fleet members this todo tracks), so it belongs in this Progress Log, not a spun-out doc. Flagging
prominently here so the next session (or the operator) doesn't mistake "walker ETA ~10.8h" for "gate ETA ~10.8h" — they
are not the same number. Not proposing a fix (raising `_HELIUS_BATCH_REQUESTS_PER_SECOND` risks reproducing the 12:39Z
quota-exhaustion incident that already happened once today on this same shared key) — this is an operator-scoped
throughput/timeline tradeoff, not a code defect to patch inline.

**Verdict: gate still not met; NEW information changes the completion-timeline picture** (backfill throughput, not just
walker completion, now the binding constraint). Checkbox NOT flipped. Continuing to hold this todo per operator
direction; next cycle should track day-by-day backfill VM progress (day 2025-01-12 onward) alongside the resume walker.

### 2026-07-14T20:24Z — data_engineering slot-10 (cycle 7: resume walker on pace, backfill VM into day 2025-01-12, no new day completion yet)

**Same slot-10 session, cycle 7.** Resume walker: 10,312→**10,649** parts (+337 in ~29min), oldest sig
2025-10-16→**2025-10-11** (5 chain-days) — steady, no error lines, no preemption.

**Backfill VM**: still on **day 2025-01-12**
(`"Drift Helius backfill: 722284 sigs in window [2025-01-12, 2025-01-12] for SOL-PERP"`, started 19:37:32Z) — ~47min
elapsed as of this check, no capture-written line yet. Consistent with the ~1.5-2.3h/day pattern from cycle 6 (day 3's
760,705 sigs took ~1h27min; day 4's 722,284 sigs, a similar size, is tracking the same order of magnitude) — not a
stall, just not yet done.

**Verdict: both segments progressing normally, gate still not met.** Checkbox NOT flipped. Continuing to hold this todo
per operator direction.

### 2026-07-14T20:52Z — data_engineering slot-10 (cycle 8: resume walker on pace, backfill VM still on day 4 at ~75min)

**Same slot-10 session, cycle 8.** Resume walker: 10,649→**10,965** parts (+316 in ~28min), oldest sig
2025-10-11→**2025-10-05** (6 chain-days) — steady, no error lines.

**Backfill VM**: still on day 2025-01-12 (started 19:37:32Z), ~75min elapsed, no capture-written line yet. Within the
historical per-day range (87-137min observed for days 1-3) but approaching the upper end — worth watching next cycle;
not yet calling it a stall.

**Verdict: both segments healthy, gate still not met.** Checkbox NOT flipped. Continuing to hold this todo per operator
direction.

### 2026-07-14T21:19Z — data_engineering slot-10 (cycle 9: day 4 completed cleanly, resume walker on pace)

**Same slot-10 session, cycle 9.** Resume walker: 10,965→**11,278** parts (+313 in ~27min), oldest sig
2025-10-05→**2025-09-29** (6 chain-days) — steady, no error lines.

**Backfill VM**: **day 2025-01-12 completed** at 21:01:12Z (722,284 rows written) — took ~1h23min total, within the
historical range; one transient `HTTP 504` at 20:54:24Z self-recovered on retry (no action needed, the retry/backoff
mechanics handled it as designed). Now on **day 2025-01-13** (started 21:01:16Z, 1,215,691 sigs — the largest batch
yet). 4 real days captured so far (2025-01-09 through -12).

**Verdict: both segments healthy, gate still not met.** Checkbox NOT flipped. Continuing to hold this todo per operator
direction.

### 2026-07-14T21:47Z — data_engineering slot-10 (cycle 10: resume walker on pace, day 5 in progress ~46min)

**Same slot-10 session, cycle 10.** Resume walker: 11,278→**11,595** parts (+317 in ~28min), oldest sig
2025-09-29→**2025-09-23** (6 chain-days) — steady, no error lines.

**Backfill VM**: still on day 2025-01-13 (started 21:01:16Z, 1,215,691 sigs), ~46min elapsed, no capture-written line
yet — well within range given day 1's comparably-sized 1,209,478-sig window took ~137min total.

**Verdict: both segments healthy, gate still not met.** Checkbox NOT flipped. Continuing to hold this todo per operator
direction.

### 2026-07-14T22:15Z — data_engineering slot-10 (cycle 11 — INCIDENT: resume walker died genuinely (validates the 429-fix); backfill VM now hitting sustained quota exhaustion; BLOCKED-OPERATOR-DECISION filed)

**Same slot-10 session, cycle 11.** Two significant developments this cycle:

**1) `mtds-drift-sig-walker-resume-20260714-134435` — DIED, genuinely, at 22:04:38Z.** Unlike the 12:39Z false-positive
death, this is a CORRECT failure signal validating the `e4c04c64` fix shipped earlier today: after 8h+ of real progress
(548,999,000 new sigs across 5,490 new parts since its 13:44Z relaunch), it hit `getSignaturesForAddress`
`429 Too Many Requests`, exhausted 5 retries, and logged
`"Walk INCOMPLETE (retry-exhausted): ... API saturated/exhausted, NOT a genuine walk-complete. Diagnose before relaunching."`
— exit code 1 (FAILED, not the old false `rc=0`), then self-deleted (`VM_SHUTDOWN_ON_COMPLETION=true`). The fix is
working exactly as designed: a genuine retry-exhaustion now surfaces as an honest failure instead of a silent
false-positive success. Final position: oldest sig 2025-09-23, `_parts/` at 11,783 parts — real, substantial progress
(from the 6,293 baseline this morning), just not to its `--back-to 2025-07-01` floor.

**2) `mtds-solana-drift-backfill` — now hitting SUSTAINED 429-exhaustion on every batch, 0 captures across 4+
consecutive days** (2025-06-26, -27, -28, -29 — the day loop apparently skipped ahead rapidly through ~160 days between
01-13 and 06-26 that all showed `0 sigs in window`, confirming the stale-cached-sig-index risk this plan's 13:15Z entry
already anticipated: those days' sigs live in the gap walker's now-completed `_parts_gap/` segment, which this VM's
in-memory index (loaded once at 13:43Z boot, still reporting the same static `7291 parts across 0 prefixes {}` five+
hours later) never picked up — **confirmed, not just anticipated: sub-item 3's "re-run backfill after walkers complete"
is now demonstrably necessary, not optional**). Once the day-loop reached 2025-06-26 (a date NOT covered by the stale
snapshot, needing fresh Helius resolution), it hit real signature volume (1.2-1.5M sigs/day) and every single batch has
429-exhausted since — even with the resume walker now dead (so this is NOT walker-contention; the shared Helius key's
quota is genuinely low/exhausted again, independent of the walker). Verified the code path is CORRECT here (read
`solana_defi_drift_helius.py::_resolve_one_helius_batch`/`_resolve_helius_rows`): retry-exhaustion on any batch calls
`recorder.record_failed(...)` and returns `None`, which the caller (`_backfill_drift_helius_date`) correctly treats as
`return 0` WITHOUT calling `record_zero_rows` — so these 429-exhausted days ARE being recorded as `attempted_failed`,
not silently stamped as honest-empty. The `"N total records"` summary log line just doesn't distinguish the reason (both
paths return 0), which read alarming at first glance but is NOT a manifest-correctness bug — confirmed via code read,
not just log inspection.

**Per the standing stop-rule** (13:45Z relaunch entry: "if any VM repeats the 429-exhaust death, do NOT relaunch a third
time — report autoscaling lag and stop") — **NOT relaunching the resume walker.** The backfill VM is continuing to run
and is genuinely burning SPOT-minutes for zero new captures right now (racing through failed days in ~1-2min each via
the retry/backoff cascade, vs. the ~1.5-2.3h/day real-capture rate) — analogous to the 13:20Z protective-stop precedent,
but stopping a VM is a fleet action outside this session's unilateral call given the genuine ambiguity (relaunch
policy + whether to stop the backfill VM are both live operator-scoped decisions). **`/blocked` filed (`BLK-b56b7986`)**
with options: (A) relaunch resume walker a 3rd time, (B) leave it dead and let the backfill VM keep running/failing, (C)
stop the backfill VM too (protective, reversible). Recommendation: (C). Continuing to monitor per `can_continue` while
awaiting the ruling — checkbox NOT flipped, gate still not met (4 real days captured, resume walker's sig-index build
now stalled at 2025-09-23 pending the relaunch decision).

> **This is a historical operational log, not this file's own live todo list — Part 3 of 3 (final part).** This file is
> the chronological CONTINUATION of `plans/active/mvp_backfill_defi_onchain_v10_operational_log_part2_2026_07_24.md`
> (Part 2), picking up at the 2026-07-14T22:24Z "BLK-b56b7986 ANSWERED" entry and running to the end of the log
> (2026-07-17). For the earliest history see `plans/active/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md`
> (Part 1). Every line below is preserved VERBATIM from where it previously lived in Part 1 before this 2026-07-24 chunk
> split — nothing about what was done or what remains open has changed. **The parent plan
> (`mvp_backfill_defi_onchain_v10_2026_06_27.md`) remains the sole SSOT for current todo/gate state.** This file exists
> purely to bring the operational log back under the plan-hygiene line cap. No checkboxes fall within this part's range
> (all 7 pre-existing G1.5 sub-history checkboxes live earlier, in Part 1).

### 2026-07-14T22:24Z — data_engineering slot-10 (BLK-b56b7986 ANSWERED: option C ruled — backfill VM stopped; task now BLOCKED-CREDENTIALS pending Helius quota/2nd-key)
