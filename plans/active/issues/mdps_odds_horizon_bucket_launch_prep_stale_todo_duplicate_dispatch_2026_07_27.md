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
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, issue-doc-lifecycle, duplicate-work, backlog-regen, stale-todo, sports, mdps, vm-launcher]
related:
  [
    /plans/archive/issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md,
    /plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md,
    /plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-07-27
assigned_vm: NA
parent_epic: orchestrator_master
execution_scope: local-only
priority: P2
estimate_class: refactor
source: mdps_odds_horizon_bucket_reprocess_launch_prep-001 (slot 9, 2026-07-27) — discovered mid-task, after launch
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

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

- [ ] [BACKEND] P3. Consider whether `regen_backlog_from_plan.py` / the issue-doc-lifecycle sweep can catch an issue doc
      whose own todo is stale-open while a `related:`-linked sibling doc (created later) already records the same work
      done — a design question for whoever owns backlog-regen, not a prescribed fix. (repo: unified-trading-pm)
