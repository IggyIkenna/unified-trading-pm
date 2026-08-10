---
doc_type: plan
title: AO satellite AO batch 10 — 6 bounded items extracted from 3 non-qualifying `ao`-tranche NA docs
summary: >-
  TENTH AO-dispatch batch for the `ao` topic tranche — produced by a satellite-batch-extraction pass (mirroring
  `/ag-closeout-audit`'s pattern) over 21 `ao`-owned `assigned_vm: NA` docs that a same-day RECLASSIFY sweep read
  end-to-end but did NOT whole-doc-flip (each has real remaining judgment/operator-gated items). This batch pulls out
  ONLY the specific bounded, worker-determinable items from 3 of those 21 docs — everything else in each source doc
  (genuine design forks, credential/host-only actions, operator-gated decisions, standing-ruling citations) is left
  untouched in place. 2 items from `ao_satellite_ao_dispatch_batch2_2026_07_30.md` (itself an `assigned_vm: NA`
  satellite doc whose own repeated na-eligibility-audit verdicts lumped 3 open items together as needing "specialized
  SSM/host/credential access" without a fresh per-item split — re-examined here: the timer-fire check and the
  wip-preserve ref recovery are ordinary read-only/git-archaeology work any AO worker on the fleet can do, only the
  token re-mint on a named host genuinely needs operator/credential access and stays behind); 3 items from
  `ao_open_issues_consolidated_close_out_2026_07_17.md` (a 980-line LOCAL/human hub doc — the archival sweep, the
  plan_reconciler end-to-end observation, and the role-lifecycle-field reclassification are all bounded audit/build work
  with stated gates, left behind: the open-ended `tmux_session_lost` churn hunt, the already-moot
  `ao_docs_reconciliation` close-out citation, and the safety-domain Layer-1 recovery-audit-signoff producer rewire,
  whose "decide a SignoffVerdict" internals are unspecified design work); 1 item from
  `dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md` (the empirically-proven, no-longer-judgment-call
  package.json version bump — its sibling "should the dashboard gate on formatting at all" item stays, a genuine
  undecided policy call). All 6 todos are file-disjoint (verified during drafting) so this plan needs no `sequential`
  gate.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, strategy-service]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-10, satellite-docs, satellite-extraction]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch10_finalize_2026_08_09.md,
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/active/issues/dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/active/issues/dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md,
    agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh,
    agent-orchestrator/agents/,
    agent-orchestrator/dashboard/package.json,
  ]
source: >-
  Satellite-batch-extraction pass, 2026-08-09, mirroring `/ag-closeout-audit`'s satellite-batch pattern per operator
  instruction — a targeted per-item extraction over the 21 `ao`-tranche `assigned_vm: NA` docs a same-day RECLASSIFY
  sweep read end-to-end without a whole-doc flip. Every item below was individually checked against
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` §"Dispatch-scope eligibility" and
  conflict-checked against the live `assigned_vm: planning` corpus (batch7/batch8/batch9, `ao_open_issues`'s own
  split-out-child-plans table, and each item's own source doc's na-eligibility-audit history) before being drafted — see
  this batch's own Progress Log for the per-item conflict-check trail.
---

# AO satellite AO batch 10

> **`status: draft`** — pending operator approval, same convention as batch5-9: flip to `active` to dispatch.
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** once approved, same as the rest of this series.

## Why this plan exists

Today's earlier RECLASSIFY sweep read all 21 `ao`-tranche `assigned_vm: NA` docs end-to-end and found 8 that qualified
for a whole-doc flip (handled separately). The other 13 did not qualify — but "doesn't qualify as a whole doc" is not
the same as "nothing in it is dispatchable." This batch is the satellite-extraction pass over those 13 (mirroring
`/ag-closeout-audit`'s pattern, generalized to per-item instead of per-doc): read each doc fully, classify every open
item against the dispatch-scope-eligibility bar, and pull out only the items that are genuinely bounded and
worker-determinable, leaving every judgment/operator-gated item untouched in its source doc.

**Yield was low by design, not by shortfall**: of the 21 candidate docs, 3 contributed the 6 items below; the other 18
had zero extractable items (each doc's remaining open work is either a genuine design fork, an explicit operator/
credential/host-only action, already fully resolved with a stale checkbox, already archived, or — in one case — already
re-flagged `assigned_vm: planning` directly by a prior session and no longer NA at all). See this plan's Progress Log
and the parent extraction session's own report for the full per-doc disposition.

## Rules for every worker on this plan

- **Do not edit the 3 source docs' remaining checkboxes** beyond what this plan's own todos below already changed at
  drafting time (a redirect-pointer replacing the extracted item's checkbox text). Append your evidence to THIS plan's
  own todo when you finish; the paired finalize plan
  (`/plans/active/ao_satellite_ao_dispatch_batch10_finalize_2026_08_09.md`) reconciles the evidence back into each
  source doc.
- The 6 todos below are file-disjoint by construction — keep new test/evidence files scoped to the todo's own concern.
- No todo below deletes prod data or launches a VM. Todo 6 mutates a `package.json` + lockfile only.

## Todos

- [x] ✅ [SCRIPT] P3. **Verify whether `na-eligibility-auditor.timer`'s most recent scheduled fire(s) since 2026-07-28
      reached `agent_kind=na_eligibility_auditor` lifecycle-complete.** — agent-orchestrator (read-only query, no
      commit). **Verdict: YES, later fires do complete end-to-end** — the specific 2026-07-28 07:00 UTC
      `TimeoutStartSec=2450` curl-TIMEOUT failure mode is superseded: `TimeoutStartSec` was raised 2450→21600s on
      2026-08-04 (`ao_scheduled_job_reserve_and_staggering_2026_08_04.md`, agent-orchestrator@17939c3), and live
      `agents` table rows postdating that fix (queried directly from `data/state/state.db` on the orchestrator VM, no
      SSM needed — DB only retains rows from 2026-08-08 onward, so the exact 2026-07-28 row itself is no longer present)
      confirm actual completions: 10 `agent_kind=na_eligibility_auditor` rows reached `exit_reason=lifecycle-complete`
      across 3 fires (2026-08-08 02:33-03:02 UTC: `agt-e640f6`/`agt-763d00`; 2026-08-09 02:10-03:26 UTC:
      `agt-913589`/`agt-aedcde`/ `agt-eee16e`; 2026-08-09 05:17-08:31 UTC — the most recent fully-terminal fire —
      `agt-f74e23` (49.1min), `agt-3df41f` (146.2min), `agt-b831d5` (127.8min), vs. 2 siblings in that same fire
      `reaped-stale` at 181.3min/ 145.8min). The most recent fire (2026-08-10 ~01:47 UTC, still in-progress as of this
      check at 02:07 UTC) has 4 still `active` and 4 already `reaped-stale` (0 `lifecycle-complete` yet) — too early to
      verdict, and in any case `reaped-stale` is a DIFFERENT, already-tracked failure mode (per-agent staleness reap,
      not the systemd-service-level curl timeout this todo was scoped to) — see the climbing-reaped-stale-rate open
      todos already tracked in `ao_scheduled_job_reserve_and_staggering_2026_08_04.md` (no new issue doc filed here to
      avoid duplicating that tracking). Timeout value left untouched per instruction. — unified-trading-pm@(this commit)
- [x] ✅ [DATA] P2. **Check + recover-or-dispose `strategy-service`'s stranded wip-preserve ref
      (`refs/wip-preserve/cascade-strategy-service-a77eb6d170ca`, 2026-07-28, a `staging-lock-check.yml`
      self-hosted-runner-migration commit).** Check whether it was independently superseded by a later rollout in
      strategy-service; if so, the ref is safely superseded and can be deleted (cite the superseding SHA). If not,
      recover it the same way the sibling `unified-trading-library` ref was already recovered under this same source
      finding (fetch the preserved ref, cherry-pick/fast-forward it onto current `origin/live-defi-rollout`, ship via
      quickmerge). **Done when**: the ref's disposition (superseded-and-deleted, or recovered-and-shipped) is recorded
      with evidence in this todo. Source: `/plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md:242` (its
      `[DATA] P2` item, itself sourced from
      `/plans/archive/2026_08/wip_preserve_refs_silently_unrecovered_2026_07_29.md`, archived). Repo: strategy-service.
      **DONE 2026-08-10 (slot 3, data_engineering) — SUPERSEDED, ref deleted, no recovery needed.** Fetched the ref's
      commit (`a77eb6d170ca03eb37babce951a1b6914f3f677c`, "fix(ci): sync staging-lock-check.yml from template
      (self-hosted runner migration)", touches only `.github/workflows/staging-lock-check.yml` `runs-on: ubuntu-latest`
      → `[self-hosted, glue]` on both jobs). Its diff is **byte-identical** to
      `strategy-service@400d3773cc727b15fc63e70b4a41c8d84f6cc9cf` ("feat(ci): migrate remaining workflows to self-hosted
      (Wave-2 A+B+C)", 2026-07-28T16:41:45+01:00, ~2h after the wip-preserve commit) — same file, same exact `runs-on`
      change on both jobs, confirmed already an ancestor of `origin/live-defi-rollout`. (The file has since been
      refactored twice more — `ddf59b8b` converted it to a thin caller into `unified-trading-ci`'s reusable
      `staging-lock-check.yml@main`, passing `self_hosted_runner_labels`, so the self-hosted intent is preserved
      end-to-end.) This cross-validates the independent automated-verifier finding already on record for this exact ref
      (`ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s fleet-wide `_orphan_verify.py` sweep, slot-15 row:
      `a77eb6d170ca` in strategy-service → `SUPERSEDED`, "staging-lock-check.yml identical"). The ref itself was never
      pushed to GitHub (`git ls-remote origin 'refs/wip-preserve/*'` on strategy-service returns empty) — it existed
      only as a stale local `refs/remotes/origin/wip-preserve/     cascade-strategy-service-a77eb6d170ca` tracking ref
      cached inside this slot's `.tabs/3/strategy-service/.git` (a leftover from an earlier ad-hoc `git fetch` by ref
      name, not a real remote ref); deleted via
      `git update-ref -d refs/remotes/origin/wip-preserve/cascade-strategy-service-a77eb6d170ca` (confirmed gone via
      `git for-each-ref`). No code change needed in strategy-service — the commit object itself is untouched in the
      object store (nothing destructive; only the stale local pointer was removed). (repo: strategy-service,
      investigation + local ref cleanup only, no quickmerge needed)
- [x] ✅ [REVIEW] P1. **Sweep `plans/active/issues/` for `ao`-tagged docs that are already resolved/fully-`[x]` but
      never archived, and archive each via the standard 6-step ritual** (banner, codex-alignment check, corpus-wide
      referrer fixup, lock check). This is the current-state form of the source doc's Phase-5 gate — do not trust its
      stale "Docs #2 and #6" reference (those predate several archival waves already landed since 2026-07-17); re-derive
      the candidate set fresh from a live grep/`check_archive_candidates.sh`-style pass scoped to `asset_group: [ao]` /
      `parent_epic: orchestrator_master` docs. **Done when**: `plans/active/issues/` contains no resolved-but-
      unarchived `ao`-tagged doc, and `regenerate_active_plan_inventory.py` is re-run clean. Source:
      `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md:479` (Phase 5, its `[REVIEW] P0` item). Repo:
      unified-trading-pm. — unified-trading-pm@ (this commit). **Re-derived the candidate set fresh (not the stale "Docs
      #2 and #6" reference)**: found all 57 `plans/active/issues/*.md` docs matching `asset_group: [ao]` OR
      `parent_epic: orchestrator_master`, checked each for 0-open-todos-with-`>0`-done (mirroring
      `check_archive_candidates.sh`'s own criterion) plus a terminal `status:` field independent of checkbox state.
      Result: **0 genuine orphans** — `check_archive_candidates.sh` (0 candidates, baseline 0) and
      `check_terminal_status_archived.py` (0 violations, baseline 0) both confirm corpus-wide, and the manual per-doc
      sweep found the same 0 within the `ao`/`orchestrator_master` subset. 4 docs surfaced by a naive 0-open-todos grep
      are NOT real orphans, each already correctly held back by an existing mechanism: (1)
      `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md` — 0 open todos but legitimately
      `gate_on_depends`-gated by its own active finalize plan
      (`multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01_finalize_2026_08_08.md`, confirmed
      `depends_on`+`gate_on_depends: true` wiring); (2)
      `ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30.md` and (3)
      `e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md` — both `archive_exempt: true`, correctly
      routed through `ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`'s and
      `ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md`'s own `[REVIEW]` archival todos respectively, both
      re-verified current as recently as 2026-08-07/2026-08-09 per their own Progress Logs; (4)
      `ao_park_disposition_blocked_answer_no_follow_through_2026_07_31.md` — `status: resolved`, 0 open todos, but
      carries the standing corpus-wide `locked_by: live-defi-rollout` lock shared with 62 other active docs (not a
      per-editor claim) — per `plans/PLAN_FORMAT.md`'s own archive-eligibility rule ("not `locked_by:` an active
      branch") this doc is archival-INELIGIBLE until an explicit `[unlock-plan]`, so per this codex's HARD RULE ("MUST
      NEVER unlock autonomously") it was correctly left untouched, not force-archived.
      `regenerate_active_plan_inventory.py` re-run: **0 orphans** (297 plans, 0 TBD, 63% done overall) — dashboard file
      regenerated + committed alongside. Net: 0 archival actions required this pass — a legitimate 0-yield audit
      outcome, not a shortfall.
- [x] ✅ [BACKEND] P1. **Prove ONE `plan_reconciler` run end-to-end (observe the next natural 01:00 UTC timer fire, or
      trigger one if the doc's stated hold has cleared) — plus pin 2 named residuals.** Gate: (a) observe a full run
      producing BOTH a `plan_health_result` activity row AND a pushed `plan_reconciler/<dispatch_id>` branch — cite the
      dispatch_id, result row, and branch name, do not tick on a green-looking journal line alone; (b) **R1** — pin the
      exact code path that flips a typed agent's slot `working`→`idle` (previously empirically observed around a service
      restart, not yet located in code — already checked & excluded: seed-from-tabs, claim_slot, the dispatch-ack
      requeue, the 25-min health stale-timeout); (c) **R2** — on the run, confirm the watchdog logs an EXEMPTION for the
      reconciler's slot (`typed_agent_sessions` continuation in `worker_liveness_watchdog.py`) instead of a kill, and
      capture the slot's status column during the run — if it still reaps, the `AgentRow` guard is being defeated
      (investigate whether a restart archives/clears the AgentRow or its `tmux_session`). The operator-directed hold on
      retrying this (pending several other AO plans settling) has since cleared — all 6 named plans are confirmed
      archived as of the source doc's 2026-08-06 re-verification. **Done when**: (a)/(b)/(c) all recorded with evidence.
      Source: `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md:806` (its `[BACKEND] P0` item). Repo:
      agent-orchestrator. — **2026-08-10, evidence below** (queried the LIVE `data/state/state.db` +
      `journalctl -u orchestrator.service` directly on the `planning` VM; no SSM needed, per this todo's own
      context_scope pointer):

      **(a) — a full run completed end-to-end**, not just once but as standing behavior since 2026-08-06 (the current
                          per-tranche-sharded form of the timer, `plan-reconciler.timer` firing `00:01:05` UTC daily, not the doc's
                          stale "01:00 UTC" description). Cited instance: `dispatch_id=agt-a398c9` — `plan_health_dispatch_initiated`
                          activity row id `396415` @ `2026-08-09 03:02:46 UTC` (`mode=reconcile`) → `plan_health_result` @
                          `2026-08-09 04:43:25 UTC` (`contradictions=5, doc_drift=5, fixes_applied=12, filed=4,
                          commit_sha=40ad77233, pr_url=https://github.com/IggyIkenna/unified-trading-pm/pull/2653`) → branch
                          `refs/heads/plan_reconciler/agt-a398c9` confirmed present on `origin` via `git ls-remote --heads origin
                          'plan_reconciler/*'` (tip `63c087dd6bb85feeb4a8c4d59a986a82db6d6281`, committed `2026-08-09 04:58:35 UTC`).
                          Not cherry-picked: cross-referencing every `mode=reconcile` dispatch_id against `plan_health_result` rows
                          across full DB history found **20 completed reconcile runs since `agt-4fdce1` (2026-08-06 00:00) through
                          `agt-a398c9` (2026-08-09)**, each with a matching pushed `plan_reconciler/<dispatch_id>` branch on origin — the
                          reconciler has been completing to its own contract on a standing, repeated basis, not as a one-off fluke.

                          **(b) R1 — the exact code path pinned**: `WorkerLivenessWatchdog._reclaim_exited_slot()`
                          (`agent-orchestrator/server/worker_liveness_watchdog.py:1311-1359`), called from `_tick_once`'s active-slots
                          loop when `has_session(tmux_session)` returns `False` for a slot in `{working, dispatched, stale}`. A typed
                          agent (plan_reconciler et al.) never populates `slot.current_task` (it's tracked via the `agents` table, not a
                          `TaskRow` dispatch), so the function's `if task_id is not None:` branch is skipped and it falls straight to
                          `reset_slot_worker_state(db, slot_id, new_status="idle")` (line ~1359) — the literal `working`→`idle` write.
                          **This is strictly GATED on `has_session()` already being `False`** — i.e. it is a downstream CONSEQUENCE of the
                          tmux session already being dead, never the cause of death. Confirmed still firing live in production (7×
                          since 2026-08-01 per `journalctl`, incl. 3× in the hour preceding this evidence alone, e.g. `"slot 0: worker
                          session gone post-spawn → reclaimed to idle (clean exit)"`). Separately, the code's own inline comment at
                          `worker_liveness_watchdog.py:1421-1426` (dated 2026-07-21, `ao_uniform_agent_liveness_contract` C1) documents
                          that the OLD `_reclaim_idle_lingering_sessions`' "typed-agent carve-out is GONE: a one-off is now `working`
                          throughout... this idle/stale-scanning reclaimer never sees a working one-off" — i.e. that function
                          (the one the doc's stale `worker_liveness_watchdog.py:1172` pointer was aimed at) is now STRUCTURALLY
                          incapable of flipping a live typed agent's slot at all (it only scans slots already `idle`/`stale`); only
                          `_reclaim_exited_slot`, gated on confirmed session-death, can do it.

                          **(c) R2 — confirmed live, in real time, during this exact investigation**: 2 of today's 4 successfully-spawned
                          reconciler tranches were STILL RUNNING while this evidence was gathered — cross-cutting (`agt-33a6ec`,
                          `orch-slot-28`, spawned `00:09:32`) and sports (`agt-8005f6`, `orch-slot-19`, spawned `00:10:51`), both
                          `agents.lifecycle="scheduled"`. At the moment of measurement, `orch-slot-19`'s `last_ping` was `3134s` (~52 min)
                          stale — well past the **900s** (15 min) persistent-worker `watchdog_heartbeat_timeout` default
                          (`server/config.py:489`) — yet `slots.status` remained `"working"`, not reaped, because
                          `WorkerLivenessWatchdog._heartbeat_timeout_for()` (`worker_liveness_watchdog.py:715-727`) grants any slot in
                          `_terminal_lifecycle_slot_ids()` (`agent.lifecycle in {"one_shot","scheduled"}`, line ~214-233 — the current-code
                          equivalent of the doc's stale `typed_agent_sessions` pointer) the extended `watchdog_scheduled_heartbeat_timeout`
                          budget (**3600s**/60min, `config.py:499`) instead. Both agents' `tmux_session` fields correctly map back to
                          `orch-slot-19`/`orch-slot-28`. **AgentRow guard is NOT being defeated** — no reap occurred despite silence
                          well past the ordinary-worker threshold, observed live rather than inferred from a log line (the current code
                          grants the exemption via an extended timeout comparison, not a printed "EXEMPTION" log — there is no such
                          string in the current source, only the numeric effect, which is what was measured here).

                          **Residual, newly-discovered — filed separately, NOT part of this todo's gate**: 2 of today's 4 dispatched
                          tranches (`ao`=`agt-128e4d`/slot-10, `ci`=`agt-f2fae2`/slot-12) DID die today — but via `tmux_pruner`'s
                          independent `has_session()==False` sweep (`tmux_session_lost`, `new_status="killed"`, NOT `"idle"`), a
                          different code path than either R1 or R2 above, and one the `f641968`-era exemption guard was never built to
                          cover. No watchdog kill-trigger log fired for either slot; root cause of the tmux-session loss itself is
                          undetermined (checked: not the 00:15 service restart per `KillMode=process` + ~25 sibling sessions spawned in
                          the same window surviving it; not an OOM-kill per `journalctl -k`). Tracked as a new issue:
                          `/plans/active/issues/plan_reconciler_unexplained_tmux_session_loss_2026_08_10.md`.

- [x] ✅ [BACKEND] P2. **Role lifecycle-field reclassification — align the declared `lifecycle` on plan-worker roles
      with reality.** `backend_engineer` / `ui_developer` / `quant_dev` / `infra` are declared `lifecycle: one_shot` in
      their role files; reclassify to `persistent`, and resolve `data_engineering` (scheduled-vs-persistent) to
      whichever it actually is. **NOT required for correctness** — the shipped dispatch fix already rekeys reaping on
      DISPATCH CONTEXT (a bound `one_shot` `AgentRow`), so nothing reads `role.lifecycle` to decide reaping any more;
      this is a declared-vs-actual documentation-integrity fix. **Done when**: each role's `lifecycle` field matches its
      real dispatch pattern, or a recorded decision states why the declared value intentionally stays (cite the reason
      inline in the role file or a codex doc). Source:
      `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md:828` (its `[BACKEND] P0` item, itself sourced
      from `ao_worker_lifecycle_dispatch_context_2026_07_21.md`, archived). Repo: agent-orchestrator. — DONE 2026-08-10:
      `agents/{backend_engineer,ui_developer,quant_dev,infra,     data_engineering}.md` all now declare
      `lifecycle: persistent` (they're plan-backlog workers draining the backlog via the same /boot-work-/done loop as
      `worker`, not event-spawned one-offs); `data_engineering` resolved to `persistent` (matches its real
      [DATA]-tag/backlog dispatch origin per the 2026-08-06 `task_role_group` ruling, not cron). Updated the
      agent-orchestrator tests/comments that hardcoded the old declared values (`test_role_registry.py` `_EXPECTED`,
      `test_reap_orphan_agents.py`, `test_task_usage_windows.py` docstrings, `tests/fixtures/agents/*.md` mirrors,
      `state_store/{agents,slots}.py` comments) + the 2 codex SSOTs that documented this as deferred
      (`agent-orchestrator-worker-liveness.md`, `agent-orchestrator-single-vm-architecture.md`). No dispatch/reap
      behavior changed (reaping keys on dispatch context, never this field) — agent-orchestrator@4421129, QG green (3092
      passed, 2 skipped).
- [x] ✅ [INFRA] P3. **Bump `agent-orchestrator/dashboard/package.json`'s `"prettier": "^3.6.2"` → `"^3.9.5"`,
      `npm install`, confirm `format:check` clean.** — agent-orchestrator@fcbc736, npm install clean, format:check green
      (262 tests passed). The version-choice question is already empirically resolved (byte-identical output + zero
      idempotency drift proven on every dashboard TS/CSS file type — the proseWrap defect this decision worried about is
      a markdown-only Prettier option, confirmed inert on `.tsx`/`.css`); this is now a mechanical version bump, no
      remaining judgment. **Done when**: `agent-orchestrator/dashboard`'s `format`/`format:check` scripts agree with
      `scripts/hooks/prettier-autostage.sh`'s 3.9.5 pin on the same file set. Source:
      `/plans/active/issues/dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md:81` (its 2nd `[INFRA] P3`
      item). Repo: agent-orchestrator.

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/pre-task-plan-conflict-check.md`,
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (todo 3).

## Progress Log

- **2026-08-09** — Authored by a satellite-batch-extraction pass over the 21 `ao`-tranche `assigned_vm: NA` docs named
  in the parent RECLASSIFY sweep's candidate list. Per-item conflict-check before drafting: (1)/(2) — grepped
  `plans/active/` for `wip-preserve/cascade-strategy-service` and `na-eligibility-auditor.timer`; only self-references
  in the source batch2 doc and unrelated archival-target mentions in batch7 (a DIFFERENT doc's archival, not this
  timer-check claim) — clear. (3) — no other active plan claims the "sweep + archive resolved-but-unarchived `ao` docs"
  ground. (4)/(5) — grepped for "plan_reconciler end-to-end"/"role lifecycle reclassification"/"lifecycle: persistent"
  across `plans/active/`; only self-references in the source doc — clear. (6) — grepped
  `dashboard_prettier_version_skew_vs_wrapper_pin` across batch7/8/9: batch8 Phase 3 explicitly assessed this doc "fully
  deferred, both items pure judgment calls" — but that assessment predates the 2026-08-08 round5 operator session that
  empirically resolved the version-choice question and split the prose follow-up into a real tracked todo (confirmed via
  the source doc's own Progress Log dating); batch8's snapshot is stale relative to the doc's current state, not a live
  conflicting claim — clear to extract. Held back from this batch (left in their source docs, not extracted): batch2's
  `[INFRA] P3` token re-mint (credential/host-specific, already ruled "correctly operator-only" by the doc family that
  originated it); `ao_open_issues`'s `tmux_session_lost` root-cause hunt (open-ended investigation, prior reaper-fix
  hypothesis already falsified, no bounded done-when beyond "find the driver or don't"); `ao_open_issues`'s
  `ao_docs_reconciliation` close-out item (its target doc,
  `/plans/archive/2026_08/ao_docs_reconciliation_2026_07_15.md`, is independently confirmed `status: resolved` and
  already archived — this todo is a stale checkbox, not real remaining work, left for a future stale-checkbox correction
  pass rather than force-extracted here); `ao_open_issues`'s Recovery-audit Layer-1 producer rewire
  (`ao_recovery_audit_layer1_deleted_2026_07_15.md`'s own sole open todo — genuine safety-domain design work, "decides a
  SignoffVerdict" has no specified decision logic, stays behind); `dashboard_prettier`'s "decide whether the dashboard
  should gate on formatting at all" (explicit undecided policy call, sequenced behind the extracted bump anyway).
- **2026-08-09** (slot 19) — Todo 3 (the `ao`-tagged archive sweep) done: 0 genuine orphans found in
  `plans/active/issues/` — see the todo's own evidence line for the 4 near-misses (gate/exempt/lock, each already
  correctly held back) and both mechanical gates' 0-candidate confirmation. `regenerate_active_plan_inventory.py` re-run
  clean (0 orphans, 297 plans). No `[unlock-plan]` requested for the one locked-but-resolved doc found
  (`ao_park_disposition_blocked_answer_no_follow_through_2026_07_31.md`) — its lock is the standing corpus-wide
  `locked_by: live-defi-rollout` convention shared with 62 other active docs, not an anomaly worth an operator ping.
- **2026-08-10** (slot 23) — Todo 4 (`plan_reconciler` end-to-end + R1/R2) done: (a) 20 completed reconcile runs found
  since 2026-08-06, each with a matching pushed `plan_reconciler/<dispatch_id>` branch — cited `agt-a398c9`; (b) R1
  pinned to `WorkerLivenessWatchdog._reclaim_exited_slot()`, gated on `has_session()==False` (a consequence of death,
  never the cause) — the OLD `_reclaim_idle_lingering_sessions` path the doc pointed at is now structurally incapable of
  touching a live typed agent's slot per the code's own 2026-07-21 `ao_uniform_agent_liveness_contract` comment; (c) R2
  confirmed LIVE during the investigation — `orch-slot-19`'s reconciler agent sat 3134s heartbeat-silent (>3.4× the
  ordinary 900s kill threshold) yet stayed `working`, protected by the terminal-lifecycle 3600s exemption budget. Full
  evidence + line/file citations in the todo itself. Also surfaced (NOT part of this gate, filed separately): 2 of
  today's 4 reconciler tranches died via an unrelated `tmux_pruner`/`has_session()==False` path with an undetermined
  root cause — `/plans/active/issues/plan_reconciler_unexplained_tmux_session_loss_2026_08_10.md`.
