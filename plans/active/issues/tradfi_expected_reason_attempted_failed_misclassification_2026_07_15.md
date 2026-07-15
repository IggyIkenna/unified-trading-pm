---
doc_type: issue
title:
  Live tradfi manifest had 34,260 rows misclassified as capture_status="attempted_failed" while carrying an
  EXPECTED_*-prefixed honest-absence error_reason (should have been "empty_confirmed") — data fixed, writer guard
  shipped to prevent recurrence
summary:
  "While triaging tradfi mbp_10 DP_RUN_MOSTLY_EMPTY alerts (data_pipeline_alerts_batch_remediation_2026_07_15), found a
  much larger cross-cutting bug in the live production tradfi manifest
  (market-data-tick-tradfi-prd-central-element-323112, _index/availability_index.parquet): 34,260 rows (not the ~7,700
  in the initial narrow grep) had error_reason starting with EXPECTED_ (a prefix that per this workspace's convention
  should ONLY pair with capture_status in {expected_unattempted, empty_confirmed} — an honest, known absence) but were
  instead stored with capture_status=attempted_failed, misclassifying honest absence as an active fetch failure. Two
  distinct reasons involved: EXPECTED_CHAIN_META_ROW_NOT_DOWNLOADABLE (18,878 rows, 100% CME blank-instrument_id
  options_chain/futures_chain meta-rows) and EXPECTED_SOURCE_NOT_AVAILABLE (15,382 rows, 100% matching the exact
  NYSE/NASDAQ/KRX out-of-scope instrument allowlists already used by 2 precedent reclassification scripts). Both reasons
  already have thousands of correctly-classified empty_confirmed sibling rows using the identical string, so each cohort
  was reclassified in place (capture_status flipped to empty_confirmed, error_reason left unchanged) via a new one-off
  script, verified before/after (attempted_failed -34260, empty_confirmed +34260, total rows unchanged). Root-cause
  provenance of the original misclassifying writer could NOT be established — all 34,260 rows share an attempted_at
  clustered in a single 2026-07-07T06:39:59Z-07:29:16Z window, but grepping the whole workspace for both literal reason
  strings only surfaces read-side consumers and 4 OTHER one-off reclassification scripts (all of which write the CORRECT
  capture_status pairing) — no committed writer path currently produces this exact misclassification, so this is flagged
  honestly as unresolved provenance rather than guessed. A systemic gap was confirmed and closed:
  ManifestWriter.record_failed(error=...) had no validation rejecting an EXPECTED_*-prefixed reason (unlike
  record_empty()'s closed-set enum check) — added a mirror-image guard that now hard-rejects this pattern at write time."
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    tradfi,
    manifest,
    honest-coverage,
    capture-status,
    empty-confirmed,
    attempted-failed,
    data-correctness,
    manifest-writer-guard,
    data-pipeline-alerts,
  ]
related:
  [
    ../data_pipeline_alerts_batch_remediation_2026_07_15.md,
    tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    ../../../codex/02-data/availability-manifest-and-data-status.md,
    ../../../codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-15
parent_epic: tradfi_master
priority: P1
source:
  [
    "operator-dispatched sub-agent task, discovered while triaging tradfi mbp_10 DP_RUN_MOSTLY_EMPTY alerts under
    data_pipeline_alerts_batch_remediation_2026_07_15.md, 2026-07-15",
  ]
assigned_vm: NA
resolved_by:
  [
    "market-tick-data-service@92d4fb18b826c7b43aa3597d5b1eeb135e26d829 (data fix: reclassification script,
    dry-run+apply, verified)",
    "unified-trading-library@c08a8d61b96d6d1570389f9396068bed51001816 (code fix: record_failed EXPECTED_*-prefix reject
    guard)",
  ]
locked_by:
locked_since:
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
---

# Tradfi manifest EXPECTED_*-reason / attempted_failed misclassification — 34,260 rows

## The bug

Every `capture_status` / `error_reason` pairing in this workspace's manifest convention follows a strict rule:
`error_reason` starting with `EXPECTED_` is an honest, KNOWN absence (calendar-pre-skip, out-of-scope instrument,
structural non-downloadable meta-row, etc.) and must pair with `capture_status` in
`{expected_unattempted, empty_confirmed}` — never `attempted_failed` (which means an active fetch was attempted and
genuinely errored). A row with `error_reason="EXPECTED_X"` + `capture_status="attempted_failed"` is a walking
contradiction: it claims BOTH "we know in advance this can never succeed" AND "we tried and it failed" at the same time.
Downstream consequences of leaving this misclassified: backfill VMs retry a request that can never succeed (wasted
compute/API budget), and `DP_RUN_MOSTLY_EMPTY` failure-ratio alerts count honest absences as real gaps, inflating the
alert noise this remediation wave was specifically trying to quiet.

## Real counts (live-queried 2026-07-15, before any fix)

Queried `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` directly (5,564,746
total rows) for `capture_status="attempted_failed"` AND `error_reason` starting with `EXPECTED_` — broader than the
single reason string (`EXPECTED_SOURCE_NOT_AVAILABLE`) the triggering task named, per its own instruction to check for
siblings:

| error_reason                               |       rows | venue(s)                              | instrument_id                                                    | data_types                                                                                                                                                            |
| ------------------------------------------ | ---------: | ------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EXPECTED_CHAIN_META_ROW_NOT_DOWNLOADABLE` |     18,878 | CME (100%)                            | blank (100%)                                                     | trades 8,630 / ohlcv_1m 7,930 / ohlcv_1s 1,206 / tbbo 1,112                                                                                                           |
| `EXPECTED_SOURCE_NOT_AVAILABLE`            |     15,382 | NYSE 7,332 / KRX 6,633 / NASDAQ 1,417 | non-blank (100%), exact match to 2 precedent scripts' allowlists | tbbo 2,365 / ohlcv_15m 2,347 / trades 2,343 / ohlcv_24h 1,964 / ohlcv_1m 1,832 / ohlcv_1s 1,739 / mbp_10 1,186 / corporate_action_confirmed 807 / earnings_result 799 |
| **Total**                                  | **34,260** |                                       |                                                                  |                                                                                                                                                                       |

A defensive broader scan for ANY other `EXPECTED_*`-prefixed reason under `attempted_failed` (not just these two)
returned **0** — these are the only two reasons involved. All 34,260 rows share `attempted_at` between
`2026-07-07T06:39:59.467880+00:00` and `2026-07-07T07:29:16.526927+00:00` — a single ~50-minute batch pass, not
scattered/ongoing.

## Root cause — writer provenance NOT established (flagged honestly, not guessed)

Grepped the whole workspace for both literal reason strings. They appear in exactly 4 places, ALL of which are one-off
reclassification scripts that correctly pair the reason with `capture_status="empty_confirmed"` via raw parquet edits
(bypassing `ManifestWriter`'s API, because — see below — neither string is a member of UAC's closed-set
`EmptyConfirmedReason` enum, so `record_empty()` would reject them):

- `market-tick-data-service/scripts/reclass_krx_eu_source_not_available.py` — `EXPECTED_SOURCE_NOT_AVAILABLE`, KRX-only,
  `expected_unattempted → empty_confirmed`.
- `market-tick-data-service/scripts/reclass_oos_equity_eu_not_in_dataset.py` — `EXPECTED_SOURCE_NOT_AVAILABLE`,
  NYSE/NASDAQ, `expected_unattempted → empty_confirmed`.
- `market-tick-data-service/scripts/reclass_cme_chain_metarows_eu_not_downloadable.py` —
  `EXPECTED_CHAIN_META_ROW_NOT_DOWNLOADABLE`, CME chain meta-rows, `expected_unattempted → empty_confirmed`.
- `market-tick-data-service/scripts/reclass_cme_chain_meta_rows.py` — a SIBLING CME chain-meta-row script using the
  DIFFERENT (canonical, enum-member) reason `EXPECTED_CHAIN_AGGREGATE` for an overlapping-but-not-identical predicate
  (see "Known taxonomy gap" below).

None of these 4 scripts' scope matches the ~34,260-row footprint (all four are pass-once, `expected_unattempted`-only
targets, already applied per their own preconditions), and none of them ever writes `capture_status="attempted_failed"`
— i.e. **the actual writer that produced the misclassified rows is not visible in currently-committed source**. The
2026-07-07 06:39-07:29 UTC clustering strongly suggests a single batch/backfill run (possibly an uncommitted or
since-reverted ad-hoc script, or a code path that has since been changed/removed) set `error_reason` correctly but
called `record_failed()` instead of `record_empty()`/`record_expected_empty()` — exactly the class of mistake the new
UTL guard (see below) now prevents at the API boundary. This provenance gap is left OPEN and undiscovered rather than
attributed to a guess.

## Known taxonomy gap (flagged, not fixed in this pass)

Neither `EXPECTED_SOURCE_NOT_AVAILABLE` nor `EXPECTED_CHAIN_META_ROW_NOT_DOWNLOADABLE` is a member of UAC's closed-set
`EmptyConfirmedReason` enum (`unified_api_contracts/canonical/crosscutting/_honest_coverage_empty_reasons.py`):

- `EXPECTED_SOURCE_NOT_AVAILABLE` has no canonical equivalent in the enum. The closest candidates
  (`EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE`, `EXPECTED_KNOWN_SOURCE_GAP`) don't quite match its actual semantic ("this
  specific instrument isn't in the vendor's dataset for this venue," a per-instrument gap, not a per-data_type or
  general-source gap).
- `EXPECTED_CHAIN_META_ROW_NOT_DOWNLOADABLE` has a near-exact canonical sibling that DOES already exist:
  `EmptyConfirmedReason.EXPECTED_CHAIN_AGGREGATE` — used by the OTHER CME chain-meta-row precedent script
  (`reclass_cme_chain_meta_rows.py`) for what is, per its own citation (operator decision BLK-ca110c07 answer A,
  2026-06-28), the SAME underlying decision. The two precedent scripts diverged into two different literal strings for
  one decision; 19,639 `empty_confirmed` rows already carry `EXPECTED_CHAIN_META_ROW_NOT_DOWNLOADABLE` specifically
  (options_chain/futures_chain, blank instrument_id) vs. an unknown number carrying `EXPECTED_CHAIN_AGGREGATE`.

**Decision made for this fix**: reclassify the misclassified rows using the SAME (existing, if non-canonical) reason
string each cohort's existing `empty_confirmed` siblings already use (15,989 + 19,639 existing rows respectively), NOT a
"more correct" canonical string — this keeps the manifest internally consistent (one root-cause class = one reason
string) rather than splitting it a third way. Migrating either non-canonical string to a canonical enum member, or
consolidating the two CME chain-meta-row strings into one, is a genuine taxonomy decision (touches tens of thousands of
already-classified rows) that needs an explicit operator call — **not done here**, flagged as follow-up.

## Part A — data fix (shipped)

`market-tick-data-service@92d4fb18b826c7b43aa3597d5b1eeb135e26d829` —
`scripts/reclass_tradfi_expected_reason_attempted_failed_2026_07_15.py` (mirrors the exact structure of
`reclass_oos_equity_eu_not_in_dataset.py`: dry-run by default, `--apply` flag, snapshot-before-write, before/after
counts logged). Targets tradfi rows where `capture_status="attempted_failed"` AND `error_reason` is one of the two
VERIFIED reasons above → flips `capture_status` to `empty_confirmed` (leaves `error_reason` unchanged). Any OTHER
`EXPECTED_*`-prefixed `attempted_failed` row (defensive check — 0 found live) is left untouched and counted separately
rather than guessed at.

**Applied for real, 2026-07-15.** Snapshot taken first:
`gs://market-data-tick-tradfi-prd-central-element-323112/_index/snapshots/pre_expected_reason_attempted_failed_reclass_20260715T024349Z.parquet`.
Before/after verification (re-queried the live manifest post-apply, not just trusted the script's own log):

| capture_status         |    before |     after |   delta |
| ---------------------- | --------: | --------: | ------: |
| `empty_confirmed`      | 3,235,132 | 3,269,392 | +34,260 |
| `attempted_failed`     |   342,134 |   307,874 | -34,260 |
| `captured`             | 1,608,392 | 1,608,392 |       0 |
| `expected_unattempted` |   379,088 |   379,088 |       0 |
| **Total rows**         | 5,564,746 | 5,564,746 |       0 |

A follow-up dry-run of the same script immediately post-apply confirms 0 remaining rows match the misclassification
predicate. 5 new regression tests pin `reclassify()` (pure function, no GCS needed):
`tests/unit/scripts/test_reclass_tradfi_expected_reason_attempted_failed.py`.

## Part B — code fix (shipped, prevents recurrence)

`unified-trading-library@c08a8d61b96d6d1570389f9396068bed51001816` —
`unified_trading_library/manifest_writer/_writer_record.py::ManifestWriterRecordMixin.record_failed()` now rejects any
`error` string starting with `EXPECTED_` (the same `EXPECTED_EMPTY_REASON_PREFIX` constant `record_expected_empty()`
already uses, applied in the opposite direction — reject rather than require the prefix), raising `ValueError` with a
message pointing the caller at `record_empty()`/`record_expected_empty()` instead. Mirrors the existing
`EmptyFromLiveInstrumentError` guard on `record_empty()` (which rejects the OPPOSITE misclassification — a live
instrument's genuine empty response masquerading as honest absence) — this is the mirror-image guard closing the other
direction.

**Verified no existing call site breaks**: grepped the whole workspace for `record_failed(` (222 non-test call sites)
and specifically for any literal `error="EXPECTED_..."` pattern — zero hits. `NormalisingManifestWriter.record_failed()`
(the strict-path-validation wrapper in `manifest_writer_normalising.py`) delegates to the same guarded
`ManifestWriter.record_failed()`, so it inherits the guard automatically — no separate change needed there. 5 new
regression tests (`tests/unit/test_manifest_writer_record_failed_expected_reason_guard.py`) pin: a genuine classified
failure string still writes normally; both verified live-bug reason strings are rejected; a THIRD, canonical
`EmptyConfirmedReason` member (`EXPECTED_HOLIDAY`) is also rejected (proves the guard is a structural prefix check, not
a narrow 2-string denylist); the pre-existing empty-string guard still fires. All 459 pre-existing `manifest_writer`
unit tests pass (no regressions); `quality-gates.sh --no-fix` green both repos.

## What was deliberately left unreclassified

Nothing — the defensive broader scan found exactly 0 `attempted_failed` rows with an `EXPECTED_*`-prefixed reason
outside the two verified strings, so no ambiguous rows were encountered. If a future run of this same reclassification
pattern (or the DP_RUN_MOSTLY_EMPTY alert) surfaces a THIRD `EXPECTED_*` reason under `attempted_failed`, the script's
own defensive counter (`other_expected_reason_attempted_failed_left_untouched`) will catch and report it rather than
silently reclassifying an unverified pattern.

## Follow-ups (not done in this pass, flagged for whoever picks these up)

- [ ] [DESIGN] P3. Taxonomy decision: should `EXPECTED_SOURCE_NOT_AVAILABLE` /
      `EXPECTED_CHAIN_META_ROW_NOT_DOWNLOADABLE` be added to UAC's closed-set `EmptyConfirmedReason` enum (making
      `record_empty()`/`record_expected_empty()` able to accept them directly, retiring the raw-parquet-edit precedent
      pattern), OR should `     EXPECTED_CHAIN_META_ROW_NOT_DOWNLOADABLE` specifically be consolidated into the
      already-canonical `EXPECTED_CHAIN_AGGREGATE` (touches 19,639+ existing rows + this fix's 18,878 + the other
      precedent script)? Needs an explicit operator call — out of scope for this data-correctness fix.
- [ ] [INVESTIGATE] P3. The actual writer that produced the original 34,260 misclassified rows (2026-07-07 06:39-07:29
      UTC) was never identified — not visible in currently-committed source. If it recurs (the new UTL guard would now
      make it loud-fail instead of silently writing bad rows, so a recurrence should surface as an exception/alert
      rather than silent drift), the guard's raised exception + callsite traceback should make finding it
      straightforward; if it does NOT recur, this may have been a one-off uncommitted/reverted script and is not worth
      further archaeology.

## Progress Log

- 2026-07-15: Bug found by a sub-agent triaging tradfi mbp_10 `DP_RUN_MOSTLY_EMPTY` alerts under
  `data_pipeline_alerts_batch_remediation_2026_07_15.md`, while investigating one narrow finding (a prior investigation
  had grepped only `EXPECTED_SOURCE_NOT_AVAILABLE` and found ~7,700 rows across 4 data_types). Re-queried the live
  manifest broadly (any `EXPECTED_*`-prefixed reason under `attempted_failed`, not just the one string) and found the
  real footprint is 34,260 rows across 2 reason strings (a second, previously-unnoticed sibling reason,
  `EXPECTED_CHAIN_META_ROW_NOT_DOWNLOADABLE`, contributes 18,878 of the 34,260). Verified `EmptyConfirmedReason`'s
  closed-set enum to determine the correct target reason string per cohort (neither is canonical; kept each cohort's
  existing, already-established non-canonical string for manifest-wide consistency rather than inventing a third variant
  — see "Known taxonomy gap" above). Data fix shipped + applied + verified:
  `market-tick-data-service@92d4fb18b826c7b43aa3597d5b1eeb135e26d829`. Code-fix guard shipped + tested:
  `unified-trading-library@c08a8d61b96d6d1570389f9396068bed51001816`. This issue doc filed per the workspace's
  findings-triage HARD RULE (data-correctness, cross-cutting, big finding — notify operator + issue doc).
