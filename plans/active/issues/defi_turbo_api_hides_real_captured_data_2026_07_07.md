---
doc_type: issue
title: 'Turbo API silently reports 0/0 for DeFi venues with real, current captured data (AAVE_V3-ARBITRUM/POLYGON, SPARK) -- a read-path bug, not a capture gap'
summary:
  'Chasing an operator hypothesis that AAVE_V3-ARBITRUM/POLYGON and EULER_V2/FLUID might have real data hiding
  under a mismatched venue name, a live read of the actual GCS DEFI availability manifest
  (market-data-tick-defi-prd-central-element-323112) found something more serious: AAVE_V3-ARBITRUM has 18,771
  real captured rows and AAVE_V3-POLYGON has 24,278, both current through 2026-06-21, under the exact canonical
  venue+chain the turbo API already expects -- yet GET /api/data-status/turbo reports dates_found=0,
  dates_expected=0, instrument_types={} for both. SPARK has 7,405 real captured rows and does not appear in the
  turbo response AT ALL. This is a read/aggregation-side bug in deployment-api, not a write-side naming mismatch
  and not a capture gap -- the data genuinely exists. EULER_V2 (both chains) and FLUID-ARBITRUM/PLASMA, by
  contrast, are confirmed to have zero real data anywhere -- those really are unwired, not hidden.'
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
    honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P0
source:
  'Operator hypothesis follow-up, 2026-07-07 -- verified against the real GCS manifest via
  instruments-service/.venv + GCP ADC, not asserted from code reading alone'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: opus-required
thinking_tier: high
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding — a live, current data-correctness bug, not a design question.** Filed P0
> because the honest-coverage dashboard is understating real DeFi coverage for at least 3 confirmed venues, and
> this class of bug (real data silently missing from the aggregation layer) is exactly the kind of thing that
> could mislead a real capital-allocation decision if someone concluded "no data → not worth pursuing" from the
> turbo API alone. It doesn't — the data was there the whole time.

## What was actually checked, and how

The operator's hypothesis was: some of the "0/0, never captured" DeFi venues from the earlier drilldown might
actually have real data sitting under a different, non-canonical venue string. A 3-way check ran in parallel:

1. **MTDS write-path trace** — confirmed the manifest-write helper (`_defi_manifest.py:760-768`,
   `_normalise_venue`) produces the exact canonical `AAVE_V3`/`EULER_V2`/`FLUID` strings, with `chain` written as a
   separate field, never folded into `venue`. No naming-format mismatch exists in the write path for any of these
   protocols.
2. **UAC registry check** — confirmed AAVE_V3-ARBITRUM/POLYGON are declared fully `"live"` in `defi_venues.py`
   with real subgraph IDs, launch dates, and capability entries; EULER_V2 has real, *recently verified* Goldsky
   subgraph IDs for both ARBITRUM and ETHEREUM (`_defi.py:217`, "Verified GREEN via Goldsky 2026-06-02") but **zero
   entries** in `DEFI_VENUE_DATA_TYPE_CAPABILITIES`, and its `defi_venues.py` phase-dict comment ("no UAC
   subgraph_id registered → 0 rows") is now **stale** — it predates the 2026-06-02 subgraph verification and was
   never updated. FLUID has only an `ETHEREUM` subgraph ID; no ARBITRUM or PLASMA entry exists anywhere, and
   "PLASMA" itself has no chain config in UAC at all (flagged by UAC's own maintainers as
   `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` — likely conflating the 2025 Tether-backed Plasma L1 with the old,
   unrelated 2018-2020 Polygon Plasma bridge; nobody has confirmed which).
3. **Live GCS manifest read** (the decisive check) — downloaded and read
   `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` directly (13,615,477
   rows) and searched case-insensitively for every aave/euler/fluid/compound/spark/radiant variant.

## The result

| Venue + chain | Real rows in GCS | Turbo API reports | Verdict |
|---|---|---|---|
| `AAVE_V3` + `ARBITRUM` | **18,771 captured**, 2022-03-12→2026-06-21 | `0/0`, `{}` | **Read-path bug — real data hidden** |
| `AAVE_V3` + `POLYGON` | **24,278 captured**, 2022-03-12→2026-06-21 | `0/0`, `{}` | **Read-path bug — real data hidden** |
| `SPARK` (Ethereum) | **7,405 captured** | not present in the response at all | **Read-path bug — omitted entirely** |
| `EULER_V2` + `ARBITRUM` | 0 captured (52,888 rows, 100% `empty_confirmed`, stopped 2024-07-31) | `0/0`, `{}` | Accurate — genuinely never captured |
| `EULER_V2` + `ETHEREUM` | 0 captured (same pattern) | `0/0`, `{}` | Accurate — genuinely never captured |
| `FLUID` + `ARBITRUM` | 0 rows of any kind | `0/0`, `{}` | Accurate — never attempted (no adapter key exists) |
| `FLUID` + `PLASMA` | 0 rows; no `PLASMA` chain value exists anywhere in the DEFI manifest | `0/0`, `{}` | Accurate — speculative placeholder, not wired |

**AAVE_V3-ARBITRUM and AAVE_V3-POLYGON are large, real, currently-active deployments with a full year+ of ongoing
capture** — the turbo dashboard was simply wrong about both. Same for SPARK, which didn't even surface as a 0/0
row — it was silently absent, a step worse than misreporting a real number as zero.

## Why this matters beyond the dashboard being wrong

This directly undermines any "which of these declared-but-empty venues should we bother with" triage done purely
from the turbo API — as this session's own capital-opportunity discussion was about to do. AAVE on Arbitrum and
Polygon were never actually empty; they were misreported. Any conclusion drawn from the dashboard's 0/0 reading
alone — deprioritizing, assuming no infra, deciding not to pursue — would have been based on a false signal.

## Update 2026-07-07 (systematic sweep — true scope is larger)

A full ~34-venue sweep of the GCS manifest (every remaining "0/0 orphan" venue from the earlier drilldown, plus
bonus finds surfaced incidentally) confirms the read-path bug is **not limited to the 3 originally found** — it
hits at least 5 more confirmed venues, plus 4 more flagged for a direct turbo-API cross-check that this sweep
(read-only GCS, no live API calls) could not itself perform.

**5 more confirmed "REAL DATA HIDDEN" venues** (same bug class as AAVE_V3/SPARK — `capture_status="captured"`,
`row_count>0`, current through 2026-06-21, but turbo API would report these as never-captured):

| Venue + chain | Real rows | Date range | Caveat |
|---|---|---|---|
| `MANTLE` + `ETHEREUM` | 990 | 2023-10-06 → 2026-06-21 | 1 row/manifest-entry |
| `PUFFER` + `ETHEREUM` | 871 | 2024-02-01 → 2026-06-21 | 1 row/manifest-entry |
| `STADER` + `ETHEREUM` | 1,078 | 2023-07-10 → 2026-06-21 | 1 row/manifest-entry |
| `STAKEWISE` + `ETHEREUM` | 937 | 2023-11-28 → 2026-06-21 | 1 row/manifest-entry |
| `SWELL` + `ETHEREUM` | 1,162 | 2023-04-17 → 2026-06-21 | 1 row/manifest-entry |

**Important caveat**: unlike AAVE_V3 (~760 rows/entry) or SPARK (~2.2 rows/entry), all 5 of these have **exactly 1
row per `captured` manifest entry** — that shape looks like a presence/liveness marker, not real tick/price
volume. Still a genuine instance of the same dashboard bug (real → reported as `0/0`), just low materiality until
someone spot-checks one shard's actual parquet contents.

**4 more flagged for a direct live turbo-API cross-check** (large, real, currently-flowing GCS data; NOT yet
confirmed hidden because this pass was GCS-only, read-only, no live API call):

| Venue | Chain | Real rows | Date range |
|---|---|---|---|
| `HYPERLIQUID` | `HYPERLIQUID` (own chain label) | 3,768,971 | 2023-11-01 → 2026-05-31 |
| `ASTER` | `BSC` | 1,066,091 | 2024-04-03 → 2026-05-31 |
| `COMPOUND_V3` (distinct from bare `COMPOUND`, which is genuinely empty — same naming-collision shape as AAVE vs `AAVE_V3`) | ARBITRUM/BASE/ETHEREUM/OPTIMISM | 233,553 | 2022-08-13 → 2026-06-21 |
| `FLUID` | `ETHEREUM` (the originally-checked FLUID-ARBITRUM/PLASMA are still genuinely empty; this is a 3rd chain not previously checked) | 690 | 2026-02-21 → 2026-06-21 (new) |

HYPERLIQUID and ASTER are the operator-flagged CEFI/DEFI hybrids (see
`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`) — chain-side data lives under
`asset_group=defi`, so if the turbo API is also mishandling these two, it's the same read bug touching the
highest-volume venues in the whole DEFI corpus.

**Everything else checked came back genuinely empty** (ACROSS, all 6 BEEFY chains, BENQI, CONVEX, FLASHBOTS, IDLE
×3 chains, JITORESTAKING, KARAK ×2, KELPDAO, PENDLE ×2, RENZO ×2, STARGATE, SYMBIOTIC, bare UNISWAP, VENUS ×2,
YEARN_V3-ARBITRUM/OPTIMISM specifically — though `YEARN_V3-ETHEREUM` does have 831 tiny real entries, so the venue
overall isn't dead) — confirming the operator's original "maybe it's a naming mismatch" instinct doesn't generalize
to the whole orphan list; most `0/0` readings ARE honest, a specific minority are not.

## Todos

- [ ] [CODE] P0. Root-cause the deployment-api read/aggregation bug that produces `0/0` for `AAVE_V3-ARBITRUM`,
      `AAVE_V3-POLYGON`, and drops `SPARK` entirely, despite real captured rows existing under the exact canonical
      `(venue, chain)` key in the source manifest. Start in `deployment-api/deployment_api/services/data_status/`
      — likely the same venue/chain-grouping or filtering logic already touched by this session's CEFI
      chains-vs-venues fix, but this is DeFi-side and venue+chain-keyed rather than chains-suppress-venues, so
      confirm it's a distinct bug before assuming the same fix applies.
- [x] [VERIFY] P1. Once root-caused, re-run the full DeFi turbo pull and check whether OTHER venues besides these
      3 are affected by the same read-path bug — this was found by chasing 3 specific protocols on an operator
      hunch, not from a systematic sweep. The true scope could be larger. **Done 2026-07-07**: systematic ~34-venue
      sweep found 5 more confirmed hidden venues (MANTLE/PUFFER/STADER/STAKEWISE/SWELL-ETHEREUM, all low-volume
      liveness-marker shaped) — see "Update 2026-07-07" section above. Everything else checked is genuinely empty.
- [ ] [VERIFY] P0. Directly query the live turbo API (`GET /api/data-status/turbo?service=market-tick-data-service&asset_group=DEFI`)
      for `venue=HYPERLIQUID`, `venue=ASTER`, `venue=COMPOUND_V3`, and `venue=FLUID&chain=ETHEREUM` to confirm
      whether they're ALSO hidden — these are large (HYPERLIQUID: 3.77M rows, ASTER: 1.07M rows, COMPOUND_V3:
      233K rows), so if hidden, this is a bigger deal than the original 3-venue finding. Raised bumping this to P0
      because HYPERLIQUID/ASTER are the two highest-volume DEFI-side datasets found hidden anywhere so far.
- [ ] [VERIFY] P3. Spot-check one shard's actual parquet contents for the 5 tiny liveness-marker-shaped venues
      (MANTLE/PUFFER/STADER/STAKEWISE/SWELL-ETHEREUM, ~1 row/entry) before treating them as commercially
      meaningful — the bug is real either way, but the fix priority should reflect actual data volume, not just
      bug presence.
- [ ] [CODE] P1. Fix the stale `defi_venues.py` phase-dict comment/state for `EULER_V2-ARBITRUM`/`EULER_V2-ETHEREUM`
      — it still says "no UAC subgraph_id registered" but real Goldsky subgraph IDs were verified GREEN
      2026-06-02, after that comment was written. The phase should likely flip once someone confirms whether the
      subgraph is actually being polled (it currently isn't — see next todo) — don't flip the label without also
      landing the capture wiring, or the dashboard will just report a different kind of wrong number.
- [ ] [CODE] P2. Decide whether to actually wire EULER_V2 capture given real subgraph infra now exists (verified
      working 2026-06-02, never actually polled) — this is a "finish what's already 90% built" case, same class as
      the RENZO finding in the tracker's unregistered-handler-audit item.
- [ ] [VERIFY] P3. Resolve which "Plasma" chain UAC's `FLUID-PLASMA`/`AAVE-PLASMA` placeholders are meant to refer
      to (the 2025 Tether-backed Plasma L1, or the unrelated pre-2020 Polygon Plasma bridge) before doing anything
      else with those two entries — UAC's own maintainers have this flagged unresolved.

## Progress Log

- **2026-07-07** — Filed after a 3-way parallel check (write-path trace, UAC registry check, live GCS manifest
  read) chasing an operator hypothesis about naming mismatches. The hypothesis wasn't quite right — no naming
  mismatch exists — but the underlying instinct ("the dashboard's 0/0 might not be honest") was correct for 3 of
  the 6 venues checked. No files edited; the GCS read was read-only (download + pandas, no writes).
