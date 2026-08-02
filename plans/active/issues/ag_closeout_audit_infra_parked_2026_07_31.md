---
doc_type: issue
title:
  "Parked findings from the 2026-07-31 /ag-closeout-audit infra run (3 findings: 2 false-unchecked/stale-state
  discrepancies + 1 asset_group mistag)"
summary: >-
  Three mechanically-verified findings surfaced across two same-day `/ag-closeout-audit infra` passes (2026-07-31,
  scheduled daily run — the original 14:06 UTC run, slot 13, and a 21:26 UTC re-dispatch, also slot 13, that verified
  the tranche unchanged and added finding 3) that this skill's own `does_not` scope excludes it from fixing directly.
  Findings 1-2 are false-unchecked checkbox / stale-doc-state reconciliation, `/plan-reconcile`'s job, not this skill's
  (this skill's classification trusts the frontmatter `status` field and checkbox state as-is). Finding 3 is a likely
  `asset_group` mistag whose real owning tranche is `ao`, not `infra` — per the skill's concurrent-sharded- worker
  safety rule, only the owning tranche may write the retag, so this run only reports it. All three are evidence-backed,
  not judgment calls — recorded here per the "Parked findings ALWAYS get a durable issue doc" hard rule so they are not
  lost in either run's ephemeral chat/evidence text.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, execution-service]
scope: [engineer, admin]
tags: [infra, ag-closeout-audit, plan-reconcile, false-unchecked, parked-findings]
related:
  [
    /plans/active/codex_violations_ratchet_to_five_2026_06_10.md,
    /plans/active/issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md,
    /plans/active/issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md,
    /plans/active/infra_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: >-
  `/ag-closeout-audit infra` run 2026-07-31 (ag_closeout_auditor scheduled worker, slot 13), Phase 1 per-doc
  classification (a 10-agent Workflow plus direct verification of two of its findings). Finding 3 added by a same-day
  re-dispatch (also slot 13, ~21:26 UTC) that re-derived the candidate set fresh via
  `generate_ag_closeout_audit_candidates.py --tranche infra` (grown 32→37 members over ~7h) and direct-read every
  net-new/still-never-cited candidate rather than re-running the full Phase 1 Workflow, per the skill's own
  iterative-drain guidance (re-check before fresh triage).
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /plans/active/codex_violations_ratchet_to_five_2026_06_10.md,
    /plans/active/issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md,
  ]
---

# Parked findings — 2026-07-31 `/ag-closeout-audit infra` run

Both items below are **mechanically verified, not ambiguous** — there is no operator decision to make, just a
checkbox/doc-state reconciliation this skill is scoped out of performing itself. `/plan-reconcile`'s next infra-scoped
(or corpus-wide) pass should pick these up as auto-fixable findings.

## 1. `codex_violations_ratchet_to_five_2026_06_10.md` — `delta_proxy_repricer.py` checkbox is false-unchecked

**Doc state**: line ~373-384, `- [ ] [CODE] P3.` for `execution_service/engine/delta_proxy_repricer.py`, last corrected
2026-07-27 to say "Real work needed is the OPPOSITE of deletion: wire it into the live execution handler + add tests ...
A separate, concurrent workstream owns the actual execution-service code wire-in — this todo is the PLAN reference
only."

**Reality, verified this run**: that "separate, concurrent workstream" has already shipped. `execution-service@89fbf99d`
("feat(execution): wire delta-proxy repricer into live MM QUOTE-instruction handling") wires `DeltaProxyRepricer`
directly into `execution_service/engine/quote_maintenance.py`
(`from execution_service.engine.delta_proxy_repricer import ... DeltaProxyRepricer` at line 74, instantiated as a
`field(default_factory=DeltaProxyRepricer)` at line 142, module docstring at line 1 states "wires DeltaProxyRepricer
into MM QUOTE-instruction handling"), with a dedicated test file
(`execution-service/tests/unit/engine/test_delta_proxy_repricer.py`) plus `test_quote_maintenance.py` covering the
integration. This is real, shipped, non-trivial wiring — not a coincidental file mention.

**Recommendation [WORKER REC]**: flip this checkbox `[x]` ✅, citing `execution-service@89fbf99d`, with a note that the
"separate, concurrent workstream" referenced in the 2026-07-27 correction has landed. Do not fold this into
`infra_satellite_ao_dispatch_batch4_2026_07_31.md` — there is no remaining work to dispatch, only a stale checkbox to
correct.

## 2. `issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md` — target directory already absent from disk

**Doc state**: `status: open`, `assigned_vm: NA`. Todo 3 (the only open item) is `[OPERATOR] P2` — delete
`.tabs/3/instruments-service-agentwork-sports-2026-07-13/` now that its 10 stash entries are bundled + independently
verified at `.tabs/3/stash-bundles/instruments-service-agentwork-sports-2026-07-13-stashes.bundle`. The doc's own latest
dated section (2026-07-31 na-eligibility-audit Progress Log entry) reconfirms this todo is still open and correctly
`assigned_vm: NA` (the delete is blocked by `block_destructive_commands.py`'s unconditional PreToolUse guardrail against
`rm -rf` for autonomous workers, no override).

**Reality, verified this run**: from this session's own filesystem
(`/home/ubuntu/unified-trading-system-repos/.tabs/3/`), **neither `instruments-service-agentwork-sports-2026-07-13/` NOR
`stash-bundles/` exist** — both are genuinely absent. This could mean the operator already ran the cited `rm -rf` (and
the bundle directory was separately cleaned up, or never persisted on this particular host/mirror), in which case the
doc is stale and should be closed out. It could equally be an artifact specific to how this sandbox's `.tabs/3` was
provisioned rather than genuine current state on the real target host — `.tabs/3` itself is clearly still a live,
actively-used slot (many sibling repo directories with `mtime` stamps from within the last hour), so this is not "the
whole slot was wiped," it looks like a targeted absence.

**Recommendation [WORKER REC]**: do not assume completion from this evidence alone — the doc's own most-recent dated
section (2026-07-31, same day as this observation) explicitly re-affirms the todo as open, which is a real signal this
absence might not be authoritative for the actual target host. `/plan-reconcile` (or the operator directly) should
positively confirm on the real host whether the directory is gone because the delete ran, and either (a) flip the
checkbox `[x]` with that confirmation and check the doc for archival-eligibility, or (b) if the absence is a
sandbox-provisioning artifact unrelated to the real target, leave the doc as-is and note the discrepancy was checked and
dismissed.

## 3. `issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` — likely `asset_group` mistag (real owner: `ao`, not `infra`)

**Found**: 2026-07-31 re-dispatch (slot 13), via `generate_ag_closeout_audit_candidates.py --tranche infra` — this is
currently the tranche's ONLY never-cited, non-self-dispatched candidate (`assigned_vm: NA`, `status: open`, cited
nowhere in any infra covering doc).

**Doc state**: `asset_group: [infrastructure]`, but `parent_epic: orchestrator_master` and its entire content (the
`ao-self-pull.sh` FF-pull cron, `agent-orchestrator/agents/main.md`'s `${WORKSPACE_ROOT}` scratch-inbox checkpoint,
`orchestrator.service` restart currency, a `_wire_sequential_prereqs` regen bug) is agent-orchestrator
dispatch/worker-lifecycle content — squarely the skill's own definition of the `ao` tranche's scope, and a match for
`ao`'s `parent_epic` hint (`orchestrator_master` + `agent_operating_framework_master`), not any of `infra`'s own 3 live
tracks (repo/script governance+CVE, org/account admin+terraform, PM plan-hygiene tooling — see
`infra_consolidated_closeout_2026_07_25.md`'s Reachability map). This reads as a real mistag, not a legitimate
dual-tranche doc.

**Why not fixed here**: `ao` is a DIFFERENT tranche than this run's (`infra`), and
`cursor-configs/skills/ag-closeout-audit/SKILL.md` § "Running as one of N concurrent sharded tranche workers" rule 1 is
explicit — a shared/cross-tranche doc's real owner (by `parent_epic`) is the only tranche allowed to WRITE to it (a
retag included), precisely to avoid two concurrent sharded workers racing the same file. This run only CLASSIFIES it
(excluded from infra's own orphan count, since infra is not its real scope) and reports the finding, per that same rule.

**Recommendation [WORKER REC]**: retag `asset_group: [infrastructure]` → `[ao]` (the `ao`-tranche's own
`/ag-closeout-audit ao` run, or a corpus-wide retag pass, should apply this — not this run). Note for whoever does: even
under the correct tag this doc would NOT be Phase-3-draftable regardless — its one open todo (`[OPERATOR] P2`, setting
`AGENT_ORCHESTRATOR_SLACK_WEBHOOK` in the planning VM's `.env.local`) is host-level config outside any worker's scope,
so the retag is a corpus-hygiene fix, not an unlock of new dispatchable work.

## Todos

- [x] ✅ [DOCS] P3. **DONE 2026-08-02** (na-eligibility-audit, infra tranche) — reconciled
      `codex_violations_ratchet_to_five_2026_06_10.md`'s `delta_proxy_repricer.py` checkbox per finding 1 above.
      Done-when met exactly as written: the checkbox is now `[x]` citing `execution-service@89fbf99d`, and the evidence
      was re-verified via `git show --stat 89fbf99d` in the execution-service checkout (873 insertions / 6 files:
      `quote_maintenance.py` +205, `v2/handlers.py` +29, `test_delta_proxy_repricer.py` +328,
      `test_quote_maintenance.py` +236, `test_router_and_handlers.py` +67) plus
      `git merge-base --is-ancestor 89fbf99d origin/live-defi-rollout` (ancestor confirmed) and a live re-read of the
      import at `quote_maintenance.py:74`. This finding sat unreconciled across three consecutive
      `/ag-closeout-audit     infra` runs (07-31, 08-01, 08-02) because that skill is scoped out of false-unchecked
      flips; it is in scope for `/na-eligibility-audit`'s KEEP-NA-stale-items verdict, which uses the same HARD evidence
      bar.
- [ ] [DOCS] P3. Positively confirm (on the real target host, not just this sandbox) whether
      `.tabs/3/instruments-service-agentwork-sports-2026-07-13/` has genuinely been deleted, then reconcile
      `issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md` per finding 2 above. Done
      when: the doc's todo 3 and `status`/`assigned_vm` accurately reflect confirmed reality, with the confirmation
      method cited.
- [ ] [DOCS] P3. Retag `issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`'s `asset_group`
      `[infrastructure]` → `[ao]` per finding 3 above (owning-tranche fix — leave to the `ao`-tranche's own audit/a
      corpus-wide retag pass, not this run). Done when: the tag is corrected and `check_ag_closeout_linkage.py` stays
      clean for both tranches.

## Progress Log

- **2026-07-31 ~21:26 UTC** — `/ag-closeout-audit infra` re-dispatched same-day (autonomous mode, scheduled, slot 13,
  ~7h after the 14:06 UTC run that produced findings 1-2 + `infra_satellite_ao_dispatch_batch4_2026_07_31.md`). Findings
  1-2 re-checked live: both still unreconciled (`delta_proxy_repricer.py` checkbox still `[ ]`, the stash-clone todo 3
  still `[ ]`) — no drift, no action needed from this run. Batch4 re-checked: still `status: draft`, untouched, awaiting
  the operator flip. Re-derived the candidate set fresh (`generate_ag_closeout_audit_candidates.py --tranche infra`:
  32→36→37 members across two re-checks straddling a mid-run `git pull --ff-only`) and direct-read every
  net-new-since-14:06 doc (3: two already self-dispatched and well-fitted to Track 1/2, one —
  `vm_launcher_setup_script_freshness_gap_2026_07_31.md` — already self-dispatched regardless of its citation's
  realness) plus the one still-never-cited, non-self-dispatched candidate at every snapshot
  (`ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`) — that one produced finding 3 above. Re-checked
  batch1's Deferred gates G1 (`base-service.sh`/`base-library.sh` serialization —
  `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s `[BACKEND] P3` sub-item 3 still `- [ ]`) and G3
  (`DataStatusTab.tsx` — `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s `[INFRA] P2` part (B) still
  `- [ ]`, folded into a still-open multi-part todo): both unchanged, nothing newly cleared. **Net result: 0 new genuine
  infra orphans, no new batch5 drafted** (nothing conflict-cleared since batch4; see the mistag caveat above for why the
  one flagged candidate doesn't count). Did not re-run the full 10-agent Phase 1 Workflow over all 37 members — per the
  skill's batchN iterative-drain methodology ("re-check the prior batch's Deferred section first... only then run a
  fresh pass over whatever's left"), a same-day re-dispatch with a near-static corpus warrants a targeted delta read,
  not a from-scratch re-classification of docs read hours earlier with no intervening change; mirrors the sibling
  `prediction` tranche's own same-day precedent (`unified-trading-pm@e89cdd5eb`, "verified unchanged, 0 new orphans").

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, stale items — 1 of 3 closed.** First
  verdict for this doc (no prior marker). Read end-to-end; `grep -cE '^- \[ \]'` = **3** at entry, matching this
  verdict's item count, **now 2**. Finding 1's todo is closed above with independently re-derived evidence. Doc stays NA
  on the remaining 2, both correctly non-worker-determinable: todo 2 requires positively confirming a directory's state
  **on the real target host**, which no slot session can observe (this sandbox's `.tabs/3` absence is explicitly
  recorded as non-authoritative by the finding itself); todo 3 is an `asset_group` retag reserved for the `ao` tranche
  by the `/ag-closeout-audit` owning-tranche-writes-only rule — see the tranche-level `BLOCKED-OPERATOR-DECISION` on
  that rule's deadlock recorded in `infra_consolidated_closeout_2026_07_25.md`'s 2026-08-02 marker. This doc is a
  parked-findings register by construction, so NA remains the correct home for it as a whole.
