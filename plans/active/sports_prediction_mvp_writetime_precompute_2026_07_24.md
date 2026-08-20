---
doc_type: plan
title: Sports/prediction MVP write-time precompute — manifest schema v9→10 stamp + historical backfill
summary: >-
  Forked out of mtds_data_status_page_parity_2026_07_21.md's sole remaining open todo (plan line-cap remediation,
  2026-07-24): implement the already-traced, already-designed write-time `mvp: bool` stamp for sports/prediction rows on
  UTL's shared `AvailabilityRecord` manifest schema (v9→10 bump), wire deployment-api's catalogue read to prefer the
  precomputed column, and scope the companion historical backfill/rebuild pass. This is a caching/perf optimization (the
  read-time `is_mvp` verdict is already correct today), not a correctness fix — see "Context" below for the key finding
  that established this.
status: active
nature: process
asset_group: [sports, prediction] # corrected 2026-08-19 (ag-closeout-audit cross-cutting reconciliation pass) -- was
  # [cross-cutting]; content is 100% sports/prediction manifest-schema precompute, filename-prefixed
  # sports_prediction_ -- classic fork-inherited-tag pattern; parent_epic (deployment_and_user_management_master) is
  # not one of cross-cutting's 5 data epics either.
stage: [meta]
repos:
  [
    deployment-api,
    deployment-ui,
    market-tick-data-service,
    market-data-processing-service,
    instruments-service,
    unified-api-contracts,
  ]
scope: [engineer]
tags: [deployment-api, mtds, mdps, sports, prediction, mvp, manifest-schema, precompute, backfill]
related:
  [
    /plans/archive/2026_07/mtds_data_status_page_parity_2026_07_21.md,
    /plans/archive/2026_08/mvp_scope_catalogue_tagging_2026_06_08.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-08-20"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  Extracted from mtds_data_status_page_parity_2026_07_21.md's sole open todo per
  plan_line_cap_remediation_2026_07_23.md's bucket-(c) triage ("Extract sole open todo →
  sports_prediction_mvp_writetime_precompute_2026_07_23.md; archive parent" — filename date mechanically rolled to
  2026_07_24, the day this split was actually executed; slug/scope unchanged). The parent plan is now fully closed and
  archived to plans/archive/2026_07/mtds_data_status_page_parity_2026_07_21.md.
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    unified-trading-library/unified_trading_library/manifest_writer/_rows.py,
    unified-trading-library/unified_trading_library/manifest_writer/_writer_captured.py,
    deployment-api/deployment_api/routes/data_status/_catalogue.py,
  ]
---

# Sports/prediction MVP write-time precompute

> **Provenance note**: this plan's single todo below is copied VERBATIM from
> `mtds_data_status_page_parity_2026_07_21.md` (now archived at
> `/plans/archive/2026_07/mtds_data_status_page_parity_2026_07_21.md`) — no content was rewritten during the fork. The
> todo's own text references "the '2026-07-21 (tick 2)' progress-log entry above" and "the deferred-work table below" —
> those sections live in the ARCHIVED parent plan, not in this file; follow the link above for that full context (the
> CeFi manifest-restamp precedent this todo's risk-comparison cites).

## Context (why this is a separate plan, not left inline)

The parent plan (`mtds_data_status_page_parity_2026_07_21.md`) shipped every other MTDS/MDPS data-status-parity item
(Bugs A/B/C, MVP-scope wiring, MDPS timeframe-awareness, the universal search bar, UI parity confirmation — see that
archived plan's Progress Log for the full shipped history) and closed with exactly one deliberately-deferred item: a
write-time `mvp: bool` precompute for sports/prediction manifest rows. That item was TRACED + DESIGNED but not
implemented (an explicit scope-risk STOP, not an oversight) because it requires a schema bump (`MANIFEST_SCHEMA_VERSION`
9→10) on UTL's shared `AvailabilityRecord` — the ONE manifest-row dataclass written by every asset_group and every
producer service — which needs a full-fleet redeploy + verified manifest-consolidator schema-evolution behavior to land
safely, not a bounded single-service change. This plan exists to carry that already-designed work forward as its own
small, independently-dispatchable unit, per the plan line-cap remediation's bucket-(c) clean-partition split
(`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).

## Todos

- [ ] [DATA] P2. **Precompute `mvp: bool` for sports/prediction — TRACED + DESIGNED this tick, deliberately NOT
      implemented (scope-risk STOP, not a skipped task).** Picks up exactly where the prior tick left off (that tick had
      already ruled out the naive "mirror `_add_mvp_column`/redirect to `prod/catalog.parquet`" fix — see
      `_catalogue.py:75-87` + `test_sports_not_in_identity_catalogue_asset_groups`, unchanged, still correct).

      **Trace (done this tick)**: sports/prediction have NO separate manifest-writer pipeline — they flow through the
      exact same universal orchestrator as every other asset_group.
      `market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py`'s
      `_finalize_prediction_bundles`/`_finalize_sports_...` closures (+ the shared `_write_bundle_shard_row` helper)
      call `unified-trading-library/unified_trading_library/manifest_writer/_writer_captured.py`'s
      `ManifestWriter.record_captured`/`record_captured_from_counts` (captured rows) and `_writer_record.py`'s
      `_record_status` (empty/failed/expected_unattempted rows), which both build ONE shared dataclass —
      `_rows.py::AvailabilityRecord` — the UNIVERSAL manifest-row schema written into `_index/availability_index.parquet`
      by EVERY asset_group and EVERY producer service (cefi/defi/tradfi/sports/prediction, plus features-service /
      ml-service / strategy-service / execution-service, which is why `AvailabilityRecord` already carries
      `feature_group`/`model_family`/`strategy_id`/`client_id`/`instruction_type` columns). There is no
      sports/prediction-scoped writer to touch in isolation — any new column lands on this ONE shared schema.

      **Key finding (changes the framing of "correct fix")**: `is_mvp_for_manifest_row`'s two extra axes beyond
      `(venue, instrument_type, data_type)` — `base_ccy` (read from a `base_asset` column) and `market_group` — are
      confirmed ABSENT not just from the read-time manifest DataFrame (already documented at `_coverage_scope.py:96-104`)
      but from the WRITE-time schema too: neither `base_asset` nor `market_group` appears in UTL's `_ROW_KEY_COLUMNS`
      or `AvailabilityRecord` fields (`_rows.py`). So a write-time `is_mvp(...)` call would resolve those two kwargs to
      `None` — IDENTICAL to what the read-time call resolves today. **Write-time precompute is a pure caching/perf
      optimization, not a correctness fix** — it would not change a single row's `is_mvp` verdict vs. today.

      **Design (for whoever implements)**:
      1. UTL `manifest_writer/_rows.py`: add `mvp: bool | None = None` (trailing field, back-compat default) to
      `AvailabilityRecord`; bump `MANIFEST_SCHEMA_VERSION` 9→10 in `_schema.py`.
      2. UTL `_writer_captured.py::record_captured`/`record_captured_from_counts`: when the resolved `asset_group` is
      `"sports"`/`"prediction"`, lazy-import UAC `is_mvp` and stamp
      `is_mvp(asset_group, venue, instrument_type, data_type, league=league_id or None, market_group=None,
      base_ccy=None, source=resolved_source)` onto the `AvailabilityRecord(...)` call; leave `None` for every other
      asset_group (no behavior change elsewhere).
      3. UTL `_writer_record.py::_record_status`: same conditional stamp (sports/prediction also write
      empty/failed/expected_unattempted rows through this path).
      4. `deployment-api/_catalogue.py::_row_is_mvp`/`_is_mvp_series`: add a THIRD branch — when `"mvp" in df.columns`
      for a manifest-backed (non-identity-catalogue) frame, use the precomputed value for rows where it's non-null
      (`_truthy_mvp` fast path, mirroring the identity-catalogue branch byte-for-byte) and fall back to
      `is_mvp_for_manifest_row` only for legacy rows where the column is null/absent — old rows keep today's exact
      behavior.
      5. Historical rows do NOT retroactively gain `mvp` from steps 1-4 alone — closing the live-compute gap for
      EXISTING data needs a companion backfill/rebuild pass (the repo already has the pattern:
      `rebuild_sports_manifest_v9.py` / `rebuild_prediction_manifest.py`), scoped separately.

      **Why this STOPS here instead of shipping (explicit scope-risk call, not an oversight)**: step 1 is not a
      sports/prediction-scoped change — it is a schema addition on the ONE shared `AvailabilityRecord` used by every
      asset_group and every producer service, so it needs a FULL FLEET redeploy (every live/backfill/cron VM, both
      clouds, all asset_groups) to take effect, not a bounded single-service change. The manifest-consolidator
      (Cloud Run/Batch-Fargate) merging old-schema and new-schema per-VM shards together is unverified here and codex
      documents it as "loud-fails on stale index" — exactly the risk class behind this SAME session's separate CeFi
      manifest re-stamp (see the "2026-07-21 (tick 2)" progress-log entry above and the deferred-work table below),
      which needed a snapshot + guarded rollout + an operator-gated Cloud Scheduler pause and is still not fully landed.
      Given the P2 (not P1) priority, the already-documented "bounded, non-regressed" live-compute cost (no active
      incident forcing urgency), and the Key Finding above (this is a perf win, not a correctness fix), rushing steps
      1-4 here would repeat the exact near-miss pattern this plan has already flagged twice. Left at P2 with the design
      above ready to hand off; NOT force-shipped.

## Codex SSOTs

- `/codex/02-data/honest-coverage-model.md`, `/codex/02-data/availability-manifest-and-data-status.md` — the
  manifest/coverage model this precompute extends (schema v9→10 bump lands here once shipped).
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — the "loud-fails on stale index" schema-evolution risk this
  todo's scope-risk STOP is about; re-verify against this doc before bumping `MANIFEST_SCHEMA_VERSION`.

## Composes with

`mvp_scope_catalogue_tagging_2026_06_08.md` (the MVP predicate/toggle this precompute caches, not replaces) ·
`mtds_data_status_page_parity_2026_07_21.md` (archived parent — full shipped history of every other MTDS/MDPS parity
item this plan was forked from).

## Progress Log

### 2026-07-24 — plan created (fork from mtds_data_status_page_parity_2026_07_21.md)

Created via the plan line-cap remediation job (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 20 /
bucket-(c) entry): the parent plan's sole open todo is moved here VERBATIM (no rewrite), and the parent — now with zero
open todos — is archived to `plans/archive/2026_07/mtds_data_status_page_parity_2026_07_21.md` with `status: resolved`.
No code was written in this fork; the todo's own TRACED + DESIGNED content (unchanged) is the full state of the work as
of 2026-07-22, the last tick that touched it.

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; only change since = context-scout `context_scope`
  frontmatter, body byte-identical): KEEP-NA, valid — the sole todo is an explicit scope-risk STOP — a
  MANIFEST_SCHEMA_VERSION 9→10 bump on UTL's shared AvailabilityRecord needing a full-fleet redeploy plus unverified
  consolidator schema-evolution behaviour.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — swapped 2 codex-only entries for the 3 source
  files the schema-bump design actually targets (`_rows.py`'s `AvailabilityRecord`, `_writer_captured.py`, and
  deployment-api's `_catalogue.py` read side).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-confirms 2026-08-02; the sole todo remains an explicit
  scope-risk STOP (a MANIFEST_SCHEMA_VERSION 9→10 bump on UTL's shared `AvailabilityRecord` needing a full-fleet
  redeploy plus unverified manifest-consolidator schema-evolution behaviour), not bounded single-service work.
- **na-eligibility-audit 2026-08-17** [body-hash:7de3005e9d576ce8]: KEEP-NA, valid -- Sole open todo is an explicit, well-reasoned 'scope-risk STOP, not an oversight': the write-time mvp:bool precompute requires a schema bump (MANIFEST_SCHEMA_VERSION 9→10) on UTL's ONE shared AvailabilityRecord dataclass written by every asset_group and every producer service (cefi/defi/tradfi/sports/prediction plus features/ml/strategy/execution services) — a full-fleet redeploy plus unverified manifest-consolidator schema-evolution behavior, explicitly not a bounded single-service change. This is exactly the rubric's warning example of a clean-sounding item that is not actually bounded because it touches live-dispatch-critical-path machinery fleet-wide. Two prior na-eligibility-audit passes (2026-08-02, 08-07) confirmed KEEP-NA with matching reasoning.
- **context-scout 2026-08-17**: re-verified; context_scope unchanged (4 entries, all resolve).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
