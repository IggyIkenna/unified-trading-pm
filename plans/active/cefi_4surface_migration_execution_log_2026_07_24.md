---
doc_type: plan
title: CeFi 4-surface canonicalization migration — execution log (extracted from cefi_consolidated_closeout)
summary: >-
  Verbatim extraction of the Progress Log from cefi_consolidated_closeout_2026_07_18.md (line-cap remediation,
  2026-07-24) — the day-by-day narrative + PRE-COMPACT checkpoints + DELTA updates + deferred-work tables tracking the
  CeFi 4-surface (GCS filename / parquet instrument_id column / manifest key / reader) canonicalization migration
  execution. This is the execution-log half of the split; the parent plan stays the lean Track-1..7 coordination index.
  Content moved verbatim, nothing summarized or dropped — see conservation check in the split's commit. **2026-07-24
  2nd-stage extraction**: this file itself grew past the 1000L hard cap — the OLDEST closed Progress Log range
  (2026-07-18 through the 2026-07-21 PRE-COMPACT checkpoint) was extracted verbatim into two history children
  (`…_history_part1_2026_07_24.md`, `…_history_part2_2026_07_24.md`); this file retains the 6+1 still-open todos, the
  most recent dated sections (2026-07-22 3rd checkpoint through 2026-07-23), and the current deferred-work table.
status: active
nature: process
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
tags: [cefi, close-out, canonicalisation, manifest, execution-log, progress-log, migration]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /plans/active/issues/_cefi_canonical_blueprint_2026_07_17.md,
    /plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part1_2026_07_24.md,
    /plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part2_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Split out of cefi_consolidated_closeout_2026_07_18.md (2103 lines, over the 1000L hard line-cap) per the plan-hygiene
  remediation job driven by plans/active/issues/plan_line_cap_remediation_2026_07_23.md row #4 — the ~1566-1568-line
  Progress Log moved verbatim into this dedicated execution-log child so the parent can trim to a lean coordination
  index. Operator-approved via interactive Q&A 2026-07-23/24. **2026-07-24**: this execution-log child itself grew to
  1635 lines (over cap again) — re-extracted per `plans/active/task_template.md` §3 finding J into 2 history children
  (part1 = 2026-07-18→07-20 narrative, part2 = the 2026-07-21 PRE-COMPACT checkpoint); the 7 open todos + all recent
  (2026-07-22/23) state stayed live in this file.
umbrella: true
---

# CeFi 4-surface canonicalization migration — execution log

> **This is the execution-log child of
> [`cefi_consolidated_closeout_2026_07_18.md`](/plans/active/cefi_consolidated_closeout_2026_07_18.md)**, split out
> 2026-07-24 for line-cap compliance (the parent hit 2103 lines, over the 1000L hard-fail cap). The parent retains
> Tracks 1-7 + the CeFi canonical spec + the Codex SSOTs pointer (the live coordination index); this file holds the full
> day-by-day Progress Log — PRE-COMPACT checkpoints, DELTA session updates, and deferred-work tables — **verbatim,
> unedited**, moved here in full. Keep appending new session entries HERE, not in the parent, going forward. Still
> actively updated as of the split (KRAKEN-SPOT `--apply` / fleet reverify / Surface-C v2 dedup in flight per the
> entries below) — this is NOT an archive-only historical doc.
>
> **2026-07-24 update**: this file itself crossed the 1000L hard cap (1635 lines). The oldest, fully-closed dated range
> — 2026-07-18 narrative through the 2026-07-21 PRE-COMPACT checkpoint (would_patch fleet ALL_DONE) — was extracted
> VERBATIM into two history children (line-cap remediation pattern, `plans/active/task_template.md` §3 finding J):
> **[part 1, 2026-07-18 → 2026-07-20](/plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part1_2026_07_24.md)**
> and
> **[part 2, the 2026-07-21 PRE-COMPACT checkpoint](/plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part2_2026_07_24.md)**.
> All 7 open todos and the most recent (2026-07-22 3rd checkpoint through 2026-07-23) state stayed live below.

## Progress Log

> **2026-07-18 → 2026-07-20 narrative extracted** (line-cap compliance, 2026-07-24) to
> [`cefi_4surface_migration_execution_log_history_part1_2026_07_24.md`](/plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part1_2026_07_24.md)
> — covers the surface-C manifest cutover/apply, Track-6 resolver fixes, the NO-ORPHANS accounting, the surface-A
> filename census + rename-fleet launch, the double-wrapped-id bug class, the UAC path-oracle stem-blindness finding,
> and the full catalogue-coverage-gap root-cause measurement. Moved verbatim, nothing summarized or dropped.

**Deferred / handoff (each needs a tracked todo before this plan archives):**

- [ ] [SCRIPT] P0. Script 2 `_PATH_RE` must tolerate an embedded-slash wire stem (KRAKEN-SPOT 25,131). FENCED to the
      live rename fleet — needs the fleet owner. The rename is a real GCS move (pseudo-dir → single object).
- [ ] [DATA] P0. De-duplicate the 658 ambiguous catalogue wire keys (off-by-one expiry duplicates) in
      `build_instrument_catalogue.py`. FENCED to the DeFi removal-probe agent.
- [ ] [DATA] P0. Enumerate the MISSING catalogue rows behind the ≈5,413 healthy-venue residue in
      `build_instrument_catalogue.py` (FENCED): OKX-SPOT fiat-quote pairs (AED/AUD/BRL/TRY), COINBASE-SPOT crypto-quote
      pairs (`-BTC`/`-ETH`), BITGET-FUTURES CME-letter-month dated futures (`BTCUSDH26`). Each measured at 0 catalogue
      rows against on-disk data that exists.
- [ ] [DATA] P1. Add a LIGHTER-ZKSYNC market-index → symbol map so the ~11,283 numeric-stem objects resolve.
- [ ] [DATA] P2. Design the COMBO-in-perp-partition move for DERIBIT.
- [ ] [DATA] P2. Register PACIFICA-SOLANA (265) in the fail-hard quarantine set.

> **NOTE (2026-07-24, added at extraction time — verify before acting, do not assume stale-closed):** later DELTA
> entries below (2026-07-22/23) show substantial forward progress that may already satisfy several of the todos above
> (e.g. KRAKEN-SPOT's underlying rename-fleet blocker reads as resolved per the 2026-07-23 apply entry below, and the
> wire-key dedup / catalogue-enumeration-gap work has its own more-current numbers in the final deferred-work table at
> the end of this file). This extraction pass did NOT re-verify or flip any of the 6 checkboxes above — that judgment
> call is out of scope for a line-cap extraction; the next session picking up this plan should re-check each one against
> the final deferred-work table before treating it as still-open.

---

> **2026-07-21 PRE-COMPACT RESUMPTION CHECKPOINT extracted** (line-cap compliance, 2026-07-24) to
> [`cefi_4surface_migration_execution_log_history_part2_2026_07_24.md`](/plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part2_2026_07_24.md)
> — covers the mid-flight endgame LIVE STATE, the would_patch fleet's live background operations, the (now superseded)
> REMAINING QUEUE, the session's lessons-learned, and the "DEFERRED WORK after 2026-07-21" table, plus same-day DELTA
> updates through 2026-07-22 ~04:33Z (would_patch fleet reaching ALL_DONE). This entire range is explicitly superseded
> by the "REVISED REMAINING QUEUE" section and the final deferred-work table later in THIS file — moved verbatim,
> nothing summarized or dropped.

## PRE-COMPACT RESUMPTION CHECKPOINT — 2026-07-22 ~05:00Z (3rd checkpoint, post would_patch-ALL_DONE)

> A fresh session with zero memory of this one resumes from THIS section. The would_patch fleet is DONE; the fleet agent
> is now self-driving the remaining chain. Do NOT restart the fleet or its watchdog — it finished. Do NOT re-launch any
> of the 74 shard VMs.

### SHIPPED THIS SESSION (all pushed, verify each sha before trusting a stale local checkout)

- `unified-api-contracts@11adf279`-lineage — OKX-FUTURES/OKX-SWAP added to `VENUES_BY_ASSET_GROUP["cefi"]` (the real fix
  for the deployment-api census mis-badge — deployment-api needed NO code change, confirmed `_canonical_set()` is a pure
  reader of this list) + DERIBIT-COMBO fully deregistered from every UAC registry (re-verified 0 captured rows across
  196 manifest rows before removing).
- `unified-api-contracts@989e9d16` — quarantine model: `is_quarantined_instrument_id` + `ResolutionEvidence` + registry
  (seeded with only PACIFICA-SOLANA) + `classify_id_form()`. Marker grammar: `UNRESOLVED:<VENUE>:<original-stem>`.
  Standalone module, not wired into any write/read guard yet (that's Stage 3, still future work).
- `instruments-service@639591f6` — the v2 manifest canonicalization script (dedup, chain-axis drop,
  DERIBIT-COMBO=purge), a dead-claim inherited from an earlier agent, committed clean.
- `unified-trading-pm@518371960`, `d42bc6c79`, `91a6ba1bd`, `d60ede7d7`, and one more in-flight for the quarantine
  checkbox flip — plan Progress Log deltas (all the fleet-recovery + investigation narrative below is captured there;
  this checkpoint is the condensed pointer).
- `unified-trading-pm/plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md` — new design doc:
  DERIBIT combo instruments mispartitioned as perpetual/future. Measured scope **15,119 rows** (76x the plan's original
  23/787 estimate) across TWO partitions (8,849 `instrument_type=perpetual` + 6,270 `instrument_type=future`),
  root-caused to `TardisAdapter._classify_row_instrument_type` (`tardis_adapter.py:354-402`) having a combo-aware guard
  scoped to `venue=="DERIBIT-COMBO"` only — the fix in `tardis_bulk_download.py` never reached the primary per-shard
  path (`tardis_cefi_shards.py`), so **this is a still-open write leak, not purely historical**: new bare-DERIBIT combo
  captures keep landing mispartitioned TODAY. Distinct mechanism from fail-hard §5.1 (chain-bundle whole-lane issue) —
  this is the per-symbol single-instrument lane, path+content+manifest-key all wrong together. The doc's own §7 todos
  (P1 write-path-leak fix, P2 partition-move dry-run, P2 operator sign-off) are the source of truth — **the
  cross-reference todo line this doc's own agent promised to add to THIS plan's closure-plan table never landed (PM
  branch contention); added just below to close that gap.**
- **would_patch fleet (surface B) reached ALL_DONE**: 74/74 shards, 0 running, 348 benign errors (290× 404 stale-wire +
  53× 503 + 5× 500 transient — same 2 classes throughout). Along the way:
  - **Found + fixed a real bug in `~/cefi_content_fleet/wp_fleet_scan.py`**: `live_vms()` queried
    `compute_v1.aggregated_list()` without filtering `inst.status == "RUNNING"` — a SPOT-preempted VM stays `TERMINATED`
    (not deleted) in GCE, so it read as "alive" forever. This silently masked **11 of 74 shards** being preempted for
    **hours** (wp33 ~7h, wp30 ~4h, others less). Fixed with a one-line status filter; verified the fix immediately
    re-classified all 11 as `GONE(preempt?)` on the next scan.
  - Recovered all 11 per the mandatory PROGRESS-checkpoint rule (never replay START_DATE): read each shard's last real
    GCS-log progress line, computed a safe resume day via the fleet's own `resume_day.py` (file-density curve −
    8,000-file safety margin), deleted the stale `TERMINATED` VM objects, relaunched all 11 SPOT from their resume
    points. One of them (wp21) was preempted a SECOND time; its GCS log was ALSO stale (see next bullet), so it was
    restarted from the SAME resume point rather than guessed forward — completed cleanly on the second attempt.
  - **Found a SEPARATE, second monitoring bug**: a relaunched VM's `vm-exec-with-gcs-tee.sh` log-upload does not refresh
    an existing GCS blob path after a same-named VM is deleted + recreated — the blob stays frozen on the pre-preemption
    content even though the local process is genuinely alive and progressing (confirmed via direct SSH on every one of
    the 11). Cosmetic only (no data/process impact), root cause not further diagnosed (deployment-service-owned script).
    New tool `~/cefi_content_fleet/check_relaunched_via_ssh.sh` works around it via direct SSH health-checks — used
    repeatedly this session to ground-truth "is it really stalled or just monitoring-blind."
  - Restarted the fleet watchdog itself once (found dead — see lessons below), confirmed alive (final PID `55259`)
    through to ALL_DONE.
  - **Resumed the fleet agent** (`ae18c5ef1b16bc8e8`) via SendMessage on ALL_DONE to self-drive: error-reconciliation
    (348) → 4-surface verifier re-measure → LATE colliding-venue renames (SERIALIZED — race avoidance) → MID window →
    KRAKEN-SPOT structural repair → 1,697 colon_wire → loop-until-dry (2 consecutive clean passes) → flag the main loop
    for consolidator drain + v2 apply. Briefed it on both monitoring bugs + that UAC/mtds have moved.
- **mtds fail-hard write-guard fix (STRUCTURAL-only enforce + Stage-0 ID_FORM observe-log) — IMPLEMENTED, NOT YET
  SHIPPED.** Extracted a shared `enforce_structural_and_observe_id_form()` helper into
  `market_tick_data_service/engine/orchestrator/symbol_rules.py` (all 3 callsites — `partitioned_writer.py`,
  `websocket_runner.py`, `book_microstructure_handler.py` — now call it; this also fixed a 900-line file-size-cap
  violation my original 3-file inline version caused). Sitting uncommitted in the SAME shared mtds tree as the A-iso
  agent's work (see below) — blocked on ITS gate, not mine.

### CROSS-REFERENCE TODO ADDED (closing the gap found during this pre-compact audit)

- [ ] [DATA] P1. DERIBIT combo mispartition — read the design doc
      `plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md` in full before touching this. Two
      DISTINCT actions: (a) **[WRITER] fix the still-open write-path leak** (widen the combo-shape guard in
      `tardis_cefi_shards.py` so new captures stop landing mispartitioned — safe to ship alone, no data motion) — do
      this FIRST, independent of (b); (b) **[DATA] the partition-MOVE for the existing 15,119 mispartitioned rows** —
      needs **explicit operator sign-off on the specific plan** (operator has seen the finding in chat and acknowledged
      it, but has NOT yet signed off on the actual `--apply` — do not execute (b) without a fresh, explicit go-ahead on
      the doc's §7 plan).

### DEFERRED WORK after 2026-07-22 ~05:00Z

| Item                                                                                                                                      | State / why deferred                                                                                                               | Blocked on                                                       |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| mtds fail-hard write-guard + A-iso per-shard isolation (both code-complete)                                                               | **not done** — uncommitted, blocked on A-iso agent's own `QUALITY_GATE_BYPASS_AUDIT.md` entry for its new broad-except             | A-iso agent (`ab49320a9e5de78fb`) finishing its own gate         |
| 658 ambiguous catalogue wire-key de-dup (P0)                                                                                              | **not done** — fenced to a different agent from earlier in the session; NOT checked this session, status genuinely unknown         | that agent / needs a fresh status check                          |
| OKX-SPOT fiat-quote + COINBASE-SPOT crypto-quote + BITGET-FUTURES CME-letter-month catalogue gaps (~422 objects, P0)                      | **not done** — same fence, same unknown status                                                                                     | same                                                             |
| LIGHTER-ZKSYNC market-index → symbol map (~11,283 objects, P1)                                                                            | **not done** — not touched this session                                                                                            | data-pipeline work, unclaimed                                    |
| Fail-hard design doc §5 three gaps (derivative/chain-bundle column gate; live-lane dual-resolver reconciliation; read-marker disposition) | **not done** — genuine unresolved DESIGN gaps, explicitly required before Stage 1 write-enforce can ship; not started this session | needs a design pass, not yet scoped to an agent                  |
| DERIBIT combo write-path leak fix (see cross-ref todo above)                                                                              | **not done** — root-caused, not yet fixed; safe to ship alone whenever picked up                                                   | nobody yet — should be next after A-iso ships (same file family) |
| DERIBIT combo partition-MOVE `--apply` (15,119 rows)                                                                                      | **operator-owned** — design is ready, needs explicit sign-off on the specific plan                                                 | operator decision                                                |
| Fleet self-drive chain (error-recon → verify B → LATE renames → MID → KRAKEN-SPOT → colon_wire → loop-until-dry)                          | **cannot be done yet** — in progress, agent self-driving, no poke needed unless it stalls                                          | fleet agent `ae18c5ef1b16bc8e8`                                  |
| Consolidator drain + v2 manifest apply                                                                                                    | **cannot be done yet** — gated on the self-drive chain finishing; main loop coordinates the drain itself                           | self-drive chain completion                                      |
| Final 4-surface done-state proof + plan archival                                                                                          | **cannot be done yet** — the actual finish line, gated on everything above                                                         | all of the above                                                 |
| chain-drop WRITER companion (UTL `_ROW_KEY_COLUMNS`/MTDS stop stamping `chain` for cefi)                                                  | **operator-owned** — fleet-wide shard-atom schema change                                                                           | operator decision                                                |
| `uts-prod-tarball-cleanup-cron` resume                                                                                                    | **cannot be done yet** — pre-dates this session's work, blocked on a base-image rebuild chain unrelated to cefi                    | UTL base-image republish (separate thread)                       |

**RECOMMENDED NEXT:** (1) nudge/wait for the A-iso agent to finish its gate and ship — this unblocks the single
highest-value backfill-safety item (per-shard isolation); (2) once shipped, pick up the DERIBIT combo write-path-leak
fix (same file family, same agent context would be efficient); (3) get a fresh status check on the fenced catalogue-gap
agent (658 keys + ~422 objects) since it was never touched this session and its state is genuinely unknown; (4) keep
waiting on the fleet agent's self-drive chain — do not poke it, it owns its own pacing.

### LESSONS (carried forward — 6 distinct fleet-monitoring failure modes this session, full detail earlier in this doc)

1. `compute_v1.aggregated_list()` returns ALL instances regardless of status — any liveness check against it MUST filter
   `inst.status == "RUNNING"` explicitly, or a preempted SPOT VM reads as healthy forever. This is the single biggest
   lesson: it silently cost ~4-7h of wall-clock on 11 shards while every layer of monitoring (the watchdog, my own
   manual scans) reported healthy.
2. A relaunched (same-name, delete+recreate) VM's GCS log-upload can silently fail to refresh — ground-truth via direct
   SSH, don't trust the GCS log alone for a just-relaunched shard.
3. A flat progress metric across 2+ genuinely-independent scans (not just a stale cached read) is a real stall signal —
   investigate immediately, don't assume "still warming up" past the second confirmation.
4. `/compact` can kill a `run_in_background`-tracked watchdog process even though the underlying shell had no crash
   condition — after ANY compaction or long gap, `ps`-verify a long-lived monitor is alive before trusting its log's
   staleness as "nothing happened." Prefer `nohup ... & disown` over the harness's background-tracking for monitors that
   must outlive a single turn.
5. A watchdog exiting cleanly on `NEEDS_RELAUNCH`/`ALL_DONE` is WORKING AS DESIGNED, not crashing — check the verdict
   before assuming a dead PID means a bug.
6. Committing to the PM repo's `live-defi-rollout` branch during a period of heavy multi-agent activity can take 25-100+
   retry attempts (observed: one commit needed 55 attempts, another 41, another gave up at 320+ across 4 batches before
   finally landing) — this is NORMAL under load, not a sign of a broken retry loop; use patient background retries
   (10-20s spacing, 60-120 attempts) rather than escalating or trying to bypass the branch-drift hook.

### DELTA — 2026-07-22 ~06:20Z (4-surface verifier MEASURED FAIL — corrects the "near done" read; KRAKEN-SPOT collision root-caused)

**CORRECTION to the 3rd checkpoint's framing above**: "would_patch fleet ALL_DONE" was Surface B (parquet
`instrument_id` column) only. It does NOT mean the migration is close to done overall. The fleet agent's 3 background
jobs (KRAKEN-SPOT full-corpus dry-run, live-lane apply, 4-surface verifier) all finished mid-turn-gap — its own task
returned `status: completed` with only a "waiting on these 3" note, no synthesis, because these are plain OS-level
background processes (not harness-tracked), so its foreground turn ended before they exited. Main loop watched all 3 to
completion directly (`kill -0` poll loop, 90s cadence) — nothing was lost, but the fleet agent couldn't self-report, so
recording the measured results here directly:

**live_lane_apply (86 objects, 2026-06-23..29): CLEAN SUCCESS.**
`already_canonical=10355 plan=86 unresolved_wire=1138 renamed=86`, 0 unhandled collisions. Manifest rewrite applied (444
relabeled, 2995 honest_unresolved, 89 collapsed_in_dedup); index backed up to
`gs://.../_index/backups/availability_index.pre_cefi_filename_canonical_livelane07220611.parquet` before write.

**verify_cefi_canonical_4surface_2026_07_20.py: RAN TO COMPLETION. `OVERALL: FAIL [A=FAIL B=FAIL C=FAIL D=PASS]`** (7
sampled days: 2025-06-15, 08-15, 10-15, 11-20, 12-15, 2026-02-01, 05-01):

- **Surface A (filename)**: 44.65% canonical (10278/23019) corpus-wide across the sample — and it gets WORSE toward the
  present (92.81% on 2025-06-15 → 23.13% on 2026-05-01). This is the real remaining backlog; the SCRIPT-2
  filename-rename fleet is the mechanism closing it, and it is nowhere near finished.
- **Surface B (column)**: 95.00% (38/40 sampled objects) — consistent with would_patch's own ALL_DONE + its 2 documented
  benign error classes. No new work here.
- **Surface C (manifest dedup)**: 98.24% of non-chain rows canonical, but BOTH verifier probe instruments
  (`BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN`, `DERIBIT:PERPETUAL:AVAX-USDC@LIN`) still carry real duplicate manifest
  rows (old wire-form key rows alongside the canonical row) — the v2 manifest dedup apply has not landed for these.
- **Surface D (reader)**: PASS — `resolve_cefi_instrument_id()` and `read_shard()` both correctly resolve wire-form
  queries to the canonical id regardless of on-disk state. No work needed; confirms the resolver design was already
  correct.

**KRAKEN-SPOT full-corpus dry-run: BLOCKED, `STOP-ON-SURPRISE`, 1157 unhandled collisions.** Planned 155,878 renames —
by far the single largest remaining venue in the whole migration (10,599 already_canonical). Refused to proceed past
dry-run: 1157 targets already exist as a "distinct" object per `_resolve_group_collisions()`'s existing-stem check
(`scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py` ~line 382).

**Root-caused before escalating** (sampled 4 colliding pairs — 2020-01-01 ATOM-USD/ETH-USD/XRP-USD + 2026-02-03 AAVE-USD
— downloaded both objects per pair, compared with pandas): identical row count/shape, ALL non-`instrument_id` columns
byte-identical (`.equals()` True) in every sample; object sizes matched exactly (checked via
`gcloud storage objects describe --format='value(md5Hash,size)'` as a cheap pre-filter before downloading). The ONLY
difference is the `instrument_id` column value — the canonical-named file already carries the fully-correct id; the
still-present wire-form file carries an older/half-fixed one. **Conclusion: these are not genuinely distinct instruments
colliding — they are the would_patch fleet's own output.** would_patch writes its column-patched result to a NEW
canonical-filename object rather than patching in place, and never deletes the wire-form original. Every one of the 1157
collisions is (very likely) exactly this: a stale wire-form duplicate whose data is now fully redundant with an
already-correct canonical copy sitting next to it — same failure shape as the fail-hard doc's precedent at
`_resolve_group_collisions()`'s mislabel-exclusion branch (line ~358), just a different resolvable class.

**Action taken**: did NOT touch `migrate_cefi_tardis_filename_canonical_2026_07_17.py` myself — it already carries the
fleet agent's own uncommitted, well-documented WIP (the Kraken slash-tolerance regex fix for ~25,131 `ATOM/USD`-style
GCS-pseudo-dir paths the old regex silently failed to parse, aka "MID window", + a `--manifest-only` Phase-B mode for
the paired manifest rewrite after a wide-parallel `--skip-manifest` rename fleet) — neither overlaps
`_resolve_group_collisions()`. Resumed the fleet agent via `SendMessage` (task had returned `completed`, not paused)
with the full verifier/dry-run results + the confirmed root cause + the ask: extend `_resolve_group_collisions` so a
`target collides with existing distinct object` case is content-compared (all columns except `instrument_id`) before
halting — match → delete the stale wire-form source (matching the existing `deleted_dup_source` outcome path, line
~330); no match → keep the existing STOP-ON-SURPRISE halt (never observed a mismatch in the 4 samples, but must not
assume it can't happen at 1157-collision scale). Then re-run the KRAKEN-SPOT dry-run clean before applying the 155,878
planned renames.

**Also in flight**: kicked off `bash scripts/quality-gates.sh --no-fix` on mtds (read-only check, not a commit) to see
whether the A-iso agent's `QUALITY_GATE_BYPASS_AUDIT.md` entry (the `_write_one_cefi_shard` writer-close-on-failure
cleanup justification) is now complete — the diff read as a finished, properly-justified entry, not a stub, but no QG
process for mtds was actually running at the time of the check (only an unrelated tab-1 deployment-service QG was), so
this needs the read-only run's result to confirm before the write-guard + A-iso commit batch can ship.

### REVISED REMAINING QUEUE (supersedes the "REMAINING QUEUE" list above — the corpus-fraction numbers are now measured, not assumed near-complete)

1. Fleet agent (resumed): implement the KRAKEN-SPOT collision content-compare fix, re-run dry-run to zero surprises,
   apply the 155,878 planned renames — the dominant remaining Surface-A item by a wide margin.
2. Ship the mtds write-guard + A-iso per-shard-isolation commit batch once the read-only QG check confirms green.
3. Surface C: land the v2 manifest dedup apply for the still-duplicate rows (confirmed present on both verifier probe
   instruments) — this is the consolidator-drain-gated apply already planned; the verifier now gives concrete
   before-numbers to diff against after.
4. Re-run `verify_cefi_canonical_4surface_2026_07_20.py` after (1)-(3) land — expect Surface A to jump substantially
   once KRAKEN-SPOT's 155,878 renames apply (it is likely the single largest venue in the corpus), but do NOT assume
   ALL_DONE without re-measuring; the 44.65%→FAIL number was a real corpus-wide measurement, not an estimate.
5. Fresh status check on the fenced catalogue-gap agent (658 keys + ~422 objects) — still genuinely unknown this
   session.
6. DERIBIT combo write-path leak fix — still open, still safe to ship alone.

### NEW LESSON

7. A sub-agent whose background `Bash` calls (`run_in_background`) are still running when its own foreground turn ends
   shows as harness `status: completed`, not `paused` — but the underlying OS processes are NOT killed; they are plain
   child processes of the shell, independent of the agent's LLM loop. Don't read "completed" as "these background jobs
   died with it" — `ps`/`kill -0` the actual PIDs before assuming lost work, and prefer `SendMessage` to resume the
   agent with the real results over re-doing its investigation solo.

### DELTA — 2026-07-22 ~06:45Z (catalogue-gap fence was NEVER picked up — re-scoped with a fresh live measurement; mtds ship blocked on a live foreign dep)

**Item 5 above answered.** The "removal-probe agent" the 658/~422/LIGHTER catalogue-gap work was fenced to never picked
it up — no commit, no uncommitted WIP, `instruments-service` working tree clean, last relevant commit (`1a73082e`,
2026-07-20, pre-fence) has no dedup/enumeration/LIGHTER code. This was a genuine dead fence, not live work — confirmed
via git log + working-tree state, not assumed.

**The 658-ambiguous-wire-key number is now STALE and understated.** Re-measured live against prod (read-only, no
`--apply`, catalogue-only download via the existing `CeFiWireCanonicalMap` in
`complete_cefi_manifest_canonical_dedup_2026_07_17.py`): **1,018 ambiguous 3-tuple keys**, not 658 — +360, entirely in
DERIBIT (442→802), every other venue unchanged (OKX-FUTURES 146, BYBIT 39, BITGET-FUTURES 18, OKX-SWAP 5,
BINANCE-DELIVERY 4, BINANCE-FUTURES 2, KRAKEN-FUTURES 2). Catalogue rows also grew 428,625→429,129. This is the expected
shape of "moving target" already documented in the 2026-07-20 investigation, just not re-checked since — confirms
non-completion positively (if the dedup fix had landed, the count would have DROPPED toward zero, not risen).

**The ~422 catalogue-enumeration-gap number cannot be re-verified** — it was a one-off manual venue-by-venue sum from a
2026-07-20 chat session; no committed script computes it. Re-scoping below adds "build the measurement script" as its
own first step rather than re-deriving the count by hand again.

**LIGHTER-ZKSYNC market-index → symbol map: confirmed zero code** — grepped
`instruments_service/reference_data/adapters/cefi/lighter.py` (203 lines) + adjacent modules for "market_index"/
numeric-stem handling, zero hits.

**Re-scoping (the dead fence is retired; these are now live todos, not a fence)**:

- `[DATA] P1.` De-dup the (now 1,018, growing) ambiguous wire-key 3-tuples in
  `instruments-service/scripts/build_instrument_catalogue.py` — target the CURRENT measured count, not the stale 658;
  DERIBIT is 79% of it and the only venue still growing, so start there.
- `[SCRIPT] P2.` Build the missing catalogue-enumeration-gap measurement script (OKX-SPOT fiat-quote, COINBASE-SPOT
  crypto-quote, BITGET-FUTURES CME-letter-month gaps) — the ~422 figure has no re-measurable SSOT today; this must exist
  before the gap itself can be fixed or even re-confirmed.
- `[DATA] P2.` Add a LIGHTER-ZKSYNC market-index → symbol map (~11,283 objects, 93.5% of stems are bare numeric indices
  with no catalogue key) — greenfield, no prior code to build on.

**Separately**: the mtds write-guard + A-iso isolation + KRAKEN-SPOT collision-fix batch is fully gate-green (confirmed
via a fresh, definitive `quality-gates.sh` run, exit 0 verified directly — not inferred from a piped command's exit
code, which is a trap: `cmd | tail -150` reports `tail`'s exit code, not `cmd`'s, and the first "exit 0" read this way
was wrong) but its first `quickmerge.sh --agent` attempt FAILED at Pre-Flight: a path dependency,
`unified-api-contracts`, has uncommitted changes to `defi_venues.py`/`test_venue_key_parity.py` with a 33-second-old
mtime and an actively-running sibling QG process on those exact files — a live claim, not a dead one (confirmed via
`ps` + mtime, per the liveness-gating rule). Correctly did NOT inherit/force through; a watchdog is polling for that
dependency to clear and will auto-retry the mtds quickmerge once it does.

### DELTA — 2026-07-22 ~09:20Z (KRAKEN-SPOT dry-run v2 died silently mid-run; unified-api-contracts still not clear after 150+ min; DERIBIT dedup fix rebased under us)

**KRAKEN-SPOT collision-fix dry-run (v2) crashed with no error/traceback.** Re-run after the collision-dedup fix landed
in the working tree (still uncommitted, but fully runnable — see below), it correctly hit hundreds of `[DUP-CONFIRMED]`
resolutions (each requiring a full download+pandas-compare of BOTH the wire-form and canonical-form parquet objects) but
the process (PID 65360) was simply gone at the next check — no `SCRIPT 2 FILENAME RENAME SUMMARY`, no Python traceback
in the log, no obvious OOM signal found in the system log (macOS's OOM killer sends SIGKILL silently, which is
consistent with what was observed but not confirmed). Day `2026-02-03` alone produced a long, dense run of confirmed
duplicates (44MB+ objects per the earlier AAVE-USD sample) — `_confirm_would_patch_duplicate` downloads and holds two
full dataframes per collision with no explicit release between iterations, which is the prime suspect if this recurs.
**Relaunched as v3** (`kraken_spot_dryrun_full_v3.log`) with an explicit exit-code capture this time so a repeat death
is diagnosable instead of silent. `[SCRIPT] P2.` if v3 also dies without a clear cause, add explicit
`del df; gc.collect()` between collision-comparison iterations in `_confirm_would_patch_duplicate` (or process the
collision list in smaller batches) before assuming it's just slow.

**CORRECTION (v3's death gave the real answer, retract the OOM guess)**: v3 crashed too, but this time WITH a clear
traceback — `requests.exceptions.ConnectionError` / `NameResolutionError("Failed to resolve 'storage.googleapis.com'")`.
That's a machine-wide DNS/network outage, not a memory bug — consistent with the same window this session's own
Anthropic API calls also failed with `ENOTFOUND`. v2's silent death (no traceback) was almost certainly the SAME root
cause hitting at a moment/code-path that didn't surface a clean exception. The `_confirm_would_patch_duplicate` memory
concern above is retracted as the likely cause (still a fine hygiene improvement, just not the actual bug here).
Relaunched as v4 once connectivity was reported restored.

**Realization: the git-ship blocker does NOT block running the migration** — the collision-fix code works from the
working tree regardless of commit state; resumed the fleet agent to keep driving KRAKEN-SPOT + its self-drive chain
locally rather than waiting on `unified-api-contracts` to clear. The git-ship (durability) and the actual data-migration
execution are independent and should not be conflated.

**`unified-api-contracts` still hasn't cleared after 150+ minutes / 4 watchdog cycles** (15/30/45/60 min, each ending in
the same 2 dirty files). Confirmed genuinely live throughout (owning process alive; its dirty file SET actually grew to
6 files at one point then shrank back to 2 as it shipped an unrelated honest-coverage commit `7338fa65` — proof of real,
ongoing activity, not a stalled/abandoned session). A 5th, 90-minute watchdog is now running.

**Caught a real bug in my own tooling before it mattered**: the DERIBIT dedup fix's commit sha (`9aed4343`) silently
changed to `a4b4b6e4` — some other process did a `git pull --rebase` on the shared `instruments-service` checkout, which
replays local commits onto a new base and changes their sha (content preserved, hash not). A ship-watchdog that
hardcodes a commit sha to look up its message will break the moment that happens. Fixed by resolving via `HEAD` +
`rev-list --count origin/live-defi-rollout..HEAD` instead of a fixed sha — **any tooling that references "my last
commit" in a shared multi-agent checkout must re-resolve by HEAD, never cache a sha across a wait.**

### DELTA — 2026-07-22 ~17:25Z (5th watchdog cycle DID clear + attempted ship — hit a real merge conflict from a concurrent sibling session sharing this checkout; resolved carefully, did not lose anyone's work)

**The specific 2 files being watched DID finally clear** (~90 min in, check 22/27) — but the mtds quickmerge attempt
still failed, this time for a NEW reason: `unified-api-contracts` had a _different_ dirty file
(`tests/internal/unit/test_schema_contracts.py`) by the time Pre-Flight actually ran — the same sibling session moved on
to editing something else. **Lesson: watching 2 specific paths was the wrong scope from the start** — quickmerge's
Pre-Flight checks the dependency's ENTIRE working tree, not specific files; a narrower watch will always eventually
"clear" on the paths it's watching while the dependency is still genuinely dirty elsewhere. Should have watched
`git status --porcelain` (full) from the start, not 2 hardcoded paths.

**More seriously**: quickmerge's own internal `git pull --ff-only` + the prek stash-based hook mechanism (stash unstaged
changes → run checks → pop) collided with a DIFFERENT concurrent sibling session that was live-editing files in this
SAME shared `market-tick-data-service` checkout (no worktree isolation between concurrent Claude sessions on this tab).
Two distinct problems surfaced from one stash/pop cycle:

1. **A genuine, unresolved merge conflict** landed in the working tree (the standard git 3-way conflict-marker sequence
   — "updated upstream" / "stash base" / "stashed changes" sections) in
   `market_tick_data_service/engine/orchestrator/partitioned_writer.py`, between an upstream commit (`04222eb0`,
   cefi-chain v6 quote/margin-tail generalization of `_assert_canonical_chain_path`) that landed via the
   `pull --ff-only` and my own uncommitted write-guard refactor of the SAME function. Read both sides, understood the
   upstream commit's intent (generalizing tradfi-only → tradfi+cefi) was orthogonal to mine (replacing the inline
   `canonical_path_violations` check with the shared `enforce_structural_and_observe_id_form` helper), and merged them
   by hand: kept upstream's now-generalized docstring/scope, applied my helper call within it
   (`identity="tradfi/cefi chain path"`). Verified zero remaining conflict markers repo-wide + a clean `ast.parse` on
   every touched `.py` file before proceeding.
2. **3 completely unrelated files got swept into MY staged index**: `_gas_fee_helpers.py`, `gas_fee_handler.py`,
   `tests/unit/test_gas_fee_handler.py` — genuine, substantial, unrelated work (a documented
   `gas_fees_crash_loop_freshness_warmup_hang_2026_07_22` incident fix: a `NamedTuple`-based freshness-context refactor
   - a bounded-timeout fix for a Cloud Run job crash-looping against an in-flight manifest-consolidator merge). This is
     NOT mine and was never in my `--files` list — some OTHER live sibling session's uncommitted work got staged as a
     side effect of the SAME stash/pop cycle. **Unstaged it (`git reset HEAD --`), did NOT discard or touch its
     content** — it stays in the working tree, unstaged, for its actual owner to find and commit themselves. Confirmed
     my own 12 files remained correctly staged throughout and re-marked the conflict file resolved (`git add`) only
     after fixing its content.

**No data was lost on either side** (my write-guard intent, upstream's cefi-chain generalization, or the foreign gas_fee
fix all survive in the working tree) but this is a real, repeatable hazard of quickmerge's own git plumbing operating on
a checkout shared by concurrent, unisolated Claude sessions — **`git status --porcelain` after ANY quickmerge attempt
(successful or not) should be treated as untrusted until re-verified**, since the attempt's own internal git operations
can silently entangle unrelated concurrent work. Re-ran a fresh `quality-gates.sh --no-fix` from scratch post-resolution
before attempting to ship again — do not trust the earlier "confirmed gate-green" result, it predates this entire
conflict.

### DELTA — 2026-07-22 ~18:30Z (mtds batch SHIPPED; CRITICAL near-miss — the DERIBIT dedup commit was silently wiped by an external hard-reset on the shared instruments-service checkout, recovered from reflog)

**mtds batch shipped clean**: `market-tick-data-service@e49e1395` — write-guard + A-iso per-shard isolation +
KRAKEN-SPOT collision auto-resolve, all landed on `live-defi-rollout` once `unified-api-contracts` finally went fully
clean. The improved watchdog (full `git status` scope, not 2 hardcoded paths) worked as intended.

**Then the instruments-service DERIBIT dedup fix (previously verified safe-to-ship, `9aed4343`→rebased to `a4b4b6e4`)
turned out to be GONE — not rebased-again, genuinely absent from `git log --all`.** `git reflog` on
`instruments-service` told the real story: the commit was rebased a THIRD time (`a4b4b6e4`→`8e67514c` via another
`pull --rebase --autostash`), then **`HEAD@{2}: branch: Reset to origin/live-defi-rollout`** — some external process
(not me, not any agent I dispatched) did a hard reset of the local branch straight to `origin/live-defi-rollout`,
discarding the locally-committed-but-unpushed `8e67514c` outright. This is a genuinely dangerous pattern on a
multi-agent-shared checkout: a _committed_ fix, already adversarially verified and gate-green, silently vaporized by
something resetting the branch rather than fast-forwarding or rebasing. **Suspect: whatever cron/sync mechanism keeps
slot checkouts current with origin** (`slot-cron-ff-pull.sh` per the per-tab-worktrees codex) **may fall back to a hard
reset when a plain `pull --ff-only` can't fast-forward past local commits, instead of erroring loud or rebasing** — this
needs an operator look, since it can eat ANY agent's locally-committed, not-yet-pushed work with zero warning.
`[INFRA] P1.` flag this to codex/operator: audit `slot-cron-ff-pull.sh` (and any other cron touching these checkouts)
for a hard-reset fallback path and make it fail loud instead.

**Recovered without any further loss**: `8e67514c` was still a real object (unreachable but not GC'd) — confirmed via
`git cat-file -t` + a content check for `_dedup_cefi_expiry_off_by_one`, cherry-picked cleanly onto current HEAD as
`f7bb9556` (0 conflicts, 417 insertions matching the original), and — learning from just having watched this exact class
of loss happen — immediately pushed a `backup-deribit-dedup-fix-2026-07-22` branch to origin as a durable safety net
BEFORE re-running quality-gates.sh, so even a repeat reset can't destroy it again while gates run. **Lesson: once a fix
is confirmed correct and verified, get it onto origin (a backup branch counts) before doing anything else that takes
wall-clock time** — a locally-committed-only fix is not safe on a checkout other processes can reset.

### DELTA — 2026-07-22 ~19:50Z (all 3 queued code fixes now SHIPPED; KRAKEN-SPOT v4 survived the dense-day zone that killed v2)

**Three independently-verified fixes all landed durably on origin this session:**

1. `market-tick-data-service@e49e1395` — write-guard (`enforce_structural_and_observe_id_form`) + A-iso per-shard write
   isolation + the KRAKEN-SPOT would_patch-duplicate collision auto-resolve.
2. `instruments-service@9956c36a` — DERIBIT ambiguous-wire-key dedup (802→0), after the hard-reset near-miss recovery
   documented above.
3. `market-tick-data-service@2ddc6d4a` — DERIBIT bare-venue combo write-path classification fix (§9 `[WRITER] P1.` of
   `deribit_combo_perpetual_partition_move_2026_07_21.md`), which needed two follow-on rounds after its own implement
   pass: (a) an unrelated stale DEFI shard-count baseline (2673→2592, `test_rule11_per_ag_shard_counts_byte_unchanged`)
   was blocking `quickmerge --agent`'s sentinel for every MTDS commit — this resolved itself when a concurrent sibling
   session shipped the identical fix (`0fcfa803`, same root cause `uac@9a047a31`, same reconciled arithmetic) while a
   dispatched agent was independently verifying it; the agent correctly recognized the duplicate and discarded its own
   redundant edit rather than double-shipping; (b) the combo fix's own diff then tripped the codex file/function-size
   caps (`tardis_shared.py` 907>900 lines, `_classify_row_instrument_type` grown to 73 lines) — fixed with a pure
   code-motion extraction (`_classify_deribit_venue_row` helper, mirroring the `enforce_structural_and_observe_id_form`
   extraction pattern from earlier the same day), verified zero behavior change via diff-against-backup-branch, then
   shipped clean.

**KRAKEN-SPOT dry-run v4 survived the exact zone that killed v2** — it's now past `2026-02-03` (the dense day with the
long `[DUP-CONFIRMED]` run) into `2026-02-05`/`02-06`, still alive, still correctly auto-resolving collisions. Not yet
complete; still monitoring for the `SCRIPT 2 FILENAME RENAME SUMMARY` completion marker.

**Pattern that repeated 3 times this session, now the standing practice**: implement → independent adversarial verify
(re-check the actual diff/data, never trust the self-report) → ship only if verified safe → for anything sitting
local-committed-but-unpushed on a shared checkout, push a throwaway backup branch to origin BEFORE any further
wall-clock-consuming step, delete it only after confirming the real content (diff, not just message — shas keep moving
under concurrent rebases) is genuinely an ancestor of `origin/live-defi-rollout`.

### DELTA — 2026-07-22 ~21:05Z (deferred-work item 4 partially SHIPPED via dispatched workflow; a genuine SSOT contradiction found and referred to operator, not silently resolved)

While KRAKEN-SPOT dry-run v4 continued running (past `2026-02-06`, still healthy), dispatched a workflow
(`wf_2550fc3e-f59`) to investigate item 4 of the deferred-work table below (residual ~216 ambiguous CeFi wire-keys) in
parallel — an explicitly independent side-track per that table's own "Recommended next" note.

**Root-caused all 5 assigned venue groups** (parallel investigate phase, one agent per group, each re-measuring against
a fresh live `prod/catalog.parquet` pull rather than trusting the existing docstring):

- **BINANCE-DELIVERY (4), BINANCE-FUTURES (2), KRAKEN-FUTURES (2)**: identical mechanism to the already-shipped DERIBIT
  off-by-one-day bug, just with a numeric `YYMMDD` wire-date encoding the existing parser didn't recognize. **Fixable —
  confirmed and shipped** (see below).
- **OKX-FUTURES (146 total)**: splits into two sub-patterns — 76 are the same numeric-date off-by-one shape (fixable,
  shipped), 70 are a linear-vs-inverse `margin_type` collision (see the SSOT-contradiction finding below — NOT shipped,
  referred to operator).
- **OKX-SWAP (5)**: same `margin_type` collision shape as OKX-FUTURES's other 70 — NOT shipped, referred to operator.
- **BYBIT (39)**: NOT a date-format issue at all — 36 are a base-asset PARSING regression between two catalogue-build
  generations (`_split_bybit_symbol` fix landed after older rows were already written); the other 3 are two genuinely
  distinct real products (a closed 2019-2020 linear market + a separate still-active inverse market) sharing one
  unmarked wire spelling — correctly excluded, not a duplicate. Confirmed `fixable: false` for different reasons per
  sub-case; not implemented (out of the narrow same-shape pattern used for the DERIBIT/numeric-date fixes).
- **BITGET-FUTURES (18)**: a _different_, already-fixed (`75bdf02d`, 2026-07-14) historical `margin_type` mislabel,
  analogous to the OKX finding below but confirmed separately — also NOT shipped (needs the same kind of explicit
  ignore-list-widening decision, not folded silently into the existing helper).

**Shipped**: `instruments-service@bf5322bb9` — extended `_dedup_cefi_expiry_off_by_one()`'s check #4 with a numeric-
`YYMMDD` wire-date parser fallback (reusing the CeFi Tardis adapter's own already-tested
`_parse_yymmdd_symbol_expiry`/`_parse_underscore_yymmdd_symbol_expiry`, not reimplemented), collapsing BINANCE-DELIVERY
(4→0), BINANCE-FUTURES (2→0), KRAKEN-FUTURES (2→0), and OKX-FUTURES's pure off-by-one sub-pattern (76→0) — **84 of the
216 residual ambiguous wire-keys resolved, 132 remain**. Independently adversarially verified (re-measured against the
real prod catalogue, spot-checked 5 real collapsed row-pairs plus the untouched margin_type cases, re-ran
`quality-gates.sh` fresh — exit 0 captured directly, not through a pipe) before shipping. Confirmed `bf5322bb9` is an
ancestor of `origin/live-defi-rollout` post-ship.

**SSOT contradiction found, NOT silently resolved**: the shipped `_dedup_cefi_expiry_off_by_one()` docstring (commit
`9956c36a`) classifies the OKX-FUTURES/OKX-SWAP margin_type collision (75 of the 216 keys) as "a REAL, different
ambiguity ... correctly ... stay excluded." The investigation found zero-exception evidence across all 75 pairs that
this is instead a stale artifact of an already-documented, already-fixed 2026-07-09 margin_type mislabeling bug
(`_infer_margin_type()` in `instruments_service/reference_data/adapters/cefi/tardis/parsing.py`). Because this is a
substantive economic-identity-field question (not a housekeeping timestamp) where a wrong call would silently merge two
real distinct instruments, the workflow's implement/verify agents both explicitly declined to act on it and flagged it
for operator review instead of guessing either direction. Filed as
`plans/active/issues/cefi_okx_margin_type_wire_key_ambiguity_reclassification_2026_07_22.md` — **operator sign-off
required before anyone builds that dedup rule.**

### DELTA — 2026-07-23 ~08:00Z (KRAKEN-SPOT apply: 2 safe near-misses, hardened, attempt 3 in flight; BYBIT dedup SHIPPED in parallel)

**KRAKEN-SPOT `--apply` (item 1) — user-confirmed to proceed after the dry-run's clean pass (157,035 planned renames, 0
unhandled collisions). Two apply attempts hit isolated, non-data transient failures, both caught safely by the script's
own STOP-ON-SURPRISE guard before any GCS mutation:**

- **Attempt 1** (`stamp=20260722T2302Z`): aborted with `PYTHON_EXIT=4` on 1 unhandled collision
  (`day=2026-02-15`/`book_snapshot_5`/`ETH-USD`). Root-caused via the log's own `dup-duplicate-confirm READ FAILED`
  line: `Connection broken: IncompleteRead(2097152 bytes read, 93500735 more expected)` — a dropped connection ~2MB into
  a ~95MB parquet download, NOT a genuine content mismatch. Verified via direct GCS spot-check (`gsutil stat`/`ls`) that
  zero renames/deletes occurred — confirmed by reading `main()`'s actual control flow: the `sys.exit(4)` fires inside
  `if surprises:`, strictly BEFORE `run_gcs_merge`/`run_gcs_rename`/`rewrite_manifest` are ever called.
- **Attempt 2** (`stamp=20260723T0236Z`, plain retry, no code change): aborted again, same failure MODE but a DIFFERENT
  object (`day=2026-02-12`/`book_snapshot_5`/`ETC-USD`) — confirming this is a recurring, not one-off, network-flakiness
  cost of one-shot large-file (~95MB) downloads inside `_confirm_would_patch_duplicate` over a multi-hour
  single-threaded run, not a corrupt/anomalous object.
- **Fix shipped**: `market-tick-data-service@b6e2ce1d` — added a 3-attempt retry-with-backoff (2s/4s) around the two
  `download_bytes` calls in `_confirm_would_patch_duplicate`; still returns `None` (safe "never assume" fallback,
  STOP-ON-SURPRISE still fires) if all 3 attempts fail — no weakening of the safety guarantee, purely resilience against
  transient reads. QG green (206s), shipped via quickmerge.
- **Attempt 3** (`stamp=20260723T0612Z`, with the fix live): launched, passed the catalogue gate, running healthy
  through the dense `2026-02-03` day at last check — in flight, being watched.
- **Process note**: the harness's background-task-completed notification reported `exit code 0` for BOTH aborted
  attempts — that is the wrapper shell's exit code (the `echo "PYTHON_EXIT=$?" >> log` line always succeeds), NOT the
  Python script's real exit code, which is `PYTHON_EXIT=4` visible only inside the log itself. This is the exact
  piped/wrapped-exit-code trap already documented earlier this session, now confirmed to also bite a `run_in_background`
  Bash launch, not just a `| tail` pipe — **always grep the log's own `PYTHON_EXIT=` line, never trust a wrapper-command
  notification's reported exit code for a script it merely shells out to.**

**BYBIT base-asset dedup (deferred item 4's "36 fixable" sub-item) — SHIPPED in parallel** while the KRAKEN-SPOT apply
ran: `instruments-service@39e26bfe` — new `_dedup_bybit_future_base_asset_parsing()`, scoped strictly to
`venue=BYBIT, instrument_type=FUTURE`, reusing the already-shipped `_split_bybit_symbol()` to re-parse `raw_symbol` and
drop the stale-generation row whose `base_asset` doesn't match a fresh parse (e.g. `base_asset="BTCUSDT"` instead of
`"BTC"`). Wired BEFORE `_dedup_cefi_expiry_off_by_one` in Phase D so the 7 three-row compound groups (a base-asset
duplicate co-occurring with a genuine off-by-one-day pair) resolve down to exactly 1 surviving row via the composition
of both functions. Independently re-verified: BYBIT ambiguous wire keys **39 → 3** (all 36 FUTURE keys resolved; the 3
PERPETUAL keys — BTCUSD/ETHUSD/XRPUSD, two genuinely distinct real linear/inverse products each — confirmed
byte-identical untouched, zero rows dropped). 9 new tests added. QG green (re-run fresh with the sentinel cache disabled
to force real test execution, twice, both `4808 passed, 0 failed`).

## Deferred work after 2026-07-22 ~20:15Z (pre-compact checkpoint — supersedes the stale "REVISED REMAINING QUEUE" above; items 1/2/5/6 there are DONE, see this session's DELTAs)

| #   | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Kind                                                     | Blocked-on                                                                                                                                                                                                       |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | ~~KRAKEN-SPOT `--apply`~~ — **DONE 2026-07-23 ~15:40Z**. Attempt 3 (with the retry-hardened fix) completed `PYTHON_EXIT=0`: 155,872 auto-renamed + 1,157 stale duplicates deleted; 6 renames hit a transient GCS 503 mid-`copyTo` (never touched by `run_gcs_rename`'s no-retry single attempt) — verified via direct `gsutil stat` that source-untouched/target-absent for all 6, then retried with a tiny script reusing `do_rename()` verbatim; all 6 now confirmed canonical via GCS spot-check. The manifest phase's `honest_unresolved_rows: 3598` figure was investigated and is a NON-ISSUE: confirmed exactly 1 manifest row per (venue, day, instrument_type, data_type) shard atom with `instrument_id=None` — a shard-level completeness marker, not a per-instrument record (per-instrument data lives in the actual GCS files, independently confirmed present + canonical for the sampled shard). **KRAKEN-SPOT Surface A is genuinely, fully clean.** | **DONE**                                                 | Nothing outstanding on KRAKEN-SPOT itself — proceed to item 2                                                                                                                                                    |
| 2   | Fleet agent (`ae18c5ef1b16bc8e8`) continue its self-drive chain: error-recon (348 would_patch errors) → re-run `verify_cefi_canonical_4surface_2026_07_20.py` → LATE colliding-venue renames (serialized) → MID window → colon_wire (1,697) → loop-until-dry (2 clean passes)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Not done                                                 | **UNBLOCKED** — item 1 (KRAKEN-SPOT) is now done; check whether agent `ae18c5ef1b16bc8e8` is still alive (SendMessage to resume) before re-dispatching this chain fresh                                          |
| 3   | Surface C: land the v2 manifest dedup apply — **fresh dry-run 2026-07-24 confirmed clean** (all "MUST be 0" safety invariants pass: 0 captured rows dropped, 0 captured rows left marker-less, 0 lossy chain-merges; DERIBIT-COMBO purge 196/196 matches the operator ruling). Drained the consolidator (`gcloud scheduler jobs pause ...`), but 3 consecutive `--apply` attempts all failed on a genuine, ongoing GCS connectivity degradation (mid-download `ConnectionResetError`/`ChunkedEncodingError`/read-timeout — same pattern independently hit the fleet-reverify and LIGHTER-backfill workflows around the same time, so this is an environment-wide blip, not a script bug). **Zero mutation occurred any attempt** (confirmed: crash is always at the initial catalogue read, before any write path executes) — consolidator RESUMED to a safe state rather than left paused through an uncertain-duration outage                                       | Dry-run: DONE / Apply: blocked on transient connectivity | Retry the drain+apply sequence once GCS connectivity stabilizes — the dry-run itself does not need to be re-run, it's still valid; just re-pause the consolidator and retry `--apply`                            |
| 4   | ~~Residual ~216 ambiguous CeFi wire-keys~~ — **213/216 SHIPPED, DONE**: `instruments-service@bf5322bb9` (BINANCE-DELIVERY 4/4, BINANCE-FUTURES 2/2, KRAKEN-FUTURES 2/2, OKX-FUTURES sub-pattern-A 76/146) + `instruments-service@39e26bfe` (BYBIT FUTURE base-asset-parsing 36/36) + `instruments-service@1c920fab` (OKX-FUTURES sub-pattern-B 70/70 + OKX-SWAP 5/5 + BITGET-FUTURES 18/18 margin_type mislabel, operator-ruled). **3 remain, forever**: BYBIT's 3 PERPETUAL keys — confirmed two genuinely distinct real products (closed 2019-2020 linear + still-active inverse), correctly excluded, not a bug, will never be "fixed"                                                                                                                                                                                                                                                                                                                             | **DONE**                                                 | Nothing outstanding — 216→3, and the 3 are a correct terminal state, not a gap                                                                                                                                   |
| 4b  | ~~OKX-FUTURES (70) + OKX-SWAP (5) + BITGET-FUTURES (18) margin_type wire-key collision reclassification~~ — **SHIPPED 2026-07-23** (`instruments-service@1c920fab`): new `_dedup_cefi_margin_type_mislabel()` reuses the live Tardis adapter's own classifier to keep the correct row, drop the stale pre-fix duplicate. Independently re-verified against a fresh prod snapshot (93→0), BYBIT's 3 PERPETUAL confirmed byte-identical untouched                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **DONE**                                                 | Folded into item 4 above, no longer a separate open item                                                                                                                                                         |
| 5   | ~~Build the missing catalogue-enumeration-gap measurement script~~ — **SHIPPED** (`instruments-service@f6f16785`): re-runnable, bounded-read script generalized to 2 case classes (spot-quote-gap, cme-letter-month-gap). Live-measured 211 gap rows today (OKX-SPOT 174, BITGET-FUTURES 33, COINBASE-SPOT 4) — the stale ~422 figure is retired in favor of this number, independently re-verified with real GCS spot-checks                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Done (measurement) / Not done (the fix itself)           | OKX-SPOT/COINBASE-SPOT need an operator decision on widening UAC's `_CEFI_VENUE_QUOTE_EXTENSIONS`; BITGET-FUTURES just needs a catalogue rollup re-run, no code change — neither fix is built yet, just measured |
| 6   | LIGHTER-ZKSYNC market-index → symbol map (~11,283 objects, 93.5% bare numeric stems)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Not done                                                 | Greenfield, zero code confirmed                                                                                                                                                                                  |
| 7   | ~~DERIBIT combo PARTITION-MOVE P1 prep~~ — **INVESTIGATED, NO CODE NEEDED**: the guard-widen already shipped this session (`mtds@2ddc6d4a`, landed the day after UAC's DERIBIT-COMBO deregistration `uac@11adf279` — synergistic, not conflicting) and `tardis_cefi_shards.py` already shares the fixed classifier (no duplicate code path to port into). The actual 15,119-row `--apply` data MOVE remains fully unstarted and Operator-owned per §7 — this ruling never covered it                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Prep: DONE (no-op) / Move: still operator-owned          | The `--apply` partition-move still needs explicit operator sign-off per `deribit_combo_perpetual_partition_move_2026_07_21.md` §7 — do not start that without a SEPARATE future review                           |
| 7c  | `[INFRA] P2.` **NEW finding, 2026-07-23**: MTDS's own orchestrator (`engine/orchestrator/__init__.py::get_venues_for_asset_groups`, `adapters/umi_tick_provider.py`) still hard-codes `DERIBIT-COMBO` as an active fetchable cefi venue and describes it in comments as "a real UAC-declared cefi venue" — factually stale since UAC deregistered it 2026-07-21 (`uac@11adf279`). Live cross-repo inconsistency, not yet causing known harm but should be corrected so MTDS doesn't attempt to fetch a venue UAC no longer declares                                                                                                                                                                                                                                                                                                                                                                                                                                   | Not done                                                 | Found by the DERIBIT-combo P1 prep investigation (this session); needs its own small fix — update MTDS's venue enumeration to match UAC's registry, verify no live fetch path still targets `DERIBIT-COMBO`      |
| 8   | `[INFRA] P1.` Audit `slot-cron-ff-pull.sh` (and any other cron touching shared slot checkouts) for a hard-reset fallback path that silently discards locally-committed-unpushed work — make it fail loud instead                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Operator-owned                                           | This session's hard-reset near-miss (documented above) is evidence, not a fix; needs an operator/infra owner to investigate the actual cron script                                                               |
| 9   | Final 4-surface done-state re-proof (all of A/B/C/D = PASS on both probe instruments) + plan archival                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Cannot be done yet                                       | Gated on items 1-3 landing — do NOT assume ALL_DONE without re-measuring; the 44.65%→FAIL baseline was a real corpus-wide measurement                                                                            |

**Recommended next**: keep watching item 1 (KRAKEN-SPOT v4) — everything else in the CeFi filename-migration critical
path (items 1-3, 9) chains directly off it. Items 4-6 (catalogue gaps) and 7-8 (operator-owned) are independent
side-tracks that can run in parallel whenever picked up, but are not blocking the critical path.
