---
doc_type: issue
title:
  "Parked findings from the 2026-08-06 /ag-closeout-audit cross-cutting run (4 asset_group mistags — genuine content is
  ui/ui-or-sports/infrastructure/infrastructure, 2 of the 4 already fully resolved — found via the Phase 1 Workflow's
  step-5 scope sanity-check, not retagged per the concurrent-sharded-worker owning-tranche rule)"
summary: >-
  4 NEW mechanically-verified `asset_group` mistags surfaced by the 2026-08-06 `/ag-closeout-audit cross-cutting` run
  (scheduled daily run, dispatch `agt-681f2d`, slot 6) — a 4-day gap since the last run (2026-08-02). Phase 0
  (`generate_ag_closeout_audit_candidates.py --tranche cross-cutting`) measured 86 tranche members and 6 never-cited
  candidates before this session's retags, 83/4 after. A Phase 1 `Workflow` (6 agents) classified all 6: **all 6
  verdicted `exclude_cross_cutting`** — zero genuine new cross-cutting orphans this run, no Phase 3 batch draft
  warranted (matches the 2026-08-02 run's outcome). Of the 6, **2 were fixed DIRECTLY this run** (both resolve to
  dropping the `cross-cutting` tag while an already-present sibling tag remains — safe per precedent, no write into a
  different tranche's namespace): `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` ([defi, cross-cutting]
  -> [defi]) and `qg_v2_fleetwide_workflow_file_issue_regression_2026_08_05.md` (archived 2026-08-06, [cross-cutting,
  ci] -> [ci]). The remaining **4 are parked here** (each needs a tag ADDED that isn't currently present, i.e. real
  ownership by a DIFFERENT tranche — per the 2026-07-30 concurrent-sharded-worker rule, that write belongs to the owning
  tranche's own audit, not this run): `deployment_api_quickmerge_blocked_pre_existing_test_failures_2026_08_04.md` (real
  owner `ui`, with a `sports` sub-component on todo 2; all 3 todos genuinely open and AO-eligible once retagged),
  `shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md` (real owner `infrastructure`; a dedicated
  na-eligibility-audit already ruled KEEP-NA — operator-direction-gated, not AO-eligible as-is),
  `unified_trading_system_ui_block_list_parity_test_failing_2026_08_04.md` (real owner `ui`; **bonus finding** — live
  git evidence shows the sole remaining todo is very likely ALREADY RESOLVED on `origin/main` as an incidental
  side-effect of an unrelated GMX-venue-removal fix, `unified-trading-system-ui@3c2efb2c` — needs verify-and-archive,
  not a fresh fix), and `resource_watchdog_host_guardian_2026_08_05.md` (real owner `infrastructure`; **bonus finding**
  — this doc has ZERO remaining open work of its own, self-declares "ready for archival once deploy is verified" in its
  own Deferred section, and its one live follow-up was already forked into a separate, already-archived-and-complete
  plan — it should be retagged AND run through the standard archival ritual, not treated as an orphan needing new work).
  Separately, this run's Orthogonality HARD CHECK (corpus-wide, not limited to the 6 Phase-1 candidates) found and fixed
  2 MORE genuine dual-tag mistags: `vm_exec_stall_watchdog_checkpoint_regex_mismatch_2026_08_03.md` ([defi,
  cross-cutting] -> [cross-cutting], kept in cross-cutting — verified via a 20-launcher grep that the underlying
  `vm-exec-with-gcs-tee.sh` stall-watchdog bug is genuinely cross-AG, not defi-specific; required a follow-up
  `check_ag_closeout_linkage.py`-driven citation fix in Track 14 of the consolidated closeout to avoid creating a fresh
  linkage-gate orphan) and `defi_manifest_column_fill_regression_from_gmx_purge_forced_full_merge_2026_08_04.md` ([defi,
  cross-cutting] -> [defi], dropped — per the established `sports_cf8` precedent, a shared-guardrail-mechanism incident
  that fires on ONE bucket is tagged to that bucket's AG alone, not cross-cutting). One more dual-tag hit,
  `over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md` ([defi, cross-cutting], `parent_epic:
  plan_hygiene_master`), was investigated and found to be a mistag on BOTH counts (real home is likely `ci`/`infra`
  plan-hygiene-tooling territory, not cross-cutting) — parked below rather than retagged, since the correct owner is
  ambiguous between two OTHER tranches, not cross-cutting itself. Iterative-drain re-check of batch1/1b/3's Deferred
  sections found one genuine clearance since 2026-08-02:
  `plans/active/issues/manifest_v6_batch3_residual_orphaned_work_2026_07_21.md`'s time-gated `gate_on_depends` block
  cleared 2026-08-03 (its blocking dependency archived resolved) and the doc self-dispatched via a separate
  na-eligibility-audit reclassify pass — batch1's Deferred section updated in place to record this, no fresh batch todo
  needed since the doc already covers itself.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cross-cutting, ag-closeout-audit, asset-group-mistag, parked-findings, orthogonality]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_01.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_cross_cutting_parked_2026_08_02.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
author: unknown
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: >-
  `/ag-closeout-audit cross-cutting` run 2026-08-06 (ag_closeout_auditor scheduled worker, dispatch `agt-681f2d`, slot
  6). Phase 0 via `generate_ag_closeout_audit_candidates.py --tranche cross-cutting` (86 members, 6 covering docs, 6
  never-cited). Phase 1 Workflow (6 agents) classified all 6 `exclude_cross_cutting`; 2 fixed directly, 4 parked here.
context_scope:
  [
    /plans/archive/issues/deployment_api_quickmerge_blocked_pre_existing_test_failures_2026_08_04.md,
    /plans/active/issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md,
    /plans/active/issues/unified_trading_system_ui_block_list_parity_test_failing_2026_08_04.md,
    /plans/active/issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# Parked findings — 2026-08-06 `/ag-closeout-audit cross-cutting` run

## New findings this run

### 1. `plans/archive/issues/deployment_api_quickmerge_blocked_pre_existing_test_failures_2026_08_04.md` — likely real owner `ui` (+ `sports` sub-component)

**Doc state**: `status: open`, `asset_group: [cross-cutting]`, `repos: [deployment-api]`, `priority: P1`. 3 open todos,
none resolved.

**Why not cross-cutting**: all 3 remaining todos live entirely inside `deployment-api` and are either single-AG-specific
or CI/CD mechanics, never spanning multiple asset groups' data-pipeline surfaces: (1) a CEFI-venue `_venue_to_category`
mapping bug (`OKX` returning `None`) in `data_query_service.py`; (2) a SPORTS-asset-group registry-count regression
(`SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES` grew 30→34 vs a 2026-07-30 operator ruling); (3) a re-ship
of an already-tested VM-classification fix through quickmerge, blocked on (1)+(2) clearing first. Zero coverage found in
any of the 6 cross-cutting covering docs by basename or by any of the specific bug-signal terms (function/constant/test
names); the only corpus mention is a one-line "blocked on this issue" cross-reference in an unrelated
`ci`/`infrastructure`-tagged plan, which doesn't touch any of the 3 todos itself.

**Recommendation [WORKER REC]**: retag `asset_group: [cross-cutting]` → `[ui]` (dominant — repo, both broken tests, and
the re-ship target all live in deployment-api) with a `sports` cross-reference note on todo 2. All 3 todos are bounded,
worker-determinable (each has an explicit test-passing gate) — genuinely AO-eligible once retagged, not just a
retag-only finding.

### 2. `plans/active/issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md` — likely real owner `infrastructure`

**Doc state**: `status: open`, `asset_group: [cross-cutting]`, `parent_epic: infrastructure_master`. 3 open `[INFRA]`
todos framed as "two independent fix directions, either or both."

**Why not cross-cutting**: a shared-host `gcloud` global mutable `core/account` state hazard that breaks ANY concurrent
`gcloud` invocation regardless of asset group or pipeline layer — not a data-pipeline concern spanning
IS/MTDS/features-service/manifest/UAC/UTL. `estimate_class: infra`, `assigned_role: infra`, all 3 `related` SSOTs live
under `codex/05-infrastructure/`. It was merely discovered/re-confirmed while running sports and prediction pipeline
checks — incidental trigger contexts, not evidence of cross-AG scope. Zero coverage found in any of the 6 cross-cutting
covering docs (basename + every content-signal term, e.g. `clobber`, `CLOUDSDK_CORE_ACCOUNT`, `per-tab-worktrees`).

**Recommendation [WORKER REC]**: retag `asset_group: [cross-cutting]` → `[infrastructure]`. **Not AO-eligible as-is**: a
dedicated na-eligibility-audit (2026-08-04, re-verified unchanged 2026-08-06) already ruled this KEEP-NA — the two fix
directions (pin `gcloud` identity per-invocation in the launcher-script family vs. give each slot its own named `gcloud`
configuration wired into shared bootstrap tooling) are both shared-blast-radius infra changes needing an operator
direction call first, not a worker-determinable outcome as currently scoped. Trust that prior assessment; don't
re-litigate it here.

### 3. `plans/active/issues/unified_trading_system_ui_block_list_parity_test_failing_2026_08_04.md` — likely real owner `ui`; bonus finding: probably already resolved on `main`

**Doc state**: `status: open`, `asset_group: [cross-cutting]`, `repos: [unified-trading-system-ui]`, `priority: P2`. 1
open `[UI]` todo.

**Why not cross-cutting**: single-repo (`unified-trading-system-ui`), single-file test-parity drift between one TS
module (`lib/architecture-v2/block-list.ts`) and one codex doc (`block-list.md`) — a strategy-archetype registry, not a
data-pipeline artifact, and it doesn't span asset groups. The doc's own todo is self-tagged `[UI]`. Zero coverage found
in any of the 6 cross-cutting covering docs or anywhere else in the corpus by filename.

**Bonus finding — likely already fixed, unlinked**: live git verification (read-only, in the local
unified-trading-system-ui clone) found the failing CI run (30896404779) this issue is built on tested a STALE `main`
commit (`633abcf4`, an LDR→main promote from 2026-08-03 — a full day before the fix existed);
`git show 633abcf4:lib/architecture-v2/block-list.ts` genuinely has only 10 `BL-` entries, confirming the reported
failure was real at that commit. But a same-day, differently-scoped `defi`-tagged issue doc's "Fifth pass"
GMX-venue-removal work added the missing `BL-12` entry to BOTH `block-list.ts` and
`/codex/09-strategy/architecture-v2/block-list.md` (shipped `unified-trading-system-ui@3c2efb2c`) with zero awareness of
this parity-test issue. Current `origin/main` (2026-08-05 21:07 UTC promote) has the identical 11-id set
`{BL-1..BL-10, BL-12}` in both files — exactly the pass condition for all 4 assertions in `block-list-parity.test.ts`
(read directly, not assumed). `vitest` itself was not executed (would require a worktree/npm-install detour on a shared
slot clone, out of scope for a read-only classification task), so this is strong git-content-level evidence, not a
runtime-verified close.

**Recommendation [WORKER REC]**: retag `asset_group: [cross-cutting]` → `[ui]`. Whoever picks this up (ui tranche or
operator) should VERIFY (`vitest run block-list-parity.test.ts`) and ARCHIVE citing the `3c2efb2c` evidence, not
schedule a fresh fix-dispatch.

### 4. `plans/archive/2026_08/resource_watchdog_host_guardian_2026_08_05.md` — likely real owner `infrastructure`; bonus finding: archival-ready, not orphaned

**Doc state**: `status: active`, `asset_group: [cross-cutting]`, `parent_epic: infrastructure_master`. All 4 phases'
checkboxes `[x]`.

**Why not cross-cutting**: a host/VM resource-protection daemon for the orchestrator/planning VM (cgroup memory
monitoring, per-process RSS/CPU/swap thresholds, systemd unit, allowlist, AO kill-relay) — infra content, never touches
IS/MTDS/features-service/manifest/UAC/UTL. All `related` SSOTs live under `codex/05-infrastructure/`.

**Bonus finding — already archival-ready**: the doc's own "Deferred work after 2026-08-05" section states verbatim "All
Phase 4 hardening items completed. No deferred work remaining. Plan is ready for archival once deploy is verified." The
newest Progress Log entry confirms live verification (SIGTERM'd two real 40GB runaway processes from slot 15); an inline
log-rotation gap was fixed the same entry; the one substantive follow-up (surfacing kill events through
deployment-api/deployment-ui) was forked into its own plan
(`/plans/archive/2026_08/watchdog_kill_events_deployment_observability_2026_08_05.md`), already archived
`status: complete` with all 7 todos `[x]` and its gated finalize plan also all `[x]`. A further-downstream residual
(`plans/active/issues/watchdog_kill_events_deployment_gaps_2026_08_05.md`, `[cross-cutting, meta]`-tagged, 1 remaining
`[OPERATOR]` todo) is a child of the FORKED plan, not of this target doc — evaluate it separately on its own merits.

**Recommendation [WORKER REC]**: retag `asset_group: [cross-cutting]` → `[infrastructure]` AND run the standard 6-step
archival ritual — it has been sitting `status: active` despite being self-declared archival-ready, past its deploy
verification.

### 5. `plans/active/issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md` — mistagged on BOTH axes, likely real owner `ci` or `infra`

**Doc state**: `status: open`, `asset_group: [defi, cross-cutting]` (dual-tag, found via this run's corpus-wide
Orthogonality HARD CHECK, not the Phase-1 candidate list), `parent_epic: plan_hygiene_master`.

**Why neither defi nor cross-cutting**: content is a `check_line_caps.sh`-vs-plan-hygiene-tooling gate-interaction bug
(an over-cap LIVE plan can never carry its own verdict marker, so `/na-eligibility-audit`, `/plan-reconcile`,
`/ag-closeout-audit`, and `/context-scout` all re-read it in full forever) — a corpus-hygiene TOOLING mechanics finding,
not defi-specific (the defi doc `lst_rate_honest_coverage_2026_07_21.md` is only the triggering example that surfaced
the bug) and not cross-cutting's data-pipeline scope either. `parent_epic: plan_hygiene_master` maps to `ci`/`infra`
territory per this skill's own classification-mechanism section (`plan_hygiene_master` is one of the epics `ci`/`infra`
split, not one of cross-cutting's 5 data-relevant epics).

**Recommendation [WORKER REC]**: retag `asset_group: [defi, cross-cutting]` → `[ci]` or `[infrastructure]` (ambiguous
between the two from content alone — needs whichever tranche's own audit to make the final call; the `defi` tag is
confidently wrong, dropped either way). Not retagged directly here since BOTH current tags are wrong and the correct
owner is a genuinely different third tranche, not cross-cutting relinquishing its own claim.

## Fixed directly this run (not parked — see summary for full detail)

- `plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`: `[defi, cross-cutting]` → `[defi]`.
- `plans/archive/2026_08/issues/qg_v2_fleetwide_workflow_file_issue_regression_2026_08_05.md`: `[cross-cutting, ci]` →
  `[ci]` (archived 2026-08-06).
- `plans/active/issues/vm_exec_stall_watchdog_checkpoint_regex_mismatch_2026_08_03.md`: `[defi, cross-cutting]` →
  `[cross-cutting]` (kept — genuinely cross-AG, verified via a 20-launcher grep of `vm-exec-with-gcs-tee.sh` callers).
- `plans/active/issues/defi_manifest_column_fill_regression_from_gmx_purge_forced_full_merge_2026_08_04.md`:
  `[defi, cross-cutting]` → `[defi]` (per the `sports_cf8` bucket-specific-incident-vs-shared-guardrail-mechanism
  precedent).

All 4 direct fixes drop-or-keep only cross-cutting's own tag with an already-present sibling tag remaining — no write
into a different tranche's namespace, consistent with the 2026-07-30 concurrent-sharded-worker rule.

## Todos

- [ ] [DOCS] P3. Retag
      `plans/archive/issues/deployment_api_quickmerge_blocked_pre_existing_test_failures_2026_08_04.md`'s `asset_group`
      `[cross-cutting]` → `[ui]` (finding 1) — owning-tranche fix, leave to the `ui` tranche's own audit. Done when: the
      tag is corrected, the doc is folded into `ui_consolidated_closeout_2026_07_30.md`'s membership, and its 3
      AO-eligible items are considered for that tranche's next batch.
- [ ] [DOCS] P3. Retag `plans/active/issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md`'s
      `asset_group` `[cross-cutting]` → `[infrastructure]` (finding 2) — owning-tranche fix, leave to the `infra`
      tranche's own audit. Done when: the tag is corrected and the doc is folded into
      `infra_consolidated_closeout_2026_07_25.md`'s membership. Remains KEEP-NA (operator-direction-gated) per the
      2026-08-04 na-eligibility-audit ruling — a retag does not change its dispatch eligibility.
- [ ] [DOCS] P3. Retag `plans/active/issues/unified_trading_system_ui_block_list_parity_test_failing_2026_08_04.md`'s
      `asset_group` `[cross-cutting]` → `[ui]` (finding 3) — owning-tranche fix, leave to the `ui` tranche's own audit.
      Done when: the tag is corrected AND the doc is verified (`vitest run block-list-parity.test.ts` green on current
      `main`) + archived citing `unified-trading-system-ui@3c2efb2c` as the incidental-fix evidence — not re-dispatched
      as a fresh fix.
- [x] [DOCS] P3. ✅ Retag `resource_watchdog_host_guardian_2026_08_05.md`'s `asset_group` `[cross-cutting]` →
      `[infrastructure]` (finding 4) AND run the standard 6-step archival ritual —
      unified-trading-pm@na-eligibility-audit 2026-08-06. Re-evaluated the "leave to the infra tranche" deferral: since
      the doc's `asset_group` was `[cross-cutting]` ONLY (single-tranche membership, confirmed via
      `generate_na_doc_tranche_inventory.py`), no `infra`-tranche na-eligibility-audit run would ever have surfaced it —
      deferring indefinitely would have meant it was never picked up. Executed directly instead (self-contained
      evidence, no genuine judgment call blocking it): retagged, banner added, moved to
      `/plans/archive/2026_08/resource_watchdog_host_guardian_2026_08_05.md`, all 6 corpus referrers fixed. See that
      doc's own Progress Log for the full ritual trail.
- [ ] [DOCS] P3. Retag `plans/active/issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md`'s
      `asset_group` `[defi, cross-cutting]` → `[ci]` or `[infrastructure]` (finding 5, owning tranche TBD by content) —
      leave to whichever of those two tranches' own audit claims it first. Done when: the tag is corrected to a single
      real tranche and the doc is folded into that tranche's closeout membership.

## Progress Log

- **2026-08-06** — `/ag-closeout-audit cross-cutting` run (autonomous, scheduled daily run, dispatch `agt-681f2d`, slot
  6, 4-day gap since the 2026-08-02 run). Phase 0: `generate_ag_closeout_audit_candidates.py --tranche cross-cutting`
  (86 members, 6 covering docs, 6 never-cited — all created 2026-08-04/05, after the last run's snapshot). Iterative-
  drain re-check of batch1/1b/3's Deferred sections: 1 genuine clearance found
  (`manifest_v6_batch3_residual_orphaned_work_2026_07_21.md`'s time-gated block cleared 2026-08-03, batch1's Deferred
  section updated in place); the remaining ~18 conflict/operator/ time-gated items spot-checked (no operator rulings
  logged since 2026-07-25, no status changes on the sampled docs) — unchanged. Orthogonality HARD CHECK (corpus-wide
  `asset_group:.*cross-cutting` dual-tag grep, not just the 6 Phase-1 candidates): found and fixed 2 genuine mistags
  directly (`vm_exec_stall_watchdog_checkpoint_regex_mismatch_2026_08_03.md`,
  `defi_manifest_column_fill_regression_from_gmx_purge_forced_full_merge_2026_08_04.md`), found 1 more
  mistag-on-both-axes parked as finding 5 (`over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md`), confirmed
  the rest of the dual-tag hits are legitimate multi-AG coordination docs (unchanged from 2026-08-01/02's clean re-runs)
  or already- corrected comment-only false positives. The `vm_exec_stall_watchdog` fix required a follow-up
  `check_ag_closeout_linkage.py` fix (added a Track 14 citation in the consolidated closeout) since dropping its second
  tag made it newly subject to that gate's single-asset-group check — confirmed clean via a fresh gate run. Phase 1
  (`Workflow`, 6 agents, one per never-cited candidate): **all 6 verdicted `exclude_cross_cutting`** — 2 fixed directly
  (see above, both drop-cross-cutting-keep-sibling-tag cases), 4 parked here (findings 1-4, each needs a tag ADDED that
  isn't present, i.e. real ownership by a different tranche). **Net result: zero genuine new cross-cutting orphans this
  run** — no Phase 3 batch draft warranted (`cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md` remains
  `status: draft`, still awaiting operator approval to dispatch — not flipped by this run per the "ASK BEFORE
  CREATING"/never-auto-flip HARD RULE). **Ledger**: 5 new parked findings this run (4 from Phase 1 + 1 from the
  Orthogonality check), 5 entries written above (1-5) — balanced.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — fresh doc (filed today), same parked-findings-register class as
  its 2026-08-02 sibling; all 5 todos are cross-tranche retag+fold-in actions the OWNING tranche must execute per the
  skill's primary-owner rule, not this doc's write.
- **na-eligibility-audit 2026-08-06 (follow-up)**: correction to the entry immediately above — finding 4's target
  (`resource_watchdog_host_guardian_2026_08_05.md`) was independently verdicted ARCHIVE by this same run's own Phase 1
  classification of the cross-cutting candidate set (it carries `asset_group: [cross-cutting]` only, so it — unlike
  findings 1/2/3's targets — genuinely IS this tranche's to act on, not a cross-tranche write). Executed: retagged +
  archived, todo #231 flipped `[x]`. Findings 1/2/3 remain correctly deferred (their targets are independently KEEP-NA
  per this run's own classification of them, so no analogous escalation applies).
- **context-scout 2026-08-07**: populated context_scope (5 entries) — pointed at the 4 still-open findings' actual retag
  targets (findings 1/2/3/5) plus SKILL.md for process context; dropped the generic conflict-check codex doc (no batch
  drafted this run) and the hub/prior-sibling pointers (less load-bearing than the todos' own direct targets).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — verified all 4 open findings' targets directly today: findings
  1/2/3/5 target docs all still carry their original mistagged `asset_group` (fresh grep confirms `[cross-cutting]` /
  `[defi, cross-cutting]`, unretagged) — all 4 todos remain genuinely open, owning-tranche work.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- reaffirms 2026-08-07 (unchanged): 4
  open findings (1/2/3/5) are all cross-tranche `asset_group` retag handoffs to `ui`/`infrastructure`/`ci`, explicitly
  scoped "owning-tranche fix, leave to X tranche's own audit" -- not this tranche's write by construction.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
