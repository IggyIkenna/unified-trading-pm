---
doc_type: issue
title: 'Fleet-wide mid-task-death sweep — remaining models (Gemini, Claude sub-accounts, GLM, Gemma) root-caused, 3 classification/forensics gaps fixed'
summary:
  'Continuation of ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md after codex-luna and DeepSeek were
  root-caused: swept every OTHER account family for the same mid-task-kill class via a 21-day tmux_session_lost
  DB lookback (Gemini 57 unexplained, Claude sub-accounts 377, GLM 11, gemma-self-hosted 3) followed by a 9-agent
  Workflow investigation (5 cluster deep-dives + 3 adversarial verify passes, one cluster given two independent
  lenses given its size). Headline result: the pkill-guard PATH-wrapper fix already shipped for DeepSeek
  (agent-orchestrator@2fe498b30f) explains 98.6% of the single biggest unexplained population fleet-wide (214
  events across 4 Claude sub-accounts) — it was already working, just not yet confirmed against this population.
  A separate, genuine classification gap was found and fixed: autospawn.py deliberately kills a live worker the
  instant its account falls out of dispatch headroom (working as designed), but tmux_pruner.py never recognized
  the event this kill logs, so every one of these misclassified as "unexplained" and wrongly penalized the
  account''s health tracking. Two more instances of the same gap (orphan_session_reclaim,
  idle_lingering_session_reclaim) and a fleet-wide forensics PATH bug (ausearch has never once successfully run,
  ever, on any death) were found and fixed in the same sweep. A Gemini LiteLLM proxy config bug (dotted vs
  dashed model-name aliases, causing live 400s) was independently found and fixed by a different session
  moments before this one attempted the same fix — discarded in favor of theirs.'
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [multi-agent-safety, agent-orchestrator, dispatch, death-forensics, classification-gap, ao-fleet-death, gemini, claude, glm, gemma]
related:
  [
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /plans/archive/issues/pkill_guard_dead_on_exec_into_claude_recurrence4_2026_08_21.md,
    /plans/active/issues/ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
priority: P1
parent_epic: agent_operating_framework_master
source: "Operator, interactive session (slot 12), 2026-08-21: 'okay now lets go over other models claude and gemini and all models that are remaining to be tested for the mid-task kill issues and update the documents with proper findings. and please look at as many jsonl files or log files of sessions as you have to so we can eliminate this at root for all models and fix this once and for all'"
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/death_forensics.py,
    agent-orchestrator/scripts/orchestrator.service,
    agent-orchestrator/config/litellm/grok_gemini_proxy.yaml,
  ]
---

# Fleet-wide mid-task-death sweep — remaining models root-caused (2026-08-21)

## Scoping

21-day `tmux_session_lost` lookback (2026-08-21), grouped by `account_id`/`death_class`, joined against a
`worker_account_unusable_killed`-within-120s check to separate "already explained by the known classification
gap" from genuine residual:

| account | unexplained (21d) | classification-gap matches |
| --- | --- | --- |
| sub-c-ikenna-odum | 79 | 0 |
| sub-g-alpavolt | 50 | 0 |
| sub-d-odum1default | 47 | 0 |
| sub-f-odum2default | 38 | 0 |
| sub-b-iggy2london | 80 | 12 |
| sub-h-igboestates | 36 | 13 |
| sub-e-odum2default | 29 | 3 |
| sub-a-ikenna | 18 | 12 |
| gemini-3-5-flash-lite-proj1 | 25 | 19 |
| gemini-3-7-flash-proj1 | 12 | 4 |
| gemini-3-5-flash-lite-proj2/3, gemini-3-7-flash-proj2/3 | 20 | 11 |
| glm-5-2 | 9 | 0 |
| glm-5-turbo | 2 | 0 |
| gemma-self-hosted | 3 | 0 |

The 4 Claude sub-accounts with ZERO classification-gap matches (sub-c/g/d/f, 214 events combined) are the single
biggest unexplained population fleet-wide — bigger than codex-luna (81) or DeepSeek (53) combined — and became
the highest-priority target.

## Findings

### 1. Classification gap: `worker_account_unusable_killed` (fixed, `agent-orchestrator@dc1d273f89`)

`autospawn.py`'s `_drain_worker_account_failover` deliberately kills a live worker the instant its bound account
falls out of dispatch headroom (disabled/rate-limited/auth-failed/over its pct ceiling — for Gemini, over its
RPM/RPD ceiling) — a genuine, working-as-designed failover, not a bug. It logs `worker_account_unusable_killed`
to `activity_log` right before the kill. But `tmux_pruner.py`'s `_INTENTIONAL_TEARDOWN_SIGNAL_EVENTS` tuple —
the list of event types that make the death classifier read `intentional_teardown` instead of `unexplained` —
never included it. Every one of these kills therefore misclassified as `unexplained`, wasting OOM/external-kill
forensics AND (via `tmux_pruner.py`'s existing `record_spawn_outcome` hook on unexplained deaths) wrongly
recording a spawn FAILURE against the account's in-memory health ring — penalizing an account for a failover
that was never its fault.

Measured match rate (deaths preceded by `worker_account_unusable_killed` within 120s, same slot): 100% for
`gemini-3-7-flash-proj2`, 76% for `gemini-3-5-flash-lite-proj1`, 15-67% for several Claude sub-accounts — but
ZERO for codex-luna, DeepSeek, GLM, Gemma, and (critically) the sub-c/g/d/f mystery cluster below.

**Fix**: added `worker_account_unusable_killed` to `_INTENTIONAL_TEARDOWN_SIGNAL_EVENTS`, auto-covered by the
existing parametrized regression suite (`tests/test_tmux_pruner_death_class_signals.py`).

### 2. The sub-c/g/d/f mystery cluster (214 events) — substantially explained, not a new bug

Two independent investigation lenses (transcript-reading + host/infra-correlation) sampled this cluster:

- **211/214 (98.6%) occurred BEFORE the pkill-guard PATH-wrapper fix landed**
  (`agent-orchestrator@2fe498b30f`, 2026-08-21 13:55:20 UTC — see
  `pkill_guard_dead_on_exec_into_claude_recurrence4_2026_08_21.md`); only 4 isolated (non-clustered) events
  occurred after. This is the SAME cross-slot pkill-guard mechanism already root-caused for DeepSeek — a bare
  `pkill -f "<name>"` from any slot's Bash tool call, unguarded due to the dead sourced-shell-function guard,
  killing every slot running that same-named process simultaneously. The fix already shipped applies fleet-wide
  (a PATH-prepended executable wrapper, not account-specific), and this population's post-fix data confirms it
  is working — no further code change needed here.
- Adversarial verification REFUTED a competing theory from this investigation (that `ao-self-pull.sh`'s
  `systemctl restart orchestrator` cycle directly kills tmux worker panes): `orchestrator.service`'s
  `KillMode=process` (root-caused + fixed 2026-05-20, per the unit's own comment) specifically prevents this —
  a restart SIGTERMs only the uvicorn main PID, and `tmux_spawn.py` decouples worker sessions via `setsid`. The
  measured correlation (5/123 residual rows near a restart) was statistically consistent with chance
  (~3.6 expected), not causation.
- **Residual sibling classification gap found, not yet fixed**: an account-wide Claude session-limit hit
  freezes every slot bound to that account near-simultaneously. AO's own `_handle_account_blocked_pane` is
  deliberately alert-only (a 2026-08-14 incident is the reason it never force-kills), so the frozen slots
  instead each independently breach the GENERIC heartbeat-staleness threshold and get a legitimate watchdog
  force-kill — but because they froze together, these land within seconds of each other, and none of the
  events this specific watchdog path emits are in `_INTENTIONAL_TEARDOWN_SIGNAL_EVENTS`, so every one
  misclassifies as unexplained. Affects `sub-d-odum1default`/`sub-f-odum2default` per the sample. See Todo.

### 3. Two more classification-gap event types (fixed, `agent-orchestrator@0704ed0a47`)

`worker_liveness_watchdog.py`'s orphan-session and idle-lingering-session reclaimers (both legitimate,
working-as-designed teardowns, confirmed live via matching `journalctl` lines to specific Gemini deaths within
the classifier's 90s lookback window) had NO distinctly-named `activity_log` event at all before this fix —
`kill_session()`'s `reason=` kwarg only ever reached a plain `logger.warning` line, invisible to the classifier
(unlike `worker_account_unusable_killed`, which at least had its own `log_activity()` call). Added the
companion `log_activity()` call at both call sites (`orphan_session_reclaim`, `idle_lingering_session_reclaim`)
and wired both into the classifier tuple. Factored the kill+log logic into two small helper methods
(`_kill_orphan_session_and_log`, `_log_reclaim_teardown_event`) to keep `_tick_once` under the ruff C901
complexity ceiling (inlining pushed it to 27 > 26). New regression tests confirm both the event fires and its
`slot_id`/`account_id` payload is correct; `tests/test_worker_liveness_watchdog.py::_make_slot` gained an
explicit `account_id` parameter (previously an unconfigured `MagicMock` attribute there would have raised
`TypeError` on JSON-serialization once a real caller started passing it through).

### 4. Fleet-wide forensics blind spot: `ausearch` has never once successfully run (fixed, same commit as #3)

`orchestrator.service`'s `Environment="PATH=...` omitted `/usr/sbin` (and `/sbin`) — but `ausearch` lives at
`/usr/sbin/ausearch`. Every `subprocess.run(['ausearch', ...])` inside `death_forensics.py`'s
`check_external_kill` raised `FileNotFoundError`, caught by its best-effort wrapper and reported as
`external_kill.checked=false`. Measured: **578/578** `unexplained_death_forensics` rows fleet-wide show this —
meaning every prior "external kill not suspected" verdict, across every investigation this session and before,
carried ZERO evidentiary weight for this leg. It was never checked, not checked-and-clean. (The OOM leg was
unaffected — `journalctl` sits on `/usr/bin`, already on the old PATH — so OOM-ruling-out conclusions from
earlier in this sweep stand.) Fixed by adding `/usr/sbin:/sbin` to the systemd unit TEMPLATE
(`scripts/orchestrator.service`) — self-heals onto the live unit via `ao-self-pull.sh`'s idempotent
`install-orchestrator-service.sh` re-run (every ~2 min), no separate deploy action needed.

**Structural gap noted, not fixed**: even with the PATH bug fixed, `ausearch`'s EXECVE-based audit search can
never see AO's OWN `kill_session()` calls — they fire via direct `os.kill(pid, SIGTERM/SIGKILL)` syscalls from
within the long-running orchestrator process, never an execve'd subprocess. auditd's EXECVE record type is
structurally blind to this entire class (~20 call sites). Closing this needs a different audit rule type
(SIGNAL records, not EXECVE) — not attempted this session, tracked as a todo.

### 5. Gemini LiteLLM proxy model-name mismatch — found here, fixed independently elsewhere

`config/litellm/grok_gemini_proxy.yaml`'s `model_name` aliases used dots (`gemini-3.5-flash-lite-proj1`) while
every real request's `ANTHROPIC_MODEL` (confirmed via the live per-account `~/.claude-accounts/<id>.env`) uses
dashes (`gemini-3-5-flash-lite-proj1`) — every affected request immediately 400'd with
`litellm.proxy.route_llm_request.ProxyModelNotFoundError`, 650 occurrences in one day (journalctl-confirmed),
steadily from ~11:00 UTC onward. **Independently fixed by a different session (slot-15) as
`agent-orchestrator@bee25ba8`, 2026-08-21 16:09:38 UTC — minutes before this investigation's own fix attempt.**
Discovered via quickmerge's not-behind gate blocking on a real working-tree overlap (both sessions edited the
same file, same direction) when this session tried to ship its own copy. Their fix is more thorough (a
dedicated new test file, `tests/test_gemini_proxy_alias_account_id_alignment.py`, plus a fix to
`gemini_translation_smoke.py`'s own same-source-of-truth gap this investigation didn't catch: the smoke test
resolved its model name by reading the same yaml file production reads, so a bug in the yaml never showed up as
a test failure). This session's own copy was discarded in favor of theirs after pulling and comparing — not
duplicated.

### 6. Lower-priority / not yet acted on

- **GLM shared-key blind quota estimator**: `glm-5-2`/`glm-5-turbo` share ONE physical Zhipu "Coding Plan" API
  key (both accounts' env files fetch the same GSM secret). Z.ai's API exposes no real quota/rate-limit signal
  at all (confirmed via `glm_quota_poller.py`'s own docstring), so its count-based usage estimate under-reports,
  and a real 429 (`[1308][Usage limit reached for 5 hour...]`, confirmed byte-for-byte in 3 separate jsonl
  transcripts) shows in `account_snapshot` as `account_status=healthy`. 11 unexplained deaths over 21 days. No
  clean fix without a real upstream quota endpoint.
- **`sub-f-odum2default`-specific residual pattern**: its slots run a `cicd`/monitoring role
  (cloud-build-failure-watcher, ldr-ci-monitor, escalation dispatch) whose background Monitor/task-notification
  watches sometimes conclude right at the moment of an "unexplained" death (not a mid-turn crash) — 3 samples,
  not yet confirmed as a real pattern vs. coincidence.
- **Possibly-stale `context_activity_silence_detected` reading**: one sampled slot showed
  `minutes_silent=1791` against a 14400s window just 9 minutes before its death, while `slot_progress` events
  showed it actively working at that exact time — flagged, not investigated further.
- **gemma-self-hosted**: all 3 unexplained deaths were the SAME single incident (a litellm/Ollama
  `reasoning_effort`-mapping bug, `"gemma3:27b" does not support thinking"`), already root-caused and fixed
  2026-08-20 (`config/litellm/ollama_thinking_monkeypatch.py`) — zero recurrences since. No action needed.

## Todo

- [x] ✅ [BACKEND] P0. Add `worker_account_unusable_killed` to `tmux_pruner.py`'s
      `_INTENTIONAL_TEARDOWN_SIGNAL_EVENTS`. Shipped `agent-orchestrator@dc1d273f89`, auto-covered by the
      existing parametrized regression suite.
- [x] ✅ [BACKEND] P1. Add companion `log_activity()` calls for `orphan_session_reclaim` and
      `idle_lingering_session_reclaim` in `worker_liveness_watchdog.py`, wire both into the classifier tuple,
      new regression tests. Shipped `agent-orchestrator@0704ed0a47`.
- [x] ✅ [INFRA] P1. Fix `orchestrator.service`'s PATH to include `/usr/sbin:/sbin` so `ausearch` can actually
      run. Shipped in the same commit as above.
- [x] ✅ [INFO] P2. Gemini proxy model-name mismatch — confirmed already fixed independently
      (`agent-orchestrator@bee25ba8`); no action needed here.
- [x] ✅ [INFRA] P2. **DONE 2026-08-21** — `agent-orchestrator@31c90ca3c1`. Found: no such event_type existed at
      all (a genuine gap, not just a missing tuple entry) — `worker_liveness_watchdog.py`'s
      `_resume_or_fresh_respawn` kills the old session then tries to `--resume` on the SAME account (correct for
      an ordinary heartbeat-silence, wrong when the account is frozen); the resume-spawn raises, and the except
      branch wrote `status="killed"` with ZERO `activity_log` signal anywhere on that path. Added a
      `"heartbeat_resume_respawn_failed"` `log_activity()` call there and to the classifier tuple. Note: a
      pre-existing comment on the tuple called this exact case (grouped with 3 siblings) "inert" to add, reasoning
      the old session name gets overwritten by a fresh respawn before `tmux_pruner` ever sees it — but
      `tmux_session` is never cleared in that except branch, so it's a genuine RACE, not a guarantee; this fix
      only helps the sub-case where `tmux_pruner`'s tick wins the race (a real row IS produced and was
      misclassified `unexplained`) and is a no-op, never a regression, when the respawn wins first. New test
      asserts the activity event; full quality-gates.sh green.
- [ ] [INFRA] P3. `death_forensics.check_external_kill`'s EXECVE-based search is structurally blind to AO's own
      `kill_session()` calls (direct `os.kill()` syscalls, not an execve'd subprocess) — needs a different audit
      rule type (auditd SIGNAL records) to close, not attempted this session.
- [ ] [DATA] P3. GLM shared-key blind quota estimator — no clean fix without a real upstream quota endpoint;
      consider pattern-matching the literal `[1308][Usage limit reached...]` 429 body as a stopgap
      classification signal if this recurs at volume.
- [ ] [DATA] P3. `sub-f-odum2default`'s cicd/monitoring-role residual pattern and the possibly-stale
      `context_activity_silence_detected` reading — both need more samples/investigation before a fix can be
      designed.
- [ ] [DOC] P3. Monitor for recurrence: confirm no new cross-slot broad-pkill-style mass-death bursts appear
      now that the pkill-guard-bin fix is live, and confirm the classification-gap fixes correctly reduce the
      "unexplained" share of new deaths (re-run this doc's scoping query in a week+).
- [ ] [OPERATOR] P1. `gemini-3-5-flash-lite-proj4` and `gemini-3-7-flash-proj5` have NO credential env file on
      this host (`~/.claude-accounts/<id>.env` does not exist) — confirmed live 2026-08-21 18:24-18:47 UTC via
      repeated `autospawn_failed` events on slots 3/4/25, all with the identical error
      `env_file ... does not exist; cannot authenticate spawn`. Every respawn attempt AO makes onto these two
      accounts fails instantly, which is directly stalling recovery for whichever slot gets picked next (a
      normal orphan-reclaim or one-task-per-session recycle then can't find a working account to resume onto).
      Needs `claude setup-token` run on a browser machine for both accounts, per
      `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`.
      **Mitigated 2026-08-21 (same session)**: both accounts DISABLED via `POST /api/accounts/{id}/disable`
      (the existing operator-directed-pause endpoint — sticky, excludes the account from spawn/rotation and
      immediately rotates any slot currently on it, until a matching `.../enable` call) — confirmed
      `status: disabled` for both post-call. This stops the respawn-failure loop above from recurring; the
      credential-provisioning ask itself is unchanged and still needs the operator. Re-enable each only after
      its `~/.claude-accounts/<id>.env` exists and `claude setup-token` has been run.
      **Operator asked directly 2026-08-21 (continued)**: chose "defer for now" — both accounts stay disabled,
      no further action from either side until revisited. Not stale; explicitly reviewed and deferred, not
      forgotten.
- [x] ✅ [BACKEND] P2. **NEW, found 2026-08-21 while live-validating the day's fixes on slots 3/4/25**: a normal,
      already-correctly-tagged intentional teardown can still misclassify as "unexplained" if the IMMEDIATE
      respawn attempt that follows it fails/stalls long enough to push `tmux_pruner`'s actual detection past
      the classifier's 90s `_INTENTIONAL_SIGNAL_LOOKBACK_SECONDS` window. Concretely reproduced on slot 25: a
      completely ordinary `worker_one_task_per_session_reset` fired at 18:43:55.628 (task
      `w15_close_out_gate_and_line_cap` had just finished cleanly) — `kill_session(reason="manual")` followed
      2ms later (confirmed via `ausearch`: the `tmux kill-session -t orch-slot-25` EXECVE record's `ppid` matches
      the live orchestrator process exactly, so this was AO's own code, not an external actor). The immediate
      respawn landed on `gemini-3-5-flash-lite-proj4` (the missing-credentials account above) and failed
      instantly at 18:45:11 — `tmux_pruner`'s next sweep didn't confirm the session actually gone until
      18:45:35, ~100 seconds after the reset event, just past the 90s window. Result: a perfectly-explained
      death read `death_class="unexplained"`, `death_class_signal_event=null`, and (being the first-ever
      confirmed positive external-kill hit post the `ausearch` PATH fix above) briefly looked like a genuine new
      external-kill mystery before the timeline was traced.

      **DONE 2026-08-21** — `agent-orchestrator@6d8f314f01`. Went with the third candidate (targeted re-check),
      not a global window widen (risks an unrelated OLDER signal explaining away a genuinely new death) or a
      new failed-respawn event (the existing `autospawn_failed` event already covers this — no new event
      needed). When the normal 90s lookback finds nothing, check for a recent `autospawn_failed` event on the
      same slot within that same 90s; if found, re-run the SAME signal search over a bounded 180s window
      instead. A new `death_class_widened_lookback` detail field marks when this path fired, so a widened match
      stays auditable rather than silently indistinguishable from a normal fast one. 2 new tests (reproduces the
      slot-25 timeline exactly; confirms an old signal WITHOUT a recent respawn failure still correctly stays
      unexplained); full quality-gates.sh green. Also documented `death_forensics.py`'s real ~25-30min auditd
      retention constraint (measured this session — see the two historical-forensics todos above) directly in
      its module docstring.

## Progress Log

- 2026-08-21 (slot 12, interactive session): operator asked to sweep every remaining model for the same
  mid-task-death class already root-caused for codex-luna/DeepSeek, reading real jsonl/log evidence rather than
  aggregate correlation alone. Scoped via a 21-day DB lookback, then ran a 9-agent Workflow (5 cluster
  investigations in parallel + 3 adversarial verify passes). While waiting on the workflow, independently found
  and confirmed the `worker_account_unusable_killed` classification gap directly in the code (not from the
  workflow) — implemented, tested, shipped as `agent-orchestrator@dc1d273f89` before the workflow even
  completed. Workflow findings then folded in: the sub-c/g/d/f mystery cluster substantially explained by the
  already-shipped pkill-guard fix; 2 more classification-gap events plus the ausearch PATH bug found and fixed
  as `agent-orchestrator@0704ed0a47`; the Gemini proxy bug found but discovered already independently fixed
  elsewhere (`bee25ba8`) via a quickmerge working-tree-overlap block, resolved by pulling theirs in rather than
  duplicating. One real mid-session mistake, caught before it caused harm: briefly edited `tmux_pruner.py`
  directly in the SHARED top-level `agent-orchestrator` checkout (used by the live server + other sessions)
  instead of this slot's own `.tabs/12` worktree — caught, reverted cleanly there via `git checkout --`
  (confirmed nothing else was touched, since it was purely my own uncommitted diff), redone correctly in
  `.tabs/12`. Filed this as a new, dedicated doc (split from `ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`
  to keep that doc under its 1000-line hard cap) rather than merged, matching the precedent that doc's own
  Cluster-B finding already set.
- 2026-08-21 (same session, continued): operator asked to check slots 3, 4, and 25 specifically (killed very
  recently) and find the real reason. Traced each directly from live `activity_log` + `journalctl` +
  (for slot 25) `ausearch` — the first genuinely useful live test of today's `ausearch` PATH fix. Slots 3/4:
  real GLM 429s (the already-documented GLM blind-quota gap above), correctly reclaimed via today's
  `orphan_session_reclaim` fix (`death_class=intentional_teardown` confirmed in the DB) — then stalled because
  the respawn landed on the missing-credentials Gemini accounts. Slot 25: genuinely new finding, folded into a
  new todo above — a legitimate reset misclassified as unexplained purely due to a timing gap against the
  classifier's 90s lookback, discovered via `ausearch`'s first-ever positive external-kill hit (which turned
  out to be AO's own process, confirmed by matching `ppid`, not an external actor — a real, reassuring
  confirmation that the earlier "structural os.kill blind spot" finding doesn't mean every future ausearch hit
  is untrustworthy, just that AO's OWN internal os.kill()-based reaping sub-step stays invisible to it).
  Reported findings directly in chat; converted both into tracked todos (the missing-credentials operator ask,
  the lookback-window timing gap) before this checkpoint per the workspace's own no-chat-only-findings rule.
- 2026-08-21 (same session, continued): operator asked to pause the two credential-less Gemini accounts.
  Confirmed both still existed live via `GET /api/accounts` (status `healthy` — the poller has no way to
  detect a missing credential file until actual spawn time, so account-level status hadn't caught up to the
  problem), then disabled both via `POST /api/accounts/{id}/disable` — confirmed `status: disabled` in the
  response for each. Noted inline on the `[OPERATOR] P1` todo above rather than as a separate item, since it's
  a mitigation of that same finding, not a new one.
