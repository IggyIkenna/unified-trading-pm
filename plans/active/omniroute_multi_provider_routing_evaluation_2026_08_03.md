---
doc_type: plan
title: OmniRoute multi-provider LLM routing — evaluation, per-provider benchmark matrix, go/no-go
summary: >-
  Evaluates OmniRoute as a self-hosted multi-provider LLM gateway for reducing Claude Max spend by routing
  non-Claude-worthy work to cheaper providers. Harness is installed and working on the operator's host with 5 providers
  wired (mistral, groq, gemini, deepseek, cerebras) and cross-provider failover empirically proven. Remaining work is
  the per-provider quality/rate-limit/cost matrix on real repo tasks, then a go/no-go. Free-tier "frontier models for
  free" is already disproven (0/4 keyless providers functional, all blocked by anti-abuse); the real question is whether
  managed failover across paid+free API keys beats the hand-rotation the team does today.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [omniroute, cost-optimization, llm-routing, claude-accounts, evaluation]
related:
  - plans/audit/results/omniroute_free_tier_cost_analysis_2026_07_31.md
  - plans/audit/results/claude_account_usage_value_measurement_2026_08_01.md
created: 2026-08-03
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: none
last_updated: 2026-06-27
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

> **🟡 A live OmniRoute instance is running on the operator's host** (`127.0.0.1:20128`, loopback-only,
> `REQUIRE_API_KEY=true`). It holds real API keys for 5 providers. Do not expose it beyond loopback and never point it
> at a Claude Max OAuth token — see the security section in
> `agent-orchestrator/scripts/orchestrator/omniroute-eval/README.md`.

## Why this plan exists

Downstream of `/plans/audit/results/omniroute_free_tier_cost_analysis_2026_07_31.md` (desk research: do not integrate)
and `/plans/audit/results/claude_account_usage_value_measurement_2026_08_01.md` (measured
~$59,900 API-equivalent value
against ~$3,400 real Max-plan spend, ~17.6×). The operator asked to stop theorising and
actually test the router.

That test happened on 2026-08-03 and **changed the conclusion materially**, so the earlier audit's flat "do not
integrate" is no longer the whole picture — see Findings.

## Findings so far (measured on the operator's host, 2026-08-03)

**Harness state**: `omniroute@3.8.49` under Node v22.23.2 (nvm `default` alias deliberately left on v22.19.0 for the
workspace UI toolchain). 5 providers active, 255 models exposed, combo `fleet-test` with `strategy: priority` ordered
`groq → mistral → gemini → deepseek` (paid DeepSeek last so free tiers absorb traffic first).

**1. The free-tier pitch is disproven.** All 4 keyless "frontier" providers failed — DuckDuckGo anti-abuse challenge,
theoldllm IP-blocked by Vercel (the software's own error suggests buying residential proxies), MiniMax 401, Augment
stream-EOF. Every path that worked was a normal API key usable without OmniRoute.

**2. Cross-provider failover genuinely works — this is the real value.** Pinned to one provider under rate-limit
pressure, Mistral returned `429` after burning the full 29,043 ms `maxRetryWaitSec=30` window. At the same moment
through the combo: 4/4 success, no stalls, served by Groq then Gemini, and it correctly never touched paid DeepSeek.

**3. Routing overhead is negligible** — ~21 ms (≈3%) steady-state vs. calling the provider directly (638 ms direct vs.
659 ms routed, mean of 3 warm calls).

**4. Silent model substitution is the disqualifying caveat for benchmarking.** A request for
`groq/llama-3.3-70b-versatile` was forwarded as `meta-llama/llama-4-scout-17b-16e-instruct` (retired → 404); a combo
pinned to `gemini-3-flash-preview` silently served `gemini-3.1-flash-lite`. **Every benchmark below MUST read
`served_by` off the response.**

**5. Provider ceilings** (org-level; more keys do not raise them): mistral ~1 req/sec · groq 30 RPM / 6K TPM / 14.4K
req/day · gemini free = Flash-family only (`gemini-3.1-pro-preview` is listed but 429s on
`generate_content_free_tier_input_token_count`) · cerebras **dead** (`402 payment_required`; free tier retires
2026-08-17) · deepseek = paid, already owned.

**6. Not a fleet capacity source.** Even Mistral's ~1B tokens/month is throttled to ~1 req/sec — exhausted in 5 calls.
Against 15+ continuously-running slots these tiers are a quality-comparison target, never capacity.

## Codex SSOTs

- `/codex/06-coding-standards/model-tier-selection.md` — the qualitative `opus-required` contract any automated routing
  must not silently violate.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — where routing would have to integrate.
- `agent-orchestrator/server/accounts.py` (`AccountProvider`) — the existing DeepSeek-routing seam.

## Todos

### Phase 1 — benchmark matrix (the operator's ask: per-provider quality, rate limits, everything checkable)

- [ ] [SCRIPT] P0. **Build `provider-matrix.sh` in `agent-orchestrator/scripts/orchestrator/omniroute-eval/`** — one
      harness that, per provider, records: `served_by` (mandatory — see finding 4), wall-clock latency, prompt/
      completion/reasoning token counts, HTTP status, and the response body for scoring. Must emit JSONL so runs are
      diffable across days. `stream:false` and `max_tokens>=300` are mandatory (README traps 1-2).
- [ ] [SCRIPT] P1. **Quality run — mistral** (`mistral-large-latest`, `codestral-latest`, `devstral-latest`) against 3
      real tasks drawn from this workspace's repos, not synthetic prompts. Record `served_by` per response.
- [ ] [SCRIPT] P1. **Quality run — groq** (`llama-3.3-70b-versatile`, `openai/gpt-oss-120b`, `qwen/qwen3.6-27b`). Note
      the model-substitution bug hit Groq specifically; verify each `served_by` matches the request or record the
      divergence.
- [ ] [SCRIPT] P1. **Quality run — gemini** (`gemini-3-flash-preview`, `gemini-3.5-flash`). Free tier is Flash-only;
      confirm whether any Pro variant is reachable or record the 429 metric name as proof it is not.
- [ ] [SCRIPT] P1. **Quality run — deepseek** (`deepseek-v4-pro`, `deepseek-v4-flash`) — the frontier-class control and
      the only paid key. Capture `reasoning_tokens` separately; it is real cost the others do not incur.
- [ ] [SCRIPT] P1. **Baseline run — Claude Sonnet 5** on the identical 3 tasks, so every number above has a reference
      point. Without this the matrix scores models against nothing.
- [ ] [SCRIPT] P2. **Rate-limit characterisation per provider** — ramp concurrency until first 429, record the
      threshold, the `Retry-After` hint if any, and time-to-recovery. Confirms or corrects the published ceilings in
      finding 5 with measured numbers.

### Phase 2 — routing behaviour

- [ ] [SCRIPT] P2. **Fallback under sustained load** — extend `fallback-test.sh` beyond the 4-call proof to a sustained
      run, recording the served-by distribution across the chain. Answers whether priority ordering holds up or
      collapses onto one provider.
- [ ] [SCRIPT] P2. **Evaluate `reset-aware` / `least-used` / `fill-first` strategies** against `priority`. `reset-aware`
      is the closest analogue to the team's manual Claude-account rotation and is the most interesting result in this
      plan.
- [ ] [SCRIPT] P3. **Measure the RTK+Caveman compression pipeline** — advertised 15-95% token savings, reviewer-reported
      quality degradation on complex reasoning. Quantify both on the Phase-1 tasks before it is ever considered.

### Phase 3 — decision

- [ ] [OPERATOR] P1. **Go/no-go on adopting OmniRoute for non-Claude routing**, written into this plan with the matrix
      as evidence. The question is NOT "free tokens" (disproven) — it is whether managed failover across paid+free API
      keys beats the status quo. Feeds the AI Compute Optimisation Strategy classification work still open in
      `/plans/audit/results/claude_account_usage_value_measurement_2026_08_01.md`.
- [ ] [OPERATOR] P2. **Decide whether the earlier audit needs a correction banner.**
      `/plans/audit/results/omniroute_free_tier_cost_analysis_2026_07_31.md` concluded "do not integrate"; findings 2-3
      here (failover works, ~3% overhead) are new evidence its desk-research could not have had. It also stated
      "Anthropic appears nowhere" — the registry does carry a `Claude Web` cookie provider, which is ToS-barred but
      factually present.
- [ ] [SCRIPT] P2. **Decommission if no-go** — `omniroute stop`, `npm uninstall -g omniroute`, revoke all 5 provider
      keys at source, delete `~/.omniroute/` and `~/.claude-accounts/*.key`, delete the eval script directory. The keys
      are live credentials; leaving them on a decommissioned box is the failure mode.

### Housekeeping

- [ ] [SCRIPT] P3. **Audit whether anything on the operator host invokes `openclaw`** — it is installed globally
      (`openclaw@2026.2.21-2`) and is the harness Anthropic blocked from Claude subscriptions on 2026-04-04. Confirm no
      automation feeds it a `CLAUDE_CODE_OAUTH_TOKEN`, then remove it if unused.

## Progress log

### 2026-08-03 — install, security hardening, 5 providers wired, failover proven

Installed and evaluated end-to-end in one session. Hardened the instance: `OMNIROUTE_SERVER_HOST=127.0.0.1` (the
`HOST`/`HOSTNAME` vars are both ignored — see README trap 5) and `REQUIRE_API_KEY=true`; verified the LAN interface now
refuses connections and `/v1/*` 401s without a bearer token. Bootstrapped a `manage`-scoped key via the server-side
`OMNIROUTE_API_KEY` env var after confirming from source that no dashboard UI for that scope exists.

Two CLI defects found and worked around: `nodes add --base-url` is shadowed by the top-level `--base-url` option, and
`keys add` hits a nonexistent endpoint — provider registration is dashboard-only regardless of the docs.

Harness promoted out of the session scratchpad to `agent-orchestrator/scripts/orchestrator/omniroute-eval/` with the
seven hard-won traps written into its README, since every one of them silently produced a wrong result before being
understood.
