---
doc_type: issue
title:
  TradFi COMBO bundle candidates never reach the G1-ENUM expected-universe denominator at all — the catalog-seed-side
  composite instrument_id mis-parse (`_derive_underlying`'s naive `"-"`-split) feeds a garbage `base_ccy` into the
  MVP-universe gate, wrongly excluding real MVP-eligible combos (incl. the ES/S&P-500 complex) BEFORE any candidate is
  ever emitted — root cause confirmed via real production probe
summary: >-
  While wiring the UAC underlying-naming reverse-lookup into the G1-ENUM present-set rollup fix
  (`tradfi_combo_underlying_naming_mismatch_blocks_g1_enum_present_rollup_2026_07_28.md`), the real production
  before/after quantification for tradfi showed the EXACT SAME `expected_unattempted` total (503,588) and the exact same
  per-instrument_type breakdown before and after the naming-value reconciliation fix — `combo` does not appear in either
  breakdown, at all. Traced to source: the catalog's 59,103 `COMBO`-typed leaf rows (58,765 of them with a BLANK
  `underlying` column and a composite `instrument_id` like `"CME:COMBO:6AF1-6AU0"`) DO roll up into 3,818 synthetic
  per-underlying combo bundle candidates via `_rollup_bundle_grain` (confirmed via direct probe) — but
  `_derive_underlying`'s naive `"-"`-split heuristic mis-parses the composite id, producing a GARBAGE key like
  `"CME:COMBO:6AF1"` or `"CBOE:COMBO:VX/F7:1:S"` instead of the real product root (`"6A"`/`"VX"`). That garbage value
  becomes the rolled-up entry's `underlying`, which `_tradfi_entry_in_mvp_universe` then passes as `base_ccy` into the
  UAC `is_mvp()` MVP-universe predicate — and a garbage `base_ccy` NEVER matches any MVP underlier, so `is_mvp()`
  returns `False` and `_enumerate_v2_tradfi` `continue`s past the WHOLE instrument (`scripts/enumerate_expected_
  universe.py` line ~1815) before the per-date/per-data_type loop ever runs. **Every combo bundle candidate is silently
  dropped before it can become an `expected_unattempted`, `empty_confirmed`, OR a present-set-matched row — the
  present-set naming-value reconciliation fix has nothing to reconcile against, because the seed itself never reaches
  the comparison.** Confirmed live: `is_mvp("tradfi", "CME", "OPTION", base_ccy="CME:COMBO:ESU4")` → `False`;
  `is_mvp("tradfi", "CME", "OPTION", base_ccy="ES")` → `True` — the SAME (venue, itype) pair, differing only in whether
  the underlying resolved to the real root. This means real MVP-eligible ES-complex (S&P 500) combo instruments —
  explicitly the ONLY tradfi options/combo underlier the 2026-07-14 operator ruling put in MVP scope — are being wrongly
  excluded from the expected-universe denominator entirely, not merely mis-keyed.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [g1-enum, expected-universe, tradfi, combo, mvp-gate, underlying-naming, data-correctness]
related:
  [
    /plans/active/issues/tradfi_combo_underlying_naming_mismatch_blocks_g1_enum_present_rollup_2026_07_28.md,
    /plans/active/issues/tradfi_combo_uppercase_casing_manifest_residual_2026_07_28.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: 2026-07-28
priority: P1
parent_epic: infrastructure_master
source:
  "autonomous dispatch, tradfi combo underlying-naming reverse-lookup wiring task, discovered via a real production
  before/after quantification showing 0 change for combo/futures_chain/options_chain, 2026-07-28"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
  "instruments-service@5853635b -- resolved directly in an interactive/autonomous session, NOT via AO backlog dispatch
  (assigned_vm: planning was never claimed -- locked_by empty throughout); noting here so the backlog regen doesn't
  redispatch already-completed work."
locked_by:
locked_since:
---

# TradFi COMBO bundle candidates never reach the expected-universe denominator — seed-side composite-id mis-parse feeds a garbage `base_ccy` into the MVP gate

## What I found

Dispatched to wire the UAC `resolve_tradfi_underlying_to_root` reverse-lookup into `_rollup_present_bundle_grain` /
`_derive_underlying` (the PRESENT-SET/manifest-side naming-value reconciliation — see the sibling issue), the task's own
"quantify first" instruction required a real before/after production run. Both an unfixed copy and the shipped fix were
run scan-only (`--apply-write` NOT passed, `--max-writes-per-run 5000000` to clear the 1M default halt-safety over full
2018-01-01..2026-07-28 history) against the live prod catalog + manifest
(`instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet`,
`market-data-tick-tradfi-prd-central-element-323112`):

- Total candidate rows: **1,958,920 → 1,958,920** (0 change)
- `expected_unattempted`: **503,588 → 503,588** (0 change), byte-identical per-instrument_type breakdown BOTH times:
  `equity 386,588 / future 49,598 / futures_chain 39,431 / index 20,900 / spot_pair 4,484 / options_chain 2,587` —
  **`combo` does not appear in the breakdown at all, in either run.**
- Confirmed via direct probe: **zero** `instrument_type=combo` rows exist anywhere in the FULL candidate output (any
  `capture_status`), for a full-history run AND for a single-day (`2024-06-03`) run with an EMPTY present_set (nothing
  captured) — if combo candidates were being generated at all, an empty present_set would have to surface them as
  `expected_unattempted`/`empty_confirmed`. None appeared.

Traced the root cause with a direct probe of the pipeline stages:

1. The catalog has 59,103 `COMBO`-typed leaf rows; 58,765 have a BLANK `underlying` column and a composite
   `instrument_id` (`"CME:COMBO:6AF1-6AU0"`, `"CBOE:COMBO:VX/F7:1:S"`, …).
2. `_rollup_bundle_grain(catalog, "tradfi")` DOES process these — it produces **3,818** synthetic
   `instrument_type= combo` bundle candidates (confirmed via direct call). So the SEED-SIDE roll-up is not the blocker.
3. But `_derive_underlying`'s pre-existing naive `"-"`-split heuristic (`iid.split("-", 1)[0]` when `"-" in iid`)
   mis-parses these composite ids — `"CME:COMBO:6AF1-6AU0"` → `"CME:COMBO:6AF1"` (garbage; NOT the real root `"6A"`),
   `"CBOE:COMBO:VX/F7:1:S"`-style ids similarly mis-parse. Of the sampled rolled-up combo candidates, only entries whose
   instrument_id happened to already be a clean root (e.g. a bare `"CL"`) survived correctly — the overwhelming majority
   get a garbage `underlying`/`instrument_id` key.
4. That garbage value becomes the synthetic catalog entry's `underlying`. `_tradfi_entry_in_mvp_universe` (called from
   `_enumerate_v2_tradfi`, line ~1815, BEFORE the per-date/data_type loop) computes
   `base_ccy = (instr.base_asset or instr.underlying).strip().upper()` — for the synthetic combo entry this IS the
   garbage key — and passes it to UAC `is_mvp("tradfi", venue, "OPTION", base_ccy=<garbage>)`.
5. **Confirmed live**: `is_mvp("tradfi", "CME", "OPTION", base_ccy="CME:COMBO:ESU4")` → `False`;
   `is_mvp("tradfi", "CME", "OPTION", base_ccy="ES")` → `True`. Same (asset_group, venue, itype) triple — the ONLY
   difference is whether the underlying resolved to the real root. Per the 2026-07-14 operator ruling ("tradfi MVP
   options scope = the S&P 500 complex ONLY"), `ES` IS the one underlier that should pass this gate for combo/option
   cells — but a garbage key from the id mis-parse means it never does.
6. `_tradfi_entry_in_mvp_universe` returning `False` makes `_enumerate_v2_tradfi` `continue` past the WHOLE instrument
   (line ~1815-1816) — no per-date loop runs, so NO row (candidate, `expected_unattempted`, `empty_confirmed`, OR
   present-set-matched) is EVER emitted for it. The present-set/manifest-side naming-value reconciliation (the sibling
   issue's fix) never gets a chance to run, because the seed candidate this session's fix was built to reconcile against
   never exists in the first place.

## Why this matters (real production impact, not theoretical)

- This is a genuine **data-correctness** finding, not a cosmetic one: real, MVP-eligible tradfi combo captures (the
  ES/S&P-500 complex specifically, per the standing 2026-07-14 operator ruling) are being wrongly excluded from the
  expected-universe denominator ENTIRELY — not merely mis-keyed or mis-counted. A combo capture that IS real, captured,
  and SHOULD be MVP-scoped is invisible to the coverage math on BOTH sides (it neither inflates a phantom
  `expected_unattempted` cell NOR gets credited as `captured` coverage) because the row never gets seeded to begin with.
- This explains — precisely and completely — why the sibling naming-mismatch fix (present-set-side reconciliation,
  SHIPPED this session, `instruments-service` `_derive_underlying`/`_rollup_present_bundle_grain`) produced a real,
  provably-correct, unit-tested mechanism (`"HEATING-OIL"` → `"HO"` reconciliation, proven via
  `test_build_present_set_reconciles_already_populated_spelled_out_underlying`) that nonetheless shows **zero** measured
  impact in a full production run: the mechanism is correct, but the SEED it was built to reconcile against is being
  filtered out one stage earlier, by a DIFFERENT bug on the CATALOG/seed side (not the manifest/present-set side this
  session was scoped to).
- Distinct from BOTH sibling issues: NOT the naming-value mismatch (present-set side, already fixed), NOT the
  `COMBO`-uppercase casing residual (manifest-index cosmetic issue). This is a THIRD, independent bug — a
  composite-instrument-id PARSING failure on the catalog-seed side that cascades into an MVP-universe FALSE EXCLUSION.

## Recommended next step

`_derive_underlying`'s `"-"`-split fallback needs to recognise and correctly parse `VENUE:COMBO:<LEG1>-<LEG2>`-shaped
composite ids (and the CBOE `VX/<expiry>:<n>:S`-shaped calendar-spread ids) BEFORE falling back to the naive first-token
split — e.g. strip a recognised `<VENUE>:<TYPE>:` prefix, then apply the same `_SINGLE_FUT_RE`-style root-extraction
(`^([A-Z0-9]{1,5})([FGHJKMNQUVXZ])(\d{1,2})$`, already used elsewhere for futures month/year parsing) to the first leg
to recover the real product root (`"6AF1"` → `"6A"`, `"ESU4"` → `"ES"`). This is a SEED-SIDE (`_rollup_bundle_grain`,
catalog path) fix, distinct from the present-set-side reconciliation this session shipped — genuinely separate code
path, separate blast radius (affects the MVP gate for every combo instrument, not just present-set matching), and needs
its own before/after production quantification once fixed (expect `combo` to start appearing in the candidate breakdown
at all, where today it is completely absent).

**Priority P1** (not P0) because it is a real, confirmed, silent denominator-correctness gap on a live-traded MVP
complex (ES options/combo) — but it is not actively corrupting a customer-facing number today (the coverage % this feeds
is already known-incomplete for tradfi per other open items), so it does not require an emergency freeze.

## Progress Log

- 2026-07-29 (autonomous session, resumed after a session-limit crash mid-workflow): implemented the recommended fix —
  `_derive_tradfi_combo_root` strips a recognised `VENUE:COMBO:` prefix and extracts the real product root from the
  first leg (root+month-code+year, same shape as the existing `futures_factory.py` precedent), validated against
  `TRADFI_ROOTS` so an unresolved shape falls through to the pre-existing "-"-split byte-identical to before
  (under-matching beats mis-keying, unchanged). Also handles the CBOE `VX/<expiry>:<n>:<side>` calendar-spread leg
  shape. Real production sampling (distinct COMBO `instrument_id` values pulled live from the prod catalog, not
  synthesised) confirmed the fix across every real shape found: CME single/multi-letter roots, digit-leading currency
  futures, crypto (`BTCG2`), CBOE `VX`, and the ICE whitespace-token shape (falls through correctly to the
  already-shipped ICE handling). **Found a SECOND, deeper bug via real end-to-end verification that a
  synthetic-fixture-only test could not have caught**: even with the id-parse fixed, the full pipeline still showed ZERO
  combo candidates. Root cause: the instruments-service catalog pre-tags EVERY COMBO leaf row `mvp=False`
  UNCONDITIONALLY (confirmed live: all 59,228 catalog COMBO rows, never `None`) — `_tradfi_entry_in_mvp_universe`'s
  "prefer the pre-tagged mvp column" behavior short-circuited before the live MVP predicate ever saw the roll-up's
  correctly-resolved underlying. Fixed by adding a `base_override` parameter that bypasses the pre-tag specifically for
  COMBO leaves in the bundle-mvp roll-up (narrowly scoped — an initial broader version that bypassed the pre-tag for ALL
  tradfi bundle types regressed a real futures_chain/options_chain test fixture, caught by re-running the full test
  suite before shipping, then narrowed to `instr.instrument_type.upper() == "COMBO"` only). **Real production
  before/after quantification** (full `2018-01-01..2026-07-28` tradfi scan, scan-only, live prod catalog + manifest):
  `combo` went from **0 rows** in the `expected_unattempted` breakdown (baseline, both pre- and post- the sibling
  naming-mismatch fix) to **1,652 rows** (3,112 total combo candidates incl. `empty_confirmed`) — **every single one
  correctly keyed `underlying=ES`**, the sole MVP-scoped tradfi combo underlier per the 2026-07-14 operator ruling,
  confirming the fix targets exactly the right instrument and nothing else leaked in. 19 new/extended unit tests
  (composite-id parse across real shapes, unresolvable-root fallback, non-tradfi/no-prefix regression guards, the
  mvp-pretag-bypass mechanism with both the bug-reproduction and fixed-behavior cases, and an end-to-end rollup test
  asserting the synthetic entry itself carries `mvp=True`) plus the full existing 227-test suite green. **DONE —
  `instruments-service@5853635b`.**
