---
doc_type: issue
title:
  deployment-service consolidator-scheduler watcher carries stale DP-WATCHER-003 self-identity in its docstrings and log
  messages after its registry_id was bumped to DP-WATCHER-004
summary: >-
  The manifest-consolidator scheduler-paused watcher in deployment-service registers itself as
  `registry_id="DP-WATCHER-004"` (consolidator_scheduler_watcher.py:136) but still describes itself as "DP-WATCHER-003"
  in its module + class docstrings (consolidator_scheduler_watcher.py:1,15,71) and in several cli.py log lines
  (cli.py:87,498,516,835). Cosmetic stale-identity only — zero functional impact (the live registry_id is correct) — but
  it causes identity confusion when correlating logs/alerts to the registry. Confirmed by review (agt-86659c) and main
  (agt-26fe12) on 2026-07-31 to be tracked as a todo NOWHERE in plans/active/ (every corpus hit for DP-WATCHER-00[34] /
  consolidator_scheduler_watcher is historical build/fix narrative, not an open fix-todo). NOTE the fix is NOT a blind
  -003→-004 find-replace: cli.py:167 references DP-WATCHER-002 (a genuinely different sibling watcher,
  DP_CRON_DID_NOT_FIRE) and some -003 mentions may be legitimate cross-references to sibling keys — the fix must update
  only THIS watcher's stale self-identity, not sibling cross-references.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [deployment-service, data-pipeline-monitors, dp-watcher, stale-identity, cosmetic, docstring]
related: []
created: "2026-07-31"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
source: [review-role-finding-agt-86659c, main-orchestrator-triage-agt-26fe12]
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# What

`deployment-service/deployment_service/data_pipeline_monitors/consolidator_scheduler_watcher.py` registers the
manifest-consolidator scheduler-paused watcher as `registry_id="DP-WATCHER-004"` (line 136), but its own module
docstring (line 1), its maintenance-window comment (line 15), and its class docstring (line 71) still call it
**DP-WATCHER-003**. Several `cli.py` log lines carry the same stale label: `cli.py:87` ("KEY #2/DP-WATCHER-003"),
`cli.py:498` + `cli.py:516` (log messages "DP-WATCHER-003 off this sweep" / "skipping DP-WATCHER-003 this sweep"), and
the `cli.py:835` comment.

# Impact

Cosmetic only. The live `registry_id` is correct (`-004`), so alerting/registry correlation works; the stale strings
only mislead a human reading the source or logs into thinking this is watcher `-003`. No data loss, no functional
regression. Review observed a predecessor pinged a worker about this ~17h earlier; still unfixed on
origin/live-defi-rollout as of 2026-07-31 22:56Z.

# Fix direction (NOT a blind find-replace)

Update only THIS watcher's stale self-identity (the module/class docstrings + maintenance-window comment at lines
1/15/71 and the `cli.py` log lines/comments at 87/498/516/835 that describe the paused-scheduler watcher) from
`DP-WATCHER-003` to `DP-WATCHER-004` to match `registry_id`. **Do NOT** touch `cli.py:167`'s `DP-WATCHER-002` reference
(a different sibling watcher, `DP_CRON_DID_NOT_FIRE`), and verify each remaining `-003` mention is this watcher's own
identity and not a legitimate cross-reference to a sibling key before changing it.

# Follow-up todo

- [ ] [SCRIPT] P3. Reconcile the stale `DP-WATCHER-003` self-identity strings in
      `deployment-service/deployment_service/data_pipeline_monitors/consolidator_scheduler_watcher.py` (lines 1, 15, 71)
      and `.../cli.py` (lines 87, 498, 516, 835) to `DP-WATCHER-004` to match the registered `registry_id` (watcher line
      136). Do NOT alter `cli.py:167`'s `DP-WATCHER-002` (a different sibling watcher); before changing any `-003`
      mention, confirm it names THIS watcher and not a sibling cross-reference. Cosmetic/non-functional — no runtime
      behavior change expected; cite
      `plans/active/issues/dp_watcher_stale_003_identity_after_registry_id_bump_to_004_2026_07_31.md` in the commit.
