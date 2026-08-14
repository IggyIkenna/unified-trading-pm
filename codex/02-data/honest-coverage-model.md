---
doc_type: codex-ssot
title: Honest Coverage v2 — Two Layers, Two Views, Instrument Gates Download
summary: >-
  SSOT for the Honest Coverage v2 model — two layers (Layer-1 instrument-denominator audit GATES Layer-2 download
  coverage), two views (day-by-day + venue×instrument_type×data_type), the reachable-vs-all-shards coverage formula
  (empty_confirmed excluded from the reachable denominator), the additive coverage.json v2 schema, the
  empty-denominator-fails-CLOSED guard, and the UAC-vs-writer vocabulary/grain alignment rule; CK3-certified 2026-06-29
  (instruments-service@051e5a8).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui, instruments-service]
scope: [engineer, admin]
tags:
  [
    honest-coverage,
    manifest,
    data-correctness,
    data-status,
    uac,
    instruments,
    verification,
    coverage-exclusions,
    out-of-bounds,
  ]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/honest_coverage_baseline_2026_05.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
  ]
created: 2026-06-28
authoritative_for:
  [
    Honest Coverage v2 model (two-layer / two-view / instrument-gates-download),
    coverage.json v2 schema,
    Layer-1 enumeration-completeness matrix,
    Bounded coverage exclusions (out-of-bounds ranges),
    Coverage-exclusion evidence + falsifier rule,
  ]
referenced_by:
  [
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
    /codex/02-data/shard-coverage-classification.md,
    /codex/03-deployment/data-status-ui-surface.md,
    /codex/04-architecture/instrument-universe-registry-consolidation.md,
    /codex/06-coding-standards/data-status-endpoint-contract.md,
    plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md,
    plans/active/issues/honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md,
    plans/archive/issues/honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md,
  ]
owner:
last_reviewed: 2026-07-25
code_refs:
---

# Honest Coverage v2 — Two Layers, Two Views, Instrument Gates Download

> **This is the SSOT for the Honest Coverage v2 model.** It is the durable reference for the two-layer / two-view /
> instrument-gate architecture **and the exact, implementable contract** (coverage.json schema + Layer-1 enumeration
> matrix + carve-outs) that `instruments-service` implements against. Plans and agents cross-reference this doc; they do
> not re-explain it.
>
> **Authoritative as of CK1+CK2 (Opus design, 2026-06-29).** The schema (§ coverage.json v2 schema) and the Layer-1
> enumeration matrix (§ Layer-1 enumeration-completeness matrix) are the design the Sonnet companion plan implements
> verbatim. CK3 (final certification, after the impl + re-measure) signs off the post-impl numbers — see the
> certification section at the foot of this doc.

---

## Why v1 was not enough

The v1 model measured Layer-2 (data-download coverage) against a denominator it never independently verified. If the
instrument-enumeration skeleton was incomplete — missing a whole `instrument_type`, a whole `data_type`, or an entire
venue — the coverage % looked fine while large swaths of the expected universe were simply absent from the denominator.

> You cannot have honest download coverage on top of a dishonest instrument denominator.

v2 makes the denominator audit first-class and **gates** download-coverage reporting on it.

---

## Two layers (the gate)

### Layer 1 — Instrument coverage (denominator audit)

**Question answered:** is the could-exist universe itself complete?

Layer 1 checks whether the enumerated skeleton (`enumerate_expected_universe.py` output, materialised into the manifest
as `expected_unattempted` + whatever has since been captured/failed/confirmed-empty) contains **every
`(venue, instrument_type, data_type)` tuple that UAC says should exist**, bounded by instrument listing windows and the
MVP scope filter.

The two axes and their **exact** authorities (CK1/CK2-verified against the live code):

| Axis                                     | Authority (exact symbol)                                                                                                                                                                               | Repo |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---- |
| Instruments in the universe              | IS catalogue → `enumerate_expected_universe.py` `ExpectedRow` (v2 path `_enumerate_v2_*`)                                                                                                              | IS   |
| Expected data_types per (ag,venue,itype) | `valid_data_types_for_venue_instrument_type(ag, venue, itype)` → fallback `valid_data_types_for_instrument_type(ag, itype)` (defi via `PROTOCOL_CAPABILITIES`; NOT the raw dict — it has no defi keys) | UAC  |
| Per-venue carve-outs + windows           | `VENUE_DATA_TYPE_CAPABILITIES[venue][data_type] → start_date` (data_type absent ⇒ venue cannot produce)                                                                                                | UAC  |
| Bundle grain (chain vs per-leg)          | `FUTURE_BUNDLE_VENUES` (`cefi:{DERIBIT,OKX}`, `tradfi:{CME,ICE}`)                                                                                                                                      | UAC  |
| MVP in-scope filter                      | `is_mvp(asset_group, venue, instrument_type, data_type, …)` / `get_mvp_data_types_for_cefi_venue(venue)`                                                                                               | UAC  |

> **CRITICAL grain fact (do NOT regress):** the expected matrix is keyed by **`(asset_group, instrument_type)` at the
> writer/lowercase grain**, NOT by the broad per-AG list `DATA_TYPES_BY_ASSET_GROUP`. The broad list is a superset and
> using it as the denominator over-counts. For cefi, `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[(cefi, option)]` is
> **`frozenset()`** — leaf `OPTION` instruments roll up into an `options_chain` **bundle** whose `data_type` is `trades`
> (i.e. the real expected tuple is `(DERIBIT, options_chain, trades)`, **not** `(DERIBIT, OPTION, options_chain)`). The
> enumerator's `_rollup_bundle_grain` (G1-ENUM) already performs this leaf→bundle roll-up; Layer-1 asserts against the
> post-roll-up grain.

A **Layer-1 hole** is any `(venue, instrument_type, data_type)` that the UAC matrix (MVP-filtered, within listing
window) says _should_ exist but the enumerated skeleton does **not** contain. Examples: an entire `options_chain` bundle
absent for a venue, an `instrument_type` the writer silently skipped, a new data_type added to UAC but not yet wired
into the enumerator.

**Layer 1 is measured BEFORE Layer 2.** Its completeness fraction is reported independently and gates Layer-2 trust.

### Layer 2 — Data-download coverage

**Question answered:** for the Layer-1-verified denominator, how many shards were actually captured?

Layer 2 applies the 4-state `capture_status` accounting (UTL `CaptureStatus`, `manifest_writer/_schema.py`) against the
denominator Layer 1 verified:

| State (`CaptureStatus`) | Meaning                                                                                       |
| ----------------------- | --------------------------------------------------------------------------------------------- |
| `captured`              | Attempt succeeded, wrote `row_count > 0` (real parquet at the canonical GCS path)             |
| `empty_confirmed`       | Attempt succeeded, source legitimately returned zero rows — MUST carry a typed `error_reason` |
| `attempted_failed`      | Attempt raised before producing rows; `error_reason` = UAC `classify_venue_error()` bucket    |
| `expected_unattempted`  | Catalogue says shard should exist, no fetch attempt yet — pre-populated by the v2 enumerator  |

**`empty_confirmed` MUST be typed** with a member of UAC `EmptyConfirmedReason`
(`canonical/crosscutting/honest_coverage.py`, `EMPTY_CONFIRMED_REASONS` frozenset; e.g. `SOURCE_RETURNED_ZERO`,
`EXPECTED_PRE_VENUE_LAUNCH`, `EXPECTED_HOLIDAY`). A blank `error_reason` on an `empty_confirmed` row is a measurability
violation (the Phase-0 fix); see
[availability-manifest-and-data-status.md](./availability-manifest-and-data-status.md#proof-of-honest-absence).

> **Known exception — `captured` is not always genuine (found 2026-08-09).** 90 sports `day=2026-04-14` manifest rows
> (30 leagues × `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES`/`FIXTURES`) read `capture_status=captured` while the underlying
> GCS parquet is a known-corrupted instrument-catalogue schema (a write-path contamination event, unrelated to this
> model). Layer-2 counts these as real coverage today — numerically negligible (90 rows) but structurally dishonest, and
> no existing state cleanly fits: not `attempted_failed` (rows genuinely WERE produced, just wrong content). A real fix
> needs either reclassification off `captured` or a new honest-corruption state — both out of scope where this was
> found. Full root cause, the affected-league list, and why no existing state fits:
> `/plans/active/issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`.

---

## Layer-2 read grain (manifest shard atom)

The harness reads the consolidated index `gs://{bucket}/_index/availability_index.parquet` via UTL
`read_availability_index(bucket, columns=…)`. The manifest is v9 (41 columns). The **shard atom** — identical across
writer/manifest/status/gate/UI (`manifest_writer/_rows.py` `_ROW_KEY_COLUMNS`) — for market-data coverage is the
projection:

```
(date, venue, instrument_type, data_type, source[, underlying, chain, league_id])
```

`instrument_type` is a **real lowercase writer-grain column** (`spot`, `perpetuals`, `options_chain`, `futures_chain`,
`pool`, `lending`, `prediction_market`, …) — NOT the UPPERCASE catalogue enum. The v2 harness MUST read
`instrument_type` (the v1 harness only read `[capture_status, venue, data_type, date]` — adding `instrument_type` is the
core Phase-2 read change). Bounded-column reads remain mandatory (the cefi index is ~tens-of-millions of rows; loading
the full frame OOM-kills the VM).

> **`migration_pending` window (2026-07-25 — case-robustness fix, D1 gate).** The statement above is TODAY's reality:
> the column is **lowercase** at the writer grain right now. The D1 ruling (2026-07-20,
> `/codex/02-data/cross-asset-canonical-target-ssot.md` §7/§11) makes the **target** canonical manifest
> `instrument_type` COLUMN **UPPERCASE**. These are the same column at two different points on the migration timeline,
> not a contradiction to resolve by flipping this doc — flipping to UPPERCASE now would break the harness against
> today's lowercase data. The harness is made **case-robust across the migration** instead:
>
> - **Layer-1** (`instruments-service/scripts/check_enumeration_completeness.py` `_canon_instrument_type` /
>   `_canon_key`) already normalises case (`.strip().lower()`) on BOTH the EXPECTED (UAC) and ENUMERATED (manifest)
>   sides before intersecting — this predates this note (`honest_coverage_uac_writer_matrix_reconciliation`, 2026-06-29)
>   and is regression-tested (`test_case_fold_instrument_type`,
>   `TestAlignmentNotArtifact.test_uppercase_manifest_matches_lowercase_expected`). The cefi Layer-2 MVP read-time gate
>   (`filter_manifest_to_expected`) delegates to the same `_canon_key`, so it is case-robust too.
> - **Layer-2 drill-down projections** (`by_venue_instrument_type` / `by_venue_instrument_type_data_type` in
>   `instruments-service/scripts/measure_honest_coverage.py`) read the manifest directly and did NOT go through that
>   normaliser — a raw groupby on `instrument_type` would silently SPLIT a shard whose history spans both the lowercase
>   and UPPERCASE spelling (a real risk during the migration cutover window) into two cells, making a fully-covered
>   shard look partially/newly uncovered from a case artifact alone. Fixed 2026-07-25: these projections now GROUP on a
>   case-folded `instrument_type` (`_casefold_instrument_type_series`) while still DISPLAYING the raw, as-written casing
>   (`_representative_instrument_type`) — merging counts across case variants without hiding the raw spelling from
>   downstream consumers that deliberately read it (e.g. deployment-api's distinct-values drift panel, which
>   case-sensitively tracks the cefi/tradfi in-flight uppercase migration on purpose).
> - Sequencing: this normalisation landed BEFORE the D1 `instrument_type`-column migration is allowed to flip any writer
>   or rewrite history — see
>   `plans/archive/issues/honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md` (gate;
>   resolved, archived).

---

## When is Layer-2 coverage trustworthy?

**Only when Layer-1 = 100% for that asset_group.**

The system NEVER reports "downloads look good" while the instrument denominator has holes. Until Layer-1 reaches 100%
for an asset_group:

- `layer_1.by_asset_group.<ag>.denominator_complete = false`,
- `by_asset_group.<ag>.instrument_gates_download = true` (additive flag on the existing Layer-2 cell),
- the Layer-2 `coverage_pct` for that AG is interpreted as a **lower bound** and surfaced with a
  `⚠ DENOMINATOR INCOMPLETE` annotation.

---

## Two views (exposed at both layers)

### View A — day-by-day (time axis)

For each day in the window, are all expected shards for that day present? Catches: missed a whole day, missed a date
range, a data_type that went missing for two weeks. Carried by `by_day` (per-AG, per-date counts). Rendered as a
calendar heat-map / time-series.

### View B — shard-breakdown (entity axis)

For each `(venue × instrument_type × data_type)` combination, complete across its full active lifetime? Catches: "we
never captured `options_chain` at all," "PERPETUALS for KRAKEN are missing an entire data_type." Carried by
`by_venue_instrument_type_data_type` (the full entity drill-down incl. the `instrument_type` axis). Rendered as a table
ranked by worst-coverage shards.

Both views exist for both Layer 1 and Layer 2.

---

## Drill-down / roll-up hierarchy

One headline number at the top expands downward:

```
asset_group
  └── venue
        └── instrument_type
              └── data_type
                    └── day
```

This is realised as a set of **rollup projection dicts** (not one giant recursive tree — that keeps the payload
consumer-friendly and bounded, matching the existing harness shape): `by_asset_group`, `by_venue`,
`by_venue_instrument_type`, `by_venue_instrument_type_data_type`, and `by_day`. Each node carries `coverage_pct` +
`all_shards_coverage_pct` + the raw 4-state counts. The UI composes the tree from these projections.

---

## Coverage formula

```python
reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)
all_shards_coverage = captured / (captured + attempted_failed + expected_unattempted + empty_confirmed)
```

`empty_confirmed` rows (legitimate absence, either source-returned-zero or a known typed gap) are **excluded from the
reachable denominator** — they represent cells the system knowingly does not expect data for. Including them would
deflate coverage for venues with known non-trading days, pre-launch windows, etc. `all_shards_coverage_pct` (which
includes them) is preserved for the completeness view only.

**Delivery-lag ruling (2026-07-14, closes `data_pipeline_e2e_check_2026_07_10` todo 29):**
`EXPECTED_SOURCE_DELIVERY_LAG` (e.g. HYPERLIQUID l2Book's rolling ~2-week vendor publish lag) stays classified
`empty_confirmed` + typed reason, **within the day window — no out-of-window denominator mechanism**. Rationale: (1) the
reachable-coverage formula above already excludes it, so the lag band does not depress reachable coverage — the honest
trailing dip appears only in the all-shards completeness view, which is exactly that view's job; (2) moving the band
out-of-window would make a genuinely-stuck capture inside the lag window invisible (a silent-failure mode), whereas the
typed reason lets any consumer exclude the band explicitly without losing the signal; (3) the dip self-heals — the
idempotent backfill re-attempts after the lag elapses and flips rows to `captured`, so the band rolls forward as an
interpretable steady-state. Same precedent as TradFi T+1 vendor lags (NASDAQ/NYSE), which also stay within-window.

> Compare to v1 formula: `coverage = (captured + empty_confirmed) / expected_universe` — this mixed legitimate-absence
> into the numerator, masking real holes.

**Symmetric-inclusion invariant (made explicit 2026-07-24, `data_pipeline_e2e_milestones_gate_2026_07_24.md` §10)**:
`empty_confirmed` must never appear in a coverage formula's **numerator without also appearing in its denominator** —
crediting a legitimate absence as "covered" while not counting it as part of the expected total would silently inflate
the percentage. It MAY appear in the denominator without the numerator (the deliberate, conservative
`all_shards_coverage` completeness-view choice — a legitimate absence still isn't `captured`, so it never belongs in the
numerator, but the completeness view still counts it as part of the universe), or be excluded from both (the deliberate,
optimistic `reachable_coverage` choice, which drops it from the universe entirely). The forbidden case is numerator-only
inclusion. The two SSOT formulas above satisfy this by construction, not by an enforced check — any THIRD
coverage-percent formula written elsewhere in the codebase (e.g. a service-local convenience helper) must be audited
against this invariant before being trusted; see `data_pipeline_e2e_milestones_gate_2026_07_24.md` §10 for the audit
todo covering this.

**A third sanctioned pattern — `attempt_coverage_pct`** (audited + proven live 2026-07-26,
`issues/coverage_percent_symmetric_inclusion_audit_2026_07_24.md`): unlike the two formulas above, whose denominator is
a sum of `CaptureStatusCounts` fields, this pattern's denominator is an **independently-derived calendar/shard-universe
cell count** (`total_expected_cells`) rather than a field-sum — so it is structurally inclusive of `empty_confirmed`
cells by construction, satisfying the invariant via a different mechanism than either SSOT formula:

```python
attempt_coverage_pct = (captured + empty_confirmed + attempted_failed) / total_expected_cells
```

Proven live and widespread across deployment-api: `derive_capture_status_rates`
(`deployment_api/services/data_status/coverage_metrics.py:406-414`), `overall_attempt_coverage_pct`
(`manifest.py:490-511`), `rollup_cache.py:180-202`, `data_status_mock.py:60-78,95-99` (numerator credits
`captured`+`empty_confirmed`+`attempted_failed` against a calendar-derived cell count — same shape); the MTDS-style
venue/bookmaker rollups `mtds_honest_coverage_for_venue`/`_for_bookmaker` (`data_status/mtds.py:822-834,987-1001`,
denominator = a schedule/calendar-derived `expected_dates` count); and the `coverage_drift.py` detector
`_coverage_per_calc_league()` (`services/coverage_drift.py:55-82`, denominator = the raw row count). A corpus-wide grep
(`empty_confirmed`/`coverage_pct`/`all_shards_coverage`/`reachable_coverage`/`coverage_ratio` across all 24 repo clones)
found **no violation of the symmetric-inclusion invariant anywhere** — every coverage-percent site in the codebase is
one of these three sanctioned patterns.

---

## Bounded coverage exclusions — out-of-bounds ranges (evidence-gated)

**SSOT: `unified_api_contracts.canonical.coverage_exclusions`** (UAC). Shipped 2026-07-17
(`unified-api-contracts@a1284b3d`) per operator proposal: _"for a genuine bounded upstream capture outage sounds like
something to put in UAC as out of bounds so doesn't affect honest coverage denominator and adaptors don't try those
ranges"_.

### The construct

`SOURCE_COVERAGE_START` expresses a **floor** ("nothing before X"). `COVERAGE_EXCLUSIONS` expresses the **bounded**
sibling — a closed mid-history interval that was genuinely never capturable, keyed `(asset_group, source, data_type)` →
closed `(start, end)` intervals. A declared range is **OUT OF MODEL**: neither `captured` nor `missing`. The oracle
emits `EXPECTED_UPSTREAM_OUT_OF_BOUNDS`, a member of `OUT_OF_COVERAGE_WINDOW_REASONS`, so it is clipped from **both**
numerator and denominator — while keeping its **own visible reported line** (deployment-api `EMPTY_REASON_KEYS` + the UI
reason badge). An out-of-model range that is invisible is indistinguishable from data we lost.

**The registry ships EMPTY, and empty is the correct state** until a range is PROVEN — the same stance
`PROTOCOL_PAUSE_WINDOWS` takes ("don't encode pauses we can't prove from data").

### WHY EVIDENCE IS MANDATORY — the floors' cautionary history

**Read this before adding any entry. This mechanism is a loaded gun and the workspace has already shot itself with it.**

`SOURCE_COVERAGE_START` **is** this pattern without an evidence requirement, and **it was WRONG for months**. Its sports
floors were justified by the claim _"our backfill never captured 2018-2020 dates"_ — **factually false**. We held that
data the whole time; the floors made it **invisible by declaration**, clipping the canonical index and hiding 2018–2020
from coverage and from ML. They were amended to measured reality only on 2026-07-16 (`unified-api-contracts@c280e1ff`),
after someone finally probed the buckets and found ~22,327 real objects — including 20/30/98-row `fixture_events`
parquets at `day=2018-01-01` — sitting under floors that declared them impossible. The earlier api_football 2015→2018
move (`@d858f67d`) is the same class of error.

A **bounded** registry can repeat that at greater scale: a floor is at least visible as one cliff at the start of
history; a mid-history interval hides a hole in the middle of a corpus where nobody thinks to look. Hence:

1. **Evidence is mandatory + validated at construction.** `CoverageExclusion` requires a typed `ExclusionReason`, a
   machine-checkable `evidence_uri` (`_audits/` / `audit://` / `https://`), a re-runnable `evidence_probe`,
   `verified_at`, `verified_by` — `__post_init__` raises `CoverageExclusionError` otherwise. An unevidenced range is
   **unconstructible**, not merely discouraged.
2. **Every declaration is continuously falsifiable** (see below).
3. **Declarations go stale.** `verified_at` older than `EVIDENCE_MAX_AGE_DAYS` (365) FAILS — upstreams backfill their
   own history; "it was true once" is not a licence to stay excluded.

### The falsifier — `unified-api-contracts/scripts/check_coverage_exclusions.py`

**This is the guard the floors never had, and why they stayed wrong for months.** A declaration is a standing, testable
claim about the world — not a one-time assertion.

- **Structural layer** (runs in QG via `tests/unit/test_coverage_exclusions.py`, so every declaration is re-falsified on
  every gate run fleet-wide): evidence currency/staleness, redundancy against a `SOURCE_COVERAGE_START` floor, overlaps.
- **Data layer** (`--index <availability_index.parquet>`): probes real manifest rows inside each declared window. **If
  real data exists, the declaration is WRONG and the check FAILS.** Takes an explicit index path because UAC is T0 and
  may not import UTL / cloud-interface.

**The asymmetry of proof (do not "fix" the sensitivity):** declaring HIDES data → HIGH bar (positive proof of absence;
per `@c280e1ff`, object existence alone is NOT evidence — the corpus replicates present-day reference data under
historical partitions, so real data means a parquet that PARSES, carries ≥1 row, and is HISTORICALLY COHERENT with its
partition). Falsifying UN-HIDES data → LOW bar (any hint of real data). A false FAIL refuses an exclusion (safe, honest-
down); a false PASS hides a corpus (the floors' failure mode). **When in doubt, the range stays IN the model.**

### What does NOT belong here

| Case                                     | Correct home                                                                    |
| ---------------------------------------- | ------------------------------------------------------------------------------- |
| **We hold the data** (capture gap)       | **RECOVER it.** Never declare — see the MDT counter-example below.              |
| Recurring closure (weekend/holiday)      | `venue_trading_calendar` + `EXPECTED_WEEKEND` / `EXPECTED_HOLIDAY`              |
| Before the archive begins                | `SOURCE_COVERAGE_START` (a floor)                                               |
| DeFi protocol pause                      | `registry.protocol_pause_windows` (detector-populated from on-chain governance) |
| Rolling vendor publish lag               | `EXPECTED_SOURCE_DELIVERY_LAG`, **within-window** — see the ruling below        |
| Purchasable data we lack entitlement for | A credential ask (`external-data-always-available-rule.md`), NOT an exclusion   |
| Sparse-but-not-empty window              | Still expected, just under-captured                                             |

`MARKET_CLOSED` is deliberately **not** an `ExclusionReason` (the operator's proposal listed it illustratively):
encoding it would duplicate a live primitive and let a recurring schedule masquerade as a one-off outage.

**Worked counter-example — the 32-day MDT window (`2022-09-07..2022-10-01`, 550,062 keys) is NOT a candidate.** The
legacy `market-data-tick-sports` bucket HOLDS those keys (verified two independent ways: the gate's gap days + 213/3,816
G1 objects with no canonical twin on 23 days, 22 matching exactly). Data in hand ⇒ a canonical capture gap to
**RECOVER**, not a range to declare. A tripwire test asserts it is never declared.

### Relationship to the delivery-lag ruling (2026-07-14)

That ruling **rejected** an out-of-window mechanism for `EXPECTED_SOURCE_DELIVERY_LAG` because it would make a
genuinely-stuck capture inside the lag band invisible. That reasoning stands and is **not** contradicted here — the two
cases differ on exactly the property that mattered: a lag band **self-heals** (the idempotent backfill flips rows to
`captured` once the lag elapses), so out-of-window would hide a real failure; a proven-uncapturable range **never
heals**, and the invisibility risk that argued against out-of-window there is answered here by the falsifier + the
mandatory visible reported line. **Absent the falsifier, the delivery-lag ruling's logic would forbid this construct
too** — the falsifier is what earns the out-of-window treatment.

### Related registries (do not add a fourth)

Bounded intervals already existed, fragmented and unevidenced. Consolidated 2026-07-17:

- `PREDICTION_KNOWN_COVERAGE_GAPS` — **DELETED**: never exported, zero importers (dead code asserting an effect it did
  not have), and redundant (ended one day below the POLYMARKET floor).
- sports `KNOWN_COVERAGE_GAPS` — **FROZEN EMPTY** (test-enforced): the unevidenced ancestor, accepting bare
  `(start, end)` tuples with no reason/evidence/falsifier. The cross-asset evidenced gate covers sports. Migrating its
  remaining MTDS classifier callsites and deleting it outright is a filed follow-up.
- `PROTOCOL_PAUSE_WINDOWS` — **KEPT**: detector-populated, therefore evidence-gated by construction. The exemplar this
  construct follows.

`EXPECTED_KNOWN_SOURCE_GAP` is **NOT** reused for this: it has live hand-stamped callsites (PYTH pre-archive, VIX 15m)
and stays **within-window**; widening its semantics would have silently moved live coverage numbers.

**`EXPECTED_UPSTREAM_OUT_OF_BOUNDS` is registry-derived ONLY** — hand-stamping it at a `record_empty` callsite asserts
an unevidenced, unfalsifiable exclusion and is review-blocking.

---

## Layer-1 enumeration-completeness matrix (CK2)

**The check (what the Sonnet companion `Phase 1` impl asserts):** for each asset_group, build the **expected matrix**
and compare it to the **enumerated matrix**, per node.

**Expected matrix** = the set of `(venue, instrument_type, data_type, day-range)` tuples derived purely from UAC +
listing windows (NOT from the manifest):

```
for ag in ASSET_GROUPS:
  for venue in venues_in_ag(ag):                     # IS catalogue venues for the AG
    for instrument_type in itypes_present(ag, venue): # writer-grain itypes, post bundle roll-up
      # AUTHORITY = the UAC FUNCTIONS, never the raw VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE dict
      # (that static dict has NO defi keys — defi/sports validity is computed dynamically).
      # Prefer the protocol/venue-narrowed function; fall back to the per-itype function.
      expected_dts = (
          valid_data_types_for_venue_instrument_type(ag, venue, instrument_type)   # defi protocol-grain (narrowed)
          or valid_data_types_for_instrument_type(ag, instrument_type)             # cefi/tradfi/sports/prediction + defi-union
          or frozenset()
      )
      for dt in expected_dts:
        if ag in VENUE_CAPABILITY_AGS and dt not in VENUE_DATA_TYPE_CAPABILITIES.get(venue, {}):
            continue                                                # venue cannot produce dt → carve-out, skip
        if not is_mvp(ag, venue, instrument_type, dt):              # out of MVP scope → skip
            continue
        listing_window = [max(venue_dt_start, instrument_listed_from) … instrument_listed_to]
        EXPECTED.add((venue, instrument_type, dt, listing_window))
```

> **AUTHORITY (do NOT regress — found 2026-06-29):** the expected data_types come from the UAC **functions**
> `valid_data_types_for_venue_instrument_type(ag, venue, itype)` (line ~987) → falls back to
> `valid_data_types_for_instrument_type(ag, itype)` (line ~925), **NOT** by indexing the raw
> `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` dict. That dict only carries cefi/tradfi/sports/prediction static entries
> and **ZERO defi keys** — defi validity is built dynamically from `capability_declarations._defi.PROTOCOL_CAPABILITIES`
> (per-protocol, narrowed by the `PROTOCOL` segment of the `PROTOCOL-CHAIN` venue id, so e.g. Aave's `lending_indices`
> does not leak to Uniswap pools). Indexing the dict directly returns ∅ for every defi tuple → `EXPECTED=0` → a **false
> "100% complete"** (the empty-denominator failure mode below). `VENUE_DATA_TYPE_CAPABILITIES` is a cefi/tradfi venue
> table (`VENUE_CAPABILITY_AGS = {cefi, tradfi}`); it must NOT be applied as a skip-filter to defi/sports/prediction
> (whose capability is already encoded in the protocol/league validity functions).

**Enumerated matrix** = the distinct `(venue, instrument_type, data_type)` tuples actually present in the skeleton
(`enumerate_expected_universe.py` output / the manifest rows in any of the 4 states).

> **VOCABULARY/GRAIN ALIGNMENT — both sides MUST be normalised to ONE grain before intersecting (HARD RULE, found
> 2026-06-29).** EXPECTED is built in UAC's vocabulary; ENUMERATED is the manifest's _written_ vocabulary. They diverge
> on three axes, and an un-normalised intersection collapses to artificial 0%/low completeness (observed: defi 0% with
> EXPECTED=3,581, sports 0% with Layer-2=100%, cefi 18/121):
>
> 1. **Casing** — manifest carries BOTH `PERPETUAL` and `perpetual`, `LENDING` and `lending`. Case-fold venue +
>    instrument_type + data_type on BOTH sides.
> 2. **instrument_type vocabulary** — UAC uses `spot_pair`/`perpetual`/`exchange_odds`/`fixed_odds`; the writer grain
>    differs (sports writes itype=`odds`). Map via the SAME IS writer canonicalisation the enumerator uses
>    (`_canonical_writer_instrument_type` / the sports league grain) so the two vocabularies meet.
> 3. **venue format** — defi manifest venue appears as `AAVE`/`AAVEV3`/`AAVE_V3` (and the EXPECTED side as the
>    `PROTOCOL`/`PROTOCOL-CHAIN` id); sports as `BETFAIR`/`BETFAIR_EX_EU`/`BETFAIR_EX_UK`. Canonicalise venue on both
>    sides before keying.
>
> The check MUST ship a **diagnostic mode** that prints, per AG, sample EXPECTED-only / ENUMERATED-only / matched keys,
> so a residual hole is provably REAL (blank `instrument_type`, genuinely-absent bundle) and not a dialect artifact.
> Only REAL holes (post-alignment) count toward `missing_tuples`; pure casing/format/vocabulary differences are NOT
> holes. **A whole-AG 0% (or near-0%) while its Layer-2 is healthy is the signature of an alignment defect — treat it as
> not-yet-trustworthy, never certify it.**

**Per-node completeness** = `|EXPECTED ∩ ENUMERATED| / |EXPECTED|` (after the alignment normalisation above), rolled up
`asset_group → venue → instrument_type → data_type`. `missing_tuples = EXPECTED − ENUMERATED` are the Layer-1 holes. A
tuple present in ENUMERATED but absent from EXPECTED is a **stray** (writer emitting something UAC doesn't sanction) —
logged as a Layer-1 warning, not a hole.

`denominator_complete = (missing_tuples == ∅)` per AG. The gate flag (`instrument_gates_download`) is the negation.

> **EMPTY-DENOMINATOR GUARD — fail CLOSED, never green (HARD RULE, found 2026-06-29).** `EXPECTED == ∅` for an AG (or
> any node) is **NOT** `100% complete` — `completeness_pct` over an empty set is _undefined_, and reporting it as 100%
> reproduces the exact v1 dishonesty v2 exists to kill (an empty denominator looks perfect). When `expected_tuples == 0`
> for an AG: set `denominator_status = "UNDEFINED"`, `denominator_complete = false`, `completeness_pct = null`, and
> `instrument_gates_download = true` (Layer-2 is a lower bound), and LOUD-LOG it. An empty expected set means the AG's
> validity authority is not wired (the defi bug above) or the catalogue enumerated no venues/instruments for the AG —
> both are certification-blocking, never a pass. CK3 cannot certify any AG whose `denominator_status == "UNDEFINED"`.

### Carve-outs — a legitimate absence is NEVER a Layer-1 hole

Carve-outs are **sourced from UAC** (not hardcoded in the checker) so the matrix stays the single SSOT. A tuple is a
legitimate absence (excluded from `EXPECTED`) when ANY of:

1. **Venue cannot produce the data_type** — `data_type ∉ VENUE_DATA_TYPE_CAPABILITIES[venue]`.
2. **Out of MVP scope** — `is_mvp(...) == False`.
3. **Outside the listing window** — day `<` venue/instrument start or `>` delist (these appear in the manifest as
   `empty_confirmed` with an `EXPECTED_*` reason, never as holes).
4. **Bundle roll-up grain** — leaf `OPTION`/`FUTURE` for a `FUTURE_BUNDLE_VENUES` venue is represented by its
   `options_chain`/`futures_chain` bundle, not per-leg.

Known, enumerated examples (the Sonnet impl's regression assertions — all are _expected absences_, not holes):

| Asset group | Carve-out                                                                 | Source authority                                                                       |
| ----------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| cefi        | DERIBIT options → `options_chain` bundle (`data_type=trades`), no per-leg | `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[(cefi,option)]=∅` + `FUTURE_BUNDLE_VENUES` |
| cefi        | ASTER has no `book_snapshot_5`, no `liquidations`                         | absent from `VENUE_DATA_TYPE_CAPABILITIES[ASTER]`                                      |
| cefi        | HYPERLIQUID has no `liquidations`                                         | absent from `VENUE_DATA_TYPE_CAPABILITIES[HYPERLIQUID]`                                |
| cefi        | COINBASE-SPOT is `trades`-only (MVP cost cut 2026-06-28)                  | `get_mvp_data_types_for_cefi_venue(COINBASE-SPOT)`                                     |
| sports      | A_LEAGUE × footystats coverage gaps (pre/post-season, paused league)      | `is_mvp(...)` + `EXPECTED_PRE_SEASON`/`EXPECTED_PAUSED_LEAGUE`                         |
| all         | Pre-listing / post-delist days                                            | listing window + `EXPECTED_PRE_VENUE_LAUNCH` etc.                                      |

> **The Deribit contradiction this resolves** (companion Phase-1 diagnostic): the live cefi manifest showed
> `options_chain` with captured≈1, 99.9% blank `instrument_type`. That is a Layer-1 hole (the bundle grain was not
> enumerated / instrument_type blank), NOT a legitimate carve-out. Layer-1 must surface it as a `missing_tuple` until
> the enumerator emits the `(DERIBIT, options_chain, trades)` bundle and the writer stamps
> `instrument_type=options_chain`.

---

## coverage.json v2 schema (CK1)

`coverage.json` written to `gs://{PROJECT}-honest-coverage/{YYYY-MM-DD}/coverage.json`.

**HARD CONSTRAINT — the schema is ADDITIVE, not greenfield.** Live consumers (deployment-api
`/api/data-status/honest-coverage` returns the payload verbatim; deployment-ui `HonestCoverageCard.tsx` +
`HonestCoverageResponse`/`HonestCoverageStatusCounts` TS types; the pinned `test_honest_coverage_route.py`) read these
**existing top-level keys and per-cell fields, which v2 MUST preserve unchanged**:

- top-level: `generated_at`, `date`, `by_asset_group`, `by_venue`, `by_venue_data_type`
- per-cell (`HonestCoverageStatusCounts`): `captured`, `empty_confirmed`, `attempted_failed`, `expected_unattempted`,
  `total`, `coverage_pct` (+ optional `all_shards_coverage_pct`, `out_of_window`)

v2 **adds** new optional top-level keys and new optional per-cell fields. Adding optional fields is back-compat (the TS
interface marks the v2 additions optional; the route returns verbatim; the test only asserts the existing keys).

```json
{
  "generated_at": "2026-06-29T00:00:00Z",
  "date": "2026-06-29",
  "schema_version": 2,
  "asset_groups_measured": ["cefi", "defi", "tradfi", "sports", "prediction"],

  "layer_1": {
    "by_asset_group": {
      "<ag>": {
        "denominator_complete": false,
        "completeness_pct": 97.3,
        "expected_tuples": 412,
        "present_tuples": 401,
        "missing_tuples": [{ "venue": "DERIBIT", "instrument_type": "options_chain", "data_type": "trades" }],
        "stray_tuples": [],
        "by_venue": {
          "<venue>": {
            "completeness_pct": 90.0,
            "expected_tuples": 20,
            "present_tuples": 18,
            "missing": [{ "instrument_type": "options_chain", "data_type": "trades" }]
          }
        }
      }
    }
  },

  "by_asset_group": {
    "<ag>": {
      "captured": 0,
      "empty_confirmed": 0,
      "attempted_failed": 0,
      "expected_unattempted": 0,
      "total": 0,
      "coverage_pct": 84.2,
      "all_shards_coverage_pct": 71.0,
      "instrument_gates_download": true,
      "denominator_complete": false,
      "layer1_completeness_pct": 97.3
    }
  },
  "by_venue": { "<ag>": { "<venue>": { "...HonestCoverageStatusCounts...": 0 } } },
  "by_venue_data_type": { "<ag>": { "<venue>": { "<data_type>": { "...counts...": 0 } } } },

  "by_venue_instrument_type": {
    "<ag>": { "<venue>": { "<instrument_type>": { "...counts...": 0 } } }
  },
  "by_venue_instrument_type_data_type": {
    "<ag>": { "<venue>": { "<instrument_type>": { "<data_type>": { "...counts...": 0 } } } }
  },

  "by_day": {
    "<ag>": { "<YYYY-MM-DD>": { "...counts...": 0 } }
  }
}
```

Key fields at each Layer-2 count node (`...counts...`): `captured`, `empty_confirmed`, `attempted_failed`,
`expected_unattempted`, `total`, `coverage_pct` (reachable formula), `all_shards_coverage_pct`.

New-in-v2 keys: `schema_version`, `layer_1`, `by_venue_instrument_type`, `by_venue_instrument_type_data_type`, `by_day`;
new-in-v2 per-AG-cell fields: `instrument_gates_download`, `denominator_complete`, `layer1_completeness_pct`. Everything
the v1 harness already wrote stays byte-for-byte compatible.

---

## Implementation contract (what the Sonnet companion plan builds)

- **Phase 1 (`enumerate_expected_universe.py` completeness check):** a function that builds `EXPECTED` from the UAC
  authorities above and `ENUMERATED` from the skeleton, returns per-node completeness + `missing_tuples` +
  `stray_tuples`. Unit-tested against the carve-out table (each row asserts "expected absence ⇒ NOT a hole"; Deribit
  options_chain bundle asserts "hole until enumerated").
- **Phase 2 (`measure_honest_coverage.py`):** (a) add `instrument_type` to `_READ_COLUMNS`; (b) add the
  `by_venue_instrument_type` + `by_venue_instrument_type_data_type` + `by_day` projections; (c) call the Phase-1 check
  to populate `layer_1` and the per-AG gate fields; (d) emit `schema_version: 2`. Preserve the existing
  `by_asset_group`/`by_venue`/`by_venue_data_type` keys and the freshest-bucket + prd/non-prd merge logic untouched.
- **Run grain:** all 5 asset_groups. Bounded-column reads only.

---

## Where the axes live (canonical)

| Axis                                                                   | Canonical location                                                                                                                                                                                                                                                        |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Instruments in the universe                                            | IS catalogue (`build_instrument_catalogue.py`; `mvp` is a stamped column)                                                                                                                                                                                                 |
| Expected data_types per (ag, instrument_type)                          | UAC `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`                                                                                                                                                                                                                          |
| Per-venue capability + listing windows                                 | UAC `VENUE_DATA_TYPE_CAPABILITIES` (+ `FUTURE_BUNDLE_VENUES` for bundle grain)                                                                                                                                                                                            |
| MVP filter (which instruments are in-scope for the current phase)      | UAC `is_mvp` / `mvp_scope.py`                                                                                                                                                                                                                                             |
| Shard atom per AG                                                      | `/codex/02-data/availability-manifest-and-data-status.md` § per-asset-group shard atoms                                                                                                                                                                                   |
| 4-state `capture_status` / typed `error_reason`                        | UTL `manifest_writer/_schema.py` `CaptureStatus`; UAC `EmptyConfirmedReason`                                                                                                                                                                                              |
| MDPS candle `timeframe` (extra axis beyond MTDS raw-tick's shard atom) | UAC `MDPS_CANONICAL_TIMEFRAMES`/`MDPS_DERIVABLE_DATA_TYPES` (`registry/processed_data_dependencies.py`); consumed in `deployment-api`'s `per_instrument_coverage`/`mtds_honest_coverage_for_venue` via an optional `timeframes` param (`None` = MTDS raw-tick, unchanged) |

**Do NOT derive the expected universe from the manifest.** The manifest is the write ledger; the expected universe is
the IS catalogue × UAC matrix. Treating the manifest as both numerator and denominator circular-references honest
coverage.

**MDPS timeframe-awareness (added 2026-07-21, `mtds_data_status_page_parity_2026_07_21.md`)**: MDPS derives candles at 7
timeframes from the same raw source data_types MTDS captures, over the SAME manifest (service-partitioned by
`service_name`) — a finer shard grain than MTDS's per-(instrument, date) atom. Extended, not replaced: the Tier-3
per-instrument denominator/found-set becomes per-(instrument, date, timeframe) ONLY when a `timeframes` list is supplied
(MDPS callers only); every MTDS call path is byte-for-byte unchanged. **The Tier-2 (venue-level) branch is ALSO now
timeframe-aware** (`deployment-api@43f067e`, 2026-07-22 follow-up) — mirrors the Tier-3 pattern via a
`_tier2_dt_entry()` helper; `timeframes=None` (every existing MTDS caller) reproduces the prior denominator
byte-for-byte. Both open design questions (pre-cutover historical-row visibility; per-timeframe start-date divergence)
were investigated directly against production data rather than left open indefinitely: MDPS has written only 6 total
rows to the shared manifest to date (a single 2026-04-16 smoke-test write), so both questions are currently
MOOT/undeterminable from real volume — the shipped defaults (`historical_coverage_gap` flag; flat
`MDPS_CANONICAL_TIMEFRAMES`) stand unconfirmed-but- unfalsified, with an explicit re-open trigger (real MDPS production
volume appearing in the manifest), not a permanently-settled answer. See the plan's Progress Log for the full
investigation.

**MVP/could-exist/all `scope` UI wiring (added 2026-07-23)**: the backend `scope` param this section's `is_mvp` plumbing
relies on (`/manifest`/`/turbo` routes) now has a UI-reachable consumer — `deployment-ui`'s
`getDataStatusManifest`/`getDataStatusTurbo` thread an optional `scope` param, and `DataStatusTab.tsx` renders a
page-level "Coverage Scope" toggle consistently across instruments-service/MTDS/MDPS (`deployment-ui@f9396e1`). Prior to
this, the backend wiring had zero UI consumer on the shared coverage grid.

---

## Relationship to existing manifest model

Layer 2 in Honest Coverage v2 is the 4-state model that already exists in the manifest (see
[availability-manifest-and-data-status.md](./availability-manifest-and-data-status.md)). v2 does NOT change the manifest
schema or write contract. It adds: (1) **Layer 1** as a first-class gate; (2) **two views** (day-by-day +
shard-breakdown incl. the `instrument_type` axis); (3) **a coverage formula** that correctly excludes `empty_confirmed`
from the reachable denominator; (4) **an additive `coverage.json`** carrying both layers, both views, and the
instrument-gates-download flag without breaking existing consumers.

---

## CK3 — final integrated certification

**Status: CERTIFIED — model & measurement honest (2026-06-29, Opus).** The Honest-Coverage-v2 model and its measurement
harness are certified CORRECT and HONEST. This is NOT a claim that coverage is 100% — it is the opposite: the system now
**honestly reports the real gaps** and gates Layer-2 on them. Evidence: `instruments-service@051e5a8`
(`scripts/check_enumeration_completeness.py` + `measure_honest_coverage.py`, CI `quality-gates-v2` GREEN run #688, 38
unit tests); live measure `coverage_v3.json` 2026-06-29 06:00 UTC.

**What is certified:**

1. **Layer-1 gates Layer-2 — verified.** All 5 AGs `denominator_status=INCOMPLETE` → `instrument_gates_download=true` on
   the Layer-2 cell → each AG's `coverage_pct` is interpreted as a lower bound. The gate field propagates into
   `by_asset_group[ag]` as designed.
2. **No silent denominator holes — verified.** Empty-denominator guard fails CLOSED (`UNDEFINED`, never false-100% —
   this caught the original defi `EXPECTED=0`). The `--diagnose-layer1` mode emits per-AG EXPECTED-only /
   ENUMERATED-only / matched samples so every hole is auditable.
3. **Both views present + schema back-compat — verified.** `by_day` (time axis) + `by_venue_instrument_type_data_type`
   (entity axis incl. instrument_type) added; `by_asset_group`/`by_venue`/`by_venue_data_type` + the 6 per-cell fields
   preserved byte-compatible for the live deployment-api/UI consumers; `schema_version: 2`.
4. **Vocabulary/grain alignment — verified.** EXPECTED (UAC vocab) and ENUMERATED (writer/manifest vocab) are normalised
   to one canonical grain before intersection (the bug that had produced artifact 0%s for defi/sports). Post-alignment
   numbers measure REAL holes.

**Certified Layer-1 (instrument-denominator) per AG — re-measured 2026-07-03 08:52 UTC after the UAC↔writer matrix
reconciliation landed** (`honest_coverage_uac_writer_matrix_reconciliation_2026_06_29`: cefi venue-suffix fold, defi
lending grain roll-up, `rate_indices` dialect fold, ASTER over-seed carve-out + 17,282-row manifest purge):

| AG         | Layer-1 completeness                                                                                                                      | present/expected    | real holes | strays                                            | Layer-2 (lower bound, gated)                         |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------- | ---------- | ------------------------------------------------- | ---------------------------------------------------- |
| cefi       | 94.52% — refreshed 2026-08-14, read directly (not recomputed) from `gs://central-element-323112-honest-coverage/2026-08-12/coverage.json` | 69/73 (as of 08-12) | 4          | 104 (2026-07-03, not re-measured in this refresh) | 37.90% (2026-07-03, not re-measured in this refresh) |
| defi       | 94.81% (was 69.44%)                                                                                                                       | 73/77               | 4          | 128                                               | 58.02%                                               |
| tradfi     | 51.43%                                                                                                                                    | 18/35               | 17         | 52                                                | 95.15%                                               |
| sports     | 30.77%                                                                                                                                    | 8/26                | 18         | 24                                                | 100.00%                                              |
| prediction | 66.67%                                                                                                                                    | 4/6                 | 2          | 17                                                | 22.73%                                               |

(Historical: the 2026-06-29 06:00 UTC certification measured cefi 65.91% / defi 69.44%; defi rose to 94.81% via the
protocol enumeration work landed 06-29→06-30, cefi to 79.55% via the reconciliation dialect folds — 6 of cefi's 15
"holes" were captured-under-suffix false holes (OKX-SPOT/-SWAP/-FUTURES rows vs bare-OKX expectation). Pre-alignment
artifacts remain retired: defi 0%/EXPECTED=3,581, sports 0%, cefi 14.9% were dialect-mismatch artifacts.)

**Real Layer-1 holes (honest backfill backlog, correctly surfaced — NOT silent):** cefi (refreshed 2026-08-14 from
`gs://central-element-323112-honest-coverage/2026-08-12/coverage.json`) `BITGET-FUTURES/future/book_snapshot_5`,
`BITGET-FUTURES/future/derivative_ticker`, `OKX-FUTURES/perpetual/book_snapshot_5`,
`OKX-FUTURES/perpetual/derivative_ticker`; defi EIGENLAYER-ETHEREUM `spot_asset` ×4; tradfi CBOE `index` ohlcv + ICE
`combo`/`options_chain` ohlcv_1m + YAHOO_FINANCE grains; sports BETFAIR/ODDS_API/PINNACLE bookmaker snapshot types;
prediction KALSHI/POLYMARKET `market_lifecycle`.

> **Known cefi denominator caveat (2026-07-03, matrix size since grown to 73 tuples per the 2026-08-14 read above):**
> the (then-44-tuple) cefi expected matrix omits whole venues the (venue,itype) gate + capability table are blind to
> (Tier-3 BITFINEX-SPOT/BITGET-\*/KRAKEN-SPOT, non-Tardis HYPERLIQUID/ASTER/EXTENDED, capability-absent
> BYBIT-SPOT/COINBASE-FUTURES/BINANCE-DELIVERY/KALSHI-PERP/…) — whether this omission still holds against the grown
> 73-tuple matrix has not been re-verified. SSOT: `plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md`.

**CERTIFICATION CAVEAT — completeness % is an UPPER bound where UAC under-specifies.** The high stray counts surfaced a
**UAC↔writer contract gap** (a newly-discovered cross-repo finding, NOT a measurement bug): the writer captures real
`(venue, instrument_type, data_type)` combos that UAC's per-itype validity matrix does not yet sanction — e.g. tradfi
CME `futures_chain` `mbp_10`/`ohlcv_24h`/`tbbo`, prediction KALSHI `book_snapshot_5`, defi AAVE `a_token` sub-grains —
so for those nodes EXPECTED is too small and completeness is over-reported. Plus one writer↔UAC carve-out contradiction
(ASTER `book_snapshot_5`/`liquidations` captured despite UAC declaring ASTER cannot produce them). These are tracked in
`plans/active/issues/honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md`; resolving them (owner-verified UAC
matrix expansion + writer canonicalisation) will refine the certified numbers. The MODEL and MEASUREMENT are certified;
the per-node % will tighten as that reconciliation lands.

**This codex doc is the standing authoritative SSOT for the Honest-Coverage-v2 model.**

---

## Codex SSOTs

| Topic                                                     | SSOT                                                             |
| --------------------------------------------------------- | ---------------------------------------------------------------- |
| 4-state `capture_status` write contract + manifest schema | `/codex/02-data/availability-manifest-and-data-status.md`        |
| Honest absence — downstream handling (read side)          | `/codex/02-data/honest-absence-downstream-handling.md`           |
| IS as SSOT for instrument universe                        | `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` |
| Data pipeline correctness hard rule                       | `/codex/02-data/data-pipeline-correctness-hard-rule.md`          |
| Coverage baseline ratchet (v1 numbers, May 2026)          | `/codex/02-data/honest_coverage_baseline_2026_05.md`             |
| Pipeline mode / source partitioning                       | `/codex/02-data/pipeline-mode-partition.md`                      |
| Data-status UI surface (coverage.json consumer)           | `/codex/03-deployment/data-status-ui-surface.md`                 |
