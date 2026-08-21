---
doc_type: issue
title: >-
  Proactive worker-slot account failover (agent-orchestrator@78a9a02) never fires for weekly/5-hour
  ceiling exhaustion — account_is_usable() doesn't check it
summary: >-
  Operator observed multiple sports_taxonomy_p4_backfill-related slots still pinned to account
  sub-b-iggy2london, which the operator believes is exhausted, despite a recently-shipped
  "proactive worker-slot account failover" fix. Investigation confirmed the fix IS deployed and
  live, but its usability check (account_is_usable()) only looks at rate_limited_until / auth-failed
  cooldown / account_status=="disabled" — never weekly_pct, five_hour_pct, or overage_status. Live
  query on the VM found sub-b-iggy2london at account_status=healthy, rate_limited_until=NULL,
  weekly_pct=95, five_hour_pct=4, overage_status=rejected — genuinely near its weekly ceiling by the
  richer signal, but invisible to the failover mechanism's narrower check. Confirmed zero
  worker_account_unusable_killed activity_log rows have ever fired.
status: resolved # (was: open) 2026-08-21 — todo 7 (last open item) resolved via model_capability_aware_dispatch_audit_2026_08_21.md's capability_tier() mechanism; archived.
resolved_by: agent-orchestrator@36d56d8638
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, autospawn, account-failover, fleet-capacity]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/state_store/account_usage.py,
    agent-orchestrator/server/model_tier.py,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator, interactive session, 2026-08-19: dashboard screenshot showing several
  sports_taxonomy_p4_backfill tasks still associated with sub-b-iggy2london, asking why the
  recently-shipped proactive worker-slot account failover (agent-orchestrator@78a9a02) apparently
  didn't kick in. Investigated by a background agent this session (read-only, no code changes) —
  full findings below.
assigned_role: infra
drift_direction: none
---

# Proactive worker-slot account failover doesn't cover weekly/5-hour ceiling exhaustion

## What the shipped fix (`agent-orchestrator@78a9a02`) actually does

`AutoSpawnLoop._drain_worker_account_failover` (`server/autospawn.py`, called every AutoSpawn tick
from `_drain_escalations`) generalizes the main-agent's proactive failover to ordinary worker
slots. Each tick: queries `SlotRow` where `status IN ("working","blocked","idle")` and
`account_id IS NOT NULL`, excluding `review_slot_ids()`/`human_slot_ids()`. For each candidate,
calls `account_is_usable(session, account_id)`; if `False`, kills the tmux session (rate-limited
to one kill per cooldown per slot) and logs `worker_account_unusable_killed`. It deliberately does
nothing else — no resume, no requeue, no account re-pick; that's left to the existing
`tmux_pruner` (classifies the kill as an ordinary death) and `_resume_pass` (re-picks an account,
degrading through providers/models via `select_account_for_spawn`'s fallback chain).

Tests: `tests/test_autospawn.py:715-841`. No plan/issue doc exists for this specific 2026-08-19
change (only the 2026-06-17 archived plan for the *original* main-agent version) — this doc is the
first tracking artifact for it.

## Root cause: the usability signal doesn't cover this exhaustion mode

`account_is_usable()` (`server/state_store/account_usage.py:340-351`) checks only
`rate_limited_until`, an auth-failed cooldown, and `account_status == "disabled"`. It never
consults `weekly_pct`, `five_hour_pct`, or `overage_status` — those feed
`pick_next_account(require_headroom=True)` at NEW-dispatch time only, not this kill-check.

Live query on the VM's `account_usage` row for `sub-b-iggy2london`:
`account_status=healthy, rate_limited_until=NULL, weekly_pct=95, five_hour_pct=4,
overage_status=rejected`. Genuinely near its weekly ceiling by the richer signal — matching the
operator's belief — but `account_is_usable()` sees a perfectly healthy account and never triggers
a kill. Confirmed: zero `worker_account_unusable_killed` activity_log rows exist, ever, on this VM.

## Secondary factor observed

24 of 33 iggy2london-bound slots were already `status="paused"` (activity_log shows they were
paused 2026-08-18 ~07:14-07:24 UTC — ~21h *before* the failover fix even existed, via
`POST /api/slots/{id}/pause`). Paused slots are outside the failover candidate query's
`("working","blocked","idle")` filter regardless of account state, so they wouldn't be touched by
this mechanism even if the usability check were fixed.

## Initial ambiguity — resolved 2026-08-19 (see live re-check below)

At investigation time, no `SlotRow.current_task` matched `sports_taxonomy_p4_backfill`, and the
backlog API showed all 15 related tasks `status=queued, dispatched_to=None` — i.e. nothing was
actively running against `sub-b-iggy2london` at that instant. The operator's dashboard observation
may have reflected a different moment than this snapshot. **Resolved**: the live re-check in the
2026-08-19 follow-up below reproduced the same result a second time — see that section and its
corresponding `[x] [SCRIPT] P3` todo.

## 2026-08-19 follow-up: multi-provider scope + mid-session exhaustion (operator conversation)

Operator reviewed the above in an interactive follow-up and expanded scope:

**Paused-slot ruling (resolves a todo below)**: paused is deliberate — operators pause slots to
reduce AO's share of a scarce account pool and leave headroom for humans, unrelated to account
exhaustion. Confirmed correctly out of the failover candidate query's scope; not a bug.

**Live re-check (resolves a todo below)**: re-ran `check-ao-backlog-status.sh
sports_taxonomy_p4_backfill` fleet-wide. Same result as the original snapshot — all 15 matching
tasks still `status=queued, dispatched_to=None`. The operator's dashboard observation has now
failed to reproduce on two separate checks.

**Multi-provider `account_is_usable()`**: operator wants per-provider usability functions rather
than one widened check, since usage-window shapes differ (Claude: weekly + five-hour pct; Gemini:
per-minute/daily message limits; more providers — DeepSeek, Gemma, Codex/Luna — coming). Confirmed
this has precedent already: `account_usage.py` special-cases Claude-only wallet reconciliation
(excludes non-anthropic accounts, `compute_claude_wallet_reconciliation`) and Gemini already has
its own separate `gemini_account_has_rate_headroom` gate (`autospawn.py`) — `account_is_usable()`
itself just doesn't route the ceiling check through anything provider-specific yet.
`AccountProvider` (`server/accounts.py:115-128`) already registers 11 providers (anthropic,
deepseek, openrouter, gemini, groq, sambanova, omniroute, glm, codex, kimi, nvidia) — the
registry breadth is there, the per-provider usability logic isn't. (Was 12 including `grok`
until Grok was fully removed from the codebase 2026-08-20, operator ruling — see
grok_gemini_translation_proxy_2026_08_14.md.)

**Mid-session model/account exhaustion — traced against current code**: operator proposed
same-model-different-account → hot-swap in the same tmux; different-model-required → full respawn
(uniformly across main/review/fleet-worker/planning/escalation slots); and asked what happens when
even a different model is unavailable everywhere. Findings:
- No same-pane hot-swap exists today for *any* case — every account/provider swap already kills
  the tmux and spawns a fresh pane with `claude --resume <uuid>`, reloading the same conversation
  transcript (`tmux_spawn.py`, `_handle_usage_cap` in `worker_liveness_watchdog.py:2143-2203`).
  Transcript continuity already happens on every swap; there's no separate "hot" path to add for
  the same-model case specifically.
- `select_account_for_spawn` (`autospawn.py:1794-2089`) never downgrades model tier — it only
  searches other providers/accounts *for the task's already-chosen tier*. There is no
  "globally-unique-model" registry anywhere (zero hits for that framing in `model_tier.py`/
  `accounts.py`/`autospawn.py`) — a provider whose model is unique isn't currently a first-class
  concept.
- **Total exhaustion (the operator's core question)**: when the chosen tier has zero headroom on
  every account/provider, `select_account_for_spawn` returns `None` (`autospawn.py:2089` — "every
  pool genuinely exhausted — legitimate wait case"). Every call site treats that as retry-later,
  never a failure. For a slot mid-session, `WorkerLivenessWatchdog._handle_usage_cap` freezes it in
  place — leaves the tmux untouched, sets `"⏸ usage-capped — awaiting account headroom"`, pages
  once (deduped on recovery), and waits; AutoSpawn re-evaluates every tick (default 60s,
  `autospawn.py:2916-2917`) until headroom appears anywhere. **It does not fall back to a different
  model tier today** — there is no auto-downgrade path, so "switch to a different model when the
  original is exhausted everywhere" is new design work, not existing behavior. Tests:
  `tests/test_account_rotation.py:164` (`test_no_headroom_anywhere_does_not_spawn_or_kill`),
  `tests/test_account_failover_resume.py:225` (`test_worker_cap_no_headroom_leaves_frozen`).

## 2026-08-19 follow-up #2: strict-vs-substitutable model policy + equivalence-class placeholder

Operator requirement: a per-{role, plan/task, scheduled-job, escalation} `strict` flag. Strict =
never substitute (today's freeze-and-wait). Non-strict (**default**) = substitute to the "next
available" model, consistently across fresh dispatch, resume-after-kill dispatch, AND a live
mid-session cap-hit — all three should follow the same policy, not three different behaviors. This
resolves the "rule on total-exhaustion policy" todo below: it's not a blanket switch, it's
conditional on the new strict flag.

**Substitution is not hypothetical — it's already live, just hardcoded per-tier, not
configurable.** `config.py` `deepseek_route_fraction` (default 0.9) already routes 90% of
sonnet-tier fresh/resume dispatches to DeepSeek accounts via `select_account_for_spawn`; opus/fable
are hardcoded Claude-only forever, no override (`autospawn.py:1838-1846`). So today's system
already encodes "strict-for-opus/fable, non-strict-for-sonnet" as a blanket-per-tier rule — the
operator's ask generalizes this into a configurable per-role/task/job/escalation flag rather than a
hardcoded tier split. **The one dispatch moment with zero substitution today, for any tier**: a
live mid-session cap-hit — `WorkerLivenessWatchdog._handle_usage_cap` always freezes-and-waits
unconditionally ("Decision B"), never attempts the same DeepSeek-routing substitution fresh/resume
dispatch already gets. That asymmetry is the actual gap the operator's requirement closes.

**Landmine found, directly relevant to the operator's own gemini-flash-lite example**:
`short_tier()` (`model_tier.py:266-274`) substring-matches only `{fable,sonnet,haiku,opus}`; any
unrecognized model string silently falls through to a **default of "sonnet" rank** (line 274). So
today, if a weak/cheap model were ever wired in under a name the matcher doesn't recognize, it
would be silently ranked sonnet-equivalent by accident — the exact failure "strict" is meant to
prevent. The new equivalence-class registry must replace this accidental fallback, not just layer a
flag on top of it.

**Equivalence-class placeholder, per operator direction — resolved 2026-08-19**: single flat class =
every registered model minus haiku; haiku excluded from substitution in both directions, no
low-end-model carve-out beyond that (operator confirmed the flat "all-but-haiku" class as literally
stated, including gemini-flash-lite-class models as valid substitutes for non-strict roles for now).
A model with no equivalent anywhere doesn't need special-case "globally-unique" machinery
(superseding the todo below that assumed it would) — it's simply alone in its own equivalence class
once the registry exists. **Real eval-backed clustering already has a plan, found 2026-08-19**:
`/plans/archive/2026_08/multi_provider_model_capability_bakeoff_2026_08_19.md` (slot-1, active) runs 6
non-Anthropic models (2x Gemini, 2x GLM, Gemma, Codex/Luna — Claude tiers deferred to a later pass)
against 36 real backlog-task attempts, scored + profiled per (model, complexity-tier) — its
Progress Log's synthesized summary table is what should eventually replace this flat placeholder
with real tiering data, not a fresh benchmark effort. Track that replacement as its own todo below
once the bake-off's synthesis todo lands, rather than duplicating its scope here.

**Confirmed attachment points per surface** (file:line):
- **Role registry** (`role_registry.py` `RoleSpec`, backed by `unified-trading-pm/agents/<role>.md`)
  — already carries `model`+`sonnet_variant` per role. Natural minimal extension: add
  `model_strict: true|false` (default false) alongside them.
- **Plan/task frontmatter** — `task_template.md:120` already stubs `model_tier: opus-required` as a
  commented-out optional per-task override; add a parallel `model_strict:` override. **Doc-drift
  found in the same area — fix in the same edit**: `PLAN_FORMAT.md` has no `model_tier:` field row
  at all (task_template.md references it, PLAN_FORMAT.md doesn't), and `assigned_role` values are
  spelled inconsistently between the two docs (PLAN_FORMAT.md hyphenated e.g. `backend-engineer`,
  task_template.md underscored) — check what `regen_backlog_from_plan.py` actually parses before
  correcting either doc.
- **Scheduled jobs** — no config surface exists at all (`server/models/scheduled_jobs.py`,
  `server/state_store/scheduled_jobs.py` have no model/tier field; tier resolution today is either
  role-inherited or hardcoded-overridden via a tuple in `plan_health.py:688-710` for nine specific
  job modes). Needs building from scratch.
- **Escalations** — also nothing today: `escalate()`/`enqueue()` (`escalation.py:623-633`,
  `1538-1546`) both default every wall type to one flat `SONNET_DEFAULT_MODEL`; `WALL_TYPES` is
  validation-only, no tier map. Needs building from scratch.

**Process note (2026-08-19)**: this work stays tracked directly in this issue doc, not a separate
plan — operator decision after weighing it. Rationale: this doc is already `assigned_vm: NA` /
`execution_scope: local-only`, mechanically identical to a human plan, and the workspace's audit
tooling (`/na-eligibility-audit`, `/ag-closeout-audit`) already handles substantial issue docs
carrying real open work. Don't re-litigate "shouldn't this be a real plan?" without new information.

## Follow-up

- [x] [BACKEND] P2. **Widen `account_is_usable()` into provider-aware usability — shipped
      2026-08-19, agent-orchestrator@7aa42f67a3.** Implementation deliberately does NOT widen
      `account_is_usable()` itself — that function is correctly reused by 6+ OTHER call sites
      (`pick_next_account` default mode, `usable_account_count`, `all_accounts_unusable`, the
      all-down alert) that must keep treating a near-ceiling-but-not-rate-limited account as
      usable. Instead added a NEW `_account_meets_dispatch_headroom()` (autospawn.py) — usable AND
      under pct ceilings (Claude) AND under RPM/RPD (Gemini, reusing the existing
      `gemini_account_has_rate_headroom`) — and refactored `_pick_headroom_account` +
      `_drain_worker_account_failover` to both call it, so dispatch-time picking and the
      worker-kill check can never drift apart again. **Dashboard mirror verified NOT needed**:
      `layout.tsx:549`'s `accountIsUsable()` answers a deliberately coarser question (fleet-wide
      "is EVERY account unusable" alert) that must NOT trip on ceiling-proximity (would false-page
      "all accounts blocked CRIT" routinely) — confirmed this was already a looser mirror than its
      own docstring claimed, pre-existing, not something this change worsened. Tests:
      `tests/test_autospawn.py` (3 new), all passing under a clean QG run.
- [x] [OPERATOR] P3. **Paused slots correctly stay out of account-failover scope — resolved
      2026-08-19.** Paused is intentional (capacity reservation for humans when few accounts
      remain), not related to account exhaustion. No code change needed.
- [x] [SCRIPT] P3. **Re-checked live 2026-08-19** via `check-ao-backlog-status.sh
      sports_taxonomy_p4_backfill` — all 15 matching tasks still `status=queued,
      dispatched_to=None`. Operator's original observation does not reproduce (second check, same
      result).
- [x] [OPERATOR] P2. **Rule on total-exhaustion policy — resolved 2026-08-19** via the
      strict-vs-substitutable framework above: strict roles/tasks freeze-and-wait permanently
      (today's behavior, unchanged); non-strict (default) roles/tasks attempt substitution in all
      three dispatch moments, including mid-session. Superseded the two now-stale
      BLOCKED-OPERATOR todos that assumed a single blanket answer.
- [x] [OPERATOR] P2. **Resolve the flat-equivalence-class tension — resolved 2026-08-19.**
      Operator confirmed the flat "all-but-haiku" class as literally stated — a weak/cheap model
      (the gemini-flash-lite example) is an acceptable substitute for a non-strict role under this
      interim placeholder, no further exclusion list needed for now.
- [x] [BACKEND] P2. **Build the equivalence-class registry — shipped 2026-08-19,
      agent-orchestrator@1b1b9eb858.** `model_tier.equivalence_class()`/`models_are_substitutable()`
      — flat "standard" class minus a Haiku singleton, deliberately NOT routed through
      `short_tier()` (whose unknown→sonnet default is load-bearing for `is_deepseek()`'s
      context-window prior — reusing it here would have reproduced the exact landmine this todo
      exists to avoid). `RoleSpec.model_strict: bool = False` + `_coerce_model_strict()`
      (role_registry.py), parsed from `agents/<role>.md` frontmatter. `agents/main.md` set to
      `model_strict: true` — directly implementing the operator's own named example
      ("must not silently fall back to something as weak as gemini-flash-lite"); flag this specific
      content decision for review since it was made on the operator's behalf, not re-confirmed.
      Tests: `tests/test_model_tier.py` (3 new) + `tests/test_role_registry.py` (4 new).
- [x] [BACKEND] P3. **Add `model_strict:` to plan/task frontmatter + fix doc-drift — shipped
      2026-08-19, agent-orchestrator@c134a9c0d4 + unified-trading-pm@cc38229b57 (the doc half,
      previously blocked — see "New finding" below for how it cleared).** `_parse_frontmatter_model_strict()` +
      `_resolve_plan_model_strict()`/`_resolve_task_model_strict()` (regen_backlog_from_plan.py,
      factored into standalone functions specifically to keep `regen()`'s cyclomatic complexity
      under the ruff C901 cap — inlining tripped it, 27>26) + `BacklogTask.model_strict: bool`
      (backlog.py) — **shipped, agent-orchestrator@c134a9c0d4**. The doc-drift fix (`PLAN_FORMAT.md`
      `assigned_role:` line was wrong in 3 ways, not just hyphenation — `data-pipeline-engineer`/
      `infra-engineer` name no real `agents/*.md` role at all; verified live against every real
      `role:` field, corrected to `backend_engineer | data_engineering | ui_developer | infra |
      monitor | review`) + `model_tier:`/`model_strict:` rows added to both `PLAN_FORMAT.md` and
      `task_template.md` + `scripts/docs/docspec.py`'s `agent-role` FieldSpec (registered
      `model_strict` as `"scalar"` not `"enum"` — a real YAML `true`/`false` parses to a Python
      bool, which would HARD-fail a string-membership enum check) — **all 4 files shipped
      unified-trading-pm@cc38229b57**, after sitting blocked for a time by an unrelated
      repo-wide gate failure that has since cleared — see "New finding" below. Also improved
      `worker_liveness_watchdog._slot_is_model_strict()` (shipped as part of todo 6's commit,
      agent-orchestrator@7aa42f67a3) to read a task-dispatched slot's `task.model_strict` DIRECTLY
      rather than re-deriving from its role — the task already carries the fully-resolved
      plan-override-vs-role-default answer, so re-deriving from role alone would have silently
      MISSED a plan-level override. Tests: `tests/test_regen_backlog_from_plan.py` (6 new).
- [x] [BACKEND] P3. **Build a scheduled-job model/tier/strict config surface — shipped 2026-08-19,
      agent-orchestrator@204bc8e1fa.** `plan_health.dispatch(..., model_strict: bool = False)`,
      wired through the new shared `autospawn.select_account_with_non_strict_retry()` helper.
      **Caveat, stated plainly**: every one of the 9 `smart_tier` modes (reconcile/docs_reconcile/
      ag_closeout/.../ao_watchdog) is ALREADY forced to sonnet-tier — the widest pool the retry
      helper searches — so the new retry is a structural no-op for every mode that exists today; it
      only matters once a scheduled job is ever pinned to a stricter tier. Verified the retry
      mechanism itself DOES fire correctly using `mode="report"` + an explicit non-sonnet `model=`
      (the one mode that doesn't force smart_tier). Tests: `tests/test_plan_health.py` (2 new).
- [x] [BACKEND] P3. **Build a per-`wall_type` escalation model/tier/strict config surface —
      shipped 2026-08-19, agent-orchestrator@204bc8e1fa.** `escalate()`/`enqueue()` both gained
      `model_strict: bool = False`, per-call (hence per-wall_type, same shape `model` already has
      — no separate WALL_TYPE→default registry invented, matching scope). Threaded through the
      SAME shared retry helper as scheduled jobs, and into BOTH places a not-yet-dispatchable
      escalation gets queued (`enqueue()`'s own payload AND `escalate()`'s internal fallback
      payload — missed the second one on the first pass; the retry-loop's `**payload` unpacking
      into a fresh `escalate()` call would have silently dropped `model_strict` back to False on
      retry otherwise). Same "no wall_type is non-sonnet today" caveat as scheduled jobs. Tests:
      `tests/test_escalation.py` (2 new).
- [x] [BACKEND] P2. **Unify the 3 dispatch moments — shipped 2026-08-19,
      agent-orchestrator@7aa42f67a3, SCOPE-LIMITED — read this carefully.** `_handle_usage_cap`
      (mid-session cap-hit) fixed to search under the slot's OWN real tier first (was hardcoded
      `model=None` → an accidental always-sonnet-blend search regardless of the slot's actual tier
      — a genuine latent bug, dormant today only because no role is currently opus/fable-tier), then
      — for a non-strict, non-Haiku slot whose own tier is exhausted everywhere — ONE retry under
      the sonnet blended pool via the new `_slot_is_model_strict()` resolution (current_task's
      `model_strict` → persistent-role `agent_kind` → **defaults to strict/True on ANY resolution
      failure**, the deliberate safe direction). **What this does NOT do**: fresh dispatch and
      resume-after-kill's OWN total-exhaustion moments were NOT given the same cross-tier retry —
      they still just fail/requeue/retry-next-tick on their own tier's exhaustion today, exactly as
      before. The todo's title says "3 dispatch moments"; only 1 of the 3 actually gained new
      retry-on-exhaustion behavior in this pass — the other 2 (fresh/resume) already had the
      EXISTING sonnet-tier DeepSeek-blend (unconditional, not model_strict-gated) for whichever
      tier they're already dispatching at, which is a DIFFERENT mechanism than what this todo adds.
      If full 3-way parity is wanted, that's real remaining work, not yet scoped. Tests:
      `tests/test_account_failover_resume.py` (10 new/changed).
- [x] [BACKEND] P3. **Close the todo-6 scope gap — shipped 2026-08-19, agent-orchestrator@539a88d400.**
      Gave fresh dispatch (AutoSpawn's routine refill) and resume-after-kill (`_resume_pass`) the
      SAME non-strict cross-tier retry `_handle_usage_cap` already had, via
      `autospawn.select_account_with_non_strict_retry` (extended with `preferred_provider`/
      `sequential_preferred_account_id`/`forced_provider`/`task` passthrough so all 3 call sites
      could share it). Also fixed a latent bug found while wiring this: a substituted account's
      headroom was only ever confirmed under the sonnet-tier search, but the spawn still requested
      the original (opus/fable) model string — now spawns at the tier actually confirmed. Tests:
      `tests/test_autospawn.py` (2 new + 10 fixed for the `_spawn_param_plan` tuple-arity change),
      `tests/test_account_failover_resume.py` (2 new). Repo: agent-orchestrator.
- [x] [DATA] P3. ✅ **DONE 2026-08-21 — answered by a narrower mechanism than this todo envisioned.**
      The bake-off's synthesis landed (`model_capability_aware_dispatch_audit_2026_08_21.md` Part 2),
      but its real tiering data was deliberately NOT folded into `model_tier.equivalence_class()`/
      `models_are_substitutable()` itself — that stays the flat "all-but-haiku" placeholder, since
      widening it would alter `model_strict` substitution behavior for EVERY caller uniformly (fresh
      dispatch, resume, scheduled jobs, escalation), a bigger blast radius than the bake-off's signal
      strength (one clean Hard-tier PASS, thin Easy/Medium coverage on 2 more models) justifies today.
      Instead, a new `model_tier.capability_tier()` (STRONG/WEAK-VERIFIED/UNVERIFIED, sourced from the
      bake-off table) is wired as a dispatch PREFERENCE — not a substitution-eligibility change — into
      the two judgment-heavy callers this fleet has: `escalation.escalate()` and
      `autospawn.ensure_review_agents()`. Fresh/resume/scheduled-job substitution stays
      capability-agnostic by design (matches this doc's own todo 6 finding: routine work doesn't need
      the bias). Full mechanism + a new follow-up (codex-luna's UNVERIFIED tier pre-dates its
      2026-08-20 streaming-bug fix, may now be stale) tracked in
      `model_capability_aware_dispatch_audit_2026_08_21.md` Part 4 and its Todos, not duplicated here.
      Evidence: agent-orchestrator@36d56d8638. Repo: agent-orchestrator.
- [x] [OPERATOR] P3. **Future eval-benchmark plan — found 2026-08-19, already exists and is
      active**: `/plans/archive/2026_08/multi_provider_model_capability_bakeoff_2026_08_19.md` (slot-1).
      Superseded this todo's original "not yet scoped" framing — see the todo directly above for
      the concrete follow-through once it completes.

## New finding 2026-08-19: unified-trading-pm quickmerge blocked repo-wide (tracked separately, now cleared for this doc)

While shipping todo 3's doc half, `quickmerge.sh`/`quality-gates.sh` repeatedly failed
`check_frontmatter_schema` against an UNRELATED auto-filed doc
(`plans/active/issues/manifest_hygiene_red_all_2026_08_19.md`, from `manifest_hygiene_daily.py`)
whose frontmatter was observed in 3 different, progressively-more-broken states across ~10
minutes without this session touching it — already on origin, so it blocked EVERY quickmerge in
this repo, not just this one. Full write-up, evidence, and its own follow-up todos (still open,
independent of this doc): `/plans/archive/issues/manifest_hygiene_daily_malformed_frontmatter_blocks_quickmerge_2026_08_19.md`.
**Consequence for THIS issue, resolved**: the blocking file's frontmatter had stabilized enough by
the next session to pass `check_frontmatter_schema` standalone; todo 3's `unified-trading-pm` half
shipped cleanly at `cc38229b57` on the first retry. The generator issue itself is unrelated to this
doc and remains tracked only in its own issue doc above — no action needed here.

## Resumption notes (2026-08-19, updated after implementation)

> **✅ CLOSED 2026-08-21** — todo 7 (the last open item) resolved; doc archived. Kept as accurate
> historical record of the implementation journey; the "what to do on resume" list below no longer
> applies.

This doc is the sole, self-contained tracking surface for this initiative — no sibling plan exists
or is planned (see Process note above). The `related:` plans (bake-off, billing-reconciliation,
`ao_consolidated_closeout`) are independent parallel efforts merely cross-referenced here, not a
dependency chain to walk.

**Implementation status**: todos 1, 2, 3, 4, 5, 6 are shipped and live (agent-orchestrator:
`1b1b9eb858`, `7aa42f67a3`, `c134a9c0d4`, `204bc8e1fa`; unified-trading-pm: `cc38229b57` for todo
3's doc half — see each todo above for which commit and its exact scope/caveats). The todo-6 SCOPE
GAP (fresh dispatch + resume-after-kill not getting the same cross-tier retry `_handle_usage_cap`
has) is its own separate `- [ ]` todo below — code written this session (agent-orchestrator,
uncommitted pending QG), see that todo for status. Todo 7 remains externally blocked, unchanged.

**What to do on resume, in order**:
1. If the todo-6 scope-gap todo below is still `- [ ]` with no commit sha cited, the implementation
   was written but not yet verified/shipped — check `git status` in `.tabs/3/agent-orchestrator` for
   uncommitted changes to `server/autospawn.py`/`server/worker_liveness_watchdog.py` and their
   tests; run `bash scripts/quality-gates.sh` and ship via quickmerge if clean.
2. Todo 7 stays blocked until `multi_provider_model_capability_bakeoff_2026_08_19.md`'s synthesis
   todo lands — check that plan's Progress Log before attempting.
3. Once the todo-6 scope gap ships and the doc has no other open `- [ ]` items besides todo 7, this
   issue is effectively done pending only the external bake-off dependency — reconsider whether it
   should stay `status: open` or move toward archival at that point.

**Lessons from this session, worth not re-learning**:
- **A shared multi-agent checkout's `bash scripts/quality-gates.sh` sees EVERY file currently on
  disk, including a peer's or a cron job's uncommitted/actively-regenerating output — not just
  yours.** Hit this twice: (1) a stale `.venv` in THIS repo and in a completely different sibling
  repo (`strategy-service`) both surfaced as test failures that had nothing to do with the code
  being changed — fixed via a plain `uv sync --frozen`, not a code change; (2) a daily-audit output
  doc with malformed, apparently-actively-changing frontmatter blocked the whole repo's quickmerge.
  Diagnose WHOSE problem a failure is (git blame the file / check if it's YOUR diff) before assuming
  your own change caused it — a full-tree gate failing on a file you never touched is a real,
  recurring failure mode here, not a fluke.
- **`bash quickmerge.sh ... | tail -N` silently discards the real exit code** — a shell pipeline's
  exit status is the LAST command's (`tail`'s, always 0) unless you capture `$?` right after the
  first command or avoid the pipe. Redirect to a file and check `$?` explicitly instead, or you'll
  read a stale/wrong "exit code 0" off a run that actually failed.
- **Adding branches to an already-large function can trip ruff's C901 complexity cap even when each
  branch is individually simple** — `regen_backlog_from_plan.py:regen()` went 26→27 from what looked
  like a small, safe addition. Fix: extract the new logic into its own small function (mirrors the
  file's own existing `_role_tier`/`_resolve_task_tier` pattern) rather than inlining — cheaper than
  it looks, and matches the codebase's own established way of keeping that function's complexity down.
- **A `with patch.multiple(...): ...` assertion on a mock's `.call_count` must live INSIDE the `with`
  block** — the patch is torn down (real function restored) the moment the block exits, so an
  assertion placed after it silently checks the REAL function, not the mock (`AttributeError:
  'function' object has no attribute 'call_count'`, not a subtler wrong-value failure — easy to
  catch, easy to introduce by habit when copying a pattern from code where the assertions happened
  to already be inside).
- `select_account_for_spawn` never downgrades model TIER — it only swaps provider/account within
  the SAME nominal tier (`autospawn.py:1794-2089`). The "strict vs substitutable" design this doc
  builds is entirely new; don't assume any tier-fallback path already exists to extend.
- Searching the plan corpus by guessed keywords for "the model-capability benchmark plan" (tried
  `benchmark`/`eval`/`capability`/`comparison`/`parity`) returned nothing useful — corpus-wide
  `benchmark` hits are mostly unrelated performance-benchmark docs. What worked: `git log
  --oneline --name-only -- plans/` filtered for a topic keyword, which surfaced the real commit
  even though its own message ("model-existence sweep") didn't literally match either. When an
  operator says "there's already a plan for X" and a keyword grep comes up empty or ambiguous,
  ask for the slug directly rather than burning more search cycles guessing — a same-window,
  same-provider-effort sibling plan (billing-reconciliation) was an easy false-positive lead here.
- `select_account_for_spawn` never downgrades model TIER — it only swaps provider/account within
  the SAME nominal tier (`autospawn.py:1794-2089`). The "strict vs substitutable" design this doc
  builds is entirely new; don't assume any tier-fallback path already exists to extend.
- Searching the plan corpus by guessed keywords for "the model-capability benchmark plan" (tried
  `benchmark`/`eval`/`capability`/`comparison`/`parity`) returned nothing useful — corpus-wide
  `benchmark` hits are mostly unrelated performance-benchmark docs. What worked: `git log
  --oneline --name-only -- plans/` filtered for a topic keyword, which surfaced the real commit
  even though its own message ("model-existence sweep") didn't literally match either. When an
  operator says "there's already a plan for X" and a keyword grep comes up empty or ambiguous,
  ask for the slug directly rather than burning more search cycles guessing — a same-window,
  same-provider-effort sibling plan (billing-reconciliation) was an easy false-positive lead here.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche batch 3/3)**: KEEP-NA, valid — sole open item (`[DATA] P3`, replace
  the flat "all-but-haiku" equivalence-class placeholder with real tiering data) is explicitly `BLOCKED-ON:
  multi_provider_model_capability_bakeoff_2026_08_19` — that doc's own synthesis todo is confirmed still open
  (per this batch's own read of that doc). Genuinely blocked, not yet actionable.
- **interactive session (slot 13) 2026-08-21**: closed the sole remaining open item (todo 7) — see
  its resolution text above. This issue doc now has 0 open todos; archived per the workspace's
  archive-immediately HARD RULE. `related:`/referrer cleanup done in the same pass:
  `idle_lingering_session_reclaim_not_firing_2026_08_19.md` and
  `ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md` (both active, cited this doc's
  pre-archival path in their own `related:`) had that entry removed rather than repointed at the new
  archive path, per `check_active_refs_archived_plans.py`'s policy.
