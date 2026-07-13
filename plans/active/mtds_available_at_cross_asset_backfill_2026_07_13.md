---
doc_type: plan
title: Cross-asset-group available_at manifest backfill (market-data-tick — prediction, tradfi, defi)
summary: >
  Backfill the historical available_at="" backlog on CAPTURED market-data-tick manifest rows, now that
  unified-trading-library@9c9cdc50 fixed record_captured()/record_captured_from_counts() to actually persist the value.
  Phases smallest-blast-radius-first — prediction (46K rows) then tradfi (1.6M rows) — reusing each asset_group's
  existing rebuild script, which already derives available_at_envelope correctly and only needed the library fix to
  land. defi (3.0M rows) has NO existing capture-path available_at threading in its rebuild script, so it is
  audit-and-decide only in this plan, gated behind an explicit operator go/no-go given the sports CF-8 full-rebuild
  regression precedent. cefi is explicitly OUT OF SCOPE — its consolidator is stale/down, tracked separately.
status: active
nature: process
asset_group: [tradfi, defi, prediction]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [data-correctness, available-at, manifest-writer, backfill, cross-asset-group, manifest-master]
related:
  [
    plans/active/issues/manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md,
    plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    plans/audit/results/available_at_fill_rate_audit_2026_07_13.py,
    codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-13
last_updated: 2026-07-13
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source: >
  manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md todo P2 ("Scope + execute a
  cross-asset-group backfill plan... route through manifest_master epic as its own plan, NOT this issue doc")
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Cross-asset-group available_at manifest backfill (market-data-tick)

## Why this plan exists

`manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md`'s audit (2026-07-13, live production read
via `read_availability_index()`, no whole-corpus walk) found `available_at` **uniformly 0% filled** on
`capture_status=captured` rows across every measurable non-sports asset_group on the `market-data-tick` (MTDS/MDPS)
write path:

| asset_group | bucket                                             | captured rows | fill rate |
| ----------- | -------------------------------------------------- | ------------: | --------: |
| defi        | market-data-tick-defi-prd-central-element-323112   |     3,010,913 |      0.0% |
| tradfi      | market-data-tick-tradfi-prd-central-element-323112 |     1,620,826 |      0.0% |
| prediction  | market-data-tick-pred-prd-central-element-323112   |        45,542 |      0.0% |
| sports      | market-data-tick-sports-prd-central-element-323112 |       377,194 |      0.0% |

Sports is already covered by `sports_cf8_available_at_backfill_regression_2026_07_13.md`'s own P1 todo (gated on an
operator-coordinated maintenance window per that doc's Finding 1) — **not** duplicated here. cefi could not be measured
(consolidator stale/down, tracked as that issue doc's INFRA P3 todo) — **also not in scope here** until that is resolved
and a fresh audit confirms its state.

**Root cause is fixed** (`unified-trading-library@9c9cdc50`, unit-tested) for the go-forward write path. This plan is
ONLY about the historical backlog on already-captured rows.

## What we already know about the backfill mechanism, per asset_group (2026-07-13 code read)

- **prediction** (`rebuild_prediction_manifest.py`) and **tradfi** (`rebuild_tradfi_manifest.py`) already call
  `writer.record_captured_from_counts(..., available_at_envelope=<correctly-derived-per-row-key>, ...)` for CAPTURED
  clusters — this was already correct, it just silently no-opped on `available_at` until `9c9cdc50` landed. Because the
  manifest consolidator is last-write-wins, **simply re-running these two scripts in `--force` mode now backfills
  `available_at` on every existing captured row** — no new code needed, same mechanism the sports rebuild used.
- **defi** (`rebuild_defi_manifest.py`) and **cefi** (`rebuild_cefi_manifest.py`) call ONLY `record_empty`/
  `record_failed` (gap-filling) — **never** `record_captured`/`record_captured_from_counts` — confirmed by grep, no call
  sites in either file. There is no existing rebuild entrypoint that touches captured rows for defi. DeFi's live
  captures instead run through ~30 separate `market_tick_data_service/cli/handlers/*_handler.py` collectors, each
  presumably deriving `available_at` its own way at capture time — a retroactive defi backfill needs to reuse each
  data_type's OWN formula, not one blanket rule. This is real, not-yet-scoped engineering work, not a "rerun a script"
  job like prediction/tradfi.

## The sports precedent this plan must respect (HARD constraint)

`sports_cf8_available_at_backfill_regression_2026_07_13.md`: a `--force` full-corpus rebuild on the IS sports surface
**regressed** `available_at` fill rate from 62.9% to 15.7% — a genuine, silent, production-data-destroying bug (root
cause: the serializer dropped the column; fixed `f5f15e3a`), only caught because the operator's own before/after
fill-rate check was run. A second incident (Finding 1) had an operator's routine `gcloud scheduler jobs resume` collide
with a paused consolidator cron mid-backfill. Both are now mitigated (`f5f15e3a` fixed the serializer; `2e132bb2` added
`_check_column_fill_regression()`/`MANIFEST_COLUMN_FILL_REGRESSION` as a defense-in-depth guardrail) but **every todo
below that touches production data must**: dry-run first, snapshot + pause the consolidator cron before applying, and
verify the guardrail did not trip + row counts are unchanged before resuming the cron.

## Todos

- [ ] [DATA] P0. Confirm `unified-trading-library@9c9cdc50` (available_at persistence fix) AND `@2e132bb2`
      (`MANIFEST_COLUMN_FILL_REGRESSION` guardrail) are both pinned in `market-tick-data-service`'s dependency lock on
      `live-defi-rollout` — bump + redeploy first if either is missing. Do NOT proceed past this todo otherwise. (repo:
      market-tick-data-service, unified-trading-library)
- [ ] [OPERATOR] P0. BLOCKED-OPERATOR-DECISION — coordinate a maintenance window with the operator for the prediction +
      tradfi consolidator crons (per the sports Finding 1 cron-collision incident) before pausing either — get explicit
      per-bucket go-ahead. (repo: NA)
- [ ] [DATA] P1. Dry-run `rebuild_prediction_manifest.py --force` (no writes) against
      `market-data-tick-pred-prd-central-element-323112`; spot-check the previewed `available_at_envelope` values
      against a handful of known-good rows before applying anything live. (repo: market-tick-data-service)
- [ ] [DATA] P1. Snapshot the prediction canonical manifest index
      (`_index/snapshots/pre_available_at_backfill_<ts>.parquet`) and pause its consolidator cron. (repo:
      market-tick-data-service)
- [ ] [DATA] P1. Apply `rebuild_prediction_manifest.py --no-dry-run --force`, force-consolidate, then re-run
      `available_at_fill_rate_audit_2026_07_13.py` (or its successor) to confirm fill rate rose from 0% — verify the
      `MANIFEST_COLUMN_FILL_REGRESSION` guardrail did NOT trip and total row count is unchanged before declaring
      success. (repo: market-tick-data-service, unified-trading-library)
- [ ] [DATA] P1. Resume the prediction consolidator cron; record the before/after fill-rate evidence in this plan's
      Progress Log. (repo: market-tick-data-service)
- [ ] [DATA] P1. Dry-run `rebuild_tradfi_manifest.py --force` against
      `market-data-tick-tradfi-prd-central-element-323112`; sanity-check envelope values across a sample of tradfi
      data_types/venues (bundled + non-bundled shards). (repo: market-tick-data-service)
- [ ] [DATA] P1. Snapshot the tradfi canonical manifest index and pause its consolidator cron. (repo:
      market-tick-data-service)
- [ ] [DATA] P1. Apply `rebuild_tradfi_manifest.py --no-dry-run --force`, force-consolidate, then verify fill rate +
      guardrail + row count via the audit script, same protocol as prediction. (repo: market-tick-data-service,
      unified-trading-library)
- [ ] [DATA] P1. Resume the tradfi consolidator cron; record evidence in the Progress Log. (repo:
      market-tick-data-service)
- [ ] [DATA] P2. Audit each `market_tick_data_service/cli/handlers/*_handler.py` DeFi collector (~30 files) for how (or
      whether) it currently derives `available_at` at live-capture time — map the per-data_type derivation formula each
      already uses, since a retroactive backfill must reuse the SAME formula per data_type rather than one blanket rule
      (confirmed via grep, 2026-07-13: `rebuild_defi_manifest.py` itself has zero
      `record_captured`/`record_captured_from_counts` call sites — no shared rebuild entrypoint exists to extend).
      (repo: market-tick-data-service)
- [ ] [OPERATOR] P2. BLOCKED-OPERATOR-DECISION — present the defi audit (prior todo) plus a scoped design option (e.g. a
      new `--backfill-available-at-only` mode on `rebuild_defi_manifest.py` that calls `record_captured_from_counts` per
      data_type's derivation without touching `capture_status`, OR a narrower manifest-only patch tool) for a go/no-go —
      defi's 3.0M rows and heterogeneous per-handler derivation make this materially riskier than prediction/tradfi's
      centralized-rebuild-script case; do not write the defi backfill code before this is decided. (repo: NA)
- [ ] [DATA] P3. _(stretch, optional)_ Once the prior todo is decided GO, implement the chosen defi backfill mechanism
      with unit-test coverage and a `--force` dry-run preview before any live write — follow the same
      dry-run/snapshot/pause-cron/guardrail-verify/resume-cron protocol as prediction and tradfi above. (repo:
      market-tick-data-service, unified-trading-library)

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — manifest schema, capture_status states, `available_at`
  semantics.
- `codex/05-infrastructure/manifest-consolidator-ssot.md` — consolidator cron pause/resume + staleness threshold.

## Progress Log

**2026-07-13 (slot 7)**: plan authored per `manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md`
todo P2. No production writes made by this touch — scoping only (code read of all four asset_groups' rebuild scripts to
determine per-asset_group backfill mechanism + risk, informed directly by the sports CF-8 regression postmortem).
