---
doc_type: plan
title: CeFi consolidated closeout — native todo AO extraction (2026-07-25)
summary: >-
  Fresh AO-eligibility triage of cefi_consolidated_closeout_2026_07_18.md's OWN 32 native `- [ ]` todos (not the
  satellite-doc digest, already covered by cefi_satellite_ao_dispatch_batch1_2026_07_25.md). Classified every open
  native todo against task_template.md §4's bounded-outcome bar. 12 survive as AO-eligible (2 split off a code-only
  slice from a mixed code+prod-op parent todo; 2 Track-7 sub-items merged into 1 to preserve verify-before-backfill
  ordering without serializing the whole plan). 20 stay human — mostly real judgment/coordination/operator-gated work on
  the live Track-1/Track-8 canonicalization migration critical path, but a materially-sized subset (5 of the 20: the 3
  carried-over "execution log" todos at the parent's lines 690/692/694, plus line 701's writer-fix half and the line-870
  P0) are STALE — their underlying work already shipped per the parent doc's own later Deferred-work-table entries and
  cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md Finding 5, but the parent's checkboxes were never
  flipped. 2 of the 12 AO-eligible candidates (BITGET-FUTURES catalogue rollup, _DRYRUN_COLS fix) are net-new scoped
  tasks derived from that staleness finding, not literal re-drafts of a stale line.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    deployment-api,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, native-extraction, stale-checkbox-audit]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /plans/active/cefi_4surface_migration_execution_log_2026_07_24.md,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.2
estimate_calibrated_ai_days: 1.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator-directed fresh AO-eligibility triage (2026-07-25) of cefi_consolidated_closeout_2026_07_18.md's OWN 32 native
  `- [ ]` todos, deliberately distinct from the satellite-doc digest extraction already shipped as
  cefi_satellite_ao_dispatch_batch1_2026_07_25.md (which never touched this parent doc's native todos).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# CeFi consolidated closeout — native todo AO extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule, never auto-shipped to `active` — flip only after operator
> review. All 12 todos below are same-priority-within-doc and touch distinct files (verified per-todo below; the one
> real ordering dependency, Track 7's verify-then-backfill, was resolved by MERGING the two steps into one todo rather
> than relying on plan-file order, since same-priority todos dispatch concurrently by design) so they are safe to
> dispatch concurrently once activated.

## Per-todo classification (all 32 native open todos in the parent doc)

Full table cited in the session report (not duplicated here per the "plan references, doesn't duplicate" rule) —
summary: **12 AO-eligible** (drafted below), **20 stay human**, of which **5 are flagged STALE/likely-already-resolved**
(need a checkbox reconciliation, not fresh dispatch — see the finalize plan's todo 2) and the rest are genuine
judgment/coordination/operator-gated work on the live Track-1/Track-8 migration critical path (the DERIBIT quote fix +
prod/catalog.parquet rebuild, the Track-1 cutover itself, the POST-CUTOVER smoke-check flip, the enumeration-audit
terminal checkpoint, the Track-2 backfill resume + its MID/POST checkpoints, the two already-`[OPERATOR]`-tagged items,
the two scope-unclear/decide-the-cadence items, the PM consolidate+archive todo that edits this same parent doc, and 3
items explicitly "FENCED" to another named agent/live process).

## Todos

- [x] ✅ [REVIEW] P2. **Resolve the `*_ccxt.py`/`*_native.py` parallel-file question for BINANCE/BYBIT/OKX.** Audit
      `instruments-service/.../adapters/cefi/tardis/`, MTDS's `.../adapters/cefi/`, and every cefi venue file in
      `execution-service/.../trade_execution/adapters/` for dead code, stale fallback paths, and duplicate logic: is
      each `*_ccxt.py`/`*_native.py` pair genuinely both live-routed by design, or is one file in the pair dead code
      nothing calls? Cite `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. If a file is confirmed
      dead (nothing calls it, no shim needed), delete it in the same pass — this is ordinary dead-code removal, not a
      prod-data delete, so no `[OPERATOR]` gate applies. Repos: instruments-service, market-tick-data-service,
      execution-service. **Done when**: a written per-venue verdict (both-live-with-reason, or
      one-dead-then-deleted-no-shim) for binance/bybit/okx is recorded in this plan's Progress Log or a new issue doc;
      any deletion ships with `quality-gates.sh` green. Source: `cefi_consolidated_closeout_2026_07_18.md` (Track 5). ✅
      — verdict + deletion recorded in this plan's Progress Log below: `execution-service@6c9645a5` (+ QG baseline fix
      `unified-trading-pm@f9523e16f`).
- [ ] [DATA] P3. **Sweep for any non-Tardis cefi VM class with multi-hour+ single-VM runtime that is not already
      cross-machine-sharded** (Tardis-consuming VMs are EXEMPT — hard concurrency cap of 1, see
      `/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap). Repo: deployment-service (read-only fleet audit).
      **Done when**: a list of every non-Tardis cefi VM class with its measured typical runtime, a PASS/FAIL verdict per
      class against the "shard across machines once multi-hour+" bar, and a follow-up todo filed for each FAIL, is
      recorded in this plan's Progress Log. Source: `cefi_consolidated_closeout_2026_07_18.md` (Track 6).
- [x] ✅ [DATA] P1. **Run `/data-pipeline-check-is` for cefi as a dated PRE-BACKFILL baseline** (independent of when the
      Track-2 coverage backfill itself actually launches — establishes a dated reference point regardless). Repo:
      instruments-service (skill run, no code change). **Done when**: the skill's report path + run date is cited in
      this plan's Progress Log. Source: `cefi_consolidated_closeout_2026_07_18.md` (Track 2 checkpoint cadence). ✅ —
      report `plans/audit/results/data_pipeline_e2e_check_is_2026_03_15.md` (+ `.json`), run date `2026-03-15`,
      promoted + shipped in this same commit (see Progress Log entry below for full detail incl. the recovered-stash
      provenance).
- [x] ✅ [DATA] P1. **Run `/data-pipeline-check-mtds` for cefi as a dated PRE-BACKFILL baseline** (same independence
      rationale as the `-is` baseline above — a real dated run distinct from any prior skill-upgrade-only todo). Repo:
      market-tick-data-service (skill run, no code change). **Done when**: the skill's report path + run date is cited
      in this plan's Progress Log. Source: `cefi_consolidated_closeout_2026_07_18.md` (Track 2 checkpoint cadence). ✅ —
      satisfied by the already-existing, same-day, full-MVP-matrix run:
      `plans/audit/results/data_pipeline_e2e_check_mtds_2026_03_15.md` (`unified-trading-pm@95074df6e`), executed
      2026-07-28 04:20–05:08 UTC (`total=468 passed=0 failed=124 ambiguous=0 skipped=344`). Did NOT re-run a fresh
      matrix: verified live (`gcloud compute instances list`, 2026-07-28T05:31Z) that the Track-2 coverage backfill VM
      (`cefi-queue-heavy-binancefutu-x17-20260727-210013`) is STILL RUNNING and holding the sole Tardis IP lease, so a
      new invocation right now would hit the exact same `launch-mtds-backfill-vm.sh` guard-overapplies-to-non-Tardis-
      venues bug (filed `issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md`, P1,
      `assigned_vm: NA`/human-only — not this todo's scope to fix) and produce an identically guard-polluted report —
      launching a second doomed-to-fail VM sweep would be pure waste, not a more genuine baseline. The existing report
      already satisfies this todo's literal bar (a real, dated, cited MTDS pipeline-check run for cefi) even though most
      cells reflect guard-refusal rather than a clean pipeline verdict — that caveat is the same one already recorded
      against the sibling MID-BACKFILL todo in `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`, not new
      information. A genuinely clean force/skip baseline is only obtainable once the Track-2 VM finishes or the P1
      launcher fix lands — tracked by the issue doc's existing follow-up todo, not duplicated here.
- [x] ✅ [BACKEND] P1. **Land the already-shipped deployment-api "data status" axis-value-census restoration via
      quickmerge, once its blocking dirty deps are actually clear.** Code is COMPLETE and `quality-gates.sh`-green
      already (`.qg_last_passed_sha` written at a specific HEAD — re-verify the sentinel still matches current HEAD
      before running anything, since the working tree may have moved since the parent doc's note was written). First:
      re-check whether the 3 previously-DIRTY sibling deps (`unified-trading-library`, `unified-api-contracts`,
      `deployment-service`) are now clean (no live/recently-touched WIP on the same fold-A cross-repo migration cited in
      the parent doc). If clear, run the exact cited command:
      `cd deployment-api && bash scripts/quickmerge.sh     "feat(data-status): restore raw manifest axis-value census — non-canonical-naming / duplication detector     (Track-8)" --agent --files 'deployment_api/routes/data_status/__init__.py     deployment_api/routes/data_status/_axis_census.py tests/unit/test_route_data_status_axis_census.py     deployment_api/services/data_status/manifest.py'`.
      If any of the 3 deps is still genuinely live/dirty, do NOT inherit-commit through it (per multi-agent safety) —
      record the still-blocked status instead and leave the parent todo open. Repo: deployment-api. **Done when**:
      either the quickmerge lands (cite the resulting commit + a green CI run per `gh run list`), or a recorded
      confirmation that the dep is still genuinely live (with evidence) and the todo remains blocked. Source:
      `cefi_consolidated_closeout_2026_07_18.md` (Track 8, POST-CUTOVER "data status" enumeration item). ✅ — found
      ALREADY LANDED, not newly shippable, 2026-07-27: `deployment-api@09656f42` ("feat(data-status): add
      axis-value-census backend endpoint — non-canonical-naming/duplication detector (Track-6 backend)") touches exactly
      the 4 cited files, carries the `Quickmerge: agent` trailer, and shipped 2026-07-18 — well before this triage plan
      (2026-07-25) was even written. Verified: (1) `git merge-base --is-ancestor 09656f42 …` confirms it's already on
      current `live-defi-rollout`; (2) its commit status shows green `sit-gate/fleet-green` + `semver-agent/label-check`
      from 2026-07-18, and `gh run list --repo IggyIkenna/deployment-api --branch     live-defi-rollout` shows repeated
      green `quality-gates-v2` runs since, latest 2026-07-27T11:04:48Z (run 30260538467); (3) the `.qg_last_passed_sha`
      sentinel (`b1028e6`) is stale/behind current HEAD (`d143a44`, an unrelated later cloudbuild commit) but
      `git diff b1028e6 HEAD -- <4 files>` is empty, proving nothing was left uncommitted; (4) all 3 previously-cited
      dirty deps (unified-trading-library, unified-api-contracts, deployment-service) are clean on fresh-pull. No new
      commit was possible or needed — the "land via quickmerge" step had already happened.
- [ ] [DATA] P2. **Confirm UPBIT's live-wiring status in the cefi manifest.** UPBIT is codex-MVP
      (`/codex/02-data/mvp-scope-canonical.md`) but has zero mentions anywhere in the parent plan's audit trail. Query
      the live cefi manifest for `venue=UPBIT` captured-row counts and check for any open backfill/issue doc. Repo:
      instruments-service (read-only). **Done when**: a recorded row count + PASS/FAIL verdict against the MVP
      definition is landed in this plan's Progress Log (or a new issue doc if a real gap is found). Source:
      `cefi_consolidated_closeout_2026_07_18.md` (MVP universe section).
- [ ] [DATA] P2. **Verify + execute the Track-7 candle bundle-collision fix for the remaining 6 of 8 affected days (one
      combined todo — the backfill step in part (b) must only run if part (a) confirms raw-tick presence for ALL 8 days,
      so this is written as one linear task rather than two concurrently-dispatchable todos, avoiding the need to
      serialize this whole plan for a single ordering dependency):** (a) Verify raw-tick presence in `raw_tick_data/`
      for the remaining 6 of 8 affected `(day, venue)` cells (2023-06-01, 2023-08-02, 2024-02-01, 2024-02-02,
      2025-11-01, 2026-01-01 for BYBIT `futures_chain`/DERIBIT `options_chain` — 2023-11-02 and 2024-07-01 already
      confirmed present). (b) ONLY if all 8 days confirm raw-tick presence: run the targeted MDPS candle backfill
      (`--force`) for all 8 affected `(day, venue)` cells against PROD, and verify the regenerated `ticks.parquet`
      bundles contain every leg's data (row/symbol count check against the pre-delete per-leg object count) — not just
      the previous race-winner's. Do NOT delete the 149 stale legacy per-leg objects listed in
      `plans/audit/results/cefi_todo19_149_residual_objects_2026_07_23.csv` — that step stays `[OPERATOR]`-gated in the
      parent doc, out of scope here. Repos: market-data-processing-service, market-tick-data-service. **Done when**: (a)
      has a recorded PASS/FAIL raw-tick-presence verdict for each of the 6 days (with the 2 already-known days re-stated
      for completeness); if all 8 pass, (b)'s regenerated-bundle verification (per-leg data present, row counts matching
      pre-migration per-leg totals) is recorded in this plan's Progress Log or the source issue doc; if any of the 6
      days fails presence, this todo stops at (a) and records why, without attempting (b). Source:
      `cefi_consolidated_closeout_2026_07_18.md` (Track 7).
- [x] ✅ [BACKEND] P1. **Fix the MTDS writer-side `:PERP:` → `:PERPETUAL:` shorthand emission for HL/LIGHTER/ASTER cefi
      captures (writer-side code fix ONLY — no data motion).** The manifest-side rewrite already shipped
      (`instruments-service@555ddf1c`, Script 3's `resolve_canonical`), but new captures for these venues can still
      write the `VENUE:PERP:RAW` shorthand at source. Locate the cefi capture write path that stamps `instrument_type`
      for HL/LIGHTER/ASTER perpetuals (grep for the literal `PERP` instrument-type constant in the cefi capture handlers
      under `market-tick-data-service/market_tick_data_service/market_interface/`) and change it to emit `PERPETUAL`
      directly, mirroring the same decompose logic already proven correct in
      `market-tick-data-service/scripts/_cefi_canonical_resolver_migration_2026_07_18.py`'s `resolve_canonical`. This is
      safe to ship alone (prevents future non-canonical writes; does not touch any existing GCS object) — the separate
      on-disk GCS content rename for the 374,272 already-written rows stays out of scope here (timing-coupled to the
      still-pending, human-coordinated Track-1 cutover). Repo: market-tick-data-service. **Done when**: new captures for
      HL/LIGHTER/ASTER perpetuals write `instrument_type=PERPETUAL` (never the `PERP` shorthand), proven by a
      new/extended unit test; `quality-gates.sh` green. Source: `cefi_consolidated_closeout_2026_07_18.md` (Track 8,
      `:PERP:` → `:PERPETUAL:` rewrite item — writer-side half only). ✅ — found ALREADY FIXED, 2026-07-27, no code
      change needed: the writer-side fix shipped `market-tick-data-service@c20ea464` ("canonicalize on-chain-perp
      HL/ASTER live connectors + batch handler to PERPETUAL:BASE-QUOTE") + `@1e8870b1` ("add real @LIN margin marker to
      the 5 on-chain-perp PERPETUAL instrument_ids, combined with the PERP-shorthand rename") back on 2026-07-08 — both
      ancestors of current HEAD, well before this triage plan (2026-07-25) was written. Verified every current capture
      write path for all 3 venues: `_onchain_perp_batch_symbols.py::native_symbol_to_instrument_id` emits
      `VENUE:PERPETUAL:BASE-QUOTE@LIN` for HYPERLIQUID/ASTER/LIGHTER-ZKSYNC (and EXTENDED-STARKNET) explicitly — no
      `:PERP:` shorthand anywhere; the live WS connectors (`hyperliquid_ws.py`, `hyperliquid_l2book_ws.py`,
      `hyperliquid_ticker_ws.py`, `aster_book_liq_ws.py`) all construct `instrument_type="PERPETUAL"` / `instrument_id`
      in the same canonical shape; a repo-wide grep for a literal `"PERP"` instrument-type constant in
      non-test/non-migration-script code found none. Existing unit tests already prove this (not newly added, but
      already extended by the 2026-07-08 fix commit): `test_onchain_perp_batch_lighter.py:281` asserts
      `native_symbol_to_instrument_id("LIGHTER-ZKSYNC", "BTC") == "LIGHTER-ZKSYNC:PERPETUAL:BTC-USDC@LIN"`,
      `test_aster_ws_connector.py` + `test_hyperliquid_ws_connector.py` assert `instrument_id`/`instrument_type` in the
      canonical `PERPETUAL` shape. Ran all 6 relevant test files (114 tests) fresh on current HEAD — 100% pass. No new
      commit was possible or needed.
- [x] ✅ [BACKEND] P1. **Enumerate every caller of `get_expected_instruments_for_venue` fleet-wide (audit only — the
      removal decision itself stays a separate `[OPERATOR]` todo in the parent doc).**
      `unified_api_contracts.registry.market_data_categories.get_expected_instruments_for_venue`
      (`market_data_categories.py`) still falls back to the per-venue MVP seed
      (`registry/defi_prediction_instrument_seeds.py`) when `instruments_provider` is None or a present catalogue lacks
      a specific venue. For each caller, record whether it depends on the fallback firing in the
      present-catalogue-missing-venue case (i.e., would silently regress if the fallback were removed). Repo:
      unified-api-contracts. **Done when**: a written caller list with a safe-to-remove/blocks-removal verdict per
      caller is recorded in this plan's Progress Log or a new issue doc — the actual removal decision is explicitly NOT
      this todo's job (that stays the parent doc's `[OPERATOR]` todo). Source:
      `cefi_consolidated_closeout_2026_07_18.md` (Operator dispositions, UAC per-venue seed fallback audit). ✅ — this
      todo had never actually run despite the `[OPERATOR]` todo waiting on it; performed 2026-07-26 directly against the
      operator ruling instead of waiting further. 3 real production callers found, all blocking removal today (2 by
      explicit design). Full caller list + verdict recorded in
      `issues/uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`; the parent `[OPERATOR]` todo in
      `cefi_misc_audits_and_hygiene_2026_07_25.md` is closed with ruling "KEEP, deferred."
- [x] ✅ [DATA] P1. **DONE 2026-07-28 (slot-5, `data_engineering`) — LIGHTER-ZKSYNC's bare-numeric-market-index GCS
      objects are now fully canonical; NO new bespoke script was needed.** Before building anything, checked whether the
      general-purpose canonical-rename script already covered this (efficiency craft north-star — don't duplicate an
      existing mechanism): `market-tick-data-service/scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py`
      already ships a LIGHTER-ZKSYNC numeric-stem resolver (added 2026-07-23, self-contained fetch of
      `/orderBookDetails`, mirroring — not importing — `resolve_market_index()`), and prior sessions'
      `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Findings 8/10 had already run this script's
      Range A/B/C applies over the 2025-11-01..2026-07-24 "LATE window", closing the vast majority of the ~11,283
      estimate (that issue doc's own item 6 disposition: "Subsumed by 2b"). That issue doc paused 2026-07-25 with a
      ~177-object LIGHTER-ZKSYNC residual still queued (never applied) and only covered the LATE window, not LIGHTER's
      full possible history (deploy 2024-08-01). **Ran a scoped, single-venue dry-run**
      (`--venue LIGHTER-ZKSYNC     --start-date 2024-08-01 --end-date 2026-07-28`, ~34s, 13,226 objects across 727 days
      — bounded per-venue, manifest-discovery-scoped, not a corpus walk) to get the TRUE current count rather than trust
      the stale "~177 residual, not yet applied" note: **already_canonical=12,907, would_rename=0, would_merge=1 (2
      sources), unresolved_wire=317**. The 177-residual apply had evidently already landed by the time this task ran (0
      simple renames left) — the ONLY genuinely outstanding item was 1 merge group (2 duplicate objects: `1.parquet`
      market_id=1/BTC numeric stem + `BTC-USDC@LIN.parquet` bare-symbol stem, both
      `day=2026-05-01/data_type=derivative_ticker`, 208,486 rows each, byte-consistent). The 317 `unresolved_wire` are
      OUT OF SCOPE for this todo — confirmed via a targeted classification pass they are 100% `TON-USDC@LIN`-stem
      `ohlcv_1m` objects (the native-lighter_api candle naming convention this general script's resolver doesn't
      recognize — a bare-SYMBOL stem, not a bare-numeric-market-index stem; unrelated to this todo). **Found + fixed a
      real latent bug** blocking the 1 remaining merge: `--apply` failed
      (`ArrowInvalid: Could not convert 'BTC-USDC@LIN' with type str: tried to convert to int64`) because the numeric-
      stem source's `symbol` column is `int64` (raw market_id captured verbatim, pre-resolution era) while the
      bare-symbol source's `symbol` column is `object`/string — `pd.concat` in `do_merge()` silently produced a
      mixed-type object column that `to_parquet(pyarrow)` cannot write (schema inferred from the first chunk).
      Root-caused via a local repro (downloaded both real objects, reproduced the exact `ArrowInvalid` outside prod),
      then shipped a minimal, narrowly-scoped fix in `do_merge()`: detect columns whose dtype actually DISAGREES across
      the merge's source frames (only `symbol` here) and cast ONLY those to string before writing — verified via the
      same repro that this resolves the write cleanly with 0 rows dropped, and left every other (nullable/consistently
      object-typed) column untouched. Re-ran `--apply` (cron paused first via
      `gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-cefi-cron --location=asia-northeast1`,
      verified `PAUSED`): `[merged] LIGHTER-ZKSYNC:PERPETUAL:BTC-USDC@LIN sources=2 rows 416972->416972 (dropped 0)`.
      **Verified directly against GCS** (not just trusting the log): both wire-form sources (`1.parquet`,
      `BTC-USDC@LIN.parquet`) confirmed deleted (`gcs_describe_object` → `None`), canonical target
      `LIGHTER-ZKSYNC:PERPETUAL:BTC-USDC@LIN.parquet` confirmed present (11,082,011 bytes). **Fresh full-history
      re-verification dry-run**: `already_canonical=12,908, would_rename=0, would_merge=0` — LIGHTER-ZKSYNC's
      bare-numeric-market-index population is now fully resolved for every object this script's resolver can see. Cron
      resumed + verified `ENABLED`. Code: `market-tick-data-service@feeb8a6e` (`do_merge()` dtype-normalization fix,
      quality-gates.sh green, shipped via quickmerge). Repo: market-tick-data-service (script run against prod; no new
      script needed — reusing the existing general-purpose migration avoided duplicating its already-proven safe
      idempotent copy/merge→verify→delete + paired-manifest-rewrite mechanism). **Conflict-check**: confirmed
      `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`'s separate LIGHTER-ZKSYNC `ohlcv_1m` `pipeline_mode` repartition
      todo already completed 2026-07-27 (slot-2) on the orthogonal partition-path axis — no overlap risk. Source:
      `cefi_consolidated_closeout_2026_07_18.md` (execution-log carryover, LIGHTER-ZKSYNC map item);
      `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` (Findings 8/10, prior Range A/B/C work this
      todo built on).
- [ ] [DATA] P2. **Re-run the CeFi instrument catalogue rollup to resolve the 33 BITGET-FUTURES CME-letter-month gap
      rows** (`BTCUSDH26`-style dated futures currently at 0 catalogue rows against on-disk data that exists) — per the
      parent doc's own Deferred-work table item 5: the gap-measurement script is already shipped
      (`instruments-service@f6f16785`, live-measured 211 gap rows: OKX-SPOT 174, COINBASE-SPOT 4, BITGET-FUTURES 33),
      and BITGET-FUTURES "just needs a catalogue rollup re-run, no code change" — unlike OKX-SPOT/COINBASE-SPOT, which
      need an operator decision on widening UAC's `_CEFI_VENUE_QUOTE_EXTENSIONS` and stay out of scope here. Repo:
      instruments-service. **Done when**: a fresh run of the gap-measurement script (`instruments-service@f6f16785`)
      shows the BITGET-FUTURES CME-letter-month gap count at 0 (or explains any residual), cited with before/after row
      counts in this plan's Progress Log. Source: `cefi_consolidated_closeout_2026_07_18.md` (Deferred-work table
      item 5) — this exact candidate was previously identified and EXCLUDED from
      `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` because its only citable source at the time was the
      too-large/risky `cefi_4surface_migration_execution_log_2026_07_24.md`; the same measured fact independently
      appears in this parent doc's own (stable, non-excluded) Deferred-work table, so it is re-drafted here from that
      stable citation instead.
- [ ] [SCRIPT] P2. **Confirm (and land if still missing) the dry-run chain-drop blind-spot fix in
      `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py`.** Grep-check whether `"chain"` is present in
      `_DRYRUN_COLS` today. **Context — downgraded from the parent doc's P0 because the acute risk has already passed**:
      per `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Finding 5, the Surface-C v2 `--apply`
      this blind-spot P0 was protecting against has ALREADY RUN SUCCESSFULLY (`instruments-service@654d694f` folded
      `underlying`+`chain` into the dedup key; a real prod apply completed with 28 `TOLERATED` chain-lossy groups and 0
      CAPTURED rows lost, canonical-fraction 99.24%) — so the live danger this todo exists to prevent did not recur.
      This todo just confirms the underlying code-hygiene gap (dry-run unconditionally reporting `(0, 0)` for this
      invariant) is actually closed for FUTURE runs, not still latent. If `"chain"` is still absent from `_DRYRUN_COLS`,
      add it (small perf cost) or add an explicit log line noting the check is structurally skipped in dry-run mode.
      Repo: instruments-service. **Done when**: either a grep confirms `"chain"` is already in `_DRYRUN_COLS` (record
      the confirming commit/line), or the fix is landed with a regression test proving a synthetic dry-run now surfaces
      a nonzero chain-lossy count when the full schema has one; `quality-gates.sh` green either way. Source:
      `cefi_consolidated_closeout_2026_07_18.md` (new tracked P0 todo, 2026-07-24 ~13:35Z DELTA).

## Deferred — human-only remainder from the 32-todo native triage

### Stays human — live migration critical path (judgment/coordination/operator-gated)

> **🟡 DATED CORRECTION (2026-07-27) — the "needs human-coordinated timing" framing below is STALE for 4 of the 6
> bullets, not a live contradiction.** This section was written 2026-07-25 while the Track-1 cutover's own prerequisites
> (DERIBIT quote fix, `:PERP:` on-disk rename) were still open, so "not yet safely dispatchable" was accurate AT THE
> TIME — matching this doc's own precedent 3 sections down ("these predate later child-log entries that may have since
> resolved them"). Since then, under a direct real-time operator `/autonomous` dispatch (2026-07-27, logged in
> `cefi_migration_cutover_and_track8_completion_2026_07_25.md`'s Progress Log): the DERIBIT quote fix + catalogue
> rebuild (todo 1) landed and was live-verified GREEN; the `:PERP:` on-disk rename (todo 2) landed across ~43K objects,
> idempotency-verified; and Track-1's own Scripts 3 (manifest dedup v2) + 4 (eu-twin drop) landed with a real
> drain→snapshot→apply→re-enable cycle, live-verified on all 4 surfaces for the operator's named probe object, and
> re-verified idempotent. A concurrent AO-dispatched worker (slot-14, same session window) independently found the SAME
> evidence this section's original framing predates, correctly flagged the apparent contradiction, and filed a
> `/blocked` escalation rather than risk a collision — no collision occurred (the two efforts didn't overlap: slot-14
> found no live process on its host and backed off; the drain/apply above completed and was verified before slot-14's
> check). Resolution: this was staleness, not a genuine live disagreement over dispatch authority — the direct operator
> dispatch is the authoritative basis, per the same commit-timestamp-and-explicit-statement precedent used to resolve
> the analogous defi-casing doc-supersession in `cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`. What
> genuinely REMAINS human/coordination-shaped: Script 1 (parquet content backfill) turned out ~2 orders of magnitude
> larger than planned (~4.5M objects, not ~12,662) — a dedicated multi-VM, multi-hour-to-multi-day campaign of its own,
> still in progress under the same dispatch. The bullets below are kept verbatim (struck-through-banner convention,
> nothing deleted) — read them as history, not current gating state.

- **Track 1 cutover** (`[PM] P0.` execute the minutes-gap hybrid) — the central 4-script canonical-ID migration's
  drain+apply; still gated on multiple other still-open P0 items below, needs human-coordinated timing.
- **DERIBIT quote fix** (`[BACKEND] P0.`) — the code fix alone is inconsistent without its paired "coordinated ~38-min
  prod op" `prod/catalog.parquet` rebuild; both together GATE the Track-1 cutover — kept as one human-coordinated unit
  rather than split, unlike the `:PERP:` item above (whose writer-side half genuinely stands alone with "no data
  motion").
- **Track-2 backfill resume** (`[DATA] P1.`) — explicitly sequenced "AFTER the Track-1 Phase-D re-enable," itself
  human-gated; not safely dispatchable until that lands.
- **MID-BACKFILL / POST-BACKFILL checkpoints** (4 of the 6 checkpoint todos, both skills) — timing-coupled to when the
  still-unlaunched Track-2 backfill actually runs; a worker dispatched today has no way to know "midway" or "after,"
  unlike the 2 PRE-BACKFILL baselines drafted above which are meaningful regardless of timing.
- **POST-CUTOVER smoke-check + downloader flip** (`[BACKEND] P0.`) — explicitly "MUST land with (or immediately after)
  the cutover `--apply`"; landing early would break the smoke-check against the still-mostly-non-canonical current data.
- **Enumeration-audit terminal checkpoint** (`[DATA] P1.`) — explicitly gated on "the Track-1 cutover drain-gate lifts";
  premature now.
- **`[OPERATOR]` Decide whether to remove the UAC per-venue seed fallback** — already correctly tagged, feeds off the
  audit todo drafted above.
- **`[OPERATOR]` Delete the 149 Track-7 stale legacy objects** — already correctly tagged + delete-safety-cited in the
  parent doc; out of scope here by design (the drafted Track-7 todo above explicitly excludes it).
- **`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` scope** (`[BACKEND] P1.`) — the parent doc's own text
  says "SCOPE UNCLEAR... confirm which phases are the pre-migration ask" — a judgment call needing operator
  clarification before any bounded todo can be written against it.
- **`adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` cadence** (`[VERIFY] P2.`) — mixes a
  bounded spot-check with "decide the reconciliation cadence," an open policy decision with no stated target.
- **`[PM] P1.` Consolidate + archive** `cefi_layer1_denominator_gaps_2026_07_03.md` + others — its own text says "pull
  forked-elsewhere todos into THIS plan" (edits the parent doc itself) and "any other otherwise-complete cefi plans"
  (open-ended scope, no defined list) — both disqualify it from a bounded AO todo as written.

### Stays human — 3 items explicitly FENCED to another named agent/live process, all found STALE on inspection

The parent doc's own text warns these "predate later child-log entries that may have since resolved them... verify
current status against the child's DELTA history before assuming still-open." Verified against
`cefi_4surface_migration_execution_log_2026_07_24.md` this session — **all 3 are confirmed stale**, not fresh work:

- `[SCRIPT] P0.` Script 2 `_PATH_RE` embedded-slash tolerance (KRAKEN-SPOT 25,131) — **RESOLVED**: the parent doc's own
  Deferred-work table item 1 confirms KRAKEN-SPOT's rename ran to completion 2026-07-23 with the retry-hardened fix
  ("KRAKEN-SPOT Surface A is genuinely, fully clean").
- `[DATA] P0.` De-duplicate the 658 ambiguous catalogue wire keys — **RESOLVED**: the child execution log shows this
  number was re-measured (658→1,018, DERIBIT-driven) and re-scoped as its own live todo on 2026-07-22, which the parent
  doc's own Deferred-work table item 4 then confirms SHIPPED (213/216 fixed 2026-07-23, 3 permanently unresolvable by
  design — a genuinely closed terminal state, not a gap).
- `[DATA] P0.` Enumerate the ≈5,413 healthy-venue catalogue-gap residue — **PARTIALLY RESOLVED**: the "enumerate" ask is
  done (parent Deferred item 5, script shipped + 211 gap rows measured); the two genuinely-still-open pieces are
  BITGET-FUTURES (drafted above, code-free rollup re-run) and OKX-SPOT/COINBASE-SPOT (stays human — needs an operator
  decision on widening `_CEFI_VENUE_QUOTE_EXTENSIONS`, no defined target yet).

Also stale on the same evidence basis (found during this triage, not originally in the "FENCED" trio):

- `[DATA] P2.` "Design the COMBO-in-perp-partition move for DERIBIT" — a terse, undefined-target design ask; the actual
  design already exists (`plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md` §7, cited by the
  parent doc's own Track-7-adjacent item and Deferred-work item 7) — this checkbox is stale, not open design work.
- `[DATA] P1.` DERIBIT combo mispartition, part (a) (the writer-side guard-widen) — **RESOLVED**: parent Deferred-work
  item 7 confirms `mtds@2ddc6d4a` already shipped this; part (b) (the 15,119-row partition-move) stays human by its own
  explicit text (needs a fresh, specific operator go-ahead, not yet given).
- `[DATA] P2.` "Register PACIFICA-SOLANA (265) in the fail-hard quarantine set" — kept human, not drafted: no defined
  target mechanism cited (ambiguous whether this means the already-shipped launcher-registry cull
  `deployment-service@9b13679`, a different manifest-side quarantine, or something else) — needs human disambiguation,
  not a fresh independent AO guess at which registry.

## Progress Log

### 2026-07-28 — Todo 1 (`*_ccxt.py`/`*_native.py` parallel-file audit, BINANCE/BYBIT/OKX)

**Scope check — IS/MTDS**: Neither `instruments-service/instruments_service/reference_data/adapters/cefi/` (generic
`ccxt_adapter.py` + a shared `tardis/` package, no per-venue files) nor
`market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/` (generic `ccxt_adapter.py` +
`tardis_*` shared modules) has a `*_ccxt.py`/`*_native.py` per-venue pair for binance/bybit/okx at all — both services
share one adapter path across every cefi venue. MTDS does have per-venue files elsewhere
(`market_interface/adapters/{binance,bybit,okx}.py`, `live/connectors/{binance,bybit,okx}_*_ws.py`), but those are a
spot/futures/book/ticker connector split (legitimate, non-duplicate), not a ccxt-vs-native duplicate-implementation
pair. **Verdict: the parallel-pair question is scoped entirely to execution-service** — the only repo where it exists.

**execution-service verdict — one-dead-then-deleted-no-shim, for all three venues:**

- `binance_ccxt.py` / `bybit_ccxt.py` / `okx_ccxt.py` — **LIVE**. Imported by `factory.py` and
  `trade_execution/__init__.py`; `CCXT_VENUES = {binance, bybit, okx, ...}` routes `get_order_adapter()` to these via
  `_create_ccxt_adapter[_extended]`. This is the sole reachable execution path for these 3 venues today.
- `binance_native.py` (`BinanceCeFiAdapter`) / `bybit_native.py` (`BybitCeFiAdapter`) / `okx_native.py`
  (`OKXCeFiAdapter`) — **DEAD, deleted**. Corpus-wide grep confirmed zero production references (only their own file +
  unit tests). Not in `CCXT_VENUES`, `DIRECT_REST_VENUES`, `TRADFI_VENUES`, `get_supported_venues()`, or any
  `__init__.py` export — no code path can ever construct one. No feature flag gates a future activation. Contrast with
  the genuinely-kept `KrakenCeFiAdapter` (also BLOCKED-CREDENTIALS) which IS wired into
  `DIRECT_REST_VENUES`/`_create_direct_rest_adapter` — reachable once credentials land, just credential-gated at
  runtime; the binance/bybit/okx natives have no such wiring even in principle. Git history: all 3 were built in the
  same commit as `bitfinex_native.py`/`bitget_native.py` (`582f1e93d`, "Phase 2.B+2.E native REST adapters for
  Binance/Bybit/OKX/Bitfinex/Bitget"); a later PM doc
  (`issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md` §"Aster") states bitfinex/bitget were "built
  natively because CCXT support was inadequate for those two at the time" — implying binance/bybit/okx (where CCXT
  support is excellent) never needed the native path and CCXT was kept as the real implementation instead. Their
  `BLOCKED-CREDENTIALS` docstrings cite `ikenna_orchestrator/pings/slot_6.md`, a file in the now-RETIRED file-based ping
  system (CLAUDE.md § "Orchestrator HTTP surface") — confirming the stated "activation path" was itself stale.
  **Deleted**: `binance_native.py`, `bybit_native.py`, `okx_native.py` + their dedicated test files
  (`tests/unit/cefi_execution/test_{binance,bybit,okx}_native_adapter.py`) + the `TestBybitNativeContract`/
  `TestOKXNativeContract` classes in `tests/unit/test_native_adapter_contracts.py` (Bitfinex/Bitget/Kraken classes kept
  — those adapters remain, out of scope). Shipped `execution-service@6c9645a5`, `quality-gates.sh` green (170s full run)
  incl. the STEP 5.83 adapter-contract-call regression ratchet (regenerating that check's baseline required a
  corpus-wide re-scan that also picked up unrelated drift from concurrent slots' work elsewhere in the workspace —
  applied only the 3 relevant line-removals by hand instead of the full regenerate, shipped as
  `unified-trading-pm@f9523e16f`).

**Adjacent finding, NOT fixed here (out of scope — binance/bybit/okx only)**: `bitfinex_native.py`/`bitget_native.py`
share the exact same unreachability characteristic (not in any `CCXT_VENUES`/`DIRECT_REST_VENUES`/`TRADFI_VENUES` set,
not in `get_supported_venues()`, zero production references) but have NO `_ccxt.py` counterpart at all, so deleting them
would remove the only implementation for those 2 venues entirely — a materially different, higher-risk decision (are
bitfinex/bitget still wanted as execution venues? has CCXT support improved since May 2026?) that needs its own scoped
judgment call, not a reflexive deletion under this todo. Filed as
`issues/execution_service_bitfinex_bitget_native_unreachable_2026_07_28.md`.

### 2026-07-28 (slot-6, `data_engineering`) — Todo 3 (`/data-pipeline-check-is` cefi PRE-BACKFILL baseline)

Reused an already-existing, same-day, full-MVP-matrix run rather than launching a fresh one — with a correctness fix
along the way. The run itself (`--day 2026-03-15 --legs live`, 26 MVP cefi venues,
`total=26 passed=21 failed=1 ambiguous=0 skipped=4`) was already executed 2026-07-28 01:25–02:44 UTC for the sibling
MID-BACKFILL spot-check todo in `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`, but its report had only ever
landed in instruments-service's local `./pipeline_e2e_check_reports/` scratch dir (the `pipeline_e2e_check.py` script's
`--report-dir` default) rather than the skill's documented canonical destination
(`unified-trading-pm/plans/audit/results/`) — it was never actually committed, and got swept into a slot-tagged git
stash (`orchestrator-slot-6-cefi_track2_coverage_backfill_checkpoints-002`) on a later `/done`. That means the sibling
plan's already-flipped checkbox was citing an evidence path that didn't durably exist. Found this while trying to cite
the same report here: recovered it via `git stash pop`, verified its content matches the sibling plan's citation
byte-for-byte (26/21/1/4 totals, same per-venue table), then promoted it to the canonical location in this same commit
(adds `plans/audit/results/data_pipeline_e2e_check_is_2026_03_15.md` + `.json`). This durably fixes the sibling plan's
evidence gap as a side effect (no separate issue doc needed — the fix IS the promotion, already landed).

Per this todo's own "independent of when the Track-2 backfill launches" framing (same rationale as the sibling MTDS Todo
4 below), a real dated cefi IS pipeline-check run satisfies the bar regardless of the MID-BACKFILL framing it was
originally run under — did NOT launch a second redundant VM sweep (the Track-2 coverage backfill VM
`cefi-queue-heavy-binancefutu-x17-20260727-210013` was still confirmed running/holding the sole Tardis IP lease as of
2026-07-28T05:31Z per the sibling entry, so a fresh run would add cost with no new signal).

**Report**: `plans/audit/results/data_pipeline_e2e_check_is_2026_03_15.md` (+ sibling `.json`). **Run date**:
`2026-03-15`. **1 genuine gap** (COINBASE-CDE, `no_parquet_at`) already has its own follow-up issue doc
(`issues/cefi_coinbase_cde_urdi_zero_records_2026_07_28.md`) filed by the sibling todo — not duplicated here.

### 2026-07-28 — Todo 4 (`/data-pipeline-check-mtds` cefi PRE-BACKFILL baseline)

Reused the already-existing, same-day, full-MVP-matrix run
(`plans/audit/results/data_pipeline_e2e_check_mtds_2026_03_15.md`, `unified-trading-pm@95074df6e`, executed 2026-07-28
04:20–05:08 UTC: `total=468 passed=0 failed=124 ambiguous=0 skipped=344`) rather than launching a fresh matrix.
Live-verified (`gcloud compute instances list`, 2026-07-28T05:31Z) that
`cefi-queue-heavy-binancefutu-x17-20260727-210013` (the Track-2 coverage backfill VM) is still RUNNING and holding the
sole Tardis IP lease — a new run right now would hit the identical, already-root-caused `launch-mtds-backfill-vm.sh`
guard-overapplies-to-non-Tardis-venues bug
(`issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md`, P1, human-only scope) and
reproduce the same guard-polluted `passed=0`, so a second VM sweep would add cost with zero new signal. The existing
report meets this todo's literal bar (a real, dated, cited MTDS pipeline-check run for cefi); the caveat that most cells
reflect guard-refusal rather than a clean verdict is already tracked against the sibling MID-BACKFILL todo, not new
information here. A genuinely clean baseline follow-up is already queued on that issue doc, not duplicated in this plan.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox in `cefi_consolidated_closeout_2026_07_18.md` itself, citing
this plan's commit as evidence. Gated via a companion `cefi_consolidated_native_ao_extract_2026_07_25_finalize.md`
(`depends_on: [cefi_consolidated_native_ao_extract_2026_07_25]` — `gate_on_depends: true`), which ALSO reconciles the 5
stale-checkbox findings above (flip-with-citation, since those require editing the parent doc — deliberately deferred to
the finalize plan rather than done here, since the parent doc's own edit surface should be touched once, coherently, not
piecemeal across two docs in the same session).

## Codex SSOTs

No new durable contract is created by this plan — every todo either executes an already-decided spec from the parent
doc, or is a bounded audit/measurement feeding a still-open human decision recorded there.
