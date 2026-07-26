---
doc_type: issue
title:
  Cross-AG never-seeded backlog scan (cefi / tradfi / prediction) — 2e follow-on to the DeFi +1.38M enumerator re-seed
summary: |
  Scan-only follow-on to Plan-5 item **"2e follow-on — cross-AG never-seeded backlog check (cefi / tradfi / pred)"** — the
  investigation split from the DeFi 2e seeding (`instruments-service@38cec01` + follow-ups) that landed ~+1.38M
  `expected_unattempted` cells. Quantifies each remaining AG's never-seeded backlog and files per-AG concrete-fix todos
  pointing at each AG's owning plan (per the plan-item contract: **scan only; file findings; seed in the owning plan,
  don't seed blind here**). Cefi has a catalogue-vs-writer historical-listing gap + a sub-bucket blank-chain phantom
  audit; tradfi carries credential-gated venue scaffolds + an ohlcv_15m/24h conversion diagnostic that leaves cells
  unseeded; prediction has an intentional decision-338 exclusion (per-conditionId) PLUS a genuine gap (the token-id
  `instrument_availability` lane whose `lifecycle-catalogue-regen-prediction-daily` regen job is PAUSED) PLUS a Kalshi
  launcher gap. No seeding performed by this scan.
status:
  resolved # (was: open) 2026-07-26 re-verify: scan-only contract fully closed -- all 7 cross-reference markers
  # verified CLOSED, no seeding of its own performed or owed; downstream work confirmed tracked (open or since
  # resolved) in each finding's owning plan, not orphaned here -- archived per the 6-step ritual
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [never-seeded, expected-universe, enumerator, honest-coverage, layer-1, cross-ag, 2e-follow-on, capture-to-100]
related:
  [
    /plans/archive/2026_07/foundation_gates_and_capture_to_100_2026_07_06.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-06
last_updated: 2026-07-26
parent_epic: instruments_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: advance-code
source:
  [
    instruments-service/scripts/enumerate_expected_universe.py#L515,
    instruments-service/scripts/enumerate_expected_universe.py#L998,
    instruments-service/scripts/enumerate_expected_universe.py#L1366,
    instruments-service/scripts/enumerate_expected_universe.py#L1705,
    plans/active/data_completion_to_100_all_ag_2026_06_21.md#L2549,
    plans/active/data_completion_to_100_all_ag_2026_06_21.md#L911,
    plans/active/data_completion_to_100_all_ag_2026_06_21.md#L3279,
    plans/active/data_completion_to_100_all_ag_2026_06_21.md#L3275,
    plans/active/data_completion_to_100_all_ag_2026_06_21.md#L3283,
    plans/active/data_completion_to_100_all_ag_2026_06_21.md#L2611,
    plans/active/data_completion_to_100_all_ag_2026_06_21.md#L2533,
  ]
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

# Cross-AG never-seeded backlog scan (cefi / tradfi / prediction) — 2026-07-06

> **🟢 COMPLETE 2026-07-26 — ARCHIVED.** Re-verified: this doc's OWN contract (scan-only — find + cross-reference, never
> seed) is 100% closed — all 7 actionable todos below carry a "CROSS-REFERENCE MARKER CLOSED" verification and none of
> the actual downstream seeding work is tracked as an open item of this doc's own; it lives in each finding's owning
> plan. Re-checked all 7 cross-references against the CURRENT corpus (the owning-plan line-number citations below are
> stale — `data_completion_to_100_all_ag_2026_06_21.md` shrank from ~3,283 to 952 lines across the 2026-07-15 and
> 2026-07-24 line-cap splits — but every finding's content is still live and traceable): (1) cefi Kraken ~6yr IS-store
> backfill — still open, `data_completion_to_100_all_ag_2026_06_21.md:782` ("Step 2"); (2) cefi sub-bucket blank-chain
> phantom audit — the durable writer fix (`instruments-service@24c0dd5`) this doc already verified is corroborated as
> landed+stable by `instruments_cefi_g1_g5_gate_execution_2026_07_24.md` (G1.3); the exact tracking line was folded away
> in the M-1 splits as already-resolved, not silently dropped as still-open; (3) tradfi credential-gated EU-seed
> scaffolds — still open, `data_completion_to_100_all_ag_2026_06_21.md:786` ("Step 4", `BLOCKED-CREDENTIALS`); (4)
> tradfi ohlcv_15m/24h conversion 4-part diagnosis — still open, now at `data_completion_tradfi_2026_07_15.md:629`
> (moved there in the 2026-07-15 split); (5) prediction token-id `instrument_availability` lane — the blocking
> `is-daily-enum-prediction` failure this doc HANDED-OFF is now `status: resolved`
> (`plans/archive/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`, OOM fix 2026-07-13, both
> jobs green); `instrument_availability/by_date/` now shows day partitions through mid-July per
> `plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md:267`, so the lane is materialising
> again — a fresher completeness read is that doc's job, not this one's; (6) prediction Kalshi launcher gap — CLOSED,
> confirmed also flipped `[x]` in the owning plan at the same commit (`data_completion_to_100_all_ag_2026_06_21.md:768`,
> `deployment-service@0a7c3f8`); (7) prediction decision-338 documentation-only affirmation — CLOSED, the docstring +
> filter are still in place unchanged in `enumerate_expected_universe.py`. Nothing of this doc's own is open; archived
> per the 6-step ritual (referrer paths fixed corpus-wide below; no DEFERRED items; no codex contradiction found).
>
> **Scope**: scan-only follow-on to the DeFi 2e seeding that landed ~+1.38M `expected_unattempted` cells
> (`instruments-service@38cec01` canonical venue-key fix + `b34416e`/`0e08237`/`1539772`/`e98a5f3` follow-ups —
> collectively repointed the DeFi enumerator to emit `venue=PROTOCOL`, `chain=X`, canonical per-pool `instrument_id`,
> and stopped emitting chain-level `gas_fees`/`token_transfers`/`mev_events` as per-protocol phantoms). The DeFi 2e
> lifted defi honest-cov from ~6.2% to ~10.1% and climbing. This scan quantifies the equivalent never-seeded backlog for
> cefi / tradfi / prediction and files each AG's concrete-fix todo pointing at the owning plan (per Plan-5's item text:
> "Scan only; file findings. Gate: each AG's never-seeded backlog quantified + filed (seed in the owning plan, don't
> seed blind here)"). **No seeding is performed by this scan.**
>
> **Method**: grep-based inspection of `instruments-service/scripts/enumerate_expected_universe.py` (v1 + v2 lanes) +
> `data_completion_to_100_all_ag_2026_06_21.md` open-item scan (line refs cited under `source:` above). Recent
> enumerator commit history (last 30 days) also grepped for point-fix pattern to distinguish already-closed cases from
> the residual backlog.

> **[2026-07-12 correction, finding 115, §A2 B-queue]**: this scan's own scope is 100% closed — all 7 actionable todos
> below carry a "CROSS-REFERENCE MARKER CLOSED" verification (cefi ×2, tradfi ×2, prediction ×3). `status: open` is
> INTENTIONALLY RETAINED, not stale — the underlying cross-AG seeding work this scan surfaced (Kraken-6yr IS backfill,
> tradfi credential-gated scaffolds, tradfi ohlcv conversion close-out, prediction token-id lane, Kalshi launcher gap)
> is tracked open in each finding's owning plan, not in this scan doc; this doc's own job (scan + file) is done, theirs
> (seed) is not.

## What I found

### cefi (per Plan-5 item; owning plans = `mvp_backfill_cefi_tick_v10_2026_06_27.md` + `data_completion_to_100_all_ag_2026_06_21.md`)

1. **Catalogue-vs-writer historical-listing gap — Kraken ~6yr + peers** (source: `data_completion_…#L3279`). MTDS has
   historical capture for venues whose IS catalogue does NOT carry the corresponding historical listing rows → the v2
   cefi enumerator's `_enumerate_v2_cefi` walks the catalogue, so the pre-catalogue MTDS captures never enter the
   `expected_unattempted` denominator (they materialise as post-hoc `captured` rows against an EU count of 0 →
   completion % looks better than reality). The plan calls this **Step 2 — IS-store backfill: historical listings for
   venues MTDS has but IS lacks (Kraken ~6yr, ...)**, priority P1. Quantum: the Kraken-6yr slice alone is ~2,190 days ×
   ~200 spot instruments × ~4 batch data_types = ~1.75M cells not enumerable today (order-of-magnitude, catalogue-drive;
   the MTDS-has side confirms non-zero captures already exist). Cross-AG total across the Kraken-class peers unknown
   until IS backfill lands. **[2026-07-12 correction, finding 344, §A2 B-queue]** (was: presented as the standing
   quantum with no staleness caveat) — this ~1.75M figure is UNDERSTATED by 1-2+ orders of magnitude:
   `defi_expected_unattempted_backlog_1m_2026_07_03.md:138-141` found this was a grep-based static estimate against the
   OLD (v1) enumerator landscape, now stale post the 2026-07-06 v1→v2 enumerator retirement.
2. **Sub-bucket blank-chain phantom audit** (source: `data_completion_…#L2611`, P2 open). Some cefi sub-bucket
   (oracle/perp) shards seed blank-chain venue rows that carry over from the pre-glue era — post-@24c0dd5 the writer is
   already glued, but stale legacy blank-chain rows survive in sub-bucket shards until the consolidator collapses them.
   These are **over-seeded phantoms** (the inverse of never-seeded — inflating EU incorrectly), included here because
   the audit surface is the same enumerator/writer canonical-key discipline the DeFi 2e closed. Quantum: TBD by the
   audit — plan flags it as a P2 sub-bucket-scoped one-off.
3. **CeFi Layer-1 already CK3-certified honest** post the recent MVP-gate / perp-gate / venue-suffix-fold work
   (`market-tick-data-service@2170d9a`, `instruments-service@e21d681`, `unified-api-contracts@3bb7acd`). No _large_
   canonical-key mismatch of the DeFi-scale kind remains. The Kraken-6yr and sub-bucket findings ARE the residual
   never-seeded backlog for cefi.

### tradfi (owning plan = `data_completion_to_100_all_ag_2026_06_21.md`)

1. **Credential-gated venue EU-seed scaffolds** (source: `data_completion_…#L3283`, P1 `BLOCKED-CREDENTIALS`). Step 4 of
   the `path_to_100pct` fold-in flags the credential-gated venues (Helius/Alchemy for defi telemetry cross-cutting,
   Glassnode-class for tradfi macro/on-chain overlays) whose adapters are scaffolded but whose EU cells are NOT
   currently seeded because the enumerator has no venue-launch/pre-genesis anchor for them (adapter present, catalogue
   entries absent). Quantum: per plan cue, "file the asks" priority — enumeration cost is small once credentials land (a
   scaffold-anchored EU seed is a per-venue × per-data_type × per-date-range Cartesian, order-of-magnitude 10k-100k
   cells per credential-unlocked venue).
2. **ohlcv_15m/24h conversion — 429 FIXED but NOT done, 4-part diagnosis** (source: `data_completion_…#L2533`, P2 open).
   The 429 backoff was corrected but the conversion pass still leaves cells in a wrong state (per plan's 4-part
   diagnosis note). Not a canonical-key gap; a materialisation-lag/idempotency gap that reads as `expected_ unattempted`
   when it should be `captured` or `honest-absence`. Included because the Plan-5 item explicitly says "the scan-only
   investigation split from the defi 2e seeding" and this is one of the two remaining tradfi Layer-1 surfaces per the
   sibling plan.
3. **Recent enumerator fixes already closed the tradfi structural gaps**: `instruments-service@6c893be` (MVP-gate the
   tradfi EU enumerator, mirror cefi), `@a510db1` (NYSE ETF alive-dates → `EXPECTED_SOURCE_DELIVERY_LAG` for
   ARCX-primary ETFs not in XNYS.PILLAR), `@9be20c9` (align enumerator `seed_instrument_id` with MTDS raw*symbol),
   `@814b14a` (VIX cash-index drop + Databento rolling-history floor-clip), `@f6d479f` (axis-3 bundle grain). Honest-cov
   moved 5.3% → 13.8% (source: `data_completion*…#L2516`). No further DeFi-scale canonical re-seed appears warranted at
   the enumerator layer; the residual backlog is the two items above.

### prediction (owning plans = `prediction_cross_venue_arb_and_coverage_2026_07_24.md` [successor to

`prediction_venue_perps_and_live_clob_depth_2026_06_20.md`, split + archived 2026-07-24] +
`prediction_capture_incident_remediation_2026_07_06.md`)

1. **Token-id `instrument_availability` lane NOT SEEDED — `lifecycle-catalogue-regen-prediction-daily` job PAUSED**
   (source: `data_completion_…#L911`). The `expected-universe-v2-prediction` Cloud Run job only seeds `_index`
   `expected_unattempted` from `gs://instruments-store-pred-prd-…/prod/catalog.parquet` — it does NOT write the token-id
   `instrument_availability` parquet, and the `lifecycle-catalogue-regen-prediction-daily` job that WOULD populate it is
   currently PAUSED. **This is the largest genuine never-seeded backlog on prediction**: the token-id dimension for
   Polymarket (~17,772 resolved tokens, per Plan-5 progress log) × per-token daily availability × the captured
   `data_types` is not currently under any EU denominator, so the honest-cov denominator is catalogue-cqg-bundle-only.
   Quantum, per plan-cited baseline: prediction Layer-2 v9 capture reads 5.3% honest-cov (captured 102,936 / empty
   1,007k / failed 10,013 / `expected_unattempted` 818k, source `data_completion_…#L2320`) — the 818k EU is
   CQG-bundle-scoped; the token-id lane is a separate off-manifest dimension.
2. **Kalshi launcher gap** (source: `data_completion_…#L3275`, P1 open). `KalshiAdapter` is wired (per plan +
   `prediction_live_clob_depth_capture_2026_07_24`, successor to `prediction_venue_perps_and_live_clob_depth_2026_06_20`
   split + archived 2026-07-24) but `launch-mtds-prediction-backfill-vm.sh` does not currently launch a Kalshi backfill
   VM → Kalshi cells never move out of `expected_unattempted` (or fail to be seeded for pre-adapter days). Quantum:
   Kalshi resolved-market coverage × trades/`book_snapshot_5` `data_types` × per-day (per plan progress log:
   `kalshi book_snapshot_5 = 2,107 parquets/06-26` shows current capture; the historical seed is the gap).
3. **Decision-338 per-conditionId exclusion** (source:
   `instruments-service/scripts/enumerate_expected_universe.py:1737-1747`). `_enumerate_v2_prediction` explicitly
   filters to cqg-bundle-grain rows when the catalogue contains any, EXCLUDING the per-conditionId trades /
   market_lifecycle universe (~435K conditionIds × ~574 days × 2 data_types → >50M FALSE EU rows if not filtered). This
   is an INTENTIONAL never-seeded state (decision 338, 2026-06-19) and is documented in the enumerator docstring — a
   design boundary, not a fix. Filed here for completeness so a future re-open ("Do we need EU coverage for
   per-conditionId?") reads the docstring rationale + catastrophic-denominator-inflation risk before proposing a seed.

## Why it matters

- **Layer-1 denominator honesty is the heartbeat** (per plan-5 § one-law + `/codex/02-data/honest-coverage-model.md`). A
  never-seeded backlog reads as "we have 100% of what we chose to enumerate" while the actual could-exist universe is
  larger — every downstream capture-%, gate flip, and Foundation sign-off then over-reports. The DeFi 2e re-seed already
  demonstrated this at ~+1.38M cells (defi honest-cov 6.2% → 10.1%). Not filing the equivalent per-AG residual now means
  the same silent over-report survives on cefi/tradfi/pred.
- **The cefi Kraken-6yr class** is the highest-quantum, highest-certainty backlog on cefi. Every day it's not seeded is
  a day the cefi Layer-1 denominator is understated at the historical tail; the `captured` rows post-hoc match no EU row
  → completion % is not measured against a real target for those years.
- **The prediction token-id lane** is the highest-severity gap because the underlying capture IS happening (Polymarket
  468/17,772 tokens resolved with book_snapshot_5) but the denominator is off-manifest — the coverage % cannot be quoted
  honestly for prediction Layer-2 until the token-id EU is materialised.

## Recommended decision

- **Do NOT seed here** — plan-5's item text is explicit: **"scan only; file findings; seed in the owning plan, don't
  seed blind here"**. Each per-AG owning plan owns the seeding decision + verification loop + the writer-materialisation
  discipline (`expected_unattempted` is materialised by the WRITER, never re-derived — see the always-on data rule).
- **Owning-plan handoff** for each finding is captured as an actionable todo below, target-repo named per RULES.md
  §4.5.b so the fix-worker can start cold from just the todo line + this doc.
- **Prediction token-id lane** — the un-pause + capacity path is already scoped under
  `prediction_capture_incident_remediation_2026_07_06.md` Workstream A/B (per the Plan-5 Progress Log entry for the live
  token-universe fix). This scan cross-references that owner and flags the un-seeded EU as the residual to tick once the
  regen job un-pauses; no new plan needed.
- **Decision-338** is intentional and stays in force — the finding here is _documentation-only_ (make sure a future
  reopener reads the >50M-row risk before proposing a per-conditionId seed).

## Actionable todos (per RULES.md §4.5.b)

- [x] ✅ [DATA] P1. Seed the cefi IS-store historical listings for venues MTDS has but IS lacks (Kraken ~6yr class), so
      the v2 cefi enumerator produces the missing pre-catalogue EU cells → over-reported completion % settles honestly
      (repo: instruments-service; owning plan: `plans/active/data_completion_to_100_all_ag_2026_06_21.md` Step 2 P1
      already open — this todo is the cross-reference marker so Plan 5's -008 gate reads "quantified + filed"). —
      **CROSS-REFERENCE MARKER CLOSED 2026-07-06** (Opus, slot-12·planning, `data_engineering`). Verified: owning plan's
      Step 2 P1 todo IS OPEN (`data_completion_to_100_all_ag_2026_06_21.md#L3279` — "IS-store backfill historical
      listings for venues MTDS has but IS lacks (Kraken ~6yr, LIGHTER/PACIFICA/EXTENDED, BITGET gap days) so MTDS↔IS
      subset closes both ways"). Plan 5's `foundation_gates_and_capture_to_100_2026_07_06.md` task -008 gate ALREADY
      reads `[x] ✅` "quantified + filed" for cefi (line 215-216 explicitly enumerates the Kraken ~6yr class ≈ ~1.75M
      cells order-of-magnitude as the cefi residual). **[2026-07-12 correction, finding 344, §A2 B-queue]** (was:
      restated here with no staleness caveat) — this ~1.75M figure is UNDERSTATED by 1-2+ orders of magnitude per
      `defi_expected_unattempted_backlog_1m_2026_07_03.md:138-141` (grep-based static estimate against the OLD v1
      landscape, stale post the 2026-07-06 v1→v2 enumerator retirement). No new code shipped here — this scan's contract
      is "file findings; seed in the owning plan, don't seed blind here" and the Kraken-6yr backfill execution stays
      owned by `data_completion_to_100_all_ag_2026_06_21.md` Step 2 P1. Evidence:
      `data_completion_to_100_all_ag_2026_06_21.md#L3279` (owning todo still open),
      `foundation_gates_and_capture_to_100_2026_07_06.md#L215-227` (Plan 5 -008 gate DONE, quantum stated).
- [x] ✅ [DATA] P2. cefi sub-bucket blank-chain phantom audit — collapse residual pre-@24c0dd5 blank-chain rows in
      oracle/perp sub-bucket shards; verify the consolidator's canonical-glue projection is applied per sub-bucket
      (repo: unified-trading-library + instruments-service; owning plan:
      `plans/active/data_completion_to_100_all_ag_2026_06_21.md` §sub-bucket item P2 already open). — **CROSS-REFERENCE
      MARKER CLOSED 2026-07-06** (Opus, slot-7·planning, `data_engineering`). **Verified current state (this session):**
      (1) durable fix at the IS seeder is IN PLACE — `_canonical_manifest_venue_chain` at
      `instruments-service/instruments_service/engine/orchestrator/writers.py:40-80` applies the canonical projection
      for on-chain CeFi perp CLOBs (LIGHTER-ZKSYNC / PACIFICA-SOLANA / EXTENDED-STARKNET) with the
      `VENUE_TO_ASSET_GROUP.get(venue_str) == "cefi"` bypass added in `instruments-service@24c0dd5` (2026-06-27) +
      catalogue builder alignment `instruments-service@79f2693` (2026-07-06 G1.3 follow-up). (2) Canonical-glue is
      applied UNIFORMLY per sub-bucket — the same `_canonical_manifest_venue_chain` helper is called in both the
      captured-row writer (`writers.py:201`) AND the EU seeder (`process_write.py:769`), so every sub-bucket data_type
      write goes through the identical projection and a seed matches its later capture atom exactly. (3) Real-infra
      verification (single-index-read per single-walk discipline): cefi `_index` (7,219,598 rows) shows
      EXTENDED-STARKNET = 1,209 rows all glued (chain=''), LIGHTER-ZKSYNC / PACIFICA-SOLANA = 0 rows, split-defi-form
      LIGHTER / PACIFICA / EXTENDED = 0 rows (`purge_cefi_perp_defi_contamination_2026_06_25.py` already applied); defi
      `_index` (13,538,204 rows) shows 0 legacy-combined blank-chain rows across oracle_prices (243,580) / perp_funding
      (217,753) / gas_fees (43,496) / token_transfers (423) / mev_events (379) — every sub-bucket row carries a
      non-blank chain (chain-level phantoms handled by
      `reconcile_phantom_manifest_rows_all.py::_chain_level_phantom_mask`). (4) Owning plan's P2 sub-bucket item at
      `data_completion_to_100_all_ag_2026_06_21.md#L2611-2613` remains OPEN as the tracking anchor per the scan contract
      ("file findings; seed in the owning plan, don't seed blind here" — issue-doc line 76 + § Recommended decision line
      170-173). (5) Plan 5's `foundation_gates_and_capture_to_100_2026_07_06.md` task -008 gate ALREADY reads `[x] ✅`
      "quantified + filed" with an explicit cefi bullet at line 216 naming "sub-bucket blank-chain phantom audit". No
      new code shipped here — the durable fix is fully propagated; the owning plan's audit item stays as the formal
      sign-off anchor. — evidence: `instruments-service@24c0dd5` (writer canonical-glue), `instruments-service@79f2693`
      (catalogue builder G1.3 follow-up), `instruments-service/scripts/purge_cefi_perp_defi_contamination_2026_06_25.py`
      (legacy split-form purge), `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py:648-825`
      (chain-level phantom reconcile), `writers.py:201` + `process_write.py:769` (canonical-glue applied per
      sub-bucket), `data_completion_to_100_all_ag_2026_06_21.md#L2611` (owning P2 open),
      `foundation_gates_and_capture_to_100_2026_07_06.md#L216` (Plan 5 -008 gate DONE with cefi bullet).
- [x] ✅ [DATA] P1. tradfi credential-gated EU-seed scaffolds — once credentials land (Glassnode-class), anchor the
      enumerator to venue-launch/coverage-start dates so the pre-credential window seeds as EXPECTED_PRE_VENUE_LAUNCH or
      EXPECTED_INSTRUMENT_NOT_LISTED and the post-credential window materialises as `expected_unattempted` until
      captured (repo: instruments-service + unified-api-contracts; owning plan:
      `plans/active/data_completion_to_100_all_ag_2026_06_21.md` Step 4 P1 `BLOCKED-CREDENTIALS` already open — this
      todo is the cross-reference marker so Plan 5's -008 gate reads "quantified + filed"). — **CROSS-REFERENCE MARKER
      CLOSED 2026-07-06** (Opus, slot-12·planning, `data_engineering`). Verified current state (this session): (1)
      owning plan's Step 4 P1 todo IS OPEN at `data_completion_to_100_all_ag_2026_06_21.md#L3283-3284` — "**Step 4 —
      credential-gated venues** `BLOCKED-CREDENTIALS`: file the asks (Helius/Alchemy, Glassnode/Kaiko, Tardis,
      Databento, Sportradar/Odds-API); build scaffold + tests now, backfill on creds." — the ask-filing + scaffold
      build + venue-launch-anchored seeding stays owned by that P1. (2) Plan 5's
      `foundation_gates_and_capture_to_100_2026_07_06.md` task -008 gate ALREADY reads `[x] ✅` "quantified + filed"
      (line 207-227) with an explicit tradfi bullet at line 217-220 naming "credential-gated EU-seed scaffolds
      (Glassnode-class, BLOCKED-CREDENTIALS)". (3) Adapter-anchor mechanism present in the enumerator today —
      `EXPECTED_PRE_VENUE_LAUNCH` + `EXPECTED_INSTRUMENT_NOT_LISTED` reasons ARE implemented and used for CeFi /
      prediction / Yahoo-index pre-genesis / DeFi chain-genesis lanes (see
      `instruments-service/scripts/enumerate_expected_universe.py:428/522/558/669/725/1055`); the residual gap is the
      venue-launch/coverage-start-date INPUT for the credential-gated tradfi venues (Glassnode-class), which cannot be
      captured or scaffold-anchored without the credentials landing. (4) Credential state: **Glassnode Pro
      (~$999/yr)
      subscription NOT YET APPROVED** — the credential ask is filed at
      `plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md#L236` ("operator approves **Glassnode Pro
      (~$999/yr)**
      credential ask") gating Phase 6 breadth expansion. (5) Cross-reference marker's purpose is fulfilled: filed +
      tracked in owning plan (Step 4 P1 open) + Plan-5 -008 gate already `[x] ✅` "quantified + filed". No new code
      shipped here — this scan's contract is **"file findings; seed in the owning plan, don't seed blind here"**
      (issue-doc line 76 + § Recommended-decision line 170-173); the seeding execution stays owned by
      `data_completion_to_100_all_ag_2026_06_21.md` Step 4 P1 and un-blocks when Glassnode-class credentials land. —
      evidence: `data_completion_to_100_all_ag_2026_06_21.md#L3283` (owning P1 open, BLOCKED-CREDENTIALS),
      `foundation_gates_and_capture_to_100_2026_07_06.md#L207-227` (Plan 5 -008 gate DONE with tradfi bullet),
      `macro_micro_econ_data_capture_audit_2026_06_05.md#L236` (Glassnode credential ask un-approved),
      `instruments-service/scripts/enumerate_expected_universe.py:428/522/558/669/725/1055` (anchor-reason mechanism
      wired).
- [x] ✅ [DATA] P2. tradfi ohlcv_15m/24h conversion 4-part diagnosis close-out — resolve the remaining cells to
      `captured` / `honest-absence` per the 429-fixed conversion pass (repo: market-tick-data-service; owning plan:
      `plans/active/data_completion_to_100_all_ag_2026_06_21.md` line 2533 P2 already open). — **CROSS-REFERENCE MARKER
      CLOSED 2026-07-06** (Opus, slot-12·planning, `data_engineering`). **Verified current state (this session):** (1)
      4-part diagnosis parts (1) MDPS row_key `instrument_id=''` MalformedRowKeyError and (2) MDPS multi-source missing
      `source=` — BOTH FIXED in-code at `market-data-processing-service@62de483` (2026-06-22, "fix(mdps-manifest):
      aggregated candle 15m/24h captures now record (omit empty instrument_id + thread source=)" — 3 files, +251/-22
      incl. 166-line `test_canonical_writer_record_helpers.py`; MDPS QG green [sentinel]; dirty-deps direct-LDR
      carve-out at commit time due to UAC/UTL peer WIP). Parts (3) ~64k migrated-1m re-key
      (`instrument_id='ticks_migrated_20260418T143552Z'` → StreamingParquet partition_mismatch on aggregated write) and
      (4) 103,651 `source=massive`/blank legacy phantoms needing re-seed to `source=databento` — BOTH REMAIN OPEN in the
      owning plan under the same P2 (see `data_completion_to_100_all_ag_2026_06_21.md#L2540-2547`). (2) Owning plan's P2
      tracking anchor at `data_completion_to_100_all_ag_2026_06_21.md#L2533` REMAINS OPEN per the scan contract ("file
      findings; seed in the owning plan, don't seed blind here" — issue-doc line 76 + § Recommended-decision line
      170-173); no owning-plan flip performed here. (3) Deploy state of the parts-(1)/(2) MDPS fix: shipped 2026-06-22
      in code; the owning plan does not yet cite a deploy-evidence line for tarball rebuild + tradfi 15m/24h backfill
      relaunch — that deploy landing plus parts-(3)/(4) execution (migrated-1m re-key + IS-enumerator source=databento
      re-seed) stays owned by the owning plan's P2. (4) Plan 5's `foundation_gates_and_capture_to_100_2026_07_06.md`
      task -008 gate ALREADY reads `[x] ✅` "quantified + filed" (line 207-227) with an explicit tradfi bullet at line
      218 naming "ohlcv_15m/24h conversion 4-part diagnosis close-out". Cross-reference marker's purpose is fulfilled:
      filed + tracked in owning plan (P2 at L2533 open) + Plan 5 -008 gate DONE. No new code shipped here — this scan's
      contract is **"file findings; seed in the owning plan, don't seed blind here"** (issue-doc line 76 + §
      Recommended-decision line 170-173); the seeding/deploy execution stays owned by
      `data_completion_to_100_all_ag_2026_06_21.md` line 2533 P2. — evidence: `market-data-processing-service@62de483`
      (parts 1/2 FIXED in `app/core/canonical_writer.py` + `canonical_writer_stamping.py` + regression tests),
      `data_completion_to_100_all_ag_2026_06_21.md#L2533-2547` (owning P2 open, incl. parts 3/4 ❌),
      `foundation_gates_and_capture_to_100_2026_07_06.md#L207-227` (Plan 5 -008 gate DONE with tradfi bullet at L218).
- [x] ✅ [DATA] P0. prediction token-id `instrument_availability` lane seed — un-pause
      `lifecycle-catalogue-regen-prediction-daily` (or wire the equivalent write in the fixed-UTL is-daily-enum image
      per the remediation plan's Workstream B), so the Polymarket ~17,772-token universe × per-day availability
      materialises as an on-manifest EU dimension (repo: instruments-service + deployment-service; owning plan:
      `plans/active/prediction_capture_incident_remediation_2026_07_06.md` Workstream A/B already open — this todo is
      the cross-reference marker so Plan 5's -008 gate reads "quantified + filed"). — **CROSS-REFERENCE MARKER CLOSED
      2026-07-06** (Opus, slot-12·planning, `data_engineering`). **Verified current state (this session):** (1)
      `lifecycle-catalogue-regen-prediction-daily` scheduler is ALREADY ENABLED (state=ENABLED, schedule=`0 1 * * *`,
      succeededCount=1 on 07-03/04/05/06) — un-paused 13 days before this scan was filed by `deployment-service@040e2fc`
      (2026-06-23) which added the missing `roles/run.invoker` grant + resumed all 5 per-AG schedulers. **(2) Correcting
      the causal chain in the scan's finding-#1 text (line ~129): un-pausing the roll-up does NOT materialise the
      token-id `instrument_availability` parquet — `build_instrument_catalogue.py` READS
      `instrument_availability/by_date/day=…/venue=…/instruments.parquet` snapshots and PRODUCES the cumulative
      `catalog.parquet` (per `lifecycle_catalogue_scheduler.tf` §6-11).** The by_date SNAPSHOT WRITER is
      `is-daily-enum-prediction` (Cloud Run Job invoking the IS orchestrator writers at
      `instruments-service/instruments_service/engine/orchestrator/writers.py:252` + `process_write.py:533`), which is
      currently FAILING exit(1) — the deployed `:latest`=f36f3bba image DOES carry the UTL 1.6.0 coercion
      (docker-inspected) but a DIFFERENT error blocks completion (root cause opaque behind the Cloud-Run observability
      gap — logs show only "Container called exit(1)"). (3) **Direct GCS verification:**
      `gs://instruments-store-prediction-central-element-323112/instrument_availability/by_date/canonical_question_group=SPX_UP_DOWN_DAILY/`
      max `day=2026-05-22` (matches the plan's stale-since claim); token-id lane is genuinely not materialising. (4) The
      actual un-block is TRACKED SEPARATELY in `plans/active/prediction_capture_incident_remediation_2026_07_06.md`
      **Workstream A residual "[INFRA] P0" — HANDED OFF (2026-07-06) → capture-hardening owner**
      (fixed-UTL→is-daily-enum image heal) + full diagnostic handoff in
      `plans/active/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`. (5) Cross-reference
      marker's purpose is fulfilled: Plan 5's `foundation_gates_and_capture_to_100_2026_07_06.md` task -008 gate ALREADY
      reads `[x] ✅` "quantified + filed" (line 207-227). — evidence: `deployment-service@040e2fc` (un-pause),
      `is-daily-enum-prediction` execution failures (HANDED-OFF P0),
      `foundation_gates_and_capture_to_100_2026_07_06.md#L207` (Plan 5 -008 flipped DONE).
- [x] ✅ [DATA] P1. prediction Kalshi launcher gap — wire Kalshi into `launch-mtds-prediction-backfill-vm.sh` so the
      Kalshi historical + post-adapter window seeds/captures via a SPOT VM per the backfill-VMs-default-SPOT HARD rule
      (repo: deployment-service + market-tick-data-service; owning plan:
      `plans/active/data_completion_to_100_all_ag_2026_06_21.md` line 3275 P1 already open). — **CROSS-REFERENCE MARKER
      CLOSED 2026-07-06** (Sonnet 4.6, slot-12·planning, `data_engineering`). **Verified current state (this session):**
      `deployment-service@0a7c3f8` (2026-06-20) shipped the `--venue     POLYMARKET|KALSHI` flag in
      `launch-mtds-prediction-backfill-vm.sh`: the VENUE variable is parameterised (default POLYMARKET), the case guard
      validates `POLYMARKET|KALSHI`, VM_NAME includes the venue slug (`mtds-prediction-kalshi-…`), and
      `VM_VENUE=${VENUE}` propagates to the VM metadata so setup-data-pipeline-vm.sh assembles `--venues KALSHI` in the
      MTDS CLI. MTDS Kalshi adapter is fully wired (adapter py + integration + unit tests in market-tick-data-service).
      No new code needed — this is a cross-reference marker close identical to the cefi/tradfi markers above. Owning
      plan item at line 3275 of `data_completion_to_100_all_ag_2026_06_21.md` also flipped in the same commit. —
      evidence: `deployment-service@0a7c3f8` (Kalshi --venue wired), `launch-mtds-prediction-backfill-vm.sh` lines
      63-66/94-98/150/164-165 (VENUE case + VM_NAME + VM_VENUE),
      `market-tick-data-service/market_tick_data_service/scripts/ingest_kalshi_bulk_to_canonical.py` (adapter wired).
- [x] ✅ [DOC] P3. prediction decision-338 documentation-only affirmation — no seed; keep the per-conditionId exclusion
      in `_enumerate_v2_prediction` and the >50M-row inflation risk visible in the docstring so a future re-open reads
      the rationale first (repo: instruments-service; owning plan:
      `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` [successor to
      `plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md`, split + archived 2026-07-24] —
      cross-reference marker only). — **CROSS-REFERENCE MARKER CLOSED 2026-07-06** (Opus, slot-12·planning,
      `data_engineering`). **Verified current state (this session):** (1) The decision-338 per-conditionId exclusion is
      IN PLACE in `_enumerate_v2_prediction` at `instruments-service/scripts/enumerate_expected_universe.py:1745-1753` —
      filter logic keeps ONLY the cqg-bundle-grain rows
      (`_cqg_rows = [c for c in catalog if c.data_type == _PREDICTION_CQG_DATA_TYPE]`) with an explicit
      `logger.info("prediction v2: cqg-bundle-grain filter active — %d cqg rows kept of %d catalogue rows (per-conditionId trades/market_lifecycle EXCLUDED; decision 338)", …)`
      runtime log tag. (2) The >50M-row catastrophic denominator-inflation risk is VISIBLE in the function docstring at
      `enumerate_expected_universe.py:1728-1738` — "**cqg-bundle grain ONLY (decision 338, 2026-06-19).** … Seeding
      `expected_unattempted` at per-conditionId grain emits >50M FALSE rows (435K conditionIds x ~574 days x 2
      data_types) that NEVER match the per-conditionId-`trades` captured present-set → catastrophic denominator
      inflation." A future re-opener reading the docstring encounters the rationale before the filter code. (3) The
      fall-through preserved: "If the catalogue has NO cqg-bundle rows (legacy / test), fall through to all rows
      unchanged (never silently drop a whole AG)" — the exclusion is data-dependent (fires only when cqg-bundle rows
      exist), so a catalogue evolution that removes the bundle grain doesn't silently zero-seed the AG. (4) Owning plan
      `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` (successor to
      `plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md`, split + archived 2026-07-24) is the
      tracking anchor per the scan contract; no owning-plan flip performed here (scan contract line 76 + §
      Recommended-decision line 170-173 — documentation-only affirmation, no code change). (5) Plan 5's
      `foundation_gates_and_capture_to_100_2026_07_06.md` task -008 gate ALREADY reads `[x] ✅` "quantified + filed"
      (line 207-227) with explicit prediction bullet at line 221-223 naming "decision-338 per-conditionId intentional
      exclusion (>50M-row inflation risk documented)". Cross-reference marker's purpose is fulfilled: filed +
      documented + tracked. No new code shipped here — this is a **documentation-only** affirmation per the item text
      ("no seed; keep the per-conditionId exclusion … the >50M-row inflation risk visible in the docstring"). —
      evidence: `instruments-service/scripts/enumerate_expected_universe.py:1728-1738` (docstring §"cqg-bundle grain
      ONLY (decision 338, 2026-06-19)" with the >50M-row risk narrative),
      `instruments-service/scripts/enumerate_expected_universe.py:1745-1753` (filter code with
      `_PREDICTION_CQG_DATA_TYPE` predicate + decision-338 logger.info tag),
      `foundation_gates_and_capture_to_100_2026_07_06.md#L221-223` (Plan 5 -008 gate DONE with prediction bullet).

## Progress Log

- **2026-07-06 20:15Z** (slot-7·planning): cefi sub-bucket blank-chain phantom audit cross-reference marker closed (4th
  marker); cefi `_index` verified glued, defi `_index` verified 0 legacy-combined blank-chain rows across oracle/perp
  sub-buckets.
- **2026-07-12** (verify-rerun-2, finding 142; correction, finding 115; correction, finding 344): substantive
  corrections applied to the body (see inline annotations).
- **2026-07-14**: verify-rerun-2 finding 142 correction landed; `last_updated` frontmatter field cleaned up to a plain
  date (was previously carrying this whole narrative as a quoted string, violating the plan frontmatter schema's
  expectation of a simple date value — moved here 2026-07-25).

## Provenance

- Task: `foundation_gates_and_capture_to_100-008` (Plan 5, Capture-to-100% §"2e follow-on — cross-AG never-seeded
  backlog check (cefi / tradfi / pred)").
- Author: slot-7·planning (Opus 4.7, `data_engineering` role, 2026-07-06 ~19:00Z).
- Method: scan-only per plan-item contract. No enumerator/manifest writes performed; no seeding executed.
- Reference: DeFi 2e enumerator canonical re-seed (`instruments-service@38cec01` +
  `b34416e`/`0e08237`/`1539772`/`e98a5f3`/`e21d681`/`3bb7acd`/`2170d9a` — commit trail via
  `git log --oneline --since="30 days ago" -- scripts/enumerate_expected_universe.py`) that landed ~+1.38M
  `expected_unattempted` cells, moved defi honest-cov from ~6.2% to ~10.1%, and is the model this scan follows.
