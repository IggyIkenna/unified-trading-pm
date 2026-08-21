---
doc_type: issue
title: >-
  Fleet dispatch stall — 824 queued tasks against 19 idle worker slots and a 76% autospawn
  failure rate; primary cause is a dot-vs-dash alias mismatch that made all 6 credentialed
  Gemini accounts 400 on every call while reporting healthy with full quota headroom
summary: >-
  Operator report (2026-08-21): "827 tasks in queue, 444 blocked, why are the others not
  getting dispatched even though there are free slots and accounts with usage-quota
  headroom?" Measured live on the orchestrator VM: 824 queued / 19 genuinely idle non-human
  worker slots / autospawn 22 failures vs 7 successes in the sampled activity window (76%
  failure rate) — and 5 of those 7 "successes" were zombie workers that booted and then
  failed every API call. PRIMARY ROOT CAUSE: the LiteLLM proxy config
  (`config/litellm/grok_gemini_proxy.yaml`) built every Gemini `model_name` alias from the
  accounts.json `variant` field (`gemini-3.5-flash-lite-proj1`, DOTTED) while a spawned
  worker resolves its backend from the account env file's ANTHROPIC_MODEL, which is the
  accounts.json `id` (`gemini-3-5-flash-lite-proj1`, DASHED). Every real Gemini request
  therefore named a model the proxy had never registered and got
  `400 anthropic_messages: Invalid model name`; the worker still booted (tmux session up,
  `autospawn_succeeded` logged), failed every call, idled, and was reclaimed — so the
  dashboard showed all 10 Gemini accounts `healthy` with full RPM/RPD headroom while 6 of
  them (25% of the 24-account pool) were structurally unable to do any work. It hid because
  `server/gemini_translation_smoke.py` resolves the model name by READING THAT SAME CONFIG,
  so the smoke test asked for the dotted alias the proxy really did serve, passed, and
  proved nothing about the string production actually sends. Config alias form corrected +
  regression test added (agent-orchestrator@bee25ba8de); four secondary causes and one
  amplifier remain open below.
status: open
resolved_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    autospawn,
    dispatch-stall,
    gemini,
    litellm,
    translation-proxy,
    fleet-capacity,
    account-failover,
    model-naming,
  ]
related:
  [
    /plans/active/grok_gemini_translation_proxy_2026_08_14.md,
    /plans/archive/issues/worker_slot_account_exhaustion_no_rotation_2026_08_19.md,
    /plans/active/issues/model_provider_badge_mismatch_2026_08_21.md,
    /codex/15-runbooks/safe-service-restart-procedures.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/config/litellm/grok_gemini_proxy.yaml,
    agent-orchestrator/server/gemini_translation_smoke.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/gemini_headroom.py,
  ]
source: >-
  Operator, interactive session slot 15, 2026-08-21. Diagnosed live read-only against the
  orchestrator VM's own localhost:8765 API + journalctl + the activity feed. Operator
  explicitly ruled out two hypotheses mid-investigation ("the 3 gemini accounts is a very
  small reason, there are plenty of other accounts"; "even if 4 slots have dirty WIP there
  are plenty of other healthy slots") and directed a proper root-cause pass across the
  slots not yet checked — which is what surfaced the alias mismatch below.
---

## Measured state at diagnosis (2026-08-21 ~15:45 UTC)

| Signal                                       | Value                                                       |
| -------------------------------------------- | ----------------------------------------------------------- |
| Backlog total / queued / done                 | 4741 / 824 / 3705                                            |
| Queued with a REAL blocker                    | 442 (361 unmet prereq, 15 `gate_on_depends`, ~66 conditions) |
| Queued that AO itself calls dispatchable      | **382** ("eligible on slot(s) […] — waiting for one to idle") |
| Slots: idle / working / paused / stale        | 33 / 8 / 6 / 1 (of 48 rows)                                  |
| Idle slots that are REAL AO workers           | **19** (14 of the 33 are human/­per-tab presence slots)        |
| autospawn_succeeded vs autospawn_failed       | **7 vs 22 — a 76% failure rate**                             |
| Of those 7 "successes", zombie (400 on call)  | 5 (accounts proj1/proj2 — see primary cause)                 |

Both halves of the operator's question check out: there genuinely were free slots, and the
accounts genuinely had quota headroom. Neither was the constraint.

## PRIMARY root cause — proxy alias built from `variant`, workers send `id`

`config/litellm/grok_gemini_proxy.yaml` declared:

```yaml
- model_name: gemini-3.5-flash-lite-proj1 # DOTTED — built from accounts.json `variant`
```

while `~/.claude-accounts/gemini-3-5-flash-lite-proj1.env` exports:

```sh
export ANTHROPIC_MODEL=gemini-3-5-flash-lite-proj1   # DASHED — the accounts.json `id`
```

`gemini-3.5-flash-lite-proj1` != `gemini-3-5-flash-lite-proj1`, so every Gemini worker's
request named an unregistered model. Live evidence from AO's own activity feed
(`spawn_retry_cap_reached`, slots 7/10/14):

```
API Error: 400 {'error': 'anthropic_messages: Invalid model name
  passed in model=gemini-3-5-flash-lite-proj1. Call `/v1/models` to view
  available models for your key.'}
```

The config's own header comment asserted the contract correctly — "`model_name` below is
deliberately the SAME string each account's env file sets via ANTHROPIC_MODEL" — but then
named the wrong field in the parenthetical, "(accounts.py's `variant` field)". That
one-word error is the whole bug; the aliases were written to match the comment.

**Why the failure was invisible rather than loud**: the spawn SUCCEEDS (tmux session comes
up, `autospawn_succeeded` is logged, the slot shows `working`), and only then does every
API call 400. From every monitoring surface the account looks healthy — `status: healthy`,
RPM/RPD headroom intact (those counters are AO-local selection counts, never a proxy
round-trip). The worker idles until the watchdog reclaims it, and the cycle repeats.

**Why no test caught it**: `server/gemini_translation_smoke.py` resolves the model name by
reading this very config (`first_gemini_model_name`, `_gemini_native_model_id`). The smoke
test asked the proxy for the dotted alias the config declared, the proxy served it, and the
test passed — validating a string no spawned worker has ever sent. Test and production
exercised different strings, so a green suite carried no signal about the live path.

## Secondary causes and one amplifier (all still open)

1. **4 of 10 Gemini accounts are declared but never provisioned.**
   `gemini-3-5-flash-lite-proj4`, `gemini-3-7-flash-proj4` have no env file, no proxy alias
   and no API key; `gemini-3-5-flash-lite-proj5`, `gemini-3-7-flash-proj5` have an alias but
   no env file and no key (`GEMINI_API_KEY_PROJ5` is referenced by the config but absent from
   `.env.local`, which holds only PROJ1-3). They still get SELECTED for dispatch, burning a
   spawn attempt each time: `env_file … does not exist` accounted for 9 of the 22 failures.
2. **Dirty-state / branch-state quarantines on slots 8, 9, 11, 16, 22** — 11 of the 22
   failures. AO correctly refuses to spawn over unpreservable WIP. Real content:
   `features-service` 2 commits ahead, `unified-trading-pm` with unresolved conflict markers
   across 10 files (slot 11 also carries 993 dirty files), and an `oms-wt.oc3YkB` worktree
   with conflict markers in `pyproject.toml`. These are genuine and need per-slot judgment,
   NOT a bulk clear.
3. **AMPLIFIER — no health feedback loop on spawn failure.** A spawn that fails on a missing
   env file or an invalid model name does not mark the account unusable, so the free-provider
   selector re-picks the same broken accounts every tick. Measured: the two most-selected
   accounts in the window (`gemini-3-5-flash-lite-proj4` ×7, `gemini-3-7-flash-proj4` ×5)
   were both credential-less. Same CLASS as
   `/plans/archive/issues/worker_slot_account_exhaustion_no_rotation_2026_08_19.md`
   (`account_is_usable()` reading too narrow a signal) — but note that issue is `resolved`
   and archived, its quota-exhaustion gap fixed via `capability_tier()`
   (agent-orchestrator@36d56d8638). The gap measured here is a DIFFERENT axis the shipped
   fix was not built for: a STRUCTURAL defect (no credential file, no proxy alias) rather
   than a consumed ceiling. That distinction is why "only a few bad accounts" still degraded
   the whole fleet instead of being routed around.
4. **The proxy returns HTTP 500 where it should return 401**, so `/health` is useless as a
   monitor. LiteLLM's auth-error handler calls `PrismaDBExceptionHandler`, which does
   `import prisma`; that optional DB extra is not installed in
   `/home/ubuntu/.venvs/litellm-proxy`, so `ModuleNotFoundError: No module named 'prisma'`
   escapes as an unhandled 500 on EVERY unauthenticated request including `/health` and
   `/v1/models`. A keyless liveness probe therefore cannot distinguish "proxy fine, you sent
   no key" from "proxy broken".
5. **The running proxy is on a stale config.** `litellm-grok-gemini-proxy.service` shows
   `ActiveState=active`, `NRestarts=0`, `ExecMainStartTimestamp=2026-08-20 11:45:20`, while
   the config on disk was last modified `2026-08-21 09:10:10` — over 22h of edits never
   loaded. Nothing reloads this service on config change.

## Fixed in this pass

- [x] [INFRA] P0. **Correct every Gemini `model_name` alias to the dashed accounts.json `id`
      form** (`config/litellm/grok_gemini_proxy.yaml`), and rewrite the header comment that
      named `variant` instead of `id` — the misleading line that produced the bug. Restores
      6 of 10 Gemini accounts (proj1/2/3 × both variants) to fully READY: alias present, env
      file present, API key present, ANTHROPIC_MODEL matching. — agent-orchestrator@bee25ba8de
- [x] [INFRA] P0. **Regression guard** `tests/test_gemini_proxy_alias_account_id_alignment.py`
      — asserts every gemini-backed alias is in dashed `id` form (a dot fails the test), and,
      where `accounts.json` is present, that every account WITH a credential env file has an
      alias. Deliberately does not re-read the config to compare it against itself, which is
      exactly how the smoke test missed this. — agent-orchestrator@bee25ba8de

- [x] [INFRA] P0. **Cross-provider audit + a guard that reads what PRODUCTION reads.**
      Operator ask: "check that's not the case with other models as well, and make sure
      tests and prod use the same paths and names so we can check this early."
      **Audit result: Gemini was the only broken provider.** All 24 accounts / 6 providers
      checked by reading each env file's real `ANTHROPIC_MODEL` + `ANTHROPIC_BASE_URL` and
      resolving it against that backend's registry — 20/20 provisioned accounts now
      resolve (litellm ×7, deepseek ×2 by URL path, codex ×1 vs the bridge constant,
      anthropic ×8 correctly pinning no model, glm ×2 honestly reported SKIP as an
      external vendor API). Also checked the BILLING path, where a name mismatch withholds
      spend silently rather than erroring: `gpt-5.6-luna` and the Gemini aliases have no
      rate card, but both are DELIBERATE (`billing_shape_for_provider` = `subscription_
      unknown` and `rate_limited_free` respectively), not drift.
      Shipped `scripts/orchestrator/check_prod_model_names_resolve.py` +
      `tests/test_prod_model_name_resolution.py` — agent-orchestrator@ebfbde53f7.
      Covers three failure modes nothing was checking: Codex model drift (fails SILENTLY —
      the bridge serves its own constant regardless), DeepSeek routing to another account's
      `/accounts/<id>` path (silently misattributes usage/billing), and an Anthropic env
      file pinning `ANTHROPIC_MODEL` (silently overrides AO's chosen tier).

- [x] [INFRA] P0. **Restarted `litellm-grok-gemini-proxy.service` and VERIFIED the fix
      end-to-end with a real call** (2026-08-21 16:35 UTC; previously running since
      2026-08-20 11:45 with `NRestarts=0`). Re-tagged from `[OPERATOR]` to `[INFRA]`: the
      original tag was over-cautious — the workspace's standing rule is that maintenance
      restarts skip operator scheduling pre-live-trading, the diagnosis was complete, and
      the service was already 100% non-functional for Gemini so a restart could not worsen
      it. Verification is a REAL `/v1/messages` call, not the smoke test:
      `{"model":"gemini-3-7-flash-proj1",...}` returned a genuine assistant response with
      real token usage, and a deliberately bogus alias still 400s (proving the check is
      model-specific, not blanket-permissive).
- [x] [INFRA] P0. **Fixed a SECOND, latent breakage the restart exposed: the LiteLLM master
      key had been rotated in `.env.local` (mtime 2026-08-21 14:50) but none of the account
      env files were updated.** The proxy had been running since 2026-08-20 11:45, so the
      old process still held the PRE-rotation key in memory — auth kept working purely
      because nothing had restarted it. The moment it restarted, every account presented a
      token that was no longer the master key; LiteLLM then treats it as a *virtual* key,
      which requires a database it does not have (see the `prisma` todo below), so every
      call failed `No connected db.` — a completely different error from the alias bug, and
      one that would have looked like "the fix made it worse" without this trace. All 14
      env files shared one token (the old master key); the 7 LIVE ones
      (6 gemini + gemma-self-hosted) were re-synced to the current master key, each with a
      `.env.bak-2026-08-21T164000Z-masterkey-sync` backup. `gemma-self-hosted.env` is
      root-owned and needed `sudo`. **Standing risk this leaves**: nothing keeps these in
      sync, so the next master-key rotation re-breaks the whole fleet the next time the
      proxy restarts — and it will again be silent until then. See the new todo below.
      NOTE `gemini-3-5-flash-lite-proj1` now returns a real Google `429 quota exceeded`
      (free-tier input-token quota genuinely spent) — that is the vendor's real limit
      working as designed, NOT a remaining config fault; `gemini-3-7-flash-proj1` on the
      same key answers normally.

## Open todos

- [ ] [INFRA] P1. **Keep account env files and the LiteLLM master key in sync automatically.**
      The 2026-08-21 rotation broke every proxied account the instant the service restarted,
      and stayed invisible until then because the running process held the old key in
      memory. Either derive the account token from the same source at spawn time rather than
      duplicating it into 14 files, or add a startup/pre-spawn check that refuses (loudly) on
      a token/master-key mismatch. `check_prod_model_names_resolve.py` deliberately does NOT
      read auth tokens, so it cannot catch this class — a separate check is needed.
- [ ] [INFRA] P1. **Run `check_prod_model_names_resolve.py` on a schedule** — it is
      currently only run by hand, which is the same "nobody thinks to look" gap that let
      the original bug live for days. Wire it into `/ao-watchdog`'s pass (cheapest) or its
      own systemd timer, and page on exit 1. On a slot checkout it needs
      `--repo-root /home/ubuntu/unified-trading-system-repos/agent-orchestrator` to see the
      deployed host state.

- [ ] [OPERATOR] P0. **Restart `litellm-grok-gemini-proxy.service`** so the corrected aliases
      load. The service is already serving a >22h-stale config and is currently 100%
      non-functional for Gemini, so a restart cannot make it worse; per
      `/codex/15-runbooks/safe-service-restart-procedures.md` diagnose-before-restart, the
      diagnosis is complete and recorded above. Verify AFTER restart with a REAL spawned
      worker (not the smoke test): confirm a Gemini slot completes a turn without
      `Invalid model name`, and re-measure the autospawn success rate.
- [ ] [OPERATOR] P1. **Provision or remove the 4 unprovisioned Gemini accounts.** proj4 (both
      variants) needs an API key in GSM + `.env.local` + a `~/.claude-accounts/<id>.env` +
      a proxy alias; proj5 (both variants) needs `GEMINI_API_KEY_PROJ5` + env files. Until
      then they are selected for dispatch and waste a spawn attempt each tick. If they are
      not going to be provisioned, remove them from `accounts.json` so the selector stops
      picking them.
- [ ] [BACKEND] P1. **Mark an account unusable after a structural spawn failure** (missing
      env file, unregistered model alias) so the selector routes around it instead of
      re-picking it every tick. NOTE the obvious prior-art doc is already CLOSED:
      `/plans/archive/issues/worker_slot_account_exhaustion_no_rotation_2026_08_19.md` is
      `status: resolved` (archived 2026-08-21 — its `account_is_usable()` gap was fixed via
      `model_capability_aware_dispatch_audit_2026_08_21.md`'s `capability_tier()`,
      resolved_by agent-orchestrator@36d56d8638), so this is NOT a matter of folding into
      open work there. START by checking whether `capability_tier()`/`account_is_usable()`
      as shipped already covers a STRUCTURAL failure (credential file absent, alias absent)
      as opposed to the QUOTA/ceiling exhaustion it was built for — the 2026-08-21 evidence
      says it does not (`gemini-3-5-flash-lite-proj4` was re-selected 7× in one window with
      no env file), but confirm against the shipped code before designing a fix.
- [ ] [BACKEND] P1. **A 400 from the provider must not read as a successful spawn.** A worker
      that boots and then fails every API call is currently logged `autospawn_succeeded` and
      shown `working`; it should be detected and the account/slot marked, so this failure mode
      is loud instead of silent. `spawn_retry_cap_reached` already captures the pane text —
      that signal exists and is simply not wired to account health.
- [ ] [INFRA] P2. **Install `prisma` into the litellm venv, or pin a LiteLLM build that
      degrades gracefully**, so an unauthenticated request returns 401 instead of a 500 from
      `ModuleNotFoundError`. Then wire a real keyless liveness probe for the proxy — there is
      currently no monitor that would have caught 22h of total unavailability.
- [ ] [INFRA] P2. **Reload the proxy on config change** (systemd path unit or an
      `ao-self-pull.sh`-style hook), so a committed config edit cannot sit unloaded for a day.
- [ ] [OPERATOR] P2. **Resolve the quarantined slot WIP** on slots 8, 9, 11, 16, 22 — each
      needs judgment (is the ahead-of-origin commit real work to preserve? are the conflict
      markers abandoned?). Slot 11's `unified-trading-pm` (993 dirty files, conflict markers in
      10 files) is the largest. Explicitly NOT a bulk-clear job.
- [ ] [BACKEND] P3. **A plan declares a role that does not exist.** The regen loop logs:
      `resolved task role 'worker # was: data (not a valid agents/*.md registry entry; corrected
      na_eligibility_audit 2026_08_19)' is not a defined agent role — its tasks will be
      unclaimable`. A malformed `assigned_role` string leaked into a plan; find and fix it, and
      consider validating `assigned_role` at regen time so it fails loud at authoring.

## Lessons

- **A test that derives its input from the artifact under test proves only self-consistency.**
  The Gemini smoke test read the config to build its request, so it could never detect that
  the config disagreed with production. Where two systems must agree on a string, the test has
  to assert the CONTRACT (the account-id form), not re-read one side.
- **A test that always SKIPS is worse than no test — it reads green forever while proving
  nothing.** The first version of the cross-provider guard was written as a pytest. It
  "passed" by skipping all 5 cases: `config.accounts_path()` is repo-relative, so from any
  slot it resolves to a `data/config/accounts.json` that does not exist, and tests only ever
  run in slots. That is the SAME false-assurance failure as the smoke test above, just
  wearing a different disguise — so it was deleted rather than shipped. The honest split is
  two layers: the repo-verifiable invariant (alias FORM) stays a CI test, and the host-state
  check becomes a script that runs where the state actually lives. When adding a guard, check
  it can actually EXECUTE in the environment it will run in, and that it FAILS on the real
  broken input (`test_catches_the_2026_08_21_dot_vs_dash_mismatch` feeds the guard the
  genuine dotted-vs-dashed inputs and asserts BROKEN) — a guard only ever exercised against
  already-fixed state demonstrates nothing.
- **`| tail`/`| head` on a gate run fabricates exit 0 AND truncates the diagnosis.** A gate
  run reported "completed (exit code 0)" while its own log said `❌ FAILED`, because the pipe
  returned `tail`'s status. It cost a full round-trip and nearly produced a false "green"
  claim to the operator. Redirect to a file (`> log 2>&1`), never pipe, and read the log's
  own verdict line rather than trusting the exit code.
- **"Service active" and "account healthy" are both proxies, not measurements.** systemd
  reported the proxy `active (running)` throughout; AO reported all 10 Gemini accounts
  `healthy` with full quota headroom. Both were true and both were useless — the only signal
  that carried the failure was the worker's own pane text, captured in
  `spawn_retry_cap_reached` and not wired to anything.
- **Ruled out before landing on the real cause** (recorded so nobody re-walks them): the QG
  host governor (admitting freely); the fleet worker cap (`ORCHESTRATOR_FLEET_WORKER_CAP=20`
  confirmed loaded in the live process's `/proc/<pid>/environ`, not the hardcoded default 10 a
  code read alone would suggest); disk pressure (19.25% free vs a 3% halt threshold); a dead
  AutoSpawnLoop (it was ticking and attempting spawns throughout).

- **A phantom "every repo is diverged" signal that cost real investigation time — recorded so
  the next person doesn't chase it.** An early sweep flagged `unified-trading-ci` as 5 commits
  ahead of origin in EVERY slot, which looked like a fleet-wide git problem. It was not:
  1. **My own measurement error first.** The sweep compared `origin/live-defi-rollout..HEAD`
     across every repo uniformly, but `unified-trading-ci` tracks `main`, not LDR. Against its
     OWN upstream every slot is `ahead=0 behind=0`, clean. Comparing against a branch a repo
     does not track manufactures a divergence that isn't there — scope a drift sweep to each
     repo's actual upstream (`@{u}`), never to one hardcoded branch name.
  2. **The underlying branch pair is also NOT diverged, despite what the counters say.**
     `origin/main` reads 5 ahead of `origin/live-defi-rollout` and LDR reads 7 ahead of main,
     which looks like a stalled two-way reconciliation. Measured: `git diff --name-only
     origin/main origin/live-defi-rollout` returns **0 files**, and all 5 duplicated-message
     commit pairs are byte-identical by `git patch-id --stable` (`cc06424`≡`3209654`,
     `632ca90`≡`e69bb66`, `bbdbbb3`≡`239b407`, `6e92bcd`≡`93209b7`, `c0d10ba`≡`403c921`).
     The two branches carry IDENTICAL trees. The counts are pure SHA-level bookkeeping from
     syncing by cherry-pick/rebase instead of merge, which re-writes each commit and so leaves
     the ahead/behind counters permanently non-zero. **Nothing is missing from either branch
     and there is nothing to fix in content** — but the counters will keep reading "diverged"
     forever and will keep drawing investigations. Verify content (`git diff`/`patch-id`)
     before ever treating an ahead/behind count in this repo as a real finding.
