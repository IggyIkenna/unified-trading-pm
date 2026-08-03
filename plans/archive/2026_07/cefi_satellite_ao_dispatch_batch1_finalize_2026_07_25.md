---
doc_type: plan
title: CeFi satellite AO batch 1 — finalize (reconcile source docs + resolve excluded items + archive)
summary: >-
  Gated closeout for cefi_satellite_ao_dispatch_batch1_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 33 of that plan's todos are done. Mirrors the tradfi batch1_finalize / prediction batch1_finalize
  pattern (reconcile each of the 21 distinct source docs' checkboxes independently), plus 2 batch1-specific additions:
  re-check the 3 too-large-doc exclusions for whether they are now scoped enough for a batch2 pass, and re-verify the 1
  cross-doc live-conflict exclusion (LATE colliding-venue renames) has actually landed via its own live session before
  spinning it into a fresh todo.
status: complete
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-1, satellite-docs, archival]
related:
  [
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-30"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_satellite_ao_dispatch_batch1_2026_07_25]
gate_on_depends: true
source: >-
  /autonomous session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs
  a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
---

# CeFi satellite AO batch 1 — finalize

> **🟢 ARCHIVED 2026-07-30.** All 4 todos done: source-doc reconciliation (todo 1), the too-large-doc batch2 re-check
> (todo 2), the LATE-renames re-verify (todo 3), and this archival (todo 4). Todo 1 flagged a gate-vs-reality mismatch —
> parent's line 355 (BYBIT futures_chain extended duplicate-verification) was still genuinely open, the ONLY one of the
> parent's 33 todos not done. Resolved by migrating it to its own named Source doc
> (`issues/bybit_futures_chain_write_shape_2026_07_13.md`) as a fresh open todo (never marked done) per the
> near-complete-plan "fold the remnant" guidance — see the parent's own Progress Log for the full rationale. Parent
> moved to `/plans/archive/2026_07/cefi_satellite_ao_dispatch_batch1_2026_07_25.md`, corpus referrers updated (17 files
> with a literal `plans/active/...` path to the parent + referrers to this finalize doc's own path). No new durable
> contract from this batch — codex-alignment check: nothing to update (every todo executed an already-decided spec, per
> the parent's own banner).
>
> **Machine-gated on `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 33 tasks in that plan are `done`. `sequential: true` because todo 2
> needs todo 1's reconciliation done first, and todo 4 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot-9, `review`).** Reconciled all 21 distinct source docs' checkboxes. See
      this plan's Progress Log below for the per-doc breakdown, the 2 real discrepancies found (one batch1 todo that was
      never actually done, one batch1 checkbox flipped prematurely), and the 4 edits made. **Reconcile all 21 distinct
      source docs' checkboxes.** For each of `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`'s 33 now-done todos: flip
      the corresponding checkbox/section in its named source doc (each todo's text ends with "Source: `<doc>.md`"),
      citing the batch-1 commit(s) that shipped it — verify the actual shipped commit exists before citing it. The 21
      source docs: `aster_and_cefi_rolling_adv_feature_2026_07_21.md`, `data_completion_cefi_2026_07_15.md` (5 todos),
      `issues/aster_mtds_failure_count_regression_2026_07_07.md`,
      `issues/bug_c_normalize_id_collision_options_futures_2026_07_22.md`,
      `instruments_cefi_g1_g5_gate_execution_2026_07_24.md`,
      `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md` (2 todos),
      `issues/bybit_futures_chain_write_shape_2026_07_13.md`,
      `issues/cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md`,
      `issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md` (2 todos),
      `issues/cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md`,
      `issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md`,
      `issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md` (3 todos),
      `issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md`,
      `issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (2 todos),
      `issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md` (3 todos),
      `issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md`,
      `issues/deribit_live_options_chain_path_noncanonical_2026_07_21.md` (2 todos),
      `issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`,
      `/plans/archive/issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md` (already resolved + archived
      2026-07-27 — no checkbox left to flip),
      `/plans/archive/issues/rotate_exchange_keys_stale_venue_registry_2026_07_23.md`,
      `issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`. For each: after flipping,
      re-check whether it now has 0 open todos remaining. Only flip a doc's `status` to `resolved` if it genuinely
      reaches 0 open todos (checkbox AND prose-form). **Done when**: all 21 source docs' corresponding
      checkboxes/sections are flipped with verified evidence, and any doc that genuinely reaches 0 open todos is flipped
      to `status: resolved`.
- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot-9, `review`).** All 3 too-large-doc exclusions re-checked against current
      state. **Verdict: 1 doc settled but needs NO new batch2 candidate** (its 2 AO-eligible items are already active
      elsewhere — a fresh candidate would duplicate live dispatched work), **2 docs still genuinely not
      batch2-extractable** (real work remains but is human/operator-gated, not a batch2 scoping gap). See this plan's
      Progress Log for the full per-doc evidence trail — no fabricated batch2 candidates were created just to satisfy
      the todo's literal wording. **Re-check the 3 too-large-doc exclusions for a batch2 pass.** For each of
      `cefi_4surface_migration_execution_log_2026_07_24.md`,
      `issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md`, and
      `issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` (all flagged
      `doc_too_large_or_risky_for_batch: true` at batch-1 triage time): re-read the doc's current state — has its
      fast-moving live-migration activity (Track 1 dedup / LATE renames / Surface C v2 apply for the first doc; the
      OOM-outage investigation gating the second doc's design fork; the sibling-doc cross-correction for the third doc)
      settled enough that a fresh, precisely-scoped triage pass could now safely extract AO-eligible work? If yes,
      recommend and scope a `cefi_satellite_ao_dispatch_batch2` candidate item per doc with a concrete done-when; if no,
      record why it's still too volatile and re-check again at the next batch cycle. **Done when**: each of the 3 docs
      has an explicit settled-vs-still-volatile verdict recorded, with a scoped batch2 candidate item for any doc found
      settled.
- [x] ✅ [DIAG] P1. **DONE 2026-07-30 (slot-4, `data_engineering`).** Verdict: Range A/B/C landed (rc=0 net of 10
      retried transient stragglers, 504,280 renamed) but do NOT qualify as "landed cleanly" under this todo's own gate —
      STOP-ON-SURPRISE grew 1114→1292 with collisions spreading from the original 6 dates to 16+ (DERIBIT, a root-caused
      same-run-order artifact per Finding 10, not new corruption, but genuinely new collisions beyond the 6 dates). The
      session was PAUSED (not stalled) 2026-07-25 on operator request (host contention); the remaining scope
      (2,962-object safe residual + loop-until-dry + 4-surface re-proof + archival) is already its own tracked open todo
      inside the source issue doc — not an extraction gap — and has independently been ruled NOT batch2/AO-extractable
      TWICE (`cefi_satellite_ao_dispatch_batch3_2026_07_26.md` + today's na-eligibility-audit sweep, both KEEP
      dedicated-session / KEEP-NA). No new batch2 candidate created — see Progress Log for full evidence trail.
      **Re-verify the LATE colliding-venue renames exclusion.** Re-read
      `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` and
      `cefi_4surface_migration_execution_log_2026_07_24.md` for the current state of the Range A/B/C `--apply` LATE
      colliding-venue rename passes (excluded from batch-1 on evidence they were "actively in progress via a live
      human-directed /autonomous session" as of 2026-07-25). If all 3 ranges have landed cleanly (rc=0, zero new
      STOP-ON-SURPRISE collisions beyond the 6 pre-known excluded dates) and the follow-up full-range verification
      dry-run has run, mark this item DONE with the evidence citation and do NOT spin a fresh todo. If the live session
      stalled or was never actually running, extract the original todo (execute the 3 `--apply` passes + final
      verification dry-run) into a new tracked `cefi_satellite_ao_dispatch_batch2` candidate. **Done when**: a
      definitive landed-vs-still-pending verdict for the Range A/B/C migration is recorded with evidence (VM
      run.log/manifest citation), and either the item is marked DONE or a scoped batch2 candidate is created.
- [x] ✅ [DOC] P1. **DONE 2026-07-30 (slot-11, `data_engineering`).** Todos 2 and 3 had already resolved the
      too-large-doc and LATE-renames exclusions with no untracked remnant, but todo 1's own discrepancy note flagged one
      genuine remnant they didn't cover: line 355 (BYBIT futures_chain extended duplicate-verification) was still
      `- [ ]`. Migrated it to `issues/bybit_futures_chain_write_shape_2026_07_13.md` as a fresh open todo (marked
      `[x] → MIGRATED`, NOT done, in the parent) per the near-complete-plan "fold the remnant" guidance — the fold
      target was unambiguous (the item's own cited Source doc), so no operator ruling was needed. Archive banner added
      to the parent; codex-alignment check found nothing to update (every todo executed an already-decided spec).
      Grepped the corpus for every referrer of `cefi_satellite_ao_dispatch_batch1_2026_07_25` and repointed the 17 files
      using the literal `plans/active/...` path form to `/plans/archive/2026_07/...` (left 1 verbatim historical
      API-response JSON quote in `issues/backlog_brief_cross_wired_adjacent_collision_group_todos_2026_07_27.md`
      untouched — a code block reproducing an exact past `GET /api/backlog` response, not a live reference). `locked_by`
      confirmed empty on both docs. **Archive `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`** via the standard
      6-step ritual (per CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo
      elsewhere (todos 2 and 3 above should have already resolved the too-large-doc and LATE-renames exclusions — verify
      none remain untracked) → add the archive banner → run the codex-alignment check → grep the corpus for every
      referrer of `cefi_satellite_ao_dispatch_batch1_2026_07_25` and fix each path to point at the archived location →
      clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`,
      every corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the
      same commit.

## Progress Log

- **2026-07-30 (slot-9, `review`) — todo 1 reconciliation complete, 2 real discrepancies found and left honest (not
  papered over).**
  - **Doc-by-doc outcome**: of the 21 source docs, **4 needed an actual edit** —
    `aster_and_cefi_rolling_adv_feature_2026_07_21.md` (Phase 2 checkboxes flipped, substantially-done-with-2-residuals
    framing), `data_completion_cefi_2026_07_15.md` (1 of 5 items — the adapter `_finalize_session_grid` verify sub-ask —
    still had its checkbox unflipped), `plans/archive/issues/bug_c_normalize_id_collision_options_futures_2026_07_22.md`
    (added the live-measured PASS numbers batch1 produced, on top of the existing structural resolution),
    `instruments_cefi_g1_g5_gate_execution_2026_07_24.md` (the Phase-2-tail purge checkbox was still `[ ]` despite the
    `--apply` having actually run), `issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md` (closed a residual todo 4
    flagged as a follow-up, citing batch1's `@94b4aff5` fix), and
    `issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (2 numbered-list items updated — see discrepancy
    below). The remaining docs were **already correctly reconciled** by other sessions with equal-or-better evidence
    than batch1's own citations (several via later, more thorough re-verifications that superseded batch1's own
    findings) — re-editing them would have been redundant churn, not a fix.
  - **Discrepancy 1 — `issues/bybit_futures_chain_write_shape_2026_07_13.md`'s batch1 todo is genuinely NOT done.**
    `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` line 355 ("Extend BYBIT futures_chain shape-2 duplicate
    verification to the full audited scope") is still `- [ ]` unchecked — the ONLY one of the 33 todos not done, despite
    this finalize plan being machine-gated (`depends_on`+`gate_on_depends: true`) on all 33 being done before dispatch.
    The dispatcher queued this finalize todo anyway. Did NOT touch the source doc (nothing to flip — no work shipped).
    **This gate-vs-reality mismatch is itself worth a look** — flagging here rather than silently working around it; the
    batch1 plan cannot be archived (todo 4 below) while this todo remains open.
  - **Discrepancy 2 — the HYPERLIQUID recent-tail fill checkbox in `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` was
    flipped `[x]` despite its own text admitting "Not 100% yet — next check-in confirms `expected_unattempted`→0."**
    Cross-checked against the source doc (`cefi_residual_followups_after_honest_done_2026_07_17.md`'s own Progress Log):
    confirms the work is genuinely still in progress (VM launched + healthy, but a subsequent `/done` attempt on this
    exact batch1 todo was hard-rejected by the AO server's M3 gate for not meeting the done criterion). Did NOT mark the
    source doc's item done — annotated it "IN PROGRESS, not yet closed" instead, matching the true state rather than
    batch1's premature flip. The sibling HYPERLIQUID phantom-re-census item in the same doc WAS genuinely done and is
    flipped accordingly.
  - No commits shipped in any service repo — this todo is doc-reconciliation only, entirely within `unified-trading-pm`.

- **2026-07-30 (slot-9, `review`) — todo 2, the 3 too-large-doc exclusions re-checked; verdicts recorded, no new batch2
  candidates fabricated.**
  - **Doc 1 — `cefi_4surface_migration_execution_log_2026_07_24.md`: SETTLED, but no new batch2 candidate warranted.**
    The fast-moving activity that got it excluded (Track 1 dedup / LATE renames / Surface C v2 apply) has substantially
    completed since the doc's last DELTA (2026-07-24 ~13:35Z): Track 1 dedup is DONE 2026-07-27 (parent
    `cefi_consolidated_closeout_2026_07_18.md`'s Track 1 checkbox); Surface C v2 apply is DONE (Finding 7 in
    `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` — `V2 APPLY COMPLETE + GATE GREEN`); the LATE
    renames bulk landed via Range A/B/C (Finding 10, 504,280 renamed) with LIGHTER-ZKSYNC (this doc's item 6) confirmed
    fully subsumed. **This doc's own Deferred-work table (items 2b/2c/3/6) is now STALE** — the sibling issue doc is the
    current SSOT and says so explicitly ("table below is STALE, see Finding 8/9/10"). The one remaining sliver
    (2,962-object safe-venue residual + final re-proof + archive) is already tracked as a SINGLE todo in that sibling
    doc, independently re-audited **today** by the na-eligibility-audit skill (KEEP-NA valid: "resumes a migration
    explicitly PAUSED 2026-07-25 on operator request... involves cron pause/resume around prod GCS"). Of this doc's own
    2 AO-eligible candidates named in the original batch-1 exclusion note (BITGET-FUTURES catalogue rollup re-run; the
    `_DRYRUN_COLS` dry-run blind-spot confirm/fix) — **both are already drafted AND currently ACTIVE** in
    `cefi_consolidated_native_ao_extract_2026_07_25.md` (`assigned_vm: planning`, `status: active`, both still `- [ ]`),
    which independently re-derived them from the parent closeout's own (stable, non-excluded) Deferred-work table rather
    than this excluded doc. **Conclusion**: creating a fresh `batch2` candidate here would dispatch a duplicate of
    already-live AO work — the correct action is "nothing to extract, it's already extracted," not force-fitting a new
    item to satisfy the todo's literal "scope a batch2 candidate" wording.
  - **Doc 2 — `issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md`: STILL NOT batch2-extractable.** The OOM
    outage that was one of the two original blockers is resolved (Track 1b, `cefi_consolidated_closeout_2026_07_18.md`,
    🟢 RESOLVED 2026-07-25). But the doc's sole remaining todo — implement the proper fix for the per-day catalogue
    reload waste — is still an **undecided 2-option architecture fork** (range-loop-in-one-process vs. a cross-process
    `CeFiCatalogReader` cache), one option of which changes the shared VM startup script fleet-wide. This is a design
    decision, not a scoping gap; no batch2 candidate can be safely drafted until the operator/main picks a direction.
    Independently reconfirmed by today's na-eligibility-audit (KEEP-NA valid, same reasoning). **Recorded for next
    cycle**: re-check after the architecture decision is made — at that point the CHOSEN option's implementation likely
    becomes a clean, bounded batch2 candidate.
  - **Doc 3 — `issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md`: STILL NOT batch2-extractable, but the
    original exclusion reason (cross-doc disagreement) is itself resolved.** The sibling doc that used to cross-correct
    this one (`cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`) is now archived + `status: resolved`, and its
    own correction record shows the two docs' PACIFICA-SOLANA disagreement converged on this doc's original
    recommendation (quarantine, not purge) — no live conflict remains. Of this doc's 4 closure-action todos: **2 are
    DONE** (LIGHTER-ZKSYNC repartition — `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`, DONE 2026-07-27, slot-2;
    fix-the-writer — `unified-trading-library@ffce0fa6`, DONE 2026-07-26). The other **2 remain genuinely blocked on a
    human call, not a scoping gap**: EXTENDED-STARKNET's re-partition needs an operator decision on which of the two
    content-divergent copies is authoritative before any merge (characterization done 2026-07-27,
    `market-tick-data-service@4346f587` — "no authoritative copy named (operator decision, per scope)"); PACIFICA-SOLANA
    quarantine registration was explicitly kept human by `cefi_consolidated_native_ao_extract_2026_07_25.md`'s own
    2026-07-25 triage ("no defined target mechanism cited... needs human disambiguation, not a fresh independent AO
    guess"). Both freshly reconfirmed by today's na-eligibility-audit (KEEP-NA valid: "3 of 4 todos are prod GCS
    pipeline_mode re-partitions requiring de-dup MERGE semantics against a live split-brain; delete/move-safety gated").
    **Conclusion**: no batch2 candidate drafted — the remaining work needs an operator ruling (authoritative copy) and a
    human disambiguation (quarantine mechanism), not mechanical extraction.

- **2026-07-30 (slot-4, `data_engineering`) — todo 3, LATE colliding-venue renames exclusion re-verified: landed-vs-
  pending verdict recorded, no new batch2 candidate created.**
  - **Range A/B/C did land** (`issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Finding 10,
    2026-07-25): 504,280 objects renamed across 3 date-range passes (Range A `2025-11-03..2025-12-31` 4,386/0 errors;
    Range B `2026-01-04..2026-07-10` 499,119 renamed + 1,333 dup-sources deleted + 10 transient-503 `copyTo` stragglers,
    all retried and confirmed renamed; Range C `2026-07-12..2026-07-24` 765/0 errors) — rc=0 net of the retried
    stragglers. LIGHTER-ZKSYNC (batch1 item 6, ~11,283 objects) confirmed fully subsumed within this same run.
  - **But the todo's own "landed cleanly" gate is NOT met.** The post-apply full-range verification dry-run (also
    Finding 10) shows STOP-ON-SURPRISE grew from the original 1114 to **1292**, and those collisions are no longer
    confined to the original "6 pre-known excluded dates" — the DERIBIT share (10→188) is a root-caused, understood
    same-run-order artifact (Range A/B's own successful PERPETUAL renames created canonical targets that a pre-existing
    mislabeled SPOT wire object now genuinely collides with) spread across **16+ distinct dates** in Nov 2025-Apr 2026
    per the source doc's own sample — not new corruption, but genuinely "new collisions beyond the 6 dates" under the
    todo's literal wording. So this is NOT the "landed cleanly → mark DONE" branch.
  - **Nor is it the "session stalled / never ran" branch.** It ran to a real, understood midpoint and was explicitly
    **PAUSED** (not abandoned) 2026-07-25 on direct operator instruction (host contention on the shared session machine,
    not a failure), with an already-recorded resume sequence. As of today (2026-07-30) it remains un-resumed — the issue
    doc's own todo (`- [ ] [DATA] P1. Resume the paused migration...`) is still open.
  - **The remaining scope is already tracked, not an extraction gap.** The issue doc's own open todo already names the
    exact remaining work: pause cron → 4 sequential venue-scoped `cefi-late-renames --apply` passes for the 2,962-object
    safe residual (EXTENDED-STARKNET 704 / LIGHTER-ZKSYNC 177 / BYBIT-SPOT 1561 / COINBASE-FUTURES 520, zero collision
    risk — none of these venues appear in the STOP-ON-SURPRISE breakdown) → resume cron → loop-until-dry full-range
    verifier (2 consecutive clean passes, confirming `colon_wire`'s ~1,697 objects along the way) →
    `verify_cefi_canonical_4surface_2026_07_20.py` final re-proof → archive. Nothing here needs a NEW tracked item.
  - **That exact remaining scope has independently been ruled NOT batch2/AO-extractable twice already**, closing off any
    argument that a fresh batch2 candidate is overdue: (1) `cefi_satellite_ao_dispatch_batch3_2026_07_26.md` (dated the
    day after the pause) explicitly excludes this doc, calling it "a live, actively-draining migration... [that] needs
    its own dedicated session, not a batch slot"; (2) today's (2026-07-30) na-eligibility-audit sweep independently
    re-verdicted the same open todo **KEEP-NA valid** ("resumes a migration explicitly PAUSED 2026-07-25 on operator
    request... involves cron pause/resume around prod GCS renames" — genuine operator/live-session-gated work, not a
    scoping gap).
  - **Verdict recorded, no new todo spun.** Creating a fresh `cefi_satellite_ao_dispatch_batch2` candidate for this
    scope today would duplicate an already-tracked todo AND directly contradict two independent same-corpus rulings
    (2026-07-26 and 2026-07-30) that this work needs a dedicated live/human-directed session, not mechanical AO
    extraction. Marking this finalize-plan todo DONE reflects that the verdict itself (not the underlying migration) is
    now definitively recorded — the underlying migration stays correctly open, tracked, and `assigned_vm: NA` right
    where it already is (`issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`).
  - No commits shipped in any service repo — this todo is doc-reconciliation/verdict-recording only, entirely within
    `unified-trading-pm`.
  - No commits shipped in any service repo — this todo is doc-reconciliation/verdict-recording only, entirely within
    `unified-trading-pm`.

- **2026-07-30 (slot-11, `data_engineering`) — todo 4, archival complete.**
  - **Resolved the gate-vs-reality mismatch todo 1 flagged**: parent line 355 (BYBIT futures_chain extended
    duplicate-verification) was the only one of the parent's 33 todos still `- [ ]`. Per
    `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s near-complete-plan handling ("split it, or
    fold the remnant"), migrated it verbatim into `issues/bybit_futures_chain_write_shape_2026_07_13.md` as a new open
    `- [ ]` todo (that doc had just gone ARCHIVE-worthy per its own 2026-07-30 na-eligibility-audit entry — this todo
    correctly keeps it active/tracked instead). Marked the parent's line 355 `[x] → MIGRATED ... NOT done` — never
    claimed shipped. No operator ruling needed: the fold target was the item's own named Source doc, not a multi-option
    epic/sibling choice.
  - **Archive banner** added to the parent (`> 🟢 ARCHIVED 2026-07-30`) and to this finalize doc; both frontmatters
    flipped `status: active` → `complete`.
  - **Codex-alignment check**: nothing to update — every todo across both plans executed an already-decided spec (data
    backfills, verification re-checks, doc reconciliation), no new durable contract emerged from this batch.
  - **Corpus referrers**: grepped for `cefi_satellite_ao_dispatch_batch1_2026_07_25` and
    `cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25` corpus-wide. 17 files carried the literal
    `plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md` path form (frontmatter `related:` lists +
    line-numbered prose citations) — all repointed to `plans/archive/2026_07/...`. Left
    `issues/backlog_brief_cross_wired_adjacent_collision_group_todos_2026_07_27.md`'s one
    `"plan_ref": "plans/active/..."` line untouched — it's inside a fenced code block reproducing a verbatim historical
    `GET /api/backlog` JSON response, not a live doc reference; rewriting it would falsify the quote. Bare-name prose
    mentions with no `plans/active/` path prefix (dozens, mostly in already-archived Progress Log narrative describing
    past events) were left as-is — they are historical narrative, not machine-checked path references. Referrers to this
    finalize doc's own path were also repointed.
  - `locked_by` confirmed empty on both docs (no unlock needed).
  - Both docs moved to `plans/archive/2026_07/` in the same commit as this final edit.
