---
doc_type: issue
title: Phantom captures — cefi manifest (2026-06-28)
summary: "Manifest: `gcp://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`"
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest, cefi, phantom-captures, data-correctness, backfill, data-status, single-walk]
related: [mvp_backfill_cefi_tick_v10_2026_06_27]
created: 2026-06-28
parent_epic: observability_master
priority: P2
source: [reconcile_phantom_manifest_rows_all.py, mvp_catalogue_finalization_v10_2026_06_27.md (G3 phantom audit task)]
assigned_vm: NA
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
locked_since: 2026-05-21
---

# Phantom captures — cefi manifest (2026-06-28)

> Auto-filed by the G3 phantom-manifest audit (`reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run`)
> run during Phase-0 catalogue finalization. Found 13,404 `capture_status=captured` rows in the MTDS cefi manifest
> (`market-data-tick-cefi-prd-central-element-323112/_index/`) with no backing GCS parquet. These are NOT
> catalogue-shape (they are market-data tick records, not instrument definition files) → issue doc per plan triage rule.

## What I found

Manifest: `gcp://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`

- Manifest rows total: 5,037,888
- Captured rows in scope: 2,794,416
- Unique (date, venue[, chain], hive-vocab) prefixes: 260,520
- **Real captures (parquet exists):** 2,781,012
- **Phantom captures (captured → no parquet):** 13,404 ← will flip to `attempted_failed` on `--apply`

Triage JSONL: `gs://central-element-323112-phantom-triage/triage_cefi_20260628_021110.jsonl` (13,404 records)

Phantom distribution by data_type:

| data_type         | phantom count |
| ----------------- | ------------- |
| (blank)           | 9,757         |
| trades            | 2,522         |
| book_snapshot_5   | 490           |
| derivative_ticker | 401           |
| futures_chain     | 223           |
| liquidations      | 9             |
| options_chain     | 2             |
| **TOTAL**         | **13,404**    |

Phantom distribution by venue (top 15):

| venue           | phantom count |
| --------------- | ------------- |
| BYBIT           | 1,993         |
| UPBIT           | 1,824         |
| BINANCE-FUTURES | 1,778         |
| OKX-SWAP        | 1,740         |
| HYPERLIQUID     | 1,628         |
| BINANCE-SPOT    | 1,519         |
| OKX-SPOT        | 863           |
| COINBASE-SPOT   | 852           |
| DERIBIT         | 669           |
| OKX-FUTURES     | 419           |
| BYBIT-FUTURES   | 45            |
| (blank)         | 34            |
| KRAKEN-FUTURES  | 20            |
| COINBASE        | 7             |
| OKX             | 7             |

Notable: blank data_type (9,757 = 72.8% of phantoms) likely represents pre-v9 schema rows where `data_type` was
null/empty. These may be pre-schema-migration historical captures.

## Why it matters

13,404 phantom rows (0.48% of captured scope) mean the cefi availability signal overstates actual data. The cefi
backfill plan (`mvp_backfill_cefi_tick_v10_2026_06_27.md`) will re-run coverage analysis; these phantoms will show as
gaps and the backfill will attempt to fill them — which is correct behavior but should be preceded by flipping them to
`attempted_failed` to keep manifest state honest.

## Recommended decision

1. **Apply fix before cefi backfill**: `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi` (no
   `--dry-run`, with `MANIFEST_PER_VM_SHARDS=true VM_NAME=cefi-reconcile` per consolidator-SSOT) to flip 13,404 phantoms
   to `attempted_failed`. Do this BEFORE the cefi backfill G0 gap analysis.
2. **Diagnose blank data_type (9,757)**: confirm these are pre-v9 schema rows; cross-check the manifest hygiene script's
   `schema_version_not_v9: 349,861` finding from `manifest_hygiene_red_2026_06_28.md`.
3. Reference triage JSONL at `gs://central-element-323112-phantom-triage/triage_cefi_20260628_021110.jsonl`.

Cold-start context: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` +
`codex/05-infrastructure/manifest-consolidator-ssot.md` + `codex/02-data/availability-manifest-and-data-status.md`.

## Todos

- [ ] [SCRIPT] P1. Apply cefi phantom reconciliation (372 rows → `attempted_failed`) after CeFi wave-1 VMs complete.
      **Re-dry-run 2026-06-28T04:31Z (slot-10):** phantom count is NOW **372** (not 13,404 — prior count had false
      positives due to stale UAC path template coverage; `canonical_path_templates` update resolved 13,032 rows). All
      372 real phantoms are HYPERLIQUID: `derivative_ticker`=170, `book_snapshot_5`=114, `trades`=88. Triage JSONL:
      `gs://central-element-323112-phantom-triage/triage_cefi_20260628_043158.jsonl`. **When to run --apply:** AFTER
      wave-1 VMs (BINANCE/OKX/BYBIT/COINBASE-SPOT/UPBIT 2025+2026) reach TERMINATED state. Running while VMs are active
      risks overwriting the consolidator's shard merges (race condition on main index). Command:
      `GCP_PROJECT_ID=central-element-323112 .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi`
      Repo: `instruments-service`.
- [x] ⚠️ [CODE] P2. Diagnose blank data_type phantoms (9,757): **CORRECTED 2026-07-15 — this claim was INCOMPLETE, not
      confirmed false.** See the 2026-07-15 investigation section below for full evidence. Summary of the correction:
      the "0 remaining, false positive, no code change needed" verdict was based ONLY on the 04:31Z re-dry-run finding
      no NEW blank-data_type candidates among rows still in `capture_status=captured` — it never verified what happened
      to the ORIGINAL 9,757 candidates. Live evidence (2026-07-15) shows they were flipped `captured`→`attempted_failed`
      by an **undocumented `--apply` run at 2026-06-28T03:12:34Z** (not either of the two logged dry-runs) using the
      STALE pre-fix templates, and have sat as `attempted_failed` with
      `error_reason=phantom_captured_no_parquet_at_canonical_path` ever since — never re-validated via `--unphantom`.
      The "0 remaining" the 04:31Z dry-run saw was simply because these rows had already left the `captured` population
      it scans, not because they were confirmed to have real parquet. — instruments-service (original: slot-10
      2026-06-28T04:31Z; correction: 2026-07-15 investigation, see below)

## 2026-07-15 corroboration — ⚠️ POSSIBLE CONTRADICTION, exact count 9,757 reappears live 17 days after "RESOLVED"

Triaging a `#data-pipeline-alerts` `DP_RUN_MOSTLY_EMPTY` batch (window 2026-07-14 23:50Z–2026-07-15 00:19Z) turned up a
cefi cell described only as "blank/empty data_type" at **9,757/9,757 attempted_failed (100.0%)** against
`market-data-tick-cefi-prd-central-element-323112`. That count is **byte-identical** to this doc's original 2026-06-28
finding ("blank data_type (9,757 = 72.8% of phantoms)") — which the very next todo above claims was fully RESOLVED as a
false-positive of the phantom-audit tool's `canonical_path_templates` coverage, re-verified down to **0** phantoms the
same day.

This is flagged, not re-diagnosed (read-only manifest-count triage only, no live GCS/manifest query run in this pass) —
but the exact-match recurrence 17 days later is suspicious enough to be worth a real look, for one of a few reasons,
none of them mutually exclusive:

1. The 2026-06-28 fix only re-verified the **phantom-audit tool's own dry-run classification** (i.e., confirmed the TOOL
   no longer flags these 9,757 rows as false-positive phantoms) — it may never have touched whatever ALREADY-WRITTEN
   `attempted_failed` rows exist in the live manifest with a genuinely blank `data_type`. If so, "0 phantoms" and "9,757
   attempted_failed with blank data_type" can both be true simultaneously (the tool stopped mis-flagging CAPTURED rows
   as phantom-captured, but a separate, real population of blank-`data_type` `attempted_failed` rows was never addressed
   and is exactly what the alert's `DP_RUN_MOSTLY_EMPTY` check is now surfacing).
2. Alternatively, a coincidentally-identical count from an unrelated, newly-recurring cause (e.g., a writer regressing
   back to emitting blank-`data_type` rows, mirroring the tradfi CF-7 "aggregate Tier-1 sentinel writer" pattern
   documented in `tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md`, which found and killed an analogous
   tradfi writer bug).
3. The DP_RUN_MOSTLY_EMPTY alert's "blank/empty data_type" label may not be measuring the same manifest slice this doc's
   `data_type` column phantom-count measured (worth confirming the alert's query definition before assuming (1) or (2)).

**Recommend**: a live re-query of the cefi manifest for
`capture_status='attempted_failed' AND (data_type='' OR data_type IS NULL)` to get a fresh count + venue/date breakdown,
and diff it against this doc's original `triage_cefi_20260628_021110.jsonl` / `triage_cefi_20260628_043158.jsonl` triage
JSONLs to determine which of the 3 explanations above actually holds. Given this doc's own 2026-06-28 resolution claimed
0 remaining and the live alert count now exactly matches the pre-fix number, this reads as a genuine data-correctness
discrepancy worth operator visibility, not routine triage noise — surfacing per the workspace's "big finding" rule (a
"resolved" checkbox whose claimed end-state doesn't hold in production).

## 2026-07-15 investigation — VERDICT: Hypothesis 1 confirmed (refined) + a corrected root cause; NOT a live writer

## regression; NOT a query-definition mismatch

Live, read-only query against the ALREADY-CONSOLIDATED cefi manifest index
(`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, read via UTL
`read_availability_index(bucket, columns=[...])` slim column-pushdown path — single read, no fresh GCS corpus walk, per
the single-walk discipline HARD RULE). Total index: 7,565,995 rows.

**Detector cross-check (rules out Hypothesis 3 — query-definition mismatch).** Read
`deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py` `_read_attempted_failed_cells` (lines
539-598) — the `DP_RUN_MOSTLY_EMPTY`/`check_high_attempted_failed` detector's EXACT query: reads only
`["capture_status", "data_type"]`, groups by `data_type.astype(str)` (exact-string groupby, blank `""` is its own
group), and for each group counts `capture_status=='captured'` vs `=='attempted_failed'`. Reproducing this exact groupby
live: `data_type=''` → `captured=0, attempted_failed=9,757, ratio=100.0%` — this is a byte-exact match to the alert. The
alert's "blank/empty data_type" cell IS measuring the identical predicate this doc's original phantom count measured.
**Hypothesis 3 ruled out.**

**Live population characterization (rules out Hypothesis 2 — live writer regression).** The 9,757 rows matching
`capture_status='attempted_failed' AND data_type blank/null`:

- `attempted_at`: **a single literal timestamp for ALL 9,757 rows** — `2026-06-28T03:12:34.851168+00:00`. Nothing has
  touched this population since. This timestamp falls BETWEEN the doc's two logged dry-runs (02:11:10Z and 04:31:58Z) —
  meaning an **undocumented `--apply` run executed at 03:12:34Z**, not captured in this doc's narrative.
- `error_reason`: 100% `phantom_captured_no_parquet_at_canonical_path` — the literal string
  `reconcile_phantom_manifest_rows_all.py`'s forward `--apply` pass writes (confirmed at script line 1420). This proves
  these rows were flipped `captured`→`attempted_failed` BY the phantom-reconcile tool's forward pass, not by MTDS or any
  other live writer.
- `written_at` (i.e., when the row was originally written as `captured`, before the flip): clustered entirely in
  **2026-04-06 to 2026-04-20** (2,141 rows at one exact instant 2026-04-06T02:20:55Z, the rest individually stamped
  through 04-19/04-20) — while the shard `date` values these rows describe span **2019-03-30 to 2026-04-17**. A tight
  April-2026 write window covering seven years of historical dates is the signature of a **backfill/migration/
  consolidation batch job**, not organic day-by-day capture. `pipeline_mode` and `source` are **100% `None`** on all
  9,757 rows — both are mandatory-populated fields under the current v8/v9 schema, so these rows were written by
  something that predates or bypasses that schema enforcement.
- **No new blank-data_type rows have appeared since 2026-06-28** (single frozen `attempted_at`) — this rules out a
  live/currently-running writer regressing back to blank `data_type` (Hypothesis 2's tradfi-CF7-style precedent).

**Root-cause refinement (why the 06-28 "false positive, RESOLVED" framing was wrong).** Two further checks:

1. The forward-audit's own matching logic (`_audit_generic`, script lines 400-530) builds the on-disk match needle as
   `dt_needle = f"data_type={data_type}/"`. For a row with a blank `data_type`, this needle is literally `"data_type=/"`
   — a path segment that **can never exist** on any real GCS object (every real write always carries a non-blank
   `data_type` in its hive path). So **any `captured` row with a blank/corrupt `data_type` is unconditionally,
   permanently flagged phantom by this tool regardless of whether real data exists** — this is a structural blind spot
   in the audit tool for corrupt-`data_type` rows, not proof the underlying data is missing. The 06-28
   "canonical_path_templates fix resolved these to false positives" explanation was never actually true for this
   population; a template-coverage fix cannot help a query that's matching against a value that never appears on disk by
   construction.
2. Cross-referencing the 9,757 blank rows' `(date, venue)` pairs against the SAME live manifest for a properly-typed
   `captured` row on the same day+venue: **9,658 of 9,757 (99.0%) already have a separate, correctly-typed `captured`
   row for that exact (date, venue)** elsewhere in the manifest. Only 99 pairs (all early-2019 `DERIBIT` dates,
   plausibly pre-genesis/no-data) have no captured counterpart at all. **This means the blank-`data_type` row is, for
   99% of the population, a redundant/orphan duplicate sitting alongside data that is already correctly captured** — not
   evidence of 9,757 shards of genuinely missing market data.

**Verdict**: Hypothesis 1 holds (old rows, not a live regression), refined with a corrected root cause the original doc
got wrong. These 9,757 rows are **stale, malformed duplicate manifest entries** — written by an unidentified April-2026
backfill/migration/consolidation process that stamped historical dates with a blank `data_type` and no
`pipeline_mode`/`source` — that the 2026-06-28 phantom-reconcile `--apply` pass correctly (mechanically) flipped to
`attempted_failed` per its own logic, but whose "0 remaining / false positive / RESOLVED" narrative was never actually
verified (no `--unphantom` reverse-validation pass was ever run against them). The population has been frozen and
un-remediated for 17 days, and the `DP_RUN_MOSTLY_EMPTY` alert is correctly, honestly reporting its current state — this
is real, currently-live, unresolved manifest data-hygiene debt, though NOT 9,757 shards of missing market data (99%
already have real captured data under the correct `data_type` elsewhere).

**This is a genuine, currently-live data-correctness problem the operator should know about** — not a measurement
artifact and not resolved. It does not represent active data loss (real data exists for ~99% of the affected day/venue
pairs), but the manifest's honest-coverage ledger is wrong for this cell and will keep re-paging `DP_RUN_MOSTLY_EMPTY`
indefinitely since nothing currently corrects it.

**No code fix shipped in this pass** — remediation (deleting the 9,757 orphan rows vs. attempting to backfill their
correct `data_type` vs. teaching the phantom-audit tool to skip/special-case blank-`data_type` rows) requires a
deliberate design decision + more validation (identifying the exact April-2026 writer/migration that produced them, and
confirming a delete pass is safe) that should not be rushed under time pressure. Recommended follow-ups, in order:

- [ ] [SCRIPT] P1. Identify the April-2026 backfill/migration script that wrote the 9,757 blank-`data_type`,
      `pipeline_mode=None`, `source=None` cefi rows (written_at clustered 2026-04-06 to 2026-04-20) — likely a
      historical-date backfill or manifest-consolidation/migration run against
      `market-data-tick-cefi-prd-central-element-323112`. Repo: instruments-service or market-tick-data-service (TBD).
- [ ] [SCRIPT] P1. Once the writer is identified and the (date, venue) real-capture overlap (99.0%, confirmed above) is
      re-verified, delete the 9,757 orphan blank-`data_type` rows from the cefi `_index` (do NOT flip them back to
      `captured` — they don't identify a real specific shard) via a dedicated pass modeled on the existing
      `--report-legacy-venue-defi-phantoms --apply` / `--report-chain-level-defi-phantoms --apply` delete-pattern
      already in `reconcile_phantom_manifest_rows_all.py`, OR handle the 99 genuine-gap DERIBIT/2019 pairs separately
      first. Repo: instruments-service.
- [ ] [SCRIPT] P2. Teach `reconcile_phantom_manifest_rows_all.py`'s forward audit to special-case blank/malformed
      `data_type` on `captured` rows (structurally unauditable via the `data_type={dt}/` needle) so future stale writes
      of this shape are caught/flagged distinctly rather than silently passing through as ordinary phantoms. Repo:
      instruments-service.

Evidence: live UTL `read_availability_index` slim-column query against the bucket above, 2026-07-15, this session (ad
hoc read-only script, not committed — single-read discipline maintained, no whole-corpus walk).
