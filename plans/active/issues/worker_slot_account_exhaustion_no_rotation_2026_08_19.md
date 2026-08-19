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
status: open
resolved_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, autospawn, account-failover, fleet-capacity]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/multi_provider_model_capability_bakeoff_2026_08_19.md,
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
`AccountProvider` (`server/accounts.py:115-128`) already registers 12 providers (anthropic,
deepseek, openrouter, gemini, groq, sambanova, omniroute, glm, codex, kimi, nvidia, grok) — the
registry breadth is there, the per-provider usability logic isn't.

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
`/plans/active/multi_provider_model_capability_bakeoff_2026_08_19.md` (slot-1, active) runs 6
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

- [ ] [BACKEND] P2. **Widen `account_is_usable()` into provider-aware usability** — per-provider
      functions (Claude: `weekly_pct`/`five_hour_pct`/`overage_status`; Gemini:
      reuse/generalize the existing separate `gemini_account_has_rate_headroom` RPM/RPD gate; stub
      for DeepSeek/Gemma/Codex-Luna as those accounts come online), dispatched by `AccountProvider`.
      Needs an operator decision on the per-provider thresholds (matching whatever
      `pick_next_account(require_headroom=True)` already uses per provider, or deliberately
      different ones for the kill-vs-avoid distinction). **Second consumer found 2026-08-19** (via
      `multi_provider_context_billing_reconciliation_2026_08_16.md`): `dashboard/src/layout.tsx:549`
      has its own `accountIsUsable()` (camelCase) that "mirrors AutoSpawn's own dispatch-eligibility
      definition verbatim" per its own docstring — update it in the SAME change or the dashboard
      silently drifts from the backend's new provider-aware logic. Repo: agent-orchestrator.
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
- [ ] [BACKEND] P2. **Build the equivalence-class registry** (replacing the accidental
      `short_tier()` unknown→sonnet fallback) + add `model_strict: true|false` to
      `role_registry.py` `RoleSpec` / `agents/<role>.md` frontmatter. **Existing string-based
      model-tier parsers to extend/mirror, found 2026-08-19**: `_parse_frontmatter_model_tier`
      (`regen_backlog_from_plan.py:916-951`, plan frontmatter → tier) and `_coerce_model`
      (`role_registry.py:108-116`, role frontmatter — already accepts both `opus`/`opus-required`
      strings, a useful template for how `model_strict` should parse). Repo: agent-orchestrator.
- [ ] [BACKEND] P3. **Add `model_strict:` to plan/task frontmatter** alongside the existing
      commented-out `model_tier:` stub in `task_template.md`, and fix the `PLAN_FORMAT.md` /
      `task_template.md` doc-drift found above (missing `model_tier:` row, `assigned_role` spelling
      mismatch) in the same edit, after confirming actual parser behavior in
      `regen_backlog_from_plan.py`. Repo: unified-trading-pm.
- [ ] [BACKEND] P3. **Build a scheduled-job model/tier/strict config surface** — none exists today;
      replaces the hardcoded mode-tuple in `plan_health.py:688-710`. Repo: agent-orchestrator.
- [ ] [BACKEND] P3. **Build a per-`wall_type` escalation model/tier/strict config surface** — none
      exists today; all wall types currently share one flat default model. Repo: agent-orchestrator.
- [ ] [BACKEND] P2. **Unify the 3 dispatch moments** (fresh dispatch, resume-after-kill, and live
      mid-session cap-hit in `WorkerLivenessWatchdog._handle_usage_cap`) to consult
      `model_strict` + the equivalence-class registry consistently — today only fresh/resume get
      DeepSeek substitution; mid-session always freezes regardless of tier. Repo: agent-orchestrator.
- [ ] [DATA] P3. **Once `multi_provider_model_capability_bakeoff_2026_08_19.md`'s synthesis todo
      lands** (its per-(model, complexity-tier) summary table), replace this doc's flat
      "all-but-haiku" equivalence-class placeholder with the real tiering data it produces — update
      the equivalence-class registry built above, not a fresh benchmark. Repo: agent-orchestrator.
- [x] [OPERATOR] P3. **Future eval-benchmark plan — found 2026-08-19, already exists and is
      active**: `/plans/active/multi_provider_model_capability_bakeoff_2026_08_19.md` (slot-1).
      Superseded this todo's original "not yet scoped" framing — see the todo directly above for
      the concrete follow-through once it completes.

## Resumption notes (2026-08-19)

This doc is the sole, self-contained tracking surface for this initiative — no sibling plan exists
or is planned (see Process note above). The `related:` plans (bake-off, billing-reconciliation,
`ao_consolidated_closeout`) are independent parallel efforts merely cross-referenced here, not a
dependency chain to walk.

**Recommended implementation order** (dependency-derived, stated in chat but not yet answered by
the operator when this session ended — default to this order if still unanswered on resume):
1. Todo 1 (widen `account_is_usable()` + the `layout.tsx:549` dashboard mirror) — independent,
   no prerequisites.
2. Todo 2 (equivalence-class registry + `model_strict` on `role_registry.py`) — foundational;
   todos 3/4/5/6 all build on it.
3. Todos 3, 4, 5 (plan frontmatter / scheduled-job / escalation config surfaces) — can proceed in
   parallel once todo 2 lands; each touches different files.
4. Todo 6 (unify the 3 dispatch moments) — needs todo 2 done, benefits from todo 1 also being done.
5. Todo 7 (replace the flat placeholder with real bake-off data) — **cannot start yet**, blocked on
   `multi_provider_model_capability_bakeoff_2026_08_19.md`'s own synthesis todo landing (external,
   not owned by this doc) — check that plan's Progress Log before attempting.

**Lessons from this session, worth not re-learning**:
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
