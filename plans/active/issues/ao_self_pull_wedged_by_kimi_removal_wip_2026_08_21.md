---
doc_type: issue
title: >-
  ao-self-pull.sh wedged 52+ min (and counting) by uncommitted Kimi-removal WIP in the root
  agent-orchestrator checkout — same failure class as 2026-07-30, alerting still unconfigured
summary: >-
  Found live 2026-08-21 while verifying a just-shipped fix (`agent-orchestrator@965259913c`)
  had reached the live orchestrator. `/var/log/ao-self-pull.log` on the planning VM shows the
  root `/home/ubuntu/unified-trading-system-repos/agent-orchestrator` checkout dirty-skipping for
  26+ consecutive ~2-min ticks (~52 min at discovery, likely longer by the time this is read) with
  `WEDGE ... deploy-currency silently frozen ... no webhook` on every tick — the exact same failure
  class as `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` (archived), just a
  different blocking cause and NOT yet resolved. The dirty content is a large, coherent, real change
  (73 files, -4074/+199 lines) removing the Kimi/Moonshot provider integration end-to-end
  (`KimiWalletPanel.tsx`, `kimi_balance.py`, `kimi_balance_poller.py`, associated tests, the
  `grok_gemini_proxy.yaml` model entries, etc.) — confirmed via `plans/active/issues/
  plan_reconciler_full_corpus_sweep_2026_08_20.md`'s 2026-08-20 checkpoint entry as a KNOWN,
  in-progress, explicitly "DO NOT TOUCH" live agent task (agent `a05af12f32ba65381`), not stray or
  abandoned WIP. File mtimes (~49 min before this doc's creation) show it was touched recently, not
  simply sitting untouched since yesterday. **No code change made here** — the same hard boundary the
  2026-07-30 precedent names applies: `agents/RULES.md` §1 forbids any slot-worker session
  (including infra) from committing/modifying a root clone; this needs the owning agent to finish and
  commit its own work, or the main agent/operator to intervene.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, deploy-currency, ao-self-pull, dirty-gate, kimi-removal, silent-alert-failure]
related:
  [
    /plans/active/issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md,
    /plans/active/issues/plan_reconciler_full_corpus_sweep_2026_08_20.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
author: unknown
priority: P1
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md,
    /plans/active/issues/plan_reconciler_full_corpus_sweep_2026_08_20.md,
    agent-orchestrator/scripts/ao-self-pull.sh,
  ]
source: >-
  Interactive session, 2026-08-21 (slot 17) — discovered while verifying whether a freshly-shipped
  fix (agent-orchestrator@965259913c) had reached the live orchestrator; the root checkout's HEAD
  had not moved, which led to /var/log/ao-self-pull.log and git status on the root clone.
---

# ao-self-pull.sh wedged by uncommitted Kimi-removal WIP — fleet-wide deploy currency frozen

## What was found (2026-08-21, live)

```
2026-08-21T07:28:01Z ao-self-pull: /home/ubuntu/unified-trading-system-repos/agent-orchestrator has TRACKED uncommitted changes — skip (manual review)
2026-08-21T07:28:01Z ao-self-pull: WEDGE (tree stuck dirty (non-churn) for 26 consecutive ticks — deploy-currency silently frozen regardless of LDR drift distance) — no webhook
```

`/tmp/ao-self-pull-dirty.ticks` = `26` at discovery (~52 min at ~2-min cadence — this VM's cadence is faster than
the 07-30 precedent's ~15-min cron, per the newer `install-*-timer.sh` conventions, so the same tick count means a
shorter but still substantial wall-clock freeze). The root checkout's `HEAD` was still `19902b468d5f` (2026-08-21
06:08:56 UTC) at discovery time, well behind `live-defi-rollout`'s actual tip.

`git status --porcelain` on the root checkout shows 73 files with TRACKED (not untracked) modifications — a
coherent Kimi/Moonshot-provider removal: `dashboard/src/KimiWalletPanel.tsx` (deleted, -344 lines),
`KimiWalletPanel.test.ts` (deleted), `server/kimi_balance.py` / `kimi_balance_poller.py` (deleted from disk,
confirmed via `stat`), `tests/test_kimi_balance*.py` / `test_kimi_wallet_reconciliation.py` (deleted), the Kimi
model entries in `config/litellm/grok_gemini_proxy.yaml`, plus associated wiring changes across
`server/accounts.py`, `server/autospawn.py`, `server/model_pricing.py`, `server/model_tier.py`, `server/orm.py`,
`server/routes/accounts.py`, `server/state_store/`, and the `dashboard/` UI panels that referenced Kimi.

## This is known, in-progress work — NOT abandoned WIP to clean up

`plans/active/issues/plan_reconciler_full_corpus_sweep_2026_08_20.md`'s "Dispatched follow-ups" section
(2026-08-20 checkpoint) already names this exact change set:

> **Grok removal / Kimi routing-block** (agent-orchestrator, ...) — IN PROGRESS, mid-quality-gate at checkpoint
> time. Uncommitted working-tree changes present in `agent-orchestrator` (`dashboard/src/KimiWalletPanel.tsx`,
> `TaskUsageWindows.tsx`, `layout.tsx`, `server/model_pricing.py`, `tests/test_deepseek_provider_routing.py`, and
> others) — **DO NOT TOUCH**, this is a live agent's in-progress work, not abandoned WIP. Resume by messaging
> agent `a05af12f32ba65381` (or re-dispatch fresh with the same brief if that session is gone) if it hasn't
> self-completed and reported.

File mtimes (`dashboard/src/App.tsx` ~49 minutes before this doc was written) show the tree was touched recently
today, not simply sitting since the 2026-08-20 checkpoint — consistent with the named agent (or a resumed/fresh
dispatch of the same task) still actively working, or having worked very recently.

**No code change made in this investigation** — per the identical hard boundary the 2026-07-30 precedent already
established and documents in detail: `agents/RULES.md` §1 forbids any slot-worker session (including infra) from
committing, editing, or otherwise mutating a root clone. Read-only investigation only (`git status`, `git diff`,
`git log`, `stat`, `/var/log/ao-self-pull.log`).

## Why this matters beyond the WIP itself

Every code fix shipped to `agent-orchestrator` reaches the live dispatcher/API surface ONLY via `ao-self-pull.sh`'s
FF-pull-and-restart of this exact root checkout (per the 07-30 precedent's own finding, still true). While this
wedge holds, **every agent-orchestrator commit landed on `live-defi-rollout` since ~06:09 UTC today is silently
NOT live** — including this session's own `agent-orchestrator@965259913c` (the CI-escalation-reserve dispatch fix)
and potentially others from concurrent slots in the same window. Landing on LDR is not evidence of being live for
as long as this wedge holds.

## Alerting is STILL not configured (same gap as 2026-07-30)

The wedge-alert path fires correctly every tick (`_track_dirty_tick`, `_post_wedge_slack_alert`) but logs
`no webhook` — `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` is still not set on this host's `.env.local`. This is the SAME
open `[BLOCKED-CREDENTIALS] P2` todo from the archived 2026-07-30 doc — reaffirmed unresolved by 9 consecutive
na-eligibility-audit passes since (last: 2026-08-21, same day as this finding). Both documented candidate secret
names (`AGENT_ORCHESTRATOR_SLACK_WEBHOOK`, `alerting-uts-live-alerts-slack-webhook`) were confirmed to resolve to
nothing under `central-element-323112` on 2026-08-19 — genuinely blocked on locating the correct secret, not a
routine config action. Not re-attempting that here; cross-referenced only. **This means TWO independent live
deploy-freeze incidents (07-30 and this one) have both gone unpaged**, over three weeks apart, with the root cause
of the silence unchanged the whole time.

## Recommended decision

1. **Check whether agent `a05af12f32ba65381` (or its resumed/re-dispatched successor) is still live and finishing
   this work** — if it self-completes and commits+pushes, the wedge clears on its own via the normal
   `ao-self-pull.sh` cycle, no intervention needed.
2. **If genuinely abandoned**: someone with root-clone authority (the main agent's own session, or the operator —
   per the 07-30 precedent's explicit boundary) needs to either finish committing the Kimi-removal work if it's
   complete, or safely set it aside (e.g. `git stash` into a named, recoverable stash — never `git reset --hard`)
   so `ao-self-pull.sh` can resume pulling, without discarding real work.
3. **Separately**, the `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` gap should get real priority given this is the SECOND
   silent multi-hour(ish) fleet-wide deploy freeze it's masked — cross-referenced to the existing
   `[BLOCKED-CREDENTIALS]` todo rather than duplicated here.

## Todos

- [ ] [OPERATOR] P1. Determine whether agent `a05af12f32ba65381`'s Kimi-removal task is still live/finishing, or
      abandoned — check `/api/agents` for that agent id's current status, or ask in chat. If live, no action
      needed beyond waiting. If abandoned, decide how to land or safely park the WIP (see Recommended decision
      above) so `ao-self-pull.sh` can resume. Repo: agent-orchestrator, host-level (root clone) — outside any slot
      worker's authorized scope.
- [ ] [SCRIPT] P2. Once the wedge clears, confirm the root checkout's `HEAD` actually reaches
      `agent-orchestrator@965259913c` (this session's CI-escalation-reserve fix) and that `orchestrator.service`'s
      `ExecMainStartTimestamp` moved forward — closes the live-re-verify todo already open in
      `ci_escalation_reserve_slots_claimed_by_class_a_dispatch_2026_08_21.md`. Repo: agent-orchestrator.
- [ ] [OPERATOR] P2. This wedge is a recurrence of the same failure class as
      `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` — consider raising the priority on that
      doc's still-open `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` secret-lookup todo (currently held on the missing
      credential), since it has now masked two separate live deploy-freeze incidents. Cross-referenced only, not
      duplicated here. Repo: agent-orchestrator, host-level.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`
- `/codex/04-architecture/agent-orchestrator-alerting.md`

## Progress Log

- **2026-08-21 (slot 17, interactive)**: found while verifying deployment of an unrelated shipped fix. Read-only
  investigation only (log tail, `git status`/`diff`/`log`, file mtimes); cross-referenced against the 2026-07-30
  precedent and the 2026-08-20 plan-reconciler checkpoint that already flagged this exact WIP as "do not touch."
  No code/root-clone change made. Filed for operator visibility given the fleet-wide, unpaged deploy-currency
  impact.
