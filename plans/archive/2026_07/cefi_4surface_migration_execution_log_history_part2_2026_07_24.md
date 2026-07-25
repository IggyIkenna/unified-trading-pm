---
doc_type: plan
title: CeFi 4-surface canonicalization migration — execution log history, part 2 (2026-07-21 PRE-COMPACT checkpoint)
summary: >-
  Verbatim extraction of the 2026-07-21 PRE-COMPACT RESUMPTION CHECKPOINT section (mid-flight endgame state, live
  background operations, remaining queue, lessons, deferred-work table) plus its same-day DELTA updates through
  2026-07-22 ~04:33Z (would_patch fleet ALL_DONE) from `cefi_4surface_migration_execution_log_2026_07_24.md`, split out
  for line-cap compliance (`plans/active/task_template.md` §3 finding J). Content moved verbatim, nothing summarized or
  dropped. This entire range is superseded by the parent's later "REVISED REMAINING QUEUE" and the final "Deferred work
  after 2026-07-22 ~20:15Z" table — it carries zero open todos. Part 1 of this history
  (`/plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part1_2026_07_24.md`) covers the earlier
  2026-07-18 → 2026-07-20 narrative; the parent plan
  (`/plans/active/cefi_4surface_migration_execution_log_2026_07_24.md`) remains the single live source of truth for all
  open work.
status: complete
nature: record
asset_group: [cefi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [cefi, close-out, canonicalisation, manifest, execution-log, progress-log, history, migration, pre-compact]
related:
  [
    /plans/active/cefi_4surface_migration_execution_log_2026_07_24.md,
    /plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part1_2026_07_24.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Split out of cefi_4surface_migration_execution_log_2026_07_24.md (1635 lines, over the 1000L hard line-cap) per the
  plan-hygiene extraction pattern (`plans/active/task_template.md` §3 finding J) — the 2026-07-21 PRE-COMPACT checkpoint
  section (fully superseded by the parent's later "REVISED REMAINING QUEUE" and final deferred-work table) moved
  verbatim into this dedicated history child so the parent can trim to recent state + open todos. Session-driven
  extraction, 2026-07-24.
---

# CeFi 4-surface canonicalization migration — execution log history, part 2 (2026-07-21 PRE-COMPACT checkpoint)

> **This is history part 2 of 2, extracted from
> [`cefi_4surface_migration_execution_log_2026_07_24.md`](/plans/active/cefi_4surface_migration_execution_log_2026_07_24.md)**
> for line-cap compliance (2026-07-24). Zero open todos live here — this whole range (the 2026-07-21 PRE-COMPACT
> checkpoint + its DELTAs through would_patch-fleet ALL_DONE) is explicitly superseded by the parent's later "REVISED
> REMAINING QUEUE" section and the final "Deferred work after 2026-07-22 ~20:15Z" table. Part 1
> (`/plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part1_2026_07_24.md`) covers the earlier
> 2026-07-18 → 2026-07-20 narrative. Content below is verbatim, unedited.

## PRE-COMPACT RESUMPTION CHECKPOINT — 2026-07-21 ~10:00Z (slot-3, mid-flight endgame)

> A fresh session with zero memory of this one resumes the migration from THIS section. Live background operations are
> running — do NOT restart them; monitor + drive them to done.

### LIVE STATE (measured, not inferred)

- **4-surface baseline** (post-collision-resolution, pre-would_patch-fleet): **A=44.65%** (early window 88-93%, LATE
  window 23-28% — pending LATE renames), **B=47.50%** (fleet running to fix), **C=98.26%** (v2 apply finishes),
  **D=PASS**. Re-measure with `market-tick-data-service@bc20cc93 scripts/verify_cefi_canonical_4surface_2026_07_20.py`
  (committed; re-runnable live metric).
- **✅ COLLISION SET FULLY RESOLVED + verified, 0 rows lost**: drop 12,123 (exact target) + 175 redundant-safe-drop
  - 4 genuine merges. Merge preservation verified per-object EXACT: `C_now == PRE_C + W_unique` (DERIBIT BTC-USD@INV bs5
    4,462→**16,904,690**; ETH-USD@INV bs5 51,852→13,940,004 + 54,762→8,470,255; trades 1→104,651). The 16.9M-row DERIBIT
    near-miss was PRESERVED, not lost. Backups: `_migration_backups/cefi_wire_collision_drop_2026_07_19/` +
    `…_MERGE_2026_07_21/`.

### LIVE BACKGROUND OPERATIONS (running now — resume monitoring, do NOT restart)

- **would_patch fleet (surface B)** — 48 SPOT `e2-highmem-16` shards, tag `wpf07210859`, ~86k files/shard, 2019-2026,
  `--workers 4`, pin `mtds@1bdbb4e0` (a744b245 resolver). ETA ~5.5h from ~09:00Z (dense book_snapshot_5 shards ~3.7 f/s
  bound wall-time). Watchdog `bidmbjps3` (SUMMARY-line completion, OOM-vs-preempt classify). ~15/48 done at checkpoint.
- **Agents**: fleet agent `ae18c5ef1b16bc8e8` (drives migration, SELF-DRIVING the queue), manifest-v2 agent
  `a6a2ea3074322f82e` (v2 dry-run READY + DERIBIT-COMBO GCS sweep, waiter `b52852yfn`). Resume via SendMessage.
- **🔴 CRON PAUSED — `uts-prod-tarball-cleanup-cron` (asia-northeast1) is PAUSED** and MUST stay paused until the UTL
  base-image republish → `BASE_IMAGE_DIGEST` fan-out → jobs-image rebuild lands + a verification run confirms a live pin
  is protected (else resuming reproduces the 2026-07-20 tarball-eviction incident). Verify with
  `gcloud scheduler jobs describe uts-prod-tarball-cleanup-cron --location=asia-northeast1 --format='value(state)'`.

### REMAINING QUEUE (agent self-driving; order is load-bearing)

1. would_patch fleet drains → re-verify surface B (expect ~canonical).
2. **LATE colliding-venue renames** (10 venues, 2026-02+, drop-disjoint) — fixes late-window surface A (23-28%). **MUST
   be SERIALIZED AFTER would_patch** — in-place column-rewrite vs copy+delete rename on the same objects RACE.
3. MID window → **KRAKEN-SPOT structural** (48/day `ADA/USD.parquet` spurious-hive-segment from `tardis_shared.py:671`
   verbatim write; needs `_PATH_RE` slash-tolerance + path rebuild + orphan-prefix drain) → **1,697 colon_wire**
   live-lane objects (`BINANCE-FUTURES:PERP:BTCUSDT`) → **loop-until-dry** (2 consecutive full-range dry passes, 0 new
   renames + 0 new collisions — catalogue growth keeps minting new collisions, so 1 clean pass is NOT convergence).
4. **v2 manifest apply** — READY (2,306,493 marker-adds + 1,281,813 dedup; ADAF0:USTF0 PASS 776,527,983 ticks;
   DERIBIT-COMBO=**purge** per operator; chain-drop lossless). GATED on: would_patch done + **consolidator DRAIN**
   (`gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-cefi`) — the main loop coordinates the
   drain. **⚠️ v2 script `instruments-service/scripts/complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py` is
   UNCOMMITTED (v2 agent owns) — commit before archival.**

### LESSONS (the "don't re-learn the hard way")

- **Laptop-egress trap**: any read/rewrite-heavy GCS op (drop, merge, would_patch) run LOCALLY is bandwidth-starved (~0
  net progress). Run IN-REGION on a VM (asia-northeast1-*, ~GB/s). Bit the drop AND the merge-scan AND would_patch.
  Local parallelism does NOT help — egress is the cap.
- **rc=137 is ambiguous**: `Killed` in the log = **OOM** (SIGKILL) → escalate memory/reduce workers, NEVER
  blind-relaunch same config (OOM-loops). `received signal 15`/no `Killed` = SPOT preemption → same-config relaunch is
  fine (idempotent). I mis-diagnosed an OOM as preemption once; the real fix was highmem-16 + `--workers 1` for the
  16.9M-row union.
- **not_in_C dtype-hash artifact**: `pd.util.hash_pandas_object` hashes identical rows DIFFERENTLY across separate
  frames when a column's dtype differs (int64-nanos vs datetime64 between wire-W and canonical-C parquets).
  `exp = 2×|u|` was the fingerprint (W==C but hashed-as-disjoint). FIX: hash inside ONE concatenated frame. 175 of 179
  "merge candidates" were actually redundant full-duplicates (safe-drop), only 4 genuine merges. The union-preservation
  proof (prove BEFORE and AFTER write; W deleted LAST) caught it — a naive not_in_C would have mis-driven the merge.
- **File-COUNT balancing ≠ file-SIZE balancing**: dense book_snapshot_5 shards (large files) bound the fleet wall-time
  even at balanced file counts. For a future would_patch fleet, balance by BYTES.
- **Background agents report-and-WAIT**: they end their turn after each chunk and idle until the next SendMessage — this
  looks like an "idle-stall" but is the agent waiting for a go-ahead. Give a SELF-DRIVE standing instruction (chain the
  queue, don't wait between steps).
- **Slice-completion via VM-absence is UNRELIABLE**: work is cumulative+idempotent across relaunches; a latest-VM at 10%
  does NOT mean 10% done. The only valid surface completion metric is the corpus-wide would_patch/verifier count.

### SHIPPED THIS SESSION (all pushed, ahead=0)

- Oracle honest-by-default: `unified-api-contracts@d40c5d7d` + `market-tick-data-service@953679de`
  (`sanitize_file_stem`).
- Shared resolver fix: `market-tick-data-service@a744b245` (EXTENDED-STARKNET 0%→100%; SSOT contradictions 23→1).
- Pin-aware tarball retention: `deployment-service@dfd7608` (+ UTL `52ee405`) — verified, refuted twice before landing.
- 4-surface verifier: `market-tick-data-service@bc20cc93`.
- Issue docs (in `plans/active/issues/`): `fail_hard_canonical_enforcement_design_2026_07_20.md`,
  `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`,
  `batch_live_filename_divergence_sanitize_symbol_2026_07_20.md`, `tarball_rotation_breaks_vm_recovery_2026_07_20.md`.

### DEFERRED WORK after 2026-07-21

| Item                                                                                                                                                                | State / why deferred                                                                                | Blocked on                                                             |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| would_patch fleet → re-verify B                                                                                                                                     | **cannot be done yet** — ~5.5h in flight                                                            | fleet drain (watchdog `bidmbjps3`)                                     |
| LATE renames → MID → KRAKEN → colon_wire → loop-until-dry                                                                                                           | **not done** — agent self-driving, serialized                                                       | would_patch fleet done                                                 |
| v2 manifest apply (DERIBIT-COMBO=purge)                                                                                                                             | **not done** — READY, gated                                                                         | would_patch done + consolidator DRAIN (main loop coordinates)          |
| Commit v2 script (`…dedup_v2_2026_07_20.py`)                                                                                                                        | ✅ **done** — instruments-service@639591f6 (dead-claim inherited, no live process, mtime stale >5h) | n/a                                                                    |
| Cron resume (`uts-prod-tarball-cleanup-cron`)                                                                                                                       | **cannot be done yet** — deployed image predates pin fix                                            | UTL base-image → BASE_IMAGE_DIGEST fan-out → jobs rebuild → verify     |
| COMPANION: chain-drop WRITER (UTL `_ROW_KEY_COLUMNS`/MTDS stop stamping chain for cefi)                                                                             | **operator-owned** — fleet-wide shard-atom SCHEMA change                                            | operator decision; else consolidator re-adds chain after v2 chain-drop |
| COMPANION: census mis-badge (`deployment-api/_distinct_values.py::_canonical_set` missing OKX-SWAP/FUTURES/OPTIONS → inverted badges; would purge 543,019 captured) | **not done** — report-only fix                                                                      | deployment-api + UAC follow-up                                         |

**RECOMMENDED NEXT (on resume):** monitor the would_patch fleet to drain (watchdog `bidmbjps3` re-invokes the fleet
agent) → the fleet agent self-drives LATE renames → loop-until-dry → then flag for the consolidator drain → v2 apply →
final 4-surface done-state proof. The collision resolution (the only irreversible, data-sensitive stretch) is DONE;
everything remaining is mechanical name/column convergence + one gated manifest apply.

> **NOTE on the `/tmp/cefi_no_orphans_accounting_2026_07_20.json` refs above (§ orphan-accounting):** that file + its
> categorizer (`categorize_cefi_orphans_mvp.py`, scratchpad copy `cefi_orphans_mvp.json`) are a POINT-IN-TIME snapshot
> (2026-07-20) in ephemeral `/tmp`+scratchpad — regenerate via the categorizer (MVP-coverage agent's tool), do not treat
> the path as durable. The committed plan text above already carries the worst-gaps summary.

### DELTA UPDATE — 2026-07-21 ~14:00Z (surface-B fleet endgame)

- **Fleet state**: would_patch fleet ~1.8h from drain. Dense parents finishing (wp25 96%, wp31/32/37/38 ~1.4-1.8h)
  - 8 NEW sub-shards (wp28→4 resume 2025-01-14, wp36→4 resume 2025-09-14, over REMAINING ranges only). ~11 superseded
    parents tracked in `~/cefi_content_fleet/split_parents.txt` (killed-and-split; watchdog treats as superseded, not
    failed). Aggregate ~376k+ patched, ~574k+ already-canonical-skipped.
- **Watchdog (FINAL, bulletproof) = `badl3zwjk` (`wp_watchdog_loop.sh`)**: a `while true` bash loop that NEVER exits on
  heartbeat; each scan is an isolated `python --once` subprocess (fresh ADC creds per scan → token-expiry-immune),
  wrapped in `timeout 300`; an empty/failed verdict just `sleep 1200` + retry (cannot die on a bad scan). Exits to
  re-invoke the agent ONLY on ALL_DONE / NEEDS_RELAUNCH / genuine LONGPOLE; ALL_DONE requires ZERO live fleet VMs (a
  booting sub-shard can't fake a drain). Live status always in `~/cefi_content_fleet/wp_fleet_status.txt`.
- **Errors = 486** (grew from 385 as more shards ran), same two benign classes: ASTER-404 stale-wire (already-renamed →
  twin-reconcile, NOT blind retry) + 503 transient (retry). Captured `~/cefi_content_fleet/wp_fleet_errors.tsv`.
- **Self-drive chain (agent `ae18c5ef1b16bc8e8` owns it — no poke needed unless the watchdog dies)**: on ALL_DONE →
  error-reconciliation (486) → **4-surface verifier (measure B, `mtds@bc20cc93`)** → LATE colliding-venue renames
  (SERIALIZED after would_patch — they RACE) → MID → KRAKEN-SPOT structural → 1,697 colon_wire → loop-until-dry → flag
  the main loop for the **consolidator drain**
  (`gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-cefi`) → v2 manifest apply
  (DERIBIT-COMBO=purge).

### NEW LESSONS (this endgame — cost real time to learn)

- **The recurring "watchdog death" was a HEARTBEAT-EXIT DESIGN flaw, NOT a crash.** A watchdog that exits cleanly on
  each 20-min heartbeat is DEAD until re-armed, and the re-arm (via a re-invoke) has latency → a no-monitor window every
  single heartbeat. Diagnosing it as a crash (token expiry / unhandled exception) was wrong — it exited 0 on schedule.
  FIX: a long-lived loop that NEVER exits on heartbeat, only on actionable verdicts. Cost 3 watchdog rebuilds to
  root-cause. For any "monitor keeps dying" symptom, first check whether it's EXITING BY DESIGN vs crashing.
- **gcloud CLI auth expires ~hourly, and a failed CLI call returns EMPTY/0 that LOOKS like completion.** I nearly
  false-concluded "fleet done / 0 VMs running" from an auth failure (the `ls`/`list` returned empty because unauthed,
  not because the work finished). ALWAYS `gcloud auth print-access-token` (or check ADC) before trusting a CLI "0/empty"
  reading as real state. Workarounds: the ADC bridge
  (`export CLOUDSDK_AUTH_ACCESS_TOKEN=$(python -c 'from google.auth import default; from google.auth.transport.requests import Request; c,_=default(); c.refresh(Request()); print(c.token)')`)
  for gcloud, or ADC/python directly (`get_storage_client`, `compute_v1.aggregated_list`). A long-lived monitor MUST
  re-mint creds per scan (subprocess-per-scan), never hold a launch-time token. **Operator ask logged**: a
  service-account key or longer session would stop this breaking unattended fleet ops every few hours.

### DELTA — 2026-07-21 ~16:55Z (v2 script committed; 4 background agents dispatched for non-fleet-blocked work)

- **v2 manifest script committed** (was flagged uncommitted/at-risk in the pre-compact checkpoint):
  `instruments-service@639591f6`. Confirmed dead-claim before inheriting (mtime 10:53Z, >5h stale, no live process) per
  the liveness-gating rule. Deferred items table row above flipped to done.
- **4 background agents dispatched** for fail-hard-enforcement + census-fix work that does NOT depend on the would_patch
  fleet drain (fenced to distinct files/repos, safe to run concurrent with the fleet + each other):
  1. UAC venue-registry fix — adds `OKX-FUTURES`/`OKX-SWAP` to `VENUES_BY_ASSET_GROUP["cefi"]` (the REAL root cause of
     the census mis-badge — deployment-api's `_canonical_set` is a pure downstream reader of this exact list, no
     deployment-api code change needed) + deregisters the legacy `DERIBIT-COMBO` venue entry (mirrors the operator's
     manifest-purge decision; agent re-verifies 0-captured-rows before removing).
  2. UAC quarantine registry — `is_quarantined_instrument_id` + `ResolutionEvidence` + registry per the fail-hard design
     doc §3/§7, seeded with only the one confirmed permanent member (PACIFICA-SOLANA).
  3. mtds A-iso rebuild — per-shard isolation for `tardis_cefi_shards.py`'s groupby loop (the same defect class that
     lost 27 DERIBIT shards 2026-07-17); changes the function's return contract to include `failed_shards` routed to
     `record_failed`, with per-caller updates.
  4. DERIBIT combo-in-perpetual-partition investigation — read-only measurement + design doc (explicitly distinguished
     from the DERIBIT-COMBO venue purge — this is live venue=DERIBIT data mis-partitioned under
     `instrument_type=perpetual`, not the dead legacy venue label).
- **Shipped, mtds**: fail-hard write-guard fix (STRUCTURAL-only enforcement + Stage-0 ID_FORM observe-log) at the 3
  `canonical_path_violations()` callsites (`partitioned_writer.py`, `websocket_runner.py`,
  `book_microstructure_handler.py`) — code complete, commit PENDING a transient tree-wide QG conflict from a concurrent
  sibling-session agent's live edit to `scripts/restamp_cefi_onchain_perp_venue_chain_2026_07_21.py` (unrelated file,
  import-pattern lint violation on THEIR in-flight WIP) — will retry once it clears.
- **Multi-agent contention observed this cycle**: confirmed via `ps aux` that multiple sibling Claude Code sessions
  (different session IDs) are concurrently active in this same slot-3 clone, editing `unified-trading-library` and
  `scripts/restamp_cefi_onchain_perp_venue_chain_2026_07_21.py` live (mtime seconds-old at observation time). Correctly
  PROTECTED (did not touch), and found pre-existing bounded retry loops (background bash jobs) already handling the
  mtds-side retry — did not duplicate them.
- Consolidator cron job's real name confirmed: `uts-prod-manifest-consolidator-market-data-cefi-cron` (asia-northeast1)
  — still ENABLED (not yet drained, correctly, since would_patch fleet hasn't finished).

### DELTA — 2026-07-21 ~17:04Z (4th watchdog-death root cause: compaction boundary kills tracked background processes)

- **Found the watchdog (`badl3zwjk`/`wp_watchdog_loop.sh`) dead** — confirmed via `ps` (PID gone) + a 34-min gap since
  its last log line (15:25:52Z), well past its own ~20-25min cadence. Its own `while true` loop has NO bug (verified by
  reading the script: isolated per-scan subprocess, `timeout 300`-wrapped, only exits on an actionable verdict) — this
  is a **4th distinct root cause**, different from the 3 already diagnosed this session (gcloud-auth-expiry /
  false-relaunch-on-superseded-parents / heartbeat-exit-design-flaw): **the watchdog was originally launched via a
  `run_in_background: true` Bash-tool call in the PRE-COMPACTION part of this session (started 3:36PM); the `/compact`
  the operator ran immediately before this turn began appears to have torn down that tracked background process tree
  along with the old context, even though the underlying shell process itself had no crash or exit condition.**
- **Verified the FLEET ITSELF was unaffected** — ran `wp_fleet_scan.py --once` directly for real ground-truth: done
  52→61, running 13, `need_relaunch=[]`, `longpoles=[]`, VERDICT=RUNNING. The migration data/VMs are idempotent and
  self-contained; only the MONITORING was dark for ~35 min, no work was lost.
- **Relaunched the watchdog** via plain `nohup bash wp_watchdog_loop.sh & disown` (not the harness's `run_in_background`
  Bash tool this time) so it does not depend on this session's own tool-call lifecycle and should survive a future
  `/compact` boundary. (Saw what looked like 2 processes in `ps` right after relaunch — verified via `ppid` that this is
  a normal, transient command-substitution subshell fork on macOS `ps` output showing the parent's un-exec'd argv, NOT a
  duplicate loop — only one real watchdog is running.)
- **NEW LESSON**: after ANY `/compact` (or long session gap), explicitly `ps`-verify any long-lived background
  watchdog/monitor is still alive before trusting its log file's staleness as "nothing happened" — a stale log + dead
  PID means the MONITOR died, not necessarily the work. Prefer `nohup ... & disown` (detached from the tool runtime's
  own process tracking) over the harness's `run_in_background: true` for monitors that must outlive a single
  conversation turn / survive compaction.
- Current fleet ETA: long poles now wp24 (3.0h), wp30 (3.3h), wp33 (3.2h); wp31/wp32 nearly done (~0.2-0.3h); wp40
  (0.6h), wp48 (1.7h). Errors holding steady ~330-490 (same 2 benign classes, fluctuates per-scan, not cumulative — not
  a growth trend).

### DELTA — 2026-07-21 (UAC quarantine registry scaffolding shipped)

Shipped the `[UAC] P2. is_quarantined_instrument_id + ResolutionEvidence + the registry` todo from
`plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md` §7 — unified-api-contracts@989e9d16. New
standalone module `unified_api_contracts/canonical/quarantine.py` (read-only compose with
`partition_paths.is_canonical_instrument_id`, no fenced-file edit) + `tests/unit/test_quarantine.py` (27 tests, all
green) + `__init__.py` export wiring. Marker grammar: `UNRESOLVED:<VENUE>:<original-stem>`. Registry seeded with EXACTLY
PACIFICA-SOLANA (265 objects, culled 2026-07-16) — the ~5,413 healthy-venue residue deliberately excluded
(NON_CANONICAL, not quarantine, per design doc §3). `classify_id_form()` composes canonical/quarantined/non_canonical
but is NOT wired into any write/read guard (standalone module only). Issue-doc checkbox flipped.

### DELTA — 2026-07-21 (mtds A-iso per-shard isolation — implemented + verified, SHIP BLOCKED on concurrent dirty dep)

Implemented the `[WRITER] P1. A-iso` todo from
`plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md` §7 in `market-tick-data-service`
(uncommitted, working tree only — see blocker below):
`market_interface/adapters/tradfi/tardis_cefi_shards.py:finalise_and_write_cefi_shards` — the per-shard inner-loop body
(`finalise_rows_and_path` → `StreamingParquetWriter` write/close → partition_writer bookkeeping) is now wrapped in one
try/except per shard; on exception it classifies via `_classify_tardis_error` (UAC `classify_venue_error` underneath),
appends a new `FailedCefiShard` record, and `continue`s instead of re-raising out of the whole function — one bad
symbol/chain-root no longer aborts every remaining shard in the same (venue, data_type, day) fetch. Return contract
changed `list[str]` → `tuple[list[str], list[FailedCefiShard]]`; both production callers
(`tardis_bulk_download._download_futures_per_instrument`, `tardis_batch_download._download_one_perp_symbol_legacy`)
updated to unpack the tuple and route `failed_shards` to `ManifestWriter.record_failed` via a new
`_emit_failed_cefi_shard_manifest` helper (mirrors the existing `_emit_pre_listing_manifest` /
`_emit_manifest_from_results` row_key + `PipelineMode.BATCH_TARDIS` convention). New regression test
`test_finalise_and_write_cefi_shards_isolates_per_shard_write_failure` proves a BTCUSDT write failure no longer kills
the sibling ETHUSDT shard in the same call (would have failed pre-fix) and that `classify_venue_error` is actually
invoked with its result flowing into the failed-shard record. All existing `finalise_and_write_cefi_shards` call sites

- mocks (tests/market_interface/adapters/cefi/test_tardis_canonical_output.py,
  tests/unit/test_futures_per_instrument.py, tests/unit/test_normalization_validation.py) updated for the tuple return —
  happy-path behaviour is byte-unchanged (asserted `failed == []` on every success-path test). Investigated the sibling
  `finalise_and_write_cefi_shards_streaming` / `_tardis_cefi_shard_router` for the same defect: its ONLY production
  caller (`_download_one_perp_symbol_streaming`) feeds single-symbol temp parquets, so the theoretical multi-shard-abort
  risk in `_tardis_cefi_shard_router`'s generator body is real but currently dormant (no live blast radius); its
  `writer.close()` failure path is ALREADY correctly isolated by UTL's
  `StreamingShardFinalizer._close_writers_and_collect` (`failed_paths`) — left unchanged as instructed ("do not force a
  change that isn't needed"), flagged here as a residual latent gap for whoever next touches that path.

**Verification**: full `bash scripts/quality-gates.sh --no-fix` in `market-tick-data-service` — basedpyright 0 errors/0
warnings; 6592 passed, 1 failed, 17 skipped (102.95s). The ONE failure
(`tests/unit/test_pipeline_e2e_prediction_canonical.py::test_rule11_per_ag_shard_counts_byte_unchanged`, CEFI shard
count 208 != pinned 200) is CONFIRMED unrelated: root-caused to this slot's `unified-api-contracts` checkout being
LIVE-dirty mid-edit on CEFI venue/mvp-scope registries (`venue_constants.py` / `venue_adapter_keys.py` /
`market_data_categories.py` / `data_type_capability.py` / `mvp_scope.py` / `venue_mapping.py` / `venue_launch_dates.py`

- 3 test files, mtime refreshing every ~10-30s across three separate checks spanning several minutes) — almost certainly
  the SAME issue doc's sibling `[DESIGN]`/`[UAC]` follow-on work in progress concurrently.
  `VENUES_BY_ASSET_GROUP["cefi"]` resolves to 26 venues live from that dirty checkout; the pinned 200 baseline predates
  whatever venue/data_type this concurrent edit is adding. Confirmed zero relation to the A-iso diff (this pinned test
  enumerates purely from UAC's `VENUES_BY_ASSET_GROUP`/`DATA_TYPES_BY_ASSET_GROUP`, never touches
  `tardis_cefi_shards.py`/`tardis_bulk_download.py`/ `tardis_batch_download.py`).

**SHIP BLOCKED**: `quickmerge --agent` requires a fresh `.qg_last_passed_sha` sentinel written only on a fully-green
run; this repo's suite cannot go fully green while the sibling UAC edit stays live-dirty in this slot's shared
`unified-api-contracts` checkout, and a raw `git push` of code is banned regardless. NOT committed, NOT pushed,
issue-doc checkbox NOT flipped (would be a false-progress claim). Next agent/session: re-run
`bash scripts/quality-gates.sh --no-fix` in `market-tick-data-service` once the concurrent UAC edit lands (commit or
revert), confirm `test_rule11_per_ag_shard_counts_byte_unchanged` passes (or is pin-updated by whoever owns that
concurrent venue work), then
`quickmerge.sh "fix(mtds): A-iso per-shard isolation for finalise_and_write_cefi_shards" --agent --files 'market_tick_data_service/market_interface/adapters/tradfi/tardis_cefi_shards.py market_tick_data_service/market_interface/adapters/tradfi/tardis_bulk_download.py market_tick_data_service/market_interface/adapters/tradfi/tardis_batch_download.py tests/market_interface/adapters/cefi/test_tardis_canonical_output.py tests/unit/test_futures_per_instrument.py tests/unit/test_normalization_validation.py'`,
then flip §7's A-iso checkbox with the resulting sha.

### DELTA — 2026-07-21 (UAC venue registry: OKX-FUTURES/OKX-SWAP census fix + DERIBIT-COMBO full deregistration)

Landed `unified-api-contracts@11adf279` (branch `live-defi-rollout`, quickmerge — full `quality-gates.sh` green,
basedpyright 0/0). Two fixes to `VENUES_BY_ASSET_GROUP["cefi"]` and its dependent registries:

1. **OKX-FUTURES / OKX-SWAP registered** (real, actively-captured venues — 119,706 and 423,313 captured manifest rows
   respectively — previously absent from the list, only bare `OKX`/`OKX-SPOT` were declared, mirroring the 2026-07-10
   `OKX-SPOT` precedent). Root cause of the data-status "Axis Value Census" false-positive drift badge:
   `deployment-api/deployment_api/routes/data_status/_distinct_values.py::_canonical_set()` reads
   `VENUES_BY_ASSET_GROUP.get(asset_group, [])` directly (verified — no separate hardcoded venue set), so the omission
   alone badged real captured data as non-canonical. No deployment-api code change needed/made (pure downstream
   consumer). `canonical_mappings.py` already carried both venues' wire-alias + `VENUE_TO_DATA_SOURCE` entries — only
   this one list was out of sync.

2. **DERIBIT-COMBO fully deregistered** (operator decision, verbatim: "delete everything to do with deribit combo since
   it is [a] once venue in practice — manifest/GCS path wise etc. all migrated to split venue+instrument_type").
   Re-verified data-safe THIS session (not just trusted the prior finding) via a direct `read_availability_index` scan
   of the prod cefi manifest scoped to `venue=="DERIBIT-COMBO"`: 196 total rows, **0 captured** (152
   `expected_unattempted` / 30 `empty_confirmed` / 14 `attempted_failed`) — confirms the venue is genuinely dead.
   Removed from every UAC registry: `VENUES_BY_ASSET_GROUP["cefi"]`, `VENUE_DATA_TYPE_CAPABILITIES`,
   `INSTRUMENT_TYPES_BY_VENUE`, `CEFI_VENUE_LAUNCH_DATES`, `VenueMapping.venue_instrument_type_to_tardis`,
   `VENUE_TO_ADAPTER_KEY` (UAC's own registry — distinct from instruments-service's internal
   `VENUE_TO_ADAPTER["DERIBIT-COMBO"]="deribit_combo"` factory entry, left untouched, out of scope), the
   `DATA_TYPE_CAPABILITY_REGISTRY` (2 `DataTypeCapability` entries), and `CeFiMvpRule` (`venues` membership,
   `venue_data_types` override, and the "COMBO" `instrument_types` entry — DERIBIT-COMBO was its only CeFi consumer;
   TradFi's separate `TradFiMvpRule` keeps its own independent "COMBO" declaration, unaffected).
   `MVP_SCOPE_CONFIG_VERSION` bumped 19→20 with a changelog entry documenting the revert of v12
   (venues/venue_data_types) and v16 (COMBO instrument_type). All dependent tests updated/removed to match
   (`tests/unit/test_venue_mapping.py`, `tests/unit/test_data_status_registries.py`, `tests/unit/test_mvp_scope.py` —
   two whole DERIBIT-COMBO test classes removed, `test_config_version_is_latest` bumped to 20).

**Follow-ups (out of scope for this change, noted per the task's own fencing — different repos/concurrent agents)**:
instruments-service's `VENUE_TO_ADAPTER["DERIBIT-COMBO"]="deribit_combo"` internal factory entry and any
market-tick-data-service DERIBIT-COMBO references are NOT yet removed (deliberately left untouched). Separately:
market-tick-data-service's pinned `test_rule11_per_ag_shard_counts_byte_unchanged` (CEFI shard count baseline) was
observed live-blocked on this exact UAC edit while it was still uncommitted (per that repo's own Progress Log entry
above) — now that `VENUES_BY_ASSET_GROUP["cefi"]` (26 venues) is committed/pushed, that baseline likely needs a pin
update by whoever owns that MTDS work; not touched here (MTDS was explicitly out of scope for this task).

Note: `OKX-OPTIONS` (a separate, unverified "registration gap" — no catalogue rows yet) was deliberately NOT added, per
explicit task scope.

### DELTA — 2026-07-21 (mtds A-iso follow-up — CEFI shard-count pin fixed, function-size ratchet fixed, still SHIP BLOCKED)

Follow-up to the A-iso DELTA above. Two more things landed in the (still uncommitted) working tree:

1. **Root-caused + fixed the CEFI-pin blocker.** The concurrent UAC edit flagged above landed as
   `unified-api-contracts@11adf279` ("register OKX-FUTURES/OKX-SWAP cefi venues, deregister legacy DERIBIT-COMBO",
   confirmed committed + pushed, checkout now clean). `VENUES_BY_ASSET_GROUP["cefi"]` is now 26 venues x 8 data_types =
   208 (was 25 x 8 = 200). Updated `tests/unit/test_pipeline_e2e_prediction_canonical.py`'s
   `_PER_AG_SHARD_COUNTS["CEFI"]` pin 200 -> 208 with provenance comment (small, clear, ≤30min out-of-plan fix per the
   findings-triage rule — this pin is UAC-registry-driven only, zero relation to the A-iso diff, and was blocking the
   ONLY way to ship A-iso: a fresh whole-tree `quality-gates.sh` green run).
2. **Function-size ratchet**: wrapping the per-shard body in the A-iso try/except pushed
   `finalise_and_write_cefi_shards` to 224 lines (limit 200). Extracted the per-shard classify+write+bookkeeping block
   into a new private `_write_one_cefi_shard(...)` helper (pure code motion, returns `(written_path, failed_shard)`
   instead of appending to caller-scoped lists) — both functions now well under the limit (129L / 141L). Zero behaviour
   change, confirmed by AST line-count + a clean `quality-gates.sh` codex pass on this specific check.

**STILL SHIP BLOCKED — a DIFFERENT dirty-dep condition, this time IN-REPO**: after both fixes, `quality-gates.sh`'s only
remaining failure is
`❌ Files exceed 900 lines: market_tick_data_service/live/websocket_runner.py (906L), market_tick_data_service/engine/orchestrator/partitioned_writer.py (902L)`
— NEITHER file touched by this task. Confirmed via `git show HEAD:<path> | wc -l`: both are UNDER 900 at HEAD (887L /
883L) — it is a DIFFERENT concurrent agent's live, uncommitted, in-progress edit to these two files (dirty since before
this session started, per the sub-agent mandatory-rules foot-gun list) that pushed them over the cap. Per the same
foot-gun rule these files are explicitly hands-off ("do NOT touch, stage, or commit those files even accidentally") —
mtime is ~16min stale as of this note (not actively being written like the earlier UAC case), but still not mine to fix
or wait out indefinitely. `quality-gates.sh`'s sentinel-write is a WHOLE-TREE check (2026-07-18 redesign, intentionally
— see quickmerge.sh's own comment on the deployment-ui incident it fixed), so a fresh `.qg_last_passed_sha` cannot be
produced while these two foreign files stay oversized, regardless of how clean the A-iso diff itself is.

**Net state**: A-iso implementation + tests + the two follow-up fixes are COMPLETE and individually verified
(basedpyright 0/0, function-size OK, only-2-remaining-violations both foreign/unrelated) but NOT committed, NOT pushed,
issue-doc checkbox NOT flipped — shipping needs either (a) `market_tick_data_service/live/websocket_runner.py`

- `.../partitioned_writer.py` to drop back under 900L (their owning agent's commit, not this task's), or (b) an operator
  decision on how to proceed given the whole-tree sentinel constraint. Files ready to ship the moment the tree is clear:
  `market_tick_data_service/market_interface/adapters/tradfi/{tardis_cefi_shards,tardis_bulk_download,tardis_batch_download}.py`
- `tests/market_interface/adapters/cefi/test_tardis_canonical_output.py` +
  `tests/unit/{test_futures_per_instrument,test_normalization_validation,test_pipeline_e2e_prediction_canonical}.py`.

### DELTA — 2026-07-21 ~17:40Z (MAJOR: fleet-scan liveness bug found silently masking 11/74 preempted shards for hours)

- **Root cause found + FIXED**: `~/cefi_content_fleet/wp_fleet_scan.py::live_vms()` queried
  `compute_v1.InstancesClient().aggregated_list()` and collected any matching-name instance WITHOUT checking
  `inst.status` — a SPOT-preempted VM stays `TERMINATED` in GCE (not deleted) until explicitly removed, so it kept
  reading as "alive" forever. Every scan since ~4-7h ago reported these shards as healthy `RUN` with frozen
  byte-offsets; `need_relaunch` never fired. Fix: `inst.status == "RUNNING"` added to the filter (one-line, verified:
  same scan immediately after the fix correctly flagged 9 shards `GONE(preempt?)` that had shown `RUN` moments before).
- **Caught by**: noticing `wp30`/`wp33`'s progress counters were BYTE-IDENTICAL across 3 consecutive heartbeat scans
  spanning ~45 min (a flat-metric stall per the async-wait discipline) — direct
  `gcloud compute instances list`/`operations list` confirmed both genuinely `compute.instances.preempted` events (wp33
  ~7h ago, wp30 ~4h ago), not a measurement artifact.
- **Full scope, once the fix revealed it**: **11 of 74 shards** (wp03, wp10, wp15, wp18, wp19, wp21, wp24, wp30, wp33,
  wp40, wp48) were actually `TERMINATED`, silently stalled anywhere from minutes to ~7h. Recovered per the mandatory
  PROGRESS-checkpoint rule (never replay START_DATE): read each shard's last GCS log progress line directly, computed a
  safe resume day via the fleet's own `resume_day.py` (file-density curve − 8,000-file margin so every day fully before
  resume is provably done), deleted the 11 stale `TERMINATED` VM objects, relaunched all 11 SPOT (`e2-highmem-16`,
  workers=4, same pin) from their resume points through original end-dates. Verified post-relaunch: fresh scan shows
  `need_relaunch=[]`, `live=11 == running=11`.
- **Resume points** (shard: resume date .. original end): wp03 2021-03-18..2021-05-14 · wp10 2022-07-28..2022-10-05
  (progress too small vs margin, restarts) · wp15 2023-04-28..2023-06-21 (restart) · wp18 2023-10-16..2024-01-02 (0
  progress, restart) · wp19 2024-01-24..2024-01-28 · wp21 2024-03-02..2024-04-14 (restart) · wp24 2024-07-22..2024-08-19
  · wp30 2025-02-19..2025-03-05 · wp33 2025-05-04..2025-06-05 (restart) · wp40 2026-01-22..2026-02-01 (restart) · wp48
  2026-05-15..2026-07-19.
- **ETA impact**: materially extends the fleet's true remaining time — 11 shards effectively restart their clocks (most
  from ~0-5% progress since preemption caught them early, a few mid-progress). No data was lost or corrupted (idempotent
  design held); this was purely a monitoring blind spot costing wall-clock time, not correctness.
- **NEW LESSON**: `compute_v1.aggregated_list()` returns ALL instances regardless of status
  (RUNNING/TERMINATED/STOPPING/etc) — any "is this VM alive" check against it MUST filter `inst.status == "RUNNING"`
  explicitly, or a preempted SPOT VM reads as healthy forever. This is a DIFFERENT bug class from the 4 watchdog-death
  root causes already logged above (those were about the MONITOR process dying; this one is about the monitor running
  fine but its own liveness query being wrong) — 5 distinct fleet-monitoring failure modes found this session total.
- Also notable from the combo-investigation agent's just-landed findings (see its own DELTA/issue doc): the DERIBIT
  combo-in-perpetual-partition scope is **15,119 rows**, ~76x the original 23/787 estimate, plus a still-open write-path
  leak (not purely historical) — that agent correctly recommends **operator sign-off required before any `--apply`**.
  Flagging for the operator's attention at the next natural checkpoint (not a code/data change, no action taken).

### DELTA — 2026-07-21 ~19:15Z (6th fleet-monitoring gotcha: GCS run.log upload stays stale after a same-name VM relaunch)

- **Found via deep SSH investigation** (triggered by wp48 showing 90 minutes of zero GCS-log change post-relaunch): the
  relaunched VMs' `vm-exec-with-gcs-tee.sh` GCS-log upload does NOT refresh the blob after a same-named VM is
  deleted+recreated — the GCS object stays frozen on the ORIGINAL pre-preemption content (confirmed via
  `blob.updated`/`blob.generation` unchanged, hours stale) even though the LOCAL process is genuinely alive and
  progressing. Root cause not further diagnosed (deployment-service-owned upload script, likely a no-clobber/generation-
  precondition bug) — out of scope to fix here; documented as a follow-up.
- **Verified via direct SSH** (`gcloud compute ssh --tunnel-through-iap`) on all 11 relaunched shards: the real
  `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py --apply` process is ALIVE and progressing normally on
  every one (wp03 35200→53000, wp10 53000, wp15 72600/84919, wp24 23600→24400/56035, wp30 28400/54986, wp33, wp40, wp48
  77600→79200/135731 — all climbing between successive checks). wp19 already correctly self-deleted on completion
  (confirmed via its own local completion message: `rc=0`, `STOP-ON-SURPRISE bounds ok=True`,
  `VM_SHUTDOWN_ON_COMPLETION=true`). **Zero actual problems — this was purely an external- visibility gap**, not a
  repeat of the VM-liveness bug (that one is genuinely fixed and confirmed working for shards that die AFTER their fresh
  launch, per `wp_fleet_scan.py`'s `need_relaunch=[]` holding clean since the restart).
- **New tool**: `~/cefi_content_fleet/check_relaunched_via_ssh.sh` — batch SSH health-check for exactly these 11 shards
  (until each is confirmed DONE), since the normal GCS-log-based scan is blind for them specifically.
- **Full tally of fleet-monitoring failure modes found this session (6 distinct root causes)**: (1) gcloud CLI auth
  expiry looks like empty/done, (2) false-relaunch-on-superseded-parents, (3) watchdog heartbeat-exit-by-design mistaken
  for a crash, (4) compaction boundary killing a `run_in_background`-tracked watchdog process, (5) `live_vms()` not
  filtering `inst.status` (masked 11 real preemptions for hours — the big one, fixed), (6) this one (GCS log staleness
  post-relaunch, cosmetic only). **Lesson for future fleets**: ground-truth via SSH/direct-process- check periodically,
  never trust a single monitoring layer (GCS logs, VM aggregated_list, or a watchdog's own log) as the sole source of
  truth for a long-running unattended fleet — each has now independently been shown to lie in a different way.
- Going forward: resuming normal watchdog-based monitoring cadence for the 63+ already-healthy shards, supplemented by
  periodic `check_relaunched_via_ssh.sh` runs for the 11 relaunched ones until each confirms DONE.

### DELTA — 2026-07-22 ~04:33Z (would_patch fleet ALL_DONE — self-drive chain resumed)

- **would_patch fleet (surface B) reached ALL_DONE**: 74/74 shards done, 0 running, `need_relaunch=[]`. Confirmed via
  the FIXED `wp_fleet_scan.py` (see the earlier "5th monitoring gotcha" entry — this ALL_DONE is trustworthy, the
  VM-liveness bug that could have masked a false drain is fixed). Final error tally: 348 total (290× 404
  stale-wire-already-renamed, 53× 503 + 5× 500 transient) — same 2 benign classes documented throughout this session, no
  new error class.
- **Resumed the fleet agent** (`ae18c5ef1b16bc8e8`) via SendMessage to proceed with its self-drive chain:
  error-reconciliation (348) → 4-surface verifier (re-measure surface B) → LATE colliding- venue renames (SERIALIZED) →
  MID window → KRAKEN-SPOT structural → 1,697 colon_wire → loop-until-dry (2 consecutive clean passes) → flag the main
  loop for the consolidator drain + v2 manifest apply. Briefed it on: the fixed VM-liveness bug, the wp21
  double-preemption + restart (no data lost, same-config idempotent restart), and that UAC/mtds have moved
  (OKX-FUTURES/SWAP + DERIBIT-COMBO deregistration landed; a shared `enforce_structural_and_observe_id_form` helper now
  exists in `symbol_rules.py`; the 3 write-guard callsites + the CEFI shard-count pin are still mid-flight uncommitted
  from the A-iso agent — told it to re-pull before touching those).
- **Total elapsed for the would_patch tranche**: fleet was already in progress at session start (~09:00Z 2026-07-21 per
  the earlier checkpoint), reached ALL_DONE ~04:33Z 2026-07-22 — roughly 19.5h wall-clock, materially extended by the
  11-shard silent-preemption gap (hours lost to the monitoring bug, not to genuine compute time) and wp21's second
  preemption.
