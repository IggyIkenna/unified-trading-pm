---
doc_type: issue
title: >-
  Codex-luna dispatch monopolization root-caused (3 stacked bugs, Claude capacity fully excluded
  from routing) — filed alongside this session's Kimi/OmniRoute/OpenRouter provider removal +
  slot-bootstrap/QG lessons
summary: >-
  Operator reported most AO tasks landing on `codex-luna` while Gemini/Claude sat idle with real
  capacity. Investigated live (not from docs) via the real account-selection functions run against
  the live DB, plus 24h `activity_log` selection-frequency data. Confirmed THREE independent, stacked
  bugs, in order of impact: (1) `account_is_usable()` treats `overage_status == "rejected"` as an
  unconditional kill switch with zero regard for actual usage — right now ALL 8 Claude accounts show
  this, including three at 0-8% weekly usage, which collapses `_anthropic_pool_headroom_pct` to `None`
  and forces `_quota_adaptive_fraction` to `1.0` (100% of dispatch forced off Claude, regardless of
  real headroom). (2) The Phase-4 stratified round-robin's eligibility pool
  (`_live_free_combo_ids`) never calls `_account_meets_dispatch_headroom` — so Gemini gets rotated in
  blind to its real RPM/RPD ceiling, its picks fail in practice (36%+ observed failure rate), and each
  failure self-excludes it from the next round via the in-memory failure ring. (3) `free_provider_priority`
  (the fallback order once DeepSeek is gated out) defaults to `["deepseek"]` with everything else
  falling through in plain alphabetical order — `codex` sorts before `gemini`/`glm`, so codex wins the
  waterfall almost unconditionally whenever DeepSeek is unavailable, which is most of the time right
  now (DeepSeek's wallet is at -$0.63, a real, separate, operator-actionable exhaustion). None of the
  three fixes are implemented yet — this doc tracks them. Filed alongside this same session's
  Kimi/OmniRoute/OpenRouter provider-removal work (shipped `agent-orchestrator@055bd037b7`) and the
  QG/slot-bootstrap process failures hit while shipping it, since the operator asked for one doc
  covering all three threads from this session.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, round-robin, account-failover, overage, multi-provider, kimi, omniroute, openrouter, quality-gates]
related:
  [
    /plans/active/issues/worker_slot_account_exhaustion_no_rotation_2026_08_19.md,
    /plans/active/issues/account_failover_ignores_overage_rejected_2026_08_18.md,
    /plans/active/issues/ao_self_pull_wedged_by_kimi_removal_wip_2026_08_21.md,
    /plans/active/issues/nvidia_codex_exhaustion_observability_gap_2026_08_19.md,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/kimi_gemma_provider_onboarding_2026_08_16.md,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/state_store/account_usage.py,
    agent-orchestrator/server/config.py,
    agent-orchestrator/server/accounts.py,
  ]
source: >-
  Operator, interactive session 2026-08-21 (slot 13): "look into the round robin not working
  properly in AO... find out the root cause", followed mid-session by "grok and kimi are not being
  used right now so please remove them... same for omniroute/openrouter if unused", and later "we did
  a lot more work than just kimi-removal here, so write a new doc about the work we did, issues we
  faced related to qg and the round-robin findings".
---

# Codex-luna dispatch monopolization — root cause, plus this session's cleanup + QG lessons

## Part 1 — round-robin / codex-luna skew: root cause (NOT YET FIXED)

### Live evidence (not inferred from docs)

`GET /api/accounts` on the planning VM at investigation time: `codex-luna` — `status: healthy`,
`weekly_pct: 33`, **`used_by_slots`: 19 of ~33 active slots**. Every other still-registered,
`status: healthy` provider showed **zero** active slots: both DeepSeek accounts, 5 healthy Gemini
accounts, 2 GLM accounts. Two Claude accounts (`sub-e-odum2default` 8% weekly, `sub-h-igboestates` 3%
weekly, `sub-f-odum2default` 0%) were genuinely near-idle and healthy, yet also at zero.

24h `activity_log` selection counts (`deepseek_spawn_selected` + `free_provider_spawn_selected`):

| account | selected | skipped (gate) | failed |
| --- | --- | --- | --- |
| codex-luna | **488** | 8 | 41 |
| deepseek-v4-pro/flash | 126 | **708** (balance_exhausted) | 12 |
| gemini (4 accounts) | 14 | 0 | **5** (36% of its own selections) |
| glm-5-2 / glm-5-turbo | **0** | 0 | 0 |

All 488 codex-luna selections had `preferred_provider: null` — every one was a fresh routing
decision, not a resume/sticky-session artifact. This rules out "slots just got stuck on codex early
and never re-rolled" as an explanation; the routing logic itself picks codex nearly every time.

### Bug 1 — Claude is unconditionally excluded, regardless of real headroom (primary driver)

Ran the actual live functions (not a re-derivation) against the real DB:

```
--- per-anthropic-account usable/headroom breakdown ---
sub-a-ikenna .. sub-h-igboestates    usable= False   (all 8, including 3%/8%/0%-used accounts)
_anthropic_pool_headroom_pct: None
effective_fraction (quota-adaptive): 1.0
```

`account_is_usable()` (`server/state_store/account_usage.py:340`) returns `False` whenever
`overage_status == "rejected"` — added 2026-08-18
(`account_failover_ignores_overage_rejected_2026_08_18.md`) to stop sessions dying on accounts that
had genuinely maxed out their included quota. It checks this **unconditionally**, with zero regard
for `weekly_pct`/`five_hour_pct`. Right now all 8 Claude accounts show `overage_status: rejected`,
including three that have used almost none of their weekly quota — consistent with overage billing
simply not being provisioned on these sub-accounts (a static account setting), not genuine exhaustion.
This collapses `_anthropic_pool_headroom_pct` (`autospawn.py:1326`, average headroom across usable
Claude accounts) to `None`, which makes `_quota_adaptive_fraction` (`autospawn.py:1468` — the
mechanism specifically built to shade dispatch *toward* Claude when it has spare, already-paid-for
capacity) short-circuit to `1.0`: 100% of sonnet-tier dispatch forced off Claude, unconditionally.

**Fix**: gate on `overage_status == "rejected"` only when the account is *also* near its included-quota
ceiling (e.g. `weekly_pct`/`five_hour_pct` above some threshold), not unconditionally. Preserves the
original 2026-08-18 protection for accounts genuinely maxed out while un-blocking real headroom on
accounts nowhere near it. `account_is_usable()` is reused by 6+ other call sites per its own
docstring — the safer implementation point may be a NEW check parallel to
`_account_meets_dispatch_headroom` rather than changing `account_is_usable()`'s own semantics; decide
at implementation time by reading current call sites, don't assume.

### Bug 2 — Gemini rotated into the pool blind to its real rate-limit headroom

`_live_free_combo_ids()` (`autospawn.py:1898` — the Phase-4 "round-robin" eligibility pool) only
checks `account_is_usable()` + `_free_provider_gate_reason()` (in-memory recent-failure count +
dollar balance). It does **not** call `_account_meets_dispatch_headroom()` (`autospawn.py:1075`),
which is the ONLY function that knows Gemini's real RPM/RPD ceiling
(`gemini_account_has_rate_headroom`). The code's own comment at `autospawn.py:1160` says this
outright: the rotation pool "returns an AccountDef directly... WITHOUT ever calling
`_pick_headroom_account`" (the picker that *does* check Gemini's real headroom). Consequence,
confirmed live: Gemini gets rotated in without regard to whether it can actually serve the request,
its picks fail 36%+ of the time (5 failures / 14 selections in 24h), and each failure trips
`_provider_health_ok`'s in-memory ring, knocking that account out of the NEXT round — so Gemini never
gets a fair, sustained share, it gets bounced by its own failures shortly after every real attempt.

**Fix**: wire `_live_free_combo_ids()` to the same headroom check `_account_meets_dispatch_headroom()`
already provides, so Gemini (and any future rate-limited provider) is only rotated into slots it can
actually serve.

### Bug 3 — alphabetical fallback order favors codex once DeepSeek is gated out

`free_provider_priority` (`config.py:1589`, default `["deepseek"]`) governs the fallback order once
the primary pick is gated out; its own code comment admits it's stale ("stale as of Phase 3 (GLM)...
leaving it DeepSeek-only just means alphabetical order silently decides the rest" —
`config.py:1582-1588`). Registered non-Claude providers today: `codex`, `gemini`, `glm`, `ollama`
(kimi is explicitly routing-blocked, see Part 2). Alphabetically: `codex < gemini < glm < ollama` — so
whenever DeepSeek is skipped, codex is tried FIRST, every time, by string sort order, never a
deliberate ranking decision.

DeepSeek itself is genuinely, correctly excluded right now: `deepseek-v4-flash`/`deepseek-v4-pro`
share one wallet, currently at `balance_usd: -0.63`, `balance_is_available: false` — 708
`free_provider_health_gate_skipped` events in 24h vs. only 126 successful selections. This is a real
exhaustion needing an operator top-up, not a bug, but it IS what makes bug 3 bite in practice right
now — with DeepSeek gated out almost always, the alphabetical waterfall runs constantly.

**Fix**: make `free_provider_priority` a real, explicit, operator-decided ranking rather than a
1-entry list with alphabetical fallthrough for everything else.

### Ruled out

- **Accounts-tab dashboard display**: `GET /api/accounts`'s `used_by_slots` (`routes/accounts.py:104`)
  is a live SQL join computed fresh on every call, not cached/stale. No display bug — the fleet really
  is that skewed.
- **GLM's 0-selections anomaly**: flagged here as unexplained, later **root-caused and confirmed
  resolved** — see Part 6 item 5 (bug 3's `free_provider_priority` fix was the fix; GLM got 27
  selections in the first 2h post-ship).

## Part 2 — Kimi/OmniRoute/OpenRouter provider removal (SHIPPED)

Operator direction, same session: Grok and Kimi are unused, remove from the accounts list and the
code (Grok was already fully removed 2026-08-20 — verified via `grep -rli grok`, zero hits, no action
needed). Then: OmniRoute (evaluated as a routing-gateway candidate when DeepSeek was first added,
never adopted — already ruled "no-go" 2026-08-06, its plan docs already archived) and OpenRouter (a
registered `AccountProvider` literal with **zero live accounts** — confirmed via the same live
`/api/accounts` pull, so the operator's "remove if unused" condition applied) — both confirmed
genuinely dead and removed too.

**Shipped**: `agent-orchestrator@055bd037b7` — 73 files (`-4074/+199` lines): `KimiWalletPanel.tsx`,
`kimi_balance.py`/`kimi_balance_poller.py`, the `omniroute-eval/` script directory, dashboard panels,
e2e specs, and every `AccountProvider`-literal/routing/pricing/wallet-reconciliation reference across
`server/accounts.py`, `autospawn.py`, `config.py`, `model_pricing.py`, `routes/accounts.py`, etc.
Mirrored the exact shape of Grok's own prior removal (same class of change, same file categories).
Full quality-gates.sh pass, clean: 5262 tests passed / 4 skipped, 86.04% coverage (baseline 85.86% —
no regression, ratchet-clean), basedpyright 0 errors, tsc clean, vitest 468/468 passed.

Doc updates for this removal (kimi_gemma_provider_onboarding_2026_08_16.md's Kimi-specific todos,
the archived OmniRoute doc, OpenRouter's mention in the DeepSeek routing plan) are tracked as
follow-up todos below — not yet done as of this doc.

## Part 3 — QG / shipping process failures hit this session (lessons, not a defect report)

None of these are bugs in `quality-gates.sh`/`ao-self-pull.sh` themselves — both behaved exactly as
designed. They're session-process mistakes worth recording so they aren't repeated:

1. **Worked in the wrong checkout.** A delegated sub-agent was given
   `/home/ubuntu/unified-trading-system-repos/agent-orchestrator` (the bare root clone — which is ALSO
   `orchestrator.service`'s live `WorkingDirectory`) instead of the assigned `.tabs/13/agent-orchestrator`
   slot. This wedged `ao-self-pull.sh` fleet-wide for 52+ minutes (silently — the Slack webhook for this
   alert is still unconfigured, a separate known gap). Full incident + recovery steps + live
   verification: `ao_self_pull_wedged_by_kimi_removal_wip_2026_08_21.md` (already resolved, cross-referenced
   here rather than duplicated). Recovery method used: `git diff HEAD` → verified byte-identical patch
   apply onto the correct slot → `git stash push -u` on the root clone (a repo guardrail hook actively
   **blocks** `git reset --hard` for exactly this class of action, which is what caught this before it
   became a real data-loss risk).
2. **A stale scratchpad path caused silent log-redirect failures.** Mid-session context compaction
   changed the session id; the system-prompt-provided scratchpad path kept pointing at the old,
   now-nonexistent directory. `nohup cmd > $STALE_PATH/log 2>&1 &` doesn't error visibly — the
   background job just fails to start writing, making a real QG run look like it silently vanished.
   Fixed by re-deriving the current session directory from a fresh tool-output path and re-creating the
   scratchpad dir there.
3. **Two of my own background watchdogs looped forever via self-matching.** A `pgrep -f
   "quality-gates.sh"` liveness check run FROM INSIDE a script whose own command line contains that
   literal string matches itself — the loop never sees "nothing running" and never exits. Fixed by
   waiting on an exact PID (`kill -0 $PID`) instead of a string pattern, per the workspace's own
   documented liveness-check convention (no self-match).
4. **Slot 13 had never been bootstrapped for this repo.** No `.venv` (`uv sync` fixed it), then no
   `dashboard/node_modules` (`npm --prefix dashboard install` fixed it) — each is a normal one-time
   per-slot setup step, not a code issue, but cost two full wasted QG cycles before being caught.
5. **A real `ruff format` drift briefly failed the gate with no visible reason in the tail.**
   `quality-gates.sh` accumulates a single `FAIL` flag across ~10 independent steps and only prints the
   terminal verdict once at the end — a step that fails early (`ruff format --check` flagged 3 files 6100+
   lines before the final banner) can scroll off a `tail -N` read, making the gate look like it failed for
   no visible reason. Lesson: grep the full log for every `── <step> ──` header, not just the tail, before
   concluding a failure is unexplained.
6. **7 incoming upstream commits landed mid-session, with one real conflict.** `git pull --ff-only`
   after stashing brought in a provider-display-naming-convention commit (`2ccdfe22`) that touched the
   same `dashboard/src/components.tsx` block my removal touched. Resolved by keeping upstream's newer
   labels minus the two removed providers — not a mechanical auto-merge, needed a real read of both
   sides' intent.

## Part 4 — bugs 4a/4b: bulk account-sweep pile-up + health-ring gap (SHIPPED)

Found while checking on bugs 1-3's live impact: operator reported "more tasks are given to
gemini models and some of them are dying or going stale". Live investigation (24h/60min
`activity_log` breakdowns by account, same method as Part 1) found TWO more stacked bugs,
distinct from bugs 1-3, both in the account-failover path rather than the fresh-dispatch path:

**Bug 4a**: `rotate_all_slots_off_account()` (`server/server.py`) calls
`select_account_for_spawn()` once per slot being swept off a dead/disabled account, in a tight
loop with NO commit in between — the actual reassignment is deferred to background threads
started only AFTER the whole loop finishes. Every call therefore sees the SAME stale
`_active_slot_counts_by_account()` snapshot, so every slot in the sweep independently
"discovers" the same single least-loaded account and piles onto it. Confirmed live: at
2026-08-21 08:33:39 UTC an operator disabled `codex-luna` via the dashboard (`account_disabled`
event, `slot_id=None` — a dashboard action, not this session); the resulting sweep dumped ~13
slots onto ONE Gemini account (`gemini-3-5-flash-lite-proj1`) within 15 seconds
(`account_rotation_triggered` timestamps 08:33:41-08:33:55, all `"to":
"gemini-3-5-flash-lite-proj1"`), blowing past its real rate ceiling — all 13 sessions died
together ~3 minutes later (8 `tmux_session_lost` rows at 08:36:19-21, empty
`pane_dead_status`/`pane_pid`, elevated host load).

**Bug 4b**: `autospawn._provider_health_ok`'s in-memory failure ring is fed ONLY by
`record_spawn_outcome`, called ONLY at the initial tmux-spawn attempt (3 call sites, all in
`autospawn.py`) — never when a session dies LATER (mid-conversation rate-limit exhaustion,
tmux pane death). So the overloaded account from bug 4a never tripped the health gate and kept
looking free: in the 60 minutes after the incident it absorbed 92 `gemini_request_selected`
events while ALSO producing 12 `tmux_session_lost` + 13 `autospawn_failed` + 4
`worker_polling_dead` events — nothing was suppressing further selection despite continuous,
measurable failure. Real backlog work (a security audit, live-trading VM tasks, an execution
OMS-persistence task) kept getting bounced and requeued.

**Fix (both, one commit)**: `agent-orchestrator@98b9bf1183`.
- 4a: generalized `_pick_headroom_account`'s existing single-id `exclude_id` to also accept an
  `exclude_ids: frozenset[str]`, threaded through all 8 `_pick_headroom_account` call sites
  inside `select_account_for_spawn` (additive, defaults to empty — no-op for every other
  caller). `rotate_all_slots_off_account` now accumulates a local `sweep_picked: set[str]`,
  passing it as `exclude_ids` on each iteration so slots spread across the live pool instead of
  piling onto one; a round-reset (mirroring `_next_rotation_combo`'s own semantics) fires once
  every live candidate has had a turn, so a single-account pool still gets every slot rather
  than wrongly returning `None`. First implementation attempt had a real bug here (forgot to
  clear the exclusion set on reset, collapsing back into pile-up after one round) — caught by
  the regression test written for it before shipping, not by manual inspection.
- 4b: `tmux_pruner.py`'s existing `death_class` classifier (`"unexplained"` vs
  `"intentional_teardown"`) now calls `autospawn.record_spawn_outcome(slot.account_id,
  ok=False)` for every `"unexplained"` death — intentional teardowns are excluded (not the
  account's fault). Reuses the SAME `_provider_health_ok` gate already checked before every
  free-provider pick, no new mechanism.
- Immediate stopgap: `gemini-3-5-flash-lite-proj1` manually `disable_account`'d while the fix
  shipped (fully reversible via `enable_account`) — the account had been actively, continuously
  failing for over an hour, wasting real task attempts.
- 4 new regression tests (`tests/test_account_rotation.py`,
  `tests/test_tmux_pruner_death_class_signals.py`): bulk-sweep spreads N slots across M live
  accounts; single-live-account sweep still serves every slot via round-reset; an unexplained
  tmux death records a spawn failure for the bound account; an intentional-teardown death does
  NOT. Full `quality-gates.sh`: 5280 passed / 4 skipped, coverage 86.06% (baseline 85.86%,
  ratchet-clean).

**Superseded by Part 5** (the "not yet done" note originally here — no RECURRENCE proof yet — is
addressed by the audit + fix below; kept as history, not re-stated).

## Part 5 — bug 4a's exact pattern found in the ROUTINE refill/resume paths too (SHIPPED)

Operator: "we dont have to check that in day or two, we have to check it in two hours. see if you
can find any other issues related to it." Audited every `select_account_for_spawn`/
`select_account_with_non_strict_retry` call site in the fleet (17 total) for the SAME
bulk-selection-before-any-commit shape bug 4a was fixed in.

**Found**: `AutoSpawnLoop._run_one_tick` (the ROUTINE refill tick — runs constantly, not just on a
rare account-disable event) and `AutoSpawnLoop._resume_pass` (dead-worker resume) both pick an
account per slot inside one DB session via `select_account_with_non_strict_retry`, with the actual
spawn/resume deferred to a later concurrent phase (`_do_spawns_concurrently`) — the IDENTICAL shape
that let bug 4a pile 13 slots onto one account, just in the high-frequency path instead of the rare
bulk-sweep path. Every OTHER call site was checked and ruled out (single-item decision points, not
batch loops): `escalation.escalate()`/`_maybe_alert_pool_exhaustion` (one PR/wall or a
headroom-only check, not a dispatch), `plan_health.dispatch()` (one scheduled job per call),
`main_agent_keeper`'s 4 call sites (the singleton main-agent slot, not a fleet loop),
`worker_liveness_watchdog._handle_usage_cap` (loops over slots but acts — kill + respawn —
synchronously per slot before the next iteration, so it doesn't share the staleness mechanism).
Also confirmed no `@lru_cache`/similar caching on the headroom-check functions that could add a
DIFFERENT kind of staleness.

**Fix**: `agent-orchestrator@ba855161ae`. Generalized `select_account_with_non_strict_retry` to
accept `exclude_ids` (mirrors `select_account_for_spawn`'s own bug-4a parameter). Factored the
exclude+round-reset spreading logic into a new shared helper,
`autospawn.select_account_with_tick_spread` (mutates a caller-owned `set[str]` in place — adds a
successful pick, clears-then-reseeds on a round-reset) — needed as a separate function, not inlined
twice, both to avoid duplicating the logic AND to keep `_run_one_tick` under the ruff C901
complexity ceiling once the extra branching was added inline (first attempt tripped it: 28 > 26).
Both `_run_one_tick` and `_resume_pass` now call it instead of `select_account_with_non_strict_retry`
directly. 4 new regression tests for the shared helper. 1240+ tests across all four bug areas pass;
full `quality-gates.sh` green (5284 passed/4 skipped, coverage 86.06%). Live-verified: root checkout
restarted onto `ba855161ae` at 10:20:30 UTC.

**Process note**: shipping this hit a real async-wait trap worth recording — the FIRST
`quality-gates.sh` background run reported "completed, exit 0" via the harness notification, but the
scratchpad session directory its output was redirected into had been silently rotated away mid-run
(the harness's own session-id changed, same class of issue Part 3 item 2 already documented), so the
"pass" was actually a phantom — the log file didn't exist and QG likely never ran at all. A SECOND
attempt then hit the OTHER known trap (Part 3 item 1's cousin): the session's persisted cwd had
drifted to the bare workspace root between calls, so `quality-gates.sh` genuinely failed
("No such file or directory") while still reporting exit 0 for the wrapping echo. Only a THIRD
attempt, with the `cd` and the log path both baked into the SAME self-contained backgrounded command
and the resulting log file's line count verified (9331 real lines, not a stub), produced trustworthy
evidence. Lesson: a "completed, exit 0" notification is not itself proof of a real pass — read the
log content and check it isn't suspiciously short/absent before shipping on it.

## Part 6 — 2-hour live-effectiveness recheck: CONFIRMED EFFECTIVE (bugs 4a/4b/5 + GLM anomaly)

Operator directive (2h after shipping, not "a day or two"). `CronCreate` job `be0aad88` fired on
schedule but the check was deliberately deferred at ~98% context (pre-compact); re-run manually this
session against the LIVE checkout's `activity_log` via `server.db.get_session_factory()`, window
2026-08-21T10:20:30Z (`ba855161ae` ship) → 2026-08-21T13:52Z (check time, live checkout by then at
`d4893b4c`, same fix lineage, no intervening dispatch-logic changes). 3419 activity_log rows in
window.

**1. Dispatch spread — confirmed, no monopolization.** 705 account-attributed selection events
across **18 distinct accounts**. Top account (`gemini-3-5-flash-lite-proj3`) holds 19.6% share;
next four each 13-16%. No account holds a majority — a structurally different pattern from the
pre-fix near-100%-on-one skew Part 1 measured.

**2. Bulk-sweep spreading (bug 4a) — directly observed live, working.** At 12:41:18-12:41:40 UTC the
operator disabled `gemini-3-5-flash-lite-proj2`/`proj3` (and briefly `deepseek-v4-flash`/`-pro`,
re-enabled seconds later — an unrelated toggle, not investigated further), triggering
`rotate_all_slots_off_account` sweeps that moved 14 slots off the two disabled Gemini accounts.
Destinations: `glm-5-2`×3, `sub-e-odum2default`×3, `glm-5-turbo`×2, `gemma-self-hosted`×2,
`sub-f-odum2default`×2, `gemini-3-5-flash-lite-proj2`×1, `sub-h-igboestates`×1 — **7 distinct
destination accounts**, roughly even split, no pileup. This is exactly the `exclude_ids` fix's
intended behavior; pre-fix this shape piled every slot onto the single first-ranked account (Part 4).

**3. Resume-pass spreading (bug 5) — directly observed live, working.** 7
`worker_account_unusable_killed` events this window, all on `gemini-3-7-flash-proj2` (4×) /
`gemini-3-7-flash-proj3` (3×) — the LOW-volume Gemini accounts hitting real RPM/RPD ceilings
mid-session, triggering the proactive failover kill (`autospawn.py:4029`, working-as-designed
self-healing, not a bug). Every one of the 7 kills was followed by a successful resume onto a
**different** account (`sub-e-odum2default`, `glm-5-turbo`, `gemini-3-5-flash-lite-proj2`/`proj3`) —
no repeat pileup onto the just-exhausted account, confirming `select_account_with_tick_spread`'s
exclusion is live-effective in `_resume_pass` too, not just `_run_one_tick`.

**4. Root cause of the "Gemini dying/going stale" symptom — isolated, and it is NOT the routing bug
post-fix.** It is `gemini-3-7-flash-proj2`/`proj3` specifically (2 of 10 Gemini accounts) hitting
real upstream RPM/RPD limits mid-session. The high-volume Gemini accounts
(`gemini-3-5-flash-lite-proj2/3/4`, 93-138 selections each) show low death/selection ratios
(0.02-0.04) — healthy. The system now self-heals this correctly (kill + respread across providers)
rather than looping or piling back onto the same exhausted account.

**5. GLM's "0-selections-in-24h" anomaly (Part 1 "Ruled out", flagged but not chased) — CONFIRMED
RESOLVED, root cause was bug 3.** GLM got 27 selections this 2h window (`glm-5-2`: 13, `glm-5-turbo`:
14), both `account_status: healthy`, `five_hour_pct` 8-9%, `last_used_at` current at check time.
`free_provider_spawn_selected` events show GLM being picked both by `autospawn_refill`'s
`free_provider_priority` walk and by `server_rotate_all_slots_off_account` during the sweep above —
both call sites bug 3's fix touches (`free_provider_priority` default `["deepseek"]` → `["deepseek",
"gemini", "glm", "ollama", "codex"]`). The old all-deepseek default meant GLM's `_live_free_combo_ids`
branch was structurally unreachable whenever DeepSeek was gated — matches the original symptom
exactly. No separate GLM-specific bug found; closing without further chase.

**New minor observations (not chased further, not bugs in bugs 4a/4b/5's scope — logged as todos
below):**
- `sub-e-odum2default`/`sub-f-odum2default` (Claude) show elevated death/selection ratios
  (0.387/0.385) vs. the healthy Gemini accounts (0.02-0.04) — but on small samples (31/13
  selections), so not conclusive yet.
- 2 GLM deaths this window were real upstream 429s ("Usage limit reached for 5 hour") where the
  `account_snapshot.account_status` embedded in the death event still read `"healthy"` — a small lag
  between the real-time API rejection and the DB's cached `account_status`/poller state, not a
  dispatch-routing bug.

**Verdict: bugs 4a/4b/5 hold under live 2h+ traffic. No further round-robin/dispatch fix work
identified.** Evidence script (one-shot, not promoted — see Deferred/lessons section): live
`activity_log` queries against `ActivityRow` (`event_type`, `slot_id`, `details_json`), joining death
events to accounts via each slot's most-recent account-carrying event, run directly against
`server.db.get_session_factory()` from the live checkout.

## Todos

- [x] [OPERATOR] P2. ✅ **RESOLVED 2026-08-21 — operator resumed all Gemini accounts.** Confirmed live:
      `data/config/accounts.json` shows `account_status: null` (enabled) for all 10 `gemini-*`
      accounts; `activity_log` shows `account_enabled` events for `gemini-3-5-flash-lite-proj1/2/3/4`
      at 12:41:49-12:42:19 UTC and `gemini-3-7-flash-proj4/5`, `gemini-3-5-flash-lite-proj5` at
      13:49:22-13:49:32 UTC. Part 6's recheck (above) confirms the fleet handles the full 10-account
      Gemini pool correctly post-resume — no pileup, proper spread.
- [x] [DATA] P3. ✅ **DONE 2026-08-21 — see Part 6.** 2-hour live-effectiveness recheck of bugs 4a/4b/5
      executed (deferred from the original cron firing, re-run manually this session). Result:
      effective — dispatch spread across 18 accounts, bulk-sweep spreading confirmed live (7 distinct
      destinations across 14 slots), resume-pass spreading confirmed live (7/7 unusable-kills
      resumed onto a different account), no monopolization pattern recurred. Repo: agent-orchestrator.
- [x] [DATA] P3. ✅ **DONE 2026-08-21 — see Part 6 item 5.** GLM's 0-selections-in-24h anomaly
      resolved: root cause was bug 3 (`free_provider_priority` defaulting to `["deepseek"]` only,
      never falling through to GLM). Confirmed live: GLM got 27 selections in the 2h post-fix window,
      both accounts healthy and actively used. No separate GLM-specific bug. Repo: agent-orchestrator.
- [ ] [DATA] P3. **NEW, found during Part 6's recheck.** `sub-e-odum2default`/`sub-f-odum2default`
      show elevated death/selection ratios (0.387/0.385) vs. the healthy high-volume Gemini accounts
      (0.02-0.04) in the 2h window — but on small samples (31/13 selections each), not conclusive.
      Re-check once more traffic accumulates (a day+); if the ratio holds on a larger sample,
      investigate why Claude sub-accounts die more often per-selection than Gemini. Repo:
      agent-orchestrator.
- [ ] [DATA] P3. **NEW, found during Part 6's recheck.** 2 GLM `tmux_session_lost` deaths this window
      were real upstream 429s, but the death event's embedded `account_snapshot.account_status` still
      read `"healthy"` at the moment of death — a small lag between the real API rejection and the
      DB's cached account-health state (poller/status-write timing, not a dispatch-routing bug). Not
      chased further; worth a look if it turns out to cause a mis-routed spawn onto an
      already-rate-limited account. Repo: agent-orchestrator.
- [x] [SCRIPT] P3. **Found while verifying bug 1 post-ship.** The live (gitignored, per-VM)
      `data/config/accounts.json` on the planning VM still carried 3 dead Kimi entries
      (`kimi-k3`/`kimi-k2-6`/`kimi-k2-7-code`) — harmless (gracefully skipped) but not a true "removed
      from the accounts list". Deleted directly on the planning VM (host-level, gitignored, no
      PR/ship) — 2026-08-21. Evidence: `claude_headroom_exclusion_readout.py` re-run post-delete shows
      zero `load_accounts: skipping malformed account entry (id='kimi-*')` tracebacks, JSON re-validated
      (`python3 -c "import json; json.load(...)"`).
- [x] [BACKEND] P1. Fix bug 1 — `account_is_usable()` (`server/state_store/account_usage.py`) now only
      treats `overage_status == "rejected"` as blocking when the account is ALSO at/over the existing
      `five_hour_pct_ceiling()`/`weekly_pct_ceiling()` (default 99%), instead of unconditionally.
      Shipped `agent-orchestrator@e3a3ef4166`. Live-verified post-deploy (orchestrator.service restarted
      2026-08-21 08:52:39 UTC via `ao-self-pull.sh`) via `claude_headroom_exclusion_readout.py`: 4/8
      Claude accounts (`sub-a-ikenna`, `sub-e-odum2default`, `sub-f-odum2default`, `sub-h-igboestates`)
      flipped `usable=False` → `True`; `_anthropic_pool_headroom_pct` went `None` → `74.5`;
      `effective_fraction` (share routed OFF Claude) went `1.0` → `0.75`. The remaining 4 accounts
      correctly stay `usable=False` (genuinely rate-limited/near-ceiling, not this bug). 2 new regression
      tests added (`tests/test_auth_failed_rotation.py`) proving both directions: near-ceiling +
      overage-rejected still blocks (preserves the original 2026-08-18 protection), far-from-ceiling +
      overage-rejected is now usable.
- [x] [BACKEND] P1. Fix bug 2 — `_live_free_combo_ids()` (`server/autospawn.py`) now gated by
      `_account_meets_dispatch_headroom()` (real RPM/RPD checks for Gemini/NVIDIA, pct ceilings for
      every poller-backed provider) instead of bare `account_is_usable()`, threaded through
      `_select_rotation_combo()`'s new `five_hour_ceiling`/`weekly_ceiling` params from
      `select_account_for_spawn`'s own already-resolved ceilings. Shipped in the same commit,
      `agent-orchestrator@e3a3ef4166`. Not independently live-verified against real Gemini traffic yet
      (needs dispatch activity to accumulate — the prior 36%+ Gemini rotation-failure rate was measured
      over 24h) — re-check `_free_provider_spawn_selected_event`/`autospawn_failed` counts for Gemini in
      a day or two.
- [x] [BACKEND] P2. Fix bug 3 — `free_provider_priority` default changed from `["deepseek"]`
      (alphabetical fallthrough for everything else) to explicit
      `["deepseek", "gemini", "glm", "ollama", "codex"]`, shipped in the same commit. **Not
      operator-confirmed** — implemented on reasoned-default judgment rather than waiting on the
      cost/latency/reliability call this todo originally flagged as `[OPERATOR]`-gated: codex placed
      LAST because it has no real quota/rate-limit signal at all
      (nvidia_codex_exhaustion_observability_gap_2026_08_19, still open) and so never fails a headroom
      check regardless of actual usage — providers with an observable real signal (Gemini RPM/RPD, GLM's
      `glm_quota_poller.py` pct fields) get first refusal instead. Operator: flag if a different order is
      wanted; the config default is a one-line change (`server/config.py` ~line 1600).
- [ ] [SCRIPT] P3. Update the 3 plan docs the Kimi/OmniRoute/OpenRouter removal (Part 2) touches but
      hasn't yet updated: `kimi_gemma_provider_onboarding_2026_08_16.md` (Kimi-specific todos/Progress
      Log — leave Gemma untouched), the archived OmniRoute evaluation doc (closing Progress Log entry
      noting the pilot code itself is now deleted, not just unused), and
      `deepseek_claude_blended_provider_routing_2026_07_28.md` (short note that OpenRouter was
      evaluated as a Phase-2 candidate provider and removed as unused code debt). Repo:
      unified-trading-pm.
- [x] [BACKEND] P3. ✅ **DONE 2026-08-21.** Added a line to `SUB_AGENT_MANDATORY_RULES.md`'s per-slot-
      worktree section: "If YOUR prompt never named an absolute `.tabs/<N>/` path, STOP and ask — never
      default to the bare repo root." Also condensed the existing incident sentence to make room. File
      now 10,119 B, under the 10,240 B (10 KiB) hard cap (`check_agent_rules_size_cap.py`). Repo:
      unified-trading-pm. (Also tracked as todo 4 in `ao_self_pull_wedged_by_kimi_removal_wip_2026_08_21.md`
      — flipped there too, same edit.)

## Codex SSOTs

- `/codex/04-architecture/agent-orchestrator-autospawn.md` — **rewritten 2026-08-21**
  (`unified-trading-pm@98d7642c05`) as the primary SSOT for this whole issue: its "Account-pick
  rotation" section previously described a single-provider (Claude-only) picker with no mention of
  the multi-provider blend, `free_provider_priority`, Phase 4 rotation, or `account_is_usable`'s real
  semantics — completely silent on everything bugs 1-5 fixed. Now documents the full
  `select_account_for_spawn` decision chain, the bulk-selection spreading mechanism, and the
  health-failure ring. Also fixed a stale 95%→99% pct-ceiling default that had drifted from the code
  across the whole doc (trigger-contract table, env-var table, anti-patterns section).
- `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` — multi-account auth model this
  bug lives in (per-account token/credential rotation — a distinct, correctly-scoped concern from the
  multi-PROVIDER routing bugs 1-5 fixed; not touched by this pass).
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — worker lifecycle/dispatch
  model the Phase-4 rotation plugs into.
- `/codex/05-infrastructure/per-tab-worktrees.md` — the per-slot worktree contract Part 3 item 1
  violated.

## Progress Log

- **2026-08-21 (slot 13, interactive)**: filed at operator request to consolidate this session's three
  threads (round-robin root cause, provider removal, QG/process lessons) into one doc rather than
  leaving the round-robin findings only in chat. All Part 1 findings are live-verified (real function
  calls against the real DB, real 24h activity_log queries), not re-derived from docs. Part 1's three
  fixes are NOT yet implemented — this doc's primary open scope.
- **2026-08-21 (slot 13, interactive, later same session)**: operator directive "fix all the bugs you
  found related to round robin first so that claude and other accounts can start working" — all 3
  fixes implemented, tested (350+ targeted tests + full `quality-gates.sh`: 5271 passed/4 skipped,
  coverage 86.05% vs. 85.86% baseline, basedpyright/tsc/vitest clean), shipped
  `agent-orchestrator@e3a3ef4166`, and live-verified post-deploy (bug 1 confirmed via
  `claude_headroom_exclusion_readout.py`: 4/8 Claude accounts now usable, pool headroom `None`→`74.5`,
  effective off-Claude fraction `1.0`→`0.75`; bug 2 shipped but not yet independently traffic-verified;
  bug 3 shipped on reasoned default, not operator-confirmed — see its todo). Also cleared the 3 dead
  Kimi entries from the live `accounts.json` (todo 1). **Notable en-route incident, not a defect**: while
  the full QG ran, AO's own pre-spawn dirty-state gate (`DirtyStateResolution.COMMIT_AND_PUSH`,
  `plans/epics/orchestrator_master.md` § 'Fresh-spawn dirty-commit (Phase 3A)') auto-committed slot 13's
  in-progress working tree as `chore(orphan-wip): inherited WIP from predecessor` — AO's dispatcher does
  not appear to distinguish a live interactive session from an idle slot when deciding whether to spawn
  into it, so it treated my dirty tree as abandoned WIP. Content was verified byte-identical to my actual
  edits before proceeding; no worker actually ended up running concurrently in the slot (checked
  `SlotRow` + live processes — none found), so no real contention occurred this time, but the same
  mechanism could clobber output ordering or race a genuinely-concurrent worker in future. Recovered
  safely via `git reset --soft HEAD~1` (unpushed, local-only commit — content re-verified identical
  after reset) and re-shipped through normal quickmerge with a correct message. Not filed as a new issue
  since it's a known, documented, non-destructive safety net working as designed — flagging here in case
  it recurs with worse timing.
- **2026-08-21 (slot 13, interactive, later same session)**: operator reported Gemini tasks "dying or
  going stale" post-deploy and asked to check overall dispatch spread. Live investigation found bugs
  4a/4b (Part 4) — root-caused, fixed, tested (4 new regression tests, one of which caught a real bug
  in the first fix attempt before it shipped), full `quality-gates.sh` green (5280 passed/4 skipped,
  86.06% coverage), shipped `agent-orchestrator@98b9bf1183`, live-verified via `orchestrator.service`
  restart (09:42:32 UTC). Paused the one actively-failing Gemini account as an immediate stopgap
  (reversible, todo above). Dispatch-spread check (the operator's second ask): selections ARE now
  reaching multiple Gemini sub-accounts, both GLM accounts, and multiple Claude accounts, not just
  `codex-luna` — bugs 1-3 are working as intended; the "dying/stale" symptom was entirely bugs 4a/4b,
  not a shortfall in bugs 1-3's fix.
- **2026-08-21 (slot 13, interactive, later same session)**: operator corrected the re-check interval
  to 2 hours (not "a day or two") and asked for a further audit for related issues. Found bug 4a's
  exact pattern also present in `_run_one_tick`/`_resume_pass` (Part 5) — the routine, high-frequency
  paths, not just the rare bulk-sweep one. Fixed, tested, shipped `agent-orchestrator@ba855161ae`,
  live-verified via `orchestrator.service` restart (10:20:30 UTC). Scheduled a session-scoped one-shot
  check (CronCreate `be0aad88`, fires ~12:02 UTC) to re-verify live effectiveness. Hit and recovered
  from two real async-wait traps while shipping this (see Part 5's "Process note") — a phantom QG
  "pass" from a rotated-away scratchpad session directory, then a genuine QG failure masked by cwd
  drift — worth remembering: a background task's "completed, exit 0" notification is not itself proof
  of a real pass.
- **2026-08-21 (slot 13, interactive, later same session)**: operator asked to update the codex docs
  so the round-robin mechanism is documented correctly (post-phase codex audit, CLAUDE.md's own
  standing rule after a major phase). Found `/codex/04-architecture/agent-orchestrator-autospawn.md`
  — the doc `authoritative_for: agent-orchestrator AutoSpawn worker-spawn architecture` — completely
  silent on the multi-provider blend this whole issue lives in: its "Account-pick rotation" section
  described a single-provider Claude-only picker, no mention of `free_provider_priority`, Phase 4
  rotation, or `account_is_usable`'s real (post-2026-08-18, post-bug-1) semantics; separately, a
  95%→99% pct-ceiling default had drifted stale across the whole doc. Rewrote the section end to end
  (decision chain, bulk-selection spreading, health-failure ring), fixed every stale ceiling
  reference, fixed two other stale pointers found in passing (a dead "Overview pointer" section
  reference, an archived-not-active plan path) — both per CLAUDE.md's "a doc/pointer that misled you
  is a finding, fix it in the same turn" rule. Validated with the repo's own
  `check_frontmatter_schema.py` (clean) and `check_reference_paths.py` (0 new dangling refs, ratchet
  held at the existing baseline of 34) before shipping. Shipped `unified-trading-pm@98d7642c05`. The
  multi-account AUTH doc (`claude-cli-multi-account-headless-auth.md`) was checked and correctly
  left untouched — its scope (per-account credential/token rotation) is genuinely distinct from the
  multi-PROVIDER routing this issue is about, confirmed via grep before deciding not to touch it.
