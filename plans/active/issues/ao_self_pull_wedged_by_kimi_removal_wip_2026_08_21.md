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

- [x] [OPERATOR] P1. ✅ **RESOLVED 2026-08-21 (interactive session, slot 13).** The WIP was this session's own
      task (Kimi + OmniRoute + OpenRouter provider removal, operator-directed cleanup) — not abandoned, but it had
      been built directly in the root checkout by mistake (a session error, not intended), which is exactly what
      caused this wedge. Root-caused and fixed: the full diff was captured as a patch (`git diff HEAD`), verified
      byte-identical after applying to the correct per-slot checkout (`.tabs/13/agent-orchestrator`), THEN the root
      checkout was safely cleared via `git stash push -u` (not `git reset --hard`, which a repo guardrail hook
      blocks outright for exactly this class of action) once the backup was confirmed. The real work was finished,
      quality-gated (5262 tests passed, 86% coverage, ratchet-clean), and shipped from the correct slot:
      `agent-orchestrator@055bd037b7`.
- [x] [SCRIPT] P2. ✅ **CONFIRMED 2026-08-21.** `ao-self-pull.sh` unwedged immediately once the root checkout went
      clean — log shows `FF b7bada32 -> 055bd037 — restarting orchestrator` at 08:04:01Z, then
      `FF 055bd037 -> 510c794a` at 08:06:01Z, `orchestrator restarted (active=active)` both times.
      `systemctl show orchestrator -p ExecMainStartTimestamp` = `2026-08-21 08:06:35 UTC` (genuinely restarted, not
      stale). `git merge-base --is-ancestor 965259913c HEAD` on the root checkout confirms TRUE — this session's own
      CI-escalation-reserve fix reached live along with everything else queued behind the wedge.
      `/tmp/ao-self-pull-dirty.ticks` is gone (counter cleared). Fully live, verified.
- [ ] [OPERATOR] P2. This wedge is a recurrence of the same failure class as
      `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` — consider raising the priority on that
      doc's still-open `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` secret-lookup todo (currently held on the missing
      credential), since it has now masked two separate live deploy-freeze incidents (07-30, and this one — both
      ran 50min+ fully unpaged). Cross-referenced only, not duplicated here. Repo: agent-orchestrator, host-level.
- [x] [BACKEND] P2. ✅ **DONE 2026-08-21.** Root cause of the mis-location itself: an interactive session's own
      delegated sub-agent was given a `WorkingDirectory`-style path
      (`/home/ubuntu/unified-trading-system-repos/agent-orchestrator` — the root clone, and coincidentally also
      `orchestrator.service`'s live `WorkingDirectory`) instead of its assigned per-slot checkout. No code fix
      needed — this is an authoring-discipline gap (the delegating prompt named the wrong path), not a bug in
      `ao-self-pull.sh`/the guardrail hook, both of which behaved correctly (wedge-and-alert, block `reset --hard`).
      Fixed by adding a line to `SUB_AGENT_MANDATORY_RULES.md`'s per-slot-worktree section: "If YOUR prompt never
      named an absolute `.tabs/<N>/` path, STOP and ask — never default to the bare repo root." File now 10,119 B,
      under the 10,240 B hard cap. Same edit also flipped todo in
      `ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md`.

- [x] [OPERATOR] P3. ✅ **RESOLVED same session, 2026-08-21 (slot 1, pre-compact audit) — a SEPARATE, narrow residual
      of this same landing, found then fixed since it was live-blocking the quality gate.** Slot 1's own
      `.tabs/1/agent-orchestrator` checkout had an unresolved `git stash pop` conflict in
      `config/litellm/grok_gemini_proxy.yaml` (both conflict-side markers present, `git status` showed `UU`) — a
      leftover autostash (`stash@{0}`) from this slot's own repeated `quickmerge`/`safe-doc-push` pull-rebase
      cycles colliding with the incoming `055bd037b7` Kimi-removal commit. Initially flagged read-only (foreign
      pre-existing content, `never git stash drop foreign WIP`), but a routine `quality-gates.sh` re-run in the
      same session found it was actively failing `test_proxy_config_file_exists_and_parses` (malformed YAML) —
      genuinely blocking, not cosmetic, so it needed resolving rather than staying flagged. Diagnosed both sides
      before touching it (`git log --all -p` confirmed the "stashed" side's Gemini Paid-Tier-3 `proj5` entries had
      NEVER been committed anywhere — the only surviving copy — while `grok_gemini_translation_proxy_2026_08_14.md`
      confirmed they were real, intentional, planned capacity, not stray content) — kept the `proj5` entries,
      dropped the Kimi block (confirmed correctly-removed per this doc's own resolution above). Verified: no
      residual conflict markers, YAML parses (9 models), the specific failing test passes (57 passed/2 skipped),
      full `quality-gates.sh` green. Shipped `agent-orchestrator@ff1abe563f`. NOT caused by or related to the
      mis-located sub-agent (todo 4) — ordinary autostash collision on a shared/reused checkout.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`
- `/codex/04-architecture/agent-orchestrator-alerting.md`

## Progress Log

- **2026-08-21 (slot 17, interactive)**: found while verifying deployment of an unrelated shipped fix. Read-only
  investigation only (log tail, `git status`/`diff`/`log`, file mtimes); cross-referenced against the 2026-07-30
  precedent and the 2026-08-20 plan-reconciler checkpoint that already flagged this exact WIP as "do not touch."
  No code/root-clone change made. Filed for operator visibility given the fleet-wide, unpaged deploy-currency
  impact.
- **2026-08-21 (slot 13, interactive) — RESOLVED.** This was that same session, having realized mid-task its
  delegated sub-agent had been pointed at the root clone by mistake. Recovered without data loss: `git diff HEAD`
  captured the full 73-file diff, applied to `.tabs/13/agent-orchestrator` (freshly pulled to match), verified
  byte-identical (`diff <(git diff HEAD) <saved patch>` empty on both sides), THEN the root checkout was cleared
  via `git stash push -u` (a repo guardrail hook actively blocks `git reset --hard` for this exact class of
  action — used the sanctioned alternative instead). Finished the removal from the correct slot: fixed a real
  `ruff format` drift the gate caught, full quality-gates.sh passed clean (5262 tests, 86.04% coverage vs 85.86%
  baseline, basedpyright/tsc/vitest all green), shipped `agent-orchestrator@055bd037b7` via quickmerge. Confirmed
  live: `ao-self-pull.sh` FF'd the root checkout twice within the next 2 ticks
  (`b7bada32→055bd037→510c794a`), restarted `orchestrator.service` both times, dirty-tick counter cleared. One
  new follow-up filed (todo 4) on the actual root cause — a sub-agent delegation prompt naming the wrong path —
  since that's a real authoring gap distinct from "abandoned WIP."
