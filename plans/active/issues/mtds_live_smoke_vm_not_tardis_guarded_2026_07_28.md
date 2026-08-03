---
doc_type: issue
title:
  launch-mtds-live.sh does not source the Tardis N=1 concurrency guard — a live-leg smoke check can contend with an
  active Tardis backfill
summary:
  launch-mtds-live.sh creates real Tardis-fetching test-run VMs without sourcing tardis-concurrency-guard.sh, unlike
  launch-mtds-backfill-vm.sh — a live-leg pipeline_e2e_check smoke test against a Tardis-sourced venue can contend for
  the shared single-IP Tardis key with an active real backfill, risking the same 403-storm/false-attempted_failed
  corruption the guard exists to prevent.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, unified-trading-pm]
scope: [engineer]
tags: [tardis, concurrency-guard, mtds, live-leg, pipeline-e2e-check]
related: [/plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md]
created: 2026-07-28
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
resolved_by:
locked_by:
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md,
    deployment-service/scripts/vm/launch-mtds-live.sh,
    deployment-service/scripts/vm/tardis-concurrency-guard.sh,
  ]
source: cefi_track2_coverage_backfill_checkpoints_2026_07_25.md
drift_direction: advance-code
depends_on: []
---

## What I found

Running `/data-pipeline-check-mtds --asset-group cefi --day 2026-03-15` (the MID-BACKFILL spot-check todo in
`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) while the Track-2 coverage backfill VM
(`cefi-queue-heavy-binancefutu-x17-20260727-210013`) was actively running and holding the sole Tardis IP lease:

- The check's **force/skip legs** (`launch-mtds-backfill-vm.sh`) correctly sourced `tardis-concurrency-guard.sh` and
  were refused/retried for the `BINANCE-SPOT/trades` cell
  (`launcher exited 1 ... 5 streams (default 4 — its own cap) ... Keep total concurrent connections well under Tardis's tolerance`)
  — the guard working as designed. Neither VM (`mtds-backfill-cefi-pipelinecheck-20260728-035930-6f8fe8` force,
  `...-035948-6f8fe8` skip) was ever created (absent from `gcloud compute instances list`).
- The check's **live leg** (`launch-mtds-live.sh --test-run --max-duration-seconds 90`) for the SAME
  `BINANCE-SPOT/trades` cell launched successfully and unconditionally
  (`mtds-live-smoke-cefi-binance-spot-trades-20260728-040020`, `RUNNING`) — no guard refusal, no retry.
  `grep -n "tardis-concurrency-guard\|tardis_concurrency_guard\|TARDIS_VM_NAME_PATTERN\|VM_TARDIS_CONSUMER" deployment-service/scripts/vm/launch-mtds-live.sh`
  returns **zero matches** — the script never sources the guard.

BINANCE-SPOT is Tardis-sourced (`VENUE_TO_ADAPTER_KEY['BINANCE-SPOT'] == 'tardis'`), so this smoke VM used the SAME
shared single-IP Tardis key as the active backfill, concurrently, with zero coordination. This is exactly the condition
the guard's incident history (measured 2026-07-16: N>1 Tardis VMs → ~94% 403 storm + 37,212 false `attempted_failed`
manifest rows + coverage regression) exists to prevent — the live-leg path is simply not wired into that protection.

Checked the backfill VM's `run.log` for the ~2 min window the smoke VM was up: **0 HTTP 403 occurrences** in that window
(real fetching continued cleanly), so no observed damage this time — but that is luck (a 90s single-instrument smoke
fetch is a small fraction of the backfill's total request volume), not a structural guarantee. A longer-running or
repeated live-leg smoke check, or a real `--mode live` producer launch, against a Tardis venue while a real
backfill/sharded-VM run is active could reproduce the measured 403-storm / false-`attempted_failed` corruption.

A prior precedent (`/plans/archive/issues/cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md`) exercised
`launch-mtds-live.sh --test-run` successfully for `mtds-live-smoke-cefi-hyperliquid-trades-...` — HYPERLIQUID is
CAP-EXEMPT (native-REST, not Tardis), so that run never touched this gap. This is the first known exercise of the
live-leg smoke path against a Tardis-sourced venue while a Tardis-consuming VM was concurrently running.

## Why it matters

The whole point of the N=1 Tardis cap (codified `tardis-concurrency-guard.sh`,
`/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap) is that EVERY Tardis-consuming VM must be counted, no
matter which launcher creates it. A launcher that creates a real Tardis-fetching VM without sourcing the guard is a
silent hole in that protection — it can corrupt the manifest (false `attempted_failed` rows that later trigger
unnecessary reclass/re-investigation churn, per the already-open `deribit_options_chain_af_g4_blocker_2026_07_03.md`
pattern) and burn real backfill throughput, exactly during the highest-value window (an active coverage backfill).

## Recommended decision

> **✅ SAME-FILE COLLISION RESOLVED 2026-07-31 (corpus-wide ownership-conflict sweep, operator ruling: only one doc's
> todo claims the edit, the other cites it).** The doc this collided with —
> `/plans/active/issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md`
> (`assigned_vm: planning`) — has **already SHIPPED its half** (`deployment-service@2d6b01a`): the shared exemption
> logic now lives in `tardis-concurrency-guard.sh` itself as `TARDIS_CAP_EXEMPT_VENUES` +
> `tardis_venue_list_needs_guard()` (verified in live code today). So the two docs are no longer racing on the same
> logic — they own **disjoint** files:
>
> | File                                           | Owner                                                            |
> | ---------------------------------------------- | ---------------------------------------------------------------- |
> | `tardis-concurrency-guard.sh` (exempt logic)   | overapplies doc — **DONE**, `deployment-service@2d6b01a`         |
> | `launch-mtds-backfill-vm.sh`                   | overapplies doc — **DONE**                                       |
> | `launch-mtds-live.sh` + sibling live launchers | **THIS doc** (P1/P2 below) — no other active doc claims the edit |
> | skill `SKILL.md` § 3 (Tardis cap)              | overapplies doc — **DONE**                                       |
> | skill `SKILL.md` Phase 2 (live leg)            | **THIS doc** (P3 below) — a different section, no overlap        |

> **📤 THE TODOS BELOW ARE EXTRACTED AND DISPATCHED ELSEWHERE — do NOT dispatch from this doc (`/na-eligibility-audit`
> 2026-08-02, tranche=cefi).** `/plans/active/cefi_satellite_ao_dispatch_batch5_2026_08_02.md` (`status: active`,
> `assigned_vm: planning`, `parent_epic: cefi_master`, `unified-trading-pm@766822efe`) carries this doc's entire
> remaining scope verbatim and Source-cites it: **batch5 todo 1 `[INFRA] P1`** covers P1 + P2 together (and widens P2
> from the 2 siblings named below to all 8 `launch-*live*.sh` scripts), **batch5 todo 2 `[DOC] P3`** covers P3. This doc
> stays `assigned_vm: NA` deliberately — flipping it would create a SECOND dispatch path for the same launcher edit. Any
> checkbox still open below is genuinely unshipped; batch5's own done-when for each todo includes flipping it, so the
> batch5 worker owns closing it.
>
> One correction batch5 verified live on 2026-08-02 that this doc's older prose gets wrong — **trust batch5, not the
> text below**: the skill path is `unified-trading-pm/cursor-configs/skills/data-pipeline-check-mtds/`, not the
> `.claude/skills/...` path P3 names (that directory does not exist).
>
> **⚠️ Integration note (2026-08-02, na-eligibility-audit batch merge)**: the audit banner above was written while all
> three todos were still open. Concurrently, batch5 todo 1 shipped and **P1 + P2 below were closed NOT-A-BUG** under
> operator ruling BLK-5aa3ce78 (`unified-trading-pm@c9bcd08ac`, `@f385698d4`) — which also retires the banner's original
> "sibling-launcher scope is 8 scripts, not 2" correction by resolving that audit outright. The banner's do-not-dispatch
> scope therefore now applies to **P3 only**; P1/P2 need no dispatch from anywhere.

- [x] ✅ **NOT-A-BUG (2026-08-02).** [DATA] P1. ~~Source `tardis-concurrency-guard.sh` in
      `deployment-service/scripts/vm/launch-mtds-live.sh`~~ — **verified via code trace that the premise does not
      hold**: MTDS's live-mode capture (both `--live-source native` and `--live-source tardis-machine`) never opens the
      authenticated `datasets.tardis.dev` connection this guard protects. The `TARDIS_CONCURRENCY_LEASE` passthrough
      this doc originally cited as evidence of live contention is inert boilerplate for the live path (only consumed by
      the batch-side `tardis_concurrency_lease.py`, never called from the live WS handler). Full evidence:
      `/plans/active/issues/mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02.md`
      (unified-trading-pm@c34bfd176). Operator-ruled Option A (BLK-5aa3ce78, 2026-08-02): do not gate a 24/7 live
      producer behind a hard refusal cap that protects against contention that cannot occur — that would be a new outage
      class (refusing a legitimate live-producer relaunch during an unrelated concurrent cefi backfill), not a
      protection. (repo: deployment-service)
- [x] ✅ **NOT-A-BUG (2026-08-02).** [DATA] P2. ~~Audit sibling live launchers for the same gap~~ — audited all 8
      `launch-*live*.sh` scripts under `scripts/vm/`; only 2 (`launch-mtds-live.sh`,
      `launch-mtds-live-cefi-consolidated.sh`) even create cefi WS-capture VMs, and per P1's finding neither actually
      contends for the authenticated Tardis slot. The other 6 are structurally non-Tardis regardless (prediction/perp
      venues, or no market-data ingestion at all — see the finding doc's "What I found" for the per-launcher verdict).
      Same resolution as P1:
      `/plans/active/issues/mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02.md`.
- [ ] [DATA] P3. Update `data-pipeline-check-mtds` skill's **Phase-2 (live leg)** section to note the guard-gap risk and
      recommend deferring live-leg checks for Tardis-sourced venues while a real Tardis backfill/sharded VM is confirmed
      running, until P1 above ships. (repo: unified-trading-pm, `.claude/skills/data-pipeline-check-mtds/`)
      **na-eligibility-audit 2026-08-03**: already tracked (still open, `- [ ]`) as todo 2 `[DOC] P3` in
      `plans/active/cefi_satellite_ao_dispatch_batch5_2026_08_02.md:149` (Source-cites this exact item as "P3 of 3");
      not closing here — that batch's own done-when includes flipping this checkbox once it ships. **Scope-fenced
      2026-07-31**: **Phase-2 ONLY.** The same file's **§ 3 (Tardis cap)** section is owned by
      `/plans/active/issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md`'s `[DATA] P3`,
      which is already **done** — read what it wrote and cross-link it rather than restating or editing it.

No corruption confirmed this run (0 403s observed in the concurrent window) — this is a structural gap finding, not a
live-incident report. Not escalating to the operator as a page; tracked here per the findings-closure rule.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY candidate PARKED on conflict-check:
  `mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md` (active, planning) is concurrently
  editing the SAME `tardis-concurrency-guard.sh` venue-exemption logic this doc's P3 todo would tighten, and
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` already records the same launcher-gap finding. Filed as
  BLOCKED-OPERATOR-DECISION in this run's Deferred list; `assigned_vm` unchanged.
- **na-eligibility-audit 2026-08-02** (tranche=cefi, autonomous): **KEEP-NA-STALE (already-duplicated) — citation fixed,
  deliberately NOT reclassified.** This doc re-entered scope because the 2026-07-31 ownership-sweep banner resolved the
  exact same-file collision that caused the 07-30 park, which on its own merits made all three todos a clean RECLASSIFY
  (bounded, named files, named helper, gap re-verified live). The Phase-2 conflict-check then found the scope had
  ALREADY been extracted verbatim, that same resolution having fed
  `/plans/active/cefi_satellite_ao_dispatch_batch5_2026_08_02.md` (`unified-trading-pm@766822efe`, active/planning) —
  its todos 1 and 2 Source-cite this doc for P1+P2 and P3 respectively. Per the verdict rubric this is a
  checkbox-citation fix, not a reclassification: flipping `assigned_vm` here would let backlog-regen derive a second
  dispatch of the same launcher edit. Extraction banner added above the todos; `assigned_vm: NA` unchanged. (Superseded
  in part the same day — see the next entry: batch5 todo 1 then closed P1+P2 NOT-A-BUG, so the banner's live scope
  narrowed to P3.)
- **2026-08-02, slot 15** (`cefi_satellite_ao_dispatch_batch5_2026_08_02.md` todo 1): P1 + P2 closed NOT-A-BUG.
  Code-trace evidence showed MTDS live-mode capture never opens the authenticated `datasets.tardis.dev` connection —
  this doc's original contention claim (inferred from `VENUE_TO_ADAPTER_KEY == 'tardis'`) conflated the BATCH-mode
  adapter classification with the structurally-different LIVE path. Operator-ruled Option A (BLK-5aa3ce78): do not wire
  the guard into the live launchers. Full evidence + follow-up todo:
  `/plans/active/issues/mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02.md`. **P3 (the
  skill Phase-2 doc note) is untouched — out of scope for this todo, tracked separately as this batch's todo 2** (its
  premise may also need revisiting given this finding, but that is not this todo's call to make).
