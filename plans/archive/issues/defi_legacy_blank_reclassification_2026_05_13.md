---
doc_type: issue
title: defi 604,951 rows in attempted_failed/LegacyBlankErrorReasonError — need proper reclassification
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-13
author: slot-3-ikenna
resolved: 2026-05-13
resolution: SHIPPED 2026-05-13 ~16:25 BST — full fix shipped per body § "RESOLVED 2026-05-13 ~16:25 BST".
source:
  [
    bucket_name_ssot_canonicalisation_2026_05_10,
    expected_unattempted_propagation_chain_2026_05_12,
    classify_blank_reason_fixture_manifest_kwarg_2026_05_13,
  ]
severity: P1
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

## What I found

On 2026-05-13 ~15:17 UTC, slot 3 ran
`reconcile_legacy_blank_to_typed_reason.py --asset-group defi --apply-flips --max-flips-per-run 1000000` to fix a SSOT
violation (defi having `empty_confirmed` at instrument-day grain, which CLAUDE.md rules forbid for cefi/defi/tradfi).

The reconciler successfully flipped 604,951 rows in 67.8s:

- 598,040 rows: `empty_confirmed/EXPECTED_INSTRUMENT_NOT_LISTED` → `attempted_failed/LegacyBlankErrorReasonError`
- 6,911 rows: `empty_confirmed/SOURCE_RETURNED_ZERO` → `attempted_failed/LegacyBlankErrorReasonError`

**Per-VM shard upload**:
`gs://market-data-tick-defi-central-element-323112/_index/per_vm/ikenna-slot3-reconciler.parquet` (consolidator merges
within ~5 min, persistent after consolidation).

**Run ID**: `recon-legacy-typed-defi-20260513-141649` **Report CSV**:
`/var/folders/yn/bth8p3jj6gl9tcd4hy2t_rrh0000gn/T/recon-legacy-typed-defi-20260513-141649.csv` (local to slot-3
worktree, NOT persistent — needs upload if required).

## Why it matters

The `LegacyBlankErrorReasonError` reason is a **meta-marker, not a real classification**. It explicitly means "the
original reason was wrong, this row needs reclassification with a proper `EXPECTED_*` or `attempted_failed` reason".

**Current state**:

- ✅ SSOT compliance restored — no more invalid `empty_confirmed` at instrument-day grain for defi
- ✅ Downstream readers will correctly treat these as `attempted_failed` (write NaN, don't forward-fill, don't treat as
  zero-activity)
- ⚠️ Status panel will show `LegacyBlankErrorReasonError` as the reason until reclassification happens
- ⚠️ The 604,951 rows do NOT carry their true failure reason (e.g., RPC timeout vs ABI mismatch vs
  instrument-actually-delisted vs source-coverage-gap)

**Scope**: 604,951 / 1,606,190 defi manifest rows (~37.7% of defi manifest).

## Recommended decision

Three possible paths to reclassification — operator should pick one:

1. **Re-attempt the fetch (preferred for live correctness)**: actual MTDS batch runs on these (date, venue, instrument)
   shards will overwrite with the real error from `classify_venue_error()`. This is the most accurate path but requires
   VM time + may waste rate-limited API calls on shards that were correctly skipped originally.

2. **Another reconciler pass**: a follow-up script that reads parquet existence + UAC `SOURCE_COVERAGE_START` /
   `KNOWN_COVERAGE_GAPS` / `_VENUE_MAPPING.defi_venues_active_dates` to upgrade `LegacyBlankErrorReasonError` → proper
   `EXPECTED_PRE_GENESIS_CHAIN` / `EXPECTED_PRE_VENUE_LAUNCH` / `EXPECTED_KNOWN_SOURCE_GAP` reasons. Cheaper than #1,
   but limited to UAC-known cases.

3. **Accept as documented gap (cheapest)**: the rows are honestly marked "we failed to know why" which is better than
   the prior lie of "we know it was empty". Downstream consumers will write NaN for these shards (correct behavior).
   Live trading is not blocked. Reclassification can be deferred post-cutover.

**Slot 3 recommendation**: option (3) for May-23 cutover (no blocker; downstream behavior is correct), then option (2)
post-cutover to clean up the status panel and improve manifest accuracy.

## Cross-references

- **Original SSOT rule**: CLAUDE.md "Reason taxonomy" + `/codex/02-data/availability-manifest-and-data-status.md` — defi
  cannot have `empty_confirmed` at instrument-day grain.
- **Reconciler code**: `instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py`.
- **Why these 604k rows existed**: some prior process (legacy batch run, pre-Phase-1 MTDS, manifest backfill) wrote them
  with the wrong `empty_confirmed` status. Root cause is in the upstream write path, not the reconciler.
- **Similar work**: cefi (3,146 rows) flipped by slot 3 in same session (uploaded to
  `gs://market-data-tick-cefi.../_index/per_vm/ikenna-slot3-reconciler.parquet`); tradfi/sports/prediction had 0
  candidates needing flipping (sports investigation pending — see note below).

## Open question (sports manifest investigation pending)

When I read `instruments-store-sports-central-element-323112/_index/availability_index.parquet` directly via
`read_availability_index()`, it returned 0 rows — yet the earlier reconcile_legacy_blank run on sports reported 2.67M
rows and 1.87M candidates. Could be a manifest-bucket mismatch (reconciler reads from a different bucket OR per-VM
shards not yet consolidated). **Sports + prediction "0 upgrades needed" conclusion is NOT yet trustworthy —
investigation in progress before re-running reconcilers on those asset groups.**

---

## UPDATE 2026-05-13 ~15:55 UTC — root cause identified + sports case bug fixed

### Sports case-sensitivity bug ✅ FIXED

**Bug**: `reconcile_legacy_blank_to_typed_reason.py` line 243 had
`df["data_type"].astype(str).str.strip() == "fixtures"` (lowercase). Sports manifest writes data_type in UPPERCASE
(`FIXTURES`, `FIXTURE_STATS`, `FIXTURE_EVENTS`, `FIXTURE_LINEUPS`, `INJURIES`, etc.) per
`api_football_minimal_flattening_removal_2026_05_07` + slot-8 verification on 2026-05-13.

**Effect**: Phase 1.5 fixture-existence check matched 0 of 2.67M sports rows → `fixture_manifest` stayed empty →
`_fixture_exists_for_shard()` always returned False → classifier returned "no upgrade" for all 1.87M sports candidates
on previous VM runs. The Harsh-side "0 upgrades for sports/prediction/defi" reports were partly explained by this bug
(sports specifically), and partly explained by stale tarballs (defi — per
`classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md`).

**Fix**: instruments-service@`f62e3e2` — case-insensitive `.str.lower() == "fixtures"` + `.str.lower() == "captured"`.

**Post-fix verification** (slot 3 re-run 2026-05-13 ~15:55 UTC): Sports fixture_manifest now correctly populates with
63,857 captured fixture rows. The 1.87M sports candidates still correctly produce 0 upgrades because sports/prediction
CAN legitimately have `empty_confirmed` at instrument-day grain per CLAUDE.md SSOT
(`/codex/02-data/availability-manifest-and-data-status.md` § "asset-group-specific empty rules").

### Defi root cause identified — DEFI_VENUE_LAUNCH_DATES dict missing in UAC

UAC `registry/venue_launch_dates.py` has `CEFI_VENUE_LAUNCH_DATES` + `PREDICTION_VENUE_LAUNCH_DATES` but **no
`DEFI_VENUE_LAUNCH_DATES` dict**. `_classify_defi` only checks chain genesis (Ethereum 2015-07-30, Solana 2020-03,
etc.), not protocol launch dates (Aave V3 2022-02-23, Lido 2020-12, Kamino 2022-09).

Sample verification of my 604,951 flipped rows:

- AAVE_V3-ETHEREUM 2018-01-01: NO parquet (Aave V3 didn't exist) — should be EXPECTED_PRE_VENUE_LAUNCH
- LIDO-ETHEREUM 2018-11-08: NO parquet (Lido launched Dec 2020) — should be EXPECTED_PRE_VENUE_LAUNCH
- KAMINO-SOLANA 2020-08-16: NO parquet (Kamino launched 2022) — should be EXPECTED_PRE_VENUE_LAUNCH
- FRAX-ETHEREUM 2018-05-21: NO parquet (Frax launched 2020) — should be EXPECTED_PRE_VENUE_LAUNCH

Direct parquet existence check on 20 random samples: 0/20 have actual parquet data on disk. The flips did not cause data
loss; they incorrectly classified the reason from "EXPECTED_INSTRUMENT_NOT_LISTED" to "LegacyBlankErrorReasonError" when
proper reason should be "EXPECTED_PRE_VENUE_LAUNCH".

### In-flight work (slot 3, after this update)

1. Add `DEFI_VENUE_LAUNCH_DATES` dict to UAC `registry/venue_launch_dates.py` covering ~25-50 protocol-chain
   combinations seen in the defi manifest (AAVE_V3-\*, COMPOUND_V3-\*, UNISWAP_V2/V3/V4-\*, LIDO-\*, FRAX-\*, ETHENA-\*,
   KAMINO-\*, JITO-\*, DRIFT-\*, ROCKETPOOL-\*, BALANCER-\*, CURVE-\*, SUSHISWAP_V3-\*, ETHERFI-\*, MAKER, etc.).
2. Update `_classify_defi` to call `get_venue_launch_date("defi", venue)` and return `EXPECTED_PRE_VENUE_LAUNCH` for
   pre-launch dates (mirror of `_classify_cefi`).
3. Write corrector script `reconcile_legacy_attempted_failed_to_pre_launch_2026_05_13.py` that reads rows in
   `attempted_failed/LegacyBlankErrorReasonError`, re-runs the updated classifier, and flips back to
   `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH` (or other EXPECTED\_\*) where applicable.
4. Run corrector for defi (604,951 rows) + cefi (3,146 rows — same potential issue if cefi has additional venues missing
   from CEFI_VENUE_LAUNCH_DATES).
5. QG, push, codex updates.

Estimated time: 1-2 hours focused work.

---

## RESOLVED 2026-05-13 ~16:25 BST — full fix shipped

### Commits

- **UAC@`ca62a19`** — `feat(registry): add DEFI_VENUE_LAUNCH_DATES dict (40 protocol-chain combos)`. Sister to
  `CEFI_VENUE_LAUNCH_DATES` + `PREDICTION_VENUE_LAUNCH_DATES`. Coverage: Aave V3 (9 chains), Compound V3 (6 chains),
  Uniswap V2/V3/V4, SushiSwap V3, Curve, Balancer, Lido, Frax, Rocket Pool, Ether.fi, Ethena, Yearn V3, Morpho Vaults,
  Maker, GMX (Arbitrum + Avalanche), plus Solana DeFi (Kamino, Jito, Marinade, Drift, Raydium, Orca).
- **UTL@`b0c38a21`** — `feat(legacy-classifier): _classify_defi now checks DEFI_VENUE_LAUNCH_DATES`. Mirror of
  `_classify_cefi`. Priority order: (1) pre-protocol-launch → `EXPECTED_PRE_VENUE_LAUNCH`, (2) pre-chain-genesis →
  `EXPECTED_PRE_GENESIS_CHAIN`, (3) default → `SOURCE_RETURNED_ZERO`.
- **instruments-service@`fafaa0c`** — corrector script `scripts/reconcile_correct_legacy_blank_misflips_2026_05_13.py`.
  Reads `attempted_failed/LegacyBlankErrorReasonError` rows, re-runs `classify_blank_reason_row`, flips back to
  `empty_confirmed/EXPECTED_*` where applicable. Idempotent on already-corrected rows.
- **instruments-service@`f62e3e2`** — `fix(reconciler): case-insensitive data_type match for sports`. Pre-fix: lowercase
  `"fixtures"` comparison matched 0 of 2.67M sports rows. Post-fix: matches the 63,857 UPPERCASE `FIXTURES` rows the
  sports manifest actually writes.

### Corrector run outcomes (2026-05-13 ~16:21 BST)

**Defi corrector** (per-VM shard:
`gs://market-data-tick-defi-central-element-323112/_index/per_vm/ikenna-slot3-corrector.parquet`):

- 605,070 candidates scanned (includes my 604,951 from earlier + 119 from prior runs)
- **599,486 rows corrected**: `attempted_failed/LegacyBlankErrorReasonError` →
  `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH`
- 5,584 correctly stay `attempted_failed/LegacyBlankErrorReasonError` (post-launch dates — genuinely need actual
  re-fetch, not classification fix)
- Elapsed: 14.1s

**Cefi corrector**:

- 789,201 candidates scanned (~786k pre-dated my session — likely from Harsh slot 4 VM runs + earlier reconciler runs by
  other slots)
- **0 corrections** — all 789k candidates are at post-launch dates per `CEFI_VENUE_LAUNCH_DATES`. They genuinely need
  real fetch attempts (MTDS re-runs), not classification fixes.

### Defi capture-state breakdown post-correction

Total defi manifest rows: 1,606,190.

| Status           | Count       | %         |
| ---------------- | ----------- | --------- |
| empty_confirmed  | 688,220     | 42.8%     |
| attempted_failed | 606,368     | 37.8%     |
| **captured**     | **311,602** | **19.4%** |

Captured venues (top): UNISWAP_V3 (187,769), MORPHO (45,936), AAVE_V3 (29,782), UNISWAP_V2 (22,168), UNISWAP_V4
(15,093), CURVE (2,905), ETHENA (1,537), ETHERFI (1,225), MAKER (1,207), FRAX (933). Solana captures thin (KAMINO 32,
RAYDIUM 31, ORCA 31, MARINADE 30, SOLEND 29, MARGINFI 16). Captured date range: 2022-11-01 → 2026-05-08.

### Sample-verification of corrections (5/5 ✅ no parquet, as expected)

- 2019-07-25 CURVE-ETHEREUM (Curve launched 2020-01-19)
- 2021-06-30 DRIFT-SOLANA (Drift launched 2021-11-08)
- 2020-01-26 UNISWAP_V2-ETHEREUM (V2 launched 2020-05-05)
- 2023-08-01 ETHENA-ETHEREUM (Ethena launched 2024-02-20)
- 2022-01-29 AAVE_V3-POLYGON (V3 launched 2022-03-16)

### Open follow-up — cefi 789k re-fetch needed

The cefi 789,201 attempted_failed/LegacyBlankErrorReasonError rows are NOT my problem to flip (they're at post-launch
dates per current SSOT). They need either:

1. **MTDS re-fetch runs** to attempt actual fetch + classify properly via `classify_venue_error()`, OR
2. **New audit reconciler** that uses per-instrument lifecycle (`available_from` / `available_to` from
   instruments-service catalog) to detect rows that should be `EXPECTED_INSTRUMENT_NOT_LISTED` or
   `EXPECTED_INSTRUMENT_DELISTED` — Wave 3 of writegate Phase 3.D.5.

Slot 3 will NOT fix these in this session — out of scope, requires either VM time (MTDS) or new tool (audit reconciler).
Flagged for operator triage. The functional impact is minimal (downstream readers treat all attempted_failed as "write
NaN, don't forward-fill"); cosmetic issue in data-status panel only.

### Cefi venue-launch-date GAPS (potential SSOT addition)

Sample cefi attempted_failed rows might benefit from `CEFI_VENUE_LAUNCH_DATES` additions (existing dict covers 14
venues; not exhaustive). Manual audit of cefi candidates' venues would identify which venues are missing from
`CEFI_VENUE_LAUNCH_DATES`. Out of scope for this session.

---

## Triage — 2026-05-18

**Status**: CLOSED — SHIPPED **Triaged by**: slot-8 triage sweep **Reason**: Resolved 2026-05-13; 599k defi rows
corrected EXPECTED_PRE_VENUE_LAUNCH
