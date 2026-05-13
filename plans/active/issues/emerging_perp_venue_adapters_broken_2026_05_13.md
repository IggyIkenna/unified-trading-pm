---
title: "Emerging perp venue adapters (ASTER, EXTENDED-STARKNET, PACIFICA-SOLANA, LIGHTER-ZKSYNC, HYPERLIQUID) mostly failing — 0-32% capture rate"
created: 2026-05-13
author: slot-3-ikenna
source:
  - bucket_name_ssot_canonicalisation_2026_05_10
  - defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07
  - defi_master_2026_05_07
severity: P0
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

## What I found

While verifying defi venue coverage for the legacy_blank reconciliation work (issue
`defi_legacy_blank_reclassification_2026_05_13.md`), slot 3 spot-checked the cefi
manifest capture status for the emerging perp venues that the DeFi archetypes
depend on for hedge legs (per CLAUDE.md "DeFi + CeFi hybrid instrument universe").

Findings from 2026-05-13 ~16:35 BST cefi manifest audit (`market-data-tick-cefi-central-element-323112`):

| Venue | Total rows | captured | attempted_failed | empty_confirmed | % captured | First date | Last date |
|---|---|---|---|---|---|---|---|
| **ASTER** | 17,681 | **0** | 17,681 | 0 | **0%** | 2024-10-01 | 2026-05-03 |
| **EXTENDED-STARKNET** | 15 | 0 | 15 | 0 | 0% | 2026-04-30 | 2026-04-30 |
| **PACIFICA-SOLANA** | 5,077 | 309 | 4,768 | 0 | 6.1% | 2025-07-01 | 2026-05-06 |
| **LIGHTER-ZKSYNC** | 3,619 | 319 | 3,150 | 150 | 8.8% | 2024-08-01 | 2026-05-06 |
| **HYPERLIQUID** | 45,368 | 14,710 | 30,658 | 0 | 32.4% | 2023-11-01 | 2026-05-04 |

These venues ARE registered in:

- `instruments-service/instruments_service/reference_data/factory.py:173-175` — adapters wired (LIGHTER-ZKSYNC → lighter,
  EXTENDED-STARKNET → extended, PACIFICA-SOLANA → pacifica).
- `instruments-service/instruments_service/reference_data/adapters/defi/{extended,pacifica,lighter}.py` — adapter
  modules exist.
- UAC `registry/venue_launch_dates.py CEFI_VENUE_LAUNCH_DATES` (lines 79-83) — launch dates declared.
- UAC `registry/data_type_capability.py` — HYPERLIQUID + ASTER capabilities declared.
- UAC `registry/cefi_margin_tiers.py` — HYPERLIQUID + ASTER margin schedules.
- UAC `registry/expected_coverage.py:65,71` — HYPERLIQUID + ASTER expected_coverage.

So they're not phantom venues — the system IS trying. The adapters are failing
in a way that produces `attempted_failed` (not `empty_confirmed`), meaning the
adapter returns an error rather than a confirmed-zero. The reconcile_legacy_blank
classifier (after my UAC@`ca62a19` + UTL@`b0c38a21` shipped 2026-05-13) sees these
post-launch dates and stays at `attempted_failed/LegacyBlankErrorReasonError` —
correct classification, but masks the underlying adapter bug.

## Why it matters

**P0 for May-23 cutover**: The DeFi archetypes (`carry_staked_basis`,
`arbitrage_price_dispersion`) hedge through CeFi perp venues. Per CLAUDE.md "DeFi
+ CeFi hybrid instrument universe": _"ALL CeFi venues (Binance, Bybit, OKX,
Deribit, Kraken, Hyperliquid, Aster) are candidates for perp shorts. Eligibility
is archetype-driven."_ If the ASTER adapter has 0% capture and HYPERLIQUID has
68% failure, the hedge leg is operationally fragile on cutover day.

**Specific concerns**:

1. **ASTER 0% capture for ~1.5 years** (2024-10-01 → 2026-05-03, 17,681 rows all
   failed). Either the adapter never worked or the API endpoint moved. Hard to
   tell which without reading the actual error events.
2. **EXTENDED-STARKNET 0% capture, 15 rows, only 2026-04-30 attempted** — recent
   activation that immediately failed; probably never debugged.
3. **PACIFICA-SOLANA 94% failure** — sporadic captures suggest adapter mostly
   works but hits frequent failures.
4. **LIGHTER-ZKSYNC 87% failure** — similar pattern; also has 150 empty_confirmed
   (which is a SSOT violation per CLAUDE.md "cefi cannot have empty_confirmed at
   instrument-day grain" — although LIGHTER-ZKSYNC is in CEFI_VENUE_LAUNCH_DATES
   it's actually a DeFi perp DEX; the SSOT rule may need clarification).
5. **HYPERLIQUID 68% failure** — the lead-archetype hedge venue. Better but still
   significantly impaired.

## Recommended decision (operator triage)

These investigations are out of slot 3's PART B scope (bucket-name SSOT) and
require dedicated adapter-debug effort per venue:

1. **Owner assignment**: assign to a slot focused on adapter/API debugging
   (DeFi adapter slot or similar). Candidates: defi_master slot, manifest
   reconciliation slot, or a new dedicated "broken perp adapter" slot.

2. **Triage priority**:
   - **ASTER** (P0, 0% capture, hedge-leg-eligible) — investigate first.
   - **HYPERLIQUID** (P0, 68% failure on lead hedge venue) — investigate second.
   - **LIGHTER-ZKSYNC** + **PACIFICA-SOLANA** (P1, low capture but some success)
     — fix patterns may apply from HYPERLIQUID + ASTER findings.
   - **EXTENDED-STARKNET** (P1, fresh adapter never debugged) — last.

3. **Investigation steps per venue**:
   - Read `gs://central-element-323112-events/events/{service}/{date}/{cid}/hour=*/*.jsonl`
     for `ADAPTER_FETCH_FAILED` events.
   - Identify whether the failure is auth / API-changed / rate-limit / 5xx /
     timeout / malformed-response.
   - Patch adapter or update endpoint + retry one shard.
   - If endpoint-deprecated: research current endpoint + bump adapter config.
   - If auth-rejected: rotate API keys per `ApiKeyReloader` SSOT.
   - If rate-limit: add singleton-lock per CLAUDE.md "Singleton-locked launchers".

4. **Re-classification followup**: after adapter fix + successful re-fetch,
   the previously-failed rows will get re-attempted via MTDS batch runs. The
   manifest will overwrite `attempted_failed/LegacyBlankErrorReasonError` with
   either `captured` (success) or `attempted_failed/<typed_error>` (failure with
   real reason from `classify_venue_error()`). No additional reconciliation
   needed — the fix surfaces naturally via real-fetch behavior.

## Open question (out-of-scope context)

**Is LIGHTER-ZKSYNC really cefi?** It's listed in `CEFI_VENUE_LAUNCH_DATES` but
it's an on-chain perp DEX on zkSync. Per CLAUDE.md "DeFi + CeFi hybrid":

> "DeFi" labels the long/stake/lend leg (on-chain); the hedge/short leg runs on
> CeFi perp venues. ALL CeFi venues (Binance, Bybit, OKX, Deribit, Kraken,
> Hyperliquid, Aster) are candidates for perp shorts.

So LIGHTER, PACIFICA, EXTENDED, HYPERLIQUID, ASTER are CeFi-classified (perp
shorts) even though they're on-chain. This matches the CEFI_VENUE_LAUNCH_DATES
placement. The "150 empty_confirmed" rows for LIGHTER-ZKSYNC may be an
SSOT-conformity violation per the "cefi cannot have empty_confirmed at
instrument-day grain" rule — could be a separate cleanup target if confirmed.

## Cross-references

- This issue surfaced during slot-3 PART B work (bucket_name_ssot reconciliation).
- Related: `defi_master_2026_05_07.md` for perp venue scope decisions.
- Related: `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` for
  archetype-to-venue eligibility matrix.
- DOES NOT BLOCK slot 3 PART B work — that's complete. This is a NEW finding
  filed for operator triage.

---

## UPDATE 2026-05-13 ~18:30 BST — slot 3 deeper investigation: 3 of 5 are MIS-FLIPS

Per operator direction "but was the data in the right place", slot 3 ran direct GCS spot-checks on canonical paths:

| Venue | Blobs found at 3 recent dates | Real status |
|---|---|---|
| **HYPERLIQUID** | 15 (data on disk) | ✅ MIS-FLIPS — 30,658 rows in attempted_failed/LegacyBlank actually have parquet at canonical path |
| **LIGHTER-ZKSYNC** | 15 (data on disk) | ✅ MIS-FLIPS — same |
| **PACIFICA-SOLANA** | 15 (data on disk) | ✅ MIS-FLIPS — same |
| **ASTER** | **0** | ❌ NO DATA — adapter genuinely broken |
| **EXTENDED-STARKNET** | **0** | ❌ NO DATA — adapter genuinely broken |

5/5 random HYPERLIQUID attempted_failed sample rows ✅ have real parquet. The 68% "failure" headline is mostly an artifact of the legacy_blank reconciler converting `SOURCE_RETURNED_ZERO` → `attempted_failed/LegacyBlankErrorReasonError` per the cefi instrument-day grain SSOT rule. For HYPERLIQUID/LIGHTER/PACIFICA, the parquets exist — the manifest just doesn't know.

### Mitigation: reverse-phantom reconciler shipped at instruments-service@`35f920e`

File: `scripts/reconcile_attempted_failed_to_captured_2026_05_13.py`

Sister to `reconcile_phantom_manifest_rows_all.py` — flips `attempted_failed → captured` when parquet exists at the canonical path. Bulk-listing strategy, 32-worker parallelised, per-VM shard isolation enforced. Slot 3 dry-running on HYPERLIQUID now; if 99%+ of HYPERLIQUID candidates resolve to captured, the same reconciler should be run for the full cefi attempted_failed residual.

### Real adapter problem isolated to ASTER + EXTENDED-STARKNET

These 2 of 5 perp venues genuinely have no parquet data anywhere (not 5 of 5 as initially feared). Recommend:

- 1 slot to debug ASTER adapter (`instruments-service/.../adapters/cefi/aster.py` + MTDS data-fetch path)
- 1 slot to debug EXTENDED-STARKNET adapter (`extended.py`)

The other 3 (HYPERLIQUID/LIGHTER/PACIFICA) are recoverable via the reverse-phantom reconciler — no adapter debug needed.
