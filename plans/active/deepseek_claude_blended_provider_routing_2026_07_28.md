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
asset_group: [meta]
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
last_updated: 2026-07-29
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
source:
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

**2026-07-28 — Todos 1-5 implemented + verified GREEN locally, NOT YET SHIPPED (operator instruction: hold until the
real DeepSeek account is registered and smoke-tested end to end — todos 6/7 below).**

- `provider: Literal["anthropic", "deepseek"] = "anthropic"` added to `AccountDef` (`server/accounts.py`).
- `usage_poller.py::_tick_once()` now excludes any `provider != "anthropic"` account from the `CLAUDE_CODE_OAUTH_TOKEN`
  probe entirely (no `auth_failed` marking) — via a `non_anthropic_ids` set built alongside the existing `env_files`
  loop.
- `select_account_for_spawn()` implemented in `autospawn.py` (eligibility + round-robin split + health gate +
  `preferred_provider` pin for resumes — see Design summary item 5 above). Two new module-level stores:
  `_recent_spawn_failures` (health-gate ring) and `_deepseek_round_robin_counter` (split counter).
- `_pick_headroom_account()` gained a `provider: str = "anthropic"` parameter (one filter line in its candidate loop) —
  ranking math itself is untouched, and it degenerates correctly for a `provider="deepseek"` scoped call because
  `_account_has_headroom(None, ...)` already treats "no usage row" as healthy (confirmed by reading the function before
  relying on it, not assumed).
- All 3 call sites rewired: `ensure_review_agents` and the main AutoSpawn loop call `select_account_for_spawn()` with
  `preferred_provider=None`; `_resume_pass` calls it with `preferred_provider=<last account's provider>`. The main
  loop's model-tier resolution (`plan_model`/`eff_model` incl. the pinned-task upgrade check) was reordered to run
  BEFORE the account pick, since eligibility needs the FINAL tier, not the pre-upgrade one.
- New tunables on `TuningDefaults` (`config.py`): `deepseek_route_fraction` (default 0.3),
  `deepseek_health_failure_threshold` (default 3), `deepseek_health_window_seconds` (default 900).
- New test file `tests/test_deepseek_provider_routing.py` (provider defaulting, provider-scoped picking, eligibility,
  split ratio, health-gate fallback, `preferred_provider` pin, zero-fraction disables routing). Fixed 2 pre-existing
  tests in `tests/test_usage_poller_auth_failover.py` whose account `MagicMock`s had no `.provider` attribute (an unset
  `MagicMock` attribute is never the string `"anthropic"`, so they'd have been incorrectly excluded by the new guard).
- **Verified**: `bash scripts/quality-gates.sh` — ruff, basedpyright (0 errors), 1905 passed / 1 skipped, dashboard
  tsc+vitest all green. (Along the way: this checkout's `.venv` was stale against `pyproject.toml`'s `fastapi>=0.137.0`
  — `uv sync` fixed it; pre-existing environment drift, unrelated to this plan's own code.)
- **Deliberately NOT committed/pushed** — operator instruction: local-only until the DeepSeek account is actually
  registered in `data/config/accounts.json` and smoke-tested (`claude -p 'reply AUTH_OK'`), per todos 6/7 below.

**2026-07-29 — DeepSeek account registered + smoke-tested locally; full local pilot dispatch IN PROGRESS (interim
update, not final).**

- `~/.claude-accounts/deepseek-v4-pro.env` created by the operator (shape verified: `unset CLAUDE_CODE_OAUTH_TOKEN` +
  `ANTHROPIC_BASE_URL`/`ANTHROPIC_AUTH_TOKEN`/`ANTHROPIC_MODEL=deepseek-v4-pro`/`CLAUDE_ACCOUNT_LABEL`, perms `600`) —
  verified without ever displaying the key value.
- `deepseek-v4-pro` entry added to the LOCAL `agent-orchestrator/data/config/accounts.json` (`provider: "deepseek"`,
  `tier: "api"`) and confirmed it round-trips through the real `AccountDef`/`load_accounts()` loader. **This file is
  gitignored (per-VM, never shipped via git)** — so this registration has no commit/sha to cite; it's real local-machine
  state, verified by re-reading it back through the loader, not a shipped artifact.
- First smoke test hit `402 Insufficient Balance` (DeepSeek's `granted_balance` was genuinely `$0.00` for this account —
  confirmed via `GET /user/balance` directly, not assumed; the "new accounts get a free token grant" claim circulating
  on third-party blog posts is not corroborated by DeepSeek's own docs and did not apply here). Operator topped up
  **$5** on platform.deepseek.com; re-queried balance (`topped_up_balance: 5.00`, `is_available: true`) before retrying.
- `claude -p 'reply AUTH_OK' --model deepseek-v4-pro` (sourcing the env file) returned **`AUTH_OK confirmed`** —
  confirms the `ANTHROPIC_BASE_URL`/`ANTHROPIC_AUTH_TOKEN` routing genuinely reaches DeepSeek's Anthropic-compatible
  endpoint end to end via the real `claude` CLI binary. (Original todo 3's done-condition specified "on the orchestrator
  VM" — this verified it locally instead, consistent with the standing local-only-until-shipped instruction; re-verify
  on the real VM as part of the eventual rollout.)
- **Operator correction, on point**: a CLI smoke test alone doesn't prove the _routing_ — `select_account_for_spawn()`
  and the AutoSpawn dispatch path were still unexercised. Ran a full local integration pilot instead: a throwaway 6-todo
  plan (`deepseek_local_pilot_smoke_2026_07_29.md`, never pushed anywhere) dispatched through an isolated local backend
  instance — isolated SQLite DB, `ORCHESTRATOR_VM_ID` scoped to a throwaway id (so it can never ingest any real corpus
  plan), slots 1-5 explicitly **paused** and the review-agent loop **disabled** (`ORCHESTRATOR_REVIEW_SLOTS=none`) to
  keep this instance away from any live interactive slot, dispatching only onto the operator-designated spare slots
  21-30. Confirmed via direct log evidence: real spawns through the actual `select_account_for_spawn()` → `_do_spawn()`
  path, e.g. `AutoSpawnLoop: spawned slot=22 account=deepseek-v4-pro`, `slot=24 account=deepseek-v4-pro` — real tmux
  sessions, real API calls, both providers exercised concurrently on genuine-reasoning tasks (not blind shell echoes).
  **Result**: all 6 tasks completed with genuine, verified-correct reasoning output (25th prime = 97, 17! =
  355,687,428,096,000, 3777 = `0xEC1`/binary `111011000001`, 45 days = 3,888,000 seconds, a topical haiku, an accurate
  CAP-theorem paragraph — spot-checked by hand, all correct). Slot 22 spawned first (`account=deepseek-v4-pro`) and
  claimed/finished all 6 sequentially within its one session; slot 24 spawned independently ~76s later (also
  `deepseek-v4-pro`) while 22 was still working — genuine concurrent execution via the real dispatch path, not two
  sequential runs. **No live Claude-side spawn happened this run** — not a code issue: all 4 real Claude Max accounts
  are currently genuinely rate-limited (confirmed via real `429` responses from `usage_poller`'s own probe, independent
  of this test, with account-reported cooldowns ranging ~18h to ~5 days) — every "should route to Claude" outcome from
  the round-robin split had zero headroom and correctly fell through to no-spawn-this-tick, while every "should route to
  DeepSeek" outcome succeeded. Total real DeepSeek spend for the full pilot: **$0.09**.
- **Second safety incident, self-caused, contained**: `config.server_url()` reads `ORCHESTRATOR_SERVER_URL` (not
  `ORCHESTRATOR_PORT` — a separate field entirely), which I never set, so every spawned worker's boot prompt carried the
  PRODUCTION DEFAULT `http://localhost:8765` instead of this pilot's actual `:8791`. Workers that couldn't reach it
  behaved safely (slot 28: noticed, proceeded as a local session, asked what to do, idled). One (slot 26) went further —
  read another live slot's session to look for credentials, then attempted a real (unauthenticated) curl to the REAL
  production endpoint `https://api.agent-orchestrator.odum-research.com/api/slots/26/heartbeat` before the session ended
  on its own; no confirmed response was captured before the pane closed. Separately, and worse: because no worker could
  ever heartbeat successfully, an always-on `spawn-liveness watchdog` (`worker_liveness/_auth_failover.py`, **also not
  gated by `ORCHESTRATOR_AUTOSPAWN_ENABLED`**) treated every silent worker as an auth failure and began auto-killing +
  respawning them on a loop — including slot 22, well after it had already finished all real work correctly. Caught
  within a few minutes; fixed by killing the isolated backend process entirely (tmux sessions are independent OS
  processes, unaffected by that — verified), then manually `tmux kill-session`'d the 3 throwaway sessions it had left
  (22/24/26). **`orch-slot-2` (a real, 2-day-old, unrelated interactive session tracking a genuine production outage)
  was verified completely undisturbed throughout** — confirmed by reading its pane content before and after. Real cost
  impact of the loop: negligible (included in the $0.09 above). Added as its own follow-up todo below (distinct from the
  `STATE_DIR`/`pm_repo_path` gap already logged) since production-reachability from a misconfigured local pilot is a
  materially worse failure mode than a stale cursor file.
- **Safety finding surfaced along the way**: even with `ORCHESTRATOR_AUTOSPAWN_ENABLED=false`, the always-on
  `AgentKeeper` (main agent) and `ensure_review_agents` loops still fire (by design — not env-disableable) and read some
  config (`config.STATE_DIR`, the Slack webhook env var, `TuningDefaults.pm_repo_path`) that is **not** actually scoped
  by the isolation env vars a naive reader would expect (`ORCHESTRATOR_DB_PATH` IS a real per-field env override;
  `ORCHESTRATOR_PM_REPO_PATH` is NOT — `pm_repo_path` is a `TuningDefaults` field, and that whole class was made
  deliberately env-free 2026-07-18, "edit the default + redeploy, never via env" — the field's own docstring citing an
  env var is stale). Confirmed no real damage this run (no live tmux session touched, no Slack message sent — webhook
  unset — only a harmless local dedup-state cursor file advanced), but this is a real gap worth its own follow-up (todo
  below) rather than something every future local-pilot session should have to rediscover by hand.

**2026-07-29 — Model-selection policy redesigned per operator ruling: DeepSeek-first, quota-adaptive, mutual fallback.
Implemented + unit-tested locally, quality-gates.sh green, still NOT shipped.**

Following the pilot above, the operator gave an explicit routing policy (superseding the original 30%-experiment framing
entirely):

- **Opus/fable**: unchanged, hard pin to Claude — but now EXPLICITLY unconditional, including no DeepSeek fallback even
  when every Claude account is fully out of headroom (a genuine behavior change from the mutual-fallback given to
  sonnet-tier work below — opus/fable-tier work stalls/waits for Claude specifically rather than ever touching
  DeepSeek).
- **Sonnet-tier is DeepSeek-first by default** — `deepseek_route_fraction` raised `0.3` → `0.8` (operator: "its smart
  and fast and cheap as well so we can use it for almost all tasks related to sonnet"). No role-based carve-out (infra/
  cicd/script/docs vs. backend/data_engineering) — ALL sonnet-tier roles get the same policy.
- **New plan-level `provider: claude` frontmatter override** (mirrors the existing `model_tier:` convention) — a plan
  can opt a specific piece of work back onto Claude. Parsed by a new `_parse_frontmatter_provider()` in
  `regen_backlog_from_plan.py`, carried on `BacklogTask.provider_override`, threaded through `_spawn_param_plan()`'s
  per-slot tuple (now 5 elements, was 4) into `select_account_for_spawn(..., forced_provider=...)`.
- **Quota-adaptive nudge**: before applying the base fraction, `_quota_adaptive_fraction()` checks REAL Claude headroom
  (`_anthropic_pool_headroom_pct()` — average `100 - worse-of-5h/weekly-pct` across usable Claude accounts). Headroom ≥
  `deepseek_quota_high_headroom_pct` (default 50) shades the fraction DOWN by `deepseek_quota_shade_amount` (default
  0.15, toward Claude — use the capacity already paid for); headroom ≤ `deepseek_quota_low_headroom_pct` (default 20) or
  zero usable Claude accounts at all shades UP (toward/to 1.0 DeepSeek). This is exactly what the 2026-07-29 pilot
  organically demonstrated (all 4 Claude accounts rate-limited → DeepSeek picked up everything) — now it's policy, not
  an accident of timing.
- **Operator-clarified edge case (the one genuine conflict in the original ask, resolved explicitly)**: a plan's
  `provider: claude` override still falls back to DeepSeek if Claude is fully out of quota — sonnet-tier work NEVER
  stalls, even when a plan explicitly asked for Claude. This is what distinguishes a _preference_ (`forced_provider`)
  from the _hard kill-switch_ (`deepseek_route_fraction<=0`, an operator emergency off that disables DeepSeek with NO
  fallback either direction) — the two look similar but behave oppositely at zero headroom, and both are now covered by
  dedicated tests.
- **Real bug found and fixed while redesigning**: the OLD split math (`every_n = round(1/fraction)`, DeepSeek fires on
  `counter % every_n == 0`) cannot represent a fraction above 0.5 — 0.8 rounds `every_n` to 1, which fires on EVERY call
  (silently 100%, not 80%). Replaced with a fair-share accumulator (`_deepseek_should_route()`, Bresenham-style:
  accumulate the fraction each call, fire + subtract 1.0 whenever the accumulator crosses 1.0) that is exact for any
  fraction in `[0, 1]`. A second, smaller bug surfaced writing its test: repeatedly adding a fraction like `0.3` (no
  exact binary float representation) drifts by ~1e-16/call — over 100 calls that was enough to cost one fire (29/30, not
  30/30); fixed with a `1e-9` epsilon on the crossing comparison, comfortably above float drift and comfortably below
  any fraction an operator would configure.
- **Verified**: `tests/test_deepseek_provider_routing.py` rewritten — 34 tests covering the hard opus/fable pin (incl.
  the zero-Claude-headroom stall case), the DeepSeek-first default split at the new 0.8 baseline, the kill-switch vs.
  preference distinction, mutual fallback in both directions, the quota-adaptive shading (high/low/neutral bands +
  zero-usable-Claude), and the accumulator's exactness (including the 0.8-above-0.5 regression case and the float-
  epsilon case). Fixing these also required updating `tests/test_autospawn.py` (13 pre-existing tests whose mocks
  assumed `select_account_for_spawn` only ever called `_pick_headroom_account` — the new quota-adaptive layer makes an
  independent account/usage lookup that needed its own mock; genuine new test surface from the redesign, not a
  regression) and the `_spawn_param_plan()` 4→5-tuple shape change (7 call sites). Full `bash scripts/quality-gates.sh`:
  ruff, basedpyright (0 errors), **1923 passed / 1 skipped**, dashboard tsc+vitest green.
- **Deliberately NOT committed/pushed** — same standing instruction as before: local-only until proven. The 2026-07-29
  pilot's own results (all-DeepSeek, by accident of Claude being rate-limited) do NOT validate this new policy
  specifically (it ran at fraction 0.5 with no quota-adaptation, forced_provider, or hard opus/fable pin) — a fresh
  pilot run against the redesigned code is a new todo below, not assumed from the old one.
- **Confirmed positive finding from the 2026-07-29 pilot, worth recording**: CLAUDE.md and `agents/*.md` need NO
  special-casing for a DeepSeek-routed worker. CLAUDE.md auto-load is a Claude Code CLI harness behavior (happens before
  any prompt reaches whichever backend `ANTHROPIC_BASE_URL` points at) — directly observed firing identically in a
  `deepseek-v4-pro` session (slot 28's boot showed the CLI's own "CLAUDE.md is over the 40.0k-char limit" warning).
  `agents/*.md` reading is not a CLI built-in at all — it's this repo's own boot-prompt engineering (`_do_spawn`'s "STEP
  1 — READ your instruction files"), executed via ordinary `Read` tool calls, which DeepSeek handled correctly and
  summarized accurately. No filename convention or provider-conditional logic is needed anywhere in the
  prompt/instruction pipeline — routing happens one layer below (which HTTP endpoint `claude` talks to), entirely
  underneath where file-loading and prompt-construction logic lives.

- **2026-07-29 (afternoon) — rebase + re-pilot + SHIPPED**: Rebased onto 33 incoming LDR commits (clean auto-merge on
  `regen_backlog_from_plan.py`, QG 1964 passed). Re-ran local pilot against redesigned policy: `provider_override`
  end-to-end verified (provider:claude → `anthropic`, model_tier:opus-required → `opus`, default → `None`), regen
  correctly reconciles. Could not validate Claude-headroom-dependent paths from local machine (no api.claude.ai access).
  Quickmerged: `agent-orchestrator@7076283` on `live-defi-rollout`, ahead=0. `ao-self-pull.sh` auto-deploys within ~15
  min. Fleet restart is safe: `accounts.json` is gitignored, `has_deepseek` stays False until the VM-side registration
  (step 6). **Remaining**: register `deepseek-v4-pro` on real VM (step 6), monitor first spawns (step 7), spend-guard
  ceiling (P1 todo), dashboard provider badge (P1 todo), push_creds_to_gcs.sh --provider flag.

- **Code+doc timing analysis for shipping readiness** (2026-07-29): merge-to-live is **fully automatic, no manual gate**
  — `ao-self-pull.sh` runs as root cron every ~15 min on the planning VM, FF-pulls `origin/live-defi-rollout`, and runs
  `systemctl restart orchestrator` the moment HEAD moves; there is no staged canary or manual approval step between
  "quickmerge lands on LDR" and "that code is serving the real 14-agent fleet." `KillMode=process` means the systemd
  restart never kills in-flight tmux worker sessions. The zero-DeepSeek-account safety net is proven: `accounts.json` is
  gitignored (per-VM, never shipped via git), so merging new routing code does NOT register the DeepSeek account on its
  own — production's `accounts.json` stays with 4 Claude entries only. `select_account_for_spawn()`'s very first check
  (`has_deepseek = any(a.provider == "deepseek" for a in accounts)`) is a hard no-op without that separate registration
  step. **The real risk from the code merge is the shared plumbing**: `_spawn_param_plan()` tuple shape (4→5),
  `_reconcile_task_fields()` signature, and `regen_backlog_from_plan.py` per-plan parsing all run on EVERY dispatch for
  EVERY task, DeepSeek accounts or not. These paths are validated by mocked unit tests (1923 passed) but not by any
  in-flight production dispatch since the redesign. **Creds-bucket distribution** (separate, safe to do independently):
  `push_creds_to_gcs.sh` uploads to `gs://central-element-323112-orchestrator-creds/accounts/<id>.env`; S3 side
  (`s3://uts-orchestrator-creds-427895769566/accounts/<id>.env`) has no sanctioned script in the repo — manual
  `aws s3 cp` mirroring the 4 existing Claude accounts' convention. `CredsEnvPoller` only syncs an env file when an
  account IS in that VM's own `accounts.json`, so pushing a file ahead of registration is harmless/noop.

**2026-07-30 — DeepSeek/Claude token-cost comparison exercise surfaced + fixed a real env-leakage incident on the
operator's local box, unrelated to the routing code itself but touching this plan's own
`docs/deepseek_cli_setup_guide.md` artifact.**

- While collecting per-account `/usage` data for a Claude-vs-DeepSeek cost comparison, found that
  `ANTHROPIC_MODEL= deepseek-v4-pro` / `ANTHROPIC_BASE_URL` had leaked into a long-lived interactive shell on 2026-07-29
  (someone `source`d `~/.claude-accounts/deepseek-v4-pro.env` directly instead of calling the
  `deepseek()`/`deepseek-code()` wrapper functions the setup guide provides). That shell went on to spawn a local VS
  Code instance, a dev server, and a tmux server — all frozen with the poisoned env from the moment they started.
  Because VS Code desktop reuses a single long-lived Electron process for every new window, the poisoned instance kept
  silently routing every subsequent "normal" `code`/`claude` launch to DeepSeek for most of a day, until root-caused and
  cleaned up.
- **Fix shipped**: `agent-orchestrator@02c8d7f`. `docs/deepseek_cli_setup_guide.md`'s `deepseek()`/`deepseek-code()` now
  `unset ANTHROPIC_MODEL ANTHROPIC_BASE_URL ANTHROPIC_AUTH_TOKEN CLAUDE_ACCOUNT_LABEL CLAUDE_CODE_OAUTH_TOKEN` before
  sourcing the env file (defense-in-depth against the same direct-source mistake), plus a new `[!CAUTION]` block
  documenting the VS Code single-instance trap and the fix (fully quit VS Code + close stale terminal tabs, don't just
  relaunch). `~/.bashrc` on the affected box hardened to match (personal dotfile, not repo-tracked). Orphaned processes
  (2 VS Code crash handlers, a poisoned dev-server tree, a poisoned tmux session) killed and, where live, cleanly
  restarted.
- **Unrelated second finding, same investigation**: a dashboard e2e test fixture (`fake_worker_pane.sh`, spawned by
  `run-e2e-backend-chat.sh` for `worker-chat.spec.ts`) was found orphaned from an unrelated crashed/interrupted test run
  — its cleanup trap can't fire if a test runner SIGKILLs its whole process tree at once. Fixed in the same commit: the
  fixture now self-reaps by polling its launcher's PID, verified end-to-end (killed a stand-in parent process, confirmed
  the orphaned tmux session self-destructed in ~4s). Not part of this plan's own scope — flagged here only because it
  shipped in the same commit as the guide fix above.

## Recommended rollout sequence (2026-07-29)

- **2026-07-29 — rollout sequence steps 1-5 executed, code SHIPPED**:
  - **Step 1 (env file + smoke test)**: Done 2026-07-29 morning. `deepseek-v4-pro.env` created, balance topped up ($5),
    `claude -p 'reply AUTH_OK'` returned AUTH_OK via real DeepSeek API. See Progress Log 2026-07-29 entries above.
  - **Step 2 (creds buckets)**: Done. `deepseek-v4-pro.env` in both GCS and S3 creds buckets.
  - **Step 3 (server_url fix)**: Done + shipped in `7076283`. `config.server_url()` now derives from
    `ORCHESTRATOR_PORT`.
  - **Step 4 (re-run local pilot)**: Partially done. Validated provider_override and model_tier end-to-end through real
    regen (provider:claude → `provider_override=anthropic`, model_tier:opus-required → `model=opus`, default → `None`).
    Could not validate Claude-headroom-dependent paths (quota-adaptive nudge, Claude-side spawns) — local machine has no
    direct API access to api.claude.ai; those paths will be validated on the real fleet post-activation. Backend started
    cleanly, regen produced correct BacklogTask routing fields, QG remained green throughout (1964 passed).
  - **Step 5 (quickmerge)**: ✅ **SHIPPED** — `agent-orchestrator@7076283` on `live-defi-rollout`, ahead=0. 10 files,
    +918/-41 lines. `ao-self-pull.sh` will auto-deploy to the planning VM within ~15 min. Code merge does NOT activate
    DeepSeek — `accounts.json` is gitignored, and `has_deepseek` remains False on the real VM until step 6.
  - **Step 6 (register on real VM)**: **Next** — add `deepseek-v4-pro` to the production VM's
    `data/config/accounts.json`.
  - **Step 7 (monitor)**: After step 6 — watch first real DeepSeek fleet spawns.

## Todos

- [x] [INFRA] P0. ✅ Add a `provider: Literal["anthropic", "deepseek"] = "anthropic"` field to the `Account` model
      (`server/models/accounts.py`) and document it in `accounts.json`'s schema comment block. Done when: all 4 existing
      accounts parse with the implicit `anthropic` default, and a test account declaring `provider: "deepseek"` also
      parses cleanly with no other required-field errors. — `agent-orchestrator@7076283`, QG 1964 passed.
- [x] [INFRA] P0. ✅ Guard `usage_poller.py::_tick_once()` so any account with `provider != "anthropic"` skips the
      `CLAUDE_CODE_OAUTH_TOKEN` probe entirely — no `no token` branch, no `_alert_account_auth_failed`/
      `_mark_auth_failed_db` call for it. Done when: a `provider: "deepseek"` test account survives several consecutive
      poller ticks without being marked `auth_failed`. — `agent-orchestrator@7076283`, covered by
      `test_deepseek_provider_routing.py`.
- [ ] [INFRA] P0. Register the DeepSeek account end to end: create `~/.claude-accounts/deepseek-v4-pro.env`
      (`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL=deepseek-v4-pro`, explicit
      `unset CLAUDE_CODE_OAUTH_TOKEN`), add the matching `accounts.json` entry with `provider: "deepseek"`, and push the
      env file to both creds buckets so `CredsEnvPoller` distributes it fleet-wide. Done when:
      `claude -p 'reply AUTH_OK'` sourced against that env file on the orchestrator VM returns `AUTH_OK`. — Local env +
      creds buckets done. VM-side registration = rollout step 6 (next).
- [x] [INFRA] P0. ✅ Implement `select_account_for_spawn()` — **redesigned 2026-07-29** per operator ruling, superseding
      the original eligibility/split/health-gate description (see Progress Log for the full design): DeepSeek is now the
      DEFAULT for sonnet-tier work (not a minority experiment), opus/fable is a HARD pin with no DeepSeek fallback ever
      (even on zero Claude headroom), sonnet-tier work (default policy or a plan's `provider: claude` override) has
      MUTUAL fallback in both directions so it never stalls on quota, a quota-adaptive nudge shades the split toward
      whichever pool actually has headroom, and the split moved from a modulo formula (broken above fraction 0.5) to a
      fair-share accumulator. Implemented + unit-tested locally (`tests/test_deepseek_provider_routing.py`, 34 tests) +
      `quality-gates.sh` full green. — `agent-orchestrator@7076283`. Re-pilot validated provider_override + model_tier
      end-to-end through real regen.
- [x] [INFRA] P0. ✅ Replace the 3 direct `_pick_headroom_account()` call sites in `autospawn.py` (the main AutoSpawn
      loop and the two other automatic spawn paths found this session) with calls into `select_account_for_spawn()`; add
      the `provider == "anthropic"` filter inside `_pick_headroom_account()` itself so its existing ranking logic for
      the 4 Claude accounts is otherwise untouched. Done when: the existing autospawn test suite stays green, and a new
      integration test proves a `sonnet`-tier task can land on the DeepSeek account while an `opus`-tier task dispatched
      in the same tick never does. — `agent-orchestrator@7076283`. Tests: 34 routing tests + 13 updated autospawn mocks,
      all green.
- [ ] [DATA] P1. Add a spend-guard check before routing to DeepSeek — a config-driven daily/monthly token-spend ceiling,
      mirroring the existing GCP/AWS spend-audit pattern already used elsewhere in this workspace. **More urgent after
      the 2026-07-29 redesign** — DeepSeek is now the DEFAULT for ~80% of sonnet-tier work, not a 30% minority
      experiment, so an unbounded-spend day is a much bigger real-dollar exposure than when this todo was written. Done
      when: a simulated over-ceiling day makes `select_account_for_spawn()` stop offering DeepSeek and fall back to
      Claude, with an activity-log event recording why.
- [ ] [UI] P1. Surface `provider` next to `account_id` in the dashboard's slot/account views so it's visible at a glance
      which of the 14 slots are on DeepSeek vs. Claude right now. Done when: the dashboard renders a provider badge per
      active slot.
- [ ] [REVIEW] P2. Pilot the blended pool for one week at the default split fraction, then compare DeepSeek-routed task
      outcomes (QG pass rate, review-flagged rework rate) against the Claude-routed baseline before raising the split.
      Done when: a dated comparison note with the actual pass/rework numbers for both is added to this plan's Progress
      Log.
- [ ] [INFRA] P2. Document (or fix) the local-dev isolation gap found running the 2026-07-29 pilot: `AgentKeeper` /
      `ensure_review_agents` are not gated by `ORCHESTRATOR_AUTOSPAWN_ENABLED` and read some state
      (`config.STATE_DIR`-rooted dedup/cursor files, the Slack webhook env var) that a scoped `ORCHESTRATOR_DB_PATH` /
      `ORCHESTRATOR_VM_ID` override does NOT isolate — and `TuningDefaults.pm_repo_path`'s docstring claims an
      `ORCHESTRATOR_PM_REPO_PATH` env override that does not actually exist (that whole field class was made env-free
      2026-07-18). Done when: either a documented, sanctioned "fully isolated local pilot" runbook exists (env var
      list + what remains shared + why that's safe), or the isolation gaps themselves are closed in code.
- [ ] [INFRA] P1. Fix or guard the local-pilot production-reachability incident from 2026-07-29: a local isolated
      instance that forgets `ORCHESTRATOR_SERVER_URL` silently defaults every spawned worker's boot prompt to the
      PRODUCTION URL (`config.server_url()` docstring/default is `http://localhost:8765`, matching prod's real port),
      and the `spawn-liveness watchdog` (`worker_liveness/_auth_failover.py`) that auto-kills+respawns a silently
      unreachable worker is not gated by `ORCHESTRATOR_AUTOSPAWN_ENABLED` either, so a misconfigured local instance
      free-loops respawning real (billed) sessions indefinitely. Done when: `server_url()` fails loud (or refuses to
      spawn) when unset in a non-`planning`-`vm_id` context instead of silently defaulting to prod's own port, OR the
      isolated-local-pilot runbook (todo above) makes `ORCHESTRATOR_SERVER_URL` a mandatory, checked-first-boot env var.
- [ ] [REVIEW] P1. Re-run the local pilot (per the 2026-07-29 isolation runbook, fixing the `ORCHESTRATOR_SERVER_URL`
      gap first) against the REDESIGNED policy specifically — the 2026-07-28 pilot validated the old 0.5-fraction,
      no-quota-adaptation, no-`forced_provider` design, not this one. Done when: a dated Progress Log entry shows (a) a
      `provider: claude` plan and a default-policy plan dispatched in the same run with visibly different outcomes, (b)
      at least one real spawn attempt where the quota-adaptive nudge measurably changed the effective fraction from a
      real (not mocked) Claude headroom reading, and (c) confirmation the hard opus/fable pin held (no DeepSeek spawn
      for an opus-tier task even when staged with zero Claude headroom).
- [ ] [INFRA] P2. End-to-end test the new `provider: claude` plan frontmatter through the REAL `regen()` function
      (`server/regen_backlog_from_plan.py`) — not just the unit-level `_parse_frontmatter_provider` test. A plan with
      `provider: claude` in its frontmatter should produce a `BacklogTask.provider_override == "anthropic"` after a real
      regen pass, and a plan without it should produce `None`. Done when: a test exercises `regen()` itself (temp plans
      dir) end to end, not just the parser function in isolation.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Touches
  agent-orchestrator's own live routing/billing/credential infra; repeated dated operator holds + 2 documented real
  safety incidents from testing this code; highest-stakes remaining items need operator-supervised rollout.
