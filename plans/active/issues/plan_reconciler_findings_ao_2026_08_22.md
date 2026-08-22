---
doc_type: issue
title: "plan_reconciler tranche sweep — ao, 2026-08-22"
summary: >-
  Interactive `/plan-reconcile ao` pass (slot 2, harsh_pc, operator-invoked — not a timer dispatch). 119 docs in the
  ao tranche (up from 104 on 2026-08-19), 354 open / 559 done todos. Ran Phase -1 (prior findings-doc
  reconciliation), Phase 0 (full mechanical inventory + entry hygiene sweep, 0 hard failures), Phase 2 (evidence
  sweep over all 354 open todos), and the mechanical/targeted half of Phase 1. 1 P1 defect CONFIRMED and FIXED: two
  docs a 2026-08-21 un-orphaning pass intended to make AO-dispatchable were STILL unreachable, because the rationale
  that pass left as a trailing YAML comment on the `assigned_vm:` line is itself what breaks
  `regen_backlog_from_plan.py`'s parser — proven by running the real function, fixed, and re-verified to
  `{'planning'}`. 1 prose-only-remaining-work doc converted to 4 tracked todos (Phase 2.4). 22 sha-citing open todos
  swept, 0 genuine missed flips (3 investigated in depth and refuted). 6 findings routed to the operator below.
  Phase 1's full cross-doc contradiction fan-out was NOT run this pass — see Coverage.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, ao-tranche]
related:
  [
    /plans/active/issues/plan_reconciler_findings_ao_2026_08_19.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/ao_satellite_ao_dispatch_batch4_2026_08_21.md,
  ]
created: "2026-08-22"
last_updated: "2026-08-22"
parent_epic: plan_hygiene_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: review
assigned_vm: NA
execution_scope: local-only
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: "interactive /plan-reconcile ao, slot 2, harsh_pc, 2026-08-22"
context_scope:
  [
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
    unified-trading-pm/agents/plan_reconciler.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
  ]
drift_direction: fix
depends_on: []
---

# plan_reconciler — ao tranche sweep, 2026-08-22

## Coverage — read this before trusting the result

- **Tranche `ao`: 119 docs** (`generate_tranche_doc_inventory.py --tranche ao`), 354 open / 559 done todos. Up from
  104 docs on the 2026-08-19 pass.
- **Entry hygiene sweep** (`run_hygiene_sweep.sh --ci --no-regen`): **0 hard failures**, 1 soft warning
  (Delete/VM-launch todo tagging, candidate signal). Advisory warns: 14 non-canonical todos, 37 estimate-drift, 1
  CLAUDE↔SUB_AGENT topic drift, 1310 uncited-symbol todos.
- **Phase 0 mechanical inventory**: run over all 119 docs. 0 conflict markers, 0 terminal-status-in-active, 0
  `superseded_by`-while-active, 0 locked docs, 0 `assigned_vm` outside `{planning, NA}`.
- **Phase 2 evidence sweep**: all 354 open todos scanned for self-cited `repo@sha` completion evidence; 22 hits, each
  adjudicated (3 in depth against live code). **0 genuine missed flips.**
- **Phase 1 multi-agent contradiction sweep: RAN** (operator-authorised mid-session). 5 read-only hunters
  (general-purpose, sonnet, `SUB_AGENT_MANDATORY_RULES.md` contract at each spawn top), partitioned by `parent_epic`
  and size-balanced: A1/A2/A3 = `orchestrator_master` (66 docs, ~1.71MB, split 22/22/22), B =
  `agent_operating_framework_master` (39 docs, ~645KB), C = `security_and_cross_cutting_master` +
  `observability_master` + `plan_hygiene_master` + `ci_master` (14 docs, ~384KB). **All 5 completed; 119/119 docs read
  in full by exactly one hunter each** (several needed paginated reads to clear the page cap; each confirmed full
  coverage), plus every cited epic hub. Zero hunter writes — read-only throughout.
- **Adversarial verification: every hunter candidate was re-verified by me against the source** (and, where the claim
  was about code, against live code on `origin/live-defi-rollout`) before any edit. This REVERSED the verdict on the
  highest-severity candidate — see Phase 1 results. No finding was applied on hunter assertion alone.

## Phase -1 — prior findings docs reconciled

`plan_reconciler_findings_ao_2026_08_19.md` had 3 genuinely-open todos. **All 3 re-verified against fresh state; all
3 are STILL OPEN.** No stale findings to retire, so the doc correctly stays `status: open`.

1. `[DOCS] P2` — `/codex/06-coding-standards/ui-testing-layers.md` missing the "PlanRegenLoop-in-mock-mode overwrites
   e2e fixtures" pattern. **Re-confirmed still open**: `grep -icE 'planregenloop|plan_regen'` over that file returns
   **0**.
2. `[DOCS] P3` — `/codex/05-infrastructure/per-tab-worktrees.md` missing the `unified-trading-ci` 2026-08-17
   cron-branch-override incident + the `check_cron_branch_override_parity.py` guard. **Re-confirmed still open, and
   this one nearly produced a false flip**: a naive `grep -c` for `cron.branch.override` returns 2 hits (lines 426,
   1381) — but both are pre-existing references to the `cron-branch-overrides.txt` DATA FILE, not to the incident or
   the guard. `git log -S 'check_cron_branch_override_parity'` on that file returns **empty** — the guard is not
   mentioned. Recorded here because the same shortcut will mislead the next run too.
3. `[PM] P3` — `plans/epics/plan_hygiene_master.md`'s `related_plans:` roster incomplete. **Still open and the gap
   has GROWN**: roster carries **6** entries; **43** docs declare `parent_epic: plan_hygiene_master`. The 2026-08-19
   doc described this as "~17 more" missing — it is now ~37. See routed item R1.

## Applied this pass

### 1. [P1, CONFIRMED, FIXED] A 2026-08-21 un-orphaning fix silently did not take — 2 docs still unreachable by AO

`ag-closeout-audit` (cefi tranche, 2026-08-21) correctly diagnosed that two docs carried a stale legacy
`assigned_vm: vm-cross-cutting` and were never reaching the AO backlog, and set them to `assigned_vm: planning`. But
it left its rationale as a trailing YAML comment **on the same line**:

```
assigned_vm: planning # FIXED 2026-08-21 (ag-closeout-audit cefi Phase 3): was stale legacy `vm-cross-cutting` ...
```

`agent-orchestrator/server/regen_backlog_from_plan.py`'s `_parse_frontmatter_assigned_vm` (line 501) matches
`_ASSIGNED_VM_RE = re.compile(r"^assigned_vm\s*:\s*(.+)$")` and returns `m.group(1).strip()` — it does **not**
`.split("#")[0]`, unlike its sibling parsers for `status` / `execution_scope` / `sequential` / `effort` (lines 786,
843, 870, 1125, which all do). So the value read back as the whole comment-laden string, and `_resolve_plan_vms`
(line 799) returned `{'planning # FIXED 2026-08-21 ...'}` — a VM set the live `planning` VM never matches.

**Net effect: the fix intended to un-orphan these docs left them exactly as unreachable as before**, with 3 open
todos between them still absent from the AO backlog.

**Proof — ran the real function, did not infer.** Before: both returned `'planning # FIXED 2026-08-21 ...'`,
`== 'planning'` → `False`. After the fix: both return `'planning'`, and `_resolve_plan_vms` returns `{'planning'}`.

Fixed (comment stripped from the frontmatter line; the rationale was already recorded in full in each doc's own
Progress Log, so nothing was lost, and a new dated Progress Log entry records this correction):

- `plans/active/issues/dp_fetch_009_cefi_liquidations_raw_contract_overwritten_2026_08_20.md:20` (2 open todos)
- `plans/active/issues/dp_fetch_009_cefi_liquidations_batch_aster_2026_08_20.md:25` (1 open todo)

**Cross-tranche note**: both docs are `asset_group: [cefi]`, found via an `ao`-tranche todo. Filed under `ao` per
CLAUDE.md's epic-assignment rule (shared mechanism → owning epic); the mechanism is AO's backlog ingester. The
code-side hardening is already tracked — `ao_satellite_ao_dispatch_batch4_2026_08_21.md` todo `[BACKEND] P3`
("Harden `_parse_frontmatter_assigned_vm` ... to strip inline `# ...` comments") — and this pass independently
confirms that todo is real, unfixed, and has now demonstrably bitten once in production.

### 2. [Phase 2.4, APPLIED] Prose-only remaining work converted to tracked todos

`plans/active/issues/gemma_4_31b_it_persistent_timeout_2026_08_19.md` had a `## Next steps for whoever picks this
up` section holding genuine remaining work as **numbered prose with zero checkboxes** — invisible to
`check_todo_format.sh`, to `regen_backlog_from_plan.py`, and to every audit that counts todos. It also carried a
structural defect (two consecutive items both numbered `2.`). Converted to **4 canonical `- [ ]` todos** (1
`[OPERATOR] P2`, 1 `[INFRA] P1`, 1 `[INFRA] P2`, 1 `[OPERATOR] P3`), each with an explicit done-when; the former
step 3 was a standing constraint rather than a task, so it is retained as a `>` guard note rather than fabricated
into a todo. The already-done item 0 is preserved verbatim, and its buried "**Real remaining gap, not code**"
(setting `health_status: "degraded"` on the live VM's `accounts.json`, without which the shipped banner never
renders in production) is now the tracked `[OPERATOR] P2` rather than a sentence inside a done item.

## Refuted (investigated, dropped — no action)

Of 22 open todos citing a `repo@sha`, 19 cite the sha as motivating context rather than completion evidence. Three
looked like genuine flip candidates and were each run down against live code:

1. **`ao_ci_aws_to_ionos_migration_2026_08_18.md:345`** (author the AWS DR-standby failback runbook) — the runbook
   **does** exist at `/codex/15-runbooks/aws-dr-standby-failback-ao-ci.md`, created by the exact sha the todo cites
   (`unified-trading-pm@6ff00d4ca7`). **Not a flip**, for two independent reasons: the doc is `status: draft` (the
   skill excludes draft plans from the flip sweep), and the todo's own stated done-when is *"a real timed dry-run ...
   completes in under 1 hour, elapsed time and any friction points logged in the Progress Log"* — the runbook's own
   frontmatter says `last_executed: NEVER`. Writing the file was half the todo. This is the half-done trap the
   HARD-evidence bar exists to catch.
2. **`ao_satellite_ao_dispatch_batch4_2026_08_21.md:64`** (harden `_parse_frontmatter_assigned_vm`) — read the live
   function: still no `.split("#")`. Genuinely open. (And now demonstrably load-bearing — see Applied #1.)
3. **`slot2_wedged_pre_boot_watchdog_resume_loop_no_respawn_2026_08_04.md:201`** (reconcile the `fleet_slot_status.py`
   / `layout.tsx` phase-split) — `fleet_slot_status.py` **does** now call the shared `ss.compute_slot_phase`, and
   `layout.tsx` reads the server-computed `s.phase`. But the todo also requires *"state which side wins and why in
   the commit — do not silently pick one"*, and the docstring's claim of shared definition is the very thing the todo
   says was aspirational. Not enough HARD evidence to flip a live-dispatch-critical-path KPI-semantics todo;
   `/na-eligibility-audit` reached the same KEEP-NA conclusion on 2026-08-21. Left open.

## Routed to operator (6)

- [ ] [PM] P1. **R1 — epic `related_plans:` roster drift. DEFERRED BY OPERATOR RULING 2026-08-22: "leave the roster
      changes for now, we will do it when we run the script so that its done properly."** No roster was touched this
      pass. Measurements recorded here so they are ready when the script is run.

      **CORRECTION to this pass's own earlier number**: I first reported "6 roster entries vs 43 children, ~37
      missing" for `plans/epics/plan_hygiene_master.md`. That compared two different populations and overstated it.
      The roster is a DERIVED projection whose definition is owned by its generator,
      `scripts/plans/populate_epic_bodies_2026_05_21.py`: it scans **`plans/active/*.md` only**, keeping only
      **`status: active`** docs. My 43 was every doc in `plans/active/` **plus** `plans/active/issues/` at any status —
      measured: **36 `plans/active/issues/` docs at `status: open`, 8 `plans/active/` docs at `status: active`**.
      Against the roster's own definition the real drift for that epic is **5 missing + 2 stale**, not 37. Corpus-wide
      the drift is real: the generator's `--dry-run` reports it **would rewrite the frontmatter of 22 of 31 epics**.

      **The blocker to resolve before the script is run** (this is what "properly" has to cover):
      `update_related_plans_frontmatter()` replaces the WHOLE `related_plans:` value, and the generator never scans
      `plans/active/issues/`. But **177 current roster entries across the epic corpus point into `../active/issues/`**
      (54 block-style + 123 flow-style, measured) — all hand-added over months. Running `--apply` as it stands would
      **delete all 177**. Decide first whether issue docs belong in epic rosters; if yes, teach the generator to scan
      `plans/active/issues/*.md` (treating `status: open` as the issue-doc equivalent of `active`) before running it.

      **Three further instances confirmed by this pass's hunters, all the same mechanism, all left untouched**:
      (a) `plans/epics/orchestrator_master.md:70` frontmatter records a roster correction applied 2026-08-19, but the
      body's auto-populated "Assigned active plans" section — the priority queue workers actually read — still says
      "26 active plans" and omits exactly the plans that note says were added (`batch23_2026_08_17` + its finalize,
      `slot0_self_cleaning_daemon_2026_08_18`), plus `batch24`/its finalize; 29 frontmatter entries − 3 = 26, an exact
      match confirming the body was never regenerated. (b) Same file `:458-460`: the last auto-generated entry renders
      `**title**: >-` — a bare YAML block-scalar indicator with the text missing — and the file ends there.
      (c) `plans/epics/security_and_cross_cutting_master.md`: 7 AO-fleet-mechanics issue docs declare it as
      `parent_epic` while its written Scope covers only shard-granularity/data-status/deployment-build, and none
      appear in its roster (hunter self-rated low confidence — could not determine whether the 2026-08-18 taxonomy
      restructure intended to reassign them).

- [ ] [PM] P2. **R2 — 2 HARD line-cap violations in the ao tranche** (splitting a plan is a planning decision, so this
      is operator-gated by the skill's own rule): `plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md`
      (1015 > 1000) and `plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md` (1010 > 1000). Both
      are barely over, so a split is not obviously warranted. 11 further docs are over the 500-line soft cap (report
      note only). **[WORKER REC]**: split neither yet — both are ~1.5% over and actively worked; revisit if either
      passes ~1200.
- [ ] [PM] P2. **R3 — 4 fully-done docs are archival candidates but each is gated on a paired finalize/operator-items
      twin that still has open todos**, so none were archived this pass:
      `ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md` (3 done / 0 open),
      `ao_satellite_ao_dispatch_batch21_2026_08_16.md` (7/0), `ao_satellite_ao_dispatch_batch8_2026_08_08.md` (4/0),
      `deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md` (18/0). **[WORKER REC]**: leave
      as-is — this is the finalize-twin gate working correctly, not a hygiene gap. Confirm the twins are being worked;
      if a twin is itself stalled, that is the finding, not the parent's archival.
- [ ] [DOCS] P2. **R4 — the 2 codex-prose todos carried over from 2026-08-19 remain open and remain operator-gated**
      (codex edits are outside trust mode's carve-out, and both need NEW prose authored rather than a single
      substitution): the missing PlanRegenLoop/e2e-fixture pattern in `/codex/06-coding-standards/ui-testing-layers.md`
      (cite `agent-orchestrator@ef73a44`), and the missing cron-branch-override cross-reference in
      `/codex/05-infrastructure/per-tab-worktrees.md` (cite `unified-trading-pm@434e3adebc`). **[WORKER REC]**:
      authorize both as a single small docs task — the evidence and the target sections are already identified.
- [ ] [PM] P3. **R5 — 3 zero-checkbox register docs need an explicit lifecycle decision.** Of 5 zero-checkbox docs
      found in this tranche, 2 were resolved (one converted — see Applied #2; one,
      `ao_satellite_ao_dispatch_batch14_2026_08_09.md`, correctly has no checkboxes because its sole todo was
      deliberately retired in place under `task_template.md` §3's CANCELLED/SUPERSEDED disposition marker). The other 3
      are standing-reference registers with no open surface:
      `ag_closeout_audit_ao_parked_2026_08_16.md` (38 parked findings), `ag_closeout_audit_ao_parked_2026_08_21.md`,
      `operator_ruling_record_plan_reconcile_ao_2026_08_18.md` (7 rulings). **[WORKER REC]**: mark all 3
      `archive_exempt: true` with a one-line justification — they are exactly the standing-reference-hub case, and
      leaving them with no checkboxes and no exemption means every future sweep re-adjudicates them. Not applied
      unilaterally because it is a class decision about where parked-findings registers live.
- [ ] [DOCS] P3. **R6 — `/codex/15-runbooks/aws-dr-standby-failback-ao-ci.md` has an EMPTY `verifier:` field.**
      CLAUDE.md's runbook rule is explicit ("declare `owner`/`cadence`/`verifier`/`last_executed`; missing =
      review-blocking"), and `check_runbook_fields.py` passes it, so present-but-blank is currently accepted by the
      machine check. `owner`, `cadence` and `last_executed: NEVER` are all populated. **[WORKER REC]**: fill
      `verifier:` when the required dry-run (tracked in the migration plan) is scheduled; separately consider whether
      `check_runbook_fields.py` should treat blank as missing.

- [ ] [BACKEND] P2. **R7 — `last_updated` staleness is a TOOLING gap, not per-doc sloppiness; hand-patching dates is
      churn that re-rots.** The hunters measured a frontmatter `last_updated` older than the doc's own newest dated
      Progress Log entry in **13 of 22 (A2), 12 of 22 (A1), 13 of 22 (A3)** docs — roughly half the tranche. Decisive
      evidence it is mechanical, not stylistic: at least **four** docs carry an inline comment recording they were
      *already corrected once* for this exact staleness and drifted again within days
      (`ao_creds_env_poller_disabled_2026_08_18`, `e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06`,
      `fleet_wide_deepseek_crash_loop_undetected_2026_08_11`, `review_agent_evidence_gated_write_capability_2026_08_09`).
      Cause: `context-scout` and `na-eligibility-audit` append Progress Log entries without bumping `last_updated`.
      Not cosmetic — Phase 1 item 5 is a case where an audit pass read an unbumped `last_updated` as a "no content
      changed" skip-signal and published a wrong verdict off it. **[WORKER REC]**: make the two appending skills bump
      `last_updated` when they write a Progress Log entry (or have `run_hygiene_sweep.sh` derive/assert it), and do
      NOT bulk-patch the ~25 current dates by hand — per CLAUDE.md's "delete the number that rotted rather than
      updating it", a hand-patched date re-rots on the next append. One exception worth fixing regardless:
      `dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md` took an `assigned_vm: NA → planning` flip (a real
      dispatch-eligibility change) on 2026-08-21 without a bump, so the timing of a material change is now
      unrecoverable from its frontmatter.

## Host hygiene (not a corpus finding, reported because it will bite someone)

- **Slot 5's `unified-trading-pm` checkout has an unresolved merge conflict** —
  `UU plans/active/issues/manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md`. A slot left mid-conflict
  blocks that slot and, per `stale_slot_conflict_markers_block_escalation_dispatch_2026_08_21.md` (an existing
  ao-tranche issue doc), is a known cause of blocked escalation dispatch. Not touched — resolving another slot's
  conflict is exactly the "never edit a dirty file you don't own" rule. Flagged for the owner.

## Phase 1 — contradiction sweep results (applied)

All six below were re-verified by me against the source before any edit. Roster findings excluded per R1's deferral.

1. **[P0 → re-adjudicated, hunter's verdict REVERSED]** `codex_luna_flex_bridge_2026_08_14.md` carries an `[x]`
   `[REVIEW] P0` "smoke-test gate before any real fleet traffic — DONE 2026-08-19" directly below a same-day finding
   documenting a 100%-reproducible (6/6) hard 400 failure that explicitly speculates the gate "didn't catch it". The
   hunter ruled the *gate* was the wrong side. **It is not.** The root cause — `codex_bridge_server.py`'s
   `AnthropicMessage.role` lacking a `"system"` variant — was **fixed in `agent-orchestrator@7a1be88b` (2026-08-19)**;
   I read the live file (`role: Literal["user", "assistant", "system"]`) and confirmed the sha is an ancestor of
   `origin/live-defi-rollout`. The STALE side is therefore the hard-failure prose ("Until this is fixed, Codex/Luna is
   NOT usable for any real dispatch"), not the gate. Annotated the prose as root-cause-resolved, kept the `[ ]` todo
   open (its Done-when is a marker-*influence* proof the schema fix unblocks but does not establish), and recorded
   that the gate's `[x]` is not contradicted. **This is why Phase 3 exists** — applying the hunter's verdict would
   have reopened a correctly-closed P0 gate and left the genuinely stale text standing.
2. **[P1, CONFIRMED, FIXED]** `ao_tmux_loss_rate_canary_likely_overtuned_2026_08_18.md`'s 2026-08-21 note says its
   gating measurement is "not yet landed". It landed the day before: `ao_satellite_ao_dispatch_batch25_2026_08_19.md`
   item 3 is `[x]` "DONE — see Progress Log 2026-08-20", with the full result (194 threshold-crossing episodes in 7
   days; 8 of 1,048 crossing rows, 0.8%, benign). Appended a dated correction — that doc's remaining
   raise-the-threshold todo is **actionable, not blocked**.
3. **[P1, CONFIRMED FALSE POSITIVE, FIXED IN 3 PLACES]** `context_scout_stale_citations_and_doc_drift_2026_08_20.md`
   called `main.md § "Account-failover triggers"` a dead citation, from `grep -rl ... agent-orchestrator` returning
   zero. The citation never pointed there: the heading is real at **`unified-trading-pm/agents/main.md:689`**, and the
   source issue doc qualifies it fully. Worse, the false finding was already propagated into an **open, undispatched**
   `[DOC] P3` todo in `ao_satellite_ao_dispatch_batch2_2026_08_21.md` telling a worker to repoint the citation at
   `server.py` — which reads the trigger table but is not the table. Corrected the originating finding, closed the
   batch2 todo with evidence and an explicit note that its instruction was deliberately not followed, and
   re-qualified both occurrences in batch25.
4. **[P2, CONFIRMED, FIXED]** `ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md:310` claims the
   `PlanRegenLoop`-in-mock-mode pattern "was already documented separately in that same codex file". A full-file grep
   of `/codex/06-coding-standards/ui-testing-layers.md` for `PlanRegenLoop`/`plan_regen` returns 0 hits — verified
   2026-08-19 and again 2026-08-22. Annotated the false half; the real work stays tracked as R4.
5. **[P1, CONFIRMED, FIXED]** `codex_mcp_tool_use_bridge_2026_08_18.md`'s 2026-08-21 audit entry says "Both open todos
   remain". The `[REVIEW] P1` unpause todo closed the same day with live `AccountUsageRow` evidence
   (`status=healthy`, 8 real dispatches across 5 slots); the doc has **1** open todo, not 2. The stale verdict came
   from trusting an unbumped `last_updated` as a "nothing changed" skip-signal — see R7.
6. **[P1, CONFIRMED, FIXED]** `ao_satellite_ao_dispatch_batch23_2026_08_17.md`'s body banner still read
   "**`status: draft`** — the safety rail. Never auto-ingested/dispatched until an operator flips this to `active`"
   while its frontmatter had been `status: active` since 2026-08-18 and workers executed todos 1-4 on 2026-08-20. A
   reader trusting the banner would conclude the plan was still gated. Rewritten to match, following sibling
   `batch22`'s correctly-updated banner as the template.

### Refuted / not acted on

- Item 1 above, re-adjudicated — the hunter's nominated authoritative side was wrong on the code facts.
- `backlog_500_malformed_depends_on_comment_2026_08_19.md`'s `assigned_vm: planning` + `execution_scope: NA` pairing:
  cosmetic — `assigned_vm` is the fail-closed dispatch matcher, so dispatch behaviour is unaffected.
- Several apparent numeric contradictions across the wedge/stash docs: each self-explained by the docs' own dated
  Progress Log entries (counts explicitly superseded). Correctly not findings.
- All roster findings: real, but deferred per R1.

## Phase 5.9 — no-miss ledger

- `routed_to_operator` = **7** (R1-R7); `parked_in_issue_doc` = **7**. **Balanced.**
- `agent_skips` = **0** (5 hunters spawned, 5 completed, none skipped or died); `enumerated` = **0**. **Balanced.**
- Hunter candidates raised = 18; CONFIRMED + applied = 6; re-adjudicated against the hunter = 1; refuted = 4;
  deferred per R1 ruling = 7 (all roster-class).
- Applied fix classes = 5 (assigned_vm parse defect ×2 docs; parent_epic parse defect ×1 doc; prose→todo conversion
  ×1 doc / 4 todos; dangling-ref repointing ×3; Phase 1 contradiction fixes ×8 edits across 8 docs).
- Candidates investigated and refuted = 3 (enumerated above, with the evidence that killed each).
- Zero-checkbox docs: found **5**, converted **1**, explained-as-correct **1**, routed **3** (R5).

## Progress Log

- **2026-08-22, interactive `/plan-reconcile ao` (slot 2, harsh_pc)**: Phases -1, 0, 2 and the mechanical/targeted
  half of Phase 1 complete. Phase 1's hunter fan-out deliberately not run (see Coverage) — a follow-up pass with it
  enabled is required before this tranche is fully reconciled.
