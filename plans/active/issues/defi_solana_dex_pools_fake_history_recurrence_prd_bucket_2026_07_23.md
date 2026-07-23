---
doc_type: issue
title:
  Solana DeFi dex_pools legacy shape in the -prd- bucket carries the SAME fake-history-snapshot bug
  solana_defi_fake_history_snapshot_2026_06_17.md already fixed once, in a scope that fix never scanned
summary: >-
  While monitoring the 2026-07-23 defi orphan-sweep + planning its backfill, sampled real
  raw_tick_data/by_date/day=2025-01-*/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=ORCA|RAYDIUM/
  chain=SOLANA/instrument_type=pool/data_type=dex_pools/ objects in market-data-tick-defi-prd-central-element-323112.
  Every sampled row's own timestamp column resolves to 2026-05-04/05-05 (a year+ after the day= partition it is filed
  under), and available_at is uniformly 2026-06-11T09-48-03 across every day= partition sampled -- the exact signature
  of the already-diagnosed "one live snapshot back-dated across every historical partition" bug. The prior fix (commit
  aa3b9f18, forward-only-honest write gate) plus its 6000-object cleanup targeted only the OLD flat prefix
  (dex_pools/PROTOCOL/SOLANA/date=star/) and a non-prd bucket variant (Gate 7,
  solana_defi_legacy_migration_2026_05_27.md, 2823 objects, fully migrated 2026-05-28) -- neither covers this
  hive-shaped, -prd- bucket population. Scanning the live sweep's own already-written checkpoint shards -- 241,281 of
  3,074,283 actionable rows found so far (7.8 pct) carry this exact data_type=dex_pools legacy shape, venues ORCA +
  RAYDIUM, days 2025-01-01 through 2025-01-17 (bounded so far; the sweep has not finished and may find more as it
  continues). MUST NOT be record_captured as genuine historical coverage until ruled on.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [defi, solana, orca, raydium, fake-history, data-correctness, orphan-sweep, canonical-migration]
related:
  [
    ../archive/issues/solana_defi_fake_history_snapshot_2026_06_17.md,
    ../archive/2026_07/solana_defi_legacy_migration_2026_05_27.md,
    estate_orphan_assessment_2026_07_21.md,
    ../defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-23
parent_epic: defi_master
priority: P0
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
assigned_vm: NA
execution_scope: local-only
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py,
    market-tick-data-service/scripts/migrate_legacy_solana_defi_to_canonical.py,
    unified-trading-library/unified_trading_library/availability_stamping.py,
  ]
depends_on: []
---

# defi Solana dex_pools fake-history recurrence in the -prd- bucket (2026-07-23)

## What I found

Investigating why the 2026-07-23 defi orphan-sweep was finding ~99% orphan rates in the Jan-2025 region (operator asked
"how do we know instruments captured match the catalogue and aren't fabricated"), sampled 10 real objects under:

```
gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2025-01-0{8,9}..2025-01-12/
  pipeline_mode=batch_onchain_rpc/asset_group=defi/venue={ORCA,RAYDIUM}/chain=SOLANA/instrument_type=pool/
  data_type=dex_pools/<pool_address>.parquet
```

**Every single sample** shows the identical pattern:

- The GCS partition key (`day=`) says January 2025.
- The row's own `timestamp` column (unix epoch) resolves to **2026-05-04 or 2026-05-05** — over a year AFTER the day=
  partition claims.
- `available_at` is **uniformly `2026-06-11T09:48:03`** across every sampled day= partition (2025-01-08 through
  2025-01-12) — a single write-time stamp smeared across 5 different logical dates.
- Where a file has 2 rows, they are byte-identical duplicates of each other.
- Nothing in the schema (`source=onchain_rpc`, no `note`/`evidence`/forward-fill flag) distinguishes this from genuine
  historical data — it is **silently indistinguishable** without checking `timestamp` against `day=` by hand.

This is the EXACT signature `solana_defi_fake_history_snapshot_2026_06_17.md` already diagnosed and marked **RESOLVED**:
Orca/Raydium/Kamino REST collectors have no historical endpoint, so a historical backfill loop wrote ONE live snapshot
into every requested historical `date=` partition. That fix (`solana_defi_handler.py:: _filter_rows_to_target_day`,
commit `aa3b9f18`) + its cleanup **only targeted the OLD flat prefix** (`dex_pools/<protocol>/SOLANA/date=*/`, 6000
objects deleted) — not the hive-shaped `raw_tick_data/by_date/...` structure. A SEPARATE remediation (Gate 7,
`solana_defi_legacy_migration_2026_05_27.md`) found 2823 objects in this same hive shape but in a bucket WITHOUT `-prd-`
(`market-data-tick-defi-central-element-323112`), fully migrated + deleted 2026-05-28. **Neither remediation's scope
includes the `-prd-` bucket's hive-shaped `dex_pools` objects** — this is a population no prior cleanup pass ever
re-scanned.

Corroborating evidence: this shape (`instrument_type=pool` lowercase, `data_type=dex_pools`) is confirmed via git blame
to be **pre-2026-06-05** code — commit `fbff8cf0` renamed Orca/Raydium/Kamino's data_type to `dex_pool_state` and their
`instrument_type` to Solana-specific types on that date. Everything in this shape predates that rename, i.e. predates
the current canonical vocabulary entirely.

## Scope — CONFIRMED FINAL 2026-07-23 (independent of the orphan-sweep; does not need to wait for ACCEPTANCE)

Rather than wait on the general orphan-sweep's full-corpus walk, ran a TARGETED, bounded existence-check walk
(read-only, `list_blobs(prefix=..., max_results=1)` per day×venue, 24-way concurrent) across the exact date range the
ORIGINAL fake-history bug's backfill loop covered per `solana_defi_fake_history_snapshot_2026_06_17.md:68`
(`--start 2023-01-01 --end 2026-04-15`) — 1,201 days × {ORCA, RAYDIUM} = 2,402 probes, ~2 minutes.

- **Exactly 34 day/venue combinations have this shape — 17 days × 2 venues, nothing more, nothing less.**
- Venues: `ORCA`, `RAYDIUM` only (confirmed — no hits for any other venue at any point in this session).
- Days: `2025-01-01` through `2025-01-17` inclusive, **every single day in that window, no gaps** — matches exactly what
  the orphan-sweep's partial walk had already found, confirming that partial sample WAS already the complete population
  (the sweep simply hadn't reached ACCEPTANCE yet to prove it independently).
- This makes todo 2 below DONE — no need to wait for the sweep or re-run
  `scope_defi_dex_pools_fake_history.py --source final`; the day/venue boundary is now proven, not merely
  observed-so-far. Row count (241,281 as of the 55-60 shard samples) is likewise final since the day/venue set it's
  derived from cannot grow.

## Why this blocks the backfill

`backfill_orphan_class_e.py --apply` would `record_captured` every orphan-E row in the sweep's report, INCLUDING this
population, stamping the manifest with **fabricated day=2025-01-XX coverage that is actually a copy of 2026-05-04/05
live state**. That is fabrication-by-construction — the exact class of harm the sports 2020-06-06 data floor rule exists
to prevent. **Do not run defi's backfill until this population is either excluded from the report or the report itself
is regenerated after a fix.**

## Todos

- [x] 1. [OPERATOR] P0. **Rule on disposition — DECIDED 2026-07-23, option (b)**. Operator ruling (verbatim): "OK YEAH
      WE need to relabel to reality." This is option (b) from the choices below: migrate-forward, re-stamp
      `available_at`/relabel each affected object as a `live`-mode snapshot under its TRUE date (2026-05-04/05, per the
      row's own `timestamp` column) instead of a fabricated historical `day=2025-01-XX`. NOT a wipe, NOT a
      leave-in-place exclusion. Implementation is a COPY-forward migration (GCS objects are immutable-by-path; per the
      delete-safety protocol, the OLD mislabeled object is left in place, unregistered, until a human confirms deletion
      — never delete-on-relabel): for each affected object, write a NEW object at the canonical path with
      `day=<true_date>` and `pipeline_mode=live_onchain_rpc` (or whatever the correct live-mode partition token is; the
      object's own row-level `timestamp` is the source of truth for `<true_date>`, NOT `available_at`, which is itself
      the uniform write-time artifact of the original bug), then `record_captured` the NEW path only. The OLD
      `day=2025-01-XX` path is left un-recorded (never `record_captured`) and flagged for a later human delete decision
      once the new copies are verified. See todo 3 for the concrete implementation. <br>Original options considered: (a)
      WIPE per the 2020-06-floor-style precedent — rejected, since Orca/Raydium pool STATE (unlike a genuinely-absent
      historical price series) has standalone present-tense value even mislabeled; (c) leave-in-place-and-exclude-only —
      rejected as a permanent non-fix, since it never produces the TRUE coverage the data actually represents.
- [x] 2. [DATA] P1. ~~**Get the TRUE final scope** once defi's orphan-sweep reaches ACCEPTANCE~~ — **DONE 2026-07-23,
      superseded by a faster independent method**: rather than wait on the sweep, ran a targeted bounded walk across the
      exact date range the original bug's backfill loop covered (2023-01-01..2026-04-15) — proved the population is
      EXACTLY 17 days × {ORCA, RAYDIUM}, 2025-01-01..17, no gaps, nothing beyond this window. See "Scope" section above.
- [ ] 3. [CODE] P1. **Build the relabel-forward migration per the todo-1 ruling — SCRIPT SHIPPED + VALIDATED 2026-07-23,
      FULL-SCALE RUN LAUNCHED 2026-07-23, still in progress.** `market-tick-data-service@67524cbb`
      (`scripts/relabel_solana_dex_pools_fake_history.py`): for each affected object, reads the row(s), derives
      `<true_date>` from the row's own `timestamp` (NOT `available_at`), computes the canonical dest path via UAC
      `build_defi_partition_path` with `day=<true_date>` + the resolved `live_onchain_subgraph` pipeline_mode +
      `data_type=dex_pool_state` (this population predates the 2026-06-05 rename), re-stamps BOTH `available_at` (via
      `stamp_available_at_onchain_tick`) and the row-level `data_type` column (a real bug caught during validation — the
      row's own column must match its new path, not just the path), uploads, `record_captured`s only the new path, and
      leaves the OLD object un-recorded + logged to a dedupe'd pending-human-delete report
      (`_index/audit/dex_pools_fake_history_pending_delete.parquet`). Preserves the original pool-address leaf filename
      (collision-safe; deliberately does not risk the separate tracked symbol-collision bug). **Validated end-to-end
      against 1 real production object** (`--apply`, then deleted + redid it once to fix the data_type bug) — also
      caught and fixed a `setup_events()`-not-initialized crash and a retry-logic gap that would have silently skipped
      `record_captured` forever after a partial failure. **Interim backfill exclusion — SHIPPED
      `instruments-service@fd8450b7`**: `split_dex_pools_fake_history()` in `backfill_orphan_class_e.py` (mirrors
      `backfill_orphan_class_e_sports.py`'s `split_pre_floor` pattern) excludes all 34 known combinations from
      `record_captured` entirely — a normal defi `--apply` run cannot touch this population before the relabel migration
      runs, regardless of what todo 1 sequencing anyone follows. 2 new unit tests, `quality-gates.sh` green (also fixed
      an unrelated empty-string-fallback baseline regression from a concurrent commit that was blocking ALL
      instruments-service commits, not just this one). **Real population count measured 2026-07-23** (concurrent listing
      across the 34 legacy prefixes, not an estimate): exactly 241,281 objects (14,094 ORCA + 99 RAYDIUM per day x 17
      days — the SAME object count every day, consistent with the original bug re-writing one live snapshot under 17
      different fake `day=` labels). **`--only-day` sharding hardened before launch**
      (`market-tick-data-service@b9a8b76e`): the script has no `--shard-of`/`--shard-index`, only
      `--only-day`/`--only-venue`; a first sharded-launch attempt failed with `gcloud: Bad syntax for dict arg` because
      `gcloud compute instances create --metadata` parses its value as a comma-delimited dict, and the day-list was
      comma-joined (`2025-01-01,2025-01-02,...`) — ANY comma anywhere in a `--metadata` value breaks it, not just at the
      top level. Fixed by accepting `:` as an additional separator (`_parse_days()`) and switching the launcher to
      colon-joined day lists. **Launcher category added** (`deployment-service@10b2fd5c` after an earlier attempt at
      `732c390d`): `defi-relabel` category in `launch-canonical-migration-vm.sh` (`_script_for()` + the
      DRY-BY-DEFAULT+--apply flag list + the direct-dispatch case-arm) — reused the already-registered
      `canonical-migration-defi-` VM-name prefix, no new registry entry needed. Resolved a real autostash-merge conflict
      with a concurrent slot's unrelated `defi-glued-reshard` category addition to the same file (both kept,
      self-contained, no overlap). **4 sharded VMs launched 2026-07-23 ~13:58 UTC** (`e2-standard-8` SPOT,
      `asia-northeast1-c`, tarballs pinned to the exact shipped SHAs):
      `canonical-migration-defi-relabel-20260723-135815-d01to05` (days 01-05), `...-135840-d06to09` (days 06-09),
      `...-135903-d10to13` (days 10-13), `...-135929-d14to17` (days 14-17) — every shard processes BOTH venues for its
      assigned days (RAYDIUM's ~99/day is negligible next to ORCA's ~14094/day). **Verified genuinely running, not just
      booted**: first shard's `run.log` shows real `wrote + recorded` lines with the CORRECT dest path
      (`day=2026-05-04/pipeline_mode=live_onchain_subgraph/.../data_type=dex_pool_state/<pool>.parquet`), matching the
      earlier single-object validation exactly. **Measured throughput constraint**: the per-VM manifest shard write hits
      GCS's per-object mutation rate limit (~1/sec) on nearly every row, logged as `429` + `backing off ~1s` —
      self-healing (every retry logged `succeeded after 1 429-retry attempt`, processing continues), NOT a hard failure,
      but caps sustained throughput to roughly 2 objects/sec per VM — consistent with the documented multi-hour estimate
      (~56K-70K objects per shard implies single-digit hours per VM, not minutes). **Still running as of last check —
      full-scale completion not yet verified; monitor to actual completion**, then the pending-delete report needs human
      review before any old-object cleanup (never automated).
- [x] 4. [REVIEW] P2. ~~Check whether the SAME bug shape exists for Kamino~~ — **PARTIALLY DONE 2026-07-23**:
      `venue=KAMINO/chain=SOLANA/instrument_type=pool/data_type=dex_pools/` has **zero objects** in the `-prd-` bucket
      across 6 sampled days (both inside and outside the affected window) — moot for the AMM-pool shape this issue
      covers (Kamino is primarily a lending protocol, not an AMM, so it likely never wrote this shape at all). **Still
      unconfirmed**: the original 2026-06-17 doc ALSO named a `lending_indices/{kamino,solend}` tree as affected — a
      quick exploratory check of `data_type=lending_indices` / `lending_rates` under `instrument_type=pool` came back
      empty too, but that's **inconclusive, not a clean bill** — I don't have confirmed knowledge of the real
      path/instrument_type shape lending data actually uses in this bucket (my guess may simply be wrong, not "no such
      data exists"). A real check needs someone to find lending's actual writer code + real path shape first, then
      re-probe.
- [x] 5. [REVIEW] P3. ~~**Audit whether other already-completed backfills this session (cefi, prediction) could have the
      same class of issue**~~ — **DONE 2026-07-23, CLEAN.** Sampled real objects at their actual `uri` (not `dest_path`,
      which is a computed display-only field for RECORD_ONLY rows — reading it 404s, since RECORD_ONLY never moves the
      physical object) and checked each row's own timestamp column against its `day=` partition: **cefi** — 10 samples
      across `trades`/`book_snapshot_5` (Tardis-sourced): 7/10 exact match, 3/10 off by a few _seconds_ (23:59:57-59 vs
      the requested day) — a benign first-row-before-midnight boundary artifact, NOT the year-later fabrication
      signature; **prediction** — 30 samples (20 KALSHI `trades`, 10 POLYMARKET `trades`/`prediction_trades`): **30/30
      exact match**. Zero evidence of the dex_pools-class bug in either asset_group's completed backfill. Both cefi and
      prediction's `record_captured` cells are genuinely clean.

## Lesson (do not re-learn)

**A previously-RESOLVED data-fabrication bug's fix scope must be checked against ALL buckets/path-shapes the bug could
have written to, not just the one the fix's own cleanup happened to scan.** The 2026-06-17 fix covered the old flat
prefix; a SEPARATE 2026-05-27 migration covered a non-`-prd-` bucket's hive-shaped copy. Neither effort's "done"
checklist included "verify the `-prd-` bucket's hive-shaped copy too" — the exact population that turned out to still
have live fake data. When closing out a fabrication-class bug, enumerate every bucket × path-shape combination the buggy
writer could have touched, not just the one instance found first.
