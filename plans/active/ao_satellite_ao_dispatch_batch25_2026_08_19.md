---
doc_type: plan
title: AO satellite AO batch 25 — conflict-clear bounded extraction from the 2026-08-19 na-eligibility-audit ao run
summary: >-
  TWENTY-FIFTH AO-dispatch batch for the `ao` topic tranche — output of a `/na-eligibility-audit ao` Phase 0-3 run
  (2026-08-19). Phase 0 found 80 in-scope-tranche docs (52 incremental-skip, unchanged since a prior dated verdict);
  Phase 1 classified the 28 in-scope docs via a 7-agent Workflow fan-out, one hunter per disjoint doc batch, full
  end-to-end read, mandatory grep-count completeness check against Phase 0's own open_todos figure. Phase 2
  conflict-check: grepped every status:draft/active `ao_satellite_ao_dispatch_batch*` (3/8/14/21/22/23/24) + their
  finalizes, `ao_consolidated_closeout_2026_08_12.md`, and every other `assigned_vm: planning` doc under
  `parent_epic: orchestrator_master`/`agent_operating_framework_master`/`plan_hygiene_master` for each candidate's
  subject matter (distinctive function/mechanism names, not just titles) — 11 items across 7 source docs survive as
  genuinely bounded, already-decided, conflict-clear work (this is the PER-TODO split path, not a whole-doc
  RECLASSIFY — every source doc stays `assigned_vm: NA` for its remaining genuinely-operator-gated/judgment items).
  ONE further candidate (a per-job reaped-stale-rate measurement) was found CONFLICTED against an explicit
  2026-08-17 operator ruling and deliberately EXCLUDED — see this run's chat report, not repeated here.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-25, satellite-docs, satellite-extraction, na-eligibility-audit]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch25_finalize_2026_08_19.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/issues/subagent_wrote_to_foreign_checkout_bare_repo_path_2026_08_18.md,
    /plans/active/issues/na_eligibility_audit_same_tranche_duplicate_concurrent_dispatch_2026_08_18.md,
    /plans/archive/issues/ao_tmux_loss_rate_canary_likely_overtuned_2026_08_18.md,
    /plans/active/ao_human_fleet_integration_2026_08_15.md,
    /plans/archive/2026_08/kimi_gemma_provider_onboarding_2026_08_16.md,
    /plans/active/issues/account_failover_ignores_overage_rejected_2026_08_18.md,
    /plans/archive/issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.9
estimate_calibrated_ai_days: 0.45
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
sequential: true # several items (7-9) touch the same account-failover subsystem (server.py/main.md trigger table)
  # with unverified file-level disjointness from this audit pass alone — serializing is the safe default rather than
  # risking a same-file collision the "different files" concurrency rule would otherwise require ruling out per-item.
context_scope:
  [
    /plans/active/issues/account_failover_ignores_overage_rejected_2026_08_18.md,
    /plans/archive/issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md,
    /plans/archive/2026_08/kimi_gemma_provider_onboarding_2026_08_16.md,
    /plans/active/ao_human_fleet_integration_2026_08_15.md,
    agent-orchestrator/server/server.py,
  ]
source: >-
  `/na-eligibility-audit ao` (2026-08-19, na_eligibility_auditor, slot 30). Phase 1 classified 28 in-scope docs (of 80
  total ao-tranche candidates, 52 skipped via an unchanged incremental-diff marker) via a 7-agent Workflow fan-out —
  one hunter per disjoint doc batch, full end-to-end read, mandatory grep-count completeness check against Phase 0's
  own open_todos figure (one false-mismatch found and resolved: a doc's grep count included 5 quoted checkboxes
  inside a fenced code block, not its own todos — self-documented known tooling artifact). Phase 2 conflict-check:
  targeted fingerprint greps across every active planning doc + the consolidated closeout for each candidate's
  distinctive mechanism (not just its title) — zero hits for the 11 items extracted here; 1 candidate held back on a
  confirmed conflict against an explicit prior operator ruling (see the run's chat report).
---

# AO satellite AO batch 25

> **`status: active`** per this skill's own Phase-3 rule (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`
> § 1(b) + the na-eligibility-audit SKILL.md's 2026-08-10 fix) — this audit's own verdict IS the authorizing decision.
> This is the PER-TODO SPLIT extraction path (verdict 5), not a whole-doc RECLASSIFY (verdict 4): every one of the 7
> source docs below stays `assigned_vm: NA` — only the specific bounded item(s) cited move here. Each source doc's
> own extracted checkbox(es) are already flipped `[x]` with a citation back to this doc (see each source doc's own
> diff, applied by this same run).

## Why this plan exists

`/na-eligibility-audit ao`'s 2026-08-19 run classified the 28 in-scope docs in the `assigned_vm: NA` "ao" tranche
population. Of the 28, 13 are KEEP-NA valid, 2 are KEEP-NA-STALE (already duplicated elsewhere), 2 are KEEP-NA-STALE
(items closed with evidence), 5 clear the bar for a WHOLE-DOC reclassify (handled separately, each with its own
`_finalize_2026_08_19.md` twin — see this run's chat report), and 6 have a MIX of bounded and genuinely-operator-
gated/judgment items — this batch extracts the bounded slice of those 6 (plus one bounded item from a 7th doc that
was itself a KEEP-NA-STALE-ITEMS case with one additional clean item):

1. **Sweep the bare (non-slot) clone's dirty files against recent sub-agent tasks to size how often a sub-agent
   wrote to a foreign checkout has happened.** Bounded, deterministic data-gathering audit (compare dirty-file
   timestamps/content against recent sub-agent task logs); no design call required to execute it — distinct from the
   sibling "consider a mechanical guard" item in the same doc, which stays NA as a genuine cost/design tradeoff.
   Source: `subagent_wrote_to_foreign_checkout_bare_repo_path_2026_08_18.md`.
2. **Harden the same-tranche concurrent-dispatch case for na-eligibility-audit** (a dispatch-time lock per tranche,
   or narrow every Phase-3 file-touching step to `Edit`-only never `Write` for any file that might already exist
   from a concurrent run) — the root cause (a design gap: `plan_health.py`'s only dispatch-coalescing gate exempts
   `mode="na_eligibility"`) is already confirmed via direct code read by a same-day plan_reconciler pass; this is now
   a scoped hardening fix with two concretely-named implementation options. Shares its underlying pattern with
   `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` todo 4 (the same gate exemption for `mode="reconcile"`) —
   cite that doc's finding when implementing, but this is a distinct fix (different `mode=` value, tracked
   separately since that doc's own todos are already claimed by `ao_satellite_ao_dispatch_batch22_2026_08_16.md`).
   Source: `na_eligibility_audit_same_tranche_duplicate_concurrent_dispatch_2026_08_18.md`.
3. **Query `ActivityRow` for `tmux_session_lost` events over the last 7 days** to measure whether the rate-canary's
   `min_count=3`/`window_seconds=600` threshold is genuinely over-tuned for this fleet's normal churn — bucket into
   rolling 10-min windows the same way the canary's own code does, cross-reference each threshold-crossing against a
   preceding `reason="manual"` `SESSION-TEARDOWN` log line (method already proven out on a different doc's cluster).
   A fully-specified measurement task with a stated method; the FOLLOW-UP "raise the threshold" action (todo 2 in the
   source doc) stays NA, correctly conditional on this measurement's result. Source:
   `ao_tmux_loss_rate_canary_likely_overtuned_2026_08_18.md`.
4. **Exclude human-kind slots from the main dashboard Fleet table's generic role-badge rendering** — Phase 3's
   `AgentKind`/`KINDS_ORDER`/`AGENT_KIND_LABEL` work only ever wired human slots into the dedicated `HumanFleet.tsx`
   page; find wherever the main Fleet table computes its per-slot role badge and add the same `human_slot_ids()`-
   style exclusion the liveness/kill sites already use. Bounded UI fix with a stated done-when (a live dashboard
   check). Source: `ao_human_fleet_integration_2026_08_15.md`.
5. **Moonshot (Kimi) wallet/balance reconciliation** — the NVIDIA/Gemma half of this item is already shipped
   (`agent-orchestrator@0c0e527` + `tests/test_nvidia_headroom.py`); the remaining Moonshot half is the same
   bounded shape (confirm a readable balance/usage endpoint or apply the DeepSeek-style available-balance-only
   design, cross-checked live against the vendor's own console, tracking TOTAL credited cash+voucher per the
   2026-08-16 operator rule). Source: `kimi_gemma_provider_onboarding_2026_08_16.md`.
6. **Kimi `/pre-compact` → `/compact` live-test** through the real Claude Code harness — the Gemma half of this item
   is already shipped and verified (context dropped 42k→8.1k of 200k tokens); the remaining Kimi half is the same
   bounded live-test shape. Source: `kimi_gemma_provider_onboarding_2026_08_16.md`.
7. **Add `overage_status == "rejected"` as an explicit 5th account-failover trigger condition**, covering both
   observed `overage_disabled_reason` values (`out_of_credits`, `org_level_disabled`), alongside the existing four
   pct/rate-limit checks feeding `rotate_all_slots_off_account`. Fully root-caused (exact trigger-table location
   cited, `unified-trading-pm/agents/main.md` § "Account-failover triggers" + `server.py`) with a stated scope; the doc's own separate
   interaction-analysis section already confirmed this fix is safe with respect to the CI-escalation reserve pool.
   Source: `account_failover_ignores_overage_rejected_2026_08_18.md`.
8. **Investigate whether account rotation excludes overage-rejected accounts from its selection pool** — a scoped
   code-read of the rotation-pool selection logic for an `overage_status` filter (or lack thereof), distinct from
   item 7's trigger-fix (a trigger fix stops sessions dying on an already-bad account; a pool-exclusion fix stops
   rotation assigning a bad account in the first place). Source: `account_failover_ignores_overage_rejected_2026_08_18.md`.
9. **Classify the overage-rejected-at-kill-time failure shape instead of leaving it `death_class: unexplained`** —
   when a killed slot's `account_snapshot.overage_status == "rejected"` at kill time, label it something
   diagnosable (e.g. `account_overage_exhausted`). Bounded classifier change with a clear trigger condition. Source:
   `account_failover_ignores_overage_rejected_2026_08_18.md`.
10. **Pull `overage_disabled_reason` for the other 21 disabled accounts** and cross-reference against the named
    in-progress provider-onboarding plans before treating any as anomalous (operator confirmed 2026-08-18 these are
    largely expected, mid-onboarding/testing) — bounded data-gathering + cross-reference task with named targets.
    Source: `ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`.
11. **Investigate why `/api/agents` returns zero rows for human slots**, feeding the human-fleet dashboard overview
    — determine which endpoint the overview actually consumes and whether human-slot rows should be added to
    `/api/agents` or the overview should read `/api/state`'s `slots[]` instead. A scoped investigation with a
    concrete done-when (the mechanism is identified and, if a real regression, root-caused). Cross-references item 4
    above (same `ao_human_fleet_integration_2026_08_15.md` subsystem) but is a distinct symptom (a different
    endpoint's row count vs. the main Fleet table's badge rendering) — no file-identity confirmed between them from
    this audit pass, hence the whole-batch `sequential: true` rather than assuming disjointness. Source:
    `ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`.

## Todos

- [x] ✅ [REVIEW] P2. Sweep the bare (non-slot) `unified-trading-pm` clone's dirty files against recent sub-agent task
      logs to size how often a sub-agent wrote to a foreign checkout instead of its named `.tabs/<N>/` slot. Done
      when: a count/report exists (even if the answer is "zero other occurrences found"). Repo: unified-trading-pm.
      Source: `plans/active/issues/subagent_wrote_to_foreign_checkout_bare_repo_path_2026_08_18.md` item 3. **DONE — 0
      foreign sub-agent writes found** across 10 swept dirty files (all legit main/review/operator artifacts; see
      Progress Log 2026-08-19).
- [x] ✅ [BACKEND] P2. Harden the na-eligibility-audit same-tranche concurrent-dispatch case: implement a dispatch-time
      lock per tranche in `server/plan_health.py::dispatch()`, OR narrow every na-eligibility-audit Phase-3
      file-touching step to `Edit`-only (never `Write`) for any file that might already exist from a
      concurrent run. Cite `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` todo 4's finding (same gate-exemption
      class for `mode="reconcile"`) as related but do not duplicate its own tracked fix. Done when: a synthetic
      concurrent-dispatch test proves the chosen mitigation prevents the collision class described in
      `na_eligibility_audit_same_tranche_duplicate_concurrent_dispatch_2026_08_18.md`. Repo: agent-orchestrator.
      **DONE-BY-CITATION 2026-08-20 (slot 4) — agent-orchestrator@bfe8fb28a0** (per this plan's own 2026-08-19
      Progress-Log note). Verified fresh: `_TRANCHE_GATED_MODES` = {reconcile, na_eligibility, ag_closeout}
      (server/plan_health.py:435) and `dispatch()` gates those modes via `_tranche_dispatch_gate(session,
      mode=mode, tranche=tranche)` at the call site; regression test
      `test_tranche_dispatch_gate_covers_na_eligibility_and_ag_closeout` (tests/test_plan_health.py:2655) plus
      dispatch()-level positive/negative tests (`test_dispatch_reconcile_mode_coalesces_no_spawn_when_tranche_gate_live`,
      `test_dispatch_na_eligibility_mode_different_tranche_still_spawns`) prove the same-day same-(mode, tranche)
      coalesce that closes the agt-72629d/agt-9095fb defi collision class; commit `bfe8fb28a0` confirmed on
      origin/live-defi-rollout.
- [x] ✅ [SCRIPT] P2. Query `ActivityRow` for `tmux_session_lost` events over the trailing 7 days, bucket into rolling
      10-min windows matching `_count_excluded_losses`'s own method, count how often the 3-in-10-min threshold is
      crossed outside any known incident window, and for each crossing cross-reference every member against a
      preceding `reason="manual"` `SESSION-TEARDOWN` log line within ~60s. Done when: a measured baseline exists
      (crossing frequency + benign-recycle share) to inform whether `tmux_session_loss_rate_min_count`/
      `_window_seconds` needs raising. Repo: agent-orchestrator. **DONE — see Progress Log 2026-08-20.**
- [x] ✅ [UI] P2. Exclude human-kind slots (`config.human_slot_ids()`) from the main agent-orchestrator dashboard Fleet
      table's per-slot role-badge computation (NOT the dedicated `HumanFleet.tsx` page, which already excludes them
      correctly). Done when: a live dashboard check shows slot 9001 (and any other human slot) absent from the main
      Fleet table's rows entirely, still correctly present on the Human Fleet page. Repo: agent-orchestrator. **DONE —
      agent-orchestrator@b25d40af36**. `fleetSlots()` (dashboard/src/layout.tsx) excluded only `kind !== "main"/
      "review"`; a human identity slot has backend `kind="worker"` (no dedicated human literal exists server-side —
      only `slot_id` distinguishes it), so it never got excluded. Added a `slot_id < 9000` clause mirroring
      `HumanFleet.tsx`'s own `buildHumanFleetRows` range check. Verified live via a new Playwright spec
      (`dashboard/tests/e2e/fleet-excludes-human-slots.spec.ts`, seeded `SlotRow(slot_id=9001, operator="ikenna")` in
      `seed_e2e_state.py`): slot 9001 absent from the main Fleet table, still present on the Human Fleet page — both
      pass. Unit regression: `layout.test.ts`'s `fleetSlots` suite. Full QG green (5249 passed, coverage 86.17%),
      dashboard vitest 469/469, tsc clean.
- [x] ✅ [REVIEW] P2. Moonshot (Kimi) wallet/balance reconciliation: confirm whether Moonshot exposes a readable
      balance/usage endpoint, or apply the DeepSeek-style available-balance-only design if not; track TOTAL credited
      (cash + any promotional voucher) per the 2026-08-16 operator rule, cross-checked live against Moonshot's own
      console. Done when: a real number is confirmed readable and matches the vendor's own dashboard. Repo:
      agent-orchestrator. **DONE 2026-08-20 (slot 7) — agent-orchestrator@60db1a79, @39d35ed6 (shipped 2026-08-16/18,
      verified live this session).** Moonshot DOES expose a readable balance endpoint — `GET /v1/users/me/balance`
      (confirmed against Moonshot's own API docs 2026-08-16 + live: 4,958 poller samples in the live orchestrator DB,
      latest `$14.969601` at 2026-08-20 10:58:57Z). Full mechanism shipped: `server/kimi_balance.py` +
      `kimi_balance_poller.py` (1-min), routes `GET/POST /api/accounts/kimi/topups` + `GET
      /api/accounts/kimi/wallet-reconciliation[/window]`, lifetime ledger `compute_kimi_wallet_reconciliation()`
      (state_store/slots.py), `KimiWalletPanel.tsx` (+ real `allKimiAccountsPaused()` paused banner),
      `tests/test_kimi_wallet_reconciliation.py`. The 2026-08-16 operator rule (track TOTAL credited cash+voucher) is
      now satisfied in the LIVE ledger (verified via orchestrator API + live DB, not assumed): recorded the two
      documented real credits — $10 cash recharge + $5 one-time voucher = **$15 total credited** — so the pool now
      reports `known_topup_total_usd=15.0`, `current_balance_usd=14.969601`, `real_total_spend_usd=0.0304`, matching
      the vendor dashboard baseline (platform.kimi.ai/console/account: Total Recharge $10 + Voucher $5 = $15 credited,
      Available $14.99978, Consumed $0.00022). Cross-checked live the way the DeepSeek $50 topup was verified.
- [x] ✅ [REVIEW] P2. Live-test `/pre-compact` → `/compact` for Kimi through the real Claude Code harness (a spawned
      `claude` subprocess, not a raw HTTP probe). Done when: a real compact cycle is observed working end-to-end for
      Kimi, matching the already-verified Gemma result. Repo: agent-orchestrator. **DONE 2026-08-20 (slot 3) — real
      compact cycle observed end-to-end via `kimi-k2-6` (Moonshot, through the live litellm proxy). Baseline
      `/context`: 72.3k/1m tokens, Messages 69k. `/pre-compact` executed as a real skill (full 8-step ritual, verdict
      "Safe to compact: YES"). `/compact` exit 0 → post `/context`: 6.6k/1m, Messages 3.2k (~95% Messages drop,
      matching the Gemma result's 42k→8.1k). Compacted session confirmed resumable (follow-up turn returned
      "session-ok"). See Progress Log 2026-08-20.**
- [x] ✅ [BACKEND] P2. Add `overage_status == "rejected"` as an explicit 5th account-failover trigger condition
      (covering both `out_of_credits` and `org_level_disabled`) in the account-monitoring path that feeds
      `rotate_all_slots_off_account` (`server.py`, per `unified-trading-pm/agents/main.md` § "Account-failover triggers"). Should fire
      regardless of `weekly_pct`/`five_hour_pct`. Done when: a session on an overage-rejected account is proactively
      rotated rather than left to die `death_class: unexplained`. Repo: agent-orchestrator. **DONE 2026-08-20 (slot
      18) — agent-orchestrator@acf72243d5.** Root-caused: `overage_status` was captured on `AccountUsageRow` but
      never read by any routing check (`server/orm.py` comment literally said "Operator-facing detail, not used for
      routing"). Fixed at the single shared gate every failover path already consults —
      `account_is_usable()` (`server/state_store/account_usage.py`) now returns `False` when
      `overage_status == "rejected"`, regardless of `weekly_pct`/`five_hour_pct`, covering both
      `out_of_credits` and `org_level_disabled`. This flows through unchanged to every existing caller: dispatch-time
      account picking (`_pick_headroom_account`/`pick_next_account`), the proactive worker-slot failover kill
      (`_drain_worker_account_failover`), and main agent's `_handle_account_unusable`. Updated the stale
      "not used for routing" comment in `orm.py` and added the 5th row to `unified-trading-pm/agents/main.md`'s "Account-failover triggers"
      table. Tests: 3 new cases in `tests/test_auth_failed_rotation.py::TestAccountIsUsable` (rejected+out_of_credits
      fires regardless of weekly_pct=90; rejected+org_level_disabled fires; overage_status="allowed" stays usable).
      Full QG green (5275 passed, coverage 86.14%, dashboard vitest 469/469, tsc clean).
- [x] ✅ [BACKEND] P2. Investigate whether account rotation's selection-pool logic already excludes (or should exclude)
      overage-rejected accounts from being assigned to a slot in the first place, separate from the trigger fix
      above. Done when: the rotation-pool selection code path is read directly and the answer (excludes / does not
      exclude) is confirmed with a citation, with a follow-up fix if it does not. Repo: agent-orchestrator. **DONE 2026-08-20 (slot 1) — agent-orchestrator@acf72243d5.**
      Additional direct path evidence: the shared `account_is_usable()` predicate
      (`server/state_store/account_usage.py:340-364`) returns false for `overage_status == "rejected"`;
      `_account_meets_dispatch_headroom()` applies it to ordinary dispatch (`server/autospawn.py:1075-1121`),
      and `_live_free_combo_ids()` applies it to stratified non-Anthropic rotation (`server/autospawn.py:1870-1895`).
      Regression coverage for both observed rejection reasons is in `tests/test_auth_failed_rotation.py:161-184`.**
- [ ] [BACKEND] P3. Classify the overage-rejected-at-kill-time failure shape (e.g. `account_overage_exhausted`)
      instead of leaving it `death_class: unexplained` when a killed slot's `account_snapshot.overage_status ==
      "rejected"` at kill time. Done when: a fresh occurrence of this failure shows the new, diagnosable
      `death_class` instead of `unexplained`. Repo: agent-orchestrator.
- [ ] [SCRIPT] P2. Pull `overage_disabled_reason` for the 21 currently-disabled non-Anthropic accounts and
      cross-reference each against the named in-progress provider-onboarding plans before treating any as anomalous.
      Named plans: `deepseek_claude_blended_provider_routing_2026_07_28.md`,
      `grok_gemini_translation_proxy_2026_08_14.md`, `codex_luna_flex_bridge_2026_08_14.md`,
      `kimi_gemma_provider_onboarding_2026_08_16.md`. Done when: every one of the
      21 is classified expected-mid-onboarding vs. genuinely anomalous, with the anomalous set (if any) flagged as a
      fresh follow-up. Repo: agent-orchestrator.
- [x] [SCRIPT] P2. **DONE — already answered by a sibling doc, same day.** `ao_human_fleet_integration_2026_08_15.md`
      re-verified `GET /api/agents?kind=human` live 2026-08-20: returns multiple live human rows (harsh, ikenna-tab5,
      ikenna-tab6, ikenna-tab2) right now. The 2026-08-18 zero-rows report was a transient snapshot, not a persisting
      regression — no reproducible bug remains to chase. Repo: agent-orchestrator.

## Progress Log

- **2026-08-19 (cross-reference note, not this batch's own dispatch)**: item 2 above ("Harden the na-eligibility-audit
  same-tranche concurrent-dispatch case… a dispatch-time lock per tranche in `server/plan_health.py::dispatch()`") is
  now **already shipped** by `agent-orchestrator@bfe8fb28a0` — `_tranche_dispatch_gate`/`_last_tranche_dispatch`,
  implemented while resolving `/plans/archive/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` todo 4 (the
  identical gate-exemption root cause for `mode="reconcile"`), generalized across
  `reconcile`/`na_eligibility`/`ag_closeout` in one fix rather than per-mode. This closes the collision class
  `na_eligibility_audit_same_tranche_duplicate_concurrent_dispatch_2026_08_18.md` describes (a dispatch-time
  coalescing gate keyed on `(mode, tranche, day)`, not the file-level `Edit`-only alternative this item's text also
  named — the gate approach was chosen). **Whoever dispatches this batch: verify `_tranche_dispatch_gate` covers your
  `na_eligibility` case (it does, per its own test `test_tranche_dispatch_gate_covers_na_eligibility_and_ag_closeout`
  in `agent-orchestrator/tests/test_plan_health.py`) and mark item 2 done-by-citation rather than re-implementing it.**
  Durable contract: `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` § "PM-repo dead-lock correlation +
  duplicate-tranche dispatch guard".
- **context-scout 2026-08-19**: verified the pre-existing context_scope (3 entries, set at authoring) — all paths
  confirmed resolving on disk, still the correct source-doc reading list; no change needed.
- **review sweep 2026-08-19 (item 1 done)**: swept the bare `unified-trading-pm` clone
  (`/home/ubuntu/unified-trading-system-repos/unified-trading-pm/`) — 10 dirty files total (2 modified tracked + 8
  untracked). **Zero foreign sub-agent writes found.** All 10 are legitimate orchestrator artifacts: 8 untracked
  `plans/active/issues/*_2026_08_19.md` (filed by main / flagged by review-role agents — `ao_sqlite_database_locked…`,
  `backlog_500_malformed_depends_on_comment…`, `mac_host_all_12_slots…`, `mac_slot3_…`, `macbook_pro_slot2_…`,
  `main_agent_own_slot_stale…`); 2 modified tracked files (`mac_slot0_base_checkout_stuck_dirty_files_2026_08_11.md`
  main's Progress-Log append re Mac slot-0 scope growth; `prediction_satellite_ao_dispatch_batch11_2026_08_13.md`
  main's fix moving a malformed inline `depends_on` comment off the machine-parsed line — matches
  `backlog_500_malformed_depends_on_comment_2026_08_19.md`); plus 2 non-doc artifacts
  (`scripts/infra/resource-watchdog/resource-watchdog.sh.bak_pre_urgent_fix`, `slack-data-pipeline-alerts-24h.json`).
  The 2026-08-18 Elysium incident remains the only known occurrence; the mechanical-guard item (source doc todo 2)
  stays NA as the residual.
- **2026-08-20 (slot 4)**: Item 2 closed **done-by-citation** — the dispatch-time tranche gate
  (`_tranche_dispatch_gate`/`_last_tranche_dispatch`, `agent-orchestrator@bfe8fb28a0`, the 2026-08-19 shipment) already
  implements the chosen mitigation (the `(mode, tranche, day)` coalescing gate, not the Edit-only alternative). Verified
  fresh rather than trusting the note: `_TRANCHE_GATED_MODES` explicitly includes `na_eligibility`
  (server/plan_health.py:435) and `dispatch()` reaches the gate for those modes; the named regression test
  `test_tranche_dispatch_gate_covers_na_eligibility_and_ag_closeout` (tests/test_plan_health.py:2655) exercises the
  exact same-(mode, tranche=defi) coalesce that the 2026-08-18 agt-72629d/agt-9095fb collision class describes; commit
  `bfe8fb28a0` confirmed on origin/live-defi-rollout. Related-but-distinct from
  `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` todo 4 (same generalized gate, shipped in the same commit) —
  not duplicated here per the 2026-08-19 note.
- **2026-08-20 (slot 10)**: Item 3 measured against the live `GET /api/activity?type=tmux_session_lost&since=2026-08-13T07:00:00Z` ActivityRow slice (2,335 raw rows through 2026-08-20 07:20Z). Applying the canary's current `_count_excluded_losses` rules using the live agent/slot snapshots removed 575 rows (one-shot/scheduled lifecycle or idle-slot exclusions), leaving 1,760 qualifying losses, or **10.46/hour**. Simulating the canary's 120-second tick over a 600-second rolling window at threshold 3 produced **194 threshold-crossing episodes in seven days (27.71/day)**; removing the only explicitly documented incident window (2026-08-14 23:30–23:40Z around the 23:33:47–48Z cluster) still produced 194, so the frequency is not explained by that known incident. The 194 episodes contained 1,048 crossing-member rows; only **8 (0.8%)** had a preceding journal `SESSION-TEARDOWN ... reason=manual` line for the same slot within 60s (36 matching manual teardown lines were available in the seven-day journal query). This is strong evidence that 3-in-10-min is routinely crossed, while the journal cross-reference is a conservative benign-recycle lower bound because service journal retention exposed only 36 manual lines; the follow-up threshold/exclusion decision remains in the source issue and is not made by this measurement.
- **context-scout 2026-08-20**: rebuilt context_scope (5 entries) — prior list covered only the batch-process meta mechanism (now fully done), none of the 8 still-open todos.
- **2026-08-20 (slot 7)**: Item 5 (Moonshot/Kimi wallet/balance reconciliation) DONE. This is a REVIEW item whose code
  was already shipped on LDR (commits 60db1a79 / 36083559 / 39d35ed6); the remaining scope was verifying the
  done-when and closing the operator-rule data gap. Verified against the LIVE running orchestrator + its DB
  (`data/state/state.db`), not assumed: (1) Moonshot's `GET /v1/users/me/balance` endpoint is real and readable —
  `server/kimi_balance.py` parses `available_balance` (raw payload also carries `cash_balance`/`voucher_balance`),
  and the 1-min poller has recorded 4,958 samples (2026-08-16 19:06:59Z → 2026-08-20 10:58:57Z), latest
  `$14.969601` — consistent with the vendor dashboard baseline ($15 credited / $14.99978 available /
  $0.00022 consumed, operator screenshot platform.kimi.ai/console/account). (2) The 2026-08-16 operator rule
  ("track TOTAL credited cash+voucher, not cash-only") was NOT yet reflected in the live ledger — `kimi_topups` was
  empty — so I recorded the two documented real credits via the sanctioned `POST /api/accounts/kimi/topups` route:
  $10 cash recharge + $5 one-time voucher = **$15 total credited** (notes cite the operator's screenshot; add-only
  audit trail, never overwrites). Reconciliation now reports `known_topup_total_usd=15.0`, `topup_count=2`,
  `current_balance_usd=14.969601`, `real_total_spend_usd=0.0304` vs `attributed_total_usd=0.0` — the $0.0304
  residual is the pre-attribution 2026-08-16 reasoning-token smoke-test spend, expected under the v1 design's
  attributed-spend-only convention. No code changes required this session.
- **2026-08-20 (slot 3)**: Item 6 (Kimi `/pre-compact` → `/compact` live-harness test) DONE — real, decisive,
  positive result, matching the already-verified Gemma half. Spawned an actual `claude` CLI subprocess (v2.1.237,
  `-p` print mode) pointed at the real `kimi-k2-6` account's proxy credentials (`~/.claude-accounts/kimi-k2-6.env`
  → `ANTHROPIC_BASE_URL=http://127.0.0.1:8768`, live litellm proxy, real Moonshot auth), run from a scratch dir
  with the real pre-compact SKILL.md copied into `.claude/skills/` (confirmed loaded via the `/context` skills
  table — Project source). Sent a real 42,533-word prompt to build genuine context; confirmed via a real `/context`
  reading: **72.3k/1m tokens (7%), Messages 69k**. Ran `/pre-compact`: genuinely executed as a real skill — full
  8-step ritual output with a real session audit ("Not a git repository", scratchpad absent, verdict **"Safe to
  compact: YES"**, Step 8b "Does not trigger") — not silently swallowed. Ran `/compact`: exit 0 — the session
  transcript records the exact "Compacted (ctrl+o to see full summary)" banner as a `<local-command-stdout>` entry
  plus a "This session is being continued from a previous conversation that ran out of context. The summary below
  covers..." continuation message; the benign `[claude-code:unrecognized_model]` capability-query warning also prints.
  Follow-up `/context`: **6.6k/1m tokens (1%),
  Messages 3.2k** — Messages dropped 69k→3.2k (~95%), total 72.3k→6.6k. **Session continuity confirmed**: the 72k
  baseline persisted across `--continue` calls (a fresh session would read ~3.4k), and a post-compact `--continue`
  turn returned `session-ok`, proving the compacted session is healthy/resumable. The session-title/`sdk`/`compact`
  capability queries emit a cosmetic `[claude-code:unrecognized_model]` warning (Claude Code's internal model-info
  path doesn't recognize `kimi-k2.6` at the proxy) — non-blocking, the chat/compact/continue all work. No code
  changes required. This closes the Moonshot/Kimi half; both halves of the item are now verified (Gemma 2026-08-18,
  Kimi today).
- **2026-08-20 (slot 1)**: Item 8 DONE — direct code read confirms the rotation pool already excludes rejected-
  overage accounts. `server/state_store/account_usage.py::account_is_usable()` returns `False` when
  `AccountUsageRow.overage_status == "rejected"` (covering both observed rejection reasons), and both
  `server/state_store/account_usage.py::pick_next_account()` and `server/autospawn.py::_pick_headroom_account()`
  call that predicate before returning a candidate. `server/server.py::pick_next_account()` has the same guard in
  its compatibility path, while `rotate_all_slots_off_account()` additionally rejects a target whose ID equals the
  account being rotated off. Therefore the item-7 shared-gate fix (`agent-orchestrator@acf72243d5`) closes the
  selection-pool path as well; no additional code change is required. The separate item-9 death-classifier follow-up
  remains open.
