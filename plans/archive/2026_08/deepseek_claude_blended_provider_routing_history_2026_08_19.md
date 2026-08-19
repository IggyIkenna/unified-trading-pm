---
doc_type: plan
title: "deepseek_claude_blended_provider_routing — extracted history (2026-07-28..2026-07-30)"
summary: >-
  Fully-closed, dated Progress Log entries extracted verbatim from
  /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md to bring that still-active plan back under
  its 1000-line hard cap (2026-08-19, was at 1027 lines after real GLM-ceiling-correction edits). Every entry here
  was already historical/shipped at extraction time — nothing here changes any todo's done-when status. Pure
  archival record, per the plan-authoring template's finding J (extract oldest fully-closed sections as you go).
status: complete
nature: record
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, deepseek, claude, provider-routing, history, extracted]
related: [/plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md]
created: "2026-08-19"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
assigned_role: infra
drift_direction: none
resolved_by: extraction-only, no new resolution
locked_by:
depends_on: []
source: >-
  Verbatim extraction from deepseek_claude_blended_provider_routing_2026_07_28.md's Progress Log, lines 169-214
  as they stood 2026-08-19, done to relieve that file's 1000-line hard cap breach.
context_scope: [/plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md]
---

# `deepseek_claude_blended_provider_routing` — extracted history (2026-07-28..2026-07-30)

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
throughout. Closed by the `[INFRA] P1 server_url()` guard todo. Adjacent gap found, no real damage this run:
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
