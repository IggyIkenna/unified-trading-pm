---
doc_type: issue
title:
  Stale issue-doc todo caused a 2-day-later duplicate 4-VM SPOT reprocess run — the underlying work was already done,
  the doc's own checkbox/status was never closed
summary: >-
  `mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md` carried an unchecked `- [ ]` todo + `status: open`
  describing a "not yet launched" MDPS odds_horizon_bucket reprocess. The reprocess it described WAS actually launched
  and completed on 2026-07-25 (by a different session, VMs `mdps-sports-bucket-20260725-*`), with results recorded in a
  SEPARATE new doc (`mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`) — but the original launch-prep
  doc's own todo/status was never flipped to reflect this. The backlog re-derived the stale open todo as task
  `mdps_odds_horizon_bucket_reprocess_launch_prep-001` and dispatched it again on 2026-07-27, causing a full duplicate
  4-VM SPOT reprocess run (2242 dates re-processed, ~35min wall-clock, non-trivial compute spend) for work that had
  already been done 2 days earlier. Harmless in outcome (the reprocess is `--force` idempotent — re-running it just
  re-confirms/re-writes the same canonical shape, independently CONFIRMING the original run's stability with an
  identical residual-failure signature 2 days apart) but wasteful, and the same gap will recur for any issue doc whose
  "ready-to-execute" recipe gets run ad-hoc without closing that SAME doc's own todo.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, issue-doc-lifecycle, duplicate-work, backlog-regen, stale-todo, sports, mdps, vm-launcher]
related:
  [
    /plans/archive/issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md,
    /plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md,
    /plans/archive/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-07-27
author: unknown
assigned_vm: NA
parent_epic: orchestrator_master
execution_scope: local-only
priority: P2
estimate_class: refactor
source: mdps_odds_horizon_bucket_reprocess_launch_prep-001 (slot 9, 2026-07-27) — discovered mid-task, after launch
resolved_by:
  "operator ruling 2026-08-06 (interactive) closed the sole open [BACKEND] P3 todo — no mechanical detector needed, the
  codex process-habit rule (/codex/12-agent-workflow/pre-task-plan-conflict-check.md) is sufficient"
locked_by:
context_scope:
  [
    /plans/archive/issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md,
    /plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
  ]
drift_direction: advance-code
depends_on: []
---

> **🟢 ARCHIVED 2026-08-07** — `status: resolved` with zero open todos; archived per
> [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)'s
> archive-on-resolve rule. The sole `[BACKEND] P3` todo was RULED closed 2026-08-06 (operator, interactive) — no
> mechanical detector needed; no open work remains.

# Stale issue-doc todo → duplicate dispatch 2 days after the work was already done

## What happened

Dispatched task `mdps_odds_horizon_bucket_reprocess_launch_prep-001` (plan_ref
`issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`) on 2026-07-27. That doc's title literally read
"launch prep done 2026-07-25, **NOT yet launched**" with `status: open` and an unchecked todo. Followed its
"Ready-to-execute next step" recipe verbatim: re-verified tarball freshness, launched 4 sharded SPOT VMs
(`mdps-sports-bucket-20260727-013917/013942/014005/014026`), monitored to completion, verified manifest stability.

Partway through writing up the completion note, cross-checked the PARENT plan
(`sports_satellite_ao_dispatch_batch2_2026_07_24.md`) and found this EXACT step already marked `[x]` ✅ done since
2026-07-25, citing a DIFFERENT VM run (`mdps-sports-bucket-20260725-035949/040027/040053/040119`) with results tracked
in a SEPARATE doc, `issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md` — created 2026-07-25,
describing the identical scope, and even the IDENTICAL residual-failure signature (18 `ADAPTER_RETURNED_EMPTY_OUTPUT` +
4 `RAW_ODDS_SHAPE_UNRECOGNIZED` (2026-06-21..24) + 4 `LOSS_GUARD_BLOCKED`, same specific dates). That doc's own
follow-up escalation todo was even already closed by a THIRD slot on 2026-07-26
(`issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md`).

So: the reprocess had been fully executed, verified, and its residual findings tracked+escalated, across THREE separate
sessions over 2026-07-25/26 — but the ORIGINAL `..._launch_prep_2026_07_25.md` doc (which is what the AO backlog
actually derives tasks from) never had its own `- [ ]` flipped to `[x]` or its `status: open` flipped to `resolved`. The
backlog regenerator saw a live open todo in a `status: open` doc and re-derived + dispatched it, 2 days after the
described work was already done, complete, and separately documented.

## Why it matters

- **Wasted compute**: a full 4-VM SPOT `e2-standard-8` reprocess run (~35min wall-clock combined, ~2242 dates, 166,849+
  shards rewritten) for work already done. Not catastrophic (SPOT is cheap, the operation is idempotent, no data was
  corrupted — `--force` mode always re-derives regardless of prior state) but a clean waste avoidable by correct doc
  bookkeeping.
- **Pattern risk, not a one-off**: this specific failure mode — "issue doc A describes a ready-to-execute recipe; a
  LATER session runs the recipe but files results in a NEW issue doc B instead of closing A's own todo" — will recur for
  any similarly-shaped prep-doc unless the closing habit is corrected. It is DISTINCT from the already-tracked
  `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` pattern (which is about the SAME task_id live on
  two slots AT THE SAME TIME via a failover/lease race) — this is a stale, unclosed doc getting re-derived DAYS LATER as
  a fresh todo, a backlog-regen/issue-doc-lifecycle gap, not a live dispatch race.
- **Silent until noticed**: nothing flagged this automatically — it was caught only because this session happened to
  cross-check the parent plan before declaring done, rather than trusting the dispatched doc's own (stale) "not yet
  launched" framing at face value.

## Recommended fix

1. **Immediate**: flip `mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`'s own todo + `status` now (done in
   this same session — see that doc's updated Todos section) so the backlog does not re-derive it a third time.
2. **Process habit**: when executing a "ready-to-execute" recipe copy-pasted FROM an issue doc, always flip THAT SAME
   doc's own todo/status when done — even if a fresh doc is ALSO filed for new residual findings (the residual findings
   belong in the new doc; the ORIGINAL doc's "is this done" bookkeeping does not).
3. **Backend consideration** (not scoped/executed here — a design question, not this todo's job): could
   `regen_backlog_from_plan.py` / the issue-doc-lifecycle sweep detect a doc whose described action is provably already
   complete (e.g. cross-referencing `related:` docs created after it, or checking whether a VM-name pattern matching the
   doc's own recipe already ran) before re-dispatching? Flagging as a question for whoever owns backlog-regen, not
   proposing a specific mechanism here.

## Todos

- [x] ✅ [BACKEND] P3. Consider whether `regen_backlog_from_plan.py` / the issue-doc-lifecycle sweep can catch an issue
      doc whose own todo is stale-open while a `related:`-linked sibling doc (created later) already records the same
      work done — a design question for whoever owns backlog-regen, not a prescribed fix. (repo: unified-trading-pm) —
      **RULED 2026-08-06 (operator, interactive): CLOSED — no mechanical detector. The codex rule is sufficient.** This
      doc's own recommended fix #2 (the process habit) was codified into a codex HARD RULE the day after this incident:
      `/codex/12-agent-workflow/pre-task-plan-conflict-check.md`, operator ruling 2026-07-28 — "any task started must be
      checked against existing plans and issues such that we ensure our implementation is not a regression to previously
      done work". That doc states the gap in exactly this incident's terms: the daily sweeps "converge the corpus over
      time; they don't protect the next hour."

      **Why no detector, stated so this is not re-proposed**: (a) the detector's core test — does a later sibling doc
                      describe *the same work*? — is a semantic judgement a regex cannot make, and a dispatch-gating check with false
                      positives is one that gets ignored; (b) the realised cost was low and bounded — the reprocess is `--force`
                      idempotent on cheap SPOT, so the duplicate run corrupted nothing and in fact independently re-confirmed the
                      original run's stability with an identical residual-failure signature; (c) one observed occurrence, with the
                      preventing rule now in place. Weighed explicitly against the same-day precedent where an honor-system HARD RULE
                      *was* replaced with a mechanical enforcer
                      (`/plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md` → `resource-watchdog`):
                      that one had 4 recurrences in a week and each was a fleet-wide outage. The cost/recurrence profiles are not
                      comparable, and the proportionate answer differs.

                      **Known residual, accepted**: the codex rule specifies *what* to check but not *when*. In this incident the
                      worker did run the conflict check — but while writing its completion note, after the 4 VMs had already run. If
                      this class recurs on an expensive or non-idempotent action, the fix to reach for first is tightening that timing
                      for VM-launching / `--force` todos (a population `scripts/plan-hygiene/check_delete_vm_launch_gating.sh` already
                      identifies), not building the semantic detector declined here.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the single open `[BACKEND] P3` labels itself 'a design question
  for whoever owns backlog-regen, not a prescribed fix', and the body repeats it ('not scoped/executed here — a design
  question, not this todo's job… not proposing a specific mechanism here'). No mechanism is specified, so the outcome is
  not determinable by a worker alone — the dispatch-scope eligibility bar excludes it.
- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — re-stamp, unchanged. Confirmed via git that the
  only change since the 2026-07-30 marker is a mechanical `context_scope` frontmatter backfill (2026-08-03) — no content
  drift. Same reasoning holds: the sole open item is an explicitly-unscoped design question, not a bounded task.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — still accurate).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
