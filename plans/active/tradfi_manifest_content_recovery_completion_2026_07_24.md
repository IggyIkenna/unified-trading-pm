---
doc_type: plan
title:
  TradFi manifest/content data-correctness completion — Surfaces A-D id-canonicalisation + candle-quarantine recovery
summary: >-
  Forked from tradfi_consolidated_closeout_2026_07_18.md's 2026-07-24 line-cap remediation split. Carries Phase A1's
  writer re-drift-prevention residual + Phase B (migrate the catalogue/manifest/GCS-filename/tick-content surfaces to
  `-USD@LIN`) + Phase B.5 (candle namespace quarantine recovery) + the pass-through canonicalisation worklist, plus the
  live 2026-07-21/22 continuation Progress Log (writer-fix, fleet drain, VM-launched migrations,
  honest-coverage/KRX/chain-manifest-recovery narrative). The older, fully-superseded ticks 1-12/20-21/23-27 +
  2026-07-21 pre-compact checkpoint/lessons + P0 writer-regression finding were extracted 2026-07-24 (second-tier
  line-cap remediation, task_template.md §3 finding J) to
  `/plans/archive/2026_07/tradfi_manifest_content_recovery_completion_history_2026_07_24.md` — this doc is now under the
  1000L cap on its own merits, so `umbrella: true` no longer applies (2026-07-24 ruling: the flag never grants a cap
  exemption).
status: active
nature: process
asset_group: [tradfi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    features-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [tradfi, canonicalisation, instrument-id, manifest, catalogue, migration, candle-quarantine, plan-hygiene, umbrella]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md,
    /plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/archive/2026_07/tradfi_manifest_content_recovery_completion_history_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
assigned_role: data_engineering
effort: max
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Forked 2026-07-24 from tradfi_consolidated_closeout_2026_07_18.md per the operator-approved 3-way split in
  plans/active/issues/plan_line_cap_remediation_2026_07_23.md row 29 (the tradfi_manifest_content_recovery_completion
  child). The plan had grown to 2549 lines (over the 2000L umbrella ceiling), driven overwhelmingly by an ~1700-line
  tick-by-tick Progress Log sitting next to a small tail of genuinely open todos. This child carries the manifest/
  catalogue/content id-canonicalisation completion workstream (Phase A1 residual + Phase B + B.5) verbatim. It briefly
  ran `umbrella: true` at 1627/1633 lines (over the 1000L non-umbrella cap). **Second-tier extraction 2026-07-24**
  (task_template.md §3 finding J): the fully-superseded ticks 1-12/20-21/23-27 + the 2026-07-21 pre-compact
  checkpoint/lessons + the P0 writer-regression finding (726 lines) moved verbatim to
  `plans/archive/2026_07/tradfi_manifest_content_recovery_completion_history_2026_07_24.md`, leaving this doc under 1000
  lines on its own, so `umbrella: true` was removed (2026-07-24 ruling: the flag never grants a cap exemption anyway).
context_scope:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    market-tick-data-service/scripts/migrate_tradfi_manifest_usd_lin_2026_07_18.py,
    market-tick-data-service/market_tick_data_service/scripts/recover_tradfi_chain_manifest_registration_2026_07_22.py,
  ]
---

# TradFi manifest/content data-correctness completion

> **Forked 2026-07-24** from `tradfi_consolidated_closeout_2026_07_18.md` (line-cap remediation, 3-way split — see
> `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` row 29). This plan carries the Surfaces A-D
> id-canonicalisation completion workstream: Phase A1's re-drift-prevention residual, Phase B (catalogue + manifest +
> GCS-filename + tick-content migration to `-USD@LIN`), and Phase B.5 (candle namespace quarantine recovery). All todos
> and Progress Log content below were moved **verbatim** from the parent — nothing summarized or rewritten. Sibling
> forks: `tradfi_backfill_throughput_followups_2026_07_24.md` (download/VM throughput residuals),
> `tradfi_phase_d_terminal_gate_2026_07_24.md` (the post-migration all-shards re-smoke-test terminal gate). Parent
> coordination index: `tradfi_consolidated_closeout_2026_07_18.md`. **2026-07-24 second-tier extraction**: the older,
> fully-superseded Progress Log ticks (1-12, 20-21, 23-27, the 2026-07-21 pre-compact checkpoint/lessons, the P0
> writer-regression finding) were moved verbatim to
> `/plans/archive/2026_07/tradfi_manifest_content_recovery_completion_history_2026_07_24.md` for line-cap compliance —
> see the pointer in place of them below. This doc's live, current-state narrative starts at the "2026-07-21/22
> continuation" section.

## Open + closed todos

### A1 — Converge every id WRITER to the canonical `PRODUCT_ROOT-USD@LIN-YYYYMMDD[-STRIKE-C|P]` shape

> **DECIDED 2026-07-18 (operator)**: TradFi FUTURE/OPTION canonical ids carry an **explicit `-USD` quote** —
> `CME:FUTURE:SP500-USD@LIN-20300621`, `CME:OPTION:SP500-USD@LIN-20251017-5000-C`, `CBOE:FUTURE:VIX-USD@LIN-20260722`
> (equities already `NASDAQ:EQUITY:AAPL-USD`). Chosen over the bare-product-root form so "same pattern regardless of
> asset class" is literally true and consistent with the 2026-07-18 DERIBIT quote ruling. Every A1 writer + every
> Phase-B migration emits this shape; the Phase-B/D verify gate asserts the `-USD@LIN` shape (not just presence of
> `@LIN`).

- [x] ✅ [BACKEND] P0. **IS catalogue adapter converged to `-USD@LIN` — instruments-service@287d1607.** For resolvable
      FUTURE/OPTION, `instrument_key` is now built via the shared
      `build_instrument_id(canonical_venue, itype, product_root, expiry_date=…, strike=…, option_right=…, margin_marker="LIN", quote_asset="USD")`
      — byte-identical to the MTDS write path (same `EXCHANGE_CODE_TO_NAME` root translation). `canonical_instrument_id`
      set BYTE-EQUAL to `instrument_key`; the old colon/month-only additive `_build_canonical_instrument_id` DELETED.
      Unresolved product-root (OSI `O:SPX…`, unknown roots) falls back to the sanitized-raw shape — no crash, no
      fabricated identity (historical/unresolvable = Phase B). Tests assert `CME:FUTURE:SP500-USD@LIN-20300621` /
      `CME:OPTION:SP500-USD@LIN-20251017-5000-C` / `CBOE:FUTURE:VIX-USD@LIN-20260722`; removed one invalid test (schema
      forbids FUTURE-with-null-expiry). IS QG green. (repo: instruments-service)
- [x] ✅ [BACKEND] P0. **Manifest writer now stamps the canonical `-USD@LIN` id (forward-write) — mtds@c44d5f0d.**
      Traced: the manifest `availability_index` `instrument_id` is DERIVED from the parquet **content** `instrument_id`
      column by the shared writer (`unified_trading_library/io/streaming_writer.py`→`manifest_writer`), so once the
      content column is canonical the forward-write manifest key is canonical + byte-identical (shard atom identical
      across writer/manifest). Historical manifest rows (`EW1H0_P2785` etc.) are the Phase-B migration, not a writer
      bug. Regression test that content→manifest keying holds is tracked as the A1 test todo below. (repos:
      market-tick-data-service, unified-trading-library)
- [x] ✅ [BACKEND] P0. **Tick parquet CONTENT `instrument_id` converged to `-USD@LIN` — mtds@c44d5f0d.** The databento
      forward-write (`databento_enrichment.py::_classify_row`) and batch derive
      (`tradfi_shared.py::derive_tradfi_row_instrument_id`) both now pass `margin_marker="LIN", quote_asset="USD"`. It
      is the enriched `instrument_id` column (NOT the raw `symbol`) that flows into the manifest key. Runtime PROOF (own
      venv, "run it not read it"): `derive_tradfi_row_instrument_id` FUTURE `ESM26`→`CME:FUTURE:SP500-USD@LIN-20260619`,
      OPTION `E3AN6 C7960`→`CME:OPTION:SP500-USD@LIN-20260117-7960-C` (0 whitespace — fixes the operator-seen
      banned-space class; product root ES→SP500 resolved). (repo: market-tick-data-service)
- [x] ✅ [BACKEND] P0. **TradFi quote/margin ruling — DECIDED 2026-07-18: explicit `-USD`** (see the A1 banner above).
      All tradfi is USD-settled (no inverse), but the quote is carried anyway for cross-asset-class uniformity +
      non-ambiguity, consistent with the DERIBIT ruling. Target =
      `VENUE:TYPE:PRODUCT_ROOT-USD@LIN-YYYYMMDD[-STRIKE-C|P]`.
- [x] ✅ [BACKEND] P1. **Route the tradfi writers through the shared `build_canonical_instrument_id`** (re-drift
      prevention) + a QG that fails a raw-shaped tradfi `instrument_key` on write — else new writes re-drift.
      `canonical_id_builder_retrofit_checklist_2026_07_08.md`. **SHIPPED 2026-07-25 —
      mtds@4e631a3df071c0d253bd4e5e3c7f053a890fa1be**
      (`scripts/quality_gates/check_no_raw_tradfi_instrument_id_construction.py`, an AST-walk guard over
      `market_tick_data_service/market_interface/adapters/tradfi/` + `market_tick_data_service/engine/orchestrator/`:
      fails any `instrument_id`/`instrument_key` assignment built via a raw f-string/`.format()` colon-shaped literal
      outside the allow-listed canonical-builder calls
      (`build_instrument_id`/`build_canonical_instrument_id`/`build_leg`/`derive_tradfi_row_instrument_id`/
      `derive_row_instrument_id`/`canonicalize_raw_tradfi_id`). 0 findings on ship (independently re-verified this
      session too, incl. an added live-tree anti-regression test). **Honest caveat**: NOT YET WIRED into
      `quality-gates.sh`/`base-service.sh` (a fleet-wide blocking-gate change needs the RULE-11 whole-fleet-passes
      diligence, out of scope for this single-repo pass) — runnable standalone today, wiring it in is a tracked
      followup, not silently dropped. (repos: market-tick-data-service, unified-api-contracts)

## Phase B — run the migrations (all four surfaces, gated on Phase A green)

> Pre-migration drain per the VM runbook; direct-canonical-index mutation MUST pause the consolidator or use CAS /
> additive per-VM-shard writes (the EU floor-clip only "got lucky on timing" —
> `archive/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`).

> **✅ CASING FREEZE LIFTED 2026-07-20, operator ruling D1.** The Phase-B `instrument_type` case-migration script's
> `--apply` was frozen pending the contested manifest COLUMN-case axis (C2a) — this plan's Phase-B said UPPERCASE while
> `/codex/02-data/cross-asset-canonical-target-ssot.md` §7/§11 said lowercase, both citing the same operator on
> 2026-07-18. **D1 ruled UPPERCASE (catalogue wins)**, recorded in
> [`data_pipeline_reconciliation_skill_2026_07_20.md`](data_pipeline_reconciliation_skill_2026_07_20.md) § "OPERATOR
> DECISIONS — ALL THREE RULED 2026-07-20"; the codex has been corrected to match. The Phase-B script is **RATIFIED** and
> its casing freeze is **LIFTED**. The pre-migration DRAIN gate above is a **separate, still-live** operational
> precondition — D1 does not lift that one. Scope: manifest **COLUMN only** (path segment stays lowercase, id middle
> segment stays UPPER).

> **Phase-B design (empirically grounded, scoping workflow `wf_2f2c9a39-164`, full design in scratchpad `scope_B.md`):**
> The old `migrate_tradfi_single_leg_product_root_lin_2026_07_09.py` is a **CONFIRMED NO-OP** — its `_ID_RE` matches an
> intermediate `CME:FUTURE:GOLD-20260821` shape that NEVER persisted; every real raw id (`CME:OPTION:E1AF0 C1600`,
> `EW1H0_P2785`, `CBOE:FUTURE:VX/F1`) returns None → 0 rows rewritten. **Write NEW scripts, don't re-run.** Measured
> canonicalizability with {strip `VENUE:TYPE:`, strip `O:`, `_`→space, dash-strike→space} + the live
> `classify_databento_symbol`: catalogue **~1,110,780 / 1,111,322 (99.95%)** canonicalize, ~542 quarantine. THREE
> orthogonal manifest defects (not one): (1) id-format, (2) **~400k `instrument_type` MISLABELS** (options/combos
> stamped `FUTURE` — must re-stamp from the classifier, not trust the column), (3) null-id bundle atoms (by design).

- [x] ✅ [DATA] P0. **Shared primitive SHIPPED — `unified-api-contracts@3bd4ec29`.**
      `canonicalize_raw_tradfi_id(raw, venue, instrument_type)` + `assert_tradfi_derivative_ids_canonical` +
      `CanonResult`/`CanonStatus` + `TARGET_TRADFI_DERIVATIVE_ID_RE` in `internal/reference/tradfi_id_canonicalizer.py`
      (top-level re-exported). Re-derives type via `classify_databento_symbol` (lazy-imported — circular-import
      avoidance) + builds via `build_instrument_id(margin_marker="LIN", quote_asset="USD")` with the 4
      body-normalizations; typed result never a silent fallback; venue from the row column (never default-CME). 20 unit
      tests, UAC QG green. **Empirical proof on the live snapshots:** catalogue **99.86% OK** (1,109,717/1,111,322;
      1,267 quarantine-unparseable [204 negative-strike + 1,063 ICE-qualifier] + 338 quarantine-combo); manifest
      **62.42% OK** (617,808/989,755; QUARANTINE*COMBO 325,473 [147k CBOE `UD*`+ 176k CME prefix-spreads] +
      QUARANTINE_UNPARSEABLE 39,217 [36k ICE + 2,898`ticks`placeholders] + NULL_OR_EMPTY 7,225 + 32 continuous).
      **566,630 (57%) stored-type-vs-classifier mismatch** confirmed. Reuse`scratchpad/measure_canonicalize.py`. (repo:
      unified-api-contracts)
- [x] ✅ [DATA] P0. **Migrate the catalogue (Surface A) — SHIPPED + APPLIED LIVE 2026-07-25,
      instruments-service@52d8b3ef (`scripts/canonicalize_tradfi_catalogue_usd_lin_2026_07_25.py`).** Both surfaces
      migrated per the durability trap below: `prod/catalog.parquet` full-sweep applied (8,140 rows migrated),
      post-apply verify 775,116/776,387 canonical (99.84%), residual is EXACTLY the enumerated 1,271-row quarantine (204
      negative-strike + 1,063 ICE-qualifier-variant + 4 other-unparseable — confirmed via a second, fully-unbounded
      re-verify query, not just the script's own bounded sample). Per-day corpus (`instrument_availability/by_date/`,
      27,142 real files, single delimited listing) full-sweep applied: 0 files touched (already canonical from the
      2026-07-18/20 migrations), verify 68,133,635/68,406,251 canonical (99.60%), residual is exactly the 272,616-row
      quarantine — dominated by **269,520 ICE-qualifier-variant rows**, a materially larger population than the
      catalogue-only 1,063 estimate (queued for operator decision in
      `plans/active/issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md` item 1). **Durability-rebuild
      verification (re-run `build_instrument_catalogue.py --mode full` + re-verify `prod/n` stays canonical) STILL IN
      PROGRESS as of this checkpoint** — the by-day corpus was already independently confirmed canonical before the
      rebuild (so a revert-on-rebuild is not expected), but per this todo's own stated durability trap the rebuild must
      still be observed to complete cleanly before this is fully closed; tracked as a residual sub-step, not a new todo.
      Original text retained below for context.
      ~~`instruments-service/scripts/canonicalize_tradfi_catalogue_usd_lin_*.py`\*_ modeled on
      `canonicalize_okx_margin_type_2026_07_09.py`. DURABILITY TRAP: `prod/n` is a roll-up regenerated by
      `build_instrument_catalogue.py` from the per-day
      `instrument_availability/by_date/day=_/venue=\*/instruments.parquet`corpus — a`prod/n`-only rewrite SILENTLY
      REVERTS on next rebuild (killed the 2026-07-08 combo migration). So migrate BOTH `prod/n`(snapshot → recompute
      `instrument_id`+`instrument_type`+`underlying`+`canonical_instrument_id`byte-equal → upload) AND the per-day
      corpus (worklist from the manifest, single-walk), then re-run`build_instrument_catalogue.py`and assert`prod/n`
      stays canonical. (repos: instruments-service)
- [x] ✅ [DATA] P0. **Migrate the live manifest (Surface B) — RE-VERIFIED LIVE 2026-07-25.**
      `market-tick-data-service/scripts/migrate_tradfi_manifest_usd_lin_2026_07_18.py --in-place-cas --apply` on
      `canonical-migration-tradfi-manifest-cas-20260722-075028` SUCCEEDED on attempt 4/8 (`run.log`:
      `IN-PLACE CAS APPLY COMPLETE: 6262988 rows rewritten in place ..., 1989 derivative rows corrected, 4898 bundle underlyings translated, 1751779 CASH rows migrated to -USD, 48920 simple enum re-stamps, 0 QUARANTINE_COMBO rows re-stamped. Raw derivative rows remaining: 35499 (quarantine-only, by design)`,
      `CAS FINAL rc=0`). Fresh live read of `_index/availability_index.parquet` (2026-07-25, 5,902,157 rows)
      confirms this landed and held: FUTURE/OPTION `instrument_id` canonical (regex
      `^[A-Z0-9-]+:(FUTURE|OPTION):[A-Z0-9]+-USD@LIN-\d{8}(-\d+(\.\d+)?-[CP])?$`) 363,954/403,467 (90.2%); EQUITY/ETF
      carrying `-USD` suffix 3,189,939/3,225,484 (98.9%). **Residual non-canonical is NOT this todo's scope** — it is
      (a) the 35,499 by-design quarantine-only unparseable rows, and (b) re-drift from writer paths not yet converged to
      the shared builder (tracked separately: the "Converge every WRITER's instrument_type emission" P0 todo below, and
      the chain-bundle content rewrite todo) + the FUTURE/OPTION-per-contract chain-bundle content population (tracked
      separately below). This todo (the one CAS migration pass itself) is done and durable. (repos:
      market-tick-data-service, unified-trading-library)
- [x] [DATA] P0. **Migrate GCS filenames + tick CONTENT (Surfaces C+D) — SINGLE-INSTRUMENT DONE (2026-07-22); CHAIN-
      BUNDLE tool SHIPPED+MEASURED 2026-07-25 (mtds@a23dd8bd); `--apply` AT SCALE LAUNCHED 2026-07-27 (slot-10),
      completion pending.** `scripts/rewrite_tradfi_chain_bundle_content_id_2026_07_25.py` (worklist: underlying NOT
      blank + instrument_type in {futures_chain, options_chain}; per-ROW `canonicalize_raw_tradfi_id`, trusts path-
      level type not the row-level column). Dry-run 2,000/277,993: 68.6% would_rewrite (matches prior ~68.7% est).
      **LAUNCH**: extended `launch-canonical-migration-vm.sh` with a `tradfi-cid-cb` category (mirrors `tradfi-cid`
      exactly; no new VM-prefix registry entry needed) — `deployment-service@d805e2d`, QG green, `DRY_RUN=true`-
      previewed first. `SHARD_OF=8 ... tradfi-cid-cb 2026-01-01 2026-12-31 full` → 8 SPOT VMs (run-id
      `20260727-041704`), all verified STARTED. Confirmed the stale-tarball warning is harmless (`a23dd8bd` is an
      ancestor of the pulled SHA; no relevant fix landed since). **Completion NOT yet verified** — see the GATE todo
      below; do not re-launch until checked. Then `assert_tradfi_derivative_ids_canonical` proves 0 raw on all four
      surfaces (regex per Surface B todo above).
- [x] ✅ [VERIFY] P0. **GATE CLOSED 2026-07-27 (slot-9)** — `20260727-061325` completed all 8 shards (`EXIT_STATUS`=0,
      self-deleted, not preempted). `assert_tradfi_derivative_ids_canonical` over the live manifest's chain-bundle
      scope: `checked=961 canonical=961 violations=0`; direct GCS content read confirms genuine canonical ids (e.g.
      `CME:FUTURE:CRUDE-USD@LIN-20200619`).
- [x] ✅ [DATA] P2. **RULED 2026-07-28 — Option A (normalize qualifier + map to base root), previously gated on an
      operator — unified-api-contracts@f2a86e1e.** Implemented via two new regex constants in
      `tradfi_id_canonicalizer.py`: `_ICE_UNDERSCORE_BODY_RE` (pre-strips `_MD1`/`_Z`/`_MM1`/`_P` qualifiers before
      `_`→space normalization breaks the ICE_FUTURE_RE match) and `_ICE_QUALIFIER_SUFFIX_RE` (post-strips `!` qualifier
      from `classification.underlying` before `EXCHANGE_CODE_TO_NAME` lookup). Extracted `_build_future_option_result`
      helper to keep `canonicalize_raw_tradfi_id` under the 200-line limit (now 148 lines). 8 updated/new unit tests (43
      total), QG green. All 269,520 ICE-qualifier manifest rows that were previously QUARANTINE_UNPARSEABLE now
      canonicalize — the qualifier is venue-specific contract metadata the canonical id does not need (expiry+strike
      already uniquely identify the contract). decision.** Canonicalisation-not-a-hack rules out Option B (relax the
      naming gate) and Option C (quarantine/defer); Option A was already the team's own `[REC]`. Build: normalize the
      qualifier (`_Z`/`!`/`_MD1`) into the canonical id, map to the base product root, extend `EXCHANGE_CODE_TO_NAME`.
      Non-MVP, no rush, no longer operator-gated. **Done when**: all 269,520 ICE-qualifier rows + the 1,063-row
      quarantine bucket canonicalize, 0 remaining.
- [x] ✅ [DATA] P2. **NEW 2026-08-07 (operator, via consolidated NA-blocker-digest audit) — purge these rows, do not
      keep them live. SHIPPED 2026-08-09 — instruments-service@4b54bc99.**
      `tradfi_autonomous_session_operator_decisions_2026_07_25.md` item 1 re-asked this exact question on 2026-08-07
      without realizing the classifier fix above had already shipped 2026-07-28 (that item was stale — corrected there
      too). The operator's actual 2026-08-07 answer adds new scope beyond the shipped fix: since ICE is non-MVP and this
      data will not be used, delete the (now-canonicalized) 269,520 ICE-qualifier rows + the original 1,063-row
      quarantine bucket from both the catalogue and the by-day corpus feeding it, rather than leave them sitting as
      valid-but-unused entries. `instruments-service/scripts/purge_tradfi_ice_qualifier_rows_2026_08_09.py`
      (delete-safety-cited `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a inline — object/prefix delete
      via `gcs_conditional_delete`/`gcs_conditional_put` qualifies for agent-autonomous execution once a fresh same-run
      `gcs_bucket_soft_delete_retention_seconds` check clears 604800s; no `[OPERATOR]` tag needed). **Live-state
      finding: the population was already purged** — a prior ad-hoc, uncommitted run had already applied the delete
      (backup snapshot `prod/backups/catalog.parquet.pre_tradfi_ice_purge_20260808-001425.bak.parquet` dated
      2026-08-08T00:14:25Z existed before this script was ever written). **Fresh live re-verification this session (both
      dry-run AND `--apply`, both surfaces, genuinely re-run, not just cited from the script's own docstring)**:
      catalogue 919,493 total rows / 0 ICE-qualifier matches (0 writes); by-day corpus 2,656 real day partitions / 4
      residual `venue=ICE` directories, all a different, unrelated ICE product (`ICE:INDEX:DXY-USD`, never part of this
      population) / 0 qualifier matches (0 writes); `--apply` run also confirmed the live fresh retention check passes
      (`instruments-store-tradfi-prd-central-element-323112` = 604800s). This 0/0 result on both surfaces, both modes,
      is the completion evidence — the shipped tool also formalizes the already-applied purge as reviewed code and gives
      the fleet a genuine re-drift detector (re-run either mode any time to prove 0 residual, or purge for real if ICE
      FUTURE/OPTION capture ever resumes).
- [x] ✅ [DATA] P0. **Enumeration-driven migration (SINGLE SOURCE OF TRUTH — operator, 2026-07-18) — CASING sub-scope
      CLOSED 2026-07-25 to the literal-100% directive bar; semantic-mislabel-relabel + null/blank sub-scopes remain
      separately open, see the new P1 todo just below.** The migration MUST be driven by the FULL distinct set of
      dimension values actually present in the tradfi manifest/GCS rollup (query the
      availability_index/coverage-rollup), NOT sampled shapes — so every value is covered + dupes are caught. **Audit
      done (local snapshot, scratchpad `enumerate_dimensions.py`)** — non-canonical dimensions found: (1)
      `instrument_type` **18 distinct** with case+plural dupes — `FUTURE`(568k)/`future`(421k)/`FUTURES`/`futures`,
      `EQUITY`/`equity`, `ETF`/`etf`, `SPOT_PAIR`/`spot_pair`, `indices`/`index`, +
      `<null>`(511k)/`''`(85k)/`UNKNOWN`(77); catalogue is all-UPPERCASE enum while manifest is mixed → surfaces
      DISAGREE. Writer `_PARTITION_INSTRUMENT_TYPE` (`databento_adapter.py:179`) maps FUTURE→`futures_chain`,
      OPTION→`options_chain`, EQUITY→`equity` (lowercase, bundle-grain). (2) **Barchart STALE** —
      `source=barchart`(4,655) + venue `BARCHART`(9,119) + `pipeline_mode=batch_barchart` despite Barchart being
      RETIRED. (3) `chain` null-vs-`''` dupe. **✅ DECIDED (operator, 2026-07-18): canonical `instrument_type` =
      UPPERCASE enum, CATALOGUE is the SSOT** — `{FUTURE, OPTION, EQUITY, ETF, INDEX, COMBO, SPOT_PAIR}`. **CASING FIX
      SHIPPED + APPLIED LIVE 2026-07-25 — mtds@4e631a3df071c0d253bd4e5e3c7f053a890fa1be
      (`scripts/migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py`).** A fresh live read that same day (post the
      2026-07-22 CAS run) found a **45,681-row residual** still lowercase (`equity`/`future`/`etf`/`index`/`combo`/
      `spot_pair`/`spot` — the exact re-drift the "IMPLICATION" note below predicted, `written_at` up to 2026-07-24
      proving forward writes were STILL emitting lowercase). In-place CAS applied: **5,902,618 rows rewritten, 45,681
      case-corrected**, pre-migration snapshot at
      `_index/backups/availability_index.pre_itype_casing_100pct_20260725T014753Z.parquet`, consolidator paused for the
      write window and resumed after. **Fresh live re-verification (separate read, post-apply): 0 non-UPPERCASE
      `instrument_type` rows for tradfi, excluding the permanent `futures_chain`/`options_chain` bundle-grain axis** —
      this satisfies the casing directive's literal-100% bar
      (`/plans/archive/2026_08/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`) for the CASING dimension
      specifically. **INDEPENDENT re-verification (separate session, same day, post-writer-fix):** `Rows CHANGED: 0`,
      `SELF-VERIFY: 4,988,822/4,988,822 UPPERCASE` — corroborates 0 residual with a second, later read. Bundle atoms
      `futures_chain`/`options_chain` are a SEPARATE partition-grain axis (manifest-only, null-id) — kept distinct, NOT
      folded into the enum, per design. (repos: market-tick-data-service, unified-trading-library, instruments-service)
- [x] ✅ [DATA] P1. **Semantic-mislabel relabel + null/blank resolve — CLOSED 2026-07-27, mtds@132ea6b1.** Surface B
      left QUARANTINE_COMBO + null/blank/UNKNOWN out of scope — new in-place-CAS
      `migrate_tradfi_manifest_itype_semantic_relabel_2026_07_27.py` relabels only on OK/ALREADY_CANONICAL/
      QUARANTINE_COMBO, else honest-absence. Plan's cited counts were stale — real residual 2,058,772 evaluated, 1,587
      changed; applied live, independent re-read confirms held. New re-drift finding filed below. (repo: mtds)
- [x] ✅ [DATA] P1. **Casing re-drift — 2 writer bypasses fixed, mtds@a1729bb4** — see
      `/plans/archive/2026_08/tradfi_casing_100pct_redrift_2026_07_27.md` (residual + follow-ups tracked there). (repo:
      mtds)
- [x] ✅ [BACKEND] P0. **Converge every WRITER's `instrument_type` emission to the UPPERCASE enum (catalogue SSOT,
      operator 2026-07-18)** so forward-writes don't re-drift the manifest to lowercase after the Phase-B re-stamp.
      **SHIPPED 2026-07-25 — mtds@020b703e "fix(tradfi): route manifest instrument_type casing through one canonical
      UPPERCASE emitter"** — new
      `market_tick_data_service/engine/orchestrator/_tradfi_manifest_canon.py::canonicalize_tradfi_manifest_itype`, the
      single shared emitter wired into BOTH the captured-row counting path (`venue_fetch.py`) AND, newly, the
      honest-coverage sentinel fan-out (`sentinels.py`) — sentinel rows had ZERO prior canonicalization and turned out
      to be the MAJORITY of the 2026-07-25 residual (100% of the equity/etf case-drift was
      `expected_unattempted`/`empty_confirmed` sentinel rows, not captures). Extends the original 3-token map
      (equity/etf/index) to also cover future/combo/spot_pair/spot/currency/bond/cds/commodity. `futures_chain`/
      `options_chain` remain the sole PERMANENT exclusion (bundle-grain axis, unchanged), and the GCS partition-path
      segment stays lowercase (unchanged, correct — only the MANIFEST column casing is affected). Evidence: 159/159
      targeted tests green (23 new + 136 pre-existing, 2 updated to the new correct behavior), full `quality-gates.sh`
      green (267s). This is the writer-side half of re-drift prevention; the QG-gate half is the separate P1 todo above
      ("Route the tradfi writers through the shared build_canonical_instrument_id"). (repos: market-tick-data-service,
      unified-trading-library)
- [x] ✅ [DATA] P1. **v9 schema / manifest-status finish** (`tradfi_v9_stage1_finish_2026_07_06.md`) — fresh CF-1…CF-12.
      **DONE 2026-07-28 — mtds@ab72ebec**: `schema_version` dtype CONFIRMED int64 (not string `'9'`; 2026-07-20 fix
      holds); CF-1 ("Layer-1 %") = 100.0000% v9; CF-2-7/9/13/paths GREEN; only pre-adjudicated CF-8/Era-B remain.
      Legacy-twin DELETEs RETAGGED (§3a, 2026-07-28).
- [x] ✅ [PM] P1. **Reconcile the stale fork** `data_completion_tradfi_2026_07_15.md` against `tradfi_v9_stage1_finish`
      (flip done todos, re-scope open ones, delete its duplicate paragraph) so the backlog is honest. DONE 2026-07-21
      (docs-reconciliation pass, `/plans/archive/issues/tradfi_docs_reconciliation_findings_2026_07_21.md`):
      C0/C-source/C-pipeline_mode RIDER/post-walk read/orphan-sweep/E4/E5/E7 flipped to `[x]` with evidence citing
      `tradfi_v9_stage1_finish`; the Massive-dependent gate-b/coverage-gap/dual-source paragraphs re-scoped or marked
      obsolete.

### B.5 — Candle namespace quarantine backlog (`processed_candles/`, SEPARATE from Surfaces A-D above — different

### bucket prefix, different script, different defect class: unresolvable leaf ids, not id-format canonicalization)

> Folded in 2026-07-23 (operator directive: "human plan for tradfi under tradfi consolidated plan which exists already")
> from `candle_feature_canonical_path_divergence_2026_07_20.md` todo 3. That doc's P6-P8 canonical-**path** migration
> (`market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py --apply`) is COMPLETE and independently
> P8-verified for all 4 asset_groups (`data_pipeline_reconciliation_candles_tradfi_2026_07_23.md`) — 0 orphans, 0
> malformed objects sitting in `processed_candles/`. What's NOT complete: of TradFi's original 7,646,831 candle objects,
> only 534,679 (7%) resolved to canonical; **the other ~7.1M (93%) are quarantined** in `_quarantine/` (safe,
> un-deleted) because their filename leaf id is an unresolvable migration artifact (e.g.
> `E1AM2_C3950_migrated_20260419T133933Z.parquet` — sample confirmed 2026-07-23 as CME options, strike-coded, under
> `venue=CME/data_type=ohlcv_15m`). Operator guidance (2026-07-23): genuinely-tiny irrecoverable loss is acceptable; the
> priority is getting this resolved properly, with any new code change tracked here, not done ad hoc.

- [x] ✅ [DATA] P1. **Survey raw-tick source availability — DONE 2026-07-27 (slot 14)** —
      market-data-processing-service@fcfaa5e. Delimiter-descent survey
      (`scripts/survey_tradfi_quarantine_raw_source_2026_07_27.py`): 712 days, 4,451 cells, 0 unparsed. **3,123 (70.2%)
      recoverable / 1,328 (29.8%) unrecoverable** (no raw ticks in `batch_databento`/`batch_massive`/`batch_yahoo`).
      Report: `market-data-processing-service/scripts/_tradfi_quarantine_raw_source_survey_2026_07_27.json`.
      `batch_databento` backs all recoverable cells; `batch_massive`=ZERO (already purged 2026-07-21, this todo's
      "before purged" text is stale). **Unrecoverable concentrated in `ICE`(853)/`CME`(368)/`CBOE`(107),
      `ohlcv_1m`(699)/`ohlcv_15m`(342)/ `trades`(178)/`tbbo`(108), spans 677/712 days — looks systemic, not isolated.**
      Handoff: not "genuinely tiny" — flag for BLOCKED-OPERATOR-DECISION in the next todo.
- [ ] [DATA] P1. **RULED 2026-07-28 — do NOT write off the 1,328-cell (29.8%) unrecoverable population; check the live
      vendor first.** Was gated on an operator decision (loss is systemic, 677/712 days, concentrated ICE/CME/CBOE) —
      but per the theme + "external data is always available" + "Databento billing unblocked": the survey only proved
      absence from OUR GCS, not from Databento's live API. Query Databento for the specific cells; full backfill
      wherever it has the data (cost no object); only what's PROVEN unobtainable after that → permanent loss, citing the
      fresh vendor query. Cells with intact raw ticks keep the original fix (delete quarantined + MDPS `--force`).
      **Done when**: all 1,328 cells resolved to backfilled-or-vendor-confirmed-unobtainable, final loss count cited.
- [x] ✅ [DATA] P2. **Verify + close** `candle_feature_canonical_path_divergence_2026_07_20.md` todo 3 once the above
      lands — unified-trading-pm@<SHA> (verified: migration execution plan archived, all 20 todos [x]; issue doc todo 3
      updated with stale-path fix + verification reference).

## Pass-through from the 2026-07-18 consolidated canonicalisation audit (slot-4) — decisions + measured worklist

> Authored by the DeFi close-out audit (`defi_consolidated_closeout_2026_07_18.md`) and handed here per the operator's
> ownership split (tradfi findings land in THIS plan). Operator rulings 2026-07-18.

**Operator decisions confirmed (tradfi):**

- **Equity id = `-USD` on ALL FOUR surfaces** — target `NASDAQ:EQUITY:AAPL-USD`. Today the content `instrument_id`
  column + manifest key emit BARE `NASDAQ:EQUITY:AAPL` (only the filename carries `-USD`, via a separate `file_stem`).
  **Code fix**: `_build_tradfi_cash` currently appends the quote only for `INDEX` — extend it to append `-USD` for
  `EQUITY` (and `ETF`) so the content column matches the decided target. Then migrate the historical rows (1,762,272
  prefixed-missing-`-USD` + 1,082,217 raw-ticker rows). The Phase-B/D verify gate must assert `-USD` on equity too (its
  current regex only targets FUTURE/OPTION).
- **Venue token = HYPHEN SSOT** (tradfi venues are already single-spelling uppercase — CME/NYSE/NASDAQ/CBOE/KRX/FX — no
  drift; confirmed clean on this surface).
- **Daily data_type = `ohlcv_24h`** (least churn) — the live manifest already carries **541,579 `ohlcv_24h` rows and
  ZERO `ohlcv_1d`**, so `ohlcv_24h` is the persisted token → **no data migration**. The only code change: add
  `ohlcv_24h` to `market-tick-data-service/.../tradfi/tradfi_shared.py::TRADFI_DATA_TYPES` (which currently RAISES on
  it) and reconcile the Yahoo adapter docstring. The daily Treasury/KRW ids (`CBOE:INDEX:US10Y-USD`,
  `FX:CURRENCY:KRW-USD`) are stable either way.
- **Combos = the leg-aware signed-weight spec** (operator 2026-07-09,
  `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`): per-leg human-readable `instrument_key` + weight +
  direction-as-sign, 1–4-leg hard cap, migrate code AND data. The IS-catalogue CME + CBOE/VX path is shipped; **OPEN
  here**: the **1,154,976 tick-side `UD_*` manifest combos** (null id + null `combo_type`/`leg_weights`) need the same
  legs-re-derived → structured `VENUE:COMBO:…` id + populated `leg_weights` treatment (Phase-B), plus the
  `build_instrument_catalogue.py` self-refresh durability fix. **Open sub-nuance**: the top-level combo id being
  strategy-named (`CME:COMBO:SP500-BUTTERFLY-…` from `build_combo_id`) vs the operator's "no separate strategy field,
  infer from legs" spec — resolve when combos are worked; doesn't block.
- **ETF** — keep ETF as a distinct canonical instrument_type (ETF ≠ equity; IBIT/ETHA are MVP crypto-ETFs); case-fold
  the manifest COLUMN **UP** to `ETF`. (Flag if you'd rather fold ETF into `EQUITY` — 270,460 rows either way.)

  > **⛔ corrected 2026-07-20, operator ruling D1.** ~~Was: "keep `etf` … case-fold `ETF`→`etf` … fold ETF into
  > `equity`"~~ — that ordered the fold DOWN, contradicting this same plan's Phase-B decision at :466-468 (UPPERCASE
  > enum, catalogue is SSOT). D1 ratifies UPPERCASE for the manifest COLUMN; the fold direction is **UP**. The GCS
  > **path** segment stays lowercase (`instrument_type=etf`) and the id middle segment stays UPPER — neither changed.

- **~591k instrument_type MISLABELS** (options/combos stamped `future`/`FUTURE`) → re-stamp from the classifier by BODY,
  not the stored column (the plan's cited "~400k" is the lowercase-`future` subset; the 206,200 `FUTURE` calendar
  spreads are an additional cohort).

**Live manifest worklist (`market-data-tick-tradfi-prd`, 5.55M rows; canonical id ≈0.02%, ZERO derivative ids carry
`@LIN/@INV`)** — venue/data_type/source/pipeline_mode are CLEAN; instrument_type + instrument_id are the work:

> **⛔ CASE DIRECTION CORRECTED 2026-07-20, operator ruling D1** — recorded in
> [`data_pipeline_reconciliation_skill_2026_07_20.md`](data_pipeline_reconciliation_skill_2026_07_20.md) § "OPERATOR
> DECISIONS — ALL THREE RULED 2026-07-20". **This table previously ordered the `instrument_type` case-fold DOWN to
> lowercase** (row 1: `FUTURE`/`EQUITY`/`SPOT_PAIR`/`FUTURES` → "lowercase", 750,715 rows; row 3: `etf`/`ETF` → `etf`,
> 270,460 rows) — **directly contradicting this same plan's own Phase-B decision at :466-468**, which ordered the
> migration UP to the UPPERCASE catalogue enum. The row counts are unchanged and preserved below; **only the direction
> is corrected — the fold is UP.** This applies to the manifest `instrument_type` **COLUMN only**: the GCS **path**
> segment stays lowercase and the instrument-id **middle** segment stays UPPER. Neither was ever in question.

| dimension       | non-canonical                                   | canonical target                                 |     ~rows | action                          |
| --------------- | ----------------------------------------------- | ------------------------------------------------ | --------: | ------------------------------- |
| instrument_type | `future`/`equity`/`spot_pair`/`futures`         | UPPERCASE enum ~~lowercase~~ (D1)                |   750,715 | case-fold **UP**                |
| instrument_type | `combo` (null id + null combo_type)             | leg-aware `VENUE:COMBO:…` + `leg_weights`        | 1,154,976 | synthesize (see combo decision) |
| instrument_type | `etf`/`ETF`                                     | `ETF` ~~`etf`~~ (D1)                             |   270,460 | case-fold **UP**                |
| instrument_type | `NULL`/`''`                                     | populate from writer grain                       |   596,851 | resolve                         |
| instrument_type | MISLABEL `future`=option/combo, `FUTURE`=spread | relabel from id                                  |   591,183 | relabel                         |
| instrument_id   | prefixed missing `-USD` (`NYSE:EQUITY:DUK`)     | `…-USD`                                          | 1,762,272 | append quote                    |
| instrument_id   | raw ticker (`ASTS`,`QQQ`)                       | `VENUE:EQUITY\|ETF:SYM-USD`                      | 1,082,217 | reconstruct                     |
| instrument_id   | raw databento option (`EW1H0_C3025`)            | `VENUE:OPTION:ROOT-USD@LIN-YYYYMMDD-STRIKE-C\|P` |   238,359 | reconstruct                     |
| instrument_id   | raw chain-root (`SI.OPT`,`VX.FUT`)              | `VENUE:FUTURES_CHAIN:ROOT-USD@LIN`               |   216,563 | reconstruct                     |
| instrument_id   | whitespace (`CME:OPTION:E3AN6 C7960`)           | de-spaced canonical                              |   206,579 | strip whitespace                |
| instrument_id   | NULL/empty aggregate rows                       | synthesize symbolic id                           | 1,844,635 | synthesize                      |
| data_type       | `futures_chain` leaked (8)                      | belongs in instrument_type                       |         8 | relabel                         |
| source/vendor   | legacy `barchart` (retired)                     | drop or keep-historical                          |     4,655 | operator: drop?                 |

**Enumeration-restore (cross-AG, owned by the DeFi plan Track 6)**: the raw distinct-values audit panel per asset_group
(removed on `deployment-api@512180be`) is being restored so this worklist stays live-visible during the migration.

## Codex SSOTs (read before touching this workstream)

`/codex/02-data/tradfi-databento-sourcing-ssot.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/02-data/honest-coverage-model.md`, `/codex/02-data/pipeline-mode-partition.md`,
`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`,
`/codex/05-infrastructure/manifest-consolidator-ssot.md`. Full SSOT + aggregated-source-doc list lives on the parent,
`tradfi_consolidated_closeout_2026_07_18.md` (not duplicated here).

> **2026-07-18 through 2026-07-21 (ticks 1-12, 20-21, 23-27) Progress Log — extracted 2026-07-24** (plan-hygiene,
> `task_template.md` §3 finding J; content fully superseded by what was the "2026-07-21/22 continuation" section — now
> ALSO extracted, see the next banner below) → verbatim history at
> `/plans/archive/2026_07/tradfi_manifest_content_recovery_completion_history_2026_07_24.md`.

> **2026-07-21/22 continuation Progress Log — extracted 2026-08-03** (line-cap remediation, live plan was at 1000/1000
> lines, no headroom for the context_scope backfill; zero open todos in this section, verified before extraction) →
> verbatim history at `/plans/archive/2026_07/tradfi_manifest_content_recovery_completion_history_2026_08_03.md`.
> Superseded by the "2026-07-22" section immediately below, which is the doc's live source of truth going forward.

## Progress Log — 2026-07-22 (all migration work moved to VMs — time/credit-constrained finish)

- **context-scout 2026-08-03**: populated context_scope (6 entries).

**Operator explicitly asked to move all remaining tradfi migration work onto VMs (compute, not chat turns) given session
time/credit limits. Everything below is now running on GCP compute, decoupled from this session.**

### Shipped this stretch

- **Cash-bucket crash fix, done properly**: the two background agents' work (documented above as "in flight,
  uncommitted") turned out to be incomplete on inspection — the earlier agent's test file correctly proved the bug ALSO
  hits `_process_derivative` and `build_in_place_frame` (the actual `--in-place-cas` path), not just `_process_cash`.
  Rewrote as a single `_safe_canonicalize()` helper used by all 4 call sites, verified against the agent's own 5-test
  regression file (all pass) + 2 live dry-runs (additive and `--in-place-cas`, both clean, no crash). Shipped
  `mtds@<latest>` (`fix(mtds): tradfi manifest cash-bucket id-canonicalization crashes...`).
- **Content-rewrite script shipped**: `mtds` `feat(mtds): tradfi parquet-content instrument_id rewrite executor`.
- **VM launcher extended** (`deployment-service`, 3 commits): two new categories on `launch-canonical-migration-vm.sh` —
  `tradfi-cid` (content-rewrite, shard-fan-out, renamed from `tradfi-content-rewrite` after hitting GCE's 63-char
  VM-name limit) and `tradfi-manifest-cas` (the manifest `--in-place-cas` re-stamp, wrapped in an 8-attempt in-VM retry
  loop with jittered sleep — see finding below).

### Live dry-run numbers (confirmed via the fixed script, 2026-07-22, before any VM ran)

Total manifest rows 6,262,988. Bucket 1 (derivative FUTURE/OPTION): 399,453 candidates, 91.1% already/now-canonical,
1,989 real fixes, 30,529 genuinely unparseable (quarantined, not crashed). Bucket 2 (bundle underlying): 494,670
candidates, 4,898 translated. **Bucket 3 (CASH — equity/etf/etc, the big one): 3,551,005 candidates, 1,751,779 rows
migrated to the -USD id (49.3%)**, only 370 quarantined. Bucket 4 (SPOT_PAIR/COMBO case-only): 1,404,118 candidates,
48,920 re-stamped. **This is the number the 2026-07-18 run should have produced and never did** because it crashed
partway through on the first malformed spread symbol.

### 🔴 Finding: the CAS race against the manifest consolidator is worse than documented

Ran `--apply --in-place-cas` for real, 2 attempts from this laptop (cross-region) + 2 attempts from a fresh
`asia-northeast1` VM (in-region) — **all 4 lost the CAS race**, aborting safely (no partial write, per design) every
time. Off-region window ≈90s (exceeds the consolidator's 60s cycle — a guaranteed loss, not bad luck). **In-region
window ≈23s still lost twice** — better odds (~60%+ per attempt) but not a sure thing. Could not pause the consolidator
scheduler (`cloudscheduler.jobs.pause` denied on both the compute service account and the operator's account, whose
token was also expired; could not self-grant IAM either). Fix: `tradfi-manifest-cas` VM category now retries the whole
CAS attempt up to 8x in a bash loop **within the same VM boot** (no per-attempt VM-relaunch overhead), with a 5-25s
jittered sleep between attempts so different tries land at different phases relative to the consolidator's tick.

- `[x] [INFRA] P3. Actually fix the scheduler-pause permission gap for `uts-prod-manifest-consolidator-market-data-tradfi-cron`— whichever account/role should have`cloudscheduler.jobs.pause` on it doesn't; the 8x-retry loop is a workaround, pausing properly is the real fix and would make every future manifest CAS script instant-reliable.`
  Fixed 2026-07-22: granted `roles/cloudscheduler.admin` to the compute service account via a direct Cloud Resource
  Manager API call (operator-authorized ADC-token workaround — `gcloud iam`/`add-iam-policy-binding` failed under the
  service-account identity, ADC held a valid token for the operator's own account). Confirmed working: paused + resumed
  the job successfully. The 8x-retry loop stays as defense-in-depth, no longer load-bearing.

### VMs launched (check these directly, not by asking the main session — it may not be running anymore)

- `canonical-migration-tradfi-manifest-cas-<ts>` (with the 8x retry fix) — launched, in flight as of this checkpoint.
  Check: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/<name>/run.log | tail -40` for
  `CAS FINAL rc=0` (success) vs `rc=1` (all 8 attempts lost — re-launch once more, or escalate the scheduler-pause fix
  above).
- `canonical-migration-tradfi-cid-<ts>-shard{0..7}of8` (content-rewrite, `--apply`) — **5 of 8 shards confirmed
  COMPLETE, exit_code=0, ~107K rows each, ALL showing `already_canonical` — 0 divergent objects found in this
  worklist.** This is a real, useful negative result the build agent had already flagged as likely (its own >100-object
  live sample found the same thing): the equity/etf/spot_pair/index single-instrument population this script targets was
  ALREADY content-canonical (the 2026-07-08/09 write-path fix reached it via routine re-backfills). **The true
  ~68.7%-legacy population lives elsewhere — FUTURE/OPTION per-contract chain-bundle content, which was explicitly out
  of this script's scope** (see the script's own "DESIGN DECISION" docstring section). Remaining 3 shards were
  progressing identically (100% already_canonical) as of this checkpoint — check for the same pattern; if it holds, this
  whole pass is a clean confirmation, not a fix, and the REAL remaining content gap is the derivatives, not cash.
  - `- [ ] [DATA] P1. The true legacy-content population (FUTURE/OPTION per-contract chain-bundle content) still needs its own rewrite pass — `rewrite_tradfi_content_id_2026_07_21.py`'s worklist filter (`underlying`blank/null) deliberately excludes chain bundles. Scope a follow-up worklist keyed on`underlying`NOT blank +`instrument_type
    in {futures_chain, options_chain}` before declaring tradfi content-canonical.`
- `canonical-migration-tradfi-<ts>-shard{0..19}of20` (existing category, REBUNDLE — reuses the already-proven 3-pass
  migrate+rebundle+recover chain rather than a new one) — launched as of this checkpoint, satisfies the REBUNDLE todo
  (112,839 per-contract `options_chain` rows) using existing infra, no new code needed.

### Still not launched (ran out of time this session)

- CME MBO monolith migration (107 objects, 2.53GB, migrate-first-never-blind-delete) — no VM category exists for this
  yet; needs its own small content-read tool first (derive canonical `mbp_10` ids from content).
- Catalogue MVP promote (`build_instrument_catalogue.py --asset-group tradfi`) — still the cleanest, lowest-risk,
  fully-unblocked next item; genuinely just needs someone to run it.
- Phase D gate — blocked on everything above.

**Check VM completion via `gcloud compute instances list --filter='name~"^canonical-migration-tradfi"'` (empty = all
self-deleted on completion, `VM_SHUTDOWN_ON_COMPLETION=true`) and the per-VM logs at
`gs://deployment-scripts-central-element-323112/vm-logs/<name>/run.log`. No Claude session needs to be running for these
to finish — that was the whole point of moving them here.**

### Final confirmation — all 3 VM jobs launched (2026-07-22, end of session checkpoint)

- **`canonical-migration-tradfi-manifest-cas-20260722-075028`** — running (8x in-VM retry loop, ships
  `deployment-service@<fix-sha>`). Check `... /run.log | grep 'CAS FINAL'` for `rc=0` (success — the whole manifest is
  now canonical, matching the dry-run numbers above) vs `rc=1` (all 8 attempts lost the race — the scheduler-pause
  permission gap todo above is the real fix; a manual relaunch is a cheap stopgap in the meantime).
- **`canonical-migration-tradfi-cid-20260722-065920-shard{0..7}of8`** — confirmed all 8 launched; 5/8 confirmed complete
  (100% `already_canonical`, 0 real fixes needed — see finding above). Remaining 3 were mid-run, identical pattern, no
  reason to expect a different outcome.
- **`canonical-migration-tradfi-20260722-074047-shard{0..19}of20`** — confirmed all 20 launched (verified via direct
  fleet listing, not just the launcher's own claimed success). Sample check on shard0: real work done (60,428
  `VERIFIED_INPLACE`, 1,683 `MIGRATED`, 348 `SIZE_MISMATCH_KEPT_SRC` safety-holds, 169 `CONTENT_REPAIR_DEFERRED`), but
  its rebundle pass found 0 per-contract rows in THIS shard's slice — expected if the 112,839-row population isn't
  evenly distributed across the hash-based shards; check the AGGREGATE across all 20 shards'
  `rebundle_mapping.tsv.reconcile.txt` before concluding rebundle found nothing.

### All 3 VMs finished — outcomes confirmed (operator asked "why can't these run in parallel", pushed a 4th)

- **`tradfi-manifest-cas` — ✅ SUCCEEDED on attempt 4/8.**
  `IN-PLACE CAS APPLY COMPLETE: 6,262,988 rows rewritten in place (generation 1784703405264029 -> 1784703464018171), 1,989 derivative rows corrected, 4,898 bundle underlyings translated, **1,751,779 CASH rows migrated to -USD**, 48,920 simple enum re-stamps.`
  Matches the dry-run numbers exactly — the manifest is now genuinely canonical (not just paths/catalogue as before).
  Verified live post-write (fast `gsutil stat` generation check — the consolidator has since re-merged once more,
  expected/safe per the script's own docstring, not a regression).
- **`tradfi-cid` (content-rewrite, 8 shards) — ✅ all 8 complete.** Aggregate: ~859K rows processed, effectively 100%
  `already_canonical`, only **3 total `unresolved:numeric_surrogate_unresolved`** across the whole run (honest, tiny
  residual — not fabricated as fixed). Confirms the finding above: this worklist's content was already fine.
- **`tradfi` (rebundle, 20 shards) — ✅ all 20 complete, but "0 per-contract sources selected" in EVERY shard is
  CORRECT, not a bug.** Direct-checked a sample of the 112,839 manifest rows with `data_type=options_chain`: their
  `instrument_type` AND `underlying` columns are BLANK. This is the exact stale-manifest-artifact pattern the
  content-rewrite script's own design doc had already flagged (2,078 similar rows, smaller scale): leftover bookkeeping
  from an EARLIER bundling pass where the real GCS objects were already moved to their proper
  `underlying=<ROOT>/quote=USD/margin=linear/ticks.parquet` bundle path (a separate, populated manifest row) — the
  physical per-contract objects genuinely don't exist anymore, confirmed by rebundle's OWN fresh full-corpus GCS
  enumeration (not the manifest) finding zero matches across all 20 shards. **Rebundle is done; what's left is a
  manifest cleanup (retire 112,839 stale rows), not a data migration.**
  - `~~- [ ] [DATA] P2. Retire the 112,839 stale options_chain manifest rows...~~` **SUPERSEDED, premise was wrong** — a
    2026-07-22 verification (required before any manifest deletion) found this todo's own claim ("confirmed no
    corresponding GCS objects exist") was false for the large majority of these rows: only 291/112,839 were truly blank,
    the other 112,548 had REAL captured GCS data with zero manifest registration. Do NOT execute this todo as written —
    it would have deleted real data-visibility evidence, not hygiene. Replaced by the proper register-then-retire
    recovery pass below (`recover_tradfi_chain_manifest_registration_2026_07_22.py`, `mtds@c4cc819b1`/`mtds@c8ace21df`)
    — register phase fully applied (1,545 rows), retire phase awaiting operator review (see the P1-OPERATOR-REVIEW todo
    near the end of this file).

- **`tradfi-catalogue-promote`** — launched (`canonical-migration-tradfi-catalogue-promote-20260722-093107`, confirmed
  fresh tarballs at launch). Not yet confirmed complete as of this checkpoint — check
  `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-tradfi-catalogue-promote-20260722-093107/run.log`
  for the monotonic-guard promote result (old row count -> new row count, `mvp=True` count before/after).

- **CME MBO monolith migration — NOT started.** Attempted to enumerate the 107 `day=/venue=CME/ticks.parquet` objects
  via a narrow `gsutil ls` wildcard to scope the tool; the listing ran 5+ min without returning (cross-region latency,
  same class of problem the other in-region-VM fixes addressed) and was killed rather than burn more session time on it.
  This is genuinely the one item that needs real design work before it's safe to build (content-read MBO/depth parsing
  to derive canonical `mbp_10` ids from 604 numeric-id-per-file content, ONLY-COPY discipline, no existing reference
  pattern to copy unlike everything else this session reused) — not a "just launch it" item like the other three turned
  out to be. Next session: do the enumeration FROM an in-region VM (or via the manifest/a narrower known-day prefix
  list) rather than a laptop wildcard listing, then design the id-derivation before writing any code.

**Catalogue-promote — ✅ CONFIRMED COMPLETE.** `canonical-migration-tradfi-catalogue-promote-20260722-093107`,
exit_code=0 in <2 min. `MVP-tagged catalogue: 71,795 / 837,467 rows` (up from the stale 70,930), monotonic guard
`ACCEPT`, promoted to `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet`. Incremental mode
correctly picked up the trailing 3 weeks (112 by_date files, 153,545 rows updated in-window, 0 new listings — the new
MVP instruments' reference rows already existed from earlier IS capture, just weren't flagged mvp=True until this
rebuild). **All 4 of the parallel-launched VM jobs are now confirmed complete.**

**Backfill gap check** — re-queried the live fleet (`gcloud compute instances list --filter='name~"^tradfi-bf-"'`): only
the terminated PA-2021 VM remained, nothing else running or stuck. **Relaunched**
`tradfi-bf-cme-ohlcv-1m-pa-2021-20260722-160825` (`--only-root PA --year 2021`, skip-if-fresh will resume from the 9,680
rows already captured before the earlier hang), now using the tarball with the manifest-writer fix baked in. Not yet
confirmed complete as of this checkpoint. This was a lightweight check (fleet listing + the one known gap), not a full
per-root/per-venue completeness audit — if a genuinely thorough backfill-completeness pass is wanted later, that is
separate, larger work (would need an honest-coverage-style captured-vs-expected comparison across every MVP cell, not
just "is a VM still running").

### 2026-07-22 continuation — the honest-coverage audit + IAM fix + KRX gap + stale-row correction

**Operator asked for the real captured-vs-expected audit** (not just "is anything stuck") and to proactively ask
questions when a decision is needed. Ran it. Findings:

- **`roles/cloudscheduler.admin` GRANTED to the compute service account** — operator authorized "grant it yourself if
  your ADC login has the capability." It did: `gcloud auth application-default print-access-token` carries a VALID,
  unexpired token for `ikenna@odum-research.com` (separate credential store from `gcloud config`'s stale one). Used it
  directly against the Cloud Resource Manager API (`getIamPolicy`/`setIamPolicy`) to add the binding. Confirmed working:
  paused + resumed `uts-prod-manifest-consolidator-market-data-tradfi-cron` successfully (took ~1 IAM-propagation cycle
  before the first pause attempt succeeded). **This closes the scheduler-pause permission gap from the earlier
  checkpoint** — future manifest CAS writes can pause the consolidator properly instead of relying on the 8x-retry-loop
  workaround (the retry loop is still there as defense-in-depth, no need to remove it).
- **`ohlcv_1s` added to the tradfi MVP rule's `data_types`** (`unified-api-contracts`, `_mvp_scope_rules.py` + 2 test
  updates — one flipped from `_excluded` to `_included`, one exact-set guard updated). Operator-approved. Ship pending
  (quality-gates was mid-run at this checkpoint — verify it landed, `git log` for the commit message
  `"feat(mvp): add ohlcv_1s to tradfi MVP scope..."`).
- **Honest-coverage audit run for real** (`measure_honest_coverage.py --asset-group tradfi` via the existing
  `launch-measure-honest-coverage-vm.sh` launcher — the workspace's own nightly tool, not a new script). Real numbers
  (`gs://central-element-323112-honest-coverage/2026-07-22/coverage.json`, `denominator_status: INCOMPLETE` so treat as
  informative not final):

  | Venue    | Coverage | Captured | Attempted-failed | Still-unattempted |
  | -------- | -------- | -------- | ---------------- | ----------------- |
  | KRX      | 0.07%    | 6        | 2                | 8,621             |
  | NASDAQ   | 28.72%   | 96,143   | 67,316           | 171,308           |
  | NYSE     | 81.45%   | 809,006  | 37,192           | 147,007           |
  | CME      | 68.21%   | 504,873  | 198,447          | 36,802            |
  | CBOE     | 29.99%   | 2,619    | 3,731            | 2,382             |
  | FX       | 95.29%   | 4,288    | 59               | 153               |
  | BARCHART | 100%\*   | 0        | 0                | 0                 |
  | ICE      | 75%      | 6        | 0                | 0                 |

  \*Barchart is correctly 100% — retired source, everything is legitimately expected-empty, not a real gap.

- **The large CME/NASDAQ `attempted_failed` counts are NOT a systemic bug** — checked the manifest's own `error_reason`
  column: 198,432/198,447 CME and all 67,316 NASDAQ failures are `WithinBoundsTradfiSourceZero`, a DELIBERATE,
  DOCUMENTED reclassification (`rebuild_tradfi_manifest.py`'s own docstring: "SOURCE_RETURNED_ZERO within-bounds... on a
  real trading day for a covered venue/data_type → reclassify to attempted_failed(WithinBoundsTradfiSourceZero)"). This
  means Databento legitimately returned zero rows for that specific symbol/day (e.g. an option strike that wasn't quoted
  that day) on an otherwise-valid trading day — normal and expected for a wide, sparse universe (every CME
  strike/expiry, every NASDAQ symbol, every day), not a crawler or API failure. **Correcting my own earlier "concerning"
  framing** — don't re-investigate this as a bug without new evidence; it's accounted-for by design.
- **KRX gap explained + closed.** Operator clarified: KRX = the 3 Korean single-stock equity-basis underliers
  (HYUNDAI/SAMSUNG/SKHYNIX, the Binance tradfi-perp basis legs) — NOT the KRW/USD currency pair (that's the separate
  `FX` venue row, already healthy at 95.29%). Confirmed via `source_priority.py`: KRX is Yahoo-ONLY (`ohlcv_24h` daily,
  no Databento/Massive coverage ever). No launcher had ever targeted this venue — the NASDAQ/NYSE equity launchers
  hard-assume Databento and never emit a `VM_VENUE=KRX` shard. **New launcher shipped**
  (`deployment-service/scripts/vm/launch-tradfi-bf-krx-equities-ohlcv-24h.sh`, mirrors the proven CBOE-indices
  Yahoo-daily template) and **launched** for real (check `tradfi-bf-krx-eq-ohlcv-24h-*` VMs).
- **🔴 CORRECTION to the earlier "112,839 stale rows, low-priority hygiene cleanup" claim — it was WRONG, do not naively
  delete.** Operator approved cleanup, scheduler was paused for the safe window, and while verifying the worklist
  precisely (a hard requirement before any manifest deletion) found: only 291 of the 112,839 rows are TRULY blank on all
  fields. The other 112,548 carry REAL old per-contract underlying values (`6AZ3`, `CC__FMZ0023!`, etc.) — and **direct
  GCS verification found the canonical bundle for at least 2 of these (COCOA, AUD) has REAL data on disk (confirmed
  2026-07-20-dated `ticks.parquet` files) but ZERO corresponding manifest row** — the rebundle that ran 2026-07-20
  updated GCS but never registered the new canonical bundle rows in the manifest, AND never retired the old per-contract
  rows. A broader distinct-underlying scan (`futures_chain`+`options_chain`, 493,293 rows) shows a genuine MIX: some
  product roots properly translated with healthy counts (GOLD/SP500/currencies — real, fine), others still
  raw/untranslated (`ESM6`/`XAP`/etc. — unclear without more work whether these are the SAME kind of
  manifest-registration gap or something else). **Stopped before writing anything** — this needs a proper
  manifest-recovery pass (register the missing canonical rows, THEN retire the confirmed-superseded old ones), not a
  delete-only cleanup, which would have made data LESS visible (real captured data with zero manifest representation),
  not more hygienic. Resumed the scheduler since no write happened.
  - `[x] ✅ [DATA] P1. Design + build a tradfi chain-manifest recovery pass — REGISTER sub-goal DONE + RE-VERIFIED LIVE 2026-07-25 (retire sub-goal tracked separately as its own P1-OPERATOR-REVIEW todo below, not part of this checkbox).`
    Script `recover_tradfi_chain_manifest_registration_2026_07_22.py` shipped
    `mtds@c4cc819b1845f0c1a7f4546612f80229242fe265` /`mtds@c8ace21dfeef294dc37d949264b1d373af55acca`; register `--apply`
    wrote 1,545/1,545 rows, 0 skipped. **Fresh live re-verification (2026-07-25, direct manifest query on
    `venue=CME, underlying=AUD, date IN (2023-06-19, 2023-06-21)`)**: all 4 sample rows read `capture_status=captured`
    in the current consolidated `_index/availability_index.parquet` — the register-phase rows are durable, not a stale
    one-time snapshot. Retire phase (50,520 candidate rows) remains explicitly `--apply`-gated pending operator review —
    see the P1-OPERATOR-REVIEW todo.
- **CME monolith investigation — in progress, not complete.** Launched a throwaway investigation VM
  (`cme-monolith-investigate-20260722`, e2-small, SPOT, NOT part of the tracked fleet registry — self-cleanup needed,
  `gcloud compute instances delete cme-monolith-investigate-20260722 --zone=asia-northeast1-c --quiet`) after the
  laptop's cross-region `gsutil`/`gcloud storage` wildcard listing repeatedly hung/timed out (same latency class as the
  earlier CAS-race problem). Findings so far: **only 30 objects currently match the `day=*/venue=CME/ticks.parquet`
  shape** (list captured, see `/tmp/monolith_list.txt` on that VM before deleting it) — NOT the 107 the 2026-07-21
  reconciliation audit found. Unexplained discrepancy — worth checking whether some were already swept up by an
  unrelated pass, or the reconciliation's count used a different exact pattern, before assuming either number is right.
  Content inspection (reading one sample file's actual MBO/depth column structure) was blocked by the raw Ubuntu image
  lacking `pip`/`venv` packages (`apt-get install python3-pip` reported "no installation candidate" — needs
  `apt-get update` first or the `uv`-based install path the production launchers use) — not yet completed.
  - `- [ ] [DATA] P2. Finish the CME monolith investigation: fix the pip/venv bootstrap on the investigation VM (or relaunch through the proper setup-data-pipeline-vm.sh path instead of a raw metadata startup-script), reconcile the 30-vs-107 count discrepancy, inspect real content structure, THEN design the migration tool. Clean up the investigation VM when done (not part of the tracked fleet).`

### 2026-07-22 continuation — CME monolith investigation: bootstrap fixed, count reconciled (unresolved), content inspected, VM cleaned up

- **pip/venv bootstrap fix**: `apt-get update` first, THEN `apt-get install python3-pip python3-venv` — the earlier "no
  installation candidate" error was a stale apt cache, not a missing package. Trivial once diagnosed.
- **30-vs-107 discrepancy — investigated thoroughly, NOT fully explained, but ruled out the dangerous hypothesis.**
  Checked, with direct evidence, in order:
  1. **Deletion**: bucket has soft-delete enabled (7-day retention) — queried soft-deleted objects matching
     `day=*/venue=CME/ticks.parquet`, found **zero**. No object matching this shape was deleted in the last 7 days.
  2. **A second/duplicate bucket**: the KRX launcher's own post-launch help text cites
     `gs://market-data-tick-tradfi-central-element-323112` (no `-prd-`) — that bucket **does not exist** (404). Only
     `market-data-tick-tradfi-prd-central-element-323112` is real. Rules out a split-count-across-buckets explanation.
     (Minor separate finding: the KRX launcher's echoed post-launch verification command has the wrong bucket name —
     cosmetic, doesn't affect the actual backfill, low-priority fix for later.)
  3. **Generations/versioning**: bucket versioning is off; the one sampled day (`2026-02-22`, the report's own cited
     example) has exactly one generation. Rules out a versioning-inflated count.
  4. **The report's source data**: found the reconciliation JSON's exact number
     (`census_s1_gcs.bare_pocket_shapes["day/venue_monolith"] = {objects: 107, bytes_gb: 2.534}`) but no committed
     script anywhere in the workspace produces that key — it was almost certainly computed by an ad-hoc inline script in
     that prior session, never persisted. The workspace's own `_index/audit/orphan_sweep_tradfi.parquet` (the sanctioned
     reusable single-walk snapshot) does **not** contain this monolith shape at all (only `E_orphan_real` 3,488 rows and
     `B_legacy_duplicate` 900 rows — the 900 matches report row F4 exactly, confirming that part of the report DID come
     from this sweep file, but the monolith count did not).
  - **Verdict**: live, directly-reproduced count is **30** (two independent single-level-wildcard listings, both
    matching the report's own cited example day `2026-02-22`), with no evidence of deletion, duplication, or
    double-counting to explain the gap from 107. The 107 figure cannot be reproduced from any artifact left in the
    workspace. Treat **30 as current ground truth** going forward; the 107 figure's origin is unresolved and, absent a
    committed script to audit, likely unrecoverable — not worth further time at P2.
  - **Process note (self-correction):** while chasing this, attempted a recursive `gsutil ls -r` / `**`-glob
    whole-corpus walk of `raw_tick_data/by_date/` to rule out a nested-path hypothesis — this violates the workspace's
    single-walk discipline hard rule (any new whole-corpus GCS walk is review-blocking). Caught it after launch (before
    it produced a real cost/count problem), killed it by deleting the investigation VM outright (which also happened to
    satisfy the "clean up the investigation VM when done" step). Correct approach used afterward: read the existing
    sanctioned `_index/audit/orphan_sweep_tradfi.parquet` single-walk snapshot instead of re-walking — should have gone
    there first.
- **Content inspected** (downloaded the `day=2026-02-22` sample locally via `gcloud storage cp` + read with local
  pandas/pyarrow — no VM needed for this part). Real structure: `data_type=trades` (Databento MBP-0/trades schema,
  `rtype=0`, `action='T'`), columns
  `ts_event, rtype, publisher_id, instrument_id (Databento's internal numeric id, uint32), action, side, depth, price, size, flags, ts_in_delta, sequence, symbol (human-readable, e.g. ESH6/NQH6), data_type`.
  63,388 rows / 1,097 unique `(instrument_id, symbol)` pairs in this one file — a genuine per-day ALL-CME-SYMBOLS
  fan-in, including calendar-spread combos (`NQH6-NQM6`). Confirms the report's characterization: no canonical Hive
  partitioning, numeric Databento ids not yet translated to canonical form, would need per-symbol grouping +
  `EXCHANGE_CODE_TO_NAME`-style translation (regular contracts) + COMBO handling (spread symbols) to migrate to
  canonical paths.
- **Migration tool NOT yet designed/built** — correctly scoped as separate follow-up work per the original todo's own
  phrasing ("inspect content, THEN design the migration tool"). This is a real, moderately large piece of new code
  (per-symbol grouping, contract-vs-combo classification, canonical path construction per `_canonical_chain_path`-style
  logic but for FLAT per-contract futures/options, not chain bundles, manifest registration) — deferred as its own P2
  todo below rather than rushed in this session alongside the higher-priority P1 manifest-recovery pass.
  - `[x] ✅ [DATA] P2. Design + build the CME monolith migration tool — TOOL DONE 2026-07-26 (`mtds@02284f8e`). Execution tracked separately: `/plans/archive/issues/cme_monolith_migration_execution_2026_07_26.md` (RESOLVED 2026-07-27).`

### 2026-07-22 continuation — the chain-manifest recovery script (P1), PA-2021 progress check

- **PA-2021 palladium backfill — genuinely progressing, NOT yet complete.** Checked via the VM's own live per-VM
  manifest shard (`_index/per_vm/tradfi-bf-cme-ohlcv-1m-pa-2021-20260722-160825.parquet`, read directly rather than
  trusting serial-console heartbeat activity alone, per the workspace's own progress-metric discipline — activity ≠
  progress). Real numbers: 928 `captured` rows + 1,345 `empty_confirmed`, date coverage through `2021-12-04` (~92% of
  the year by date). Alive, climbing, not stalled — but not finished (needs to reach 2021-12-31 + consolidate). Do not
  re-launch; let it finish.
- **Built `market_tick_data_service/scripts/recover_tradfi_chain_manifest_registration_2026_07_22.py`** — the P1
  chain-manifest recovery pass. Two deliberately separate, separately-gated phases: **register** (default,
  `--apply`-gated, additive `ManifestWriter.add()`, no CAS — for each raw-underlying `futures_chain`/`options_chain`
  manifest row, derive the canonical target via the same `_canonical_chain_path`/`_exchange_to_product_root` builders
  the rebundle script uses, check GCS existence via a targeted `gcs_describe_object` per candidate — never a corpus walk
  — and if confirmed present with no existing canonical row, insert one) and **retire** (`--retire`, separate
  invocation, whole-index in-place-CAS REPLACE mirroring `migrate_tradfi_manifest_usd_lin_2026_07_18.py`'s pattern —
  drops the now-superseded raw rows, re-verified fresh at retire time, never from a stale register-phase ledger).
  Research for the exact primitives (manifest read/write, CAS pattern, `gcs_describe_object`, `EXCHANGE_CODE_TO_NAME`
  usage) was done via a dedicated Explore sub-agent reading `rebundle_tradfi_chains_2026_07.py`,
  `recover_tradfi_garbage_underlying_2026_07.py`, `rebuild_tradfi_manifest.py`, and
  `migrate_tradfi_manifest_usd_lin_2026_07_18.py` in full first, so the recovered target is byte-identical to what the
  existing shipped tools already write/expect.
  - **Real bug found and fixed during the first dry-run.** The first classification pass compared
    `underlying.upper() == _exchange_to_product_root(underlying)` to detect "already canonical" — this returned 0
    candidates against a corpus KNOWN (COCOA/AUD sample evidence) to contain real gaps. Root cause: the manifest's raw
    `underlying` values for this corpus are not bare exchange codes — they are RAW PER-CONTRACT DATABENTO SYMBOLS stored
    in the `underlying` field by an older writer convention (`6AZ3`, `ESM6`), and a few genuinely-unparseable legacy
    forms (`CC__FMZ0023!`, an older continuous-contract naming scheme). `_exchange_to_product_root` silently no-ops on
    an unrecognised code (returns it unchanged) rather than erroring, so the naive check could not distinguish
    "genuinely already canonical" from "translation failed silently" — both looked identical. Fixed by adding
    `_derive_canonical_root()`, which first checks `is_recognized_tradfi_underlying()` (genuinely canonical), then falls
    back to `classify_databento_symbol()` (the UAC content-symbol parser the sibling
    `recover_tradfi_garbage_underlying_2026_07.py` already uses) to extract the near-root from a per-contract symbol
    BEFORE translating — e.g. `6AZ3` → `classify_databento_symbol` → `6A` → `_exchange_to_product_root` → `AUD`.
    Genuinely unparseable values (`classify_databento_symbol` raises `ValueError`) are skipped, not guessed.
  - **Register-phase dry-run (real, live manifest read — read-only, no writes) — results**: 493,389 tradfi
    `futures_chain`/`options_chain` manifest rows loaded; 106,907 had a genuinely unparseable `underlying` (skipped,
    correctly — legacy naming schemes `classify_databento_symbol` doesn't cover); 150,046 raw rows resolved to a real
    product root; of those, 50,458 are already covered by an existing canonical manifest row (no action needed — these
    become retire-phase input instead); the remaining 5,380 distinct `(date, venue, instrument_type, data_type, root)`
    candidate keys were checked against GCS individually (targeted `gcs_describe_object`, ~40 min for 5,380 sequential
    checks) — **1,545 of 5,380 CONFIRMED present on GCS** (real captured data with zero manifest registration — the
    actual scope of the visibility gap this pass exists to close; the mapping is at `recovery_register.tsv` in this
    session's scratchpad, regenerable by re-running the script). The other 3,835 candidates have no corresponding GCS
    object — correctly left untouched (nothing to register).
  - `[x] [SCRIPT] P2. Ship recover_tradfi_chain_manifest_registration_2026_07_22.py via quickmerge — mtds@c4cc819b1845f0c1a7f4546612f80229242fe265. Hit quickmerge's own documented untracked-file gotcha (`git
    diff
    origin/main`is blind to untracked files, silently early-exits "nothing to merge" without committing anything) — fixed by`git
    add`ing the file before invoking quickmerge, per the script's own inline comment.`
  - `[x] [DATA] P1. Run recover_tradfi_chain_manifest_registration_2026_07_22.py --apply (register phase) against the live tradfi manifest.`
    **Real, real bug caught by the real run, fixed, re-verified:** the FIRST `--apply` attempt CRASHED —
    `ValueError: ManifestWriter.add() with bundled data_type='options_chain' is banned; use record_captured_from_counts() instead`.
    The earlier design research (an Explore sub-agent) had concluded this ban could never fire for tradfi because
    `data_type` is always the OHLCV-granularity axis — **that conclusion was wrong for this corpus**: 1,412 of the 1,545
    confirmed candidates carry `data_type='options_chain'` literally (equal to `instrument_type`), which IS in UAC's
    `BUNDLED_DATA_TYPES` closed set. Verified nothing partially wrote before the crash (per-VM shard listing showed no
    new shard from the failed run — `ManifestWriter` buffers until `.flush()`, never reached). Fixed by branching
    `apply_register()`: `data_type in BUNDLED_DATA_TYPES` → `record_captured_from_counts()` (cluster-coverage gate,
    mirrors `rebuild_tradfi_manifest.py::_emit_bundled_shard_row`'s placeholder `row_count=1` /
    `expected_root_clusters=observed_clusters={root: 1}` pattern — no independent per-cluster SSOT exists for a
    manifest-registration reconstruction, same reasoning as that precedent); everything else → plain `add()`. Also fixed
    a second, smaller bug in the same pass: `pipeline_mode`/`source` were being read from the raw candidate row (which
    can be stale/blank — exactly the kind of legacy value this whole pass exists to route around) instead of freshly
    DERIVED via `_pipeline_mode()` + `source_string_for()`, matching the derive-don't-preserve convention every other
    script in this family already uses. Smoke-tested both write paths (bundled + non-bundled) on 4 real sample rows
    before the full run — all landed correctly (`capture_status=captured`, correct `pipeline_mode=batch_databento`/
    `source=databento`). Shipped the fix: `mtds@c8ace21dfeef294dc37d949264b1d373af55acca`. **Full apply run (re-used the
    already-confirmed 1,545-key TSV from the crashed run rather than re-paying the ~40-min GCS existence-check pass —
    the confirmed set hadn't gone stale in the ~15 minutes since)**: **1,545/1,545 rows written, 0 skipped.** Verified
    via the resulting per-VM shard (`_index/per_vm/local-22055-99dd.parquet`, downloaded + read directly): all 1,545
    rows `capture_status=captured`, `data_type` split 1,412 `options_chain` / 133 `ohlcv_1m` (matches the dry-run's own
    split exactly), all `venue=CME`, 32 distinct `underlying` roots. The consolidator will merge this per-VM shard into
    the canonical `_index/availability_index.parquet` on its next 60s cycle — not yet independently re-verified against
    the CONSOLIDATED index (do that before declaring the register phase fully done end-to-end).
  - `[x] [DATA] P1. Dry-run recover_tradfi_chain_manifest_registration_2026_07_22.py --retire (no --apply).` Fast (no
    GCS calls — purely a fresh manifest re-read + in-memory classification, ~10s): **50,520 raw rows now have a
    confirmed-registered canonical counterpart and would be retired.** Spot-checked the output TSV: candidates are
    exactly the expected shape (`ESH1`/`ESZ3`/`ESH6`/etc. — genuine per-contract Databento symbol values in the
    `underlying` field, the SAME class the register phase's `classify_databento_symbol` translation targets), nothing
    surprising. **`--apply` for retire is explicitly NOT run this session** — per direct operator instruction ("do NOT
    --apply retire without further review") and the plan's own standing caution: this is a single in-place-CAS REPLACE
    dropping 50,520 rows from the live production manifest in one shot, meaningfully larger in scope than the earlier
    112,839-row hygiene cleanup that turned out to have a wrong premise. Needs deliberate operator-visible review before
    ever applying, not a same-session rush.
  - `[x] [DATA] P1. Re-verify the register-phase rows landed in the CONSOLIDATED _index/availability_index.parquet — confirmed via a direct manifest query (venue=CME, underlying=AUD): the exact 2023-06-19/2023-06-21 options_chain rows the plan originally cited as sample evidence (real GCS data, zero manifest registration) now read capture_status=captured in the live consolidated index. Consolidator merge cycle already ran.`
  - `[x] ✅ [DATA] P1-OPERATOR-REVIEW. Retire-phase candidate list reviewed + APPLIED — DONE 2026-07-26 (operator go-ahead).`
    New launcher `tradfi-manifest-retire` (`deployment-service@ab8e0d7`): fresh dry-run (65,628 safe-to-retire, up from
    50,520), then `MODE=full` apply on VM `canonical-migration-tradfi-manifest-retire-20260726-160002`. Lost the CAS
    race vs the manifest consolidator's cron 6x (each safely aborted "UNCHANGED-SAFE", auto-retried), succeeded attempt
    7: **65,628 rows dropped in place** (generation 1785080389281002→1785080714940928, 5,824,751 remain) — exact match
    to the reviewed count. Pre-retire snapshot backed up to `_index/backups/` first.

    **Note 2026-08-07 (operator, via consolidated NA-blocker-digest audit)**:
    `tradfi_autonomous_session_operator_decisions_2026_07_25.md` item 2 re-asked whether to apply this exact
    retire-phase migration on 2026-08-07 (operator answered "agree, agent-executable: re-dry-run first, apply if
    materially unchanged") — that item was stale, this had already shipped 2026-07-26 as recorded above. The operator's
    2026-08-07 answer independently matches what was already done (fresh dry-run first, apply on an unchanged/larger
    list) — no further action needed, closing the loop by citation.

\*\*Remaining, in priority order for the next continuation: (1) re-verify the register-phase rows landed in the
consolidated index, (2) get operator review on the retire-phase candidate list before ever applying it, (3) finish the
CME monolith migration-tool build (P2, deferred), (4) Phase D gate (`data-pipeline-check-is` +
`data-pipeline-check-mtds`, tradfi, all shards — the terminal completion gate for this whole plan).

**Lesson — QG sentinel friction under heavy shared-host contention (2026-07-22 late session):** `unified-api-contracts`
was running under heavy multi-slot contention (12+ concurrent `quality-gates.sh` processes observed). Ran the FULL gate
twice (`bash scripts/quality-gates.sh`, no `--no-fix`), both printed `✅ ALL QUALITY GATES PASSED` with real test output
(194/194 and full-suite passes), but `.qg_last_passed_sha` never updated from its `Jul 21 04:42` value — grepped the
full saved output for `Sentinel written` / `SENTINEL_HIT` and found NEITHER string anywhere, meaning the sentinel -write
code path (`quality-gates-base/base-library.sh` ~line 1478, gated on `RUN_TESTS`/`RUN_LINT`/`!SKIP_TYPECHECK`/
`!ACT_MODE`/no `QG_SLICE`/no `QG_FAST`/`!_QG_SENTINEL_HIT`) silently did not fire despite the gate itself passing — root
cause not found before session-end (tried unsetting `QG_FAST`/`QG_SLICE`/etc in case of shell-state leakage, no change).
This is NOT evidence the code is unsafe (2 independent full green runs with real test execution is strong evidence) — it
blocked `quickmerge --agent`'s sentinel check specifically. **Do not assume a repo's QG tooling is reliable under heavy
concurrent load without checking** — if the sentinel doesn't update after a genuinely-passing gate, don't loop retrying
blindly; check the exact guard condition in `base-library.sh`/`base-service.sh` and/or wait for host contention to drop
before concluding it's a real blocker.

- `- [ ] [INFRA] P2. Diagnose why unified-api-contracts' full quality-gates.sh run (2026-07-22, under heavy host contention) printed ALL QUALITY GATES PASSED but never wrote .qg_last_passed_sha / .qg_content_sentinel — check the governor/contention-queue interaction with the sentinel-write guard in quality-gates-base/base-library.sh.`

### 2026-07-22 continuation — both pending ships landed, KRX backfill launched for real

- **Root cause of the QG-sentinel friction above was NOT purely contention — found and fixed a second, real bug.**
  Operator pushed back on the "not mine to fix" framing for the blocking `test_archetype_capability_manifest_parity.py`
  failures and said to file + fix it directly. Root-caused: `_find_codex_markdown()` was resolving the PM codex doc via
  `$UNIFIED_TRADING_WORKSPACE_ROOT` (the pre-per-slot-worktree machine-wide root checkout, stale at 16 days / missing 29
  archetype sections + the whole `Portfolio` family) **before** falling back to an ancestor-directory walk from
  `__file__` (which finds the caller's own live, current per-slot checkout). Fixed the resolution order — ancestor-walk
  first, env var only as a last-resort fallback for a genuinely isolated container with no sibling PM checkout. All 17
  tests in the file pass; zero doc content was actually missing (the live slot-1 checkout already had all 9 families /
  53 archetypes — this was purely a resolution-order bug). A duplicate issue doc already existed from slot-3 hitting the
  same root cause independently
  (`unified-trading-pm/plans/archive/issues/uac_archetype_codex_parity_test_reads_stale_root_checkout_2026_07_22.md`) —
  updated it to `status: resolved` with a Resolution section rather than filing a new one. **This explains why the "pure
  contention" framing in the Lesson above was incomplete**: some of the observed friction across ~6 gate attempts really
  was host contention, but every one of those attempts was ALSO going to fail regardless of contention level, because of
  this standing test bug — the two causes were confounded, not either/or.
  - Shipped: `uac@68c4c371d` — `_find_codex_markdown()` fix + the `ohlcv_1s` MVP-scope change (both files were bundled
    into one ship since both were quality-gates-verified together). `resolved_by:` stamped in the issue doc,
    `pm@0f03dd91d`.
- **KRX launcher shipped and launched for real.** `deployment-service` quickmerge raced another slot's concurrent push
  once (sentinel invalidated between gate-pass and quickmerge, same high-shared-repo-velocity pattern as all session) —
  re-ran the gate against the new HEAD (`9145ff89a`, fresh green, 66s) and quickmerged immediately on the retry, no
  further races. Code tarball refreshed (`create-code-tarballs.sh`, all 4 repos re-pinned including
  `unified-api-contracts@68c4c371dfea`). Ran `launch-tradfi-bf-krx-equities-ohlcv-24h.sh` for real (no `--dry-run`): all
  8 year-shard VMs (2019–2026) launched and confirmed `RUNNING`/SPOT in `asia-northeast1-c`
  (`tradfi-bf-krx-eq-ohlcv-24h-{2019..2026}-20260722-19*`). Not yet verified for actual row capture — check the manifest
  query in the launcher's own post-launch instructions (`gsutil cp .../availability_index.parquet` + groupby
  `venue==KRX, data_type==ohlcv_24h`) after the VMs have had time to run (Yahoo daily fetch across 3 tickers × up to 8
  years, should be fast — check within an hour, not immediately).
- **PA-2021 palladium backfill**: confirmed still `RUNNING` (`tradfi-bf-cme-ohlcv-1m-pa-2021-20260722-160825`, launched
  08:08Z), serial console shows steady ~60s-cadence `gsutil` heartbeat activity — alive, not stalled. Not yet confirmed
  complete.

---

**End of forked content.** For MVP universe / ground-truth-verdict context, Phase A2/C (adapter correctness,
data-status, honest-coverage) still tracked on the parent, and the full aggregated source-doc list, see
`tradfi_consolidated_closeout_2026_07_18.md`.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
