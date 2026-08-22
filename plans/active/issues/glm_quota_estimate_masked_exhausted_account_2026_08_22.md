---
doc_type: issue
title: >-
  GLM quota was a local ESTIMATE that read ~14% while Z.ai's real weekly meter was 100%
  exhausted — AO kept dispatching onto a refusing account, and the estimate also vetoed
  every genuine 429 in tmux_pruner's reactive catch
summary: >-
  Operator reported AO believing accounts healthy while usage limits were exhausted, and
  that tasks dispatched to them "die or keep wasting time doing nothing" — confirmed exactly.
  `glm_quota_poller.py` never contacted Z.ai: it counted AO's OWN `free_provider_spawn_selected`
  activity_log rows, multiplied by an assumed credits-per-request constant and divided by an
  assumed ceiling. That estimate existed only because a 2026-08-18 investigation concluded Z.ai
  exposes no quota signal — measured WRONG on 2026-08-22: that probe looked at INFERENCE
  response headers and never looked for a separate monitoring API. `GET
  https://api.z.ai/api/monitor/usage/quota/limit` returns real per-window allowance,
  consumption, remaining credits and reset instant. First real read: 5-hour meter 66% (677
  credits left) but the WEEKLY meter 100% / `remaining: 0`, resetting ~26h out — while AO's
  estimate said weekly 14%, `account_status: healthy`. Two consequences, both live-confirmed:
  (1) `autospawn._account_has_headroom` reads those very fields, so dispatch kept selecting a
  dead account (429 storm across ~14 slots, 2026-08-21/22); (2) `tmux_pruner`'s
  `_PANE_HEURISTIC_TRUST_CEILING_PCT` guard treats those percentages as "real-probe evidence"
  and used them to DISCARD every genuine 429 pane, so `rate_limited_until` was never set.
  Poller replaced with a real vendor read; the guard's premise is now documented + pinned.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    glm,
    z-ai,
    quota,
    rate-limit,
    account-health,
    dispatch,
    usage-poller,
    measurement-discipline,
  ]
related:
  [
    /plans/active/issues/model_provider_badge_mismatch_2026_08_21.md,
    /plans/active/issues/ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
  ]
created: "2026-08-22"
last_updated: "2026-08-22"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/glm_quota.py,
    agent-orchestrator/server/glm_quota_poller.py,
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/state_store/account_usage.py,
    agent-orchestrator/server/routes/accounts.py,
  ]
source: >-
  Operator, interactive session 2026-08-22 (slot 15): "the account usage data being wrong
  suggests deeper problems that we have to fix, if the AO believes that accounts are healthy
  when usage limits are exhausted, AO will keep dispatching tasks to this account and since
  accounts are exhausted, those tasks will die or keep wasting time doing nothing", followed by
  "usage poller should get the usage stats every 30 minutes just like anthropic models and when
  user clicks on the refresh usage button in the UI. There shouldnt be any exceptions in both of
  these things ... take it slow and one model at a time and fix it at root and measure".
---

# GLM quota: an estimate that masked a fully-exhausted account

## What was measured (not inferred)

`GET https://api.z.ai/api/monitor/usage/quota/limit`, header `Authorization: <token>` (Bearer
prefix optional — both return 200), no query parameters. Live response, 2026-08-22:

```json
{"code":200,"success":true,"data":{"level":"lite","limits":[
  {"type":"CREDIT_LIMIT","unit":3,"number":5,"usage":2000,"currentValue":1322,
   "remaining":677,"percentage":66,"nextResetTime":1787377400135},
  {"type":"CREDIT_LIMIT","unit":6,"number":1,"usage":10000,"currentValue":10010,
   "remaining":0,"percentage":100,"nextResetTime":1787469611997}]}}
```

`unit=3,number=5` is the rolling 5-hour meter; `unit=6,number=1` the weekly one. `usage` is the
allowance, `currentValue` the consumption, `nextResetTime` epoch-ms. Note `currentValue` (10010)
EXCEEDS `usage` (10000) on the exhausted window — the vendor does not clamp it, so `remaining <= 0`
is the reliable exhaustion signal.

| | AO believed (estimate) | Z.ai actually reported |
| --- | --- | --- |
| 5-hour | 28-30% | 66% (677 credits left) |
| weekly | 13-14% | **100% — `remaining: 0`**, resets 2026-08-23 07:20 UTC |
| status | `healthy` | refusing every request |

Both GLM accounts return IDENTICAL numbers: they share one Coding Plan
(`api_key_secret_name: glm-coding-plan-api-key` on both), so the quota is **per-plan, not
per-account** — the old per-account count-based estimate was wrong in that dimension too.

This also explains a detail that had looked inconsistent: the 429 text says "Usage limit reached
for 5 hour", and each 5-hour reset came and went with no recovery, because the binding meter was
the weekly one.

## Why the estimate existed, and why that reasoning failed

`glm_quota_poller.py`'s own docstring asserted *"Z.ai's API also has no documented usage-query
endpoint ... there is no server-side quota signal to poll for GLM, full stop"*, citing a
2026-08-18 live check. That check inspected the complete raw response headers of a real
`POST /api/anthropic/v1/messages` call and correctly found no `anthropic-ratelimit-*`-style
signal. The error was the leap from "no quota headers on the inference endpoint" to "no quota
signal anywhere" — it never probed for a separate monitoring API. A wrong-vocabulary
absence-proof, the exact failure mode `/codex/12-agent-workflow/measurement-claims-discipline.md`
warns about ("0 hits ≠ missing").

The guessed CEILINGS turned out to be exactly right (2000 / 10000 match the vendor's `usage`); it
was `glm_assumed_credits_per_request` — explicitly a placeholder — and the count-based model that
could not track real consumption.

## Todos

- [x] ✅ [BACKEND] P1. Replace the count-based estimate with the real vendor read: new
      `server/glm_quota.py` (fetch + parse + GSM-first token resolution mirroring
      `deepseek_balance.py`), `glm_quota_poller.py` rewritten to consume it, write
      `rate_limited_until` from the FURTHEST-OUT exhausted window (an exhausted weekly meter keeps
      rejecting long after the 5-hour one resets), clear a stale mark on a healthy read, and never
      substitute a fabricated number when the fetch fails. Delete the three now-unused estimate
      config knobs. — DONE 2026-08-22, `agent-orchestrator@c8c6f5c7f0`. Evidence: full
      `quality-gates.sh` PASSED (every step verified individually — 5427 passed/5 skipped,
      coverage 86.2119% vs 85.8559% baseline, basedpyright 0 errors, ruff format/lint clean, tsc +
      468 vitest). Live end-to-end verification through the real GSM token path, both GLM accounts:
      `five_hour 66% (1322/2000, remaining 677)`, `weekly 100% (10010/10000, remaining 0)`,
      `exhausted_until=2026-08-23T07:20:11Z`, `gate-fires=True`. Cadence 5 -> 30 min to match
      `usage_poll_interval_minutes`. Both accounts return IDENTICAL numbers — the quota is
      per-PLAN, not per-account (they share `glm-coding-plan-api-key`), so the old per-account
      count-based split was wrong in that dimension too.

- [x] ✅ [BACKEND] P1. Make `tmux_pruner`'s `_PANE_HEURISTIC_TRUST_CEILING_PCT` premise explicit and
      pinned: the guard (added for `ao_pane_heuristic_contradicts_real_usage_2026_08_17`) is sound
      ONLY while those percentages are a genuine vendor measurement. Regression tests both
      directions — a real exhausted reading (weekly 100) must NOT suppress a 429 mark; healthy real
      percentages must still veto a stale/re-rendered banner. — DONE 2026-08-22, same commit
      `agent-orchestrator@c8c6f5c7f0`. Note the inversion needed no restructuring of the guard: with
      the real read the exhausted account reports `weekly_pct=100`, which fails the `< 90` ceiling,
      so the mark now correctly proceeds. The ESTIMATE was the entire bug. Verified by evaluating
      the guard's own condition against both readings — estimate (14/30) -> veto fires, mark
      SUPPRESSED; real (100/66) -> veto stands down, mark PROCEEDS.

- [ ] [SCRIPT] P2. **Found while shipping the above — the gate does not lint `tests/`.**
      `scripts/quality-gates.sh:104` runs `ruff check server/` only, so a lint error in a test file
      passes the gate GREEN and then blocks the commit at pre-commit (which lints everything
      staged). Cost two full ship cycles here on three `N802` test-name violations that a green gate
      had already blessed. Either widen the gate's ruff step to the same paths pre-commit lints, or
      scope pre-commit to match the gate — but the two must not disagree, because "gate green" is
      the documented commit contract. Repo: agent-orchestrator.

- [ ] [BACKEND] P2. **Residual staleness window, deliberately not papered over.** With a 30-min
      poll, an account that exhausts 1 minute after a healthy read keeps healthy-looking (real,
      but stale) percentages for up to ~29 minutes, during which the pct veto still suppresses the
      reactive 429 catch. Bounded (the next poll corrects it) and far better than the previous
      "forever", but real. Fixing it properly needs a "when was this figure last probed" timestamp
      on `AccountUsageRow` so the veto can require freshness, not just presence — a schema change,
      deliberately not bundled into this fix. Repo: agent-orchestrator.

- [x] ✅ [BACKEND] P2. Uniform refresh — provider dispatch added to
      `/api/accounts/{id}/refresh-usage` so the button is no longer Anthropic-only. — DONE
      2026-08-22 for GLM, `agent-orchestrator@fd7bfbe531`. A GLM account now takes
      `_refresh_glm_usage` (real Z.ai read, same generic fields, `rate_limited_until` from the
      furthest exhausted window, slot rotation when genuinely blocked) instead of the
      `claude /usage` pty — which is Anthropic-only by construction, and which also 400s on GLM
      because GLM authenticates from GSM rather than an `oauth_token_env_file`. 6 new tests incl.
      one asserting the pty is NEVER invoked for GLM. Full gate PASSED (5432 passed/5 skipped,
      coverage 86.2214% vs 85.8559%). **Scope: GLM only** — Codex and Gemini still fall through to
      the Anthropic path; see the two follow-ups directly below, which are what remains of "no
      exceptions".

- [ ] [BACKEND] P2. **Codex arm of the uniform refresh.** `codex_rate_limit_poller` already does a
      REAL vendor read (`account/rateLimits/read` via the Codex SDK) and writes the same generic
      `five_hour_pct`/`weekly_pct`, so this is wiring, not discovery — but it runs inside
      `codex_bridge_server.py`'s OWN uvicorn process (port 8769), the only one holding an
      authenticated `openai_codex.Codex()` session, so the refresh route cannot simply call it
      in-process. Decide: proxy the refresh to the bridge, or move the read. Repo: agent-orchestrator.

- [ ] [BACKEND] P2. **Gemini arm of the uniform refresh.** Gemini's real signal is RPM/RPD/TPM
      per GCP project (`gemini_headroom.compute_gemini_capacity_snapshot`), NOT a 5-hour/weekly
      pct pair — `AccountView` already carries the 5 gemini_* capacity fields for exactly this.
      So the refresh arm should recompute + return that snapshot rather than forcing Gemini into a
      Claude-shaped window, which is the same category error
      `model_provider_badge_mismatch_2026_08_21` already fixed once in the dashboard's generic
      `AccountRow`. Repo: agent-orchestrator.

- [ ] [BACKEND] P3. Audit the remaining providers for the same estimate-vs-measurement confusion
      now that the pattern is known: confirm each poller's numbers are a genuine vendor read, and
      that each writes `rate_limited_until` (not just percentages) — a percentage alone never
      stopped dispatch. `ollama`/`gemma-self-hosted` is self-hosted with no vendor quota at all and
      should be explicitly modelled as "no quota" rather than silently None. Repo:
      agent-orchestrator.

## Progress Log

- **2026-08-22 (slot 15, `/autonomous`)**: filed while fixing. Root cause found by probing the
  endpoint rather than trusting the in-repo "no quota signal, full stop" claim — that claim is
  itself the finding, and its own docstring is corrected in the same change. Verified end-to-end
  through the real GSM token path (both GLM accounts, `gate-fires=True` on the exhausted weekly
  window). One trap worth recording for whoever touches the token path next: the live GLM env
  files hold `ANTHROPIC_AUTH_TOKEN="$(gcloud secrets versions access ...)"`, a command
  substitution — `usage_tracker.read_env_var_from_file`'s `\S+` capture stops at the first space
  and yields the 9-character fragment `"$(gcloud`, which Z.ai rejects with a 401 that reads like a
  genuine auth failure. GSM (`api_key_secret_name`) is the intended path for these accounts;
  `glm_quota.py` now detects the unexpanded substitution and reports "no token" instead of sending
  garbage. `deepseek_balance.py`'s own docstring already documented this hazard.

- **2026-08-22 (slot 15, `/autonomous`) — shipped `agent-orchestrator@c8c6f5c7f0`.** Four process
  frictions on the way, each worth remembering because none was a code defect:
  (1) The gate FAILED on a single `ruff format --check` step at the TOP of a 9,578-line log while
  all 5,419 tests passed — and my failure-greps (`FAILED`, `error:`, `N failed`) do not match
  ruff's `Would reformat:` wording. Reading every `── step ──` header's own verdict is the only
  reliable check; neither the exit code nor a keyword grep is sufficient.
  (2) Quickmerge correctly BLOCKED on `QUICKMERGE_BLOCKED code=PRECOMMIT_WORKING_TREE_CONFLICT` —
  2 commits behind with `server/server.py` dirty on both sides. Recovered via the documented recipe
  (save the diff, `git stash push -- <file>` BY NAME, `git pull --ff-only`, pop, then verify content
  survival in BOTH directions) rather than the `QUICKMERGE_ALLOW_BEHIND=1` override. Confirmed my
  comment AND upstream's `slot_is_operator_paused` guard both present afterwards.
  (3) That ff-pull moved HEAD, invalidating the green sentinel — so the gate had to re-run against
  the MERGED tree. Correct, not waste: upstream's two commits touch `worker_liveness_watchdog.py`
  and `dispatch.py`, the same module family as the rate-limit path this change edits, and that
  combination had never been tested together.
  (4) **A real gap, now tracked as its own todo above**: the gate lints `server/` only, so three
  `N802` violations in my new test files passed a GREEN gate and then blocked the commit at
  pre-commit. "Gate green" is the documented commit contract, so the gate and pre-commit disagreeing
  about what gets linted is a defect in the contract, not just an annoyance.

## Deferred work after 2026-08-22

Recommended NEXT item: **the Codex arm of the uniform refresh** — it is the only remaining
"no exceptions" gap whose vendor read already exists and is proven, so it is wiring rather
than investigation. Gemini's arm needs a shape decision first (RPM/RPD is not a 5h/weekly
pair), and everything else below is either waiting on elapsed time or owned by a human.

| item | state / why deferred | blocked on |
| --- | --- | --- |
| Codex arm of uniform refresh | **Not done** — vendor read exists (`codex_rate_limit_poller`), but it lives in the separate bridge process (:8769) that owns the authenticated Codex session; needs a proxy-or-move decision | nobody — pick it up |
| Gemini arm of uniform refresh | **Not done** — needs the RPM/RPD/TPM shape, not a Claude-shaped 5h/weekly pair | nobody — pick it up |
| Cross-provider audit: every poller writes `rate_limited_until`, not just percentages | **Not done** — the GLM lesson generalises; `ollama`/`gemma-self-hosted` should be modelled as "no vendor quota" explicitly rather than silently None | nobody — pick it up |
| Residual ≤29-min staleness window in `tmux_pruner`'s pct veto | **Not done** — needs a "last probed at" column on `AccountUsageRow` so the veto can require freshness, not just presence. Deliberately NOT bundled: it is a schema change | nobody, but it is a design step |
| Gate lints `server/` only, pre-commit lints everything staged | **Operator-owned** — operator said 2026-08-22 they will take this with another agent. Do not start it | operator (explicitly claimed) |
| 4 `gemini-*` accounts have no env file; `gemini-3-5-flash-lite-proj5` is still `healthy`/selectable | **Operator-owned** — `claude setup-token` is an interactive OAuth flow, not scriptable. Until then every spawn onto one 503s | operator |
| GLM/DeepSeek/Gemma resume | **Cannot be done yet** — operator paused them deliberately; GLM's own weekly meter is also exhausted until 2026-08-23 07:20 UTC regardless | elapsed time + operator |

## Lessons (would otherwise be re-learned the hard way)

- **An absence-proof is only as good as the vocabulary it probed.** "Z.ai exposes no quota
  signal, full stop" came from inspecting INFERENCE response headers. The quota lives on a
  separate monitoring endpoint. Before trusting any in-repo "X does not exist" claim, check
  what was actually probed — the claim here was confidently written, cited a live check, and
  was wrong.
- **A wrong number in the SAFE direction is worse than no number.** The estimate read 14%
  weekly against a real 100%. Had it errored or returned None, dispatch would have skipped the
  account; instead it kept selecting it. Hence: a failed fetch now leaves prior values alone
  and never substitutes a fabricated one.
- **A percentage never stopped dispatch — `rate_limited_until` does.** Any future provider
  poller that writes only percentages will reproduce this bug in its own provider.
- **Gate green ≠ commit-ready** (see the todo above), and **a task-completion notification's
  exit code is not the gate's verdict** — one run reported "exit code 0" for a gate that
  exited 1, because a trailing `echo` in the backgrounded command was what exited 0. Read the
  log, and read every `── step ──` header's own verdict: one run failed on a single
  `ruff format` step at the TOP of a 9,578-line log while all 5,419 tests passed, and the
  standard failure-greps (`FAILED`, `error:`, `N failed`) do not match ruff's
  `Would reformat:` wording.
- **Rejected approach**: restructuring `tmux_pruner`'s pct veto. Its premise ("real-probe
  evidence overrides a weak text match") is correct and it was added for a real 2026-08-17
  incident; the premise was simply FALSE for GLM. Fixing the data source fixed the veto. Do
  not weaken that guard — a stale/re-rendered banner really can re-block a healthy account.
- **The quota is per-PLAN, not per-account** for GLM: both accounts share
  `glm-coding-plan-api-key` and return byte-identical numbers.
