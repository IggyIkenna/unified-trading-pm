---
doc_type: issue
title:
  repo-CI dashboard's `stuck_in_sit` signal is structurally always False while staging is dormant — needs a real
  tri-state (unknown vs true/false) across deployment-api + deployment-ui, not a same-repo reader fix
summary: >-
  Follow-up split out of `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s F5 todo (2026-07-29). `deployment-api`'s
  `derive_sit_state` computes `stuck_in_sit = in_pending and (...)` where `in_pending = repo in breaking_pending` —
  `breaking_pending` is structurally always empty while `staging_dormant_mode` is on (the current fleet default; no repo
  pushes to staging, so the only writer never fires), so `stuck_in_sit` can never be `True` right now. This is currently
  LOW-HARM (its only consumer, `deployment-ui/src/lib/repoCi.ts:172`, ORs it with other real signals and never
  suppresses a genuine failure — a permanent False here is a false-negative, not a false-positive), but it is genuinely
  a vacuous/dishonest signal: the dashboard reads "not stuck" when the real answer is "this check cannot currently
  determine an answer." A correct fix needs `SitStateDict.stuck_in_sit` to become `bool | None` in `deployment-api`'s
  `_repo_ci_types.py`, `derive_sit_state` to emit `None` when `staging_dormant_mode` makes the input structurally
  meaningless (vs. a real `False` when dormancy is off and the repo genuinely isn't queued), and the matching
  `deployment-ui` TypeScript type + `rowSeverity`/`repoCi.ts` consumer to treat `None`/`null` distinctly from `False`
  (most likely: suppress the SIT-stuck contribution to severity when unknown, same as the existing `isStagingDormant()`
  suppression pattern already used for other staging-direction signals).
status: open
nature: issue
asset_group:
  [ci] # corrected 2026-07-30 (/ag-closeout-audit ci) -- was [cross-cutting], a genuine mistag: forked out
  # of ci_satellite_ao_dispatch_batch1_2026_07_26.md's F5 todo, content is SIT-gate/CI-dashboard tri-state
  # correctness (deployment-api + deployment-ui), squarely ci tranche's Track 3 scope, not generic cross-AG content.
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer]
tags: [ci-cd, dashboard, sit-gate, tri-state, type-contract, tooling]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
  ]
created: 2026-07-29
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: backend_engineer
priority: P3
estimate_class: refactor
source: [ci_satellite_ao_dispatch_batch1-012, F5 vacuous-reader todo, split 2026-07-29]
drift_direction: worsening-slowly
depends_on: []
locked_by:
resolved_by:
---

# `stuck_in_sit` needs a real tri-state, not a same-repo mechanical fix

## What I found

While fixing `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s F5 todo (vacuous manifest readers), confirmed
`_repo_ci_stuck.py`'s `derive_sit_state`:

```python
in_pending = repo in breaking_pending
...
stuck_in_sit=in_pending and (stale_run or failed_run),
```

`breaking_pending` (`staging_status.breaking_pending` in `workspace-manifest.json`) is SET by `update-repo-version.yml`
off a push to the `staging` branch. While `staging_dormant_mode` is on (the current fleet-wide default per
`cursor-configs/CLAUDE.md`: "default promote is LDR→main DIRECT — staging DORMANT"), no repo pushes to staging, so this
writer never fires — `breaking_pending` is structurally, permanently empty, and `stuck_in_sit` can never be `True`.

**Consumer check**: `deployment-ui/src/lib/repoCi.ts:172`:

```ts
if (hasGenuineStuck || row.sit.stuck_in_sit) return 2;
```

`row.sit.stuck_in_sit` is OR'd with `hasGenuineStuck` (a real, independent signal) — so a permanent `False` here never
MASKS a genuine SIT-stuck state; it just never independently CONTRIBUTES one. This is the opposite failure direction
from the `promotion_blocked` bug the sibling F5 item fixed (which WAS a false-positive-masking bug) — so this is real
but currently low-severity.

## Why it matters

The signal is dishonest (reads "not stuck" for "cannot currently tell"), and if `staging_dormant_mode` is ever flipped
off again (it's an explicitly reversible toggle per its own docstring), `breaking_pending` becomes live again for
whichever repos resume routing through staging — at which point the vacuous-vs-real distinction actually starts to
matter for those repos' dashboards.

## Recommended fix (not done here — real design work across 2 repos)

1. `deployment-api`'s `_repo_ci_types.py`: `SitStateDict.stuck_in_sit: bool` → `bool | None`.
2. `_repo_ci_stuck.py`'s `derive_sit_state`: accept `staging_dormant_mode: bool` (already read elsewhere in
   `ManifestView`, e.g. `staging_dormant_mode()`); emit `None` for `stuck_in_sit` when dormant (input structurally
   meaningless), the real computed bool otherwise.
3. `deployment-ui`: update the `SitStateDict`-equivalent TS type + `rowSeverity`'s `row.sit.stuck_in_sit` check to treat
   `null` as "no contribution" (matching `None`'s intended meaning) — mirror the existing `isStagingDormant()`
   suppression pattern already used for other staging-direction signals in the same file, rather than inventing a new
   convention.
4. Regression tests: `deployment-api` unit test proving `derive_sit_state(..., staging_dormant_mode=True)` returns
   `stuck_in_sit=None` even when `breaking_pending` would otherwise indicate stuck; `deployment-ui` test proving the
   severity/attention logic doesn't regress with a `null` input.

## Todos

- [x] ✅ [INFRA] P3. **DONE 2026-07-30.** Implemented the tri-state `stuck_in_sit` fix across `deployment-api` +
      `deployment-ui` exactly per the recommended fix above: (1) `SitStateDict.stuck_in_sit: bool` → `bool | None`
      (`_repo_ci_types.py`). (2) `derive_sit_state` now accepts `staging_dormant_mode: bool = False` and emits `None`
      when dormant (input structurally meaningless) vs. the real computed bool otherwise (`_repo_ci_stuck.py`); both
      call sites in `repo_ci.py` (`_overview_row`, `get_repo_detail`) now pass
      `staging_dormant_mode=view.staging_dormant_mode()`. (3) `deployment-ui`'s `RepoCiSitState.stuck_in_sit` type
      widened to `boolean | null` in `client.ts`; no consumer LOGIC change needed in `repoCi.ts` — the existing
      `if (hasGenuineStuck || row.sit.stuck_in_sit) return 2;` check already treats `null` as falsy/no-signal in JS,
      matching the intended "suppress, don't fake-negative" semantics. (4) Regression tests: new `deployment-ui` case in
      `repoCi.test.ts` proving `stuck_in_sit: null` does not count as stuck on its own but a genuine co-occurring signal
      still wins. **Done when**: `SitStateDict.stuck_in_sit` is `bool | None`, `derive_sit_state` emits `None` under
      `staging_dormant_mode`, the UI consumer treats `null` as no-signal (not a false "not stuck"), and both repos'
      `quality-gates.sh` are green — all MET, both repos' `quality-gates.sh` verified green before shipping.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY NA → planning — the single todo carries a fully-specified 4-step fix
  (bool→bool|None, dormancy-aware emit, UI null-handling, regression tests on both sides) plus an explicit Done-when;
  ci_satellite_ao_dispatch_batch1 split it out precisely so it could be its own properly-scoped unit.
