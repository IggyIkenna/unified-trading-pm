---
doc_type: issue
title: >-
  context-scout 2026-08-20 sweep — 6 stale-citation / doc-drift findings surfaced during Phase 1 scouting,
  routed here since this skill only writes context_scope + a marker, never the target doc's own prose
summary: >-
  The daily /context-scout run (2026-08-20, 28 docs scouted) surfaced 6 findings that are outside the skill's
  own writable scope (context_scope frontmatter + a dated marker only — never a target doc's status/todos/prose,
  per cursor-configs/skills/context-scout/SKILL.md's explicit scope boundary). Filed here per the skill's own
  Phase 3 routing rule ("carry into the report... so a human/plan-reconcile can judge it") and per this
  workspace's "every deferral becomes a tracked item, never only prose in a chat summary" rule — none of these
  were fixed by this sweep; all are read-only observations for /plan-reconcile or the operator to action.
status: open
nature: issue
asset_group: [cross-cutting, ao, sports, tradfi]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [context-scout, plan-reconcile, stale-citation, doc-drift, findings-routing]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/issues/backlog_500_malformed_depends_on_comment_2026_08_19.md,
    /plans/active/issues/codex_luna_heartbeat_sandbox_network_stuck_loop_2026_08_20.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
  ]
created: "2026-08-20"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
assigned_role: infra
drift_direction: none
source: >-
  /context-scout daily sweep, 2026-08-20 (dispatch agt-23fb1b, slot 28) — 4-agent Phase 1 hunter fan-out over 28
  in-scope docs. Each finding below is a hunter's own STALE_CANDIDATES/SUGGESTIONS/doc-drift observation that this
  skill is scoped NOT to fix directly.
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    cursor-configs/skills/context-scout/SKILL.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md,
    /plans/active/issues/backlog_500_malformed_depends_on_comment_2026_08_19.md,
  ]
---

# context-scout 2026-08-20 — findings outside this skill's writable scope

## 1. `sports_taxonomy_p2_migration_2026_08_08.md` — the "DOUBLE-GATED" banner is now stale (moderate priority)

The doc's own header banner + "Why the API-Football gate exists" section describe this plan as gated on BOTH
`sports_taxonomy_p1_capture_and_contracts_2026_08_08` and `sports_af_full_entity_completion_2026_08_03`. Both are
now confirmed **archived** (`status: complete` and `status: resolved` respectively) — the gate has already
lifted. This doc is `assigned_vm: planning` (AO-dispatched); a worker reading the still-present banner could
mistakenly self-skip a genuinely-available item. Only 1 of 26 todos remains open (a `P0
BLOCKED-OPERATOR-DECISION`, unrelated to the gate itself), so the practical impact is small, but the banner
itself is misleading and should be updated or removed. Routed to `/plan-reconcile`, not fixed here (context-scout
never touches target-doc prose).

## 2. `ao_satellite_ao_dispatch_batch25_2026_08_19.md` items 7-9 — dead citation to "main.md § Account-failover triggers"

Items 7-9's own text cites `main.md § "Account-failover triggers"` as the trigger-table location for the
`overage_status == "rejected"` fix. `grep -rl "Account-failover triggers" agent-orchestrator` returns **zero
matches** — the only `main.md` in the repo is an unrelated test fixture at `tests/fixtures/agents/main.md`. This
is either a stale/imprecise citation left over from the source issue doc, or the real table lives outside this
checkout (a different repo, or renamed since the citation was written). Not blocking — `server.py` is already the
actual trigger-table location per direct code read — but whoever picks up items 7-9 should verify the citation
before trusting it literally.

**CORRECTED 2026-08-22 (`/plan-reconcile ao`) — this finding was a FALSE POSITIVE.** The citation is real and
resolves: `### Account-failover triggers` exists at **`unified-trading-pm/agents/main.md:689`**. The grep above was
scoped to the `agent-orchestrator` repo, but the citation never claimed to point there — the source issue doc
(`account_failover_ignores_overage_rejected_2026_08_18.md:14,234`) qualifies it fully as
`unified-trading-pm/agents/main.md`. Only batch25's restatement dropped the repo prefix, making it *ambiguous*, not
dead. The correct remedy is to **re-qualify** the citation with its repo prefix, NOT to repoint it at `server.py` —
that would replace a correct pointer to the trigger TABLE with a pointer to the code that reads it. Wrong-repo grep
scoping is the same measurement error class as CLAIM <= MEASUREMENT's "0 hits != missing".

## 3. `backlog_500_malformed_depends_on_comment_2026_08_19.md` — Codex SSOTs citation doesn't cover its own claim

The doc's "## Codex SSOTs" section cites `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` as
covering "the review-role done-rejected-family cross-check that this route outage broke." Verified: that codex
doc is the SSOT for the AO scheduled-job DISPATCH layer (systemd timers, plan_health modes, capacity queue) — it
does not cover review-role done-rejected-family cross-checks anywhere in its actual content. No confirmed
replacement citation was found this session. Routed to `/plan-reconcile` for a prose fix or removal.

## 4. `data_completion_tradfi_2026_07_15.md` — stale `last_updated` frontmatter field

Frontmatter reads `last_updated: 2026-08-09`, but in-body dated annotations (e.g. a "STATUS 2026-08-16" note, a
`plan_reconciler` stale-check reference) run through 2026-08-16. Minor, cosmetic — flagged for the next editor to
bump rather than fixed here (out of this skill's scope).

## 5. `codex_luna_heartbeat_sandbox_network_stuck_loop_2026_08_20.md` — unconfirmed candidate worth a follow-up look

`/plans/active/issues/idle_lingering_session_reclaim_not_firing_2026_08_19.md`'s title plausibly overlaps this
doc's own "session was reaped, not gracefully released" observation (both describe a session outliving its real
work and only getting cleaned up via a reap mechanism). This was **not body-verified** this session — flagging as
a candidate cross-reference for a future scout/reconcile pass to confirm or rule out, not a confirmed fingerprint
match.

## 6. `sports_taxonomy_p2_migration_2026_08_08.md` — unconfirmed related-doc suggestion

`/plans/active/sports_taxonomy_p2_consumer_inventory_2026_08_12.md` sits in this doc's own `related:` frontmatter
and is plausibly relevant to the sole remaining open item, but its content was not read/confirmed this session —
flagging rather than guessing it into `context_scope`.

## Findings from the 2026-08-20 sweep (slot 29, dispatch agt-06ab0c)

A second, independent context-scout run the same day surfaced 5 more out-of-scope findings while scouting a
different 30-doc in-scope population (Phase 0 verdicts NEVER_SCOUTED/STALE, disjoint from slot 28's batch above).

### 7. `redemption_wallet_transfer_execution_2026_08_20.md` (+ its finalize plan) — duplicate copy left at the
   active/ path after archival (real corpus bug, higher priority than the other findings here)

Mid-sweep, an incoming commit (`aed6d266a7`, "docs(plans): archive redemption_wallet_transfer_execution (6/6 done) +
finalize (3/3 done)") landed a correct, `status: archived` copy of both docs at
`plans/archive/2026_08/redemption_wallet_transfer_execution_2026_08_20.md` (+ finalize) — but **left the original
`plans/active/` copies in place, byte-identical in body content and still reading `status: active`**, instead of a
clean `git mv`. Verified directly (`git show HEAD:<path>` on both locations): the archive copy correctly shows
`status: archived` + `superseded_by: redemption_wallet_transfer_execution_finalize_2026_08_20`; the active copy
shows `status: active` with the full original body, no banner, no redirect. A worker who greps `plans/active/` for
open redemption/wallet-transfer work would find this doc, see `status: active`, and could re-work or re-dispatch
already-completed, already-archived work. **UPDATE same session**: a later incoming commit deleted both stale
active/ copies cleanly — this finding is now RESOLVED, kept here for provenance only.

### 8. `manifest_hygiene_daily_ag_list_boilerplate_bug_2026_08_19.md` todo 1 — possibly stale/already-fixed checkbox

`manifest_hygiene_red_changed_all_2026_08_20.md`'s shipped fix (`e2e-testing@0a43d0ec70`) derives both the AG-list
and finding-class list from AGs/rows that actually produced a candidate CSV — this may be the same fix
`manifest_hygiene_daily_ag_list_boilerplate_bug_2026_08_19.md` todo 1 is still tracking as open. Not independently
confirmed (would need to read that doc's exact todo text against the shipped diff).

### 9. `publish_package_semver_tag_race_breaks_consumer_builds_2026_08_20.md` — possible wrong propagation mechanism
   cited in its own recommended fix

The doc's recommended-fix prose says changing `.github/workflows/publish-package.yml` "must go through the
workflow-template + `rollout-workflow-templates.sh` path" — but `rollout-workflow-templates.sh`'s own `.tmpl` set
does not include `publish-package.yml`; the real propagation template appears to live under
`unified-trading-pm/scripts/propagation/templates/publish-package.yml`, a different mechanism. Moderate confidence,
not independently confirmed by reading `rollout-workflow-templates.sh`'s full logic.

### 10. `epsilon_zero_determinism_proof_never_runs_2026_08_20.md` body text — wrong-repo citation in its own prose

The doc's "Measured 2026-08-20" section cites
`` `strategy_service/cli/handlers/daily_determinism_handler.py:59-68` `` — this file does not exist in
strategy-service; the real file is `batch-live-reconciliation-service/batch_live_reconciliation_service/cli/handlers/daily_determinism_handler.py`.
This skill's own `context_scope` for that doc already carries the corrected path — this finding is about the
DOC'S OWN PROSE repeating the same wrong-repo error, which this skill cannot edit.

### 11. `zombie_cloud_scheduler_targets_missing_cloud_run_jobs_2026_08_20.md` — possible infra regression, HIGHEST
    priority finding in this doc (flagging prominently, not confirmed)

This doc's 7 named "enabled" dead-target Cloud Schedulers are IDENTICAL to 7 schedulers already investigated,
bulk-PAUSED, and root-caused in `asia_northeast1_zombie_schedulers_dead_targets_2026_08_07.md` (2026-08-07),
confirmed still paused as of a 2026-08-15 resolution note there. That doc's Progress Log shows no re-enable action.
Either (a) a genuine regression — something re-enabled schedulers verified paused through 08-15 — or (b) a
measurement error in the newer doc's "enabled" claim. **Not resolvable read-only** (needs a live
`gcloud scheduler jobs describe`), out of this skill's scope to investigate further.

### 12. Line-cap and archive-safety-ratchet gates blocked 11 further context_scope refreshes this session

3 docs (`deepseek_claude_blended_provider_routing_2026_07_28.md`, `defi_migration_audit_log_2026_07_24.md`,
`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`) hit the corpus line-cap hard gate mid-session
— all were already over/near the 1000L cap and the ratchet tightened between the start and end of this session
(unrelated incoming commit), so a `context_scope`-only diff that previously passed standalone later failed as
"HARD, no exemption" in the real pre-commit hook. 8 more docs (`asset_class_to_asset_group_rename_2026_07_21.md`,
`ci_satellite_ao_dispatch_batch15_2026_08_16.md`, `citadel_satellite_ao_dispatch_batch2_2026_08_19.md`,
`client_archetype_vehicle_eligibility_sma_vs_fund_2026_08_20.md`,
`cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md`,
`cloud_build_uac_publish_ordering_race_recurrence_2026_08_20.md`,
`cloud_build_uac_publish_ordering_race_recurrence_strategy_service_2026_08_20.md`,
`vm_disk_guard_wipes_active_slot_venvs_2026_08_20.md`) carry pre-existing `related:` citations to archived plans,
blocked by `check_active_refs_archived_plans.py --only` (corpus-wide baseline count=925, `operator ruling
2026-08-17`) — none of these 8 citations were added by context-scout; they predate this session. Both classes are
**structural**: they will keep blocking on every future context-scout pass over the same 11 docs until someone
(a) splits/shrinks the 3 over-cap docs, or (b) migrates the 8 `related:` archive citations to codex-doc pointers per
the archival ritual step 5 — neither is context-scout's job (it only ever writes `context_scope` + a marker). Not a
context-scout bug; flagging so the retry isn't silently assumed to be self-resolving.

## Disposition

- [ ] [DOC] P3. Fix or remove the stale "DOUBLE-GATED" banner in `sports_taxonomy_p2_migration_2026_08_08.md`
      (finding 1). Repo: unified-trading-pm. Extracted to `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_21.md` item 1 (na-eligibility-audit 2026-08-21, RECLASSIFY per-todo split).
- [ ] [DOC] P3. Verify/correct the "main.md § Account-failover triggers" citation in
      `ao_satellite_ao_dispatch_batch25_2026_08_19.md` items 7-9, or confirm `server.py` alone is sufficient and
      drop the dead citation (finding 2). Repo: unified-trading-pm. Extracted to `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_21.md` item 2 (na-eligibility-audit 2026-08-21, RECLASSIFY per-todo split).
- [ ] [DOC] P3. Fix or remove the miscited Codex SSOTs line in
      `backlog_500_malformed_depends_on_comment_2026_08_19.md` (finding 3). Repo: unified-trading-pm. Extracted to `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_21.md` item 3 (na-eligibility-audit 2026-08-21, RECLASSIFY per-todo split).
- [ ] [DOC] P3. Bump `last_updated` on `data_completion_tradfi_2026_07_15.md` (finding 4). Repo: unified-trading-pm. Extracted to `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_21.md` item 4 (na-eligibility-audit 2026-08-21, RECLASSIFY per-todo split).
- [ ] [DOC] P3. Confirm or rule out the `idle_lingering_session_reclaim_not_firing_2026_08_19.md` cross-reference
      for `codex_luna_heartbeat_sandbox_network_stuck_loop_2026_08_20.md` (finding 5). Repo: unified-trading-pm. Extracted to `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_21.md` item 5 (na-eligibility-audit 2026-08-21, RECLASSIFY per-todo split).
- [ ] [DOC] P3. Read `sports_taxonomy_p2_consumer_inventory_2026_08_12.md` and confirm whether it belongs in
      `sports_taxonomy_p2_migration_2026_08_08.md`'s `context_scope` (finding 6). Repo: unified-trading-pm. Extracted to `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_21.md` item 6 (na-eligibility-audit 2026-08-21, RECLASSIFY per-todo split).
- [x] [DOC] P2. ✅ RESOLVED — the stale `status: active` duplicate copies of
      `redemption_wallet_transfer_execution_2026_08_20.md` + its finalize plan were deleted by a later same-session
      incoming commit; the real, correctly-archived content lives in `plans/archive/2026_08/` (finding 7).
- [ ] [DOC] P3. Confirm whether `manifest_hygiene_daily_ag_list_boilerplate_bug_2026_08_19.md` todo 1 is already
      closed by `e2e-testing@0a43d0ec70` (finding 8). Repo: unified-trading-pm. Extracted to `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_21.md` item 7 (na-eligibility-audit 2026-08-21, RECLASSIFY per-todo split).
- [ ] [DOC] P3. Verify the correct propagation mechanism for `publish-package.yml` and fix
      `publish_package_semver_tag_race_breaks_consumer_builds_2026_08_20.md`'s recommended-fix prose if it names
      the wrong one (finding 9). Repo: unified-trading-pm. Extracted to `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_21.md` item 8 (na-eligibility-audit 2026-08-21, RECLASSIFY per-todo split).
- [ ] [DOC] P3. Fix the wrong-repo `daily_determinism_handler.py` citation in
      `epsilon_zero_determinism_proof_never_runs_2026_08_20.md`'s own body prose (finding 10). Extracted to `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_21.md` item 9 (na-eligibility-audit 2026-08-21, RECLASSIFY per-todo split). Repo:
      unified-trading-pm.
- [ ] [OPERATOR] P1. Verify live via `gcloud scheduler jobs describe` whether the 7 schedulers named in
      `zombie_cloud_scheduler_targets_missing_cloud_run_jobs_2026_08_20.md` are a genuine regression of
      `asia_northeast1_zombie_schedulers_dead_targets_2026_08_07.md`'s already-paused set, or a measurement error
      (finding 11). Repo: deployment-service.
- [ ] [DOC] P3. Split the 3 line-cap-blocked docs (or shrink one section each) and/or migrate the 8
      archive-ref-blocked docs' `related:` citations to codex pointers per the archival ritual step 5 (finding 12),
      so the next context-scout pass can actually land their `context_scope` refresh instead of retrying
      indefinitely. Repo: unified-trading-pm. Extracted to `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_21.md` item 10 (na-eligibility-audit 2026-08-21, RECLASSIFY per-todo split).

## Progress Log

- **2026-08-20 (context_scout_auditor, dispatch agt-23fb1b, slot 28)**: filed from the daily context-scout sweep's
  Phase 1 hunter reports — none of these 6 findings were fixed by this sweep (out of scope by design), all
  6 todos above are fresh and unclaimed.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
- **context-scout 2026-08-20 (dispatch agt-06ab0c, slot 29, recovered after a rebase conflict)**: this session
  independently scouted the same doc in parallel with the run above and had written a fuller `## Findings from the
  2026-08-20 sweep` section (findings 7-11) plus 5 more Disposition todos — a `git checkout --ours` conflict
  resolution during this session's own push (2 concurrent context-scout dispatches touching this exact file) dropped
  that section from the first push. Recovered from this session's pre-rebase local commit (`a8e5ea648e`) and
  re-appended here rather than lost; finding 7 is now marked resolved (a later incoming commit fixed it live during
  this same window) and finding 12 records the line-cap/archive-ref structural blockers this session hit on 11
  other docs. Left the other run's 4-entry `context_scope` untouched — both scouting passes are independently valid,
  no need to re-litigate whose list wins.
- **na-eligibility-audit 2026-08-21 (ao tranche batch 2/3)**: RECLASSIFY (per-todo split) — 10 of 12 findings (1-6, 8-10, 12) are bounded, single-file doc-fixes with a stated verification method and no design/judgment call remaining; extracted to `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_21.md` (+ gated `_finalize` twin), each Disposition checkbox above updated with a pointer to its extraction item. Finding 7 stays `[x]` already-resolved. Finding 11 ([OPERATOR] P1, live GCP scheduler verification) stays here — explicitly tagged for human/admin action, the sole remaining reason this doc stays `assigned_vm: NA`.
