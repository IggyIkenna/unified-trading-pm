---
doc_type: plan
title: DeepSeek/Claude blended provider routing for agent-orchestrator
summary:
  Register DeepSeek V4 Pro as a second, first-class model provider in agent-orchestrator's account pool, and add a
  routing layer so AutoSpawn decides per-task whether a fresh spawn uses DeepSeek or a Claude Max account — a real
  policy (model-tier eligibility + tunable split + health gate), not blending it into the existing usage%-based
  Claude-account ranking, which would greedily over-select a pay-per-token account every tick.
status: active
nature: process
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, deepseek, model-routing, multi-provider, cost-optimization, reliability]
related:
  [
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/06-coding-standards/model-tier-selection.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-28
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-05
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
source:
context_scope:
  [
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/config.py,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    /codex/06-coding-standards/model-tier-selection.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
  ]
---

# DeepSeek/Claude blended provider routing for agent-orchestrator

## Why

Operator goal: reduce Claude Max token spend and outage exposure across the ~14 parallel AO slots by running some spawns
on DeepSeek V4 Pro instead of Anthropic, decided automatically per task (not a mid-session switch — that's explicitly
out of scope for this plan; see "Non-goals").

**Codex SSOTs this plan depends on** (read before touching the cited code):

- `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` — the `oauth_token_env_file` +
  `CLAUDE_CODE_OAUTH_TOKEN` setup-token contract every account currently assumes.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — worker lifecycle + dispatch model this
  routing layer plugs into.
- `/codex/04-architecture/agent-orchestrator-overview.md` — account auth model, `AgentKeeper`, fleet-cap semantics.
- `/codex/06-coding-standards/model-tier-selection.md` — the `sonnet < opus < fable` tier semantics this plan's
  eligibility gate reuses (`opus-required` is qualitative judgment work only, never routed to DeepSeek).

**Findings from a live code read (2026-07-28) that this plan exists to fix, not just add to:**

1. `server/usage_poller.py::_tick_once()` regex-scrapes every account's env file for `CLAUDE_CODE_OAUTH_TOKEN`
   (`usage_tracker.py`'s `_TOKEN_RE`) to poll `/usage`-style quota. An account without that token (any DeepSeek entry,
   by design) hits the `parsed.raw_text_preview == "no token"` branch (`usage_poller.py:377-379`), which calls
   `self._alert_account_auth_failed(...)` and `self._mark_auth_failed_db(...)` — the SAME status
   `_pick_headroom_account()` uses to exclude an account from automatic selection. Adding a DeepSeek account to
   `accounts.json` with no further change gets it marked broken within one poll tick.
2. `server/autospawn.py::_pick_headroom_account()` (called from the main AutoSpawn loop and two other automatic spawn
   paths) ranks **every** account in `accounts.json` by `(five_hour_pct, weekly_pct, active_slot_count)` ascending and
   picks the lowest. A DeepSeek account has no such usage-cap concept — if finding 1's `auth_failed` marking is fixed
   without also addressing this, a DeepSeek entry would read as a permanently-idle "0% used" account and get greedily
   picked for nearly every automatic spawn, starving the 4 Claude accounts of dispatch. Blending providers into this
   ranking function is the wrong fix; a task/tier-aware routing layer in front of it is the right one (see Track 1
   below).
3. The codex SSOT `claude-cli-multi-account-headless-auth.md` and prior session notes referenced a
   `POST /api/slots/{id}/rotate-account` endpoint for manual account switching. Grepped the live code
   (`routes/slots_ops.py`, `server.py`) 2026-07-28: **no such route exists.** The real mechanism is
   `POST /api/slots/{id}/reassign` (kills the session) followed by `POST /api/slots/{id}/spawn` with a different
   `account_id` (starts a fresh session, no conversation resume). Out of scope for this plan to fix the codex drift
   itself, but any todo below that touches manual account switching should use the real mechanism, not the documented
   one.

## Non-goals

- **Mid-session / live model switching is explicitly out of scope.** `ANTHROPIC_BASE_URL` is read once at `claude`
  process launch (confirmed via Anthropic's own GitHub issue tracker); crossing providers requires a fresh spawn. This
  plan only covers **which provider a fresh spawn uses**, decided automatically at spawn time.
- Not touching the interactive Claude Code CLI or VS Code extension surfaces — operator is exploring those manually,
  separately.
- Not fixing the `claude-cli-multi-account-headless-auth.md` doc-vs-code drift on the `rotate-account` endpoint (finding
  3 above) — flagged for a separate, smaller doc-correction pass.

## Design summary

A new `select_account_for_spawn(task_context)` function sits in front of the existing `_pick_headroom_account()`:

1. **Eligibility** — only `sonnet`-tier tasks are DeepSeek-eligible. Any `opus`/`fable`-tier task always routes to the
   existing Claude-only pool, unconditionally (reuses `model_tier.py`'s existing rank — no new judgment call).
2. **Split** — an operator-tunable `tuning.deepseek_route_fraction` config value (start conservative) decides what
   fraction of _eligible_ spawns go to DeepSeek. Round-robin counter, not randomness, so behavior is predictable and
   debuggable during the pilot.
3. **Health gate** — before routing to DeepSeek, check its recent spawn-failure count (mirrors the existing
   `_SPAWN_FAILED_ALERTED` dedup-state pattern already used for spawn failures). Falls back to the Claude pool
   automatically if DeepSeek looks unhealthy — this is what makes the blend a reliability win, not just a cost split.
4. The Claude branch delegates to the **existing, unmodified** `_pick_headroom_account()` ranking, scoped by one added
   `provider == "anthropic"` filter.
5. **Resume is a special case, discovered during implementation (2026-07-28)**: `_resume_pass` (dead-worker `--resume`)
   must NOT run the full eligibility/split/health-gate decision — it must stay on the SAME PROVIDER the dying session
   was already running on. Replaying one model's transcript into a DIFFERENT model mid-task is a correctness risk, not a
   cost/routing decision. `select_account_for_spawn()` therefore takes a `preferred_provider` parameter: `None` (the two
   fresh-dispatch call sites — the main AutoSpawn loop and `ensure_review_agents`) runs the full decision;
   `_resume_pass` passes the slot's last-bound account's provider (looked up via `SlotRow.account_id` →
   `accounts_file.get(...).provider`), pinning the pick to that provider's pool unconditionally.

## Progress Log

- **2026-08-11 (slot 3, interactive) — flash-vs-pro A/B is LIVE; first measured routing readout. Does NOT close the
  `[REVIEW] P2` pilot todo** (see the caveat at the end — that todo's done-when asks for QG-pass/rework vs a CLAUDE
  baseline, which is not obtainable right now). Operator asked to "extend DeepSeek to scheduled tasks and all roles" and
  to add a 50/50 flash-vs-pro A/B; **both turned out to be already built and already running** — recorded here so the
  next agent does not re-implement them:
  - **All four spawn paths already route through the one provider-aware router** `autospawn.select_account_for_spawn`:
    scheduled/cron (`plan_health.py`, `plan_health_deepseek_fallback_2026_08_06`), review
    (`autospawn.ensure_review_agents`), main (`main_agent_keeper`, 3 call sites), escalation (`escalation.py`,
    `escalation_deepseek_fallback_2026_08_05`). Nothing was left on the anthropic-only `_pick_headroom_account` path.
  - **The A/B is not inert.** `deepseek_flash_route_fraction` was already `0.5`, and the planning VM's
    `data/config/accounts.json` registers BOTH halves — `deepseek-v4-pro` (`variant: "pro"`) and `deepseek-v4-flash`
    (`variant: "flash"`). The `config.py` comment claiming "no such account exists in any accounts.json today" was STALE
    and actively misleading (it reads as "this knob does nothing"); corrected in the same change with the numbers below
    — agent-orchestrator@e2a3083624.
  - **Measured 24h to 2026-08-11 06:00Z**, from `activity_log` split by `account_id`:

    | signal                              | flash | pro | normalised                     |
    | ----------------------------------- | ----- | --- | ------------------------------ |
    | `deepseek_spawn_selected`           | 1201  | 944 | **56.0% / 44.0%** vs 50/50 aim |
    | `autospawn_succeeded`               | 618   | 449 | —                              |
    | `autospawn_failed`                  | 27    | 22  | 95.8% vs 95.3% spawn success   |
    | `spawn_retry_cap_reached`           | 106   | 108 | 8.8% vs 11.4% of selections    |
    | `free_provider_health_gate_skipped` | 177   | 106 | 14.7% vs 11.2%                 |
    | `main_agent_autospawned`            | 14    | 12  | opus-tier main IS on DeepSeek  |
    | `agentkeeper_review_succeeded`      | 74    | 68  | review agents on DeepSeek      |

  - **Fleet share**: DeepSeek took 5,643 of 5,705 spawns in that window (~99%); all six Anthropic accounts together took
    62, because every one of them is rate_limited/disabled. `_quota_adaptive_fraction`'s "no usable Claude account →
    1.0" short-circuit is doing exactly what it was built for.
  - **Two things worth a follow-up rather than a silent assumption**: (a) the split is running ~6 points flash-heavy
    against a 50/50 target — the accumulator is fair-share per DeepSeek-bound selection, so this is worth confirming is
    sampling noise over a single window rather than a systematic skew; (b) flash trips
    `free_provider_health_gate_skipped` ~30% more often than pro, normalised.
  - **CAVEAT — this is a ROUTING readout, not the pilot's outcome comparison.** `[REVIEW] P2` asks for QG pass rate and
    review-flagged rework rate against the **Claude baseline**; neither is in these numbers, and a contemporaneous
    Claude baseline is not collectable while every Anthropic account is exhausted (62 spawns is not a comparison
    cohort). That todo stays OPEN.

> Condensed 2026-08-05 (was 999/1000 lines, at the hard cap) — every dated entry below still cites its sha/evidence;
> trimmed the essay-length rationale now redundant with the shipped code + tests. Nothing removed changes done-when
> status of any todo.

**2026-07-28** — Todos 1-5 implemented, QG green (1905 passed), held per operator instruction until the real DeepSeek
account was registered and smoke-tested. `provider` field added to `AccountDef`; `usage_poller.py` excludes any
non-anthropic account from the token probe entirely; `select_account_for_spawn()` implemented (eligibility + round-robin
split + health gate + `preferred_provider` pin for resumes); all 3 automatic spawn call sites rewired; new tunables on
`TuningDefaults`; new `tests/test_deepseek_provider_routing.py`.

**2026-07-29 — DeepSeek account registered + smoke-tested; 6-task local pilot.** Env file + `accounts.json` entry
created (gitignored, no sha). First smoke hit `402` (balance $0); operator topped up $5; `AUTH_OK` confirmed via the
real DeepSeek endpoint. Full pilot via an isolated local backend (slots 1-5 paused, review loop disabled, spare slots
21-30): all 6 tasks completed with verified-correct reasoning (spot-checked by hand), genuine concurrent dispatch
proven, $0.09 total spend. No live Claude spawn — all 4 real accounts were genuinely rate-limited at the time.
**Self-caused incident, contained**: an unset `ORCHESTRATOR_SERVER_URL` meant every spawned worker's boot prompt
defaulted to the PRODUCTION URL; one worker attempted an unauthenticated curl toward the real prod heartbeat endpoint
before its session ended (no confirmed response captured). Separately, the always-on spawn-liveness watchdog (ungated by
`ORCHESTRATOR_AUTOSPAWN_ENABLED`) began auto-killing+respawning silently-unreachable workers in a loop. Caught within
minutes; isolated backend + throwaway sessions killed; a real, unrelated production session verified undisturbed
throughout. Closed by the `[INFRA] P1 server_url()` guard todo below. Adjacent gap found, no real damage this run:
`AgentKeeper`/`ensure_review_agents` stay always-on regardless of `ORCHESTRATOR_AUTOSPAWN_ENABLED` and read some
unscoped state (`STATE_DIR`, Slack webhook, `pm_repo_path`) — documented via the isolation-runbook todo.

**2026-07-29 — Model-selection policy redesigned per operator ruling** (DeepSeek-first, quota-adaptive, mutual fallback;
supersedes the original 30%-experiment framing): opus/fable get an unconditional hard pin to Claude (no DeepSeek
fallback ever, even at zero Claude headroom); sonnet-tier is DeepSeek-first by default (`deepseek_route_fraction`
0.3→0.8); new plan-level `provider: claude` frontmatter override; a quota-adaptive nudge shades the fraction by real
Claude headroom; a `provider: claude` override still falls back to DeepSeek at zero Claude quota so sonnet-tier work
never stalls — distinct from the hard kill-switch (`fraction<=0`, no fallback either direction). Real bug found+fixed:
the old modulo split formula couldn't represent fractions above 0.5 (0.8 silently fired 100%) — replaced with a
Bresenham-style fair-share accumulator (1e-9 epsilon for float drift). 34 tests, QG green (1923 passed). Confirmed:
CLAUDE.md/`agents/*.md` need no DeepSeek special-casing — both load identically regardless of which backend
`ANTHROPIC_BASE_URL` points at.

**2026-07-29 (afternoon) — SHIPPED.** Rebased onto 33 incoming commits, re-piloted (`provider_override` end-to-end
verified; could not validate Claude-headroom-dependent paths from a machine with no `api.claude.ai` access).
`agent-orchestrator@7076283` on `live-defi-rollout`, ahead=0. `accounts.json` stays gitignored, so the code merge alone
does not activate DeepSeek in production.

**2026-07-30 — env-leak incident found+fixed** (unrelated to the routing code itself, same plan's setup-guide artifact).
A shell that directly-sourced the DeepSeek env file (bypassing the `deepseek()`/`deepseek-code()` wrappers) poisoned a
long-lived VS Code Electron process for most of a day, silently routing every subsequent `claude`/`code` launch to
DeepSeek. Fixed: `agent-orchestrator@02c8d7f` — wrappers now `unset` the relevant env vars before sourcing; setup guide
gained a `[!CAUTION]` block. (Same investigation also fixed an unrelated orphaned e2e test fixture, same commit.)

**2026-07-30 — `[INFRA] P1` server_url() guard SHIPPED.** `config.server_url()` now raises instead of silently
defaulting to the prod URL when standalone and unconfigured; all 5 real call sites walked and confirmed fail-safe. New
autouse fixture clears `ORCHESTRATOR_STANDALONE` in tests. `agent-orchestrator@fcc7f24`, ahead=0, QG green (2068
passed).

**2026-07-30 — `[DATA] P1` spend-guard ceiling SHIPPED.** No real DeepSeek billing telemetry exists, so used a
route-selection COUNT (rolling 24h/30d, not calendar-boundary) as a spend proxy via a new `deepseek_spawn_selected`
event. `agent-orchestrator@4c5267d`, QG green (2076 passed).

**2026-07-30 — `[UI] P1` provider badge SHIPPED.** Server resolves `provider` once per `/api/state`/`/api/accounts`
request; new `ProviderBadge` wired into `SlotTable`/`SlotCards`/`AccountRow`. A Playwright spec caught a real bug
pre-ship (badge blanked on dead rows, inconsistent with sibling fields) — fixed before commit.
`agent-orchestrator@12ae7c2`, QG green (2086 passed), 2 new Playwright tests passed. Unrelated flake found+filed, not
fixed: `plans/archive/issues/backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30.md`.

**2026-07-30 — `[INFRA] P2` local-dev isolation runbook SHIPPED.** New
`/codex/15-runbooks/agent-orchestrator-local-pilot-isolation-runbook.md` documenting the 5 real gaps hit by the
2026-07-29 incident, with a pre-launch checklist — a documentation fix, not a code change (the always-on
AgentKeeper/review-agent behavior is by design). Also fixed a stale `ORCHESTRATOR_PM_REPO_PATH` docstring claim in 5
places (`pm_repo_path` is env-free by design, 2026-07-18 ruling). `agent-orchestrator@30568ec`, ahead=0 (plus an
unrelated same-day quickmerge sentinel/CI fix needed to ship at all).

**2026-07-30 — `[INFRA] P2` e2e regen() provider test SHIPPED — last locally-doable todo this phase.** Added missing
unit coverage for `_parse_frontmatter_provider` plus a real end-to-end `regen()` pass proving the frontmatter reaches
`BacklogTask.provider_override` through the real code path. `agent-orchestrator@ac70068`, ahead=0.

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).

**2026-08-02 — `/autonomous` dispatch on Phase 2 todos.** `[DATA] P2` (health-gate ring generalized to a per-provider
map) SHIPPED, proven via simulated multi-provider-failover tests. `[INFRA] P2` (AccountProvider generalization) ships
code+tests but stays open — its own done-when needs a real second-provider credential nobody has provisioned.
`[DATA] P1` confirmed not locally doable (`accounts.json` gitignored/per-VM). Also fixed an unrelated Mac-only test
failure blocking every AO QG run since 2026-08-01 (a liveness test reads `/proc`, absent on macOS — narrow platform skip
only). `agent-orchestrator@24bd611`, +220/-16, 2224 passed. **`[REVIEW] P2` grep/symbol context-reduction — closed with
a measured finding.** Compared naive full-file reads against grep-anchored bounded-window reads for 2 real shipped task
classes this session: **~10.8x reduction** (config-field threading) and **~7.7x reduction** (Literal/enum generalization
across a 2,877-line module). Finding: grep/symbol-based reduction is already highly effective for localized changes — no
evidence a vector-embedding layer is currently warranted (consistent with the workspace's standing grep-native
principle). Honest limitation: both cases had obvious anchor symbols — doesn't test the dense/many-call-sites case.

- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — swapped in `autospawn.py`/`config.py`, the actual
  files hosting `select_account_for_spawn`/`_pick_headroom_account`/`_resume_pass` and the `deepseek_route_fraction`
  tuning knob.

**2026-08-04 — `[INFRA] P0` VM-side registration ✅ COMPLETE.** Via AWS SSM `send-command` (no SSH, no inbound firewall
change, CloudTrail-audited): read-only recon first confirmed the VM was genuinely live (~15 real worker slots doing real
work); deployed the env file + `accounts.json` entry via an idempotent script (safe to re-run); `AUTH_OK` verified as
the `ubuntu` user. **Real finding**: `accounts.json` → `AccountRow` syncs ONLY at server boot (no periodic resync) — but
this does NOT block dispatch, since `select_account_for_spawn()` reads `accounts.json` fresh every call and the
headroom-picker already treats a missing DB row as healthy by design. Dashboard visibility was the only real gap, closed
by an operator-confirmed restart (verified safe first: `KillMode=process` means tmux/claude workers survive a backend
restart — the same restart `ao-self-pull.sh` performs routinely). Post-restart: 10/10 tmux sessions survived,
`/api/accounts` confirmed `deepseek-v4-pro` `status:healthy`. Separately: operator wants the key GSM-sourced eventually
— no `deepseek*` secret exists in GSM yet (checked 2026-08-04); waiting on the operator to supply a name.

**2026-08-04 (later, slot-2) — sandboxed DeepSeek pilot, 3 real tasks.** Reconciliation: this session redundantly
re-registered DeepSeek locally (gitignored, zero effect on the real fleet) before discovering the VM-side registration
above had already landed same-day — flagged, not fixed, since the pilot evidence itself is new. Balance dropped
$5.00→$4.93, consistent with the pilot's own $0.07 spend. All 3 tasks (simple/medium/hard) completed correctly,
independently re-verified (not trusting the agent's own claim); the hard task correctly applied commit-attribution
conventions unprompted. New finding: `/pre-compact` (Skill-tool invocation) does not work under a DeepSeek-backed
session — investigated further same day, see next entry.

**2026-08-04 (later still, slot-2) — isolated the /pre-compact gap: harness/CLI-version issue, NOT a DeepSeek reasoning
gap.** Control test: identical tool lists (no `Skill` tool) on both a Claude-backed and a DeepSeek-backed session.
Typing `/pre-compact` directly into an idle Claude-backed pane returned `Unknown slash command` even with the real
`SKILL.md` copied into the sandbox cwd (ruling out "missing skill file"). Root cause: the spawn binary is
`claude 1.0.112`, predating the Skills feature entirely (workers run `DISABLE_AUTOUPDATER=1` by design, so a fleet
install never self-updates). Confirmed by reading `context_lifecycle.py:349` directly: the forced
`/pre-compact`→`/compact` two-phase path only checks whether text left the input box — it cannot distinguish "skill ran"
from "Unknown slash command" silently swallowed, so the pre-compact durability ritual can silently no-op fleet-wide
(Claude-backed workers too, not just DeepSeek) with zero signal. `/compact` itself still fires (a real CLI built-in), so
compaction proceeds, but the checkpoint-first guarantee is unverified fleet-wide. Not yet confirmed whether the
PRODUCTION VM's own pinned binary is on the same pre-Skills version — new todo below. (Correction to the earlier entry:
not a DeepSeek-specific gap — the shell-out fallback was a reasonable improvisation given a structurally absent
capability.) Cost: ~$0.01
($4.93→$4.92), confirmed via `GET /user/balance` before/after.

## Phase 2 — multi-provider generalization + external-ideology reconciliation (2026-07-30)

Operator shared an external "AI Compute Optimisation Strategy" doc (generic, not written for this fleet) proposing 7→2
Claude Max accounts via free/open-provider routing + retrieval-based context reduction, and asked for its ideas to be
merged into "our plan doc." This plan — not the narrow, unrelated OmniRoute pilot doc
(`omniroute_llm_gateway_pilot_design_2026_07_30.md`) — is the real home: it already ships almost exactly the router the
external doc describes (opus/fable hard-pinned to Claude; sonnet-tier default-routed to a cheaper provider with
quota-adaptive, mutual-fallback routing), just generalized to one provider (DeepSeek) instead of several.

**Reconciling the external doc's numbers against this fleet's real state (operator-confirmed 2026-07-30):** actual count
is **6** Claude Max accounts today (this plan's own Progress Log/rollout text says "4" — stale as of 2026-07-29/30;
ratio any of the external doc's figures — $2,800/mo, ~560M output-token value/mo — against 6, not the external doc's
generic 7, if a baseline dollar figure is ever needed). Critically, **the goal is not "shrink to 2 accounts" as an end
in itself** — the operator reports real outages/rate-limit exhaustion still happening AT 6 accounts (directly consistent
with this plan's own 2026-07-29 pilot finding: _"all 4 real Claude Max accounts are currently genuinely rate-limited"_ —
the same failure mode, now at a higher account count). Desired effective throughput is **~7-Claude-account-equivalent**
— so the actual target is: eliminate quota outages at 6 (or fewer) real Claude subscriptions by offloading enough work
to free/cheap providers that effective capacity matches ~7 accounts' worth, without necessarily buying a 7th. The
external doc's "2 accounts" is a stretch/upper-bound aspiration worth keeping as a long-term direction, not the
near-term target this section's todos below are scoped against.

**Why the mechanism should be generalized, not replaced.** `select_account_for_spawn()` + `AccountProvider` (Progress
Log 2026-07-29) already implement the external doc's "Router Rules" (free/cheap provider first, escalate to Claude on
low confidence/repeated failure/architectural work) — with real safety properties an OmniRoute-style opaque gateway
would not have for free: a hard, unconditional opus/fable pin, quota-adaptive fair-share splitting, mutual fallback, and
a `provider: claude` per-plan override. Broadening this from `Literal["anthropic", "deepseek"]` to an open provider set
(OpenRouter, Gemini, Groq, SambaNova, per the external doc's candidate list) reuses a proven, tested design instead of
introducing a second, parallel routing mechanism that would compete with it. This is also the concrete resolution of the
OmniRoute plan's own guardrail (never extend that pilot to the worker fleet without a fresh model-tier-risk review) —
the fresh review's conclusion is: **don't use OmniRoute for the fleet; generalize the mechanism already built here
instead.**

**Retrieval-layer reconciliation.** The external doc's retrieval pipeline (vector search → symbol graph → dependency
graph → file ranking, targeting ~500k→200k token code context) is a DIFFERENT retrieval domain than this workspace's
existing grep-native L0-L4 system (`context_scout`/`context_scope`, targets plan/codex/frontmatter retrieval, not
general source-code symbol lookup) — so there's no direct doc-vs-doc conflict. But this workspace has an explicit,
broadly-worded governing principle on record: _"The whole retrieval design is grep-native, NOT vector-RAG... embeddings
rejected"_ (`/codex/11-project-management/doc-frontmatter-schema.md:49`). Any code-context-reduction work should
evaluate grep/symbol-based techniques (ripgrep, ctags/AST-grep-style symbol lookup, import/dependency graphs derivable
from existing tooling) FIRST, consistent with that principle — a vector-embedding code-retrieval layer is its own
separate, explicitly-flagged decision if grep/symbol-based reduction proves insufficient, never something to adopt by
default from an external reference.

## Todos

- [x] [INFRA] P0. ✅ Add `provider: Literal["anthropic", "deepseek"] = "anthropic"` to the Account model. —
      `agent-orchestrator@7076283`, QG 1964 passed.
- [x] [INFRA] P0. ✅ Guard `usage_poller.py::_tick_once()` so non-anthropic accounts skip the token probe entirely (no
      `auth_failed` marking). — `agent-orchestrator@7076283`, covered by `test_deepseek_provider_routing.py`.
- [x] [INFRA] P0. ✅ Register the DeepSeek account end to end (env file + `accounts.json` entry + creds-bucket push). —
      Done 2026-08-04 on the real VM (`i-0c9b283b31d6b5ca7`) via SSM; `AUTH_OK` verified; `orchestrator.service`
      restarted; `/api/accounts` confirms `status: healthy`. See Progress Log 2026-08-04.
- [x] [INFRA] P0. ✅ Implement `select_account_for_spawn()` — redesigned 2026-07-29 (DeepSeek-first for sonnet-tier,
      hard opus/fable pin, mutual fallback, quota-adaptive nudge, fair-share accumulator split). —
      `agent-orchestrator@7076283`, 34 tests, QG green.
- [x] [INFRA] P0. ✅ Replace the 3 direct `_pick_headroom_account()` call sites with `select_account_for_spawn()`; scope
      the original ranking to `provider == "anthropic"`. — `agent-orchestrator@7076283`.
- [x] [DATA] P1. ✅ Spend-guard ceiling before routing to DeepSeek (daily/monthly, activity-log on trip). —
      `agent-orchestrator@4c5267d`, QG green (2076 passed).
- [x] [UI] P1. ✅ Provider badge on dashboard slot/account views. — `agent-orchestrator@12ae7c2`, QG green (2086
      passed), 2 Playwright tests.
- [ ] [REVIEW] P2. Pilot the blended pool for one week at the default split, then compare DeepSeek-routed task outcomes
      (QG pass rate, review-flagged rework rate) against the Claude baseline before raising the split. Done when: a
      dated comparison note with actual pass/rework numbers lands in this plan's Progress Log. **Partial input landed
      2026-08-11** (routing + spawn-health readout in the Progress Log) — still OPEN: that readout carries neither QG
      pass rate nor rework rate, and a contemporaneous Claude baseline is uncollectable while every Anthropic account is
      exhausted (62 spawns in 24h is not a cohort). Re-attempt once a Claude account clears its weekly window.
- [ ] [REVIEW] P2. Confirm whether the flash-vs-pro split running ~6 points flash-heavy (measured 2026-08-11:
      `deepseek_spawn_selected` flash 1201 / pro 944 = 56.0%/44.0% against a 0.5 target) is sampling noise over one 24h
      window or a systematic skew in `_deepseek_flash_should_route`'s accumulator. Done when: either a second
      independent window lands within a couple of points of 50/50 (→ noise, close it), or the accumulator is shown to
      drift and is fixed. Note the accumulator is deliberately fair-share, not `random.random()`, so a persistent skew
      would be a real defect rather than variance. Repo: agent-orchestrator.
- [ ] [REVIEW] P3. Investigate why the flash variant trips `free_provider_health_gate_skipped` ~30% more often than pro,
      normalised (measured 2026-08-11: flash 177/1201 = 14.7% vs pro 106/944 = 11.2%). The health gate skips a DeepSeek
      account after `deepseek_health_failure_threshold` spawn failures in the trailing window, so a systematically
      higher skip rate means flash spawns fail more — which, if real, is a genuine A/B signal about the cheaper variant
      and belongs in the pilot comparison above. Done when: the difference is either explained as an artifact of the
      higher flash spawn volume or confirmed as a real per-variant failure-rate gap. Repo: agent-orchestrator.
- [x] [INFRA] P2. ✅ Document/fix the local-dev isolation gap (`AgentKeeper`/`ensure_review_agents` ungated by
      `ORCHESTRATOR_AUTOSPAWN_ENABLED`; `pm_repo_path` env-override docstring stale in 5 places). — New runbook
      `/codex/15-runbooks/agent-orchestrator-local-pilot-isolation-runbook.md`; `agent-orchestrator@30568ec`.
- [x] [INFRA] P1. ✅ Fix the local-pilot production-reachability incident (`server_url()` silently defaulted to prod
      when unset). — `config.server_url()` now raises when standalone+unconfigured; `agent-orchestrator@fcc7f24`, QG
      green (2068 passed).
- [ ] [REVIEW] P1. Re-run the local pilot against the REDESIGNED policy specifically (the 2026-07-28 pilot validated the
      old 0.5-fraction design, not this one). Done when: a dated Progress Log entry shows (a) a `provider: claude` plan
      and a default-policy plan dispatched in the same run with visibly different outcomes, (b) at least one real spawn
      where the quota-adaptive nudge measurably changed the effective fraction from a real Claude headroom reading, (c)
      the hard opus/fable pin held even at zero Claude headroom.
- [x] [INFRA] P2. ✅ End-to-end test `provider: claude` plan frontmatter through the real `regen()` function, not just
      the unit-level parser. — `agent-orchestrator@ac70068`.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Touches
  agent-orchestrator's own live routing/billing/credential infra; repeated dated operator holds + 2 documented real
  safety incidents from testing this code; highest-stakes remaining items need operator-supervised rollout.
- [x] [REVIEW] P2. ✅ Investigate whether DeepSeek-backed sessions can invoke Claude Code Skills — isolated +
      root-caused 2026-08-04: NOT a DeepSeek-specific gap, the fleet's pinned `claude` CLI binary (1.0.112) predates the
      Skills feature entirely (`DISABLE_AUTOUPDATER=1` by design). `context_lifecycle.py`'s forced `/pre-compact` path
      can't distinguish "skill ran" from "Unknown slash command" silently swallowed — production impact confirmed by
      reading the code. See Progress Log 2026-08-04 for the full isolation writeup.
- [ ] [INFRA] P1. Confirm whether the production VM's pinned `claude` CLI supports Skills at all, and if not, fix
      `context_lifecycle.py`'s forced `/pre-compact` path to detect "Unknown slash command" and fall back/alert instead
      of silently proceeding to `/compact`. Done when: (a) the VM's actual `claude --version` (or equivalent
      pane-capture evidence) is checked and recorded, (b) fixed via a binary bump or a hardened `submitted` check, (c)
      verified against a real forced-precompact cycle, not just unit-tested.

### Phase 2 todos (2026-07-30, added — none of the above touched or re-ordered)

- [ ] [DATA] P1. Ratio-check the account-count/cost assumptions against real `accounts.json` + `/usage` data (6 real
      Claude Max accounts as of 2026-07-30). Done when: a dated Progress Log entry states the real per-account tier/cost
      and a computed monthly total. Not locally doable — `accounts.json` is gitignored/per-VM.
- [x] ✅ [INFRA] P2. Generalize `AccountProvider` from `Literal["anthropic", "deepseek"]` to an open provider set
      (openrouter/gemini/groq/sambanova), reusing `select_account_for_spawn()`'s existing design, not OmniRoute.
      **Code+tests SHIPPED `agent-orchestrator@24bd611`** — a pure no-op in production until a real second-provider
      credential exists. — **CLOSED 2026-08-06 (operator, interactive): buildable part done; the real-pilot-dispatch
      proof is deliberately deferred to first real use.** Ruling source: the same 2026-08-06 `/plan-reconcile ao`
      session that ruled the sibling provider-strategy decision recorded in
      `/plans/archive/2026_08/omniroute_multi_provider_routing_evaluation_2026_08_03.md` § "Phase 3 — decision"
      (OmniRoute no-go) — one coherent call about which providers this workspace routes to, recorded in two docs.

      **Why closed rather than left open**: the original done-when required proving the abstraction "via a real
                                                                  isolated local pilot dispatch", which needs a provisioned credential for a provider the operator has just ruled
                                                                  out — "for now we are going to work with claude and deepseek only" (same session). As written the todo was
                                                                  **unsatisfiable without reversing that ruling**, so leaving it open would put a permanently un-actionable item in
                                                                  front of every future audit. When a second provider IS adopted, running that pilot dispatch simply *is* the
                                                                  integration work — not a separate task to remember — and the operator's own estimate for that integration is "a
                                                                  few hours".

                                                                  **Known, accepted risk — state it plainly rather than let the ✅ imply more than it should**: this code has never
                                                                  executed against a real second provider. It is tested (34 pre-existing routing tests pass unmodified, plus
                                                                  simulated multi-provider-failover tests) but unproven in production, and a no-op cannot regress anything today.
                                                                  **The first real second-provider integration must treat this as unverified code**, not as a working feature to
                                                                  configure. Do not re-file this as a standing todo — re-open it at that moment instead.

- [x] [DATA] P2. ✅ Generalize the DeepSeek-specific health-gate ring to a per-provider map (failing free provider
      degrades to the next-priority free provider before falling back to Claude). — `agent-orchestrator@24bd611`, proven
      via simulated multi-provider-failover tests; all 34 pre-existing routing tests pass unmodified.
- [x] [REVIEW] P2. ✅ Investigate grep/symbol-based code-context reduction for implementation-tier work, evaluated
      before any vector-embedding approach. — See Progress Log 2026-08-02: ~8-11x reduction on 2 real task classes; no
      evidence a vector-embedding layer is currently warranted.
- [x] ✅ [OPERATOR] P3 (stretch). Evaluate self-hosted open-weight models (Kimi, Qwen Coder, DeepSeek open-weights) as a
      further execution-cost layer once the multi-provider generalization above is proven — a GPU-hosting/infra-cost
      business decision, not to build speculatively ahead of it. — **DONE / RULED 2026-08-06 (operator, interactive).**
      Ruling source: the same 2026-08-06 `/plan-reconcile ao` session recorded in
      `/plans/archive/2026_08/omniroute_multi_provider_routing_evaluation_2026_08_03.md` § "Phase 3 — decision", where
      the companion OmniRoute no-go was ruled — both are the same provider-strategy call. The evaluation happened:
      **"all these models were evaluated briefly on a few tasks."** **Outcome: Claude + DeepSeek only for now** — no
      self-hosted open-weight layer, no GPU hosting. The gate this todo was waiting on (the multi-provider
      generalization) is therefore moot for THIS decision; the operator answered the underlying business question
      directly rather than waiting for the abstraction.

      **Explicitly NOT a permanent no**, and the reason it needs no standing todo: per the operator, integrating a
                                                                  further model later is **"not going to be hard, maybe a few hours of work only."** A cheap, well-understood
                                                                  future option does not need to sit open in the corpus being re-audited every sweep — re-open this only when
                                                                  there is an actual decision to add a provider. **Do not re-file this as a follow-up**: closing it is the point.

- [x] [UI] P1. ✅ Surface DeepSeek's real dollar balance on the dashboard (available-balance-only design — DeepSeek's
      API exposes no spend/usage-history endpoint). — New `DeepSeekBalancePoller` (30-min cadence) +
      `deepseek_balance.py`; `AccountUsageRow`/`AccountView` gained balance fields; dashboard renders a
      `DeepSeekBalanceLine`. — `agent-orchestrator@8cc6a4f`, 27 new tests, full suite green (2322 passed).
- [x] [UI] P1. ✅ Operator-directed account pause/resume via the dashboard (bundled into the same commit as the balance
      todo). Reuses the pre-existing `account_status="disabled"` state (sticky, only `enable_account` clears it). — same
      commit, `agent-orchestrator@8cc6a4f`.
- [x] [BUG] P1. ✅ Live incident 2026-08-04 — the fleet-wide `is_pool_critically_exhausted` halt was
      Claude-only/provider-blind, starving a healthy funded DeepSeek pool behind a Claude-only 90% signal (519 queued, 1
      dispatched). Root-caused live by the main orchestrating agent after an operator report; fixed same-day. Full
      writeup: `plans/active/issues/autospawn_pool_critical_halt_starves_deepseek_2026_08_04.md`
      (`unified-trading-pm@a5e22fb398d7b19380ab2e94c08d59ef28a7b827`). Fix: the halt now also requires
      `_non_anthropic_pool_has_capacity` to be False. — `agent-orchestrator@3f06bea`, ahead=0. Also bumped
      `deepseek_route_fraction` 0.8→0.9 — `agent-orchestrator@d18e6830cbabd402345fe6bacb071fe24bb2e01e`.
- [x] [OPERATOR] P2. ✅ Top up the `deepseek-v4-pro` balance ($0.34 as of 2026-08-04T14:05Z). — Done: confirmed $4.84
      live via `/api/accounts` at 2026-08-04T14:33Z.
- [ ] [OPERATOR] P2. **Recurrence, found 2026-08-09 (slot 30, while re-sourcing the token below): `deepseek-v4-pro`
      balance is back to
      $0 — a live `claude -p` auth probe under this account returned `API Error: 402 Insufficient
      Balance` (confirmed via TWO separate probes: the pre-existing literal-token env file AND the GSM-indirection
      version, byte-identical error both times — so this is a genuine account-balance exhaustion, not an auth/token
      regression from the re-sourcing todo below). Same pattern as the 2026-08-04 top-up above (~$4.50
      spent in ~5 days) — top up again, ideally by enough margin to reduce recurrence frequency.** (repo: N/A, operator
      action)
- [x] ✅ [OPERATOR] P2. **DONE 2026-08-09 (operator, interactive ruling recorded in this same doc,
      `deepseek_claude_blended_provider_routing_2026_07_28.md`): "Yes, create it now".** Created live via the exact
      prepared command below: `deepseek-v4-pro-api-key` (project `central-element-323112`), version 1, confirmed via
      `gcloud secrets create` success. Operator can now delete the plaintext key from
      `~/.claude-accounts/deepseek-v4-pro.env` once the re-sourcing todo below lands. Raised P3 → P2 originally: this is
      a live API credential sitting in plaintext on two hosts, not housekeeping. **Ruled 2026-08-06 (operator,
      interactive, this doc's own `deepseek_claude_blended_provider_routing_2026_07_28.md` Progress Log): split of
      duties confirmed — the operator creates and names the secret; an agent then wires the re-sourcing** (next todo).
      Naming stays with the operator by this doc's original instruction ("do not guess a name"), and independently
      because an agent session may not hold `secretmanager` create permission. **Done when**: the secret exists and its
      exact resource name is recorded in this todo.

      **PREPARED 2026-08-08 (operator ruling, ao round-5 apply session item 19): "Operator will create it - needs
                                                  Claude to provide the exact secret name + gcloud/aws command to run."** Proposed name (matching this repo's
                                                  existing `{vendor}-api-key` GSM convention — see `tardis-api-key`/`databento-api-key`/`graph-api-key` in
                                                  `/codex/05-infrastructure/auth-setup.md`, extended with the account variant since DeepSeek now has 2 distinct
                                                  keys, pro + flash, per `deepseek_flash_ab_routing_test_2026_08_05.md`): **`deepseek-v4-pro-api-key`** (project
                                                  `central-element-323112`, matching every other secret cited above). Exact command (run on whichever host holds
                                                  the live literal key, currently `~/.claude-accounts/deepseek-v4-pro.env`'s `ANTHROPIC_AUTH_TOKEN` value — do
                                                  NOT paste the key into shell history; use the `-n`-into-stdin form or a temp file deleted after):
                                                  ```bash
                                                  gcloud config set project central-element-323112
                                                  echo -n "<the literal ANTHROPIC_AUTH_TOKEN value from ~/.claude-accounts/deepseek-v4-pro.env>" | \
                                                    gcloud secrets create deepseek-v4-pro-api-key \
                                                      --data-file=- \
                                                      --replication-policy=automatic
                                                  ```
                                                  If/when the flash account (`deepseek-v4-flash.env`, provisioned on the orchestrator VM per the A/B test plan's
                                                  todo 6, not present on this host) also needs GSM-sourcing, the matching name is **`deepseek-v4-flash-api-key`**
                                                  (same command, swap the secret name + source the flash env file's token instead). Once created, hand the exact
                                                  name(s) to an agent session to wire the re-sourcing (next todo) — no guessing needed, this doc already states
                                                  the name.

- [ ] [INFRA] P2. **Re-source `ANTHROPIC_AUTH_TOKEN` from the GSM secret on BOTH hosts** — this machine and the planning
      VM — so `~/.claude-accounts/deepseek-v4-pro.env` no longer contains the literal key. ~~BLOCKED on the operator
      todo above~~ **UNBLOCKED 2026-08-09**: the secret was created live (see the todo above), naming resolved.
      **Verified still open 2026-08-06** by direct file read: the env file contains no `gcloud secrets` / secret-manager
      indirection of any kind, i.e. the key is still literal — this half is unambiguously undone regardless of whether a
      secret has since been created. **Done when**: both hosts read the token via secret-manager indirection, a fresh
      spawn authenticates successfully, and the literal key is removed from both files. **➡️ EXTRACTED 2026-08-09 to
      `ao_satellite_ao_dispatch_batch14_2026_08_09.md` todo 1 — do NOT action here.** **Evidence appended 2026-08-09
      (slot 30) — DONE in batch14, checkbox left unflipped here per that plan's own rule (finalize plan reconciles):**
      "both hosts" was stale (only ONE VM exists post-2026-08-03 termination); the executing slot's own host IS the
      planning VM (verified via IMDSv2 instance-metadata), so one file fix (`~/.claude-accounts/deepseek-v4-pro.env`)
      covers it. Full verification method + the fresh $0-balance finding this surfaced: see batch14's flipped todo 1 and
      this doc's own new `[OPERATOR] P2` balance-recurrence todo above.

      > **⚠️ Measurement trap recorded 2026-08-06 — do not repeat it.** This todo's earlier line "Confirmed 2026-08-04:
                                                                  > no `deepseek*` secret exists in GSM yet" should be re-verified before being trusted. A 2026-08-06 attempt to
                                                                  > re-confirm it returned an empty list that looked like proof of absence but was **permission denial**: the
                                                                  > session identity (`github-actions-deploy@central-element-323112`) lacks `secretmanager.secrets.list` on
                                                                  > `central-element-323112`, `uts-prod`, and `unified-trading-system`, and `gcloud secrets list --filter=...`
                                                                  > exits 0 with no rows rather than erroring visibly when filtered. **Check the identity's permission before
                                                                  > reading an empty secret list as absence** — same class as the journald-retention trap recorded in
                                                                  > `/plans/active/issues/ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md`, where a `--since` predating
                                                                  > retention returned a confident zero that meant nothing.

- [x] [INFRA] P1. ✅ Durable per-task token usage (`TaskUsageRow`, any provider), persisted at `/done`. —
      `agent-orchestrator@b310c68`. Same-session follow-up: historical backfill script (dry-run default) +
      window-aggregated (1h/5h/24h/7d/lifetime) per-task-averaged dashboard view — `agent-orchestrator@5f6b20f`.
- [x] [INFRA] P1. ✅ Give workers a within-task turn/token compaction trigger. Turned out ALREADY SHIPPED same-day
      10:35, before this investigation started: `context_lifecycle.py` force-compacts every working slot unconditionally
      at 60% context — `agent-orchestrator@9747537d91dd4337f24a9c087c9dcd4d760b6abc`. Verified by re-reading the current
      file directly, not trusting a stale sub-agent claim of "workers excluded" (2 earlier proposals on this todo were
      retracted as a result — see Progress Log discipline note).
- [x] [DATA] P1. ✅ DeepSeek's `cache_read_input_tokens` discount confirmed real — operator-reported actual spend
      ≈$35 for the 16h/2.5B-token window matches the ~$22-25 implied by the published 120x hit/miss rate against the
      40%/40%/10% hit/miss/output dollar-share breakdown; a fake/near-full-rate discount would imply ~$1000+.
- [x] [INFRA] P2. ✅ Made `one_task_per_session_enabled` gate 1 sequential-plan-aware, scoped to `provider=="deepseek"`
      only (Claude's ~5min/1hr cache TTL makes the same skip a plausible net loss there; DeepSeek's disk cache verified
      to survive hours-to-days). — `agent-orchestrator@b310c68`.
- [x] [OPERATOR] P2. ✅ Run `backfill_task_usage.py --apply` on the orchestrator VM once the dry-run confirms sane
      numbers. — Blocked twice on the way, both found+fixed same session: (1) the unscoped full-history dry-run (3259
      candidates) didn't complete in a 1h SSM timeout — root cause a real O(candidates) perf bug
      (`find_slot_transcripts`/ `scan_session_usage` re-globbed/re-parsed per candidate with no caching); fixed via
      per-slot/per-file caching — `agent-orchestrator@ac02c79` — cut a `--since 2026-07-29` (1236 candidates) dry-run
      from >20min-incomplete to 39s. (2) `--apply` then hit a live schema-drift bug (`task_usage` missing the
      `backfilled` column on the real VM, `create_all_tables()` never alters an existing table) that turned out to ALSO
      be breaking `/done` fleet-wide — see `/plans/archive/2026_08/task_usage_schema_drift_done_outage_2026_08_05.md`
      for the full incident (fixed live via `ALTER TABLE`, plus a deeper isolation fix — `agent-orchestrator@7a7dd8d` —
      so a usage-write failure can never roll back `/done` again). **Final `--apply` run**: `matched=1236 unmatched=0`,
      verified live via `GET /api/backlog/usage/windows`: 1h=5 tasks/$0.47, 5h=54 tasks, 24h=269 tasks, 7d=1235 tasks,
      lifetime=1252 tasks (37.3M input / 234.5M cache-creation / 26.8B cache-read / 54.2M output tokens) — the
      dashboard's Task Usage Windows panel is now populated with real data end to end.
- [x] [INFRA] P3. ✅ **DONE — `agent-orchestrator@ae44244` (2026-08-14) shipped the runnable tool.**
      `agent-orchestrator/scripts/orchestrator/deepseek_flash_pro_split_readout.py` (lifecycle: permanent, per its own
      header markers) is exactly this instruction carried out: a read-only readout of the live flash-vs-pro split,
      driven by `account_id` rows in `activity_log` cross-referenced against each account's declared
      `AccountDef.variant` in `accounts.json` — its own docstring states verbatim that it satisfies this todo, and
      repeats the same measurement-trap warning ("the split is visible ONLY in `account_id`, not a distinct event
      name"). Verified live: `server/config.py`'s `deepseek_flash_route_fraction` field comment (still current,
      ~L1370-1386) still tells the next reader to "re-measure rather than trusting this block" — that instruction is now
      actionable via `python3 scripts/orchestrator/deepseek_flash_pro_split_readout.py [--hours N]` on the orchestrator
      VM. Original todo text (kept for context, not re-derived — the tool already exists): **Give
      `deepseek_flash_route_fraction`'s "re-measure rather than trusting this block" instruction an actual way to be
      carried out.** `server/config.py` (just above the field) tells the next reader to re-measure the
      flash-vs-non-flash split if they change the fraction — but no committed tool does that, so the instruction is
      currently unactionable and the next agent will re-derive the query from scratch, as this session did. The method,
      recorded here so it survives even if nobody writes the script (read-only, runs on the AO VM):

      ```sql
                      -- account_id distribution over spawns/dispatches, last 24h
                      -- DB: file:<repo>/agent-orchestrator/data/state/state.db?mode=ro   (open read-only; run as ubuntu)
                      SELECT json_extract(details_json,'$.account_id') AS a, COUNT(*) AS n
                      FROM activity_log
                      WHERE ts > datetime('now','-24 hours')
                        AND json_extract(details_json,'$.account_id') NOT IN ('')
                      GROUP BY a ORDER BY n DESC;
                      ```

                      Done when: either a small read-only readout script lands under `agent-orchestrator/scripts/orchestrator/` with a
                      lifecycle marker, or the config.py comment carries the query inline so "re-measure" names its own method. Note the
                      measurement trap found this session: the split is only visible in `account_id` on spawn/dispatch rows — event-type
                      greps for `deepseek`/`free_provider` return nothing useful, so an agent probing that way concludes the A/B is
                      inactive when it is running normally. Repo: agent-orchestrator.

- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — Prior verdict re-verified — content unchanged since the
  2026-08-06 marker. Of the 6 open items: 2 are operator-review pilots, 1 is a live-VM-only data check, 2 are
  operator-credential items (one blocked on the other), 1 is a design-judgment CLI-support fix. Note (not blocking this
  marker): this doc's `locked_by: live-defi-rollout` / `locked_since: 2026-05-21` predates its own `created: 2026-07-28`
  — the same bogus copy-paste-lock pattern this corpus already flags elsewhere (see
  `ao_open_issues_consolidated_close_out_2026_07_17.md`'s note on
  `ao_park_disposition_blocked_answer_no_follow_through`) — flagged for operator awareness, not acted on here since this
  is a Progress Log append, not an archival action.
- **na-eligibility-audit 2026-08-09 (round9)**: satellite-extraction, not whole-doc RECLASSIFY — the operator created
  the GSM secret `deepseek-v4-pro-api-key` this session (see the todo above), unblocking exactly ONE of the 5 remaining
  open items (the `[INFRA] P2` re-sourcing todo, whose sole blocker was "needs the secret's exact name"). Extracted to
  `ao_satellite_ao_dispatch_batch14_2026_08_09.md`. The other 4 items stay KEEP-NA, valid — unaffected by the credential
  fact: 2 operator-review production pilots (time-gated), 1 CLI-version design call, 1
  `accounts.json`-is-gitignored-per-VM data check. Whole-doc RECLASSIFY bar not cleared.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — prior verdict re-verified,
  content unchanged since round9. The re-sourcing todo remains correctly EXTRACTED (do not action here). Of the 4 items
  still open on this doc: 2 are operator-review production pilots (one time-gated week-long comparison, one needing a
  real Claude-headroom-dependent run this checkout cannot exercise), 1 is a CLI-version/design fix on a fleet-wide
  worker-boot-critical-path file, 1 is a data check explicitly "not locally doable — `accounts.json` is
  gitignored/per-VM." None bounded for a background worker today.

**2026-08-14 (bookkeeping pass) — `[INFRA] P3` remeasure-tool todo flipped, confirmed already shipped.**
`agent-orchestrator/scripts/orchestrator/deepseek_flash_pro_split_readout.py` (introduced
`agent-orchestrator@ae44244c7f3ae53f9b71c56411d1a4167612a65b`, "feat(scripts): add read-only flash-vs-pro DeepSeek A/B
readout script") is that tool — verified via its own docstring (states verbatim that it satisfies this exact todo, cites
this plan by path) and via `server/config.py`'s `deepseek_flash_route_fraction` field comment (~L1370-1386), which still
carries the "re-measure rather than trusting this block" instruction the script now makes actionable. No code changed
this pass — pure checkbox reconciliation.

## Phase 3 — GLM (Zhipu) onboarding + DeepSeek peak/off-peak pricing (2026-08-14)

**Why.** Same-session operator ruling (interactive, 2026-08-14): onboard GLM as a second fallback provider using the
SAME generalized `select_account_for_spawn()`/`AccountProvider` mechanism Phase 2 already built — GLM's Coding Plan
exposes a native Anthropic-compatible endpoint (`https://api.z.ai/api/anthropic`), so this is a config/registry
addition, not new mechanism, mirroring DeepSeek's own onboarding exactly. Separately: DeepSeek is changing its own
pricing structure to peak/off-peak at **2026-08-16T16:00:00Z** — confirmed directly from `api-docs.deepseek.com`
2026-08-14 (peak windows 01:00-04:00 UTC + 06:00-10:00 UTC = 7h/day; off-peak = exactly 50% of peak; **every off-peak
rate is still above today's pre-change price**, this is a net price increase, not a discount tier). Operator ruling:
disable DeepSeek entirely during its own peak window and route elsewhere automatically, rather than dispatch at 2x.
Every new provider gets a DeepSeek-style accurate-usage-capture proxy (operator instruction, 2026-08-14) — self-reported
numbers are not trusted by default, per this plan's own precedent (DeepSeek's compat endpoint under-reported before
`deepseek_native_proxy_server.py` was built to catch it). Routing stays simple for now — even split across all
registered providers/models, same pattern as the existing flash-vs-pro A/B (operator, 2026-08-14: "just route things
even split ... because I just want to get an idea of how well they complete things and also how much things cost ...
We'll calibrate everything").

**New exact DeepSeek rates** (USD/1M tokens, effective 2026-08-16T16:00:00Z):

|                           | Off-peak | Peak (exactly 2x off-peak) |
| ------------------------- | -------- | -------------------------- |
| V4-Flash cache-hit input  | $0.007   | $0.014                     |
| V4-Flash cache-miss input | $0.22    | $0.44                      |
| V4-Flash output           | $0.66    | $1.32                      |
| V4-Pro cache-hit input    | $0.022   | $0.044                     |
| V4-Pro cache-miss input   | $0.66    | $1.32                      |
| V4-Pro output             | $1.98    | $3.96                      |

**Non-goal (explicit):** GLM-5.2 and GLM-4.7-FlashX are pooled under ONE Coding Plan Max subscription ($160/mo, ~1,600
prompts/5h + 8,000/wk) — not metered pay-per-token API billing. Do not register a separate metered GLM rate card unless
the operator later decides to also run pay-per-token GLM alongside the subscription.

### Todos

- [ ] [OPERATOR] P1. Complete Z.ai GLM Coding Plan Max signup and hand over the API key + confirm the exact
      Anthropic-compatible base URL (`https://api.z.ai/api/anthropic`, per Z.ai's own Claude Code integration docs —
      verify still current at signup time). Done when: a real key exists and is handed to an agent session for
      registration.
- [ ] [INFRA] P1. Register the GLM Coding Plan account end to end mirroring the DeepSeek account pattern exactly: env
      file (`ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`, `unset CLAUDE_CODE_OAUTH_TOKEN`) + `accounts.json` entry +
      GSM secret `glm-coding-plan-api-key` (new naming-SSOT entry, `/codex/05-infrastructure/secret-manager-naming.md`
      §2.7 has no LLM-provider-key convention yet — add one while here, matching the `{vendor}-api-key` pattern already
      used for `deepseek-v4-pro-api-key`). Done when: `AUTH_OK` verified via a real smoke `claude -p` call and
      `/api/accounts` shows `status: healthy`.
- [ ] [INFRA] P1. Extend `AccountProvider` Literal to add `"glm"`. Register two model variants via the existing
      `variant` field pattern (same mechanism as DeepSeek's pro/flash split): `glm-5.2` (flagship) and `glm-4.7-flashx`
      (fast/cheap), both reachable under the one Coding Plan credential. Done when: QG green, routing tests extended to
      cover the new provider value (mirrors `test_deepseek_provider_routing.py`).
- [ ] [DATA] P1. Add GLM `RateCard` entries to `model_pricing.py`: GLM-5.2 ($1.40 input / $4.40 output /
      $0.26 cached
      input — 81% cache discount, confirmed) and GLM-4.7-FlashX ($0.07 input /
      $0.40 output — cache rate NOT published
      anywhere found; verify against the live API response's `usage.prompt_tokens_details.cached_tokens` field at
      registration, do not hardcode a guessed number). These are informational rates for cost-tracking only — actual
      billing is the flat $160/mo
      subscription, not these per-token numbers; `price_usage()` still needs them to compute the
      metered-equivalent-value comparison the reconciliation todo below produces. Done when: `price_usage()` returns
      non-None for both models against a real captured usage sample.
- [ ] [INFRA] P1. Build GLM's accurate-usage-capture proxy, mirroring `deepseek_native_proxy_server.py`: verify GLM's
      Anthropic-compatible endpoint reports real usage (input/output/cache-read/cache-write) before trusting it directly
      — DeepSeek's own compat endpoint under-reported 2.5-3.2x before this was caught. If GLM under-reports the same
      way, add the same kind of intercepting translation layer; if it reports accurately, document that finding instead
      of building unneeded infra. Done when: a dated comparison of captured-vs-Z.ai-dashboard usage for a real sample of
      turns is recorded, with a stated tolerance.
- [ ] [UI] P2. Surface GLM's subscription-quota usage reusing the SAME `five_hour_pct`/`weekly_pct` fields Claude
      already uses (GLM Coding Plan Max's 1,600/5h + 8,000/wk shape is structurally identical to Claude's tier system) —
      GATE dispatch on it in `_pick_headroom_account()`/`select_account_for_spawn()`, not just display it. Done when: a
      simulated-near-ceiling test shows the account excluded from selection, same proof standard as Claude's existing
      headroom exclusion.
- [ ] [DATA] P2. Build a heuristic reconciliation pass that infers any unpublished multiplier (e.g. GLM-4.7-FlashX's
      cache-read rate, whatever the live API doesn't disclose for Grok/Gemini either — reused by the sibling Grok/Gemini
      plan) from real observed usage vs billed spend, mirroring the existing DeepSeek cache-discount verification (this
      plan's 2026-08-04 Progress Log: operator-reported ≈$35 actual spend matched the
      ~$22-25 implied by the
      published hit/miss ratio). Done when: a documented, derivation-shown heuristic rate lands in `model_pricing.py`
      for any provider/model missing a published number, with the derivation cited inline.
- [x] [INFRA] P0. ✅ Implement time-window-aware peak/off-peak pricing for DeepSeek: one shared hour-of-day utility used
      by BOTH `model_pricing.py` (which rate applies right now) and `autospawn.py` (is DeepSeek dispatch-eligible right
      now) — not two separate implementations of the same check. New `RateCard` entries for both peak and off-peak, both
      models, `effective_from=2026-08-16`. — `agent-orchestrator@07bca2954f`, 19 new tests, full suite green (3717
      passed). Self-review caught and fixed a real bug before shipping: a precise pre-16:00-UTC timestamp on the cutover
      date itself was resolving to the new off-peak rate instead of staying on the old flat rate — regression test added
      (`test_resolve_priced_model_key_precise_time_before_actual_cutover_instant_stays_old_rate`).
- [x] [INFRA] P0. ✅ Wire the same peak/off-peak time-window check into DeepSeek's dispatch eligibility inside
      `select_account_for_spawn()`: during DeepSeek's peak window, exclude it from the fallback pool entirely and fall
      through to the next-priority free provider. — `agent-orchestrator@07bca2954f` (same commit as above), verified via
      `test_deepseek_skipped_during_its_own_peak_window`/`test_deepseek_available_during_its_own_offpeak_window`/
      `test_deepseek_not_gated_before_the_peak_offpeak_cutover`.
- [ ] [REVIEW] P2. After GLM + the peak/off-peak gate are live ~1 week, compare real measured cost-per-task and
      completion quality across DeepSeek (off-peak only), GLM, and the Claude baseline — the "get an idea of how well
      they complete things and how much things cost" calibration the operator asked for (2026-08-14). Done when: a dated
      Progress Log entry with real per-provider $/task and quality numbers lands, informing whether the even-split
      default should shift.

- **2026-08-14 (later, separate session) — Gemini auth/billing findings, cross-reference only, not owned here.** This
  plan's Phase 2 background text lists Gemini among candidate providers for the generalized `AccountProvider` set (never
  implemented for Gemini specifically — that's the sibling plan below). A same-day session independently verified real
  Gemini auth/tiering mechanics: `generateContent` 404s are per-retired-model-name, not an API-surface problem; a GCP
  project's free-vs-paid tier is binary and project-scoped (billing-enabled = no parallel free bucket, full stop); and a
  newly-found failure mode where a project's billing can look fully healthy in every config read yet still have every
  paid call denied by Google's internal payment-dunning gate (confirmed live on the org's shared
  `central-element-323112` project). Full findings + an actionable pre-flight todo land in
  `/plans/active/grok_gemini_translation_proxy_2026_08_14.md`'s Progress Log, which owns Gemini onboarding.
