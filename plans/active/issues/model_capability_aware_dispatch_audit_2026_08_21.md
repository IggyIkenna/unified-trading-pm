---
doc_type: issue
title: >-
  Dispatch is headroom-only, zero model-capability awareness — audit every agent-type's round-robin
  correctness + design capability-tier-aware routing using the (already-collected, never-synthesized)
  multi-provider bake-off data
summary: >-
  Operator asked (1) to re-verify whether CI-escalation dispatch is still single-account-concentrated
  (it was, per `ci_escalation_reserve_slots_claimed_by_class_a_dispatch_2026_08_21.md` todo 5, before
  today's bugs 1-5 round-robin fixes landed) and (2) to confirm every worker/agent type in the fleet
  round-robins correctly AND that dispatch takes model capability into account — weaker/cheaper models
  (e.g. `gemini-3-5-flash-lite`) should not be treated as fungible with stronger ones (Claude
  sub-accounts, `gemini-3-7-flash`, `glm-5.2`) for judgment-heavy work like CI-escalation resolution.
  Part 1 (re-verification) is DONE — the single-account claim no longer holds, self-corrected exactly
  as predicted once `ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md`'s bugs 1-5 shipped.
  Part 2 (round-robin-across-all-agent-types audit + capability-aware routing design) confirmed a real,
  previously-undocumented gap: NOTHING in today's dispatch logic (`select_account_for_spawn` and its
  whole family) considers model capability at all — every account within a provider-priority tier is
  treated as equally capable, gated purely on rate-limit headroom. Separately, this fleet already ran a
  real 6-model capability bake-off (`multi_provider_model_capability_bakeoff_2026_08_19.md`, all 6 runs
  complete) but never finished its own synthesis todo — the exact data this capability-tier design
  needs already exists, uncollated.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [ao, agent-orchestrator, dispatch, round-robin, multi-provider, model-capability, task-routing,
    escalation]
related:
  [
    /plans/active/issues/ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md,
    /codex/04-architecture/agent-orchestrator-autospawn.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/model_tier.py,
    agent-orchestrator/server/config.py,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/plan_health.py,
  ]
source: >-
  Operator, 2026-08-21, following up on ci_escalation_reserve_slots_claimed_by_class_a_dispatch_
  2026_08_21.md's own open todo: "verify if that claim still holds and if it does then fix it. and
  also make sure that all the worker and agent types are using the correct round robin mechanism and
  all accounts are being used across agent types as well according to their capabilities. some models
  are smarter than the other ones and we have to take that into account when dispatching tasks."
---

# Dispatch is headroom-only, zero model-capability awareness

## Part 1 — CI-escalation single-account claim: RE-VERIFIED, no longer holds

See `ci_escalation_reserve_slots_claimed_by_class_a_dispatch_2026_08_21.md` todo 5 (flipped `[x]`
2026-08-21) — full evidence lives there, not duplicated here. Summary: live `activity_log` since
`agent-orchestrator@ba855161ae` shipped shows `escalation_dispatch_initiated` spread across 6 distinct
accounts (Claude subs `sub-e-odum2default`/`sub-f-odum2default` + 4 Gemini flash-lite projects), zero
`codex-luna`. Self-corrected exactly as that doc's own todo predicted once the round-robin bugs landed.

## Part 2 — round-robin-across-agent-types audit + capability-aware dispatch design (IN PROGRESS)

Two parallel investigations dispatched 2026-08-21:

1. **Agent-type dispatch catalog**: every `select_account_for_spawn`/`select_account_with_non_strict_
   retry`/`_pick_headroom_account` call site (reportedly ~17 total, only 4 previously verified: AutoSpawn
   refill tick, resume pass, `rotate_all_slots_off_account` bulk sweep, `escalation.escalate()`) — for
   each: which agent/worker type it serves, single-pick vs. batch-loop, and whether a batch-loop
   correctly threads `exclude_ids`. Also checking for any SEPARATE, non-round-robin selection mechanism
   elsewhere (scheduled/plan_health dispatch, review-role dispatch, main-agent singleton, typed one-shot
   agents, `worker_liveness_watchdog._handle_usage_cap` failover).
2. **Bake-off synthesis**: `multi_provider_model_capability_bakeoff_2026_08_19.md` ran 6 real-task
   benchmarks (Gemini 3.5-flash-lite, Gemini 3.7-flash, GLM 5.2, GLM 5-Turbo, DiffusionGemma 26B/NVIDIA
   NIM, Codex/Luna) across easy/medium/hard task complexity, but never finished its own todo to
   synthesize a final per-(model, complexity-tier) table + routing recommendation. That's the exact
   input a capability-tier dispatch design needs, and it already exists uncollated — completing it here
   rather than re-running a fresh bake-off.

**Preliminary finding, confirmed by direct code read before dispatching either investigation**:
`server/model_tier.py` is exclusively about ANTHROPIC/Claude model variants (sonnet-light/sonnet-
default/opus/fable) — `model_rank()` only ranks those 4. There is no cross-provider capability concept
anywhere in the codebase today. `accounts.json`'s per-account `variant` field (e.g. `3.5-flash-lite` vs
`3.7-flash`, `flash` vs `pro`, `5.2` vs `5-turbo`) already encodes real capability differences by name
but is read only for headroom/pricing/health — never for a "is this account strong enough for this task"
decision. Every account within a provider-priority tier is dispatch-fungible today, gated purely on
rate-limit headroom.

### Bake-off synthesis result (DONE 2026-08-21) — the missing capability-tier input

Read all 676 lines of `multi_provider_model_capability_bakeoff_2026_08_19.md`, tracking each model's
FINAL state through every re-run/backfill (several early "zero usable data" verdicts in that doc are
superseded later by a paid-tier retry — a naive first-mention read would get several models wrong).

| Model | Usable signal | Verdict |
|---|---|---|
| Gemini 3.5-flash-lite | 4 clean PASS + 2 interrupted-with-real-work, across ALL 3 tiers incl. one clean 75-turn/60.5-min Hard PASS — the only model with any verified Hard-tier signal at all | **STRONG-VERIFIED** |
| GLM 5-Turbo | 2 clean Easy PASS + 1 Medium interrupted-with-real-work (81 turns); zero Hard attempts | **WEAK-BUT-VERIFIED** (Easy solid, no Medium/Hard track record) |
| GLM 5.2 | 1 clean Easy PASS + 1 Easy interrupted (90 turns real depth); zero Medium/Hard attempts | **WEAK-BUT-VERIFIED** (Easy only) |
| Gemini 3.7-flash | 0/12 usable (6 free + 6 paid-retry, both runs 100% blocked) | **UNVERIFIED-INFRA-BLOCKED** — diagnosed cause: per-model RPM bucket too low + a free-tier billing-classification bug that survived the paid-tier upgrade; fixable (regenerate the API key), not yet applied |
| DiffusionGemma 26B (NVIDIA NIM) | 0/6 usable, confirmed twice not a one-off | **UNVERIFIED-INFRA-BLOCKED** — vendor-side (NVIDIA) endpoint instability under real request load, 4 distinct failure signatures, ruled out as our payload/proxy via direct curl. **Superseded in production regardless**: this NVIDIA-hosted variant was replaced entirely by `gemma-self-hosted` (Ollama) per `kimi_gemma_provider_onboarding_2026_08_16.md`'s closing note — this bake-off has ZERO data for the account actually running in prod today. |
| Codex/Luna | 0/6 usable | **UNVERIFIED-INFRA-BLOCKED** — deterministic bridge bug (rejects any `system`-role message, HTTP 400) in `codex_luna_flex_bridge_2026_08_14.md`, not yet fixed; not a single token of real model output was ever produced, so this is genuinely zero capability signal, not weak signal |

**Routing recommendation** (full reasoning + per-model justification in the bake-off doc itself, to be
copied there as its own closing synthesis per that plan's own open todo — not duplicated in full here):

- **Hard/judgment-heavy (CI-escalation, security audits)**: no model earns unconditional trust yet.
  Gemini 3.5-flash-lite's single clean Hard PASS justifies PREFERRING it over the alternatives once its
  quota/billing fix lands, with continued monitoring — not a hard guarantee (n=1 clean Hard result).
  Everything else has zero Hard-tier signal and should not receive Hard dispatch at all.
- **Easy/mechanical (routine doc updates)**: Gemini 3.5-flash-lite, GLM 5.2, GLM 5-Turbo are reasonable,
  contingent on two real infra fixes neither of which exists yet: (a) GLM needs a headroom/quota poller
  — its 5-hour usage window is ACCOUNT-level, shared across `glm-5-2`/`glm-5-turbo`, and was invisible to
  AO throughout the whole bake-off, meaning live GLM dispatch likely has the same blind spot today; (b)
  Gemini needs request pacing/serialization plus the API-key billing-classification fix — even Easy-tier
  reliability wasn't fully solved on the paid tier in this trial.
- **No reliable data — exclude from dispatch entirely, not just deprioritize**: Gemini 3.7-flash,
  DiffusionGemma 26B (superseded by `gemma-self-hosted` regardless), Codex/Luna. Each has a specific,
  already-diagnosed infra bug blocking every single attempt regardless of task complexity — routing
  ANYTHING to them today has a near-100% observed failure rate for reasons unrelated to model capability.

## Todos

- [x] [DATA] P1. ✅ **DONE 2026-08-21.** Re-verify CI-escalation single-account concentration claim —
      see Part 1. Repo: agent-orchestrator.
- [ ] [DATA] P1. Complete the agent-type dispatch catalog (investigation dispatched, pending). Produce
      a table of every call site, agent type served, batch-vs-single pick, exclude_ids correctness.
      Fix any newly-found unfixed batching gap the SAME way bugs 4a/5 were fixed (thread `exclude_ids`/
      `select_account_with_tick_spread`). Repo: agent-orchestrator.
- [x] [DATA] P1. ✅ **DONE 2026-08-21 — see Bake-off synthesis result above.** Completed
      `multi_provider_model_capability_bakeoff_2026_08_19.md`'s own open `[DATA] P2` todo (synthesis +
      routing recommendation). Its sibling `[REVIEW] P1` diff-vs-diff todo turned out to be
      unanswerable from the data: both intended comparison pairs (Gemini-vs-Codex/Luna on
      repo-touched-capture, GLM-vs-Codex/Luna on sequential-ordering) have zero real attempts on the
      Codex/Luna side — there is no second diff to compare against, which is itself the honest
      verdict. **Follow-on**: copy this synthesis + recommendation into the bake-off plan itself
      (its own todo asked for the table to live there) and flip both its remaining todos. Repo:
      unified-trading-pm.
- [ ] [BACKEND] P1. Design + implement a capability-tier classification (derived from the bake-off
      synthesis + `accounts.json`'s `provider`/`variant` fields) and wire it into `autospawn.py`'s
      selection pipeline: capability-sensitive callers (CI-escalation, review-role, any judgment-heavy
      dispatch) should PREFER higher-capability accounts, falling back to weaker ones only under real
      exhaustion of the stronger pool — never a hard block that could stall dispatch entirely. Routine
      Class-A backlog dispatch stays capability-agnostic (any headroom account, current behavior).
      Include regression tests mirroring the existing `select_account_for_spawn` test patterns. Repo:
      agent-orchestrator.
- [ ] [SCRIPT] P2. Once the fix ships, update `/codex/04-architecture/agent-orchestrator-autospawn.md`
      (the primary account-pick-rotation SSOT, already rewritten once today) with the new
      capability-tier layer. Repo: unified-trading-pm.
- [ ] [SCRIPT] P3. **Found while archiving the bake-off plan** (its own last 2 todos closed above, hit
      0 open todos, archived per the HARD RULE). 2 OTHER active docs still cite its pre-archival
      active-path form of `multi_provider_model_capability_bakeoff_2026_08_19.md` in their own
      `related:` frontmatter and will dangle: `worker_slot_account_exhaustion_no_rotation_2026_08_19.md`,
      `nvidia_codex_exhaustion_observability_gap_2026_08_19.md`. Same class as the earlier
      `kimi_gemma_provider_onboarding_2026_08_16` archival's dangling-referrer todo — not fixed here
      for the same reason (touching unfamiliar active docs unilaterally). Fix: REMOVE each dead
      `related:` entry (never repoint at the new `/plans/archive/2026_08/...` path —
      `check_active_refs_archived_plans.py` bans that too). Repo: unified-trading-pm.

## Progress Log

- **2026-08-21 (interactive session)**: filed following operator's direct request to re-verify
  Part 1 and audit/fix Part 2. Part 1 verified and closed same session. Part 2's two investigations
  dispatched in parallel (read-only, independent files/topics); this doc will be updated with their
  findings and the resulting implementation.
