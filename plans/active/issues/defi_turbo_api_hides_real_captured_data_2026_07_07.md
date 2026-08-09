---
doc_type: issue
title:
  "Turbo API silently reports 0/0 for DeFi venues with real, current captured data (AAVE_V3-ARBITRUM/POLYGON, SPARK) --
  a read-path bug, not a capture gap"
summary:
  "Chasing an operator hypothesis that AAVE_V3-ARBITRUM/POLYGON and EULER_V2/FLUID might have real data hiding under a
  mismatched venue name, a live read of the actual GCS DEFI availability manifest
  (market-data-tick-defi-prd-central-element-323112) found something more serious: AAVE_V3-ARBITRUM has 18,771 real
  captured rows and AAVE_V3-POLYGON has 24,278, both current through 2026-06-21, under the exact canonical venue+chain
  the turbo API already expects -- yet GET /api/data-status/turbo reports dates_found=0, dates_expected=0,
  instrument_types={} for both. SPARK has 7,405 real captured rows and does not appear in the turbo response AT ALL.
  This is a read/aggregation-side bug in deployment-api, not a write-side naming mismatch and not a capture gap -- the
  data genuinely exists. EULER_V2 (both chains) and FLUID-ARBITRUM/PLASMA, by contrast, are confirmed to have zero real
  data anywhere -- those really are unwired, not hidden."
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [deployment-api, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [honest-coverage, defi, turbo-api, data-correctness, read-path, aave, spark, euler, fluid]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    /plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
created: 2026-07-07
author: unknown
parent_epic: instruments_master
priority: P0
source:
  "Operator hypothesis follow-up, 2026-07-07 -- verified against the real GCS manifest via instruments-service/.venv +
  GCP ADC, not asserted from code reading alone"
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: local-only
model_tier: opus-required
thinking_tier: high
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
last_updated: 2026-07-12
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/defi_venues.py,
    unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py,
    /plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
    deployment-api/deployment_api/services/data_status/defi.py,
  ]
---

> **NOTIFY-OPERATOR class finding — a live, current data-correctness bug, not a design question.** Filed P0 because the
> honest-coverage dashboard is understating real DeFi coverage for at least 3 confirmed venues, and this class of bug
> (real data silently missing from the aggregation layer) is exactly the kind of thing that could mislead a real
> capital-allocation decision if someone concluded "no data → not worth pursuing" from the turbo API alone. It doesn't —
> the data was there the whole time.

## What was actually checked, and how

The operator's hypothesis was: some of the "0/0, never captured" DeFi venues from the earlier drilldown might actually
have real data sitting under a different, non-canonical venue string. A 3-way check ran in parallel:

1. **MTDS write-path trace** — confirmed the manifest-write helper (`_defi_manifest.py:760-768`, `_normalise_venue`)
   produces the exact canonical `AAVE_V3`/`EULER_V2`/`FLUID` strings, with `chain` written as a separate field, never
   folded into `venue`. No naming-format mismatch exists in the write path for any of these protocols.
2. **UAC registry check** — confirmed AAVE*V3-ARBITRUM/POLYGON are declared fully `"live"` in `defi_venues.py` with real
   subgraph IDs, launch dates, and capability entries; EULER_V2 has real, \_recently verified* Goldsky subgraph IDs for
   both ARBITRUM and ETHEREUM (`_defi.py:217`, "Verified GREEN via Goldsky 2026-06-02") but **zero entries** in
   `DEFI_VENUE_DATA_TYPE_CAPABILITIES`, and its `defi_venues.py` phase-dict comment ("no UAC subgraph_id registered → 0
   rows") is now **stale** — it predates the 2026-06-02 subgraph verification and was never updated. FLUID has only an
   `ETHEREUM` subgraph ID; no ARBITRUM or PLASMA entry exists anywhere, and "PLASMA" itself has no chain config in UAC
   at all (flagged by UAC's own maintainers as `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` — likely conflating the 2025
   Tether-backed Plasma L1 with the old, unrelated 2018-2020 Polygon Plasma bridge; nobody has confirmed which).
3. **Live GCS manifest read** (the decisive check) — downloaded and read
   `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` directly (13,615,477 rows)
   and searched case-insensitively for every aave/euler/fluid/compound/spark/radiant variant.

## The result

| Venue + chain           | Real rows in GCS                                                     | Turbo API reports                  | Verdict                                            |
| ----------------------- | -------------------------------------------------------------------- | ---------------------------------- | -------------------------------------------------- |
| `AAVE_V3` + `ARBITRUM`  | **18,771 captured**, 2022-03-12→2026-06-21                           | `0/0`, `{}`                        | **Read-path bug — real data hidden**               |
| `AAVE_V3` + `POLYGON`   | **24,278 captured**, 2022-03-12→2026-06-21                           | `0/0`, `{}`                        | **Read-path bug — real data hidden**               |
| `SPARK` (Ethereum)      | **7,405 captured**                                                   | not present in the response at all | **Read-path bug — omitted entirely**               |
| `EULER_V2` + `ARBITRUM` | 0 captured (52,888 rows, 100% `empty_confirmed`, stopped 2024-07-31) | `0/0`, `{}`                        | Accurate — genuinely never captured                |
| `EULER_V2` + `ETHEREUM` | 0 captured (same pattern)                                            | `0/0`, `{}`                        | Accurate — genuinely never captured                |
| `FLUID` + `ARBITRUM`    | 0 rows of any kind                                                   | `0/0`, `{}`                        | Accurate — never attempted (no adapter key exists) |
| `FLUID` + `PLASMA`      | 0 rows; no `PLASMA` chain value exists anywhere in the DEFI manifest | `0/0`, `{}`                        | Accurate — speculative placeholder, not wired      |

**AAVE_V3-ARBITRUM and AAVE_V3-POLYGON are large, real, currently-active deployments with a full year+ of ongoing
capture** — the turbo dashboard was simply wrong about both. Same for SPARK, which didn't even surface as a 0/0 row — it
was silently absent, a step worse than misreporting a real number as zero.

## Why this matters beyond the dashboard being wrong

This directly undermines any "which of these declared-but-empty venues should we bother with" triage done purely from
the turbo API — as this session's own capital-opportunity discussion was about to do. AAVE on Arbitrum and Polygon were
never actually empty; they were misreported. Any conclusion drawn from the dashboard's 0/0 reading alone —
deprioritizing, assuming no infra, deciding not to pursue — would have been based on a false signal.

## Update 2026-07-07 (systematic sweep — true scope is larger)

A full ~34-venue sweep of the GCS manifest (every remaining "0/0 orphan" venue from the earlier drilldown, plus bonus
finds surfaced incidentally) confirms the read-path bug is **not limited to the 3 originally found** — it hits at least
5 more confirmed venues, plus 4 more flagged for a direct turbo-API cross-check that this sweep (read-only GCS, no live
API calls) could not itself perform.

**5 more confirmed "REAL DATA HIDDEN" venues** (same bug class as AAVE_V3/SPARK — `capture_status="captured"`,
`row_count>0`, current through 2026-06-21, but turbo API would report these as never-captured):

| Venue + chain            | Real rows | Date range              | Caveat               |
| ------------------------ | --------- | ----------------------- | -------------------- |
| `MANTLE` + `ETHEREUM`    | 990       | 2023-10-06 → 2026-06-21 | 1 row/manifest-entry |
| `PUFFER` + `ETHEREUM`    | 871       | 2024-02-01 → 2026-06-21 | 1 row/manifest-entry |
| `STADER` + `ETHEREUM`    | 1,078     | 2023-07-10 → 2026-06-21 | 1 row/manifest-entry |
| `STAKEWISE` + `ETHEREUM` | 937       | 2023-11-28 → 2026-06-21 | 1 row/manifest-entry |
| `SWELL` + `ETHEREUM`     | 1,162     | 2023-04-17 → 2026-06-21 | 1 row/manifest-entry |

**Important caveat**: unlike AAVE_V3 (~760 rows/entry) or SPARK (~2.2 rows/entry), all 5 of these have **exactly 1 row
per `captured` manifest entry** — that shape looks like a presence/liveness marker, not real tick/price volume. Still a
genuine instance of the same dashboard bug (real → reported as `0/0`), just low materiality until someone spot-checks
one shard's actual parquet contents.

**4 more flagged for a direct live turbo-API cross-check** (large, real, currently-flowing GCS data; NOT yet confirmed
hidden because this pass was GCS-only, read-only, no live API call):

| Venue                                                                                                                      | Chain                                                                                                                           | Real rows | Date range                    |
| -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------- | ----------------------------- |
| `HYPERLIQUID`                                                                                                              | `HYPERLIQUID` (own chain label)                                                                                                 | 3,768,971 | 2023-11-01 → 2026-05-31       |
| `ASTER`                                                                                                                    | `BSC`                                                                                                                           | 1,066,091 | 2024-04-03 → 2026-05-31       |
| `COMPOUND_V3` (distinct from bare `COMPOUND`, which is genuinely empty — same naming-collision shape as AAVE vs `AAVE_V3`) | ARBITRUM/BASE/ETHEREUM/OPTIMISM                                                                                                 | 233,553   | 2022-08-13 → 2026-06-21       |
| `FLUID`                                                                                                                    | `ETHEREUM` (the originally-checked FLUID-ARBITRUM/PLASMA are still genuinely empty; this is a 3rd chain not previously checked) | 690       | 2026-02-21 → 2026-06-21 (new) |

HYPERLIQUID and ASTER are the operator-flagged CEFI/DEFI hybrids (see
`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`) — chain-side data lives under
`asset_group=defi`, so if the turbo API is also mishandling these two, it's the same read bug touching the
highest-volume venues in the whole DEFI corpus.

**Everything else checked came back genuinely empty** (ACROSS, all 6 BEEFY chains, BENQI, CONVEX, FLASHBOTS, IDLE ×3
chains, JITORESTAKING, KARAK ×2, KELPDAO, PENDLE ×2, RENZO ×2, STARGATE, SYMBIOTIC, bare UNISWAP, VENUS ×2,
YEARN_V3-ARBITRUM/OPTIMISM specifically — though `YEARN_V3-ETHEREUM` does have 831 tiny real entries, so the venue
overall isn't dead) — confirming the operator's original "maybe it's a naming mismatch" instinct doesn't generalize to
the whole orphan list; most `0/0` readings ARE honest, a specific minority are not.

## Todos

- [x] [CODE] P0. **ROOT-CAUSED + FIXED 2026-07-10.** Two independent, now-resolved bugs explain every symptom in this
      doc: 1. **AAVE_V3-ARBITRUM/POLYGON's original `0/0`** — the 2026-07-10 re-verification pass (below) correctly
      found the on-demand compute already returns real numbers, but couldn't identify why. Root cause: the `/turbo`
      all-asset-group (unfiltered) path is served from an **offline precomputed rollup blob**
      (`gs://{pid}-data-status-rollups/market-tick-data-service/full.json.gz`, refreshed every 5 min by a Cloud
      Scheduler → Cloud Run Job) rather than live-computing per request. That rollup worker has been stuck
      (`Cloud Scheduler firing every 10min into UNAVAILABLE, gRPC code 14`) since **2026-07-05T15:53Z** — confirmed live
      via `client.get_blob_metadata(...)`, blob `last_modified=2026-07-05T15:53:10.161Z`, matching exactly. The 30-min
      staleness gate that should have caught this and fallen through to on-demand compute (`_read_rollup_if_fresh`) had
      its own bug — it read `meta.updated` (an attribute that does not exist on the real `BlobMetadata` dataclass; only
      `meta.last_modified` does), so `getattr(meta, "updated", None)` always returned `None` and the staleness check
      silently no-op'd, serving the frozen 2026-07-05 blob indefinitely. **Already fixed** by `deployment-api@3847d6f`
      (2026-07-08, `fix(data-status): rollup staleness gate never fires — meta.updated doesn't exist`) — landed
      BEFORE this 2026-07-10 sub-agent session started, which is why the on-demand path (used by the 2026-07-10
      re-verification pass, and independently re-confirmed here via `svc.get_manifest_status(...)` with the rollup
      correctly falling through:
      `INFO rollup for market-tick-data-service is stale (415964s > 1800s threshold) — falling through to on-demand`)
      already returns correct data. The underlying rollup-worker infra outage is still open (noted as such in 3847d6f's
      own commit message) — `/turbo`'s DEFAULT unfiltered response is now CORRECT but SLOW (~3-4 min cold, one full GCS
      manifest read) until the Cloud Run Job is restarted; that's a separate ops ticket, not a data-correctness bug. 2.
      **SPARK-ETHEREUM's "not present in the response at all"** — `unified-api-contracts`'s
      `DEFI_INSTRUMENTS_NOT_YET_COLLECTED` (`capability_declarations/_defi_coverage.py`) still listed `SPARK-ETHEREUM`,
      with a comment claiming "instruments-service has never written historical parquets for this venue" as of
      2026-04-29 — stale since at least 2026-07-07 (7,405 real captured `lending_indices` rows exist,
      2023-03-07→2026-06-21). `venue_has_no_expected_defi_coverage("SPARK-ETHEREUM")` returned `True`, which
      short-circuited every `mtds_expected_dates_cached()` call for the venue to an empty set → the MTDS honest-coverage
      override always computed `expected_shards=0` for it. **Fixed**: removed the stale entry
      (`unified-api-contracts@92b1d1a8`). 3. **Bonus, found during root-cause verification**: 5 more venues from the "5
      more confirmed hidden" table below (MANTLE/STADER/STAKEWISE/SWELL/ANKR-ETHEREUM) had real captured `lst_rates`
      shards but ZERO `DEFI_VENUE_DATA_TYPE_CAPABILITIES` entry at all — same failure mode as (2) but via a different
      code path (`get_expected_data_types_for_venue` returning `[]` rather than the coverage-exclusion flag). **Fixed**,
      same commit. See the "Update 2026-07-10" section below for the full verified evidence + the PUFFER-ETHEREUM
      resolution (item 4 in that section directly explains the "internal inconsistency" the 2026-07-10 re-verification
      pass flagged as unexplained). Regression test: `unified-api-contracts`
      `tests/unit/test_mtds_venue_coverage.py::TestDefiTurboApiHiddenVenuesFix` (4 tests, all passing against current
      HEAD).
- [x] [VERIFY] P1. Once root-caused, re-run the full DeFi turbo pull and check whether OTHER venues besides these 3 are
      affected by the same read-path bug — this was found by chasing 3 specific protocols on an operator hunch, not from
      a systematic sweep. The true scope could be larger. **Done 2026-07-07**: systematic ~34-venue sweep found 5 more
      confirmed hidden venues (MANTLE/PUFFER/STADER/STAKEWISE/SWELL-ETHEREUM, all low-volume liveness-marker shaped) —
      see "Update 2026-07-07" section above. Everything else checked is genuinely empty.
- [x] [VERIFY] P0. **DONE 2026-07-10 — confirmed via direct code-path reproduction
      (`DataStatusService._read_defi_merged_index`), not a live HTTP call, but this IS the exact function `/turbo`
      wraps.** `COMPOUND_V3-{ARBITRUM,BASE,ETHEREUM,OPTIMISM,SCROLL}` and `FLUID-ETHEREUM` are all present in the merged
      DEFI index with real captured data through 2026-07-09 (COMPOUND_V3-POLYGON stopped 2023-02-13 and
      COMPOUND_V3-SCROLL stopped 2024-04-21 — genuine capture gaps, not a read-path bug) — **ruled out, NOT hidden**,
      both already have correct `DEFI_VENUE_DATA_TYPE_CAPABILITIES` entries. `HYPERLIQUID`/`ASTER`: **CONFIRMED
      hidden**, zero substring matches anywhere in the merged DEFI index (main bucket + all 10 sub-dimension buckets)
      despite the doc's own GCS sweep finding 3,768,971 / 1,066,091 real rows under `asset_group=defi`. Root cause
      (distinct from the read-path bug fixed above): neither venue is declared in UAC `ALL_DEFI_VENUES` (they're
      primarily CEFI-registered venues — `cefi_instrument_universe.py`, `cefi_margin_tiers.py`,
      `cefi_perp_venue_endpoints.py`), so `_filter_to_canonical_defi_venues`'s whitelist (built from `ALL_DEFI_VENUES` +
      `LEGACY_DEFI_VENUE_ALIASES`) drops their rows before they ever reach the aggregator — this is a
      **registry-completeness gap for CEFI/DEFI hybrid venues**, not the same read/aggregation bug as AAVE/SPARK/the LST
      venues (those WERE declared and still zeroed out; these were never declared at all). **NOT fixed this pass** —
      wiring HYPERLIQUID/ASTER into the DEFI venue registry needs the CEFI/DEFI dual-counting axis decision from
      `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` first (declaring them into
      `ALL_DEFI_VENUES` without that decision risks double-counting the same on-chain rows under both CEFI and DEFI
      totals). Tracked as new P1 todo below.
- [x] [VERIFY] P3. **DONE 2026-07-10** — spot-checked all 6 (5 + PUFFER) via `capture_status` breakdown against the live
      main DEFI bucket (not just row presence): every one of MANTLE/STADER/STAKEWISE/SWELL/ANKR/PUFFER-ETHEREUM has
      `capture_status=='captured'` (not `empty_confirmed`/`expected_unattempted`) specifically on
      `data_type=='lst_rates'` — MANTLE 990, STADER 1,078, STAKEWISE 937, SWELL 1,162, PUFFER 871, ANKR 2,000 real
      captured rows, all through 2026-06-21 (none show data past that date — worth its own note: capture appears to have
      stalled for this venue family ~2.5 weeks before this check, unlike AAVE/SPARK/COMPOUND_V3/FLUID which are current
      through 2026-07-09; not investigated further here, out of scope). Confirmed genuine `lst_rates` liveness/rate data
      (not zero-volume placeholders) — commercially low-materiality per row count, but real.
      `DEFI_VENUE_DATA_TYPE_CAPABILITIES` entries added for all 6 (PUFFER's pre-existing entry had the WRONG data_type
      declared — `staking_yields`/`oracle_prices`, 0 captured rows — `lst_rates` added alongside).
- [x] [CODE] P1. **SPLIT 2026-07-12 (§A2 finding 113) — ETHEREUM half DONE.** Original combined todo text (kept for
      context): "Fix the stale `defi_venues.py` phase-dict comment/state for `EULER_V2-ARBITRUM`/`EULER_V2-ETHEREUM` —
      it still says 'no UAC subgraph_id registered' but real Goldsky subgraph IDs were verified GREEN 2026-06-02, after
      that comment was written. The phase should likely flip once someone confirms whether the subgraph is actually
      being polled (it currently isn't — see next todo) — don't flip the label without also landing the capture wiring,
      or the dashboard will just report a different kind of wrong number." **ETHEREUM resolved**: verified real —
      `defi_venues.py` phase flipped pipeline→live for EULER_V2-ETHEREUM with an accurate comment
      (`unified-api-contracts@42ce2de3`, 2026-07-10; IS reference-catalog side `instruments-service@9b0c1095`, both
      code-verified). This is reference-data-catalog wiring only, NOT MTDS market-data capture — MTDS was never actually
      polled for EULER_V2 (see the reworded capture-gap todo below, which stays fully open). The ARBITRUM half of the
      original todo was still wrong as of this split and is spun out as its own open todo immediately below (the fix
      needed there is NOT "confirm polling then flip," per the original text — see why).
- [x] [CODE] P1. **New 2026-07-12 (§A2 finding 113), split from the todo above.** `EULER_V2-ARBITRUM`'s
      `defi_venues.py:457` phase-dict comment is STILL factually wrong:
      `# EULER_V2-ARBITRUM + FLUID-ARBITRUM: no UAC subgraph_id registered → 0 captured rows.` — but real Goldsky
      `SUBGRAPH_IDS` have been registered for EULER_V2-ARBITRUM and verified GREEN since 2026-06-02
      (`capability_declarations/_defi.py:211-221`). The real reason EULER_V2-ARBITRUM stays `pipeline` (unlike
      EULER_V2-ETHEREUM, now `live`) has nothing to do with subgraph registration: the instruments-service `euler_v2.py`
      reference-data adapter is Ethereum-only. Fix: correct the ARBITRUM comment to state that real reason, mirroring
      the accurate ETHEREUM comment already in the file (`defi_venues.py:525-527`: "EULER_V2-ARBITRUM stays pipeline:
      euler_v2.py's adapter only supports ETHEREUM (\_DEFAULT_CHAIN, single flat \_MVP_MARKETS list, no per-chain
      dict)") instead of repeating the stale no-subgraph-id claim. — already covered by
      defi_satellite_ao_dispatch_batch1_2026_07_25.md (see that doc for execution).
- [x] [CODE] P2. **REWORDED 2026-07-12 (§A2 finding 113) — three concrete gaps, not a single open decision.** Original
      todo text (kept for context): "Decide whether to actually wire EULER_V2 capture given real subgraph infra now
      exists (verified working 2026-06-02, never actually polled) — this is a 'finish what's already 90% built' case,
      same class as the RENZO finding in the tracker's unregistered-handler-audit item." Code-verified breakdown of what
      "wire it" actually requires: 1. **Capability `mtds_operations` mismatch** — the `euler_v2` `_ProtocolCapability`
      declares `mtds_operations=["collect-lending-indices", "collect-liquidations"]`
      (`capability_declarations/_defi.py:476`), but neither MTDS's `LendingIndicesHandler` nor `LiquidationsHandler`
      references `euler`/`EULER_V2` anywhere — the real EULER_V2 collector lives under the `collect-evm-defi` CLI
      operation (`market_tick_data_service/cli/handlers/evm_defi_handler.py` / `evm_defi_collectors.py`, wired via
      `cli/main.py`'s `"collect-evm-defi": EvmDefiHandler` mapping). Fix: either repoint the capability's
      `mtds_operations` to `collect-evm-defi`, or add real EULER_V2 handling to the lending/liquidations handler
      defaults — whichever matches how the collector is actually meant to be invoked. 2. **Capability-gate entries exist
      but zero rows ever captured** — `EULER_V2-ETHEREUM`/`EULER_V2-ARBITRUM` DO have
      `DEFI_VENUE_DATA_TYPE_CAPABILITIES` entries (`defi_venue_capabilities.py:155-156`, `lending_indices` only), added
      incidentally in `unified-api-contracts@92b1d1a8` alongside the RADIANT-ETHEREUM/VENUS/BENQI D10 capability
      backfill — but that same commit's own comment confirms "the prod manifest shows ZERO real
      captured/attempted_failed rows for ANY data_type on ANY of these 4 venues, ever"
      (`defi_venue_capabilities.py: 139-140`). The capability-gate declaration existing does not mean capture has
      ever run. 3. **NEW — stalled upstream subgraph (~38 days behind), found 2026-07-10.** The same `92b1d1a8` comment
      block records a live probe: "the EULER_V2 Goldsky subgraph IS reachable but its indexed HEAD is ~271K blocks (~38
      days) behind current Ethereum mainnet — a dead/stalled upstream that should be re-verified before any future phase
      flip to 'live'" (`defi_venue_capabilities.py:150-153`). Any capture wiring landed before this is re-verified as
      caught-up would produce results that are stale by construction — re-check the subgraph's sync lag BEFORE wiring
      gap 1 above, not after. — **RE-VERIFIED 2026-07-26 (slot-11, data_engineering) — CLOSED as BLOCKED-UPSTREAM, worse
      than measured.** Live-queried both Goldsky endpoints
      (`api.goldsky.com/api/public/project_cm4iagnemt1wp01xn4gh1agft/subgraphs/euler-v2-{mainnet,arbitrum}/latest/gn`)
      with the standard `_meta` health-check query — both return
      `HTTP 404 "Subgraph not found. Have you deleted this subgraph recently?"`, confirmed on retry (not transient)
      and via an alternate version-pinned path. This is NOT "still 38 days behind" — the subgraph no longer exists at
      this endpoint at all. Per this todo's own gate ("do NOT wire capture if it is still stalled"), gaps 1+2
      (capability `mtds_operations` repoint, capture trigger) are NOT actioned — nothing to wire against. No code
      changed for this sub-item. Note: `defi_venues.py` currently has `EULER_V2-ETHEREUM: "live"` despite this — a
      pre-existing inconsistency flagged here for whoever next touches that phase dict, not fixed in this pass (out of
      scope for a capture-wiring todo; the phase-dict fix would be its own small follow-up). — already covered by
      defi_satellite_ao_dispatch_batch2_2026_07_26.md (slot-11, BLOCKED-UPSTREAM) (see that doc for execution).
- [x] ✅ [VERIFY] P3. Resolve which "Plasma" chain UAC's `FLUID-PLASMA`/`AAVE-PLASMA` placeholders are meant to refer to
      (the 2025 Tether-backed Plasma L1, or the unrelated pre-2020 Polygon Plasma bridge) before doing anything else
      with those two entries — UAC's own maintainers have this flagged unresolved. — **DONE (slot-11, 2026-07-26):
      RESOLVED via real-world verification, not a guess — `unified-api-contracts@fc788094`.** Web search confirms Aave
      launched on Plasma (the 2025 Tether-backed L1, XPL, chain_id 9745) 2025-09-25 with >$6.5B deposits in the first
      week (now Aave's 2nd-largest deployment by TVL after Ethereum mainnet); Fluid also has a confirmed live Plasma
      deployment. The pre-existing code comment claiming "Polygon Plasma bridge-side" (the dead 2018-2020 bridge) was
      simply wrong — fixed with the real-world citation. This is a large, real, currently active market with ZERO chain
      registration anywhere in this codebase (no `MAINNET_CHAIN_IDS`, no `CHAIN_GENESIS_DATES`, no capture adapter) —
      full onboarding is real feature work, properly scoped as its own follow-up:
      `issues/defi_plasma_chain_onboarding_gap_2026_07_26.md` (not attempted here — identity resolution was this todo's
      actual scope).
- [ ] [SCRIPT] P1. **RECLASSIFIED 2026-08-08 — axis decision already ruled, only mechanical UAC registration remains.**
      Original text (kept for context): "PARTIALLY FIXED 2026-07-21 (Track 6,
      `defi_consolidated_closeout_2026_07_18.md`) — user-facing symptom resolved via a deployment-api-local stopgap, UAC
      declaration still open." `deployment-api@427ede5` adds a supplemental whitelist
      (`_CEFI_DEFI_HYBRID_VENUE_CHAIN_PAIRS` in `defi.py`) admitting the exact confirmed
      `(HYPERLIQUID, HYPERLIQUID)`/`(ASTER, BSC)` pairs so their real captured rows stop being dropped by
      `_filter_to_canonical_defi_venues` — NOT a double-counting risk (this whitelist only gates DEFI-category bucket
      reads; CEFI's own coverage numbers come from a completely separate CEFI-category read), matching the
      operator-confirmed hybrid architecture already on record (Update §3 below: CEFI holds instrument definitions, DEFI
      holds chain-level settlement data — two distinct row sets). **The "CEFI/DEFI dual-counting axis decision" this
      todo names as a prerequisite is not actually undecided** — this todo's own prior text above already states the
      whitelist is "NOT a double-counting risk," and the sibling doc
      `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` records the operator ruling directly:
      "Separately confirmed as NOT a bug: HYPERLIQUID and ASTER appear in DeFi's venue list too (operator-confirmed
      intentional, 2026-07-07)... CEFI holds the instrument definitions... while DEFI holds the chain-level
      classification/context... The `0/0` under DEFI isn't evidence of a bug on its own." That doc's own broader
      Decision Gate D6 (generalizing `instrument_type` into a breakdown dimension everywhere) stays genuinely open, but
      the narrow question this todo was blocked on — whether declaring HYPERLIQUID/ASTER into DEFI's registries risks
      double-counting against CEFI — is already ruled: it does not, by design. Re-verified 2026-08-08: both venues are
      still absent from `ALL_DEFI_VENUES` (`unified-api-contracts/unified_api_contracts/registry/defi_venues.py`, 0 grep
      hits for `HYPERLIQUID`/`ASTER`) and from `DEFI_VENUE_DATA_TYPE_CAPABILITIES`
      (`unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py`, same 0 hits). **Remaining work
      is now purely mechanical**: declare `(HYPERLIQUID, HYPERLIQUID)` and `(ASTER, BSC)` in `ALL_DEFI_VENUES`, and add
      matching `DEFI_VENUE_DATA_TYPE_CAPABILITIES` entries, mirroring the confirmed real data types (`data_type`
      observed in the GCS sweep above) — no further design decision needed first.
- [x] [OPS] P1. **New 2026-07-10.** Restart/fix the `uts-prod-data-status-rollup` Cloud Run Job — Cloud Scheduler has
      been firing into `UNAVAILABLE` (gRPC code 14) since at least 2026-07-05T15:53Z (confirmed still broken 2026-07-10,
      blob age ~4.8 days at check time). The 2026-07-08 staleness-gate fix (3847d6f) means `/turbo` now degrades to
      correct-but-slow (~3-4 min, one full GCS manifest read) on-demand compute instead of silently serving stale data,
      but the DEFAULT unfiltered `/turbo` view is effectively unusable in that window without the rollup — this is the
      actual remaining user-facing symptom, not a data-correctness bug anymore. — already covered by
      defi_satellite_ao_dispatch_batch1_2026_07_25.md (slot-7, DONE) (see that doc for execution).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - residual is gated on the CEFI/DEFI dual-counting axis decision
  in a still-open sibling doc; declaring HYPERLIQUID/ASTER without it risks double-counting

- **2026-07-10 (later same day)** — **Root-caused + fixed for real.** Picked up right where the earlier 2026-07-10
  re-verification pass left off (root cause unidentified, PUFFER anomaly unexplained, HYPERLIQUID/ASTER unconfirmed).
  Found and confirmed, all via live GCP ADC reads against the real prod GCS DEFI manifest (never asserted from code
  reading alone):
  1. AAVE_V3-ARBITRUM/POLYGON's original `0/0` = the `/turbo` unfiltered path serving a rollup blob frozen since
     2026-07-05T15:53Z (rollup-worker Cloud Scheduler outage) past its 30-min staleness window, because the
     staleness-check itself read a non-existent `meta.updated` attribute (always `None`) instead of the real
     `meta.last_modified` — **already fixed** by `deployment-api@3847d6f` (2026-07-08), landed before this session;
     verified live
     (`rollup for market-tick-data-service is stale (415964s > 1800s threshold) — falling through to on-demand`, blob
     `last_modified=2026-07-05T15:53:10.161Z` confirmed via `client.get_blob_metadata`).
  2. SPARK-ETHEREUM's "not present at all" = stale `DEFI_INSTRUMENTS_NOT_YET_COLLECTED` entry (claimed never-captured as
     of 2026-04-29; 7,405 real captured `lending_indices` rows exist). **Fixed**: removed
     (`unified-api-contracts@92b1d1a8`).
  3. MANTLE/STADER/STAKEWISE/SWELL/ANKR-ETHEREUM = real captured `lst_rates` shards (990/1,078/937/1,162/2,000 rows,
     `capture_status=='captured'` confirmed, not placeholder rows) but zero `DEFI_VENUE_DATA_TYPE_CAPABILITIES` entry.
     **Fixed**: added, same commit.
  4. PUFFER-ETHEREUM's "internal inconsistency" (`dates_found=0` despite `captured=21`) from the earlier re-verification
     pass = its EXISTING capability entry declared the WRONG data_type (`staking_yields`/ `oracle_prices`, 0 real
     captured rows) — its real 871 captured rows are `lst_rates`, same as the other 5, just previously mis-declared
     instead of undeclared. **Fixed**: `lst_rates` added alongside the existing (roadmap, 0-captured) entries, same
     commit.
  5. HYPERLIQUID/ASTER = **CONFIRMED genuinely hidden** (not "intentional CEFI-side-only scoping" as the earlier pass
     guessed) — neither is declared in UAC `ALL_DEFI_VENUES` at all, so the DEFI-venue whitelist filter drops their rows
     before the aggregator ever sees them. Real bug, but NOT the same read/aggregation bug as the rest of this doc
     (those venues WERE declared and still zeroed; these were never declared) — needs the CEFI/DEFI axis-model decision
     first. New P1 todo filed, not fixed this pass.
  6. COMPOUND_V3 (5 of 6 chains)/FLUID-ETHEREUM confirmed correctly wired already — ruled out. Shipped:
     `unified-api-contracts@92b1d1a8`
     (`fix(defi): turbo API hid real captured MANTLE/STADER/STAKEWISE/SWELL/ ANKR/PUFFER/SPARK-ETHEREUM DeFi data`) +
     new regression test class `TestDefiTurboApiHiddenVenuesFix` (4 tests, passing against current
     `unified-api-contracts` HEAD). **Caveat on the commit**: this repo's `live-defi-rollout` branch had 4+ other
     concurrent same-slot agent processes actively committing to the exact same file (`defi_venue_capabilities.py`)
     during this session (git lock contention observed directly, `.git/index.lock` collisions, one full edit silently
     wiped by a concurrent reset and had to be redone) — the shipped commit's diff ended up also containing an unrelated
     D10 capability backfill (RADIANT-ETHEREUM/EULER_V2/VENUS/BENQI) from one of those concurrent processes, picked up
     incidentally by the file-scoped `git add`. Verified no duplicate/conflicting entries resulted and all tests pass
     against final HEAD, but flagging the attribution mismatch for the record. deployment-api itself was not touched —
     the actual bug lived entirely in `unified-api-contracts` registry data (deployment-api consumes it via an editable
     local path dependency, so no deployment-api code change or version bump was needed for this local checkout; prod
     picks it up on `unified-api-contracts`'s next version bump + deployment-api's pin update).
- **2026-07-10** — **Re-verification pass (sub-agent, part of the instruments-completion-tracker sweep) — the read-path
  bug is NOT reproducible today via the exact code path `/turbo` uses (with the honest caveat that root cause was never
  found, so this is not a confident "fixed").** Direct call to `DataStatusService().get_manifest_status(...)` against
  real prod GCS (the function `/turbo`'s `_manifest_source` wraps) returns correct, non-zero coverage for all 8
  originally-flagged venues (AAVE_V3-ARBITRUM/POLYGON, SPARK-ETHEREUM, MANTLE/STADER/STAKEWISE/SWELL-ETHEREUM,
  COMPOUND_V3 all 4 chains, FLUID-ETHEREUM). Full detail + one real residual anomaly found (PUFFER-ETHEREUM,
  dates_found=0 despite captured=21 — a different, smaller bug) in the updated P0 todo above. No code changed — this was
  a read-only reproduction attempt against live data. Recommend a live-HTTP `/turbo` call with the cache cleared as the
  final confirming step before closing this doc.
- **2026-07-07** — Filed after a 3-way parallel check (write-path trace, UAC registry check, live GCS manifest read)
  chasing an operator hypothesis about naming mismatches. The hypothesis wasn't quite right — no naming mismatch exists
  — but the underlying instinct ("the dashboard's 0/0 might not be honest") was correct for 3 of the 6 venues checked.
  No files edited; the GCS read was read-only (download + pandas, no writes).
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — dropped the tracker/plasma-onboarding docs (both
  spun-out or upstream context, not needed for the sole remaining open [CODE] P1 item); added
  `defi_venue_capabilities.py` (DEFI_VENUE_DATA_TYPE_CAPABILITIES — the durable HYPERLIQUID/ASTER declaration still
  needs both this and `defi_venues.py`'s ALL_DEFI_VENUES).
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid (prior verdict re-affirmed) —
  the sole remaining todo (durable UAC registry declaration for HYPERLIQUID/ASTER) is still gated on the open CEFI/DEFI
  dual-counting axis decision in a still-open sibling doc. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — re-confirmed independently; no content change
  since the 2026-08-04 audit (context-scout metadata only, per git log). Sole remaining todo (durable UAC registry
  declaration for HYPERLIQUID/ASTER) is still gated on the open CEFI/DEFI dual-counting axis decision in a still-open
  sibling doc. Doc stays `assigned_vm: NA`.
- **2026-08-08**: prior audits (07-30/08-04/08-07) mischaracterized the residual as blocked on an open axis decision —
  re-read of this todo's own text plus `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` shows the
  narrow HYPERLIQUID/ASTER dual-counting question was already operator-ruled NOT a double-counting risk on 2026-07-07
  (that doc's broader Decision Gate D6 stays open, but that's a separate, wider question this todo never actually
  depended on). Re-verified live: `HYPERLIQUID`/`ASTER` still absent from both `ALL_DEFI_VENUES`
  (`unified-api-contracts/unified_api_contracts/registry/defi_venues.py`) and `DEFI_VENUE_DATA_TYPE_CAPABILITIES`
  (`.../defi_venue_capabilities.py`) — 0 grep hits each. Reclassified the sole open todo `[CODE]` -> `[SCRIPT]` P1
  (deterministic UAC registration, no remaining judgment call). Flipped `assigned_vm: NA` -> `assigned_vm: planning` —
  this was the doc's only open todo.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.
