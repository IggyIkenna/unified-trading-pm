---
doc_type: issue
title: >-
  Consolidated operator action items — everything from the 2026-08-08 blocker-digest Q&A + apply + RECLASSIFY session
  that only the operator can do
summary: >-
  Single tracked list of every action across the 2026-08-08 session (80-item interactive Q&A, 6 tranche apply agents,
  7-tranche RECLASSIFY sweep) that genuinely requires the operator's own hands, credentials, exchange logins, or
  judgment — staged commands, GitHub UI clicks, git-stash cleanup across 6+ checkouts, permanent hard-stops, and reviews
  nobody else can do. Everything NOT on this list has already been applied autonomously.
status: open
nature: issue
asset_group: [cross-cutting, ao, cefi, ci, defi, infrastructure, sports]
stage: [meta]
repos: [unified-trading-pm, features-service, deployment-service]
scope: [admin]
tags: [operator-action-items, session-wrapup, stash-cleanup, secrets, blocker-digest]
related:
  [
    /plans/archive/issues/prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md,
    /plans/active/issues/tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md,
  ]
created: 2026-08-08
author: claude-agent
parent_epic: agent_operating_framework_master
priority: P1
source: >-
  End-of-session consolidation of the 2026-08-08 na-corpus blocker-digest Q&A round (80 items answered interactively),
  the 6 tranche apply agents that applied those answers, and the 7-tranche RECLASSIFY sweep that followed — requested
  explicitly by the operator ("put it all in one document... so i know at the end what to look at to do all my operator
  stuff that only i can do").
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: none
depends_on: []
locked_by:
resolved_by:
context_scope:
  [
    /plans/archive/issues/prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md,
    /plans/active/issues/tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md,
    /plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
---

# Operator action items — 2026-08-08 session

Everything below genuinely needs you — a credential only you can create, an exchange login, a UI click with no API, a
permanent hard-stop, or a judgment call flagged as needing your own review. Everything else from today's session (80 Q&A
answers, dozens of doc updates, 21 corpus reclassifications, several executed prod-bucket deletes) has already been
applied autonomously and is not repeated here.

## 1. Secrets / credentials only you can create

- [x] ✅ [OPERATOR] P2. **DONE 2026-08-09** — GSM secret `deepseek-v4-pro-api-key` created live. See
      `plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md` for evidence; re-sourcing on both hosts is
      the next (non-operator) todo there.
- [x] ✅ [OPERATOR] P2. **DONE 2026-08-09 — 5 Slack alerting webhooks provisioned to GSM, unprompted operator offer
      ("would be good to get them all ready so we can monitor them with agents").** Operator pasted all known webhook
      URLs (8 total, including duplicates); hash-compared the 2 ambiguous duplicate pairs (`#uts-live-alerts`,
      `#agent-orchestrator-alerts`) against what's already live in GSM to resolve which is current without guessing —
      `#uts-live-alerts` resolved cleanly (one pasted value matched the live `alerting-uts-live-alerts-slack-webhook`
      secret exactly, confirming which of the two was current); `#agent-orchestrator-alerts` had no existing secret to
      compare against, so the choice there is unverified — **flagging for a quick confirm**, not blocking.
      `#paper-trading-alerts` already matched the live `agent-orchestrator-paper-trading-slack-webhook` secret exactly —
      no change needed. Created/populated: `cloud-monitoring-slack-ci-failures-webhook` (was an empty shell, now has
      v1), `alerting-monitoring-deadman-slack-webhook` (new), `alerting-data-pipeline-alerts-slack-webhook` (new),
      `alerting-agent-orchestrator-alerts-slack-webhook` (new — **unverified which of 2 candidate URLs is current,
      picked the one matching the pattern of the resolved `#uts-live-alerts` case; operator should confirm the
      #agent-orchestrator-alerts channel is actually receiving posts before relying on this for paging**). Raw webhook
      URLs handled via a scratchpad temp file (session-isolated, not git-tracked) deleted immediately after use — never
      committed, never echoed back in chat.
- [ ] [OPERATOR] P2. **Set `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` in the planning VM's `.env.local`** so `ao-self-pull.sh`
      wedge/drift alerts page instead of silently logging "no webhook." Exact resolution+restart steps (mirroring
      `bootstrap_vm.sh`'s own logic) are in
      `plans/active/issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`.
- [ ] [OPERATOR] P2. **Run the staged `ORCHESTRATOR_JWT_SECRET` reconcile commands** (SM ← vm-0 direction) — exact
      `aws secretsmanager put-secret-value` + `gcloud secrets versions add` commands staged in
      `plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md`. Agent-side secret writes are permission-blocked by
      design (deliberate split of duties).
- [ ] [OPERATOR] P3. **Create `bybit-trade-api-key`/`bybit-trade-api-key-secret` in GCP** — direction already approved
      (2026-07-28), only your own Bybit exchange login can create the actual key.
      `plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md`.
- [ ] [OPERATOR] P3. **Wallet-key provisioning for OKX/Binance/Bybit + live-trading kill-switch arming** — permanent
      human-only hard-stop, gating the `ML_DIRECTIONAL_CONTINUOUS` cutover to real capital. Not time-sensitive; do when
      ready.

## 2. GitHub UI clicks (no public REST API exists for these)

- [ ] [OPERATOR] P1. **`unified-trading-pm` → Settings → Actions → General → "Require approval for all outside
      collaborators"** on fork-PR workflow runs. Confirmed live P0 exposure (public repo, 8 self-hosted runners
      attached, verified 2026-08-06 that no API endpoint exists for this setting). Sibling `allowed_actions` tightening
      in the same finding was already applied via the API. Cited in both
      `plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` and (duplicate)
      `plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md`.

## 3. Git stash cleanup — 6 checkouts audited today, all read-only, nothing dropped

Every checkout below was content-reviewed entry-by-entry (diffed against live HEAD, cross-referenced against git
history) — not just timestamp-sorted. **CLEARLY SAFE entries are ready for you to drop directly**; AMBIGUOUS entries
need your own quick look first (reasons given per checkout). `git stash drop`/`clear` is categorically blocked for
autonomous workers, so none of this was executed.

- [ ] [OPERATOR] P3. **`.tabs/1` (96 entries, ALL safe)** — `cd .tabs/1/unified-trading-pm && git stash clear` (safer
      than discrete drops here — this checkout has a live `*/5 * * * *` cron that mutates the stash list, so a
      SHA-anchored `clear` sidesteps index-drift risk). Zero genuinely-lost content found across all 96.
- [ ] [OPERATOR] P3. **`.tabs/2` (26 entries: 16 safe, 10 ambiguous)** — 16 safe drop commands ready (descending-index
      list in the audit). The 10 ambiguous entries (idx 0-9) are 10 successive snapshots of the SAME unlanded content —
      a `cefi_fwd_vm_preempted...md` "duplicate-launch race" fix section that doesn't exist anywhere in git history,
      **and the live working tree currently has an unresolved 3-way merge conflict (raw git conflict-marker syntax, all
      three parts) on that exact file** — resolve that conflict first, verify the cited `deployment-service@4c28ca640f`
      commit is real, then all 10 become safe to drop as duplicates.
- [ ] [OPERATOR] P3. **`.tabs/3` (42 entries: 30 safe, 12 ambiguous)** — 30 safe drop commands ready. Of the 12
      ambiguous: 9 are one big never-committed full-repo reformat sweep (prettier/black-style, ~988 files, matches the
      workspace's own banned "bare unpinned prettier" pattern — likely abandoned, your call whether it was ever wanted);
      the other 3 are each a single small never-landed doc-accuracy line (quoted verbatim in the audit, trivial to
      hand-reapply if wanted).
- [ ] [OPERATOR] P3. **`.tabs/4` (12 entries: 10 safe, 2 ambiguous)** — 10 safe drop commands ready. The 2 ambiguous
      (idx 7, 8) are an unlanded analytical finding from an archived issue (low stakes — the functional fix shipped a
      different way).
- [ ] [OPERATOR] P3. **`.tabs/7` (1 entry, safe)** — `git stash drop stash@{0}` (an orphan-adopted WIP already fully
      superseded by the live committed doc).
- [ ] [OPERATOR] P3. **Root clone `unified-trading-pm/` (12 entries: 11 safe, 1 ambiguous)** — 11 safe drop commands
      ready. The 1 ambiguous (idx 5) is a small "RATIFIED + LOAD-BEARING" doc-text rewrite that never landed — low
      stakes.
- [ ] [OPERATOR] P3. **`sandbox-test-user` checkout (12 entries: 7 safe, 5 ambiguous)** — this checkout turned out to be
      a **dead automation artifact from March 2026** (the actual live `quickmerge.sh` checkout of that era, last commit
      5 months ago, on `main` not `live-defi-rollout`) — worth deciding whether it's worth reconciling further at all
      vs. just retiring. 7 safe drop commands ready. Of the 5 ambiguous: 4 share the same **never-landed,
      still-outstanding security fix** — a hardcoded GCP project ID (`central-element-323112`) that should be
      `${GCP_PROJECT_ID}` in 6 scripts, attempted and lost 4 separate times across March 4-7. Worth recovering before
      dropping those 4.

Full per-entry tables with exact commands are in each sub-agent's report (not re-quoted here for length) — ask me to
pull any specific checkout's full table back up if you want it before deciding.

## 4. Reviews only you can do (judgment, not a fact-check)

- [ ] [OPERATOR] P2. **Honest-coverage mockup design reviews** (4 related sub-questions, paced to your own cadence):
      re-verify the SPORTS/PREDICTION leaf model, approve CEFI instrument-type groupings, + 2 others in the same thread.
      You said you need to review these yourself. `plans/active/cefi_consolidated_closeout_2026_07_18.md`.
- [x] ✅ [DOCS] P2. **See `plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` — RULED
      2026-08-09.** Option 2 approved (hash UAC's + UTL's resolved git ref/commit) — the doc's own stated
      recommendation. Full ruling + a mixed-eligibility cleanup found while reclassifying the doc for AO dispatch are
      recorded there, not re-litigated here. Nothing shipped yet — implementation is now AO-dispatchable
      (`assigned_vm: planning`), not hand-implemented in this pass (highest-blast-radius fleet CI gate).
- [x] ✅ [DOCS] P3. **See
      `plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md` — RULED
      2026-08-09.** Bridge the gates (option A). Full ruling + a newly-found conflict with an unproven
      backfill=paper=live precondition are recorded there, not re-litigated here.

## 5. Permanent hard-stops (not time-sensitive, listed for completeness)

- [ ] [OPERATOR] P3. **Live wallet + custody approval (Copper/CEFFU)** for the live-trading leg of the paper↔batch↔live
      determinism proof. `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md`.
- [ ] [OPERATOR] P3. **Final go-ahead for real-money live trading activation** — sports Groups A-H readiness ladder AND
      the general cross-cutting live-trading sign-off (same underlying decision, cited from 2 docs). Reserved for your
      own explicit sign-off. `plans/active/issues/sports_predictions_live_mode_activation_readiness_2026_07_21.md`.

## 6. Loose ends worth a quick look

- [x] ✅ [VERIFY] P1. **RE-CHECKED 2026-08-09 (operator, interactive) — already resolved, no action needed.**
      `.tabs/2`'s `cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md` has 0 conflict markers now;
      last touch was a routine `na-eligibility-audit` commit (`a3c8a449f`), not a manual conflict resolution — some
      other session's normal edit flow cleared it. Stale finding, closing.
- [x] [OPERATOR] P1. ✅ **`prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md`** — resolved and archived
      2026-08-09 (`/plans/archive/issues/prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md`): the
      issue's own 4 todos shipped — deterministic repro, flock-serialized `git commit` in
      `safe-doc-push.sh`/`quickmerge.sh` (`unified-trading-pm@d38f16f66`), a checksum-verify hard-stop on silent reverts
      (`unified-trading-pm@f8a307bad`), and a documented scratchpad-backup HARD RULE
      (`/codex/05-infrastructure/per-tab-worktrees.md` § "What worktree isolation does NOT cover", item 4). No remaining
      priority look needed.
- [ ] [OPERATOR] P2. **`tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md`** — a Cloud Scheduler job
      believed paused since 2026-06-25 was found still firing daily during today's tradfi §8 purge; protectively paused
      (plus a second, never-tracked weekly job) but the root cause of why the pause never took needs a look.

## Progress Log

- 2026-08-08: Filed as the consolidated wrap-up of the full 80-item Q&A + 6-agent apply + 7-tranche RECLASSIFY session,
  per the operator's explicit request for one document to work through.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **2026-08-09 (operator ruling)**: the Finding E-1 item above was ruled — bridge the gates (option A). Marked done here
  as a pointer; full ruling recorded in
  `plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md`.
- **na-eligibility-audit 2026-08-09 (round9)**: KEEP-NA, valid — this doc is a pure consolidated OPERATOR-only action
  list (credential/wallet-key provisioning, IAM/GitHub-org settings, human design reviews, live-trading sign-off,
  per-checkout stash-drop judgment calls) — every remaining item genuinely requires the operator's own hands or
  judgment. The 2 credential items this round's cheat-sheet flagged are already recorded here as DONE, with the
  re-sourcing follow-up correctly pointed at (and now extracted from)
  `deepseek_claude_blended_provider_routing_2026_07_28.md`.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of all 16 items.
  This doc's own purpose is curation of genuinely operator-only leftovers (credentials/exchange logins, GitHub UI clicks
  with no API, git-stash-drop (categorically blocked for agents), permanent hard-stops, human judgment reviews) — every
  remaining item still requires the operator's own hands per its own definition. Round9 (2026-08-09) already re-verified
  this same conclusion in detail; no new facts found this pass.

## Carried in from the 2026-08-10 ag-closeout parked-corpus close-out

Six items that genuinely still need the operator, lifted out of five dated `ag_closeout_audit_<tranche>_parked_*.md`
reports on 2026-08-10 so they live on one list instead of five, and so those reports can reach zero open todos and
archive. Nine other `[OPERATOR]` items in those same reports were resolved or re-homed to AO the same day and are closed
in place with their evidence — they are deliberately NOT repeated here.

- [ ] [OPERATOR] P2. **Confirm the 6 transcribed rulings in
      `operator_ruling_record_ao_round5_apply_session_2026_08_08.md` are accurate.** Operator-only — cannot be
      worker-determined. Carried from `ag_closeout_audit_ao_parked_2026_08_10.md` (finding 4 item 1), 2026-08-10.
- [ ] [OPERATOR] P3. **Approve or decline the ICE/OPRA Databento subscription add.** Billing decision, no data-derivable
      answer. Source `/plans/active/issues/databento_ice_opra_subscription_ask_2026_08_09.md` (retagged `[tradfi]`
      2026-08-10). Carried from `ag_closeout_audit_cross_cutting_parked_2026_08_10.md` finding 2.
- [ ] [OPERATOR] P3. **Provision `glassnode-api-key` in Secret Manager, or decline.** Glassnode is NOT a removed
      provider and the adapter is scaffolded; per `/codex/02-data/external-data-always-available-rule.md` exhausting the
      free path is a credential ask, not a descope. The Kaiko half of the original joint ask was closed by the
      2026-08-10 ruling — do not provision `kaiko-api-key`. Source
      `/plans/active/issues/glassnode_kaiko_credential_ask_2026_08_09.md`.
- [ ] [OPERATOR] P3. **Provision `sportradar-api-key` and decide Sportradar's scope, or decline.** Human-held
      credential; the sports-only `SportradarAdapter` is blocked on it. Source
      `/plans/active/issues/sportradar_credential_ask_2026_08_09.md` (retagged `[sports]` 2026-08-10). Carried from
      `ag_closeout_audit_cross_cutting_parked_2026_08_10.md` finding 6.
- [ ] [OPERATOR] P2. **Rule on `tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md`**: flip
      `status: draft` → `active`, OR provision the IPRoyal residential-proxy credential (~$7 PAYG) to unblock its items
      4/5/7, OR decline and leave it parked. Carried from `ag_closeout_audit_tradfi_parked_2026_08_10.md` finding 2.
- [ ] [OPERATOR] P1. **Complete or explicitly re-park the 2026-08-07 ruling's remaining 2/8 + 0/1 items**: flip
      `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` (+ its finalize twin) to `active`, and schedule item 8's
      fold/archive of `tradfi_consolidated_closeout_2026_07_18.md` once the currently-active tradfi batches clear.
      Carried from `ag_closeout_audit_tradfi_parked_2026_08_10.md` finding 5.

### Design calls carried in the same pass (2026-08-10)

Six human-judgment items that were pinning four dated `ag_closeout_audit_*_parked_*.md` reports open. They are not
`[OPERATOR]`-tagged at source — they are `[DOCS]`/`[LOCAL]`/`[DOC]` design calls — but none has a worker-determinable
outcome, so they belong on this list rather than in an audit report nobody owns.

- [ ] [OPERATOR] P3. **Decide where future operator-ruling sessions get recorded** among the 3 options named in
      `/plans/active/issues/operator_ruling_record_ao_round5_apply_session_2026_08_08.md` item 2. A judgment call, low
      urgency. Carried from `ag_closeout_audit_ao_parked_2026_08_10.md` 2026-08-10.
- [ ] [OPERATOR] P3. **Resolve the aggregate-zero-path signal design fork** in
      `/plans/active/issues/ao_context_pct_0_for_monitor_heavy_workers_2026_07_29.md`'s `[DATA]` todo — a two-direction
      design choice with no evidence-based tiebreaker; its `[UI]` and `[BACKEND]` todos are both blocked behind it.
      Carried 2026-08-10.
- [ ] [OPERATOR] P3. **Run `/plan-brainstorm` on
      `/plans/active/issues/context_scope_sufficiency_measurement_2026_08_08.md`'s sufficiency-metric question** before
      any implementation todo is authored — the doc's own text calls it "genuinely open-ended". Carried 2026-08-10.
- [ ] [OPERATOR] P3. **Rule on the `self_dispatched_orphan_count` addition to
      `/scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py`** — segment the headline orphan count so runs
      don't overstate the batch-needed backlog, or drop the idea. A tooling-priority call. Re-confirmed unchanged on 5
      separate audit runs (08-04/-06/-08/-09/-10), which is past the escalation trigger — it needs a ruling, not a 6th
      re-confirmation. Carried from `ag_closeout_audit_infra_parked_2026_08_03.md` finding 12, 2026-08-10.
- [ ] [OPERATOR] P3. **Scope the 2 flagged `CITE_RE`-era candidates, or drop them**: the `CITE_RE` hardening design
      (should a Progress Log narrative mention of a filename count as a dispatch citation?), and
      `/plans/active/repo_scripts_governance_audit_2026_06_18.md`'s L208/L213. Neither is ready to batch as written.
      Same 5-run escalation trigger as the entry above. Carried from `ag_closeout_audit_infra_parked_2026_08_03.md`
      finding 13, 2026-08-10.
- [ ] [OPERATOR] P2. **Decide whether `/ag-closeout-audit all` mode should budget for the full candidates-generator +
      Phase-1 sweep per tranche, or explicitly document its orphan counts as a lower bound.** The 2-vs-31 orphan gap
      between two same-day tradfi passes is a real methodology difference, not noise — an operator reading only an
      `all`-mode report would not currently know the count is partial. Carried 2026-08-10.
