---
doc_type: plan
title: Finalize — MTDS lending instrument_type historical manifest re-stamp
summary:
  Gated close-out twin for market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24, reclassified
  NA -> planning by /na-eligibility-audit defi on 2026-07-30. Verifies the re-stamp landed honestly (row-count parity,
  no duplicate row_keys, only the confirmed-lending rows flipped), confirms the paused consolidator cron was resumed,
  and checks archival eligibility.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit, manifest, restamp, canonicalisation]
related:
  [
    /plans/active/market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes: []
superseded_by:
depends_on: [market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24]
gate_on_depends: true
source:
  [
    "/na-eligibility-audit defi, 2026-07-30 — paired finalize twin authored per
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md § 1(b) (retroactive reclassification:
    assigned_vm flipped in place, name unchanged, bolt-on finalize sibling dated the day of the pass).",
  ]
---

# Finalize — MTDS lending instrument_type historical re-stamp

> **Gated twin.** `depends_on` + `gate_on_depends: true` hold every todo here until every todo in
> `/plans/active/market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md` is done. Do not
> start these before that.

## Codex SSOTs

- `/codex/02-data/availability-manifest-and-data-status.md` — manifest row-key / CAS-write model
- `/codex/02-data/defi-canonical-naming-ssot.md` — lending `instrument_type` canonical spelling

## Todos

- [x] [DATA] P1. ✅ **Verify the re-stamp landed honestly against the LIVE prod manifest** (not against the script's own
      self-report). Re-read `market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` with a
      column-projected / predicate-pushdown read (never a full materialisation — see
      `/plans/active/issues/reconcile_phantom_manifest_rows_all_defi_memory_footprint_2026_07_28.md`) and confirm all
      three properties the source plan's own script asserts: rows-in == rows-out, 0 duplicate `row_key`s, and ONLY the
      confirmed-lending rows flipped `liquidation` -> `lending`. **Done when**: the three measured numbers are cited
      here with the read's own date. — **2026-07-30 (slot-12)**: independent standalone read (not a re-run of
      `restamp_lending_instrument_type_2026_07_24.py`'s `dry_run()`/`classify()` — own script, own column-projection,
      own dedup-key re-derivation) at live generation `1785416725122865`. Total manifest rows via **parquet footer
      metadata only** (zero data read): **29,135,266** (up from the source plan's same-day 29,121,036 baseline — normal
      append-only growth from ongoing live capture, not truncation/corruption — confirms **rows-in == rows-out**: the
      apply attempt performed no write, per the source plan's own `try_once()` trace, and the corpus continued growing
      normally through and after that no-op). `data_type="liquidations"` candidate subset (row-group
      predicate-pushdown + 18-column projection, never the full 29M-row frame): **7,164 rows** — 7,070
      `instrument_type="lending"` + 94 `None` (`record_zero_rows` path), **0** rows still carrying the buggy literal
      `instrument_type="liquidation"`. **Duplicate `row_key`s** (production dedup key —
      `date/venue/data_type/service_name/timeframe/league_id/chain/instrument_type/underlying/feature_group/     model_family/training_period/strategy_id/client_id/instruction_type/instrument_id`,
      independently re-derived, not imported from the restamp script) within the candidate subset: **0**. All three
      properties hold — the re-stamp (a genuine no-op on a 0-affected corpus) landed honestly.
- [x] [INFRA] P1. ✅ **DONE 2026-07-30 (slot-3)** — Confirmed the MTDS manifest-consolidator cron for the DEFI tick
      bucket is `state=ENABLED`, live. Identified the exact job name from
      `deployment-service/terraform/gcp/     manifest_consolidator_scheduler.tf`
      (`${env_prefix}-manifest-consolidator-${each.key}-cron`, `each.key =     "market-data-defi"` for the
      `market-data-tick-defi-prd-central-element-323112` bucket this restamp touched), then queried it live (not the
      terraform state, not the source plan's self-report):
      `gcloud scheduler jobs describe uts-prod-manifest-consolidator-market-data-defi-cron --location=asia-northeast1 --project=central-element-323112`
      → `state: ENABLED`, `schedule: '*/1 * * * *'`, `lastAttemptTime: '2026-07-30T13:24:01.793611Z'` (≈1 minute before
      this check, i.e. actively firing on schedule right now, not stalled). This is consistent with — and independently
      confirms — the source plan's own 2026-07-30 Progress Log finding that the cron was never paused for this restamp
      in the first place: the `--apply` run measured `safe_idx` empty (0 rows to re-stamp), and `try_once()` returns
      `"nothing_to_do"` before any CAS write on an empty `safe_idx`, so there was no write-vs-consolidator-cron race to
      protect and no pause was taken. Nothing to resume; the live infra state matches the narrative exactly.
- [ ] [DATA] P2. **Confirm the distinct-values panel no longer badges `liquidation` for this writer path** and
      cross-link the result into `/plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md`'s Progress
      Log, per the source plan's own closing todo.
- [ ] [PM] P2. **Check archival eligibility for the source plan.** If every todo is done and `locked_by:` is empty, run
      the standard 6-step archival ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) and
      archive this finalize doc alongside it. If `locked_by:` is set, STOP and escalate for `[unlock-plan]` — never
      autonomous.

## Progress Log

- **2026-07-30 (slot-3)** — Picked up todo 2 (AO task
  `market_tick_data_service_lending_instrument_type_historical_restamp_finalize-002`). Resolved the exact GCP Scheduler
  job name from terraform (not guessed) and queried it live: `state: ENABLED`, `lastAttemptTime` ≈1 min old, firing on
  its `*/1 * * * *` schedule. Confirms the source plan's own account (no pause was ever taken, since the apply was a
  provable no-op with nothing to protect against). Flipped todo 2. Todos 3-4 (distinct-values cross-link, archival
  eligibility) remain open for the next dispatch.
- **2026-07-30 (slot-12)** — Picked up todo 1 (AO task
  `market_tick_data_service_lending_instrument_type_historical_restamp_finalize-001`). Wrote a standalone,
  independently-derived verification read (column-projected + predicate-pushdown, footer-metadata row count, own
  dedup-key re-derivation — deliberately not a call into the restamp script's own `dry_run()`/`classify()`) against the
  live prod manifest. All three asserted properties confirmed at generation `1785416725122865`: rows-in==rows-out
  (29,135,266 total, normal growth from the 29,121,036 same-day baseline), 0 duplicate row_keys in the
  `data_type=liquidations` candidate subset, 0 rows still carrying the buggy `instrument_type="liquidation"` literal
  (7,070 correctly `lending` + 94 `None`). Flipped todo 1. Todos 2-4 (cron state, distinct-values panel, archival
  eligibility) remain open for the next dispatch.
- **2026-07-30 (slot-2)** — Gate opened: all 5 todos in the source plan
  (`/plans/active/market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md`) are now done
  (`locked_by:` empty). Flipped `status: draft` -> `active` per `gate_on_depends: true`. Not yet worked — the todos
  below still need their own independent re-verification against live prod (not the source plan's self-report), per this
  doc's own design.
- **2026-07-30** — Authored by `/na-eligibility-audit defi` as the paired finalize twin for a `NA -> planning`
  reclassification. The source plan cleared the shared conflict-check (§ 3 of the naming/conflict-check SSOT) against
  all 231 currently-active `assigned_vm: planning` docs: the two mentions found (`defi_satellite_ao_dispatch_batch1`,
  `batch2`) are provenance/closed-todo references, not open competing claims.
