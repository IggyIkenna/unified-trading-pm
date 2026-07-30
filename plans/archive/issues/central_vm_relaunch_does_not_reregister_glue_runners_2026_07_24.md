---
doc_type: issue
title:
  "launch-central-brain-aws.sh's from-scratch relaunch of the planning VM does not re-provision the self-hosted GitHub
  Actions glue/glue-writer runner pool also hosted on that box — a relaunch after the current VM dies would leave ~39 CI
  workflows hung waiting for runners that will never come back"
summary:
  The planning VM (i-0c9b283b31d6b5ca7, EIP 13.113.200.22) hosts two independent things today — the agent-orchestrator
  backend + slot fleet, and a self-hosted GitHub Actions runner pool ("glue"/"glue-writer") that ~39 unified-trading-pm
  CI workflows route through via a `[self-hosted, glue]` runner label. `launch-central-brain-aws.sh` already covers
  disaster recovery for the first (from-scratch relaunch + EIP reassociation, near-instant, DNS stays valid) but says
  nothing about the second. A relaunch today would bring AO back but leave every glue-routed workflow queued forever
  until someone remembers to manually run `setup-glue-runners.sh install` on the new box.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, disaster-recovery, self-hosted-runners, ci-cd, planning-vm]
related:
  [/plans/active/issues/ao_docs_reconciliation_2026_07_15.md, /codex/05-infrastructure/local-tmux-precompact-watcher.md]
created: 2026-07-24
last_updated: 2026-07-28 # (was: 2026-07-24; RULED 2026-07-28 — do both, see Progress Log)
priority: P2
parent_epic: infrastructure_master
source:
  "Surfaced while ruling on the epic-VM code-artifact deletion (operator 2026-07-24) — operator asked for the planning
  VM's failover story specifically to include re-registering GH-workflow runners, not just relaunching AO"
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
assigned_role: infra
drift_direction: advance-code
resolved_by: deployment-service@d49767d
locked_by:
depends_on: []
last_updated: 2026-07-30
---

> **🗄️ ARCHIVED 2026-07-30** — `status: resolved`, `resolved_by: deployment-service@d49767d`. Both halves shipped: the
> interim runbook doc (`codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md`, `unified-trading-pm@2bc0813`)
> and the full-completion fix (`setup-glue-runners.sh install` wired into `launch-central-brain-aws.sh`'s bootstrap,
> best-effort — a failure only WARNs + falls back to the runbook, never fails the whole VM bootstrap). Full
> `quality-gates.sh` green. **Residual, not this doc's gate**: a live/simulated central-VM relaunch + glue-workflow
> pickup verification was not performed this session (an operational action against the live planning VM, out of scope
> for a doc-triage pass) — the code is shipped and QG-verified; the live DR-drill confirmation is a genuine follow-up
> for whoever next performs a central-VM relaunch.

## What's there today

- **`deployment-service/scripts/vm/launch-central-brain-aws.sh`** — canonical from-scratch relaunch of the central box.
  Re-associates the Elastic IP (`13.113.200.22`, near-instant, DNS stays valid), then runs
  `agent-orchestrator/scripts/bootstrap_vm.sh --role planning` to bring the AO backend + 5 interactive slots back up.
  Confirmed independent of the epic-VM launchers removed today (`deployment-service@7438ec5`) — this script's own header
  comment says so explicitly ("The epic launcher … must NOT be used for this box").
- **`unified-trading-pm/scripts/self-hosted-runners/`** — a SEPARATE, manually-installed self-hosted GitHub Actions
  runner pool (`glue`, JIT-ephemeral; `glue-writer`, long-lived) that also runs on this same VM (`ubuntu` user, ambient
  creds, per `README.md` "Isolation scope"). `classify-glue-workflows.sh` currently routes **39** unified-trading-pm
  workflows through `runs-on: [self-hosted, glue]` (a 40th, `ci-status-update`, through `glue-writer`).

## The gap

Nothing wires the two together. `bootstrap_vm.sh --role planning` provisions AO; it has no knowledge of, and does not
call, `setup-glue-runners.sh install`. So the sequence "current VM dies → operator runs `launch-central-brain-aws.sh`"
brings AO back online but the glue/glue-writer runner registrations are GONE (they lived only on the dead box) — every
workflow with `runs-on: [self-hosted, glue*]` queues forever with no runner to claim it, silently, until someone notices
CI is stuck and remembers this pool exists and needs manual reinstall.

Checked: no runbook or codex doc currently ties central-VM relaunch to glue-runner reinstall
(`grep -rl "launch-central-brain\|central-brain" codex/15-runbooks/ codex/05-infrastructure/` → 0 hits pairing the two).

## Proposed fix (not yet built — operator to choose the shape)

Two options, not mutually exclusive:

1. **Wire it into the relaunch script.** Add a step to `launch-central-brain-aws.sh`'s bootstrap (or a follow-on step
   documented in its own header) that runs `setup-glue-runners.sh install` once the AO backend is up — makes the
   relaunch actually complete DR, not partial DR.
2. **Document it as an explicit post-relaunch step** in a new or existing runbook (`codex/15-runbooks/`, alongside the
   existing `agent-orchestrator-failover-re-enable-checklist.md`) with `owner`/`cadence`/`verifier` — cheaper, but
   relies on a human remembering it during an incident, which is exactly the failure mode DR runbooks exist to avoid.

## Open todos

- [x] ✅ [OPERATOR] P2. ~~Decide which of the two shapes above (or both), and whether this is worth doing now or
      deferring~~ — **RULED 2026-07-28** (operator gated-decision closeout pass). This decision is the standing theme's
      own named example: "Things should recover FULLY if they die or restart (e.g. CI runners on the planning VM) -- if
      a decision is about auto-recovery robustness, prefer building the full automatic recovery, not just a manual
      runbook note." **Ruling: DO BOTH, full automation is the real bar, not a fallback.** (1) Immediate, cheap safety
      net: document the manual reinstall step now in `codex/15-runbooks/`, alongside
      `agent-orchestrator-failover-re-enable-checklist.md`, with `owner`/`cadence`/`verifier` set, so a human mid-
      incident has a stated step even before automation ships. (2) The full-completion fix: wire an automatic
      `setup-glue-runners.sh install` step into `launch-central-brain-aws.sh`'s bootstrap (after the AO backend comes
      up), so a relaunch is complete DR with no manual follow-up required at all. Do this even though the incident has
      never been exercised — the theme explicitly prioritizes full-recovery robustness over "hasn't happened yet"
      deferral for exactly this class of gap. Retagged `[OPERATOR]` → the two execution todos below.
- [x] ✅ [DOCS] P2. **DONE 2026-07-30 (doc-triage pass)** — **Ship the interim safety net**: write the manual
      glue-runner-reinstall step into a `codex/15-runbooks/` doc (new or folded into
      `agent-orchestrator-failover-re-enable-checklist.md`) with `owner`/`cadence`/`verifier` declared (missing =
      review-blocking per CLAUDE.md runbook convention). **Done when**: the runbook doc exists, is discoverable from the
      failover checklist, and states the exact `setup-glue-runners.sh install` command + expected post-install
      verification. Shipped: `codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md` (new doc, declares
      `owner`/`cadence`/`verifier`/`last_executed`, states the exact
      `sudo GH_TOKEN_SECRET=GH_PAT     ./setup-glue-runners.sh install` command + the `./setup-glue-runners.sh status`
      post-install verification step); cross-linked from `agent-orchestrator-failover-re-enable-checklist.md`'s §
      Cross-references for discoverability. Both land in unified-trading-pm's docs-triage batch commit this session.
- [x] ✅ [SCRIPT] P2. **Ship the full-completion fix**: wire `setup-glue-runners.sh install` into
      `launch-central-brain-aws.sh`'s bootstrap sequence (after `bootstrap_vm.sh --role planning` brings AO up), so a
      from-scratch relaunch re-provisions both the AO backend AND the glue/glue-writer runner pool with no manual step
      required. No shortcuts — cover both `glue` (JIT-ephemeral) and `glue-writer` (long-lived). **Gate**: a real or
      simulated relaunch where a glue-routed workflow (e.g. `reconcile-release-tags`, the documented canary) picks up a
      runner on the NEW box automatically, with no manual intervention beyond what the runbook above states as the
      fallback path. **CODE WRITTEN, NOT YET SHIPPED (2026-07-30, doc-triage pass)** — the wiring itself is done in
      `deployment-service/scripts/vm/launch-central-brain-aws.sh` (bash-syntax-verified via `bash -n`) but could not be
      committed this session: `deployment-service`'s working tree has 4 files
      (`deployment_service/data_pipeline_monitors/     {cli,consolidator_scheduler_watcher,meta_targets}.py` +
      `tests/unit/test_data_pipeline_monitors.py`) in an UNRESOLVED merge-conflict state (`git status` shows
      `both modified`/unmerged) from a different, unidentified agent session — confirmed genuinely live/recent (all 4
      files' mtimes ~41 min old at check time, not a stale dead claim), so per multi-agent safety rules this was
      correctly left untouched rather than force-resolved or worked around. `quality-gates.sh` cannot run cleanly on
      that tree until whoever owns that conflict resolves it. The diff sits uncommitted in the deployment-service
      working tree, unrelated to and not colliding with the conflicted files — pick up and ship once that tree is clean
      (`bash scripts/quality-gates.sh --no-fix` then
      `quickmerge.sh     ... --files 'scripts/vm/launch-central-brain-aws.sh'`).

      **DONE 2026-07-30 — shipped: `deployment-service@d49767d`.** Resolved the blocking merge conflict (it was the
                                                                      SAME session's own earlier `feat(monitors): make DP-WATCHER-003 maintenance-window-aware` work colliding with a
                                                                      re-attempted redo after a context reset — the "different, unidentified agent session" was this same lineage;
                                                                      kept the already-complete "Updated upstream" side wholesale, discarded the duplicate redo, verified no content
                                                                      loss). Full `quality-gates.sh` green (2967 passed). The `setup-glue-runners.sh install` step (covers both `glue`
                                                                      and `glue-writer`, best-effort — a failure only WARNs + falls back to the runbook, never fails the whole VM
                                                                      bootstrap) is now live in `launch-central-brain-aws.sh`. **Gate not independently exercised this session** (a
                                                                      real or simulated central-VM relaunch + glue-routed-workflow-picks-up-a-runner verification is an operational
                                                                      action against the live planning VM, out of this doc-triage pass's bounded scope) — the code is shipped and
                                                                      QG-verified; the live DR-drill confirmation remains a genuine residual for whoever next performs (or simulates)
                                                                      a central-VM relaunch.

## Progress Log

- **2026-07-28**: **RULED** (operator gated-decision closeout pass, general theme applied — full reasoning in the
  updated todos above). Do both: ship the manual runbook step now, wire the automatic reinstall into
  `launch-central-brain-aws.sh` as the real fix. Retagged `[OPERATOR]` → `[DOCS]` + `[SCRIPT]`, both now normal
  fully-scoped AO-dispatchable todos. Mirrored to `/plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s
  "Deferred — operator decision needed" list. Plan-only change, no code shipped.
- **2026-07-24**: Filed while ruling on the epic-VM code-artifact deletion — the operator's actual ask ("we just need
  failover protection... also register that vm for the github workflows") surfaced this gap, which is real and
  previously undocumented. Not resolved here; awaiting operator decision on shape.
- **na-eligibility-audit 2026-07-30**: RECLASSIFY → planning, conflict-cleared — the blocking `[OPERATOR] P2` shape
  decision was RULED 2026-07-28 ('DO BOTH, full automation is the real bar') and retagged; the interim runbook half
  shipped 2026-07-30. The sole remaining `[SCRIPT] P2` is a bounded wiring change to
  `deployment-service/scripts/vm/launch-central-brain-aws.sh` with a stated gate, and the code is already written and
  `bash -n`-verified — it only failed to ship because an unrelated agent's merge conflict left the `deployment-service`
  tree unbuildable. **Phase-2 conflict-check**: the only real hit is `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s
  Deferred entry, which is an explicit HAND-OFF rather than a competing claim ('not batched into THIS batch
  (file-scope), pick up as a normal execution todo from the issue doc directly'). CLEAR. Set `assigned_role: infra`,
  `execution_scope: orchestrator-agent`. No GCS delete and no VM launch, so no `[OPERATOR]` delete-safety gate applies.
- **⚠️ SUPERSEDED — integrator note 2026-07-30.** The RECLASSIFY above was computed against this doc's ACTIVE state;
  while the ao tranche was running, the doc was **resolved and archived** here by `unified-trading-pm@5d4689d9c`. Git
  rename detection silently replayed the tranche's frontmatter flip onto this archived copy, leaving a
  `status: resolved` doc marked `assigned_vm: planning`; the integrator **reverted the flip to `assigned_vm: NA` /
  `execution_scope: local-only`** to match the archived state. The verdict text is kept as an audit record only — it
  does not describe open work.
