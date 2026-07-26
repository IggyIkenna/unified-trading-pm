---
doc_type: plan
title:
  Route CBOE/VX multi-leg spreads through the real InstrumentLeg/COMBO infrastructure already proven for CME, with
  human-readable leg symbols
summary: >-
  TradFi multi-leg spreads (calendar spreads, butterflies, etc.) on CBOE/VX currently land in the catalog as flat,
  undecomposed strings using the wrong instrument_type (`SPOT_PAIR`, reused from equity spot) and a whitespace-padded
  dash as an uncontrolled leg-separator — a real, confirmed bug affecting 34,017 (2-leg) + 4,211 (3-leg) + 5 (4-leg)
  real catalog rows. The fix is not a from-scratch design: `unified_api_contracts.internal.InstrumentLeg` (structured
  instrument_key/side/ratio fields) and a real ticker-to-human-name registry (`ES→SP500`, `GC→GOLD`, `VX→VIX`) already
  exist and are already proven working for CME calendar spreads — CBOE/VX spreads just bypass that pathway entirely
  today, and even the working CME path doesn't yet apply the human-name translation or drop a redundant per-leg venue
  prefix.
status: active
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [instrument-id, canonicalization, tradfi, combo, spread, bug-fix, p1]
related:
  [
    ../audit/results/canonical_instrument_id_audit_2026_07_08.md,
    issues/instrument_id_format_canonicalization_2026_07_08.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
model_tier: sonnet-doable
thinking_tier: medium
source:
  "Finding 7 in instrument_id_format_canonicalization_2026_07_08.md, refined 2026-07-08 after operator pushback on an
  initial flat-string proposal that reused raw exchange tickers instead of real human-readable names ('It's not
  human-readable canonical format, right? ... The whole point of canonical mapping is not just to get the thing from the
  source where it's called. It's to map it into something human-readable'). Investigation found real, proven prior art
  (InstrumentLeg/COMBO + the tradfi_symbology human-name registry) rather than a from-scratch design question."
---

> **Real code gap, not a naming decision** — the structured leg representation and the human-name translation registry
> this plan needs both already exist in production, proven for CME. This is about wiring CBOE/VX into the same pathway
> and closing 2 gaps in that pathway itself, not inventing new infrastructure.

## Root cause

`instruments_service/reference_data/adapters/tradfi/databento/symbology.py`:

- `_parse_cme_calendar_spread_legs()` (lines 169-189) builds real
  `InstrumentLeg(instrument_key=f"{venue}:FUTURE: {front}", side="BUY"/"SELL", ratio=1)` objects for CME calendar
  spreads (`ESM6-ESU6` format), wired into `databento/adapter.py:802`. This is real, working, structured infrastructure.
- `_FUTURES_DATASETS = frozenset({"GLBX.MDP3"})` (line 108) — CME only. The comment above it is explicit: "XCBF.PITCH is
  deliberately NOT here: VX class-'S' calendar spreads are dropped (outright-only universe)." CBOE/VX spreads never
  reach this pathway at all.
- Wherever the real 34,017+ CBOE `SPOT_PAIR` rows in `prod/catalog.parquet` actually come from, it bypasses this
  infrastructure entirely — real example: `CBOE:SPOT_PAIR:VX/F1:1:S - VX/G1:1:B` (wrong type, whitespace-padded dash
  leg-separator, raw ticker+month-code instead of a human-readable symbol).
- Even the working CME path has 2 gaps: `instrument_key=f"{venue}:FUTURE:{front}"` uses the raw ccxt-native-style ticker
  (`ESM6`), not the human name via `_resolve_product_root()` (which already exists and already maps `ES→SP500`,
  `GC→GOLD`, `VX→VIX` — `unified_api_contracts.registry.tradfi_symbology`); and it repeats `VENUE:` on every leg, which
  is redundant since a combo is already scoped to one venue at its own top-level `VENUE:COMBO:...` id.

## Operator spec, 2026-07-09 — the exact leg/combo shape wanted (supersedes/refines the todos below)

Read in full before touching any todo — this is the concrete acceptance spec, not just a bug fix:

- **Per leg**: real, canonical, human-readable `instrument_key` (via `_resolve_product_root()` + the SAME `@LIN`/
  `@INV`-`YYYYMMDD`[-`STRIKE`-`C`|`P`] dated-derivative format decided for CeFi — NOT the raw exchange ticker), a
  **weight** (the existing `ratio` field), and a **direction exposed as a sign** — a consumer must be able to get a
  signed weight per leg (positive = long/BUY, negative = short/SELL) without extra lookup logic. Whether this is a new
  computed field/property on `InstrumentLeg` or a documented convention derived from `side`+`ratio` is an implementation
  choice — the requirement is that "signed weight" is directly usable, not that a new stored field is mandatory.
- **Leg count: 1 to 4 legs supported, hard cap.** A real combo with 5+ legs is dropped (not captured, not truncated) —
  log/record why (real count) rather than silently losing it. This covers every real combo shape found this session
  (2-leg: 34,017 CBOE rows + the CME calendar-spread precedent; 3-leg: 4,211; 4-leg: 5) with headroom, and deliberately
  excludes anything larger.
- **No separate stored "strategy name" field** (call calendar, put spread, butterfly, etc.) — the strategy shape is
  inferable from the legs' own properties (types, expiries/strikes, signed weights) per-leg, matching the operator's own
  reasoning: "the weights tell us that anyway." Don't add a parallel taxonomy to maintain.
- **This is now cross-asset-group, not TradFi-only** — the SAME leg shape (human-readable symbol + signed weight, 1-4
  legs) applies to CeFi's Deribit combos too (`DERIBIT-COMBO`), not just CME/CBOE. Route through the shared
  `build_leg()` (`unified_api_contracts.internal.reference.canonical_id_builder`) for both, so there's one real
  implementation, not two independently-evolving ones.
- **Migrate code AND data** — this is not a go-forward-only decision (see the resolved migration-mechanics todo below):
  existing combo rows get their `legs` re-derived from already-captured raw fields and rewritten in place, not
  re-fetched from the venue. Extends to **parquet file naming** anywhere a combo's canonical id is embedded in a
  filename (per this workspace's existing filename-vs-instrument_id convention) — MTDS and any other downstream
  reader/writer of combo data must read the new canonical shape, not the old flat string.
- **Minimize the change surface** — route everything through the shared Instrument Builder
  (`build_canonical_instrument_id`/`build_leg`) and canonical SSOT readers/writers rather than patching each consumer
  independently, so this ideally lands in a small number of real places (the builder + the write path + the affected
  adapters), not a scattered per-consumer rewrite.
- **Rollout methodology (operator, 2026-07-09)**: code fix first → smoke test on a small real sample (VM-based if
  practical) → measure real timing → report a real ETA for the full historical sweep → **pause for confirmation before
  running the full sweep** → optimize afterward once it's working correctly. Do not run an unsupervised multi-hour/day
  full sweep without reporting the smoke-test ETA back first.

## Todos

- [x] [DATA] P1. **Extend leg-parsing to CBOE/VX calendar spreads** — `_parse_cboe_spread_legs()` (new, `symbology.py`)
      parses the real, confirmed `TICKER:RATIO:SIDE` — joined-by-`" - "` shape (2-leg calendar spreads AND 3-leg
      butterflies), producing real `InstrumentLeg` objects. Wired into `adapter.py` via `_SPREAD_LEG_PARSERS` dataset
      dispatch (`XCBF.PITCH` alongside `GLBX.MDP3` in `_FUTURES_DATASETS`). Evidence: instruments-service (this
      commit) +
      `tests/unit/test_databento_tardis_adapter.py::     TestTradfiG1FoundationRegression::test_g1c_xcbf_spreads_decompose_to_combo`
      (2-leg, 3-leg, unparseable-drops, 5-leg-drops, outright-unaffected).
- [x] [DATA] P1. **Apply `_resolve_product_root()` human-name translation to leg instrument_keys** — done via the new
      shared `_build_leg_key()` helper, both CME and CBOE paths (`FUTURE:SP500`, `FUTURE:VIX`).
- [x] [DATA] P1. **Drop the redundant per-leg `VENUE:` prefix** — done via `_build_leg_key()`, both paths (legs are
      `TYPE:SYMBOL` only). **Real deviation from "route through UAC's `build_leg()`"**: UAC's real `build_leg()`
      unconditionally embeds venue and cannot produce a venue-less key — extending it is a separate, cross-repo
      (`unified-api-contracts`) follow-up, out of this fix's repo scope. See `docs/TRADFI_INSTRUMENTS.md` §11 for the
      full rationale.
- [x] [DATA] P1. **Correct the top-level instrument_type** — `SPOT_PAIR`→`InstrumentType.COMBO` for both CME and CBOE
      class-"S" rows in `adapter.py`.
- [x] [VERIFY] P1. **Confirm real output against `prod/catalog.parquet`** — real dry-run against the live bucket
      (`instruments-store-tradfi-prd-central-element-323112`, 2026-07-09) confirms the migration script's `classify()`
      predicate (same `_parse_cboe_spread_legs` the fixed adapter uses) correctly identifies the real affected
      population; unit tests confirm legs decompose correctly, human names resolve, no whitespace, `COMBO` type.
- [x] [DATA] P2. **Re-check the other 12 DEX-pool-unrelated multi-leg cases (3-leg/4-leg)** — `_parse_cboe_spread_legs`
      has no leg-count special-casing (parses N `" - "`-joined legs identically), confirmed via the 3-leg butterfly unit
      test; a real 1-4 leg hard cap (operator spec, 2026-07-09) was added so a genuine 5+-leg combo is dropped + logged,
      never truncated — no real 5-leg row exists in the live catalog today (`prod/catalog.parquet` re-read 2026-07-09: 0
      rows at 3+ legs in the CBOE population, see below).
- [x] [SCRIPT] P2. **Scope migration mechanics** — RESOLVED per the parent issue doc's operator decision: rewrite
      already-captured rows in place (never re-download). Two scripts implement this:
      `scripts/canonicalize_cboe_vx_combo_catalog_2026_07_08.py`,
      `scripts/canonicalize_dbeq_stock_class_catalog_2026_07_08.py` (K→EQUITY, adjacent finding). **Real, IMPORTANT
      finding (2026-07-09)**: `--apply` was already run once, 2026-07-08 (pre-migration snapshot blob confirmed in GCS,
      timestamp 2026-07-08 18:50:17 UTC), but `prod/catalog.parquet` is a **self-refreshing roll-up**
      (`scripts/build_instrument_catalogue.py`) that regenerated the entire catalog from the (still-unfixed) per-day
      `instrument_availability/by_date/` corpus at **2026-07-09 01:03:00 UTC** — confirmed via `gsutil stat` — which
      re-introduced a PARTIAL residual population (91 of the original 4,216 CBOE rows; 312 of the original 318 DBEQ rows
      — row-level diff against the 2026-07-08 snapshot confirms these are the SAME historical rows re-surfacing, not new
      pollution). **The historical catalog-level migration is real but NOT durable on its own** — it needs re-running
      after every rollup cycle until the upstream by_date corpus is also migrated (deferred, single-walk discipline).
      The CODE fix (this commit) IS durable: every future capture is correct going forward. Both scripts re-verified
      dry-run-safe against real, live GCS 2026-07-09 (stable across repeated runs); NOT applied in this pass — deferred
      to operator confirmation per this plan's rollout methodology (small, safe, sub-5-second single-file operation —
      91+312=403 of 1,096,472 total rows — ready to run on approval).
- [x] [SCRIPT] P2. **Ship via quickmerge**, quality-gates green. `bash scripts/quality-gates.sh --no-fix` — full suite
      green (exit 0), including the fix for a real pre-existing test-signature regression in
      `tests/unit/test_cefi_tradfi_comprehensive.py` (`_parse_cme_calendar_spread_legs` calls still passed a 2nd `venue`
      positional arg after the function's signature was narrowed to 1 arg as part of the venue-drop decision above).
- [x] [SCRIPT] P1 (filed 2026-07-09, writer-side DONE 2026-07-18). **TradFi single-leg `@LIN`/`@INV`-`YYYYMMDD`
      extension.** The parent issue doc's finding 1 was REVERSED 2026-07-09 (operator: "I'd rather adjust tradfi...
      that's the whole point of cross-AG normalisation") — TradFi single-leg dated derivatives (`FUTURE`/`OPTION`) are
      in scope for the same margin-marker suffix already shipped for CeFi. The CATALOGUE-surface writer is now
      IMPLEMENTED: `instruments-service@287d1607` — the Databento catalogue adapter emits canonical
      `PRODUCT_ROOT-USD@LIN` `instrument_key` for FUTURE/OPTION (was raw sanitized symbol), `canonical_instrument_id`
      byte-equal, old colon/month additive builder deleted. **Scope note**: this is the catalogue-adapter writer path
      only — it does not, by itself, rewrite the historical raw-tick-parquet/manifest `instrument_id` COLUMN content for
      single-leg rows already on disk; that content-level migration is tracked separately under the TradFi
      canonical-path migration effort (`plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md`).
- [ ] [SCRIPT] P2. (NEW, filed 2026-07-09) **Extend the 1-4 leg hard cap + logged-drop behavior to Deribit's existing
      combo builders** (`cefi/deribit_combo_adapter.py`, `cefi/tardis/combos.py`) — the operator spec (2026-07-09)
      explicitly made this cross-asset-group, not TradFi-only. Not attempted in this pass (untouched by this commit's
      diff; needs fresh investigation of those adapters).
- [ ] [SCRIPT] P3. (NEW, filed 2026-07-09) **Extend UAC's `build_leg()` with an opt-in venue-omission mode** so TradFi
      combo legs (and any other future venue-less-leg consumer) can route through the real shared builder instead of the
      local `_build_leg_key()` helper — cross-repo (`unified-api-contracts`), deliberately deferred out of this fix's
      scope (see the P1 "drop venue prefix" todo above for the full rationale).

## Progress Log

- **2026-07-08** — Filed after the operator correctly rejected an initial flat-string proposal for reusing raw exchange
  tickers instead of real human-readable names, and after investigation found real, proven prior art
  (`InstrumentLeg`/`InstrumentType.COMBO` + the `tradfi_symbology` human-name registry) rather than a from-scratch
  design question. No fix applied yet — this plan holds the scope. See
  [[instrument_id_format_canonicalization_2026_07_08]] finding 7 for the full evidence trail.
- **2026-07-09** — Inherited as dead WIP (dirty tree, uncommitted, stalled sibling agent — all files shared one
  git-stash-pop-signature mtime, zero further changes across 40+ minutes) and completed. Real state found: CBOE/VX
  leg-parsing, human-name translation, venue-prefix drop, `SPOT_PAIR`→`COMBO` correction, the 2 migration scripts, and
  the Databento `K`→`EQUITY` adjacent fix were ~90% done in the working tree; a real regression (stale 2-arg calls to
  `_parse_cme_calendar_spread_legs` in `tests/unit/test_cefi_tradfi_comprehensive.py`, never updated for the 1-arg
  venue-drop signature) was blocking `quality-gates.sh` — fixed. Completed in this pass: the 1-4 leg hard cap (was
  entirely missing), IBKR's `_SEC_TYPE_MAP` STK/BOND/CASH→EQUITY/BOND/CURRENCY fix (docs already claimed this was done;
  code did not actually do it — implemented for real to match), corrected the docs' stale row-count claims (yesterday's
  4,216/318 figures vs today's real 91/312 — see the migration-mechanics todo above for why they differ and why it's not
  a bug), and discovered + documented the historical-migration non-durability finding (catalog roll-up regeneration
  silently reverts the in-place fix for any date the by_date corpus wasn't also migrated). Explicitly did NOT implement:
  the TradFi single-leg `@LIN`/`@INV` extension (separate, large, filed as its own follow-up above), the Deribit combo
  leg-cap extension (cross-asset-group, filed as its own follow-up), UAC `build_leg()` venue-omission mode (cross-repo,
  filed as its own follow-up). `quality-gates.sh --no-fix` green (exit 0). Landed instruments-service@<pending — see
  commit list in the parent task's final report> together with 3 pre-existing, already-verified, unrelated commits that
  were blocked from landing only by this WIP's test regression contaminating the shared tree.
