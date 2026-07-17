---
doc_type: issue
title: CeFi residual follow-ups after honest-done close-out (non-Tardis, operator-deferred)
summary:
  The CeFi completion program was CLOSED at honest-done on 2026-07-17 (operator accepted current coverage 50.79% against
  a COMPLETE denominator; the 2.89M-cell tick gap is honestly-labelled expected_unattempted, not closable at the N=1
  Tardis throughput ceiling). This doc migrates the genuine NON-Tardis residuals that outlive that plan so they stay
  visible — none block the accepted deliverable; each is a discrete, independently-pickup-able follow-up. The Tardis-cap
  backfill work (WS A/B/F/G-tick + af=0 census + ConnectionTimeout diagnosis) is NOT here — it was superseded by the
  operator accept-decision, not deferred.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [cefi, honest-coverage, residual, hyperliquid, phantom, eu-twin, consolidator, follow-up]
related:
  [
    cefi_completion_program_2026_07_15.md,
    cefi_hl_aster_batch_data_gaps_2026_06_22.md,
    cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md,
    phantom_captures_cefi_2026_06_28.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: data
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: CeFi completion program /autonomous close-out (slot-3, 2026-07-17) — archival ritual step 1 (migrate DEFERRED)
resolved_by:
---

# CeFi residual follow-ups after honest-done close-out

> **Context**: `plans/archive/2026_07/cefi_completion_program_2026_07_15.md` closed at honest-done on 2026-07-17 —
> operator chose **accept current coverage** (50.79%, denominator COMPLETE, the 2,892,108-cell gap honestly-labelled
> `expected_unattempted`). The full 2026-02..07 tick backfill is not closable at the N=1 Tardis throughput ceiling (~186
> cells/hr ≈ 1.8 years; N=3 = ~94% 403s; US region ruled out on egress). Everything achievable inside that ceiling
> shipped. The items below are the genuine **NON-Tardis** residuals — none block the accepted deliverable; each is a
> discrete, independently-pickup-able follow-up. Filed as archival-ritual step 1 (migrate DEFERRED) so they survive the
> plan archive.

## Residuals (all NON-Tardis — not subject to the accepted ceiling)

1. **[P2] HYPERLIQUID recent-tail fill (~2026-06-24 → now-2).** HL is a DEX venue (non-Tardis, exempt from the N=1 cap)
   so its tail IS fillable — it was simply not run before the close-out. Fill via the HL batch lane (not the Tardis
   fleet). Detail: `cefi_hl_aster_batch_data_gaps_2026_06_22.md`. Evidence on pickup: manifest rows for HL over the tail
   range.

2. **[P2] HYPERLIQUID phantom re-census (1,277 rows → `@LIN` canonical path).** Cosmetic manifest-labelling — does NOT
   affect captured data. Blocked only on box size: the re-census (`reconcile_phantom_manifest_rows_all.py`) OOMs on the
   15GB VM; needs a 32-64GB box. Detail: `phantom_captures_cefi_2026_06_28.md`. Evidence: phantom count → 0 for HL.

3. **[P1] Drop eu twins of natively-canonical (non-Tardis) captures — ~10,368 rows.** The OnchainPerp/native-canonical
   lane writes canonical `captured` rows but nothing drops the matching `expected_unattempted` twin, so the relabel gate
   is RED on these and its reconcile structurally cannot fix them (it only reconciles its own relabels). This is a
   pre-existing defect, independent of the Tardis ceiling. Detail + namespace root cause:
   `cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md`. Fix: a targeted eu-twin drop keyed on
   `(venue, data_type, day)` where a canonical `captured` twin exists.

4. **[P3] Manifest consolidator lost-update redeploy — watch item, likely unnecessary.** The maintenance-window
   durability fix (purging `_legacy_seed.parquet` so aliases can't re-merge) held across the resumed consolidator +
   backfill for ~70 min, verified 3×. The CAS lost-update race is documented in
   `manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md`; redeploy only if a future purge fails to stick.

## Not here (superseded, not deferred)

The Tardis-cap backfill work — WS **A** (recent-tail main-venue backfill), **B** (403 re-capture + af=0 census), **F**
(DERIBIT-COMBO historical `by_date`), **G-tick** (equity-perp tick download), the **final `af=0`/`eu=0` recompute**, and
the **ConnectionTimeout-storm diagnosis** — is **superseded by the operator accept-decision (2026-07-17)**, not
deferred. It is only pursuable if the operator later revisits the Tardis licence/scope decision. Do not re-file it as
open work.
