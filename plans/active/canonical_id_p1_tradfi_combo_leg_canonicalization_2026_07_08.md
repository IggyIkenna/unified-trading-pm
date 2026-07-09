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

- [ ] [DATA] P1. **Extend leg-parsing to CBOE/VX calendar spreads** — either generalize
      `_parse_cme_calendar_spread_legs()` beyond `GLBX.MDP3`, or add a CBOE-specific equivalent, so VX spreads produce
      real `InstrumentLeg` objects instead of landing as an undecomposed flat string. Confirm real production CBOE
      spread symbol shapes first (the audit's `VX/F1:1:S - VX/G1:1:B` example used a slash-separated ticker+month-code
      form, not CME's concatenated `ESM6` form — don't assume the same parser regex works verbatim).
- [ ] [DATA] P1. **Apply `_resolve_product_root()` human-name translation to leg instrument_keys** (both the existing
      CME path and the new CBOE/VX path) — legs should read `FUTURE:SP500`/`FUTURE:VIX`, not `FUTURE:ESM6`/
      `FUTURE:VX/F1` or similar raw ticker forms.
- [ ] [DATA] P1. **Drop the redundant per-leg `VENUE:` prefix** in `_parse_cme_calendar_spread_legs()`'s
      `instrument_key` construction — legs should be `TYPE:SYMBOL` only, venue is already carried once at the combo's
      own top-level id.
- [ ] [DATA] P1. **Correct the top-level instrument_type** for these rows from the reused `SPOT_PAIR` to the real
      `InstrumentType.COMBO` (already exists, `symbology.py:60`, `_CLASS_TO_TYPE["T"]`).
- [ ] [VERIFY] P1. **Confirm real output against `prod/catalog.parquet`** for a real CBOE/VX spread post-fix — legs
      decompose correctly, human names resolve, no whitespace anywhere, `instrument_type=COMBO`.
- [ ] [DATA] P2. **Re-check the other 12 DEX-pool-unrelated multi-leg cases** (finding 7's 4,211 three-leg + 5 four-leg
      rows) for the same treatment — the 2-leg case above is the primary target; confirm 3-leg/4-leg spreads route
      through the same generalized parser without special-casing leg count.
- [ ] [SCRIPT] P2. **Scope migration mechanics** — go-forward-only (new captures use the fixed pathway, historical rows
      keep the old flat-string shape) vs. a real backfill of the 34,017+/4,211+/5 affected historical rows;
      operator-decision-gated per this workspace's migration-mechanics discipline, don't decide unilaterally.
- [ ] [SCRIPT] P2. **Ship via quickmerge**, quality-gates green.

## Progress Log

- **2026-07-08** — Filed after the operator correctly rejected an initial flat-string proposal for reusing raw exchange
  tickers instead of real human-readable names, and after investigation found real, proven prior art
  (`InstrumentLeg`/`InstrumentType.COMBO` + the `tradfi_symbology` human-name registry) rather than a from-scratch
  design question. No fix applied yet — this plan holds the scope. See
  [[instrument_id_format_canonicalization_2026_07_08]] finding 7 for the full evidence trail.
