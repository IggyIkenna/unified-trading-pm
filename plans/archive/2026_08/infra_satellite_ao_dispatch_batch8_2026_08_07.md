---
doc_type: plan
title:
  Infra satellite AO batch 8 — fix `lc_verify_tarball_freshness`'s auto-mode silent dirty-tree skip (VM launches proceed
  onto stale code)
summary: >-
  Eighth AO-dispatch batch for the `infra` topic tranche, produced by `/ag-closeout-audit infra` (autonomous mode,
  2026-08-07). Phase 0 re-derived the covering set via `generate_ag_closeout_audit_candidates.py --tranche infra` (51
  members / 12 covering docs / 7 never-cited). Of the 7, 4 are unchanged since the 2026-08-06 run's own classification
  (non-batchable or claimed elsewhere — see the parked-findings doc); 3 are genuinely new since that run's snapshot
  (created 2026-08-06 after the prior audit ran). Of those 3, exactly ONE is a conflict-clear, bounded, never-drafted
  candidate: `issues/lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md`'s `auto`-mode bug in
  `deployment-service/scripts/vm/lib/launcher_common.sh` — the pre-launch tarball-freshness guard silently reports
  success (and lets a VM launch proceed) when its own republish attempt was SKIPPED due to unrelated dirty tracked files
  in a shared multi-slot checkout, a normal and expected state in this workspace's multi-agent model. The other 2 new
  candidates are NOT infra's to extract: `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` is ci-owned
  content (dual-tag `[ci, infrastructure]`, direct sequel to `shared_ci_workflow_repo_extraction_2026_08_06.md`);
  `archive/issues/ao_worker_context_thrash_no_recycle_escape_2026_08_06.md` is a genuine `asset_group` mistag
  (agent-orchestrator worker-lifecycle content, `parent_epic: orchestrator_master`, tagged `infrastructure` instead of
  `ao`) — reported as a new finding in the parked-findings doc, not retagged here (owning-tranche-writes-only rule, same
  precedent as the still-open finding 6 mistag). Single-todo plan per `task_template.md` §4's carve-out
  (`check_finalize_plan_coverage.py`'s `_todo_count(...) <= 1` threshold) — no separate finalize plan; archival is
  folded into the one todo's own "Done when", mirroring `infra_satellite_ao_dispatch_batch4_2026_07_31.md` and
  `infra_satellite_ao_dispatch_batch5_2026_08_01.md`.
status: archived
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, satellite-docs, batch-8, plan-hygiene, vm-launcher, tarball-freshness]
related:
  [
    /plans/active/issues/lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md,
    /plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md,
    /plans/active/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch9_2026_08_07.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_infra_parked_2026_08_07.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-07"
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: infra
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/scripts/vm/create-code-tarballs.sh,
    deployment-service/tests/unit/test_vm_launcher_scripts.py,
    /plans/active/issues/lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
source: >-
  `/ag-closeout-audit infra` run 2026-08-07 (ag_closeout_auditor scheduled worker, slot 8). Phase 0 re-derived the
  covering set via `generate_ag_closeout_audit_candidates.py --tranche infra` (51 members / 12 covering docs / 7 never
  cited). Per the skill's batchN iterative-drain methodology, re-checked all carried-forward findings from
  `issues/ag_closeout_audit_infra_parked_2026_08_06.md` live before considering fresh Phase-1 triage of the 3 genuinely
  new never-cited candidates (confirmed via `git log --follow --diff-filter=A`, all 3 first-committed AFTER the
  2026-08-06 run's ~08:41 UTC snapshot). That targeted delta read — not a from-scratch full-corpus re-classification of
  all 51 members — is what surfaced this batch's one todo.
---

# Infra satellite AO batch 8

> **Drafted `status: draft` per the skill's autonomous-mode safety rail (CLAUDE.md § "Plan destination — ASK BEFORE
> CREATING"). Flipping to `active` is the operator's call — parked as a follow-up in this run's parked-findings doc, not
> auto-flipped.** Nothing here has been shipped.

## Why this batch exists — a genuinely new, conflict-clear orphan

`issues/lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md` (filed 2026-08-06, never cited in any
infra covering doc) documents a real, twice-hit-in-one-session bug: `launcher_common.sh`'s
`lc_verify_tarball_freshness`, in its default `auto` mode, republishes a stale tarball via
`create-code-tarballs.sh --include <repo>` and then **unconditionally returns success** as long as that subprocess exits
0 — but `create-code-tarballs.sh` also exits 0 when it SKIPPED the repo entirely because of unrelated dirty tracked
files (a normal state on this workspace's shared multi-slot checkouts, per
`/codex/05-infrastructure/per-tab-worktrees.md`). The recursive re-verify call inside `auto` mode DOES correctly detect
the tarball is still stale, but runs in `warn` mode, which itself always returns 0 by design — and the outer `auto`
branch never inspects that inner result. Net effect: a VM launcher using `auto` mode (the default) can silently boot a
VM onto pre-fix code every time a shared checkout has foreign dirty files present, with only an easy-to-miss WARNING
line as the signal. This is the exact incident class
`features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md` was filed to prevent — the mechanism
built to close that gap has its own gap.

## Why a single-todo plan with no finalize twin

`task_template.md` §4's finalize-plan-coverage rule requires a gated finalize twin for an `assigned_vm: planning` plan —
EXCEPT the single-todo carve-out, which `scripts/quality_gates/check_finalize_plan_coverage.py` implements literally
(`_todo_count(...) <= 1`, filtered on `assigned_vm: planning` regardless of `status`). This plan has exactly one todo,
so the archival + source-checkbox-reconciliation work a finalize twin would normally do is folded into that todo's own
"Done when" — the same shape `infra_satellite_ao_dispatch_batch4_2026_07_31.md` and
`infra_satellite_ao_dispatch_batch5_2026_08_01.md` used.

## Conflict check performed before drafting

- **`lc_verify_tarball_freshness` (the function itself)** — corpus-wide `rg -l "lc_verify_tarball_freshness"` across all
  of `plans/active/` (plans + issues, not just infra-tagged) returns 12 hits. 11 are either the source doc itself, docs
  that merely NAME-DROP the function in passing evidence trails
  (`cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`, `bucket_iam_write_protection_per_tier_2026_06_09.md`,
  etc. — none propose changing its `auto`-mode logic), or the two related-but-different docs addressed below. The 12th,
  same-day hit — `cefi_satellite_ao_dispatch_batch9_2026_08_07.md` (drafted today by a concurrent cefi-tranche worker) —
  references this exact bug as a **confound to note, not a claim to fix**: its own todo text reads "the sibling bug
  `issues/lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md` ... can confound the observation — if a
  silent skip is suspected, record it and note the confound rather than forcing the result." It explicitly does not
  extract or fix the underlying `auto`-mode logic. **No competing claim.**
- **`features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`** — `status: open`,
  `assigned_vm: planning`, 5/5 todos `[x]` (0 open). This is the PRIOR, DIFFERENT gap (stale universe-filter settlement
  suffixes) that motivated building `lc_verify_tarball_freshness` in the first place; already fully shipped, not a
  competing claim on this bug.
- **`vm_launcher_setup_script_freshness_gap_2026_07_31.md`** — `status: open`, 1 open todo, but scoped to a DIFFERENT,
  broader remediation (migrating 139 raw-`gcloud compute instances create` launchers onto the `lc_gcloud_create` wrapper
  so pre-launch guards apply uniformly) — does not touch `lc_verify_tarball_freshness`'s own `auto`-mode result-checking
  logic. No overlap.
- **Existing test coverage** — `deployment-service/tests/unit/test_vm_launcher_scripts.py`'s `TestTarballFreshnessGuard`
  class covers `off`/`warn`/`enforce` modes (`test_off_mode_short_circuits`, `test_stale_tarball_warn_does_not_block`,
  `test_stale_tarball_enforce_blocks`, `test_missing_manifest_enforce_blocks`) but has no `auto`-mode test at all — this
  todo's regression test is net-new, not a duplicate of existing coverage.
- **`check_delete_vm_launch_gating.sh` shape** — the todo is a bash-function correctness fix + a regression test. No GCS
  delete, no `--apply`, no VM launch performed BY this todo itself (it fixes the guard a launcher calls). No
  `[OPERATOR]` tag or delete-safety citation required.

## Todos

- [x] ✅ [INFRA] P2. **Fix `lc_verify_tarball_freshness`'s `auto` mode to check the actual post-republish freshness
      result, not just the republish subprocess's exit code** (`deployment-service/scripts/vm/lib/launcher_common.sh`).
      Today, `auto` mode's `return 0` fires unconditionally once `$republish_cmd`
      (`create-code-tarballs.sh --include <repo>`) exits 0 — but that subprocess also exits 0 when it SKIPPED the repo
      (uncommitted changes present, a normal state on a shared multi-slot checkout). The recursive
      `LC_TARBALL_FRESHNESS=warn lc_verify_tarball_freshness` re-verify call already detects this correctly but its
      result is discarded (`warn` mode itself always returns 0 by design). Capture the recursive call's actual
      stale/fresh verdict (e.g. refactor the freshness CHECK into its own function returning a stale-repo list, separate
      from the warn/enforce/auto DISPOSITION logic, so `auto` can call the check function directly post-republish
      instead of recursing into itself and discarding the result) and propagate it as `auto`'s own return value — `auto`
      must return non-zero (matching the existing "ERROR: auto-republish failed" path) when the post-republish state is
      still stale, not just when the republish subprocess itself hard-failed. Add a regression test to
      `TestTarballFreshnessGuard` in `deployment-service/tests/unit/test_vm_launcher_scripts.py` that reproduces the
      exact reported case: a stale tarball manifest + a dirty (uncommitted) tracked file in the repo under test +
      `LC_TARBALL_FRESHNESS=auto` → asserts the function returns non-zero (does NOT silently report success), mirroring
      the existing `test_stale_tarball_enforce_blocks`/`test_missing_manifest_enforce_blocks` fixture shape. Then
      **reconcile the source doc**: in `issues/lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md`,
      flip todo 1's `[ ]` to `[x]` citing this todo's actual shipped commit sha (re-verify the sha resolves with
      `git show`, do not copy this todo's own text blind); leave todo 2 (`[DIAG] P3`, the optional
      `--allow-dirty-tarball` auto-scoping stretch idea) as-is on the source doc — it is a separate, smaller design
      consideration, not required for this fix, and stays tracked there for a future pass to pick up if warranted.
      **Then archive this batch plan itself** (it will have zero remaining open todos) via the standard 6-step archival
      ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — update every corpus-wide referrer
      of this plan's path (expected: none yet, this is a brand-new plan) before moving it. **Done when**: `auto` mode
      returns non-zero when the post-republish state is still stale (verified by the new regression test, which fails
      against the current code and passes after the fix), the new test is added to `TestTarballFreshnessGuard`,
      `bash scripts/quality-gates.sh` is green in `deployment-service`, the source doc's todo 1 checkbox is flipped with
      a verified sha, and this batch plan is archived. Repo: deployment-service (the fix), unified-trading-pm
      (source-doc reconciliation + this plan's own archival). Source:
      `issues/lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md` (todo 1). —
      deployment-service@450b212. QG green; test passes.

## Codex SSOTs (read before executing this todo)

- `/codex/05-infrastructure/vm-launcher-runbook.md` — VM launch conventions this guard protects
- `/codex/05-infrastructure/per-tab-worktrees.md` — why foreign dirty files legitimately sit in a shared checkout (the
  root condition that triggers this bug)
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the conflict-check protocol this batch
  ran before drafting
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step ritual this todo folds in
- `plans/active/task_template.md` §4 — the single-todo finalize-plan-coverage carve-out this plan uses

## Progress Log

- **2026-08-07** — Drafted by `/ag-closeout-audit infra` (Autonomous/AO-dispatched mode, scheduled daily run, slot 8).
  Phase 0 re-derived the 12-doc covering set via `generate_ag_closeout_audit_candidates.py --tranche infra` (51 members,
  down from 57 on 2026-08-06 — plausibly explained by the same-day 2026-08-06 archive-candidates-audit sweep archiving
  76 resolved issue docs corpus-wide, not investigated further as it doesn't affect this batch's own candidate). 7
  never-cited: 4 unchanged from 2026-08-06's own classification (non-batchable or claimed elsewhere), 3 genuinely new
  (confirmed via first-commit timestamps, all after the 2026-08-06 run). Of the 3 new: this batch's one todo
  (conflict-clear, see above); `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` (ci-owned, not
  drafted here); `ao_worker_context_thrash_no_recycle_escape_2026_08_06.md` (asset_group mistag, ao-owned content —
  reported as a new finding, not retagged; **archived 2026-08-07 by na-eligibility-audit ao tranche** — resolved by a
  parallel session's fix to the same live incident, see
  `/plans/archive/issues/ao_worker_context_thrash_no_recycle_escape_2026_08_06.md`, so the mistag finding is now moot).
  Left `status: draft` deliberately; the flip to `active` is the operator's call. Other findings from this run
  (carried-forward re-verifications, 2 resolved since 2026-08-06, 2 new mistag findings) are recorded in
  `issues/ag_closeout_audit_infra_parked_2026_08_07.md`, not here.
- **Operator ruling 2026-08-07 (interactive session, via consolidated NA-blocker-digest audit)**: APPROVED — flipped
  `status: draft` → `active`. Now AO-dispatchable.
- **AO slot-9 2026-08-07**: Picked up and executed. deployment-service@450b212 — fix + regression test shipped. QG
  green. Source doc todo 1 flipped. Batch plan archived (all todos done, no lock).
