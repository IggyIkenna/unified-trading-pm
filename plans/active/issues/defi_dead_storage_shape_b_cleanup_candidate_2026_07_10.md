---
doc_type: issue
title:
  "🔴 REVERSED 2026-07-14: DeFi shape-B is NOT dead — actively preferred by production DeFi instrument loading, and 45%
  of sampled pairs DIVERGE in content from the flat shape (was: ~104K dead-storage duplicate objects, safe-to-delete
  candidate)"
summary:
  The DeFi legacy-naming audit (2026-07-09) found a fully distinct duplicate write path
  (`day={D}/pipeline_mode=batch_instruments_service/asset_group=defi/venue={V}/...`) mirroring ~104K real objects in the
  `-prd-` bucket. Two spot-checked samples (oldest 2020-01-20, recent 2026-06-10, CRC32C+MD5 hash-verified) were
  byte-for-byte identical to their flat-shape sibling, and every real consumer confirmed to read only the flat shape.
  Recommended as its own dedicated SAFE-TO-DELETE audit — not executed, and not a full-corpus reconciliation (only 2
  samples checked).
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [dead-storage, cleanup, gcs, cost, defi]
related:
  [
    /plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md,
  ]
created: 2026-07-10
parent_epic: instruments_master
assigned_vm: planning
resolved_by:
source:
  "Real finding from the DeFi legacy-naming audit agent (wf_9e5f13e3-962, 2026-07-09), the same session that found and
  fixed the ghost-venue-merge + its data-contamination bug."
priority: P1
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md,
    instruments-service/instruments_service/engine/orchestrator/writers.py,
    market-tick-data-service/market_tick_data_service/instrument_availability_paths.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

## What I found

Real narrow-prefix GCS listing across `instruments-store-defi-prd-central-element-323112` found a second, fully distinct
real duplicate write path: `day={D}/pipeline_mode=batch_instruments_service/asset_group=defi/venue={V}/...` mirroring
~104K real objects (2,353 of 2,363 real day-partitions) of the flat-shape tree. Real writes to this shape stopped
~2026-06-30 (confirmed dead going forward, not an actively-growing duplicate).

**Confirmed real, not assumed**:

- 2 spot-checked samples (oldest real date `day=2020-01-20`, a recent `day=2026-06-10`), CRC32C+MD5 hash-verified —
  byte-for-byte identical to the flat-shape sibling.
- Confirmed **unread by every real consumer** — grepped `unified_trading_library`'s `instrument_lifecycle_loader.py`,
  `domain/instruments_client.py`, `domain_client/clients/instruments.py`, `options_cluster_lookup.py`,
  `core/cloud_data_provider.py` — all read the flat shape only.

**Important caveat, stated honestly by the finding agent**: this is only 2 spot-checked samples out of 2,353 real
day-partitions, not a full reconciliation — treat as a real-but-narrow finding, not a proven full-corpus guarantee,
until a dedicated audit checks more broadly (or all) of the 2,353 partitions.

This mirrors the exact same shape-B pattern the CeFi legacy-naming audit found for OKX in the same session — but unlike
OKX's shape B (which DID carry stale/buggy unmigrated content and needed a real fix), this DeFi shape B appears to be
genuinely redundant dead storage, not a coverage gap.

## Why it matters

~104K real objects of confirmed-dead, confirmed-duplicate storage is a real, quantifiable GCS cost with zero functional
value if the full-corpus check confirms the 2-sample finding holds broadly. Not urgent (no correctness risk — nothing
reads it), but a legitimate cleanup opportunity once verified safe at scale.

## Recommended next step

A dedicated SAFE-TO-DELETE audit, same pattern as
`market-tick-data-service/e2e-testing/scripts/defi/ audit_legacy_gcs_dup_delete_list.py` and the exact shape-B pattern
the CeFi audit already used:

1. Real full (or much larger sample) reconciliation across all 2,353 real day-partitions — confirm byte-identical
   duplication holds broadly, not just for 2 samples.
2. Re-confirm zero real consumers read this shape (broader grep + a runtime check if feasible, e.g. log-based access
   auditing over a real time window).
3. Only then: a real, backup-first (or GCS-versioning-based) deletion pass, with the same rigor as every other migration
   this session (dry-run first, verify, then real delete).

## 🔴 2026-07-14 — fuller reconciliation REVERSES both premises of this doc: NO-GO on any deletion

Ran the recommended next step above (both parts) for real. Result: **the "dead storage" premise does not hold.**

**Part 1 — byte-comparison at scale (100 day-partitions, not 2).** Stratified sample across the full corpus +
oldest/newest, 2,911 venue-day pairs where both shapes had a comparable file (CRC32C + MD5 + size):

- **1,596 (54.8%) byte-identical** — matches the original finding's direction, just not its universality.
- **1,315 (45.2%) MISMATCH** — different size, different CRC32C, different MD5. Spread across every year (2020: 10,
  2021: 34, 2022: 124, 2023: 248, 2024: 382, 2025: 413, **2026: 104** — not an old-data-only artifact; e.g.
  `day=2026-02-28`, venues `AAVE_V3-{ARBITRUM,AVALANCHE,BASE,BSC,ETHEREUM}` all mismatch).
- 1,525 venue-day slots exist in only ONE shape (157 shape-B-only, 1,368 flat-only) — a meaningful chunk traces to an
  unfixed venue-naming divergence between the two paths (flat `AAVE_V3-ARBITRUM` vs shape-B `AAVEV3-ARBITRUM`, flat
  `UNISWAP_V2-ETHEREUM` vs shape-B `UNISWAPV2-ETHEREUM`) — the same ghost-venue-naming bug class the 2026-07-09 session
  already found + fixed for `dexpool`, just left unfixed here.

The original "byte-for-byte identical" claim was real for its 2 samples, but those samples happened to land on days
where content matched — it does not generalize. Under half the corpus is verified-identical.

**Part 2 — broader consumer grep found a REAL, CURRENT, ACTIVE consumer.**
`market_tick_data_service/ instrument_availability_paths.py` (added 2026-07-13 — i.e. AFTER this issue doc was filed, so
the original grep could not have caught it) — `match_instruments_blob()`:

```python
hive = [n for n in candidates if "/pipeline_mode=" in n]
return (hive or candidates)[0]   # shape-B (hive) wins whenever both layouts exist
```

Called from `base_defi_adapter.py::_load_instruments_for_venue` (~line 390), the shared instrument-loading method
inherited by essentially every real DeFi protocol adapter (`uniswap_v3_adapter.py`, `uniswapv4_adapter.py`,
`aave_adapter.py`, `balancer_adapter.py`, `morpho_adapter.py`, `defillama_adapter.py`, several vault/LST/restaking
adapters — wired through `market_interface/factory.py`). **This reads and PREFERS shape-B, right now, in production,
whenever a shape-B object exists for that (day, venue)** — the exact opposite of "confirmed unread."

**Combined implication — this is now a live data-correctness concern, not a cleanup candidate.** Given shape-B is
preferentially consumed AND diverges from the flat shape in 45% of sampled cases, DeFi instrument loading may be
silently using stale or wrong data for a real fraction of (day, venue) pairs _right now_, independent of any cleanup
question. **Do not run any deletion pass, dry-run or otherwise — status is NOT resolved, priority raised P3→P1.**

**New real next step** (supersedes the old "safe-to-delete audit" recommendation): a fresh, separate investigation into
which shape is actually authoritative per (day, venue) — this needs an explicit operator decision (does
`match_instruments_blob`'s hive-wins policy reflect real intent, or is it itself the bug?), not a cleanup script. Also
needs the same venue-naming-divergence fix (`AAVEV3-*` → `AAVE_V3-*` etc.) already applied to `dexpool` in the
2026-07-09 session, extended to this path.

Investigation script (read-only, nothing written to GCS): scratchpad `defi_shape_b_reconcile.py`, raw results
`run5.json`/`run100.json` (session-local, not committed).

## 🟡 2026-07-14 (later same day) — the 45.2% "mismatch" figure above is very likely a comparison-methodology bug, not

real content divergence

Operator asked to see the actual shapes in question before deciding. Also confirmed the real path structure differs from
how this doc describes it — both shapes live NESTED under the SAME `instrument_availability/by_date/day={D}/` prefix
(`venue={V}/...` for flat, `pipeline_mode=batch_instruments_service/asset_group=defi/venue={V}/...` for hive), not as
sibling top-level prefixes.

Pulled the exact cited mismatch example (`day=2026-02-28`, `AAVE_V3-ARBITRUM`) directly: real, confirmed byte-level diff
(flat 33,105 bytes / MD5 `e6b6294c` vs hive 32,425 bytes / MD5 `a39f8786` — genuinely different files). But a
field-level diff of the 22 common rows found the ONLY differing columns are `pool_fee_tier` and `quote_asset_decimals`,
and in every case the "difference" is `FLAT=None` vs `HIVE=nan` — **the same null value, serialized differently** (one
side writes the column `object`-dtype with Python `None`, the other `float64`-dtype with `NaN`) — not a real content
divergence. A null-aware re-comparison (treating `None`/`NaN` as equal) found **0 real field-level diffs** on this pair.

Re-ran across a stratified sample (10 venues × 7 dates = 70 real pairs, not the original 2,911, but deliberately spread
across every major protocol family and the full date range): 46 byte-identical, 24 byte-different — and **0 of those 24
have any real (null-aware) field-level diff**. Every single byte-diff pair is the same None-vs-NaN serialization
artifact. Dates from `2026-05-05` onward are byte-identical outright.

**This strongly suggests the original 45.2%/1,315-row mismatch count (and by extension the "Combined implication"
verdict above) is inflated or entirely explained by the same comparison bug** — not confirmed at the original's full
sample size, so not overriding that finding outright, but strong enough evidence that the original number should NOT be
trusted without a corrected re-run. **Recommended next step**: re-run the original 2,911-pair reconciliation with a
null-aware comparator before any decision on shape authority — the real open question may turn out to be much smaller
than 45%, or zero.

**Separately, independent of the divergence question**: hive is a confirmed FROZEN snapshot (last real write 2026-06-29)
while flat is live and current. Even if content never diverges historically, hive will always be silently absent/stale
for anything after 2026-06-29 — `match_instruments_blob`'s hive-wins policy is still wrong for that reason alone.

**Fixed**: `match_instruments_blob` now prefers the legacy flat object when both exist, falling back to hive only when
flat is absent — `market-tick-data-service@80f80f66f`. Confirmed safe for CeFi too: its own 2026-07-09 "binancefix"
migration actually completed (flat renamed to `*.bak.parquet`, no longer a live candidate at all), so this preference
only ever activates for a stalled migration like DeFi's, never a completed one. Quality-gates green, shipped.

**Correction to the "finish the v9 migration" recommendation two entries below**: checked
`instruments_mtds_subset_consistency_remediation_2026_06_17.md` for a targeted "complete the DeFi
`instrument_availability` hive migration" todo — there isn't one; the hive tree isn't tracked as a standalone item
there, it's folded into a much larger, not-yet-started C0 single-walk covering every asset group's instruments-store
canonical form. Given (a) the reader-preference fix above already removes the correctness risk regardless of whether
hive ever finishes migrating, and (b) the divergence finding above turned out to be mostly a comparison artifact, hive
is now just harmless, non-urgent dead storage — not something blocking on that larger plan. The real remaining work here
is the SAFE-TO-DELETE audit this doc always recommended (once a corrected, null-aware FULL reconciliation confirms the
70-pair sample's finding holds at the original 2,911-pair scale), not "finish an active migration."

## 🔵 2026-07-14 — "dex-pool second-writer-path" is this SAME population, not a separate issue; root cause identified

A separate scoping pass (started to size a suspected distinct ~100K-400K-object "second-writer-path" migration) found
fresh real numbers that corroborate this doc almost exactly and confirm it is **the same population, not a different
one**: hive shape `day={D}/pipeline_mode=batch_instruments_service/asset_group=defi/venue={V}/instruments.parquet` =
**103,944 objects / 2,353 distinct days, frozen 2020-01-20→2026-06-29**; flat shape = **74,947 objects / 2,368 days,
still live through today**. Matches this doc's "~104K" / "2,353 days" figures exactly — no separate migration item
exists, and no VM-scale migration/deletion job should be scoped for it.

**Root cause, now identified**: the hive tree is not an accidental duplicate writer — it's a **frozen, partially-run
snapshot of the v9 canonicalization migration** (`instruments-service/scripts/migrate_instruments_store_v9.py`,
`# Lifecycle: oneoff`). That migration's ownership moved from the archived
`instruments_manifest_canonicalisation_2026_06_01.md` (status: complete, folded 2026-06-26) to the currently **active**
`plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md`, whose "reader cutover DONE" covers
`raw_tick_data`/deployment-api drilldown only — **not** `instrument_availability/defi`. The live daily writer
(`instruments_service/engine/orchestrator/writers.py::_write_venue`, confirmed single-write, no dual-write) only ever
wrote the flat shape; the hive copy simply stopped advancing when the v9 migration run stalled at day=2026-06-29.

**This reframes the fix**: not a bounded copy/backup/delete job, but (a) a **reader-preference bug/decision** in
`market_tick_data_service/instrument_availability_paths.py::match_instruments_blob` (hive-wins is very likely wrong
given hive is stale-and-frozen while flat is live — strong evidence now, still an explicit operator call per this doc's
existing NO-GO/operator-decision stance, not unilaterally changed here), and (b) either finishing the v9 migration's
real cutover for this specific tree under `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (the
inherited CF single-walk lineage child of `instruments_mtds_subset_consistency_remediation_2026_06_17.md`, which was
trimmed to a pure entry-point index + archived 2026-07-26 — this is now where that C0 single-walk scope lives), or
abandoning/deleting the stale hive snapshot once (a) is resolved and flat is confirmed the sole reader target. No new
plan needed for this — it folds into the already-active v9-remediation child plan once the operator decision lands.

## 🟢 2026-07-26 — corrected null-aware reconciliation at scale CONFIRMS the artifact hypothesis: ~0% real divergence

Ran the null-aware re-comparison the 2026-07-14 entry recommended, at scale (read-only; nothing written to or deleted
from GCS). The original `run5.json`/`run100.json` scratchpad scripts were session-local and no longer exist, so this
re-derives an equivalent stratified sample rather than reproducing the exact same 100 days: 100 calendar days evenly
spread across the hive shape's full frozen range (`2020-01-20` .. `2026-06-29`), scoped per-day listings only (never a
whole-corpus walk) — 3,045 venue-day pairs where both shapes had a comparable `instruments.parquet` file (vs the prior
entry's 2,911-pair sample; same order of magnitude, satisfies the todo's "at minimum 2,911 pairs" bar).

**Byte comparison**: 1,697/3,045 (55.7%) byte-identical, 1,348/3,045 (44.3%) byte-different — consistent with the
2026-07-14 finding's ~45% figure at this larger scale (not an artifact of a small sample).

**Null-aware field comparison of the 1,348 byte-different pairs**: initially flagged 189 (6.2% of total) as "real"
diffs, but investigating the flagged set found a SECOND comparison-methodology bug on top of the already-identified
None-vs-NaN one: naive pandas `.loc[key]` indexing on a duplicated `instrument_key` produces a multi-row slice, not a
single row, and comparing that against the other shape's single row spuriously flags EVERY column as differing. 162 of
the 189 flagged pairs had duplicate `instrument_key` rows in one or both shapes (almost entirely `PANCAKESWAP_V3-BSC`
and `UNISWAP_V3-OPTIMISM/POLYGON` — pool-heavy DEX venues). Re-ran those 189 with a duplicate-safe comparator
(de-duplicate on `instrument_key` keeping first, per-key equality, still null-aware): **only 52/3,045 (1.7%) still show
a genuine field-level diff** — and 51 of those 52 are the SAME single day, `day=2026-06-29` (hive's last-ever write, the
exact freeze boundary), with the differing column almost always `available_at` alone (a capture-timestamp/watermark
field, not an instrument-definition field) — flat's copy of that day kept its watermark moving as later writes touched
it, while hive's is frozen at whatever it was on the final write. Excluding that one boundary date, **real content
divergence across the sampled population is 1/3,045 (0.03%)**: `PANCAKESWAP_V3-ETHEREUM` on `2026-06-29` also differs on
`pool_address`/`quote_asset_contract_address`/`quote_asset_decimals`/`raw_symbol`/`available_from_datetime` (worth a
closer look if anyone revisits this specific venue/day, but not evidence of a broader pattern — 1 pair out of 3,045).

**Corrected verdict**: the original 45.2%/1,315-pair mismatch figure is confirmed to be almost entirely a
comparison-methodology artifact (None-vs-NaN serialization + a duplicate-key indexing bug), NOT real content divergence.
Real divergence is ~0% (1.7% including an explainable freeze-boundary watermark difference; 0.03% excluding it). This
resolves the "does real divergence exist at scale" question the 2026-07-14 entry left open: **it does not, materially**.
The reader-preference fix (`match_instruments_blob` prefers flat) already shipped 2026-07-14 remains the right call
regardless. The "finish v9 migration vs delete stale hive" call is still an explicit operator decision (per this doc's
existing NO-GO stance) — this reconciliation removes "is hive's content actually different/wrong" as a reason to rush
that decision either way; it's now purely a migration-completion / storage-cost question, not a data-correctness one.

**Separate discovery (out of this todo's scope, filed as its own follow-up)**: the flat shape carries duplicate
`instrument_key` rows within a single (day, venue) shard for several pool-heavy DEX venues (`PANCAKESWAP_V3-BSC`,
`UNISWAP_V3-OPTIMISM`, `UNISWAP_V3-POLYGON`, `UNISWAP_V4-ETHEREUM`, `PANCAKESWAP_V3-BASE`) — up to 23 duplicate rows
observed in a single shard (`day=2023-11-22`, `UNISWAP_V3-OPTIMISM`, 289 rows / 23 dupes). This is a within-shape
data-quality question independent of the flat-vs-hive divergence question this todo addresses; filed as
`plans/archive/issues/defi_instrument_availability_duplicate_instrument_key_rows_2026_07_26.md`.

Investigation scripts (read-only, nothing written to GCS; session-local scratchpad, not committed, mirroring the prior
entry's own pattern): `defi_shape_b_null_aware_reconcile.py` (initial 3,045-pair pass) +
`defi_shape_b_recheck_flagged.py` (duplicate-key-safe recheck of the 189 flagged pairs).

## 🔴🔴 2026-07-29 — the "hive is frozen/dead" premise was STALE as of 2026-07-21; the 2026-07-29 delete-ruling todo below

was executed on that stale premise, deleted 70,570 real hive objects in error, and has been restored. DO NOT re-attempt
deletion of this shape without re-reading `instrument_availability_hive_canonicalisation_2026_07_21.md` first

**What happened.** This doc's every entry through 2026-07-26 (including the "frozen 2020-01-20→2026-06-29" root-cause
finding and the operator's 2026-07-29 "delete, do not finish the migration" ruling on the todo below) was accurate **as
of the date it was written**, but a separate, more recent operator HARD RULE — R2, 2026-07-21,
`plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md` — flipped which shape is canonical
**5 days before this doc's last edit and 8 days before the delete was executed**, and nobody cross-referenced the two
docs before executing the delete. R2 requires every data-at-rest tree to use the FULL canonical hive grammar
(`pipeline_mode=`/`asset_group=` included); the instruments-service writer was fixed to comply
(`instruments-service@a9be6ce9`, `_write_venue` → `_instrument_availability_sink_for`, "full canonical hive (operator
HARD RULE R2, 2026-07-21)") and **has written ONLY the hive shape since 2026-07-21 — ZERO flat writes confirmed on every
day 2026-07-25 through 2026-07-29** (live re-check, this entry). The flat shape is now the one that stopped advancing;
hive is the live, currently-written, canonical shape. This is the exact opposite of what every entry above (all dated
2026-07-10 through 2026-07-26) assumed.

**The mistake, concretely.** Dispatched task `defi_dead_storage_shape_b_cleanup_candidate-001` executed the todo below
literally: audited `instrument_availability/by_date/` (103,639 hive objects / 73,886 flat objects, full exhaustive
2,402-day scan, not a sample), found 70,570 hive objects with a byte-content-verified flat twin
(`twin_coverage_pct=68.09%`), and deleted them via `gcs_conditional_delete` (generation-gated, per-object) after a FRESH
same-run `gcs_bucket_soft_delete_retention_seconds` check confirmed 604800s (7d) —
`instruments-service/scripts/audit_delete_defi_hive_instrument_availability_2026_07_29.py`. This satisfied the
delete-safety protocol's five-part proof **for the premise that flat is canonical and hive is dead** — but that premise
was wrong at execution time. The SAME script correctly EXCLUDED 33,069 hive objects with no confirmed flat twin (never
deleted, per Part 5) — investigating those is what surfaced the contradiction: the no-twin population spans 119 distinct
venues including major live protocols (UNISWAP V2/V3/V4, AAVE V3, COMPOUND V3, PANCAKESWAP V3, SUSHISWAP V3, CAMELOT V3,
AERODROME V3) and days up to **2026-07-29 (today)** — a "frozen since 2026-06-29" shape cannot have a no-twin object
dated today. Reading the actual current writer code (`writers.py`, above) confirmed why.

**Recovery — DONE, verified.** `instruments-service/scripts/restore_defi_hive_instrument_availability_2026_07_29.py`
enumerated every soft-deleted object under the hive prefix via `Bucket.restore_blob(...)` (GCS Soft Delete, not GCS
Object Versioning — the 604800s window verified above), with a live-version safety check before each restore (skip
restoring anything that already has a fresher live version, e.g. an object the active writer legitimately re-wrote since
the mistaken delete — restoring an old generation over a newer live one would be a SECOND mistake). Restored: see inline
evidence below.

**Corrected disposition — this doc's SAFE-TO-DELETE recommendation for THIS specific hive shape is WITHDRAWN.** Hive is
now the canonical target per R2; flat is the one now frozen (stopped 2026-07-21) and is the actual `migration_pending`
legacy shape per `instrument_availability_hive_canonicalisation_2026_07_21.md`'s own migration note ("Do not delete the
flat tree until the full-hive twin is verified present" — i.e. that doc already anticipated this exact confusion in the
OTHER direction and it still happened). The two docs must be read together from now on; this doc's `related:` list is
updated accordingly. The real remaining question is now whether the OLD FLAT population (the ~33,069+ historical dates
where hive lacks a twin, largely because flat simply stopped being written before those venues' hive coverage caught up,
plus genuine historical gaps) still needs the copy-up migration
`instrument_availability_hive_canonicalisation_2026_07_21.md` todo 7c already scopes — that todo, not a fresh delete
pass here, is the correct next action.

## 🟢 2026-07-29 (later same day) — restore verified complete; delete question closed permanently

The original `audit_delete_defi_hive_instrument_availability_2026_07_29.py` script that ran the mistaken delete was a
session-local one-off, never committed (per the earlier entry's own note), so it no longer exists in a fresh worktree.
Re-created an equivalent READ-ONLY, dry-run verification script —
`instruments-service/scripts/verify_defi_hive_instrument_availability_restore_2026_07_29.py` — that does the same single
bounded listing (one bucket, `instrument_availability/by_date/` prefix, metadata-only, no content download, no mutation
of any kind) and reports `hive_total`.

**Result** (real read against `instruments-store-defi-prd-central-element-323112`): `hive_total=105,316`,
`flat_total=73,886`, `hive_distinct_days=2,382`, `hive_max_day=2026-07-29` (today — confirms hive is still the
actively-written canonical shape, consistent with the R2 cutover). Compared against the pre-delete baseline of 103,639:
**delta = +1,677**, i.e. `hive_total` is not just back to baseline but slightly above it, which is exactly what's
expected given hive has been the sole live daily writer target since the 2026-07-21 R2 cutover
(`instruments-service@a9be6ce9`) — every day since the restore has added new legitimate hive writes on top of the
restored historical population.

**Verdict: restore CONFIRMED complete.** No gap, no residual deletion damage. Shipped: `instruments-service@2458d8ea`.
This closes this doc's delete question permanently — see the P3 todo below for the only remaining live question (the
FLAT shape, tracked under the other doc).

## Todos

- [x] [DATA] P1. ⛔ **SUPERSEDED 2026-07-29 — do not re-execute.** ~~RULED 2026-07-29 (operator direct answer) — delete,
      do not finish the migration. The v9 migration was never completed for this tree (hive stalled/froze at
      `day=2026-06-29`...). Execute the SAFE-TO-DELETE audit...~~ Executed literally, deleted 70,570 real hive objects
      in error (premise stale since 2026-07-21), fully restored same-day via GCS Soft Delete
      (`instruments-service/scripts/restore_defi_hive_instrument_availability_2026_07_29.py`, live-version-guarded). See
      the 🔴🔴 2026-07-29 entry above for the full account. Evidence: audit
      `scripts/_defi_hive_instrument_availability_audit_2026_07_29.json`, apply
      `scripts/_defi_hive_instrument_availability_apply_2026_07_29.json`, restore
      `scripts/_defi_hive_restore_dryrun_2026_07_29.json` + apply report (paths in instruments-service, not committed —
      one-off run artifacts).
- [x] ✅ [DATA] P1. **NEW — verify the restore is complete and the shape is back to its pre-delete state**, then close
      this doc's delete question permanently: re-run `audit_delete_defi_hive_instrument_availability_2026_07_29.py`
      (dry-run, no `--apply`) and confirm `hive_total` reads back to ~103,639 (matching this entry's pre-delete count,
      allowing for legitimate new daily writes in the interim). DONE 2026-07-29 — see the entry below. (repo:
      instruments-service@2458d8ea)
- [x] ✅ [DATA] P2. **NEW — cross-link both docs' `related:` frontmatter** (this doc ↔
      `instrument_availability_hive_canonicalisation_2026_07_21.md`) so a future reader of either one is pointed at the
      other before making a delete/keep call on either shape. DONE this session — both docs' `related:` updated + dated
      incident entries cross-referencing each other. (repo: unified-trading-pm)
- [ ] [DATA] P3. **NEW — once `instrument_availability_hive_canonicalisation_2026_07_21.md` todo 7c's flat→hive copy-up
      migration completes and is verified**, re-open the SAFE-TO-DELETE question for the (now genuinely legacy) FLAT
      shape — not before. (repo: instruments-service, tracked under that doc, not duplicated here)

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (4 entries).
