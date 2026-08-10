---
doc_type: issue
title:
  "`scheduled_job_already_ran.py` — mutual blindness between `--list-done-tranches` (sharded) and `--no-tranche`
  (`all`-mode) scoping"
summary: >-
  The `--list-done-tranches` guard filters on `row.get("tranche")` being truthy, so an `all`-mode row (tranche=null) is
  invisible to per-tranche dispatchers. Conversely, `--no-tranche` filters out rows WITH a tranche value. The two
  scoping paths are mutually blind — if both an `all`-mode and a sharded dispatch run for the same `job_name` on the
  same day, neither sees the other as blocking. Found during investigation of the 2026-08-10 tradfi triple-dispatch
  (todo 12 of `meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md`).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [scheduled-jobs, ag-closeout-audit, deconfliction, already-ran-guard, mutual-blindness, sharding]
related:
  [
    /plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-10"
author: ikennaigboaka [slot-11·planning-vm]
parent_epic: agent_operating_framework_master
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
priority: P2
source:
  [
    "2026-08-10 investigation (slot 11, review) of tradfi triple-dispatch —
    `/plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md` todo 12",
  ]
drift_direction: advance-code
depends_on: []
---

## What I found

`agent-orchestrator/scripts/scheduled_job_already_ran.py`'s `--list-done-tranches` path (lines 169-179) filters blocking
rows on `row.get("tranche")` being truthy. An `all`-mode dispatch has `tranche=null` and is therefore invisible — the
sharded timer would not see a completed `all`-mode run as a reason to skip a per-tranche dispatch. The inverse gap also
exists: `--no-tranche` only sees rows WITHOUT a tranche value, so a completed sharded `tradfi` row is invisible to an
`all`-mode dispatch check.

The `ag-closeout-auditor` timer itself ONLY dispatches per-tranche (never `all` mode), so the gap only materializes when
an `all`-mode dispatch comes from outside the timer (manual operator invocation, direct skill dispatch). But the gap is
structural — it would also affect any future job that legitimately runs both modes.

## Why it matters

- If an `all`-mode run and per-tranche runs overlap on the same day, the same corpus is audited redundantly, wasting
  fleet capacity (a full `all`-mode run is ~10× the work of a single tranche)
- The gap is latent for every job that uses both `--list-done-tranches` and `--no-tranche` scoping — currently only
  `ag_closeout_auditor` and `plan_reconciler` (Saturday exception) use both, but the pattern is extensible
- The specific 2026-08-10 incident (3 tradfi dispatches) also involved a likely manual `all`-mode dispatch that bypassed
  scheduled-job reporting entirely — that secondary gap ("a manual dispatch leaves no row, so no guard can see it") is
  not addressed here but is noted

## Recommended fix

- [ ] [BACKEND] P2. **Make `--list-done-tranches` also see `tranche=null` rows as blocking ALL tranches.** In
      `scheduled_job_already_ran.py`, when `--list-done-tranches` is active, also scan for `tranche=null` rows for the
      same `job_name` on the same day with a blocking status. A completed `all`-mode run covers every tranche, so
      finding one should produce the FULL tranche list as "done" (blocking every per-tranche dispatch). **Done when**: a
      `tranche=null` row with `status=dispatched, agent_exit_reason=lifecycle-complete` causes `--list-done-tranches` to
      output all tranches (not just the truthy-tranche set), and an `agent-orchestrator` QG-green tree confirms no
      regressions.
