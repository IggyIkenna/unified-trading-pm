---
doc_type: plan
title: CeFi satellite AO batch 10 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Finalize twin for `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` (drafted 2026-08-08 by the /ag-closeout-audit
  skill, slot 8, dispatch agt-6bc9c4). Reconciling 6 source docs' checkboxes once batch10's 6 todos land, asking the
  operator to unlock the 2 fully-done-but-locked docs found this run, and archiving batch10 via the 6-step ritual.
  `status: active` from the start per the 2026-07-30 no-double-gate ruling; `gate_on_depends: true` machine-holds every
  todo until batch10's own tasks are done.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-10, finalize, iterative-drain]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch9_2026_08_07_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-15"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
effort: high
sequential: true
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_satellite_ao_dispatch_batch10_2026_08_08]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-08-08 (scheduled autonomous dispatch, agent-orchestrator slot 8, dispatch
  agt-6bc9c4, tranche=cefi), paired with `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` per task_template.md §4's
  finalize-plan-coverage rule.
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
---

# CeFi satellite AO batch 10 — finalize

> **Status: active from the start (2026-07-30 ruling — no double gate).** `gate_on_depends: true` already machine-holds
> every todo below until batch10's own 6 tasks are `done`, regardless of batch10's own `status` (draft or active). Only
> the batch itself needs `status: draft` + explicit operator approval; this finalize plan carries no independent
> judgment call. **Machine-gated on `cefi_satellite_ao_dispatch_batch10_2026_08_08.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 6 tasks in that plan are `done`.
> `sequential: true` because todo 2 depends on todo 1's reconciliation, and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-08-10 (slot-17).** Reconcile all 6 source docs' checkboxes. Batch 10's 6 todos draw
      from 6 distinct source docs — for each landed todo, flip/append the corresponding checkbox/status text in its
      named source doc citing the shipping commit: (1)
      `issues/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` (Phase C); (2)
      `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` (Finding 8/10, append investigation result
      to Findings — do not flip a checkbox that doesn't exist for an audit-only item); (3)
      `issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md` (Relaunch todo); (4)
      `issues/coverage_floor_new_backfill_gaps_found_2026_07_27.md` AND its duplicate in
      `issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md` (keep both in sync); (5)
      `issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md` (both Open Questions items); (6)
      `issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (line 718 P3 checkbox). **Verify each cited
      commit is reachable on `origin/live-defi-rollout` before citing it.** **Done when**: every landed todo's source
      checkbox/section is flipped or appended with a verified commit, and each source doc's remaining-open count is
      explicitly re-stated.
- [x] ✅ [DOC] P1. **DONE 2026-08-15 (slot-3).** **STALE PREMISE CORRECTED (2026-08-15, /plan-reconcile)** — both named
      docs' `locked_by` was already cleared corpus-wide 2026-08-12
      (`locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`, operator ruling Option B); re-verified
      2026-08-15, neither `issues/cefi_coinbase_cde_urdi_zero_records_2026_07_28.md` nor
      `issues/cefi_universe_capture_rule_2026_06_23.md` carried a `locked_by` value — both were bridged via
      `archive_exempt: true` (0 open todos each) awaiting this follow-on archival pass. No operator unlock-ask was
      needed for either doc. **Ran the standard 6-step archival ritual on both**
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — dropped each `archive_exempt` bridge
      line, added an ARCHIVED banner, `git mv`'d both to `plans/archive/2026_08/issues/`, fixed every corpus referrer
      using an actual path form (6 files: `/codex/02-data/cefi-capture-universe.md` ×3,
      `plans/active/instruments_completion_tracker_2026_07_06.md`,
      `plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` ×2). Codex-alignment check: doc2's durable
      content already lives at `/codex/02-data/cefi-capture-universe.md` (that doc's own "durable concise reference"
      anchor line); doc1's fix is fully described in code + tests, no new codex contract. Bare-filename prose citations
      (no path form) were left as historical narrative, matching the existing corpus convention (e.g. archived
      `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` cites sibling archived docs by bare name). **Done when**: both
      docs are archived and every corpus referrer resolves to the new path. See Progress Log below for the shipping
      commit.
- [x] ✅ [REVIEW] P1. **DONE 2026-08-15 (slot-3).** **STALE PREMISE CORRECTED**: "before batch11's Phase-1 re-triage" no
      longer applies — batch11 was drafted+dispatched+archived 2026-08-09
      (`plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md`), and the series has since run through
      batch19 (`plans/active/cefi_satellite_ao_dispatch_batch19_2026_08_13.md`, currently active) — the real next batch
      is **batch20**. Re-checked all 32 Deferred items from `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` against
      live corpus/VM state. Full per-item breakdown in the Progress Log below. Zero new batch todos drafted, per this
      todo's own instruction.
- [ ] [DOC] P1. **Archive `cefi_satellite_ao_dispatch_batch10_2026_08_08.md`** via the standard 6-step ritual: confirm
      the Deferred/Archivable/Cross-tranche/Orthogonality-fixes sections (informational, never batch todos) need no
      separate migration → add the archive banner → run the codex-alignment check (batch10 creates no new durable
      contract beyond the 2 orthogonality retags already landed directly on their source docs; confirm still true) →
      grep the corpus for every referrer of `cefi_satellite_ao_dispatch_batch10_2026_08_08` and repoint each to the
      archived path → clear `locked_by` (already empty, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_08/`, every corpus referrer resolves to the new path, `run_hygiene_sweep.sh` stays green, and
      this finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual (todo 4) and the
  locked-plan-needs-human-unlock rule (todo 2).
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol
  that shaped batch10's extraction.

## Progress Log

- **2026-08-15 (slot-3, todo 3)** — re-checked all 32 Deferred items from batch10 for cleared gates. **Premise
  correction**: batch11 (drafted+archived 2026-08-09) through batch19 (active, 2026-08-13) already ran while this
  finalize plan sat gated behind batch10's own todos — this todo's "before batch11" framing is 9 batches stale; the next
  batch to draft against these findings is batch20. Per-item outcome (grouped by batch10's own Deferred taxonomy; docs
  not named below had no material change — still gated exactly as batch10 described):
  - **Fully resolved + archived since batch10 (no batch20 action — already closed out)**: (1)
    `issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md` (resolved 2026-08-08, same day as
    batch10's own draft — a same-day race, not a batch10 audit miss); (2) `data_completion_cefi_2026_07_15.md`
    (conflict-gated parent hub — archived); (3)
    `issues/cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md` (conflict-gated,
    `resolved_by: cefi_content_migration_fleet_half_incomplete_2026_07_26`); (4)
    `issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md` (time-gated, resolved
    2026-08-08). All 4 confirmed via `find plans/archive -name <basename>` + an ARCHIVED/resolved banner grep.
  - **Gate cleared, doc now 0-open but not yet archived (archive-candidate for the hygiene sweep, not fresh batch
    work)**: `issues/bybit_futures_chain_write_shape_2026_07_13.md` — operator ruled 2026-08-09 ("delete over
    leave-as-is"), the 490-object delete executed same day, open=0.
  - **Gate cleared via `tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`**: both items
    resolved (dispatched task `-a9c2510c68f9`, slot-27, 2026-08-09), open=0 — same as above, archive-candidate only.
  - **Already claimed + shipped by an intervening batch (no batch20 action — would double-dispatch)**:
    `aster_and_cefi_rolling_adv_feature_2026_07_21.md`'s flagged item moved to
    `cefi_satellite_ao_dispatch_batch12_2026_08_09.md` todo 2 (archived, done); one of
    `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`'s items was independently picked up as batch11 todo 6
    (archived, done) — that doc's OTHER ~14 open items are unrelated human-only design calls, unchanged.
  - **(a) `issues/deribit_combo_perpetual_partition_move_2026_07_21.md`** — the specific gate batch10 named (an explicit
    future operator review) **cleared**: operator approved the `--apply` 2026-08-11 (via main). Not a batch20 candidate
    though — a worker (slot 7, task `-74ce5c3b03c5`) began executing the same day, found the 2026-07-21 15,119-row
    baseline had materially drifted (new wrong-partition duplicates from ongoing ingestion not in the original count)
    and paused `--apply` pending a GCS-driven re-census; this is live work under the doc's existing open todo, not a gap
    to draft into batch20.
  - **(b) `issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md`** — gate **unchanged**: the conflicting
    active claim (`issues/cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md`) is
    confirmed still `status: open` and still live (round 5/6 relaunches ongoing per its own 2026-08-09 context-scout
    note) — has neither shipped nor gone stale. Re-check again before batch20.
  - **(c) `issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`** — the 8th relaunch VM
    (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, last independently confirmed RUNNING at 24% progress
    2026-08-10T22:01Z) is **no longer present in `gcloud compute instances list`** as of this check (2026-08-15) — it
    has reached a terminal state (`name~cefi-queue` and `name~cefi AND status=RUNNING` filters both confirm it's gone;
    the currently-running cefi fleet is all `mdps-cefi-*`/`mtds-live-cefi-*`, a different workload). **Whether it
    completed the full 2019-01-01..2026-08-08 span or died a 9th time is NOT verified this pass** — the
    `DeploymentsRegistry`/`PROGRESS.json` check needed to distinguish those needs UTL's `cloud_interface` (`gsutil cat`
    is blocked fleet-wide by `block_destructive_commands.py`'s GCS-object-op guardrail, correctly, per
    `/codex/05-infrastructure/gcs-object-operations.md`) — flagging as the next concrete step rather than guessing.
    Gate: **partially cleared** (VM is terminal, a re-check is now actionable) but the underlying "genuinely completes"
    done-when is still unconfirmed — not drafted here per this todo's own instruction, and the outcome determines
    whether batch20 needs a 9th-relaunch todo or can close this doc out.
  - **Reaffirmed still-gated, no change** (spot-checked, no clearance found): `crypto_alpha_research_2026_07_24.md` (20
    open, book-sizing judgment calls), `instruments_cefi_g1_g5_gate_execution_2026_07_24.md` (G1/G4 still need ruling),
    `issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md` (explicitly retagged `[OPERATOR]` again
    2026-08-12), `issues/upbit_cefi_data_gap_may_2026_2026_08_04.md` (re-confirmed `NA`/credential-gated),
    `cefi_ml_directional_continuous_live_2026_06_20.md` (7-day live-capital cutover re-checked 2026-08-09, result
    NOT-COMPLETE), the remaining human-only design docs, and the remaining time/conflict-gated docs not named above. Two
    docs showed operator/design engagement worth a closer read before batch20 without a confirmed full clearance:
    `issues/fail_hard_canonical_enforcement_design_2026_07_20.md` (an operator-requested design pass ran 2026-08-11,
    open count dropped since batch10 but the doc still shows 4 open) and
    `issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md` (an interactive
    `/plan-reconcile` operator pass 2026-08-12 addressed the sole open item's technical finding, still shows 1 open as
    of 2026-08-15). Method: fresh-pulled every slot repo to `origin/live-defi-rollout`, then for all 32 docs checked
    on-disk location (active vs. archived), `status:`/open-vs-done checkbox counts, and grepped each for any
    2026-08-09-through-2026-08-15-dated Progress Log activity; the 3 explicitly-named items (a/b/c) + the docs showing
    dated post-08-08 activity got a full tail-read; the rest were confirmed unchanged via the dated-activity grep
    finding nothing new.
- **2026-08-15 (slot-3, todo 2)** — archived both `cefi_coinbase_cde_urdi_zero_records_2026_07_28.md` (0 open, 3/3 todos
  `[x]`) and `cefi_universe_capture_rule_2026_06_23.md` (0 open, 16/16 todos `[x]`) via the 6-step ritual: dropped each
  `archive_exempt` bridge line, flipped `status: open` → `resolved`, added an ARCHIVED banner citing this doc,
  `git mv`'d both to `plans/archive/2026_08/issues/`. Referrer sweep: both docs' only ACTUAL-path-form referrers (6
  files: `/codex/02-data/cefi-capture-universe.md` frontmatter `related:` + anchor line + composes-with line,
  `plans/active/instruments_completion_tracker_2026_07_06.md` `related:` entry,
  `plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` `related:` + `context_scope:` entries) repointed to
  `/plans/archive/2026_08/issues/`. Bare-filename prose mentions across ~8 other docs (both active and already-archived)
  left unchanged, matching the corpus's existing convention for historical narrative citations. Codex-alignment check:
  doc2's durable content already lives at `/codex/02-data/cefi-capture-universe.md` (its own pre-existing "durable
  concise reference" anchor, now updated to state it is the live SSOT); doc1's crash-hardening fix is fully captured in
  code + regression tests, no separate codex contract needed. No new referrer-broken links found post-move (`grep -rl`
  re-run on both new paths after the `git mv` confirmed only the fixed files + the two archived docs themselves
  reference the new paths).
- **2026-08-10 (slot-17, todo 1)** — reconciled all 6 source docs' checkboxes for batch10's 6 landed todos; **every
  cited commit verified as an ancestor of `origin/live-defi-rollout` before citing**. Per-doc outcome + remaining-open
  count: (1) `cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` — Phase C already `[x]`
  DONE-BY-FAIT-ACCOMPLI (flip `aba237f1b9`, slot-8 2026-08-08); **2 open** remain (Phase D/E VM-scale rebuild items).
  (2) `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` — Finding 11 (2026-08-09) already appended
  (`b8336a6b24`); audit-only item, no checkbox exists to flip; **1 open** remains (operator question on the 1292
  collisions). (3) `cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md` — Relaunch todo already `[x]`
  (`0273bc1e08`/`aa51d8d3f5`, evidence `market-data-processing-service@e9f9819` verified) + "2026-08-08 84-cell audit"
  appended; **2 open** remain (2025-11-01/2026-01-01 raw-gap investigation; per-day relaunch gated on
  `mdps-backfill-cefi-20260808-095136` terminal state). (4) `coverage_floor_new_backfill_gaps_found_2026_07_27.md`
  (archived resolved, **0 open**; deregistration `unified-api-contracts@56db28e6` verified) + duplicate
  `coverage_floor_registries_no_cross_propagation_2026_07_17.md` kept in sync with a RESOLVED 2026-08-10 note on its
  `[x]` BINANCE-DELIVERY checkbox; **2 open** remain there (both unrelated P3 items). (5)
  `tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md` — **both P3 follow-up checkboxes FLIPPED this
  run**: heartbeat status field (`deployment-service@88f8834c`) + `_publish_boundary_event` exception
  (`market-tick-data-service@f6b7f8b7`); **0 open** remain. (6)
  `cefi_residual_followups_after_honest_done_2026_07_17.md` — line-718 P3 already `[x]` (`6ae449bbb3`,
  `deployment-service@7b4c69d72` verified); **5 open** remain (all other independent P0-P2 items). See also the
  `## Todos` flip above; source-doc edits shipped via `safe-doc-push.sh`.
- **2026-08-08** — drafted by the `/ag-closeout-audit` cefi run (slot 8, dispatch agt-6bc9c4) alongside batch10;
  authored `status: active` per the 2026-07-30 no-double-gate ruling, machine-held by `gate_on_depends: true` until
  batch10's todos are done.
- **context-scout 2026-08-15**: populated/refreshed context_scope (3 entries) — added
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` (already cited in this doc's own "Codex
  SSOTs" section).
