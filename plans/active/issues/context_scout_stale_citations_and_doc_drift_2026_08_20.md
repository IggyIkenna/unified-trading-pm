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

## Disposition

- [ ] [DOC] P3. Fix or remove the stale "DOUBLE-GATED" banner in `sports_taxonomy_p2_migration_2026_08_08.md`
      (finding 1). Repo: unified-trading-pm.
- [ ] [DOC] P3. Verify/correct the "main.md § Account-failover triggers" citation in
      `ao_satellite_ao_dispatch_batch25_2026_08_19.md` items 7-9, or confirm `server.py` alone is sufficient and
      drop the dead citation (finding 2). Repo: unified-trading-pm.
- [ ] [DOC] P3. Fix or remove the miscited Codex SSOTs line in
      `backlog_500_malformed_depends_on_comment_2026_08_19.md` (finding 3). Repo: unified-trading-pm.
- [ ] [DOC] P3. Bump `last_updated` on `data_completion_tradfi_2026_07_15.md` (finding 4). Repo: unified-trading-pm.
- [ ] [DOC] P3. Confirm or rule out the `idle_lingering_session_reclaim_not_firing_2026_08_19.md` cross-reference
      for `codex_luna_heartbeat_sandbox_network_stuck_loop_2026_08_20.md` (finding 5). Repo: unified-trading-pm.
- [ ] [DOC] P3. Read `sports_taxonomy_p2_consumer_inventory_2026_08_12.md` and confirm whether it belongs in
      `sports_taxonomy_p2_migration_2026_08_08.md`'s `context_scope` (finding 6). Repo: unified-trading-pm.

## Progress Log

- **2026-08-20 (context_scout_auditor, dispatch agt-23fb1b, slot 28)**: filed from the daily context-scout sweep's
  Phase 1 hunter reports — none of these 6 findings were fixed by this sweep (out of scope by design), all
  6 todos above are fresh and unclaimed.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
