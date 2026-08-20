---
doc_type: plan
title: Instruments catalogue — one definitions aggregation, monthly grain, with field-change history
summary: >-
  Downstream consumers need ONE aggregated instrument-definitions catalogue, not daily dumps. Today the rolled-up
  catalogue lacks the definitions themselves, so consumers still read day by day. Target: a monthly-grain catalogue
  already split by venue, carrying the definitions, plus a narrow field-change history so a point-in-time query
  resolves correctly when a mutable attribute (tick size, contract size, protocol risk params) changes — without
  full-row versioning blowing up storage. Also declares which attributes are deliberately STATIC in UAC and never
  historised, and adds a gate that downstream services query the catalogue rather than deriving attributes themselves.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, unified-api-contracts, market-tick-data-service, features-service, strategy-service, execution-service]
scope: [engineer, admin]
tags: [instruments, catalogue, slowly-changing-dimensions, point-in-time, registry-ssot, backtest-correctness]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /codex/04-architecture/instrument-universe-registry-consolidation.md,
  ]
created: 2026-08-17
source: >-
  Operator direction 2026-08-17. The storage-efficient history design is a PROPOSAL for operator review — the operator
  set the requirement ("a smart way to do that") and did not prescribe the mechanism.
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: design
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 3.6
assigned_role: infra
effort: high
last_updated: "2026-08-20"
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /codex/04-architecture/instrument-universe-registry-consolidation.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/active/strategy_service_centralization_fixes_2026_08_16.md,
    instruments-service/scripts/migrate_instrument_availability_hive_2026_08_03.py,
  ]
---

# Instruments catalogue — definitions aggregation with field history

> Parent epic: [`/plans/epics/system_readiness_master.md`](/plans/epics/system_readiness_master.md). Related gate
> register: [`/plans/active/data_pipeline_completion_2026_08_21.md`](/plans/active/data_pipeline_completion_2026_08_21.md).

## The requirement, restated

**Downstream consumers ultimately need one thing: the aggregated instrument definitions.** They do not need the daily
dumps. The rolled-up catalogue is the right shape — but today it does not actually carry the instrument definitions,
so consumers fall back to reading day by day, which is the wrong grain and the wrong cost.

**Target grain: monthly, grouped, already split by venue.** Scale is modest — expected to stay within a few hundred
thousand to ~1M rows, so this is not a big-data problem and should not be engineered as one. A consumer wanting the
state for a given period queries that month's catalogue rather than reconstructing it from dailies.

## MEASURED STATE — 2026-08-17, live PROD buckets via the UTL SDK

Read directly from `instruments-store-{ag}-prd-central-element-323112`. **This changes the scope from what the
requirement assumed** — three findings are larger than "the roll-up lacks definitions".

**1. The rolled-up catalogue does not exist at all.** `catalogue/` is **EMPTY in all four asset groups** (cefi, defi,
tradfi, sports). The code writes a `catalogue/registry` path (`orchestrator/sink.py`) but nothing is there. So this is
not "the roll-up is missing definitions" — there is no roll-up to add definitions to. It is a build, not a fix.

**2. The daily dump already carries the full definitions — 51 columns.** Measured on one canonical cefi file
(`day=2019-03-30`, `venue=DERIBIT`): 295 rows, 51 columns, including every attribute this plan cares about:

```
instrument_key · venue · instrument_type · raw_symbol · base_asset · quote_asset · canonical_instrument_id
product_root · status · available_from_datetime · available_to_datetime · asset_class · settle_asset
tick_size · min_size · contract_size · expiry · strike · option_type · exercise_style · underlying
margin_type · legs · is_trading_day · regular_open_utc · regular_close_utc · early_close_utc
pre_market_open_utc · post_market_close_utc · auction_open_utc · auction_close_utc · holiday_calendar
timezone · pool_address · pool_fee_tier · base_asset_contract_address · quote_asset_contract_address
base_asset_decimals · base_asset_symbol_onchain · quote_asset_decimals · quote_asset_symbol_onchain
atoken_address · debt_token_address · rate_method_selector · source_archive_url_template
source_record_types · source_coverage_start · source_coverage_end · listed_at · delisted_at · available_at
```

**So the definitions are not missing — they are only reachable at the wrong grain.** The mutable fields this plan is
built around are all present (`tick_size`, `contract_size`, `min_size`, `pool_fee_tier`, `rate_method_selector`), and
some temporal fields already exist (`available_from_datetime`/`available_to_datetime`, `listed_at`, `delisted_at`,
`available_at`) — **but there is no change-history mechanism**: no `changed_at`, no prior value. Point-in-time truth
today is implicit in which day's file you happen to read.

**3. Path duplication and stale backups are material.** In a bounded 4,000-blob sample of cefi:

| Class | Count | Note |
| --- | --- | --- |
| Canonical (`pipeline_mode=` + `asset_group=`) | 2,730 | the intended shape |
| **NON-canonical** (no `pipeline_mode`, no `asset_group`) | **1,000** | same day+venue as a canonical twin, and a *different size* (23,959 B vs 33,468 B) — a narrower older schema, not a copy |
| **`.bak` files in PROD** | **270** | e.g. `instruments.usdlin.20260718-164721.bak.parquet`, dated 2026-07-18 |

Roughly **a third of sampled objects are either a non-canonical duplicate or a stale backup.** This is the
backup/stale-path cleanup already named in the parent epic's W4, now quantified.

**4. Sports uses a different path grammar** — `day=/league=/venue=`, with no `pipeline_mode=` or `asset_group=`
segment. Any roll-up must handle both grammars or normalise them first.

**5. `prediction` has NO `instruments-store` bucket at all** — the registry offers only CEFI, DEFI, SPORTS, TRADFI.
That is a scope gap, not a naming detail.

**RE-MEASURED 2026-08-18 (corpus-wide, not sampled) — findings 3 and 4 across all four asset groups.** Full
prefix-scoped listing (`client.list_blobs(bucket, prefix="instrument_availability/by_date/")`, the SAME bounded
prefix `instruments-service/scripts/migrate_instrument_availability_hive_2026_08_03.py` already sizes — sanctioned
route #1/#3 of the single-walk constraint, `four-surface-reconciliation-procedure.md` §5; never a whole-bucket walk).
Classification: canonical = path contains both `/pipeline_mode=` and `/asset_group=`; `.bak` = filename contains
`.bak.`; everything else = non-canonical.

| AG     | total (this prefix) | canonical         | non-canonical                | `.bak`               |
| ------ | -------------------- | ------------------ | ----------------------------- | ---------------------- |
| cefi   | 49,340                | 42,985 (87.1%)      | 1,706 (3.5%)                    | 4,649 (9.4%)              |
| defi   | 141,866               | 110,344 (77.8%)     | 31,522 (22.2%)                  | 0 (0%)                    |
| tradfi | 32,945                | 15,746 (47.8%)      | 67 (0.2%)                       | **17,132 (52.0%)**        |
| sports | 362,347               | 180,031 (49.7%)     | **182,316 (50.3%)**             | 0 (0%)                    |

**Cross-check against the bounded cefi sample above (1,000/4,000 = 25% non-canonical, 270/4,000 = 6.75% `.bak`):**
the corpus-wide non-canonical ratio for cefi is now far lower (3.5% vs. 25%) — consistent with the flat→hive
migration having EXECUTED for cefi/defi/tradfi/prediction between the original sample and this re-measurement
(`canonical-cutover-register.md` §6b, `non-canonical-path-inventory.md` item 16: 84,320/117,166 flat objects
copied-to-hive-and-purged). The `.bak` ratio, by contrast, is HIGHER corpus-wide (9.4% vs. 6.75%) — that migration
never touched `.bak` files at all, so the stale-backup problem is undiminished; **tradfi is the standout, at 52% of
its `instrument_availability` tree** — worse than the cefi sample implied and not previously quantified per-AG.
defi and sports show **0** `.bak` objects in this specific prefix (none found; may exist elsewhere in those
buckets outside this bounded prefix — out of scope for this measurement, not asserted absent bucket-wide).
**Finding 4 confirmed corpus-wide**: sports is 50.3% non-canonical under this classifier — its live writer emits
the `day=/league=/venue=` grammar (no `pipeline_mode=`/`asset_group=` keys) documented in
`non-canonical-path-inventory.md` item 16's residual note, not a sampling artifact.
**Scope caveat**: bounded to the `instrument_availability/by_date/` prefix (the dominant tree per finding 1 — no
other tree scoped here); does not claim bucket-wide coverage of every root.

**Sizing check — the operator's estimate holds.** cefi runs daily from 2019-03-30 at ~295 rows per venue-day. A
monthly-grain roll-up over ~25 venues × ~90 months × ~300 rows lands around **675k rows** — inside the
"few hundred thousand to ~1M" the operator predicted, and roughly a **30× object-count reduction** versus daily. The
grain change is justified on both counts.

- [x] ✅ [DATA] P1. Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 11 (na-eligibility-audit 2026-08-17). Re-measure findings 3 and 4 across all four asset groups. The dual-path/`.bak` figures above are a
      *bounded 4,000-blob cefi sample*, not a full census — the ratio may differ per AG, and a cleanup scoped from one
      sample would be wrong. Use the manifest, not a new whole-corpus walk.

## Why this cannot be a simple snapshot — the corner case that drives the design

Most instrument attributes are stable. A few genuinely change, and they are exactly the ones a backtest is sensitive
to:

| Attribute | Changes? | Consequence if stale |
| --- | --- | --- |
| **Tick size** | **Yes** | Fills round to the wrong grid; a backtest silently prices at impossible levels |
| **Contract size** | **Yes** | Every notional and PnL figure is wrong by a multiple |
| **Protocol risk params** (e.g. per-pool/per-instrument risk parameters on lending venues, changed by governance) | **Yes** | Liquidation and health-factor logic evaluates against parameters that were not in force |
| DeFi contract addresses | Believed **no** | — (assumption to verify, not assert) |
| Instrument type, venue, identity | No | — |

So the catalogue must answer **"what was true then"**, not only "what is true now" — while the *default* read stays
"latest is the truth".

## Proposed design — current-state + narrow change log (for operator review)

The obvious approach is full-row versioning (one row per instrument per version). **Rejected**: storage grows as
`rows × versions × full row width`, and every immutable field is duplicated on every change to a mutable one. With ~1M
instruments and wide definition rows, that inflates fast for a handful of real changes.

**Proposed instead — three artefacts, each cheap:**

1. **Current-state catalogue** — one row per instrument, the latest truth, partitioned by venue as today. This is what
   the overwhelming majority of consumers read, and it stays the default.
2. **Monthly catalogue** — the rolled-up definitions at monthly grain, split by venue. This is the point-in-time read
   surface for a period-scoped query, and the thing that replaces day-by-day reading.
3. **Field-change log** — a NARROW table, appended only when a mutable field actually changes:
   `(instrument_id, venue, field_name, changed_at, old_value, new_value, source, observed_at)`.

**Why this stays small**: storage is proportional to **the number of actual changes**, not to rows × versions. Only
fields declared mutable can ever enter the log, so stable attributes contribute nothing. A tick-size change on one
instrument costs one narrow row, not a duplicated definition row.

**Point-in-time semantics**: latest state is a direct read. State as of date D is the current state with the change log
replayed backwards for any field whose `changed_at > D` — or, for coarse queries, simply that month's catalogue.
Both paths must return the same answer, and that equivalence is a test, not an assumption.

- [ ] [OPERATOR] P0. **Ratify or replace this design.** The requirement is the operator's; the mechanism is a proposal.
      The decision worth making explicitly: current-state + narrow change log (above) versus monthly snapshots alone
      (simpler, but cannot resolve an intra-month change) versus full-row versioning (simplest to query, most
      expensive to store).
- [ ] [BACKEND] P0. **Declare the mutable-field set explicitly in UAC.** Only declared-mutable fields are historised.
      A field that changes but was never declared mutable is a silent correctness bug — so the declaration is the
      control, and adding a field to it is a deliberate act.
- [ ] [BACKEND] P0. **Add the definitions to the rolled-up catalogue** at monthly grain, split by venue — the actual
      gap that currently forces day-by-day reads.
- [ ] [BACKEND] P0. **Implement the field-change log** with the schema above, written by the same writer that updates
      current state, in the same transaction/step — never a later reconciliation pass, or the two drift.
- [ ] [BACKEND] P1. **Prove point-in-time equivalence**: for a sampled set of instruments and dates, the change-log
      replay and the monthly catalogue agree. Include a negative control — a known tick-size change must make a naive
      latest-state read visibly wrong.
- [x] ✅ [BACKEND] P1. Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 12 (na-eligibility-audit 2026-08-17). Verify the DeFi-address immutability assumption rather than carrying it as belief. If
      addresses can change (migration, proxy upgrade), they are mutable and belong in the declared set.
- [ ] [BACKEND] P1. **Measure the real storage cost** of the change log over a representative period, so the
      "stays small" claim is a number rather than an argument.

## Deliberately STATIC in UAC — not historised

Per operator direction, these stay as current-state declarations in UAC. Recording their history would add cost for no
backtest benefit:

- **Exchange liquidation rules** — marginal difference for backtesting; current state is sufficient.
- **Exchange protocols, endpoints, WebSocket details** — if an endpoint changes we do not need the old one; it does not
  affect a backtest.
- **League ID identities.**

**Stating this explicitly is the point.** The boundary between "historised in the catalogue" and "static in UAC" should
be a recorded decision, not an accident of which one someone happened to implement.

## The query-don't-derive gate

- [ ] [BACKEND] P0. **A downstream service must query the catalogue for an instrument attribute, never derive or hardcode it.**
      Tick size and contract size are the specimens: a service computing its own tick size is carrying
      a stale copy of a mutable field. Add a check that fails when a consumer hardcodes an attribute the catalogue
      owns — this is the same class as the reference-data-in-a-code-path rule in
      [`/plans/active/strategy_service_centralization_fixes_2026_08_16.md`](/plans/active/strategy_service_centralization_fixes_2026_08_16.md),
      and the two checks should share one discriminator rather than inventing a second.
- [ ] [BACKEND] P1. **Provide the queryable field so a service does not have to derive it** — where a consumer today
      computes something the catalogue could state, add the field. UAC can canonically tag it.

## Access pattern — read the published catalogue, not the service

**Every service eventually needs to know an instrument attribute.** That must not become a service-to-service
dependency: consumers read the **published catalogue artefact** (GCS for batch, the event stream for live), exactly as
strategy-service reads published ML outputs rather than calling an ML service. instruments-service remains the SSOT and
the publisher; it does not become a runtime dependency in every other service's call graph. A direct call would violate
the tier rule; reading the published artefact does not.

## Noted, not scoped — corporate actions

**Corporate actions are the transient class that would genuinely break a backtest** (splits, symbol changes,
delistings). They belong to features rather than the instruments catalogue, and per operator direction they are **not
essential for MVP**. Recorded here so the gap is known rather than discovered later.

- [ ] [AGENT] P2. **Note only — do not scope**: corporate-action handling, owned by features, deferred past MVP.
      Revisit when a backtest crosses a known corporate action and the result is materially wrong.

## Progress Log

**2026-08-17 — authored.** Captured from operator direction. The requirement (one aggregated definitions catalogue at
monthly grain, with field-level history for the attributes that actually change) is the operator's; the current-state +
narrow-change-log mechanism is a proposal awaiting ratification, and is flagged as such rather than presented as
settled.

The load-bearing insight worth preserving: **the design is driven entirely by a small number of mutable fields.** Tick
size, contract size and protocol risk params are the ones that move, and they are precisely the ones a backtest is
sensitive to — so historising *only* the declared-mutable set keeps storage proportional to real changes while
protecting exactly the fields whose staleness produces wrong numbers rather than merely stale ones. Full-row versioning
would pay for every immutable field on every change; monthly snapshots alone cannot resolve an intra-month change.

**na-eligibility-audit 2026-08-17** [body-hash:7154f83bf9f523b6]: RECLASSIFY (per-todo split) -- 2 of 11 open todos are
independent of the pending operator ratification (todo #2) and genuinely bounded: re-measure findings 3/4 across all
4 AGs (confirmed real, externally-relied-upon work -- `data_pipeline_completion_2026_08_21.md` cites this doc twice
as the owner of that exact measurement) and verify the DeFi-address immutability assumption (factual investigation,
not a design call). Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` items 11-12. Remaining
9 items stay `assigned_vm: NA`: todo #2 (ratify/replace the history-log design) `[OPERATOR]` + its direct dependents
(#3, #5, #6, #8), plus #4/#9/#10 (MISCLASSIFIED_LIKELY_AO_ELIGIBLE, lower confidence -- not extracted this round per
the rubric's "not a fallback for borderline items" rule), and #11 (explicit non-scope placeholder note). Conflict-check
clear. Cross-cutting tranche audit.
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) -- added
`strategy_service_centralization_fixes_2026_08_16.md`, named directly in this doc's own query-don't-derive gate
section as sharing "the same class as the reference-data-in-a-code-path rule" with a note the two checks should
share one discriminator; kept the 3 architecture codex SSOTs + the parent gate-register plan. No source path added --
this is a pure design proposal awaiting operator ratification, not yet executed.
- **na-eligibility-audit 2026-08-17** [body-hash:5d2dc6fec1021b31]: KEEP-NA, valid -- re-verified, no content change since the 2026-08-17 RECLASSIFY (per-todo split) marker; still 9 open items (1 [OPERATOR] ratification + 4 direct dependents + 3 lower-confidence MISCLASSIFIED_LIKELY_AO_ELIGIBLE + 1 explicit non-scope note, grep-confirmed against inventory's open_todos=9). Flagged in-scope this run by the body-hash-drift bug this same tranche's na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md tracks, not a real edit. Cross-cutting tranche audit.
- **na-eligibility-audit 2026-08-18** [body-hash:14c3c0a2c25bede4]: KEEP-NA, valid -- re-verified, ZERO commits to this file since the 2026-08-17 marker (confirmed via git log -- last touch was the marker-append commit itself), confirming the body-hash-drift bug (na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md) re-triggered a third time, not a real edit. Closed the loop on the 3 MISCLASSIFIED_LIKELY_AO_ELIGIBLE items flagged 2026-08-17 (add-definitions-to-catalogue, query-don't-derive gate, provide-queryable-field): re-assessed, all 3 stay NA -- each is transitively gated on the pending [OPERATOR] design ratification (the catalogue schema/grain those items would build against isn't decided yet), downgrading from MISCLASSIFIED to ordinary DEPENDENCY_BLOCKED. Remaining 9 items unchanged: 1 OPERATOR ratification + 4 direct dependents + 3 now-confirmed dependents (ex-MISCLASSIFIED) + 1 explicit non-scope note. Cross-cutting tranche audit.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — 9 open todos, all already triaged across 3 prior na-eligibility-audit passes (2026-08-17 x2, 08-18): 1 [OPERATOR] design-ratification question + 7 dependents gated on it + 1 explicit non-scope deferred note; the only 2.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
