---
doc_type: plan
title: CeFi satellite AO batch 9 — iterative-drain extraction over the batch8 residual
summary: >-
  Ninth AO-dispatch batch for cefi, produced by the `/ag-closeout-audit` skill run 2026-08-07 (scheduled autonomous
  dispatch, tranche=cefi, slot 4, dispatch agt-ed7b44). Phase 0 re-derived the covering-plan set via
  `generate_ag_closeout_audit_candidates.py --tranche cefi` (79 cefi-tagged AG-primary members, 16 real active covering
  docs — the consolidated closeout, the 4-surface migration log, the deribit-bundle verification pair, batches 4/6/7/8 +
  finalize pairs (all 4 now `status: active`, operator-approved 2026-08-06), and the track2/track7 pairs; batch4 is 4/7
  done, batch6 2/6, batch7 2/3, batch8 2/3 — no covering batch has fully shipped, so no coverage expiry) — 8 "never
  cited" candidates via the citation heuristic, of which 6 were already classified by the 2026-08-06 run (all
  non-AO-eligible verdicts re-verified unchanged this run) and 2 are NEW docs filed 2026-08-06. UNIONED with the
  cefi-tagged subset of `check_ag_closeout_linkage.py`'s stricter graph/mention check (77 orphans corpus-wide vs 69
  baseline — the filed regression persists, only 6 cefi-tagged; of those, 3 overlap the citation heuristic's set, 3 are
  additional). 5 docs deep-audited this run via a `Workflow` (one agent per doc, all 16 covering docs + yesterday's
  parked-findings doc passed as context per agent). Verdicts: 3 orphaned_never_touched (cefi_derivative_ticker `[DATA]
  P3` case-sensitivity audit; features_universe_filter done-when half-2 real-VM-launch observation; cefi_fwd_vm — mixed:
  its `[SCRIPT] P2` launcher-race item is AO-eligible, items 1/3 operator/time-gated), 1 exclude_cross_cutting
  (mtds_pipeline_check_process_killed — genuinely multi-AG, needs root/VM-level access; defi's 2026-08-06 parked doc
  independently lands the same verdict), 1 archivable_after_planned_work (mtds_cefi_docker_image — fully claimed by
  batch6's open `[OPS] P2` todo). Phase 3 conflict-checked all 3 AO-eligible candidates against the full covering set +
  corpus-wide greps (zero overlap; one adjacent-but-distinct prior fix — the perp_funding singleton-filter collision
  resolved at deployment-service@fa794a1 — noted in todo 2's own text to prevent confusion, NOT a real conflict). 3
  todos below, zero genuine conflicts, zero BLOCKED-OPERATOR-DECISION parked this run (the 2 carried conflict-gated
  items are re-verified still open — 5th consecutive re-check — and flagged explicitly for the operator per
  batch8-finalize's own instruction, not silently re-deferred).
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-9, satellite-docs, iterative-drain]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch8_2026_08_06.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch8_2026_08_06_finalize.md,
    /plans/active/issues/cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md,
    /plans/active/issues/cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md,
    /plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md,
    /plans/archive/2026_08/ag_closeout_audit_cefi_parked_2026_08_06.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-07"
last_updated: "2026-08-07"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-08-07 (scheduled autonomous dispatch, agent-orchestrator slot 4, dispatch
  agt-ed7b44, tranche=cefi). Phase 0 used `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py --tranche cefi`
  (79 members, 16 covering, 8 never-cited) UNIONED with the cefi subset of `check_ag_closeout_linkage.py` (77 orphans
  corpus-wide, 6 cefi-tagged). Phase 1 ran a `Workflow` (5 parallel agents over the 5-doc deep-audit set — the 2 new
  never-cited docs + the 3 additional linkage-flagged docs), each reading its doc in full (incl. dated sections) and
  grepping all 16 covering docs + the 2026-08-06 parked-findings doc for citations. Phase 3 conflict-checked every
  AO-eligible candidate against the full covering set AND a corpus-wide grep for each candidate's target files/topics
  before drafting.
context_scope:
  [
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch8_2026_08_06.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
---

# CeFi satellite AO batch 9 — iterative-drain extraction

> **Status: ACTIVE — operator-approved 2026-08-07** (was DRAFT; missed by an earlier casing-sensitive grep fixing the
> frontmatter and PLAN_FORMAT.md reference but not this differently-cased banner — corrected here). The paired finalize
> plan ships `status: active` from the start — `gate_on_depends: true` machine-holds it until this batch's todos are
> done, no double gate.
>
> **Cross-todo file-collision check: PASS.** The 3 todos touch, respectively: (1) `market-tick-data-service` — a
> read-only confirm/refute audit with a conditional scoped fix in `HyperliquidS3Downloader.fetch_l2_book`'s S3-key path;
> (2) `deployment-service/scripts/vm/launch-cefi-forward-poll.sh` (+ its lock helper in
> `deployment-service/scripts/vm/lib/launcher_common.sh` if a shared lock primitive is the chosen fix) — a code fix; (3)
> `deployment-service` launcher _execution_ + a PM docs edit — runs an existing launcher (explicitly NOT
> `launch-cefi-forward-poll.sh`, which todo 2 is concurrently editing) against a throwaway-named stale tarball and
> records the observation in its source doc. No file is edited by more than one todo.
>
> **Every claim below was re-verified against live corpus/code state on 2026-08-07** by the Phase-1 agents (each read
> its target doc in full, including dated sections, and confirmed zero covering-doc citations via direct greps).

## Todos

- [ ] [DATA] P3. **Chase the flagged-but-unconfirmed `fetch_l2_book` / `book_snapshot_5` case-sensitivity hypothesis for
      HYPERLIQUID.** The source doc's Open Questions section states the uppercased K\*-symbol coin feeds
      `HyperliquidS3Downloader.fetch_l2_book`'s S3 object key (`l2Book/KPEPE.lz4` vs `kPEPE.lz4`), which would 404 on
      every hour for the 6 k-prefixed symbols as a SILENT absence — flagged as a plausible follow-up, never chased,
      never confirmed against the live manifest. Verify or refute: (a) read the live manifest / GCS object listing for
      the k-prefixed HYPERLIQUID symbols (KPEPE etc.) across the book_snapshot_5 write path and compare against the
      `fetch_l2_book` key construction in `market-tick-data-service`; (b) if the hypothesis is CONFIRMED, apply the
      scoped fix (preserve case / case-insensitive key fallback in the S3-key path) with regression tests + QG green;
      (c) record the verdict (confirm/refute + evidence) in the source doc's Follow-ups checkbox, flipping it `[x]` only
      with cited evidence. The untraced instruments-service catalogue uppercasing source (Open Questions) is out-of-repo
      and explicitly non-blocking — do NOT expand scope to it. Source:
      `issues/cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md` (Follow-ups, line ~617). **Done
      when**: the source doc's `[DATA] P3` Follow-ups checkbox is flipped `[x]` citing a confirm/refute verdict backed
      by live manifest + archive-key evidence (or, if confirmed and a fix is out of the audit's scope, a new issue filed
      with the evidence).
- [x] ✅ [SCRIPT] P2. **Fix the `launch-cefi-forward-poll.sh` singleton-lock TOCTOU double-insert race — ALREADY
      SHIPPED, found stale on pickup 2026-08-09.** This todo's own fix was landed by `deployment-service@4c28ca640f`
      ("fix(vm): close cefi-fwd duplicate-launch TOCTOU race with an atomic GCS singleton lock", 2026-08-06 14:57 BST) —
      the SAME DAY the source issue doc was filed, **a full day before this batch9 plan itself was drafted
      (2026-08-07)**. Neither the source doc's checkbox nor 4 subsequent na-eligibility-audit passes (2026-08-07/08/09)
      caught that the code-level fix already existed; they only checked "is an active plan claiming this todo," not the
      live code state. Verified live on pickup: `deployment-service/scripts/vm/launch-cefi-forward-poll.sh` calls
      `lc_acquire_singleton_lock "cefi-fwd-launch" "$PROJECT" 300 "$LAUNCHER_FORCE"` before the RUNNING-VM check
      (`scripts/vm/lib/launcher_common.sh:281`) — an atomic GCS create-if-absent conditional PUT
      (`--if-generation-match=0`) with TTL-based stale-lock reclaim, exactly the fix shape this todo specified. 6
      regression tests exist in `tests/unit/test_vm_launcher_scripts.py::TestAcquireSingletonLock` (well over the "2+"
      bar): acquire-when-absent, refuse-on-fresh-lock, reclaim-past-TTL, force-bypass, independent-lock-keys, and a
      12-process concurrent-race test (`test_concurrent_launches_exactly_one_wins`) asserting exactly 1 of 12
      simultaneous racers acquires the lock and the other 11 are refused — the "otherwise demonstrated closed" done-when
      clause (a real live double-launch would cost real GCP spend + 403-storm risk for no new information). Re-ran all
      11 `TestAcquireSingletonLock`/`Singleton`-selected tests fresh on 2026-08-09 pickup: 11 passed. The 2026-08-09
      Tardis-cap hardening pass (`deployment-service@58af2ab1`, see the coordination note this todo originally carried)
      only renamed `FORCE`→`LAUNCHER_FORCE` and added `tardis_guard_reserve_slot` — it did not touch
      `lc_acquire_singleton_lock` itself, which predates it by 3 days. No new code shipped by this todo; it closes the
      paperwork gap. Source: `issues/cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md` (todo 2,
      line ~182 — flipped in the same commit as this checkbox; the doc's items 1 and 3 stay OPEN, untouched).
- [ ] [DATA] P3. **Complete `features_universe_filter`'s done-when half-2: real-VM-launch observation of the
      `LC_TARBALL_FRESHNESS` auto-republish.** The source doc's `[SCRIPT] P2` todo (flipped `[x]` 2026-08-06,
      `deployment-service@c1e0481`) has a two-half done-when; half-2 — "a real VM launch against an intentionally-stale
      tarball is observed auto-republishing before the workload starts" — was explicitly NOT performed. Execute the
      observation SAFELY: (a) upload an intentionally-stale tarball under a THROWAWAY name in the deployment-scripts
      bucket (e.g. `code/<service>-code-closeout-obs.tar.gz` — NEVER overwrite the live `<service>-code.tar.gz`; the
      2026-08-06 "launched onto stale code twice" incident shows a shared-bucket overwrite would poison concurrent
      sibling launches); (b) launch a short-lived VM via an existing launcher that is NOT `launch-cefi-forward-poll.sh`
      (todo 2 is concurrently editing that file) and NOT one a sibling may concurrently use, pinned to the throwaway
      tarball name; (c) observe auto-republish before workload start + verify the workload runs the FRESH code (per the
      source doc's done-when); (d) lifecycle per the vm-launcher runbook (STARTED → ≥1 progress signal → STOPPED, verify
      T+10 min), no GCS deletes of shared objects (the throwaway tarball may be left for natural overwrite or removed
      via `gcs_delete_object` with a fresh same-run `gcs_bucket_soft_delete_retention_seconds()` ≥ 604800s reversibility
      check). Caveat: the sibling bug `issues/lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md`
      (auto mode returning success on a silent dirty-checkout skip) can confound the observation — if a silent skip is
      suspected, record it and note the confound rather than forcing the result. Source:
      `issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md` (`[SCRIPT] P2` todo,
      done-when half-2). **Done when**: the observation is recorded in the source doc's `[SCRIPT] P2` DONE note (half-2
      completed) with the observed auto-republish evidence + VM lifecycle (STARTED/STOPPED) + any confound noted.

## Cross-tranche notes (informational — out of cefi scope, not drafted here)

- **`/plans/archive/2026_08/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`** — classified
  this run: `exclude_cross_cutting`. Genuinely multi-AG (asset_group lists all 5 AGs, parent_epic
  `infrastructure_master`); all remaining work needs root/VM-level host access ("no new privileges" blocked
  dmesg/journalctl; systemd/loginctl policies need root). The defi tranche's own 2026-08-06 parked-findings doc
  independently lands the same verdict and recommends a future cross-cutting round/operator re-scope a bounded VM-backed
  repro todo (strace/py-spy/setsid) — that recommendation belongs to cross-cutting/ao, not this batch. Its zero-checkbox
  prose-only shape was registered in the monthly zero-checkbox sweep. Not cefi-owned; no cefi write.

## Deferred — BLOCKED-OPERATOR-DECISION (conflict/operator-gated, carried — 5th consecutive re-check)

Both items below are the same two carried from batch4→batch6→batch7→batch8. Re-verified live this run (2026-08-07,
direct greps): **both still open, unchanged — FIFTH consecutive re-check to find them so.** Per batch8-finalize's own
todo-2 instruction ("if BOTH are still unresolved a fourth time when batch9 is next drafted, flag explicitly for the
operator as a standing item rather than silently re-deferring"), this batch FLAGS both for the operator explicitly:

- **`issues/fail_hard_canonical_enforcement_design_2026_07_20.md`'s `[DESIGN] P1`** "Close the three §5 gaps
  (derivative-bundle column gate; live-lane dual-resolver reconciliation; read…)" (line 156) — still `- [ ]` open. Its
  transitive gate holds: Schema v10 `instrument_id_form` backfill Stage 2 (a future batch10 candidate) stays blocked
  until this design item + Stage 1 (write-enforce) ship. **Needs the operator to run the §5 design session.**
- **`issues/estate_orphan_assessment_2026_07_21.md` todo 6** — cross-tranche boundedness disagreement (cefi+sports
  KEEP-NA vs defi RECLASSIFY); the "Operator/next-toucher: rule on todo 6's boundedness, then flip deliberately" note
  (line ~558) is still present, unresolved. **Needs the operator to rule on todo 6's boundedness.**

## Deferred — operator-gated

- **`issues/cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md` item 1 (`[OPERATOR] P2`)** —
  confirm/trigger a fresh `deployment-api` build+deploy so the live `uts-prod-dp-exit-code-monitor` Cloud Run job picks
  up the shipped `is_spot` veto fix (`deployment-service@5bd0017b96c9` / `unified-trading-library@59acbe2fa591`);
  done-when is machine-checkable (deployment-api image `UPDATE_TIME` after the fix's merge). Not drafted — prod-deploy
  confirmation is operator action. (Item 2 extracted to this batch's todo 2; item 3 below.)
- **`issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` items 1-3 (of 4)** — carried from batch4's
  Deferred: prod-GCS lane re-partitions (EXTENDED-STARKNET / LIGHTER-ZKSYNC batch_tardis → real pipeline_mode) requiring
  de-dup MERGE semantics against a documented "live split-brain" — prod-bucket mutations stay operator/human-gated
  (delete-safety protocol §3a) until a fresh reversibility check + live-state re-verification is run under operator
  supervision. Re-checked: still no ruling, still not drafted.
- **`issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md` item 2** — gated on item 1's
  second sub-condition (test provenance on the deployed deployment-api build, not just the image timestamp — the image
  timestamp condition cleared 2026-08-02). Not drafted; re-check once the named test's presence on the deployed build is
  confirmed.

## Deferred — time-gated

- **`issues/cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md` item 3 (`[SCRIPT] P3`)** — capture
  the shutdown-script's own log line on a freshly-stopped VM, contingent on future runtime/serial-console access; not
  blocking (the `is_spot` veto already closes the observable symptom).
- **`issues/mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02.md`** — sole remaining item
  is a standing observability tripwire that fires only IF a future connector change happens; not actionable now (carried
  verdict from 2026-08-06, re-verified unchanged).

## Reconciliation (this run — 2026-08-07)

- **6 carried never-cited docs re-verified unchanged** (all classified 2026-08-06 as non-AO-eligible; verdicts hold):
  `aster_and_cefi_rolling_adv_feature_2026_07_21.md` (design-gated Phase 3),
  `issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md` (design choice range-loop vs cache),
  `issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md` (2 design decisions),
  `issues/mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02.md` (tripwire, see above),
  `issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md` (3 `[HUMAN]` credential actions),
  `l2_book_microstructure_capture_2026_07_13.md` (2 `BLOCKED-DATA-CORRECTNESS` items). No new work landed on any of them
  since their classification (only hygiene/na-audit/context-scout touches, per git log).
- **Parked-findings doc housekeeping**: `/plans/archive/2026_08/ag_closeout_audit_cefi_parked_2026_08_06.md`'s open todo
  2 ("add a `related:`/digest mention for
  `multi_timeframe_phantom_captured_manifest_rows_on_universal_write_failure_2026_08_03.md`") is now **MOOT** — that doc
  was archived 2026-08-06 in the 76-doc resolved-issues archive sweep (work resolved), so the linkage mention is void;
  todo flipped with a note in the same commit as this batch.
- **Linkage-gate regression persists** (`check_ag_closeout_linkage.py`: 77 orphans vs 69 baseline — the filed issue
  `ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md` tracks the corpus-wide remediation; only 6 of the 77
  are cefi-tagged). This run's digest additions (see "Linkage housekeeping" below) clear the cefi-tagged share.

## Linkage housekeeping (informational — not AO-eligible batch content)

One-line digest additions made this run to `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md` for the 6
cefi-tagged linkage-orphans so each has a graph/mention path to the closeout family (the skill's own sanctioned remedy
for a linkage gap; same pattern as batch8's "Self-dispatched, linkage-fix-only" section):
`issues/cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md`,
`issues/cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md`,
`issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`,
`issues/mtds_cefi_docker_image_stale_5mo_2026_07_30.md`,
`issues/mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02.md`,
`issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md`.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — §3 conflict-check protocol this
  batch's Phase 3 ran (shared with /na-eligibility-audit).
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the
  bounded/checkable test applied to each candidate.
- `plans/PLAN_FORMAT.md` — `status: draft` semantics (this batch was operator-approved 2026-08-07, now `active`).
- `/codex/05-infrastructure/vm-launcher-runbook.md` — VM lifecycle (STARTED/progress/STOPPED) + the SPOT default rule
  todo 3 must respect for its observation VM.

## Progress Log

- **Operator ruling 2026-08-07**: APPROVED — flipped `status: draft` → `active`. Pre-flip investigation (read-only,
  separate from this edit) confirmed this batch's own explicit Phase 3 conflict-check + cross-todo file-collision
  statement, no rename/archival ops among its todos (the class of the 2026-07-25 mass-flip safety incident), content
  verified safe to dispatch.
