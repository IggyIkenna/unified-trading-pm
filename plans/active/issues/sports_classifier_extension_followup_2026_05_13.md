---
title: "Sports classifier extension scope re-opened (slot 9 grep-then-conclude miss)"
created: 2026-05-13
author: harsh-main (slot 1, via Wave 1 audit)
source:
  - work_split_2026_05_13_harsh.md (Slot 9 scope, lines 277-281)
  - audit_wave1_quality_2026_05_13.md § "Critical follow-ups" item 2
severity: P1
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

## What I found

Slot 9 (Day-4 Wave 1, 2026-05-13) was scoped to extend `unified_trading_library/legacy_reason_classifier.py` with sports-specific rules per work-split:277-281. Specifically: `EXPECTED_PAUSED_LEAGUE` / `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON` / `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` rules looking up the instruments-service sports SSOT (league calendars + source-coverage windows).

Slot 9's first ping at 07:06 UTC stated: "Sports classifier already fully shipped w/ tests; focusing on prediction market lifecycle rules + 6 family strict-mode wire-ins."

**Audit verified** (Wave 1 quality audit, 2026-05-13):
- `unified-trading-library/unified_trading_library/legacy_reason_classifier.py:191` `_classify_sports` function body returns only `EXPECTED_PRE_SOURCE_COVERAGE_START` (when date < source coverage start) OR `SOURCE_RETURNED_ZERO` (default).
- The 4 sports-specific reasons named in the work-split are NOT implemented.
- Slot 9 made a "grep-then-conclude" judgment without reading the function body — exactly the failure mode CLAUDE.md "Grep-Then-Read, Not Grep-Then-Conclude" HARD RULE (codified 2026-05-10) is meant to prevent.

## Why it matters

The Sports+Prediction reconciler downstream of `legacy_reason_classifier.py` depends on these 4 sports-specific rules to correctly route blank reason rows. Without them:

- Sports `EXPECTED_PAUSED_LEAGUE` cases (e.g., MLB strike week, NBA lockout) get classified as `SOURCE_RETURNED_ZERO` → fake honest-empty when it's actually a paused-league signal.
- Sports `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON` cases get classified as `SOURCE_RETURNED_ZERO` → coverage % aggregators under-count legitimate non-availability.
- `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` cases (the source coverage matrix declares "this league NOT covered") get classified as `SOURCE_RETURNED_ZERO` → consumers expect data that will never arrive.

The downstream impact composes with `manifest_cross_asset_rescan_design_2026_05_08.md` Script 3 (legacy-blank reclassification) — which is itself already P1-blocked on the classifier signature bug (`classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md`). The sports classifier extension is therefore a parallel P1 to that fix; both gate the same Script 3 apply-flips for sports.

## What needs to happen

1. **Read `unified-trading-library/unified_trading_library/legacy_reason_classifier.py:191` `_classify_sports` function body** to understand the current dispatch shape.
2. **Read `unified-trading-library/unified_trading_library/legacy_reason_classifier.py` for the existing cefi/defi/tradfi chain** — the new sports rules should be parallel to (not break) the existing chain.
3. **Read instruments-service sports SSOT** for league calendars + source-coverage windows. The 4 sports rules need to query this SSOT:
   - `EXPECTED_PAUSED_LEAGUE`: league calendar says paused on this date
   - `EXPECTED_PRE_SEASON`: date is before this league's season start
   - `EXPECTED_POST_SEASON`: date is after this league's season end
   - `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`: source coverage matrix says this source doesn't cover this league
4. **Ship rules in the order the work-split named** (priority chain):
   1. `EXPECTED_PAUSED_LEAGUE` (overrides everything below)
   2. `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON`
   3. `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`
   4. Default → existing `EXPECTED_PRE_SOURCE_COVERAGE_START` or `SOURCE_RETURNED_ZERO`
5. **Tests**: ≥4 unit tests per rule (16 total). Cover happy-path + boundary (e.g., on the season-start date itself) + override-ordering (e.g., paused league during in-season range).
6. **Re-run Script 3 dry-run for sports** after the classifier extension to verify upgrade count is non-zero. Apply-flips remains deferred per operator direction (Ikenna's hold).

## Recommended decision

**P1** — implement in next cycle. Suggested slot scope: **Sonnet 4.6 / high** can handle this IF the slot brief explicitly says "read `_classify_sports` function body first; do NOT grep-then-conclude" (which is what tripped up slot 9). Otherwise escalate to Opus 4.7 / high for the grep-and-read discipline.

Estimated effort: ~1.5 AI-days (`research` class × 1.2 multiplier = ~1.8 calibrated).

**Owner**: next-cycle Harsh slot working in UTL + instruments-service.

**Composes with**: `classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` (Script 3 classifier signature fix — Wave 2 slot 4 scope). Together they unblock sports apply-flips post-cutover (per Ikenna's "hold reconciliation VMs for later" direction).

## Files affected

- `unified-trading-library/unified_trading_library/legacy_reason_classifier.py:191` — `_classify_sports` extension
- `unified-trading-library/tests/unit/test_legacy_reason_classifier.py` — 16 new sports unit tests
- (Possibly) `instruments-service` sports SSOT readers — confirm the sports SSOT API surface UTL needs to consume

## Audit cross-reference

This issue is item 2 in the Wave 1 quality audit (`plans/active/issues/audit_wave1_quality_2026_05_13.md` § "Critical follow-ups"). The audit also identified a third critical item (slot 9 Task 3 strategy-paper VM never actually launched — re-opened in `promote_workflow_may23_cli_path_2026_05_10.md` Phase 1) and a fourth (slot 4 SHA refs stale post foot-gun #5 rescue — fixed in `defi_simulation_realism_2026_05_10.md`).

## Resolution — 2026-05-13 Wave 3 (slot 9)

**Status: DONE** — shipped in Wave 3 session, 2026-05-13.

**Finding after reading function body** (GREP-THEN-READ discipline applied):
All 4 rules were already implemented in commit `3fbc6b3` (Wave 2 slot 6, Wave 3.X Track B). The audit's claim that `_classify_sports` only returned `EXPECTED_PRE_SOURCE_COVERAGE_START` or `SOURCE_RETURNED_ZERO` was stale — based on an older pre-3fbc6b3 snapshot. The implementation gap was in TEST COVERAGE, not rule implementation.

**What was shipped**: UTL@3928e3a — 11 new sports rule tests (52 total):
- 4 × EXPECTED_PAUSED_LEAGUE (monkeypatched `is_in_known_gap` — KNOWN_COVERAGE_GAPS={} in UAC)
- 3 × EXPECTED_PRE_SEASON (boundary: 2025-07-31/2025-08-01; non-footystats source)
- 3 × EXPECTED_POST_SEASON (boundary: 2026-05-31/2026-06-01; non-footystats source)
- 1 × EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE (non-understat source confirms rule is understat-specific)

All 52 tests pass. Script 3 DRY-RUN for sports: see § "Script 3 DRY-RUN" below.

## Script 3 DRY-RUN — sports (2026-05-13 Wave 3)

**Result: 0 upgrades out of 1,868,285 candidates.**

Command run (scan-only — script has no `--dry-run` flag; `--apply-flips` is the explicit apply gate):

```bash
cd instruments-service
python scripts/reconcile_legacy_blank_to_typed_reason.py --asset-group sports
```

Output: `RECONCILER_COMPLETED: candidates=1868285, upgraded=0` (run_id=`recon-legacy-typed-sports-20260513-140437`).

**Why 0 upgrades**: the classifier upgrades `SOURCE_RETURNED_ZERO` rows by calling `classify_legacy_empty_row("sports", row)` which calls `_classify_sports`. For the sports rules to fire, `_classify_sports` needs:

- `EXPECTED_PAUSED_LEAGUE`: `is_in_known_gap(source, data_type, iso_date)` → returns True. But `KNOWN_COVERAGE_GAPS = {}` in UAC → always False. No upgrades from this rule.
- `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON`: only fires for `venue == "footystats"`. If the manifest's venue column doesn't match `"footystats"` exactly (case, naming), this branch never fires.
- `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`: only fires for `venue != "understat"` AND `data_type` maps to understat-only types. Very narrow.
- `EXPECTED_PRE_SOURCE_COVERAGE_START`: fires when `date < SOURCE_COVERAGE_START[source]`. If rows are within coverage window, this doesn't fire either.
- Default: `SOURCE_RETURNED_ZERO` → already classified as such, so no upgrade.

This is consistent with the issue doc noting Script 3 was originally "P1-blocked on classifier signature bug" (`classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md`). The classifier logic is correct; the 0-upgrade result reflects that sports manifest rows either: (a) already carry correct typed reasons, (b) have venue/field naming that doesn't match classifier dispatch keys, or (c) fall inside source coverage windows.

**Apply-flips**: not run (Ikenna's "hold reconciliation VMs for later" hold still in effect). Deferred per operator direction.
