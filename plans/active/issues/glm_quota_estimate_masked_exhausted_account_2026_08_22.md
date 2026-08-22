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

- [x] ✅ [BACKEND] P2. **Codex arm of the uniform refresh** — `agent-orchestrator@b52c306750`.
      **This todo's own stated premise was wrong, and disproving it WAS the unit.** It said the read
      "runs inside `codex_bridge_server.py`'s OWN uvicorn (port 8769), the only one holding an
      authenticated `openai_codex.Codex()` session, so the refresh route cannot simply call it
      in-process — decide: proxy, or move the read." Neither was needed: the poller opens its OWN
      `with Codex()` every tick, and `Codex()` authenticates from `~/.codex/auth.json` on DISK, not
      from any in-process session. Verified by running the exact RPC from this slot's venv,
      out-of-process, while the live bridge was up — real data returned. The route now calls
      `fetch_codex_quota()` directly.
      Two defects found only because the read was actually measured rather than wired:
      (a) **the account has TWO limit buckets** — `rate_limits` (the headline field the old poller
      read) is only `limit_id="codex"`; `rate_limits_by_limit_id` also carries `codex_bengalfox`
      ("GPT-5.3-Codex-Spark"). Reading the headline alone is the SAME defect as this issue's own
      exhausted-weekly-behind-healthy-5h. New `server/codex_quota.py` parses every bucket and
      reports the max per window kind, because `_account_has_headroom` asks "is there room".
      (b) **`resetsAt` was dropped entirely**, so codex never wrote `rate_limited_until` — the only
      field that actually gates dispatch. An exhausted account stayed selectable until a real 429,
      whose 300s cooldown then re-opened it. Now written from the FURTHEST-OUT exhausted window.
      Trap pinned by test: Codex's `resetsAt` is epoch **seconds**, Z.ai's is **milliseconds** —
      mixing them lands in 1970 or year 58000 and never raises.
      Cadence 5min → 30min. Evidence: gate green (5462 passed/5 skipped, basedpyright 0 errors,
      coverage ratchet held); 30 new tests across `test_codex_quota.py`,
      `test_codex_rate_limit_poller.py`, `test_refresh_account_usage_codex_provider.py`, with the
      verbatim measured vendor payload as the fixture; live end-to-end through the real route arm
      returned `5h=0 wk=37 binding=weekly rate_limited_until=None`, identical to the direct read.
      Three docstrings asserting the now-disproved "no proactive quota API exists for Codex" /
      "only this process can read it" corrected in the same change.

- [x] ✅ [BACKEND] P2. **Gemini arm of the uniform refresh** — `agent-orchestrator@da46d06188`.
      Shipped as `gemini_rate_limit_poller` (30-min) + `_refresh_gemini_usage` (button) +
      `gemini_headroom.gemini_rate_block`. **This is an OBSERVABILITY fix, not a dispatch fix** —
      unlike GLM, dispatch was correctly gated the whole time, because
      `_account_meets_dispatch_headroom` consults Gemini's own RPM/RPD check. What was broken is
      that the block lived ONLY inside that gate: measured 2026-08-22, **six of ten accounts were
      at or over their daily ceiling while all ten displayed `account_status: healthy` with
      `rate_limited_until: None`** (3-7-flash proj1 22/20 · proj2/3/4/5 20/20 · 3-5-flash-lite
      proj2 500/500). `gemini_rate_block` derives the recovery instant from the SAME rows and
      windows the gate reads, so it publishes the existing decision and imposes no new
      restriction — verified against a read-only snapshot of the live DB before any code shipped.
      Followed the todo's shape advice (RPM/RPD, never a Claude-shaped 5h/weekly pair) and its
      no-rotation corollary: this reports a LOCAL gate, so rotating slots on a button click would
      kill live mid-session work the vendor never refused.
      Evidence: gate green (5491 passed/5 skipped, basedpyright 0 errors); 23 new tests across
      `test_gemini_rate_block.py`, `test_gemini_rate_limit_poller.py`,
      `test_refresh_account_usage_gemini_provider.py`. `test_server_lifespan` caught a real
      wiring gap mid-flight — the poller was registered to START but not to be SUPERVISED or
      STOPPED, so it would have died silently at the first supervisor restart; all three
      registries are now wired.

- [x] ✅ [BACKEND] P2. **Self-hosted (`ollama`) arm** — `agent-orchestrator@61a2f9943f`. Worse than
      a missing button: `gemma-self-hosted` DECLARES an `oauth_token_env_file`, so it never hit the
      400 — it fell through to the Anthropic path and spent ~12s driving `claude /usage` in a pty
      against a local Ollama endpoint with no such concept. It degraded safely (`looks_valid`
      False, last-known values survived) but burned the operator's time and reported a parse
      failure for something that was never going to parse. There is no vendor, so there is no
      quota: a REAL answer, not a gap. The arm says so immediately, writes NO percentages and no
      `rate_limited_until`, touches the row so the click is visibly registered, and logs the reason
      so "why does this card never show usage?" has an answer on record rather than looking like a
      poller that quietly never ran. Evidence: gate green (5495 passed/5 skipped, basedpyright 0
      errors); 4 new tests, the load-bearing one being the negative — no fabricated 0%.

- [ ] [UI] P3. **The Refresh button's label and tooltip are now wrong for 13 of 24 accounts.**
      Non-DeepSeek cards render "Refresh from /usage" with the tooltip "Drive `claude /usage` on
      the backend's box, parse, update this card (~12s)" (`dashboard/src/layout.tsx`, the
      account-card footer). That is false for GLM, Codex and Gemini as of the arms above — each now
      does a fast provider-specific read, not a ~12s Anthropic pty — and it was already false for
      Ollama. A genuine misleading-string defect, deliberately NOT fixed inline: any UI tick needs
      `[UI]` + `pw:L2 ✓` + a cited regression spec per
      `/codex/06-coding-standards/ui-testing-layers.md`, which is disproportionate to a label while
      the substantive arms were landing. Repo: agent-orchestrator (dashboard).

- [ ] [BACKEND] P3. **Fold DeepSeek's balance refresh onto the one `/refresh-usage` endpoint.**
      RE-SCOPED (see the correction in the coverage section): this is NOT a user-facing gap —
      DeepSeek's button works today via `/refresh-deepseek-balance`. It is a backend tidy-up: two
      routes doing one job, with the provider branch duplicated in the UI. Extract the shared body
      into `_refresh_deepseek_usage(account_id, acc_def)`, dispatch to it from
      `refresh_account_usage`, and have the dedicated route delegate. Only delete the old route
      once the UI stops calling it (`dashboard/src/api.ts:327`), and that UI change carries the
      Playwright-gate cost, so it is worth doing together with the label todo above. Repo:
      agent-orchestrator.

- [ ] [DOCS] P3. **This issue doc is past the 500-line soft cap (541 as of 2026-08-22).** It grew
      from 285 as five provider arms landed against it. Hard cap is 1000, so nothing is blocked
      today, but the hygiene sweep flags the soft breach and it will keep growing while the
      follow-ups below are worked. Split along the natural seam: the GLM incident + its lessons are
      the ORIGINAL issue and are closed; the per-provider "no exceptions" rollout and its follow-ups
      (restart gap, credential ask, racy gate, UI label) are a distinct workstream that outlived it.
      Repo: unified-trading-pm.

- [ ] [BACKEND] P3. Audit the remaining providers for the same estimate-vs-measurement confusion
      now that the pattern is known: confirm each poller's numbers are a genuine vendor read, and
      that each writes `rate_limited_until` (not just percentages) — a percentage alone never
      stopped dispatch. `ollama`/`gemma-self-hosted` is self-hosted with no vendor quota at all and
      should be explicitly modelled as "no quota" rather than silently None. Repo:
      agent-orchestrator.

- [ ] [BACKEND] P2. **`ao-self-pull.sh` restarts ONLY `orchestrator` — the two sibling uvicorn
      services keep running stale code indefinitely.** Measured 2026-08-22 (slot 15): the script's
      only restart target is `systemctl restart orchestrator`, while `codex-bridge.service` (:8769)
      and `deepseek-native-proxy.service` (:8767) run from the SAME checkout and are never
      restarted. `RESTART_RELEVANT_PATHS=(server/ config/ pyproject.toml uv.lock)` already matches
      edits to `server/codex_bridge_server.py`, `server/codex_rate_limit_poller.py` and
      `server/deepseek_native_proxy_server.py` — the relevance gate fires, but the wrong process is
      bounced.
      **Measured proof, not inference:** at 06:59 UTC the root checkout was already FF'd to
      `b52c306750` (so `orchestrator`, and therefore the Refresh-button arm, was live), while the
      bridge process had been running since **2026-08-21 07:48:51** — ~23 h of stale code, having
      consumed 18 h 01 m CPU. Nothing reported the drift. Restarting it by hand made the poller arm
      live immediately: `codex-luna` went from `5h=None wk=37 claim=None` (old poller: headline
      bucket only, no binding window) to `5h=0 wk=37 claim=weekly` within the poller's 30 s settle.
      **NOT a privilege problem** — passwordless `sudo` is available to the fleet user; a bare
      `systemctl restart codex-bridge` fails with "Interactive authentication required" only
      because `ao-self-pull.sh` runs as ROOT from cron (it uses `sudo -u "${SLOT_USER}"` to drop
      DOWN for git), so `sudo systemctl restart codex-bridge` works fine. The fix is purely that
      the script never targets the other two units.
      Constraint on the fix: the script deliberately rate-limits restarts because the fleet ships
      its own commits to LDR (52 self-restarts on 2026-08-21), so this must be relevance-scoped per
      service — bounce codex-bridge only when a codex module changed — not a blanket "restart all
      three on any `server/` change". Repo: agent-orchestrator.

- [ ] [BACKEND] P3. **codex-bridge peaked at 14.3 GB RSS + 1.1 GB swap over one ~23 h run.**
      Reported by systemd on the 2026-08-22 restart above (`Consumed 18h 1min 44.820s CPU time,
      14.3G memory peak, 1.1G memory swap peak`). Noticed incidentally, not investigated — but that
      is a large footprint for an Anthropic↔Codex translation facade, and it grew unbounded across
      a run precisely because nothing ever restarts the process (see the todo above), so a slow
      leak would never be truncated. Worth one look before assuming it is normal. Repo:
      agent-orchestrator.

- [ ] [DOCS] P3. **The restart runbook has no `codex-bridge` / `deepseek-native-proxy` entry at
      all.** `/codex/15-runbooks/safe-service-restart-procedures.md` returns zero matches for either
      (grepped 2026-08-22), so the fix-vs-not table CLAUDE.md points every agent at is silent on two
      of the three live uvicorn services — including what an in-flight Codex turn loses on a bounce.
      Depends on the todo above resolving how they get restarted. Repo: unified-trading-pm.

- [ ] [BACKEND] P3. **Re-decide `free_provider_priority` now that codex has a real headroom
      signal.** The default `[deepseek, gemini, glm, ollama, codex]` puts codex LAST on the stated
      grounds that "it has no proactive quota/rate-limit poller at all, so it never fails a headroom
      check regardless of real usage". That premise is void as of the change above — codex now
      reports per-window percentages AND a `resetsAt` for every limit bucket, and fails a headroom
      check on real exhaustion. `/codex/04-architecture/agent-orchestrator-autospawn.md` §4 has been
      corrected to say the rationale no longer holds AND that the ordering has not been re-decided;
      this todo is the re-decision (there may still be cost/capability reasons to keep codex last —
      that is a separate argument from the one that was actually written down). Repo:
      agent-orchestrator.

- [ ] [OPERATOR] P2. **BLOCKED-CREDENTIALS — grant the fleet SA read access to the five Gemini
      GCP projects, so Gemini's numbers become a vendor MEASUREMENT instead of a self-count.**
      Probed 2026-08-22 from the planning VM as
      `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`, all three vocabularies:
      `gcloud services list` and `gcloud alpha quotas info list` both return PERMISSION_DENIED
      (`cloudquotas.quotas.get` denied) on `gen-lang-client-0008266149`, and a successful
      `GET generativelanguage.googleapis.com/v1beta/models` returns HTTP 200 carrying **no**
      quota/ratelimit/retry-after header. So — unlike GLM, where "no signal exists" was a
      wrong-vocabulary absence-proof — Google's signal genuinely EXISTS (Cloud Monitoring's
      `serviceruntime.googleapis.com/quota/*` series, Cloud Quotas for the ceilings) and is
      credential-blocked. Per `/codex/02-data/external-data-always-available-rule.md` that is a
      credential ask, not a descope, and the adapter scaffold is already built and shipped.
      **Needs**: `roles/monitoring.viewer` (and ideally `roles/cloudquotas.viewer`) for that SA on
      `gen-lang-client-0008266149`, `elated-nectar-440116-e9`, `poetic-bongo-456907-e4`,
      `371216509644`, `spring-mix-426915-t9`. This is NOT self-serviceable under the usual
      IAM-self-service rule: those are AI-Studio-created projects outside the fleet's own project,
      so only someone with admin on them can grant it. Two payoffs: the count stops being blind to
      non-fleet traffic, and `GEMINI_RATE_CEILINGS` stops being hardcoded operator-supplied numbers
      from 2026-08-14. Repo: agent-orchestrator (once granted).

- [ ] [BACKEND] P3. **The Gemini RPD gate is racy — check-then-act with no lock.** Measured
      2026-08-22: `gemini-3-7-flash-proj1` sat at **22 selections against a ceiling of 20**, all 22
      inside one ~52-minute burst on 2026-08-21 (08:34-09:26), well under the 5 RPM ceiling. So the
      overshoot is on RPD: `gemini_account_has_rate_headroom` admits while `count < rpd`, and N
      concurrent spawns can each read 19 and all proceed. 10% overshoot on a ceiling of 20. Not
      urgent (the vendor 429s rather than billing), but it means the gate cannot be described as a
      hard ceiling. Repo: agent-orchestrator.

- [ ] [BACKEND] P3. **`GEMINI_RATE_GATE_SKIPPED_EVENT` is declared but nothing ever emits it.**
      `server/gemini_headroom.py` defines the constant; a repo-wide grep finds that definition and
      no writer at all, and the activity log has zero rows of that type. It reads as observability
      coverage that does not exist — anyone asking "is the gate ever being skipped?" would find the
      constant and wrongly conclude the question is already instrumented. Either emit it at the
      real skip path (the unregistered-`variant` fail-open branch is the obvious candidate) or
      delete it. Repo: agent-orchestrator.

- [ ] [BACKEND] P3. **Confirm whether Gemini free-tier RPD is a rolling 24h window or a calendar
      day.** `gemini_headroom` models it as ROLLING 24h (`_RPD_WINDOW = timedelta(days=1)`), which
      is what `gemini_rate_block` now publishes as `rate_limited_until`. Google documents free-tier
      RPD as a per-CALENDAR-DAY quota. If the calendar-day reading is right, AO holds an account
      blocked after Google has already reset it — wrong in the SAFE direction (under-dispatch, not
      a 429 storm), but it silently costs capacity: on 2026-08-22 six accounts were held with
      recovery instants spread from 08:34 to 14:14 that a midnight-PT reset would have cleared at
      once. **Do not "fix" this by guessing a reset hour** — the whole point of this issue is not
      substituting a plausible number for a measured one. Confirm against a real reading (the
      credential ask above would settle it directly). Repo: agent-orchestrator.

## Coverage of the "no exceptions" directive — measured, not estimated

Counted from the live `data/config/accounts.json` on the planning VM, 2026-08-22 (24 accounts):

| provider  | accounts | 30-min poll             | Refresh button                  |
| --------- | -------: | ----------------------- | ------------------------------- |
| anthropic |        8 | ✅ `usage_poller`       | ✅ pty `/usage`                 |
| gemini    |       10 | ✅ `gemini_rate_limit_poller` | ✅ `_refresh_gemini_usage` |
| glm       |        2 | ✅ `glm_quota_poller`   | ✅ `_refresh_glm_usage`         |
| deepseek  |        2 | ✅ balance/usage poller | ✅ own endpoint, works          |
| codex     |        1 | ✅ `codex_quota` (live) | ✅ `_refresh_codex_usage`       |
| ollama    |        1 | n/a — no vendor exists  | ✅ `_refresh_selfhosted_usage`  |

**All 24 accounts covered — the directive is satisfied.**

**Correction to an earlier reading in this doc.** I first recorded DeepSeek's separate button as
"exactly the shape the directive named" and scoped folding it as directive work. Reading the
actual render logic (`dashboard/src/layout.tsx`, the `isDeepseek` ternary in the account card's
footer) shows that is wrong: the UI branches exactly ONCE — DeepSeek gets its own button, and
**every other provider** gets "Refresh from /usage" wired to `/refresh-usage`. So GLM, Codex,
Gemini and Ollama cards always HAD a button; it simply 400'd or ran a meaningless Anthropic pty
probe until the arms above existed. DeepSeek's button works. Folding it onto one endpoint is a
backend tidy-up (two routes doing one job), NOT a user-facing gap, and is re-filed at that
priority. What the re-scoping exposed is that `ollama` was the real last gap, and a worse one
than a missing button — see its todo.

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

- **2026-08-22 (slot 15, `/autonomous`) — shipped `agent-orchestrator@b52c306750` (Codex arm).**
  The unit turned out to be disproving this issue's own recorded premise. The todo asserted the
  read was locked inside the bridge process and needed a proxy-or-move decision; measuring it
  first showed the poller opens its OWN `with Codex()` per tick and authenticates from
  `~/.codex/auth.json` on disk, so the route calls it directly and neither option was needed.
  Two live defects surfaced only because the response was actually read: a SECOND limit bucket
  (`codex_bengalfox`) invisible to the headline `rate_limits` field, and `resetsAt` being dropped
  so codex never wrote the one field that gates dispatch. Both are the same shapes this issue
  already documents for GLM, which is the argument for treating the pattern as cross-provider
  rather than per-vendor. Also measured: `ao-self-pull.sh` restarts ONLY `orchestrator`, so
  `codex-bridge`/`deepseek-native-proxy` run stale code after every LDR pull — filed as its own
  P2 todo, since it means poller changes to those modules do not take effect on their own.

- **2026-08-22 (slot 15, `/autonomous`) — shipped `agent-orchestrator@da46d06188` (Gemini arm).**
  Gemini turned out NOT to be the "wire up the existing snapshot" job the todo assumed, in two
  directions. Better than feared: dispatch was never broken — `_account_meets_dispatch_headroom`
  has always consulted Gemini's RPM/RPD check, so unlike GLM nothing was being dispatched into a
  dead account. Worse than feared: that check was the ONLY place the block existed, so six of ten
  accounts sat at/over their daily ceiling while all ten displayed healthy. And the numbers behind
  it are a LOCAL self-count, not a vendor read — structurally the same shape as the GLM estimate
  this issue is named for, which is why the credential ask above is filed rather than the fact
  being glossed. I deliberately did not repeat the GLM error in reverse: rather than assume "no
  signal exists", I probed Cloud Quotas, Service Usage and the inference headers, and the honest
  finding is that the signal EXISTS and is permission-denied. Three smaller defects fell out of the
  measurement (racy RPD gate at 22/20, a never-emitted observability event, rolling-vs-calendar RPD
  semantics), all filed above rather than fixed inline. Process note: `test_server_lifespan` caught
  a genuine wiring gap I had introduced — the new poller was registered to START but not to be
  SUPERVISED or STOPPED, so it would have died silently at the first supervisor restart. That test
  earned its keep; nothing else in the suite would have noticed.

- **2026-08-22 (slot 15, `/autonomous`) — shipped `agent-orchestrator@61a2f9943f` (self-hosted arm);
  directive COMPLETE.** All 24 accounts now covered on both the poll and the button. Two things
  worth carrying forward. First, a correction to my own earlier reading in this doc: I had recorded
  DeepSeek's separate button as a directive gap, and reading `layout.tsx` showed it is not — the UI
  branches once, DeepSeek gets its own working button and everything else already pointed at
  `/refresh-usage`. Re-scoping it is what surfaced `ollama` as the genuine last gap, and a nastier
  one than a missing button, because it declares an env file and therefore fell through to a ~12s
  Anthropic pty probe rather than failing fast. Second, the arithmetic reconciled on purpose: the
  gate went 5491 → 5495 while I expected +5, and the discrepancy was my own miscount (the file has
  4 tests), not a silently uncollected test file — worth checking rather than assuming, since a
  test file that never gets collected is indistinguishable from a passing one in the summary line.

## Deferred work after 2026-08-22

The operator's "no exceptions" directive is COMPLETE: all 24 accounts are covered on both the
30-min poll and the Refresh button. Everything below is follow-up the measurements exposed, not
the directive itself.

Recommended NEXT item: **the `ao-self-pull.sh` restart gap** — it is the only open item that
silently un-does shipped work. `codex-bridge` ran 23h-old code until it was restarted by hand on
2026-08-22, and the next edit to any of its three modules will do the same again with nothing
reporting it. After that, the Gemini credential ask is the highest-value one, since it converts
Gemini's self-count into a real vendor measurement.

| item | state / why deferred | blocked on |
| --- | --- | --- |
| Fold DeepSeek onto the one `/refresh-usage` endpoint | **Not done** — RE-SCOPED to a backend tidy-up; its button already works, so this is two routes doing one job, not a user-facing gap. Pairs with the UI label todo (shared Playwright cost) | nobody — pick it up |
| Refresh button label/tooltip wrong for 13 of 24 accounts | **Not done** — says "Refresh from /usage … ~12s Anthropic pty", false for GLM/Codex/Gemini/Ollama now. Needs the `[UI]` + `pw:L2` gate | nobody — pick it up |
| Gemini numbers are a self-count, not a vendor measurement | **Operator-owned** — needs `monitoring.viewer` for the fleet SA on five AI-Studio GCP projects; not self-serviceable, they sit outside the fleet's own project | operator (IAM on those projects) |
| Gemini RPD gate is racy (22/20 measured) | **Not done** — check-then-act with no lock; concurrent spawns can each see 19 and proceed | nobody — pick it up |
| `GEMINI_RATE_GATE_SKIPPED_EVENT` declared but never emitted | **Not done** — emit it at the real skip path or delete it; today it reads as coverage that does not exist | nobody — pick it up |
| Gemini RPD: rolling 24h vs calendar day | **Not done** — AO models rolling; Google documents calendar-day. Wrong in the safe direction, but costs capacity. Needs a real reading, NOT a guessed reset hour | the credential ask above would settle it |
| `ao-self-pull.sh` restarts only `orchestrator`; `codex-bridge` + `deepseek-native-proxy` run stale code | **Not done** — measured 2026-08-22. Fix must be relevance-scoped per service, not a blanket restart-all (the script rate-limits restarts for a real reason: 52 fleet self-restarts on 2026-08-21) | nobody — pick it up |
| Restart runbook has no `codex-bridge` / `deepseek-native-proxy` entry | **Not done** — zero grep matches; depends on the row above deciding how they get restarted | the row above |
| Re-decide `free_provider_priority` now codex has a real headroom signal | **Not done** — the written rationale for codex-last is void; the ordering itself may still be right for other reasons | nobody, but it is a judgment call |
| Cross-provider audit: every poller writes `rate_limited_until`, not just percentages | **Not done** — the GLM lesson generalises; codex is now done, the rest are not | nobody — pick it up |
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
- **A premise recorded in a todo is not evidence — re-measure it before designing around it.**
  The Codex todo above confidently framed the work as "proxy or move the read", and both options
  were real engineering. Neither was necessary: one 30-second out-of-process probe disproved the
  constraint. The premise had been written down twice (module docstring, then copied into the
  todo), which is exactly what makes this class of error survive — each restatement reads as
  corroboration. Cost of checking: one command. Cost of not checking: a cross-process proxy
  nobody needed.
- **"One vendor field per meter" is an assumption, not a reading.** Codex reports MULTIPLE limit
  buckets keyed by model family, and the response's headline field is only the first of them.
  Before trusting any vendor usage number, enumerate what the response actually contains — the
  aggregate you want may not be the one the API puts in the obvious place.
- **Epoch units differ per vendor and fail silently.** Z.ai's `nextResetTime` is milliseconds;
  Codex's `resetsAt` is seconds. Both parse. Both produce a plausible-looking `datetime`. Only one
  is in this decade. Any new vendor timestamp gets an explicit assertion on the resulting YEAR.
