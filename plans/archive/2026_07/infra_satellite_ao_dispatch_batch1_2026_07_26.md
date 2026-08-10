---
doc_type: plan
title:
  Infra satellite docs — AO dispatch batch 1 (25 AO-eligible todos extracted from 17 human-only infra plans/issues; the
  infra tranche's FIRST batch)
summary: >-
  The infra tranche's covering set is a ZERO-TODO digest. `infra_consolidated_closeout_2026_07_25.md` lists 32 Source
  docs for discoverability and carries no `- [ ]` of its own (verified: `grep -cE '^\s*-\s*\[[ xX]\]'` on it returns 0),
  and no `infra_*_satellite_ao_dispatch_batch*` plan has ever existed — so unlike the 5 asset groups, NOTHING in the
  infra covering set dispatches anything. That makes every infra doc with genuine remaining work orphaned by
  construction (29 of 34 tranche-primary docs, per the 2026-07-26 `/ag-closeout-audit infra` run). This plan is the
  first extraction pass: 25 conflict-cleared, bounded, worker-determinable todos pulled DIRECTLY out of 17 satellite
  docs (never out of the hub's own content). Internally-sequential chains inside one source doc are combined into ONE
  todo rather than fanned out (AO has no per-todo prereq syntax short of `sequential: true` for the whole plan, and
  these 25 genuinely benefit from concurrent dispatch). Every drafted todo was checked for file-level collision against
  all 93 existing batch/finalize/closeout plans AND against the other 24 todos here — 14 further AO-eligible items were
  DEFERRED for a named conflict rather than drafted (see `## Deferred`), and 3 were resolved by logic (the competing
  side had already shipped or an operator had already ruled) rather than re-drafted as a competing claim.
status: archived
nature: process
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    unified-trading-pm,
    deployment-service,
    deployment-api,
    deployment-ui,
    unified-api-contracts,
    unified-trading-library,
    unified-trading-system-ui,
    instruments-service,
    market-tick-data-service,
    execution-service,
    strategy-service,
    alerting-service,
    e2e-testing,
    system-integration-tests,
    agent-orchestrator,
  ]
scope: [engineer, admin]
tags: [infra, ao-dispatch, satellite-docs, batch-1, plan-hygiene, close-out]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /plans/archive/issues/setuptools_fleet_pysec_2026_3447_bump_2026_07_14.md,
    /plans/archive/issues/uv_pin_fleet_drift_2026_06_22.md,
    /plans/active/issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md,
    /plans/archive/2026_08/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md,
    /plans/archive/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md,
    /plans/active/issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md,
    /plans/archive/2026_07/utl_uac_reuse_consolidation_remediation_2026_06_10.md,
    /plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md,
    /plans/active/codex_violations_ratchet_to_five_2026_06_10.md,
    /plans/active/repo_scripts_governance_audit_2026_06_18.md,
    /plans/archive/issues/service_dockerfile_pattern_normalization_2026_06_17.md,
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md,
    /plans/active/issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md,
    /plans/archive/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md,
    /plans/archive/2026_07/l0_doc_index_generator_2026_06_24.md,
    /plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md,
    /plans/active/stash_pile_workspace_cleanup_2026_06_03.md,
    /plans/active/issues/reference_path_convention_2026_07_23.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 9.0
estimate_calibrated_ai_days: 7.2
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
supersedes:
superseded_by: infra_satellite_ao_dispatch_batch12_2026_08_09
depends_on: []
source: >-
  `/ag-closeout-audit infra` run 2026-07-26 (Autonomous/AO-dispatched mode, operator away). Phase 0 found the infra
  covering set is a single zero-todo digest with no batch plan; Phase 1 read all 34 tranche-primary docs end-to-end and
  classified 29 as orphaned; Phase 3 applied the dispatch-scope eligibility test + the HARD conflict check against all
  93 existing batch/finalize/closeout plans before drafting anything here.
---

# Infra satellite docs — AO dispatch batch 1

> **ARCHIVED 2026-08-09** — All 25 todos shipped and verified. Closed out by
> `/plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`, which reconciled all 17 source-doc
> checkboxes (todo 1), re-checked all 10 CONFLICT-GATED Deferred items (todo 2), re-measured the infra tranche's orphan
> count + closed the covering hub's dispatch-vs-digest gap (todo 3), and archived this plan (todo 4). Every Deferred
> item below was migrated to a real home before archival — see the "Deferred item disposition" note at the end of the
> `## Deferred` section, and the finalize plan's own todo 4 RESULT for full detail. One genuinely new AO-eligible item
> (item 5, `managed-by` launcher label standardization) was cleared and drafted as
> `/plans/archive/2026_08/infra_satellite_ao_dispatch_batch12_2026_08_09.md`; every other Deferred item was confirmed
> already-resolved, already-shipped, or already tracked in its own live doc — nothing was lost.

## Why this plan exists (the coverage gap, measured)

`infra_consolidated_closeout_2026_07_25.md` § "Aggregated source docs" is a **digest, not dispatch** — the same
structural gap `/ag-closeout-audit`'s SKILL.md documents for every AG. For infra it is more acute than for any AG:

- The hub carries **zero** `- [ ]` todos
  (`grep -cE '^\s*-\s*\[[ xX]\]' plans/active/infra_consolidated_closeout_2026_07_25.md` → `0`).
- Its `depends_on:` is `[]` and its `related:` names only the 3 sibling tranche closeouts + the audit SKILL — so the
  dependency-graph discovery path finds **no forked children** either.
- `ls plans/active/ | grep -E 'infra.*(satellite|ao_dispatch|batch)'` → **nothing**; `plans/archive/*/` has no archived
  infra batch. The 5 AGs have 41 such plans between them; infra has 0.

So the audit question "if the closeout plan's own todos and every active batch ran to completion, what is left
orphaned?" resolves to "everything," because nothing in the covering set does anything. This plan starts the drain.

## Rules this plan follows

- Every todo ends with `Source: `<doc>.md`` naming the satellite doc it was extracted from, plus a **Done when** clause.
- Same-priority todos dispatch CONCURRENTLY by default, so **zero same-file collisions** was a hard requirement —
  verified pairwise across all 25 todos and against all 93 existing claimer plans. Where two candidates collided, one
  was folded into the other or deferred (never drafted as a racing pair).
- `sequential:` deliberately UNSET — this is not a dependency chain. Multi-step work inside a single source doc is
  combined into one todo instead.
- Anything gated on an unmade operator/design decision, on a competing in-flight claim, or on corpus-wide file
  contention is in `## Deferred` with the reason — not dispatched speculatively.

## Todos

- [x] ✅ [SCRIPT] P2. **DONE (2026-07-28, slot-8) — steps (1)/(2) were already shipped by other slots before this
      dispatch** (`instruments-service@fe27be91` "fix(deps): bump setuptools to 83.0.0 (PYSEC-2026-3447)",
      `market-tick-data-service@0413e5cd` same message; verified via `grep -A1 '^name = "setuptools"' uv.lock` → both
      83.0.0, and `git log -1 -- uv.lock` on each confirms the bump commit). e2e-testing was already at 83.0.0 as noted
      in the source doc. Only step (3) remained: removed the now-stale `--ignore-vuln PYSEC-2026-3447` from
      `e2e-testing/scripts/quality-gates.sh`'s `PIP_AUDIT_EXTRA_ARGS` (was line 26) and its explanatory comment (was
      line 36-37) — `e2e-testing@4c324e8`. Verified: fleet-wide sweep across all 3 target repos shows setuptools
      83.0.0/83.0.0/83.0.0 (no repo below 83.0.0); `bash scripts/quality-gates.sh` in e2e-testing is green
      (`pip-audit clean`, 0 codex violations) with the ignore removed;
      `grep -n PYSEC-2026-3447 e2e-testing/scripts/quality-gates.sh` returns nothing. **Fleet-wide setuptools
      PYSEC-2026-3447 bump (3-step chain, combined).** (1) Sweep every repo's `uv.lock` for a setuptools pin `< 83.0.0`
      (`grep -A1 '^name = "setuptools"' */uv.lock`) and for each hit add a `setuptools>=83.0.0` constraint (or
      equivalent) so the transitive resolve picks the fixed version, then `uv lock` that repo. Known-affected as
      measured 2026-07-26: **instruments-service** (82.0.1) and **market-tick-data-service** (82.0.1); e2e-testing is
      already at 83.0.0. (2) Re-run each bumped repo's `bash scripts/quality-gates.sh` and confirm pip-audit is clean
      for PYSEC-2026-3447 with NO `--ignore-vuln` entry for it. (3) Remove the TEMPORARY `--ignore-vuln PYSEC-2026-3447`
      from `e2e-testing/scripts/quality-gates.sh`'s `PIP_AUDIT_EXTRA_ARGS` (line 26) **and** its explanatory comment
      (line 36) — the ignore has already outlived the fix in the one repo that is fixed, which is exactly what the
      source doc's Acceptance forbids. **Do NOT add a constraint to `workspace-constraints.toml` /
      `canonical-dependency-manifest.json`** — those two files are deferred hotspots in this batch (see `## Deferred`,
      dep-manifest contention); use per-repo constraints only. **Done when**: the sweep command returns no setuptools
      version below 83.0.0 in any repo, each touched repo's QG is green with codex-compliance at 0 violations, and
      `grep -n PYSEC-2026-3447 e2e-testing/scripts/quality-gates.sh` returns nothing. Repos: instruments-service,
      market-tick-data-service, e2e-testing. Source:
      `/plans/archive/issues/setuptools_fleet_pysec_2026_3447_bump_2026_07_14.md` (ARCHIVED 2026-07-30 — all 3 of its
      own todos independently re-verified + flipped).

- [x] [INFRA] P1. **Fix the `scripts/setup.sh` bootstrap-uv fallback in the PM template + roll it out fleet-wide — DONE
      (slot-7, 2026-07-26): 25/25 repos now carry the astral-installer fallback, all committed+pushed. 24 were already
      shipped by prior slots (verified via `git log -1 -- scripts/setup.sh` per repo — real commits, listed in the
      "Re-check 2026-07-26" note below). The 25th, `agent-orchestrator`, never had a `scripts/setup.sh` at all
      (confirmed in scope via `workspace-manifest.json`); copied PM's canonical file in, `bash scripts/setup.sh` +
      `bash scripts/quality-gates.sh` both green (1763 passed, 1 skipped), shipped `agent-orchestrator@89ca717`. Hit +
      worked through a host disk-full emergency mid-task (see `issues/shared_host_home_filesystem_full_2026_07_26.md`,
      `BLK-8afbcd6b`) — stashed WIP safely rather than force a red-QG ship, waited for the operator's fix, resumed once
      disk had headroom. (combined: the source doc lists this twice — once under "Durable fix" and once as "couples to
      the fleet rollout" — they are ONE unit, not two racing todos).** Replace the pip fallback in
      `unified-trading-pm/scripts/setup.sh` with the astral standalone installer so a drifted box self-realigns pip-free
      (the exact replacement block is quoted verbatim in the source doc's "Durable fix" section —
      `curl -LsSf https://astral.sh/uv/0.10.8/install.sh | env UV_UNMANAGED_INSTALL="$HOME/.local/bin" sh` + `hash -r`,
      with the pip path kept as the last resort). Today, when uv is present-but-wrong-version, the fallback shells out
      to a uv-managed CPython that has no pip → non-zero → `set -e` exits 1, which is why human-planning-vm's bootstrap
      reported "Failed: 25". Then roll the fixed template out via
      `python3 unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py` and commit the updated
      `scripts/setup.sh` to **every** repo's `live-defi-rollout` in the same unit — the rollout is NOT done until all
      per-repo copies are committed and pushed (leaving them dirty jams the `slot-cron-ff-pull` cron). Target repos: all
      25 in `workspace-manifest.json`. **Keep the pin at 0.10.8** — do NOT bump to 0.11.x (that would force re-locking
      every repo `revision = 3 → N`, exactly the churn the pin exists to prevent). **Done when**: `scripts/setup.sh` in
      PM and in all 25 repo copies contains the astral branch, every copy is committed + pushed, and a deliberate
      wrong-version smoke (temporarily place a non-0.10.8 uv on PATH, run `scripts/setup.sh`, confirm it realigns and
      exits 0) passes. Repos: unified-trading-pm + all 25. Source:
      `/plans/archive/issues/uv_pin_fleet_drift_2026_06_22.md`.

- [x] ✅ [INFRA] P1. **DONE 2026-07-26 (slot-7) — already shipped same-day via the carve-out; verified, not re-landed.**
      Land the two written-but-unshipped workspace boot-script hardenings (the blocker they were held on has cleared).
      Both were authored + validated on slot-3 (`bash -n` + `shellcheck -S error` clean) and then held because PM's
      `main`↔`live-defi-rollout` version split hard-blocked any PM commit; the source doc's own later `[CICD] P1` entry
      records that split RECONCILED (`main` merged down to LDR, "main is now 0 commits ahead of LDR"), so re-derive and
      land them from the doc's spec: (a) `scripts/workspace/workspace-bootstrap.sh` — Phase 1 enforce the pinned uv
      `0.10.8` via the astral installer when the present uv differs (today it logs `[SKIP] uv already installed`,
      letting 0.11.x ride); Phase 1 install pnpm (corepack → npm → sudo npm fallback) so the UI repo's setup.sh works;
      after the clone loop `git checkout live-defi-rollout` for every repo (git clone leaves them on `main`, which the
      FF-pull cron skips and which causes cross-branch dep conflicts). (b)
      `scripts/workspace/setup-workspace-config-symlink.sh` — emit the root `.code-workspace` as a REGULAR file with
      root-relative paths (sed-rewrite `"../../X"`→`"X"`, `"../../"`→`"."`) instead of a symlink into
      `.cursor/workspace-configs/`, whose `../../`-relative folder paths resolve above the workspace root and make VS
      Code/Cursor report "no folders containing Git repositories". **Do NOT edit `scripts/setup.sh` here** — the todo
      above owns that file. **Done when**: both scripts carry the changes, `bash -n` + `shellcheck -S error` are clean
      on both, and a fresh `.code-workspace` render is verified to be a regular file whose folder paths resolve inside
      the workspace root. Repo: unified-trading-pm. Source: `/plans/archive/issues/uv_pin_fleet_drift_2026_06_22.md`.
      Full verification evidence in the Progress Log below — no new commit needed (the fix already shipped
      `unified-trading-pm@703b1e912`, 2026-06-22, via carve-out #3, same day the issue doc's "BLOCKED from landing"
      section was written — that section went stale the moment the carve-out push landed and was never updated).

- [x] ✅ [TEST] P2. **Repair the repo-wide E2E login helper contract — DONE 2026-08-09 (slot-28, infra),
      unified-trading-system-ui@15e4b4bc.** Root cause of the UAT-redirect was NOT a classification bug in
      `isDemoPersonaEmail()` — `next.config.mjs` unconditionally loaded `.env.production`
      (`NEXT_PUBLIC_SITE_URL=https://www.odum-research.com`) into every `next dev` too, wrongly satisfying
      `login/page.tsx`'s `isProdSite` check under `pnpm dev:mock`; fixed by making the env-file load `NODE_ENV`-aware.
      Also restored the `?persona=<id>` fast-path in `app/(public)/login/page.tsx` (gated to demo/mock mode, resolves
      via `PERSONAS`, auto-submits). **Verified live** via Playwright trace: `?persona=admin` now logs in locally and
      reaches `/dashboard` (previously silently redirected to UAT). 2/21 `user-management.spec.ts` tests now pass
      end-to-end post-login (up from 0/21 timing out at login) — full-suite green is blocked by two SEPARATE,
      pre-existing, unrelated gaps found during verification (`/api/v1/*` needs real Firebase Admin creds; the mock dev
      server itself is unstable under sustained Playwright load), filed rather than absorbed:
      `issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md` (carries item
      3's `admin-strategy-assignments.spec.ts` re-run as its own todo 3). Prod login path unchanged (both fixes gated
      behind demo/mock checks). QG green. Repo: unified-trading-system-ui. Source:
      `issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md`.

- [x] ✅ [UI] P2. **Fix the 8 pre-existing deployment-ui smoke failures** — deployment-ui@2340c68. `pw:L2 ✓`. (a)
      `daily_costs_and_vm_detail.spec.ts`'s 5 "DailyCosts page" failures + `accessibility_audit.spec.ts`'s "Daily Costs
      has no critical/serious WCAG AA violations": traced to **mock-data-shape drift, not a page regression** —
      `CostObservability.tsx`'s git history (`feat(costs):` commits through `4aa0c2b`) shows the page was deliberately,
      incrementally redesigned from a single-day/asset-group view into the multi-cloud (GCP/AWS/GitHub) range-based Cost
      Observability page, and is already fully covered by `cost-observability.spec.ts` (passing, unmodified). Deleted
      the obsolete "DailyCosts page" describe block (5 tests asserting dead selectors: "Daily VM Costs" heading,
      `total-usd` testid, "By Asset Group" text, `aria-label="Select date"` single-date input, `/api/costs/daily` error
      path) — kept the still-valid `VmDetail page` tests in the same file. The a11y failure WAS a real bug (not drift):
      `InfoTip`'s trigger `<span>` carried `tabIndex`+`aria-label` with no ARIA role (axe `aria-prohibited-attr` — a
      roleless span can't carry `aria-label`); fixed by adding `role="button"` (it's a focusable, hover/focus disclosure
      trigger). (b) `mobile_responsive.spec.ts` "hamburger menu is visible and opens nav": scoped the locator to
      `getByTestId("mobile-menu-btn")` (the always-visible `nav-cockpit` button's aria-label now also matches the old
      `/menu|hamburger|navigation/i` regex) and asserted against `getByTestId("mobile-nav")` instead of a generic
      `nav, [role='navigation']` locator, which matched `TopNavBar`'s always-in-DOM but `md:hidden` (mobile- hidden)
      `<nav>` instead of the mobile dropdown. (c) `nav-menu-dedup.spec.ts` — re-verified: already passes at 6
      `cockpit-navlink-*` entries against the currently-shipped nav (0 fix needed; the 5→6 count drift the issue doc
      flagged on 2026-07-21 was already reconciled by the time of this dispatch). **Evidence**:
      `npx playwright test --project=chromium tests/smoke/` — 413 passed, 1 failed. The 1 residual failure
      (`alerts-page.spec.ts` "kind filter, date range, and column sort compose correctly") is a DISTINCT, non-flaky (3/3
      on `--repeat-each=3`), pre-existing-as-of-2026-07-26 regression unrelated to (a)/(b)/(c) and outside this todo's
      named scope (also outside the original 2026-07-21 8-failure count — the suite grew from 404→419 total tests since
      then, making the todo's literal "404/404" done-when stale); filed as
      `/plans/archive/issues/deployment_ui_alerts_page_combined_filter_sort_regression_2026_07_26.md` (resolved +
      archived) per the findings-closure rule rather than absorbed into this dispatch. tsc/ESLint/Vitest (101 tests) all
      green; `DataStatusTab.tsx` untouched per the scope guard. Repo: deployment-ui. Source:
      `issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md`.

- [x] ✅ [BACKEND] P2. **Wire `PROGRESS.json` checkpoint emission into the no-checkpoint launcher families** —
      `deployment-service@e191d58`. Root cause confirmed: the generic MTDS `--operation download` path aggregates via
      `PartitionedGroupWriter` → `record_captured_from_counts`
      (`market_tick_data_service/engine/orchestrator/manifest_finalize.py`), which never calls
      `unified_trading_library.manifest_writer._vm_progress.record_vm_progress` (only the sibling per-row
      `record_captured` does) — so the generic UTL hook silently never fires for these families, contrary to the
      original todo's assumption that a shared-lib edit alone would suffice. Fixed at the shell chunk-loop layer instead
      (the tee-wrapper's marker grep is agnostic to which layer emits it): added
      `[[VM_PROGRESS]] last_completed_date=<date> monotonic=true` emission, gated on a per-run `HAD_FAILURE` flag (a
      LATER chunk's success must never paper over an EARLIER chunk's failure/kill — a bug caught during this todo's own
      simulation and fixed before shipping), to `mtds_chunk_loop.sh` and `cefi_hl_aster_loop.sh`
      (`deployment-service/scripts/vm/setup-data-pipeline-vm.sh`) and to the `defi-per-instrument` per-year loop
      (`deployment-service/scripts/vm/launch-canonical-migration-vm.sh`, full-mode only). Covers `tradfi-bf-*`,
      `mtds-backfill-tradfi-pipelinecheck`, `cefi-queue-heavy-binancefutu-x17` (all VM_TASK=mtds-backfill),
      `cefi-aster`/`cefi-hyperliquid` (VM_TASK=cefi-hl-aster-backfill), and `canonical-migration-defi-per-instrument`.
      **Verified by local bash simulation** (not a VM launch, per the todo's own instruction): a 6-day/2-day-chunk run
      with a child that self-`kill -9`s mid-chunk, confirming (a) the marker only emits on success, (b) a later
      successful chunk after an earlier failure emits NO marker (gap-safety proof), (c) the tee-wrapper-style regex
      extraction + `PROGRESS.json` write + a second-invocation JSON read-back all resolve to the last
      GENUINELY-completed date, never skipping the killed chunk. `defi-pi-range`/`defi-rebuild` (single-invocation, no
      shell chunk boundary to hang a marker on) and `mtds-dex-swaps-backfill`/`af-backfill` (route through the generic
      single-shot `elif [ -n "$VM_TASK" ]` fallback, also no chunk loop) remain genuinely unconformant — restructuring
      either into a chunked loop is a materially different, higher-blast-radius change (the generic fallback is shared
      by every VM_TASK with no dedicated branch) and is out of scope for this todo; tracked as the two follow-up todos
      immediately below. `/codex/05-infrastructure/spot-vms-for-backfill.md` records the full per-family conformance
      table. Repos: deployment-service. Source:
      `issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md`.

- [x] ✅ [BACKEND] P3. **Close the `defi-pi-range`/`defi-rebuild` PROGRESS.json gap** — these two
      `launch-canonical-migration-vm.sh` categories are single Python-module invocations with no shell chunk boundary
      (unlike `defi-per-instrument`'s per-year loop, fixed above), so a SPOT preemption mid-run still replays
      `RESUME_START_DATE` verbatim with no partial-progress resume. Lower severity than the chunked families (one VM per
      quarter/whole-range, not day-granular, so the replay cost is smaller) but still a real gap. Options to evaluate:
      (a) wrap the single invocation in an artificial N-way date-sub-chunk loop mirroring `defi-per-instrument`'s
      pattern, or (b) thread a periodic marker into `migrate_defi_batch_to_per_instrument`/`rebuild_defi_manifest`
      themselves (Python-side, mirrors `migrate_candle_canonical_2026_07.py`'s existing
      `MIGRATION_PROGRESS-shard{N}.json` precedent). VERIFY BY SIMULATION per the same discipline as the parent todo —
      no VM launch required. Repo: deployment-service, or market-tick-data-service if (b). Source: this todo
      (`infra_satellite_ao_dispatch_batch1_2026_07_26.md`). **Checkbox-flip closeout 2026-08-01 (slot-6) — code was
      already shipped ~2h before this dispatch, verified not re-implemented**: both options were taken, one per repo,
      exactly matching the todo's own "Repo: deployment-service, or market-tick-data-service if (b)" framing. (a)
      `defi-pi-range` — `deployment-service@1e8af34a` precomputes N-day sub-windows (`MIGRATION_PI_RANGE_CHUNK_DAYS`,
      default 30) as a launch-time bash for-loop mirroring `defi-per-instrument`'s per-year pattern, emitting
      `[[VM_PROGRESS]] last_completed_date=${w_end} monotonic=true` after each successful window (full-mode only). (b)
      `defi-rebuild` — the SAME `deployment-service@1e8af34a` commit passes `--chunk-days ${REBUILD_CHUNK_DAYS:-90}` to
      `rebuild_defi_manifest.py`, whose paired `market-tick-data-service@a2839705` adds the Python-side `_run_chunked()`
      loop that prints the identical `[[VM_PROGRESS]]` marker after each chunk's writer flush (verified: grepped
      `_run_chunked`/`--chunk-days` in the actual file, not just the launcher's comment claim). Both commits confirmed
      on origin via `git log     origin/live-defi-rollout -- <file>`. Verification-by-simulation (the todo's own
      requirement) is documented in `1e8af34a`'s own commit message (stubbed-tool full run incl. a mid-loop chunk
      failure, dry-mode leak check). No code change needed from this dispatch — closing the plan-bookkeeping gap only.

- [x] ✅ [BACKEND] P3. **Close the `mtds-dex-swaps-backfill`/`af-backfill` PROGRESS.json gap** —
      `deployment-service@0c5fa5b`. Chose the minimal end-of-run-marker option over a new chunk loop: `VM_TASK` is a
      copy-paste constant shared by ~10 DeFi and ~8 sports launchers each, so a chunk loop keyed on it alone would
      change behavior for every unrelated launcher sharing the label, not just these two. The non-fanout dispatch in the
      generic `elif [ -n "$VM_TASK" ]` fallback now emits ONE
      `[[VM_PROGRESS]] last_completed_date=$VM_END_DATE     monotonic=true` marker on a successful (rc=0) whole-range
      run — additive-only, no-op for any launcher that never sets `VM_END_DATE` (e.g. live/websocket tasks). Neither
      launcher ever fans out (mtds-dex-swaps-backfill sets `VM_OPERATION=collect-dex-swaps` not `download`; af-backfill
      sets `VM_SERVICE=instruments_service`), so the fanout supervisor script is untouched — a regression test asserts
      this. **Found while implementing**: `vm-exec-with-gcs-tee.sh`'s PROGRESS.json watchdog only scans for the marker
      on a poll where `kill -0 "$CMD_PID"` still finds the process alive AFTER its 60s `STALL_POLL_SEC` sleep — a
      process that writes the marker and exits within that same window dies mid-sleep, so the post-sleep check finds it
      dead and `break`s WITHOUT scanning, silently dropping the marker. The existing chunked loops (mtds-backfill etc.)
      are mostly insulated (an earlier chunk's marker already landed even if the final chunk's is lost to this exact
      race), but a single end-of-run marker has no earlier marker to fall back on. Fix: sleep 75s (60s default + margin)
      after the marker echo, before the wrapped process actually exits. **VERIFIED BY SIMULATION** (a standalone bash
      script replicating the real watchdog's poll loop, verbatim regex, against a real log file — no VM launched): 5/5
      runs dropped the marker without the delay, 5/5 captured it with the delay. (repo: deployment-service)

- [x] ✅ [BACKEND] P3. **Close the two fleet-monitor blind spots on checkpoint reading and preemption alert severity** —
      `deployment-service@b501a5e`. (a) Confirmed `read_progress_checkpoint()` globs only the literal `PROGRESS.json`
      and does NOT recognize `canonical-migration-*-cdlap`'s `MIGRATION_PROGRESS-shard{N}.json`. Documented it as an
      **accepted per-launcher naming exception** (not generalized) — the two checkpoint schemas are structurally
      incompatible (line-index vs. calendar date; there is no date to extract from a line-index checkpoint), and the
      resume already works WITHOUT this reader's help: `RelaunchPreemptedVm` relaunches the SAME `vm_name` (via
      `VM_NAME_OVERRIDE`, captured in `LAUNCH_PARAMS.json`), and `migrate_candle_canonical_2026_07.py` reads its OWN
      checkpoint keyed on that same `vm_name` internally — so this reader's blind spot is purely cosmetic (no
      `progress_checkpoint` detail on the alert), never a resume-safety gap. Documented in
      `_gcs.py::read_progress_checkpoint`'s docstring + a new row in `spot-vms-for-backfill.md`'s per-launcher
      conformance table; regression test proves the intentional `None` return
      (`test_read_progress_checkpoint_ignores_cdlap_non_standard_checkpoint_filename`). (b) Hardened
      `DP_VM_PREEMPTED_RECOVERED`: it now emits INFO + `checkpoint_resumed=true` when the relaunch resumed from a
      monotonic checkpoint, vs. WARN + `checkpoint_resumed=false` when it had no usable checkpoint and replayed
      `launch_env` verbatim (the non-force silent-gap condition — force+no-checkpoint already PAGEs earlier in the same
      function). Existing tests updated (`test_preempted_relaunch_replays_captured_launch_env`) + new regression tests
      added for both the resumed and non-resumed classification. QG: 3016 passed, 0 failures. Codex SSOTs updated:
      `/codex/05-infrastructure/spot-vms-for-backfill.md`.

- [x] ✅ [BACKEND] P2. **DONE 2026-07-31 (slot 8) — `deployment-service@b4503ef`** (rebased onto a concurrent slot-2 fix
      to the same file's stale comment, `deployment-service@daf3ad5` — no conflict, cleanly rebased). Make the
      launcher's two best-effort GCS writes reliable — `LAUNCH_PARAMS.json` at create time and the `PREEMPTED` marker at
      shutdown. (a) `LAUNCH_PARAMS.json`: live-swept all 50 `af-backfill-*` `vm-logs/` dirs
      (`gs://deployment-scripts-central-element-323112/vm-logs/`, 2026-07-17..2026-07-31) — **0/29 present before
      2026-07-25, 21/21 present after** (the 3 launched on 2026-07-25 itself, before the fix actually landed that day,
      are also absent — consistent, not noise). This exactly matches
      `vm_tarball_upload_expired_wif_token_interactive_slot_2026_07_25.md`'s already-shipped fix (`gsutil -q cp` →
      `gcloud storage cp`, ADC-backed instead of the CLI's active-account credential) — that fix predates none of the
      "before" sample and postdates all of the "after" sample. Mechanism named: the write WAS silently failing under the
      WIF-token-expiry bug (not a genuine entity-level resume path); it is already fixed, no further code change needed.
      (b) `PREEMPTED` marker: cross-referenced the same 50 VMs against
      `gcloud compute operations list     --filter="operationType=compute.instances.preempted AND targetLink~'af-backfill'"`
      — **5 confirmed preemptions (2026-07-25..2026-07-31), marker missing 5/5 (100%)**, not a one-off. Root cause: this
      launcher hand-rolled its own inline shutdown-script (unlike the 14 other launchers already calling
      `lc_write_preemption_signal_file`) that queried `VM_NAME`/`PROJECT` live via 2 metadata round-trips and shelled
      out to `gcloud storage cp` (multi-second Python-CLI cold start) — both add latency inside the ~30s GCE preemption
      grace window. **Fix**: `lc_write_preemption_signal_file` (`launcher_common.sh`) now takes optional
      `vm_name`/`project` args to bake identity in at launch time (skips 2 of 3 round-trips; backward-compatible —
      omitting both falls back to the original live-metadata form the 14 existing callers still use) and uploads via a
      lightweight curl+retry PUT to the GCS JSON API (the VM's own metadata-server OAuth token) instead of the gcloud
      CLI. `launch-api-football-backfill-vm.sh` now calls this hardened helper instead of its inline duplicate, and also
      gained the `lc_verify_setup_script_freshness` guard (it calls `gcloud compute instances create` directly, so it
      never got this guard automatically — see the new fleet-wide finding below). 6 new tests
      (`TestApiFootballLauncherHardenedPreemptionSignal`, `deployment-service/tests/unit/test_vm_launcher_scripts.py`)
      prove the baked identity, the curl-based upload, and shellcheck/syntax cleanliness of the generated shutdown
      script — full 148/148 `test_vm_launcher_scripts.py` suite green, `quality-gates.sh` green. **New finding, filed
      rather than absorbed as unplanned scope**: investigating WHY the fleet-wide `uts-preemption-signal.service`
      systemd unit (`setup-data-pipeline-vm.sh`, already hardened 2026-07-20/21 with its own retry) also missed 5/5
      surfaced that 139 of 143 launchers (incl. af-backfill before this fix) call `gcloud compute instances create`
      directly and never invoke `lc_verify_setup_script_freshness` — only 4 launchers use the `lc_gcloud_create` wrapper
      that auto-checks it, not the "~80" `launcher_common.sh`'s own comment claims. Could not confirm whether a stale
      GCS copy of `setup-data-pipeline-vm.sh` explains the 5/5 miss (the bucket has no object versioning, no historical
      generation to inspect) — filed as `issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md` with the measured
      evidence + a scoped operator-decision todo (too large — up to 139 files — for this todo to absorb).

- [x] ✅ [DOCS] P1. **Reconcile `utl_uac_reuse_consolidation_remediation_2026_06_10.md`'s 25 open checkboxes against its
      10 ARCHIVED split children — this is almost certainly false-unchecked split residue, not open work.** That
      tracker's own 2026-07-13 banner says its remaining todos were carved into 10 per-phase `assigned_vm: planning`
      plans, that the tracker "is no longer AO-ingestible", that nobody should "dispatch work from here directly", and
      that it should be archived "once every split plan reaches C5". Measured 2026-07-26: all 10 children now live under
      `plans/archive/2026_07/utl_reuse_phase{0..9}_*_2026_07_13.md` and **every one has 0 open todos**
      (`grep -c -E '^\s*-\s*\[ \]'` → 0 on all ten). Spot-verified the hardest case: the tracker still shows Phase 9's
      `deployment-api → deployment-service — EXTRACT the shared registry to UTL` as `- [ ]`, while the archived
      `utl_reuse_phase9_deployment_registry_extract_2026_07_13.md` records it `[x] ✅` shipped
      `unified-trading-library@5926c6f0`, and `unified_trading_library/deployment_registry.py` EXISTS and is exported
      from `unified_trading_library/__init__.py:695`. Walk each of the 25 open boxes: find its owning phase, find the
      corresponding entry in that phase's archived plan, and either flip it `[x]` citing the child's shipped sha (verify
      the sha resolves with `git show` — do not copy the child's evidence line blind) or, if a box genuinely has no
      counterpart in any child, leave it open and say so explicitly in the tracker's Progress Log. Then propose
      archival. **Do NOT archive it** — it carries `locked_by: live-defi-rollout`, and clearing a lock needs an explicit
      `[unlock-plan]` from the operator (ASK, never autonomous). **Done when**: every one of the 25 boxes is either
      flipped with a verified sha or explicitly recorded as genuinely-still-open with a reason, and the tracker's
      Progress Log states an archive-readiness verdict plus the `[unlock-plan]` ask. Repo: unified-trading-pm. Source:
      `utl_uac_reuse_consolidation_remediation_2026_06_10.md`. — DONE (2026-07-26, slot-11): walked all 25 boxes against
      the 10 archived children; 24/25 were false-unchecked split residue (each shipped sha verified via `git show`
      before flipping) and 1/25 (Phase 8's closing archival todo) is genuinely still open — its own split-child copy was
      FOLDED OUT to `plans/epics/infrastructure_master.md` § "Folded-in scope 2026-07-15", which still carries it as an
      open item today. Tracker's Progress Log now states the archive-readiness verdict + the `[unlock-plan]` ask
      (tracker NOT archived — lock untouched, per instruction).

- [x] ✅ [CODE] P3. **DONE 2026-08-03 (slot-4, backend_engineer) — execution-service@8479a77f.** Normalized every
      `service_name` producer to canonical singular `"execution-service"`. Wider than the source doc's 1-file framing:
      all 3 `ManifestWriter(...)` sites were ALREADY singular (`git log --all -S`, never plural — **manifest backfill
      NOT needed**); real drift was the config default + 3 CLI event-setup sites + 2 `DependencyReport(...)` sites (9
      occurrences/5 files) + 9 dependent test-sites/8 files. Also fixed a live silent-skip this drift caused:
      `test_shard_combinatorics.py`'s `SERVICE_NAME` looked up a nonexistent sharding config, masked by `pytest.skip`.
      Left ~50 prose/path/unrelated-namespace hits untouched. **Evidence**: `quality-gates.sh` green (203s, 7811
      passed); runtime log confirms `service=execution-service` emitted. Repo: execution-service. Source:
      `issues/issue_docs_remediation_sweep_2026_06_02.md`. **Follow-up filed** (different repo):
      `issues/deployment_service_execution_service_plural_naming_gaps_2026_08_03.md`.

- [x] ✅ [BUILD] P2. **CHECKBOX-FLIP CLOSEOUT 2026-08-01 (slot-5, infra) — both sub-fixes already shipped BEFORE this
      dispatch, no code change needed.** (a) `MANIFEST_ALIGNMENT_SKIP=true` was added to
      `system-integration-tests/scripts/quality-gates.sh` at `system-integration-tests@19fea221` (2026-06-10,
      "test-harness repo, imports live under tests/ (excluded by the 2026-06-10 alignment-scanner parity change)") —
      this is the correct fix, not the "import them or drop the declaration" framing this todo's own text proposed:
      SIT's manifest-alignment scanner categorically excludes `tests/` (by design, to avoid false build-DAG edges from
      test-only sibling imports — see `check_manifest_import_alignment.py`'s own docstring), and SIT is a pure
      test-harness repo whose entire body is `tests/` (`SOURCE_DIR="tests"`), so EVERY declared dep would always read as
      "not imported" regardless of which two are named — confirmed by re-running the raw checker
      (`check_manifest_import_alignment.py --repo     ../system-integration-tests`), which flags all 10 declared deps,
      not just the two this todo names. (b) `.coverage-floor-exception.md` already exists on origin, added at
      `system-integration-tests@28b2efc9` (2026-06-07), content matches this todo's own ask verbatim (states
      `MIN_COVERAGE=2` is intentional because SIT is a cross-repo integration harness whose "source" is `tests/` itself
      — a self-referential coverage floor would be circular). **Verified against the actual done-when**: fresh
      `cd system-integration-tests && bash scripts/quality-gates.sh` (full run, no skip flags) →
      `✅ ALL QUALITY GATES PASSED (120s)`, sentinel written at `system-integration-tests@66ea65dc`. Both named
      sub-failures are gone; this todo's premise (that they are "standing") was stale as of dispatch — both fixes
      predate the 2026-07-26 batch-1 draft by 6+ weeks. Repo: system-integration-tests. Source:
      `issues/issue_docs_remediation_sweep_2026_06_02.md`.

- [x] ✅ [CODE] P3. **Reconcile UAC's stale `defi_position.py` liquidation threshold to the registry-driven form.** —
      unified-api-contracts@194f3f7f. `is_at_risk` now resolves
      `LIQUIDATION_PARAMS_REGISTRY[AAVE_V3].     health_factor_critical` (`1.15`) instead of hardcoded `1.1`, mirroring
      execution-service's local copy. Grepped + read every consumer —
      `execution-service/execution_service/models/position.py` is a bare re-export, no consumer depended on `1.1`. Added
      `tests/internal/unit/domain/execution_service/test_defi_position.py` pinning `1.15`. QG green. Repo:
      unified-api-contracts. Source: `codex_violations_ratchet_to_five_2026_06_10.md`.

- [x] ✅ [CODE] P3. **Rename UAC's `infura_*` Starknet endpoint-template key away from the banned provider name.** —
      unified-api-contracts@862ff5a6. Premise stale at dispatch: the `infura_compatible` template was already
      **deleted** (not renamed) 2026-06-09 as D8 (UAC@8a117153, no consumer referenced the key) — nothing left to
      rename/migrate. Re-`rg -rni infura unified-api-contracts/` found one surviving hit (a comment naming the banned
      provider in `_defi_chain_data.py`); reworded it. `rg 'infura' unified-api-contracts/` now 0 hits (done-when met).
      QG green. Repo: unified-api-contracts. Source: `issues/issue_docs_remediation_sweep_2026_06_02.md`.

- [x] ✅ [INFRA] P2. **Drive deployment-api's codex violations from 5 to 0.** — deployment-api@4c4b007. Premise was
      stale at dispatch: file-size/function-size were already cleared (moved to a separate zero-tolerance gate, already
      passing); honest `QG_SLICE=lint-codex` measurement at pickup was `V=3` across 3 classes (imports-inside-functions,
      direct-cloud-SDK, broad-except), not 5 across 4. All 3 cleared to `V=0`: imports-inside-functions (~104 sites —
      genuine lazy-import sites got a per-line `# noqa: imports-inside-functions` with a stated reason; trivial stdlib
      imports hoisted to module top-level); direct-cloud-SDK (2 comment-only false positives reworded off the literal
      grep match; genuine sites got the sanctioned `# noqa: cloud-sdk-direct` marker, ordered so ruff's own TID251 rule
      still parses it — a self-caused regression from that reordering was caught and fixed in the same pass, plus a
      missing RUF100 per-file-ignore); broad-except (4 sites with a bounded stdlib exception surface narrowed in place —
      one narrowing missed a `TypeError` from a FastAPI `Query` object and was caught + fixed by the full test run; 7
      files wrapping a genuinely unbounded vendor-SDK/pandas-manifest exception surface documented + excluded via a new
      `BE_EXCLUDE_GLOBS`, per `QUALITY_GATE_BYPASS_AUDIT.md` § "Broad except Exception exceptions").
      `CODEX_MAX_VIOLATIONS` ratcheted 3→0. Full `quality-gates.sh` green (5077 passed). Also ratcheted the DTZ/TID251
      `ruff_rule_ratchet_baseline.yaml` (dtz 11→10, tid251 20→19) — unified-trading-pm@<see PM flip commit>. Repo:
      deployment-api. Source: `codex_violations_ratchet_to_five_2026_06_10.md`.

- [x] ✅ [SCRIPT] P2. **DONE 2026-08-02.** Measured fleet-wide lifecycle-marker coverage across all 25 repos in the
      standard fleet (~1998 `scripts/` files): 3 files (2 repos) missing a mandatory field, 96 files with an `Epic:`
      value outside the epic registry, 2 files misusing `Delete-when: NA` on a non-`permanent` lifecycle, plus a
      supplementary 136 files with an invalid `Lifecycle:` enum value (mostly the `one-off` vs `oneoff` near-miss).
      Per-repo table + verdict + recommended sequencing written into `repo_scripts_governance_audit_2026_06_18.md` §
      "Fleet-wide lifecycle-marker coverage measurement (2026-08-02)". **Verdict: gate-clearable — NO** (down from 11+
      repos at the 2026-07-15 baseline, but not yet clean; the checker would still fail CI fleet-wide on
      invalid-Epic/invalid-Lifecycle/na-misuse even once the missing-field precondition clears). Did **not** build or
      wire the checker, per scope. Source: `repo_scripts_governance_audit_2026_06_18.md`.

- [x] ✅ [BUG] P3. **Confirm or rule out the strategy-service → market-tick-data-service tier violation hiding in a
      Dockerfile.** **VERDICT (a): zero live MTDS imports — already resolved, no code change needed this session.**
      Re-verified fresh against current `strategy-service` HEAD across every surface this todo names: (1)
      `grep -rn     "import market_tick_data_service\|from market_tick_data_service"` over all `.py` files → 0 hits; (2)
      `pyproject.toml` → no `market-tick-data-service`/`market_tick_data_service` entry; (3) `uv.lock` → no
      `market-tick-data-service` package entry; (4) `Dockerfile` → no `COPY market-tick-data-service/` (Pattern-A
      single-context `COPY . .` only, with an explanatory comment on the removal); (5) `cloudbuild.yaml` → no
      `stage-siblings` step or MTDS vendoring (only a comment documenting the prior removal); (6) `buildspec.aws.yaml` →
      MTDS clone explicitly removed (comment: "market-tick-data-service is NOT cloned here (Pattern-A normalization
      2026-07)"). This confirms — and is consistent with — the archived source doc's own resolution:
      `plans/archive/issues/service_dockerfile_pattern_normalization_2026_06_17.md` `resolved_by` field states the
      Pattern-A normalization fan-out (2026-07-28) already dropped the vestigial `COPY` + `stage-siblings` step as a
      side effect, after confirming the real dependency was removed 2026-06-10 (`strategy-service@d1f5a6a8`). This todo
      in the active plan was stale (duplicate of already-landed work) — no follow-up todo needed. Repos:
      strategy-service (read-only verification). Source: `issues/service_dockerfile_pattern_normalization_2026_06_17.md`
      (archived, resolved).

- [x] ✅ [DOCS] P2. **Land the 3 bounded codex FIX-STALE corrections this audit plan has carried unowned since
      2026-06-01.** (a) **AUDIT-03 F-45**: code wins — the events GCS path keys on `instance_id`; `correlation_id` is a
      column, NOT a path key. Find every codex doc claiming `correlation_id` is a path key and correct it to the
      implemented `instance_id` path semantics (verify against the writer's actual path construction before editing).
      (b) **AUDIT-03 F-06**: declare `/codex/04-architecture/custody-providers.md` the **entity-governance SSOT**; the
      entities are **Odum Research UK** + **Odum Group Cayman**; scrub every stale Elysium reference (Elysium is a
      removed provider per CLAUDE.md). (c) Fix the malformed hive-partition path examples in the relevant codex doc to
      canonical `key=value` form (doc-fix ONLY — the corresponding GCS data remediation stays operator-deferred and is
      NOT in scope here). **Do NOT build the URDI grep CI guard** also listed in that source doc — it lands in
      `base-service.sh`, a deferred contention hotspot in this batch. **Done when**: all three corrections are shipped,
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is no worse than before, and each corrected claim
      is verified against code/registry rather than restated. Repo: unified-trading-pm. Source:
      `codex_vs_repo_docs_ssot_audit_2026_06_01.md`. — **DONE 2026-08-02 (slot 7, data_engineering) — already resolved
      as no-op, this todo was stale**: this exact source doc already carries all 3 items flipped `[x]` since 2026-07-27
      (Phase-2, `unified-trading-pm@7c3fcfe68` — "flip 3 AUDIT-03/gcs_hive codex-migration items (all verified no-op)"),
      one day AFTER this plan (created 2026-07-26) copied the still-open finding across — the two tracks diverged and
      this copy was never updated. Independently re-verified against current code/registry before trusting the prior
      resolution (per this todo's own done-when bar): (a) `rg correlation_id codex/` — every hit is a log field / column
      / PubSub attribute / function param, none describe it as a GCS path key; the events path keys on `instance_id`
      exactly as claimed. (b) `custody-providers.md`'s sole `Elysium` reference is the
      `pod-elysium-client-onboarding.md` link (the client POD), not the removed data provider — no stale ref to scrub;
      the entity-governance SSOT already lives in `org-fund-client-entity-model.md` +
      `capital-structure-and-regulatory.md`, not custody-providers.md (grafting it there would violate the plan's own
      no-duplicate-SSOT rule). (c) Sampled hive-partition path examples in
      `sports-data-source-coverage-matrix.md`/`sports-data-types-catalog.md` — all canonical `key=value` segments
      (`by_date/day=*/entity=.../league=...`, `asset_group=sports`), nothing malformed. **No codex edit needed** — 0
      corrections to ship, all three verified already-correct. `run_hygiene_sweep.sh --ci --no-regen` baseline: 0 hard
      failures (1 pre-existing unrelated soft warning), unchanged by this checkbox-only edit.

- [x] ✅ [INFRA] P1. **Produce the resource-by-resource classification of the prod terraform drift backlog (READ-ONLY —
      the apply stays operator-only).** `terraform/state/prod` (`deployment-service/terraform/gcp`) shows
      21-add/18-change/0-destroy of committed-but-un-applied resources (BigQuery `feature_external` tables,
      `paper_stream` job/cron, `batch_live_smoke_matrix`, the recovered `expected_universe_v2` run.invoker IAM,
      `odum_portal` domain mapping, defi_forward_poll updates). Re-run `tofu plan` FRESH first — the 21/18 counts are as
      of 2026-06-23 and may have shifted — then walk the diff resource by resource and classify each as INTENDED (should
      apply), STALE/ABANDONED (should be removed from the tree instead), or DELIBERATELY-STAGED-AHEAD-OF-A- CUTOVER
      (should stay unapplied, with the cutover named). This todo is **safe-idempotent by construction**: `tofu plan` is
      read-only and writes no state, so no `[OPERATOR]` gate is required for it. **Do NOT run `tofu apply`** — a prod
      apply is human-only, and applying blind risks reverting or half-shipping unrelated resources. **Scope guard**: two
      cross-cutting batch todos separately own the wave-launcher job image pin and `lifecycle_catalogue_scheduler.tf`'s
      bucket-name fix; classify those rows but do not edit those files. **Done when**: the source doc carries a dated
      per-resource table with the three-way classification and a recommended apply order, and an `[OPERATOR]`-tagged
      follow-up todo exists for the gated apply itself. Repo: deployment-service (read) + unified-trading-pm (the
      table). Source: `issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md`. — DONE (2026-07-26, slot-11): fresh
      `ENV=prod ./tofu.sh plan` shows 10-add/67-change/0-destroy — an entirely NEW set, the whole 2026-06-23 backlog is
      gone. Classified all 12 real resources INTENDED (a defi_removal_probe feature bundle, a Firestore- migration IAM
      grant, 4 missing canonical buckets, 2 t1_recon label fixes) with a recommended apply order; the other 65 are
      cosmetic `client`/`client_version` Cloud Run metadata churn (not real drift — filed as a separate code-fix
      follow-up, not an apply candidate). **Found + filed a blocking gap**: `unified-trading-sa` lacks read IAM on 112
      other resources (58 buckets/22 secrets/26 project-IAM/6 pubsub), including the 2 scope-guard-named rows
      (wave-launcher, lifecycle_catalogue bucket-IAM) — could not classify those, filed as its own `[OPERATOR]`
      IAM-grant follow-up. 3 new todos filed in the source doc (2× `[OPERATOR]`, 1× `[INFRA]`).

- [x] ✅ [INFRA] P2. **2026-07-28 retag** (was `[OPERATOR]` — the gated delete already EXECUTED under the operator's
      explicit autonomous-mode grant + the standing RULE-11 approval on record below, so no live operator gate remains;
      retagged to the reflecting `[INFRA]` tag per this file's convention for shipped infra work). **DONE 2026-07-28 —
      RULE-11 prove-then-retire the two superseded plan-hygiene runtimes EXECUTED**, under an explicit operator
      autonomous-mode grant (this specific execution named: "archive 9 previously-locked docs..., including RULE-11
      execution") on top of the standing approval below. (a) SHIPPED: `.github/workflows/plan-health-agent.yml` + its
      `scripts/self-hosted-runners/hosted-baseline/` template twin both dropped the `schedule:` trigger + the entire
      Haiku `plan-health`/`notify` job pair — only the `pull_request`-triggered `plan-health-gate` hard gate remains
      (verified YAML-valid, both files byte-identical post-edit). (b) SHIPPED: live-deleted
      `uts-prod-plan-hygiene-sweep-cron` (Cloud Scheduler) then `uts-prod-plan-hygiene-sweep` (Cloud Run Job) via
      `gcloud scheduler jobs delete` / `gcloud run jobs delete` (both
      `--project=central-element-323112 --region/location=asia-northeast1`); confirmed gone via
      `gcloud run jobs describe`/`gcloud scheduler jobs describe` (`NOT_FOUND`) and `gcloud run jobs list` (absent — the
      two `hygiene` hits remaining are unrelated `uts-prod-dp-manifest-hygiene-{changed,full}` data-pipeline jobs).
      Removed `deployment-service/terraform/gcp/hygiene_sweep_scheduler.tf` + both repos' copies of
      `cron_hygiene_sweep_entrypoint.sh` (`git rm`); replaced the 2 corresponding `import {}` blocks in
      `deployment-service/terraform/gcp/_imports_reconcile.tf` with removal comments (matching this file's own
      documented convention for a config-removed import target); removed the stale `cloud_run_job_registry.py` entry so
      it stops rendering as a dangling job in deployment-ui/cockpit. (c) SHIPPED: both
      `/codex/11-project-management/plan-hygiene.md` and `/codex/12-agent-workflow/plan-hygiene.md` rewritten to the
      timer-on-central model (removed stale `code_refs`, corrected the cron schedule table, added the "Daily deep
      reconciler" retirement record + corrected the now-inverted reaper/reconciler ordering note); also fixed 2 corpus
      referrers describing the retired job as live (`/codex/04-architecture/agent-orchestrator-alerting.md`,
      `/codex/11-project-management/active-plan-inventory-tracker.md`) and appended a retirement note to
      `plans/epics/plan_hygiene_master.md`'s original implementation record. **Original approval on record
      (2026-07-27)**: The daily deep reconciler that replaced them is live: `agent-orchestrator`'s
      `plan-reconciler.timer` (`OnCalendar=*-*-* 01:00:00 UTC`) hits `POST /api/plan-health/dispatch`, is watched by
      `plan_reconciler_liveness_canary.py` which PAGES if the timer goes inactive or no successful run lands in >26h,
      and `/docs-reconcile` rides the same cadence via `docs-reconciler.timer` (both verified live 2026-07-24 in
      `issues/plan_quality_four_line_defense_architecture_2026_07_23.md`). So the prerequisite is satisfied. Retire in
      this order: (a) drop the `schedule:` trigger + the Haiku drift-detection steps from
      `.github/workflows/plan-health-agent.yml` AND its `scripts/self-hosted-runners/hosted-baseline/` template twin —
      **KEEP** the `pull_request` `plan-health-gate` job and the escalate-on-gate-failure path; (b) delete the Cloud Run
      job `uts-prod-plan-hygiene-sweep` + its Cloud Scheduler +
      `deployment-service/terraform/gcp/hygiene_sweep_scheduler.tf` + `cron_hygiene_sweep_entrypoint.sh` (this job has
      been failing ~every other day with `Container called exit(1)` and ZERO stdout since 2026-06-12, dying before its
      own inbox-ping failure handling — it is not providing the signal anyone thinks it is); (c) update CLAUDE.md §
      "Plan Hygiene" + `/codex/11-project-management/plan-hygiene.md` to the timer-on-central model.
      **`[OPERATOR]`-tagged because (b) DELETES live prod cloud resources** — the delete-safety justification is RULE-11
      prove-then-retire (the replacement is live, canary-watched, and independently verified), but the operator confirms
      before the delete. Never hand-edit a per-repo workflow copy — edit the template then
      `rollout-workflow-templates.sh`, and the rollout is not done until every copy is committed and pushed. **Never
      write the literal skip-ci marker** in any commit message or body here. **Done when**: (a) is shipped with the PR
      gate intact, (b) is confirmed deleted by the operator with `gcloud run jobs list` showing the job gone, and (c)
      both docs describe only the live model. Repos: unified-trading-pm, deployment-service. Source:
      `/plans/archive/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md`. **Operator approval now on
      record (2026-07-27)**: `june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED #21 — "RULE-11 — APPROVED
      (drop `schedule:`/Haiku, delete the Cloud Run hygiene-sweep job)." (Historical context only — as of 2026-07-28 the
      job, scheduler, terraform, and entrypoint files named above are all deleted; see the DONE entry at the top of this
      todo for the actual execution record.)

- [x] ✅ [CI] P2. **DONE 2026-08-02 (slot-5, infra) — unified-trading-pm@f3afa397d.** Added a PM-only, content-sentinel-
      gated "Plan hygiene hard gate" step (`run_hygiene_sweep.sh --ci --no-regen`) to the `checks` leg of
      `python-quality-gates-v2.yml`, gated on repo==PM + the leg's existing skip_slice/QG_CONTENT_HIT fast-paths.
      **Prove-then-retire evidence**: full sweep locally = 0 hard failures; a scratch no-frontmatter file reproduced the
      exact hard-failure exit 1 the old job caught (discarded, never committed). Then retired the standalone job:
      deleted `plan-health-agent.yml` + its hosted-baseline twin, pruned `MANIFEST.tsv` + the catalog script's entry,
      regenerated `CICD-WORKFLOW-CATALOG.md`. Real upgrade not lateral: the old job was advisory-only (not a required
      check); the fold makes hygiene an ACTUAL blocking PR gate. Auto-fix-and-escalate isn't carried over (this step
      only detects) but isn't a gap — `ldr-docs-gate.yml` (hourly) + the daily `plan-reconciler` already independently
      cover that. Updated both plan-hygiene codex SSOTs + the one dangling `AGENTS.md` mention. `actionlint` clean.
      Repo: unified-trading-pm. Source:
      `/plans/archive/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md`.

- [x] ✅ [BACKEND] P2. **DONE 2026-08-01 (slot-4) — Serve the generated L0 doc-graph from the AO dashboard for central
      human visibility.** — agent-orchestrator@517a0bc. `GET /api/docs/doc-graph` (`server/routes/docs.py`, auth-gated
      via the same `AUTHED_DEPS` every other dashboard API route uses) serves the current on-disk
      `DOC_GRAPH.generated.html` from the sibling PM checkout — read-only, serve-latest-on-disk, never regenerates or
      commits the gitignored artifact. New `/doc-graph` dashboard page (`dashboard/src/DocGraph.tsx`, wired into
      `App.tsx`'s Router + a "Doc Graph →" button on `Landing.tsx`) fetches it with the existing Bearer-token auth flow
      and renders via `<iframe srcDoc>` (a bare `<iframe src>` can't carry the auth header on direct navigation, so the
      client-side-fetch-then-srcDoc pattern is required — same reasoning as `FleetGit`/`FleetKpis`'s authenticated-fetch
      pages). Dashboard `tsc --noEmit` + vitest (171 tests) and backend `basedpyright`/`pytest`/`ruff` all green under
      `quality-gates.sh`. `scripts/docs/gen_doc_graph.py` already produces `DOC_GRAPH.generated.html` (self-contained,
      gitignored, per-host: 1,119 nodes / 3,113 `related`+`referenced_by` edges, 3D force layout, facet filters +
      search + neighborhood isolate + doc panel, shipped `pm@d03703d0e`). The one remaining piece of the source todo is
      serving that file as a static route from the agent-orchestrator dashboard so a human can open it without a local
      checkout. Keep it READ-ONLY and regenerate-on-demand or serve-latest-on-disk — do NOT commit the artifact (it is
      deliberately gitignored + per-host so there is no fleet-shared multi-writer hotspot). **Scope guard**: serve it
      from the **AO dashboard**, not deployment-ui — a sibling todo in this batch owns deployment-ui's test surface.
      **Done when**: a documented dashboard URL renders the current graph, the route is auth-gated the same way the rest
      of the dashboard is, and nothing gitignored got committed. Repo: agent-orchestrator. Source:
      `l0_doc_index_generator_2026_06_24.md`.

- [x] ✅ [SCRIPT] P3. **Add the on-demand L0-index stale-check wrapper an agent calls before grepping.** — DONE
      2026-08-03 (slot-6, infra), `unified-trading-pm@54d7779a4`. Added `scripts/docs/refresh-doc-index.sh`: a thin
      wrapper that resolves the calling clone's own generator + venv and runs `gen_doc_index.py --stale-check`
      (regenerates only on content change, ~1.4s; no-op when fresh), closing the FF-cron's inter-tick staleness window
      for the "grep the L0 index FIRST" rule. Made the generator's write atomic (`gen_doc_index.py::_atomic_write_text`
      — temp sibling + fsync + `os.replace`) so the cron and this wrapper can regenerate the same per-clone file
      concurrently without ever leaving a truncated index; concurrency test
      `test_atomic_write_never_leaves_truncated_index_under_concurrency` (8 writers + a reader) proves 0 partial reads.
      CLAUDE.md § Doc-retrieval one-liner now points at the wrapper. Shipped via the dirty-deps direct-push carve-out
      (quickmerge blocked by the unrelated stalled aiohttp-CVE fan-out, tracked in
      `aiohttp_canonical_floor_stale_vs_mtds_cve_fix_2026_08_03.md`). Source: `l0_doc_index_generator_2026_06_24.md`.

- [x] ✅ [TEST] P3. **DONE 2026-07-31 (slot-13) — NOT REPRODUCIBLE, closing.** Re-ran the reproduction recipe against
      today's dependency universe: `uv lock --upgrade` (full fleet-wide upgrade, not one-by-one — deliberately broader
      than the original ask, to give the failure every chance to resurface) then
      `.venv/bin/python -m pytest tests/unit/notifiers/test_router_synthetic_suppression.py -v` → **8/8 passed**,
      including `test_synthetic_false_does_not_log_suppressed_event`. Ran the FULL `tests/unit/` suite under the same
      fully-upgraded deps too (907 passed, 3 failed) — the 3 failures are `test_safety_ops_routes.py` mock-mode
      seed-data assertions (`len(rows) >= 1` on an empty list), unrelated to synthetic suppression or this todo.
      Upgraded set included `fastapi`/`starlette` (the exact cap still active fleet-wide on 2026-06-18 when this test
      first failed — confirmed via this doc's own "Breaking-version caps" table above — since lifted fleet-wide per this
      doc's own DONE entry), `vcrpy` 8.2.1→8.3.0, `pytest` 9.0.3→9.1.1, `pydantic` 2.12.5→2.13.4, `web3` 6.20.4→7.16.0,
      and ~60 other packages. **Conclusion**: the original 2026-06-18 failure was tied to that exact 1.5b
      validation-pass dependency snapshot (most plausibly the fastapi<0.137/starlette<1.3 cap that was still live then),
      which the fleet has since moved past through the many CVE-remediation + cap-lift bumps this same issue doc tracks.
      No code or test change needed — reverted the exploratory `uv lock --upgrade` (`git checkout -- uv.lock` +
      `uv sync`) so alerting-service ships no dep drift from this investigation; tree confirmed clean before `/done`.
      Repo: alerting-service (investigation only, zero-diff). Source:
      `issues/cve_affected_pinned_deps_remediation_2026_06_18.md`.

- [x] ✅ [INFRA] P3. **DONE 2026-08-04 — `unified-trading-pm@1fa747856`.** Smoke-test the stash-pile classifier before
      anyone trusts its auto-drop classes (dry-run only, no `--apply`). Ran
      `bash scripts/dev/audit-stash-pile.sh --repo unified-trading-pm` (dry-run, nothing dropped/popped/applied) against
      the host's shared root-clone stash pile — **76 stashes** (grown from the 31 the parent plan measured against),
      classifying to **1 `redundant`** / 0 `empty` / 0 `foreign-park` / 75 `genuine-WIP`. The done-when's "≥3
      hand-verified redundant calls" does not hold against the current data (there is only 1 such call to verify, not an
      oversight) — hand-verified that 1 as a TRUE POSITIVE (byte-identical vs `origin/live-defi-rollout`, no
      captured-untracked 3rd parent) and broadened to 5 additional `genuine-WIP` boundary-case spot-checks (smallest
      file-counts) to compensate, including one case (`stash@{37}`) that validates the untracked-file safety net
      actually fires on an empty tracked diff. Confirmed base-ref resolution (`origin/main` for agent-orchestrator,
      `origin/live-defi-rollout` otherwise) correct both by source read and by this run's own `base-verified: yes`.
      **Verdict: classifier trustworthy: YES** (zero false positives found; caveat: redundant-class n=1, re-verify when
      the pile's redundant count grows). Full report:
      `plans/archive/issues/stash_audit_reports/stash-audit-ip-172-31-5-118-20260804.md`. No stash dropped, popped, or
      applied. Repo: unified-trading-pm. Source: `stash_pile_workspace_cleanup_2026_06_03.md`.

- [x] ✅ [INFRA] P3. **DONE 2026-07-30 — `unified-trading-pm@59756e802`.** Folded a WARNING-only `--max-stash-age`-style
      signal into `scripts/dev/slot-git-status-report.sh`: a new standalone detector
      (`scripts/dev/stash-pile-detect.sh`, mirrors the existing `ff-starvation-detect.sh` pattern) measures each repo's
      stash count + oldest-entry age; the reporter pings the slot inbox (deduped per episode, reusing
      `post_starve_ping`, now with a distinguishing log label so it's not confused with the FF-starvation watchdog) when
      either threshold trips. Never touches `git stash` content — no read of stash payloads, no apply, no drop.
      Thresholds picked from a measured cross-slot distribution (one laptop, 4 populated slots + main-workspace clone,
      2026-07-30): normal churn sits at ≤11 entries / ≤10 days oldest, a genuinely regrown pile sits at 33+ entries /
      5-8 weeks oldest — chose **count>15** and **oldest>14d** (buffer above normal-churn ceiling, below regrown-pile
      floor). Documented with the full measured table in `/codex/05-infrastructure/per-tab-worktrees.md` § "Stash-pile
      regrowth signal". **Validated**: fires on the real 45-entry slot-1 pile, silent on a clean repo and on a
      never-stashed repo, fires on a synthetic age-only trigger (1 entry, backdated 20 days via `GIT_COMMITTER_DATE`)
      independent of count, correct exit codes on bad args, full end-to-end dry-run against a fabricated workspace
      (unreachable orch URL) confirms the script never fails/hangs the report. Surfaced by, and shipped alongside, a
      full stash-pile audit of every populated slot on this laptop —
      `plans/active/issues/unified_trading_pm_stash_pile_accumulation_2026_07_26.md` has the findings.

- [x] [REVIEW] P3. ✅ **DONE 2026-08-02 (slot-12)** — determination: NOT sufficient as they stood. Verified from the
      actual code (not the skill's own prose): `check_reference_paths.py` DOES scan body text corpus-wide, but
      `run_hygiene_sweep.sh` invokes it `--quiet` (suppressing the itemized violation list) and it's a shrinking-ratchet
      check with substantial slack (baseline 901, live 913 as of 2026-08-02) — a moderate single-move regression (this
      todo's own cited 78/66/3 incidents) can land inside that slack without ever failing the gate, which is exactly why
      none of the three cited incidents were caught by a `/plan-reconcile` pass. Extended
      `cursor-configs/skills/plan-reconcile/SKILL.md` with Phase 1 hunter 8 ("Moved-doc referrer hunter") — a
      git-log-diff-driven, ratchet-independent per-move referrer check. Full evidence + determination recorded in
      `issues/reference_path_convention_2026_07_23.md`'s own matching todo (now flipped). `pm@<commit-pending>`.

- [x] ✅ [INFRA] P2. **Add prefix-scoped lifecycle rules to the deployment-scripts bucket + a cross-bucket soft-delete
      bloat audit.** Rehomed 2026-07-27 from `issues/issue_docs_remediation_sweep_2026_06_02.md`'s "Operator-gated
      infra" section as a true orphan. **RESOLVED 2026-08-02 (slot 7, infra):** lifecycle-rule half is **STALE PREMISE,
      no TF change** — the `log-archive/`>90d "sketch" this todo names is the ORIGINAL proposal, but
      `/plans/archive/issues/deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md` shows the operator overrode
      it same-day with a stricter flat 30d cap on every retained prefix incl. `log-archive/`, already TF-codified
      (`deployment-service@75012d3`) and live in `main.tf` today — drafted the 90d split, caught the conflict, reverted
      it (would have silently loosened a deliberate live decision). Bloat-audit half **RUN**: `gcs_bucket_stats.py` (no
      `--bloat_pct` flag — it's a CSV column) walked 103 buckets, 75 non-empty, 64.69 TiB, via Cloud Monitoring (no
      object-walk); CSV in task transcript. One real finding tracked, not dropped: `deployment-scripts` itself reads
      94.7% bloat (9.2/9.7 TiB soft-deleted) — same shape as the archived 2026-06-01 incident, smaller scale, consistent
      with the retention drift fixed same-day in
      `issues/deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md` (live retention confirmed `0`;
      residual = expected 7d bleed-off). Follow-up verification todo added there (same bucket/drift, one home). Other
      audited buckets are intentional versioning or already-remediated 2026-06-02 offenders holding steady. Repo:
      deployment-service (audit + doc only, no code change). Source: `issues/issue_docs_remediation_sweep_2026_06_02.md`
      (deployment_scripts_bucket).

- [x] ✅ [CODE] P3. **DONE 2026-08-04 — `deployment-api@4c394e9` + `deployment-ui@10d2a60`.** Built GAP G-TRACE.
      `GET /api/data-status/pipeline-trace?instrument&date&asset_group` (orchestrates the existing
      `lookup_capture_status_for_shard` per-hop, no new manifest-read logic) threads one instrument/date through all 8
      hops (IS→MTDS→MDPS→3x features families→strategy→execution) and returns per-hop `capture_status` + `stuck_at`.
      Live-verified against real GCS data (MTDS/MDPS real `captured` + timestamps for a real instrument, 2026-08-04); 5
      backend unit tests. `PipelineTraceCard` added to deployment-ui's `DataStatusTab.tsx` (unconditional, matching
      `HonestCoverageCard`). `pw:L2 ✓` (3/3 new + 48/48 matched specs, 0 regressions) | regression:
      `tests/smoke/pipeline_trace_card.spec.ts`. Vitest `PipelineTraceCard.test.tsx` (6/6) closed a global
      branch-coverage floor miss the new component caused (63.62%→64.21%, floor 64%). Both repos full `quality-gates.sh`
      green, both shas confirmed ancestors of `origin/live-defi-rollout`. Repos: deployment-api, deployment-ui. Source:
      `issues/issue_docs_remediation_sweep_2026_06_02.md` (e2e-pipeline-manifest-wiring, G-TRACE).

## Deferred — real AO-eligible work held back, with the reason (per the non-batchable taxonomy)

**CONFLICT-GATED** (a competing live claim on the same file/mechanism — re-checkable in a future batch once the other
side ships or is superseded; this is the ONLY category a batch2 can convert):

1. **MTDS ungated test families / `PYTEST_UNIT_DIR`.** `codex_violations_ratchet_to_five_2026_06_10.md`'s `[TEST] P2`
   says set `PYTEST_UNIT_DIR="tests/"` and "absorb any newly collected failures in the same unit". The cefi-tranche doc
   `issues/mtds_ungated_test_families_2026_07_17.md` (`asset_group: [cefi]`, `status: open`) prescribes a DIFFERENT
   approach to the same file — widen it to the specific `market_interface` unit/adapters/clients/schema_validation/cli
   dirs — and GATES it behind two `[BACKEND] P1` todos fixing 8 + 14 currently-FAILING tests first. Drafting the
   whole-tree version would immediately red MTDS's QG on 22 known failures. **Parked as an operator question, not
   guessed at.** **RESOLVED 2026-07-26** (operator decision #34, cefi's narrower approach won) **and shipped
   2026-07-31** — see `/plans/archive/issues/mtds_ungated_test_families_2026_07_17.md` (archived, all 5 todos done).
2. **PM `base-service.sh` / `base-library.sh` items (4 of them).** The domain-client base-gate retarget
   (`unified_domain_client` → `unified_trading_library.domain`), the pip floor bump (CVE-2026-3219/-6357/PYSEC-2026-196
   ignore drops), the cryptography/idna/CVE-2026-4539 re-check, and the uv drift-guard all edit
   `scripts/quality-gates-base/base-service.sh` and/or `base-library.sh`.
   `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` item (3) evaluates adding a lint step to
   `base-service.sh`, and `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md` touches `base-library.sh`. Those two files
   are a multi-tranche hotspot with no serialisation rule — parked. **Ruled 2026-07-26** (resolved
   `autonomous_session_operator_decisions_2026_07_25.md` entry #36, option A): declare
   `scripts/quality-gates-base/base-service.sh` + `base-library.sh` a serialized resource — one owning plan at a time.
   Batch these 4 deferred infra items (domain-client retarget, pip floor bump, cryptography/idna re-check, uv
   drift-guard) into one unit in the NEXT infra batch (`sequential: true`, since they share these 2 files), rather than
   continuing to park them individually batch over batch.
3. **Moving the `0.10.8` constant into `resolve-canonical-versions.py`** — same `base-service.sh`/`base-library.sh`
   contention (the constant lives in 3 hardcoded sites, 2 of them there). **RESOLVED 2026-08-10:
   `infra_satellite_ao_dispatch_batch9_2026_08_09.md` todo 1, unified-trading-pm@e5697ac5c — UV version centralization
   shipped.**
4. **deployment-ui `DATA_PIPELINE_SERVICES` (GAP G-UI).** Stale `features-cefi/defi/tradfi/prediction-service` names +
   omitted strategy-service in `DataStatusTab.tsx`. `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` item (B)
   already edits `DataStatusTab`/`HonestCoverageCard` for a different change. Same file, two batches — parked.
5. **`managed-by` launcher label standardization.** Touches `deployment-service/scripts/vm/launch-*.sh` (adjacent to
   this batch's `PROGRESS.json` rollout, which edits the shared launcher lib those scripts source) AND Cloud-Run job
   terraform (which `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` also touches). Low value on its own —
   the source doc says `launched_by` already answers the operator's "who launched this" question.
6. **repo_scripts DEPRECATE remediation (~10 named scripts' cloud-discipline gaps).** Subsumed by
   `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` item (k)'s broader "cloud-agnostic sweep of ~60 scripts
   (`google.cloud`/`boto3` → `get_storage_client()`) + ~30 inline bucket literals → `resolve_bucket_name`". Same fix
   class, wider scope, already claimed.
7. **fastapi/starlette cap lift + the pyarrow/twisted/mako/ujson pip-audit follow-ups.** Both edit
   `workspace-constraints.toml` + `canonical-dependency-manifest.json`, and the starlette one additionally needs UTL's
   `_IncludedRouter` route-introspection fix plus 15 repos' pyproject + atomic re-locks. Dep-manifest contention plus
   genuinely too large for a batch todo.
8. **MTDS >900-line file tail (12 modules).** Splitting them touches `market_tick_data_service/market_interface/`, which
   four currently-active batches (`cefi` batch1, `defi` batches 2/3/4) are editing. High collision.
9. **The zero-checkbox corpus sweep and the reference-path `format_count` / `existence_count` baseline drains.** All
   three are corpus-wide multi-hundred-file edits that would race the concurrent per-tranche `/plan-reconcile` and
   `/ag-closeout-audit` runs (this very run fixed 9 docs in this tranche today, and sibling tranche runs are live).
10. **The two reference-path fixes blocked on splitting a SPORTS doc**
    (`issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` at 1216L and
    `sports_satellite_ao_dispatch_batch2_2026_07_24.md` at exactly 1000L, both blocked by `check_line_caps.sh`'s
    no-exceptions-on-touched-files rule). Both splits are claimed by sports batches 3 and 5.

**RESOLVED BY LOGIC — do NOT re-draft these; cite the existing answer instead** (the evidence made exactly one answer
provably right, per the skill's auto-resolve bar):

11. **`vm_billing_waste`'s P3 "was dropping the CME BTC/ETH OPT atom deliberate?"** — **YES, operator-ruled.**
    `tradfi_consolidated_closeout_2026_07_18.md:196-197` states: "**CME BTC/ETH/MBT/MET futures** — FUTURES ONLY, no
    crypto options (operator 2026-07-21 'no CME option for BTC and ETH'; `option_underliers={ES}`)." So CME BTC/ETH
    options coverage did not quietly go from "expected, failing" to "no longer expected" — it was explicitly narrowed by
    an operator decision 4 days before the audit that raised the question. That P3 todo can be closed citing this, not
    dispatched.
12. **`issue_docs_remediation_sweep`'s `[INFRA] P2 tofu apply vm_log_archival_scheduler.tf`** — the vm_log_archival half
    is **already applied**: `infra_capture_and_devops_leftovers_2026_07_06.md` records it `[x] ✅` verified 2026-07-07
    (`deployment-service@3cd0b1d`, Cloud Run Job `vm-log-archival-prd` + Cloud Scheduler ENABLED `0 2 * * * UTC`,
    Terraform `vm_log_archival_scheduler.tf`, runbook attesting ENABLED), and
    `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s own Deferred section independently reached the same
    conclusion. The `vm_serial_capture_scheduler.tf` + `api_host_auto_reboot.tf` residual is unproven either way and
    belongs with the cross-cutting tofu-apply cluster, not here.
13. **`issue_docs_remediation_sweep`'s DeFi items** (MTDS `liquidations` path for radiant/euler, MTDS `risk_params` emit
    vs declared capabilities, strategy-service `_RECURSIVE_STAKED_LEND` lending legs, UAC D15 HYPERLIQUID/ASTER
    `pipeline`→`live`) — all four are already claimed by `defi_satellite_ao_dispatch_batch{1,3,4}` and
    `cross_cutting_satellite_ao_dispatch_batch1`. Covered, not orphaned.

**BLOCKED-OPERATOR-DECISION** (no amount of re-triage resolves these; they need a ruling, then they become normal batch
candidates):

14. Already in the reconcile register `issues/infra_plan_reconcile_parked_decisions_2026_07_26.md` (6 items): the VM
    startup-script auto-rollout fix shape; folding the aiohttp doc into the execution-service holdout; deprecating
    `plans/active/INDEX.md`; re-targeting `stash_pile`'s Phase-3 fan-out off the retired per-epic VMs;
    `org_migration_to_odumresearch`'s still-wanted-or-abandon call; and the "line 2" definition. **Plus, newly surfaced
    by this audit**: the `PYTEST_UNIT_DIR` two-approach conflict (item 1 above), the `DataStatusTab.tsx` two-batch
    collision (item 4), the `base-service.sh`/`base-library.sh` multi-tranche hotspot with no ownership rule (item 2),
    whether `issues/human_led_audit_pool_2026_05_21.md`'s 12 `SEEDED` rows are still human-only now that the
    context-size Opus trigger is retired, and whether this plan should be flipped `active` at all. Also operator-gated
    and NOT re-triageable: the `execution-service` aioresponses migration (operator 2026-06-23: "do not refactor its
    tests mid-active-development" — nobody has lifted that); the Dockerfile Pattern-A normalization design call ("Owner:
    Ikenna" in the doc itself); the `scripts/` DELETE execution + the D16 strict-quickmerge carve scope; the
    `pm_scripts_typecheck_debt` exclude-the-scan-vs-annotate-the-debt fork; `delta_proxy_repricer.py`'s dead-code delete
    (needs an architect confirm it is not a planned consumer's WIP); the known-dead-shard pre-flight gate's
    manifest-schema-vs-side-table choice (schema blast radius); and the AWS `ec2:DescribeSpotInstanceRequests` IAM
    grant.

**TOO-LARGE-OR-RISKY-FOR-A-BATCH-TODO** (needs its own dedicated triage/design pass as a standalone plan, not a batch
slot):

15. `artifact_pipeline_observability_2026_07_17.md` — 23 open todos in a 958-line live multi-phase build with an active
    Progress Log, a `## Deferred work after 2026-07-23` table, and a `[REVIEW] P0` "STILL OPEN — prod is silent even
    with all three fixes live" item. Folding even its cleanest candidate risks colliding with its own in-flight state.
16. `codex_vs_repo_docs_ssot_audit_2026_06_01.md`'s per-repo consolidation across 20 repos (~520 docs) — the doc itself
    calls migrate-vs-redirect-vs-delete "irreversible-ish editorial calls" needing Opus-grade cross-repo judgment. Its 3
    bounded codex FIX-STALE items ARE drafted above; the 20-repo sweep needs a phased plan of its own.
17. `codex_violations_ratchet_to_five_2026_06_10.md`'s Phase-3 schema-provenance migration and its per-repo "clear the
    remaining check-classes" catch-all — not precisely scoped enough to be worker-determinable as written.

**GENUINELY HUMAN-ONLY (by the source doc's own design)**:

18. `issues/human_led_audit_pool_2026_05_21.md` — 12 of its 14 rows are `SEEDED` (no human picked up). The doc's model
    is explicit: "**Human work** = audit + plan upgrades + wrapper-plan creation + ack decisions. **Agent work** =
    remediation execution against the wrapper plan." So the remaining work is human by construction, and this doc will
    keep reporting orphaned until a human picks rows up — an accurate signal, not a stuck audit. (See the parked
    question above about whether that premise still holds.)

### Deferred item disposition (added 2026-08-09, finalize plan todo 4 — nothing lost to archival)

Every item above was migrated to a real home before this plan archived:

- **1, 4, 11-13** — RESOLVED BY LOGIC / already shipped, self-documenting inline above. No action.
- **2+3 (base-service.sh/base-library.sh bundle incl. `0.10.8`)** — CLEARED (finalize todo 2) and already SHIPPED by
  `infra_satellite_ao_dispatch_batch9_2026_08_09.md` (G1 + G2 both `[x]`). No batch-2 todo needed.
- **5 (managed-by launcher label)** — CLEARED; genuinely unbatched, so drafted fresh:
  `/plans/archive/2026_08/infra_satellite_ao_dispatch_batch12_2026_08_09.md`.
- **6 (repo_scripts DEPRECATE / item (k))** — STILL-CONFLICTING; real home confirmed:
  `repo_scripts_governance_audit_2026_06_18.md`'s own open `[AUDIT] P2` todo + Progress Log already record this exact
  CONFLICT-GATED status.
- **7 (pyarrow/mako/twisted/ujson residual)** — real home confirmed: `codex_violations_ratchet_to_five_2026_06_10.md`'s
  own open `[CODE] P2` pip-audit todo already covers all four packages (fastapi/starlette half separately shipped).
- **8 (MTDS >900-line split)** — CLEARED; real home confirmed: `mtds_file_size_refactor_2026_06_08.md` (active) already
  tracks every named `market_interface/` module.
- **9 (corpus-wide sweeps)** — STILL-CONFLICTING; real homes confirmed:
  `issues/zero_checkbox_sweep_all_tranches_2026_07_31.md` and `issues/reference_path_convention_2026_07_23.md` are both
  still `status: open` and own this work directly.
- **10a** — resolved by workaround, no action. **10b** — real home confirmed:
  `issues/reference_path_convention_2026_07_23.md` already carries the exact repoint todo.
- **14 (operator-gated)** — the 6 originally-registered items in
  `/plans/archive/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md` are ALL resolved (`status: resolved`,
  archived 2026-07-28). Of the "newly surfaced" sub-questions: the `PYTEST_UNIT_DIR`, `DataStatusTab.tsx`, and
  `base-service.sh`-ownership conflicts are all independently RESOLVED/RULED above (items 1, 2, 4); "should this plan
  flip active" is moot (archived instead); the `human_led_audit_pool` SEEDED-rows question is MOOT — that doc is itself
  `status: superseded` (archived 2026-07-27), its whole mechanism replaced by `plans/audit/README.md`'s per-epic audit
  lifecycle + the `/ag-closeout-audit` skill. The "also operator-gated" list (execution-service aioresponses, Dockerfile
  Pattern-A, scripts/ DELETE+D16, pm_scripts_typecheck_debt, delta_proxy_repricer, known-dead-shard gate, AWS IAM grant)
  were never batch1-exclusive — each already lives in its own named source doc; batch1 only catalogued them. No new
  register entry needed.
- **15-17 (too-large)** — `artifact_pipeline_observability_2026_07_17.md` already has its own active 958-line plan (no
  migration needed). `codex_vs_repo_docs_ssot_audit_2026_06_01.md` and `codex_violations_ratchet_to_five_2026_06_10.md`
  both already carry their own open todos for the 20-repo sweep / Phase-3 schema-provenance migration respectively, with
  Progress Log entries that already cross-reference this exact batch1 Deferred section.
- **18** — genuinely human-only by the source doc's own design; unchanged.

## Findings surfaced during extraction that are NOT todos here

Recorded so they are not lost, and because two of them mean a source doc's checkbox is currently wrong:

- **`codex_violations_ratchet_to_five_2026_06_10.md`'s `[REFACTOR] P3` "Remaining >900 tail" catch-all is almost
  entirely superseded by `[x] ✅` items ABOVE it in the same doc** — instruments reference_data adapters (done
  `@354ab43`), features onchain/delta_one orchestrators (`@06a83fb6`/`@966b985a`), strategy archetype_slot_resolver +
  legacy_strategy_mapping + portfolio archetypes (`@08582739`), agent-orchestrator worker_liveness/state_store/
  worktree_clean_check/models (`@209937f`), alerting router (`@8b12fcb`), ml uniform_training_pipeline (`@6004170`), UAC
  honest_coverage (`@f1599ee`, 1,141→788). The only genuine residual named in the doc is instruments `_solana_utils.py`
  (1,016, "deferred at agent limit"). A reconcile pass should rewrite that todo to just that file.
- **`issues/pm_scripts_typecheck_debt_2026_06_11.md`'s first `[SCRIPT] P3` todo asks to "ratchet
  `BASEDPYRIGHT_MAX_ERRORS` in `scripts/quality-gates.sh` back down to 1511" — that variable no longer exists.**
  Measured 2026-07-26: `grep -n 'BASEDPYRIGHT_MAX_ERRORS' scripts/quality-gates.sh` returns only three DO-NOT-re-add
  comment lines (31/33/37); the ceiling itself was REMOVED by `pm@22b2f89d7` when basedpyright went warn-only for PM
  `scripts/`. The annotate-the-4-files half is still live; the ratchet half is void.
- **`/plans/archive/issues/uv_pin_fleet_drift_2026_06_22.md` carries two provably-stale open todos**: the `[INFRA] P2`
  "human-planning-vm per-repo setup: 19/23 OK, 6 failures" item is contradicted by the same doc's own later UPDATE ("all
  6 previously-failing repos set up OK (0 failed)"), and the `[CICD] P1` "PR #498 v2 still RED on
  `QG slice (typecheck)`" residual-blocker item dates to 2026-06-27 and predates months of PM shipping.
- **`/plans/archive/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md`'s `[TEST] P1` "prove via a LOCAL
  orchestrator dispatch" is superseded** — it gates installing the plan-reconciler timer on central, and the timer has
  been installed and firing daily since ~2026-07-23 (verified in
  `issues/plan_quality_four_line_defense_architecture_2026_07_23.md`).
- **`codex_vs_repo_docs_ssot_audit_2026_06_01.md`'s parenthetical "CLAUDE.md's system-map 'URDI phantom' note is also
  stale"** is itself now stale — CLAUDE.md already reads "URDI is a live internal module — 'phantom' label retired
  2026-07-12".

## Operator approval gate

Approving this plan means: flip `status: draft` → `active` here AND in
`infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`, then ship both. Until then nothing here is ingested or
dispatched (`plans/PLAN_FORMAT.md` — `status: draft` is not ingested). Before flipping, note three things:

1. **Todo 19 is `[OPERATOR]`-tagged** because it deletes a live prod Cloud Run job + its scheduler + terraform. The
   delete-safety justification is RULE-11 prove-then-retire and it is stated in the todo, but it wants your explicit
   go-ahead, not just a plan flip.
2. **Five newly-surfaced operator questions** are in `## Deferred` item 14 and in this run's structured report. Two of
   them (`PYTEST_UNIT_DIR`, `DataStatusTab.tsx`) block real work; one (`base-service.sh` ownership) is a recurring
   structural problem that will keep deferring items every batch until there is a rule.
3. **This is batch 1 of an expected several.** 14 deferred items are conflict-gated and therefore re-checkable by a
   `batch2` once the competing sides ship; the operator-gated and human-only ones will keep reporting orphaned until
   they are ruled on or done, which is the correct signal.

## Codex SSOTs (read before touching a todo)

`/codex/06-coding-standards/quality-gates.md` · `/codex/06-coding-standards/script-homes.md` ·
`/codex/05-infrastructure/spot-vms-for-backfill.md` ·
`/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md` ·
`/codex/05-infrastructure/vm-launcher-runbook.md` · `/codex/04-architecture/tier-and-import-architecture.md` ·
`/codex/06-coding-standards/ui-testing-layers.md` · `/codex/11-project-management/plan-hygiene.md` ·
`/codex/11-project-management/cross-reference-path-convention.md` · `/codex/08-workflows/ci-cd-flow.md`

## Progress Log

- **2026-07-26** — Drafted by `/ag-closeout-audit infra` (Autonomous/AO-dispatched mode, operator away ~6h). Phase 0
  established that the infra covering set is one zero-todo digest with no batch plan and no forked children. Phase 1
  read all 34 tranche-primary docs end to end (not checkbox counts) and classified 29 as orphaned. Phase 3 ran the HARD
  conflict check against all 93 existing batch/finalize/closeout plans plus pairwise across these 25 todos before
  drafting: 25 drafted, 10 deferred conflict-gated, 3 resolved by logic, the rest operator-gated / human-only /
  too-large. Left `status: draft` deliberately — the flip to `active` is the operator's call.
- **2026-07-26** — Flipped `status: active` per resolution of
  `issues/autonomous_session_operator_decisions_2026_07_25.md` entry #38 (option A: flip both — give the hub real todos
  next so future audits measure a real covering set instead of re-deriving the same 29-orphan verdict). Flipped batch1
  only here; finalize stays `draft` (already `gate_on_depends: true`, self-activates once this batch's todos land — same
  reasoning as entries #22/#26). Todo 19 stays gated by its own `[OPERATOR]` tag regardless of this flip (deletes a live
  prod Cloud Run job + scheduler + terraform) — not touched.
- **2026-07-26** (slot-11) — Worked item 2 (`scripts/setup.sh` astral-uv fix + fleet rollout). PM template fix landed
  (`unified-trading-pm@4ce056d7d`), then a follow-up correction (`unified-trading-pm@713dc3d4b`) after discovering the
  first version quoted `"uv==0.10.8"` in the pip-fallback line, which broke the codex-compliance `pip install` exclusion
  regex (`grep -v "pip install uv"` no longer matched with the quote in between) — this would have newly red-gated every
  repo with a tight violation ceiling, not just the 2 it was caught on. **Shipped (7 repos + PM):**
  `deployment-service@98b1581e`, `market-tick-data-service@c7862b5a`, `instruments-service@40240042` (a repo-blocker
  round-trip: pre-existing unrelated function-size violation in `sports_reference.py`, fixed by another agent),
  `ml-service@c2de6209`, `unified-trading-library@d27813b1`, `deployment-ui@d3aa192`, `system-integration-tests@c0663d0`
  (green via `--ignore-timeout` after a pure host-contention wall-clock-SLA failure — no correctness issues). **Filed 2
  issue docs + repo-blockers** for genuinely pre-existing unrelated red gates hit along the way: instruments-service
  function-size (`/plans/archive/issues/instruments_service_qg_red_function_size_sports_reference_2026_07_26.md`,
  RESOLVED by another agent), unified-api-contracts codex-compliance ceiling
  (`/plans/archive/issues/unified_api_contracts_qg_red_codex_compliance_ceiling_2026_07_26.md`, RESOLVED —
  `unified-api-contracts@da76afe1`, `partition_paths.py` split under the 900L cap), ibkr-gateway-infra pyasn1 CVE
  (`/plans/archive/issues/ibkr_gateway_infra_qg_red_pyasn1_pysec_2026_07_26.md`, RESOLVED —
  `ibkr-gateway-infra@133a78f`). **Also hit + worked around**: a fleet-wide `/home` disk-full incident (290G at 0 bytes
  free, ~18:00-18:15 UTC) that corrupted 2 in-flight venvs (`unified-trading-library` pydantic/polars install,
  `unified-api-contracts` pydantic) — both self-healed via `scripts/setup.sh --force`; other slots were already
  remediating the disk fleet-wide, so no cleanup action taken here beyond my own scratchpad. **Key finding (see Deferred
  table + lesson below)**: the orchestrator's `MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN=900` (15 min) branch-realign
  guard silently reset local commits on repos whose real QG runtime regularly exceeds 15 min under the current fleet's
  host load (`unified-api-contracts` alone hit 4 resets across attempts of 613s/972s/1228s QG runtime) —
  batch-committing many repos up front before shipping each is the anti-pattern that caused this; see Deferred table for
  exact current state and `/codex/12-agent-workflow/commit-push-flip-rule.md` "Half 1 without Half-2 in the SAME turn"
  for why single-repo tight cycles are the correct pattern instead.
- **2026-07-26 (slot-7)** — Worked the "Land the two written-but-unshipped workspace boot-script hardenings" todo.
  Before writing any diff, read both target files and found **both already carry every change the todo spec asks for**:
  `scripts/workspace/workspace-bootstrap.sh` lines 543-555 enforce pinned uv `0.10.8` via the astral installer
  (`REQUIRED_UV="0.10.8"` + `curl -LsSf https://astral.sh/uv/${REQUIRED_UV}/install.sh | env UV_UNMANAGED_INSTALL=...`),
  lines 563-575 install pnpm via corepack → npm → sudo npm fallback, lines 668-685 `git checkout live-defi-rollout` for
  every cloned repo; `scripts/workspace/setup-workspace-config-symlink.sh` lines 48-59 write the root `.code-workspace`
  as a regular file with `sed`-rewritten root-relative paths instead of a symlink. `git log` traced this to
  `unified-trading-pm@703b1e912` ("fix(workspace): harden bootstrap so fresh VMs avoid today's failures", 2026-06-22
  16:34 +0100) — landed the SAME DAY the issue doc's "Durable boot-script hardening — WRITTEN + VALIDATED, BLOCKED from
  landing" section was written, via the PM `scripts/**` carve-out #3 direct-push path (bypasses the local-only
  version-alignment gate that was blocking normal quickmerge at the time). The issue doc's "BLOCKED" framing was never
  updated after that push landed, so it read as still-open when this batch1 plan extracted the todo from it.
  **Verification performed (Done-when bar) instead of a no-op re-commit**: `bash -n` clean on both files;
  `shellcheck -S error` clean on both files (`/home/ubuntu/.local/bin/shellcheck`); re-ran
  `setup-workspace-config-symlink.sh` fresh in this slot's `.tabs/7/` — produced a regular file (`file` reports "JSON
  text data", `test -L` false) with root-relative `"path"` entries (`.`, `unified-trading-api`, `unified-trading-pm`,
  …), spot-checked 2 of them (`unified-trading-api/.git`, `unified-trading-pm/.git`) resolve to real repos inside the
  workspace root. No commit needed — nothing to ship.
- **context-scout 2026-08-03**: re-scouted; context_scope unchanged (5 entries) — dispatch-batch coordinator.

## Deferred work after 2026-07-26 (slot-11, item 2 fleet rollout — 8/25 shipped incl. PM) — SUPERSEDED, see slot-7 re-check below the table

| Repo (17 remaining)                                                                                                                                                  | State                                                                                                                                                                                             | Blocked-on                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| agent-orchestrator, batch-live-reconciliation-service, e2e-testing, greeks-service, unified-trading-api, unified-trading-system-ui, ibkr-gateway-infra               | **Not done** — corrected commit still local (ahead=1), never reset                                                                                                                                | Pick up next: fresh-pull, run QG, quickmerge. ibkr-gateway-infra also needs its pyasn1-CVE repo-blocker to clear first (see issue doc)                                                                                                                                                                                                                                                                                                                                                                                                   |
| alerting-service, client-reporting-api, deployment-api, execution-service, features-service, market-data-processing-service, strategy-service, unified-api-contracts | **Not done** — local commit was silently RESET by the orchestrator's branch-realign guard (>900s unpushed); fix must be re-copied from `unified-trading-pm/scripts/setup.sh` before re-committing | Re-run: `cp ../unified-trading-pm/scripts/setup.sh scripts/setup.sh && chmod 755 scripts/setup.sh && git add scripts/setup.sh && git commit -m "fix(setup): sync astral-uv bootstrap fallback from PM template" && bash scripts/quality-gates.sh` then ship the MOMENT it's green — unified-api-contracts specifically needs the full commit→QG→ship cycle to land in well under 15 min (its real QG runtime is 15-20 min, so expect repeat resets; consider running it first, alone, right after a fresh boot when host load is lowest) |
| unified-api-contracts (partition_paths.py 1297L)                                                                                                                     | **Done** — split under 900L cap, `bash scripts/quality-gates.sh` PASSES                                                                                                                           | `/plans/archive/issues/unified_api_contracts_qg_red_codex_compliance_ceiling_2026_07_26.md`                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ibkr-gateway-infra (pyasn1 CVE)                                                                                                                                      | **Done** — resolved by cicd-agent slot-10, `ibkr-gateway-infra@133a78f`                                                                                                                           | `/plans/archive/issues/ibkr_gateway_infra_qg_red_pyasn1_pysec_2026_07_26.md`                                                                                                                                                                                                                                                                                                                                                                                                                                                             |

**Update (2026-07-26, slot-11)**: fund-administration-service + trading-agent-service (both previously in the first row
above) are now DONE — QG green, shipped `fund-administration-service@8c8bc25` + `trading-agent-service@2d57283`.

**Recommended next item**: `unified-trading-system-ui` or `unified-trading-api` (both `ahead=1`, never reset, no known
blockers) — ship those first while host load is checked, THEN tackle the 8 reset repos (cheap re-copy, just needs a
clean QG window), saving `unified-api-contracts` for a low-host-load moment given its 15-20 min QG runtime.

### Re-check 2026-07-26 ~21:50 UTC (slot-7) — 24/25 shipped, only agent-orchestrator remains

Diffed every repo named in the table above against PM's canonical `scripts/setup.sh`. All 15 repos slot-11 had listed as
"Not done" (either flavor) are now genuinely committed+shipped — other slots continued this rollout after slot-11's
checkpoint (verified via `git log -1 -- scripts/setup.sh` per repo, real commits, not coincidental content match):
`batch-live-reconciliation-service@8521395`, `e2e-testing@fd23a90`, `greeks-service@264d77c`,
`unified-trading-api@447f69e`, `unified-trading-system-ui@acdd569f`, `ibkr-gateway-infra@23b9a66`,
`alerting-service@4f9f37e`, `client-reporting-api@ec925ed`, `deployment-api@53a9e44`, `execution-service@fea26219`,
`features-service@ff67e6c9`, `market-data-processing-service@19c7a52`, `strategy-service@3439a8e2`,
`unified-api-contracts@562220e3` — plus `fund-administration-service@8c8bc25` + `trading-agent-service@2d57283` already
noted done by slot-11.

**Only `agent-orchestrator` remains — a DIFFERENT case, not a repeat of the reset-guard issue.** It never had a
`scripts/setup.sh` at all (confirmed in scope via `workspace-manifest.json`'s 25-repo list;
`rollout-quality-gates-unified.py --repo agent-orchestrator --dry-run` confirms it would create one). Copied PM's
canonical file in — syntactically clean (`bash -n` OK) — but **could not complete QG verification: the host disk-full
condition (`/plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md`) got WORSE while working this**
(`df -h /` went 1.2GB → 3.4M → 2.4M free across ~15 min), and a fresh `uv pip install -e ../unified-trading-library` for
agent-orchestrator's never-before-built `.venv` hard-failed with `No space left on device (os error 28)` mid-copy of a
`ccxt` wheel — a real, current, externally-caused blocker, not a code defect. Stashed the addition cleanly (`git stash`
on `agent-orchestrator`, message `slot7-agent-orchestrator-setup-sh-disk-blocked`) rather than leave it as loose
uncommitted WIP or force a red-QG ship. **Next pickup**: `git stash pop` in `.tabs/<slot>/agent-orchestrator`, re-check
`df -h /` has real headroom (need enough for a fresh venv + ruff/basedpyright/pytest/unified-trading-library — budget at
least a few hundred MB), then `bash scripts/setup.sh && bash scripts/quality-gates.sh` and ship the moment it's green.
This is the LAST repo — closing it closes this todo.

- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
