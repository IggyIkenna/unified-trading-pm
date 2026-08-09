---
doc_type: plan
title: AO satellite AO batch 10 — 6 bounded items extracted from 3 non-qualifying `ao`-tranche NA docs
summary: >-
  TENTH AO-dispatch batch for the `ao` topic tranche — produced by a satellite-batch-extraction pass (mirroring
  `/ag-closeout-audit`'s pattern) over 21 `ao`-owned `assigned_vm: NA` docs that a same-day RECLASSIFY sweep read
  end-to-end but did NOT whole-doc-flip (each has real remaining judgment/operator-gated items). This batch pulls out
  ONLY the specific bounded, worker-determinable items from 3 of those 21 docs — everything else in each source doc
  (genuine design forks, credential/host-only actions, operator-gated decisions, standing-ruling citations) is left
  untouched in place. 2 items from `ao_satellite_ao_dispatch_batch2_2026_07_30.md` (itself an `assigned_vm: NA`
  satellite doc whose own repeated na-eligibility-audit verdicts lumped 3 open items together as needing "specialized
  SSM/host/credential access" without a fresh per-item split — re-examined here: the timer-fire check and the
  wip-preserve ref recovery are ordinary read-only/git-archaeology work any AO worker on the fleet can do, only the
  token re-mint on a named host genuinely needs operator/credential access and stays behind); 3 items from
  `ao_open_issues_consolidated_close_out_2026_07_17.md` (a 980-line LOCAL/human hub doc — the archival sweep, the
  plan_reconciler end-to-end observation, and the role-lifecycle-field reclassification are all bounded audit/build work
  with stated gates, left behind: the open-ended `tmux_session_lost` churn hunt, the already-moot
  `ao_docs_reconciliation` close-out citation, and the safety-domain Layer-1 recovery-audit-signoff producer rewire,
  whose "decide a SignoffVerdict" internals are unspecified design work); 1 item from
  `dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md` (the empirically-proven, no-longer-judgment-call
  package.json version bump — its sibling "should the dashboard gate on formatting at all" item stays, a genuine
  undecided policy call). All 6 todos are file-disjoint (verified during drafting) so this plan needs no `sequential`
  gate.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, strategy-service]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-10, satellite-docs, satellite-extraction]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch10_finalize_2026_08_09.md,
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/active/issues/dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/active/issues/dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md,
    agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh,
    agent-orchestrator/agents/,
    agent-orchestrator/dashboard/package.json,
  ]
source: >-
  Satellite-batch-extraction pass, 2026-08-09, mirroring `/ag-closeout-audit`'s satellite-batch pattern per operator
  instruction — a targeted per-item extraction over the 21 `ao`-tranche `assigned_vm: NA` docs a same-day RECLASSIFY
  sweep read end-to-end without a whole-doc flip. Every item below was individually checked against
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` §"Dispatch-scope eligibility" and
  conflict-checked against the live `assigned_vm: planning` corpus (batch7/batch8/batch9, `ao_open_issues`'s own
  split-out-child-plans table, and each item's own source doc's na-eligibility-audit history) before being drafted — see
  this batch's own Progress Log for the per-item conflict-check trail.
---

# AO satellite AO batch 10

> **`status: draft`** — pending operator approval, same convention as batch5-9: flip to `active` to dispatch.
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** once approved, same as the rest of this series.

## Why this plan exists

Today's earlier RECLASSIFY sweep read all 21 `ao`-tranche `assigned_vm: NA` docs end-to-end and found 8 that qualified
for a whole-doc flip (handled separately). The other 13 did not qualify — but "doesn't qualify as a whole doc" is not
the same as "nothing in it is dispatchable." This batch is the satellite-extraction pass over those 13 (mirroring
`/ag-closeout-audit`'s pattern, generalized to per-item instead of per-doc): read each doc fully, classify every open
item against the dispatch-scope-eligibility bar, and pull out only the items that are genuinely bounded and
worker-determinable, leaving every judgment/operator-gated item untouched in its source doc.

**Yield was low by design, not by shortfall**: of the 21 candidate docs, 3 contributed the 6 items below; the other 18
had zero extractable items (each doc's remaining open work is either a genuine design fork, an explicit operator/
credential/host-only action, already fully resolved with a stale checkbox, already archived, or — in one case — already
re-flagged `assigned_vm: planning` directly by a prior session and no longer NA at all). See this plan's Progress Log
and the parent extraction session's own report for the full per-doc disposition.

## Rules for every worker on this plan

- **Do not edit the 3 source docs' remaining checkboxes** beyond what this plan's own todos below already changed at
  drafting time (a redirect-pointer replacing the extracted item's checkbox text). Append your evidence to THIS plan's
  own todo when you finish; the paired finalize plan
  (`/plans/active/ao_satellite_ao_dispatch_batch10_finalize_2026_08_09.md`) reconciles the evidence back into each
  source doc.
- The 6 todos below are file-disjoint by construction — keep new test/evidence files scoped to the todo's own concern.
- No todo below deletes prod data or launches a VM. Todo 6 mutates a `package.json` + lockfile only.

## Todos

- [ ] [SCRIPT] P3. **Verify whether `na-eligibility-auditor.timer`'s most recent scheduled fire(s) since 2026-07-28
      reached `agent_kind=na_eligibility_auditor` lifecycle-complete.** Query the live orchestrator's `agents` table
      (read-only — `/check-agent-orchestrator` skill or
      `agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh`; a worker dispatched on the orchestrator VM
      itself can query `data/state/state.db` directly, no SSM needed). The 2026-07-28 07:00 UTC fire is already known to
      have hit `Active: failed` on a curl TIMEOUT past `--max-time 2400`/`TimeoutStartSec=2450`; record whether a LATER
      fire (pre- or post- any timeout fix since) actually completed end-to-end. Do NOT touch the timeout value itself.
      **Done when**: this todo's own evidence records the fire-completion verdict (dispatch id, timestamps, terminal
      state) for the most recent fire(s). Source: `/plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md:199` (its
      `[SCRIPT] P3` item, itself sourced from `na_eligibility_auditor_timer_not_yet_installed_2026_07_27.md`, archived).
      Repo: agent-orchestrator (read-only).
- [ ] [DATA] P2. **Check + recover-or-dispose `strategy-service`'s stranded wip-preserve ref
      (`refs/wip-preserve/cascade-strategy-service-a77eb6d170ca`, 2026-07-28, a `staging-lock-check.yml`
      self-hosted-runner-migration commit).** Check whether it was independently superseded by a later rollout in
      strategy-service; if so, the ref is safely superseded and can be deleted (cite the superseding SHA). If not,
      recover it the same way the sibling `unified-trading-library` ref was already recovered under this same source
      finding (fetch the preserved ref, cherry-pick/fast-forward it onto current `origin/live-defi-rollout`, ship via
      quickmerge). **Done when**: the ref's disposition (superseded-and-deleted, or recovered-and-shipped) is recorded
      with evidence in this todo. Source: `/plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md:242` (its
      `[DATA] P2` item, itself sourced from
      `/plans/archive/2026_08/wip_preserve_refs_silently_unrecovered_2026_07_29.md`, archived). Repo: strategy-service.
- [ ] [REVIEW] P1. **Sweep `plans/active/issues/` for `ao`-tagged docs that are already resolved/fully-`[x]` but never
      archived, and archive each via the standard 6-step ritual** (banner, codex-alignment check, corpus-wide referrer
      fixup, lock check). This is the current-state form of the source doc's Phase-5 gate — do not trust its stale "Docs
      #2 and #6" reference (those predate several archival waves already landed since 2026-07-17); re-derive the
      candidate set fresh from a live grep/`check_archive_candidates.sh`-style pass scoped to `asset_group: [ao]` /
      `parent_epic: orchestrator_master` docs. **Done when**: `plans/active/issues/` contains no resolved-but-
      unarchived `ao`-tagged doc, and `regenerate_active_plan_inventory.py` is re-run clean. Source:
      `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md:479` (Phase 5, its `[REVIEW] P0` item). Repo:
      unified-trading-pm.
- [ ] [BACKEND] P1. **Prove ONE `plan_reconciler` run end-to-end (observe the next natural 01:00 UTC timer fire, or
      trigger one if the doc's stated hold has cleared) — plus pin 2 named residuals.** Gate: (a) observe a full run
      producing BOTH a `plan_health_result` activity row AND a pushed `plan_reconciler/<dispatch_id>` branch — cite the
      dispatch_id, result row, and branch name, do not tick on a green-looking journal line alone; (b) **R1** — pin the
      exact code path that flips a typed agent's slot `working`→`idle` (previously empirically observed around a service
      restart, not yet located in code — already checked & excluded: seed-from-tabs, claim_slot, the dispatch-ack
      requeue, the 25-min health stale-timeout); (c) **R2** — on the run, confirm the watchdog logs an EXEMPTION for the
      reconciler's slot (`typed_agent_sessions` continuation in `worker_liveness_watchdog.py`) instead of a kill, and
      capture the slot's status column during the run — if it still reaps, the `AgentRow` guard is being defeated
      (investigate whether a restart archives/clears the AgentRow or its `tmux_session`). The operator-directed hold on
      retrying this (pending several other AO plans settling) has since cleared — all 6 named plans are confirmed
      archived as of the source doc's 2026-08-06 re-verification. **Done when**: (a)/(b)/(c) all recorded with evidence.
      Source: `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md:806` (its `[BACKEND] P0` item). Repo:
      agent-orchestrator.
- [ ] [BACKEND] P2. **Role lifecycle-field reclassification — align the declared `lifecycle` on plan-worker roles with
      reality.** `backend_engineer` / `ui_developer` / `quant_dev` / `infra` are declared `lifecycle: one_shot` in their
      role files; reclassify to `persistent`, and resolve `data_engineering` (scheduled-vs-persistent) to whichever it
      actually is. **NOT required for correctness** — the shipped dispatch fix already rekeys reaping on DISPATCH
      CONTEXT (a bound `one_shot` `AgentRow`), so nothing reads `role.lifecycle` to decide reaping any more; this is a
      declared-vs-actual documentation-integrity fix. **Done when**: each role's `lifecycle` field matches its real
      dispatch pattern, or a recorded decision states why the declared value intentionally stays (cite the reason inline
      in the role file or a codex doc). Source: `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md:828`
      (its `[BACKEND] P0` item, itself sourced from `ao_worker_lifecycle_dispatch_context_2026_07_21.md`, archived).
      Repo: agent-orchestrator.
- [ ] [INFRA] P3. **Bump `agent-orchestrator/dashboard/package.json`'s `"prettier": "^3.6.2"` → `"^3.9.5"`,
      `npm install`, confirm `format:check` clean.** The version-choice question is already empirically resolved
      (byte-identical output + zero idempotency drift proven on every dashboard TS/CSS file type — the proseWrap defect
      this decision worried about is a markdown-only Prettier option, confirmed inert on `.tsx`/`.css`); this is now a
      mechanical version bump, no remaining judgment. **Done when**: `agent-orchestrator/dashboard`'s
      `format`/`format:check` scripts agree with `scripts/hooks/prettier-autostage.sh`'s 3.9.5 pin on the same file set.
      Source: `/plans/active/issues/dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md:81` (its 2nd
      `[INFRA] P3` item). Repo: agent-orchestrator.

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/pre-task-plan-conflict-check.md`,
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (todo 3).

## Progress Log

- **2026-08-09** — Authored by a satellite-batch-extraction pass over the 21 `ao`-tranche `assigned_vm: NA` docs named
  in the parent RECLASSIFY sweep's candidate list. Per-item conflict-check before drafting: (1)/(2) — grepped
  `plans/active/` for `wip-preserve/cascade-strategy-service` and `na-eligibility-auditor.timer`; only self-references
  in the source batch2 doc and unrelated archival-target mentions in batch7 (a DIFFERENT doc's archival, not this
  timer-check claim) — clear. (3) — no other active plan claims the "sweep + archive resolved-but-unarchived `ao` docs"
  ground. (4)/(5) — grepped for "plan_reconciler end-to-end"/"role lifecycle reclassification"/"lifecycle: persistent"
  across `plans/active/`; only self-references in the source doc — clear. (6) — grepped
  `dashboard_prettier_version_skew_vs_wrapper_pin` across batch7/8/9: batch8 Phase 3 explicitly assessed this doc "fully
  deferred, both items pure judgment calls" — but that assessment predates the 2026-08-08 round5 operator session that
  empirically resolved the version-choice question and split the prose follow-up into a real tracked todo (confirmed via
  the source doc's own Progress Log dating); batch8's snapshot is stale relative to the doc's current state, not a live
  conflicting claim — clear to extract. Held back from this batch (left in their source docs, not extracted): batch2's
  `[INFRA] P3` token re-mint (credential/host-specific, already ruled "correctly operator-only" by the doc family that
  originated it); `ao_open_issues`'s `tmux_session_lost` root-cause hunt (open-ended investigation, prior reaper-fix
  hypothesis already falsified, no bounded done-when beyond "find the driver or don't"); `ao_open_issues`'s
  `ao_docs_reconciliation` close-out item (its target doc,
  `/plans/archive/2026_08/ao_docs_reconciliation_2026_07_15.md`, is independently confirmed `status: resolved` and
  already archived — this todo is a stale checkbox, not real remaining work, left for a future stale-checkbox correction
  pass rather than force-extracted here); `ao_open_issues`'s Recovery-audit Layer-1 producer rewire
  (`ao_recovery_audit_layer1_deleted_2026_07_15.md`'s own sole open todo — genuine safety-domain design work, "decides a
  SignoffVerdict" has no specified decision logic, stays behind); `dashboard_prettier`'s "decide whether the dashboard
  should gate on formatting at all" (explicit undecided policy call, sequenced behind the extracted bump anyway).
