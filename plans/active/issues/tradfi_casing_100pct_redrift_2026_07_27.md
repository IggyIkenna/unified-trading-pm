---
doc_type: issue
title:
  TradFi instrument_type casing re-drift found 2026-07-27 — the 2026-07-25 100% directive is no longer literally true
summary: >-
  A fresh live read of the tradfi availability_index (2026-07-27), taken while closing an adjacent semantic-relabel
  todo, found ~63,143 tradfi manifest rows still carrying a lowercase instrument_type — materially more than the
  45,428-row residual migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py closed (and self-verified 0 residual on)
  the same day. Either an active writer path still bypasses canonicalize_tradfi_manifest_itype, or the earlier
  self-verify sampled a stale consolidator-merge window. Diagnose via written_at freshness before re-running the casing
  script blindly.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [tradfi, casing, instrument-type, manifest, re-drift, data-correctness]
related:
  [
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-27
priority: P1
parent_epic: tradfi_master
author: agent-orchestrator worker slot-9
assigned_vm: planning
source: [tradfi_manifest_content_recovery_completion_2026_07_24.md]
resolved_by: market-tick-data-service@a1729bb4
locked_by:
---

## What I found

While closing `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s semantic-mislabel/null-blank todo
(mtds@132ea6b1), a fresh live read of the tradfi `availability_index.parquet` (2026-07-27) found ~63,143 tradfi rows
still carrying a LOWERCASE `instrument_type`:

| value     |  count |
| --------- | -----: |
| equity    | 28,914 |
| combo     | 23,428 |
| future    |  4,307 |
| etf       |  5,372 |
| index     |    790 |
| spot_pair |    316 |
| FUTURES   |     16 |
| UNKNOWN   |  2,902 |

This is materially larger than the 45,428-row residual `migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py` was
built to close (and did close, per that script's own fresh live re-verification the same day: "SELF-VERIFY:
4,988,822/4,988,822 UPPERCASE" — 0 non-UPPERCASE residual at that point).

## Why it matters

`cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md` set a literal-100% UPPERCASE bar for tradfi. Either the
writer-side fix (`_tradfi_manifest_canon.py::canonicalize_tradfi_manifest_itype`, wired into `venue_fetch.py` +
`sentinels.py`) has a gap some capture path still bypasses, or a third write path (not covered by either prior audit) is
re-introducing lowercase rows. This directly affects: (a) the semantic-relabel script this issue was found alongside —
those lowercase rows are OUTSIDE its `_TOUCHABLE_STORED_TYPES` scope (which matches exact-case
`{FUTURE, OPTION, COMBO, ...}` — a `future`/`combo` typed row is silently skipped by that script too, not just the
casing script); (b) any downstream consumer trusting the UPPERCASE-enum contract.

## Recommended decision

Diagnose the source before re-running the casing script blindly a third time (which would fix the symptom again without
closing the actual re-drift gap):

1. Check `written_at` on a sample of the lowercase rows — if recent (post the 2026-07-25 writer fix ship), it is an
   ACTIVE re-drift (writer bug not yet found); if old, it's evidence the 2026-07-25 self-verify sampled a
   consolidator-merge window that hadn't caught up to the full corpus yet (a staleness artifact, not a new bug).
2. If active: find the write path that still bypasses `canonicalize_tradfi_manifest_itype` (grep every
   `record_captured`/`ManifestWriter.add` call site for tradfi that doesn't route through it) and fix it there, THEN
   re-run the casing restamp for the residual.
3. If stale: just re-run `migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py --apply` again (idempotent,
   already-proven-safe) to close the residual.

- [x] ✅ [DATA] P1. Diagnose the tradfi instrument_type casing re-drift per the recommended decision above (check
      `written_at` freshness, find/fix any writer path still emitting lowercase, re-run the casing restamp for the
      residual). (repo: market-tick-data-service)

## Diagnosis (2026-07-27, slot-13)

**`written_at` freshness (live read, no new whole-corpus walk — the single already-materialized
`_index/availability_index.parquet` read the casing/relabel scripts already do):** ACTIVE re-drift, not a stale
snapshot. Population grew from ~63,143 (this doc's original finding) to **82,311** lowercase rows in the hours since,
`written_at` spanning 2026-07-26 through the live-read moment (nothing older) — grouped by (instrument_type, venue):

| instrument_type   | venue  | written_at span       |  count |
| ----------------- | ------ | --------------------- | -----: |
| combo             | CME    | 2026-07-27 (same day) | 23,428 |
| continuous_future | CME    | 2026-07-26            | 19,184 |
| equity            | NASDAQ | 2026-07-26 → 07-27    | 15,484 |
| equity            | NYSE   | 2026-07-26 → 07-27    | 12,956 |
| etf               | NYSE   | 2026-07-27            |  4,108 |
| future            | CBOE   | 2026-07-26 → 07-27    |  4,108 |
| etf               | NASDAQ | 2026-07-26 → 07-27    |  1,264 |
| index             | CBOE   | 2026-07-26 → 07-27    |    790 |
| equity            | KRX    | 2026-07-26 → 07-27    |    474 |
| spot_pair         | FX     | 2026-07-26 → 07-27    |    316 |
| future            | CME    | 2026-07-27            |    199 |

**Root-caused TWO genuine code-level bypasses of the shared `canonicalize_tradfi_manifest_itype` emitter — both fixed
this session, mtds (sha pending quickmerge):**

1. **`migrate_cme_monolith_trades_2026_07_26.py::write_day_plan`** — the manifest-row `shard_it` computation hand-rolled
   `group_key.instrument_type.value.lower()` for every non-chain group (COMBO included) instead of routing through the
   shared emitter. **Exact match** for the `combo`/CME/`data_type=trades` rows above (23,428 rows, `written_at`
   2026-07-27T00:07–00:18 — matches this plan's own Progress Log entry "`--apply` AT SCALE LAUNCHED 2026-07-27
   (slot-10)" to the minute). Fixed: `shard_it` now calls
   `canonicalize_tradfi_manifest_itype(_VENUE, group_key.instrument_type.value)` for the non-chain branch;
   `futures_chain`/`options_chain` branches untouched (correct — those are the permanent bundle-grain lowercase tokens).
   Added `test_write_day_plan_apply_stamps_uppercase_combo_instrument_type`.
2. **`rebuild_tradfi_manifest.py`** — BOTH manifest-emission call sites (`_emit_bundled_shard_row`'s
   `row_key["instrument_type"]` and `scan_and_rebuild`'s `target.add(instrument_type=...)`) stamped the raw GCS
   hive-path token directly, with ZERO import of or route through `_tradfi_manifest_canon.py` at all — a latent bypass
   (this script did not run recently per the VM-log/deployment-registry check below, so it is not the active driver of
   the CURRENT re-drift, but it would silently reproduce this exact bug on its next invocation, and it is a real
   reusable shared primitive — `_emit_bundled_shard_row` is also called by
   `reshape_tradfi_ice_cme_legacy_chain_tail_2026_07_13.py`). Fixed both call sites to route through
   `canonicalize_tradfi_manifest_itype(parsed.venue, parsed.instrument_type)`; the `covered_keys` dedup-tracking set
   (used only to gate `reemit_honest_absence_rows`'s re-emission, which itself replays raw types from the existing
   index) deliberately left UNCHANGED to avoid a covered-keys/CF11 casing mismatch regression. Added
   `test_scan_rebuild_apply_canonicalizes_instrument_type_casing`.
3. **`continuous_future` is a genuinely NEW, unmapped token** — confirmed NOT a member of UAC's `InstrumentType` enum at
   all (unlike every other lowercase token this module maps, which ARE real enum members just case-drifted), so
   `canonicalize_tradfi_manifest_itype`'s honest-absence "never guess on an unmapped token" rule left it lowercase
   forever. `rebuild_tradfi_manifest.py`'s own `BUNDLED_ITYPES` already treats it as the same kind of bundle-grain
   partition axis as `futures_chain`/`options_chain` — added it to `_tradfi_manifest_canon.py`'s
   `_BUNDLE_GRAIN_EXCLUDED` set to match. Extended the parametrized bundle-grain test.

**NOT fully root-caused — flagging rather than guessing:** the dominant remaining population (equity/etf/future/index/
spot_pair across NASDAQ/NYSE/CBOE/KRX/FX, ~59K rows, `written_at` fresh through 2026-07-27) is NOT explained by either
bypass above (neither script touches those venues) and no VM launched recently for those venues (checked GCP + AWS
instance lists and the `vm-logs/` prefix — only a `tradfi-bf-cme-ohlcv-1m-es-2020` relaunch loop from the zombie-
watchdog auto-recovery pattern, CME-only). The only process touching ALL of tradfi recently is the daily Cloud Run job
`uts-prod-market-tick-data-service-tradfi-databento-t1-recon` (venue_fetch.py code path — confirmed CORRECT at current
HEAD). Its image tag is mutable (`:latest`); the digest tagged `:latest` as of this session was rebuilt only at
2026-07-27T19:47:46Z (commit `c36d35d`, well AFTER this morning's 00:35:02Z execution), which is at minimum consistent
with — though not proven to be — the same "a shipped code fix does not mean a fixed fleet" class already documented in
this plan's Progress Log, except for a Cloud Run JOB image rather than a VM tarball. **Follow-up todo added below**
rather than asserting this as confirmed root cause.

- [ ] [DATA] P1. Re-run `migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py --apply` for the residual — but only
      AFTER confirming the `uts-prod-market-tick-data-service-tradfi-databento-t1-recon` Cloud Run job's `:latest` image
      actually contains the current `_tradfi_manifest_canon.py` (byte-grep the pulled image or re-check after its next
      daily 00:35 UTC run lands with a definitely-post-fix image) — re-running the restamp before confirming the daily
      job is fixed just re-hides the symptom on the next 00:35 UTC run. (repo: market-tick-data-service)
- [ ] [DATA] P2. Confirm whether `market-tick-data-service`'s Cloud Run job image build is triggered automatically on
      every `main` merge (should be, per the standard CI/CD flow) or has its own gap — if the latter, this is a second,
      independent deployment-staleness class distinct from the VM-tarball one already documented, and needs its own
      codex note. (repo: market-tick-data-service or deployment-service, whichever owns the Cloud Run deploy trigger)
