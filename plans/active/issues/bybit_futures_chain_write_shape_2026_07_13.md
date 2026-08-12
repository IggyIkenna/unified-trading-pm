---
doc_type: issue
title:
  "BYBIT futures_chain historical writes have 3 inconsistent shapes (flat glued-symbol files, a bare bundled
  ticks.parquet, and the correct underlying= hive form) — the base+quote regex bug fixed 2026-07-09 was never backfilled"
summary: >-
  BYBIT's raw_tick_data instrument_type=futures_chain data is written in at least 3 different shapes depending on when
  it was captured: (1) correct underlying=/ hive-partitioned form (2023-06 era, coexisting with (2) that same day), (2)
  legacy flat SYMBOL.parquet siblings at the same directory level, and (3) from ~2026-01 through the 2026-07-09 code
  fix, ONLY flat glued-base+quote files (e.g. BTCUSDT.parquet instead of underlying=BTC/ticks.parquet) — traced to a
  documented `_extract_underlying_for_chain` regex bug (canonical-write-conventions.md lines 212-217) that captured
  "BTCUSDT" instead of "BTC". The code fix landed 2026-07-09 but historical BYBIT futures_chain data written before that
  date was never backfilled/re-shaped to the correct form.
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service]
scope: [engineer]
tags: [futures_chain, bybit, write-shape, hive-partition, data-correctness, backfill]
related: [/plans/archive/2026_07/aster_cefi_data_defi_bucket_migration_2026_07_13.md]
created: 2026-07-13
author: unknown
parent_epic: mtds_mdps_master
priority: P2
source:
  "Found as a byproduct of investigating why deployment-service's cefi__trades BigQuery external table
  (bigquery_feature_external_tables.tf) failed to create — a classification sub-agent confirmed DERIBIT's
  futures_chain/underlying= shape is correct + load-bearing (do not touch), but while comparing venues to confirm
  underlying= is genuinely necessary everywhere, found BYBIT specifically has 3 coexisting/sequential shapes over time,
  one of which is a known-fixed-but-not-backfilled regex bug. Deliberately not fixed in the same pass — this is a data
  backfill/re-shape task, not a BQ config fix, and outside that session's scope."
assigned_vm: NA
execution_scope: local-only
model_tier: sonnet-doable
drift_direction: advance-code
depends_on: []
archive_exempt: true # BRIDGE 2026-08-12: clearing the stale locked_by:live-defi-rollout placeholder (operator ruling, option B, see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md) immediately surfaces this doc as 0-open-todos archive-eligible. Per that ruling's explicit scope ("do NOT auto-archive in this same pass"), archival is deferred to a separate follow-on pass. Bridged via the sanctioned flip-then-mv two-commit pattern documented in scripts/plan-hygiene/check_archive_candidates.sh -- drop this line + git mv to plans/archive/[issues/] in that follow-on pass.
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    /plans/archive/2026_07/bybit_futures_chain_write_shape_migration_2026_07_13.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch4_2026_07_31.md,
    market-tick-data-service/scripts/audit_bybit_futures_chain_shape2_duplicates_2026_07_13.py,
  ]
---

# BYBIT futures_chain write-shape inconsistency (3 shapes across history)

> **🟡 TRACKED — plan filed 2026-07-13**: `bybit_futures_chain_write_shape_migration_2026_07_13.md` (agent-orchestrator
> plan, `assigned_vm: planning`) owns the actual fix. A same-day rescoping check (before filing the plan) found the
> affected window is WIDER than this doc's original estimate — glued-shape files confirmed present 2025-06-01 through
> 2026-05-01 (not just ~2026-01), and no BYBIT `futures_chain` data at all is found from 2026-06-01 onward (needs
> explanation — the new plan's Phase 1 owns this). Leave `status: open` here until the plan reports the fix complete.

## Finding (2026-07-13)

`gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/`, `venue=BYBIT`,
`instrument_type=futures_chain` has at least 3 shapes depending on capture date:

1. **Correct hive form**: `.../data_type=trades/underlying={U}/ticks.parquet` — matches the SSOT-documented shape
   (`market-tick-data-service/docs/GCS_PATHS.md` lines 61-71, 109-117; `docs/canonical-write-conventions.md` lines
   16-51), the same shape DERIBIT uses correctly across its entire 2019-2026 history.
2. **Legacy flat siblings**: e.g. `day=2023-06-01` has BOTH `underlying=BTC/`, `underlying=ETH/` hive dirs AND flat
   `BTC.parquet`/`ETH.parquet` files at the same directory level; `day=2025-01-01` additionally has a bare unqualified
   `ticks.parquet` whose size ≈ sum of the three per-underlying hive files that day (a bundled dump, not a duplicate).
3. **Glued base+quote flat files (the actively-broken window)**: by 2026-01 through ~2026-05, BYBIT
   `futures_chain`/`trades` is written ONLY as flat glued-symbol files (`BTCUSDT.parquet`, `ETHUSDT.parquet`, etc., no
   `underlying=` segment at all). Root cause is documented in `canonical-write-conventions.md` lines 212-217:
   `_extract_underlying_for_chain`'s regex captured the full `BTCUSDT` symbol instead of splitting out `BTC` as the
   underlying. **Fixed in code 2026-07-09**, but the historical window this bug affected (~2026-01 → 2026-07-09) was
   never backfilled/re-shaped.

This is UNRELATED to the DERIBIT `underlying=` finding from the same investigation (DERIBIT's shape is correct and 100%
consistent across its whole history — `underlying=` is load-bearing there, not a bug). BYBIT is the one venue with
genuine write-path inconsistency.

## Why this matters

Any BigQuery external table (or other tool) that assumes a uniform `underlying=` hive-partition depth for
`futures_chain` data will break the instant it scans a BYBIT day inside the 2026-01→2026-07-09 window (flat files with
no `underlying=` key), or the 2023-06/2025-01-era legacy-sibling days (duplicate flat+hive forms inflating counts). This
surfaced as a contributing factor while diagnosing why
`deployment-service/terraform/gcp/bigquery_feature_external_tables.tf`'s `cefi_trades` table failed to create — though
the PRIMARY blocker there was a separate `futures_chain`/`underlying=` (DERIBIT, legitimate) vs non-`futures_chain`
depth mismatch, not this BYBIT-specific issue; this BYBIT finding would be the NEXT blocker once the primary one is
resolved via a split-table design.

## Suggested remediation (not scoped/estimated — future plan should own this)

1. Confirm the exact date range affected (spot-checked 2026-01 and mid-2026; the full window needs a proper day-by-day
   audit, not sampling).
2. Backfill/re-shape the 2026-01→2026-07-09 window: parse the glued `BTCUSDT.parquet` filenames back into
   `{underlying}/{quote}` (same split logic the 2026-07-09 code fix now uses going forward), write to the correct
   `underlying=` hive path, verify parity, then decide whether to clean up the flat originals (mirrors the same
   data-safety discipline as any other legacy-shape migration in this workspace — do not delete before verifying).
3. Decide whether the 2023-06/2025-01-era legacy flat siblings are safe-to-delete duplicates (their hive-form twins
   already exist) or need their own investigation — this issue doc did not verify duplication status for that older
   window, only confirmed the coexistence.

## Not done here

Read-only investigation only — no GCS objects modified, no code changed. This needs its own scoped plan when picked up
(estimate class: likely `infra` given the backfill/reshape nature, similar to other legacy-shape migrations in this
workspace).

## Todos

- [x] ✅ [DATA] P2. **[already covered by
      `/plans/archive/2026_07/bybit_futures_chain_write_shape_migration_2026_07_13.md`, see that doc for execution]** —
      closed 2026-07-30 (`/na-eligibility-audit` tranche=cefi, stale-citation correction). Backfill/re-shape BYBIT
      `futures_chain` historical writes to the correct `underlying=` hive form. **The owning agent-orchestrator plan
      named in this doc's own 🟡 TRACKED banner has since reached `status: complete` (0 open / 11 done) and was ARCHIVED
      2026-07-15**, so the banner's own release condition ("leave `status: open` here until the plan reports the fix
      complete") is satisfied. That plan's phases record the full day-by-day audit, the reshape script, the dry-run
      parity check, the `--apply`, the post-apply verification (0 non-canonical shapes remaining), and the manifest-row
      rewrite. The "not started, no GCS objects modified yet" text above was written before that plan ran and was never
      updated.

> **📤 THE OPEN P1 BELOW IS EXTRACTED — do NOT dispatch it from this doc (`/na-eligibility-audit` 2026-08-02,
> tranche=cefi).** `/plans/archive/2026_07/cefi_satellite_ao_dispatch_batch4_2026_07_31.md` todo 1 `[SCRIPT] P1`
> (`assigned_vm: planning`, `unified-trading-pm@2d5fb4b59`) carries it verbatim and Source-cites this doc; its done-when
> is "the full-scope diff completes, results are recorded in the source doc, and its open P1 todo is flipped citing this
> run". **Caveat — batch4 is still `status: draft`, so it is NOT ingested and this work has no live dispatch path**
> until the operator activates it. That is an activation decision, not a reason to reclassify this doc (which would
> create a second, competing dispatch path for the same read-only diff); see this run's report for the parked item.

- [x] ✅ [DATA] P1. **MIGRATED 2026-07-30 — DONE 2026-08-06, `market-tick-data-service@1a32b6e7`.** Full-scope duplicate
      verification completed across all 546 scope days (2023-04-05 → 2025-09-23), processing 1,114 flat objects (408
      mixed / 97 bare_flat_only / 41 bundled_flat_only). **Results** — 490 duplicate (44%; flat rows ⊆ hive counterpart;
      safe to supersede once hive verified present), 290 not_duplicate (26%; flat has rows NOT in hive counterpart;
      unique data at risk), 334 no_counterpart (30%; no same-day hive counterpart exists anywhere; flat is the ONLY copy
      — deleting it would lose data permanently). The original 5-day sample's "all duplicates" conclusion was a sampling
      artifact: the full scope reveals 56% of shape-2 objects carry unique or orphan data. Audit parquet:
      `gs://.../_index/audit/bybit_futures_chain_shape2_duplicate_verify_2026_07_13.parquet` (1,114 rows). Script
      already shipped: `scripts/audit_bybit_futures_chain_shape2_duplicates_2026_07_13.py` (`1a32b6e7`). The
      "sample-based, not exhaustive" caveat is now closed. Read-only — no GCS objects modified. Actual cleanup of the
      490 pure-duplicate objects stays BLOCKED-OPERATOR-DECISION per the original scope.

- [x] ✅ [DATA] P3. **DONE 2026-08-09 — DELETE the 490 confirmed pure-duplicate BYBIT `futures_chain` shape-2 objects.**
      RULED 2026-08-09 (operator): delete over leave-as-is. Executed via
      `market-tick-data-service/scripts/delete_bybit_futures_chain_shape2_duplicates_2026_08_09.py --apply` per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`: fresh §3a soft-delete retention check (604800s,
      qualifies), fresh Part-1 re-verify of each object's counterpart twin immediately before delete,
      `gcs_conditional_delete` with generation-match (never `gcs_delete_object` directly, never a subprocess
      `gsutil`/`gcloud storage` call). Parts 3+4 (no live writer/reader) grep-then-READ-verified this session across
      market-tick-data-service/market-data-processing-service/execution-service/features-service/deployment-api/
      deployment-service/unified-api-contracts. **Result: 490/490 deleted, 0 precondition failures.** Post-delete
      re-verify: 0/490 still present; 10-row spot-check of `not_duplicate`/`no_counterpart` rows confirms none were
      touched.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA-STALE, citation corrected - the owning plan
  named in this doc's own TRACKED banner (`bybit_futures_chain_write_shape_migration_2026_07_13.md`) reached
  `status: complete` (0 open / 11 done) and was ARCHIVED 2026-07-15, so the banner's "leave open until the plan reports
  the fix complete" condition is met. Todo closed with that evidence; doc is now ARCHIVE-worthy but
  `locked_by: live-defi-rollout` blocks autonomous archival.
- **2026-07-30 (slot-11, `data_engineering`, `cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md` todo 4, archival
  ritual)**: `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` line 355 dispatched this exact extended
  duplicate-verification scope as an AO todo (`assigned_vm: planning`) and it was never shipped — the ONLY one of that
  plan's 33 todos left undone (flagged 2026-07-30 by the finalize plan's own todo-1 reconciliation pass). Per the
  archival discipline ("split it, or fold the remnant" for a near-complete plan with a genuine open item —
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`), the remnant is folded back into this, its own
  named Source doc, as a fresh open todo above (never marked done — the work itself still needs doing) rather than
  silently evaporating inside the archived batch1 plan. This doc stays correctly active (not archive-eligible) as long
  as this todo is open, superseding the prior entry's ARCHIVE-worthy note above. Kept `assigned_vm: NA` here (no
  operator ruling taken on re-promoting it to AO-dispatched) — a future `/na-eligibility-audit` or operator call can
  reclassify it.
- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **na-eligibility-audit 2026-08-02** (tranche=cefi, autonomous): **KEEP-NA-STALE (already-duplicated) — citation fixed,
  NOT reclassified.** Re-entered scope on the 2026-07-30 folded-back P1. That entry explicitly invited this skill to
  reconsider ("a future `/na-eligibility-audit` or operator call can reclassify it"), and on its own merits the todo
  does clear the bounded-outcome bar — read-only row-level diff, scope fixed by an existing audit parquet, an explicit
  **Done when**, no delete/`--apply`/VM launch, and it was already deemed AO-eligible once when batch1 dispatched it.
  The Phase-2 conflict-check nevertheless found it ALREADY re-extracted verbatim into
  `cefi_satellite_ao_dispatch_batch4_2026_07_31.md` todo 1 (`unified-trading-pm@2d5fb4b59`, Source-cited), so a flip
  here would be the near-verbatim duplicate claim conflict-check § 3 forbids. Citation banner added above the todo;
  `assigned_vm: NA` unchanged. `locked_by: live-defi-rollout` is not the deciding factor (PLAN_FORMAT § locked_by blocks
  ARCHIVAL, not an `assigned_vm` flip) and no unlock question arises — the doc has genuine open work either way.
  **Parked for the operator**: batch4 has sat `status: draft` since 2026-07-31, so this todo currently has no live
  dispatch path via either doc — see this run's report.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added the batch4 satellite-dispatch plan the
  extraction banner now points to.
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA-STALE (already-duplicated) — reaffirms the
  2026-08-02 verdict; banner and citations still accurate. **batch4 is STILL `status: draft` as of this run (stuck since
  2026-07-31, now 4 days)** — this doc plus at least 2 siblings this same run
  (`cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md`,
  `cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31.md`) have real, extracted,
  ready-to-execute work sitting with no live dispatch path pending batch4's activation — flagged again in this run's
  report per the 2026-08-02 pass's own note.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — the citation banner above the sole
  open item is already correct and current: the work is extracted verbatim into
  `cefi_satellite_ao_dispatch_batch4_2026_07_31.md` todo 1, which remains `status: draft` (unactivated 6+ days,
  confirmed via today's `/plans/archive/2026_08/ag_closeout_audit_cefi_parked_2026_08_06.md`). Nothing to fix; revisit
  only if batch4 stalls without ever activating.
- **DONE 2026-08-06 (slot 13, `data_engineering`, `cefi_satellite_ao_dispatch_batch4-001`)** — full-scope duplicate
  verification completed. `market-tick-data-service/scripts/audit_bybit_futures_chain_shape2_duplicates_2026_07_13.py`
  (`1a32b6e7`, already shipped) run across all 546 scope days (2023-04-05 → 2025-09-23), 1,114 flat objects. Results:
  490 duplicate (44%), 290 not_duplicate (26%), 334 no_counterpart (30%). The 5-day sample's "all duplicates" was
  misleading — 56% of shape-2 objects have unique/orphan data. Audit parquet written to
  `_index/audit/bybit_futures_chain_shape2_duplicate_verify_2026_07_13.parquet`. P1 checkbox flipped above; the
  "sample-based, not exhaustive" caveat is closed.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — added the audit script
  (`audit_bybit_futures_chain_shape2_duplicates_2026_07_13.py`) now that both tracked todos are `[x]` and the remaining
  substantive work is the operator-gated cleanup decision over the 490 confirmed-duplicate objects it classified.
- **na-eligibility-audit 2026-08-08** (tranche=cefi, autonomous): KEEP-NA, valid — genuinely operator-gated (delete vs.
  keep 490 confirmed-duplicate GCS objects), correctly NOT bounded/deterministic for an AO worker. In scope this run
  because both prior todos flipped `[x]` on 2026-08-06, leaving the doc showing 0 open checkboxes while the 2026-08-07
  context-scout note (and the P1 item's own text) already flagged a real prose-only remaining decision — the exact
  "prose-only remaining work" trap this skill watches for. Added an explicit `[OPERATOR] P3` todo above capturing that
  decision (with a Done-when and the delete-safety-protocol cite) instead of leaving it as prose, so the doc no longer
  misreads as fully resolved to a future archive-candidate sweep. `locked_by: live-defi-rollout` unchanged — no archival
  action taken or implied.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — sole item is an explicit [OPERATOR]
  P3 delete-vs-keep decision over 490 GCS-confirmed-duplicate objects (market-tick-data-service@1a32b6e7, DONE
  2026-08-06), correctly gated by the delete-safety protocol.
- **2026-08-09 (operator ruling, interactive session)**: operator ruled DELETE the 490 confirmed pure-duplicate objects.
  Todo retagged `[OPERATOR]`→`[DATA]` with the ruling recorded inline. Execution against the delete-safety protocol
  tracked in this same session.
- **2026-08-09 (execution, same interactive session)**: wrote + ran
  `market-tick-data-service/scripts/delete_bybit_futures_chain_shape2_duplicates_2026_08_09.py`. Dry-run first (490/490
  confirmed live and deletable), then a background Explore agent grep-then-READ-verified Parts 3+4 (no live
  writer/reader for the flat shape — `build_partition_path` in `tardis_shared.py:501-574` can no longer reach the
  fallback branch for BYBIT since the 2026-07-09 `_extract_underlying_for_chain` fix; no reader assumes the flat shape),
  then `--apply`: 490/490 deleted, 0 precondition failures. Post-delete re-verify: 0/490 still present, 10-row
  spot-check of the 290 `not_duplicate` + 334 `no_counterpart` rows confirms zero collateral deletes. This doc's sole
  open todo is now closed — no `locked_by` on this doc, so it's archive-candidate on the next hygiene sweep.
- **2026-08-12** — `locked_by`/`locked_since` cleared (corpus-wide fix, operator ruling Option B, interactive session
  2026-08-12; see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md). This doc has
  0 open todos, so clearing the placeholder lock immediately makes it archive-eligible. Per the ruling's explicit scope
  ("do NOT auto-archive in this same pass"), archival itself is deferred to a separate follow-on pass; bridged with
  `archive_exempt: true` (the sanctioned flip-then-mv two-commit pattern documented in
  `scripts/plan-hygiene/check_archive_candidates.sh`) so this commit doesn't trip the archive-candidates pre-commit
  gate. The follow-on pass should drop `archive_exempt` and `git mv` this doc to `plans/archive/[issues/]`.
