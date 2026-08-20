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
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /plans/archive/2026_07/issues/cefi_canonical_blueprint_2026_07_17.md,
  ]
  # 2026-08-19 (na-eligibility-audit): dropped 3 archived-plan citations to satisfy the archive-safety-ratchet gate
  # (active docs must not cite /plans/archive/... in `related:`) — all 3 remain fully preserved as inline body
  # links (the history-part1/part2 pointers appear verbatim in the header blockquote; the line-cap-remediation
  # source is cited in the `source:` field below), so no discoverability is lost.
created: "2026-07-24"
last_updated: "2026-08-19" # 2026-07-25: appended the parent's 4 remaining DELTA sections (01:30Z/01:20Z/05:55Z/13:35Z) + Deferred-work table + Step 8 verdict, completing the migration this file's header always intended
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
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
context_scope:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/issues/cefi_canonical_blueprint_2026_07_17.md,
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part1_2026_07_24.md,
    market-tick-data-service/scripts/verify_cefi_canonical_4surface_2026_07_20.py,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
  ]
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

- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
> **2026-07-18 → 2026-07-20 narrative extracted** (line-cap compliance, 2026-07-24) to
> [`cefi_4surface_migration_execution_log_history_part1_2026_07_24.md`](/plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part1_2026_07_24.md)
> — covers the surface-C manifest cutover/apply, Track-6 resolver fixes, the NO-ORPHANS accounting, the surface-A
> filename census + rename-fleet launch, the double-wrapped-id bug class, the UAC path-oracle stem-blindness finding,
> and the full catalogue-coverage-gap root-cause measurement. Moved verbatim, nothing summarized or dropped.

**Deferred / handoff (each needs a tracked todo before this plan archives):**

- [x] ✅ [SCRIPT] P0. Script 2 `_PATH_RE` must tolerate an embedded-slash wire stem (KRAKEN-SPOT 25,131). FENCED to the
      live rename fleet — needs the fleet owner. The rename is a real GCS move (pseudo-dir → single object). **CLOSED
      2026-08-04 (na-eligibility-audit)**: DONE per the "Deferred work after 2026-07-24 ~13:35Z" table row 1 below
      ("~~KRAKEN-SPOT Surface A~~ — DONE") — 155,872 objects auto-renamed, genuinely fully clean.
- [x] ✅ [DATA] P0. De-duplicate the 658 ambiguous catalogue wire keys (off-by-one expiry duplicates) in
      `build_instrument_catalogue.py`. FENCED to the DeFi removal-probe agent. **CLOSED 2026-08-04
      (na-eligibility-audit)**: DONE per the "Deferred work after 2026-07-24 ~13:35Z" table row 4/4b below ("~~Residual
      ambiguous wire-keys + margin_type mislabel~~ — DONE") — re-measured (658→1,018) then resolved via
      `instruments-service@bf5322bb9`+`@39e26bfe`+`@1c920fab` (213/216 shipped; 3 remain forever, correctly excluded).
- [x] ✅ [DATA] P0. Enumerate the MISSING catalogue rows behind the ≈5,413 healthy-venue residue in
      `build_instrument_catalogue.py` (FENCED): OKX-SPOT fiat-quote pairs (AED/AUD/BRL/TRY), COINBASE-SPOT crypto-quote
      pairs (`-BTC`/`-ETH`), BITGET-FUTURES CME-letter-month dated futures (`BTCUSDH26`). Each measured at 0 catalogue
      rows against on-disk data that exists. **ENUMERATION HALF DONE, FIX HALF STILL OPEN (re-verified 2026-08-05,
      slot-15)**: per table row 5 below ("~~Catalogue-enumeration-gap script~~ — DONE"), a re-runnable measurement
      script (`instruments-service@f6f16785`) shipped and live-measured 211 gap rows, retiring this stale ~5,413/~422
      estimate — the enumeration half is genuinely done. The underlying fix (adding the missing catalogue rows) is
      separately tracked and still open: OKX-SPOT/COINBASE-SPOT stays human (needs operator decision on widening
      `_CEFI_VENUE_QUOTE_EXTENSIONS`, no defined target yet); BITGET-FUTURES fix half disposition — the
      `cefi_consolidated_native_ao_extract_2026_07_25.md` todo 1 (candidate 11) already rolled up the BITGET-FUTURES
      catalogue entry, so that half is closed via `unified-trading-pm@1ea317100`.
- [x] ✅ [DATA] P1. Add a LIGHTER-ZKSYNC market-index → symbol map so the ~11,283 numeric-stem objects resolve. **CLOSED
      2026-08-06 (na-eligibility-audit)**: done 2026-07-28 per this doc's own Deferred-work table row 6 — the dry-run +
      apply completed via the existing migration script, `already_canonical=12,908, would_rename=0, would_merge=0`.
      Code: `market-tick-data-service@feeb8a6e` (dtype fix in `do_merge()`). Evidence was already recorded in this file
      but never reflected back onto this checkbox.
- [x] ✅ [DATA] P2. Design the COMBO-in-perp-partition move for DERIBIT. **CLOSED 2026-08-04 (na-eligibility-audit)**:
      the design doc `/plans/archive/2026_08/issues/deribit_combo_perpetual_partition_move_2026_07_21.md` (archived
      2026-08-16, all todos done) exists and is described
      as ready — this checkbox's ask was the DESIGN only; the actual partition-move APPLY (15,119 rows) is a separate,
      still-open, operator-gated action tracked by the cross-reference todo further down this file and by table row 7
      below ("DERIBIT combo PARTITION-MOVE — Operator-owned, explicitly out of scope").
- [x] ✅ [DATA] P2. Register PACIFICA-SOLANA (265) in the fail-hard quarantine set. **CLOSED 2026-08-09
      (stale-check-cefi, staleness re-audit)**: DONE since `unified-api-contracts@989e9d16` (2026-07-21) — same commit
      the SHIPPED-THIS-SESSION section a few lines above already documents ("quarantine model:
      `is_quarantined_instrument_id` + `ResolutionEvidence` + registry (seeded with only PACIFICA-SOLANA)").
      Live-verified today: `unified_api_contracts/canonical/quarantine.py`'s `QUARANTINE_REGISTRY` carries exactly one
      entry, `"PACIFICA-SOLANA"` (`venue="PACIFICA-SOLANA"`, `instrument_stem="*"`, reason cites "265 objects,
      permanently honest-raw"), matching this todo's ask verbatim. Five prior na-eligibility-audit passes (2026-07-30
      through 2026-08-07) left this open/"could not confirm" despite the registration already existing in the same file
      this doc's own text points to (`unified-api-contracts/unified_api_contracts/canonical/quarantine.py`) — a
      grep-then-read gap, not new work.

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

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - todos are FENCED to other owners
  (live rename fleet / DeFi removal-probe agent), the DERIBIT combo partition-MOVE needs explicit operator sign-off, and
  the doc records an explicit operator STOP.
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, stale items — doc stays NA (live,
  connectivity-sensitive, multi-repo GCS migration execution work with explicit dated operator gating, not
  worker-determinable bounded audit work), but re-checked the 6 handoff checkboxes above against the final "Deferred
  work after 2026-07-24 ~13:35Z" table per this doc's own 2026-07-24 invitation to do so: closed 3 (KRAKEN-SPOT
  `_PATH_RE`, the 658-key dedup, the DERIBIT combo design) as DONE, left the enumeration-vs-fix item open with a
  clarifying note (measurement done, fix not), and left 2 (LIGHTER-ZKSYNC symbol map, PACIFICA-SOLANA quarantine
  registration) open — could not confirm either resolved.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — sole open item carries a redirect
  banner to a sibling doc's own live todo (citation verified). Caught a real checkbox-vs-prose trap: this doc's top
  checklist reads 0-open (already flagged as a false archive-candidate 2026-08-09), but its own 'Deferred work' table
  further down still carries this genuine open item.
- **na-eligibility-audit 2026-08-16** [body-hash:f8c0a8a44b52b236]: KEEP-NA, valid — Read the full 950-line doc end-to-end (two Read calls, lines 1-499 and 500-950 — no gaps).

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
- `unified-trading-pm/plans/archive/2026_08/issues/deribit_combo_perpetual_partition_move_2026_07_21.md` (archived
  2026-08-16, all todos done) — new design doc:
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

- [x] ✅ [DATA] P1. DERIBIT combo mispartition — read the design doc
      `plans/archive/2026_08/issues/deribit_combo_perpetual_partition_move_2026_07_21.md` in full before touching this. Two
      DISTINCT actions: (a) **[WRITER] fix the still-open write-path leak** (widen the combo-shape guard in
      `tardis_cefi_shards.py` so new captures stop landing mispartitioned — safe to ship alone, no data motion) — **PART
      (a) DONE (re-verified 2026-08-05, slot-15)**: `mtds@2ddc6d4a` confirmed ancestor of `origin/live-defi-rollout`;
      the writer-side guard-widen already shipped per Deferred-work table row 7 below; (b) **[DATA] the partition-MOVE
      for the existing 15,119 mispartitioned rows** — **STILL OPEN, operator-owned**: needs **explicit operator sign-off
      on the specific plan** (operator has seen the finding in chat and acknowledged it, but has NOT yet signed off on
      the actual `--apply` — do not execute (b) without a fresh, explicit go-ahead on the doc's §7 plan).

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
`plans/archive/issues/cefi_okx_margin_type_wire_key_ambiguity_reclassification_2026_07_22.md` — **operator sign-off
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

| #   | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Kind                                                     | Blocked-on                                                                                                                                                                                                  |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | ~~KRAKEN-SPOT `--apply`~~ — **DONE 2026-07-23 ~15:40Z**. Attempt 3 (with the retry-hardened fix) completed `PYTHON_EXIT=0`: 155,872 auto-renamed + 1,157 stale duplicates deleted; 6 renames hit a transient GCS 503 mid-`copyTo` (never touched by `run_gcs_rename`'s no-retry single attempt) — verified via direct `gsutil stat` that source-untouched/target-absent for all 6, then retried with a tiny script reusing `do_rename()` verbatim; all 6 now confirmed canonical via GCS spot-check. The manifest phase's `honest_unresolved_rows: 3598` figure was investigated and is a NON-ISSUE: confirmed exactly 1 manifest row per (venue, day, instrument_type, data_type) shard atom with `instrument_id=None` — a shard-level completeness marker, not a per-instrument record (per-instrument data lives in the actual GCS files, independently confirmed present + canonical for the sampled shard). **KRAKEN-SPOT Surface A is genuinely, fully clean.** | **DONE**                                                 | Nothing outstanding on KRAKEN-SPOT itself — proceed to item 2                                                                                                                                               |
| 2   | Fleet agent (`ae18c5ef1b16bc8e8`) continue its self-drive chain: error-recon (348 would_patch errors) → re-run `verify_cefi_canonical_4surface_2026_07_20.py` → LATE colliding-venue renames (serialized) → MID window → colon_wire (1,697) → loop-until-dry (2 clean passes)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Not done                                                 | **UNBLOCKED** — item 1 (KRAKEN-SPOT) is now done; check whether agent `ae18c5ef1b16bc8e8` is still alive (SendMessage to resume) before re-dispatching this chain fresh                                     |
| 3   | Surface C: land the v2 manifest dedup apply — **fresh dry-run 2026-07-24 confirmed clean** (all "MUST be 0" safety invariants pass: 0 captured rows dropped, 0 captured rows left marker-less, 0 lossy chain-merges; DERIBIT-COMBO purge 196/196 matches the operator ruling). Drained the consolidator (`gcloud scheduler jobs pause ...`), but 3 consecutive `--apply` attempts all failed on a genuine, ongoing GCS connectivity degradation (mid-download `ConnectionResetError`/`ChunkedEncodingError`/read-timeout — same pattern independently hit the fleet-reverify and LIGHTER-backfill workflows around the same time, so this is an environment-wide blip, not a script bug). **Zero mutation occurred any attempt** (confirmed: crash is always at the initial catalogue read, before any write path executes) — consolidator RESUMED to a safe state rather than left paused through an uncertain-duration outage                                       | Dry-run: DONE / Apply: blocked on transient connectivity | Retry the drain+apply sequence once GCS connectivity stabilizes — the dry-run itself does not need to be re-run, it's still valid; just re-pause the consolidator and retry `--apply`                       |
| 4   | ~~Residual ~216 ambiguous CeFi wire-keys~~ — **213/216 SHIPPED, DONE**: `instruments-service@bf5322bb9` (BINANCE-DELIVERY 4/4, BINANCE-FUTURES 2/2, KRAKEN-FUTURES 2/2, OKX-FUTURES sub-pattern-A 76/146) + `instruments-service@39e26bfe` (BYBIT FUTURE base-asset-parsing 36/36) + `instruments-service@1c920fab` (OKX-FUTURES sub-pattern-B 70/70 + OKX-SWAP 5/5 + BITGET-FUTURES 18/18 margin_type mislabel, operator-ruled). **3 remain, forever**: BYBIT's 3 PERPETUAL keys — confirmed two genuinely distinct real products (closed 2019-2020 linear + still-active inverse), correctly excluded, not a bug, will never be "fixed"                                                                                                                                                                                                                                                                                                                             | **DONE**                                                 | Nothing outstanding — 216→3, and the 3 are a correct terminal state, not a gap                                                                                                                              |
| 4b  | ~~OKX-FUTURES (70) + OKX-SWAP (5) + BITGET-FUTURES (18) margin_type wire-key collision reclassification~~ — **SHIPPED 2026-07-23** (`instruments-service@1c920fab`): new `_dedup_cefi_margin_type_mislabel()` reuses the live Tardis adapter's own classifier to keep the correct row, drop the stale pre-fix duplicate. Independently re-verified against a fresh prod snapshot (93→0), BYBIT's 3 PERPETUAL confirmed byte-identical untouched                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **DONE**                                                 | Folded into item 4 above, no longer a separate open item                                                                                                                                                    |
| 5   | ~~Build the missing catalogue-enumeration-gap measurement script~~ — **SHIPPED** (`instruments-service@f6f16785`): re-runnable, bounded-read script generalized to 2 case classes (spot-quote-gap, cme-letter-month-gap). Live-measured 211 gap rows today (OKX-SPOT 174, BITGET-FUTURES 33, COINBASE-SPOT 4) — the stale ~422 figure is retired in favor of this number, independently re-verified with real GCS spot-checks. ✅ **DONE 2026-08-04 (BITGET-FUTURES fix, candidate 11 of `cefi_consolidated_native_ao_extract_2026_07_25.md`)** — fresh gap-measurement run (`instruments-service@9167e5d7`): BITGET-FUTURES=0 (before: 33, after: 0). Catalogue already rebuilt 2026-08-04T01:02Z; gap closed by prior rollup. No code change needed — read-only verification. OKX-SPOT/COINBASE-SPOT residual (170+1) still needs operator decision on UAC `_CEFI_VENUE_QUOTE_EXTENSIONS`.                                                                          | **DONE**                                                 | BITGET-FUTURES resolved — nothing outstanding. OKX-SPOT/COINBASE-SPOT stay open per operator-decision gating.                                                                                               |
| 6   | ~~LIGHTER-ZKSYNC market-index → symbol map (~11,283 objects, 93.5% bare numeric stems)~~ ✅ **DONE 2026-07-28 (candidate 10 of `cefi_consolidated_native_ao_extract_2026_07_25.md`)** — reused existing migration script, dry-run: `already_canonical=12,908, would_rename=0, would_merge=0`. Code: `market-tick-data-service@feeb8a6e` (dtype fix in `do_merge()`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | **DONE**                                                 | Nothing outstanding on LIGHTER-ZKSYNC stems; live capture remains BLOCKED-CREDENTIALS (separate).                                                                                                           |
| 7   | ~~DERIBIT combo PARTITION-MOVE P1 prep~~ — **INVESTIGATED, NO CODE NEEDED**: the guard-widen already shipped this session (`mtds@2ddc6d4a`, landed the day after UAC's DERIBIT-COMBO deregistration `uac@11adf279` — synergistic, not conflicting) and `tardis_cefi_shards.py` already shares the fixed classifier (no duplicate code path to port into). The actual 15,119-row `--apply` data MOVE remains fully unstarted and Operator-owned per §7 — this ruling never covered it                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Prep: DONE (no-op) / Move: still operator-owned          | The `--apply` partition-move still needs explicit operator sign-off per `deribit_combo_perpetual_partition_move_2026_07_21.md` §7 — do not start that without a SEPARATE future review                      |
| 7c  | `[INFRA] P2.` **NEW finding, 2026-07-23**: MTDS's own orchestrator (`engine/orchestrator/__init__.py::get_venues_for_asset_groups`, `adapters/umi_tick_provider.py`) still hard-codes `DERIBIT-COMBO` as an active fetchable cefi venue and describes it in comments as "a real UAC-declared cefi venue" — factually stale since UAC deregistered it 2026-07-21 (`uac@11adf279`). Live cross-repo inconsistency, not yet causing known harm but should be corrected so MTDS doesn't attempt to fetch a venue UAC no longer declares                                                                                                                                                                                                                                                                                                                                                                                                                                   | Not done                                                 | Found by the DERIBIT-combo P1 prep investigation (this session); needs its own small fix — update MTDS's venue enumeration to match UAC's registry, verify no live fetch path still targets `DERIBIT-COMBO` |
| 8   | `[INFRA] P1.` Audit `slot-cron-ff-pull.sh` (and any other cron touching shared slot checkouts) for a hard-reset fallback path that silently discards locally-committed-unpushed work — make it fail loud instead                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Operator-owned                                           | This session's hard-reset near-miss (documented above) is evidence, not a fix; needs an operator/infra owner to investigate the actual cron script                                                          |
| 9   | Final 4-surface done-state re-proof (all of A/B/C/D = PASS on both probe instruments) + plan archival                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Cannot be done yet                                       | Gated on items 1-3 landing — do NOT assume ALL_DONE without re-measuring; the 44.65%→FAIL baseline was a real corpus-wide measurement                                                                       |

**Recommended next**: keep watching item 1 (KRAKEN-SPOT v4) — everything else in the CeFi filename-migration critical
path (items 1-3, 9) chains directly off it. Items 4-6 (catalogue gaps) and 7-8 (operator-owned) are independent
side-tracks that can run in parallel whenever picked up, but are not blocking the critical path.

### DELTA — 2026-07-24 ~01:30Z (`/autonomous` invoked, operator away 6h — driving to completion, no further check-ins)

**Operator invoked `/autonomous` explicitly**, stating they are away for 6 hours and to "complete everything." Per
`cursor-configs/AUTONOMOUS_AGENT_RULES.md` (read in full this tick), decisions the operator could make are now mine to
make using the documented record of intent — logging the one scope decision made under that authority:

**DERIBIT combo partition-move `--apply` (item 7, the actual 15,119-row data MOVE) remains OUT OF SCOPE for this
autonomous drive, NOT reinterpreted as newly-authorized.** Reasoning: earlier THIS SAME session, the operator gave an
explicit, specific ruling on this exact item — "Proceed with P1 prep now" — deliberately answering a question that
distinguished the P1 prep work (approved) from the actual `--apply` data move (explicitly NOT covered, "a SEPARATE
future review required"). That is a recent, specific, documented decision from this operator about this exact action,
not a vague old plan note — the autonomous rules direct using "the documented record of intent" to decide, and the most
faithful reading of that record is that this carve-out stands: "complete everything" naturally refers to the currently
in-flight work threads (Surface C, fleet chain, LIGHTER backfill, MTDS fix, final re-proof, archival), not a dormant,
explicitly-deferred, hard-to-reverse production data migration on live-served financial data that wasn't even part of
the in-flight list reported to the operator. If this reasoning is wrong, it is the conservative direction to be wrong in
(leaving a real migration deferred, not launching an under-scrutinized one while unsupervised).

Also leaving item 8 (`slot-cron-ff-pull.sh` hard-reset audit) untouched — it is shared cross-slot infra affecting OTHER
concurrent agents' sessions, outside this plan's actual scope (flagged Operator-owned for a different reason: needs an
infra owner, not a data-migration sign-off) — modifying it unsupervised carries real risk of breaking sibling sessions
mid-task with no one able to notice quickly.

**Everything else in this plan**: driving to actual completion per rule 1 (no `DEFERRED`/`BLOCKED-OPERATOR` end states),
looping per rule 12 (self-paced `ScheduleWakeup`, journaling every tick to this Progress Log, terminating when items
2/3/9 all reach DONE).

### DELTA — 2026-07-24 ~01:20Z (item 7c SHIPPED; fresh 4-surface re-measure is REAL and FAIL as expected; Surface C hit a genuine data-safety gate)

**Item 7c DONE**: `market-tick-data-service@5334bff6` removes `DERIBIT-COMBO` from both active-venue-enumeration
call-sites (`engine/orchestrator/__init__.py::get_venues_for_asset_groups`, `adapters/umi_tick_provider.py`'s
`_TARDIS_CEFI_VENUES`), adds a live-UAC-registry-backed regression test (imports the real
`unified_api_contracts.registry.market_data_categories.VENUES_BY_ASSET_GROUP` and asserts non-membership, so it stays in
sync automatically rather than hardcoding an assumption), confirmed shipped
(`git rev-list --count origin/live-defi-rollout..HEAD` = 0).

**Fresh `verify_cefi_canonical_4surface_2026_07_20.py` re-measure — a REAL, complete run** (prior 2 attempts crashed on
GCS connectivity before reaching any surface; this one got all the way through): **OVERALL: FAIL [A=FAIL B=FAIL C=FAIL
D=PASS]**. Corpus-level fractions: **A (filename) 48.04%** — but this hides a sharp day-by-day gradient: 94-95%
canonical on 2025-06/08/10/11-12, then 67.04% (2025-12-15), 33.02% (2026-02-01), 23.99% (2026-05-01) — the "LATE window"
the plan already flagged (23-28%), now re-confirmed fresh and post-KRAKEN-SPOT. **B (column) 95.00%** (38/40 sampled
objects). **C (manifest) 98.22%** (excl. chain bundles) — 2 concrete FAIL examples shown (BITFINEX- FUTURES ADA: 7
duplicate wire-form manifest rows alongside 4628 canonical; DERIBIT AVAX-USDC: 2 duplicates alongside 814 canonical) —
exactly the shape the Surface C v2 apply is designed to collapse. **D (reader) PASS** — resolver correctly handles both
wire and canonical forms either way. This is genuinely useful, not just a re-confirmation: it pinpoints the LATE-renames
scope precisely (the 3 low-fraction dates/pattern) rather than relying on a stale 2026-07-20 histogram.

**Surface C v2 manifest apply — 4th attempt got PAST the earlier connectivity failures, hit a REAL data-safety gate
instead**:
`STOP (DATA LOSS): dropping 'chain' would merge 3304 PIN_ATOM group(s) holding >1 CAPTURED row with DIFFERING non-zero row_count`.
Critically, **the dry-run run a few hours earlier (2026-07-23 ~18:58Z) measured this EXACT invariant at 0/0**
("`[v2 CHAIN-DROP=True] rows merging on chain-differing PIN_ATOM groups=0 LOSSY (captured w/ differing count)=0 [MUST be 0]`")
— the underlying manifest data genuinely changed in the few hours between the dry-run and this apply attempt (very
plausibly ongoing live capture continuing to write new cefi rows in that window — the whole corpus grew by other,
unrelated measurements around the same time). Zero mutation occurred (the script's own validation stage refused before
any write — confirmed no "Backed up original index"/"Wrote canonicalised index" log lines appear). Consolidator cron
RESUMED again to a safe state. **Next: investigate the 3304 lossy groups before deciding whether to re-run the dry-run
fresh (the corpus has moved since 18:58Z) + apply, or use the script's own offered `--keep-chain` escape hatch** — the
script's error message explicitly names `--keep-chain` as the safe alternative to a forced collapse, which is a stronger
safety property than the "operator directive 2026-07-20: derive chain from UAC on demand" preference for cleanup; do NOT
force past this check without understanding it first.

### DELTA — 2026-07-24 ~05:55Z (`/pre-compact` mid-autonomous-loop; genuine connectivity degradation confirmed, 3 workflows lost to it, 1 real commit recovered before it could be lost)

**Item 7c's LIGHTER-ZKSYNC follow-up SHIPPED**: `market-tick-data-service@8835b899` ("fix(cefi): LIGHTER-ZKSYNC numeric
market_id stem resolution for Script 2") — threads the shipped `resolve_market_index()` resolver through Script 2's
shared `_cefi_canonical_resolver_migration_2026_07_18.py` as an optional, default-empty
`ResolverMaps.lighter_market_index` field; substitutes a bare-numeric LIGHTER-ZKSYNC stem for its resolved symbol before
the ordinary catalogue lookup. This commit existed locally (made by the LIGHTER-backfill workflow before it stalled) but
was NEVER PUSHED — found by this exact pre-compact audit's Step 1 git-status check, independently re-verified green
(`quality-gates.sh --no-fix` exit 0, fresh re-run, not trusting the stalled workflow's own claim) before pushing. **This
is exactly the kind of loss this ritual exists to catch — a real, valuable, QG-green commit that would have been
invisible to any future session had it stayed local.**

**All 3 dispatched workflows this tick failed identically**: `LATE colliding-venue renames` (Measure phase),
`LIGHTER- ZKSYNC backfill` (DryRun phase, already had the above commit banked from an earlier resumed attempt), and
`Surface C chain-drop investigation` (Investigate phase) — every one "agent stalled on all 6 attempts (no progress for
180000ms each)", burning 208/244/221 minutes respectively before giving up. **Root-caused, not assumed**: directly timed
`gsutil stat` against the same object checked earlier tonight — took ~19-25s just now vs ~3-7s a few hours ago (same
command, same object, same host). Host load (3.13/2.51/2.29) and free memory are unremarkable; only 1 heavy process was
running at measurement time — this is NOT local resource contention, it is a genuine, currently-ongoing GCS connectivity
degradation, most likely the same condition that caused 3 separate transient failures on the Surface C apply earlier
tonight. **The LATE-renames/LIGHTER-backfill/Surface-C-investigation items are reclassified from "in progress" to
"cannot be done yet — blocked on connectivity, not on any decision or code issue.**

**LESSON (new, real cost tonight)**: when GCS connectivity is degraded, a Workflow-dispatched sub-agent running a long
GCS-heavy script can silently stall for 180s x 6 retries (~200+ minutes wall-clock, real token spend) before the harness
gives up and reports failure — a MUCH more expensive failure mode than a direct `Bash run_in_background` command hitting
a clean, fast exception (the same connectivity issue crashed the direct Surface C `--apply` attempts in under a minute
each, with a clear traceback, captured cheaply). **Going forward: during any SUSPECTED connectivity degradation, prefer
direct `Bash run_in_background` execution over Workflow-dispatched agents for long-running, GCS-heavy scripts** — it
fails fast and cheaply instead of stalling expensively. Confirm suspected degradation with a cheap, timed `gsutil stat`
check before deciding which path to use.

**Cross-check consolidator cron state (safety-critical, mid-audit)**: confirmed `PAUSED` at this exact moment — the
failed `Surface C chain-drop investigation` workflow's `Investigate` phase never reached the point of pausing it
(read-only phase, per its own design), so this PAUSED state must be a leftover from the last DIRECT apply attempt this
session (~01:14Z) that I resumed after — re-verified and RESUMED again now, confirmed ENABLED, so it is not left paused
through this connectivity-degraded window.

**`/autonomous` loop continues** — per rule 12(e) (stall-safety: a flat progress metric = STOP and diagnose, never burn
ticks blindly repeating a failing action), NOT re-dispatching another heavy workflow into the same degraded connectivity
immediately. Backing off for a longer interval, will re-check connectivity health (cheap `gsutil stat` timing) before
resuming LATE renames / LIGHTER backfill / Surface C investigation.

### DELTA — 2026-07-24 ~13:35Z (connectivity recovered, resumed briefly, operator returned and called a stop — `/pre-compact` run interactively, nothing local to quickmerge)

**Connectivity re-check**: `time gsutil stat` on the small (9MB) catalog object came back ~3.0s — matches the healthy
baseline, not the ~19-25s degraded reading from the prior tick. Pulled in 17 commits (`unified-trading-pm`) + 5 commits
(`market-tick-data-service`, across 2 pulls) that landed from other concurrent sessions while this loop was backed off;
`instruments-service` was already current. All 3 repos fast-forwarded cleanly, no conflicts.

**Surface C chain-drop investigation — STARTED, INTERRUPTED before conclusion, but already overturns the ~01:20Z DELTA's
working hypothesis.** Read `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py` + its imported v1 module directly
(not via Workflow, per the standing lesson). Found, by reading the code rather than assuming: `_chain_merge_safety()`
early-returns `(0, 0)` whenever `"chain" not in df.columns`; `main()`'s dry-run path calls
`v1._load(..., columns=v1._DRYRUN_COLS)`, and confirmed directly (`'chain' in v1._DRYRUN_COLS` → `False`) that
`_DRYRUN_COLS` does **not** include `"chain"`; `_ensure_cols` only re-materialises `pipeline_mode`/`row_count`, never
`chain`. **This means every dry-run reports the chain-drop invariant as 0/0 UNCONDITIONALLY, regardless of the real
data** — `--apply` is the ONLY code path that loads the full schema (`columns=None`) and therefore the only path that
can ever see a nonzero `chain_lossy`. **This is a plausible alternate/additional root cause to the ~01:20Z DELTA's
"corpus moved between dry-run and apply" hypothesis — quite possibly the ENTIRE explanation, not just a contributing
factor**, since a dry-run showing 0/0 provides zero actual evidence either way; it was never measuring anything. **NOT
YET FULLY CONFIRMED**: a follow-up script (`investigate_chain_lossy_20260724.py`, written to the session scratchpad) was
mid-run — it had proven the `_DRYRUN_COLS` fact above, then hit a transient `ChunkedEncodingError` on the 187MB
full-index download (connectivity had recovered per the cheap `gsutil stat` check on the small object, but a large-blob
download can still hit a one-off reset independent of general degradation), was retried, and was killed mid-flight when
the operator called this stop — so the actual current `chain`-column presence and live lossy-group count in the FULL
schema were never re-measured this tick. **Nothing was mutated**: this was a pure read/diagnostic investigation, zero
`--apply` calls made.

**New tracked todo (do not lose this finding)**:

- [x] ✅ [SCRIPT] P0. Fix (or explicitly justify) `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py`'s dry-run
      chain-drop blind spot: `_DRYRUN_COLS` excludes `"chain"`, so `_chain_merge_safety()` always reports `(0, 0)` in
      dry-run mode regardless of the real data — the STOP-ON-SURPRISE gate for this invariant only ever fires at
      `--apply` time. Either add `"chain"` to `_DRYRUN_COLS` (small perf cost, real safety value: a dry-run would then
      give an honest early warning) or add an explicit log line when the check is structurally skipped, so a clean
      dry-run is never mistaken for a proven-safe one. Re-run `investigate_chain_lossy_20260724.py` (scratchpad, this
      session — promote it to `scripts/` first per the one-off lifecycle rule if it earns its keep) against the FULL
      schema to get the actual current lossy-group count and inspect a sample before deciding `--keep-chain` vs. a
      repair vs. a fixed dry-run + clean `--apply`. **CLOSED 2026-08-09 (stale-check-cefi, staleness re-audit)**:
      direct-code-verified `"chain"` IS present in `instruments-service`'s `_DRYRUN_COLS`
      (`scripts/complete_cefi_manifest_canonical_dedup_2026_07_17.py`), and the v2 script
      (`load_cols = None if args.apply else v1._DRYRUN_COLS`) reuses v1's list via `importlib`, so the fix reaches both
      entry points. The fixing commit (message "include chain in dry-run column projection so chain-drop safety gate
      isn't a no-op") lives on `origin/live-defi-rollout` under current SHA `97801b5d` — the doc's own cited SHAs
      `1284606a`/`654d694f` predate the 2026-08-05 `instruments-service` history rewrite (see the sibling
      `.stale-pre-history-rewrite-*` checkout) and are no longer ancestors under their old hashes, which is why the
      2026-08-07 marker's "sibling audit pass" citation read as unverifiable and was left open — the equivalent-content
      commit genuinely is live.

**Operator returned and said stop** (not the 6-hour window elapsing — an explicit interrupt). Per the autonomous skill's
own instruction ("On operator 'stop': kill the loop/sleeper PID immediately and don't re-arm"), this session is ending
the `/autonomous` loop now. **No `ScheduleWakeup` will be re-armed.**

**Consolidator cron state**: re-verified `ENABLED` (not paused) — the interrupted investigation never reached the pause
step (it's a read-only diagnostic phase by design), and no apply attempt happened this tick, so there was nothing to
resume.

**Nothing local to quickmerge**: `git status --porcelain` + `git diff --stat HEAD` came back empty across all 3 repos
before this doc edit — every change from this entire `/autonomous` window was already committed and pushed (confirmed
`ahead=0` repeatedly, most recently by the ~05:55Z pre-compact tick before this one). This plan-doc edit itself is the
only uncommitted change at stop time, shipped via the standard `docs(plans):` direct-push carve-out.

## Deferred work after 2026-07-24 ~13:35Z (supersedes all earlier Deferred-work sections in this file — items 1/4/4b/5/6/7/7c below are DONE, see DELTAs above)

| #    | Item                                                                                                                                                                                                                                                                                      | Kind                                                          | Blocked-on                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | ~~KRAKEN-SPOT Surface A~~                                                                                                                                                                                                                                                                 | **DONE**                                                      | —                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 2a   | Fleet chain: error-recon + fresh 4-surface reverify                                                                                                                                                                                                                                       | **DONE**                                                      | —                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 2b   | LATE colliding-venue renames (fresh scope measurement, then per-venue dry-run+apply)                                                                                                                                                                                                      | Not done                                                      | Connectivity confirmed healthy now — no longer blocked; operator called a stop before this was started this tick                                                                                                                                                                                                                                                                                                                                            |
| 2c   | MID window (KRAKEN-SPOT `ADA/USD.parquet` spurious hive-segment) + colon_wire (1,697) + loop-until-dry                                                                                                                                                                                    | Not done                                                      | Next link after 2b; not yet started                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 3    | Surface C v2 manifest apply                                                                                                                                                                                                                                                               | Code-level UNBLOCKED (2026-07-24 later tick)                  | `instruments-service@654d694f` folds `underlying`+`chain` into the manifest dedup key — chain-drop invariant now fully understood (0 DERIBIT/ASTER residual; 28 groups BITFINEX-SPOT/BYBIT-SPOT accepted as a small, logged, tracked tolerance). Full detail: `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Finding 5. The apply itself (pause cron → fresh dry-run → `--apply` → verify → resume) has NOT run yet — do that next. |
| 4/4b | ~~Residual ambiguous wire-keys + margin_type mislabel~~                                                                                                                                                                                                                                   | **DONE**                                                      | —                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 5    | ~~Catalogue-enumeration-gap script~~                                                                                                                                                                                                                                                      | **DONE**                                                      | —                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 6    | ~~LIGHTER-ZKSYNC numeric-stem GCS rename backfill (~11,283 objects)~~ ✅ **DONE 2026-07-28** — dry-run + apply completed via existing migration script, `already_canonical=12,908, would_rename=0, would_merge=0`. Code: `market-tick-data-service@feeb8a6e` (dtype fix in `do_merge()`). |
| 7    | DERIBIT combo PARTITION-MOVE (15,119 rows, actual data move)                                                                                                                                                                                                                              | **Operator-owned, explicitly out of scope for `/autonomous`** | Per the `/autonomous` DELTA above — a specific, recent operator ruling this session already deferred this, not reinterpreted as newly authorized                                                                                                                                                                                                                                                                                                            |
| 7c   | ~~MTDS DERIBIT-COMBO venue staleness~~                                                                                                                                                                                                                                                    | **DONE**                                                      | —                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 8    | `slot-cron-ff-pull.sh` hard-reset audit                                                                                                                                                                                                                                                   | **Operator-owned, explicitly out of scope for `/autonomous`** | Shared cross-slot infra affecting other concurrent sessions — per the `/autonomous` DELTA above                                                                                                                                                                                                                                                                                                                                                             |
| 9    | Final 4-surface done-state re-proof + plan archival                                                                                                                                                                                                                                       | Cannot be done yet                                            | Gated on 2b/2c/3/6 all landing — do not assume done without re-measuring                                                                                                                                                                                                                                                                                                                                                                                    |

✅ **DONE 2026-08-04 — dry-run chain-drop blind spot (candidate 12 of
`cefi_consolidated_native_ao_extract_2026_07_25.md`):** `"chain"` already in `_DRYRUN_COLS` at
`instruments-service@1284606a` (2026-07-24, "include chain in dry-run column projection so chain-drop safety gate isn't
a no-op"). Fix predates even the triage plan's creation — no code change needed. The v2 script reuses v1's
`_DRYRUN_COLS` via `importlib`, so the fix reaches both paths. Confirmed: `'chain' in v1._DRYRUN_COLS → True`.

**Recommended next (on resume)**: with the dry-run chain-drop blind spot now closed, re-run the chain-drop investigation
against the full schema for real numbers, decide `--keep-chain` vs. repair vs. clean apply, then proceed to 2b (LATE
renames) via direct Bash, then 2c, then 9.

**cicd escalation agt-558c62 2026-08-09**: this doc's own checkbox-tracked "Deferred / handoff" list above (all `[x]`)
was 0-open-todos-flagged by `check_archive_candidates.sh`'s ratchet as an archive candidate, but the "Deferred work
after 2026-07-24 ~13:35Z" table two sections up its own row 9 ("Final 4-surface done-state re-proof + plan archival")
still reads "Cannot be done yet" — a genuine checkbox-vs-prose gap, not a stale table. Live-verified this is not
duplicate/orphaned tracking: `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` already carries the
LIVE open todo for exactly this remaining work
(`- [ ] [DATA] P2. Once the 2 blockers above resolve ..., re-run verify_cefi_canonical_4surface_2026_07_20.py for a clean PASS, then archive this doc + parent`).
Adding an explicit todo here too so this doc's own checkbox state stops falsely reading as fully closed — archiving THIS
doc (25+ corpus referrers, several near/at the 1000L line-cap, real risk of the exact broken-link/line-cap deadlock
documented in `issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md`) is out of scope for a
one-shot CI-gate fix and belongs to whichever session closes out the sibling doc's own open todo above.

- [ ] [DATA] P2. Final 4-surface done-state re-proof (Surface A/B/C/D all PASS on both probe instruments) + this doc's
      own archival, once `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`'s open todo lands
      (KRAKEN-SPOT LATE renames [2b] → MID window + colon_wire loop-until-dry [2c] → Surface-C v2 manifest apply [3] →
      re-proof [9]). Tracked live on that sibling doc — do not duplicate-drive from here, just gate this doc's own
      archival on it per that doc's own stated plan ("re-run verify_cefi_canonical_4surface_2026_07_20.py for a clean
      PASS, then archive this doc + parent").

## Step 8 verdict (`/pre-compact` run interactively — operator present, called the stop; this closes out the `/autonomous` window)

**Safe to compact/stop: YES.** All 3 repos (`unified-trading-pm`, `market-tick-data-service`, `instruments-service`)
confirmed clean (`git status --porcelain` empty) and `ahead=0` against `origin/live-defi-rollout` immediately before
this doc edit; this edit itself is the only pending change, about to be pushed via the `docs(plans):` direct-push
carve-out. **Nothing to quickmerge**: no code changes were made this tick (pure investigation/reading), so there is no
`--files`-scoped quickmerge to run — the operator's "quickmerging everything local" instruction found nothing local.
**What was at risk and is now saved**: the chain-drop dry-run blind-spot finding — a genuine, non-obvious discovery that
would otherwise have lived only in this turn's transcript — is now a tracked P0 todo, not a chat-only fact. **What was
killed, not lost**: two background diagnostic Python processes (`investigate_chain_lossy_20260724.py` attempts) — both
pure read-only GCS downloads, zero mutation, safe to kill; the script itself remains in the session scratchpad for the
next session to resume from rather than rewrite. **Where to resume**: read this DELTA + the new P0 todo, promote/re-run
`investigate_chain_lossy_20260724.py` against the full schema first, then continue down the Deferred-work table above.
The `/autonomous` loop is now OFF — resuming requires a fresh explicit invocation.

> **2026-07-25 note (added when the parent's Progress Log section was trimmed during the 4-child split — see
> `cefi_consolidated_closeout_2026_07_18.md`'s Reconciliation/source docs list)**: the two "post-split DELTA updates"
> the parent used to retain locally (the ~01:30Z/~01:20Z/~05:55Z/~13:35Z DELTAs above, the Deferred-work table, and the
> Step 8 verdict) are now appended here, verbatim, completing the migration this file's own header always intended
> ("moved verbatim, nothing summarized or dropped" — see the top-of-file note). The parent no longer duplicates any of
> this — read here for the full narrative.

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — trimmed 7→6, dropped the operator-owned
  deribit_combo_perpetual_partition_move issue + the cross-cutting codex doc (superseded here by the CeFi-specific
  blueprint), added the verify_cefi_canonical_4surface_2026_07_20.py source path (the migration's central verification
  tool, cited throughout).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, stale items — flipped 1 of 3 open checkboxes
  to `[x]` this run: the LIGHTER-ZKSYNC market-index map (done 2026-07-28 per `market-tick-data-service@feeb8a6e`,
  evidence already recorded later in this doc's own Deferred-work table but never reflected back onto the checkbox).
  Independently re-verified the chain-drop dry-run blind-spot item is only PARTIALLY done — the `_DRYRUN_COLS` sub-fix
  is confirmed (`instruments-service@1284606a`) but this doc's own "Recommended next" text still calls for re-running
  the investigation and deciding a remediation approach, so that checkbox stays open (correcting a first read that would
  have over-closed it). Doc stays NA overall — PACIFICA-SOLANA quarantine registration and the doc's live
  migration-execution character (operator sign-off gates, an SSOT contradiction referred to the operator) remain genuine
  judgment work.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — swapped out the superseded `history_part2` (07-21
  PRE-COMPACT checkpoint, explicitly superseded by this file's own later "REVISED REMAINING QUEUE"/final deferred-work
  table) for `unified-api-contracts/unified_api_contracts/canonical/quarantine.py` — the actual source module
  (`is_quarantined_instrument_id`/`ResolutionEvidence` registry) behind the sole remaining open todo (PACIFICA-SOLANA
  quarantine registration).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 2 open items confirmed directly (PACIFICA-SOLANA quarantine
  registration, genuine work; the `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py` dry-run chain-drop
  blind-spot fix, genuine work). Note: a same-run sibling audit pass reported this doc's dry-run chain-drop item as
  already resolved (citing instruments-service@1284606a/@654d694f + Surface C v2 apply GATE GREEN) — that evidence does
  not match this specific `_DRYRUN_COLS` script item on direct read, so left open rather than closed on an unverified
  citation; worth a follow-up re-check.
- **stale-check-cefi 2026-08-09** (staleness re-check on already-KEEP-NA-marked docs, operator-requested): both items
  the 2026-08-07 pass left open were in fact already done and never flipped. (1) PACIFICA-SOLANA quarantine registration
  — done since `unified-api-contracts@989e9d16` (2026-07-21), same commit this doc's own "SHIPPED THIS SESSION" section
  already cites; live-verified `QUARANTINE_REGISTRY` in
  `unified-api-contracts/unified_api_contracts/canonical/quarantine.py` today. (2) the `_DRYRUN_COLS` chain-drop
  blind-spot fix — the 2026-08-07 pass's instinct that the cited SHAs didn't check out was right (they don't, as old
  hashes), but the underlying finding was wrong: `instruments-service` underwent a full history rewrite on 2026-08-05
  (see the sibling `.stale-pre-history-rewrite-*` checkouts), which changed every pre-08-05 commit's SHA while
  preserving content — the SAME fix exists today under a new hash (`97801b5d`, confirmed `git merge-base --is-ancestor`
  of `origin/live-defi-rollout`), and direct code read confirms `"chain"` is in `_DRYRUN_COLS`. Both checkboxes flipped
  above with evidence. Doc stays `assigned_vm: NA` overall — no other open items existed in this doc at this pass.
- **context-scout 2026-08-15**: refreshed context_scope (6 entries) — swapped `unified-api-contracts/.../quarantine.py`
  (its PACIFICA-SOLANA todo landed 2026-08-09, no longer this doc's live blocker) for
  `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`, which this doc's own sole remaining open todo
  (the cicd-escalation-added Final 4-surface re-proof + archival gate) explicitly names as the doc to read instead of
  duplicate-driving from here.
- **na-eligibility-audit 2026-08-17** [body-hash:19cf1ba844e6cee9]: KEEP-NA, valid — Reaffirmed. Sole open item (line 881, final 4-surface re-proof + this doc's own archival) is citation-hold class (a): redirects to `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` as the doc carrying the live work. Doc stays assigned_vm: NA.
- **na-eligibility-audit 2026-08-19** [body-hash:e93a608b86e0446d]: KEEP-NA, valid — Reaffirmed. Fresh full re-read (2 Read calls, offset-continued, 953 lines) confirms exactly 1 open item unchanged (line 881, final 4-surface re-proof + this doc's own archival), same citation-hold redirect to `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`. Doc stays assigned_vm: NA.
- **context-scout 2026-08-19**: re-verified context_scope, no change needed (6 entries) — sole open item unchanged since 2026-08-17; existing set (closeout parent, canonical blueprint, residual-followups issue, history_part1 child, verify_cefi_canonical_4surface script, chain-drop root-cause issue) remains accurate.
