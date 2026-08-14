---
doc_type: issue
title: >-
  DP_VM_STALL relaunch for `mtds-backfill-odds-smallchunk10-20260809` (agt-adfeaf) blocked by a cross-launcher-family
  relaunch-budget collision bug (fixed) — underlying VM has independently failed OOM twice today (unresolved)
summary: >-
  Dispatched as the `data_pipeline_failure` worker for escalation `agt-adfeaf` (DP-VM-003 `DP_VM_STALL`, repo
  `deployment-service`) to relaunch `mtds-backfill-odds-smallchunk10-20260809` via
  `launch-mtds-sports-odds-backfill-vm.sh`. Found + fixed a genuine root-cause bug before ever reaching the relaunch:
  `relaunch_stalled_vm.vm_prefix()` / `relaunch_backfill_vm.vm_prefix()` keyed the `_MAX_RELAUNCHES_PER_DAY=2` budget on
  a naive first-hyphen-segment of the VM name (e.g. `"mtds"`) instead of the registered launcher-family prefix (e.g.
  `"mtds-backfill-odds-"`), despite both functions' own docstrings claiming to mirror
  `vm_zombie_watchdog.VM_PREFIX_TO_BUCKET`'s (multi-segment) keying. Confirmed live: `/tmp/uts_stalled_relaunch_budget/
  mtds.json` already read `{"day": "2026-08-09", "count": 2}` — exhausted by OTHER, unrelated `mtds-*` VM families
  relaunching today — while `mtds-backfill-odds-` itself had never used its own budget. Fixed in both files (longest-
  prefix match against `VM_PREFIX_TO_BUCKET`, same registry the docstrings always intended), shipped
  `deployment-service@6e6f509f` (quality-gates.sh green, targeted tests + full suite pass, post-push ancestry verified
  on `origin/live-defi-rollout`). Separately (NOT fixed by the above): `DeploymentsRegistry.list_recent_archive()` shows
  this exact VM shard already failed TWICE today independently of my dispatch — `07:53:36-13:10:02Z` (exit_code 125) and
  `17:21:07-17:40:02Z` (exit_code 1, following an internal `chunk=1/435 league=BUNDESLIGA ... exit=137
  reason=OOM_KILLED`, RSS climbing ~5GiB→~29.6GiB in under 90s against the launcher's `MACHINE_TYPE=e2-highmem-4`
  default) — both exit codes are non-137 at the VM level, so `RelaunchBackfillVm`'s own OOM path (`exit_code==137` only)
  would have SKIPPED them (`reason=not_oom`) and fallen through to the page-tier rather than auto-recovering. No VM has
  run for this shard since 17:40Z (>3h stale as of this session). Given the runbook's own "re-fails the same way twice →
  STOP relaunching, diagnose root cause" rule, and given `CHUNK_SIZE=5` (the launcher's already-reduced default, set
  after a PRIOR OOM incident on this exact launcher) still OOM'd on a single BUNDESLIGA/`odds_api` chunk, I did **not**
  perform a third blind relaunch — filing this issue + paging the operator per the NEEDS-A-HUMAN-DECISION protocol
  instead of guessing between "resize the machine up" and "there's a real memory-growth bug in the odds_api fetch path"
  (`market-tick-data-service`'s own `RelaunchBackfillVm` docstring explicitly calls machine resize "the human call").
status: open
nature: issue
asset_group: [sports, cross-cutting]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [dp-vm-stall, relaunch-budget, oom, mtds, odds-api, sports, escalation]
related: [/codex/15-runbooks/incidents/rb_infra_relaunch.md, /codex/05-infrastructure/data-pipeline-alerts.md]
created: "2026-08-09"
author: data_pipeline_failure-worker-slot5
parent_epic: infrastructure_master
resolved_by:
locked_by:
locked_since:
source: >-
  Dispatched as escalation agt-adfeaf (DP-VM-003 DP_VM_STALL, repo deployment-service, authoring_slot=dp-fleet-monitor)
  per RB-INFRA-RELAUNCH.
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
    deployment-service/scripts/recovery/relaunch_stalled_vm.py,
    deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh,
    market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py,
  ]
---

# `mtds-backfill-odds-smallchunk10-20260809` relaunch — budget bug (fixed) + unresolved OOM root cause

## What I found

1. **Relaunch budget cross-contamination bug (FIXED, shipped).** `relaunch_stalled_vm.py`'s and
   `relaunch_backfill_vm.py`'s `vm_prefix(vm_name)` returned `vm_name.split("-", 1)[0]` — for
   `mtds-backfill-odds-smallchunk10-20260809` that's `"mtds"`, a bucket shared by every `mtds-*` launcher family
   (`mtds-live-cefi-consolidated-`, `mtds-dex-swaps-backfill`, `mtds-prediction-`, `mtds-backfill-odds-`, ...). The real
   `VM_PREFIX_TO_BUCKET` registry (`deployment_service/vm_prefix_registry.py`, the SSOT both docstrings claimed to
   mirror) keys on the FULL multi-segment prefix. Live evidence at dispatch time:
   `/tmp/uts_stalled_relaunch_budget/mtds.json` = `{"day": "2026-08-09", "count": 2}` (budget exhausted) while
   `mtds-backfill-odds-` had never used its own budget — an unrelated VM family's relaunches were blocking mine.
2. **The underlying VM has independently failed twice today (NOT fixed by the above; separate concern).**
   `DeploymentsRegistry.list_recent_archive(days=3)` for `mtds-backfill-odds-smallchunk10-20260809`:

   | deployment_id  | started_at (UTC) | completed_at (UTC) | exit_code | notes                                                                                                                                                                                                                                 |
   | -------------- | ---------------- | ------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | `b5742639-...` | 07:53:36         | 13:10:02           | 125       | log overwritten by the later run, root cause not directly visible                                                                                                                                                                     |
   | `52467378-...` | 17:21:07         | 17:40:02           | 1         | `run.log` shows `CHUNK_FAILED: chunk=1/435 league=BUNDESLIGA range=2020-08-29→2020-09-02 exit=137 reason=OOM_KILLED` at 17:32:07Z — RSS samples climbed 17667MiB→20153MiB→29628MiB in the ~90s leading up to it, cpu pinned ~100-180% |

   `launch-mtds-sports-odds-backfill-vm.sh` defaults `MACHINE_TYPE=e2-highmem-4` and `CHUNK_SIZE=5` — the latter already
   reduced from an original default of 250 after a prior OOM incident on this same launcher (per the script's own inline
   comment: "CHUNK_SIZE=250 hit 15 OOM-kills in ~80min vs ... CHUNK_SIZE=5 ... hit only 2"). Even at the already-reduced
   `CHUNK_SIZE=5`, a single chunk (one league, 5-day range) OOM-killed a `e2-highmem-4` VM. Both observed VM-level exit
   codes (125, 1) are non-137, so `RelaunchBackfillVm`'s exit-code-fleet-monitor OOM path (`exit_code == 137` only)
   would classify these `not_oom` → `SKIPPED` → falls to the page-tier, NOT the automatic resize-up/relaunch path — i.e.
   the system's own design does not auto-recover this failure shape either.

3. **Secondary, non-blocking finding**: `run.log` shows repeated
   `WARNING firestore dual-write ... failed (best- effort, GCS authoritative): 403 Missing or insufficient permissions`
   for the deployment-registration heartbeat. Explicitly best-effort (GCS stays authoritative) and not implicated in the
   crash — noting for visibility, not chasing further in this session.

No VM has run for this shard since 17:40:02Z (>3h stale as of 2026-08-09T~21:00Z when I checked) — this is not a
currently-stalled/hung process; the last real attempt already terminated.

## Why it matters

- The budget-collision bug (item 1) is a real cross-cutting correctness gap: ANY `mtds-*`-prefixed VM stall/OOM relaunch
  could have silently exhausted the shared `"mtds"` bucket and blocked an unrelated shard's legitimate relaunch — this
  was actively happening to my dispatch. Now fixed for both actuators.
- The unresolved OOM (item 2) means `mtds-backfill-odds-smallchunk10-20260809`'s work (SPORTS odds_api backfill,
  `2020-08-29`-earliest chunk onward for the affected leagues) is NOT progressing and won't progress from a bare
  relaunch — the runbook's own "re-fails the same way twice → STOP, diagnose root cause" threshold is already met by the
  two independent failures above, so I did not attempt a third blind relaunch (would very plausibly repeat the same OOM
  on the same BUNDESLIGA chunk or a similarly memory-heavy one further down the 435-chunk queue).

## Recommended decision

Two independent paths, not mutually exclusive:

- **A [WORKER REC — quick mitigation]**: bump `MACHINE_TYPE` for this launcher one tier up (e.g. `e2-highmem-4` →
  `e2-highmem-8`) and relaunch. Bounded, mechanical, reversible — but the `RelaunchBackfillVm` docstring explicitly
  frames a resize as "the human call," so deferring the actual bump to operator sign-off rather than self-servicing it
  blind.
- **B [deeper fix]**: investigate why a single `odds_api` BUNDESLIGA chunk (5-day range) drives RSS from ~5GiB to
  ~29.6GiB in under 90 seconds even at the already-reduced `CHUNK_SIZE=5` — that growth rate is fast enough to suggest
  unbounded accumulation (e.g. a pagination/response-buffering bug in the odds_api fetch path) rather than genuinely
  large legitimate payload, which a machine resize alone would only postpone, not fix, for the remaining ~434 chunks.
  This is in `market-tick-data-service`, not `deployment-service` — out of this dispatch's bounded scope to chase
  synchronously.

## Todos

- [x] ✅ [SCRIPT] P1. Fix `vm_prefix()` in `relaunch_stalled_vm.py` + `relaunch_backfill_vm.py` to longest-prefix-match
      `VM_PREFIX_TO_BUCKET` instead of a naive first-hyphen split; update `test_vm_prefix_keying` for the corrected
      expected value. Repo: deployment-service. — **deployment-service@6e6f509f** (Quickmerge, verified ancestor of
      `origin/live-defi-rollout`): targeted `test_dp_recovery_actuators.py` tests (11/11, `vm_prefix`/
      `stalled_relaunch` selection) + full `quality-gates.sh` green, sentinel=6e6f509f.
- [ ] [OPERATOR] P2. Decide + apply path A (machine-type resize for `launch-mtds-sports-odds-backfill-vm.sh`) and/or
      dispatch path B (investigate the odds_api BUNDESLIGA memory-growth root cause in market-tick-data-service) for
      `mtds-backfill-odds-smallchunk10-20260809` (and any sibling `smallchunk*` shards hitting the same pattern —
      `smallchunk12/13/14` are also in-flight/recent per the registry, worth a quick cross-check once path B lands).
      Once decided, relaunch via `RelaunchStalledVm`/`RelaunchBackfillVm` — the budget-collision bug no longer blocks it
      (fixed above, `mtds-backfill-odds-` bucket currently at 0/2 today).

## Progress Log

- **2026-08-09**: Filed by the `data_pipeline_failure` worker (slot 5) dispatched for escalation `agt-adfeaf`. Found +
  fixed the relaunch-budget cross-contamination bug inline (todo 1). Did not perform the VM relaunch itself — the
  underlying shard has independently OOM'd twice today at the launcher's already-reduced `CHUNK_SIZE=5` safeguard,
  meeting the runbook's "re-fails the same way twice" stop condition; paging the operator (todo 2) rather than guessing
  between a machine resize and a deeper odds_api memory-growth investigation.

- **2026-08-09T21:52Z (`data_pipeline_failure` worker, slot 4, ALSO dispatched for `agt-adfeaf` — a 3rd concurrent
  dispatch for the same escalation)**: had not read this doc before acting (process gap — see the full account in
  `/plans/active/issues/mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`'s matching entry). Relaunched
  `smallchunk10` a 3rd time from GCS-recovered `LAUNCH_PARAMS.json`/checkpoint (same `start_date=2020-08-29` as both
  prior attempts here); it hung again ~2 min into real work, this time via the OTHER doc's tracked silent-hang signature
  (not OOM) — a 3rd independent failure, now spanning both known failure modes for this exact shard. Deleted the wedged
  instance after ~13 min of confirmed non-progress. Confirmed the main campaign (`smallchunk2→14` lineage, tracked in
  the sibling doc) is healthy and unaffected, currently `smallchunk14`, fresh heartbeat. Bumped the local
  relaunch-budget sentinel to today's cap (blocks a reflexive 4th auto-relaunch). Does not resolve todo 2 below — adds a
  3rd data point (now via a different failure mode) supporting the same "don't blindly relaunch again" conclusion, plus
  a path-C suggestion (abandon `smallchunk10` specifically rather than resize/investigate it, since the main lineage
  already covers its date range) in the sibling doc's new entry.
- **2026-08-12 (operator, interactive session)**: ruled option (2) investigate the odds_api bug rather than
  resize/abandon. Investigation found the "BUNDESLIGA memory growth" framing was a mislabel -- the OOM recurs across
  nearly every league (EPL, LA_LIGA, SERIE_A, LIGUE_1, EREDIVISIE, etc.), already under 15+ sessions of investigation in
  `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` since 2026-07-22, with the Python heap already ruled out via
  tracemalloc; the real next step (a `memray --native` VM run) remains blocked on cost, unchanged by this session. While
  investigating, found and fixed a real, previously-undocumented, separate bug: `odds_api_adapter.py`'s
  `_fetch_all_leagues` matched a `--league` request by canonical-id-OR-raw-name, so `--league BUNDESLIGA` (Germany,
  api_football_id=78) also silently fetched Austria (raw name "Bundesliga" too, api_football_id=218) -- doubling
  fetch/memory/credit cost for that pairing and defeating the 2026-08-06 per-league VM isolation for it. Same collision
  pattern affects Serie A/Brasileirao, Serie B/Brasileirao-Serie-B, Championship/Scottish-Championship, Primera-Division
  Argentina/Chile, and the 3-way Super-League Greece/Switzerland/China. Fixed: canonical-id matching now takes priority,
  raw-name is fallback-only for non-canonical requests -- `market-tick-data-service@719e4d0dd1` (10 new regression
  tests, full quality-gates.sh green). Does not close this todo -- the general OOM root cause is still open, only this
  additive amplifier is fixed.

**context-scout 2026-08-14**: populated context_scope (5 entries)
