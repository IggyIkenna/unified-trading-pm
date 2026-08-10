---
doc_type: issue
title: ag-closeout-audit defi parked findings — 2026-08-10
summary: >-
  Parked findings from the scheduled ag_closeout_auditor run (2026-08-10, tranche=defi, slot 14). Phase 0: 91 corpus
  members (up from 80 on 2026-08-08), 25 covering docs, 15 never-cited candidates. 1 resolved directly via live infra
  investigation (iterative-drain step 1) before Phase 1 triage; 14 deep-classified via Phase 1 Workflow — 7 confirmed
  exclude_cross_cutting (legitimate multi-AG span, no new classic dual-tag mistags), 7 orphaned_never_touched. Of the 7
  orphans' combined open items, exactly 1 is genuinely AO-eligible-and-defi-owned right now (HYPERLIQUID perp_funding
  gap scoping query) — pool too thin to justify a new batch13 doc (precedent: 08-07/08-08's Option A for equally-thin
  pools), flagged as a batch13 candidate for a future round. 2 docs flagged as likely mistagged into defi from an
  unrelated AO-dispatch-mechanism incident (other tranche's write remit, informational only). 2 carried-forward
  informational findings (other-tranche remit) re-verified still open. 7 findings total. **Third run same day (slot 20,
  agt-af667b, iterative-drain follow-up ~4h later)**: 93 members (was 91), 1 genuinely new candidate classified (Finding
  8, exclude_cross_cutting) + 1 material live-state update (Finding 9: the R3 rebuild VM tracked by Finding
  5/defi_track01 failed a 2nd time, resource-exhaustion pattern, no 3rd relaunch attempted; consolidator lock separately
  confirmed self-healed, not a second stuck-lock problem). Batch13 decision unchanged (still 1-item pool). 9 findings
  total across all 3 runs today.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ag-closeout-audit, parked, defi, orphan]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    /plans/active/defi_satellite_ao_dispatch_batch10_2026_08_06.md,
    /plans/active/defi_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_06.md,
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_07.md,
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_08.md,
    /plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md,
    /plans/active/issues/defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md,
    /plans/active/issues/defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md,
  ]
created: 2026-08-10
parent_epic: defi_master
assigned_vm: NA
priority: P3
last_updated: 2026-08-10
source: >-
  ag_closeout_auditor scheduled run 2026-08-10 (tranche=defi, slot 14, DISPATCH_ID=agt-f508ad); iterative-drain
  follow-up same day (tranche=defi, slot 20, DISPATCH_ID=agt-af667b)
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_08.md,
    /plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# ag-closeout-audit defi parked findings — 2026-08-10

## Phase 0 summary

`generate_ag_closeout_audit_candidates.py --tranche defi`: 91 corpus members (up from 80 on 2026-08-08 — 11 new/
newly-qualifying docs over 2 days), 25 covering docs (consolidated closeout + every active batch/finalize pair +
`depends_on`-resolved forks), 15 never-cited, 76 cited-somewhere. `check_ag_closeout_linkage.py`: 38 orphans (baseline
49, PASS) — 3 defi-tagged hits, all reconciled: 2 are in this run's 15-candidate set (see below), 1
(`defi_oracle_family_empty_path_exception_classification_2026_08_09.md`) is correctly excluded from the candidate
script's never-cited bucket because it is `self_dispatched` (`assigned_vm: planning` + `status: open` — it covers
itself, no external citation needed). This refines Finding 4 of the 08-08 report: the candidate-script-vs-linkage-gate
disagreement isn't only a `cited_in_covering_doc` blind spot, it also covers the `self_dispatched` exclusion path — the
candidate script remains the correct oracle to trust in both cases; the linkage gate's narrower closeout-family graph
doesn't model self-dispatch. Orthogonality check (below) found no new classic "defi + exactly one other tranche"
dual-tag mistags this round.

**Iterative-drain step 1** (re-check the 2026-08-08 report's carried findings before fresh triage) resolved every
AO-eligible item it had flagged, without needing fresh triage agents:

- Finding 1 item 1 (`defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md`) — now cited in
  `defi_satellite_ao_dispatch_batch11_2026_08_09.md:438` (picked up by na-eligibility-audit's RECLASSIFY sweep since
  08-08). Resolved, no longer a candidate.
- Finding 1 item 2 (`defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md` item 3) — already noted ARCHIVED
  2026-08-09 in the 08-08 report itself. Resolved.
- Finding 3 (`defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md`) — live-investigated today (see Finding 5
  below); alert-clearing half closed directly, only the operator/design-gated todo 3 remains.

Findings 2 and 5 (both explicitly other-tranche write remit, not defi's to fix) were re-verified still accurate and are
carried forward once more as Finding 6 below, per this doc's own stated ownership note.

## Finding 1 — `defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md` (orphaned_never_touched)

2 genuinely remaining open items, 0 citation anywhere in the 25-doc covering set:

1. **`[DIAG] P2` — READY NOW, the sole genuinely AO-eligible-and-defi-owned item this entire run.** Bounded manifest
   query: scope the HYPERLIQUID `perp_funding` gap around 2026-04-20 across April-May 2026 (single-day hole vs wider
   window; confirm it's a separate incident from the already-tracked
   `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02` gap, since 2026-04-20 predates that gap's window). Repo:
   market-tick-data-service. `ao_eligible=true`, `gate_type=none`.
2. `[DATA] P3` — re-run `backfill_lst_yields_30day.sh` once both item 1 and the manifest-consolidator outage (Finding 5)
   resolve. `ao_eligible=true` but `gate_type=time` — the consolidator has NOT genuinely caught up yet (see Finding 5's
   live evidence: the resumed scheduler's cycles are still no-op'ing on a lock held by an in-flight rebuild VM). Not yet
   dispatchable.

## Finding 2 — `defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md` (orphaned_never_touched)

2 genuinely remaining open items, 0 citation anywhere in the 25-doc covering set:

1. `[DESIGN] P2` — detection/warning mechanism design call for the `ALLOW_STALE_FALLBACK` false-completion signature.
   `ao_eligible=false`, `gate_type=human-only`. Genuinely uncovered corpus-wide (not just within the covering set — the
   Phase-1 agent independently confirmed via a non-covering tracker doc that this is explicitly "Not done... Nobody").
2. `[DATA] P1` — relaunch the `dex_swaps` legacy-fold VM run without `--allow-stale-fallback`, once the consolidator
   catches up. `ao_eligible=true` but `gate_type=time`, **and already actively tracked outside the 25-doc covering set**
   by `/plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` row 4 (an active, defi-tagged,
   `assigned_vm: NA` plan that isn't a batch/finalize/consolidated-closeout doc, so it's invisible to the candidate
   script's strict covering-set definition by design, not by bug). **Do not draft a batch item for this — it would
   duplicate existing tracking.** Live-confirmed today (see Finding 5): the precondition is still unmet.

This doc's `[defi, infrastructure]` dual-tag was flagged by the Phase-1 agent as matching the "defi + exactly one other
tranche" mistag heuristic, but it is **not a fresh finding** — the infra tranche's own audit
(`ag_closeout_audit_infra_parked_2026_08_08.md` finding 22, carried to `…_08_09.md` finding 6) already surfaced this,
and the operator explicitly ruled 2026-08-09 to retag from single `[infrastructure]` to this dual-tag (recommendation B:
the DATA todo is genuinely defi-specific, the DESIGN todo is data-pipeline-flavored but not squarely either tranche).
Noted for completeness only.

## Finding 3 — 3 orphaned docs with zero AO-eligible remaining work

Each has exactly one operator/design-gated remaining item; none warrant batch-drafting attention regardless of citation
status:

1. **`defi_aavev3_bare_alias_enumerator_bug_2026_08_08.md`** — `[OPERATOR] P2` (46,300-row manifest purge; twin-exists
   precondition confirmed satisfied 2026-08-09, but the todo stays explicitly operator-tagged and Part 1 of the 5-part
   delete-safety proof wasn't independently re-verified this pass) + `[DESIGN] P3` (whether `PROTOCOL_LAUNCH_DATES`
   should keep alias dict-keys). Both `ao_eligible=false`.
2. **`defi_lst_adapter_factory_family_unused_by_production_path_2026_08_09.md`** — `[OPERATOR] P2` (delete vs. wire-a-
   real-consumer decision for 6-7 LST adapter classes). Already independently reaffirmed KEEP-NA by a same-day
   round9-reclassify-satellite-sweep entry in its own Progress Log. `ao_eligible=false`.
3. **`onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md`** — `[DESIGN] P1` (quant-math methodology
   call for the `staking_apy_bps` annualization formula; 3 undecided candidate directions, explicitly out of
   `data_engineering` craft scope per a prior round9-reclassify-satellite-sweep entry). `ao_eligible=false`. (This doc's
   OTHER item was already extracted to the now-archived `defi_satellite_ao_dispatch_batch12_2026_08_09.md`.)

## Finding 4 — 2 likely-mistagged AO-dispatch-mechanism docs, out of defi's write remit

Both are part of a 3-doc family of near-identical "task repeat-wedged N slots, durably parked" issue docs filed
2026-08-08 for the same fleet-wide AO crash-loop incident (TmuxPruner/AgentKeeper kill-logic — the root-cause doc
itself, `review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md`, is tagged `asset_group: [ao]`, now archived/
resolved). Their own remaining content is 100% AO dispatch-mechanism work with zero defi-domain content — the
`asset_group: [defi]` tag on each appears inherited from "which AG did the originally-wedged task belong to," not from
these docs' own substance:

1. **`defi_compute_gcp_migration_009_repeat_wedge_parked_2026_08_08.md`** — 3 items: 1 workload-correlation check
   (`ao_eligible=true`, `gate_type=time` — the tmuxpruner prerequisite is now resolved but this doc's own operator
   checkpoint stays "parked" as of 2026-08-09), 1 operator unpark decision (`ao_eligible=false`), 1 post-unpark
   verification (`ao_eligible=true`, `gate_type=time`).
2. **`solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md`** — 3 items, 2 of which are genuinely
   `ao_eligible=true`/`gate_type=none` (READY NOW): the same workload-correlation check, and a proposed
   `skip-current-task`-to-`park` auto-escalation feature mirroring `auto_park.py`'s existing threshold logic. Both are
   pure agent-orchestrator fleet-dispatch-reliability work.

Per the corpus's established primary-owner rule (mirrors the 08-08 report's Finding 2 handling), defi classifies and
reports these — the actual dispatch (a mistag fix + likely an `ao`-tranche satellite batch) is the `ao` tranche's own
write remit, not actioned here. The third sibling doc in this family
(`citadel_satellite_ao_dispatch_batch1_004_repeat_wedge_parked_2026_08_08.md`) is already correctly tagged
`[cross-cutting]`, suggesting this may be a partial rather than corpus-wide convention gap.

## Finding 5 — `defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md`: iterative-drain resolution (already landed)

Live-investigated today as part of iterative-drain step 1 (re-checking the 08-08 report's Finding 3 time-gate) — this
surfaced more than a simple "is it done yet" check, so the full evidence trail is recorded directly on the source doc
(commit pending in this same session) rather than only here:

- The original rebuild VM (`canonical-migration-defi-rebuild-20260806-223130`) was **SPOT-preempted**, not naturally
  completed (`PROGRESS.json` showed `last_completed_date=2024-09-05` against a 2026-12-31 target when its heartbeats
  stopped). A successor VM (`canonical-migration-defi-rebuild-20260809-163511`) is the preemption-recovery relaunch,
  RUNNING as of this check — the rebuild itself is genuinely still in-flight, tracked at
  `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s R3 item ("terminal state (not yet)"), not duplicated in the
  consolidator doc.
- The consolidator Cloud Scheduler job resumed EARLY (`state=ENABLED` since 2026-08-09T11:25Z) — roughly 4 hours
  _before_ the original VM's last heartbeat, i.e. genuinely concurrent with the still-running rebuild, not
  post-completion as the source doc's todo had assumed.
- **Verified this is NOT a correctness race**: live Cloud Run logs for the consolidator job show every invocation over
  the trailing hour as `success=True shards=0 ... error=locked` ("fresh lock present") — the consolidator's own code
  defends against concurrent-merge regardless of the scheduler's enabled/paused state. `CONSOLIDATOR_DOWN` has genuinely
  cleared (zero occurrences in Cloud Logging over the trailing 24h).
- Closed the alert-clearing half of the source doc's todo 2 directly (with full evidence + citations); left the
  rebuild-completion tracking to `defi_track01`'s R3 item (already covers it, not duplicated); todo 3 (Slack-routing
  design question) remains open, operator/design-gated.

This doc is now fully accounted for: 1 item closed today, 1 item (todo 3) remains genuinely open but
`ao_eligible=false`. Not a batch candidate.

## Finding 6 (informational, carried forward) — other-tranche write remit, re-verified still open

From the 08-06/08-07/08-08 reports, re-checked live today, both still accurate:

1. Stale "0 open todos" claims for `phantom_audit_estate_coverage_gap_2026_07_10.md` persist in
   `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md:316` and
   `tradfi_consolidated_closeout_2026_07_18.md:745` (line number shifted from the 08-08 report's `:860` citation — the
   file has changed since; the doc still carries 1 open `[SCRIPT] P2` checkbox). Fix belongs to cefi/tradfi workers, not
   defi.
2. `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` and
   `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` both still carry `asset_group: [defi]`,
   unretagged after 3 days (flagged 2026-08-07, still open today) — both are `ui`-tranche content per the 08-07 report's
   original finding. This is a `ui`-tranche pickup, not defi's write remit.

## Finding 7 (informational) — orthogonality + linkage-gate cross-checks clean

Phase 1's 7 `exclude_cross_cutting` verdicts (of 14 classified) all carry genuine multi-AG spans (2-6 distinct tags)
backed by real, differentiated per-AG body content — none is the flagged "defi + exactly one other specific AG" mistag
pattern (the one dual-tag doc found, Finding 2's `defi_manifest_allow_stale_fallback...`, was already operator-
adjudicated, not a fresh mistag). No new mistags of that specific pattern to report this run. The linkage-gate
cross-check (Phase 0 summary above) is likewise clean once the `self_dispatched` exclusion path is accounted for.

---

## Batch13 decision

**No `defi_satellite_ao_dispatch_batch13` drafted this round.** Total AO-eligible-and-defi-owned pool: **1 item**
(Finding 1's HYPERLIQUID perp_funding scoping query) — well below the established batch size range (batch9=17 todos,
batch10=9 todos) and even below the 08-08 report's own 3-item pool that it also declined to batch (Option A precedent).
The 2 additional `ao_eligible=true`/`gate_type=none` items found (Finding 4, the solana_dex_pool_swaps_indexer sibling)
are not defi-owned and are excluded from this tranche's pool per the primary-owner rule. Flagging the single ready item
here for a future audit (or an operator electing to batch now) to pick up directly.

**Parked count reconciliation**: 7 findings (2 orphaned docs with a mix of ready-now/time-gated/human-only items + 1
grouped finding covering 3 zero-AO-eligible docs + 1 grouped mistag finding covering 2 docs + 1 already-resolved
iterative-drain finding + 1 grouped informational carry-forward + 1 informational cross-check note) = 7 entries written
to this doc. ✓

## Progress Log

- **ag_closeout_auditor 2026-08-10** (tranche=defi, slot 14, DISPATCH_ID=agt-f508ad): scheduled run. Phase 0 (candidate
  script + linkage-gate cross-check + iterative-drain step 1, including one live infra investigation that resolved a
  carried time-gate finding directly on its source doc) + Phase 1 (14-agent Workflow classification of all never-cited
  candidates) + Phase 2 (this synthesis) complete. Phase 3: no batch13 drafted (1-item pool, see decision above). 7
  findings parked, ledger reconciled.
- **Second concurrent run, same day — `/ag-closeout-audit all` (slot 26, task-less one-off)**: an independent
  all-tranche run hit a filename collision with this doc mid-push (both runs landed
  `ag_closeout_audit_defi_parked_2026_08_10.md` the same day — expected under concurrent sharded/all-mode dispatch, per
  SKILL.md's own documented hazard). Resolved per the "append, don't replace" rule rather than picking one side: this
  doc (the more thorough 15-candidate, full-pre-filter run) is kept as the base; the slot-26 run's independent, narrower
  pass (using `check_ag_closeout_linkage.py`'s stricter graph-reachability signal directly, 2 defi candidates only)
  reached IDENTICAL conclusions on both docs it examined — `defi_aavev3_bare_alias_enumerator_bug_2026_08_08.md`
  (verdict `operator_gated_other`, same 2 items: the operator-only 46,300-row purge + the `PROTOCOL_LAUNCH_DATES` design
  call) and `onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md` (verdict
  `orphaned_never_touched`/design-gated, matching this doc's Finding 3 item 3) — no new content, no contradiction,
  cross-verification only. Slot-26's own batch16 draft (unrelated — cefi tranche) and 6 other tranches' parked-findings
  docs shipped independently in that same push; see `ag_closeout_audit_cefi_parked_2026_08_10.md` / `…ao_parked…` /
  `…cross_cutting_parked…` / `…tradfi_parked…` / `…infra_parked…` / `…prediction_parked…` for that run's other tranches.
  `check_ag_closeout_linkage.py` baseline ratcheted 49→0 corpus-wide by that run (this doc's own 2 defi orphans included
  in that count at the time, both resolved by the same mechanism this doc already independently confirmed —
  operator-gated, not a coverage gap).

## Third run, same day — iterative-drain follow-up (slot 20, DISPATCH_ID=agt-af667b)

Re-ran Phase 0's candidate script fresh (~4h after the slot-14 run): 93 members (was 91), 17 never-cited (was 15).
Diffed the two never-cited lists by name — 15 of 17 are the SAME docs already classified above (8 named
orphaned/resolved + 7 unlabeled `exclude_cross_cutting`); the +2 delta is this doc's own filename (self-referential,
expected, not a new orphan) and exactly ONE genuinely new candidate:

## Finding 8 — `dp_cron_did_not_fire_false_positive_burst_2026_08_10.md` (exclude_cross_cutting)

New today (created after the slot-14/26 runs). `asset_group: [cross-cutting, tradfi, sports, prediction, defi]`,
`parent_epic: infrastructure_master` — genuinely spans 5 asset groups (a DP-LIVE-003 false-positive-burst root-cause doc
covering VM-prefix-registry findings across multiple AGs' live producers), matching the legitimate
multi-AG-plus-cross-cutting pattern, not the "one AG + cross-cutting" mistag shape. Per the primary-owner rule
(`parent_epic: infrastructure_master`), its owning tranche is `infra`, not `defi` — defi classifies and reports only. 4
open todos (2 `[OPERATOR]` cross-AG decisions, 2 `[SCRIPT]` infra/prediction-scoped verification steps); none is a
bounded defi-only extractable item — the one defi-relevant line item (`defi-recursive-` VM absence) is bundled inside a
shared multi-AG operator todo, not separable without duplicating/fragmenting that decision. `ao_eligible=false` for
defi's purposes.

## Finding 9 (informational) — R3 rebuild VM 2nd terminal failure + consolidator self-heal, documented at source

Live re-check of Finding 1 item 2 / Finding 5's time-gates (iterative-drain step 1) surfaced a material update: the
`canonical-migration-defi-rebuild-20260809-163511` successor VM (Finding 5's subject) has ALSO now reached a terminal
state (2026-08-10T03:57:22Z) — a resource-exhaustion-pattern kill (`rc=137`, GCS connection-pool exhaustion symptoms,
self-delete via `VM_SHUTDOWN_ON_COMPLETION`), NOT a SPOT preemption. Progress advanced to
`last_completed_date= 2025-06-02` (from `2024-09-05`) but is still far short of the `2026-12-31` target. This is the
prefix's 2nd terminal-non-completion in a row, matching the sibling `defi-per-instrument` prefix's 2026-08-06 OOM-pair
failure signature that triggered `RB-INFRA-RELAUNCH`'s "same shape twice → stop, fix root cause" clause. Per that clause
and this doc's own operator/main-escalation gate on relaunching R3, **no 3rd relaunch was attempted**. Separately
confirmed the manifest consolidator's lock self-healed correctly (new legitimate cycle acquired the lock at `05:12:56Z`,
not a second stuck-lock problem) — likely to clear Finding 1 item 2 / Finding 2 item 2's "consolidator catches up" gate
within the hour, independent of the R3 relaunch question. **Full evidence + citations recorded at the owning doc**
(`/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s R3 item + Progress Log,
`unified-trading-pm@353ecdac88` + `@503017d9bd`) per the primary-owner rule — not duplicated here in full. Findings 4
and 6's items were NOT independently re-verified this pass (re-checked 4h ago in the slot-14 run; low-value to re-check
twice in one day) — carried forward as-is, still presumed accurate.

## Batch13 decision (reconfirmed)

**Still no `defi_satellite_ao_dispatch_batch13` drafted.** Finding 8 added zero AO-eligible-and-defi-owned items to the
pool (still 1 — Finding 1's HYPERLIQUID scoping query). No change to the prior decision.

**Parked count reconciliation (this run)**: 2 findings (Finding 8 + Finding 9) = 2 entries written to this doc. ✓
Cumulative doc total: 9 findings across 3 runs today.

## Progress Log

- **ag_closeout_auditor 2026-08-10** (tranche=defi, slot 20, DISPATCH_ID=agt-af667b): iterative-drain follow-up run, ~4h
  after slot-14's primary run. Phase 0 re-run (candidate script + linkage-gate re-check, both clean/consistent) +
  targeted re-verification of the prior report's time-gated items (not a full fresh 14-agent Phase-1 pass, since 15 of
  17 candidates were unchanged from 4h ago — re-classifying identical content would have been pure waste). Classified
  the 1 genuinely new candidate directly (Finding 8). Surfaced 1 material live-state update (Finding 9: R3 rebuild VM's
  2nd terminal failure + consolidator self-heal), documented at the owning doc per the primary-owner rule rather than
  duplicated here. Batch13 decision reconfirmed unchanged. 2 findings parked this run, ledger reconciled.
- **2026-08-10 (prose-findings formalization sweep)**: converted 0 prose findings into 0 formal todos (0 already
  resolved). Full re-read of every finding confirmed each genuinely-actionable item already carries a real `- [ ]`
  checkbox at its own source doc, verified via direct grep: Finding 1's HYPERLIQUID `perp_funding` scoping query
  (`defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md`, todos
  present), Finding 3's 3 zero-AO-eligible docs (`defi_aavev3_bare_alias_enumerator_bug_2026_08_08.md`,
  `defi_lst_adapter_factory_family_unused_by_production_path_2026_08_09.md`,
  `onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md`), and Finding 4's 2 AO-mechanism docs
  (`defi_compute_gcp_migration_009_repeat_wedge_parked_2026_08_08.md`,
  `solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md`) all already have their own tracked todos. This
  is a findings ledger correctly pointing at already-tracked work; no `## Todos` section needed.
