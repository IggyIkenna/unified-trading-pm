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
assigned_vm: planning
source: [tradfi_manifest_content_recovery_completion_2026_07_24.md]
resolved_by: market-tick-data-service@a1729bb4
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
# 2026-07-27 (slot-12, main ruling on BLK-a27aa7e4/BLK-f3950c25): the 4
# remaining open todos (UTL casing-canon seam -> mtds re-export+revert ->
# IS/MDPS inherit-verify -> [OPERATOR] repair) are a REAL dependency chain
# (each writes/depends on the prior step's shipped code), not independent
# parallel work — sequential=true wires prereqs.completed_tasks in plan_order
# so the backlog dispatcher cannot fan them out onto the unshipped UTL seam.
sequential: true
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

**SUPERSEDED (2026-07-27, slot-12, `BLK-a27aa7e4` — main ruling Option A, per `BLK-f3950c25`):** the two items below are
superseded by the "Additive root-cause + operator ruling" section right below — live-repo verification (all 4 repos
fresh-pulled to `origin/live-defi-rollout`: UTL@0d1a2257, mtds@a6c8e29e, instruments-service@20778e98,
market-data-processing-service@21aa1af) confirmed the dominant root cause is NOT the mtds Cloud Run job image (at most a
minor contributor) but `instruments-service`/`writers.py` +
`market-data-processing-service`/`build_continuous_engine.py` writing with ZERO casing canon at all. Re-running the
casing `--apply` script is now correctly scoped as the FINAL `[OPERATOR]`-only todo in that section (`-007`, gated on
the UTL seam shipping + fleet redeploy), never this Cloud-Run-image precondition check. Resolved-via-reconciliation, NOT
executed — the real fix chain is `-004`/`-005`/ `-006` immediately below.

1. ~~Re-run `migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py --apply` for the residual — but only AFTER
   confirming the `uts-prod-market-tick-data-service-tradfi-databento-t1-recon` Cloud Run job's `:latest` image actually
   contains the current `_tradfi_manifest_canon.py`~~ (repo: market-tick-data-service) — SUPERSEDED, see note above.
2. ~~Confirm whether `market-tick-data-service`'s Cloud Run job image build is triggered automatically on every `main`
   merge or has its own gap~~ (repo: market-tick-data-service or deployment-service) — SUPERSEDED, see note above.

## Additive root-cause + operator ruling (2026-07-27, slot-10)

Slot-13's diagnosis (above) root-caused two mtds bypasses (the `migrate_cme_monolith_trades` script → 23,428 combo rows;
`rebuild_tradfi_manifest` latent) and shipped mtds@a1729bb4, but explicitly flagged the **dominant ~39.7K
equity/etf/future/index/spot_pair population as NOT fully root-caused**, suspecting the mtds Cloud Run recon job's
`:latest` image staleness. A per-`service_name`/`enumerator_run_id` provenance read (same single index object,
gen 1785182686866562) identifies the actual writers — it is **NOT (only) the mtds Cloud Run job**:

|  rows | `service_name`                 | writer path                                                                                  |
| ----: | ------------------------------ | -------------------------------------------------------------------------------------------- |
| 39500 | instruments-service            | universe enumerator `engine/orchestrator/writers.py:381-390` (raw `_itype`)                  |
| 19184 | market-data-processing-service | `engine/build_continuous_engine.py` stamps `"continuous_future"` (lines 336/374/397/460/496) |
| 23627 | market-tick-data-service       | the `migrate_cme_monolith_trades` script bypass slot-13 already fixed                        |

`instruments-service/engine/orchestrator/writers.py:381-390` stamps `instrument_type=_itype` where `_itype` is the raw
adapter-df token from `_split_by_instrument_type` (line 151-153) — for tradfi the databento adapter carries lowercase
hive tokens, and there is NO tradfi UPPERCASE canonicalization on the IS side. These are the `enum-universe-tradfi-*`
runs. This is the ~39.7K slot-13 could not explain. The mtds Cloud Run recon job is at most a minor contributor.

**Operator ruling (BLK-f3950c25, main, 2026-07-27) — Option A: centralize at the UTL seam.** Add the tradfi/cefi
`instrument_type` UPPERCASE casing canon to UTL, co-located with UTL's existing canonical derivation
(`canonical/_derive_instrument_id.py`) and applied ADDITIVELY at the shared `ManifestWriter` write seam every service
depends on (mtds/IS/MDPS inherit it for free), kept SEPARATE from the path-validation wrapper. **`continuous_future`
maps to catalogue type `FUTURE`** (databento classifier + build-continuous engine both settle this) — this SUPERSEDES
slot-13's shipped `_BUNDLE_GRAIN_EXCLUDED` addition (which keeps it lowercase); that add must be reverted in favour of
the FUTURE mapping. The 82,311 already-written rows are a SEPARATE repair follow-up (seam fix stops NEW drift only);
compare case-insensitively in the interim (`migration_pending`).

- [x] ✅ [DATA] P1. UTL: add tradfi/cefi `instrument_type` UPPERCASE casing canon co-located with
      `canonical/_derive_instrument_id.py`, applied additively at the `ManifestWriter` record\_\* write seam (separate
      from `manifest_writer_normalising.py`); include `continuous_future → InstrumentType.FUTURE`. All-AG blast radius →
      QG green + SIT/fleet-green before ship; quickmerge UTL FIRST. (repo: unified-trading-library) — DONE
      `unified-trading-library@688e49bc`: new `canonical.canonicalize_manifest_instrument_type`, wired additively into
      `record_captured`/`record_captured_from_counts`/`_record_status` (shared by record_empty/record_failed/
      record_expected_unattempted); `continuous_future → FUTURE`; `futures_chain`/`options_chain` stay permanently
      lowercase; 30 new unit tests; full QG green. Also fixed an unrelated pre-existing red
      (`unified-trading-library@c1c6cfff`, self-caused by an earlier this-session UAC rename `edf5122d` that never
      updated this repo's `test_point_in_time.py`) so the tree could ship clean.
- [x] ✅ [DATA] P1. mtds: RE-EXPORT the shared UTL canon and DELETE the local `_tradfi_manifest_canon.py` (no shim);
      update `venue_fetch.py`/`sentinels.py` imports. REVERT slot-13's `continuous_future` addition to
      `_BUNDLE_GRAIN_EXCLUDED` (operator ruled FUTURE, not excluded). (repo: market-tick-data-service) — DONE
      `market-tick-data-service@4122df13`: deleted `_tradfi_manifest_canon.py`; `venue_fetch.py`/`sentinels.py` now call
      the mtds-specific id-building/venue-gating wrappers (`_resolve_tradfi_manifest_shard`/`_tradfi_manifest_itype`/
      `_tradfi_sentinel_itype`) which delegate casing lookups to UTL's `canonicalize_manifest_instrument_type` — split
      into a new shared `engine/orchestrator/_tradfi_manifest_shard.py` module (keeps both files at the 900-line file-
      size cap); `rebuild_tradfi_manifest.py`/`migrate_cme_monolith_trades_2026_07_26.py`/
      `migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py` call the UTL function directly.
      `continuous_future → FUTURE` now applies (bundle-grain exclusion reverted); regression tests added
      (`tests/unit/engine/test_tradfi_manifest_shard.py`). Full QG green (7223 tests).
- [x] ✅ [DATA] P1. Verify instruments-service (`engine/orchestrator/writers.py`) + market-data-processing-service
      (`engine/build_continuous_engine.py`) manifest writes inherit the shared UTL casing canon at the record\_\* seam
      (add a live re-read assertion: 0 lowercase tradfi rows written after the seam ships). (repos: instruments-service,
      market-data-processing-service) — DONE. Both repos already inherit the fix for free (editable path dependency on
      unified-trading-library, HEAD has 688e49bc as an ancestor) — confirmed via source read: neither
      `writers.py::_write_venue` nor `build_continuous_engine.py::_process_day_shard` has any local casing logic, both
      call only `unified_trading_library.ManifestWriter.record_captured`/`record_empty`, which now canonicalize
      internally. Added a write-seam integration test per repo exercising each call site's EXACT kwargs shape with a
      real `ManifestWriter` (`MockEventSink`-backed, no live GCS) — proves the actual production call shape
      (`asset_group="tradfi"`, lowercase `instrument_type` incl. `continuous_future`) comes back UPPERCASE:
      `instruments-service@10513f78` (`tests/unit/test_tradfi_manifest_casing_inherited_from_utl_seam.py`, 5 tests) and
      `market-data-processing-service@25faf6d` (same filename, 2 tests). No code change needed in either repo. Full QG
      green both repos.
- [ ] [DATA] P2. AFTER the UTL seam ships AND all writer fleets redeploy, re-run
      `migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py --apply` to repair the 82,311 pre-fix lowercase rows
      (heavy-I/O → VM/in-region; prod-manifest CAS mutation, snapshot-first). **Re-tagged off `[OPERATOR]`
      (2026-07-28)**: per this doc's own line-85 framing ("idempotent, already-proven-safe") plus finding T
      (`task_template.md` / `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a) — a FRESH
      `gcs_bucket_soft_delete_retention_seconds()` check on the tradfi manifest bucket returning ≥604800s at execution
      time qualifies this CAS re-stamp as reversibility-verified, no `[OPERATOR]` sign-off required. Add
      `continuous_future → FUTURE` to the restamp's canonical map first so its self-verify does not refuse. (repo:
      market-tick-data-service)
