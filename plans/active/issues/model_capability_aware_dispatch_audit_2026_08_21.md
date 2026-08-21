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

## Part 3 — agent-type dispatch catalog (DONE 2026-08-21)

Every `select_account_for_spawn`/`select_account_with_non_strict_retry`/`_pick_headroom_account` call
site audited. Confirmed: every real dispatch path — Class-A refill, resume, bulk account-rotation
sweep, CI escalation, scheduled-job (`plan_health`) dispatch, the singleton main agent, review-role,
and the usage-cap failover watchdog — routes through the SAME picker family; no separate/alternate
selection mechanism exists anywhere.

**One real, previously-unknown bug found**: `server/autospawn.py::ensure_review_agents()` (called from
`main_agent_keeper.py`'s `AgentKeeper` tick) is a `for slot_id in sorted(review_ids):` batch-loop —
the exact bug-4a/5 shape — calling `select_account_for_spawn` with **zero** `exclude_ids`. Dormant
today (`ORCHESTRATOR_REVIEW_SLOTS` defaults to 1 slot, so there's nothing to pile up onto), but real
the moment a second review slot is configured. Fixed (see Part 4).

**Confirmed definitively — no capability-awareness existed anywhere before this doc's fix (Part 4)**:
`model_tier.py::equivalence_class()`'s own docstring stated outright *"a gemini-flash-lite-class model
is just as acceptable a substitute as opus today... INTERIM PLACEHOLDER, not real capability data"*
and named this bake-off by path as the eventual fix. The Phase-4 stratified rotation reads task
difficulty only to pick a fairness cursor, never to bias account choice. `AccountDef.variant` was read
in exactly 3 places, none capability-related (a DeepSeek pro/flash A/B split ratio, Gemini's RPM/RPD
ceiling lookup, telemetry naming). The only pre-existing capability-ish gate was the coarse
opus/fable-tier hard-pin (Claude-only) — sonnet-tier work (the overwhelming majority of dispatch) had
zero capability signal.

## Part 4 — capability-tier dispatch implemented (SHIPPED 2026-08-21)

Implementation, reusing the ALREADY-BUILT `exclude_ids` mechanism from bugs 4a/5 rather than adding a
new sort-preference parameter threaded through `_pick_headroom_account`'s ~9 internal call sites (a
much larger, riskier diff for the same-day-shippable, easily-reversible shape a preference-not-filter
change should take):

- `model_tier.py`: new `capability_tier(provider, variant) -> int` (3 tiers: `CAPABILITY_TIER_STRONG`
  = Anthropic/DeepSeek [established, not bake-off targets] + `gemini`/`3.5-flash-lite` [bake-off
  STRONG-VERIFIED]; `WEAK_VERIFIED` = `glm`; `UNVERIFIED` = everything else). `equivalence_class()`
  deliberately left untouched — it governs cross-model SUBSTITUTION eligibility, a different, blunter
  question than this ROUTING PREFERENCE; touching it would change `model_strict` retry behavior for
  every caller uniformly, a bigger blast radius than warranted today. Docstring updated to explain why.
- `autospawn.py`: new `low_capability_account_ids(session) -> frozenset[str]` — classifies the live
  `accounts.json` roster, returns everything below `CAPABILITY_TIER_STRONG`.
- `autospawn.py::ensure_review_agents()`: fixed the Part 3 batch-loop bug (threads `review_picked`
  across the loop, mirroring `_run_one_tick`/`_resume_pass`) AND applies capability preference (review
  is judgment-heavy) — 2-pass select (capability+round-robin exclusion, then round-robin-only relaxed
  retry), true exhaustion falls through to the existing "no account, retry next tick" handling.
- `escalation.py::escalate()`: 2-pass capability-preferred select wrapping
  `select_account_with_non_strict_retry` (capability exclusion first, full-pool fallback second) — a
  CI-escalation is a judgment call. `model_strict=True` correctly skips the fallback retry too (exactly
  one search attempt total, matching that flag's existing "never retry" contract — caught by a
  pre-existing regression test that failed on the first implementation attempt, fixed same session).
- Class-A backlog dispatch (`_run_one_tick`/`_resume_pass`) deliberately UNCHANGED — stays
  capability-agnostic, matching the audit's own recommendation (routine work doesn't need bias away
  from fair headroom-based spreading).
- Tests: 4 new `model_tier` tests (tier classification per provider/variant), 4 new `autospawn` tests
  (classification helper + review-agent capability-preference/fallback/multi-slot-spreading), 3 new
  `escalation` tests (preference/fallback/strict-skip).
- Evidence: `quality-gates.sh` green — ruff clean, basedpyright 0 errors, 5295 passed/4 skipped/0
  failed, coverage 86.07% (above the 85.86% ratchet baseline). Shipped
  `agent-orchestrator@36d56d8638`. One coverage-ratchet run (of 3 total across this shipping session)
  transiently failed by 0.66 points; re-run TWICE more against the IDENTICAL tree both came back
  clean (86.07%/86.07%, both above baseline) — cross-checked against a before/after per-line coverage
  diff on all 3 touched files showing ZERO newly-uncovered lines from this change (missed-line counts
  identical before/after, only line numbers shifted by the insertion offset) — confirmed pre-existing
  test-run flakiness in this suite, not a real regression from this change.

**Deliberately NOT done in this pass** (scoped out, tracked below): a hard hierarchy encoding EXACTLY
which task types require which tier beyond escalation/review (e.g. per-`wall_type` granularity) — the
bake-off data doesn't yet support that fine a cut; today's 2 capability-sensitive callers (escalation,
review) cover the operator's explicit ask (CI-escalation dispatch) plus the other clearly judgment-
heavy caller found during the audit.

## Todos

- [x] [DATA] P1. ✅ **DONE 2026-08-21.** Re-verify CI-escalation single-account concentration claim —
      see Part 1. Repo: agent-orchestrator.
- [x] [DATA] P1. ✅ **DONE 2026-08-21 — see Part 3.** Agent-type dispatch catalog complete: every call
      site audited, one real batching bug found (`ensure_review_agents`) and fixed (Part 4), no
      separate/alternate selection mechanism exists. Repo: agent-orchestrator.
- [x] [DATA] P1. ✅ **DONE 2026-08-21 — see Bake-off synthesis result above.** Completed
      `multi_provider_model_capability_bakeoff_2026_08_19.md`'s own open `[DATA] P2` todo (synthesis +
      routing recommendation). Its sibling `[REVIEW] P1` diff-vs-diff todo turned out to be
      unanswerable from the data: both intended comparison pairs (Gemini-vs-Codex/Luna on
      repo-touched-capture, GLM-vs-Codex/Luna on sequential-ordering) have zero real attempts on the
      Codex/Luna side — there is no second diff to compare against, which is itself the honest
      verdict. **Follow-on**: copy this synthesis + recommendation into the bake-off plan itself
      (its own todo asked for the table to live there) and flip both its remaining todos. Repo:
      unified-trading-pm.
- [x] [BACKEND] P1. ✅ **DONE 2026-08-21 — see Part 4.** Capability-tier classification implemented and
      wired into escalation + review-role dispatch as a PREFERENCE (graceful fallback, never a hard
      block). Class-A backlog dispatch deliberately left capability-agnostic. 11 new regression tests,
      full `quality-gates.sh` green. Repo: agent-orchestrator.
- [x] [SCRIPT] P2. ✅ **DONE 2026-08-21.** Added a new "Capability-tier dispatch preference" section to
      `/codex/04-architecture/agent-orchestrator-autospawn.md` (the primary account-pick-rotation SSOT)
      covering the mechanism, the 2 wired-in callers, the distinction from `equivalence_class`, and the
      `ensure_review_agents` bug fix. Frontmatter `related:`/`authoritative_for:`/`code_refs:` updated
      too. Repo: unified-trading-pm.
- [ ] [BACKEND] P2. **Found during this session's live-checkout-write incident (Progress Log).**
      Neither `SUB_AGENT_MANDATORY_RULES.md`'s guidance nor any tool enforces that a write actually
      lands under `.tabs/<N>/` — today it's self-verification discipline only, and this incident shows
      that's insufficient even for the main interactive session, not just a delegated sub-agent (the
      class the existing `SUB_AGENT_MANDATORY_RULES.md` fix from
      `ao_self_pull_wedged_by_kimi_removal_wip_2026_08_21.md` targets). Investigate a mechanical guard
      — e.g. a pre-commit/pre-write hook on the bare-root checkouts specifically that refuses a write
      when a `.tabs/<N>/` sibling exists for the same repo and the caller isn't `ao-self-pull.sh`
      itself, or a lighter periodic dirty-tree canary alert. Scope + design this as its own small
      investigation before implementing — not obviously worth a hard block given legitimate direct
      bare-root writes may exist (operator-driven, host-level ops). Repo: unified-trading-pm
      (guidance) and/or agent-orchestrator (a guard script, if one is built).
- [x] [SCRIPT] P3. ✅ **DONE 2026-08-21.** Removed the dangling `related:` entry from both docs
      (`worker_slot_account_exhaustion_no_rotation_2026_08_19.md`,
      `nvidia_codex_exhaustion_observability_gap_2026_08_19.md`). While fixing the first, found its
      OWN sole remaining open todo (todo 7) was `BLOCKED-ON` this doc's Part 2 synthesis, which had
      since landed — resolved it (see that doc's todo 7 for the full accounting) and, since that was
      its last open item, archived it per the archive-immediately HARD RULE. That archival's own
      referrer fixups (2 more active docs citing its pre-archival path) done in the same pass:
      `idle_lingering_session_reclaim_not_firing_2026_08_19.md`,
      `ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md`. **New follow-up found while
      resolving todo 7**: `capability_tier()`'s `codex` → UNVERIFIED classification is sourced from
      the bake-off's pre-fix 0/6 result (the codex-bridge streaming bug, fixed
      `agent-orchestrator@39604c9ced` 2026-08-20, postdates the bake-off run) — live post-fix
      production traffic shows codex-luna handling real dispatch at ~8.9% failure rate (488
      selections/41 failures/24h, `ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md`
      Part 1). Tracked as a new todo below rather than re-derived here. Repo: unified-trading-pm.
- [ ] [DATA] P3. **Found while closing the todo above.** Re-evaluate whether `codex` still belongs in
      `model_tier.CAPABILITY_TIER_UNVERIFIED` now that the codex-bridge streaming bug
      (`agent-orchestrator@39604c9ced`, 2026-08-20) is fixed — the bake-off's 0/6 result that
      classification is sourced from predates the fix and reflects a broken bridge, not the model's
      real capability. Once enough POST-FIX production data accumulates, re-check via live
      `activity_log` selection/failure/death counts for `codex-luna` (the same method
      `ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md` Part 6 used), not the pre-fix
      bake-off numbers and not a fresh benchmark. If it holds up, promote it out of UNVERIFIED. Repo:
      agent-orchestrator.

## Progress Log

- **2026-08-21 (interactive session)**: filed following operator's direct request to re-verify
  Part 1 and audit/fix Part 2. Part 1 verified and closed same session. Part 2's two investigations
  dispatched in parallel (read-only, independent files/topics); this doc will be updated with their
  findings and the resulting implementation.
- **2026-08-21 (interactive session) — incident: accidentally edited the LIVE bare-root checkout
  instead of slot 13, wedged `ao-self-pull.sh` ~20+ min, recovered clean, no data lost.** While
  implementing Part 4, a sequence of `nohup`/backgrounded shell commands (chasing an unrelated
  `.venv`-missing problem, itself caused by the SAME underlying cwd confusion) left the session
  believing it was operating in `.tabs/13/agent-orchestrator` when several `Edit` calls actually
  landed in `/home/ubuntu/unified-trading-system-repos/agent-orchestrator` — the bare, LIVE checkout
  `orchestrator.service` runs from and `ao-self-pull.sh`'s 2-minute cron actively manages. Caught by:
  a QG run reporting a suspiciously clean baseline (no trace of the new code in its own log despite
  believing it had just been added), then `git status`/`grep` run with explicit `git -C <path>`
  (cwd-independent) on BOTH checkouts confirming the 6 modified files sat in the bare root, not slot
  13. Live evidence the wedge was real and already detected:
  `/tmp/ao-self-pull-dirty-wedge.alerted` (created 15:06 UTC) and `/tmp/ao-self-pull-dirty.ticks`
  (at 11 ticks by the time this was caught, ~15:20+ UTC) — the exact same failure shape as this
  session's earlier `ao_self_pull_wedged_by_kimi_removal_wip_2026_08_21.md` incident, root-caused
  there as "a delegating prompt named the wrong path"; this one shows the SAME root cause can hit the
  main interactive session too, not just a delegated sub-agent — the `SUB_AGENT_MANDATORY_RULES.md`
  fix from that incident doesn't cover this case.

  **Recovery** (no `git reset --hard`, no destructive command): `git -C <bare-root> diff >
  /tmp/.../recovery.patch` (475 lines, 6 files — captured the FULL uncommitted change safely) →
  `git apply --check` then `git apply` the SAME patch onto slot 13 (byte-identical application,
  verified via `grep -c capability_tier` before/after) → `git -C <bare-root> checkout --
  <the 6 files>` (safe: this was 100% my own accidental WIP, not foreign work, so reverting it is
  correcting my own mistake, not destroying someone else's) → confirmed bare root
  `git status` clean, `ahead=0/behind=0` against origin, ready for `ao-self-pull.sh`'s next tick to
  resume normally on its own (its dirty-wedge markers are the script's own bookkeeping — left alone
  to clear themselves rather than hand-edited).

  **New todo, found while diagnosing**: neither `SUB_AGENT_MANDATORY_RULES.md`'s existing "verify an
  absolute `.tabs/<N>/` path" guidance nor any existing tool wraps a HARD, mechanical check that a
  `git -C <target-path>` write is actually landing under `.tabs/<N>/` before an Edit/Write/Bash call —
  today it's discipline (self-verification via `pwd`), not enforcement, and this incident shows
  discipline alone isn't sufficient even for the main interactive session, not just delegated
  sub-agents. See Todos below.
