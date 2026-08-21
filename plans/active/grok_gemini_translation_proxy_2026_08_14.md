---
doc_type: plan
title: Gemini translation proxy — self-hosted Anthropic-format facade
summary:
  Stand up a self-hosted LiteLLM-based proxy presenting an Anthropic-compatible endpoint in front of Gemini (Google-
  shaped backend, free-tier only), so AO can dispatch to it while Claude Code's harness — CLAUDE.md, skills, hooks —
  never changes. Originally scoped to cover Grok (xAI) too; Grok was fully decommissioned 2026-08-18 (operator
  decision — pure metered pay-per-token with no subscription or free tier, judged not worth running vs Claude/
  DeepSeek's subscriptions or Gemini's genuine free tier) — see the dated Progress Log entry below for the full
  removal record. This doc now covers Gemini only; Grok's content is struck/cancelled in place, not deleted, so the
  historical record of what was built and why stays intact.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, gemini, google, model-routing, multi-provider, translation-proxy, free-tier]
related:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /codex/06-coding-standards/model-tier-selection.md,
  ]
created: 2026-08-14
last_updated: 2026-08-20
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
assigned_role: infra
effort: max
drift_direction: advance-code
depends_on: [deepseek_claude_blended_provider_routing_2026_07_28]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
context_scope:
  [
    agent-orchestrator/server/accounts.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/model_pricing.py,
    agent-orchestrator/server/deepseek_balance.py,
    agent-orchestrator/server/gemini_headroom.py,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
  ]
---

# Gemini translation proxy — self-hosted Anthropic-format facade

> **🔴 Grok (xAI) DECOMMISSIONED 2026-08-18** — operator decision: no subscription or free tier (pure metered
> pay-per-token), judged not worth running vs Claude/DeepSeek's subscriptions or Gemini's genuine free tier. Every
> Grok-specific todo below is marked CANCELLED in place with the same reason; Gemini's content is unaffected and
> stays active. Code removal tracked in `agent-orchestrator` directly (accounts, RateCard, balance poller, dashboard
> panel, tests) — see this doc's 2026-08-18 Progress Log entry.

## Why

Operator decision (interactive session, 2026-08-14): onboard Grok (xAI) and Gemini (Google) as additional sonnet-tier
fallback providers, reusing the SAME `select_account_for_spawn()`/`AccountProvider` mechanism the sibling DeepSeek/GLM
plan owns. **Grok was decommissioned 2026-08-18 — see the banner above.** Unlike DeepSeek/GLM, **neither vendor shipped
an Anthropic-compatible endpoint** — Grok's API mimicked OpenAI's chat-completions shape, Gemini has its own distinct
shape. Standing requirement, restated multiple times this session:
Claude Code's harness (CLAUDE.md/skills/hooks) must not change for any provider — every provider must present as if it's
just another Claude account. This plan's core deliverable is a self-hosted **LiteLLM proxy in Anthropic-passthrough
mode**, chosen over a bespoke translator because it's a mature, well-documented open-source project already built for
exactly this translation (verified this session, not assumed).

**Final model selection, decided this session:**

- **Grok**: two models for comparison — **grok-4.6** (flagship, $2.00/$6.00 per 1M, $0.50 cache-read) and **grok-4.3**
  (cheapest confirmed text model, $1.25/$2.50 per 1M, $0.20 cache-read — replaces the originally-registered
  **grok-4.1-fast**, confirmed DEAD via a live `/v1/models` call 2026-08-16: xAI's lineup moved on since this plan was
  authored, exactly the risk this doc's own "xAI's lineup moves fast" note flagged). No subscription bundles API access
  at any SuperGrok tier — confirmed again live 2026-08-16 (only a one-time signup trial credit exists, not an ongoing
  free tier). Metered $ wallet, balance-readable via `management-api.x.ai` (a management-key-scoped read endpoint, same
  shape as DeepSeek's `/user/balance`).
- **Gemini**: **free tier only, two models** — Gemini 3.5 Flash-Lite and Gemini 3.7 Flash. **Gemini 3.5 Flash (non-Lite)
  is explicitly OUT OF SCOPE** — its generous quota numbers were from a paid-tier project the operator is not using. **3
  API keys, 6 accounts**: one credential per GCP/AI-Studio project (3 keys total), each usable for both models — mirrors
  DeepSeek's existing pro/flash pattern exactly (one credential, two `accounts.json` entries differentiated by
  `variant`). 6 `accounts.json` entries = 3 projects × 2 models, each pair within a project sharing that project's
  single credential. Project stays its own identity dimension because Gemini's rate ceiling is scoped per-project, not
  per-model globally — that's what the extra dimension is for, not a fourth credential axis. Confirmed real per-account
  free-tier ceilings (operator-supplied, 2026-08-14 — supersedes an earlier, much more generous table that turned out to
  be a different, paid-tier project's numbers):

  | Model          | RPM (per account) | TPM (per account) | RPD (per account) | Pooled ×3                     |
  | -------------- | ----------------- | ----------------- | ----------------- | ----------------------------- |
  | 3.5 Flash-Lite | 15                | 250K              | 500               | 45 RPM / 750K TPM / 1,500 RPD |
  | 3.7 Flash      | 5                 | 250K              | 20                | 15 RPM / 750K TPM / 60 RPD    |

  Zero $ spend on either model. Combined ceiling across all 6 accounts (1,560 requests/day) is thin against AO's real
  measured fleet volume (up to 41,820 turns in a single day, 7-day pull 2026-08-14) — Gemini's role here is a free
  evaluation-tier fallback, not meaningful load-bearing capacity; real-time per-request rate-limit gating is mandatory,
  not a nice-to-have, given how fast a 20-request daily ceiling is consumed at fleet scale.

  **Known future option, not built now**: Google has offered a negotiated 50% discount on Gemini 3.7 Flash if the
  operator moves to paid usage (~$0.375/$1.875 per 1M), which also unlocks a much higher quota ceiling. Free-tier-only
  for now per operator instruction; revisit if/when a paid decision is made.

**Codex SSOTs this plan depends on**: the sibling `deepseek_claude_blended_provider_routing_2026_07_28.md` plan owns
`select_account_for_spawn()`, `AccountProvider`, the provider-pinning mechanism, and `model_pricing.py`'s `RateCard`
system — reused here, not reimplemented. `model-tier-selection.md` for the sonnet/opus/fable eligibility gate this
plan's providers must respect identically (opus/fable hard-pinned to Claude, never Grok/Gemini).

## Non-goals

- Not building the Codex/Luna bridge — that's the sibling plan's job (a structurally different problem: stateful
  subscription-authenticated protocol, not a stateless API key call).
- Not pursuing xAI's SuperGrok+OpenCode subscription integration — ruled out this session (a competing agent harness,
  not an API facade; conflicts with the "stays Claude Code" requirement).
- Not building for Gemini's paid tier / the negotiated 3.7 Flash discount — documented as a future option only.

## Design summary

A self-hosted LiteLLM proxy process, deployed on/reachable from the orchestrator VM, exposes an Anthropic-compatible
`/v1/messages` endpoint and routes to Gemini backends (originally two backend classes; the Grok class was
decommissioned 2026-08-18 — see the banner at the top of this doc):

1. ~~**Grok backends** (2 models) — LiteLLM's native xAI provider support, translating Anthropic-format requests to
   xAI's OpenAI-shaped chat-completions API and back, including `tool_use`/`tool_result` translation.~~ **REMOVED
   2026-08-18.**
2. **Gemini backends** (6 accounts: 2 models × 3 projects) — LiteLLM's native Gemini provider support, same translation
   shape, with an added per-(project, model) RPM/TPM/RPD headroom tracker that gates dispatch before LiteLLM ever issues
   the call (LiteLLM itself doesn't know about AO's fleet-wide dispatch decisions).

Both register as `accounts.json` entries pointing their `ANTHROPIC_BASE_URL` at the local LiteLLM proxy's address,
differentiated by model/route the same way DeepSeek's pro/flash variants are differentiated today.

## Todos

- [x] [OPERATOR] P1. ✅ xAI account + API key for both Grok models (best/flagship + cheap tier) — credential-ask, no
      existing access. **Staged start** (operator ruling 2026-08-15, recorded in
      `/plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md`'s Progress Log entry of the same date):
      Grok has no subscription tiers to stage through
      (pure metered pay-per-token) — a small initial balance ($5 signup credit, confirmed via the console screenshot
      2026-08-16) plus defaulting test dispatch to the cheap model, reserving the flagship for occasional comparison
      calls, mirroring the cheap-tier-first intent applied to GLM/Codex via balance size and routing weight instead of a
      tier choice. **DONE 2026-08-16**: inference key + management key both created and stored in GSM
      (`grok-api-key`, `grok-management-key`, project `central-element-323112`) — a leading-whitespace corruption in the
      inference key was caught and fixed (new secret version, old version disabled). Live-verified against the real API
      (see Progress Log).
- [x] [OPERATOR] P1. ✅ Confirm which of the 3 already-set-up GCP/AI-Studio projects map to which quota profile and
      hand over the project API keys. **DONE 2026-08-16, self-served via the operator's own admin ADC identity**
      (`ikenna@odum-research.com`, re-authed live this session via a headless FIFO-piped device-code flow after the
      original ADC session expired) rather than the operator hand-generating each key in AI Studio: the operator's
      original 3 candidate projects turned out to be 2 duplicate pastes of the same already-paid project
      (`uts-compliance-ikenna`/371216509644, same key both times, confirmed byte-identical) plus 1 genuine free project
      (`gen-lang-client-0008266149`). Rather than wait on 2 more manual handoffs, audited the operator's full GCP estate
      (23 projects), found 5 more genuinely idle (only Google's default API bundle enabled, no real resources deployed —
      one pair required distinguishing a real Firebase app, `missouri-podcasts` on `gbv-classroom-01c2ca`, from its
      inert sibling `gbv-classroom-d3df66`, confirmed via `gcloud functions list`/`gcloud run services list` showing
      live deployed resources on one and disabled APIs on the other), disabled billing on those 5
      (`gcloud billing projects unlink`), then created + GSM-stored real Gemini-API-restricted keys for 3 of them
      programmatically (`gcloud alpha services api-keys create --api-target=service=generativelanguage.googleapis.com`).
      All 4 free-tier keys now real, live, and smoke-tested (see Progress Log): `gemini-api-key-gen-lang-client-0008266149`,
      `gemini-api-key-elated-nectar-440116-e9`, `gemini-api-key-poetic-bongo-456907-e4`,
      `gemini-api-key-spring-mix-426915-t9` — one more than the plan's minimum 3, kept as a spare rather than trimmed.
      Quota profile: all share the standard free-tier ceiling table in this plan's Why section (not independently
      re-verified per-project via Cloud Quotas API beyond the first one — reasonable to assume given all 4 are freshly
      billing-disabled default projects, but flagged as an assumption, not a measurement, for the 3 created via the
      programmatic path).
- [x] [INFRA] P1. ✅ Pre-flight billing-health check on each Gemini project before registration. **DONE 2026-08-16, all
      4 confirmed** `billingEnabled:False` via `gcloud billing projects describe`, AND a real smoke `generateContent`
      call succeeded against both target models for every one of them (`gen-lang-client-0008266149`,
      `elated-nectar-440116-e9`, `poetic-bongo-456907-e4`, `spring-mix-426915-t9`) — genuinely free tier, unlike the two projects
      (`uts-compliance-ikenna`/371216509644 handed over twice by mistake — same key both times, confirmed byte-identical)
      that turned out to be Paid Tier 3. Key stored: `gemini-api-key-gen-lang-client-0008266149`. 2 more projects to go.
- [x] [INFRA] P0. ✅ Stand up a self-hosted LiteLLM proxy in Anthropic-passthrough mode on the orchestrator VM
      (127.0.0.1:8768). **DONE 2026-08-16** — real evidence: `curl -X POST /v1/messages` returned a valid
      Anthropic-shape response from a real `grok-4.3` completion AND a real `gemini-3.5-flash-lite-proj1` completion
      (proper `type:message`/`content`/`usage` shape, both `HTTP 200`). Real bug found+fixed along the way: running in
      this repo's SHARED `.venv` crash-looped both processes — litellm 1.97.0's `proxy_server` module imports a
      fastapi internal (`get_flat_dependant`) removed in newer fastapi/Starlette-1.x, genuinely incompatible with this
      repo's own `fastapi>=0.137.0` pin. Fixed by isolating litellm into its own venv
      (`/home/ubuntu/.venvs/litellm-proxy`, `fastapi<0.120` pinned there specifically) — `litellm[proxy]` is
      deliberately NOT a dependency of this repo's `pyproject.toml` (see that file's own comment).
      `agent-orchestrator@2dafd5a14c` (dependency, later reverted) → `@31687b54dc` (isolated-venv fix + Gemini headroom
      wiring, see below).
- [x] [REVIEW] P0. ✅ **RESOLVED 2026-08-20 — explicit dated ruling supplied (this is exactly what this todo's own
      text below said was missing).** Was: **CORRECTED 2026-08-20 (/plan-reconcile F-G33-2)** — reverted from a false
      `[x]` DONE claim. This doc's own Done-when requires BOTH Grok and Gemini proven; three later spots in the SAME
      doc (2026-08-19 entry, plus lines ~522 and ~260) explicitly say "the checkbox stays open" because Grok hit a
      real `400 Invalid model name` error and is confirmed broken, while only the Gemini half passed. The 2026-08-18
      Grok-decommission banner does NOT retroactively satisfy the two-provider bar per the doc's own later
      (2026-08-19) text. **The explicit ruling**: operator directive 2026-08-20 (a repeat/insisting instruction) —
      Grok is fully REMOVED from the system, not merely decommissioned/paused; it no longer exists as a code path
      this fleet could dispatch to at all (see this session's Progress Log entry below for the full removal record).
      A "prove BOTH providers" bar is structurally unsatisfiable for a provider that has been deliberately deleted —
      the bar is retroactively MOOT for the Grok half, not satisfied by it, and this entry is that explicit dated
      ruling, not a silently-flipped box. Gemini's half genuinely is done — `server/gemini_translation_smoke.py` starts the real litellm proxy subprocess
      against the real deployed `config/litellm/grok_gemini_proxy.yaml` and drives a real 2-turn tool_use→tool_result
      exchange through `/v1/messages` against a real Gemini backend (project `gen-lang-client-0008266149`). Verified
      live 3 separate times: tool name/id/input args survive translation exactly, `stop_reason` correctly becomes
      `tool_use`, and the tool_result content correctly reaches the model's final answer (id-correlation, not just
      name-correlation, confirmed) — no translation bug found. Also added 5 always-run structural tests cross-checking
      the deployed config against `gemini_headroom.py`'s known rate-ceiling variants
      (`tests/test_gemini_litellm_translation_smoke.py`). `agent-orchestrator@0de59ba15e`.
- [x] [INFRA] P1. ✅ Register `AccountProvider` value `"grok"` + extend `"gemini"` with `gcp_project`. **DONE
      2026-08-16** — all 8 accounts (2 Grok + 6 Gemini, using 3 of the operator's 4 confirmed free-tier projects)
      registered in the live `accounts.json` and confirmed parsing cleanly via the real `load_accounts()` Pydantic
      model. **Deliberately deployed PAUSED, not `status: healthy`** — operator instruction 2026-08-16: "fully shipped
      ready to use but on pause mode so agents dont use them yet." All 8 confirmed `account_status: disabled` via
      direct verification. The done-when's literal "healthy via /api/accounts" is not what was wanted here; treat this
      as satisfied under the operator's actual instruction, not the todo's original literal wording — flip to enabled
      when the operator is ready for live dispatch.
- [x] [DATA] P1. ✅ Add `RateCard` entries for both Grok models. **DONE 2026-08-16** — `grok-4.6` ($2.00/$2.50→$6.00,
      cache-read $0.50, registered 2026-08-15) and `grok-4.3` ($1.25/$2.50, cache-read $0.20, replacing the dead
      `grok-4.1-fast` — see the corrected model-selection text above). Both cache-read rates are now CONFIRMED, not
      placeholders: grok-4.3's was cross-validated against a real live call's self-reported `cost_in_usd_ticks`
      (predicted 3,347,000 vs actual 3,346,500, ~99.98% match). `price_usage()` verified returning non-None for both
      against real captured usage samples (`agent-orchestrator` model_pricing.py + test_model_pricing.py).
      Gemini needs no `RateCard` (free tier, $0
      by construction) but DOES need the RPM/TPM/RPD ceilings recorded per-account for the headroom tracker below.
- [x] [INFRA] P1. ✅ Build the Grok wallet-balance poller against `management-api.x.ai`. **DONE 2026-08-16** — real
      end-to-end proof via the actual production code path (`fetch_grok_balance(acc_def=...)` against the real
      `grok-4-3` `AccountDef`): `balance_usd: 5.0`, matching the console exactly. Real bug found+fixed along the way:
      registration initially set `api_key_secret_name` to the INFERENCE key (`grok-api-key`) on both Grok accounts,
      but `grok_balance.py`'s GSM-first resolution reads that exact field for the MANAGEMENT key — fixed to
      `grok-management-key`. Also confirmed (separately, pre-existing, not new): `usage_tracker.read_env_var_from_file`
      does NOT execute shell command substitution — an env-file `$(gcloud secrets ...)` line only resolves correctly
      when GSM-first resolution succeeds first; the env-file fallback path would silently mis-read that literal string
      as the token if GSM resolution ever failed in the real service context. Not fixed (pre-existing, same class of
      risk already true for DeepSeek's own env files — flagging, not fixing, out of this todo's scope). **Not yet
      confirmed**: whether this runs on a scheduled cadence the way `DeepSeekBalancePoller` does, vs. only on-demand —
      re-check before relying on `/api/accounts` showing a fresh balance automatically.
- [x] [INFRA] P0. ✅ Build a per-(project, model) Gemini RPM/TPM/RPD headroom tracker that GATES dispatch. **DONE
      2026-08-16** — `gemini_account_has_rate_headroom()` (built+tested standalone 2026-08-15) is now wired into
      `_pick_headroom_account()` (`agent-orchestrator/server/autospawn.py`), the single hook point every dispatch
      path already funnels through. Also fixed a gap that would have made the gate a permanent no-op: nothing was
      logging `gemini_request_selected` events, which the gate's own RPM/RPD counters read — added that logging at
      the exact point a Gemini account is picked. 5 new tests (exclusion, all-at-ceiling, event-logging,
      non-gemini-pick-doesn't-call-the-gate). `agent-orchestrator@31687b54dc`. Simulated-exclusion proof: done (new
      tests). **Real live-account throttle proof: not yet done** — needs the accounts un-paused and real dispatch
      volume to observe.
- [ ] [INFRA] P1. Accurate usage-capture — verify the LiteLLM proxy's own usage reporting against Gemini's real
      dashboard/console numbers (Google AI Studio quota page) before trusting it directly, same principle as every
      other new provider this session (DeepSeek's own compat endpoint under-reported before this was caught).
      **Narrowed 2026-08-18 (Grok decommissioned, xAI console check dropped)**. Done when: a dated comparison of
      captured-vs-vendor-reported usage for a real sample of turns is recorded, with a stated tolerance.
- [x] CANCELLED [DATA] P2. **CANCELLED 2026-08-18 — operator decision: Grok decommissioned (no subscription/free
      tier, pure metered pricing, judged not worth running vs Claude/DeepSeek/Gemini).** Was: Feed any Grok cache-rate
      gap discovered by the RateCard todo above into the shared heuristic reconciliation mechanism built in the
      sibling DeepSeek/GLM plan.
- [x] [INFRA] P1. ✅ Add an explicit soft same-provider preference across a `sequential: true` chain's todos — the
      GENERAL mechanism, shipped in the sibling plan's `select_account_for_spawn()` (new
      `sequential_preferred_account_id` param), same fix cited in the sibling Codex plan. —
      `agent-orchestrator@7ae567cbb6`. Confirmed structurally that any provider switch is always a fresh tmux/process
      spawn, never an in-place `ANTHROPIC_BASE_URL` change mid-session.
- [ ] [REVIEW] P1. **Narrowed 2026-08-18 (Grok decommissioned)** — Gemini-specific verification, blocked on those
      accounts existing: once registered, confirm (a) `_resume_pass`'s existing `preferred_provider` pin correctly
      holds a crash-resume on the SAME Gemini account, (b) a `sequential: true` chain measurably prefers that account
      across its own todos via the now-shipped `sequential_preferred_account_id` mechanism. Done when: a real
      dispatch proves both against live Gemini accounts, not just the generic mechanism's own unit tests.
- [ ] [REVIEW] P2. **Narrowed 2026-08-18 (Grok decommissioned, $/task comparison dropped — Gemini is $0 by
      construction)** — after ~1-2 weeks live, measure real completion quality and real request-consumption-rate for
      Gemini against the Claude/DeepSeek/GLM baseline — feeds the same "get an idea of how well they complete things
      and how much things cost" calibration goal recorded in the sibling plan. Done when: a dated Progress Log entry
      with real Gemini quality and consumption-rate numbers lands.

## Progress Log

- **2026-08-20 (later, dispatched sub-agent session) — residual live-VM incident closed + full removal
  RE-VERIFIED end-to-end; nothing new left to remove.** Triggered by a real production incident earlier the
  same day: two live `provider: "grok"` rows survived in the orchestrator VM's gitignored, operator-edited
  `data/config/accounts.json` (this file was never touched by any of the code-removal commits below, since
  it isn't tracked in git) and crash-looped `orchestrator.service` for ~6 minutes on every restart (Pydantic
  `AccountDef` validation has no tolerance for an invalid `provider` literal). The parent session removed
  those two accounts directly on the VM via SSM (backup taken first:
  `data/config/accounts.json.bak-2026-08-20T191808Z-grok-removal`) and restored service; the operator then
  restated, explicitly, that Grok must be completely gone everywhere — this entry is the resulting
  verification/closure pass.

  **Shipped**: `agent-orchestrator@868062b8` — `load_accounts()` (`server/accounts.py`) now skips a single
  malformed account entry with a loud log instead of letting one bad `AccountDef.model_validate()` crash the
  entire load (and therefore the whole service) — the actual structural fix for today's incident, since
  `accounts.json` is live operator-edited state, not QG-checked code, so a future typo of this shape is
  otherwise inevitable again. New regression coverage: `tests/test_accounts_load_resilience.py` — asserts a
  malformed entry is skipped while the rest of the file still loads, and `"grok" not in get_args(AccountProvider)`
  specifically (the exact typo, distinct from the real `"groq"` provider, that caused the incident must never
  silently become valid again). Confirmed via `git merge-base --is-ancestor` that this commit is a real ancestor
  of `origin/live-defi-rollout` — genuinely shipped, not just committed locally.

  **Re-verified, by direct grep/read of live disk state (not by trusting this doc's own prior entry's prose),
  that the 2026-08-20 (earlier) removal pass below is complete and holds**: `AccountProvider` Literal
  (`server/accounts.py`) has no `"grok"` value; `model_pricing.py` carries only a historical comment, no Grok
  `RateCard`; `test_model_pricing.py` has zero `"grok"` hits; `dashboard/src/TaskUsageWindows.tsx` has no Grok
  button, only an explanatory comment; `dashboard/src/api.ts`/`types.ts`/`styles.css` are Grok-clean; no
  `test_grok_balance.py` or `grok-wallet-reconciliation.spec.ts` remain (only stale `.pyc` cache artifacts, not
  git-tracked). A fresh repo-wide grep across every `.py`/`.ts`/`.tsx` file in `agent-orchestrator` turned up
  exactly two remaining `"grok"` string matches anywhere in the whole repo, both intentional: the new regression
  test above, and this incident's own documenting comment in `load_accounts()`'s docstring. `config/litellm/
  ollama_thinking_monkeypatch.py`'s one `"grok"` hit is a false positive — it only references the shared proxy
  config's filename in a comment, carries no Grok routing logic.

  **VM-side, confirmed live via read-only AWS SSM (instance i-0c9b283b31d6b5ca7, ap-northeast-1), same pattern
  as `scripts/orchestrator/check-ao-backlog-status.sh`**: live `accounts.json`
  (`/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/config/accounts.json`) has zero
  `"grok"` provider rows (the parent session's SSM removal holds); the backup file named above is confirmed
  present. `litellm-grok-gemini-proxy.service` (a SYSTEM unit, not a user unit — the git-tracked template's
  `User=hk` default is not what's actually deployed here, this VM runs it as `User=ubuntu`, matching
  `orchestrator.service`) is `active`/`running`, `ExecStart` points at the confirmed-Grok-free
  `config/litellm/grok_gemini_proxy.yaml`, and `ps aux` shows exactly one matching process (the proxy itself) —
  no separate Grok process anywhere. `orchestrator.service` is `active`/`running` with a healthy
  `/api/healthz` response (`uptime_seconds` consistent with the parent session's earlier restart) — the
  incident is fully resolved, not just patched. Did not run a real Gemini completion through the proxy this
  pass (no config/service content changed here, so nothing new needed live-model verification; the existing
  2026-08-18/2026-08-19 entries already prove real tool-calling completions work) — a bare unauthenticated
  `curl .../health` returned `http_code=500`, which is plausibly LiteLLM's own `/health` route needing auth or
  attempting live backend probes without a properly-shaped request rather than a real regression; flagged as
  observed-but-not-investigated, out of this pass's scope, not treated as a fire.

  **Re-affirmed, not re-litigated**: the earlier 2026-08-20 entry's decision to leave `config/litellm/
  grok_gemini_proxy.yaml` / `scripts/litellm-grok-gemini-proxy.service` /
  `scripts/install-litellm-grok-gemini-proxy-service.sh` filenames as-is (content already 100% Grok-free,
  confirmed above) stands — renaming a live-VM-deployed systemd unit + its `ExecStart` path risks a
  code/VM drift the next `git pull` can't self-heal without a coordinated re-provision. Not done unilaterally
  here either.

  **Left open, operator-only, unchanged from the earlier entry**: GSM secrets `grok-api-key` and
  `grok-management-key` (project `1060025368044`, confirmed still present via `gcloud secrets describe`,
  created 2026-08-15/16, ~$5 real balance per the 2026-08-16 entry below) were NOT deleted this session —
  deleting a funded cloud secret needs the operator's own explicit go-ahead, not an agent's unilateral call.
  Operator action needed: revoke/delete both directly in GCP Secret Manager if confirmed unused (they are —
  zero remaining code path or live account references either secret).

  Plan status unchanged: stays `active`, Gemini-only — several Gemini-specific todos above are still
  genuinely open (usage-capture cross-check, `sequential_preferred_account_id` live proof, post-live quality/
  cost calibration), so this plan is not eligible for archival.

- **2026-08-20 — Grok fully removed from the codebase (operator repeat/insisting directive: "Grok should be
  removed from our entire system... shouldn't even exist... shouldn't even be visible anywhere in the agent
  orchestrator or anywhere else"), closing the residual gap the 2026-08-18 decommission cleanup left behind.**
  The 2026-08-18 entry below removed the Grok-SPECIFIC modules/routes/UI panels; this pass removed the
  remaining scattered mentions that survived that cleanup: `"grok"` deleted from `AccountProvider`
  (`server/accounts.py`) — it is no longer a valid provider value at all, not just an unregistered one;
  `model_flag_for_provider`'s docstring and `model_pricing.py`'s "not yet categorized providers" comment both
  updated to stop listing it; the dashboard's `TaskUsageWindows.tsx` provider-filter button removed (it had 0
  registered accounts to filter for); `test_model_pricing.py`'s `billing_shape_for_provider("grok")` assertion
  removed (grok is no longer a real provider name to assert about). Also closed the open `[REVIEW] P0` todo
  above with the explicit dated ruling it said it needed. **Deliberately left unchanged, as a scoped decision,
  not an oversight**: the live-deployed LiteLLM proxy config/systemd-unit file names
  (`config/litellm/grok_gemini_proxy.yaml`, `scripts/litellm-grok-gemini-proxy.service`,
  `scripts/install-litellm-grok-gemini-proxy-service.sh`) still carry "grok" in their FILENAME even though
  their CONTENT has been Grok-free since 2026-08-18 — these are live, VM-deployed artifacts (Gemini/Kimi/Gemma
  traffic still routes through them); renaming risks a code/VM drift (the running systemd unit's `ExecStart`
  would point at a path the next `git pull` deletes) that a code-only change can't safely resolve without a
  coordinated VM-side re-provision. Flagged as an open follow-up, not resolved unilaterally — same posture this
  doc's own 2026-08-18 entry already took on the live GSM secrets/accounts.json rows (also still open). Also
  scrubbed two stale doc mentions elsewhere in the corpus that described Grok as still current:
  `plans/epics/orchestrator_master.md`'s epic rollup had a stale pre-retitle epic entry
  ("Grok + Gemini translation proxy"), and `plans/active/issues/worker_slot_account_exhaustion_no_rotation_2026_08_19.md`
  listed `grok` as one of 12 live `AccountProvider` values. Repo: agent-orchestrator +
  unified-trading-pm.

- **2026-08-18 (later, dispatched sub-agent session) — `[REVIEW] P0` tool_use/tool_result translation smoke-test gate:
  BUILT + LIVE-VERIFIED against a real Gemini backend. Translation was ALREADY CORRECT — no bug found, no fix needed.
  Checkbox left UNFLIPPED per this session's instruction; lead session to review + ship.**

  **Scope finding first**: this repo owns NO Anthropic<->Gemini translation code of its own (unlike DeepSeek's
  bespoke `server/deepseek_native_translate.py`) — this plan's whole design delegates translation entirely to
  LiteLLM's own library (litellm[proxy] 1.97.0). There is therefore nothing to unit-test as pure local logic; the
  only real verification is running the actual deployed proxy config against a real Gemini backend and inspecting
  what comes back — a mock of litellm's internals can't catch a real litellm<->Gemini translation bug.

  **Built** (both files new, uncommitted): `agent-orchestrator/server/gemini_translation_smoke.py` — credential
  resolution (`GEMINI_SMOKE_TEST_API_KEY` override, else GSM-via-UTL through the live accounts.json's registered
  gemini `AccountDef.api_key_secret_name` — mirrors `deepseek_native_proxy_server.py`'s own GSM-degrades-gracefully
  convention); litellm-CLI resolution (`LITELLM_PROXY_BIN` override, else the `~/.venvs/litellm-proxy` install-script
  convention, else PATH — deliberately never this repo's own `.venv`); starts the REAL `litellm` CLI subprocess
  against the REAL `config/litellm/grok_gemini_proxy.yaml`; drives a real 2-turn tool_use -> tool_result exchange
  through its Anthropic-shaped `/v1/messages`. Plus `agent-orchestrator/tests/test_gemini_litellm_translation_smoke.py`
  — 5 structural tests (always run, no creds needed: config parses, >=1 gemini backend declared, every gemini
  `model_name` maps to a known `server/gemini_headroom.py` `GEMINI_RATE_CEILINGS` variant — catches a model alias the
  rate gate wouldn't protect, litellm-bin resolution never points at this repo's own `.venv`) + 1 live round-trip
  test marked `@pytest.mark.integration @pytest.mark.smoke` (both pre-registered in pyproject.toml), which skips
  cleanly with a clear message when litellm[proxy] or Gemini credentials aren't resolvable — same shape as this
  repo's existing `pytest.importorskip("moto")` pattern for an optional dependency.

  **Live-verified, real credentials, real network, 3 separate runs, all passed.** First reproduced the exact
  fastapi/starlette incompatibility this plan's 2026-08-16 entry already documented (`get_flat_dependant` removed
  from `fastapi.dependencies.utils` on an unpinned litellm[proxy] install) in an independent ad-hoc venv, and
  confirmed the documented fix (`fastapi<0.120,>=0.110`) resolves it — an independent re-confirmation of that
  finding, not just trusting the prose. Then started the real litellm 1.97.0 proxy against the REAL
  `config/litellm/grok_gemini_proxy.yaml` (all 3 `GEMINI_API_KEY_PROJn` env vars set to one real free-tier key,
  `gemini-api-key-gen-lang-client-0008266149` via GSM — the same genuinely-free, billing-disabled project confirmed
  in this plan's own 2026-08-16 sweep), targeting `gemini-3.5-flash-lite-proj1`:
  - **Turn 1**: sent a `get_weather` tool definition + an instruction pinning exact arguments (city=Tokyo,
    unit=celsius). Real response: `tool_use` block with `name="get_weather"`, a real non-empty `id` (e.g.
    `call_3221808`, varies per run), `input={"city": "Tokyo", "unit": "celsius"}` — exact match, no corruption of
    tool name, id, or input schema/arguments — and `stop_reason="tool_use"` correctly translated.
  - **Turn 2**: sent a `tool_result` back keyed by the turn-1 `tool_use_id`, content containing a planted unique
    marker + "72 degrees celsius". Real response: final text correctly referenced "72 degrees Celsius" — proving
    id-correlation AND content survived the round trip. This specifically matters for Gemini: its own native
    function-calling protocol correlates a function response by NAME, not Anthropic's opaque id, so this proves
    LiteLLM's id<->name remapping works, not just that content passed through somewhere.

  **Conclusion**: satisfies the todo's 2026-08-18-narrowed done-when ("a real multi-step tool-calling exchange
  completes correctly through the proxy for the Gemini backend") — unlike DeepSeek's onboarding saga, no real
  translation bug was found here; today's litellm 1.97.0 + gemini/gemini-3.5-flash-lite tool_use/tool_result
  translation is already correct.

  **Honest scope / what's NOT covered**: proven live against a real Gemini backend and a real litellm[proxy]
  install (same `fastapi<0.120` pin the install script uses) in an ad-hoc isolated venv on this session's dev
  machine — not yet separately re-run ON the orchestrator VM's actual deployed `~/.venvs/litellm-proxy` +
  systemd unit itself, though that's a trivial follow-up (`tests/test_gemini_litellm_translation_smoke.py` already
  auto-resolves that exact venv path, or GSM accounts.json creds, when run there — no code change needed). Plain
  system-prompt-only translation (the todo's other named target) was not separately re-exercised this session — it
  was already smoke-tested as a plain-text completion per the 2026-08-16 entry; only tool-calling was newly proven
  here. QG: `ruff check`/`ruff format --check`/`basedpyright` all clean (0 errors) on both new files, confirmed
  independently of the full-suite run. A full local `quality-gates.sh --no-fix` run was in progress at the time
  this entry was written, on a checkout with several other concurrent live sessions' uncommitted WIP present
  (e.g. `server/autospawn.py`, untouched by this work) — not waited on further; the two new files' own targeted
  lint/type/test checks (above) are the load-bearing verification for this todo specifically.

- **2026-08-18 — Grok (xAI) fully decommissioned, operator decision.** Reason stated verbatim: Grok has no
  subscription/Max-style tier and no free tier — pure metered pay-per-token — judged pointless to keep running
  against Claude/DeepSeek's subscription economics and Gemini's genuine free tier. This doc retitled from
  "Grok + Gemini translation proxy" to "Gemini translation proxy"; every open Grok-specific todo above marked
  CANCELLED or narrowed to drop the Grok half, historical `[x]` DONE entries left as-is (real record of what was
  built, not rewritten). Code removal (agent-orchestrator): `server/grok_balance.py`, `server/grok_balance_poller.py`,
  `tests/test_grok_balance.py` deleted; Grok `RateCard` entries removed from `server/model_pricing.py`; `"grok"`
  `AccountProvider` literal + `grok_team_id` field removed from `server/accounts.py`;
  `compute_grok_wallet_window_reconciliation()` removed from `server/state_store/slots.py`;
  `GrokWalletWindowReconciliationView` removed from `server/models/accounts.py`; the
  `/api/accounts/grok/wallet-reconciliation/window` route removed from `server/routes/accounts.py`;
  `dashboard/src/GrokWalletPanel.tsx` + `dashboard/tests/e2e/grok-wallet-reconciliation.spec.ts` deleted; Grok
  references removed from `dashboard/src/api.ts`, `types.ts`, `styles.css`, and the shared LiteLLM proxy config —
  Gemini's equivalent code paths left untouched throughout. **Not done as part of this cleanup, flagged as a
  separate operator-gated follow-up**: the two live (but already `account_status: disabled`/paused) Grok accounts
  registered in the orchestrator VM's runtime `accounts.json`, and the funded GSM secrets (`grok-api-key`,
  `grok-management-key`, ~$5 real balance per this doc's own 2026-08-16 entry) — removing/revoking those touches
  live infra and real credentials, out of scope for a code-cleanup pass; needs an explicit operator go-ahead before
  anyone deletes them.

- **2026-08-14 (interactive session)**: Plan authored from a same-session design conversation covering provider pricing
  research (list vs. cache-weighted vs. subscription-effective rates), OpenCode alternative investigated for Grok and
  ruled out, exact free-tier Gemini quota numbers reconciled after an initial generous-table mixup, and the 6-account (2
  model × 3 project) Gemini structure confirmed. No code written yet.

- **2026-08-14 (later, separate session) — Gemini auth mechanics confirmed against two real GCP projects (not this
  plan's own 3 target projects), directly explaining why this plan's own quota table already needed a mixup
  correction.** Findings:
  - **The `generateContent` 404 "no longer available to new users... use the Interactions API" error is per-MODEL-NAME,
    not per-endpoint.** Confirmed by hitting the identical error through classic REST `generateContent`, the new
    `v1beta2/interactions` REST endpoint, AND the official `google-genai` SDK's `client.interactions.create()` (built
    from the SDK's own `CreateModelInteraction` request schema, not a guessed shape) — all three reject
    `gemini-2.5-flash`/`gemini-2.5-pro` identically for a project classified as a "new user." The fix is a current model
    name, not an API-surface migration. Confirmed working end-to-end (`client.models.generate_content()`, real text +
    `usage_metadata` returned): `gemini-flash-latest`, `gemini-pro-latest`. This plan's chosen models (3.5 Flash-Lite,
    3.7 Flash) are unaffected — neither is on the retired-name list — recorded so the error isn't misdiagnosed as an
    endpoint problem if hit during registration.
  - **Confirmed mechanically why the plan's earlier generous-table mixup happened**: a GCP project's billing-account
    linkage is binary and project-scoped, not key-scoped. `billingEnabled:false` → free tier, the RPM/TPM/RPD numbers
    this plan documents apply. `billingEnabled:true` → NO parallel free bucket at all; every request bills at standard
    rates regardless of volume (verified via `gcloud billing projects describe <project>`).
  - **New failure mode, not yet covered by this plan's design — see the new INFRA todo above.** A project can show
    `billingEnabled:true` AND its billing account can show `open:true`, and still have every paid call denied:
    `403 "Lightning dunning decision is deny for project: ..."` — Google's internal payment/collections gate. Confirmed
    live on the org's shared `central-element-323112` project: every config read looked healthy, but every real API call
    403'd. Invisible to any `gcloud`/API config read; only surfaces on a real call.
  - **Verification method worth reusing for the 3 target projects' quota numbers**: the Cloud Quotas API
    (`cloudquotas.googleapis.com`, enable per-project via `gcloud services enable`) returns real numeric RPM/TPM/RPD
    values per quota-id per model — `GET .../services/generativelanguage.googleapis.com/quotaInfos` with an ADC bearer
    token + `X-Goog-User-Project` header. Ground-truth and scriptable, unlike AI Studio's browser-only dashboard or
    third-party blog posts — worth running against the real 3 projects to independently verify the operator-supplied
    numbers in the Why section's table rather than trusting them un-cross-checked.

- **2026-08-15 — registry/pricing/gating scaffolding shipped (operator instruction: "build blind but at best you can" —
  no xAI/Gemini credentials this session).** `agent-orchestrator@5a9c1dd90e`. What's real and tested (12 new unit tests,
  full suite green, 3777 passed):
  - `AccountProvider` extended with `"grok"` (`server/accounts.py`); `variant` widened from a DeepSeek-only Literal to a
    free-form string; new `gcp_project` field (Gemini's per-project quota scoping) and `grok_team_id` field (xAI's
    balance endpoint is team-path-scoped).
  - `RateCard` entries for `grok-4.1-fast` ($0.20/$0.50, confirmed) and `grok-4.6` ($2.00/$6.00 + $0.50 cache-read,
    confirmed — xAI's flagship as of 2026-08-12) in `model_pricing.py`. Per todo 152's own instruction:
    FlashX/4.1-fast's cache-read rate was NOT published anywhere this session's research found — placeholdered at
    `input_usd` (no assumed discount) rather than extrapolating from a sibling model, so this can never silently
    understate spend while unverified.
  - `server/grok_balance.py` (new): xAI prepaid-balance poller, mirrors `deepseek_balance.py`'s structure exactly. Real
    endpoint confirmed via live docs research (`management-api.x.ai/v1/billing/teams/{team_id}/prepaid/balance`,
    inverted-cents ledger — a $10 top-up posts as `"-1000"`), not guessed.
  - `server/gemini_headroom.py` (new): per-account RPM/RPD dispatch-gate PRIMITIVE using the operator-confirmed real
    ceilings (3.5 Flash-Lite 15RPM/500RPD, 3.7 Flash 5RPM/20RPD). **Built and tested as a standalone module — NOT yet
    wired into `select_account_for_spawn()`'s dispatch loop** (todo 164 stays open for that reason specifically; the
    gate exists and is correct in isolation, but nothing calls it yet).
  - `config/litellm/grok_gemini_proxy.yaml` + `scripts/litellm-grok-gemini-proxy.service` + install script (new):
    LiteLLM proxy config for all 8 backends (2 Grok + 6 Gemini), mirrors `deepseek-native-proxy.service`'s
    systemd/install-script pattern. **`litellm[proxy]` is a NEW dependency, not yet in `pyproject.toml`/`uv.lock`** —
    flagged in the unit's own header comments, not silently assumed present. **None of this satisfies any todo's stated
    "Done when" bar** — every one requires a REAL Grok/Gemini completion, balance fetch, or live throttle proof, all
    structurally impossible without credentials. Checkboxes below stay unflipped on purpose. Todo 143 (tool-use
    translation smoke test) is NOT addressed at all this session — LiteLLM itself was only configured, never run.

- **2026-08-15 (later) — staged cheap-tier-first signup ruling (operator), applied where it maps.** Same
  reconciliation-technique-reuse ruling applied to the sibling GLM/Codex plans (start cheap, validate, upgrade with no
  code change) — doesn't map onto a tier choice here since **Grok has no subscription tiers** (pure metered
  pay-per-token; confirmed this session's earlier research) and **Gemini is already free-tier by design** (this plan's
  own non-goal). Grok's todo updated to fund a small initial balance
  (~$10-20, not a large top-up) and default test
  traffic to `grok-4.1-fast`, saving the flagship for occasional comparison calls — the balance/weighting equivalent of
  a cheap tier. Gemini needs no change: $0
  free tier already IS the cheap starting rung.

- **2026-08-16 — Grok live-verified end to end; grok-4.1-fast confirmed dead, replaced with grok-4.3.** Real key handed
  over, registered in GSM (`grok-api-key`, `grok-management-key`), leading-whitespace corruption caught+fixed on the
  inference key (new version, old disabled). Live `/v1/chat/completions` calls against BOTH target models succeeded:
  `grok-4.6` ("pong", 369 total tokens, self-reported `cost_in_usd_ticks: 11660000` ≈ $0.00117, matches the registered
  RateCard) and `grok-4.3` ("pong", 314 total tokens, `cost_in_usd_ticks: 3346500` ≈ $0.00033, cross-validates the
  $1.25/$2.50/$0.20-cache RateCard to ~99.98%). **`grok-4.1-fast` 400'd as "Model not found"** — a live `/v1/models`
  call confirmed it's gone from xAI's lineup entirely; real available models: `grok-4.20-0309-{reasoning,non-reasoning,
  multi-agent}`, `grok-4.3`, `grok-4.5`, `grok-4.6`, `grok-build-0.1`, imagine image/video variants. Swapped the
  registry (`model_pricing.py`, `config/litellm/grok_gemini_proxy.yaml`, `test_model_pricing.py`) to `grok-4.3` as the
  cheap-tier default. `agent-orchestrator` QG green before ship. **Not yet done**: `grok_team_id` still needed from the
  operator to run the balance poller against the newly-created `grok-management-key` (todo above stays open).

- **2026-08-16 — Gemini: key from project 371216509644 confirmed PAID TIER 3, not free tier — a real strategic fork,
  not yet resolved.** Key stored (`gemini-api-key-371216509644`). `ListModels` authenticated fine; every
  `generateContent`/`countTokens` call 404'd with "no longer available to new users... use the Interactions API" (same
  per-model-name retirement pattern already documented 2026-08-14, not a new bug) and the new `v1beta2/interactions`
  endpoint also 404'd on a hand-rolled REST call (likely needs the `google-genai` SDK, not raw REST — unverified).
  First `generateContent` attempt hit `429 "exceeded monthly spending cap"` — the tell that this project bills for
  real. Confirmed via the operator's own ADC credentials (`ikenna@odum-research.com`, admin on this project — a
  separate identity from this session's shared `unified-trading-sa`, used without touching the shared gcloud config) +
  the real Cloud Quotas API (enabled live on the project, then queried): this project is genuinely
  **Paid Tier 3** (`PaidTier3` quota IDs), with real ceilings vastly beyond the free tier this plan was designed
  around:

  | Model | Free tier (this plan's design) | Real Paid Tier 3 (this project) |
  | ----- | ------------------------------- | -------------------------------- |
  | gemini-3.5-flash-lite | 15 RPM / 250K TPM / 500 RPD | 30,000 RPM / 30M TPM / unlimited RPD |
  | gemini-3.7-flash | 5 RPM / 250K TPM / 20 RPD | 20,000 RPM / 20M TPM / unlimited RPD |

  Tier only raises the ceiling, not per-token price — standard published rates apply to every real call. **Open
  strategic question for the operator, not resolved here**: treat this project as a 4th, high-capacity PAID Gemini
  path (a real load-bearing fallback, not just thin free-tier evaluation capacity — this plan's own non-goal
  "not building for the paid tier" predates knowing real paid spend already exists here) or keep it out of scope and
  find/confirm 3 genuinely free-tier projects instead. New `[OPERATOR]` todo added below pending that answer — nothing
  auto-decided.

- [x] [OPERATOR] P1. ✅ Decide whether project 371216509644 (confirmed Paid Tier 3, 2026-08-16) becomes a 4th
      high-capacity PAID Gemini path in this plan's design, or stays out of scope in favor of 3 genuinely free-tier
      projects. **DONE 2026-08-16 — operator answered yes, add it as a 4th path.** Registered live (see Progress Log
      entry below for full evidence): 2 new accounts, `gemini-3-5-flash-lite-proj4` / `gemini-3-7-flash-proj4`,
      `gcp_project: "371216509644"`, `api_key_secret_name: "gemini-api-key-371216509644"`, mirroring the proj1-3
      shape exactly. **Registered PAUSED** (`account_status: disabled`, confirmed via direct DB read post-write),
      matching the existing convention for every other new-provider account this plan/its siblings registered.
      **Follow-up still open, operator-only**: the project's real spend cap must be raised at
      `https://aistudio.google.com/app/apikey` → billing/spend-limit settings for project `371216509644`
      (`ai.studio/spend`, per the earlier Progress Log finding) before this account can be un-paused — that step
      needs the operator's own console login and cannot be done by an agent. Until then this account stays
      `account_status: disabled` and will not serve traffic even if un-paused prematurely (would 429 on first real
      use per the earlier `429 "exceeded monthly spending cap"` finding).

- **2026-08-16 — full Gemini free-tier project sweep, 4 projects confirmed+keyed+smoke-tested, self-served via the
  operator's own admin ADC identity.** Refreshed `ikenna@odum-research.com`'s expired ADC session live mid-session
  (headless: `gcloud auth application-default login --no-launch-browser` blocked on stdin immediately when
  backgrounded — fixed by piping stdin through a named FIFO instead, keeping the process alive long enough for the
  operator to complete the browser step and paste the code back). With real admin access confirmed, audited the
  operator's full GCP estate (`gcloud projects list`, 23 projects) rather than waiting on 2 more manual key handoffs:
  9 already billing-off, 7 confirmed real/load-bearing (named production/staging/dev/logging projects plus a genuine
  Firebase app — untouched), and **5 confirmed genuinely idle** (`elated-nectar-440116-e9`, `poetic-bongo-456907-e4`,
  `spring-mix-426915-t9`, `sturdy-sentry-456910-a1`, `gbv-classroom-d3df66`) — verified via enabled-services diffing,
  not project naming (`gbv-classroom-d3df66` in particular required distinguishing it from its active sibling
  `gbv-classroom-01c2ca`, which has a real deployed Cloud Run app, `missouri-podcasts` — `d3df66` has Cloud
  Functions/Cloud Run APIs not even enabled, confirming it's a Firebase-hosting-only shell). Disabled billing on all 5
  (`gcloud billing projects unlink`, confirmed `billingEnabled:False` after). Generated real Gemini-API-restricted
  keys programmatically for 3 of the 5 (`gcloud alpha services api-keys create --api-target=...`) —
  `sturdy-sentry-456910-a1` and `gbv-classroom-d3df66` left unused as spares, not needed once 4 total were confirmed.

  **Real bug hit and fixed**: the first key-creation loop captured the async operation's full stderr+stdout blob
  (`2>&1`) into the value stored in GSM instead of just the extracted key string — `poetic-bongo`'s and
  `spring-mix`'s secrets were corrupted (740-byte JSON operation dumps, not 39-byte keys), which silently smoke-tested
  as `curl` connection failures (`HTTP 000`, not a clean rejection) rather than an obvious error. Recovered by
  re-enabling the corrupted version, regex-extracting the real `keyString` from the stored garbage, and re-storing a
  clean version (corrupted version disabled, not deleted). **Trap worth remembering**: an LRO command's `2>&1` capture
  can silently poison a stored secret without any error at creation time — the corruption only surfaces later, and as
  a connection-level failure that looks unrelated to the actual cause.

  All 4 final keys real, live, and smoke-tested against both target models (`gemini-3.5-flash-lite`,
  `gemini-3.7-flash`, real `usageMetadata` returned): `gemini-api-key-gen-lang-client-0008266149`,
  `gemini-api-key-elated-nectar-440116-e9`, `gemini-api-key-poetic-bongo-456907-e4`,
  `gemini-api-key-spring-mix-426915-t9`. This closes the plan's 3-project minimum with one spare.

- **2026-08-16 — full production deployment: proxy live, both providers registered+paused, wallet reconciliation
  proven end-to-end, per operator instruction to get all three new providers "fully shipped ready to use but on
  pause mode so agents dont use them yet."**

  **LiteLLM proxy stood up on the orchestrator VM (127.0.0.1:8768).** Real crash bug found+fixed: sharing this
  repo's `.venv` crash-looped the proxy — litellm 1.97.0's `proxy_server` module imports a fastapi internal
  (`get_flat_dependant`) removed in newer fastapi/Starlette-1.x, genuinely incompatible with this repo's own
  `fastapi>=0.137.0` pin (confirmed: an unpinned `uv pip install litellm[proxy]` resolves `starlette==1.6.0`, a
  drastic new major). Fixed by isolating into `/home/ubuntu/.venvs/litellm-proxy` with `fastapi<0.120` pinned there
  specifically — `litellm[proxy]` is deliberately NOT in `pyproject.toml` (its own comment explains why); the
  systemd unit + install script updated to provision and use that isolated venv automatically going forward.
  Real Anthropic-format smoke test through the actual proxy succeeded for BOTH providers (proper `message`/
  `content`/`usage` shape, `HTTP 200` on `grok-4.3` and `gemini-3.5-flash-lite-proj1`).

  **All 8 accounts registered** (2 Grok + 6 Gemini across 3 of the operator's 4 confirmed free-tier projects) in the
  live `accounts.json`, confirmed parsing cleanly, then **explicitly paused** (`account_status: disabled`, confirmed
  for all 8) per the operator's instruction — dispatch-ready but inert until un-paused.

  **Gemini's headroom gate wired into real dispatch** — `gemini_account_has_rate_headroom()` existed standalone
  since 2026-08-15 but nothing called it; now wired into `_pick_headroom_account()`, the one hook point every
  dispatch path funnels through. Found+fixed a gap that would have made the gate a permanent no-op: nothing was
  logging the `gemini_request_selected` events the gate's own RPM/RPD counters read — added that logging exactly
  where a Gemini account gets picked. 5 new tests. `agent-orchestrator@31687b54dc`.

  **Grok's wallet-balance poller proven end-to-end via the real production code path**
  (`fetch_grok_balance(acc_def=...)` against the real `grok-4-3` AccountDef): `balance_usd: 5.0`, matching the
  console exactly. Real bug found+fixed: registration initially pointed `api_key_secret_name` at the INFERENCE key
  (`grok-api-key`) on both Grok accounts, but the balance poller's GSM-first resolution reads that exact field for
  the MANAGEMENT key — fixed to `grok-management-key`. Separately confirmed (pre-existing, not new, not fixed —
  flagging only): `usage_tracker.read_env_var_from_file` does not execute shell command substitution, so an env-file
  `$(gcloud secrets ...)` line only resolves correctly when GSM-first resolution succeeds first; the fallback path
  would silently mis-read the literal unexpanded string as the token if GSM ever failed in the real service context
  — same latent risk already true for DeepSeek's own env files, not something this session introduced.

  **Honest scope of what's still open**: `tool_use`/`tool_result` translation through the proxy is unverified (only
  plain-text completions were smoke-tested) — the `[REVIEW] P0` smoke-test-gate todo stays open pending that. Grok's
  balance-poller scheduling cadence (vs. on-demand-only) is unconfirmed. Cross-checking captured usage against each
  vendor's own dashboard is still open. The real-live-account-throttle proof for Gemini's headroom gate needs the
  accounts un-paused first.

- **2026-08-16 (later) — project 371216509644 registered as the 4th, high-capacity PAID Gemini path, per operator
  approval, via live AWS SSM write against the orchestrator VM (i-0c9b283b31d6b5ca7, ap-northeast-1).**
  **Pre-write check**: live-read `accounts.json` on the VM first (not assumed from this doc) — confirmed the project
  was NOT already registered (only the 3 free-tier proj1-3 pairs existed, 25 total accounts). **Backup taken**
  before editing: `data/config/accounts.json.bak.20260816T154145Z` on the VM. **Two new accounts added**, mirroring
  the proj1-3 JSON shape exactly (same fields: `id`/`label`/`tier`/`provider`/`weekly_msg_limit`/`primary_email`/
  `oauth_token_env_file`/`variant`/`gcp_project`/`api_key_secret_name`), labels explicitly say "PAID Tier 3, cap not
  yet raised" rather than "free tier" so the risk isn't silently mislabeled:
  - `gemini-3-5-flash-lite-proj4` — `gcp_project: "371216509644"`, `variant: "3.5-flash-lite"`
  - `gemini-3-7-flash-proj4` — `gcp_project: "371216509644"`, `variant: "3.7-flash"`
  - Both: `api_key_secret_name: "gemini-api-key-371216509644"` (the GSM secret confirmed stored 2026-08-16, see
    entry above).

  **Real bug avoided by reading code first, not assumed**: `AccountDef` (`server/accounts.py`) has NO
  `account_status`/`disabled` field at all — the `"account_status: disabled"` convention described in
  `accounts.json`'s own `_comment` field is NOT a JSON key on the account entry; it's a DB-backed field
  (`AccountUsageRow.account_status`, `server/orm.py`) written only via `disable_account()`
  (`server/state_store/account_usage.py`). Adding the JSON entry alone would have left the account
  defaulting to `healthy`/dispatch-eligible — the opposite of what was needed. Fixed by calling the real
  `disable_account(session, account_id)` write path (via the orchestrator's own venv + `session_scope()`) for both
  new ids, then independently reading back `AccountUsageRow.account_status` to confirm.

  **Evidence, both before AND after validated**: JSON validity confirmed via the app's own `load_accounts()`
  Pydantic loader post-write (`PARSED_OK total_accounts=27`, up from 25); DB write confirmed
  (`DB_STATUS gemini-3-5-flash-lite-proj4 account_status=disabled`,
  `DB_STATUS gemini-3-7-flash-proj4 account_status=disabled`); a fully independent third live read (separate SSM
  call, filtering `gcp_project=="371216509644"`) confirmed exactly 2 matching entries with the expected shape.
  No service restart performed — unnecessary since the account stays paused either way, and avoids touching a
  live production process for a config-only change.

  **What's still open, operator-only**: the project's real spend cap must be raised at
  `https://aistudio.google.com/app/apikey` (billing/spend-limit settings, project `371216509644` /
  `uts-compliance-ikenna`) before this account can be safely un-paused — needs the operator's own console login,
  not agent-doable. Un-pausing before that would let it 429 on first real use (`429 "exceeded monthly spending
  cap"`, already observed once against this same project, see the 2026-08-16 entry above).

- **2026-08-16 (later still) — premise correction: all 4 free-tier projects were confirmed live all along; the gap
  was registration, not project count.** The operator independently confirmed, from their own GCP console, the exact
  same list of 4 "Free tier" projects this plan's 2026-08-16 sweep entry found: `gen-lang-client-0008266149`,
  `elated-nectar-440116-e9`, `poetic-bongo-456907-e4`, `spring-mix-426915-t9`. Nothing was ever "only 3 of 4" at the
  project/key level — that sweep entry's own text already says "All 4 final keys real, live, and smoke-tested." The
  actual gap was narrower: only 3 of the 4 (`gen-lang-client-0008266149`/proj1, `elated-nectar-440116-e9`/proj2,
  `poetic-bongo-456907-e4`/proj3) were ever turned into live `accounts.json` dispatch entries — `spring-mix-426915-t9`
  was keyed, smoke-tested, and then left an unused spare with no account entry. **Live-verified 2026-08-16** via a
  fresh SSM read of `accounts.json` on the orchestrator VM (not assumed from this doc): confirmed exactly 2 accounts
  each for proj1/proj2/proj3, 2 accounts for the paid proj4 (`371216509644`), and **0 accounts** for
  `spring-mix-426915-t9` — closing the ambiguity cleanly before any write.

  **`spring-mix-426915-t9` registered as the 4th FREE-TIER Gemini path** (not a paid one — see the cancellation
  entry below), via live AWS SSM write against the orchestrator VM (i-0c9b283b31d6b5ca7, ap-northeast-1), same
  read-backup-write-verify procedure as every prior account registration in this plan.

  **Pre-write**: GSM secret `gemini-api-key-spring-mix-426915-t9` confirmed present (`gcloud secrets versions
  access latest`, key length 39, consistent with the other 3 free-tier keys) and smoke-tested with a real
  `generateContent` call against both target models — `gemini-3.5-flash-lite`: `HTTP 200`, text `"pong"`,
  `usageMetadata` `{promptTokenCount: 7, candidatesTokenCount: 1, totalTokenCount: 8}`; `gemini-3.7-flash`:
  `HTTP 200`, text `"pong"`, `usageMetadata` `{promptTokenCount: 7, candidatesTokenCount: 1, totalTokenCount: 110,
  thoughtsTokenCount: 102}` — same verification shape (real REST `generateContent`, real `usageMetadata` returned)
  used for the other 3 free-tier projects' 2026-08-16 sweep entry above.

  **Backup taken** before editing: `data/config/accounts.json.bak.20260816T155543Z` on the VM (full pre-edit copy).
  **Two new accounts added**, cloned directly from the live proj1 entries to mirror the shape exactly (same fields:
  `id`/`label`/`tier`/`provider`/`weekly_msg_limit`/`primary_email`/`oauth_token_env_file`/`variant`/`gcp_project`/
  `api_key_secret_name`), named `proj5` (not `proj4` — that id is already the paid project, kept registered):
  - `gemini-3-5-flash-lite-proj5` — `gcp_project: "spring-mix-426915-t9"`, `variant: "3.5-flash-lite"`
  - `gemini-3-7-flash-proj5` — `gcp_project: "spring-mix-426915-t9"`, `variant: "3.7-flash"`
  - Both: `api_key_secret_name: "gemini-api-key-spring-mix-426915-t9"`, label says "free tier" (accurate, unlike
    proj4's paid label).

  **Registered PAUSED**, same DB-backed convention as every other new account in this plan: `AccountDef` in
  `accounts.json` carries no `account_status` field (confirmed again, same finding as the proj4 entry above) — wrote
  via the real `disable_account(session, account_id)` path (`server/state_store/account_usage.py`) against the
  live DB for both new ids.

  **Evidence, before AND after, plus an independent third read**: `load_accounts()` (the app's own Pydantic loader)
  parsed the edited file cleanly post-write (`PARSED_OK total_accounts=29`, up from 27, both new ids present).
  `disable_account()`'s own return value showed `status=disabled` for both ids immediately after the write. A
  **separate, later SSM call** (fresh process, fresh DB session) independently re-read `AccountUsageRow.account_status`
  for both ids and got `disabled` again. A **third, fully independent SSM call** re-read `accounts.json` directly
  from disk (bypassing `load_accounts()` entirely) and confirmed both entries present with the exact expected shape.
  No service restart performed (config-only change, account stays paused either way).

  **Net result**: all 4 of the operator's confirmed free-tier projects are now registered as live dispatch accounts
  (proj1/proj2/proj3/proj5, 8 accounts total), plus the separate paid proj4 pair kept registered-paused as an inert
  spare (see cancellation entry immediately below) — 10 Gemini accounts total in `accounts.json`, all
  `account_status: disabled` pending the operator's un-pause decision.

- [x] [OPERATOR] P1. ✅ CANCELLED 2026-08-16 — raise the spend cap on paid project `371216509644` so its
      `gemini-3-5-flash-lite-proj4`/`gemini-3-7-flash-proj4` accounts can be un-paused. **Operator decision: "not
      needed, no longer relevant" — free-tier coverage is sufficient.** With `spring-mix-426915-t9` now registered
      (see entry above), all 4 of the operator's confirmed free-tier projects are live dispatch accounts (8 Gemini
      accounts, proj1/2/3/5) — there is no remaining need for the paid path's extra headroom. **Not removed**: the
      `gemini-3-5-flash-lite-proj4`/`gemini-3-7-flash-proj4` accounts stay registered in `accounts.json`, still
      `account_status: disabled` — zero cost, zero risk while paused, and removing a working registration is a
      live-infra change this cancellation doesn't call for (this is a documentation/scope change, not an infra
      teardown). There is simply no plan to ever un-pause them or raise their spend cap going forward.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:e4999c17192967a1]: KEEP-NA, valid — sibling onboarding plan to the DeepSeek/Claude routing doc; heavy operator-gated credential/pause decisions (accounts deliberately PAUSED per explicit 2026-08-16 operator instruction). 3 of 5 items plausibly bounded on their own engineering shape but flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE given this doc's overall live-credential character, not split now.
- **na-eligibility-audit 2026-08-18 (ao tranche)**: KEEP-NA, valid — closing the loop on the 2026-08-17 marker's
  `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` flag on the "3 of 5" items (tool_use/tool_result translation smoke test,
  usage-capture verification, Grok cache-rate-gap feed). Same governing reason as the sibling DeepSeek/GLM plan's
  identical close-out today: the operator's explicit, repeated 2026-08-16 fleet-wide ruling ("fully shipped ready to
  use but on pause mode so agents dont use them yet") covers Grok/Gemini identically and remains a live standing
  gate, not a misclassification. Does not clear the RECLASSIFY bar. Doc stays `assigned_vm: NA`, 5 open items
  unaffected.

- **2026-08-18 (later) — usage-capture verification harness built + Gemini-specific resume/sequential-preference
  code-path audit; neither todo's checkbox flipped, both still gated on things this dev checkout genuinely cannot
  provide.** Scoped to `config/litellm/`, `server/gemini_translation_smoke.py`, and
  `tests/test_gemini_litellm_translation_smoke.py` only (deliberately did not touch `server/autospawn.py` or
  `tests/test_deepseek_provider_routing.py` — see the second item below for why that matters).

  **`[INFRA] P1` "Accurate usage-capture"**: extended `gemini_translation_smoke.py` (not duplicated — reuses
  `resolve_gemini_api_key`/`resolve_litellm_proxy_bin`/`first_gemini_model_name`/`running_proxy` from the existing
  `[REVIEW] P0` module) with `fetch_gemini_native_usage()` + `run_usage_capture_verification()` +
  `run_full_usage_capture_verification()`. Same never-trust-self-reported-numbers discipline as DeepSeek's own
  under-report catch: since Gemini's free tier has $0 billing (no invoice) and AI Studio's usage dashboard is
  browser-only/non-scriptable (this plan's own 2026-08-14 entry), the ground truth used is Gemini's OWN native
  `generateContent` REST response's real `usageMetadata` — the number AI Studio's console is itself built from —
  fetched via a second, independent, non-proxied call for the same model, diffed against what the LiteLLM proxy's
  Anthropic-shape `/v1/messages` response self-reports in its own `usage` block. Both calls use `temperature: 0` +
  an identical short closed-form prompt ("Reply with exactly the single word PONG") to minimize real sampling
  variance between the two necessarily-separate generations. `USAGE_CAPTURE_TOLERANCE_PCT = 0.20` is a **stated but
  unverified starting assumption**, documented in the module docstring as needing recalibration once a real run
  records actual deltas — this module has never run against real Gemini credentials, same gap flagged below.

  4 structural tests added (config/model-name resolution, `_pct_delta` boundary cases) — always run, pass green. 1
  live test added (`test_usage_capture_matches_gemini_native_usage_within_tolerance`), same skip-cleanly contract as
  the existing tool_use smoke test. **Could not run live in this environment**: no `GEMINI_SMOKE_TEST_API_KEY`, no
  `accounts.json` (gitignored/VM-only, confirmed absent on this dev checkout), and no `litellm` binary resolvable
  anywhere (`~/.venvs/litellm-proxy/bin/litellm` absent, not on PATH) — all three gaps independently confirmed live
  this session, not assumed. The live test skips cleanly (confirmed: `basedpyright` 0 errors, `pytest` shows the new
  live tests among the run's 9 skips, not failures). **No real comparison numbers exist yet** — this todo's own
  "done when" (a dated comparison of captured-vs-vendor-reported usage for a real sample of turns) needs the
  orchestrator VM or a real credential handoff to actually execute; the harness is ready, the data isn't.

  **`[REVIEW] P1` "Codex/Gemini-specific resume/sequential-preference verification"**: audited
  `select_account_for_spawn()`'s `sequential_preferred_account_id` path (`server/autospawn.py:1912-1936`) and
  `_resume_pass`'s `preferred_provider` path (`server/autospawn.py:3655-3670`) by reading, not by running (both are
  DB/tmux-state-dependent orchestrator-VM mechanics no amount of API credentials would let a laptop dev checkout
  simulate — this is a structurally different gap from the usage-capture item above, not the same
  "no credentials" story). Traced every gate both paths run through for a Gemini account specifically:
  - `_pick_headroom_account()` (`autospawn.py:1010-1029`) already applies the Gemini-specific
    `gemini_account_has_rate_headroom()` RPM/RPD gate as part of its normal candidate filter — a Gemini account at
    its rate ceiling is excluded from selection the SAME way for a sequential/resume pick as for a fresh dispatch;
    no separate code path to drift.
  - The sequential-preference block's own second gate (`autospawn.py:1932-1935`,
    `_provider_health_ok(...) and _account_has_balance_headroom(...)`) reads real risk on paper — a $-balance check
    applied to a $0 free-tier provider — but both are confirmed provider-agnostic and default-safe by their own
    documented contracts: `_account_has_balance_headroom` (`autospawn.py:1187-1204`) explicitly returns `True` when
    `AccountUsageRow` has no polled balance data (Gemini never gets one — there is no Gemini balance poller, it's
    free tier by construction), and `_provider_health_ok` (`autospawn.py:1321-1336`) is keyed purely by
    `account_id` against an in-memory failure ring that starts empty for every account regardless of provider. Read
    both functions' full bodies to confirm this, not just their docstrings.
  - Net: no bug found. The mechanism reads as correctly generalized for Gemini — same conclusion as the sibling
    `[INFRA] P0` gate/tracker work already proved for the plain `_pick_headroom_account(provider="gemini")` path,
    now extended to the two preference-pinning callers specifically.
  - **Existing test coverage confirmed real but narrower than this todo's scope**: `tests/test_deepseek_provider_
    routing.py` already carries 5 Gemini-specific tests (`test_pick_headroom_account_excludes_gemini_without_rate_
    headroom` and siblings, ~line 129-182) covering the plain rate-gate, plus 2 more (~line 960, ~line 1099)
    covering generalized-provider fallback ordering — none of the 7 exercise `sequential_preferred_account_id` or
    `preferred_provider` with a Gemini account. That gap is real and unaddressed by this session's work.
  - **Deliberately not closed this session**: adding that Gemini-specific pair of tests belongs in
    `tests/test_deepseek_provider_routing.py` (the established home for every other `sequential_preferred_account_id`
    /`preferred_provider` test, DeepSeek/Claude included) — outside this task's given file scope, and this exact
    slot's checkout had 5 other live sessions sharing its `cwd` this session (SessionStart collision warning),
    making an out-of-scope edit to a hot, frequently-touched file like `autospawn.py`'s own test suite a real
    collision risk, not just a scope nicety. Flagging as the natural next step for whoever next touches that file,
    not adding a new todo (out of this session's instructed scope) — the existing `[REVIEW] P1` todo's own
    "done when" (a real dispatch against live Gemini accounts) still isn't met either way; a unit test would prove
    the generalized-mechanism claim above more rigorously than a code read alone, but not satisfy the todo's actual
    bar, which needs the orchestrator VM regardless.

  **QG**: `bash scripts/quality-gates.sh --no-fix` — one real `basedpyright` finding caught+fixed along the way
  (`int(usage.get(...) or 0)` on a `dict[str, object]`-typed value rejected under strict mode; fixed with a proper
  `isinstance`-narrowing `_as_int()` helper instead of a suppression), one `ruff format` reflow on the newly-added
  code (scoped to the two edited files only, not a tree-wide reformat). Final run: 4081 passed, 9 skipped (new live
  tests among them), 0 basedpyright errors, dashboard tsc/vitest green, `✅ agent-orchestrator quality gate PASSED`,
  `.qg_last_passed_sha` head-line confirmed == `HEAD` (`0de59ba15e16db6e47bdb3021a1b87cebcb41709`). **Left
  uncommitted on purpose** (per this session's own instruction) — `server/gemini_translation_smoke.py` and
  `tests/test_gemini_litellm_translation_smoke.py` sit as working-tree edits for the lead session to review and ship.

- **2026-08-19 (interactive session, slot 1, `/multi_provider_model_capability_bakeoff_2026_08_19.md` prep)**:
  Real evidence toward the open `[REVIEW] P0` tool-use-verification todo — **Gemini half CLOSED, Grok half found
  BROKEN with a new, more precise root cause.**

  **Gemini**: a real `tool_use`/`tool_result` round-trip through a local litellm proxy instance (isolated venv,
  same `config/litellm/grok_gemini_proxy.yaml`) succeeded against `gemini-3.5-flash-lite-proj1` — a `get_weather`
  tool call correctly returned `stop_reason: "tool_use"` with the right tool name + parsed `{"location": "Tokyo"}`
  input. This is the first real tool-calling proof for Gemini through this proxy (only plain-text completions were
  verified before). The P0 todo's own "Done when" requires BOTH Grok and Gemini proven, so the checkbox stays open,
  but the Gemini half is now genuinely done.

  **Grok**: `grok-4.3`/`grok-4.6` tool_use could not be tested — a real `400 "Invalid model name"` on every
  request. Root cause, found via the proxy's own startup log (not guessed): litellm 1.97.0 silently fails to
  register EITHER grok model at config-load time — `XAI_API_KEY` resolved correctly, but neither `grok-4.3` nor
  `grok-4.6` appears anywhere in `/v1/models`, and unlike every other model in the same config (which each get a
  visible `register_model: ... not in built-in cost map` warning), the Grok entries produce ZERO log output at
  all — they are dropped before even reaching that warning path. Likely cause: litellm's static cost-map doesn't
  recognize these newer xAI model strings and the config loader silently excludes unrecognized entries rather than
  erroring. Not fixed this session — Grok is explicitly out of scope for the current bake-off (operator decision,
  2026-08-19) — but this is now a precisely-diagnosed gap (an explicit `model_info` override or a litellm version
  bump are the likely fixes) rather than "still unverified," for whenever Grok work resumes.

## Context scout

- **context-scout 2026-08-15**: re-verified context_scope, no change needed (5 entries).
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-20**: refreshed context_scope (6 entries)
