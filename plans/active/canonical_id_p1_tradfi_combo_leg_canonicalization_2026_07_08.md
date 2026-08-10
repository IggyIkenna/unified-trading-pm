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
    /plans/archive/2026_08/canonical_id_builder_retrofit_checklist_2026_07_08.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P2
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
context_scope:
  [
    /plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/audit/results/canonical_instrument_id_audit_2026_07_08.md,
    /plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md,
    instruments-service/instruments_service/reference_data/adapters/tradfi/databento/symbology.py,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md,
  ]
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
      `tests/unit/test_databento_tardis_adapter.py::TestTradfiG1FoundationRegression::test_g1c_xcbf_spreads_decompose_to_combo`
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
- [x] ✅ [SCRIPT] P2. (NEW, filed 2026-07-09) **DONE 2026-07-27 (slot-8, data_engineering), flipped by
      `tradfi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md`'s reconciliation pass.** **Extend the 1-4 leg hard
      cap + logged-drop behavior to Deribit's existing combo builders** (`cefi/deribit_combo_adapter.py`,
      `cefi/tardis/combos.py`) — the operator spec (2026-07-09) explicitly made this cross-asset-group, not TradFi-only.
      **Evidence: instruments-service@9416be7d** — added `_MAX_COMBO_LEGS = 4` to both files;
      `deribit_combo_adapter.py::_build_legs()` now checks `len(raw_legs) > _MAX_COMBO_LEGS` and drops+logs (with
      `combo_id` context) before per-leg parsing; `tardis/combos.py::_parse_deribit_combo_legs()` checks
      `len(structure) > _MAX_COMBO_LEGS` right after resolving the structure code and drops+logs (with `code`/`raw_id`
      context) — a defensive backstop since every entry in `_DERIBIT_COMBO_STRUCTURES` today tops out at 4 legs. New
      unit tests added to `test_cefi_deribit_combo_boost.py` (`test_5_legs_dropped_not_truncated`),
      `test_cefi_tradfi_comprehensive.py` (`test_parse_combo_instrument_5_legs_dropped_not_truncated`,
      `test_parse_combo_legs_5_leg_structure_dropped_not_truncated`), all asserting drop-not-truncate.
      `quality-gates.sh --no-fix` green, shipped via `quickmerge --agent`. Full detail:
      `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s 5th todo.
- [x] ✅ [SCRIPT] P3. **DONE 2026-07-26 (slot-10, data_engineering)** — Extended UAC's `build_leg()` with an opt-in
      `include_venue: bool = True` parameter (`unified-api-contracts@e1023c80`) and migrated all 3 TradFi combo-leg call
      sites (`instruments-service@de870864`) to it, deleting the local `_build_leg_key()` helper. Full detail:
      `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md`'s corresponding todo.
- [x] ✅ [DATA] P2. **RULED 2026-08-06 (operator): go-ahead to run --apply.** `[DATA]` tag (was `[OPERATOR]`),
      AO-dispatchable — 403 of 1,096,472 rows, dry-run-verified, sub-5-second. Note this is not durable long-term; needs
      re-running after every rollup cycle until the upstream by_date corpus migration lands. **Re-apply the historical
      catalog canonicalization scripts** (`canonicalize_cboe_vx_combo_catalog_2026_07_08.py`,
      `canonicalize_dbeq_stock_class_catalog_2026_07_08.py`) against the residual 91-CBOE + 312-DBEQ rows re-introduced
      by `prod/catalog.parquet`'s self-refreshing roll-up (see the "Scope migration mechanics" todo above) — a small,
      safe, sub-5-second single-file `--apply` (403 of 1,096,472 total rows), pending operator go-ahead per this plan's
      rollout methodology. Not durable on its own; needs re-running after every rollup cycle until the upstream
      `by_date` corpus is migrated (`tradfi_canonical_path_migration_design_2026_07_19.md`). **DONE 2026-08-09 (slot-9,
      data_engineering) via `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md` todo 1.** Fresh dry-run against live
      `prod/catalog.parquet` (919,493 total rows, not the stale 1,096,472 figure) found the residual had shifted since
      drafting: CBOE 91→**0** (natural rolloff, short-dated VX spreads expired), DBEQ 312→**318** (317→EQUITY,
      1→ETF/IBIT). `--apply` completed for both scripts, GATE passed (rows unchanged, no unexpected drift), post-apply
      dry-run confirms 0 residual for both. **Not closing this permanently** — still not durable against the
      self-refreshing roll-up; needs re-running again after the next rollup cycle until
      `tradfi_canonical_path_migration_design_2026_07_19.md`'s upstream `by_date` migration lands. See the standing
      re-check todo directly below, which tracks that recurrence explicitly instead of leaving it as prose.

- [ ] [DATA] P3. **Standing reconciliation — re-check `prod/catalog.parquet` for residual CBOE `SPOT_PAIR`/DBEQ
      `SPOT_PAIR` rows after each future `build_instrument_catalogue.py` roll-up cycle.** This is the recurring
      counterpart to the item above: the CODE fix (2026-07-09) is durable for all future captures, but the historical
      catalogue rewrite is NOT — every roll-up cycle re-derives the catalogue from the still-unmigrated per-day
      `by_date` corpus and can reintroduce non-canonical rows. Not durable until
      `tradfi_canonical_path_migration_design_2026_07_19.md`'s upstream `by_date` corpus migration lands (that doc is
      the actual permanent fix; this todo is the interim mitigation). Last re-applied 2026-08-09 (0 CBOE + 318 DBEQ
      residual cleared, 0 residual confirmed post-apply). **Done when** (each cycle): re-run
      `canonicalize_cboe_vx_combo_catalog_2026_07_08.py` and `canonicalize_dbeq_stock_class_catalog_2026_07_08.py`
      dry-run against live `prod/catalog.parquet`; if either reports >0 candidates, `--apply` per this doc's rollout
      methodology, re-verify 0 residual, and re-flip this checkbox citing the fresh run evidence (mirrors the pattern of
      the item above across batch1-8). Repo: instruments-service.

## Progress Log

- **2026-08-09 (slot-9, data_engineering, via `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md` todo 1)**: Re-applied
  both historical catalog canonicalization scripts against live `prod/catalog.parquet`. Fresh dry-run found the residual
  population had shifted since the plan was drafted: CBOE 91→0 (short-dated VX spreads rolled off), DBEQ 312→318
  (317→EQUITY, 1→ETF/IBIT). `--apply` completed for both, GATE passed (rows unchanged 919,493, no unexpected
  (venue,instrument_type) drift), post-apply dry-run confirms 0 residual for both. Flipped the sole open todo, but added
  a new standing re-check todo (P3) rather than letting this doc reach 0-open-todos archive-eligible — the underlying
  non-durability (self-refreshing roll-up vs. still-unmigrated `by_date` corpus) is real and unresolved; archiving this
  doc would silently drop the only tracked place this recurring reconciliation lives, since
  `tradfi_canonical_path_migration_design_2026_07_19.md` (the doc that owns the actual permanent fix) doesn't yet
  reference this interim mitigation loop itself.
- **na-eligibility-audit 2026-08-08** (tradfi tranche, dispatch agt-29c933): **KEEP-NA, valid — the 2026-08-07 entry
  below's flagged contradiction is now RESOLVED, not open.** Independently traced via commit timestamps + a direct
  re-read of both referenced docs' CURRENT live text (not just the 08-06/08-07 self-reports): a later same-day commit
  (`unified-trading-pm@f9672e180e`, 2026-08-07T08:49:19Z UTC, ~5.3h after the 08-07 marker below was written) resolved
  it — `governance_sweep_deferred_followups_2026_08_06.md` item 1/6 now reads "RESOLVED 2026-08-07 (operator, via
  consolidated NA-blocker-digest audit): 'go ahead' confirmed as the current, correct ruling ...
  `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` was simply stale ... fixed in that doc directly," and batch7's own
  live text is now struck through with "**STALE, corrected 2026-08-07 ... 'go ahead' is the confirmed-current answer ...
  No longer operator-gated.**" This doc's own "RULED 2026-08-06 (operator): go-ahead to run --apply" todo text was right
  all along — batch7 was the stale side. Sole open todo (1/1 reconciled) already independently extracted verbatim into
  `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md` (drafted today, todo 1, `status: draft`) — doc correctly stays
  `assigned_vm: NA` pending that batch's operator review/activation, consistent with this doc's entire history (every
  prior fix here has landed via satellite-batch dispatch, then reconciled back as a checkbox flip, never a direct
  `assigned_vm` flip of this doc itself). Not reclassifying independently of batch8 to avoid a duplicate dispatch path.
- **na-eligibility-audit 2026-08-07** (tradfi tranche, dispatch agt-aca83b): **KEEP-NA — do NOT trust this doc's own
  "RULED 2026-08-06 (operator): go-ahead to run --apply" todo text at face value; do NOT reclassify.** That text (added
  `unified-trading-pm@13f80f797`, 2026-08-06T17:14:59Z) directly contradicts
  `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`'s "Deferred — operator-gated ... NOT re-asked if already asked"
  framing of the SAME residual-91-CBOE+312-DBEQ `--apply` item — batch7 was last touched 2026-08-06T14:04:44Z, ~3h
  before the "RULED" text landed here, so the contradiction is most likely just batch7 going stale rather than a
  competing ruling, but that is NOT independently confirmed by this pass. This exact contradiction is already filed as
  item 1/6 ("genuine same-day factual contradiction, highest priority of the 6") in
  `/plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md`'s conflict-check list. Resolving which side
  is current is plan_reconciler/operator territory, not this skill's (my `does_not` scope excludes corpus-wide
  contradiction reconciliation) — staying NA until that already-filed conflict resolves, not re-deriving or re-filing a
  duplicate ruling here.
- **na-eligibility-audit 2026-08-03** (tradfi tranche, dispatch agt-06b4c6): **KEEP-NA, valid — re-verified, disposition
  unchanged.** The 2026-08-02 plan-hygiene sweep (`17b53df1`) converted this doc's prose-only remaining action into a
  real `- [ ] [OPERATOR] P2` checkbox ("Re-apply the historical catalog canonicalization scripts") — a formatting
  change, not new content: the SAME residual (91-CBOE + 312-DBEQ rows) and the SAME operator-gating (this plan's own
  "Rollout methodology" section, ¶114-117: pause for confirmation before any unsupervised sweep) that the 2026-07-31
  pass below already assessed when this was still buried in the "Scope migration mechanics" prose. No stale items, no
  duplicate claim elsewhere, no reclassify — a GCS-catalog `--apply` rewrite genuinely awaiting the recorded operator
  go-ahead, now just correctly tracked as its own checkbox instead of a prose aside.
- **na-eligibility-audit 2026-07-31** (tradfi tranche, dispatch agt-6d6eaf): **KEEP-NA, valid.** 0 open checkboxes
  (matches tranche-inventory tool), but this doc is a live "prose-only remaining work" case — the entry below already
  self-flags that it does not genuinely reach 0 open todos (the residual 91-CBOE + 312-DBEQ historical catalog `--apply`
  reapply). That residual is operator-gated on citation alone: the doc's own "Rollout methodology (operator,
  2026-07-09)" section (pause-for-confirmation before any unsupervised sweep) explicitly covers it, and a fresher,
  independent 2026-07-29 pass (`tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`'s own "Deferred — operator-gated"
  section) re-confirmed the same disposition 2 days ago. No stale items, no duplicate claim, no reclassify — the pending
  action is a GCS-catalog `--apply` rewrite genuinely requiring the recorded operator go-ahead.
- **2026-07-30 (tradfi_satellite_ao_dispatch_batch1_finalize reconciliation pass)** — Flipped the Deribit 1-4 leg
  hard-cap checkbox to `[x]`, citing `instruments-service@9416be7d` (verified reachable). This was the doc's only
  remaining `- [ ]` checkbox — but `status` stays `active`, NOT `resolved`: the "Scope migration mechanics" `[x]` item
  above documents a genuinely still-open prose-form action (the historical catalog `--apply` rewrite for the residual 91
  CBOE + 312 DBEQ rows is deferred pending operator confirmation, and is not durable against the self-refreshing
  `prod/catalog.parquet` roll-up until the upstream `by_date` corpus is migrated per
  `tradfi_canonical_path_migration_design_2026_07_19.md`) — this doc does not genuinely reach 0 open todos.
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
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: re-verified context_scope (6 entries), unchanged — already carries the databento
  symbology.py source path and all entries still resolve.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — swapped the now-superseded
  `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md` pointer (its cited todo is long `[x]` done) for
  `/plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md`, which is actively tracking the same-day
  contradiction the 2026-08-07 na-eligibility-audit entry above flags on this doc's sole open todo (the "RULED
  2026-08-06: go-ahead to run --apply" text vs. `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`'s
  still-operator-gated framing of the identical residual-91-CBOE+312-DBEQ item) — a worker picking up that todo needs
  this pointer before running `--apply`.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tradfi tranche, dispatch agt-3df41f) [body-hash:07b1aaeea1fc99f4]: **KEEP-NA,
  valid -- confirmed unchanged.** Phase-0 flagged this doc as "changed since the 08-08 marker" (git-date fallback), but
  `git diff <08-08-marker-sha>..HEAD` shows the ONLY intervening change is the context-scout line directly above (a
  context_scope refresh) -- zero todo/verdict content changed. Reaffirming the 08-08 verdict without a fresh full
  re-read; see `na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md` for the underlying
  false-positive class this run found and filed.
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:1c528fd3236a536e]: **KEEP-NA,
  valid -- fresh full read; considered and DECLINED promoting to RECLASSIFY.** The sole open todo (standing
  reconciliation: re-run 2 already-built/tested scripts dry-run after each future catalogue roll-up cycle, `--apply`
  only if residual >0, small/idempotent, operator go-ahead already on record and executed 8x) reads as bounded for any
  SINGLE execution, but its own framing is explicitly a perpetual "after each future roll-up cycle" check, not a
  one-shot outcome -- flipping `assigned_vm` here would let the backlog derive ONE dispatch from this ONE checkbox; a
  worker would run it once, flip the checkbox `[x]`, and the standing safety net for every LATER roll-up cycle would
  have no open item left to catch it. That is a structural mismatch between "standing/recurring" checks and the
  checkbox-driven one-shot dispatch mechanism, not a judgment call this doc's content itself resolves. Independently
  corroborated same-day: `/ag-closeout-audit tradfi`'s `tradfi_satellite_ao_dispatch_batch11_2026_08_10.md` (drafted
  hours earlier) evaluated this exact doc/item and reached the same conclusion under its own criteria -- filed under
  "Deferred -- standing/recurring (not a single bounded AO outcome)." Two independent audit mechanisms agreeing today is
  a strong signal, not a coincidence to re-litigate; staying KEEP-NA. `assigned_vm` unchanged.
