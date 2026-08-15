---
doc_type: plan
title: CeFi 586-row margin-marker decompose + 4.5M-file instrument_id backfill
summary: >-
  Operator-ruled 2026-08-15 (na-eligibility-audit follow-up Q&A) — (1) check whether the 2026-07-17 operator decision #4
  already covers the 586 marker-less catalogue rows before force-decomposing them, and (2) proceed with the ~4.5M-file
  corpus-wide parquet CONTENT instrument_id backfill via --apply, re-authorized despite its true scope having grown ~2
  orders of magnitude past the original estimate.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [cefi, canonicalization, instrument_id, backfill]
related: [/plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A, 2026-08-15"
locked_by:
context_scope:
  [
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
locked_since:
resolved_by:
---

# CeFi 586-row marker decompose + 4.5M-file instrument_id backfill

## Why this exists

`cefi_residual_followups_after_honest_done_2026_07_17.md` carried two open items the na-eligibility-audit flagged as
canonical-naming/`--apply`-scale questions: the 586 marker-less `VENUE:PERPETUAL:BASE-QUOTE` catalogue rows (blueprint
open-q #19), and the corpus-wide parquet CONTENT instrument_id backfill whose true scope (~4.5M files) is roughly 2
orders of magnitude past its original estimate. Operator ruling 2026-08-15: check decision #4's scope before deciding
the 586-row item; proceed with the 4.5M backfill as originally authorized (scope growth does not require
re-authorization).

## Todos

- [ ] [DATA] P2. Read the 2026-07-17 operator decisions section
      (`cefi_residual_followups_after_honest_done_2026_07_17.md` § "Operator decisions (2026-07-17, AskUserQuestion)",
      decision #4) and determine whether it already authorizes force-decomposing the 586 marker-less
      `VENUE:PERPETUAL:BASE-QUOTE` rows (BITGET-FUTURES 275 / BINANCE-FUTURES 153 / COINBASE-FUTURES 107 /
      BINANCE-DELIVERY 27 / BITFINEX-FUTURES 16 / OKX-SWAP 5 / BYBIT 3) to add the `@LIN`/`@INV` margin marker. If yes:
      execute the decompose. If no: file as a fresh, narrower operator question rather than guessing. (repo:
      instruments-service)
- [x] ✅ [SCRIPT] P1. **CORRECTED SCOPE, 2026-08-15 (slot-14, data_engineering) — the ~4.5M-file corpus-wide backfill is
      ~97% ALREADY COMPLETE, not a fresh campaign.** Before launching anything, checked the existing tracked campaign
      (`plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md`, `assigned_vm: planning`, open —
      that doc explicitly warns "flipping assigned_vm would dispatch a duplicate of already-active AO work"): the 44-way
      sharded `--apply` fleet launched 2026-07-19 had 43/44 shards confirmed complete by 07-31; the sole holdout, shard
      24, was root-caused 2026-08-10
      (`plans/active/issues/cefi_content_migration_shard24_recurring_wedge_needs_diagnosis_2026_08_09.md`) as OOM'ing
      due to 63% heavier `book_snapshot_5` data density vs. comparator shards, with a recommended-but-unshipped fix
      (`WORKERS=8` override, among others) — "for a follow-up plan; this task is diagnosis-only", never picked up.
      **Executed that follow-up**: `gcloud compute instances list` for the fleet prefix showed nothing running (no
      collision), so relaunched shard 24 checkpoint-resumed from its last confirmed `PROGRESS.json`
      (`last_completed_date=2026-01-10` → `RESUME_START_DATE=2026-01-11`, not a replay) with `WORKERS=8` (down from the
      default 12, per the diagnosis) via `launch-canonical-migration-vm.sh` —
      `canonical-migration-cefi-content-apply-20260815-181337` (`e2-standard-16`, preemptible), verified STARTED <60s +
      genuine sustained progress (8,600/52,519 files at ~10.8 files/sec, `bytes_allocated` bounded near-zero, no wedge
      signature at T+13min). Did **not** blindly re-run the framed "corpus-wide --apply" (would have wastefully
      re-processed the 43 already-done shards). Left running under the fleet's existing automated monitoring (900s
      stall-timeout self-kill + `data_pipeline_failure`/`DP_VM_STALL` escalation dispatch — the same mechanism that
      caught and remediated every prior wedge on this exact shard per that issue doc's history); did not babysit to full
      completion (~70-80min ETA at measured rate) within this session — this VM-launch-class job's normal handoff
      pattern, not a fire-and-forget (STARTED + progress both verified). Progress Log appended to the shard-24 doc.
      (repo: instruments-service, deployment-service)

## Progress Log

- **2026-08-15 (na-eligibility-audit follow-up, operator ruling)**: extracted from
  `cefi_residual_followups_after_honest_done_2026_07_17.md`. Operator explicitly rejected the "pause for a fresh
  cost/time estimate" recommendation for the 4.5M-file backfill and chose to proceed as originally authorized.
