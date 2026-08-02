---
doc_type: issue
title:
  lst_rates empty-marker writer hardcodes venue=LST — pre-genesis absence markers land at the non-canonical aggregate
  path (manifest/GCS split-brain)
summary: >-
  `lst_rates_handler.py::_write_empty_lst_marker` hardcodes `venue="LST"` (the instrument_type category value, not a
  real protocol) when persisting a zero-row absence marker for pre-Lido-genesis days, while its sibling function
  `_record_empty_manifest` correctly records the same absence under the real per-protocol venue (LIDO/ETHERFI/ETHENA/
  MARINADE/...). Result: the manifest is correct, but GCS accumulates orphaned zero-row parquet objects at the retired
  `venue=LST` aggregate path with no manifest row pointing at them. 551 such objects (334 `_migrated_` tombstones from
  the 2026-06 canonicalisation pass + 217 freshly-written `empty.parquet` files dated 2026-07-26) were found and deleted
  this session; the write-path bug itself is still live as of commit 45a9fe69 (2026-07-26).
status: resolved
nature: issue
asset_group: defi
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, lst, venue, canonical-path, empty-marker, split-brain, honest-absence]
related:
  [
    defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20,
    defi_manifest_canonicalisation_2026_06_01,
    defi_venue_lst_rates_residual_2026_07_24,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
drift_direction: worsening-slowly
depends_on: []
source:
  [
    "found 2026-07-27 during an operator-directed forensic dig into
    gs://market-data-tick-defi-prd-central-element-323112's day=2020-03-26 venue=LST/.../lst_rates/ shard; cleanup (551
    objects) executed same session via the sanctioned unified_trading_library.cloud_interface.gcs_delete_object SDK path
    after fresh-verifying the bucket's 7-day soft-delete retention",
  ]
resolved_by:
  "market-tick-data-service@5bf8a3c7 (2026-07-29) — _write_empty_lst_marker now loops the 4 real (venue, chain) pairs
  with no fallback/placeholder venue; the 551 orphaned venue=LST objects were deleted 2026-07-27 after a fresh
  soft-delete-retention check"
locked_by:
locked_since:
---

> **🗄️ ARCHIVED 2026-07-31 (operator-ruled locked-plan unlock + archive sweep, 2026-07-30 Q&A session)** — the lock on
> this doc was **INVALID on its face**: `locked_by: live-defi-rollout` is a branch name, not a person, and
> `locked_since: 2026-05-21` predated this doc's own `created: 2026-07-27` by two months. Operator ruling: clear the
> invalid lock, then apply the normal unlock-and-archive-if-done logic. It is done — the single `[BACKEND]` todo shipped
> (`market-tick-data-service@5bf8a3c7`). Its one remaining item was **prose-only** (the architectural question of
> whether to drop the physical zero-row marker write entirely in favour of manifest-only absence), so per archival
> ritual step 1 it was migrated into a real tracked `- [ ]` todo before this archive landed:
> `/plans/active/defi_consolidated_closeout_2026_07_18.md` § "Open follow-ups" (`[REVIEW] P3`). Per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

# lst_rates empty-marker writer hardcodes venue=LST

## What was found

Path in question:
`gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2020-03-26/ pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=LST/chain=ETHEREUM/instrument_type=lst/data_type=lst_rates/`
held two objects — `_migrated_lst_rates_1585224000.parquet` (created 2026-07-19) and `empty.parquet` (created
2026-07-26) — byte-identical (same MD5), both genuine 0-row parquets (verified via pyarrow: columns
`instrument_id, venue, chain, instrument_type, data_type, available_at`, 0 rows).

`venue=LST` is not canonical — real DeFi LST venues are per-protocol (`LIDO`, `ROCKETPOOL`, `ETHERFI`, `ETHENA`,
`MARINADE`, ... — 14 in `LST_VENUE_TO_TOKENS`). `LST` is the `instrument_type` category value
(`/codex/02-data/defi-canonical-naming-ssot.md:87-88`) leaking into the venue slot.

Widening the check to the full pre-Lido-genesis window (Lido/stETH genesis 2020-12-18/19,
`/codex/02-data/instrument-pipeline-defi.md:142-143`) found the SAME shard exists for **all 353 days**, 2020-01-01
through ~2020-12-18 — confirmed as the FULL scope via an independent `gsutil du -s` total (1,764,302 bytes = exactly 551
× 3,202-byte files, matching the object count below). Of those 353 days, **217 had a freshly-written `empty.parquet`
dated 2026-07-26** (yesterday relative to this session) — i.e. this is not dead historical debris, it is an
actively-recurring write.

## Root cause

`market-tick-data-service/cli/handlers/lst_rates_handler.py::_write_empty_lst_marker` (lines ~577-604) hardcodes
`venue="LST"` at line 588 when it writes the zero-row marker for a pre-genesis/no-data day. The sibling function in the
same handler, `_record_empty_manifest` (lines ~607-649), correctly records the SAME absence event under the real
per-protocol venue (LIDO/ETHERFI/ETHENA/MARINADE, ...). This is a genuine split-brain: **the manifest is right, the
physical GCS object is wrong** — every absence-marker write puts a zero-row file at the retired `venue=LST` aggregate
path that no manifest row references.

`git blame` on line 588 shows it was last touched by commit `33a14c1f8` (2026-06-11) — _after_ the C0-RD1 venue-split
migration below was marked done — and the file's latest commit is `45a9fe69` (2026-07-26 22:43:15 UTC, "fix(lst-rates):
derive per-shard pipeline_mode..."), the same day the fresh `empty.parquet` objects were written. The hardcoded venue
was never touched by either change.

## Why this wasn't caught by the 2026-07-24 sibling fix

`defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md`'s "Update 2026-07-24 (session 2)" fixed a **different**
bug in this exact same function: the empty-marker `file_name=` used to glue a wall-clock timestamp
(`lst_rates_{ts_label}.parquet`), so every re-run wrote a NEW, uniquely-named junk object. That fix dropped the
timestamp, letting `write_defi_rows` fall back to its own stable `"empty.parquet"` default (see
`lst_rates_handler.py:566` in that doc's fix list). That fix is real and correct — but it only addressed the
**filename**, not the **venue** argument passed at line 588. The two bugs live in the same function but are independent:
the filename fix shipped cleanly; the venue-hardcoding was out of scope for that issue and was never separately caught.

The practical effect: **before** the 2026-07-24 fix, each re-run of the pre-genesis marker write created a new
uniquely-timestamped `lst_rates_<epoch>.parquet` at the wrong `venue=LST` path (which the 2026-06 migration then
tombstoned to `_migrated_lst_rates_<epoch>.parquet`, one per day, 334 of them). **After** the fix, re-runs instead write
to the SAME stable `empty.parquet` name — still at the same wrong path — which is exactly the 217 fresh objects found
this session. The stable-filename fix was correct on its own terms; it just made the pre-existing wrong-venue bug more
visible/systematic rather than fixing it.

## Was the 2026-06 migration ever actually applied?

`plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md` documents the intended fix in detail (C0-RD1/
RD2/RD3, lines 1190-1215): row-split the aggregate `venue=LST` objects by protocol via UAC `LST_VENUE_TO_TOKENS` +
`to_canonical_venue`, superset-union-write to the canonical per-protocol path, then rebuild the manifest from the
rewritten data. All three are marked ✅ DONE, cited only by commit SHA (`mtds@e14d656b`, `mtds@90aac6e1`) — i.e. code
shipped, not data verified. **C0-RD3b is explicitly labeled a VM dry-run ("GREEN"), not an apply.** Critically, **C0-RD4
(completeness gate) and C0-RD5/RD5b (delete-all-legacy) remain unchecked `[ ]`** in the same archived document — the
plan itself never claims the actual delete ran. Confirming this independently:
`market-tick-data-service/scripts/one_offs/delete_migrated_defi_markers_2026_07_23.resume.jsonl` (47,084 records) shows
**0** `"action":"deleted"` and 46,772 `"would_delete"` as of 2026-07-23 — the dedicated cleanup tool has, to date, only
ever run in dry-run mode. So: **yes, scripted in detail, but the apply/delete step was never executed** — this session's
551-object delete is the first real execution of that cleanup, for this one shard.

## Cleanup executed this session (2026-07-27)

- Verified the bucket's soft-delete policy fresh (not assumed): `soft_delete_policy.retentionDurationSeconds = "604800"`
  (7 days), active since 2026-05-12 — satisfies the reversibility-verified bar for a prod delete
  (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a).
- Deleted all 551 objects under `venue=LST/chain=ETHEREUM/instrument_type=lst/data_type=lst_rates/` across the full
  353-day pre-genesis range (334 `_migrated_*.parquet` tombstones + 217 `empty.parquet`) via the sanctioned SDK path
  (`unified_trading_library.cloud_interface.gcs_delete_object`, never a raw `gsutil`/`gcloud` subprocess — the workspace
  guardrail correctly blocked the CLI form and pointed at this path). 0 errors; verified gone via a sampled
  re-`gcs_describe_object` pass returning `None` for all sampled URIs.
- No manifest rows were touched or needed touching — `_record_empty_manifest` already recorded these absences correctly
  under the real per-protocol venues, so these GCS objects were pure orphaned dead weight.

## Fix applied 2026-07-27 (operator ruling: fail fast, no fallback/default venue)

Operator direction: the fix must fail fast with no fallback/default venue value — never invent or default to a
placeholder venue string. Applied in `market_tick_data_service/cli/handlers/lst_rates_handler.py`:

- `_write_empty_lst_marker` no longer takes a single `venue` — it now loops over the same 4 real (venue, chain) pairs
  `_record_empty_manifest` already uses (`_LST_REAL_VENUES`: LIDO/ETHERFI/ETHENA on ETHEREUM, MARINADE on SOLANA) and
  writes one stable `empty.parquet` marker per real protocol path. No aggregate/placeholder venue remains anywhere in
  the write path — there is no fallback branch to fail fast from, because the four real venues are an explicit,
  complete, already-known constant list (the same one this file already used twice elsewhere), not a runtime guess.
- Also fixed a related correctness gap surfaced while making this change: the function previously stamped `available_at`
  using only `evm_attempted_at`, even for the Solana/MARINADE marker. It now uses `solana_attempted_at` for the MARINADE
  row and `evm_attempted_at` for the three EVM rows, matching `_record_empty_manifest`'s existing split exactly.
- Updated `tests/unit/test_lst_rates_handler_coverage.py::test_writes_empty_marker_and_records_zero_rows` to assert 4
  `upload_bytes` calls (one per real venue/chain path) and explicitly assert no `venue=LST/` path is ever written.
- Full `bash scripts/quality-gates.sh --no-fix` run: **7223 passed, 17 skipped, 1 xpassed, 0 failed**, coverage 80.46%
  (floor 79%), `QG_EXIT=0`. Not yet committed/shipped — pending an explicit shipping decision.

`/codex/02-data/honest-absence-downstream-handling.md:101-102` (writers should not emit physical zero-row placeholder
parquets at all, `record_empty()` is the manifest-only SSOT) was considered as an alternative, larger fix (remove the
physical marker write entirely) but was not applied here — the operator's instruction was specifically about eliminating
the fallback/default-venue behavior, not about removing the marker mechanism itself, and the `_write_empty_lst_marker`
docstring's original stated purpose ("so manifest-scans see this date") implies a GCS-scan consumer may depend on the
physical marker existing. Whether to also remove the physical write in favor of manifest-only absence is a separate,
larger architectural question left open.

## Wider sweep (this session) — is "scripted but not applied" systemic?

Mixed, not uniform:

- `plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md:215-222` — genuinely executed: operator ran the
  prod delete 2026-07-21, legacy prefixes verified at 0 objects.
- `plans/archive/issues/defi_lst_rates_migrated_marker_unfiltered_live_reader_2026_07_25.md:56-58` — a real fold-VM run
  (346/346, 0 flagged) but explicitly defers final purge to a still-active plan
  (`defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`).
- This doc's case — scripted, code shipped, but the delete/completeness-gate todos left unchecked and the dedicated
  cleanup tool stuck in dry-run for 4+ days.

So "marked ✅ DONE at the code layer, never actually applied/verified at the data layer" is a real, recurring failure
mode in this corpus, not a one-off. Separately, `venue=LST` is still flagged "ambiguous/suspicious" in
`VENUES_BY_ASSET_GROUP['defi']` as of `plans/audit/results/data_pipeline_reconciliation_defi_2026_07_24.md` FIND-05 (3
days before this doc) — i.e. the June migration did not fully retire the aggregate venue string from the live registry
either. Same report's FIND-04 flags a distinct but same-class defect (bare chain names `venue=ETHEREUM`/
`venue=POLYGON`, bounded to one historical day). `audits/data_quality_backfill_status_audit_instructions.md:145` (DQ-04,
OPEN) flags a third instance (`GAS_FEES`, a data_type, contaminating the venue axis). None of the UAC canonical-path
validators check venue against an enum (`_partition_path_canonicality.py` is structure-only) — this class of defect will
keep recurring silently until either the writer-side handlers are audited for hardcoded/wrong venue literals, or a
venue-vs-`VENUE_TO_ADAPTER_KEY` membership check is added to the canonicality oracle.

## Todos

- [x] ✅ [BACKEND] P2. **DONE 2026-07-29 — Shipped the fix.** The venue-hardcoding fix (4-real-venue loop, no fallback
      venue) is now committed — market-tick-data-service@5bf8a3c7. The separate architectural question (whether to
      remove the physical zero-row marker write entirely per
      `/codex/02-data/honest-absence-downstream-handling.md:101-102` in favor of manifest-only absence recording)
      remains genuinely open and out of this shipping todo's scope — not resolved here, left for a future decision.

**Note on `locked_by` — RESOLVED 2026-07-31**: this doc's frontmatter carried `locked_by: live-defi-rollout` /
`locked_since: 2026-05-21`, flagged here as a stale/invalid artifact (a branch name is not a valid locker identity, and
the lock date predated this doc's own `created: 2026-07-27`). The operator reviewed exactly this flag on 2026-07-30 and
ruled the lock invalid — cleared, and the doc archived. The architectural-question sub-item did NOT evaporate with the
archive: it is now a tracked `- [ ]` todo in `/plans/active/defi_consolidated_closeout_2026_07_18.md` § "Open
follow-ups".

## Provenance

Found 2026-07-27 answering an operator question about a specific GCS path; investigated via direct GCS inspection
(pyarrow row-count/schema check, full-range listing, bucket soft-delete-policy check) plus two parallel Explore agents
auditing the archived migration plan's execution evidence and sweeping for sibling venue-leak defects elsewhere in DeFi.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - 0 open checkboxes but a real prose-only open architectural
  question (remove the physical zero-row marker write entirely?); locked_by blocks archival
