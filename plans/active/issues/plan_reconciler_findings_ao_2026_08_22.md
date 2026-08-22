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
- **NOT RUN THIS PASS — Phase 1's multi-agent cross-doc contradiction fan-out.** The skill's Phase 1 calls for up to
  10 parallel read-only hunters reading every non-grace doc in full (the 2026-08-19 pass used 6 hunters over ~1.16MB);
  this session operated under a standing instruction not to spawn sub-agents, so cross-doc contradiction hunting was
  limited to mechanical flags plus targeted verification of specific claims. **What that means concretely**: the
  contradiction classes this pass CAN'T have found are plan↔plan and plan↔epic disagreements that require reading two
  full docs side by side. The classes it DID cover — mechanical flags, evidence-backed flips, prior-findings
  reconciliation, and every claim reachable by targeted grep-then-read — are complete. A follow-up run with the
  hunter fan-out enabled is needed before this tranche can be called fully reconciled.

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

- [ ] [PM] P1. **R1 — `plans/epics/plan_hygiene_master.md` `related_plans:` roster is 6 entries against 43 real
      children** (measured this pass: `rg -l '^parent_epic: plan_hygiene_master$'` over `plans/active/` +
      `plans/active/issues/` → 43). The 2026-08-19 pass filed this as "~17 missing"; it is now ~37, i.e. the roster is
      drifting faster than it is being patched, which makes hand-patching the wrong fix. **[WORKER REC]**: do not
      hand-edit — `plans/epics/orchestrator_master.md:345` cites `scripts/plans/populate_epic_bodies_2026_05_21.py`
      for exactly this roster-population job, and the script is present and executable. Decide whether to (A) re-run
      it for every epic as the standing mechanical refresh, (B) re-run it for `plan_hygiene_master` only, or (C) wire
      it into `run_hygiene_sweep.sh` so rosters can't drift again. Operator-gated because a fleet-wide re-run mutates
      every epic doc, which is beyond a single tranche's remit.
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

## Host hygiene (not a corpus finding, reported because it will bite someone)

- **Slot 5's `unified-trading-pm` checkout has an unresolved merge conflict** —
  `UU plans/active/issues/manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md`. A slot left mid-conflict
  blocks that slot and, per `stale_slot_conflict_markers_block_escalation_dispatch_2026_08_21.md` (an existing
  ao-tranche issue doc), is a known cause of blocked escalation dispatch. Not touched — resolving another slot's
  conflict is exactly the "never edit a dirty file you don't own" rule. Flagged for the owner.

## Phase 5.9 — no-miss ledger

- `routed_to_operator` = **6** (R1-R6); `parked_in_issue_doc` = **6**. **Balanced.**
- `agent_skips` = **0** (no sub-agents spawned this pass — see Coverage); `enumerated` = **0**. **Balanced.**
- Applied fix classes = 2 (assigned_vm parse defect ×2 docs; prose→todo conversion ×1 doc / 4 todos).
- Candidates investigated and refuted = 3 (enumerated above, with the evidence that killed each).
- Zero-checkbox docs: found **5**, converted **1**, explained-as-correct **1**, routed **3** (R5).

## Progress Log

- **2026-08-22, interactive `/plan-reconcile ao` (slot 2, harsh_pc)**: Phases -1, 0, 2 and the mechanical/targeted
  half of Phase 1 complete. Phase 1's hunter fan-out deliberately not run (see Coverage) — a follow-up pass with it
  enabled is required before this tranche is fully reconciled.
