---
doc_type: plan
title: Multi-provider context accuracy + unified billing reconciliation
summary:
  Two linked problems surfaced testing the 4 new providers (Grok/Gemini/GLM/Codex) live — (1) context_used_pct, the
  number driving AO's 60% pre-compact trigger — is fed by per-turn token counts that are REAL for some providers and a
  known-fake char/4 estimate for Codex specifically, so the same uniform compact mechanism behaves accurately for some
  backends and not others; (2) there is no unified way to reconcile per-task billing to a fleet total, or to compare
  "what we spend / what we get" across metered-$, first-party-token, subscription-flat-rate, and rate-limited-free-tier
  providers on one normalized (input/output/cache-read/cache-write) basis. Human-driven — investigation, live testing,
  and design calls throughout, not bounded background-worker todos.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    context-window,
    tokenizer,
    pre-compact,
    billing,
    reconciliation,
    multi-provider,
    gemini,
    glm,
    codex,
  ]
related:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/grok_gemini_translation_proxy_2026_08_14.md,
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/issues/claude_anthropic_flat_rate_billing_calibration_2026_08_12.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-08-16
last_updated: 2026-08-20
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 6
assigned_role: infra
effort: max
drift_direction: advance-code
depends_on:
  [
    deepseek_claude_blended_provider_routing_2026_07_28,
    grok_gemini_translation_proxy_2026_08_14,
    codex_luna_flex_bridge_2026_08_14,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
context_scope:
  [
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/codex_bridge_server.py,
    agent-orchestrator/scripts/orchestrator/calibrate_account_value.py,
    agent-orchestrator/server/model_pricing.py,
    agent-orchestrator/server/orm.py,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
  ]
---

# Multi-provider context accuracy + unified billing reconciliation

## Why

Testing the 4 new providers live (2026-08-16) surfaced two related gaps that predate this session but only became
visible once real traffic flowed through real proxies:

**1. Context-window/tokenizer accuracy is NOT uniform across providers, but the mechanism that depends on it IS.**
`context_lifecycle.py`'s 60% pre-compact trigger reads `context_used_pct` by scraping Claude Code's own self-reported
"N% context used" pane text — a number Claude Code computes from the `usage.input_tokens`/`output_tokens` fields in
each turn's response. For Gemini/GLM those fields are REAL (LiteLLM/GLM's native endpoint pass through the
vendor's own usage accounting — Grok was identical before its 2026-08-18 decommission). For **Codex/Luna they are a
placeholder**:
`server/codex_bridge_server.py::_estimate_tokens` is `len(text) // 4` — a crude heuristic, explicitly marked
"never to be trusted for billing" in its own docstring. This session independently demonstrated exactly how
unreliable a naive text-length-based token estimate can be: a word-count heuristic on a real Grok 4.6 context-limit
test undercounted the real (xAI-tokenizer-measured) count by 1.6x. If Codex's fake estimate has a similar or worse
skew, `context_used_pct` for a Codex-backed session is silently wrong, and the SAME 60%-trigger mechanics that work
correctly for Gemini/GLM will misfire for Codex specifically — either compacting too early (wasted turns) or,
worse, letting a session run past its real context ceiling undetected (an uncontrolled 400 mid-session, a materially
worse failure than the "recover with a fresh session" path this codebase already has for a *known*-saturated session).

The context-window claims themselves (from vendor docs/research, not yet all live-verified) also need direct testing
rather than trusted at face value — this session tested exactly one (Grok 4.6's 500K ceiling, confirmed real and
hard-enforced, no silent server-side truncation) and found nothing wrong, but that's 1 of 9 registered models. The
same test also settled a separate, real question: **none of the raw provider APIs self-compact** — Grok 4.6 rejected
an over-limit request with a clean `400`, not a truncated/summarized response. Context self-compaction only exists as
a **Claude Code harness feature** (`/compact`), never as vendor-API server-side behavior — worth stating plainly since
it was live-tested, not assumed.

**Separately (operator correction, 2026-08-16): the self-compaction question needs re-testing through the REAL path.**
The 500K-limit test above was a raw HTTP probe directly against the proxy, bypassing Claude Code entirely — it proves
the *backend* doesn't self-compact, but says nothing about whether Claude Code's own `/pre-compact` → `/compact`
mechanism, and the skills/hooks wrapped around it, actually work correctly when the backend is Gemini/GLM/Codex
specifically (Grok was decommissioned 2026-08-18, before this verification ran for it). DeepSeek already proved this end-to-end (`deepseek_claude_blended_provider_routing_2026_07_28` Progress
Log, 2026-07-29: "CLAUDE.md/agents/\*.md need no DeepSeek special-casing — both load identically regardless of which
backend ANTHROPIC_BASE_URL points at"), but that result does not automatically transfer to the 4 new providers and
needs its own live verification, the same way DeepSeek's was actually proven rather than assumed.

**Historical incident check**: one real, already-fixed compact-related bug was located
(`agent-orchestrator@c00dc13f9d`, 2026-08-04 — a pre-Skills CLI binary silently swallowed `/pre-compact` with no
error signal). That fix is generic (pane-text detection of "Unknown command"), not provider-specific, and does not
need re-verification per new provider. **A second, different incident the operator specifically recalled — "compact
runs, but the next turn still resends the full pre-compact history as if it hadn't shrunk" — was NOT located** in
this session's search. Either it exists in a doc/conversation not yet surfaced by grep, or it's being conflated with
something else. Flagged as an open question rather than guessed at (see todo below).

**2. There is no unified, model-agnostic per-task billing reconciliation.** Two distinct goals, stated by the
operator 2026-08-16, not yet designed:

- **Reconciliation**: the sum of every task's attributed billing should equal the fleet's real total spend. Today
  this exists cleanly for DeepSeek (`task_usage` table, real per-token cost) **and, corrected 2026-08-16, for
  Anthropic too** — `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md` shipped a real, live
  `boost_multiplier` system (`compute_claude_wallet_reconciliation()`, `ClaudeWalletPanel.tsx`,
  `agent-orchestrator@616450ffac`) with real per-account numbers already pulled (Max20 accounts cluster 14x-32x; a
  genuine Pro-tier ~1047x outlier is still under investigation there, not a data bug — see that doc's own open
  todos). This plan's original framing wrongly described the Claude subscription-value question as unsolved; it
  isn't — it's the reusable PRECEDENT this plan should generalize, not a gap to fill from scratch. The 3 newer
  providers (Gemini/GLM/Codex) still have no per-task cost attribution built at all (Grok would have been a 4th,
  decommissioned 2026-08-18 before this work started — no subscription/free tier, judged not worth running).
- **Normalized bang-for-buck**: everything should reduce to input/output/cache-read/cache-write token counts so
  providers are comparable regardless of billing shape — metered-$ (DeepSeek), first-party token counts we trust
  (Anthropic, Gemini), subscription-flat-rate where the real value per dollar is now KNOWN for Claude (see above) but
  still genuinely UNKNOWN for GLM's Coding Plan (the one remaining real "Sonnet multiplier"-shaped gap — no
  equivalent calibration has been built for GLM's flat-rate subscription), and rate-limited-free-tier where "spend"
  doesn't exist but capacity does (Gemini's free tier — remaining-RPD-as-a-proxy needs a tested methodology, not an
  assumption). **Every number that lands in this system should be the provider's PUBLISHED rate** (not a computed
  effective rate) — that published number times real token counts is what answers "how much bang for the buck are we
  actually getting" against what we pay.

Real turn-shaped variance matters here too, not just $/token: "some models are cheap per turn but need many turns;
some are cheap per token but burn a lot of them" (operator, 2026-08-16) — a single-prompt test (what this session ran)
is a proxy, not a real workflow, and the eventual dashboard needs to show real per-task turn counts alongside token
counts once this reconciliation layer exists, so that distinction is visible on real work, not just a synthetic probe.

**Backfill is explicitly required, not optional** (operator ruling, 2026-08-16): whatever reset-aware reconciliation
mechanism gets built must be run back across ALL existing `account_usage_history`, not just applied going forward —
the existing ledger's reset-crossing windows should be reconciled, not left as dropped/unknown data.

## Non-goals

- Not rebuilding `calibrate_account_value.py`'s conservative single-clean-window design — that script answers a
  narrower, different question ($-per-percent-multiplier for ONE quota window) and merging across a reset there would
  genuinely corrupt that specific calculation (two different weekly-budget dollar values, ambiguous transcript
  attribution). The new reset-aware primitive is additive, not a replacement for that script.
- Not attempting to make Gemini's free tier report a dollar cost — it's genuinely $0. The goal there is a tested
  capacity-consumption proxy, not inventing a price that doesn't exist.
- Not building this as an AO-dispatched background-worker plan — see the operator's explicit "human plan" instruction,
  2026-08-16. The design calls and live-testing judgment here don't fit the AO-eligible bar (deterministic,
  worker-executable outcome).

## Todos

- **[OPERATOR] P2. CANCELLED — SUPERSEDED 2026-08-16 (operator confirmed this no longer occurs).** Was: Point at the actual incident doc/conversation for "compact runs but the next turn resends the
      full pre-compact history as if it hadn't shrunk" — this session's grep found the 2026-08-04 unsupported-binary
      incident (a different failure mode, already fixed, generic) but not this one. Done when: either the real
      incident is located and its fix's generality (provider-specific vs. generic) is confirmed, or the operator
      confirms it should be independently re-tested rather than assumed to be the same class of bug.
- [~] [INFRA] P0. Fix Codex/Luna's fake token-count estimate (`_estimate_tokens = len(text)//4`,
      `codex_bridge_server.py`) — confirmed unreliable via this session's own 1.6x-off word-count test on a real
      tokenizer comparison. **PARTIAL `agent-orchestrator@f7214e31b5` (shipped 2026-08-19)** — the "easy fix" this
      todo predicted was real: `openai_codex._run.TurnResult.usage: ThreadTokenUsage | None` already carries real
      per-turn accounting (`.total`/`.last`, each a `TokenUsageBreakdown`: `cached_input_tokens`, `input_tokens`,
      `output_tokens`, `reasoning_output_tokens`, `total_tokens`) — confirmed by reading
      `.venv/lib/python3.13/site-packages/openai_codex/_run.py` and `generated/v2_all.py` directly, not assumed.
      Both `run_codex_turn` (plain-text path) and `_drive_codex_turn`'s `TurnFinished` (tool-use completion path)
      now thread this through to `translate_codex_result_to_anthropic` via a new `_codex_usage_to_anthropic_usage`
      mapper (`codex_bridge_server.py`) instead of estimating. **Live-verified field-mapping, not guessed**: a
      real 2-turn same-thread SDK probe (`gpt-5.6-luna`, real `~/.codex/auth.json`) proved OpenAI's
      `cached_input_tokens` is a SUBSET of `input_tokens` (turn 2's `last`: `cached=13056 input=14006 output=6
      total_tokens=14012`, and `14006+6 == 14012` — total excludes cached, confirming subset not additive), unlike
      Anthropic's own additive `cache_read_input_tokens` shape — so the mapper does
      `anthropic.input_tokens = codex.input_tokens - codex.cached_input_tokens` (not a straight rename) to avoid
      double-counting/inflating `context_used_pct`; `reasoning_output_tokens` folds into Anthropic's single
      `output_tokens` (same "reasoning bills as output" convention Claude's own extended thinking uses). The ONE
      remaining estimate: the mid-turn `tool_use` pause response (`translate_tool_call_paused_to_anthropic`) — real
      usage genuinely doesn't exist yet at that point (the Codex turn hasn't reached a terminal state; see
      `_tiktoken_estimate`'s own docstring for why capturing it live would mean a materially riskier rewrite of the
      just-shipped pause/resume machinery, not attempted here) — now a real `tiktoken` (`o200k_base`) count instead
      of `len(text)//4`, per this todo's own explicit fallback instruction. Quality gates green
      (`bash scripts/quality-gates.sh --no-fix`: ruff/basedpyright clean, 4210 passed/8 skipped pytest, dashboard
      tsc/454 vitest green — the first run caught a real gap, `uv lock` alone doesn't `uv sync` a new dependency
      into `.venv`, `basedpyright` flagged `tiktoken` unresolved until `uv sync` ran). **NOT yet done**: (1) this
      fix hasn't been deployed to the production `codex-bridge.service` VM — LDR only auto-pulls the main
      `orchestrator` service, `codex-bridge` needs the same manual `uv sync` + restart
      `codex_mcp_tool_use_bridge_2026_08_18.md`'s Progress Log already documents; (2) the full "Done when" bar
      (cross-check against the real ChatGPT/Codex usage DASHBOARD, a login-gated web page) needs either operator
      access or a real sample of fleet-dispatched Codex turns to check against — neither exists yet while
      `codex-luna` stays operator-gated disabled (`codex_mcp_tool_use_bridge_2026_08_18.md`'s still-open unpause
      todo, now flagged ready for operator review). Tracked as the 2 new todos immediately below rather than left
      as unstructured prose.
- [ ] [INFRA] P1. New (2026-08-19) — deploy the real-usage fix above (`agent-orchestrator@f7214e31b5`) to the
      production `codex-bridge.service` VM: `uv sync` (installs the new `tiktoken` dependency — `ao-self-pull.sh`
      pulls code only, confirmed does not run `uv sync`) then `systemctl restart codex-bridge`, same two-step
      pattern `codex_mcp_tool_use_bridge_2026_08_18.md`'s Progress Log already used for the `mcp` dependency. Low
      risk to do ahead of the operator's unpause decision (zero real traffic on this service today) — doing it now
      means accurate usage is already live the moment real dispatch starts. Done when: a real post-deploy smoke
      test against the VM's `codex-bridge.service` shows non-estimated (`TurnResult.usage`-sourced) numbers in the
      response, not the old `len(text)//4` shape.
      **STILL NOT DONE, live-confirmed 2026-08-20** (investigating the slot-31 context-99% incident below): SSM'd
      directly into `i-0c9b283b31d6b5ca7`'s real `codex-bridge.service` checkout
      (`/home/ubuntu/unified-trading-system-repos/agent-orchestrator`) — the checked-out `server/codex_bridge_server.py`
      DOES already carry the real-usage mapper (`_codex_usage_to_anthropic_usage`, 2 matches), but
      `.venv/bin/python -c 'import tiktoken'` still raises `ModuleNotFoundError` — `uv sync` was never run. The
      service HAS restarted since the code landed (`systemctl show codex-bridge`: `ActiveState=active`,
      `ExecMainStartTimestamp=2026-08-20T00:10:46Z`), so this is a restart-without-`uv-sync`, not a not-yet-restarted
      state — the exact half-deployed condition this todo's own "Done when" bar was written to catch. `codex-luna`
      is enabled and live-dispatched right now (slot 31), so this is not a hypothetical.
- [ ] [REVIEW] P2. New (2026-08-19) — once real fleet traffic flows through Codex/Luna (gated on
      `codex_mcp_tool_use_bridge_2026_08_18.md`'s operator-gated unpause, not mine to flip), cross-check a real
      sample of captured token counts against the actual ChatGPT/Codex usage dashboard within a stated tolerance —
      the one part of this todo's original "Done when" bar that genuinely cannot be satisfied before real traffic
      exists (no dashboard access from this session either — needs either operator visual confirmation or a
      dashboard-scraping mechanism neither of which exists today).
- [ ] [REVIEW] P1. **Narrowed 2026-08-18 (Grok decommissioned)** — verify Claude Code's own end-to-end
      `context_used_pct` display is accurate for Gemini/GLM — the individual API responses carry real vendor-reported
      usage (confirmed this session), but the CUMULATIVE session-level percentage Claude Code itself computes and
      displays has not been independently checked end-to-end. Done when: a real multi-turn session against each of
      the 2 providers shows a `context_used_pct` reading that tracks real cumulative token consumption within a
      stated tolerance.
- [ ] [REVIEW] P0. **Narrowed 2026-08-18 (Grok decommissioned)** — live-test `/pre-compact` and `/compact` through
      the REAL harness (not a raw HTTP probe) for each of Gemini, GLM, and Codex — spawn real `claude` CLI sessions
      against each new account, run long enough to approach or force the 60% threshold, and confirm: (a) the
      skill/command actually executes (not silently swallowed), (b) `context_used_pct` genuinely drops afterward —
      proving compaction reduces what gets resent, not just that the command ran, (c) CLAUDE.md/skills/hooks behave
      identically to the already-proven DeepSeek case. Done when: a dated Progress Log entry records this for all 3
      remaining providers, each independently verified, not assumed to transfer from DeepSeek's or each other's
      result.
      **Real live failure observed for Codex specifically, 2026-08-20 (not yet the full test above, but directly
      relevant new evidence)**: operator reported slot 31 (real `codex-luna` dispatch, `used_by_slots: [31]`
      confirmed via `/api/accounts`) hit 99% context in the dashboard before compacting — AO's 60%/70% guided
      pre-compact/compact tiers never intervened; only Claude Code's own hard auto-compact eventually fired
      (`compactions_total: 11` on this slot, `last_compacted_at: 2026-08-20T05:22:59Z`, matching the operator's "now
      around 30%" observation). Root cause traced to the model-window-registration gap, see the new `[INFRA] P0`
      todo below — not yet the systematic multi-turn test this todo asks for, but real, unplanned confirmation that
      Codex's `/pre-compact`→`/compact` path is NOT yet proven safe end-to-end.
- [x] ✅ [INFRA] P0. **New (2026-08-20, live incident — root cause of the slot-31 context-99% failure, `[REVIEW] P0`
      above)** — register `gpt-5.6-luna` in `model_tier._ALLOWED_MODEL_WINDOWS`, or give it `is_deepseek()`-style
      special-casing in `context_probe.context_window_for()`. Confirmed by reading `model_tier.py` directly:
      `_ALLOWED_MODEL_WINDOWS` is a CLOSED set — the 5 Anthropic snapshots
      (haiku-4-5/sonnet-4-6/sonnet-5/opus-5/fable-5) plus DeepSeek matched by substring — and `gpt-5.6-luna` (the
      real `message.model` string the bridge echoes into the transcript, confirmed live) is in neither, so
      `context_window()` would raise `UnknownModelContextWindowError` for it. Because a learned-registry entry
      already exists for it, `context_window_for()` never even reaches that failure — it takes the STORED
      `calibrated_window` instead, with NO guard against the "poisoned calibration" bug class already documented
      for DeepSeek/sonnet-4.6: Claude Code doesn't recognise an unregistered model string, falls back to its own
      ~200K internal guess, and a pane-scraped pct calibrated against THAT wrong denominator gets stored as real.
      DeepSeek is protected by an explicit `is_deepseek()` early-return; `gpt-5.6-luna` had no equivalent.
      **Live-confirmed 2026-08-20** via `data/state/learned_context_windows.json` on `i-0c9b283b31d6b5ca7`:
      `gpt-5.6-luna` → `calibrated_window: 263941`, `watermark_hits: 1` (not yet corroborated —
      `_WATERMARK_CONFIRM_HITS` is 3) — a suspiciously ~200-280K figure sitting in exactly the same band as the
      CLI's known-wrong DeepSeek/sonnet-4.6 fallback (see the correction below — the real figure is smaller still).
      A too-small learned window does not by itself explain a run to 99% (it would make AO's pct read HIGH,
      compacting too early not too late) — the codex-bridge fake-token-estimate deploy gap (`[INFRA] P1` above) is
      the more likely DIRECT cause, with this as a compounding, independently-real problem. Done when: `gpt-5.6-luna`
      has a real registered prior or deepseek-style guard, AND the stale `263941` entry is purged.
      **DONE `agent-orchestrator@e307fa5897`** — widened beyond just Codex/Luna per operator ask ("wire in the real
      actual context window numbers for all the models that AO supports... check official docs").
      `model_tier._ALLOWED_MODEL_WINDOWS` grew from 5 Anthropic-only entries to 16 total: DeepSeek folded in as literal
      keys (was a separate substring branch), plus `glm-5.3`/`glm-5-turbo`, `kimi-k3`/`kimi-k2.6`/`kimi-k2.7-code`,
      `gemini-3.5-flash-lite`/`gemini-3.7-flash`, `gemma-self-hosted`, `gpt-5.6-luna` — each sourced from that
      vendor's own docs (citations in `model_tier.py`'s per-constant comments), deliberately EXCLUDING
      retired/superseded snapshots `model_pricing.py` keeps for historical billing only
      (`claude-opus-4-6/4-7/4-8`, `claude-sonnet-4-5`, the 2 NVIDIA Gemma entries, `devstral-latest`) — registering
      those would reopen the exact hole the retired-snapshot regression test exists to catch. **Correction to this
      todo's own number above: `gpt-5.6-luna`'s real registered window is 272,000, NOT 1.05M** — Codex/Luna runs
      through the Codex App Server/CLI, whose own real enforced metadata for GPT-5.6 Sol/Terra/Luna is 272,000;
      `codex_bridge_server.py` never unlocks the raw spec, so registering it would have repeated the sonnet-4.6
      mistake exactly — see the corrected `[REVIEW] P2` todo below. **Also generalized the mechanism, not just the
      numbers**: new `model_tier.is_anthropic_native()` + narrower `is_known_proxied_model()` (registered AND
      non-Anthropic — deliberately not "any unrecognised string", so a genuinely novel future model keeps the
      default calibration-trusting behavior until specifically investigated) — `context_window_for()`/`observe()`'s
      calibration gate now trust the registered prior for every known-proxied model, not just DeepSeek. Full
      `quality-gates.sh` green (5226 backend + 463 dashboard tests, coverage ratchet matched baseline). **Still
      open**: purging the now-inert `calibrated_window: 263941` VM entry (code ignores it going forward); the
      `[INFRA] P1` and `[REVIEW] P0` gaps above.
- [ ] [REVIEW] P2. **Narrowed 2026-08-18 (Grok decommissioned, its 4.3's 1M claim dropped — untested and now moot)**
      — live-test the remaining context-window claims from this session's research table (GLM's 1M/131K, Gemini's
      1,048,576/65,536 — already confirmed live for Gemini, DeepSeek's 1,048,576/384,000,
      GPT-5.6's **272,000 as actually enforced by Codex CLI for Sol/Terra/Luna — corrected 2026-08-20, see the
      `[INFRA] P0` todo above; the raw API spec is 1.05M/128K but that is NOT what this fleet's bridge dispatches
      against**) the same way Grok 4.6's 500K was — a real oversized request, built on-host to avoid transport
      payload limits, confirming the vendor/CLI enforces its documented ceiling and does not silently truncate.
      Done when: each is either confirmed live or explicitly flagged as still resting on published docs only.
- [ ] [INFRA] P1. Design + build the reset-aware rolling-window cumulative-consumption primitive: given a wall-clock
      period that may cross one or more quota resets, compute TRUE total consumption as
      `(100 - pct_at_period_start) + pct_at_first_reset_boundary + ... + pct_at_period_end`, chained across every
      reset the period spans, using the existing `*_window_start`/`*_resets_at` fields `account_usage_history`
      already carries. Additive to, not a replacement for, `calibrate_account_value.py`'s existing conservative
      single-window design. **Refinement (operator, 2026-08-16): raw percentages are only addable across a reset if
      the account's TIER stayed constant for the whole period.** A pre-reset 1% (e.g. of a Pro $20/wk budget) and a
      post-reset 25% (e.g. of a Max $200/wk budget, if the account was upgraded — or if it's simply a DIFFERENT
      account/model entirely) are not the same unit and cannot be summed as "26%" — each segment must be converted to
      a common unit (dollars, via the same prorated-budget method `compute_claude_wallet_reconciliation` already
      uses) BEFORE summing, using whichever tier/account was actually active during THAT segment. This requires
      tier/account identity tracked PER SEGMENT, not read once at query time as "whatever the account's current tier
      is now" — check whether `account_usage_history` (or any sampled table) already carries a tier snapshot per row;
      if not, that's a real gap to close as part of this same todo, not a separate one. Done when: a real historical
      window that crosses at least one confirmed reset produces a correct, testable total (verified against real
      5h/weekly reset timestamps in the live data, not synthetic), AND a synthetic/real case where the tier changed
      mid-window is handled correctly (dollar-normalized, not raw-percentage-summed).
- [ ] [INFRA] P1. Backfill the reset-aware primitive across the FULL existing `account_usage_history` table —
      explicit operator requirement (2026-08-16): this is not going-forward-only. Must use the tier-per-segment logic
      above, not a naive percentage sum, for any historical window where the account's tier changed. Done when: every
      historical reset-crossing window in the live table has a computed, correct cumulative-consumption value, not
      left as dropped/unknown.
- [ ] [UI] P2. **New, operator 2026-08-16**: once a window's tier/account changed mid-window, its `boost_multiplier`
      (both the existing `ClaudeWalletPanel.tsx` and any new per-provider equivalent this plan builds) must be
      VISIBLY marked unreliable, not silently shown as a normal number — a dashed/red indicator with a hover reason
      ("account switched mid-window: sub-X → sub-Y" or "tier changed: pro → max20"). This is per-window, not
      per-account: a 1h window fully inside one tier is still a valid, normal-styled multiplier; the SAME account's
      lifetime view spanning a tier change is not. Depends on the tier-per-segment tracking in the todo above (the
      flag can't be computed until segment tier identity is actually tracked). Done when: a real window with a tier
      change renders visibly flagged, and a real window without one renders normally, side by side.
- [x] ✅ [DATA] P1. Design the unified per-task billing schema — draft below, from real pilot evidence (isolated local
      pilot, 2026-08-19: real `claude` CLI dispatches against GLM/Gemini/Codex/Gemma, plus real dashboard
      cross-checks), not a from-scratch guess. Must generalize DeepSeek's existing `task_usage` table rather than
      create a second, parallel per-task ledger.

      **Common per-task fields (confirmed uniform across every provider's `claude --output-format json` output —
      this shape already exists today, nothing to invent here):** `task_id`, `provider`, `requested_model` (what
      the account config asked for), `served_model` (what the response's own `model` field reports — MUST be
      tracked separately from `requested_model`: GLM's server-side aliasing, confirmed both by a live response
      header AND by real Zhipu billing data 2026-08-19, means a `glm-5.2` request is actually billed as `glm-5.3` —
      any schema keyed on the requested model alone will misattribute cost), `num_turns`, `duration_ms`,
      `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`.

      **`tokens_per_second` (decode speed) — new field, operator ask 2026-08-19**: track this alongside token
      counts wherever a provider exposes it. Confirmed real and provider-published for GLM (Zhipu's own "System
      Health" dashboard panel: Lite tier peaked ~98 tok/s over the last 7 days, currently ~60; Max&Pro tier peaked
      ~115, currently ~80) — first real throughput numbers on record for any of the newer providers. Check
      per-provider availability (Gemini/NVIDIA's `nvext.timing`-style response metadata, per the Gemma onboarding
      plan's own real telemetry finding, is a likely second real source) rather than assuming every provider
      exposes it the same way.

      **Per-provider billing-SHAPE categorization (real, not assumed — 5 distinct shapes, not 2)**:
      1. `metered_dollar` (DeepSeek — real, existing `task_usage` precedent; Kimi — real $ wallet exists per
         `kimi_gemma_provider_onboarding_2026_08_16.md`, not yet schema-integrated).
      2. `subscription_boost_multiplier` (Anthropic/Claude — real, existing, `ClaudeWalletPanel.tsx`).
      3. `subscription_credits` (GLM — **confirmed 2026-08-19, a genuinely distinct third shape**: Zhipu's own
         dashboard tracks a "Credits" unit directly — 2,000/5h + 10,000/week on the real Lite-Monthly plan — that is
         neither a dollar figure NOR a raw prompt-count; `server/glm_quota_poller.py` currently estimates against
         the WRONG unit, prompt-count, per the real bug found and filed in
         `deepseek_claude_blended_provider_routing_2026_07_28.md`'s new `[INFRA] P2` todo — fix that first, this
         schema should read the corrected poller, not re-derive credits itself).
      4. `rate_limited_free` (Gemini, NVIDIA/Gemma — no $ or credits from the vendor at all, only RPD/RPM/TPM
         consumed against a real ceiling; Gemini's real numbers checked 2026-08-19 via Google AI Studio's own
         dashboard: 3.5 Flash Lite sat at 21/500 RPD, 4/15 peak RPM, 164.37K/250K peak TPM over the trailing 28
         days — real, low-headroom-risk evidence this tier has room, not a guess).
      5. `subscription_unknown` (Codex/Luna's ChatGPT Plus — NOT YET checked against a real dashboard this session;
         do not assume it matches GLM's credits shape or Claude's boost-multiplier shape without verifying against
         OpenAI's own usage page first).

      Every non-`metered_dollar` shape should ALSO carry a `computed_usd_equivalent` (using `model_pricing.py`'s
      published per-token rate) purely for cross-provider comparison — clearly labeled as computed, never presented
      as a real bill, per this plan's own "PUBLISHED rate, not a computed effective rate" rule above.

      Done when: a design doc or schema proposal covers all 7 currently-registered providers with a concrete field
      mapping for each, incorporating the 5-shape categorization and `tokens_per_second` field above (Grok
      decommissioned 2026-08-18, dropped from scope).
      **DONE `agent-orchestrator` (shipping this session)** — see 2026-08-19 Progress Log entry below for the full
      field-mapping table and evidence. Directly unblocks the `[UI] P2` billing-display todo below, which names this
      exact todo as its own real sequencing constraint.
- [x] ✅ [DATA] P1. Build a minimal v0 capture mechanism so real testing stops losing its own history — operator ask
      2026-08-19, after a pilot session's real GLM/Gemini reconciliation had to be done entirely by hand (CLI JSON
      output cross-checked against vendor dashboards manually, nothing persisted anywhere in AO). Scope: FIRST
      investigate how AO's real dispatch path currently captures a worker's completion evidence today (is
      `--output-format json`'s structured output already parsed anywhere, or only tmux pane text watched? — check
      before assuming) — extend whatever that real mechanism is to persist the common per-task fields above into a
      generic `task_usage`-shaped row for every provider, not just DeepSeek. This is v0: persistence only, not the
      full reconciliation/UI work the other todos here cover — but it's the prerequisite that makes every later
      todo here actually possible instead of a one-off manual exercise each time. Done when: a real AO-dispatched
      task against a non-DeepSeek provider leaves a real, queryable row behind with no manual capture step.
- [~] [UI] P2. **New (2026-08-19)** — display the unified per-task billing schema (the `[DATA] P1` schema-design
      todo above) once real data actually flows through the `[DATA] P1` v0-capture-mechanism todo above: a view
      showing `requested_model` vs `served_model` (flagged when they diverge — e.g. GLM's server-side
      `glm-5.2`→billed-as-`glm-5.3` aliasing), `tokens_per_second` where the provider exposes it, and the 5-shape
      billing categorization (`metered_dollar` / `subscription_boost_multiplier` / `subscription_credits` /
      `rate_limited_free` / `subscription_unknown`) with each row's `computed_usd_equivalent`.

      **Design (two complementary surfaces, not one monolithic new panel — researched against the real dashboard
      this session, `agent-orchestrator/dashboard/src/`)**:
      1. **Per-task drill-down** — extend `BacklogDetailModal`'s existing per-attempt table (`App.tsx` ~line 3505,
         the only place a single task's real per-attempt usage already renders: Input/Cache write/Cache read/
         Output/Reasoning/Total/Spend/Session) with 3 new columns: served model (shown only when it diverges from
         the attempt's already-rendered provider/model), tok/s, and a billing-shape badge. This is the natural
         per-task grain — do not build a second, parallel per-task table next to it.
      2. **Fleet-wide billing-shape overview** — sits BESIDE `TaskUsageWindowsPanel.tsx` (the existing windowed/
         provider-filtered aggregate view), same fetch/poll/provider-filter pattern, adding a billing-shape
         dimension so $ spend is comparable across metered/subscription/free-tier providers on one screen instead
         of requiring a separate wallet panel per provider (today: Claude/DeepSeek/Kimi have one, Gemini/NVIDIA
         have a capacity-only variant, GLM/Codex have none — see the GLM/Codex wallet-reconciliation `[DATA] P1`
         todo above).

      **Prep work already shipped ahead of the schema landing (2026-08-19, this session)**: the panel's
      "which provider/model is currently usable" signal needs the same live-derived pattern `KimiWalletPanel.tsx`'s
      `allKimiAccountsPaused()` and `NvidiaCapacityPanel.tsx`'s `degradedNvidiaAccounts()` already use, generalized
      so it doesn't require a bespoke wallet/capacity panel per provider first. Studying those two surfaced a real,
      currently-shipping gap, fixed as real prep rather than left as a TODO: the generic Accounts panel's own "N/M
      available" counts (`AccountsPanel`/`AccountProviderGroup`, `layout.tsx`) only ever checked
      `status === "healthy"`, blind to `health_status` — an enabled-but-degraded account (`status: "healthy"`,
      `health_status: "degraded"`, e.g. NVIDIA's real `gemma-4-31b-it` per
      `/plans/active/issues/gemma_4_31b_it_persistent_timeout_2026_08_19.md`) silently counted as available. Fixed
      via a new `isAccountAvailableForDisplay()`, deliberately NOT merged into the existing `accountIsUsable()`
      (`layout.tsx:549`) — that one mirrors AutoSpawn's own dispatch-eligibility definition verbatim (its own
      docstring says so) and has no opinion on `health_status`; conflating the two would silently change dispatch
      semantics, a decision this UI-display task has no business making. Also added a generic per-row "⚠ Degraded"
      badge in `AccountRow` that fires for ANY provider's `health_status: "degraded"` account, not just NVIDIA's
      existing bespoke banner. Real, tested, and already live in the generic Accounts panel today — not gated on
      the new schema at all, and directly reusable as the future panel's own availability signal.

      **Evidence**: `agent-orchestrator@befc0e3723` — `dashboard/src/layout.tsx` (`isAccountAvailableForDisplay`,
      wired into both the top-level `AccountsPanel` count and each `AccountProviderGroup` count, plus `AccountRow`'s
      new badge), `dashboard/src/layout.test.ts` (5 new vitest cases), `dashboard/tests/e2e/provider-badge.spec.ts`
      (1 new Playwright case against the real e2e fixture `nvidia-gemma-4-31b-demo` — confirms `1/2` not `2/2`, and
      the badge fires only on the degraded account). Full `quality-gates.sh --no-fix` green (4146 passed/8 skipped
      pytest, basedpyright 0 errors/0 warnings, dashboard `tsc` clean, 432/432 vitest); `pw:L2 ✓` —
      `provider-badge.spec.ts` 6/6 passed against the real e2e stack (`mode=mock`).

      **Real sequencing constraint (do not build the full panel before this lands)**: the per-task grain fields
      (`requested_model`/`served_model`/`tokens_per_second`/billing-shape) don't exist on `TaskUsageRow`/
      `TaskUsageView` yet — that's the `[DATA] P1` schema todo above, still open. Building this panel's real
      data-fetching now would mean either faking the schema or wiring against fields that don't exist yet — wait
      for that todo (and the v0-capture-mechanism todo, so real rows actually populate) to land first. Done when:
      `BacklogDetailModal`'s per-attempt table shows real served-model/tok-per-sec/billing-shape data for at least
      one non-DeepSeek/non-Claude provider task, and the fleet-wide billing-shape overview renders real $ figures
      for at least 2 of the 5 billing shapes side by side.
- [x] ✅ [DATA] P1. Reconciliation proof: sum of every task's attributed billing (once the schema above is populated for
      a real window) must equal the fleet's real total spend for that window, per provider. Done when: a dated
      Progress Log entry shows this reconciling within a stated tolerance for at least DeepSeek + one new provider.
      **DONE by finding** — see 2026-08-19 Progress Log entry below: `compute_deepseek_wallet_reconciliation`
      (DeepSeek) + `compute_kimi_wallet_reconciliation` (Kimi, a genuinely new provider) already existed, already
      shipped, already tested with real tolerance-bound numbers.
- [x] ✅ [REVIEW] P2. Gemini free-tier capacity-as-proxy methodology: design and run a real test that translates
      "remaining RPD/RPM capacity in a given window" into a spend-equivalent comparison figure, the way
      `gemini_headroom.py`'s ceilings are already tracked for dispatch-gating — this is the same underlying data,
      repurposed for the reconciliation/comparison goal rather than just the dispatch gate. Real starting data point
      (2026-08-19): a single real 5-turn CLI task against `gemini-3.5-flash-lite` consumed 16,204 input +
      16,211 cache-read tokens per the CLI's own report — cross-reference against Google's real TPM-peak reading in
      the same window (~120-130K, i.e. several real calls stacked in one minute) to calibrate the methodology
      against, rather than starting from zero. Done when: a documented, tested methodology exists, not just the raw
      ceiling numbers already recorded.
      **DONE `agent-orchestrator` (shipping this session)** — `gemini_headroom.tpm_capacity_consumed_pct()`,
      calibrated exactly against the real 2026-08-19 data point above (12.97%). See 2026-08-19 Progress Log entry.
- [ ] [REVIEW] P2. Verify the "manual/interactive Claude usage sits on separate accounts from AO dispatch" assumption
      is actually true today, not just believed — this is the stated precondition for treating AO's own usage
      tracking as clean/isolated from personal usage. Done when: the account roster is checked against what AO
      actually dispatches to vs. what's used interactively, and any overlap is flagged.
- [ ] [UI] P3. Once the reconciliation layer exists, surface real per-task turn counts alongside token counts on the
      dashboard — the stated reason for building this at all: "some models are cheap per turn but need many turns;
      some are cheap per token but use lots of tokens" is only visible on real task data, not a synthetic single-prompt
      probe. Done when: a real dispatched task's turn count and token count are both visible in one place.
- [ ] [SCRIPT] P1. New, operator-refined 2026-08-17, step 1 of the Codex/GLM subscription-model workstream below —
      confirm real end-to-end task completion through AO's actual backlog/worker path (not a raw HTTP or direct-CLI
      smoke test) for both GLM and Codex specifically. Check each account's current `account_status` first (may
      already be `disabled`/paused per the same "register paused until routing exists" pattern used for
      Kimi/Gemma, `kimi_gemma_provider_onboarding_2026_08_16.md` — not yet confirmed for GLM/Codex, do not assume
      either way); if paused, that's an explicit operator call before unpausing, not a default action to take
      unilaterally. Done when: at least one real backlog task exists in `task_usage` for a GLM account and one for a
      Codex account, each completed through the normal `/done` gate (not a synthetic/manual row).
- [ ] [REVIEW] P1. New, operator-refined 2026-08-17, step 2 — determine each provider's REAL usage-limit metric before
      building any reconciliation math on top of it. Operator's own framing: "Codex usage limit and GLM's usage
      limit: one's based on messages, I think, and one's based on tokens" — explicitly not yet verified, don't build
      on the assumption. Check each vendor's own docs/account dashboard directly (same live-verification discipline
      the sibling `kimi_gemma_provider_onboarding_2026_08_16.md` plan already used for model names/pricing — trust a
      live source, not vendor marketing copy or memory). Done when: both GLM's and Codex's real usage-limit unit
      (messages vs. tokens) and the real numeric cap are confirmed against a live source, cited by URL/screenshot,
      not guessed.
- [ ] [DATA] P1. New, operator-refined 2026-08-17, step 3 — build the wallet-reconciliation / `boost_multiplier`
      calculation for GLM and Codex, generalizing `compute_claude_wallet_reconciliation()`
      (`claude_anthropic_flat_rate_billing_calibration_2026_08_12.md`, shipped `agent-orchestrator@616450ffac`) —
      read real token usage plus the real usage-limit-percentage-consumed (from the todo above) and convert it into
      an implied/API-equivalent spend, the same "what would this usage have cost as pay-per-token" shape Claude's
      multiplier already computes. Depends on the usage-metric todo directly above — do not build against an assumed
      metric. Also wire the display side: extend `dashboard/src/layout.tsx:4485`'s `isDeepseek`-only branch to a real
      `providerUsageKind(provider)` lookup so Codex/GLM stop inheriting the raw `weekly_msg_limit=240` default
      (`server/accounts.py:142`) with no live signal behind it, and render the same weekly/5-hour + boost-multiplier
      columns Anthropic already has (`ClaudeWalletPanel.tsx`). Done when: a real computed `boost_multiplier` exists
      for at least one GLM and one Codex account, backed by real usage data, and both render in the dashboard using
      the same columns as Anthropic — apples-to-apples once tasks start flowing to all three, per the operator's
      stated reason for doing this at all.
- [ ] [REVIEW] P1. New, operator-refined 2026-08-17, step 4 — three-way reconciliation check for GLM and Codex: does
      (a) AO's own computed implied-spend/usage-pct (from the todo above), (b) what the provider's own site/docs
      state as the plan's limits and real consumption, and (c) the actual dollar amount paid for the subscription,
      all agree? This is the "check that dollars spent are recorded correctly" check the operator asked for
      explicitly, not just a one-sided computation. Done when: a real 3-way comparison table exists in this doc's
      Progress Log for both GLM and Codex, with any mismatch explained (not silently dropped).
- [x] ✅ [UI] P2. New, operator-refined 2026-08-17 — for Gemma (NVIDIA NIM, free tier): explicitly SKIP the $/
      boost-multiplier reconciliation above — operator's own words, "there's nothing to really reconcile with," and
      it's genuinely $0 (see this plan's existing Non-goals section, same principle already applied to Gemini's free
      tier). But still show REAL request/token counts on the dashboard, not a placeholder, an omitted panel, or a
      copy of another provider's shape. Done when: Gemma's account row shows real usage numbers with no
      reconciliation math attached, visibly distinct from the metered/subscription rows (not silently blank or
      mislabeled as reconciled). **DONE — already shipped `agent-orchestrator@0c0e527`, found + cross-linked
      2026-08-18 via `kimi_gemma_provider_onboarding_2026_08_16.md`'s own Progress Log (that doc's author flagged
      this exact drift: the shipment was never recorded here).** `server/nvidia_headroom.py` (shared-key RPM gauge)
      + `GET /api/accounts/nvidia/capacity` (`server/routes/accounts.py:924`) + `NvidiaCapacityPanel.tsx` (wired
      into `App.tsx`, no $ reconciliation math, visibly distinct panel type from the Wallet panels) +
      `dashboard/tests/e2e/nvidia-capacity.spec.ts` (real Playwright e2e spec). — /plan-reconcile 2026-08-18.
- [ ] [UI] P2. New, operator-refined 2026-08-17 — add an operator-facing quick sanity-check surface: show "requests
      tracked by AO" per account (GLM/Codex/Gemma first, but not exclusive to them) so the operator can manually spot
      -check it against the provider's own console/dashboard. Operator's own framing: "It might make sense for an
      operator to quickly check the UI to just see how many requests that shows versus what we're tracking." This is
      deliberately a manual cross-check aid, not a new automated poller — no live "requests remaining" API is assumed
      to exist for every provider (confirmed absent for Codex specifically, `FlatRateBoostPanel.tsx:9-16`). Done
      when: an operator can view AO's tracked request count for a given account, with enough detail (account id,
      window) to manually verify it against the vendor's own console.
- [ ] [DATA] P3. New, operator-refined 2026-08-17 — forward-looking capacity question, explicitly gated on the
      request-tracking sanity-check above being validated first (do not attempt before that todo is done — the
      operator's own sequencing: "once we know we're tracking requests in the right way, what we really care about
      is: is there enough requests to do a task"). Once tracking accuracy is confirmed, measure the real
      requests-per-task consumption rate from actual dispatched tasks (per provider), to answer whether a given
      plan's request/message allowance is sufficient capacity for the number of tasks intended to run through it.
      Done when: a real measured requests-per-task figure exists for at least one subscription-shaped provider,
      derived from real completed tasks, not estimated.
- [x] ✅ [DATA] P1. New (2026-08-17): join per-task compaction occurrence — whether a given `task_id` triggered
      `forced_precompact`/`forced_compact`/`forced_compact_ineffective` during its own run — onto a queryable
      per-task record. `ao_death_diagnostics_compaction_kpis_and_sequential_carveout_2026_08_15.md` already logs these
      events with a timestamp + `slot_id` (`server/fleet_kpis.py`/`server/context_lifecycle.py`), and `TaskUsageRow`
      (`server/orm.py:292`) already carries `assigned_at`/`completed_at` per task — the join key (an event's
      timestamp falling inside a task's own `[assigned_at, completed_at]` window for that `slot_id`) exists in
      principle but is never materialized as a field or query today. Precondition for retrospective complexity
      routing — "give me all tasks that required autocompact," so a model with a small context ceiling can be routed
      away from tasks that historically need compaction. Done when: a real query (or a new persisted field, e.g.
      `TaskUsageRow.compact_count`) answers "did task X trigger compaction" for a real historical task without
      hand-correlating timestamps. **Extracted 2026-08-18 (na-eligibility-audit, ao tranche) → `ao_satellite_ao_dispatch_batch24_2026_08_18.md` item 1** — conflict-checked clear (outside the doc-level Non-goals ruling's own stated scope). Track dispatch/completion there, not here.
- [x] ✅ [INFRA] P1. New (2026-08-17): capture the PEAK/high-watermark `context_used_pct` reached during a task, not
      just the end-state token sums `TaskUsageRow` already stores. `context_lifecycle.py`'s per-tick reader already
      sees `context_used_pct` live for every active target — nothing records the max value seen during a task's own
      window onto its durable per-task record. Second precondition for complexity routing (route historically
      low-peak-context tasks to a model with a small context ceiling). Done when: a real completed task's record
      shows a real peak-context value, cross-checked against a live session known to have approached a specific pct.
      **Extracted 2026-08-18 (na-eligibility-audit, ao tranche) → `ao_satellite_ao_dispatch_batch24_2026_08_18.md` item 2** — conflict-checked clear. Track dispatch/completion there, not here.
- [x] ✅ [DATA] P2. New (2026-08-17): capture which repo(s) a task actually touched (from its real diff/commits, not the
      plan's declared `repos:` frontmatter, which is a stated intent, not a measurement) and persist it per task. No
      such field exists today — confirmed by grep: `repos_touched`/`repo_count` in `server/` only match unrelated
      dirty-worktree-state concepts (`server/routes/git_health.py:277`, `server/worktree_clean_check/_report.py:51`).
      Useful as a difficulty heuristic alongside turns/context. Done when: a real completed task's record shows the
      real repo(s) it committed to, sourced from actual commit/push evidence. **Extracted 2026-08-18
      (na-eligibility-audit, ao tranche) → `ao_satellite_ao_dispatch_batch24_2026_08_18.md` item 3** —
      conflict-checked clear. Track dispatch/completion there, not here.
- [x] ✅ [DATA] P2. New (2026-08-17): persist the task's `context_scope` (the reading-list already passed to the worker
      at dispatch, `server/dispatch.py:564`) onto the completed-task record, so it's retrospectively joinable against
      the task's real turn count/token usage/compaction outcome (todo above). Today `context_scope` is
      dispatch-time-only and never carried through to `TaskUsageRow` or any other durable per-task table — this is
      what lets a future analysis ask "does a bigger context_scope reading list predict more turns/context/
      compaction" rather than assuming it. Done when: a real completed task's record shows both its `context_scope`
      size and its real outcome metrics (turns/tokens/compacted) joinable in one query. **Extracted 2026-08-18
      (na-eligibility-audit, ao tranche) → `ao_satellite_ao_dispatch_batch24_2026_08_18.md` item 4** —
      conflict-checked clear. Track dispatch/completion there, not here.
- [x] [BACKEND] P2. **New, operator ask 2026-08-18 — hourly, clock-aligned time-series aggregation per
      (provider, role_group).** Built `fleet_kpis.compute_hourly_provider_role_usage()` (extends
      `compute_dispatch_efficiency_by_day`'s UTC-calendar-day pattern to hourly, per the plan's own instruction — not a
      parallel mechanism), bucketed by FIXED UTC clock-hour boundaries (`_hour_bucket()` truncates to
      minute=second=microsecond=0, never a rolling window). Exposed as `GET /api/backlog/usage/hourly-series` in
      `server/routes/backlog.py` (`provider`/`role_group`/`start`/`end` query params, same AND-composing/laissez-faire
      convention as `/api/backlog/usage/windows`); range defaults to `fleet_kpis.earliest_usage_timestamp()` (MIN across
      `task_usage.completed_at` and `task_dispatched` activity rows) when `start` omitted. Each bucket reports
      published rate(s) actually in use (`model_pricing.rates_for()` per distinct model seen that hour — never an
      averaged blend across models), 4-way token usage, $ spend (poisoned to None by any unpriced row, same rule as
      `window_task_usage_totals`), completed-task count, and dispatch-ATTEMPT count. Dispatch attempts resolve
      provider via `slot_account_attribution.resolve_turn_account()` against `tmux_spawn.session_name(slot_id)` (a
      `task_dispatched` activity event's own `details_json` carries no account_id — confirmed via direct read of
      `routes/slots_worker.py:709-715`); role_group resolves via `state_store.task_role_group()` (same taxonomy
      `/api/backlog/usage/windows` already filters on), not `RoleDispatchEfficiency.role`'s finer raw-role bucketing.
      New Pydantic views: `HourlyUsageBucketView`/`HourlyModelRateView` in `server/models/backlog.py`.
      **Evidence — real query against a real seeded DB** (`dashboard/tests/e2e/fixtures/seed_e2e_state.py`'s own
      fixture, via the real `run-e2e-backend.sh` mock-mode env, not a synthetic script):
      ```
      hour=2026-08-18T05:00:00+00:00 provider=anthropic role_group=planning task_count=2 dispatch_attempts=2
      hour=2026-08-18T06:00:00+00:00 provider=deepseek  role_group=cicd     task_count=1 dispatch_attempts=5
      ```
      The 06:00 bucket is the burst — 5 dispatch attempts landing only 1 completion, visibly identifiable against the
      05:00 bucket's healthy 2-attempts/2-completions neighbor, satisfying the "done when" bar verbatim. Full backend
      quality gate green (`bash scripts/quality-gates.sh --no-fix`: ruff/basedpyright 0 errors, pytest 4022 passed/7
      skipped).
- [x] [UI] P2. **New, operator ask 2026-08-18 — adopt a charting library (operator's explicit choice over a
      hand-rolled SVG alternative, since this dashboard has zero charting precedent today — confirmed via
      `dashboard/package.json`, no recharts/chart.js/d3/victory/visx/nivo anywhere).** Added `recharts@^3.10.1`
      (the actively-maintained major — 2.x is deprecated upstream, confirmed via `npm install`'s own deprecation
      warning before switching; React 16-19 peer range, compatible with this dashboard's React 18.3). Composes cleanly:
      `npm run typecheck`/`test`/`format:check` all green, `npm audit`'s pre-existing 8 vulnerabilities are all
      transitive dev-tooling (vite/vitest/postcss/esbuild/babel/nanoid) unchanged before/after adding recharts —
      confirmed by diffing `npm audit --json` output pre/post. Proof-of-concept chart:
      `dashboard/src/UsageTimeSeriesModal.tsx` (`ComposedChart` — dispatch-attempts/tasks-completed bars +
      spend line, dual y-axis, custom tooltip) renders real data from the new hourly endpoint. `pw:L2 ✓` —
      `dashboard/tests/e2e/usage-time-series.spec.ts`, 3/3 passed against the real e2e stack.
- [x] [UI] P2. **New, operator ask 2026-08-18 — shared popup/modal chart component, launched from MULTIPLE entry
      points, not duplicated per-panel.** One component (`UsageTimeSeriesModal.tsx`) consuming the new hourly endpoint
      (provider/role-group filter toggles reusing `TaskUsageWindows.tsx`'s own `ROLE_GROUP_FILTER_OPTIONS`), opened via
      an "Usage over time" button added to the `Panel`'s `right` slot in ALL FIVE named entry points: `FleetKpis.tsx`,
      `ClaudeWalletPanel.tsx` (pre-scoped `initialProvider="anthropic"`), `DeepSeekWalletPanel.tsx` (pre-scoped
      `"deepseek"`), `KimiWalletPanel.tsx` (pre-scoped `"kimi"`), `TaskUsageWindows.tsx` (pre-scoped to that panel's
      own current filter selection) — one implementation, five launch sites, not five copies.
      **Real bug found + fixed while wiring this** (not pre-existing scope, a genuine regression this feature's FleetKpis
      entry point was the first to expose): `.topbar` sets `backdrop-filter` for its frosted-glass look, which per the
      CSS spec establishes a new containing block for `position: fixed` descendants — the shared `Modal` component
      (`components.tsx`) was never portaled, so a Modal instantiated from inside a TopBar popover (FleetKpisMenu's
      "KPIs" dropdown) rendered fixed-relative-to-the-144px-tall-topbar instead of the viewport, landing its content
      far outside clickable/visible bounds (confirmed via `getBoundingClientRect()`: `.modal-back` measured
      `144px` tall instead of the full `720px` viewport). Fixed by portaling `Modal` to `document.body` via
      `createPortal` — a general fix benefiting every future modal-in-popover case, not a workaround scoped to this
      feature. That portal in turn broke `usePopover`'s outside-click detection (a portaled modal's DOM node is no
      longer a descendant of the popover's own `ref`, so any click inside it read as "click outside the popover" and
      closed it, unmounting the modal); fixed with an explicit `.closest(".modal-back")` carve-out in
      `layout.tsx`'s `usePopover`. Both fixes are small, targeted, and verified via the real Playwright run below —
      not present in any other Modal usage's behavior (confirmed all other Modal call sites render from `App.tsx`'s
      top level, never nested inside a TopBar popover, so this bug never manifested before).
      **Evidence**: `dashboard/tests/e2e/usage-time-series.spec.ts` — 3/3 passed real end-to-end runs: (1) opens from
      FleetKpis's "KPIs" popover, renders a real chart; (2) opens from ClaudeWalletPanel, pre-scoped to anthropic,
      renders the same live data; (3) changing the provider filter from "All providers" to "Anthropic" re-fetches and
      the burst-note banner (only present for deepseek's HOUR_B burst) correctly disappears. New fixture data:
      `dashboard/tests/e2e/fixtures/seed_e2e_state.py`'s `E2E_USAGE_TS_*` constants — two real UTC-hour-anchored
      buckets (anthropic/planning healthy pattern + deepseek/cicd deliberate 5-attempts/1-completion burst), with
      dedicated `AgentRow` rows on slots 2/6 so `slot_account_attribution` has real intervals to resolve against.

- [~] [DATA] P2. New, operator ask 2026-08-18 — capture reasoning/thinking tokens as part of the unified per-task
      billing schema above (that todo scopes cache-read/write; reasoning tokens are the one dimension it doesn't yet
      name). Investigate what's actually capturable per vendor before assuming uniform feasibility.
      **PARTIAL `agent-orchestrator@b6fe23c7c6`** — DeepSeek: **DONE**, `DeepSeekNativeUsageRow.reasoning_tokens` is
      now joined onto `TaskUsageRow.reasoning_tokens` (new nullable column, migrated via
      `_TASK_USAGE_MIGRATION_COLUMNS` per the 2026-08-05 schema-drift-outage lesson) at both `/done` write-path call
      sites (`_record_done_task_usage` in `routes/slots_worker.py`, and the human-usage-push route) — persisted going
      forward, not just computable via the pre-existing live read-time join in `routes/backlog.py`. NULL (never a
      fabricated 0) when no matching `DeepSeekNativeUsageRow` exists for the session. Evidence: 2 new pytest cases in
      `tests/test_record_done_task_usage_isolation.py` (5/5 passing), full backend suite 4047 passed/5 skipped,
      full `quality-gates.sh` green. Claude: confirmed **N/A** (no reasoning-token field in the API's `usage` object
      at all — unchanged from `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md`'s known gap). Codex:
      confirmed still **blocked** on the P0 fake-token-estimate fix above landing real usage data first (unchanged).
      **Still open — Kimi/GLM**: the generic Anthropic-shape proxy parser these route through never reads a
      reasoning-token field, and it's not yet established whether Moonshot/Zhipu's actual API response even carries
      one — that requires either reading vendor API docs or a live probe, and a live probe against Kimi specifically
      is undesirable right now given Kimi's accounts are deliberately paused fleet-wide (see the "Kimi Blocked"
      badge work above; do not spend metered requests probing this before the Moonshot waitlist resolves). If the
      field does exist, capturing it durably would need a DeepSeek-style dedicated native proxy (a real, separate
      build — not a quick parser tweak), since the generic proxy is intentionally shape-agnostic. Done when: Kimi/GLM
      resolved either way (captured + joined, or documented N/A same as Claude) — the other three providers already
      meet the original "capture-or-explicitly-N/A" bar.
- [x] ✅ [DATA] P2. New, operator ask 2026-08-18 — bring Kimi's wallet reconciliation up to the same depth Claude/
      DeepSeek already have. Today `compute_kimi_wallet_window_reconciliation()` (`server/state_store/slots.py:1373`)
      only covers the 1h/24h/7d/Lifetime WINDOWED view — no lifetime LEDGER table (known top-up total / opening
      balance / attributed spend / residual), the shape `compute_claude_wallet_reconciliation()`
      (`account_usage.py:533`) and `compute_deepseek_wallet_reconciliation()` (`slots.py:1468`) both already have.
      `kimi_gemma_provider_onboarding_2026_08_16.md`'s own todo explicitly forward-points here for "full
      billing-schema inclusion" rather than duplicating scope in that doc. No new UI pattern needed — same
      `KimiWalletPanel.tsx` component, same lifetime-table shape already proven twice. Done when: `KimiWalletPanel.tsx`
      shows a lifetime reconciliation table alongside its existing windowed one, backed by a real
      `compute_kimi_wallet_reconciliation()`-equivalent, same as DeepSeek's/Claude's.
      **DONE `agent-orchestrator@39d35ed696`** — new `compute_kimi_wallet_reconciliation()` (mirrors
      `compute_deepseek_wallet_reconciliation()`, simpler: no worker/orchestrator/review split, no opening-balance
      freeze — Kimi's wallet has no pre-observability gap), new `KimiTopupRow`/`GET+POST /api/accounts/kimi/
      wallet-reconciliation`+`topups`, new lifetime table + top-up form in `KimiWalletPanel.tsx` alongside the
      existing windowed one. **Evidence**: 6 new backend pytest cases (`tests/test_kimi_wallet_reconciliation.py`),
      `pw:L2 ✓` — 2 new e2e tests in `kimi-wallet-reconciliation.spec.ts` (real computed numbers:
      $20.0000 topup − $12.5000 balance = $7.5000 real spend, $2.0000 attributed, $5.5000 residual; a second
      recorded top-up updates the table in place), full backend+dashboard quality gate green before shipping.

## Progress Log

- **2026-08-19 (interactive session) — Task Token Usage / Batching Efficiency provider + role-group filter
  completeness, prompted by an operator screenshot review.** Operator asked whether round-robin dispatch tiering
  includes planning/escalation and whether analytics treats every model uniformly; the concrete, actionable half of
  that turned out to be this plan's own dashboard panels. Two real gaps confirmed by direct code read + screenshot:
  (1) `PROVIDER_MODEL_FILTER_OPTIONS` (`TaskUsageWindows.tsx`) only had DeepSeek/Anthropic buttons while the account
  row underneath already listed real accounts from Gemini/GLM/Codex-Luna/Kimi/Gemma(NVIDIA) — six providers reachable
  only by scrolling the account row, never as a top-level filter; (2) `ROLE_GROUP_FILTER_OPTIONS` was missing
  `quality_gate_resolution` even though the backend (`TASK_ROLE_GROUPS`/`_ESCALATION_ROLES`,
  `server/state_store/slots.py`) already classifies that role_group independently — counted in "All roles" but never
  independently filterable.
  - Also found, same session, a THIRD thing already fixed but uncommitted in this exact working tree (2-hour-stale,
    no live edit lock — inherited per the liveness-gated dirty-WIP rule): `accountFilterOptions()` scoping the
    per-account row to the selected provider, plus a new `UsageFilterStore.ts` syncing the provider selection between
    this panel and `BatchingEfficiencyPanel.tsx`. Both were exactly the operator's own follow-up ask ("filter to
    accounts under that provider") — already built, just unshipped.
  - **Shipped, agent-orchestrator@b65f6d42** (landed by a concurrent session sharing this slot's checkout while this
    session was running its own QG pass — confirmed via `git log`/`git show`, correct slot-6 author identity, pushed
    to `origin/live-defi-rollout`, ahead=0): the inherited account-scoping/cross-panel-sync fix, this session's
    6-provider filter addition, plus Playwright coverage for both (`task-usage-provider-account-sync.spec.ts` gained
    2 new tests: every new provider button renders, and selecting Gemini scopes the account row correctly).
  - **Shipped separately, agent-orchestrator@d318745830** (verified ancestor of `origin/live-defi-rollout`): the
    `quality_gate_resolution` role-group addition wasn't
    covered by the concurrent session's own edits to `task-usage-role-group-filter.spec.ts`, so added one more test
    there (button renders + filters to a zeroed bucket for this fixture) and shipped via quickmerge in this same
    session.
  - Full verification chain run this session: `tsc --noEmit` clean, full dashboard `vitest` (463 tests) green, the
    3 touched/extended Playwright specs green (18 + 9 + 6 tests) against the real e2e mock backend, then a full
    `bash scripts/quality-gates.sh --no-fix` pass (4421 python tests + dashboard checks) green.
- **2026-08-18 (delta investigation, operator ask) — re-investigated existing coverage before adding scope, per
  operator instruction ("investigate the delta ... I'm not sure why there are so many extra to-dos").** Operator's
  original ask ("reconciliation, task usage, batch call usage, terms, reasoning, tokens ... across all providers")
  mapped almost entirely onto this plan's ALREADY-open scope: cache-token schema unification (existing `[DATA] P1`
  unified-schema todo already names all 6 providers), published-rate "terms" (already the Why section's explicit
  requirement), Codex's fake-token bug (already the #1 `[INFRA] P0` todo, re-confirmed today still current via a
  fresh read of `codex_bridge_server.py:237-254` — unchanged). "Batch call usage" was a genuine misread on my part —
  the operator clarified it means TOOL-CALL BATCHING (the hook that nudges chaining Bash/Read/Edit calls, not LLM
  provider batch-billing APIs). Verified real, not a gap: `cursor-configs/hooks/batching-nudge.py` is the actual
  hook; `server/batching_stats.py` + `batching_stats_poller.py` (registered `server.py:329`) do real transcript
  scanning (with a genuine, hard-won multi-line `message.id`-grouping fix documented in its own module docstring);
  `dashboard/src/BatchingEfficiencyPanel.tsx` already surfaces it with the same 1h/5h/24h/7d/Lifetime window shape as
  every other reconciliation panel, filterable by provider/model/role-group/account — nothing to build there. Two
  genuine deltas found and added as todos above: (1) reasoning tokens are not named anywhere in this plan's existing
  unified-schema todo, captured for DeepSeek only, never joined onto `TaskUsageRow`; (2) Kimi's reconciliation depth
  is windowed-only, no lifetime ledger table the way Claude/DeepSeek both have. No new UI pattern for either — same
  existing panel/table shapes, real accuracy work only, per the operator's own framing ("it's just accuracy on all
  the providers, we already have the things we need shown there").
- **2026-08-18 (implementation) — all 3 hourly-usage-chart todos shipped, uncommitted in the working tree.**
  `agent-orchestrator` files touched: `server/fleet_kpis.py` (new `compute_hourly_provider_role_usage`,
  `earliest_usage_timestamp`), `server/models/backlog.py` + `server/models/__init__.py` (new
  `HourlyUsageBucketView`/`HourlyModelRateView`), `server/routes/backlog.py` (new `GET
  /api/backlog/usage/hourly-series`), `dashboard/package.json` (+`recharts@^3.10.1`), new
  `dashboard/src/UsageTimeSeriesModal.tsx` + `.test.ts`, `dashboard/src/{FleetKpis,ClaudeWalletPanel,
  DeepSeekWalletPanel,KimiWalletPanel,TaskUsageWindows}.tsx` (launch button wiring), `dashboard/src/components.tsx`
  (Modal portal fix — see the 3rd todo above for why), `dashboard/src/layout.tsx` (usePopover click-outside carve-out
  — same root cause), `dashboard/src/styles.css` (`.usage-ts-tooltip`), new
  `dashboard/tests/e2e/usage-time-series.spec.ts`, `dashboard/tests/e2e/fixtures/seed_e2e_state.py`
  (`E2E_USAGE_TS_*` fixture block). Backend quality gate green (ruff/basedpyright/4022 pytest); dashboard
  typecheck/408 vitest/format:check green; new Playwright spec 3/3 passed against the real e2e stack. Judgment calls
  made without an operator ruling (flagged, not hidden): exact endpoint path/param names
  (`/api/backlog/usage/hourly-series?provider=&role_group=&start=&end=`, mirroring `/api/backlog/usage/windows`'s
  existing convention); burst-detection threshold (`dispatch_attempts >= 3 AND >= 2x task_count`, chosen so a single
  crash/timeout requeue never false-flags); modal styling (plain `Modal`/`Panel` reuse, `ComposedChart` with dual
  y-axis — bars for attempts/completions, line for spend — token totals surfaced via tooltip/rates-line rather than a
  5th chart series, to avoid a scale mismatch against attempt/completion counts). No todo's "done when" bar was
  infeasible — real historical spread existed (or was fixture-added) for every claim above.
- **2026-08-18 (/plan-brainstorm) — 3 new todos added: hourly per-provider/per-role usage time-series + chart UI.**
  Operator ask: plot usage over time per provider, broken down by role, showing published API rates/usage/real $
  spent/task-completion counts, PLUS dispatch-attempt counts (not just completions — "trying a lot of times" without
  landing the task is its own signal), launched as a popup from the KPI panel and/or each wallet-reconciliation/
  task-usage panel. Operator explicitly ruled: fold into an existing plan, no new plan doc. Researched first (this
  doc's own `context_scope` + `FleetKpis.tsx`/`server/fleet_kpis.py`): `DailyDispatchEfficiency`/
  `RoleDispatchEfficiency`/`DispatchRetryStats` already exist (daily-granularity dispatch/done/retry KPIs) — this is
  NOT greenfield, it's an hourly generalization + a new billing/rate dimension layered on. The plan that originally
  built FleetKpis (`ao_fleet_observability_kpis_2026_07_20`) is archived, and the only other active KPI-adjacent plan
  (`ao_death_diagnostics_compaction_kpis_and_sequential_carveout_2026_08_15.md`) is scoped to compaction/death-
  diagnostics specifically — neither is the right home, so this doc (already covering per-task/per-provider billing
  reconciliation) is. Two operator decisions resolved via `/plan-brainstorm` clarifying questions: (1) adopt a real
  charting library (not hand-rolled SVG) despite this being the dashboard's first-ever charting dependency; (2)
  hourly buckets (not daily) to actually surface intraday burst patterns. Operator separately clarified mid-session:
  buckets must be FIXED UTC clock-hour boundaries (00:00, 01:00, ...), never a rolling "last N hours from now"
  window — a different shape from every existing `window_hours` lookback endpoint in this codebase (the wallet
  panels' own 1h/24h/7d/Lifetime toggle shipped earlier today), folded into the new todo's own text so it isn't
  conflated by whoever builds it.

- **2026-08-18 — Grok (xAI) decommissioned, operator decision; every open todo above narrowed to drop it.** Reason
  stated verbatim: no subscription/Max-style tier and no free tier — pure metered pay-per-token — judged pointless
  vs Claude/DeepSeek's subscription economics and Gemini's genuine free tier. Full removal record (code + the
  dedicated onboarding plan) lives in `grok_gemini_translation_proxy_2026_08_14.md` (retitled to drop Grok, its own
  2026-08-18 Progress Log entry has the file-by-file `agent-orchestrator` diff). This doc's provider-count references
  updated (4→3 new providers: Gemini/GLM/Codex; 7→6 total registered providers), and the `[REVIEW]` context-window/
  compaction-verification todos narrowed to the remaining providers. Historical findings (e.g. the real Grok 4.6
  context-ceiling test that grounded this doc's "vendors don't self-compact" finding) left untouched — they're a
  record of what was measured, not live scope.

- **2026-08-16 (created)**: Plan authored from a same-session investigation following the live 9-model billing/context
  test battery (see the sibling provider plans' 2026-08-16 Progress Log entries for that raw data). Real findings this
  session, cited above: Codex's fake `len(text)//4` token estimate (confirmed via direct code read), the
  provider-agnostic-mechanism-vs-provider-specific-data-accuracy gap in `context_lifecycle.py`, Grok 4.6's 500K
  context ceiling confirmed live (hard-enforced, no self-compaction), and `calibrate_account_value.py`'s deliberate
  (not buggy) reset-window-dropping design. No code written yet — investigation + plan authoring only.
- **2026-08-17 — 5 new todos from an interactive UI/telemetry review**: operator reviewed the AO dashboard and asked
  three things. (1) What does "Input per turn" mean — answered inline, not a gap: confirmed real cache-miss input
  tokens/turn, working as intended (`dashboard/src/TaskUsageWindows.tsx:320-323`, `server/routes/backlog.py:928`), not
  a tool-call count. (2) Why every account shows Anthropic-shaped weekly/5-hour limits regardless of provider —
  confirmed a real gap (`server/accounts.py:142`, `dashboard/src/layout.tsx:4485`), narrowed by the operator's own
  follow-up correction: Codex and GLM are subscription-shaped like Anthropic and should get the SAME
  weekly/5-hour+boost treatment, not be excluded from it — new `[UI] P1` todo above. (3) Whether enough per-task
  telemetry exists to retrospectively identify "hard" tasks before more providers go live. Confirmed `TaskUsageRow`
  (`server/orm.py:292`) already durably captures turn_count/4-way token breakdown/spend/duration per task, but four
  things do not exist yet — per-task compaction-occurred flag, peak-context high-watermark, real repos-touched, and
  context_scope size carried through to the completed-task record — added as the 4 new todos above. None of this
  plan's existing todos covered those four; the existing `[DATA] P1` unified-billing-schema todo is billing-shaped
  (token counts × published rate), not difficulty-shaped (turns/compaction/context/repos as future routing signals) —
  kept separate, not merged, since they answer different questions. No code written this session — doc-only.
- **2026-08-17 — Codex/GLM boost-parity todo refined into a 7-step workstream**: operator broke the single
  Codex/GLM-parity todo (added earlier the same day) into an explicit sequence: (1) confirm real end-to-end task
  completion through AO for GLM/Codex specifically (not just a smoke test), (2) determine each provider's real
  usage-limit metric — messages vs. tokens, not yet verified for either, don't assume — before doing any math on it,
  (3) build the `boost_multiplier`/wallet-reconciliation calculation generalizing Claude's
  `compute_claude_wallet_reconciliation()` once the metric is known, and wire the same dashboard columns Anthropic
  already has, (4) a three-way check that AO's computed spend, the vendor's own stated docs/limits, and the actual
  dollars paid all agree. Separately: Gemma should explicitly SKIP $ reconciliation (genuinely free, "nothing to
  reconcile with") but still show real, non-placeholder usage numbers. Two more items added: an operator-facing
  "requests tracked by AO" surface so the operator can manually spot-check AO's count against each vendor's own
  console, and a forward-looking (explicitly gated on that surface being validated first) measurement of real
  requests-per-task, to eventually answer whether a plan's request allowance covers the number of tasks intended to
  run through it. Replaced the single prior todo with these 7, rather than leaving both (no work had landed against
  the original yet). No code written this session — doc-only.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:ee26e6744e46c17e]: KEEP-NA, valid — explicit dated operator ruling on record: 'human plan, not AO-dispatched' for the whole doc's live-testing/design-call content (multi-provider billing/context research).
- **na-eligibility-audit 2026-08-18 (ao tranche)**: RECLASSIFY (per-todo split) — re-read end to end. The doc-level 'human plan' ruling correctly covers the bulk of the remaining ~19 open todos (live-testing verification, schema/methodology design work, the GLM/Codex boost-parity workstream), all KEEP-NA on that citation. But 4 telemetry-capture todos added 2026-08-17 (compaction-occurrence join, peak-context watermark, repo-touched capture, context_scope-size capture) are pure bounded backend/DB engineering with zero design or live-testing judgment component — outside the cited ruling's own stated scope. Conflict-checked clear and extracted to `ao_satellite_ao_dispatch_batch24_2026_08_18.md` items 1-4. Doc stays `assigned_vm: NA` for its remaining ~19 items.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)

## Gates 7-8 — post-hoc performance analysis + final model recommendation (operator's 8-gate provider-readiness framework, added 2026-08-18)

> **Why here**: this doc already owns the cross-provider comparison/reconciliation goal (Gates 7-8 of the operator's
> framework are exactly "how did each model do" and "what should we recommend given all of it") and is already ruled
> human-driven — the natural home for the ONE dimension a 2026-08-18 corpus audit found with literally zero coverage
> anywhere: whether bursting usage costs more than pacing it, and a final synthesized recommendation. See
> `plans/audit/provider_smoke_test_registry_2026_08_18.md` for the full 8-gate status map this doc's existing todos
> already cover most of (Gate 7's data exists in `TaskUsageRow`; the normalizing billing schema this doc's own
> `[DATA] P1` todo builds is Gate 7's real prerequisite, already tracked, not duplicated here).

- [ ] [DATA] P2. **Gate 8a — burst-vs-pace cost analysis, Claude first (richest usage-history data of the six
      providers).** Test whether concentrating a given token/message volume into a short burst within a window
      consumes quota at a different effective rate than spreading the same volume evenly across that window. A
      2026-08-18 web-research pass found no official Anthropic documentation of a burst penalty on the weekly meter
      specifically (the one confirmed rate-shaping mechanism, peak-hour throttling, only ever touched the 5-hour
      meter and was removed 2026-05-06) — this todo is the empirical check that research couldn't answer from docs
      alone. Reuse `account_usage_history`'s existing ~30-min sampling cadence; compare two real historical windows
      with materially different intra-window usage concentration but similar total consumption. **Done when**: a
      dated Progress Log entry states, with real data, whether burst vs. paced usage measurably differs in effective
      quota cost for at least one Claude account, and whether the same question is even answerable for the metered/
      free-tier providers (DeepSeek/Kimi/Gemini/Gemma have no comparable "quota efficiency" concept — state explicitly
      if this dimension is N/A for them rather than silently skipping).
- [ ] [OPERATOR] P3. **Gate 8b — final model/provider recommendation.** Once Gates 1-7 close out (tracked in
      `plans/audit/provider_smoke_test_registry_2026_08_18.md` and this doc's own existing comparison todos),
      synthesize a deep-research recommendation on the best model and best model-combination given the fleet's full
      real history — cost, completion quality, turn-efficiency, and the burst-vs-pace finding above. Explicitly
      operator-gated (a judgment call over incomplete/evolving data, not a bounded worker outcome) — but the DATA
      GATHERING this recommendation depends on (the burst-vs-pace measurement above, the per-task quality/cost
      comparison todos already tracked in this doc) is agent-doable and should be forked out per the
      `task_template.md` §3 finding-Y operator-item-separation pattern once ready, so this final judgment call never
      blocks the data-gathering work behind it. **Done when**: every dependency this recommendation needs is either
      done or explicitly named as still-missing, and the recommendation itself is recorded with its own dated
      Progress Log entry, not folded silently into another todo's evidence.

- **2026-08-19 — isolated pilot session, two findings that had only existed in chat, captured here so they aren't
  lost.**
  1. **Real Gemini CLI task result** (companion data point to the GLM one already in
     `deepseek_claude_blended_provider_routing_2026_07_28.md`'s Progress Log): a real end-to-end `claude` CLI task
     against `gemini-3.5-flash-lite-proj1` — 5 turns, real file edit completed, CLI-reported
     `total_cost_usd: $0.1617` (computed equivalent — Gemini's free tier has no real $ bill; see the
     `subscription_credits`/`rate_limited_free` shape split in the schema todo above).
  2. **Full-system model-existence sweep (2026-08-19, isolated pilot, free list-endpoints only — no generation
     cost)**: every currently-registered model across every provider confirmed real and listed, nothing
     deprecated — `deepseek-v4-flash`/`deepseek-v4-pro` (DeepSeek `/models`); `glm-5.2`→served-as-`glm-5.3`,
     `glm-5-turbo` (Z.ai `/v1/models`); `gemini-3.5-flash-lite`, `gemini-3.7-flash` ×3 pooled keys each, all keys
     individually valid (Google `/v1beta/models`); `diffusiongemma-26b-a4b-it`, `gemma-4-31b-it` (NVIDIA
     `/v1/models` — both listed; `gemma-4-31b-it`'s real problem is the persistent timeout in
     `plans/active/issues/gemma_4_31b_it_persistent_timeout_2026_08_19.md`, not a missing/dead model); `kimi-k3`,
     `kimi-k2.6`, `kimi-k2.7-code` (Moonshot `/v1/models` — bonus: `kimi-k2.7-code-highspeed` exists too,
     unregistered, FYI only); `gpt-5.6-luna` (Codex/Luna — already proven live). No action needed from this
     finding alone; recorded so a future session doesn't re-run the same free sweep from scratch.

- **2026-08-19 — new `[UI] P2` todo added: display the unified per-task billing schema once it lands, plus real
  prep work shipped ahead of it.** There was no tracked UI todo for surfacing the schema this plan's own
  `[DATA] P1` todo designs (`requested_model`/`served_model`/`tokens_per_second`/5-shape billing categorization) —
  added one, with a concrete design (extend `BacklogDetailModal`'s per-attempt table for the per-task grain; a new
  fleet-wide billing-shape view beside `TaskUsageWindowsPanel.tsx`), explicitly gated on the schema-design and
  v0-capture-mechanism `[DATA] P1` todos landing real data first — not attempted before then, to avoid a
  half-wired panel against fields that don't exist yet. Real, shippable prep work was pulled forward instead of
  left purely as design prose: studying `KimiWalletPanel.tsx`'s `allKimiAccountsPaused()` and
  `NvidiaCapacityPanel.tsx`'s `degradedNvidiaAccounts()` (the "live-derived, not hardcoded, which provider/model is
  usable" precedent the new panel will need) surfaced a real, currently-shipping gap: the generic Accounts panel's
  "N/M available" counts never accounted for `health_status`, only `status` — an enabled-but-degraded account
  (real case: NVIDIA's `gemma-4-31b-it`, `/plans/active/issues/gemma_4_31b_it_persistent_timeout_2026_08_19.md`)
  silently read as available. Fixed via a new `isAccountAvailableForDisplay()`
  (`agent-orchestrator/dashboard/src/layout.tsx`) — kept deliberately separate from the existing
  `accountIsUsable()`, which mirrors AutoSpawn's own dispatch-eligibility definition and has no opinion on
  `health_status`; merging the two would have silently changed dispatch semantics, a call this UI task has no
  standing to make unilaterally. Also added a generic per-row "⚠ Degraded" badge (`AccountRow`) firing for any
  provider, not just NVIDIA. Shipped `agent-orchestrator@befc0e3723` — full `quality-gates.sh --no-fix` green
  (4146 passed/8 skipped pytest, basedpyright clean, dashboard `tsc` clean, 432/432 vitest), `pw:L2 ✓`
  (`provider-badge.spec.ts` 6/6, new case against the real `nvidia-gemma-4-31b-demo` e2e fixture). Full todo text
  + evidence citation above, under the new `[UI] P2` entry. No work attempted on the schema/capture-mechanism
  todos themselves this session (explicitly out of scope — a parallel session owns that track).

- **2026-08-19 (implementation, the "parallel session" the entry above refers to) — 4 [DATA]/[REVIEW] P1/P2 todos
  above shipped, `agent-orchestrator@a93eb0c9b1` (GLM poller fix, sibling plan) + `agent-orchestrator@4e2d3797fb`
  (this doc's schema/capture/reconciliation/Gemini work). GLM/Codex/Gemini/Gemma accounts stayed
  `account_status: disabled` throughout — every proof
  below is either a real-code-path proof against a constructed local fixture (per
  `/codex/15-runbooks/agent-orchestrator-local-pilot-isolation-runbook.md`'s isolated pattern) or a citation of
  historical Progress Log data already in this doc or a sibling plan, never a live fleet dispatch.**

  1. **Unified per-task billing schema — implemented, not just drafted.** `server/orm.py` `TaskUsageRow` gains two
     nullable columns (`server/bootstrap.py` `_TASK_USAGE_MIGRATION_COLUMNS`, same ALTER-TABLE pattern as
     `reasoning_tokens`): `requested_model` (the account's declared `AccountDef.variant`, e.g. GLM's "5.2") and
     `tokens_per_second` (always NULL today — honest N/A, no transcript-derivable timing signal exists; needs a
     provider-native telemetry source, out of scope for this pass, same class of gap as `reasoning_tokens` for
     Codex). `server/model_pricing.py` gains `billing_shape_for_provider()`, a pure function (not a stored column —
     a provider's shape doesn't vary per-task, so storing it per-row would just rot) implementing the 5-shape
     categorization. Concrete field mapping, all 7 real registered providers (this doc's own "6" tally undercounts —
     `nvidia`/Gemma is a distinct `AccountProvider`, separate from the 6 named in the 2026-08-18 Grok-removal entry
     above; noted here rather than silently corrected elsewhere):

     | provider    | `model` (served)     | `requested_model`        | `billing_shape`                 | `tokens_per_second` |
     |-------------|----------------------|---------------------------|----------------------------------|----------------------|
     | anthropic   | transcript `msg.model` | `AccountDef.variant` (usually unset) | `subscription_boost_multiplier` | NULL (no signal)     |
     | deepseek    | transcript `msg.model` | `AccountDef.variant` (pro/flash)     | `metered_dollar`                | NULL (no signal)     |
     | glm         | transcript `msg.model` (may alias, e.g. `5.2`→`5.3`) | `AccountDef.variant` | `subscription_credits` | NULL (no signal yet — Zhipu's real tok/s exists on their dashboard, not the API response) |
     | gemini      | transcript `msg.model` | `AccountDef.variant`     | `rate_limited_free`             | NULL (no signal)     |
     | codex       | transcript `msg.model` | `AccountDef.variant`     | `subscription_unknown`          | NULL (no signal — blocked on the [INFRA] P0 fake-token-estimate fix landing real usage first, same as `reasoning_tokens`) |
     | kimi        | transcript `msg.model` | `AccountDef.variant`     | `metered_dollar`                | NULL (no signal)     |
     | nvidia (Gemma) | transcript `msg.model` | `AccountDef.variant`  | `rate_limited_free`             | NULL (no signal)     |

     `computed_usd_equivalent` = the existing `TaskUsageRow.spend_usd` (already computed via `model_pricing.price_usage`
     for any provider with a registered `RateCard` — confirmed real for glm/kimi/gemma today; **gemini has no
     registered `RateCard`, a real gap** — `spend_usd` is currently always None for Gemini tasks, so there is no
     computed-$-equivalent for Gemini yet despite the schema calling for one on every non-`metered_dollar` shape;
     flagged here rather than silently worked around — needs Google's real published metered-API rate registered in
     `model_pricing.py`, a small follow-up, not done this session). This directly unblocks the `[UI] P2`
     billing-display todo above, which named these exact fields as its own real sequencing constraint. Evidence:
     `tests/test_model_pricing.py` (`test_billing_shape_for_provider_*`),
     `tests/test_record_done_task_usage_isolation.py` (`test_requested_model_*`).

  2. **v0 capture mechanism — investigated first, per the todo's own instruction, before writing anything.** Real
     finding: AO's `/done` path (`_record_done_task_usage` -> `state_store.record_task_usage` -> `TaskUsageRow`) was
     ALREADY generic across every provider before this session — it keys off `claude_session_id` + a plain
     transcript scan (`deepseek_usage.compute_task_usage`/`scan_session_usage`), and neither function branches on
     `provider` anywhere. `--output-format json`'s structured output is NOT what's read (contra one plausible
     assumption the todo raised) — the real mechanism is a transcript-file scan, and it was already
     provider-agnostic. The "real testing stops losing its own history" gap the operator hit was never a missing
     capture mechanism: isolated-pilot ad hoc `claude` CLI runs (used to test GLM/Gemini/Codex/Gemma before real
     dispatch is enabled) simply never go through AO's real `/boot`->`/done` flow at all, so of course nothing
     persisted for them — a process gap (pilot runs bypass AO), not a code gap. Proven with a new test,
     `tests/test_multi_provider_v0_capture.py`, driving a REAL GLM account (`AccountDef(provider="glm",
     variant="5.2")`) through the REAL `/done` HTTP-level flow (`slots_worker.done_slot`) with a transcript shaped
     exactly as Claude Code writes one, `message.model="glm-5.3"` (the real aliasing case) — the resulting
     `TaskUsageRow` correctly shows `provider="glm"`, `model="glm-5.3"` (served), `requested_model="5.2"`
     (requested), proving both the pre-existing generic mechanism AND the new `requested_model` field with zero
     manual capture step, zero live account, zero fleet-state touched.

  3. **Reconciliation proof — resolved by finding, not new code.** `compute_deepseek_wallet_reconciliation()`
     (`server/state_store/slots.py:1564`) and `compute_kimi_wallet_reconciliation()` (`:1478`, shipped
     `agent-orchestrator@39d35ed696` per this doc's own 2026-08-18 entry above) already do exactly what this todo
     asks — sum every task's attributed spend from `task_usage` and compare against real wallet drawdown
     (topups − current balance) — for DeepSeek and for Kimi, a genuinely new provider onboarded this cycle. Both
     are already tested with real tolerance-bound numbers: `tests/test_deepseek_wallet_reconciliation.py`
     (`residual_usd == 10.0`, `abs(residual_since_observability_usd - (-16.40)) < 1e-9`) and
     `tests/test_kimi_wallet_reconciliation.py` (`real_total_spend_usd == 5.0`, `residual_usd == 2.0`; the doc's own
     2026-08-18 entry separately cites a real production reconciliation: `$20.0000 topup − $12.5000 balance =
     $7.5000 real spend`). No live GLM/Gemini/Codex/Gemma reconciliation exists yet because none of those 3 shapes
     (`subscription_credits`/`rate_limited_free`/`subscription_unknown`) has a real $ "total spend" signal to
     reconcile against at all — a genuine two-sided $-reconciliation is structurally only possible for the
     `metered_dollar` shape today, which DeepSeek+Kimi already both satisfy.

  4. **Gemini capacity-as-proxy methodology.** New `gemini_headroom.tpm_capacity_consumed_pct(consumed_tokens, *,
     tpm_ceiling)` — real TPM-ceiling-consumed pct, deliberately NOT a fabricated dollar figure (Gemini's free tier
     is genuinely $0, per this doc's own Non-goals). Calibrated exactly against the real 2026-08-19 data point
     already in the todo above: `tpm_capacity_consumed_pct(32_415, tpm_ceiling=250_000) == 12.97` — one real 5-turn
     task alone consumed ~13% of the ENTIRE per-minute TPM budget, and cross-referenced against the real observed
     TPM peak (~120-130K) that same window, ~25-27% of the real peak-minute traffic was this one task — confirming
     TPM (not RPM/RPD, both roomy) is the real binding constraint `gemini_headroom.py`'s own module docstring
     already predicted. Evidence: `tests/test_gemini_headroom.py`
     (`test_tpm_capacity_consumed_pct_matches_real_2026_08_19_calibration_point` + 2 more).

  **Judgment calls made without an operator ruling (flagged, not hidden)**: `requested_model` stores the raw
  `AccountDef.variant` string as-is rather than normalizing it to `model`'s exact format (e.g. "5.2" vs "glm-5.2")
  — sufficient to detect a requested/served divergence without an exact string match, and normalizing would need a
  per-provider format-mapping table that doesn't exist yet; `billing_shape_for_provider` is computed at read time
  from `provider` rather than stored per-row, to avoid a denormalized field going stale on reclassification (e.g.
  Codex's `subscription_unknown` once its real usage-limit metric is confirmed, [REVIEW] P1 todo above).
  Also fixed in the sibling plan while in this exact code area:
  `deepseek_claude_blended_provider_routing_2026_07_28.md`'s `[INFRA] P2` `glm_quota_poller.py` real bug (wrong
  ceiling constants AND wrong unit, prompt-count vs credits) — see that doc's own Progress Log for the fix detail;
  cross-linked here since it shares this session and this code area.

- **2026-08-20 (interactive session, investigating a live incident, not a scoped todo) — operator reported slot 31
  (real `codex-luna` dispatch) showed 99% context in the dashboard before compacting, despite AO's guided
  pre-compact/compact tiers being configured to fire at 60%/70%. Confirmed live, not guessed, via SSM against the
  real orchestrator VM (`i-0c9b283b31d6b5ca7`) and reading `agent-orchestrator/server/model_tier.py` +
  `context_probe.py` directly:

  1. `codex-luna` is currently enabled and live-dispatched (`GET /api/accounts` → `codex-luna` `status: healthy`,
     `used_by_slots: [31]`) — this is real fleet traffic, not a stale/paused config; the account's own plan
     (`codex_mcp_tool_use_bridge_2026_08_18.md`) still shows the unpause as "ready for operator review" as of
     2026-08-19, so it was flipped on since.
  2. `gpt-5.6-luna` (the real `message.model` the bridge's Anthropic-shaped responses echo back — confirmed by
     reading `codex_bridge_server.py`'s own docstring on `_drive_codex_turn`) is not registered in
     `model_tier._ALLOWED_MODEL_WINDOWS`, and has no `is_deepseek()`-style guard in `context_probe.context_window_for()`
     protecting it from calibrating off Claude Code's own wrong internal window guess for an unrecognized model —
     see the new `[INFRA] P0` todo above for the full mechanism and the live `calibrated_window: 263941` figure
     pulled from the VM's `learned_context_windows.json`.
  3. Separately, and independently real: `[INFRA] P1`'s "deploy the real-usage fix to `codex-bridge.service`" todo
     (open since 2026-08-19) is confirmed STILL not done as of this session — `tiktoken` is missing from the
     deployed venv even though the service has restarted since the fix's code landed. See that todo's own updated
     evidence above.

  Both gaps are independently real and both need closing; which one was the PROXIMATE cause of this specific
  99% spike is not fully disambiguated this session (a too-small learned window alone would make AO's own pct
  read HIGH and compact EARLY, not late — so the fake/missing-tiktoken usage-estimate path is the more likely
  direct explanation for the CLI running all the way to its own hard ceiling before anything intervened, with the
  window-registration gap as a second, compounding problem). No code changed this session — investigation only,
  new evidence appended to the 3 todos above (2 existing, 1 new) rather than left as unstructured chat, per this
  workspace's own findings-triage rule. `[unresolved]`: neither underlying todo is fixed; slot 31's context risk
  is UNCHANGED by this session and could recur on its next long run.
  cross-linked here since it shares this session and this code area.
