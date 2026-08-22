---
doc_type: plan
title: AO satellite AO batch 2 — bounded doc-fix extraction from context-scout's 2026-08-20 stale-citation sweep
summary: >-
  Extracted from `plans/active/issues/context_scout_stale_citations_and_doc_drift_2026_08_20.md` (a `/context-scout`
  Phase-3-routing doc that only ever writes `context_scope` + a marker, never a target doc's own prose — so its own
  findings sit as un-actioned Disposition checkboxes). 10 of the doc's 12 findings are bounded, mechanical doc-fixes
  (verify/correct a stale citation, bump a frontmatter date, confirm a cross-reference, migrate a batch of `related:`
  citations) with no design/judgment call remaining. Finding 7 was already resolved same-session (stays closed in the
  source doc). Finding 11 ([OPERATOR] P1, verify a live GCP scheduler regression) stays in the source doc — explicitly
  tagged for human/admin action, not extracted here.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags:
  [
    ao,
    agent-orchestrator,
    ao-dispatch,
    close-out,
    batch-2,
    satellite-docs,
    satellite-extraction,
    na-eligibility-audit,
    context-scout,
    doc-drift,
  ]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch2_finalize_2026_08_21.md,
    /plans/active/issues/context_scout_stale_citations_and_doc_drift_2026_08_20.md,
    /plans/active/task_template.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
effort: low
drift_direction: advance-docs
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/context_scout_stale_citations_and_doc_drift_2026_08_20.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md,
    /plans/active/issues/backlog_500_malformed_depends_on_comment_2026_08_19.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
  ]
source: >-
  `na-eligibility-audit 2026-08-21` (ao tranche, batch 2/3) — RECLASSIFY (per-todo split) of
  `context_scout_stale_citations_and_doc_drift_2026_08_20.md`. Conflict-check run per
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3 against every currently-active
  `assigned_vm: planning` doc + sibling `ao_satellite_ao_dispatch_batch*` docs for each of the 10 target files/findings
  below — zero overlapping claims found.
---

# AO satellite AO batch 2

> **`status: active`** — same convention as batch5-25. **`assigned_vm: planning` / `execution_scope: orchestrator-agent`**.

## Why this plan exists

`context_scout_stale_citations_and_doc_drift_2026_08_20.md`'s own summary states its scope boundary explicitly: the
`/context-scout` skill "only ever writes `context_scope` + a marker, never a target doc's own prose... routed here...
so a human/plan-reconcile can judge it." None of its 12 findings were fixed by the sweep that surfaced them. 10 of the
12 are bounded, single-file doc-fixes with a stated verification method (grep, direct read, diff comparison) and no
open design question — extracted here so they actually get dispatched instead of sitting as un-actioned Disposition
checkboxes. The source doc stays `assigned_vm: NA` for its one remaining genuinely operator-gated item (finding 11).

**Included (10 todos below)** — each touches a distinct target doc (safe for full intra-plan concurrency, no
`sequential: true` needed). **Do not edit `context_scout_stale_citations_and_doc_drift_2026_08_20.md`'s own findings
prose** — this batch's own Progress Log + the paired finalize plan reconcile evidence back into that doc's Disposition
checkboxes.

**Explicitly excluded**:

1. **Finding 7** (stale `redemption_wallet_transfer_execution_2026_08_20.md` active-copy duplicate) — already
   `[x]` RESOLVED in the source doc (a later same-session commit deleted the stale copies). Nothing to extract.
2. **Finding 11** ([OPERATOR] P1, verify 7 Cloud Scheduler targets via live `gcloud scheduler jobs describe`) — stays
   in the source doc, explicitly tagged for human/admin action (repo: deployment-service, needs live GCP access this
   skill's own charter routes to an operator, not a doc-fix worker).

## Todos

- [ ] [DOC] P3. **Finding 1 — fix or remove the stale "DOUBLE-GATED" banner** in
      `/plans/active/sports_taxonomy_p2_migration_2026_08_08.md`. The doc's header banner + "Why the API-Football gate
      exists" section describe the plan as gated on BOTH `sports_taxonomy_p1_capture_and_contracts_2026_08_08` and
      `sports_af_full_entity_completion_2026_08_03` — both are now `status: complete`/`status: resolved`
      (re-verify live before editing) and archived, so the gate has already lifted. Update or remove the banner so a
      worker reading it doesn't self-skip a genuinely-available item. Done when: the banner reflects the current
      (lifted) gate state, or is removed if no longer needed. Repo: unified-trading-pm.
- [x] ✅ [DOC] P3. **Finding 2 — the "main.md § Account-failover triggers" citation — RESOLVED 2026-08-22** in
      `/plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` items 7-9. `grep -rl "Account-failover triggers"
      agent-orchestrator` returns zero matches (checked 2026-08-20; re-verify fresh) — the only `main.md` in that repo
      is an unrelated test fixture. **RESOLVED 2026-08-22 (`/plan-reconcile ao`) — the source finding was a FALSE
      POSITIVE, and this todo as written would have made the citation worse.** `### Account-failover triggers` is real,
      at **`unified-trading-pm/agents/main.md:689`**; the zero-match grep was scoped to `agent-orchestrator`, but the
      citation was never claimed to live there (the source issue doc qualifies it as `unified-trading-pm/agents/main.md`
      at `:14` and `:234`) — only batch25's restatement dropped the repo prefix. Action taken: re-qualified both
      occurrences in `ao_satellite_ao_dispatch_batch25_2026_08_19.md` and corrected the originating finding in
      `/plans/active/issues/context_scout_stale_citations_and_doc_drift_2026_08_20.md`. The original instruction
      (repoint at `server.py`) was deliberately NOT followed — `server.py` reads the trigger table, it is not the
      table. Repo: unified-trading-pm.
- [ ] [DOC] P3. **Finding 3 — fix or remove the miscited Codex SSOTs line** in
      `/plans/active/issues/backlog_500_malformed_depends_on_comment_2026_08_19.md`. Its "## Codex SSOTs" section
      cites `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` as covering "the review-role
      done-rejected-family cross-check that this route outage broke" — that codex doc is the SSOT for the AO
      scheduled-job DISPATCH layer (systemd timers, plan_health modes, capacity queue), not review-role
      done-rejected-family cross-checks. Search the codex corpus for the actual SSOT covering that cross-check; if
      none is found, remove the miscited line rather than leave a wrong pointer. Repo: unified-trading-pm.
- [ ] [DOC] P3. **Finding 4 — bump stale `last_updated` frontmatter** on
      `/plans/active/data_completion_tradfi_2026_07_15.md`. Frontmatter currently reads `last_updated: 2026-08-09`
      (re-verify live), but in-body dated annotations (a "STATUS 2026-08-16" note, a `plan_reconciler` stale-check
      reference) run through 2026-08-16 or later. Set `last_updated` to the most recent in-body dated annotation's
      date. Repo: unified-trading-pm.
- [ ] [DOC] P3. **Finding 5 — confirm or rule out a cross-reference** between
      `/plans/active/issues/idle_lingering_session_reclaim_not_firing_2026_08_19.md` and
      `/plans/active/issues/codex_luna_heartbeat_sandbox_network_stuck_loop_2026_08_20.md`. The latter's own "session
      was reaped, not gracefully released" observation plausibly overlaps the former's title — not body-verified as
      of 2026-08-20. Read both docs' full bodies; if the mechanisms genuinely match, add a cross-reference in both
      docs' `related:` frontmatter (do not merge or edit either doc's own findings/todos); if they don't match, note
      that in this batch's own Progress Log and leave both docs untouched. Repo: unified-trading-pm.
- [ ] [DOC] P3. **Finding 6 — confirm whether a consumer-inventory doc belongs in another doc's `context_scope`**.
      Read `/plans/active/sports_taxonomy_p2_consumer_inventory_2026_08_12.md` (currently sitting in
      `/plans/active/sports_taxonomy_p2_migration_2026_08_08.md`'s own `related:` frontmatter, not yet confirmed
      relevant to that doc's sole remaining open item) and confirm whether it is genuinely relevant to that item; if
      so, add it to the migration doc's `context_scope`; if not, leave `context_scope` unchanged and note why in this
      batch's Progress Log. Repo: unified-trading-pm.
- [ ] [DOC] P3. **Finding 8 — confirm whether a todo is already closed by a shipped fix**. Read
      `/plans/active/issues/manifest_hygiene_daily_ag_list_boilerplate_bug_2026_08_19.md` todo 1's exact text against
      the shipped fix in `/plans/active/issues/manifest_hygiene_red_changed_all_2026_08_20.md`
      (`e2e-testing@0a43d0ec70` — derives both the AG-list and finding-class list from AGs/rows that actually produced
      a candidate CSV). If the shipped fix genuinely closes todo 1, flip it `[x]` with the commit SHA as evidence; if
      not, leave it open and note the gap in this batch's Progress Log. Repo: unified-trading-pm.
- [ ] [DOC] P3. **Finding 9 — verify the correct propagation mechanism for `publish-package.yml`** and fix
      `/plans/active/issues/publish_package_semver_tag_race_breaks_consumer_builds_2026_08_20.md`'s recommended-fix
      prose if it names the wrong one. The doc's recommended-fix prose says changing
      `.github/workflows/publish-package.yml` "must go through the workflow-template + `rollout-workflow-templates.sh`
      path" — but that script's own `.tmpl` set does not include `publish-package.yml`; the real propagation
      mechanism appears to be `unified-trading-pm/scripts/propagation/templates/publish-package.yml`. Confirm by
      reading `rollout-workflow-templates.sh`'s full logic + the propagation-templates dir, then correct the doc's
      prose to name the right mechanism. Repo: unified-trading-pm.
- [ ] [DOC] P3. **Finding 10 — fix a wrong-repo citation in body prose**. `/plans/active/issues/
      epsilon_zero_determinism_proof_never_runs_2026_08_20.md`'s "Measured 2026-08-20" section cites
      `strategy_service/cli/handlers/daily_determinism_handler.py:59-68` — this file does not exist in
      strategy-service; the real file is
      `batch-live-reconciliation-service/batch_live_reconciliation_service/cli/handlers/daily_determinism_handler.py`
      (already correct in the doc's own `context_scope`, only the body prose is wrong). Fix the citation in the body
      prose to match. Repo: unified-trading-pm.
- [ ] [DOC] P3. **Finding 12 — split/shrink 3 line-cap-blocked docs and/or migrate 8 archive-ref-blocked docs'
      `related:` citations**. Two structural gates blocked 11 context-scout `context_scope` refreshes on 2026-08-20:
      (a) 3 docs at/near the 1000-line corpus cap
      (`deepseek_claude_blended_provider_routing_2026_07_28.md`, `defi_migration_audit_log_2026_07_24.md`,
      `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`) — split or shrink each below the cap;
      (b) 8 docs carrying pre-existing `related:` citations to archived plans, blocked by
      `check_active_refs_archived_plans.py --only`
      (`asset_class_to_asset_group_rename_2026_07_21.md`, `ci_satellite_ao_dispatch_batch15_2026_08_16.md`,
      `citadel_satellite_ao_dispatch_batch2_2026_08_19.md`,
      `client_archetype_vehicle_eligibility_sma_vs_fund_2026_08_20.md`,
      `cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md`,
      `cloud_build_uac_publish_ordering_race_recurrence_2026_08_20.md`,
      `cloud_build_uac_publish_ordering_race_recurrence_strategy_service_2026_08_20.md`,
      `vm_disk_guard_wipes_active_slot_venvs_2026_08_20.md`) — migrate each doc's archived-plan `related:` citation to
      a codex-doc pointer per the archival ritual step 5 (cite the fact the archived doc established, not the archived
      path itself). Done when: all 3 docs are under the line cap and all 8 docs' `related:` lists no longer cite an
      archived plan directly. This is the largest single todo in this batch — still bounded/mechanical (no design
      call), but touches 11 files; safe to split across multiple workers if picked up piecemeal (file-disjoint).
      Repo: unified-trading-pm.

## Progress Log

- **2026-08-21 (na-eligibility-audit, ao tranche batch 2/3)**: Authored as the per-todo-split extraction from
  `context_scout_stale_citations_and_doc_drift_2026_08_20.md`. Conflict-checked all 10 target docs/findings against
  currently-active `assigned_vm: planning` docs and sibling `ao_satellite_ao_dispatch_batch*` docs — zero overlapping
  claims found. No todos executed yet.
