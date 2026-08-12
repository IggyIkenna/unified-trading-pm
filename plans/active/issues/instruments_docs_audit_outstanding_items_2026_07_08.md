---
doc_type: issue
title:
  Instruments-service docs audit (2026-07-08) — consolidated outstanding items across all 7 asset docs, with
  code-verified evidence and fix options
summary: |
  A docs-cleanup pass over the 7 instruments-service asset docs (ADAPTER_ARCHITECTURE, CEFI, DEFI, PREDICTION,
  SETUP_GUIDE, SPORTS, TRADFI) stripped audit-trail narration and, for every "outstanding" claim in those docs,
  VERIFIED it against live code. This doc is the consolidated tracker of everything that survived verification as
  genuinely-still-open — every item, no matter how light — with file:line evidence, a root cause, and concrete fix
  options. Items that already have a dedicated issue doc / plan are cross-referenced (this doc is an index for those and
  the SSOT for the rest). A closing appendix records the items that verification proved ALREADY FIXED (removed from the
  docs, not carried forward). Two items whose root cause the docs left unpinned — Sports league_id="UNKNOWN" (2,373
  rows) and the missing `sports-odds-ready` publisher — were re-investigated this session; their traced root cause is
  in-line below.
status: open
nature: notes
asset_group: [cefi, defi, sports, prediction, tradfi]
stage: [data]
repos:
  [
    instruments-service,
    unified-api-contracts,
    market-tick-data-service,
    execution-service,
    strategy-service,
    features-service,
    deployment-service,
  ]
scope: [engineer]
tags:
  [
    instruments-service,
    docs-audit,
    canonical-instrument-id,
    reference-data,
    data-correctness,
    outstanding-items,
    fix-options,
  ]
related:
  [
    plans/active/issues/sports_manifest_unknown_league_id_2026_07_08.md,
    plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md,
    plans/active/issues/betfair_instrument_id_delimiter_cross_repo_2026_07_08.md,
    plans/active/issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
    plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md,
    plans/active/issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md,
    plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md,
    plans/active/prediction_canonical_identity_migration_2026_07_08.md,
  ]
created: 2026-07-08
author: unknown
last_updated: 2026-07-29
parent_epic: instruments_master
priority: P1
source:
  Docs-cleanup audit of instruments-service/docs/*.md (slot-3, this session). Each doc's audit-trail was stripped to
  spec; each outstanding claim was verified against live code. Operator asked for a single consolidated issues doc
  covering every open item with fix options, plus deeper root-cause investigation for the uncertain ones.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
context_scope:
  [
    instruments-service/docs/,
    /plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/archive/2026_08/canonical_id_builder_retrofit_checklist_2026_07_08.md,
    /plans/active/issues/instruments_remaining_work_audit_2026_07_10.md,
  ]
locked_since:
resolved_by:
audited_scope: reference-data-docs
---

# Instruments-service docs audit — consolidated outstanding items (2026-07-08)

## What this is

The 7 instruments-service asset docs were cleaned from audit-trail ("we found X and fixed it") style into current-state
spec. Doing that, every "outstanding" claim in them was **verified against live code**. This doc lists everything that
survived verification as genuinely open — **every item, no matter how minor** — each with:

- **Evidence** — the exact `file:line` that proves it's still true.
- **Root cause** — why it's the way it is (traced, not assumed; two uncertain ones re-investigated this session).
- **Fix options** — concrete A/B/C with a recommendation.
- **Tracked** — a cross-reference if a dedicated issue doc / plan already owns it; otherwise this doc is the SSOT.

Priorities: **P0** = live correctness / blocks a downstream consumer · **P1** = real gap, should fix · **P2** = cleanup
/ minor · **DECISION** = needs an operator call, not an engineer fix · **DATA** = needs a GCS/prod run, not a code edit.

TRADFI is intentionally excluded here — its doc + adapter code were mid-edit by a parallel session at audit time; its
cleanup + outstanding items are captured in the deferred note (see §H).

---

## A. Correctness / data-integrity bugs

### A1. Sports `league_id="UNKNOWN"` — 2,373 manifest rows — `P1` — RESOLVED 2026-07-09 — tracked: `sports_manifest_unknown_league_id_2026_07_08.md`

- **What:** 2,373 rows in the real sports availability manifest carry the literal `league_id="UNKNOWN"`, spanning all 17
  sports data_types and 7 source families, dated 2025-12-15 → today. All are
  `capture_status ∈ {expected_unattempted, empty_confirmed}` (gap-fill bookkeeping, not corrupted captured data), so the
  failure mode is a phantom "UNKNOWN" pseudo-league polluting the honest-coverage denominator, recurring daily.
- **Evidence:** manifest `_index/availability_index.parquet` (4.94M rows); prior candidates ruled out —
  `sports_reference_fixtures.py::_write_per_fixture_entities` (guards bare writes),
  `sports.py:57 _canonical_league_id()` (no UNKNOWN fallback), `base.py:357` (error classifier), UAC `LEAGUE_REGISTRY`
  (clean).
- **Root cause (CONFIRMED this session — a self-sustaining catalogue↔enumerator loop; 2,363/2,373 = 99.6% pinned via
  `enumerator_run_id` provenance + exact reason-count match against the real 4.97M-row manifest):**
  - **Phantom source —**
    [build_instrument_catalogue.py:1234-1258](instruments-service/scripts/build_instrument_catalogue.py#L1234)
    (`build_sports_catalogue_from_manifest`) rolls the manifest into one catalogue row per distinct `league_id`,
    filtering only `league_id != ""` — it does **not** exclude the `"UNKNOWN"` sentinel and applies **no
    `capture_status` filter**. So it mints a catalogue row
    `instrument_id="UNKNOWN"/league_id="UNKNOWN"/available_from="2025-12-15"/available_to=None` (confirmed present in
    the real `prod/catalog.parquet`, 116 rows, exactly 1 UNKNOWN).
  - **Amplifier / write site —**
    [enumerate_expected_universe.py:1934](instruments-service/scripts/enumerate_expected_universe.py#L1934)
    (`_enumerate_v2_sports`) does `league_id = instr.league_id or instr.instrument_id` with no sentinel guard, then
    emits one row per sports data_type × every alive day for that phantom league. Emit sites match the manifest exactly:
    L2019-2030 → `expected_unattempted` = **1,352**; L1957-1967 → `EXPECTED_NO_PROVIDER_COVERAGE` = **897**; L1992-2002
    → `EXPECTED_POST_SEASON` **90** + `EXPECTED_PRE_SEASON` **24** (= 1,011 `empty_confirmed`).
  - **Self-sustaining:** the catalogue-builder reads _all_ manifest rows including the enumerator's own expected/empty
    rows, so even removing the seed leaves the loop alive; the daily `enum-universe-sports-*` cron is why max date =
    today.
  - **The 10 `captured` bootstrap rows** (api_football FIXTURE_STATS/EVENTS, `instrument_count=0`, written once
    2026-05-01) trace to
    [api_football_reference.py:165](instruments-service/instruments_service/reference_data/adapters/sports/adapters/api_football_reference.py#L165)
    (`... if league_name else "UNKNOWN"`). These are **frozen** — the `_is_in_canonical_write_universe` gate
    (`sports.py:104`, incident 2026-06-24) now returns `False` for `"UNKNOWN"` and blocks new such captures.
  - This resolves the prior doc's open "shared helper vs 7 broken fetchers" question: **ONE shared enumerator iterating
    a single phantom league**, not systemic per-fetcher breakage. (Verified against real GCS with ADC, read-only.)
- **Fix options:**
  - **A (recommended): kill the phantom at the catalogue source.** In `build_sports_catalogue_from_manifest` (~L1237)
    drop sentinel `league_id`s (`"UNKNOWN"`, and defensively any not in the canonical league universe) before roll-up.
    Breaks the loop at root; blast radius = sports catalogue only. **Must be paired** with a one-time manifest cleanup
    of the 2,373 + 10 rows, else they persist until the next enumerator run stops re-writing them.
  - **B: defense-in-depth** — add a sentinel guard in `_enumerate_v2_sports` (~L1927/1934) and change
    `api_football_reference.py:165` to skip/None instead of `"UNKNOWN"`. Do this **in addition to A**, not instead (B
    alone leaves the phantom catalogue row polluting `prod/catalog.parquet`).
  - **C: manifest cleanup only — futile.** The next daily `enum-universe-sports-*` run regenerates all 2,363 rows from
    the still-present catalogue UNKNOWN league. Cleanup without A/B does nothing lasting.
  - **Residual:** the 10 bootstrap rows aren't traced fixture-for-fixture (manifest carries no `fixture_id` for them);
    unnecessary for the fix since the write-universe gate already blocks new UNKNOWN captures.
- **Note:** the dedicated doc `sports_manifest_unknown_league_id_2026_07_08.md` still records this root cause as "not
  yet pinned" — it should be updated to point here (now pinned).
- **RESOLVED 2026-07-09 (both fix options A + B shipped together, plus the backfill):**
  `build_sports_catalogue_from_manifest` now excludes a `SPORTS_LEAGUE_ID_SENTINELS = frozenset({"UNKNOWN"})` set
  (case-insensitive) before the roll-up — deliberately a narrow sentinel check, NOT the "defensively any not in the
  canonical league universe" language above, because verifying against the real prod catalogue found 22 real leagues
  (raw numeric long-tail ids, `LA_LIGA_2`, `RFPL`, `SCOTTISH_LEAGUE_CUP_185`) that are NOT in `LEAGUE_REGISTRY` — a
  membership-based filter would have wrongly dropped all 22. `_enumerate_v2_sports` carries a matching defense-in-depth
  sentinel guard. `api_football_reference.py:165` intentionally left untouched (frozen by the 2026-06-24 write-universe
  gate already; not the fix's blast radius). Backfill executed against real prod GCS
  (`instruments-store-sports-prd-central-element-323112`): 1 catalogue row (116→115) + 2,373 manifest index rows
  removed, both objects backed up first (`*.20260708-234112.unknown_league_backfill.bak.parquet`); per-VM shards checked
  and confirmed clean (0 rows, no cleanup needed). Post-backfill verify: 0 sentinel rows remain anywhere; rebuilding the
  catalogue from the live post-backfill manifest through the patched roll-up still mints 0 `"UNKNOWN"` rows (loop
  confirmed broken, not just patched at one layer). Full evidence in `sports_manifest_unknown_league_id_2026_07_08.md`'s
  "Resolution (2026-07-09)" section.

### A2. Deribit multi-leg combo id is malformed (missing `:TYPE:` segment) — `P1` — RESOLVED 2026-07-09

- **RESOLVED 2026-07-09**: `deribit_combo_adapter.py::_build_legs` now routes through the shared `build_leg()` builder
  via a new `_classify_deribit_leg_instrument_type()` classifier, verified against Deribit's real live
  `public/get_combos` API (89 real BTC combos / 32 unique legs, 88 real ETH combos / 30 unique legs, 2026-07-09). Real
  before/after: `DERIBIT:BTC-PERPETUAL` → `DERIBIT:PERPETUAL:BTC-PERPETUAL`; `DERIBIT:BTC-10JUL26` →
  `DERIBIT:FUTURE:BTC-10JUL26`; `DERIBIT:BTC-17JUL26-65000-C` → `DERIBIT:OPTION:BTC-17JUL26-65000-C`. Shipped
  `instruments-service@ca2f44e5`, confirmed ancestor of `origin/live-defi-rollout`. Same pass also opportunistically
  retrofitted the 5 on-chain-perp adapters (Hyperliquid/Aster/Pacifica/Extended/Lighter) onto the shared builder — pure
  DRY, byte-identical output, closing `canonical_id_builder_retrofit_checklist_2026_07_08.md` todos 4 and 5.
- **What (original finding):** Deribit combo legs build an `instrument_key` with no type segment, so the id doesn't
  parse under the canonical `VENUE:TYPE:PAYLOAD` grammar.
- **Evidence:**
  [deribit_combo_adapter.py:310](instruments-service/instruments_service/reference_data/adapters/cefi/deribit_combo_adapter.py#L310)
  — `instrument_key=f"DERIBIT:{leg_name}"`.
- **Root cause:** hand-rolled f-string that predates / bypasses the shared `build_leg`/`build_instrument_id` builder.
- **Fix options:**
  - **A (recommended):** route leg construction through the shared canonical builder (`build_leg`) so the `:TYPE:`
    segment and grammar are enforced centrally — folds into the retrofit (§B1).
  - **B:** minimal in-place fix — insert the correct type segment into the f-string (`f"DERIBIT:OPTION:{leg_name}"` or
    the real per-leg type). Faster, but leaves the ad-hoc pattern that §B1 wants to eliminate.

### A3. Real `.env.example` ships wrong secret names — `P2` — NEW

- **What:** the doc's `.env.example` block was corrected during the audit, but the actual repo file still ships stale
  secret names, so a fresh clone configures the wrong secrets.
- **Evidence:** [instruments-service/.env.example](instruments-service/.env.example) has
  `GRAPH_SECRET_NAME=graph-api-key` (code default is `thegraph-api-key`, per
  `unified-trading-library/.../cloud_config.py:576-580`) and no `IBKR_CREDENTIALS_SECRET_NAME` line (field exists at
  `cloud_config.py:619-626`, default `ibkr-account-credentials`).
- **Root cause:** template file drifted from the config dataclass defaults; never regenerated.
- **Fix options:**
  - **A (recommended):** edit `.env.example` — set `GRAPH_SECRET_NAME=thegraph-api-key` and add
    `IBKR_CREDENTIALS_SECRET_NAME=ibkr-account-credentials`. One-line, no code risk.
  - **B:** drop the back-compat `GRAPH_SECRET_NAME` alias entirely and standardize the template on
    `THEGRAPH_SECRET_NAME` (also touches the alias in `cloud_config.py`).

### A4. Stale hardcoded feature count `672` — `P2` — NEW

- **What:** the sports SSE stream advertises a hardcoded `feature_count=672` that silently goes stale as calculators
  change.
- **Evidence:** [sse_stream.py:13](features-service/features_service/sports/api/sse_stream.py#L13) —
  `feature_count=672`.
- **Root cause:** literal instead of a registry-derived count.
- **Fix options:**
  - **A (recommended):** derive the count from the live feature registry at import/startup so it can't drift.
  - **B:** update the literal to the current count and add a keep-in-sync comment + a unit test asserting it matches the
    registry.

---

## B. Canonical instrument_id migration (target decided, not shipped)

The largest cross-cutting thread. The target grammar and the shared builder exist; adoption is partial. Umbrella
tracking: `instrument_id_format_canonicalization_2026_07_08.md` +
`canonical_id_builder_retrofit_checklist_2026_07_08.md`.

### B1. Shared builder adopted by only ~4 of ~63 adapters — `P1` — tracked: `canonical_id_builder_retrofit_checklist_2026_07_08.md`

- **Evidence:** only `deribit_options_adapter.py`, `ccxt_adapter.py`, `databento/adapter.py`, `polymarket/parsing.py`
  import `build_instrument_id`/`build_leg`; ~59 adapter files still build `instrument_key = f"..."` ad hoc.
- **Fix options:**
  - **A (recommended):** execute the retrofit checklist plan — migrate adapters in batches to the shared builder.
  - **B:** add a QG lint that bans new ad-hoc `instrument_key = f"..."` in `adapters/` to stop regression while the
    retrofit lands incrementally. (Best combined with A.)

### B2. `@LIN`/`@INV` margin-marker suffix not implemented — `P1` — tracked: `instrument_id_format_canonicalization_2026_07_08.md`

- **Evidence:**
  [canonical_id_builder.py](unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py)
  `_build_future`/`_build_option` still emit the embedded `-inverse-`/`-linear-` word form; `@LIN`/`@INV` only exists
  today in strategy-service/MTDS PERPETUAL position-ids.
- **Fix options:** **A (recommended)** add the suffix logic to the builder + a go-forward switch, then a
  rewrite-in-place catalog migration. **B:** defer until B1 adoption is complete (avoids migrating the same rows twice).

### B3. Asset-class prefix (`CEFI:`/`DEFI:`) unimplemented — RESOLVED 2026-07-09 (operator): drop it

- **Evidence:** `grep -rn '"CEFI:"|"DEFI:"'` across `instruments_service/` → 0 hits; the doc labelled it "aspirational".
- **Decision:** operator confirmed this was about the instrument_id prefix specifically, and dropped it — venues are
  already distinct per asset group without needing an extra leading token. **Fix option C applied**: delete the
  aspirational language from the spec. Not yet applied to `ADAPTER_ARCHITECTURE.md` itself — that file is mid-edit by
  another agent this session; whoever next has a clean window on it should strip this language.

### B4. DeFi pool fee-tier is colon-separated + raw units, not dash/bps — `P1` — tracked: `instrument_id_format_canonicalization_2026_07_08.md`

- **Evidence:**
  [uniswap_v3.py:590](instruments-service/instruments_service/reference_data/adapters/defi/uniswap_v3.py#L590) builds
  `{base}-{quote}:{fee_str}` with a colon before raw `feeTier`.
- **Fix options:** **A (recommended)** change the builder to dash/bps + catalog regen (DATA follow-up C1). **B:** leave
  format, document as the accepted current form (only if the target is abandoned).

### B5. Prediction `canonical_instrument_id` always `None`; `underlying` never populated — `P1` — tracked: `prediction_canonical_identity_migration_2026_07_08.md`

- **Evidence:** Polymarket
  [parsing.py:138-158](instruments-service/instruments_service/reference_data/adapters/prediction/polymarket/parsing.py#L138)
  and Kalshi `kalshi.py:798-818` construct `InstrumentRecord(...)` with neither `canonical_instrument_id=` nor
  `underlying=`; `underlying_for_group()` is only called from `cross_venue_mapping.py`.
- **Fix options:** **A (recommended)** populate both at adapter `_parse_market()` time via the shared builder + the
  underlying classifier. **B:** compute `underlying` in a post-build pass if adapter-time data is insufficient.

### B6. Betfair `market_id/selection_id` delimiter fix (3-repo) — `P1` — tracked: `betfair_instrument_id_delimiter_cross_repo_2026_07_08.md`

- **Evidence:** builder still uses `/` at
  [betfair.py:279](instruments-service/instruments_service/reference_data/adapters/sports/adapters/betfair.py#L279);
  consumers `strategy-service/.../fill_event_consumer.py:72` (`rsplit("/",1)`) and
  `execution-service/.../betfair_order_mapping.py:180,286`.
- **Fix options:** **A (recommended)** coordinated change: switch the builder to a reserved-safe delimiter and update
  both consumers in the same rollout. **B:** keep `/` and document it as the accepted Sports-exchange exception (only if
  the collision risk is judged acceptable).

---

## C. DeFi adapters / coverage not built or not wired

### C1. No A_TOKEN / DEBT_TOKEN split for 6 lending protocols — `P1` — RESOLVED 2026-07-13 — tracked: `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md`

- **RESOLVED 2026-07-13**: all 9 DeFi lending protocols (AAVE_V3, SPARK, COMPOUND_V3, MORPHO, FLUID, VENUS, RADIANT,
  EULER_V2, BENQI — wider than this item's original 6-protocol scope) now emit exactly two `InstrumentRecord`s per
  position-bearing reserve/market: `instrument_type=A_TOKEN` (supply side) + `instrument_type=DEBT_TOKEN` (borrow side),
  keyed `VENUE-CHAIN:A_TOKEN:...` / `VENUE-CHAIN:DEBT_TOKEN:...`. Real production catalogue verified: 2,949 rows across
  all 9 protocols, 100% canonical. Shipped `instruments-service@72e0113`+`5226818`, `unified-api-contracts@48bfadff5`.
  Full per-protocol evidence in `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md`'s 2026-07-13 entry. Fix
  option A below (implement the supply/borrow split per protocol) is what shipped.
- **Original evidence (historical, pre-fix):** Morpho/Euler_V2/Fluid/Radiant/Venus/Benqi each emitted one flat
  `LENDING_MARKET` record (`adapters/defi/{morpho,euler_v2,fluid,radiant,venus,benqi}.py`).

### C2. MARGINFI / SOLEND have no instruments-service adapter — `DECISION` — NEW

- **Evidence:** `grep -rln "marginfi|solend" instruments_service/` → 0 hits.
- **Fix options:** **A** build the two Solana-lending adapters; **B (decide first)** confirm whether Solana lending is
  in the DeFi MVP scope before building.

### C3. MTDS + execution-service hardcode bare `"YEARN-ETHEREUM"` — `P1` — NEW

- **Evidence:** `market-tick-data-service/.../vault_yearn_adapter.py:37`;
  `execution-service/.../defi_execution/protocols/yearn.py:50,100`.
- **Fix options:** **A (recommended)** replace the literals with the canonical venue constant/resolver (2-repo change,
  keeps them in sync with the instruments-service `YEARN_V3` rename). **B:** leave, accept the cross-repo divergence
  (not recommended — silent mismatch).

### C4. Solana venues carry a key-vs-field mismatch (Sanctum/Solblaze/Jito/Drift + ~9 more) — `P1` — NEW

- **Evidence:** `sanctum.py:121,124`, `solblaze.py:95,98`, `jito_restaking.py:141,144`, `drift.py:253,259` — field
  doesn't match the venue key.
- **Fix options:** **A (recommended)** align the field to the key (same one-line fix pattern used for the LST adapters).
  **B:** batch it into the §B1 retrofit.

### C5. MTDS restaking adapters emit divergent `:VAULT:` `RESTAKING_VAULT` keys (live, wired) — `P1` — NEW

- **Evidence:** `market-tick-data-service/.../factory.py:37-50,168-181` + `restaking_{karak,jito,symbiotic}_adapter.py`,
  `vault_pendle_adapter.py` — these are wired and live (not dead scaffolding), but their instrument_id form diverges
  from instruments-service canonical.
- **Fix options:** **A (recommended)** reconcile MTDS restaking key construction with the instruments-service canonical
  form. **B:** define restaking as an intentionally MTDS-only shape and document the divergence (only if reconciliation
  is out of scope).

### C6. `DEFI_MAJOR_ASSET_ADDRESS_LIST` Ethereum-only; V2/V4/Balancer skip the major-asset query — `P2` — NEW

- **Evidence:**
  [defi_major_assets.py:81-124](unified-api-contracts/unified_api_contracts/registry/defi_major_assets.py#L81) is
  ETH-mainnet only; `_fetch_major_asset_pools` is referenced only in `uniswap_v3.py`.
- **Fix options:** **A** extend the address list to the other chains and wire the supplementary query into Uniswap
  V2/V4 + Balancer. **B:** document ETH-only as the accepted major-asset ceiling if multi-chain isn't needed yet.

### C7. Fluid: `utilization_rate` is a raw cross-asset ratio; multi-chain unverified — `P2` — NEW

- **Evidence:** `market-tick-data-service/.../fluid_adapter.py:619` (raw ratio); UAC `_defi.py:112-115` ("Fluid subgraph
  IDs need verification"); Morpho restricted to ETH+Base (`_defi.py:103-111`).
- **Fix options:** **A** compute a proper per-market utilization + verify the multi-chain subgraph IDs. **B:** flag the
  metric as approximate in the schema until corrected.

### C8. Live per-block DEX swap streaming does not exist (placeholder only) — `P1` — NEW

- **Evidence:** `market-tick-data-service/.../dex_swap_scaffold_ws.py:103` — `DexSwapPlaceholderWSFeedConnector`.
- **Fix options:** **A (recommended)** implement the real WS connector (larger build — new work). **B:** confirm whether
  batch swap ingestion is sufficient for near-term strategies before investing (relates to the OHLCV-vs-raw-swaps
  decision E5).

---

## D. Prediction & Sports wiring gaps

### D1. `build_cross_venue_mapping()` not wired into the write path — `P1` — NEW

- **Evidence:** zero callers in `instruments-service/` outside tests; only used in features-service/e2e — it runs on
  demand, never persisted onto the catalog.
- **Fix options:** **A (recommended)** call it in the per-day write path and persist the mapping onto the catalog.
  **B:** leave as an on-demand tool if cross-venue identity is not needed at write time.

### D2. Polymarket `_cross_reference_fixture()` defined but never called — `P2` — NEW

- **Evidence:**
  [parsing.py:296](instruments-service/instruments_service/reference_data/adapters/prediction/polymarket/parsing.py#L296);
  only other hits are tests.
- **Fix options:** **A** wire it into the sports-fixture alignment path (needed for prediction↔sports identity); **B**
  delete it as dead code if that alignment is descoped.

### D3. Open `TODO(mvp-scope)` to narrow Prediction sources — `P2` — NEW

- **Evidence:** `unified-api-contracts/.../canonical/crosscutting/mvp_scope.py:725` — TODO to narrow to
  `{polymarket_clob, polymarket_gamma_api}`.
- **Fix options:** **A** resolve the TODO (narrow the set). **B:** operator confirms the intended MVP source set first.

### D4. Sports Unity feed I/O is stubbed — `P1 (BLOCKED-VENDOR)` — NEW

- **Evidence:** `execution-service/.../sports_execution/adapters/unity/__init__.py:13-14` — docstring: I/O intentionally
  stubbed, needs the Unity-issued binary + TCP framing spec.
- **Fix options:** **A** implement once the vendor binary/spec is available (blocked on vendor). **B:** keep the
  scaffold
  - status BLOCKED-VENDOR (do not present as complete).

### D5. Dead `_resolve_*` helpers in deployment-api `venue_resolution.py` — `P2` — NEW (related: `instruments_service_data_status_endpoint_dead_code_2026_07_07.md`)

- **Evidence:** `deployment-api/.../data_status/venue_resolution.py:307-334` — `_resolve_expected_dates()` never calls
  `_is_transfer_window_venue`/`_resolve_transfer_window_dates`/`_is_understat_venue`/`_resolve_understat_fixture_dates`;
  confirmed dead by grep.
- **Fix options:** **A (recommended)** delete the dead helpers + fix the inaccurate docstring. **B:** wire them in if
  the transfer-window/understat date resolution was actually intended to run.

### D6. No ml-service Cloud Run Job for `inference_pre_match` — `P1` — NEW

- **Evidence:** `deployment-service/configs/sports-trigger-tiers.yaml:187-201` — entry ships an empty
  `cloud_run_job_name` (fires a warning, skips).
- **Fix options:** **A (recommended)** create the ml-service Cloud Run Job and set `cloud_run_job_name`. **B:** remove
  the tier entry if pre-match inference isn't launching yet (don't leave a silently-skipped entry).

### D7. `sports-odds-ready` publisher not located — `P0` (bumped from P1, 2026-07-29 — see impact note below) — NEW

- **What:** the sports odds→downstream trigger references a `sports-odds-ready` topic whose consumer exists but whose
  publisher could not be found; MTDS publishes to `persist-{asset_group}-{data_type}` instead.
- **Verdict (investigated this session): NEVER-PUBLISHED — dead trigger** (a real functional gap, not a doc/naming
  mismatch). The topic is terraform-provisioned with a real, working subscriber, but **no shipped code in any repo
  publishes to it.**
- **Root cause / evidence:**
  - MTDS's live sink `market-tick-data-service/.../live/event_facade_sink.py` is the unconditional default tick sink for
    every asset group in live mode; its `flush()` publishes to `persist-{asset_group}-{data_type}` (→
    `persist-sports-odds` for odds), via the UTL naming SSOT
    `unified-trading-library/.../streaming/event_facade.py:273-276`. It never emits `sports-odds-ready`.
  - The canonical `InternalPubSubTopic` enum (`unified-api-contracts/.../pubsub_service/pubsub.py:12-40`) has **no**
    `SPORTS_ODDS_READY` member — `sports-odds-ready` exists only as a raw string in terraform and as hardcoded
    features-service CLI defaults. No `"{x}-ready"` topic-builder / indirection exists.
  - The subscriber is real and idle: `features-service/features_service/sports/app/pubsub/subscriber.py:76`
    (`DEFAULT_SUBSCRIPTION_ID="sports-odds-ready"`) + `cli/handlers/live_handler.py:107`, `cli/main.py:92-93`.
  - Intended design was documented but never built: `e2e-testing/scripts/sports/LIVE_PUBSUB_README.md:23,110-121` ("MTDS
    publishes `sports-odds-ready` after flushing the canonical odds snapshot to GCS"). The `-ready` pattern DOES work
    elsewhere (`features-service/.../multi_timeframe/engine/orchestrator.py:599` publishes `features-mtf-ready`) —
    sports-odds was simply never finished on the MTDS side.
- **Impact:** live-mode sports feature computation never fires — the subscriber idles with **no crash/error/alert**, so
  it would go undetected in prod. **UPDATE 2026-07-29 — no longer latent, now live-armed:** the live Odds API connector
  (`market_tick_data_service/live/connectors/odds_api_ws.py:154`) was `BLOCKED-CREDENTIALS`, so live sports odds had
  never actually run — but the operator rotated `odds-api-key` (Secret Manager, project `central-element-323112`) to a
  new working key on 2026-07-29 (this connector resolves that exact secret), so live sports odds capture can now
  actually start. Once it does, this dead-trigger bug means live sports feature computation will silently never fire,
  with no crash/error/alert to surface it. Bumped P1→P0 accordingly. Batch mode is unaffected. Same bug class as
  `plans/archive/2026_08/issues/live_mode_event_sink_topic_missing_2026_06_21.md` (topic-naming drift between a service
  sink and terraform-provisioned topics) — worth flagging as systemic.
- **Fix options:**
  - **A (recommended):** repoint FSS's subscriber default from `sports-odds-ready` → the real `persist-sports-odds`
    topic MTDS already publishes (4 files: `subscriber.py`, `cli/handlers/live_handler.py`, `cli/main.py`,
    `cli/parser.py`). Zero new MTDS code; matches the fleet-wide "Live = batch event-log spine" SSOT
    (`/codex/02-data/live-data-persistence-and-event-log.md`) and the resolution chosen for the sibling bug. Deprecate
    the unused `sports-odds-ready` terraform entry after cutover.
  - **B:** implement the originally-designed publisher — add a real `sports-odds-ready` publish in MTDS's odds
    snapshot-flush path (per `LIVE_PUBSUB_README.md`), keeping subscriber + terraform topic as-is. More code; preserves
    a semantically distinct "odds ready" signal.
  - **C (no longer viable, 2026-07-29):** doc-only defer — this option's premise was that live sports odds was
    `BLOCKED-CREDENTIALS` with no impact yet; that credential is now fixed (see impact note above), so a doc-only defer
    would leave a genuinely live-triggerable dead-trigger bug unaddressed. Prefer **A**.
  - **Residual uncertainty:** did not exhaustively rule out a console-created (non-terraform) Eventarc/GCS-finalize
    trigger bridging `persist-sports-odds` → `sports-odds-ready`; grep of `deployment-service/terraform` found none.

### D8. instruments-service `--trigger` live dispatch only partly wired — `P2` — NEW

- **Evidence:** `instruments_service/triggers/` contains only `sports_fixtures_daily_repoll.py`; `cli/main.py` lists
  just `sports.fixtures.daily_repoll` as implemented.
- **Fix options:** **A** wire the remaining triggers per `instruments_master`. **B:** document the current
  single-trigger set as intentional if the rest are genuinely deferred.

### D9. Sports reference leagues still numeric-`league_id`-keyed (subset) — `P2` — NEW

- **Evidence:** `instruments_service/engine/orchestrator/sports.py:57` `_canonical_league_id()` passes unknown numerics
  through unchanged (by its own docstring).
- **Fix options:** **A** add registry entries so those leagues canonicalize. **B:** accept numeric keys for the
  long-tail leagues and document them as the fallback form.

---

## E. Operator decisions required (not engineer fixes)

- **E1. Odds↔instruments row-level join key** — no `af_fixture_id` threaded through the odds schema. **A (recommended)**
  thread `af_fixture_id` through the odds writer schema (enables per-fixture joins); **B** accept the team-name-only
  join and document the limitation.
- **E2. Sports fixture/team/player-grain coverage tracking** — never built. **A** build it; **B** confirm it isn't
  wanted and close the gap in the spec.
- **E3. CeFi 6 reused tickers** (`CFG/DIA/INX/ROBO/SLX/SPX`, `cefi_instrument_universe.py:268,284-285`) — kept despite
  Binance ticker reuse. **DECIDED 2026-07-09 (operator): keep all 6**, accept the ambiguity — no cross-venue audit
  needed. Doc update (not yet applied — coordinate with whichever agent next has a clean window on
  `CEFI_INSTRUMENTS.md`): replace the "PARTIALLY OPEN" framing with this resolved decision.
- **E4. CeFi `FI_`/`FF_` Kraken-Futures subtype** — code comment (`tardis_shared.py`) says `FI*` "no longer active" but
  real 2024-26 data contradicts it. **A** update the comment + add a contract-subtype field to the schema; **B** confirm
  inactive and drop the data. (Needs a GCS data check — DATA.)
- **E5. DeFi MVP framing** — no dedicated DeFi MVP set exists distinct from the factory registry (tracked:
  `defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`). **A** retire the "MVP universe" framing for DeFi; **B**
  define an explicit DeFi MVP set. **C** OHLCV-vs-raw-swaps derivation (relates C8) is an open architecture question to
  settle alongside this.

---

## F. Data-state / operational (needs a GCS/prod run — not a code edit)

These are code-verified as "the code is correct but the production data/backfill hasn't been run/confirmed." Confirm via
a GCS/manifest read, not a code change.

- **F1. DeFi:** DEX-pool catalog regen to target id format; on-chain-perp `--apply` migration; Sanctum/Solblaze/Spark
  first production backfill; MTDS ghost-dir consolidation (`MORPHO_VAULTS`/`MORPHOVAULTS`, `YEARNV3`/`YEARN_V3`,
  `UNISWAPV3`/`UNISWAP_V3`).
- **F2. Prediction:** catalog regen to pick up `raw_symbol`/`base_asset`; legacy `market-data-tick-prediction-*` bucket
  migration completion; `market-data-processing-service` test-pin still asserts the old unabbreviated bucket
  (`test_dependency_checker_sports_prediction.py:149`).
- **F3. Sports:** odds gap 2025-12-31 → 2026-03-21 (~80 days); FootyStats ~73% residual coverage (tracked:
  `footystats_matches_predictions_fetch_gaps_2026_07_08.md`); stale backfill row-count table (2026-03-27 snapshot);
  SFI/Transfermarkt coverage snapshots are point-in-time.

---

## G. Verified-resolved during this audit (record only — removed from the docs, NOT open)

Listed so nobody re-opens them: these were written in the docs as open problems but the code proves them fixed.

- **CCXT live≠batch instrument_id (P0)** — `ccxt_adapter.py::_build_instrument_key` (commit `8544273d`); tracked plan
  `canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md`.
- **CCXT live position reconciliation defeated (P0)** — `strategy-service/.../reconciliation_engine.py:197-217` now
  raises (commit `0c407b57`); plan `canonical_id_p0_strategy_reconciliation_2026_07_08.md`.
- **23 DeFi adapters empty-on-type-filter** — regression test `test_instrument_type_filter_regression_2026_07_08.py`;
  plan `canonical_id_p0_defi_adapter_type_filter_bug_2026_07_08.md`.
- **Kraken-Futures dated-future collision** — `tardis_shared.py` `_KRAKEN_FUTURES_RE`; plan
  `canonical_id_p0_kraken_futures_collision_2026_07_08.md`.
- **AAVEV3-OPTIMISM misspelled duplicate** — `aave_v3.py:234,287` builds the correct venue tag.
- **Compound_V3 "SUPPLY/BORROW crash risk"** — never real; field is `InstrumentType.LENDING` for both records.
- **Curve "not wired"** — now fully on `api.curve.finance` REST across 7 chains (`curve.py:30-42`).
- **Sanctum/Solblaze "adapters not built"** — both exist and are wired (`factory.py:60,62`).
- **FootyStats naming-mismatch risk** — fetch is by numeric season id (`footystats.py:480-482`), not by name.
- **Doc factual corrections:** bitstamp/huobi/huobi-dm still in `venue_mapping.py` despite a "removed from all
  registries" claim (corrected); `DataSourceMapping.get_required_secrets` exists despite a "doesn't exist" claim
  (corrected); DeFi "24 adapters" arithmetic corrected to 37.

---

## G2. Resolved later the same day (2026-07-09 reconciliation pass) — record only, NOT open

A large parallel fix wave landed after this doc was filed. Cross-referencing against real shipped commits:

- **A2 (Deribit combo `:TYPE:` missing)** — folded into and shipped as part of the unified canonical-id-builder work;
  `build_leg()` now exists in `canonical_id_builder.py`. ✅ **DONE 2026-07-12 correction** (was: "Still needs: the
  actual retrofit of `deribit_combo_adapter.py:310` to call it — tracked as its own todo in
  `canonical_id_builder_retrofit_checklist_2026_07_08.md` todo 5, not yet executed. Downgrading from 'NEW' to 'tracked,
  unexecuted.'") — the retrofit shipped `instruments-service@ca2f44e5` (2026-07-09 00:50 UTC, on `live-defi-rollout`,
  verified via `git log`/`git show`): `_build_legs` now routes through `build_leg()` with a new
  `_classify_deribit_leg_instrument_type()` classifier verified against Deribit's real live `public/get_combos` API;
  commit message cites both "checklist todo 4/5" and "this doc's A2/G2" by name.
  `canonical_id_builder_retrofit_checklist_2026_07_08.md` todo 5 is checked `[x]` DONE with this same commit. Finding
  #124, plan-reconciliation `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 B-queue
  ruling.
- **B1 infra** — the shared builder itself (`build_canonical_instrument_id`, `build_leg`, `passthrough=True`) shipped in
  full (`unified-api-contracts`, this session), with one live retrofit (`deribit_options_adapter.py`) proven. The
  ~59-adapter retrofit itself is still the open work — `canonical_id_builder_retrofit_checklist_2026_07_08.md` is
  current or B1 tracker, not superseded.
- **C3 (bare `YEARN-ETHEREUM` in MTDS/execution-service)** — independently reconfirmed by a separate agent pass the same
  day (DeFi venue-token cleanup); still explicitly open, not fixed — matches this doc's existing status, no change.
- **C6 (major-asset query Ethereum-only)** — partially addressed: Uniswap V3 + the 8 protocols sharing
  `UniswapV3ReferenceDataAdapter` now run the supplementary major-asset query (real fix, `instruments-service`, found a
  real DAI/USDT pool at ~$0.0004 TVL that was previously unreachable). Uniswap V2/V4/Balancer/Curve remain unfixed —
  item stays open, scope narrowed.
- **D5 (dead `_resolve_*` helpers in `venue_resolution.py`)** — independently reconfirmed by a separate agent
  investigating the SFI/Transfermarkt coverage metric; verified these functions don't affect any real coverage number
  (only touch 92 orphaned health-check rows + 2,991 unrelated legacy rows). Still open (not deleted), same
  recommendation (A: delete + fix the docstring).
- **D6 (no ml-service Cloud Run Job)** — independently reconfirmed by the SportsTriggerScheduler fix; the
  `sports-trigger-tiers.yaml` entry is now correctly left empty with a loud warn+skip (previously silent). Real ML job
  creation is still open — this doc's fix option A stands.
- **E3 (CeFi 6 reused tickers)** — independently reconfirmed the same day during an equity-perp MVP universe sync:
  Binance now tags `CFG/DIA/INX/ROBO/SLX/SPX` as `underlyingType=COIN` (ticker reuse by unrelated crypto tokens, not a
  clean delisting); all 6 still have live entries in `TRADFI_EQUITY_PERP_BASIS_UNIVERSE` + `crypto_equity_link.py`.
  Flagged as "PARTIALLY OPEN" in `CEFI_INSTRUMENTS.md`'s Known Bugs table — still needs the cross-venue DATA audit this
  doc's fix option A calls for; not resolved, just re-confirmed with fresher evidence.
- **C1 (No A_TOKEN/DEBT_TOKEN split for 6 lending protocols)** — RESOLVED 2026-07-13, scope widened to all 9 protocols
  (AAVE_V3/SPARK/COMPOUND_V3/MORPHO/FLUID/VENUS/RADIANT/EULER_V2/BENQI): real production backfill verified, 2,949 rows
  100% canonical `A_TOKEN`/`DEBT_TOKEN`. Shipped `instruments-service@72e0113`+`5226818`,
  `unified-api-contracts@48bfadff5`. See `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md`'s 2026-07-13
  entry.
- **Newly and fully resolved, not previously listed above:**
  - Sports coverage-metric "framing bug" hypothesis for Transfermarkt/SFI — investigated and found to be **stale
    numbers, not a live bug**: the denominator-grain fix already shipped a month earlier (`deployment-api@6b7aa696`,
    2026-06-11). Real current coverage: Transfermarkt 75.4% all-time / 99.6% current-era; SFI 99.9% all-time / 99.6%
    current-era. Docs corrected with real numbers.
  - `SportsTriggerScheduler` (D6's parent context) — root-caused and fixed for real: CLI never passed
    `backend=`/`workspace_root=`/`cloud_run_config=`, silently defaulting to `backend="local"` inside a container that
    can't run it; a second latent Cloud Run Jobs V2 `args`-vs-`command` bug was also found and fixed. Verified against
    real production GCS state (`last_run.reference` went from 14-days-stale to fresh, confirmed durable on re-check).
    Shipped `deployment-service`/`instruments-service`/`unified-trading-pm`.
  - Legacy sports feature-tracking registry (adjacent to A4/D-section context, not separately itemized above) —
    confirmed dead scaffolding (zero real consumers, single git-subtree import, never updated in 30+ days, and even its
    "10 complete" claim was wrong — mis-attributed to an unrelated real-time signal detector). Deleted cleanly,
    `features-service`.
  - Sports feature count doc staleness (related to A4, but the DOC number, not the SSE-stream literal in A4 itself) —
    updated from a stale 672 (dated 2026-03-27) to a live-verified 1,138 across 32 calculators.
  - Promotion/relegation historical-form feature (real design intent, previously unbuilt per `promoted_team_handler.py`
    existing-but-unwired) — `blend_promoted_features()` now wired into the real live compute path; a new first-season
    cohort-baseline feature was also built and verified against a real example (Luton Town's real 2022-23 promotion +
    real first 9 Premier League 2023-24 results). Real injury-data usage was checked and found to ALREADY be wired (not
    a gap).
  - 14 unused Sports bookmaker scrapers + retirement decision — retired cleanly (`execution-service`, 17 files),
    consumer-checked workspace-wide first (0 real callers), `bookmaker_api/onexbet.py` correctly kept (real, active,
    different category).
  - CeFi Bitfinex BTC-margined-perp accepted-quote gap — fixed (`unified-api-contracts` + `instruments-service`).
  - CeFi equity-perp MVP universe sync (105 → 124 real Binance tickers, KRX naming fixed) — done; connects to E3 above
    (the 6 reused tickers were found IN this same pass, not separately).
  - Kraken-Futures historical collision damage — scoped (125 real files / 37.5M rows found across the full corpus) and
    fully remediated in place (backed up first, rewritten from the untouched raw `symbol` column, re-verified zero
    remaining collisions).
  - DeFi AAVE_V3-OPTIMISM / MORPHO 3rd-colon / Balancer 5-cross-chain-collision venue-token bugs — all fixed and
    re-verified against real `prod/catalog.parquet` (0 remaining duplicates/collisions of any kind, catalog-wide).
  - On-chain-perp `PERP`→`PERPETUAL` + base-quote normalization (5 venues: Hyperliquid/Aster/Pacifica/Extended/ Lighter)
    — implemented with real, live-verified settlement currencies (Pacifica/Lighter's real quote had to be confirmed via
    docs, not their APIs, which don't expose it). Historical migration script written; a real dry-run against production
    ran 25+ min without finishing, so `--apply` was correctly NOT forced — this specific item stays in §F1 as unexecuted
    DATA work, not closed.
  - `market-tick-data-service`'s repo-wide "Empty string fallback" zero-tolerance Codex-compliance gate (338
    pre-existing sites, unrelated to any of the above, but blocking ALL pushes to that repo) — given a proper
    baseline-ratchet mechanism (mirroring the existing DTZ/TID251 pattern) instead of being left as a standing blocker;
    all 338 sites individually judged and fixed (annotate-deliberate vs. rewrite-fail-fast) across 4 batches, several
    genuine bugs caught in the process (a Snapshot governance-proposal id collision risk, a
    schema-drift-masked-as-empty-data risk in a Massive/Polygon flat-file parser).

## H. TRADFI — deferred (mid-edit by a parallel session at audit time)

Not cleaned in this pass. Ready-to-run cleanup note (audit-trail to strip + outstanding items to re-verify once the
sibling session commits) is captured separately. **Highest-value TRADFI item to re-verify:** the doc's "MVP Universe"
(§6) doesn't match runtime — the real adapter fetch uses `TRADFI_DATABENTO_INSTRUMENTS` with **no MVP filter**, so the
documented MVP scope doesn't actually restrict day-to-day fetches. Also: US2Y genesis date unverified; `ETHA` misses
`KNOWN_ETFS` → reclassifies as `EQUITY`; the CBOE per-day historical snapshot rewrite was explicitly deferred.

---

## Todos

- [ ] [REVIEW] P1. **Track the remaining corpus-wide outstanding items** — this doc's sections B-F list dozens of
      still-open items as plain prose/bullets, never checkboxes (e.g. B1-B6 canonical-id migration, C2-C8 DeFi
      adapter/coverage gaps, D1-D9 prediction/sports wiring gaps, F1-F3 data-ops follow-ups); see those sections for the
      full item-by-item list, evidence, and fix options.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - index doc whose section E is explicitly 'Operator decisions
  required (not engineer fixes)'; the single todo is meta-tracking over dozens of prose items

- 2026-07-08: Created from the instruments-service docs-cleanup audit (slot-3). 6 of 7 docs rewritten to spec + all
  outstanding items verified vs code; TRADFI deferred (§H).
- 2026-07-08: A1 (Sports `UNKNOWN` league_id) root cause **CONFIRMED** — catalogue↔enumerator feedback loop
  (`build_instrument_catalogue.py:1234` + `enumerate_expected_universe.py:1934`), verified against 4.97M real manifest
  rows. Fix A/B/C recorded. Follow-up: update `sports_manifest_unknown_league_id_2026_07_08.md` to mark root cause
  pinned.
- 2026-07-08: D7 (`sports-odds-ready` publisher) resolved to **NEVER-PUBLISHED dead trigger** (latent — live odds is
  BLOCKED-CREDENTIALS). Fix A/B/C recorded.
- 2026-07-09: A1 (Sports `UNKNOWN` league_id) **RESOLVED** — fix options A + B both shipped
  (`build_instrument_catalogue.py`'s roll-up + `enumerate_expected_universe.py`'s `_enumerate_v2_sports`, both
  `instruments-service`), narrowed from the "defensively any not in LEAGUE_REGISTRY" language to an exact sentinel check
  after verifying 22 real leagues would otherwise have been wrongly dropped. Backfill executed against real prod GCS (1
  catalogue row + 2,373 manifest rows removed, backed up first, per-VM shards confirmed clean). Verified 0 remaining + a
  live post-backfill catalogue rebuild via the patched code mints 0 new phantom rows. Regression tests added in
  `instruments-service/tests/unit/scripts/`. Full evidence: `sports_manifest_unknown_league_id_2026_07_08.md`.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the sole todo is an open-ended
  tracking meta-item over dozens of prose-only findings in sections B-F; no bounded outcome.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — the sole todo is a meta-tracking ask spanning
  dozens of prose bullets across sections B-F and 5 asset groups, and section E is literally titled 'Operator decisions
  required (not engineer fixes)' — converting that corpus to checkboxes requires per-item triage including those
  operator calls, so the outcome is not determinable by a worker alone

- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — still accurate against current content.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — sole open checkbox is open-ended
  meta-tracking over dozens of prose findings spanning 5 asset groups, several explicitly §E operator-decision
  territory; converting it to bounded AO todos itself needs human triage. Reaffirms 3 prior 2026-07-30 passes (cefi x2,
  sports).
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — consolidated docs-audit index across
  5 asset groups; sole open item is an open-ended meta-tracking pointer over prose-only findings sections, with an
  explicit 'Operator decisions required' section. Reaffirmed across 4 prior passes.
- **round9-reclassify-satellite-sweep 2026-08-09** (cefi tranche): KEEP-NA, valid — reaffirms the same-day
  na-eligibility-audit verdict above. Additionally checked per-item satellite-extraction potential on the doc's smaller
  bounded-looking prose findings (A3 `.env.example` secret-name drift, A4 stale `feature_count=672` literal, D5 dead
  `_resolve_*` helpers, C4 Solana venue key-vs-field mismatch): each either partially overlaps an already-tracked
  finding elsewhere in the corpus in a way that needs dedicated de-duplication (e.g. D5's `venue_resolution.py` and C4's
  `solblaze.py:95/98` both have near-hits in `tradfi_satellite_ao_dispatch_batch7/8` and
  `issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md` respectively, covering adjacent-but-not-identical bugs
  in the same files) or is small enough that extracting it alone risks a false sense of coverage over this doc's much
  larger prose-only B-F sections. No clean, conflict-free extraction found this pass — reporting near-zero yield rather
  than forcing a partial extraction. Doc stays `assigned_vm: NA`.
