---
doc_type: issue
title: Parked findings from the 2026-07-31 /ag-closeout-audit infra run (2 false-unchecked/stale-state discrepancies)
summary: >-
  Two mechanically-verified discrepancies surfaced while running Phase 1 of `/ag-closeout-audit infra` (2026-07-31,
  scheduled daily run, slot 13) that this skill's own `does_not` scope excludes it from fixing directly —
  false-unchecked checkbox / stale-doc-state reconciliation is `/plan-reconcile`'s job, not this skill's (this skill's
  classification trusts the frontmatter `status` field and checkbox state as-is). Both findings are evidence-backed, not
  judgment calls — recorded here per the "Parked findings ALWAYS get a durable issue doc" hard rule so they are not lost
  in this run's ephemeral chat/evidence text.
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
    /plans/active/infra_satellite_ao_dispatch_batch4_2026_07_31.md,
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
  classification (a 10-agent Workflow plus direct verification of two of its findings).
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

## Todos

- [ ] [DOCS] P3. Reconcile `codex_violations_ratchet_to_five_2026_06_10.md`'s `delta_proxy_repricer.py` checkbox per
      finding 1 above. Done when: the checkbox is `[x]` citing `execution-service@89fbf99d`, re-verified via
      `git show --stat 89fbf99d`.
- [ ] [DOCS] P3. Positively confirm (on the real target host, not just this sandbox) whether
      `.tabs/3/instruments-service-agentwork-sports-2026-07-13/` has genuinely been deleted, then reconcile
      `issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md` per finding 2 above. Done
      when: the doc's todo 3 and `status`/`assigned_vm` accurately reflect confirmed reality, with the confirmation
      method cited.
